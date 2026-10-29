"""
STEP 5 - LOAD EVERYTHING INTO A SQL DATABASE
============================================
Builds data/bank.db (SQLite) using sql/01_schema.sql and the CSV files, so
you can run sql/02_analysis_queries.sql straight away. No SQL Server needed.

SQLite is a tiny database that lives in one file. Open bank.db with
"DB Browser for SQLite" or the "SQLite Viewer" extension in VS Code.

(If you prefer SQL Server / MySQL / PostgreSQL: run sql/01_schema.sql there
 and import the three CSV files with your tool's import wizard.)

Run:
    python python/05_load_to_sqlite.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
SCHEMA_FILE = BASE_DIR / "sql" / "01_schema.sql"
DB_FILE = BASE_DIR / "data" / "bank.db"

needed = ["customers_clean.csv", "loans.csv", "churn_scores.csv"]
for f in needed:
    if not (PROCESSED / f).exists():
        raise SystemExit(f"Missing {f}. Run steps 01, 02 and 04 first.")

if DB_FILE.exists():
    DB_FILE.unlink()  # start fresh every time

conn = sqlite3.connect(DB_FILE)

# 1. create the tables from the schema file
conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

# 2. fill them from the CSV files (column names match the schema)
pd.read_csv(PROCESSED / "customers_clean.csv").to_sql("customers", conn, if_exists="append", index=False)
pd.read_csv(PROCESSED / "loans.csv").to_sql("loans", conn, if_exists="append", index=False)
pd.read_csv(PROCESSED / "churn_scores.csv").to_sql("churn_scores", conn, if_exists="append", index=False)

# 3. quick check
for table in ["customers", "loans", "churn_scores"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table:<14} {count:>7,} rows")

conn.commit()
conn.close()
print("\nDatabase created:", DB_FILE)
