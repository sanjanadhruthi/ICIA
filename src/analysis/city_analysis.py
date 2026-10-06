"""
city_analysis.py - crime in India's 19 metropolitan cities (2022-2024).

Run: python -m src.analysis.city_analysis
"""
import matplotlib.pyplot as plt

from src.analysis.common import COLORS, pct, query, save_fig, write_insights


def run():
    city = query("SELECT * FROM metro_city_crimes")
    latest = city.year.max()
    now = city[city.year == latest].dropna(subset=["crime_rate"])
    figures = []

    # 1. crime rate ranking
    r = now.sort_values("crime_rate")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(r.city, r.crime_rate, color=COLORS[0])
    ax.set_xlabel("Crime rate (per lakh people, 2011 census population)")
    ax.set_title(f"Crime rate in metropolitan cities, {latest}")
    figures.append(save_fig(fig, "11_city_crime_rate"))

    # 2. crime rate vs chargesheeting rate: are high-crime cities also solving fewer cases?
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.scatter(now.crime_rate, now.chargesheet_rate, s=now.cases / 400, color=COLORS[1], alpha=0.6)
    for _, row in now.iterrows():
        ax.annotate(row.city, (row.crime_rate, row.chargesheet_rate), fontsize=8,
                    xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Crime rate (per lakh people)")
    ax.set_ylabel("Chargesheeting rate (%)")
    ax.set_title(f"Crime rate vs chargesheeting rate, {latest} (bubble size = cases)")
    figures.append(save_fig(fig, "12_city_rate_vs_chargesheet"))

    # 3. change since first year
    first = city.year.min()
    wide = city.pivot_table(index="city", columns="year", values="cases")
    wide["change"] = [pct(a, b) for a, b in zip(wide[first], wide[latest])]
    wide = wide.sort_values("change")

    corr = now.crime_rate.corr(now.chargesheet_rate)
    lines = [
        f"Highest crime rate among metros in {latest}: {r.iloc[-1].city} ({r.iloc[-1].crime_rate:.0f} per lakh); "
        f"lowest: {r.iloc[0].city} ({r.iloc[0].crime_rate:.0f}).",
        f"Largest rise in cases {first}-{latest}: {wide.index[-1]} ({wide.change.iloc[-1]:+.1f}%); "
        f"largest fall: {wide.index[0]} ({wide.change.iloc[0]:+.1f}%).",
        f"Correlation between crime rate and chargesheeting rate across metros: {corr:+.2f} "
        + ("(weak - a high crime rate does not mean police solve fewer cases)." if abs(corr) < 0.3
           else "(a noticeable relationship worth investigating)."),
        "Caution: NCRB computes city rates with 2011 census population, so fast-growing cities "
        "look worse than they really are.",
    ]
    write_insights("04_city_analysis", "Metropolitan cities", lines, figures)


if __name__ == "__main__":
    run()