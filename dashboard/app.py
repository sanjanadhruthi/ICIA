"""
ICIA dashboard - Indian Crime Intelligence & Analysis

Run from the project root:
    streamlit run dashboard/app.py
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # lets "src..." imports work when Streamlit runs this file

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database.connection import get_engine
from src.utils.config import DB_PATH

st.set_page_config(page_title="ICIA - Indian Crime Intelligence & Analysis",
                   page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# ======================================================================= design
NAVY, KHAKI, BRICK, TEAL, SLATE = "#1D3557", "#A67C1E", "#B23A48", "#2A7F62", "#6B7785"
ZONE_COLORS = {"Northern": NAVY, "Central": KHAKI, "Eastern": BRICK, "Western": TEAL,
               "Southern": "#5B5EA6", "North Eastern": "#8C6D46"}
CAT_COLORS = [NAVY, KHAKI, BRICK, TEAL, "#5B5EA6", "#8C6D46", SLATE]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, label, p, li { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
h1, h2, h3, h4 { font-family: 'Source Serif 4', Georgia, serif !important; color: #1B2430; letter-spacing: -0.01em; }

/* page: dotted "graph paper" background, full width */
[data-testid="stAppViewContainer"] { background-color: #F3F5F8;
  background-image: radial-gradient(#D5DBE3 1px, transparent 1px); background-size: 22px 22px; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 1.6rem 2.2rem 3rem 2.2rem; max-width: 100%; }

/* sidebar: navy navigation panel */
[data-testid="stSidebar"] { background: #1D3557; min-width: 260px !important; }
[data-testid="stSidebar"] * { color: #E8ECF2 !important; }
[data-testid="stSidebar"] .brand { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.7rem; font-weight: 700; }
[data-testid="stSidebar"] .brandsub { font-size: 0.85rem; opacity: 0.75; margin-top: -0.3rem; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding: 0.55rem 0.7rem; border-radius: 6px; margin-bottom: 2px; width: 100%; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,0.08); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: rgba(166,124,30,0.28); box-shadow: inset 3px 0 0 #D4A63C; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] p { font-size: 1rem; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }
[data-testid="stSidebar"] [data-testid="stExpander"] details { background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { background: transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background: rgba(255,255,255,0.08) !important; }
[data-testid="stSidebar"] table { font-size: 0.82rem; }
[data-testid="stSidebar"] th, [data-testid="stSidebar"] td { border-color: rgba(255,255,255,0.15) !important;
  background: transparent !important; vertical-align: top; }

/* hero band */
.hero { background: #1D3557; color: #F4F1E8; border-radius: 14px; padding: 1.8rem 2.2rem;
        margin-bottom: 1.2rem; position: relative; overflow: hidden; }
.hero::after { content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
        border: 36px solid rgba(212,166,60,0.18); border-radius: 50%; }
.hero h1 { color: #FFFFFF !important; font-size: 2.3rem !important; margin: 0 0 0.4rem 0; padding: 0; }
.hero p { font-size: 1.05rem; line-height: 1.6; max-width: 70ch; color: #D9DFE8; margin: 0; }
.hero .stat { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.35rem; line-height: 1.45;
        color: #FFFFFF; max-width: 62ch; margin-top: 1rem; border-left: 4px solid #D4A63C; padding-left: 1rem; }
.hero .stat b { color: #F2C66B; }
.hero .wrap { display: flex; gap: 2.5rem; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; }
.hero .facts { display: grid; grid-template-columns: repeat(2, minmax(120px, 1fr)); gap: 0.9rem 1.8rem;
        position: relative; z-index: 1; margin-right: 2rem; }
.hero .facts div { border-top: 1px solid rgba(255,255,255,0.25); padding-top: 0.4rem; font-size: 0.85rem; color: #C9D2DE; }
.hero .facts b { display: block; font-family: 'Source Serif 4', Georgia, serif; font-size: 1.7rem; color: #FFFFFF; }

/* cards: every bordered container */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
  background: #FFFFFF; border: 1px solid #E1E5EB !important; border-radius: 12px;
  box-shadow: 0 1px 2px rgba(27,36,48,0.04), 0 6px 18px rgba(27,36,48,0.05);
  animation: rise 0.55s ease-out both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* KPI cards */
.kpi { background: #FFFFFF; border: 1px solid #E1E5EB; border-radius: 12px; padding: 1rem 1.2rem;
       display: flex; align-items: center; gap: 1rem; min-height: 118px;
       box-shadow: 0 6px 18px rgba(27,36,48,0.05); animation: rise 0.55s ease-out both; }
.kpi .label { font-size: 0.85rem; color: #5A6573; }
.kpi .value { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.9rem; font-weight: 700; color: #1B2430; line-height: 1.15; }
.kpi .sub { font-size: 0.85rem; color: #5A6573; margin-top: 0.15rem; }
.kpi .up { color: #B23A48; font-weight: 600; } .kpi .down { color: #2A7F62; font-weight: 600; }
.ring { position: relative; width: 84px; height: 84px; flex: none; }
.ring svg { transform: rotate(-90deg); }
.ring .track { fill: none; stroke: #E7EAEF; stroke-width: 9; }
.ring .bar { fill: none; stroke-width: 9; stroke-linecap: round; animation: fill 1.3s ease-out forwards; }
@keyframes fill { to { stroke-dashoffset: var(--off); } }
.ring .num { position: absolute; inset: 0; display: grid; place-items: center;
             font-weight: 600; font-size: 1.05rem; color: #1B2430; }

/* explanations */
.about { font-size: 0.95rem; color: #3D4855; line-height: 1.55; max-width: 100ch; margin: -0.2rem 0 0.6rem 0; }
.howto { font-size: 0.9rem; color: #4A5562; background: #F7F5EF; border-radius: 8px;
         padding: 0.6rem 0.85rem; line-height: 1.5; margin-top: 0.3rem; }
.howto strong { color: #1B2430; }
.anom { border-bottom: 1px solid #EEF0F3; padding: 0.55rem 0.2rem; }
.anom .t { font-weight: 600; color: #1B2430; }
.anom .m { font-size: 0.85rem; color: #5A6573; }
.anom .c { float: right; font-weight: 600; }
.catcard { background: #FFFFFF; border: 1px solid #E1E5EB; border-radius: 12px; padding: 0.9rem 1rem;
           height: 100%; border-top: 4px solid var(--c); animation: rise 0.55s ease-out both; }
.catcard .n { font-family: 'Source Serif 4', Georgia, serif; font-size: 1.5rem; font-weight: 700; }
.catcard .d { font-size: 0.85rem; color: #4A5562; line-height: 1.45; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; } .ring .bar { stroke-dashoffset: var(--off); } }
</style>
""", unsafe_allow_html=True)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def about(text):
    """One or two lines saying what this data is."""
    html(f'<div class="about">{text}</div>')


