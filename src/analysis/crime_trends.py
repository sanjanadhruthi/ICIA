"""
crime_trends.py - how crime in India changed from 2016 to 2024.

Run: python -m src.analysis.crime_trends
"""
import matplotlib.pyplot as plt

from src.analysis.common import COLORS, pct, query, save_fig, write_insights

LABELS = {
    "ipc_bns_crime": "IPC/BNS", "sll_crime": "SLL", "violent_crime": "Violent",
    "crime_against_women": "Against women", "crime_against_children": "Against children",
    "cyber_crime": "Cyber",
}


def run():
    trend = query("SELECT * FROM v_national_trend ORDER BY year")
    total = trend[trend.category == "total_cognizable"].set_index("year")
    figures = []

    # 1. total cases (bars) + crime rate (line)
    fig, ax = plt.subplots()
    ax.bar(total.index, total.cases / 1e5, color=COLORS[0], alpha=0.85, label="Cases (lakh)")
    ax.set_ylabel("Cases registered (lakh)")
    ax2 = ax.twinx()
    ax2.plot(total.index, total.crime_rate, color=COLORS[1], marker="o", lw=2.5,
             label="Crime rate (per lakh people)")
    ax2.set_ylabel("Crime rate")
    ax2.set_ylim(0, total.crime_rate.max() * 1.25)  # start at 0 so changes are not exaggerated
    ax2.grid(False)
    ax.set_ylim(0, total.cases.max() / 1e5 * 1.25)
    ax.annotate("COVID-19 lockdown\nviolations registered", xy=(2020, total.cases[2020] / 1e5),
                xytext=(2021.1, total.cases.max() / 1e5 * 1.12), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="gray"))
    ax.set_title("Total cognizable crime in India, 2016-2024")
    fig.legend(loc="lower center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, -0.06))
    figures.append(save_fig(fig, "01_national_total_trend"))

    # 2. growth index: 2016 = 100, so categories of very different sizes are comparable
    fig, ax = plt.subplots()
    for i, (code, label) in enumerate(LABELS.items()):
        s = trend[trend.category == code].set_index("year").cases
        ax.plot(s.index, s / s.iloc[0] * 100, marker="o", lw=2, label=label, color=COLORS[i])
    ax.axhline(100, color="black", lw=0.8)
    ax.set_ylabel("Index (2016 = 100)")
    ax.set_title("Which crime categories grew fastest? (cases, 2016 = 100)")
    ax.legend(fontsize=9, ncol=2)
    figures.append(save_fig(fig, "02_category_growth_index"))

    # 3. rate trends for the three focus areas
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    for ax, code, color in zip(axes, ["crime_against_women", "crime_against_children",
                                      "cyber_crime"], COLORS[1:]):
        s = trend[trend.category == code].set_index("year").crime_rate
        ax.plot(s.index, s, marker="o", color=color, lw=2)
        ax.set_title(LABELS[code], fontsize=11)
        ax.set_ylim(0, s.max() * 1.2)
    axes[0].set_ylabel("Rate per lakh population")
    fig.suptitle("Crime rate trends in three focus areas", fontweight="bold")
    figures.append(save_fig(fig, "03_focus_area_rates"))

    # insights computed from the data, not typed by hand
    growth = {LABELS[c]: pct(trend[(trend.category == c) & (trend.year == 2016)].cases.iat[0],
                             trend[(trend.category == c) & (trend.year == 2024)].cases.iat[0])
              for c in LABELS}
    fastest = max(growth, key=growth.get)
    lines = [
        f"Total cognizable crime went from {total.cases[2016]/1e5:.1f} lakh cases (2016) to "
        f"{total.cases[2024]/1e5:.1f} lakh (2024), a change of {pct(total.cases[2016], total.cases[2024]):+.1f}%. "
        f"The crime rate moved from {total.crime_rate[2016]:.1f} to {total.crime_rate[2024]:.1f} per lakh people.",
        f"2020 was the peak year ({total.cases[2020]/1e5:.1f} lakh cases, "
        f"{pct(total.cases[2019], total.cases[2020]):+.1f}% vs 2019). This spike reflects COVID-19 lockdown "
        f"violations being registered as cases, not a rise in conventional crime.",
        f"Fastest-growing category 2016-2024: {fastest} ({growth[fastest]:+.1f}% cases). "
        + ", ".join(f"{k} {v:+.0f}%" for k, v in sorted(growth.items(), key=lambda kv: -kv[1]) if k != fastest) + ".",
        "Caution: rising numbers can also mean better reporting (e.g. online FIRs, cyber helplines), "
        "not only more crime.",
    ]
    write_insights("01_crime_trends", "National crime trends (2016-2024)", lines, figures)


if __name__ == "__main__":
    run()