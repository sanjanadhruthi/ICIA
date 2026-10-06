"""
transformation.py - builds the final analysis table from the cleaned CSVs.

Run from the project root (after cleaning):
    python -m src.preprocessing.transformation

What it does:
    1. Harmonises states so trends stay comparable across 2016-2024:
         Jammu & Kashmir + Ladakh            -> "Jammu & Kashmir (incl. Ladakh)"   (split in 2019)
         Dadra & Nagar Haveli + Daman & Diu  -> "DNH & Daman & Diu"                (merged in 2020)
    2. Derives total_cognizable (IPC + SLL) for 2016-2021, where NCRB has no ready table.
    3. Interpolates population for every year (NCRB only gives it for 2018, 2021, 2024)
       and computes a consistent crime rate (cases per lakh population) for all years.
    4. Adds year-on-year change and the zone of each state.

Output (data/processed/):
    crime_state_year.csv   state, zone, year, category, cases, population_lakhs,
                           crime_rate, yoy_change_pct, is_derived
    population.csv         state, year, population_group, population_lakhs, is_interpolated
"""
import numpy as np
import pandas as pd

from src.utils.config import PROCESSED_DIR
from src.utils.logger import get_logger

log = get_logger("transformation")

HARMONISE = {
    "Jammu & Kashmir": "Jammu & Kashmir (incl. Ladakh)",
    "Ladakh": "Jammu & Kashmir (incl. Ladakh)",
    "Dadra & Nagar Haveli": "DNH & Daman & Diu",
    "Daman & Diu": "DNH & Daman & Diu",
}

ZONES = {  # based on India's Zonal Councils
    "Northern": ["Chandigarh", "Delhi", "Haryana", "Himachal Pradesh",
                 "Jammu & Kashmir (incl. Ladakh)", "Punjab", "Rajasthan"],
    "Central": ["Chhattisgarh", "Madhya Pradesh", "Uttar Pradesh", "Uttarakhand"],
    "Eastern": ["Bihar", "Jharkhand", "Odisha", "West Bengal"],
    "Western": ["DNH & Daman & Diu", "Goa", "Gujarat", "Maharashtra"],
    "Southern": ["Andaman & Nicobar Islands", "Andhra Pradesh", "Karnataka", "Kerala",
                 "Lakshadweep", "Puducherry", "Tamil Nadu", "Telangana"],
    "North Eastern": ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya",
                      "Mizoram", "Nagaland", "Sikkim", "Tripura"],
}
STATE_TO_ZONE = {s: z for z, states in ZONES.items() for s in states}

# which population each category's rate is based on (same as NCRB)
POP_GROUP = {
    "crime_against_women": "female",
    "crime_against_children": "children",
}
POP_SOURCE_CATEGORY = {"general": "ipc_bns_crime", "female": "crime_against_women",
                       "children": "crime_against_children"}


def harmonise(df):
    df = df.copy()
    df["state"] = df["state"].replace(HARMONISE)
    return df


def build_population(indicators):
    """One population series per state, year and group, filled for every year 2016-2024."""
    years = range(2016, 2025)
    frames = []
    for group, category in POP_SOURCE_CATEGORY.items():
        pop = (indicators[indicators.category == category]
               .groupby(["state", "year"], as_index=False)["population_lakhs"]
               .sum(min_count=1))
        for state, g in pop.groupby("state"):
            known = g.dropna().set_index("year")["population_lakhs"]
            if known.empty:
                continue
            x, y = known.index.to_numpy(float), known.to_numpy(float)
            if len(x) == 1:
                filled = np.full(len(years), y[0])
            else:  # linear fit through the known points (handles extrapolation for 2016-17)
                filled = np.interp(list(years), x, y)
                slope_lo = (y[1] - y[0]) / (x[1] - x[0])
                filled = [y[0] + slope_lo * (yr - x[0]) if yr < x[0] else v
                          for yr, v in zip(years, filled)]
            frames.append(pd.DataFrame({
                "state": state, "year": list(years), "population_group": group,
                "population_lakhs": np.round(filled, 2),
                "is_interpolated": [yr not in known.index for yr in years],
            }))
    return pd.concat(frames, ignore_index=True)


