"""
cleaning.py - turns raw NCRB "Crime in India" tables into tidy CSV files.

Run from the project root:
    python -m src.preprocessing.cleaning

Outputs (data/processed/):
    state_crime_cases.csv   state, year, category, cases, edition, source_file
    state_indicators.csv    state, year, category, population_lakhs, crime_rate, chargesheet_rate
    police_disposal.csv     state, year, metric, value
    metro_city_crimes.csv   city, state, year, cases, population_lakhs, crime_rate, chargesheet_rate
    crime_heads.csv         law, crime_head, serial, is_subtotal, year, cases, crime_rate, ipc_cases, bns_cases
    property_stolen.csv     state, year, value_stolen, value_recovered, recovery_pct
"""
import re

import pandas as pd

from src.utils.config import PROCESSED_DIR, RAW_DIR
from src.utils.logger import get_logger

log = get_logger("cleaning")

# ---------------------------------------------------------------- constants
CATEGORY_RULES = [  # order matters: first match wins
    ("children", "crime_against_children"),
    ("women", "crime_against_women"),
    ("cyber", "cyber_crime"),
    ("violent", "violent_crime"),
    ("total ipcbns & sll", "total_cognizable"),
    ("sll", "sll_crime"),
    ("ipc", "ipc_bns_crime"),
]

STATE_ALIASES = {
    "a & n islands": "Andaman & Nicobar Islands",
    "andaman & nicobar islands": "Andaman & Nicobar Islands",
    "d & n haveli": "Dadra & Nagar Haveli",
    "dadra & nagar haveli": "Dadra & Nagar Haveli",
    "d & n haveli & daman & diu": "DNH & Daman & Diu",
    "dnh & daman & diu": "DNH & Daman & Diu",
    "dadra & nagar haveli & daman & diu": "DNH & Daman & Diu",
    "daman & diu": "Daman & Diu",
    "delhi": "Delhi",
    "delhi ut": "Delhi",
    "nct of delhi": "Delhi",
    "jammu & kashmir": "Jammu & Kashmir",
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
}

MISSING = {"", "-", "--", "na", "n.a.", "nan", "none"}


# ---------------------------------------------------------------- helpers
def read_raw(path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, header=None)
    return pd.read_excel(path, header=None)


def text(x):
    return "" if pd.isna(x) else str(x).strip()


def to_number(x):
    s = text(x).replace(",", "")
    if s.lower() in MISSING:
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def as_year(x):
    s = text(x)
    if s.endswith(".0"):
        s = s[:-2]
    if s.isdigit() and 2010 <= int(s) <= 2030:
        return int(s)
    return None


def is_data_row(row):
    """A real state/city/crime row: serial number in col 0, a name in col 1."""
    sl = text(row.iloc[0]).rstrip(".")
    name = text(row.iloc[1])
    return sl.isdigit() and bool(re.search(r"[A-Za-z]", name)) and "total" not in name.lower()


def is_all_india_row(row):
    joined = (text(row.iloc[0]) + " " + text(row.iloc[1])).lower()
    return "total" in joined and "india" in joined


def clean_state(name):
    s = re.sub(r"[\*\+@#]", "", text(name))
    s = re.sub(r"\s+", " ", s).strip()
    key = s.lower().replace(" and ", " & ").replace("&", " & ")
    key = re.sub(r"\s+", " ", key).strip()
    return STATE_ALIASES.get(key, s)


def category_from_name(filename):
    name = re.sub(r"\s+", " ", filename.lower())
    for keyword, category in CATEGORY_RULES:
        if keyword in name:
            return category
    raise ValueError(f"no category rule matches '{filename}'")


def slug(s):
    s = re.sub(r"\(.*?\)", "", s.lower())
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def header_text(hdr, col):
    return " ".join(text(v) for v in hdr.iloc[:, col] if text(v)).lower()


# ---------------------------------------------------------------- state-wise tables
def find_year_columns(hdr):
    """Map year -> column. Handles merged year cells (e.g. 2024 -> IPC | BNS | Total)."""
    year_row = next(
        (r for r in range(len(hdr)) if sum(as_year(v) is not None for v in hdr.iloc[r]) >= 2),
        None,
    )
    if year_row is None:
        raise ValueError("no row with year headers found")

    row, ncol, cols = hdr.iloc[year_row], hdr.shape[1], {}
    for j in range(ncol):
        year = as_year(row.iloc[j])
        if year is None:
            continue
        span, k = [j], j + 1
        while (k < ncol and not text(row.iloc[k])
               and all(not text(hdr.iat[r, k]) for r in range(year_row))):
            span.append(k)
            k += 1
        chosen = span[0]
        if len(span) > 1:  # merged cell: prefer the sub-column labelled "Total"
            for c in span:
                below = " ".join(text(v) for v in hdr.iloc[year_row + 1:, c]).lower()
                if "total" in below:
                    chosen = c
                    break
        cols[year] = chosen
    return cols


