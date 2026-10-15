import dataclasses
import json

import pytest

from app.conflicts import (SEVERITIES, STATUSES, ConflictRules, Product, actives, check_conflicts,
                           load_conflict_rules, normalize, parse_conflict_rules, unchecked)
from app.scoring import RULES_DIR, load_rules, parse_rules

# Small fixed rules, so these tests do not change when the files in rules/ are edited.
SCORING = {
    "baseline": 70,
    "colors": {"red": {"points": -15, "cap": -45}},
    "min_rated_share": 0.5,
    "rinse_off_categories": ["Face Wash & Cleansers"],
    "grades": [{"min": 0, "grade": "Any"}],
}
INGREDIENTS = [
    {"name": "water", "color": "blue", "aliases": ["aqua"], "reason": "solvent"},
    {"name": "glycerin", "color": "blue", "reason": "humectant"},
    {"name": "retinol", "color": "green", "family": "retinoid", "reason": "r"},
    {"name": "ascorbic acid", "color": "green", "aliases": ["l-ascorbic acid"], "family": "vitamin_c_acid", "reason": "c"},
    {"name": "ascorbyl glucoside", "color": "green", "reason": "gentle vitamin c, no family"},
    {"name": "glycolic acid", "color": "green", "family": "aha", "reason": "a"},
    {"name": "niacinamide", "color": "green", "reason": "n"},
]
RULES = parse_rules(SCORING, INGREDIENTS)


def conflict_rule(id, a, b, severity, raise_if_sensitive=False, status="reviewed"):
    return {"id": id, "a": a, "b": b, "severity": severity, "reason": "why", "suggestion": "fix",
            "raise_if_sensitive": raise_if_sensitive, "source": "https://example.com", "status": status}


CONFLICTS = parse_conflict_rules({
    "trace_after_share": 0.67,
    "trace_min_ingredients": 6,
    "rules": [
        conflict_rule("retinoid-x-vitamin_c_acid", "retinoid", "vitamin_c_acid", "separate", raise_if_sensitive=True),
        conflict_rule("aha-x-aha", "aha", "aha", "caution"),
        conflict_rule("retinoid-x-aha", "retinoid", "aha", "avoid", status="draft"),
    ],
})


def product(id, *ingredients, category=None):
    return Product(id, list(ingredients), category)


def check(routine, new, profile=None):
    return check_conflicts(routine, new, profile, RULES, CONFLICTS)


def flags(routine, new, profile=None):
    return [(f.rule_id, f.severity) for f in check(routine, new, profile)]


RETINOL = product("ret", "water", "retinol", "glycerin")
VITAMIN_C = product("vitc", "water", "l-ascorbic acid", "glycerin")
AHA = product("aha", "glycolic acid", "water")


@pytest.mark.parametrize(
    "name, family",
    [("retinol", "retinoid"), ("L-Ascorbic Acid (Vitamin C)", "vitamin_c_acid"),
     ("ascorbyl glucoside", None), ("water", None), ("mystery extract", None)],
)
def test_normalize(name, family):
    assert normalize(name, RULES) == family


def test_actives_full_strength():
    assert actives(RETINOL, RULES, CONFLICTS) == {"retinoid": "full"}
    assert actives(product("x", "water", "glycerin"), RULES, CONFLICTS) == {}


def test_actives_rinse_off_is_weak():
    cleanser = product("c", "water", "glycolic acid", category="Face Wash & Cleansers")
    assert actives(cleanser, RULES, CONFLICTS) == {"aha": "weak"}


def test_actives_last_third_of_a_long_list_is_weak():
    filler = ["water", "glycerin", "niacinamide", "mystery one", "mystery two"]
    assert actives(product("p", *filler, "glycolic acid"), RULES, CONFLICTS) == {"aha": "weak"}
    assert actives(product("p", *filler[:3], "glycolic acid", *filler[3:]), RULES, CONFLICTS) == {"aha": "full"}
    # Short lists have no trace amounts.
    assert actives(product("p", "water", "glycolic acid"), RULES, CONFLICTS) == {"aha": "full"}


def test_actives_full_anywhere_wins():
    filler = ["water", "glycerin", "niacinamide", "mystery one"]
    assert actives(product("p", "glycolic acid", *filler, "glycolic acid"), RULES, CONFLICTS) == {"aha": "full"}


