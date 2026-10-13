"""Load Sephora skincare products into products and product_ingredients.

Safe to rerun: each product is upserted and its ingredient rows are replaced.
Usage: python -m scripts.load_sephora [path]   (default: data/product_info.csv)
"""

import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import psycopg

from app.config import database_url
from app.ingredients import is_kit, parse_ingredients

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "product_info.csv"
REQUIRED = ["product_id", "product_name", "brand_name", "ingredients", "primary_category",
            "secondary_category", "tertiary_category"]
# Not single topical products: multi-product boxes, devices, supplements.
EXCLUDED_SECONDARY = {"Value & Gift Sets", "High Tech Tools", "Wellness"}


def _text(value) -> str | None:
    return None if pd.isna(value) else str(value)


def load(path: Path) -> None:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SystemExit(f"{path} is missing columns {missing}; the loader must change before it runs")

    counts = Counter(rows_in_file=len(df))
    df = df[df.primary_category == "Skincare"]
    counts["skincare"] = len(df)
    df = df[~df.secondary_category.isin(EXCLUDED_SECONDARY)]
    counts["after_excluding_sets_tools_wellness"] = len(df)

    with psycopg.connect(database_url()) as conn, conn.cursor() as cur:
        for row in df.itertuples(index=False):
            raw = _text(row.ingredients)
            if is_kit(raw):
                counts["skipped_kits"] += 1
                continue

            ingredients = parse_ingredients(raw)
            category = _text(row.tertiary_category) or _text(row.secondary_category)
            cur.execute(
                """
                INSERT INTO products (source, source_id, name, brand, category, ingredients_raw, has_ingredients)
                VALUES ('sephora', %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, source_id) DO UPDATE SET
                    name = EXCLUDED.name, brand = EXCLUDED.brand, category = EXCLUDED.category,
                    ingredients_raw = EXCLUDED.ingredients_raw, has_ingredients = EXCLUDED.has_ingredients
                RETURNING id
                """,
                (row.product_id, row.product_name, _text(row.brand_name), category, raw, bool(ingredients)),
            )
            product_id = cur.fetchone()[0]
            cur.execute("DELETE FROM product_ingredients WHERE product_id = %s", (product_id,))
            cur.executemany(
                "INSERT INTO product_ingredients (product_id, position, name) VALUES (%s, %s, %s)",
                [(product_id, position, name) for position, name in enumerate(ingredients, start=1)],
            )
            counts["loaded"] += 1
            counts["loaded_with_ingredients" if ingredients else "loaded_without_ingredients"] += 1
            counts["ingredient_rows"] += len(ingredients)
        conn.commit()

    for key, value in counts.items():
        print(f"{key:<45} {value}")


if __name__ == "__main__":
    load(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH)