def howto(text):
    html(f'<div class="howto">{text}</div>')


def ring_svg(pct, color):
    r = 36
    c = 2 * math.pi * r
    off = c * (1 - max(0, min(pct, 100)) / 100)
    return (f'<div class="ring"><svg width="84" height="84" viewBox="0 0 84 84">'
            f'<circle class="track" cx="42" cy="42" r="{r}"/>'
            f'<circle class="bar" cx="42" cy="42" r="{r}" stroke="{color}" '
            f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{c:.1f}" style="--off:{off:.1f}"/></svg>'
            f'<div class="num">{pct:.0f}%</div></div>')


def kpi(label, value, sub="", ring=None, color=NAVY):
    left = ring_svg(ring, color) if ring is not None else ""
    return (f'<div class="kpi">{left}<div><div class="label">{label}</div>'
            f'<div class="value">{value}</div><div class="sub">{sub}</div></div></div>')


def style(fig, x=None, y=None, height=None, top=10):
    fig.update_layout(template="simple_white", font=dict(family="IBM Plex Sans", size=13, color="#1B2430"),
                      title=None, margin=dict(l=10, r=10, t=top, b=10), legend_title_text="",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      hoverlabel=dict(font_family="IBM Plex Sans"), height=height,
                      transition=dict(duration=500, easing="cubic-in-out"))
    fig.update_xaxes(title_text=x, showgrid=False)
    fig.update_yaxes(title_text=y, gridcolor="#ECEEF1", showgrid=True)
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ======================================================================= content
CATEGORY_INFO = {
    "total_cognizable": "Every serious crime police registered: IPC/BNS plus Special & Local Laws.",
    "ipc_bns_crime": "Crimes under India's main criminal code: murder, theft, assault, cheating and more.",
    "sll_crime": "Crimes under separate laws for specific issues: drugs, alcohol, arms, gambling.",
    "violent_crime": "Crimes involving force or threat: murder, kidnapping, rape, robbery, rioting.",
    "crime_against_women": "Crimes where a woman is the victim, e.g. cruelty by husband, assault, dowry deaths.",
    "crime_against_children": "Crimes against anyone under 18, including POCSO (child sexual abuse) cases.",
    "cyber_crime": "Crimes using computers or the internet: online fraud, identity theft, cyber stalking.",
}
SHORT = {"total_cognizable": "All crimes", "ipc_bns_crime": "IPC/BNS", "sll_crime": "Special & Local Laws",
         "violent_crime": "Violent", "crime_against_women": "Against women",
         "crime_against_children": "Against children", "cyber_crime": "Cyber"}

