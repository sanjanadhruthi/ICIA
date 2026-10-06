"""
anomaly_detection.py - finds state-years that moved very differently from the rest of India.

Method (simple and explainable):
    1. For each state, category and year, take the growth vs the previous year (log ratio).
    2. Compare it with how every other state moved that same year (median and spread).
    3. Robust z-score = (state growth - median growth) / (1.4826 * MAD).
       |z| > 3.5 and at least 500 cases -> flagged as an anomaly.
Because each state is compared with all states in the SAME year, a nationwide shock
(like COVID in 2020) is not flagged everywhere - only states that broke from the pattern.

Run: python -m src.analysis.anomaly_detection
"""
import matplotlib.pyplot as plt
import numpy as np

from src.analysis.common import COLORS, query, save_fig, write_insights
from src.utils.config import INSIGHTS_DIR

Z_LIMIT = 3.5
MIN_CASES = 500


def find_anomalies():
    """Return every flagged state-year (also used by the dashboard)."""
    df = query("SELECT state, zone, year, category, category_label, cases FROM v_crime "
               "WHERE cases IS NOT NULL ORDER BY state, category, year")
    df["prev"] = df.groupby(["state", "category"]).cases.shift()
    df = df[(df.prev > 0) & (df.cases > 0)].copy()
    df["growth"] = np.log(df.cases / df.prev)

    grp = df.groupby(["category", "year"]).growth
    df["median_growth"] = grp.transform("median")
    mad = grp.transform(lambda g: (g - g.median()).abs().median())
    df["z"] = (df.growth - df.median_growth) / (1.4826 * mad.replace(0, np.nan))
    df["change_pct"] = (np.exp(df.growth) - 1) * 100

    flags = df[(df.z.abs() > Z_LIMIT) & (df[["cases", "prev"]].max(axis=1) >= MIN_CASES)]
    return flags.sort_values("z", key=abs, ascending=False)


def run():
    flags = find_anomalies()
    out = flags[["state", "year", "category", "prev", "cases", "change_pct", "z"]].round(2)
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(INSIGHTS_DIR / "anomalies.csv", index=False)

    figures = []
    fig, ax = plt.subplots()
    counts = flags.groupby("year").size().reindex(range(2017, 2025), fill_value=0)
    ax.bar(counts.index, counts.values, color=COLORS[1])
    ax.set_ylabel("Number of anomalies")
    ax.set_title("Unusual state-level jumps or drops per year")
    figures.append(save_fig(fig, "13_anomalies_per_year"))

    lines = [f"{len(flags)} anomalies found (|robust z| > {Z_LIMIT}, at least {MIN_CASES} cases). "
             f"Full list: reports/insights/anomalies.csv."]
    for _, r in flags.head(8).iterrows():
        lines.append(f"{r.state}, {r.category_label}, {r.year}: {r.prev:,.0f} -> {r.cases:,.0f} cases "
                     f"({r.change_pct:+.0f}%, z = {r.z:+.1f}).")
    lines.append("An anomaly is a question, not a conclusion: it can mean a real change in crime, "
                 "a reporting or registration change, or a data error. Each one needs checking.")
    write_insights("05_anomalies", "Anomaly detection", lines, figures)


if __name__ == "__main__":
    run()