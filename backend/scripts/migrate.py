"""Apply backend/migrations/*.sql in order, each once, each in its own transaction."""

from pathlib import Path

import psycopg

from app.config import database_url

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def migrate() -> None:
    with psycopg.connect(database_url()) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        conn.commit()
        applied = {row[0] for row in conn.execute("SELECT name FROM schema_migrations")}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            with conn.transaction():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
            print(f"applied {path.name}")
    print("migrations up to date")


if __name__ == "__main__":
    migrate()