GLOSSARY = """
| Term | What it means |
|---|---|
| **NCRB** | National Crime Records Bureau. It collects crime data from every state's police and publishes *Crime in India* each year. |
| **IPC** | Indian Penal Code (1860), India's main criminal law until 30 June 2024. |
| **BNS** | Bharatiya Nyaya Sanhita, the code that replaced the IPC from 1 July 2024. |
| **SLL** | Special & Local Laws: separate laws for specific crimes (drugs, alcohol, arms, gambling, IT Act). |
| **Cognizable crime** | A serious offence where police can register a case (FIR) and arrest without a court's permission. |
| **Crime rate** | Cases per 1 lakh (100,000) people, so big and small states can be compared fairly. |
| **Chargesheeting rate** | Of the cases police finished investigating, the share sent to court with enough evidence. |
| **Pendency** | Cases still under investigation at the end of the year. |
"""

POLICE_MEASURES = [  # (keywords that must all appear in the metric name, friendly name, explanation)
    (["chargesheet", "rate"], "Chargesheeting rate",
     "Share of investigated cases sent to court with enough evidence. Higher is better."),
    (["pendency"], "Pendency %",
     "Share of cases still under investigation at year end. Lower is better."),
    (["pending", "end"], "Cases pending at year end",
     "How many cases were still being investigated on 31 December."),
    (["reported", "during"], "Cases reported this year",
     "New cases registered during the year."),
    (["false"], "Closed as false",
     "Cases closed because the complaint was found to be false."),
    (["not", "investigated"], "Not investigated",
     "Cases police did not take up for investigation."),
]

# ======================================================================= data
@st.cache_resource(show_spinner="Building the database from the raw NCRB files (first run only)...")
def ensure_database():
    """On a fresh machine (or Streamlit Cloud) the .db file does not exist yet: build it."""
    if not DB_PATH.exists():
        from src.database import create_tables, load_data
        from src.preprocessing import cleaning, transformation
        for step in (cleaning, transformation, create_tables, load_data):
            step.run()
    return True


@st.cache_data
def q(sql, **params):
    return pd.read_sql(sql, get_engine(), params=params or None)


@st.cache_data
def anomalies():
    from src.analysis.anomaly_detection import find_anomalies
    return find_anomalies()


ensure_database()
cats = q("SELECT category_code, category_label FROM dim_category ORDER BY category_id")
LABEL = dict(zip(cats.category_code, cats.category_label))
YEARS = q("SELECT DISTINCT year FROM fact_crime ORDER BY year").year.tolist()

# ======================================================================= sidebar
with st.sidebar:
    html('<div class="brand">🛡️ ICIA</div><div class="brandsub">Indian Crime Intelligence & Analysis</div>')
    st.markdown("---")
    page = st.radio("Navigate", ["Overview", "States", "Crime types", "Cities", "Police performance"],
                    label_visibility="collapsed")
    st.markdown("---")
    with st.expander("What do IPC, BNS, SLL mean?"):
        st.markdown(GLOSSARY)
    with st.expander("About this project"):
        st.markdown("ICIA combines the official statistics NCRB publishes in separate yearly tables into "
                    "one consistent dataset, so states and years can be compared fairly.\n\n"
                    "**Source:** NCRB *Crime in India* 2018, 2021 and 2024 editions (2016-2024), via data.gov.in.\n\n"
                    "**Method:** 25 raw tables cleaned automatically; J&K includes Ladakh and DNH is "
                    "combined with Daman & Diu so trends stay comparable; national rates are total "
                    "cases ÷ total population.\n\n"
                    "**Read with care:** these are *recorded* crimes. Easier reporting raises the "
                    "numbers without more crime happening.")
    st.caption("Built by Sanjanadhruthi Toutam · Data: NCRB")


