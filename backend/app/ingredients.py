"""Turn raw ingredient text into an ordered list of ingredients.

Handles two input shapes: a Python list literal as stored in the Sephora CSV
("['Water, Glycerin, ...']"), and plain text as returned by Open Beauty Facts.
"""

import ast
import re
import warnings

# A stated percentage, removed from the name: "Salicylic Acid 2.0%", "Ceramide Np(0.2%)", "(less than 1%)".
PCT = re.compile(r"(?i)\(?\s*(?:less than|<)?\s*\d+(?:\.\d+)?\s*%\s*\)?")
MAY_CONTAIN = re.compile(r"(?i)\[?\s*\+\s*/\s*-\s*\]?|\bmay contain\b")
# A footnote after the list, such as "Fragrance*. *100% Naturally Derived."
FOOTNOTE = re.compile(r"\.\s*\*.*$", re.S)
# A sentence describing an ingredient, such as "Vinolevure: Strengthens, moisturizes, and tones."
PROSE = re.compile(r"^[^,:]{1,40}:\s+\S")
LEADING_LABEL = re.compile(r"(?i)^\s*(active )?ingredients?\s*:\s*")
# Longer than any real ingredient name; seen only when a list has no usable separators.
MAX_NAME_LENGTH = 200


def _sections(raw_text: str) -> list[str]:
    """The text pieces of a value; a Sephora list literal, or the whole plain text."""
    text = raw_text.strip()
    if text.startswith("["):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)  # "Water\Aqua" is not a real escape
                value = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return [text]
        if isinstance(value, list):
            return [str(v) for v in value]
    return [text]


def _is_label(section: str) -> bool:
    return section.strip().endswith(":")


def is_kit(raw_text: str | None) -> bool:
    """True when the value lists several products, each under its own label ("Step 1:", "The Essence:")."""
    if not raw_text:
        return False
    labels = [s for s in _sections(raw_text) if _is_label(s) and not MAY_CONTAIN.search(s)]
    return len(labels) >= 2


def _split_top_level(text: str) -> list[str]:
    """Split on commas, except inside parentheses and between digits ("1,2-hexanediol").

    Brackets hold a blend's own ingredients ("Botanical Blend [Aqua, Aloe ...]"), so they are split
    like the rest. Unbalanced parentheses ("Chickweed( Extract") are ignored rather than trusted.
    """
    text = re.sub(r"\s*\(and\)\s*", ", ", text, flags=re.I)
    text = text.replace("[", ", ").replace("]", ", ")
    balanced = text.count("(") == text.count(")")
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "(" and balanced:
            depth += 1
        elif ch == ")" and balanced:
            depth = max(depth - 1, 0)
        elif ch == "," and depth == 0:
            between_digits = 0 < i < len(text) - 1 and text[i - 1].isdigit() and text[i + 1].isdigit()
            if not between_digits:
                parts.append(text[start:i])
                start = i + 1
    parts.append(text[start:])
    return parts


def _clean(token: str) -> str | None:
    if ": " in token:
        token = token.split(". ")[0]  # "Phenoxyethanol. -Benzoyl Peroxide: helps ..." is a note
    if PCT.search(token):
        token = PCT.sub(" ", token)
        token = re.sub(r"(?i)\bsunscreen\b", "", token)  # "Avobenzone 3% Sunscreen"
    token = token.split("\\")[0]  # "Water\Aqua\Eau": keep the first synonym
    token = token.replace("*", "")
    token = re.sub(r"\s+", " ", token).strip(" .;")
    if re.fullmatch(r"\(.*\)", token):
        return None  # a batch code or remark such as "(F.I.L. B260371/2)"
    if not re.search(r"[a-zA-Z]", token):
        return None
    return token.lower()


def parse_ingredients(raw_text: str | None) -> list[str]:
    """Ordered ingredients; an empty list means missing, empty or unparseable."""
    if not raw_text or not raw_text.strip():
        return []

    kept = []
    for section in _sections(raw_text):
        section = LEADING_LABEL.sub("", section)
        if MAY_CONTAIN.search(section) and _is_label(section):
            break  # what follows is a list of shades, not this product's ingredients
        if _is_label(section) or PROSE.match(section):
            continue
        kept.append(section)

    # Pieces are sometimes cut mid-name ("Pentylene" / "Glycol, ..."), so join with a space.
    text = " ".join(kept)
    text = MAY_CONTAIN.split(text)[0]
    text = FOOTNOTE.sub("", text)

    ingredients = [i for i in map(_clean, _split_top_level(text)) if i is not None]
    if any(len(name) > MAX_NAME_LENGTH for name in ingredients):
        return []
    return ingredients

