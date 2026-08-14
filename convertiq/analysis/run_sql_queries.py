"""Executes each SQL file against convertiq.db and saves results as CSV
for use in the analysis/visualization step and for the README write-up."""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "/home/claude/convertiq/data/convertiq.db"
SQL_DIR = Path("/home/claude/convertiq/sql")
OUT_DIR = Path("/home/claude/convertiq/outputs")
OUT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)

def strip_comment_lines(stmt):
    """Remove full-line '--' comments, keep the actual SQL."""
    kept = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
    return "\n".join(kept).strip()

def run_and_save(sql_file, out_prefix):
    """A .sql file may contain multiple ';'-separated statements — run each,
    save each result set that returns rows."""
    sql_text = Path(sql_file).read_text()
    raw_statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    idx = 0
    for raw in raw_statements:
        stmt = strip_comment_lines(raw)
        if not stmt or not any(c.isalpha() for c in stmt):
            continue
        try:
            df = pd.read_sql_query(stmt, conn)
        except Exception as e:
            print(f"  (skipped a statement in {sql_file.name}: {e})")
            continue
        if df.empty and len(df.columns) == 0:
            continue
        idx += 1
        out_path = OUT_DIR / f"{out_prefix}_{idx}.csv"
        df.to_csv(out_path, index=False)
        print(f"Saved {out_path.name}  ({len(df)} rows)")

run_and_save(SQL_DIR / "funnel_conversion.sql", "funnel")
run_and_save(SQL_DIR / "cohort_retention.sql", "retention")
run_and_save(SQL_DIR / "rfm_segmentation.sql", "rfm")

conn.close()
print("Done.")