def filters(show_year=True):
    """Category choices shown as visible buttons, not hidden in a dropdown."""
    c = st.pills("Crime category", list(SHORT), format_func=SHORT.get, default="total_cognizable",
                 key="cat") or "total_cognizable"
    y = YEARS[-1]
    if show_year:
        y = st.segmented_control("Year", YEARS, default=YEARS[-1], key="year") or YEARS[-1]
    html(f'<div class="about"><b>{LABEL[c]}:</b> {CATEGORY_INFO[c]}</div>')
    return c, y


def per(c):
    return {"crime_against_women": "women", "crime_against_children": "children"}.get(c, "people")


# ======================================================================= overview
if page == "Overview":
    category, year = (st.session_state.get("cat") or "total_cognizable",
                      st.session_state.get("year") or YEARS[-1])
    nat = q("SELECT * FROM v_national_trend WHERE category = :c ORDER BY year", c=category)
    now = nat[nat.year == year].iloc[0]
    prev = nat[nat.year == year - 1]
    change = ""
    if not prev.empty:
        d = (now.cases / prev.iloc[0].cases - 1) * 100
        change = f", {'up' if d > 0 else 'down'} {abs(d):.1f}% from {year - 1}"
    html(f"""<div class="hero"><div class="wrap"><div>
      <h1>How much crime does India record, and where?</h1>
      <p>Nine years of official police statistics (2016-2024) for every state, cleaned and combined
      in one place. Choose a category and a year below; everything updates.</p>
      <div class="stat">In {year}, police in India registered <b>{now.cases:,.0f}</b> cases of
      {LABEL[category].lower()}{change}. That is <b>{now.crime_rate:.1f} for every lakh {per(category)}</b>.</div>
      </div><div class="facts">
        <div><b>9</b>years of data</div><div><b>35</b>states and UTs</div>
        <div><b>7</b>crime categories</div><div><b>25</b>NCRB tables combined</div>
      </div></div></div>""")

    category, year = filters()
    nat = q("SELECT * FROM v_national_trend WHERE category = :c ORDER BY year", c=category)
    cur = q("SELECT * FROM v_crime WHERE category = :c AND year = :y", c=category, y=year)
    now = nat[nat.year == year].iloc[0]
    prev = nat[nat.year == year - 1]

    k = st.columns(4)
    if prev.empty:
        sub = "first year in the data"
    else:
        d = (now.cases / prev.iloc[0].cases - 1) * 100
        sub = f'<span class="{"up" if d > 0 else "down"}">{"▲" if d > 0 else "▼"} {abs(d):.1f}%</span> vs {year - 1}'
    k[0].markdown(kpi("Cases registered", f"{now.cases:,.0f}", sub), unsafe_allow_html=True)
    k[1].markdown(kpi("Crime rate", f"{now.crime_rate:.1f}", f"cases per lakh {per(category)}"),
                  unsafe_allow_html=True)
    valid = cur.dropna(subset=["crime_rate"])
    above = int((valid.crime_rate > now.crime_rate).sum())
    k[2].markdown(kpi("States/UTs above the national rate", f"{above} of {len(valid)}",
                      "higher rate than India overall", ring=above / max(len(valid), 1) * 100, color=BRICK),
                  unsafe_allow_html=True)
    total_cases = cur.cases.sum()
    top5 = cur.nlargest(5, "cases").cases.sum() / total_cases * 100 if total_cases else 0
    lead = cur.nlargest(1, "cases").iloc[0] if total_cases else None
    k[3].markdown(kpi("Share of all cases in the 5 biggest states",
                      lead.state if lead is not None else "-",
                      f"registers the most: {lead.cases / total_cases * 100:.0f}% on its own" if lead is not None else "",
                      ring=top5, color=KHAKI), unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([2.2, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### Cases registered each year")
            fig = px.bar(nat, x="year", y="cases")
            fig.update_traces(marker_color=[BRICK if y_ == year else NAVY for y_ in nat.year],
                              hovertemplate="%{x}: %{y:,.0f} cases<extra></extra>")
            show(style(fig, y="Cases registered", height=330))
            howto("<strong>How to read this:</strong> each bar is all cases registered across India that "
                  "year; red is the year you picked. More cases <em>recorded</em> is not always more crime.")
        with st.container(border=True):
            st.markdown(f"#### Crime rate: cases per lakh {per(category)}")
            fig = px.area(nat, x="year", y="crime_rate", markers=True)
            fig.update_traces(line_color=NAVY, line_width=3, fillcolor="rgba(29,53,87,0.10)",
                              hovertemplate="%{x}: %{y:.1f} per lakh<extra></extra>")
            fig.update_yaxes(rangemode="tozero")
            show(style(fig, y=f"Cases per lakh {per(category)}", height=300))
            howto("<strong>Why a rate?</strong> Population grows every year, so raw counts can rise even "
                  "if nobody is less safe. The rate divides by population. The axis starts at zero so "
                  "small changes aren't exaggerated.")
        if category == "violent_crime" and year == 2024:
            st.warning("**Read 2024 with care:** NCRB's own violent-crime count for 2024 is far above "
                       "2023 in many states. 2024 is also the year the BNS replaced the IPC and several "
                       "offences were reclassified, so part of this jump may be a change in how crimes "
                       "are counted rather than in how many happened.")
        if category in ("total_cognizable", "ipc_bns_crime", "sll_crime"):
            st.info("**Why 2020 jumps:** during the COVID-19 lockdown, people breaking lockdown rules were "
                    "booked as criminal cases. It was a change in what got registered, not a crime wave.")

    with right:
        with st.container(border=True):
            st.markdown("#### Unusual spikes and drops")
            about("States that moved very differently from the rest of India in the same year. "
                  "Each is a question worth checking, not a verdict.")
            an = anomalies()
            search = st.text_input("Search state", placeholder="Search a state, e.g. Manipur",
                                   label_visibility="collapsed")
            if search:
                an = an[an.state.str.contains(search, case=False)]
            box = st.container(height=640, border=False)
            if an.empty:
                box.caption("No unusual movements found for that search.")
            for _, r in an.head(60).iterrows():
                color = BRICK if r.change_pct > 0 else TEAL
                box.markdown(
                    f'<div class="anom"><span class="c" style="color:{color}">{r.change_pct:+.0f}%</span>'
                    f'<div class="t">{r.state}, {r.year}</div>'
                    f'<div class="m">{r.category_label}: {r.prev:,.0f} → {r.cases:,.0f} cases</div></div>',
                    unsafe_allow_html=True)
            howto("<strong>How it works:</strong> each state's yearly change is compared with all other "
                  "states that year (robust z-score above 3.5). It caught the 2023 Manipur violence and "
                  "Tamil Nadu's 2020 lockdown cases without being told about them.")

# ======================================================================= states
elif page == "States":
    st.markdown("## States and Union Territories")
    about("Compare all 35 states and UTs for any crime category and year, or follow one state over time. "
          "Jammu & Kashmir includes Ladakh, and Dadra & Nagar Haveli is combined with Daman & Diu, so "
          "every year has the same 35 areas.")
    category, year = filters()
    nat = q("SELECT * FROM v_national_trend WHERE category = :c ORDER BY year", c=category)
    cur = q("SELECT * FROM v_crime WHERE category = :c AND year = :y", c=category, y=year)
    now = nat[nat.year == year].iloc[0]

    left, right = st.columns([1.5, 1], gap="large")
    with left, st.container(border=True):
        measure = st.segmented_control("Compare by", ["crime_rate", "cases"], default="crime_rate",
                                       format_func={"crime_rate": "Crime rate (fair)",
                                                    "cases": "Number of cases (favours big states)"}.get,
                                       key="measure") or "crime_rate"
        ranked = cur.dropna(subset=[measure]).sort_values(measure)
        fig = px.bar(ranked, x=measure, y="state", orientation="h", color="zone",
                     color_discrete_map=ZONE_COLORS)
        if measure == "crime_rate":
            fig.add_vline(x=now.crime_rate, line_dash="dash", line_color=SLATE,
                          annotation_text=f"India: {now.crime_rate:.1f}", annotation_position="top right")
        fig.update_layout(legend=dict(orientation="h", y=1.04, x=0))
        show(style(fig, x=f"Cases per lakh {per(category)}" if measure == "crime_rate" else "Cases registered",
                   height=900, top=60))
        howto("<strong>How to read this:</strong> sorted from lowest to highest; colours show the region. "
              "Switch to <em>Number of cases</em> and the most populous states jump to the top. States "
              "with easy online FIR registration, such as Kerala and Delhi, often look higher because "
              "more crimes get recorded.")
    with right:
        with st.container(border=True):
            st.markdown("#### One state over time")
            state = st.selectbox("Choose a state or UT", sorted(cur.state))
            hist = q("SELECT year, crime_rate, cases FROM v_crime WHERE category = :c AND state = :s "
                     "ORDER BY year", c=category, s=state)
            both = pd.concat([hist.assign(series=state), nat[["year", "crime_rate"]].assign(series="India")])
            fig = px.line(both, x="year", y="crime_rate", color="series", markers=True,
                          color_discrete_map={state: BRICK, "India": SLATE})
            fig.update_yaxes(rangemode="tozero")
            fig.update_layout(legend=dict(orientation="h", y=1.1, x=0))
            show(style(fig, y=f"Cases per lakh {per(category)}", height=330, top=40))
            howto(f"Red is {state}, grey is India. Where red is above grey, {state} records more of this "
                  f"crime per person than the country overall.")
        with st.container(border=True):
            st.markdown("#### Biggest changes, 2016 to 2024")
            ch = q("SELECT state, rate_2016, rate_2024, rate_change FROM v_state_change "
                   "WHERE category = :c AND rate_change IS NOT NULL ORDER BY rate_change", c=category)
            movers = pd.concat([ch.head(5), ch.tail(5)]).drop_duplicates("state")
            fig = px.bar(movers, x="rate_change", y="state", orientation="h")
            fig.update_traces(marker_color=[TEAL if v < 0 else BRICK for v in movers.rate_change])
            show(style(fig, x="Change in rate (per lakh)", height=340))
            howto("Green: rate fell the most. Red: rate rose the most.")

# ======================================================================= crime types
elif page == "Crime types":
    st.markdown("## Types of crime")
    about("Two levels of detail. <b>Seven broad categories</b> cover every year from 2016 to 2024. "
          "<b>Individual offences</b> (theft, hurt, NDPS cases...) come from NCRB's crime-head tables, "
          "which were collected for 2022-2024 only.")

    nat_all = q("SELECT * FROM v_national_trend ORDER BY year")
    first, last = nat_all.year.min(), nat_all.year.max()
    cols = st.columns(len(SHORT))
    for i, (code, name) in enumerate(SHORT.items()):
        s = nat_all[nat_all.category == code].set_index("year")
        g = (s.cases[last] / s.cases[first] - 1) * 100
        cols[i].markdown(f'<div class="catcard" style="--c:{CAT_COLORS[i]}"><div class="d"><b>{name}</b></div>'
                         f'<div class="n">{s.cases[last] / 1e5:.1f} lakh</div>'
                         f'<div class="d">{g:+.0f}% since {first}<br>{CATEGORY_INFO[code]}</div></div>',
                         unsafe_allow_html=True)
    st.write("")

    with st.container(border=True):
        st.markdown(f"#### How each category grew, {first}-{last}")
        idx = nat_all.copy()
        idx["index"] = idx.groupby("category").cases.transform(lambda s: s / s.iloc[0] * 100)
        idx["name"] = idx.category.map(SHORT)
        fig = px.line(idx, x="year", y="index", color="name", markers=True,
                      color_discrete_sequence=CAT_COLORS)
        fig.add_hline(y=100, line_color="#9AA3AE", line_width=1)
        fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
        fig.update_yaxes(type="log", tickvals=[50, 100, 150, 200, 300, 500, 800, 1000])
        show(style(fig, y=f"Cases ({first} = 100, log scale)", height=400, top=40))
        howto(f"<strong>How to read this:</strong> every category starts at 100 in {first}, so a "
              "small category (cyber) and a huge one (IPC) can share one chart. A line at 200 means "
              f"cases doubled since {first}. The scale is logarithmic so cyber crime's huge growth "
              "doesn't flatten the other lines. Click a name in the legend to hide or show it.")

    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.markdown("#### Most common offences")
        a, b = st.columns(2)
        law = a.segmented_control("Law", ["IPC/BNS", "SLL"], default="IPC/BNS", key="law") or "IPC/BNS"
        hy = b.segmented_control("Year", [2022, 2023, 2024], default=2024, key="hy") or 2024
        about("IPC/BNS: the main criminal code. SLL: special laws such as NDPS (drugs), Excise and Gambling Acts.")
        heads = q("SELECT crime_head, cases FROM crime_heads WHERE law = :l AND year = :y AND is_main = 1 "
                  "AND cases > 0 AND crime_head NOT LIKE 'Other%'", l=law, y=hy).nlargest(12, "cases")
        fig = px.bar(heads.sort_values("cases"), x="cases", y="crime_head", orientation="h")
        fig.update_traces(marker_color=NAVY, hovertemplate="%{y}: %{x:,.0f}<extra></extra>")
        show(style(fig, x="Cases registered", height=430))
        howto("Main offence groups only: sub-types such as <em>vehicle theft</em> are already counted "
              "inside <em>theft</em>, and NCRB's catch-all 'Other' rows are left out. "
              "Longer bars are more frequent offences. Top SLL entries (alcohol prohibition, gambling) "
              "reflect police enforcement drives as much as public behaviour.")
    with right, st.container(border=True):
        st.markdown("#### 2024: the year the criminal code changed")
        about("The BNS replaced the IPC on 1 July 2024, so 2024 cases are split between the two laws.")
        bns = q("SELECT * FROM v_bns_transition WHERE total_cases >= 1000 "
                "AND crime_head NOT LIKE 'Other%' ORDER BY total_cases DESC").head(12)
        long = bns.melt(id_vars="crime_head", value_vars=["ipc_cases", "bns_cases"],
                        var_name="law", value_name="cases")
        long["law"] = long.law.map({"ipc_cases": "Old IPC", "bns_cases": "New BNS"})
        fig = px.bar(long, x="cases", y="crime_head", color="law", orientation="h",
                     color_discrete_map={"Old IPC": SLATE, "New BNS": KHAKI},
                     category_orders={"crime_head": bns.crime_head.tolist()})
        fig.update_layout(legend=dict(orientation="h", y=1.06, x=0))
        show(style(fig, x="Cases registered in 2024", height=430, top=30))
        howto("A crime is charged under the law in force <em>when it happened</em>, so offences "
              "reported late, such as fraud found months later, stay under the IPC.")

# ======================================================================= cities
elif page == "Cities":
    st.markdown("## Metropolitan cities")
    about("NCRB reports separately for India's 19 cities with over 20 lakh people (2011 census). "
          "Figures cover all IPC/BNS and SLL crimes for 2022-2024.")
    city = q("SELECT * FROM metro_city_crimes")
    cyears = sorted(int(v) for v in city.year.unique())
    cyear = st.segmented_control("Year", cyears, default=cyears[-1], key="cyear") or cyears[-1]
    latest = cyears[-1]
    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.markdown(f"#### Cases registered, {cyear}")
        sel = city[city.year == cyear].sort_values("cases")
        fig = px.bar(sel, x="cases", y="city", orientation="h")
        fig.update_traces(marker_color=NAVY, hovertemplate="%{y}: %{x:,.0f}<extra></extra>")
        show(style(fig, x="Cases registered", height=560))
        howto("Total cases per city. Bigger cities naturally register more; see the right chart for rates.")
    with right, st.container(border=True):
        st.markdown(f"#### Crime rate vs cases sent to court, {latest}")
        rate = city[city.year == latest].dropna(subset=["crime_rate", "chargesheet_rate"])
        fig = px.scatter(rate, x="crime_rate", y="chargesheet_rate", size="cases", text="city", size_max=40)
        fig.update_traces(marker_color=KHAKI, marker_opacity=0.75, textposition="top center", textfont_size=11)
        show(style(fig, x="Crime rate (per lakh people)", y="Chargesheeting rate (%)", height=560))
        howto("Each bubble is a city; bigger bubbles registered more cases. Further right: more crime "
              "per person. Higher up: police sent a bigger share of cases to court. NCRB uses 2011 "
              "population for cities, so fast-growing cities look worse than they are.")
    with st.container(border=True):
        st.markdown(f"#### Which cities changed most, {cyears[0]} to {latest}")
        wide = city.pivot_table(index="city", columns="year", values="cases")
        wide["change"] = (wide[latest] / wide[cyears[0]] - 1) * 100
        wide = wide.dropna(subset=["change"]).sort_values("change").reset_index()
        fig = px.bar(wide, x="city", y="change")
        fig.update_traces(marker_color=[TEAL if v < 0 else BRICK for v in wide.change],
                          hovertemplate="%{x}: %{y:+.1f}%<extra></extra>")
        fig.add_hline(y=0, line_color="#9AA3AE", line_width=1)
        show(style(fig, y="Change in cases (%)", height=340))
        howto("Red: cases rose. Green: cases fell. A rise can mean more crime or better reporting.")

# ======================================================================= police
elif page == "Police performance":
    st.markdown("## Police performance")
    about("How efficiently do police forces handle the cases they register? From NCRB's police "
          "disposal tables for IPC/BNS cases, 2021 and 2024. Useful for planning and resources; it is "
          "not about investigating individual cases.")
    metrics = q("SELECT DISTINCT metric FROM police_disposal ORDER BY metric").metric.tolist()
    found = []
    for words, name, desc in POLICE_MEASURES:
        matches = [x for x in metrics if all(w in x for w in words)]
        m = min(matches, key=len) if matches else None  # shortest = the general column, not a sub-column
        if m and m not in [f[0] for f in found]:
            found.append((m, name, desc))
    names = {m: n for m, n, _ in found}
    descs = {m: d for m, _, d in found}

    a, b = st.columns([3, 1])
    choice = a.pills("Measure", [m for m, _, _ in found] + ["__more"], key="pm",
                     default=found[0][0] if found else "__more",
                     format_func=lambda m: names.get(m, "More measures…")) or (found[0][0] if found else "__more")
    pd_years = q("SELECT DISTINCT year FROM police_disposal ORDER BY year").year.tolist()
    pyear = b.segmented_control("Year", pd_years, default=pd_years[-1], key="pyear") or pd_years[-1]
    metric = choice
    if choice == "__more":
        metric = st.selectbox("All measures in the NCRB table", metrics,
                              format_func=lambda m: m.replace("_", " ").capitalize())
    label = names.get(metric, metric.replace("_", " ").capitalize())
    about(f"<b>{label}:</b> {descs.get(metric, 'A column from the NCRB police disposal table.')}")

    data = q("SELECT state, value FROM police_disposal WHERE year = :y AND metric = :m "
             "AND value IS NOT NULL", y=pyear, m=metric).sort_values("value")
    left, right = st.columns([2, 1], gap="large")
    with left, st.container(border=True):
        st.markdown(f"#### {label} by state, {pyear}")
        med = data.value.median()
        fig = px.bar(data, x="value", y="state", orientation="h")
        fig.update_traces(marker_color=[TEAL if v >= med else SLATE for v in data.value],
                          hovertemplate="%{y}: %{x:,.1f}<extra></extra>")
        fig.add_vline(x=med, line_dash="dash", line_color=KHAKI,
                      annotation_text=f"Middle state: {med:,.1f}", annotation_position="top right")
        show(style(fig, height=880, top=40))
        howto("Teal bars are above the middle (median) state, grey bars below it.")
    with right:
        if not data.empty:
            hi, lo = data.iloc[-1], data.iloc[0]
            html(kpi("Highest", hi.state, f"{hi.value:,.1f}"))
            st.write("")
            html(kpi("Lowest", lo.state, f"{lo.value:,.1f}"))
            st.write("")
            html(kpi("Middle state (median)", f"{data.value.median():,.1f}", "half the states are above this"))
            st.write("")
        with st.container(border=True):
            st.markdown("#### How a case moves")
            howto("1. A complaint is registered as an FIR.<br>2. Police investigate.<br>"
                  "3. It ends with a <strong>chargesheet</strong> (enough evidence, sent to court) or a "
                  "<strong>final report</strong> (closed, e.g. false or untraceable).<br>"
                  "4. Unfinished cases carry over as <strong>pending</strong> to next year.")