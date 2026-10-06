"""
category_analysis.py - what kinds of crime, and the 2024 IPC -> BNS switch.

Run: python -m src.analysis.category_analysis
"""
import matplotlib.pyplot as plt

from src.analysis.common import COLORS, query, save_fig, write_insights

LATEST = 2024


def run():
    figures, lines = [], []

    # 1. top IPC/BNS crime heads
    heads = query("SELECT crime_head, cases FROM crime_heads WHERE law = 'IPC/BNS' "
                  "AND year = :y AND is_subtotal = 0 AND cases > 0", y=LATEST)
    top = heads.nlargest(12, "cases").sort_values("cases")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top.crime_head.str.slice(0, 45), top.cases / 1e3, color=COLORS[0])
    ax.set_xlabel("Cases (thousand)")
    ax.set_title(f"Most common IPC/BNS crimes, {LATEST}")
    figures.append(save_fig(fig, "07_top_ipc_bns_heads"))
    lines.append(f"Most common IPC/BNS crime head in {LATEST}: {top.iloc[-1].crime_head} "
                 f"({top.iloc[-1].cases:,.0f} cases).")

    # 2. top SLL acts
    sll = query("SELECT crime_head, cases FROM crime_heads WHERE law = 'SLL' "
                "AND year = :y AND is_subtotal = 0 AND cases > 0", y=LATEST)
    top_sll = sll.nlargest(10, "cases").sort_values("cases")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(top_sll.crime_head.str.slice(0, 50), top_sll.cases / 1e3, color=COLORS[2])
    ax.set_xlabel("Cases (thousand)")
    ax.set_title(f"Most common Special & Local Law (SLL) crimes, {LATEST}")
    figures.append(save_fig(fig, "08_top_sll_acts"))
    lines.append(f"Most common SLL crime in {LATEST}: {top_sll.iloc[-1].crime_head} "
                 f"({top_sll.iloc[-1].cases:,.0f} cases).")

    # 3. IPC -> BNS transition (BNS came into force on 1 July 2024)
    total = query("SELECT ipc_cases, bns_cases, cases FROM crime_heads WHERE law = 'IPC/BNS' "
                  "AND year = :y AND crime_head LIKE 'Total Cognizable%'", y=LATEST)
    bns = query("SELECT * FROM v_bns_transition WHERE total_cases >= 1000")
    if not total.empty and total.cases.iat[0]:
        share = total.bns_cases.iat[0] / total.cases.iat[0] * 100
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(["2024"], [total.ipc_cases.iat[0] / 1e5], color=COLORS[0], label="Under IPC")
        ax.barh(["2024"], [total.bns_cases.iat[0] / 1e5], left=[total.ipc_cases.iat[0] / 1e5],
                color=COLORS[3], label="Under BNS")
        ax.set_xlabel("Cases (lakh)")
        ax.set_title("2024: the year India switched from IPC to BNS")
        ax.legend()
        figures.append(save_fig(fig, "09_ipc_bns_split"))
        lines.append(f"{share:.1f}% of 2024 IPC/BNS cases were registered under the new BNS, "
                     f"which applied only from 1 July 2024.")
        if not bns.empty:
            hi, lo = bns.nlargest(1, "bns_share_pct").iloc[0], bns.nsmallest(1, "bns_share_pct").iloc[0]
            lines.append(f"BNS share varies by crime: highest for '{hi.crime_head}' ({hi.bns_share_pct:.0f}%), "
                         f"lowest for '{lo.crime_head}' ({lo.bns_share_pct:.0f}%). Crimes reported long after "
                         f"they happen stay under IPC, because the law at the time of the offence applies.")

    # 4. cyber crime hotspots
    cyber = query("SELECT state, cases, crime_rate FROM v_crime WHERE category = 'cyber_crime' "
                  "AND year = :y AND crime_rate IS NOT NULL", y=LATEST)
    top_cy = cyber.nlargest(10, "crime_rate").sort_values("crime_rate")
    fig, ax = plt.subplots()
    ax.barh(top_cy.state, top_cy.crime_rate, color=COLORS[4])
    ax.set_xlabel("Cyber crime rate (per lakh people)")
    ax.set_title(f"Cyber crime hotspots, {LATEST}")
    figures.append(save_fig(fig, "10_cyber_hotspots"))
    lines.append(f"Highest cyber crime rate in {LATEST}: {top_cy.iloc[-1].state} "
                 f"({top_cy.iloc[-1].crime_rate:.1f} per lakh). Top 3 states hold "
                 f"{cyber.nlargest(3, 'cases').cases.sum() / cyber.cases.sum() * 100:.0f}% of all cyber cases.")

    write_insights("03_category_analysis", "Crime categories and the BNS transition", lines, figures)


if __name__ == "__main__":
    run()