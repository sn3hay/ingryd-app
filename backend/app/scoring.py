"""Rules-based ingredient ratings and product score. No LLM: the same product always gets the same result.

Each ingredient gets a color from rules/ingredients.json:
  green   helps the skin
  blue    fine, does its job, no known concern
  orange  could be a concern (irritant, allergen, pore-clogging, restricted)
  red     harmful or restricted
  grey    not rated yet

A rating can give a different color for rinse-off products (cleansers, wash-off masks), where
exposure is brief: pore-clogging oils are blue there, for example.

The product score follows from the colors, using the points and caps in rules/scoring.json.
Ratings that share a group count once: five ceramides are one green, fragrance plus its
allergens are one orange. No score is given when fewer than min_rated_share of the
ingredients are rated, since it would mostly be a guess.
"""

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parents[2] / "rules"
COLORS = ("green", "blue", "orange", "red", "grey")


@dataclass(frozen=True)
class Rating:
    color: str
    rinse_off_color: str | None
    group: str
    reason: str
    source: str | None


@dataclass(frozen=True)
class RatedIngredient:
    name: str
    color: str
    reason: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class ScoreResult:
    score: int | None  # None when too few ingredients are rated
    grade: str | None
    rated_share: float
    ingredients: tuple[RatedIngredient, ...]  # in label order


@dataclass(frozen=True)
class Rules:
    baseline: int
    points: dict[str, tuple[int, int]]  # color -> (points, cap)
    min_rated_share: float
    rinse_off_categories: frozenset[str]
    grades: tuple[tuple[int, str], ...]  # (min score, grade), highest first
    ratings: dict[str, Rating]  # every name and alias -> rating


def parse_rules(scoring: dict, ingredients: list[dict]) -> Rules:
    ratings = {}
    for entry in ingredients:
        rating = Rating(
            color=entry["color"],
            rinse_off_color=entry.get("rinse_off_color"),
            group=entry.get("group", entry["name"]),
            reason=entry["reason"],
            source=entry.get("source"),
        )
        for name in [entry["name"], *entry.get("aliases", [])]:
            ratings[name] = rating
    return Rules(
        baseline=scoring["baseline"],
        points={color: (c["points"], c["cap"]) for color, c in scoring["colors"].items()},
        min_rated_share=scoring["min_rated_share"],
        rinse_off_categories=frozenset(scoring["rinse_off_categories"]),
        grades=tuple(sorted(((g["min"], g["grade"]) for g in scoring["grades"]), reverse=True)),
        ratings=ratings,
    )


@lru_cache(maxsize=1)
def load_rules() -> Rules:
    return parse_rules(
        json.loads((RULES_DIR / "scoring.json").read_text()),
        json.loads((RULES_DIR / "ingredients.json").read_text()),
    )


def lookup_keys(name: str) -> list[str]:
    """Spellings to try, most specific first: "aqua/water/eau" -> [..., "aqua", "water", "eau"]."""
    full = name.lower().strip(" .*")
    no_notes = re.sub(r"\s*\([^)]*\)", "", full).strip(" .")  # "parfum (fragrance)" -> "parfum"
    keys = [full, no_notes, *(part.strip(" .") for part in no_notes.split("/"))]
    return list(dict.fromkeys(k for k in keys if k))


def rate(name: str, rinse_off: bool, rules: Rules) -> tuple[RatedIngredient, Rating | None]:
    rating = next((rules.ratings[k] for k in lookup_keys(name) if k in rules.ratings), None)
    if rating is None:
        return RatedIngredient(name, "grey"), None
    color = rating.rinse_off_color if rinse_off and rating.rinse_off_color else rating.color
    return RatedIngredient(name, color, rating.reason, rating.source), rating


def grade_for(score: int, rules: Rules) -> str:
    return next(grade for minimum, grade in rules.grades if score >= minimum)


def score(ingredients: list[str] | None, category: str | None = None,
          rules: Rules | None = None) -> ScoreResult | None:
    """Rate each ingredient and score the product; None ("Not enough data") when there is no list."""
    if not ingredients:
        return None
    rules = rules or load_rules()
    rinse_off = category in rules.rinse_off_categories

    rated = []
    groups: dict[str, set[str]] = {color: set() for color in rules.points}
    for name in ingredients:
        ingredient, rating = rate(name, rinse_off, rules)
        rated.append(ingredient)
        if rating and ingredient.color in groups:
            groups[ingredient.color].add(rating.group)

    rated_share = sum(i.color != "grey" for i in rated) / len(rated)
    if rated_share < rules.min_rated_share:
        return ScoreResult(None, None, rated_share, tuple(rated))

    total = rules.baseline
    for color, (points, cap) in rules.points.items():
        effect = points * len(groups[color])
        total += max(effect, cap) if points < 0 else min(effect, cap)
    total = max(0, min(100, total))
    return ScoreResult(total, grade_for(total, rules), rated_share, tuple(rated))
