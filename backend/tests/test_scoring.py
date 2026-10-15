import json

import pytest

from app.scoring import COLORS, RULES_DIR, grade_for, load_rules, lookup_keys, parse_rules, score

# Small fixed rules, so these tests do not change when the files in rules/ are edited.
SCORING = {
    "baseline": 70,
    "colors": {
        "red": {"points": -15, "cap": -45},
        "orange": {"points": -8, "cap": -24},
        "green": {"points": 4, "cap": 30},
    },
    "min_rated_share": 0.5,
    "rinse_off_categories": ["Face Wash & Cleansers"],
    "grades": [
        {"min": 85, "grade": "Excellent"},
        {"min": 70, "grade": "Good"},
        {"min": 50, "grade": "Fair"},
        {"min": 30, "grade": "Poor"},
        {"min": 0, "grade": "Avoid"},
    ],
}
REDS = ["red1", "red2", "red3", "red4"]
ORANGES = ["orange1", "orange2", "orange3", "orange4"]
GREENS = [f"green{i}" for i in range(1, 10)]
INGREDIENTS = (
    [{"name": n, "color": "red", "reason": "r"} for n in REDS]
    + [{"name": n, "color": "orange", "reason": "o"} for n in ORANGES]
    + [{"name": n, "color": "green", "reason": "g"} for n in GREENS]
    + [
        {"name": "water", "color": "blue", "aliases": ["aqua", "eau"], "reason": "solvent"},
        {"name": "glycerin", "color": "blue", "reason": "humectant"},
        {"name": "fragrance", "color": "orange", "aliases": ["parfum"], "group": "fragrance", "reason": "allergen"},
        {"name": "limonene", "color": "orange", "group": "fragrance", "reason": "allergen"},
        {"name": "ceramide np", "color": "green", "group": "ceramides", "reason": "lipid"},
        {"name": "ceramide ap", "color": "green", "group": "ceramides", "reason": "lipid"},
        {"name": "coconut oil", "color": "orange", "rinse_off_color": "blue", "reason": "pores",
         "source": "https://example.com/coconut"},
        {"name": "alcohol", "color": "orange", "reason": "drying"},
        {"name": "alcohol denat", "color": "orange", "reason": "drying"},
    ]
)
RULES = parse_rules(SCORING, INGREDIENTS)


def run(ingredients, category=None):
    return score(ingredients, category, RULES)


def colors(ingredients, category=None):
    return [i.color for i in run(ingredients, category).ingredients]


@pytest.mark.parametrize("ingredients", [None, []])
def test_no_ingredients_is_not_enough_data(ingredients):
    assert run(ingredients) is None


def test_baseline_when_everything_is_blue():
    assert run(["water", "glycerin"]).score == 70


def test_short_list_is_scored_normally():
    assert run(["water"]).score == 70


def test_red():
    assert run(["water", "red1"]).score == 55


def test_orange():
    assert run(["water", "orange1"]).score == 62


def test_green():
    assert run(["water", "green1"]).score == 74


def test_blue_and_grey_add_nothing():
    assert run(["water", "glycerin", "mystery extract"]).score == 70


def test_red_cap():
    assert run(REDS[:3]).score == 25
    assert run(REDS[:4]).score == 25


def test_orange_cap():
    assert run(ORANGES[:3]).score == 46
    assert run(ORANGES[:4]).score == 46


def test_green_cap():
    assert run(GREENS[:7]).score == 98
    assert run(GREENS[:8]).score == 100
    assert run(GREENS[:9]).score == 100


def test_colors_combine():
    assert run(["water", "red1", "orange1", "green1"]).score == 70 - 15 - 8 + 4


def test_group_counts_once():
    assert run(["ceramide np", "ceramide ap", "water"]).score == 74
    assert run(["fragrance", "limonene", "water"]).score == 62


def test_each_ingredient_gets_a_color_in_label_order():
    assert colors(["water", "red1", "mystery extract", "green1", "parfum"]) == [
        "blue", "red", "grey", "green", "orange"]


def test_rated_ingredient_carries_reason_and_source():
    coconut = run(["coconut oil"]).ingredients[0]
    assert (coconut.reason, coconut.source) == ("pores", "https://example.com/coconut")
    assert run(["mystery extract", "water"]).ingredients[0].reason is None


def test_rinse_off_color_applies_only_to_rinse_off_categories():
    assert colors(["coconut oil"]) == ["orange"]
    assert colors(["coconut oil"], "Moisturizers") == ["orange"]
    assert colors(["coconut oil"], "Face Wash & Cleansers") == ["blue"]
    assert colors(["parfum"], "Face Wash & Cleansers") == ["orange"]


def test_no_score_when_mostly_grey():
    result = run(["water", "mystery one", "mystery two"])
    assert (result.score, result.grade) == (None, None)
    assert result.rated_share == pytest.approx(1 / 3)
    assert run(["water", "mystery one"]).score == 70  # exactly half rated is enough


@pytest.mark.parametrize(
    "name, color",
    [
        ("aqua/water/eau", "blue"),
        ("water (aqua, eau)", "blue"),
        ("parfum (fragrance)", "orange"),
        ("fragrance/parfum", "orange"),
        ("alcohol denat. (sd alcohol 40-b)", "orange"),
        ("cetearyl alcohol", "grey"),
        ("ceramide np", "green"),
        ("ceramide npx", "grey"),
    ],
)
def test_spelling_variants(name, color):
    assert colors([name, "water"])[0] == color


def test_lookup_keys():
    assert lookup_keys("Aqua/Water/Eau.") == ["aqua/water/eau", "aqua", "water", "eau"]
    assert lookup_keys("Niacinamide (Vitamin B3/skin-restoring)") == [
        "niacinamide (vitamin b3/skin-restoring)", "niacinamide"]


@pytest.mark.parametrize(
    "value, grade",
    [(100, "Excellent"), (85, "Excellent"), (84, "Good"), (70, "Good"), (69, "Fair"),
     (50, "Fair"), (49, "Poor"), (30, "Poor"), (29, "Avoid"), (0, "Avoid")],
)
def test_grade_boundaries(value, grade):
    assert grade_for(value, RULES) == grade


def test_rules_files_are_valid():
    scoring = json.loads((RULES_DIR / "scoring.json").read_text())
    ingredients = json.loads((RULES_DIR / "ingredients.json").read_text())
    seen = set()
    for entry in ingredients:
        assert entry["color"] in COLORS and entry["color"] != "grey", entry
        assert entry.get("rinse_off_color", "blue") in COLORS, entry
        assert entry["reason"], entry
        assert entry.get("family", "x").isidentifier(), entry
        if entry["color"] in ("red", "orange"):
            assert entry.get("source", "").startswith("https://"), f"{entry['name']} needs a source"
        for name in [entry["name"], *entry.get("aliases", [])]:
            assert name == name.lower().strip(), name
            assert name not in seen, f"{name} is rated twice"
            seen.add(name)
    assert set(scoring["colors"]) <= set(COLORS)
    assert min(g["min"] for g in scoring["grades"]) == 0
    load_rules.cache_clear()
    assert load_rules().ratings["water"].color == "blue"
