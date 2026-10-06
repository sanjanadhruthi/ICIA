"""
state_analysis.py - which states stand out, and why raw counts mislead.

Run: python -m src.analysis.state_analysis
"""
import matplotlib.pyplot as plt
import pandas as pd

from src.analysis.common import COLORS, query, save_fig, write_insights

LATEST = 2024


def run():
    rank = query("SELECT * FROM v_state_ranking WHERE year = :y AND category = 'total_cognizable'",
                 y=LATEST)
    figures = []

    # 1. top 10 by raw cases vs top 10 by rate
    by_cases = rank.nsmallest(10, "cases_rank").sort_values("cases")
    by_rate = rank.nsmallest(10, "rate_rank").sort_values("crime_rate")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.5))
    a1.barh(by_cases.state, by_cases.cases / 1e5, color=COLORS[0])
    a1.set_title("Top 10 by number of cases (lakh)")
    a2.barh(by_rate.state, by_rate.crime_rate, color=COLORS[1])
    a2.set_title("Top 10 by crime rate (per lakh people)")
    fig.suptitle(f"Same data, different story: size vs rate ({LATEST})", fontweight="bold")
    figures.append(save_fig(fig, "04_states_cases_vs_rate"))

    # 2. biggest rate changes 2016 -> 2024
    change = query("SELECT * FROM v_state_change WHERE category = 'total_cognizable' "
                   "AND rate_change IS NOT NULL ORDER BY rate_change")
    movers = pd.concat([change.head(7), change.tail(7)]).drop_duplicates("state")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(movers.state, movers.rate_change,
            color=[COLORS[2] if v < 0 else COLORS[1] for v in movers.rate_change])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Change in crime rate, 2016 to 2024 (per lakh people)")
    ax.set_title("Biggest improvers (green) and biggest increases (red)")
    figures.append(save_fig(fig, "05_state_rate_change"))

    # 3. zones over time
    zone = query("SELECT * FROM v_zone_trend WHERE category = 'total_cognizable' ORDER BY year")
    fig, ax = plt.subplots()
    for i, (z, g) in enumerate(zone.groupby("zone")):
        ax.plot(g.year, g.crime_rate, marker="o", lw=2, label=z, color=COLORS[i])
    ax.set_ylabel("Crime rate (per lakh people)")
    ax.set_title("Crime rate by zone, 2016-2024")
    ax.legend(fontsize=9)
    figures.append(save_fig(fig, "06_zone_trend"))

    # 4. chargesheeting: how often police investigations end in a chargesheet
    cs = query("SELECT state, chargesheet_rate FROM ncrb_indicators "
               "WHERE category = 'total_cognizable' AND year = :y AND chargesheet_rate IS NOT NULL",
               y=LATEST).sort_values("chargesheet_rate")
    lines = []
    top_c, top_r = rank.nsmallest(1, "cases_rank").iloc[0], rank.nsmallest(1, "rate_rank").iloc[0]
    overlap = set(by_cases.state) & set(by_rate.state)
    lines.append(f"In {LATEST}, {top_c.state} registered the most cases ({top_c.cases/1e5:.1f} lakh), "
                 f"but {top_r.state} had the highest crime rate ({top_r.crime_rate:.0f} per lakh). "
                 f"Only {len(overlap)} states appear in both top-10 lists: raw counts mostly reflect population size.")
    if not change.empty:
        best, worst = change.iloc[0], change.iloc[-1]
        lines.append(f"Biggest improvement 2016-2024: {best.state} (rate {best.rate_2016:.0f} -> {best.rate_2024:.0f}). "
                     f"Biggest increase: {worst.state} (rate {worst.rate_2016:.0f} -> {worst.rate_2024:.0f}).")
    z24 = zone[zone.year == LATEST].sort_values("crime_rate")
    lines.append(f"Highest-rate zone in {LATEST}: {z24.iloc[-1].zone} ({z24.iloc[-1].crime_rate:.0f}); "
                 f"lowest: {z24.iloc[0].zone} ({z24.iloc[0].crime_rate:.0f}).")
    if not cs.empty:
        lines.append(f"Chargesheeting rate {LATEST} ranges from {cs.iloc[0].chargesheet_rate:.1f}% "
                     f"({cs.iloc[0].state}) to {cs.iloc[-1].chargesheet_rate:.1f}% ({cs.iloc[-1].state}).")
    lines.append("High crime rates can partly reflect easier registration of FIRs, so a high rate "
                 "is not automatically a sign of a less safe state.")
    write_insights("02_state_analysis", "State-level analysis", lines, figures)


if __name__ == "__main__":
    run()