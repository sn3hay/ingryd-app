import pytest

from app.ingredients import is_kit, parse_ingredients


def names(raw):
    return parse_ingredients(raw)


@pytest.mark.parametrize("raw", [None, "", "   ", "[]", "['']"])
def test_missing_or_empty_gives_empty_list(raw):
    assert parse_ingredients(raw) == []


def test_sephora_list_literal_keeps_order_and_lowercases():
    assert names("['Water, Glycerin, Niacinamide']") == ["water", "glycerin", "niacinamide"]


def test_plain_text_from_open_beauty_facts():
    assert names("Ingredients: Aqua, Glycerin.") == ["aqua", "glycerin"]


def test_pieces_cut_mid_name_are_joined():
    assert names("['Water, Pentylene', 'Glycol, Glycerin']") == ["water", "pentylene glycol", "glycerin"]


def test_commas_inside_parentheses_and_numbers_do_not_split():
    assert names("['Water (Aqua, Eau), 1,2-Hexanediol']") == ["water (aqua, eau)", "1,2-hexanediol"]


def test_asterisks_trailing_period_and_footnote_removed():
    raw = "['Glycerin*, Rosa Canina Seed Oil*, Fragrance/Parfum*. *100% Naturally Derived.']"
    assert names(raw) == ["glycerin", "rosa canina seed oil", "fragrance/parfum"]


def test_backslash_synonyms_keep_first():
    assert names(r"['Water\\Aqua\\Eau, Glycerin']") == ["water", "glycerin"]


def test_may_contain_section_dropped():
    raw = "['Water, Dimethicone', 'May Contain (+/-):', 'Iron Oxides (Ci 77491)']"
    assert names(raw) == ["water", "dimethicone"]
    assert names("['Mica, Silica [+/- Ci 77491, Ci 77891]']") == ["mica", "silica"]


def test_single_label_and_prose_dropped():
    assert names("['Sources of vitamin C:', 'Water, Glycerin']") == ["water", "glycerin"]
    raw = "['Vinolevure: Strengthens, moisturizes, and tones.', 'Aqua, Butylene Glycol']"
    assert names(raw) == ["aqua", "butylene glycol"]


@pytest.mark.parametrize(
    "raw",
    [
        "['Salicylic Acid 2.0%, Water']",
        "['2% Salicylic Acid, Water']",
        "['Salicylic Acid(0.2%), Water']",
        "['Salicylic Acid 15 %, Water']",
        "['Salicylic Acid 3% Sunscreen, Water']",
        "['Salicylic Acid (less than 1%), Water']",
    ],
)
def test_percentages_removed_from_names(raw):
    assert names(raw) == ["salicylic acid", "water"]


def test_kit_detection():
    assert is_kit("['Step 1:', 'Water, Glycerin', 'Step 2:', 'Water, Niacinamide']")
    assert not is_kit("['Sources of vitamin C:', 'Water, Glycerin']")
    assert not is_kit("['Water, Dimethicone', 'May Contain (+/-):', 'Iron Oxides']")
    assert not is_kit(None)


def test_unbalanced_parentheses_do_not_swallow_the_list():
    assert names("['Stellaria Media (Chickweed( Extract, Malt Extract, Panthenol']") == [
        "stellaria media (chickweed( extract", "malt extract", "panthenol"]


def test_bracketed_blend_is_split():
    assert names("['Botanical Blend [Aqua, Aloe Extract], Glycerin']") == [
        "botanical blend", "aqua", "aloe extract", "glycerin"]


def test_and_separator():
    assert names("['Water (and) Argan Oil (and) Xanthan Gum']") == ["water", "argan oil", "xanthan gum"]


def test_periods_inside_names_kept():
    assert names("['Sigesbeckia Orientalis (St. Paul Wort) Extract, Alcohol Denat. (SD Alcohol 40-B)']") == [
        "sigesbeckia orientalis (st. paul wort) extract", "alcohol denat. (sd alcohol 40-b)"]


def test_note_inside_list_dropped():
    raw = "['Water, Phenoxyethanol. -Five Percent Benzoyl Peroxide: helps the look of blemishes.']"
    assert names(raw) == ["water", "phenoxyethanol"]


def test_batch_code_dropped():
    assert names("['Water, Phenoxyethanol, (F.I.L. B260371/2).']") == ["water", "phenoxyethanol"]


def test_list_without_separators_is_unparseable():
    assert parse_ingredients("['" + "Propylene Glycol Dimethicone Glycerin " * 10 + "']") == []