def run():
    cases = pd.read_csv(PROCESSED_DIR / "state_crime_cases.csv")
    indicators = pd.read_csv(PROCESSED_DIR / "state_indicators.csv")

    # 1. harmonise states, then sum the merged ones
    cases = (harmonise(cases)
             .groupby(["state", "year", "category"], as_index=False)["cases"]
             .sum(min_count=1))
    cases["is_derived"] = False
    unmerged = indicators[~indicators.state.isin(HARMONISE)]  # for the rate check
    indicators = harmonise(indicators)

    # 2. derive total_cognizable = IPC + SLL where NCRB has no table
    wide = cases.pivot_table(index=["state", "year"], columns="category",
                             values="cases", aggfunc="sum").reset_index()
    have_total = set(map(tuple, cases.loc[cases.category == "total_cognizable",
                                          ["state", "year"]].values))
    derived = wide[[(s, y) not in have_total for s, y in zip(wide.state, wide.year)]].copy()
    derived = pd.DataFrame({"state": derived.state, "year": derived.year,
                            "category": "total_cognizable",
                            "cases": derived.ipc_bns_crime + derived.sll_crime,
                            "is_derived": True})
    cases = pd.concat([cases, derived], ignore_index=True)
    log.info("derived total_cognizable for %d state-years (IPC + SLL)", len(derived))

    # check: does IPC + SLL equal NCRB's own total where both exist? (2022-2024)
    check = wide.dropna(subset=["total_cognizable"])
    diff = (check.ipc_bns_crime + check.sll_crime - check.total_cognizable).abs()
    if (diff > 1).any():
        log.warning("IPC + SLL differs from NCRB total in %d rows (max diff %.0f)",
                    (diff > 1).sum(), diff.max())
    else:
        log.info("check passed: IPC + SLL matches NCRB total for 2022-2024")

    # 3. population and crime rate
    population = build_population(indicators)
    cases["population_group"] = cases.category.map(POP_GROUP).fillna("general")
    cases = cases.merge(population, on=["state", "year", "population_group"], how="left")
    cases["crime_rate"] = (cases.cases / cases.population_lakhs).round(2)

    # check: our rate vs the rate NCRB printed (only for years NCRB printed it)
    cmp = cases.merge(unmerged[["state", "year", "category", "crime_rate"]],
                      on=["state", "year", "category"], suffixes=("", "_ncrb"))
    cmp = cmp.dropna(subset=["crime_rate", "crime_rate_ncrb"])
    off = cmp[(cmp.crime_rate - cmp.crime_rate_ncrb).abs() > 0.15 * cmp.crime_rate_ncrb.abs() + 0.2]
    log.info("rate check: %d of %d NCRB-reported rates matched within 15%%",
             len(cmp) - len(off), len(cmp))
    if len(off):
        print(off[["state", "year", "category", "crime_rate", "crime_rate_ncrb"]]
              .head(15).to_string(index=False))

    # 4. year-on-year change and zones
    cases = cases.sort_values(["state", "category", "year"])
    cases["yoy_change_pct"] = (cases.groupby(["state", "category"])["cases"]
                               .pct_change(fill_method=None).mul(100).round(1))
    cases["zone"] = cases.state.map(STATE_TO_ZONE)
    missing_zone = cases.loc[cases.zone.isna(), "state"].unique()
    if len(missing_zone):
        log.warning("states without a zone: %s", list(missing_zone))

    final = cases[["state", "zone", "year", "category", "cases", "population_lakhs",
                   "crime_rate", "yoy_change_pct", "is_derived"]]
    final.to_csv(PROCESSED_DIR / "crime_state_year.csv", index=False)
    population.to_csv(PROCESSED_DIR / "population.csv", index=False)
    log.info("saved crime_state_year.csv  %d rows | %d states | %d categories",
             len(final), final.state.nunique(), final.category.nunique())

    print("\nStates per category and year after harmonising (should be 35):")
    print(final.pivot_table(index="category", columns="year", values="state",
                            aggfunc="nunique").to_string())


if __name__ == "__main__":
    run()