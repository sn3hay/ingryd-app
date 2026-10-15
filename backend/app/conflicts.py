"""Rules-based conflict check between products in one routine. No LLM: the model only explains the flags.

Rules in rules/conflicts.json are written on ingredient families (retinoid, aha, ...), which come
from the `family` field in rules/ingredients.json. Only rules with status "reviewed" are used.

A rule's severity is adjusted for the products and the person, and kept at or below "avoid":
  one level down  when either product's active is weak: the product is rinse-off, or the active
                  is in the last third of a longer list (percentages are not stored, so list
                  position stands in for strength); below "caution" there is no flag
  one level up    when the rule has raise_if_sensitive and the profile's skin type is sensitive
"""

import json
from dataclasses import dataclass
from functools import lru_cache

from app.scoring import RULES_DIR, Rules, find_rating, load_rules

SEVERITIES = ("caution", "separate", "avoid")  # lowest first
STATUSES = ("draft", "reviewed")


@dataclass(frozen=True)
class Product:
    id: str
    ingredients: list[str]
    category: str | None = None


@dataclass(frozen=True)
class ConflictRule:
    id: str
    a: str
    b: str
    severity: str
    reason: str
    suggestion: str
    raise_if_sensitive: bool
    source: str
    status: str


@dataclass(frozen=True)
class ConflictRules:
    trace_after_share: float  # an active past this share of the list is a trace amount
    trace_min_ingredients: int  # shorter lists have no trace amounts
    rules: tuple[ConflictRule, ...]


@dataclass(frozen=True)
class Flag:
    rule_id: str
    severity: str  # after adjustments
    rule_severity: str  # as written in the rule
    adjustments: tuple[str, ...]  # why the severity changed, e.g. "rinse-off product"
    product_id: str  # the routine product that conflicts with the new one
    reason: str
    suggestion: str
    source: str


def parse_conflict_rules(data: dict) -> ConflictRules:
    rules = tuple(
        ConflictRule(
            id=r["id"], a=r["a"], b=r["b"], severity=r["severity"], reason=r["reason"],
            suggestion=r["suggestion"], raise_if_sensitive=r["raise_if_sensitive"],
            source=r["source"], status=r["status"],
        )
        for r in data["rules"]
    )
    return ConflictRules(data["trace_after_share"], data["trace_min_ingredients"], rules)


@lru_cache(maxsize=1)
def load_conflict_rules() -> ConflictRules:
    return parse_conflict_rules(json.loads((RULES_DIR / "conflicts.json").read_text()))


def normalize(ingredient: str, rules: Rules | None = None) -> str | None:
    """The ingredient's family, or None when it has none or is not rated."""
    rating = find_rating(ingredient, rules or load_rules())
    return rating.family if rating else None


def actives(product: Product, rules: Rules | None = None,
            conflict_rules: ConflictRules | None = None) -> dict[str, str]:
    """{family: "full" or "weak"}; a family found at full strength anywhere in the list is full."""
    rules = rules or load_rules()
    conflict_rules = conflict_rules or load_conflict_rules()
    rinse_off = product.category in rules.rinse_off_categories
    count = len(product.ingredients)
    has_trace = count >= conflict_rules.trace_min_ingredients

    found: dict[str, str] = {}
    for position, name in enumerate(product.ingredients, start=1):
        family = normalize(name, rules)
        if family is None:
            continue
        trace = has_trace and position / count > conflict_rules.trace_after_share
        if rinse_off or trace:
            found.setdefault(family, "weak")
        else:
            found[family] = "full"
    return found


def unchecked(product: Product, rules: Rules | None = None) -> list[str]:
    """Ingredients that are not rated, so could not be checked for conflicts."""
    rules = rules or load_rules()
    return [name for name in product.ingredients if find_rating(name, rules) is None]


def _adjust(rule: ConflictRule, weak: bool, sensitive: bool) -> tuple[str | None, tuple[str, ...]]:
    level = SEVERITIES.index(rule.severity)
    adjustments = []
    if weak:
        level -= 1
        adjustments.append("weaker exposure: rinse-off product or a trace amount")
    if sensitive and rule.raise_if_sensitive:
        level += 1
        adjustments.append("sensitive skin")
    level = min(level, len(SEVERITIES) - 1)
    return (SEVERITIES[level] if level >= 0 else None), tuple(adjustments)


def check_conflicts(routine_products: list[Product], new_product: Product, profile: dict | None = None,
                    rules: Rules | None = None, conflict_rules: ConflictRules | None = None) -> list[Flag]:
    """Flags for adding new_product to the routine that holds routine_products."""
    rules = rules or load_rules()
    conflict_rules = conflict_rules or load_conflict_rules()
    reviewed = [r for r in conflict_rules.rules if r.status == "reviewed"]
    sensitive = (profile or {}).get("skin_type") == "sensitive"
    new_actives = actives(new_product, rules, conflict_rules)

    flags = []
    for other in routine_products:
        if other.id == new_product.id:
            continue
        other_actives = actives(other, rules, conflict_rules)
        for rule in reviewed:
            for mine, theirs in ((rule.a, rule.b), (rule.b, rule.a)):
                if mine in new_actives and theirs in other_actives:
                    weak = "weak" in (new_actives[mine], other_actives[theirs])
                    severity, adjustments = _adjust(rule, weak, sensitive)
                    if severity:
                        flags.append(Flag(rule.id, severity, rule.severity, adjustments, other.id,
                                          rule.reason, rule.suggestion, rule.source))
                    break
    return flags
