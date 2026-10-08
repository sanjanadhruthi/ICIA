"""
run_queries.py - runs every query in sql/analysis_queries.sql and prints the results.

Run from the project root:
    python -m src.database.run_queries
"""
import re

import pandas as pd

from src.database.connection import get_engine
from src.utils.config import ROOT

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 10)


def run():
    text = (ROOT / "sql" / "analysis_queries.sql").read_text(encoding="utf-8")
    engine = get_engine()
    # each query starts with a "-- Qn." comment and ends with ";"
    for block in re.split(r"\n(?=-- Q\d+\.)", text)[1:]:
        title = block.splitlines()[0].lstrip("- ").strip()
        sql = block.strip().rstrip(";")
        df = pd.read_sql(sql, engine)
        print(f"\n{'=' * 80}\n{title}\n{'-' * 80}")
        print(df.head(15).to_string(index=False))
        if len(df) > 15:
            print(f"... {len(df) - 15} more rows")


if __name__ == "__main__":
    run()