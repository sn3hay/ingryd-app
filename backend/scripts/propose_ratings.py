"""Suggest ratings for the most common grey (unrated) ingredients, for a person to approve.

An LLM suggests a color, group, family and reason for each. Nothing is added to rules/: a person
reviews data/proposed_ratings.jsonl, adds a source link for every orange or red suggestion (the
LLM's own links are never used), and copies the approved entries into rules/ingredients.json.

Needs ANTHROPIC_API_KEY in .env.
Usage: python -m scripts.propose_ratings [how many, default 200]
"""

import json
import os
import sys
from collections import Counter
from pathlib import Path

import anthropic
import psycopg

from app.config import database_url
from app.scoring import find_rating, load_rules

MODEL = "claude-opus-5-5"
BATCH_SIZE = 50
OUTPUT = Path(__file__).resolve().parents[2] / "data" / "proposed_ratings.jsonl"

PROMPT = """You rate skincare ingredients for an app that shows each ingredient as a color.

Colors:
  green   helps the skin (a well-studied active or barrier ingredient)
  blue    fine, does its job (solvent, emulsifier, thickener, preservative), no known concern
  orange  could be a concern: irritant, allergen, pore-clogging, or restricted by a regulator
  red     harmful, or banned or restricted in the EU
  grey    you are not sure, or the text is not one ingredient (a parsing error, a note)

Existing groups (ingredients in a group count once in the score): {groups}
Existing families (used by conflict rules between products): {families}
Use an existing group or family only when the ingredient truly belongs to it; otherwise null.
Most ingredients have no family.

For each ingredient below, give one JSON object per line, nothing else:
{{"name": "<exactly as given>", "color": "...", "group": null, "family": null, "reason": "<one short sentence>"}}

Ingredients:
{names}
"""


def grey_ingredients(limit: int) -> list[tuple[str, int]]:
    rules = load_rules()
    with psycopg.connect(database_url()) as conn:
        rows = conn.execute(
            "SELECT lower(name), count(DISTINCT product_id) FROM product_ingredients GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
    return [(name, count) for name, count in rows if find_rating(name, rules) is None][:limit]


def propose(client: anthropic.Anthropic, names: list[str]) -> list[dict]:
    rules = load_rules()
    # An ungrouped rating has its own name as its group; list only the named groups.
    groups = sorted({r.group for r in rules.ratings.values() if r.group not in rules.ratings})
    families = sorted({r.family for r in rules.ratings.values() if r.family})
    message = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": PROMPT.format(
            groups=", ".join(groups), families=", ".join(families), names="\n".join(names))}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    proposals = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                proposals.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipped a line that is not JSON: {line[:80]}")
    return proposals


def main(limit: int) -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set; add it to .env")
    client = anthropic.Anthropic()
    grey = grey_ingredients(limit)
    counts = dict(grey)

    OUTPUT.parent.mkdir(exist_ok=True)
    colors = Counter()
    with OUTPUT.open("w") as out:
        for start in range(0, len(grey), BATCH_SIZE):
            names = [name for name, _ in grey[start:start + BATCH_SIZE]]
            for proposal in propose(client, names):
                if proposal.get("name") not in counts:
                    continue  # the model renamed it; skip rather than guess
                proposal["products"] = counts[proposal["name"]]
                proposal["source"] = ""  # filled in by the person who approves it
                out.write(json.dumps(proposal, ensure_ascii=False) + "\n")
                colors[proposal.get("color")] += 1
    print(f"Wrote {sum(colors.values())} of {len(grey)} suggestions to {OUTPUT}")
    for color, count in colors.most_common():
        print(f"  {color}: {count}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
