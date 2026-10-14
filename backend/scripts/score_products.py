"""Score every product and store score and grade. Rerun after reloading products or editing rules/.

Usage: python -m scripts.score_products
"""

from collections import Counter

import psycopg

from app.config import database_url
from app.scoring import score


def score_all() -> None:
    grades = Counter()
    with psycopg.connect(database_url()) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT p.id, p.category, array_agg(pi.name ORDER BY pi.position) FILTER (WHERE pi.name IS NOT NULL)"
            " FROM products p LEFT JOIN product_ingredients pi ON pi.product_id = p.id"
            " WHERE p.has_ingredients GROUP BY p.id, p.category"
        )
        updates = []
        for product_id, category, ingredients in cur.fetchall():
            result = score(ingredients, category)
            updates.append((result.score, result.grade, product_id))
            grades[result.grade or "Too few rated"] += 1

        cur.execute("UPDATE products SET score = NULL, grade = NULL WHERE NOT has_ingredients")
        grades["Not enough data"] += cur.rowcount
        cur.executemany("UPDATE products SET score = %s, grade = %s WHERE id = %s", updates)
        conn.commit()

    for grade in ["Excellent", "Good", "Fair", "Poor", "Avoid", "Too few rated", "Not enough data"]:
        print(f"{grade:<16} {grades[grade]}")


if __name__ == "__main__":
    score_all()
