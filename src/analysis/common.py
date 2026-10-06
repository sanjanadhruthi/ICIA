"""common.py - shared helpers for every analysis module."""
import matplotlib

matplotlib.use("Agg")  # draw charts to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

from src.database.connection import get_engine
from src.utils.config import FIGURES_DIR, INSIGHTS_DIR

COLORS = ["#1f4e79", "#c0392b", "#2e8b57", "#d68910", "#7d3c98", "#17a589", "#5d6d7e"]
plt.rcParams.update({
    "figure.figsize": (10, 5.5), "figure.dpi": 120, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3,
    "axes.titleweight": "bold", "axes.titlesize": 13,
})


def query(sql, **params):
    """Run SQL against the ICIA database and return a DataFrame."""
    return pd.read_sql(sql, get_engine(), params=params or None)


def save_fig(fig, name, source="Source: NCRB, Crime in India 2018, 2021, 2024"):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.text(0.01, 0.005, source, fontsize=8, color="gray")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIGURES_DIR / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    return f"{name}.png"


def write_insights(name, title, lines, figures=()):
    """Save findings as Markdown so they can go straight into the README."""
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    md = [f"# {title}", ""] + [f"- {line}" for line in lines]
    if figures:
        md += ["", "## Charts", ""] + [f"![{f}](../figures/{f})" for f in figures]
    (INSIGHTS_DIR / f"{name}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n### {title}")
    for line in lines:
        print(f"  - {line}")


def pct(a, b):
    """Percentage change from a to b."""
    return (b - a) / a * 100 if a else float("nan")