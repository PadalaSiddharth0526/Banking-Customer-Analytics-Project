"""
database.py
============
Loads the cleaned & segmented dataset into a SQLite database and provides
a small helper to run the .sql scripts in sql/ against it.

Why SQLite (with PostgreSQL notes)?
SQLite requires zero setup (no server, no credentials) which makes this
portfolio project runnable by anyone who clones the repo. All SQL in
sql/*.sql is written in standard ANSI SQL and is PostgreSQL-compatible;
the two PostgreSQL-only syntax differences (SERIAL, generate_series) are
called out in sql/README references so the project can be pointed at a
real Postgres instance by changing only the connection string in this
file (see `get_connection`).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path("data/processed/banking_analytics.db")
REVENUE_CSV = Path("data/processed/bank_customers_revenue.csv")
TABLE_NAME = "customers"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection.

    To point this at PostgreSQL instead, replace with e.g.:
        import psycopg2
        return psycopg2.connect(host=..., dbname=..., user=..., password=...)
    and adjust the few PostgreSQL-only statements noted in sql/03_views.sql.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def load_dataframe_to_db(csv_path: Path = REVENUE_CSV, db_path: Path = DB_PATH,
                          table_name: str = TABLE_NAME) -> None:
    """Load the final analytics-ready CSV into the `customers` table."""
    logger.info("Loading %s into table '%s'", csv_path, table_name)
    df = pd.read_csv(csv_path)
    conn = get_connection(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
        logger.info("Loaded %d rows into '%s'", len(df), table_name)
    finally:
        conn.close()


def run_sql_file(sql_path: Path, db_path: Path = DB_PATH) -> list[pd.DataFrame]:
    """Execute every statement in a .sql file; return a DataFrame per SELECT statement."""
    logger.info("Running SQL file: %s", sql_path)
    sql_text = sql_path.read_text()
    statements = [s.strip() for s in sql_text.split(";") if s.strip() and not s.strip().startswith("--")]

    conn = get_connection(db_path)
    results = []
    try:
        for stmt in statements:
            cleaned = "\n".join(line for line in stmt.splitlines() if not line.strip().startswith("--"))
            if not cleaned.strip():
                continue
            if cleaned.strip().lower().startswith("select") or "with " == cleaned.strip().lower()[:5]:
                results.append(pd.read_sql_query(cleaned, conn))
            else:
                conn.execute(cleaned)
        conn.commit()
    finally:
        conn.close()
    return results


def run_query(query: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Run a single ad-hoc SQL query and return the result as a DataFrame (used by the dashboard)."""
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    # 01_schema.sql is a documentation/reference script for PostgreSQL
    # deployments (see its header comment) - the actual table is created
    # here directly from the cleaned CSV so Python and SQL never drift.
    # Only the business-query and view scripts are executed against SQLite.
    load_dataframe_to_db()
    for script in sorted(Path("sql").glob("*.sql")):
        if script.name == "01_schema.sql":
            logger.info("Skipping %s (PostgreSQL reference schema, not executed against SQLite)", script.name)
            continue
        run_sql_file(script)
    logger.info("Database build complete: %s", DB_PATH)
