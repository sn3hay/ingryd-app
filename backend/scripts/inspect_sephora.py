"""Describe the Sephora products CSV before any loading code depends on its shape.

Usage: python -m scripts.inspect_sephora [path]   (default: data/product_info.csv)
"""

import sys
from pathlib import Path

import pandas as pd

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "product_info.csv"

# Columns the loader will rely on. If any is missing, the loader must change before it runs.
REQUIRED = ["product_id", "product_name", "brand_name", "ingredients", "primary_category"]


def main(path: Path) -> None:
    df = pd.read_csv(path)
    print(f"file: {path}")
    print(f"rows: {len(df)}   columns: {len(df.columns)}\n")

    missing = [c for c in REQUIRED if c not in df.columns]
    print("required columns:", "all present" if not missing else f"MISSING {missing}")

    print("\ncolumn, dtype, non-null count, example:")
    for col in df.columns:
        non_null = df[col].dropna()
        example = repr(non_null.iloc[0])[:70] if len(non_null) else "-"
        print(f"  {col:<22} {str(df[col].dtype):<8} {len(non_null):>6}  {example}")

    if "product_id" in df.columns:
        print(f"\nduplicate product_id values: {df['product_id'].duplicated().sum()}")

    for col in ["primary_category", "secondary_category"]:
        if col in df.columns:
            print(f"\n{col} counts:")
            print(df[col].value_counts(dropna=False).to_string())

    if "ingredients" in df.columns:
        ing = df["ingredients"]
        print(f"\ningredients missing: {ing.isna().sum()}   empty: {(ing.fillna('').str.strip() == '').sum()}")
        print("\nfive ingredient values, raw:")
        for value in ing.dropna().sample(5, random_state=0):
            print("  ---")
            print("  " + value[:400])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH)