def parse_state_table(df, source, edition):
    first = next(i for i in range(len(df)) if is_data_row(df.iloc[i]))
    hdr = df.iloc[:first]
    year_cols = find_year_columns(hdr)
    latest = max(year_cols)
    category = category_from_name(source)

    ind_cols = {}
    for c in range(df.shape[1]):
        if c in year_cols.values():
            continue
        h = header_text(hdr, c)
        if "population" in h:
            ind_cols["population_lakhs"] = c
        elif "chargesheet" in h:
            ind_cols["chargesheet_rate"] = c
        elif "rate" in h and "percentage" not in h:
            ind_cols["crime_rate"] = c

    cases, indicators, all_india = [], [], None
    for i in range(first, len(df)):
        row = df.iloc[i]
        if is_all_india_row(row):
            all_india = row
            continue
        if not is_data_row(row):
            continue
        state = clean_state(row.iloc[1])
        for year, c in year_cols.items():
            cases.append({"state": state, "year": year, "category": category,
                          "cases": to_number(row.iloc[c]), "edition": edition,
                          "source_file": source})
        ind = {"state": state, "year": latest, "category": category}
        ind.update({k: to_number(row.iloc[c]) for k, c in ind_cols.items()})
        indicators.append(ind)

    cases = pd.DataFrame(cases)
    # built-in check: do our state rows add up to NCRB's All-India total?
    if all_india is not None:
        for year, c in year_cols.items():
            ours = cases.loc[cases.year == year, "cases"].sum()
            theirs = to_number(all_india.iloc[c])
            if theirs and abs(ours - theirs) / theirs > 0.005:
                log.warning("  %s %s: states sum %.0f vs All-India %.0f",
                            source, year, ours, theirs)
    else:
        log.warning("  %s: no All-India total row found (check skipped)", source)

    log.info("OK  %-60s %s | %d states | years %s",
             source[:60], category, cases.state.nunique(), sorted(year_cols))
    return cases, pd.DataFrame(indicators)


# ---------------------------------------------------------------- police disposal
def parse_police_disposal(df, source):
    hrow = next(r for r in range(len(df)) if any(text(v).lower() == "state/ut" for v in df.iloc[r]))
    title = " ".join(text(v) for v in df.iloc[:hrow, 0])
    year = int(re.findall(r"20\d\d", title)[-1])

    starts = [c for c in range(df.shape[1]) if text(df.iat[hrow, c]).upper().rstrip(".") == "SL"]
    starts.append(df.shape[1])
    data_rows = [i for i in range(hrow + 1, len(df)) if is_data_row(df.iloc[i])]

    out = []
    for b in range(len(starts) - 1):
        state_col = starts[b] + 1
        parent = ""
        for c in range(state_col + 1, starts[b + 1]):
            top, sub = text(df.iat[hrow, c]), text(df.iat[hrow + 1, c])
            if top:
                parent = top
            metric = slug(f"{parent} {sub}" if sub else parent)
            if not metric:
                continue
            for i in data_rows:
                if not is_data_row(df.iloc[i, starts[b]:]):
                    continue
                out.append({"state": clean_state(df.iat[i, state_col]), "year": year,
                            "metric": metric, "value": to_number(df.iat[i, c])})
    out = pd.DataFrame(out).drop_duplicates(["state", "year", "metric"])
    log.info("OK  %-60s police_disposal | %d metrics | year %d",
             source[:60], out.metric.nunique(), year)
    return out


# ---------------------------------------------------------------- metro cities
def parse_metro(df, source):
    hrow = next(r for r in range(len(df)) if any(text(v).lower() == "city" for v in df.iloc[r]))
    hdr = df.iloc[:hrow + 1]
    year_cols = {as_year(v): c for c, v in enumerate(df.iloc[hrow]) if as_year(v)}
    latest = max(year_cols)
    ind_cols = {}
    for c in range(df.shape[1]):
        h = header_text(hdr, c)
        if "population" in h:
            ind_cols["population_lakhs"] = c
        elif "chargesheet" in h:
            ind_cols["chargesheet_rate"] = c
        elif "rate" in h:
            ind_cols["crime_rate"] = c

    out = []
    for i in range(hrow + 1, len(df)):
        row = df.iloc[i]
        if not is_data_row(row):
            continue
        m = re.match(r"^(.*?)\s*\((.*)\)\s*$", text(row.iloc[1]))
        city, state = (m.group(1), clean_state(m.group(2))) if m else (text(row.iloc[1]), None)
        for year, c in year_cols.items():
            rec = {"city": city, "state": state, "year": year, "cases": to_number(row.iloc[c])}
            if year == latest:
                rec.update({k: to_number(row.iloc[cc]) for k, cc in ind_cols.items()})
            out.append(rec)
    out = pd.DataFrame(out)
    log.info("OK  %-60s metro | %d cities", source[:60], out.city.nunique())
    return out