def test_unchecked_lists_unrated_ingredients():
    assert unchecked(product("p", "water", "mystery extract", "retinol"), RULES) == ["mystery extract"]


def test_rule_flags_in_both_directions():
    assert flags([VITAMIN_C], RETINOL) == [("retinoid-x-vitamin_c_acid", "separate")]
    assert flags([RETINOL], VITAMIN_C) == [("retinoid-x-vitamin_c_acid", "separate")]


def test_flag_carries_rule_details():
    flag = check([VITAMIN_C], RETINOL)[0]
    assert (flag.product_id, flag.suggestion, flag.source, flag.adjustments) == (
        "vitc", "fix", "https://example.com", ())


def test_no_flag_without_a_rule():
    assert flags([product("n", "niacinamide")], RETINOL) == []
    assert flags([product("g", "ascorbyl glucoside")], RETINOL) == []


def test_same_family_rule():
    assert flags([AHA], product("aha2", "glycolic acid")) == [("aha-x-aha", "caution")]


def test_draft_rules_are_not_used():
    assert flags([AHA], RETINOL) == []


def test_product_is_not_checked_against_itself():
    assert flags([AHA], AHA) == []


def test_each_routine_product_is_checked():
    result = check([VITAMIN_C, product("n", "niacinamide"), AHA], product("both", "retinol", "glycolic acid"))
    assert [(f.rule_id, f.product_id) for f in result] == [
        ("retinoid-x-vitamin_c_acid", "vitc"), ("aha-x-aha", "aha")]


def test_rinse_off_drops_one_level():
    cleanser = product("c", "water", "l-ascorbic acid", category="Face Wash & Cleansers")
    assert flags([cleanser], RETINOL) == [("retinoid-x-vitamin_c_acid", "caution")]


def test_caution_dropped_below_caution_is_no_flag():
    cleanser = product("c", "water", "glycolic acid", category="Face Wash & Cleansers")
    assert flags([cleanser], AHA) == []


def test_trace_amount_drops_one_level():
    trace = product("t", "water", "glycerin", "niacinamide", "mystery one", "mystery two", "ascorbic acid")
    assert flags([trace], RETINOL) == [("retinoid-x-vitamin_c_acid", "caution")]


def test_sensitive_skin_raises_one_level():
    assert flags([VITAMIN_C], RETINOL, {"skin_type": "sensitive"}) == [("retinoid-x-vitamin_c_acid", "avoid")]
    assert flags([AHA], product("aha2", "glycolic acid"), {"skin_type": "sensitive"}) == [("aha-x-aha", "caution")]


def test_weak_and_sensitive_cancel_out():
    cleanser = product("c", "water", "l-ascorbic acid", category="Face Wash & Cleansers")
    flag = check([cleanser], RETINOL, {"skin_type": "sensitive"})[0]
    assert (flag.severity, len(flag.adjustments)) == ("separate", 2)


# The real rules: every rule fires in both directions once reviewed.
def family_members():
    members = {}
    for name, rating in load_rules().ratings.items():
        if rating.family:
            members.setdefault(rating.family, name)
    return members


@pytest.mark.parametrize("rule", load_conflict_rules().rules, ids=lambda r: r.id)
def test_every_real_rule_in_both_directions(rule):
    members = family_members()
    reviewed = ConflictRules(0.67, 6, (dataclasses.replace(rule, status="reviewed"),))
    first, second = product("first", members[rule.a]), product("second", members[rule.b])
    for routine, new in ((first, second), (second, first)):
        result = check_conflicts([routine], new, None, load_rules(), reviewed)
        assert [(f.rule_id, f.severity) for f in result] == [(rule.id, rule.severity)]


def test_conflict_rules_file_is_valid():
    data = json.loads((RULES_DIR / "conflicts.json").read_text())
    families = {r.family for r in load_rules().ratings.values() if r.family}
    ids = [r["id"] for r in data["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    for rule in data["rules"]:
        assert {rule["a"], rule["b"]} <= families, f"{rule['id']} uses a family no ingredient has"
        assert rule["severity"] in SEVERITIES, rule["id"]
        assert rule["status"] in STATUSES, rule["id"]
        assert rule["scope"] == "same_routine", rule["id"]
        assert rule["source"].startswith("https://"), f"{rule['id']} needs a source"
        assert rule["reason"] and rule["suggestion"], rule["id"]
    load_conflict_rules.cache_clear()
    assert load_conflict_rules().rules
