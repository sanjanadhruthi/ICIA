"""
load_data.py - loads data/processed/*.csv into the database, then builds the views.

Run from the project root (after create_tables):
    python -m src.database.load_data
"""
from contextlib import closing
import sqlite3

import pandas as pd

from src.database.connection import get_engine, run_sql_file
from src.utils.config import DB_PATH, PROCESSED_DIR, ROOT
from src.utils.logger import get_logger

log = get_logger("load_data")

CATEGORIES = {  # code -> (label, population basis)
    "total_cognizable": ("Total cognizable crimes (IPC/BNS + SLL)", "general"),
    "ipc_bns_crime": ("IPC/BNS crimes", "general"),
    "sll_crime": ("Special & Local Laws (SLL) crimes", "general"),
    "violent_crime": ("Violent crimes", "general"),
    "crime_against_women": ("Crimes against women", "female"),
    "crime_against_children": ("Crimes against children", "children"),
    "cyber_crime": ("Cyber crimes", "general"),
}

SUPPORTING = {  # table name -> csv file
    "population": "population.csv",
    "ncrb_indicators": "state_indicators.csv",
    "police_disposal": "police_disposal.csv",
    "metro_city_crimes": "metro_city_crimes.csv",
    "crime_heads": "crime_heads.csv",
    "property_stolen": "property_stolen.csv",
}


def run():
    engine = get_engine()
    crime = pd.read_csv(PROCESSED_DIR / "crime_state_year.csv")

    # dimensions
    states = (crime[["state", "zone"]].drop_duplicates().sort_values("state")
              .reset_index(drop=True))
    states.insert(0, "state_id", states.index + 1)
    states = states.rename(columns={"state": "state_name"})

    unknown = set(crime.category) - set(CATEGORIES)
    if unknown:
        raise ValueError(f"categories missing a label in load_data.py: {unknown}")
    cats = pd.DataFrame([{"category_id": i + 1, "category_code": code,
                          "category_label": label, "population_basis": basis}
                         for i, (code, (label, basis)) in enumerate(CATEGORIES.items())])

    # fact table
    fact = (crime.merge(states, left_on="state", right_on="state_name")
                 .merge(cats, left_on="category", right_on="category_code"))
    fact = fact[["state_id", "category_id", "year", "cases", "population_lakhs",
                 "crime_rate", "yoy_change_pct", "is_derived"]]
    fact["is_derived"] = fact["is_derived"].astype(int)
    if len(fact) != len(crime):
        log.warning("fact rows %d != csv rows %d (some rows did not match a dimension)",
                    len(fact), len(crime))

    # load (append keeps the types and keys defined in schema.sql)
    states.to_sql("dim_state", engine, if_exists="append", index=False)
    cats.to_sql("dim_category", engine, if_exists="append", index=False)
    fact.to_sql("fact_crime", engine, if_exists="append", index=False)
    for table, fname in SUPPORTING.items():
        path = PROCESSED_DIR / fname
        if not path.exists():
            log.warning("skipped %s: %s not found", table, fname)
            continue
        df = pd.read_csv(path)
        for col in ("is_subtotal", "is_interpolated"):
            if col in df:
                df[col] = df[col].astype(int)
        df.to_sql(table, engine, if_exists="append", index=False)

    run_sql_file(ROOT / "sql" / "views.sql")

    # ---- built-in checks
    with closing(sqlite3.connect(DB_PATH)) as con:
        bad_fk = con.execute("PRAGMA foreign_key_check").fetchall()
        if bad_fk:
            log.warning("foreign key problems: %s", bad_fk[:5])
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name")]
        print("\nRows per table / view:")
        for t in tables:
            n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            print(f"  {t:<20} {n:>6}")

    trend = pd.read_sql("SELECT year, cases, crime_rate FROM v_national_trend "
                        "WHERE category = 'total_cognizable' ORDER BY year", engine)
    print("\nSanity check - All-India total cognizable crime:")
    print(trend.to_string(index=False))
    log.info("database ready: %s", DB_PATH)


if __name__ == "__main__":
    run()