# ---------------------------------------------------------------- crime heads
SUB_MAP = {"cases": "cases", "total ipc+bns cases": "cases", "crime rate": "crime_rate",
           "ipc cases": "ipc_cases", "bns cases": "bns_cases"}


def parse_crime_heads(df, source):
    hrow = next(r for r in range(len(df)) if any(text(v).lower() == "crime head" for v in df.iloc[r]))
    law = "SLL" if "sll" in source.lower() else "IPC/BNS"

    col_map, current = {}, None  # col -> (year, field)
    for c in range(2, df.shape[1]):
        top = df.iat[hrow, c]
        if text(top):
            current = as_year(top)  # non-year text (e.g. "% Share") stops the year
        field = SUB_MAP.get(re.sub(r"\s+", " ", text(df.iat[hrow + 1, c]).lower()))
        if current and field:
            col_map[c] = (current, field)

    out = []
    for i in range(hrow + 2, len(df)):
        row = df.iloc[i]
        head = re.sub(r"\s+", " ", text(row.iloc[1]))
        if not re.search(r"[A-Za-z]", head):
            continue
        serial = text(row.iloc[0])
        recs = {}
        for c, (year, field) in col_map.items():
            recs.setdefault(year, {})[field] = to_number(row.iloc[c])
        for year, vals in recs.items():
            out.append({"law": law, "crime_head": head, "serial": serial,
                        # main heads have plain serials (12, 41, E3); sub-heads (6A, 23.1) sit inside them
                        "is_main": bool(re.fullmatch(r"E?\d+", serial)),
                        "year": year, **vals})
    out = pd.DataFrame(out)
    log.info("OK  %-60s crime heads | %d heads", source[:60], out.crime_head.nunique())
    return out


# ---------------------------------------------------------------- property stolen
def parse_property(path):
    df = pd.read_csv(path)
    state_col = next(c for c in df.columns if "state" in c.lower())
    serial_col = df.columns[0]
    df = df[df[serial_col].astype(str).str.strip().str.isdigit()]

    out = {}
    for col in df.columns:
        m = re.match(r"\s*(20\d\d)", col)
        if not m:
            continue
        low = col.lower()
        field = ("recovery_pct" if "percentage" in low
                 else "value_recovered" if "recovered" in low
                 else "value_stolen" if "stolen" in low else None)
        if not field:
            continue
        for _, r in df.iterrows():
            key = (clean_state(r[state_col]), int(m.group(1)))
            out.setdefault(key, {})[field] = to_number(r[col])
    out = pd.DataFrame([{"state": s, "year": y, **v} for (s, y), v in out.items()])
    log.info("OK  %-60s property | %d states", path.name[:60], out.state.nunique())
    return out


# ---------------------------------------------------------------- main
def run():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cases, indicators, disposal, heads, metro, prop = [], [], [], [], None, None

    for path in sorted(RAW_DIR.rglob("*")):
        if path.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
            continue
        name = path.name.lower()
        try:
            if "property stolen" in name:
                prop = parse_property(path)
            elif "total cases registered" in name:
                log.info("--  %s (complaints/e-FIR table, used in analysis later)", path.name)
            elif "police disposal" in name:
                disposal.append(parse_police_disposal(read_raw(path), path.name))
            elif "metropolitan" in name:
                metro = parse_metro(read_raw(path), path.name)
            elif "crime-head" in name or "crime head" in name:
                heads.append(parse_crime_heads(read_raw(path), path.name))
            else:
                c, i = parse_state_table(read_raw(path), path.name, path.parent.name)
                cases.append(c)
                indicators.append(i)
        except Exception as e:  # keep going, report at the end
            log.error("FAILED %s -> %s: %s", path.name, type(e).__name__, e)

    outputs = {
        "state_crime_cases.csv": pd.concat(cases, ignore_index=True) if cases else None,
        "state_indicators.csv": pd.concat(indicators, ignore_index=True) if indicators else None,
        "police_disposal.csv": pd.concat(disposal, ignore_index=True) if disposal else None,
        "metro_city_crimes.csv": metro,
        "crime_heads.csv": pd.concat(heads, ignore_index=True) if heads else None,
        "property_stolen.csv": prop,
    }
    for fname, frame in outputs.items():
        if frame is None or frame.empty:
            log.warning("nothing to save for %s", fname)
            continue
        frame.to_csv(PROCESSED_DIR / fname, index=False)
        log.info("saved %-25s %d rows", fname, len(frame))

    # ---- built-in checks
    sc = outputs["state_crime_cases.csv"]
    if sc is not None:
        dupes = sc.duplicated(["state", "year", "category"]).sum()
        if dupes:
            log.warning("%d duplicate state-year-category rows", dupes)
        print("\nStates per category and year (should be ~36):")
        print(sc.pivot_table(index="category", columns="year", values="state",
                             aggfunc="nunique").to_string())
        print("\nAll state names found (check for spelling variants):")
        print(sorted(sc.state.unique()))


if __name__ == "__main__":
    run()