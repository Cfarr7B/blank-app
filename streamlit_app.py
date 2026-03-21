"""
7BREW Financial Performance Dashboard
Pure Streamlit + Plotly implementation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import tempfile
from pathlib import Path

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="7BREW | Financial Performance Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# DESIGN TOKENS & THEME
# ─────────────────────────────────────────────
RED    = "#cd2128"
GREEN  = "#12a06e"
BLUE   = "#1d6fcf"
DARK   = "#2d2f36"
MID    = "#5a6070"
MUTED  = "#8a919e"
AMBER  = "#e8940a"
BORDER = "#e2e4e9"
BODY   = "#111318"
SUB    = "#4a5060"
BG     = "#ffffff"
BG2    = "#f5f6f8"
GRID   = "rgba(0,0,0,0.055)"

REGION_COLORS = {
    "CTX-N": "#1d6fcf", "CTX-S": "#2980b9", "FL-P": "#12a06e",
    "FL-P1": "#1a8c5c", "FL-SW": "#0e7a6e", "Middle Earth": "#7c3aed",
    "NM": "#c2410c", "OKC-N": "#cd2128", "OKC-S": "#9b1a1f",
    "Permian Basin": "#e8940a", "WTX": "#d97706",
}

# Inject Google Fonts + custom CSS
st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  /* Global font override */
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
  h1,h2,h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px; }

  /* Tab strip */
  .stTabs [data-baseweb="tab-list"] {
    gap: 2px; background: #f5f6f8; border-radius: 10px; padding: 4px;
    border: 1px solid #e2e4e9;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important; font-weight: 600;
    font-size: 12px; letter-spacing: 0.5px; text-transform: uppercase;
    background: transparent; border-radius: 8px; color: #5a6070;
    padding: 8px 16px;
  }
  .stTabs [aria-selected="true"] {
    background: #cd2128 !important; color: white !important;
  }

  /* Sidebar */
  [data-testid="stSidebar"] { background: #f5f6f8; border-right: 1px solid #e2e4e9; }
  [data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 20px; letter-spacing: 2px; color: #2d2f36;
  }

  /* Metrics */
  [data-testid="stMetric"] { background: white; border: 1px solid #e2e4e9;
    border-radius: 10px; padding: 16px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
  [data-testid="stMetricLabel"] { font-size: 10px !important; font-weight: 600 !important;
    letter-spacing: 1px; text-transform: uppercase; color: #5a6070!important; }
  [data-testid="stMetricValue"] { font-family: 'Bebas Neue', sans-serif !important;
    font-size: 28px !important; color: #111318 !important; }
  [data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace !important;
    font-size: 11px !important; }

  /* DataFrames */
  [data-testid="stDataFrame"] thead th {
    background: #f5f6f8 !important; color: #2d2f36 !important;
    font-family: 'DM Mono', monospace !important; font-size: 11px !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px;
  }
  [data-testid="stDataFrame"] td {
    font-family: 'DM Mono', monospace !important; font-size: 11px !important;
    color: #111318 !important;
  }

  /* Select boxes */
  .stSelectbox select, [data-baseweb="select"] {
    font-family: 'DM Mono', monospace !important; font-size: 12px !important;
  }

  /* KPI cards (custom HTML) */
  .kpi-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
  .kpi-card {
    background: white; border: 1px solid #e2e4e9; border-radius: 10px;
    padding: 16px 18px; flex: 1 1 170px; min-width: 160px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05); position: relative; overflow: hidden;
  }
  .kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; }
  .kpi-card.red::before { background:#cd2128; }
  .kpi-card.green::before { background:#12a06e; }
  .kpi-card.blue::before { background:#1d6fcf; }
  .kpi-card.amber::before { background:#e8940a; }
  .kpi-card.grey::before { background:#5a6070; }
  .kpi-label { font-size:10px; font-weight:700; letter-spacing:1px;
    text-transform:uppercase; color:#5a6070; margin-bottom:6px; }
  .kpi-value { font-family:'Bebas Neue',sans-serif; font-size:30px;
    line-height:1; color:#111318; letter-spacing:1px; }
  .kpi-value.good { color:#12a06e; }
  .kpi-value.bad  { color:#cd2128; }
  .kpi-value.warn { color:#e8940a; }
  .kpi-sub { font-family:'DM Mono',monospace; font-size:10px; color:#8a919e; margin-top:4px; }
  .kpi-delta { display:inline-block; font-family:'DM Mono',monospace;
    font-size:10px; font-weight:600; padding:2px 7px; border-radius:10px; margin-top:5px; }
  .kpi-delta.up   { background:rgba(18,160,110,0.1); color:#12a06e; }
  .kpi-delta.down { background:rgba(205,33,40,0.1); color:#cd2128; }
  .kpi-delta.neut { background:rgba(29,111,207,0.1); color:#1d6fcf; }

  /* Section headers */
  .section-hdr {
    font-family:'Bebas Neue',sans-serif; font-size:26px; letter-spacing:3px;
    color:#2d2f36; margin-bottom:2px; margin-top:8px;
    display:flex; align-items:center; gap:8px;
  }
  .section-hdr::before { content:''; width:6px; height:6px; border-radius:50%;
    background:#cd2128; display:inline-block; flex-shrink:0; }
  .section-sub { font-family:'DM Mono',monospace; font-size:11px;
    color:#8a919e; margin-bottom:16px; margin-left:14px; }
  .red-rule { width:36px; height:3px; background:#cd2128;
    border-radius:2px; margin-bottom:18px; margin-left:14px; }

  /* Insight / alert cards */
  .insight-card {
    background:white; border:1px solid #e2e4e9; border-radius:10px;
    padding:16px 18px; margin-bottom:10px;
    border-left: 4px solid #cd2128;
  }
  .insight-card.win { border-left-color: #12a06e; }
  .insight-card.watch { border-left-color: #e8940a; }
  .insight-card .ic-title { font-weight:700; font-size:13px; color:#2d2f36; margin-bottom:4px; }
  .insight-card .ic-body  { font-size:12px; color:#4a5060; line-height:1.6; }
  .insight-card .ic-tag   { display:inline-block; font-family:'DM Mono',monospace;
    font-size:10px; padding:2px 8px; border-radius:10px; margin-top:6px; }
  .ic-tag.red   { background:rgba(205,33,40,0.1);   color:#cd2128; }
  .ic-tag.green { background:rgba(18,160,110,0.1);  color:#12a06e; }
  .ic-tag.amber { background:rgba(232,148,10,0.1);  color:#e8940a; }
  .ic-tag.grey  { background:rgba(90,96,112,0.1);   color:#5a6070; }

  /* Utility / R&M info box */
  .info-box {
    background:#f5f6f8; border:1px solid #e2e4e9; border-radius:10px;
    padding:14px 18px; font-size:12px; color:#4a5060; margin-bottom:16px;
  }
  .info-box strong { color:#2d2f36; }

  /* Divider */
  hr.brew { border:none; border-top:1px solid #e2e4e9; margin:20px 0; }

  /* Story block */
  .story-block {
    background:white; border:1px solid #e2e4e9; border-radius:10px;
    padding:20px 24px; margin-bottom:16px;
    box-shadow:0 1px 4px rgba(0,0,0,0.04);
  }
  .story-label { font-family:'DM Mono',monospace; font-size:10px;
    text-transform:uppercase; letter-spacing:1px; color:#8a919e; margin-bottom:6px; }
  .story-headline { font-family:'Bebas Neue',sans-serif; font-size:20px;
    letter-spacing:1.5px; color:#cd2128; margin-bottom:8px; }
  .story-body { font-size:13px; color:#4a5060; line-height:1.7; }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 24px !important; max-width: 1600px !important; }
</style>
""")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _fmt_d(v):
    if v is None: return "—"
    return "$" + f"{abs(float(v)):,.0f}"

def _fmt_p(v, dec=1):
    if v is None: return "—"
    return f"{float(v)*100:.{dec}f}%"

def _fmt_bps(delta):
    b = round(float(delta) * 10000)
    return ("+"+str(b) if b >= 0 else str(b)) + " bps"

def brew_fig(fig, height=320, show_legend=True, margin=None):
    m = margin or dict(t=16, b=40, l=8, r=8)
    fig.update_layout(
        height=height, paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", color=BODY, size=12),
        margin=m, showlegend=show_legend,
        legend=dict(font=dict(size=10, color=MID, family="DM Mono")),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=BORDER,
                     tickfont=dict(size=9, color=MID, family="DM Mono"))
    fig.update_yaxes(gridcolor=GRID, linecolor=BORDER,
                     tickfont=dict(size=9, color=MID, family="DM Mono"))
    return fig

def section(title, sub=""):
    st.html(f"""
    <div class="section-hdr">{title}</div>
    {"<div class='section-sub'>" + sub + "</div>" if sub else ""}
    <div class="red-rule"></div>""")

def kpi_row(cards):
    """Render a row of KPI cards. cards = list of dicts with label,value,sub,delta,color,valcls"""
    inner = ""
    for c in cards:
        vcls = c.get("valcls", "")
        delta_html = ""
        if c.get("delta"):
            d = c["delta"]
            dcls = d.get("cls", "neut")
            delta_html = f'<div class="kpi-delta {dcls}">{d["str"]}</div>'
        inner += f"""
        <div class="kpi-card {c.get('color','grey')}">
          <div class="kpi-label">{c['label']}</div>
          <div class="kpi-value {vcls}">{c['value']}</div>
          <div class="kpi-sub">{c.get('sub','')}</div>
          {delta_html}
        </div>"""
    st.html(f'<div class="kpi-row">{inner}</div>')

def insight_card(title, body, tag="", tag_cls="grey", card_cls=""):
    tag_html = f'<span class="ic-tag {tag_cls}">{tag}</span>' if tag else ""
    st.html(f"""
    <div class="insight-card {card_cls}">
      <div class="ic-title">{title}</div>
      <div class="ic-body">{body}</div>
      {tag_html}
    </div>""")

def delta_style(val, inv=False):
    """Return delta dict for KPI card: {str, cls}"""
    b = round(val * 10000)
    s = ("+" if b >= 0 else "") + str(b) + " bps"
    good = (val < 0) if inv else (val > 0)
    return {"str": s, "cls": "up" if good else "down"}

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_base_data():
    """Load DASH data — tries data.json first, falls back to extracting from dashboard.html."""
    base_dir = Path(__file__).parent

    # Prefer data.json if present (faster)
    data_path = base_dir / "data.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fall back: extract from embedded dashboard.html
    html_path = base_dir / "dashboard.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        idx   = html.index("const DASH = ")
        start = idx + len("const DASH = ")
        decoder = json.JSONDecoder()
        dash, _ = decoder.raw_decode(html, start)
        return dash

    st.error("No data source found. Add data.json or dashboard.html to the repo.")
    st.stop()

def get_dash():
    """Return merged DASH: base + any session-uploaded periods."""
    base = load_base_data()
    if "uploaded_dash" not in st.session_state:
        return base
    return st.session_state["uploaded_dash"]

def get_periods_df(dash):
    df = pd.DataFrame(dash["period_summaries"])
    df["period_num"] = df["period_key"].apply(lambda x: int(x.split("_P")[1]))
    df["year"] = df["period_key"].apply(lambda x: int(x.split("_")[0]))
    df.sort_values(["year", "period_num"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def get_stands_df(dash):
    return pd.DataFrame(dash["stand_records"])

def get_regions_df(dash, period_key):
    rows = dash.get("region_by_period", {}).get(period_key, [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ─────────────────────────────────────────────
# SIDEBAR: Upload + Navigation
# ─────────────────────────────────────────────
def render_sidebar():
    st.html("### 7BREW DASHBOARD")
    st.html("<hr>")
    st.html("**📤 Upload P&L Files**")
    st.html(
        '<div class="info-box">Upload 7BREW <strong>PTD Side By Side</strong> Excel files '
        'to add new periods or enrich existing ones with utility detail.</div>'
    )

    uploaded = st.file_uploader(
        "Drop .xlsx P&L files here",
        type=["xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        from pl_parser import parse_pl_file, merge_into_dash
        import copy

        base = load_base_data()
        dash = copy.deepcopy(base)
        parsed = []
        errors = []

        for uf in uploaded:
            try:
                suffix = ".xlsx"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(uf.read())
                    tmp_path = tmp.name
                result = parse_pl_file(tmp_path)
                os.unlink(tmp_path)
                if result and result.get("stands"):
                    parsed.append(result)
                    st.success(f"✓ {uf.name} → {result['period_key']} ({len(result['stands'])} stands)")
                else:
                    errors.append(f"No stands found in {uf.name}")
            except Exception as e:
                errors.append(f"{uf.name}: {e}")

        if errors:
            for e in errors:
                st.error(e)

        if parsed:
            updated = merge_into_dash(dash, parsed)
            st.session_state["uploaded_dash"] = updated
            st.session_state["upload_count"] = len(parsed)
            st.rerun()

    if "upload_count" in st.session_state:
        st.info(f"✅ {st.session_state['upload_count']} period(s) merged into dashboard")
        if st.button("🗑 Clear Uploaded Data"):
            del st.session_state["uploaded_dash"]
            del st.session_state["upload_count"]
            st.rerun()

    st.html("<hr>")
    st.html('<div style="font-family:DM Mono,monospace;font-size:10px;color:#8a919e;">7BREW · CONFIDENTIAL · FY2025–2026</div>')

# ─────────────────────────────────────────────
# TAB: CEO SNAPSHOT
# ─────────────────────────────────────────────
def tab_ceo(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)

    latest = periods_df.iloc[-1]
    prev   = periods_df.iloc[-2] if len(periods_df) > 1 else None
    first  = periods_df.iloc[0]

    # ── System KPIs ──
    section("CEO SNAPSHOT", f"Latest period: {latest['label']} · {int(latest['stands'])} active stands · FY2025–2026")

    total_revenue_ytd = periods_df[periods_df["year"] == 2025]["net_sales"].sum()
    total_ebitda_ytd  = periods_df[periods_df["year"] == 2025]["ebitda"].sum()
    growth_rate       = dash.get("yoy_growth", 1.0) - 1.0
    avg_ebitda_pct    = periods_df[periods_df["year"] == 2025]["ebitda_pct"].mean()

    kpi_row([
        {"label": "FY2025 Total Revenue",     "value": f"${total_revenue_ytd/1e6:.1f}M",  "sub": "13-period total",             "color": "red"},
        {"label": "YoY Revenue Growth",       "value": f"+{growth_rate*100:.1f}%",        "sub": "vs prior year class",         "color": "green",
         "valcls": "good"},
        {"label": "FY2025 Total EBITDA",      "value": f"${total_ebitda_ytd/1e6:.1f}M",  "sub": "after rent",                  "color": "blue"},
        {"label": "FY2025 Avg EBITDA%",       "value": _fmt_p(avg_ebitda_pct),             "sub": "system-wide average",         "color": "green",
         "valcls": "good" if avg_ebitda_pct >= 0.18 else "warn"},
        {"label": f"{latest['label']} Stands","value": str(int(latest["stands"])),        "sub": "active this period",          "color": "grey"},
        {"label": f"{latest['label']} Avg Sales","value": _fmt_d(latest["avg_sales"]),    "sub": "per stand",                   "color": "amber"},
    ])

    # ── Revenue + EBITDA Trend (all periods) ──
    col1, col2 = st.columns([3, 2])
    with col1:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;color:#2d2f36;margin-bottom:4px;">REVENUE & EBITDA TREND — ALL PERIODS</div>')
        fig = go.Figure()
        fig.add_bar(x=periods_df["label"], y=periods_df["avg_sales"],
                    name="Avg Sales/Stand", marker_color=BLUE, opacity=0.7,
                    yaxis="y1")
        fig.add_scatter(x=periods_df["label"], y=periods_df["ebitda_pct"] * 100,
                        name="EBITDA %", mode="lines+markers",
                        line=dict(color=RED, width=2.5), marker=dict(size=6),
                        yaxis="y2")
        fig.update_layout(
            xaxis=dict(tickangle=-35),
            yaxis=dict(title="Avg Sales / Stand ($)", tickprefix="$", tickformat=",.0f",
                       title_font=dict(size=10, color=MID)),
            yaxis2=dict(title="EBITDA %", overlaying="y", side="right",
                        ticksuffix="%", title_font=dict(size=10, color=RED),
                        tickfont=dict(size=9, color=RED)),
            barmode="overlay",
        )
        brew_fig(fig, height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        # YoY growth story
        best  = periods_df.loc[periods_df["ebitda_pct"].idxmax()]
        worst = periods_df.loc[periods_df["ebitda_pct"].idxmin()]
        st.html(f"""
        <div class="story-block">
          <div class="story-label">Performance Narrative</div>
          <div class="story-headline">PEAK: {best['label']} AT {_fmt_p(best['ebitda_pct'])}</div>
          <div class="story-body">
            The system reached peak EBITDA of <strong>{_fmt_p(best['ebitda_pct'])}</strong> in {best['label']}
            on avg sales of <strong>{_fmt_d(best['avg_sales'])}</strong>/stand.
            The trough was {worst['label']} at {_fmt_p(worst['ebitda_pct'])}—typical of
            {"year-end cost absorption" if int(worst['period_num']) >= 12 else "seasonal volume pressure"}.
            <br><br>
            Revenue grew <strong>{growth_rate*100:.1f}% YoY</strong> driven by {int(latest['stands']) - int(first['stands'])}
            net new stand additions across the dataset.
            <br><br>
            As the network matures, EBITDA improvement opportunity lies in labor
            efficiency (target &lt;20% hourly) and stand-level utility cost control.
          </div>
        </div>""")

    st.html('<hr class="brew">')

    # ── Cohort Analysis ──
    col3, col4 = st.columns(2)
    with col3:
        section("COHORT PERFORMANCE", "EBITDA% & Labor% by stand maturity")

        age_buckets = ["New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        age_colors  = [RED, AMBER, BLUE, GREEN]

        cohort_rows = []
        for bkt in age_buckets:
            sub = stands_df[stands_df["Age_Bucket"] == bkt]
            if len(sub) == 0:
                continue
            cohort_rows.append({
                "Cohort": bkt,
                "EBITDA%": round(sub["Store_EBITDA_pct"].mean() * 100, 1),
                "Labor%":  round(sub["Total_Labor_pct"].mean() * 100, 1),
                "Avg Sales": round(sub["Net_Sales"].mean(), 0),
                "Stands": len(sub["Stand"].unique()),
            })
        if cohort_rows:
            cdf = pd.DataFrame(cohort_rows)
            fig2 = go.Figure()
            fig2.add_bar(x=cdf["Cohort"], y=cdf["EBITDA%"], name="EBITDA %",
                         marker_color=age_colors[:len(cdf)], text=cdf["EBITDA%"].map(lambda v: f"{v}%"),
                         textposition="outside", marker_line_width=0, width=0.4)
            fig2.add_scatter(x=cdf["Cohort"], y=cdf["Labor%"], name="Labor %",
                             mode="lines+markers", line=dict(color=MUTED, dash="dot"),
                             marker=dict(size=7), yaxis="y")
            brew_fig(fig2, height=280)
            fig2.update_layout(yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with col4:
        section("REGIONAL PERFORMANCE SNAPSHOT", f"EBITDA% by region — {latest['label']}")
        reg_df = get_regions_df(dash, latest["period_key"])
        if not reg_df.empty:
            reg_df = reg_df.sort_values("ebitda_pct", ascending=True)
            colors = [GREEN if v >= 0.22 else (AMBER if v >= 0.15 else RED) for v in reg_df["ebitda_pct"]]
            fig3 = go.Figure(go.Bar(
                x=reg_df["ebitda_pct"] * 100, y=reg_df["region"],
                orientation="h",
                marker_color=colors,
                text=reg_df["ebitda_pct"].map(lambda v: f"{v*100:.1f}%"),
                textposition="outside",
            ))
            fig3.add_vline(x=latest["ebitda_pct"] * 100, line_dash="dot",
                           line_color=MID, annotation_text="Sys avg",
                           annotation_font_size=9)
            brew_fig(fig3, height=280)
            fig3.update_layout(xaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    st.html('<hr class="brew">')

    # ── Regional Heatmap (all periods) ──
    section("REGIONAL EBITDA HEATMAP", "EBITDA% by region × period — red = below 15%, green = above 22%")
    all_regions = sorted(set(r for pk in dash["region_by_period"] for r in [x["region"] for x in dash["region_by_period"][pk]]))
    heat_data = []
    for pk in periods_df["period_key"]:
        regs = {r["region"]: r["ebitda_pct"] for r in dash["region_by_period"].get(pk, [])}
        row = {"Period": periods_df.loc[periods_df["period_key"]==pk, "label"].values[0]}
        for reg in all_regions:
            row[reg] = round(regs.get(reg, float("nan")) * 100, 1) if reg in regs else None
        heat_data.append(row)

    heat_df = pd.DataFrame(heat_data).set_index("Period")
    fig4 = go.Figure(go.Heatmap(
        z=heat_df.values,
        x=heat_df.columns.tolist(),
        y=heat_df.index.tolist(),
        colorscale=[[0, "#cd2128"], [0.5, "#e8940a"], [1, "#12a06e"]],
        zmid=18, zmin=5, zmax=30,
        text=[[f"{v:.1f}%" if v is not None else "—" for v in row] for row in heat_df.values],
        texttemplate="%{text}",
        textfont=dict(size=9, family="DM Mono"),
        hoverongaps=False,
        colorbar=dict(ticksuffix="%", tickfont=dict(size=9)),
    ))
    brew_fig(fig4, height=360)
    fig4.update_layout(xaxis=dict(tickangle=-35))
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    st.html('<hr class="brew">')

    # ── Forward Story ──
    section("LOOKING FORWARD", "Key themes for 2026 P3–P13 and beyond")
    col5, col6 = st.columns(2)
    with col5:
        fc = dash.get("forecast_26", [])
        fc_df = pd.DataFrame(fc)
        if not fc_df.empty:
            fig5 = go.Figure()
            actuals = fc_df[fc_df["is_actual"] == True]
            forecast = fc_df[fc_df["is_actual"] == False]
            if not actuals.empty:
                fig5.add_bar(x=actuals["period"], y=actuals["ns_base"],
                             name="2026 Actual", marker_color=DARK, opacity=0.85)
            if not forecast.empty:
                fig5.add_bar(x=forecast["period"], y=forecast["ns_base"],
                             name="2026 Base Forecast", marker_color=BLUE, opacity=0.7)
                fig5.add_bar(x=forecast["period"], y=forecast["ns_opt"],
                             name="Optimistic", marker_color=GREEN, opacity=0.5)
                fig5.add_bar(x=forecast["period"], y=forecast["ns_risk"],
                             name="Risk", marker_color=RED, opacity=0.4)
            brew_fig(fig5, height=280)
            fig5.update_layout(barmode="group",
                               yaxis=dict(tickprefix="$", tickformat=",.0f", tickfont=dict(size=9)))
            st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
    with col6:
        themes = [
            ("📈 Growth Engine", "New stand pipeline of 10+ locations in H2 2026 will dilute system EBITDA% by ~150–200bps per cohort during ramp. Labor at new locations averages 30%+ for the first 60–90 days.", "watch", "amber"),
            ("⚡ Utility Pressure", "Summer periods (P6–P8) historically see utility cost increases of 30–50bps. Proactive chiller maintenance and LED retrofits in 2026 pipeline stands can cap this.", "watch", "amber"),
            ("🏆 Regional Maturity", "CTX and OKC mature stands consistently at 22–25% EBITDA. FL-SW structural labor gap (28%+) requires dedicated RM coaching and scheduling discipline.", "win", "green"),
            ("🔧 R&M Watch", "Stands opened 2022–2023 are approaching the 2–3yr equipment cycle. Budget preventive maintenance in P9–P11 to avoid emergency R&M spikes.", "", "red"),
        ]
        for title, body, cls, tag_cls in themes:
            insight_card(title, body, tag=cls.upper() if cls else "", tag_cls=tag_cls, card_cls=cls)


# ─────────────────────────────────────────────
# TAB: OVERVIEW
# ─────────────────────────────────────────────
def tab_overview(dash):
    periods_df = get_periods_df(dash)
    section("SYSTEM OVERVIEW", "Select a period to view performance KPIs and cost structure")

    all_labels = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {lbl: pk for lbl, pk in all_labels}

    c1, c2 = st.columns([2, 1])
    with c1:
        sel_lbl = st.selectbox("View Period", [l for l, _ in all_labels], key="ov_period")
    with c2:
        cmp_lbl = st.selectbox("Compare To", [l for l, _ in all_labels][1:] + [all_labels[-1][0]], key="ov_compare")

    pk  = label_to_key[sel_lbl]
    pkB = label_to_key.get(cmp_lbl, periods_df.iloc[-2]["period_key"])
    ps  = periods_df[periods_df["period_key"] == pk].iloc[0]
    psB = periods_df[periods_df["period_key"] == pkB].iloc[0] if pkB else None

    # KPI cards
    def d(a, b, inv=False):
        if psB is None:
            return None
        delta = a - b
        return delta_style(delta, inv=inv)

    avg_delta = None
    if psB is not None:
        pct_diff = (ps["avg_sales"] - psB["avg_sales"]) / psB["avg_sales"]
        avg_delta = {"str": f"{pct_diff:+.1f}% vs {psB['label']}", "cls": "up" if pct_diff > 0 else "down"}

    kpi_row([
        {"label": "Total Net Sales",     "value": _fmt_d(ps["net_sales"]),    "sub": f"{int(ps['stands'])} stands",     "color": "red"},
        {"label": "Avg Sales / Stand",   "value": _fmt_d(ps["avg_sales"]),    "sub": "per-stand average",              "color": "red",  "delta": avg_delta},
        {"label": "COGS %",              "value": _fmt_p(ps["cogs_pct"]),     "sub": "% of net sales",                 "color": "blue", "delta": d(ps["cogs_pct"], psB["cogs_pct"] if psB is not None else 0, inv=True)},
        {"label": "Hourly Labor %",      "value": _fmt_p(ps["hourly_pct"]),   "sub": "wages only",                     "color": "amber",
         "valcls": "good" if ps["hourly_pct"] <= 0.18 else ("bad" if ps["hourly_pct"] > 0.22 else ""),
         "delta": d(ps["hourly_pct"], psB["hourly_pct"] if psB is not None else 0, inv=True)},
        {"label": "Total Labor & Ben %", "value": _fmt_p(ps["labor_pct"]),    "sub": "incl. mgmt & benefits",          "color": "amber",
         "delta": d(ps["labor_pct"], psB["labor_pct"] if psB is not None else 0, inv=True)},
        {"label": "R&M %",               "value": _fmt_p(ps["rm_pct"]),       "sub": "repair & maintenance",           "color": "grey",
         "valcls": "good" if ps["rm_pct"] <= 0.012 else ("bad" if ps["rm_pct"] >= 0.02 else ""),
         "delta": d(ps["rm_pct"], psB["rm_pct"] if psB is not None else 0, inv=True)},
        {"label": "Unit EBITDAR %",      "value": _fmt_p(ps["ebitdar_pct"]),  "sub": "before rent",                    "color": "green", "valcls": "good"},
        {"label": "Store EBITDA $",      "value": _fmt_d(ps["ebitda"]),       "sub": "total portfolio",                "color": "green"},
        {"label": "Store EBITDA %",      "value": _fmt_p(ps["ebitda_pct"]),   "sub": "% of net sales",                 "color": "green",
         "valcls": "good" if ps["ebitda_pct"] >= 0.20 else ("warn" if ps["ebitda_pct"] >= 0.15 else "bad"),
         "delta": d(ps["ebitda_pct"], psB["ebitda_pct"] if psB is not None else 0)},
        {"label": "Rent %",              "value": _fmt_p(ps["rent_pct"]),     "sub": "occupancy cost",                 "color": "grey"},
    ])

    # Charts row 1
    col1, col2 = st.columns(2)
    with col1:
        reg_df = get_regions_df(dash, pk)
        if not reg_df.empty:
            reg_df = reg_df.sort_values("net_sales", ascending=False)
            fig = go.Figure(go.Bar(
                x=reg_df["region"], y=reg_df["net_sales"],
                marker_color=[REGION_COLORS.get(r, MID) for r in reg_df["region"]],
                text=reg_df["net_sales"].map(lambda v: f"${v/1000:.0f}k"),
                textposition="outside",
            ))
            brew_fig(fig, height=260)
            fig.update_layout(title_text="NET SALES BY REGION", title_font=dict(family="Bebas Neue", size=15),
                              yaxis=dict(tickprefix="$", tickformat=",.0f"), showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        if not reg_df.empty:
            reg_ebi = reg_df.sort_values("ebitda_pct", ascending=True)
            colors = [GREEN if v >= 0.22 else (AMBER if v >= 0.15 else RED) for v in reg_ebi["ebitda_pct"]]
            fig2 = go.Figure(go.Bar(
                x=reg_ebi["ebitda_pct"] * 100, y=reg_ebi["region"],
                orientation="h", marker_color=colors,
                text=reg_ebi["ebitda_pct"].map(lambda v: f"{v*100:.1f}%"),
                textposition="outside",
            ))
            fig2.add_vline(x=ps["ebitda_pct"] * 100, line_dash="dot", line_color=MID,
                           annotation_text="Sys avg", annotation_font_size=9)
            brew_fig(fig2, height=260)
            fig2.update_layout(title_text="EBITDA % BY REGION", title_font=dict(family="Bebas Neue", size=15),
                               xaxis=dict(ticksuffix="%"), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Charts row 2
    col3, col4 = st.columns(2)
    with col3:
        stands_df = get_stands_df(dash)
        ps_stands = stands_df[stands_df["Period_Key"] == pk]
        age_buckets = ["New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        cohort_data = []
        for b in age_buckets:
            sub = ps_stands[ps_stands["Age_Bucket"] == b]
            if len(sub):
                cohort_data.append({"Cohort": b,
                                    "EBITDA%": round(sub["Store_EBITDA_pct"].mean() * 100, 1),
                                    "Labor%":  round(sub["Total_Labor_pct"].mean() * 100, 1)})
        if cohort_data:
            cdf = pd.DataFrame(cohort_data)
            fig3 = go.Figure()
            fig3.add_bar(x=cdf["Cohort"], y=cdf["EBITDA%"], name="EBITDA %",
                         marker_color=[RED, AMBER, BLUE, GREEN][:len(cdf)],
                         text=cdf["EBITDA%"].map(lambda v: f"{v}%"), textposition="outside")
            fig3.add_scatter(x=cdf["Cohort"], y=cdf["Labor%"], name="Labor %",
                             mode="lines+markers", line=dict(color=MUTED, dash="dot"))
            brew_fig(fig3, height=260)
            fig3.update_layout(title_text="PERFORMANCE BY STAND MATURITY",
                               title_font=dict(family="Bebas Neue", size=15),
                               yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col4:
        other = max(0, 1 - ps["cogs_pct"] - ps["labor_pct"] - ps["rent_pct"] - ps["ebitda_pct"])
        fig4 = go.Figure(go.Pie(
            labels=["COGS", "Total Labor", "Rent", "Other OpEx", "EBITDA"],
            values=[ps["cogs_pct"], ps["labor_pct"], ps["rent_pct"], other, ps["ebitda_pct"]],
            hole=0.55,
            marker_colors=[BLUE, AMBER, MID, MUTED, GREEN],
            textinfo="label+percent",
            textfont=dict(size=10, family="DM Mono"),
        ))
        brew_fig(fig4, height=260)
        fig4.update_layout(title_text="COST STRUCTURE", title_font=dict(family="Bebas Neue", size=15),
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# TAB: PERIOD COMPARISON
# ─────────────────────────────────────────────
def tab_comparison(dash):
    periods_df = get_periods_df(dash)
    section("PERIOD COMPARISON", "Compare any two periods across all key metrics")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}

    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        lbl_a = st.selectbox("Period A", [l for l, _ in all_options], key="cmp_a")
    with c2:
        st.html('<div style="text-align:center;font-family:Bebas Neue;font-size:24px;color:#5a6070;padding-top:28px;">VS</div>')
    with c3:
        lbl_b = st.selectbox("Period B", [l for l, _ in all_options][1:], key="cmp_b")

    pka = label_to_key[lbl_a]
    pkb = label_to_key.get(lbl_b)
    psA = periods_df[periods_df["period_key"] == pka].iloc[0]
    psB = periods_df[periods_df["period_key"] == pkb].iloc[0] if pkb else None

    if psB is None:
        st.warning("Select a second period to compare")
        return

    # Metric comparison table
    metrics = [
        ("Avg Net Sales",            "avg_sales",        True,  True),
        ("COGS %",                   "cogs_pct",         False, False),
        ("Hourly Labor %",           "hourly_pct",       False, False),
        ("Total Labor & Benefits %", "labor_pct",        False, False),
        ("R&M %",                    "rm_pct",           False, False),
        ("Utilities %",              "utilities_pct",    False, False),
        ("Controllable %",           "controllable_pct", False, False),
        ("Unit EBITDAR %",           "ebitdar_pct",      False, True),
        ("Rent %",                   "rent_pct",         False, False),
        ("Store EBITDA %",           "ebitda_pct",       False, True),
        ("Discount %",               "discount_pct",     False, False),
    ]

    rows = []
    for label, field, is_dollar, higher_good in metrics:
        va = psA.get(field, 0)
        vb = psB.get(field, 0)
        delta = va - vb
        good = (delta > 0) if higher_good else (delta < 0)
        rows.append({
            "Metric": label,
            f"{psA['label']} (A)": _fmt_d(va) if is_dollar else _fmt_p(va),
            f"{psB['label']} (B)": _fmt_d(vb) if is_dollar else _fmt_p(vb),
            "Δ A − B":  (f"+${delta/1000:.1f}k" if is_dollar else _fmt_bps(delta)),
            "Signal": "↑ Better" if good else ("↓ Worse" if not good else "—"),
        })
    cmp_df = pd.DataFrame(rows)
    st.dataframe(cmp_df, hide_index=True, use_container_width=True,
                 column_config={
                     "Signal": st.column_config.TextColumn("Signal", width="small"),
                     "Δ A − B": st.column_config.TextColumn("Δ A − B", width="small"),
                 })

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Bar(
            x=[psA["label"], psB["label"]],
            y=[psA["avg_sales"], psB["avg_sales"]],
            marker_color=[BLUE, GREEN],
            text=[_fmt_d(psA["avg_sales"]), _fmt_d(psB["avg_sales"])],
            textposition="outside",
        ))
        brew_fig(fig, height=260)
        fig.update_layout(title_text="AVG SALES COMPARISON", title_font=dict(family="Bebas Neue", size=15),
                          yaxis=dict(tickprefix="$", tickformat=",.0f"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        reg_a = pd.DataFrame(dash["region_by_period"].get(pka, []))
        reg_b = pd.DataFrame(dash["region_by_period"].get(pkb, []))
        if not reg_a.empty and not reg_b.empty:
            merged = reg_a.merge(reg_b, on="region", suffixes=("_a", "_b"))
            fig2 = go.Figure()
            fig2.add_bar(x=merged["region"], y=merged["ebitda_pct_a"] * 100,
                         name=psA["label"], marker_color=BLUE, opacity=0.85)
            fig2.add_bar(x=merged["region"], y=merged["ebitda_pct_b"] * 100,
                         name=psB["label"], marker_color=GREEN, opacity=0.75)
            brew_fig(fig2, height=260)
            fig2.update_layout(title_text="EBITDA % BY REGION", title_font=dict(family="Bebas Neue", size=15),
                               barmode="group", yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Distribution charts
    stands_df = get_stands_df(dash)
    col3, col4 = st.columns(2)
    with col3:
        sa = stands_df[stands_df["Period_Key"] == pka]
        fig3 = go.Figure(go.Histogram(x=sa["Total_Labor_pct"] * 100, nbinsx=12,
                                       marker_color=RED, opacity=0.8,
                                       name=psA["label"]))
        brew_fig(fig3, height=240)
        fig3.update_layout(title_text=f"LABOR % DISTRIBUTION — {psA['label']}",
                           title_font=dict(family="Bebas Neue", size=14),
                           xaxis=dict(ticksuffix="%"), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    with col4:
        fig4 = go.Figure(go.Histogram(x=sa["Total_COGS_pct"] * 100, nbinsx=10,
                                       marker_color=BLUE, opacity=0.8))
        brew_fig(fig4, height=240)
        fig4.update_layout(title_text=f"COGS % DISTRIBUTION — {psA['label']}",
                           title_font=dict(family="Bebas Neue", size=14),
                           xaxis=dict(ticksuffix="%"), showlegend=False)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# TAB: STAND DETAIL
# ─────────────────────────────────────────────
def tab_stands(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)
    section("STAND DETAIL", "Filter, sort, and drill into individual stand performance")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}

    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 2])
    with c1:
        sel_lbl = st.selectbox("Period", [l for l, _ in all_options], key="std_period")
    with c2:
        regions = ["All Regions"] + sorted(stands_df["Region"].dropna().unique().tolist())
        sel_reg = st.selectbox("Region", regions, key="std_region")
    with c3:
        ages = ["All Ages", "New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        sel_age = st.selectbox("Age Bucket", ages, key="std_age")
    with c4:
        search = st.text_input("Search Stands", placeholder="Type stand name...", key="std_search")

    pk = label_to_key[sel_lbl]
    df = stands_df[stands_df["Period_Key"] == pk].copy()
    if sel_reg != "All Regions":
        df = df[df["Region"] == sel_reg]
    if sel_age != "All Ages":
        df = df[df["Age_Bucket"] == sel_age]
    if search:
        df = df[df["Stand"].str.contains(search, case=False, na=False)]

    st.caption(f"Showing {len(df)} stands")

    display_cols = {
        "Stand": "Stand", "Region": "Region", "Age_Bucket": "Age",
        "Net_Sales": "Net Sales", "Total_COGS_pct": "COGS%",
        "Total_Hourly_pct": "Hourly%", "Total_Labor_pct": "Labor%",
        "Total_RM_pct": "R&M%", "Controllable_pct": "Ctrl%",
        "Total_Utilities_pct": "Util%", "Total_Fixed_pct": "Fixed%",
        "Unit_EBITDAR_pct": "EBITDAR%", "Total_Rent_pct": "Rent%",
        "Store_EBITDA_pct": "EBITDA%", "Discounts_pct": "Disc%",
    }
    disp = df[list(display_cols.keys())].rename(columns=display_cols).copy()
    for col in ["COGS%", "Hourly%", "Labor%", "R&M%", "Ctrl%", "Util%",
                "Fixed%", "EBITDAR%", "Rent%", "EBITDA%", "Disc%"]:
        if col in disp.columns:
            disp[col] = disp[col].map(lambda v: f"{v*100:.1f}%" if pd.notna(v) else "—")
    disp["Net Sales"] = disp["Net Sales"].map(lambda v: f"${v:,.0f}" if pd.notna(v) else "—")

    st.dataframe(disp, hide_index=True, use_container_width=True, height=420)


# ─────────────────────────────────────────────
# TAB: REGIONS
# ─────────────────────────────────────────────
def tab_regions(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)
    section("REGIONAL ANALYSIS", "Performance by region for selected period")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}
    sel_lbl = st.selectbox("Period", [l for l, _ in all_options], key="reg_period")
    pk = label_to_key[sel_lbl]
    ps = periods_df[periods_df["period_key"] == pk].iloc[0]
    reg_df = get_regions_df(dash, pk)

    if reg_df.empty:
        st.info("No regional data for this period.")
        return

    # Region cards
    reg_sorted = reg_df.sort_values("net_sales", ascending=False)
    cols = st.columns(min(len(reg_sorted), 4))
    for i, (_, row) in enumerate(reg_sorted.iterrows()):
        col_idx = i % len(cols)
        color = REGION_COLORS.get(row["region"], MID)
        ebi_color = "good" if row["ebitda_pct"] >= 0.22 else ("warn" if row["ebitda_pct"] >= 0.15 else "bad")
        with cols[col_idx]:
            st.html(f"""
            <div class="kpi-card" style="border-top:3px solid {color}; margin-bottom:10px;">
              <div class="kpi-label">{row['region']}</div>
              <div class="kpi-value">${row['net_sales']/1000:.0f}k</div>
              <div class="kpi-sub">{int(row['stands'])} stands · ${row['avg_sales']:,.0f}/stand</div>
              <div class="kpi-delta {'up' if row['ebitda_pct']>=0.20 else 'down'}">EBITDA {_fmt_p(row['ebitda_pct'])}</div>
            </div>""")

    st.html('<hr class="brew">')

    col1, col2 = st.columns(2)
    with col1:
        # Labor vs EBITDA scatter
        ps_stands = stands_df[stands_df["Period_Key"] == pk]
        reg_agg = ps_stands.groupby("Region").agg(
            ebitda_pct=("Store_EBITDA_pct", "mean"),
            labor_pct=("Total_Labor_pct", "mean"),
            net_sales=("Net_Sales", "sum"),
            stands=("Stand", "count"),
        ).reset_index()
        fig = go.Figure(go.Scatter(
            x=reg_agg["labor_pct"] * 100,
            y=reg_agg["ebitda_pct"] * 100,
            mode="markers+text",
            text=reg_agg["Region"],
            textposition="top center",
            marker=dict(
                size=reg_agg["net_sales"].map(lambda v: max(10, min(40, v / 30000))),
                color=[REGION_COLORS.get(r, MID) for r in reg_agg["Region"]],
                opacity=0.85,
                line=dict(width=1, color="white"),
            ),
            textfont=dict(size=9, family="DM Mono"),
        ))
        brew_fig(fig, height=300)
        fig.update_layout(title_text="LABOR% vs EBITDA% (bubble = sales volume)",
                          title_font=dict(family="Bebas Neue", size=14),
                          xaxis=dict(ticksuffix="%", title="Total Labor %"),
                          yaxis=dict(ticksuffix="%", title="EBITDA %"),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        # Cost stack
        reg_stack = reg_df.copy()
        cost_fields = {"cogs_pct": "COGS", "labor_pct": "Labor", "rm_pct": "R&M",
                       "ebitda_pct": "EBITDA"}
        fig2 = go.Figure()
        colors_stack = [BLUE, AMBER, MID, GREEN]
        for (field, name), color in zip(cost_fields.items(), colors_stack):
            fig2.add_bar(
                x=reg_stack["region"],
                y=reg_stack[field] * 100 if field in reg_stack.columns else [0] * len(reg_stack),
                name=name,
                marker_color=color,
            )
        brew_fig(fig2, height=300)
        fig2.update_layout(title_text="COST STACK BY REGION",
                           title_font=dict(family="Bebas Neue", size=14),
                           barmode="stack", yaxis=dict(ticksuffix="%"))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# TAB: WINS & OPPORTUNITIES
# ─────────────────────────────────────────────
def tab_insights(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)
    section("WINS & OPPORTUNITIES", "Evidence-based findings with recommended actions")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}
    sel_lbl = st.selectbox("Analyze Period", [l for l, _ in all_options], key="ins_period")
    pk = label_to_key[sel_lbl]
    ps = periods_df[periods_df["period_key"] == pk].iloc[0]
    ps_stands = stands_df[stands_df["Period_Key"] == pk]
    if ps_stands.empty:
        st.info("No stand data for this period.")
        return

    # Auto-generate wins
    wins = []
    opps = []

    top_ebitda = ps_stands.nlargest(3, "Store_EBITDA_pct")
    wins.append({
        "title": f"🏆 Top Performers: {', '.join(top_ebitda['Stand'].str.split(',').str[0].tolist())}",
        "body": f"These stands achieved {_fmt_p(top_ebitda['Store_EBITDA_pct'].mean())} average EBITDA — {_fmt_bps(top_ebitda['Store_EBITDA_pct'].mean() - ps['ebitda_pct'])} above system avg. Best-in-class labor efficiency ({_fmt_p(top_ebitda['Total_Labor_pct'].mean())}) drives the margin.",
        "tag": f"Avg EBITDA: {_fmt_p(top_ebitda['Store_EBITDA_pct'].mean())}", "tag_cls": "green",
    })

    strong_regions = []
    for _, row in get_regions_df(dash, pk).iterrows():
        if row.get("ebitda_pct", 0) >= 0.22:
            strong_regions.append(row["region"])
    if strong_regions:
        wins.append({
            "title": f"📍 Strong Regions: {', '.join(strong_regions)}",
            "body": f"These regions cleared the 22% EBITDA threshold this period, showing mature unit economics and disciplined cost management.",
            "tag": "22%+ EBITDA", "tag_cls": "green",
        })

    if ps["labor_pct"] < 0.22:
        wins.append({
            "title": "✅ System Labor Under Control",
            "body": f"System-wide Total Labor & Benefits at {_fmt_p(ps['labor_pct'])} — within the 22% target ceiling. Hourly labor at {_fmt_p(ps['hourly_pct'])} shows scheduling discipline.",
            "tag": f"Target: <22%", "tag_cls": "green",
        })

    # Auto-generate opportunities
    high_labor = ps_stands[ps_stands["Total_Labor_pct"] > 0.30].nlargest(3, "Total_Labor_pct")
    if len(high_labor):
        opps.append({
            "title": f"⚠️ High Labor Outliers ({len(high_labor)} stands > 30%)",
            "body": f"Top offender: {high_labor.iloc[0]['Stand']} at {_fmt_p(high_labor.iloc[0]['Total_Labor_pct'])} Total Labor. With {_fmt_d(high_labor.iloc[0]['Net_Sales'])} in sales, EBITDA is compressed to {_fmt_p(high_labor.iloc[0]['Store_EBITDA_pct'])}. Pull scheduling data and compare with similar-volume stands.",
            "tag": "Labor Risk", "tag_cls": "red",
        })

    high_disc = ps_stands.nlargest(3, "Discounts_pct")
    if high_disc.iloc[0]["Discounts_pct"] > 0.04:
        opps.append({
            "title": f"💸 Discount Rate Alert: {high_disc.iloc[0]['Stand'].split(',')[0]}",
            "body": f"Discount rate of {_fmt_p(high_disc.iloc[0]['Discounts_pct'])} is {_fmt_p(high_disc.iloc[0]['Discounts_pct'] - 0.028)} above the 2.8% system avg. Investigate POS config and unauthorized promotion use.",
            "tag": "Discount Risk", "tag_cls": "red",
        })

    low_ebitda = ps_stands[ps_stands["Store_EBITDA_pct"] < 0.10]
    if len(low_ebitda):
        opps.append({
            "title": f"🔴 Below-Floor EBITDA ({len(low_ebitda)} stands < 10%)",
            "body": f"Stands below 10% EBITDA need immediate attention. Common root causes: high labor (>{_fmt_p(low_ebitda['Total_Labor_pct'].mean())} avg), sub-scale sales volume, or high fixed cost absorption.",
            "tag": "<10% EBITDA", "tag_cls": "red",
        })

    high_rm = ps_stands[ps_stands["Total_RM_pct"] > 0.02].nlargest(3, "Total_RM_pct")
    if len(high_rm):
        opps.append({
            "title": f"🔧 R&M Spike Watch ({len(high_rm)} stands > 2%)",
            "body": f"Top: {high_rm.iloc[0]['Stand'].split(',')[0]} at {_fmt_p(high_rm.iloc[0]['Total_RM_pct'])} R&M. Elevated R&M suggests equipment issues or deferred maintenance. Correlate with stand age and equipment vintage.",
            "tag": "R&M Risk", "tag_cls": "amber",
        })

    col1, col2 = st.columns(2)
    with col1:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#12a06e;margin-bottom:10px;">🏆 WINS</div>')
        for w in wins:
            insight_card(w["title"], w["body"], w.get("tag",""), w.get("tag_cls","green"), "win")
    with col2:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#cd2128;margin-bottom:10px;">⚠ OPPORTUNITIES</div>')
        for o in opps:
            insight_card(o["title"], o["body"], o.get("tag",""), o.get("tag_cls","red"))


# ─────────────────────────────────────────────
# TAB: FORECAST
# ─────────────────────────────────────────────
def tab_forecast(dash):
    section("FORECAST P3–P13 2026", "2025 actuals as baseline · 3 scenarios · Seasonal watch notes")

    fc = dash.get("forecast_26", [])
    if not fc:
        st.info("No forecast data available.")
        return

    fc_df = pd.DataFrame(fc)
    periods_df = get_periods_df(dash)

    # Forecast chart
    actuals  = fc_df[fc_df["is_actual"] == True]
    forecast = fc_df[fc_df["is_actual"] == False]

    col1, col2 = st.columns([3, 2])
    with col1:
        fig = go.Figure()
        if not actuals.empty:
            fig.add_bar(x=actuals["period"], y=actuals["ebitda_base"] * 100,
                        name="2026 Actual EBITDA%", marker_color=DARK, yaxis="y2")
        if not forecast.empty:
            fig.add_bar(x=forecast["period"], y=forecast["ns_base"],
                        name="Base Forecast Sales", marker_color=BLUE, opacity=0.7)
            fig.add_bar(x=forecast["period"], y=forecast["ns_opt"],
                        name="Optimistic Sales", marker_color=GREEN, opacity=0.5)
            fig.add_bar(x=forecast["period"], y=forecast["ns_risk"],
                        name="Risk Sales", marker_color=RED, opacity=0.4)
            fig.add_scatter(x=forecast["period"], y=forecast["ebitda_base"] * 100,
                            name="Base EBITDA%", mode="lines+markers",
                            line=dict(color=DARK, width=2), marker=dict(size=6), yaxis="y2")
        fig.update_layout(
            barmode="group",
            yaxis=dict(tickprefix="$", tickformat=",.0f", title="Avg Sales/Stand"),
            yaxis2=dict(title="EBITDA %", overlaying="y", side="right",
                        ticksuffix="%", range=[0, 35]),
        )
        brew_fig(fig, height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        # Prior year comparison
        sa = dash.get("seasonal_actuals", {})
        sa_rows = []
        for pk, vals in sa.items():
            sa_rows.append({"period_key": pk, **vals})
        if sa_rows:
            sa_df = pd.DataFrame(sa_rows).sort_values("period_key")
            fig2 = go.Figure()
            fig2.add_scatter(x=sa_df["period_key"].str.replace("2025_", ""),
                             y=sa_df["ebitda_pct"] * 100,
                             mode="lines+markers", name="2025 EBITDA%",
                             line=dict(color=MID, dash="dot"), marker=dict(size=5))
            if not forecast.empty:
                fig2.add_scatter(x=forecast["period"],
                                 y=forecast["ebitda_base"] * 100,
                                 mode="lines+markers", name="2026 Base",
                                 line=dict(color=RED, width=2), marker=dict(size=6))
            brew_fig(fig2, height=300)
            fig2.update_layout(title_text="2025 vs 2026 EBITDA%",
                               title_font=dict(family="Bebas Neue", size=14),
                               yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Forecast table
    st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#2d2f36;margin:16px 0 8px;">PERIOD-BY-PERIOD FORECAST TABLE</div>')
    watchpts = {
        "P1":"Winter floor — manage labor vs minimum staffing",
        "P2":"Early spring — discount audit; COGS relief as volume ramps",
        "P3":"Spring momentum — new stand ramp watch",
        "P4":"Spring peak — lock vendor pricing, strong sales window",
        "P5":"Strong period — loyalty driving; watch discounts",
        "P6":"Summer start — utility costs rise, vacation labor risk",
        "P7":"Peak summer — quality + speed; manage call-outs",
        "P8":"Late summer — back-to-school shift",
        "P9":"Fall shoulder — volume moderates; good for R&M catch-up",
        "P10":"Steady fall — new stand pipeline; plan training resources",
        "P11":"Holiday ramp — marketing spend critical",
        "P12":"Pre-holiday slowdown — cost control",
        "P13":"Year-end close — no deferred expenses; prep 2027 plan",
    }
    fc_display = fc_df[["period", "is_actual", "ns_base", "ns_opt", "ns_risk",
                          "ebitda_base", "ebitda_opt", "ebitda_risk",
                          "prior_yr_sales", "prior_yr_ebitda"]].copy()
    fc_display["Watch Note"] = fc_display["period"].map(lambda p: watchpts.get(p, ""))
    fc_display["Type"]       = fc_display["is_actual"].map(lambda v: "★ Actual" if v else "Forecast")
    for col in ["ns_base", "ns_opt", "ns_risk", "prior_yr_sales"]:
        fc_display[col] = fc_display[col].map(lambda v: f"${v:,.0f}")
    for col in ["ebitda_base", "ebitda_opt", "ebitda_risk", "prior_yr_ebitda"]:
        fc_display[col] = fc_display[col].map(lambda v: f"{v*100:.1f}%")
    fc_display = fc_display.drop(columns=["is_actual"])
    fc_display.columns = ["Period", "Base Sales", "Opt Sales", "Risk Sales",
                           "Base EBITDA%", "Opt EBITDA%", "Risk EBITDA%",
                           "Prior Yr Sales", "Prior Yr EBITDA%", "Watch Note", "Type"]
    st.dataframe(fc_display[["Type", "Period", "Prior Yr Sales", "Prior Yr EBITDA%",
                               "Base Sales", "Base EBITDA%", "Opt EBITDA%", "Risk EBITDA%",
                               "Watch Note"]],
                 hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# TAB: POTHOLE WATCH
# ─────────────────────────────────────────────
def tab_potholes(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)
    section("⚠ POTHOLE WATCH", "Forward-looking risks — act before they become a crisis")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}
    sel_lbl = st.selectbox("Analyze Period", [l for l, _ in all_options], key="pot_period")
    pk = label_to_key[sel_lbl]
    ps_stands = stands_df[stands_df["Period_Key"] == pk]
    if ps_stands.empty:
        st.info("No data for this period.")
        return

    ps = periods_df[periods_df["period_key"] == pk].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#cd2128;margin-bottom:10px;">🚨 CRITICAL ISSUES</div>')

        top_disc  = ps_stands.nlargest(1, "Discounts_pct").iloc[0]
        top_labor = ps_stands.nlargest(1, "Total_Labor_pct").iloc[0]
        worst_ebi = ps_stands.nsmallest(1, "Store_EBITDA_pct").iloc[0]
        top_rm    = ps_stands.nlargest(1, "Total_RM_pct").iloc[0]

        insight_card(
            f"🚨 Highest Discount Rate: {top_disc['Stand'].split(',')[0]}",
            f"{_fmt_p(top_disc['Discounts_pct'])} discount rate — {top_disc['Discounts_pct']/0.028:.1f}× the 2.8% system avg. "
            f"Possible POS mis-config or unauthorized promos. Direct EBITDA impact.",
            tag=_fmt_p(top_disc['Discounts_pct']), tag_cls="red",
        )
        insight_card(
            f"🚨 Highest Labor Rate: {top_labor['Stand'].split(',')[0]}",
            f"{_fmt_p(top_labor['Total_Labor_pct'])} Total Labor on {_fmt_d(top_labor['Net_Sales'])} sales. "
            f"EBITDA compressed to {_fmt_p(top_labor['Store_EBITDA_pct'])}. "
            f"Pull scheduling report and compare vs similar-volume stands.",
            tag=_fmt_p(top_labor['Total_Labor_pct']), tag_cls="red",
        )
        insight_card(
            f"🚨 Lowest Store EBITDA: {worst_ebi['Stand'].split(',')[0]}",
            f"Generating {_fmt_p(worst_ebi['Store_EBITDA_pct'])} EBITDA on {_fmt_d(worst_ebi['Net_Sales'])} sales. "
            f"Root causes: Labor {_fmt_p(worst_ebi['Total_Labor_pct'])}, COGS {_fmt_p(worst_ebi['Total_COGS_pct'])}.",
            tag=_fmt_p(worst_ebi['Store_EBITDA_pct']), tag_cls="red",
        )
        if top_rm["Total_RM_pct"] > 0.02:
            insight_card(
                f"🚨 Highest R&M: {top_rm['Stand'].split(',')[0]}",
                f"{_fmt_p(top_rm['Total_RM_pct'])} R&M — {top_rm['Total_RM_pct']/0.011:.1f}× system avg. "
                f"Equipment issues or deferred maintenance catch-up. Correlate with stand age.",
                tag=_fmt_p(top_rm['Total_RM_pct']), tag_cls="amber",
            )

    with col2:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#e8940a;margin-bottom:10px;">⚠ WATCH ITEMS</div>')
        watch_items = [
            ("⚠ FL-SW Region: Structural Labor Risk",
             "FL-SW has averaged 28%+ Total Labor & Benefits across most 2025 periods. A persistent 550bps gap vs system avg. Bradenton FL-2 and Belleview FL-1 are chronic outliers.",
             "28%+ avg", "amber"),
            ("⚠ WTX New Opens: Regional Ramp Pattern",
             "Levelland, Dumas, and Plainview showing below-target ramp performance. Average ~$112k sales and 30%+ labor. This is a regional opening model issue, not isolated incidents.",
             "~30%+ Labor", "amber"),
            ("⚠ Summer Labor P6–P8",
             "2025 data shows P6–P8 EBITDA compressed to 16–20% vs 22–24% in P3–P5. Vacation coverage, call-outs, and new stand training overlap create labor creep every summer.",
             "Forward Risk", "amber"),
            ("⚠ P12–P13 Year-End Pattern",
             "2025 P12 EBITDA was 14.4% and P13 was 11.5% — holiday fixed cost absorption and reduced traffic. 2026 P12–P13 will face same pressure. Plan ahead.",
             "Seasonal Risk", "amber"),
            ("⚠ H2 2026 New Stand Pipeline",
             "10+ new locations planned for H2 2026. Each carries 25–35% labor for 60–90 days. System EBITDA% will be diluted 150–200bps per cohort.",
             "~150–200bps dilution", "grey"),
            ("⚠ R&M Aging Stand Watch",
             "Stands opened 2022–2023 are now 2–3 years old. 2025 data shows R&M% creeping up in P11–P13. Any stand over 2.0% R&M should have an equipment condition audit.",
             "Equipment Risk", "grey"),
        ]
        for title, body, tag, tag_cls in watch_items:
            insight_card(title, body, tag, tag_cls, "watch")


# ─────────────────────────────────────────────
# TAB: UTILITIES & R&M
# ─────────────────────────────────────────────
def tab_utilities(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)
    section("UTILITIES & R&M", "Period-over-period cost trends · Seasonality · Opportunity flags")

    # Detect if sub-category data is available
    has_elec  = "Electricity" in stands_df.columns and stands_df["Electricity"].sum() > 0
    has_water = "Water_Sewer" in stands_df.columns and stands_df["Water_Sewer"].sum() > 0
    has_waste = "Waste_Removal" in stands_df.columns and stands_df["Waste_Removal"].sum() > 0
    has_rm_eq = "RM_Equipment" in stands_df.columns and stands_df["RM_Equipment"].sum() > 0
    has_rm_bld= "RM_Building" in stands_df.columns and stands_df["RM_Building"].sum() > 0
    has_detail = any([has_elec, has_water, has_waste, has_rm_eq, has_rm_bld])

    if not has_detail:
        st.html("""
        <div class="info-box">
          <strong>📤 Upload P&L files to unlock detailed utility breakdowns.</strong><br>
          The charts below show Total Utilities & Total R&M from embedded period data.
          Upload 7BREW PTD Side By Side Excel files via the sidebar to add
          Electricity, Water & Sewer, Waste Removal, R&M Equipment, and R&M Building
          breakdowns per period.
        </div>""")

    # ── Total Utilities & R&M PoP ──
    pct_df = periods_df.copy()
    pct_df["util_$"] = pct_df["utilities_pct"] * pct_df["net_sales"]
    pct_df["rm_$"]   = pct_df["rm_pct"] * pct_df["net_sales"]

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_bar(x=pct_df["label"], y=pct_df["util_$"] / 1000,
                    name="Total Utilities ($k)", marker_color=BLUE, opacity=0.8)
        fig.add_scatter(x=pct_df["label"], y=pct_df["utilities_pct"] * 100,
                        name="Utilities % (right)", mode="lines+markers",
                        line=dict(color=RED, width=2), marker=dict(size=5),
                        yaxis="y2")
        fig.update_layout(
            yaxis=dict(title="Total Utilities ($k)", tickprefix="$", ticksuffix="k"),
            yaxis2=dict(title="% of Net Sales", overlaying="y", side="right",
                        ticksuffix="%", tickfont=dict(size=9, color=RED)),
        )
        brew_fig(fig, height=280)
        fig.update_layout(title_text="TOTAL UTILITIES — PERIOD OVER PERIOD",
                          title_font=dict(family="Bebas Neue", size=14),
                          xaxis=dict(tickangle=-35))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        fig2 = go.Figure()
        fig2.add_bar(x=pct_df["label"], y=pct_df["rm_$"] / 1000,
                     name="Total R&M ($k)", marker_color=AMBER, opacity=0.8)
        fig2.add_scatter(x=pct_df["label"], y=pct_df["rm_pct"] * 100,
                         name="R&M % (right)", mode="lines+markers",
                         line=dict(color=DARK, width=2), marker=dict(size=5),
                         yaxis="y2")
        fig2.update_layout(
            yaxis=dict(title="Total R&M ($k)", tickprefix="$", ticksuffix="k"),
            yaxis2=dict(title="% of Net Sales", overlaying="y", side="right",
                        ticksuffix="%", tickfont=dict(size=9, color=DARK)),
        )
        brew_fig(fig2, height=280)
        fig2.update_layout(title_text="TOTAL R&M — PERIOD OVER PERIOD",
                           title_font=dict(family="Bebas Neue", size=14),
                           xaxis=dict(tickangle=-35))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.html('<hr class="brew">')

    # ── Sub-category detail (from uploads) OR placeholder ──
    if has_detail:
        # Build per-period sub-category aggregates from stand_records
        sub_cols = {}
        if has_elec:  sub_cols["Electricity"]  = "Electricity"
        if has_water: sub_cols["Water_Sewer"]   = "Water & Sewer"
        if has_waste: sub_cols["Waste_Removal"] = "Waste Removal"

        agg_dict = {col: "sum" for col in sub_cols}
        agg_dict["Net_Sales"] = "sum"
        sub_df = stands_df.groupby("Period_Key").agg(agg_dict).reset_index()
        sub_df = sub_df.merge(periods_df[["period_key", "label"]], left_on="Period_Key", right_on="period_key")
        sub_df = sub_df.sort_values(["period_key"])

        cols_left, cols_right = st.columns(2)
        col_list = [cols_left, cols_right]

        chart_idx = 0
        for field, display_name in sub_cols.items():
            if field not in sub_df.columns:
                continue
            with col_list[chart_idx % 2]:
                fig = go.Figure()
                fig.add_bar(x=sub_df["label"], y=sub_df[field] / 1000,
                            marker_color=[BLUE, GREEN, RED, AMBER, MID, DARK][chart_idx % 6],
                            opacity=0.8, name=f"{display_name} ($k)")
                # Add % line
                sub_df[f"{field}_pct"] = sub_df[field] / sub_df["Net_Sales"]
                fig.add_scatter(x=sub_df["label"], y=sub_df[f"{field}_pct"] * 100,
                                mode="lines+markers", name="% of Sales",
                                line=dict(color=RED, width=1.5, dash="dot"),
                                marker=dict(size=5), yaxis="y2")
                fig.update_layout(
                    yaxis=dict(title=f"{display_name} ($k)", tickprefix="$", ticksuffix="k"),
                    yaxis2=dict(title="% of Sales", overlaying="y", side="right",
                                ticksuffix="%", tickfont=dict(size=9, color=RED)),
                )
                brew_fig(fig, height=260)
                fig.update_layout(title_text=f"{display_name.upper()} — PERIOD OVER PERIOD",
                                  title_font=dict(family="Bebas Neue", size=14),
                                  xaxis=dict(tickangle=-35))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                # Spike detection for Waste Removal
                if field == "Waste_Removal":
                    median_val = sub_df[field].median()
                    spikes = sub_df[sub_df[field] > median_val * 1.5]
                    if not spikes.empty:
                        st.html(f"""
                        <div class="info-box">
                          <strong>🗑 Waste Removal Spike Detected</strong> — {', '.join(spikes['label'].tolist())}
                          show 1.5× above median. This may indicate overage charges (3× pickup frequency or
                          volume overage fees). Review pickup schedule and container sizing for these periods.
                        </div>""")
            chart_idx += 1

        # R&M sub-categories
        st.html('<hr class="brew">')
        rm_cols = {}
        if has_rm_eq:  rm_cols["RM_Equipment"] = "R&M Equipment"
        if has_rm_bld: rm_cols["RM_Building"]  = "R&M Building"

        if rm_cols:
            rm_agg = {col: "sum" for col in rm_cols}
            rm_agg["Net_Sales"] = "sum"
            rm_sub = stands_df.groupby("Period_Key").agg(rm_agg).reset_index()
            rm_sub = rm_sub.merge(periods_df[["period_key", "label"]], left_on="Period_Key", right_on="period_key")
            rm_sub = rm_sub.sort_values("period_key")

            cols3, cols4 = st.columns(2)
            for idx, (field, display_name) in enumerate(rm_cols.items()):
                with (cols3 if idx == 0 else cols4):
                    fig = go.Figure()
                    fig.add_bar(x=rm_sub["label"], y=rm_sub[field] / 1000,
                                marker_color=[AMBER, MID][idx], opacity=0.8, name=f"{display_name} ($k)")
                    rm_sub[f"{field}_pct"] = rm_sub[field] / rm_sub["Net_Sales"]
                    fig.add_scatter(x=rm_sub["label"], y=rm_sub[f"{field}_pct"] * 100,
                                    mode="lines+markers", name="% of Sales",
                                    line=dict(color=RED, width=1.5, dash="dot"),
                                    marker=dict(size=5), yaxis="y2")
                    fig.update_layout(
                        yaxis=dict(title=f"{display_name} ($k)", tickprefix="$", ticksuffix="k"),
                        yaxis2=dict(title="% of Sales", overlaying="y", side="right",
                                    ticksuffix="%", tickfont=dict(size=9, color=RED)),
                    )
                    brew_fig(fig, height=260)
                    fig.update_layout(title_text=f"{display_name.upper()} — PERIOD OVER PERIOD",
                                      title_font=dict(family="Bebas Neue", size=14),
                                      xaxis=dict(tickangle=-35))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    else:
        # Placeholder sub-category grid
        sub_metrics = [
            ("⚡ Electricity", "electricity_pct"),
            ("💧 Water & Sewer", None),
            ("🗑 Waste Removal", None),
            ("🔧 R&M Equipment", None),
            ("🏗 R&M Building", None),
        ]
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#2d2f36;margin-bottom:12px;">SUB-CATEGORY DETAIL — UPLOAD P&L FILES TO ACTIVATE</div>')
        cols_p = st.columns(5)
        for i, (name, _) in enumerate(sub_metrics):
            with cols_p[i]:
                st.html(f"""
                <div class="kpi-card grey" style="text-align:center;opacity:0.5;">
                  <div style="font-size:20px;margin-bottom:6px;">{name.split()[0]}</div>
                  <div class="kpi-label">{' '.join(name.split()[1:])}</div>
                  <div class="kpi-value" style="font-size:18px;color:#8a919e;">—</div>
                  <div class="kpi-sub">Upload P&L to activate</div>
                </div>""")

    st.html('<hr class="brew">')

    # ── Seasonality Analysis ──
    section("SEASONALITY ANALYSIS", "How period of year drives utility & R&M costs")
    col5, col6 = st.columns(2)
    with col5:
        # Utilities % by period (seasonality pattern)
        fig = go.Figure()
        fig.add_scatter(x=pct_df["label"], y=pct_df["utilities_pct"] * 100,
                        mode="lines+markers+text",
                        text=pct_df["utilities_pct"].map(lambda v: f"{v*100:.1f}%"),
                        textposition="top center",
                        textfont=dict(size=8),
                        fill="tozeroy",
                        fillcolor=f"rgba(29,111,207,0.08)",
                        line=dict(color=BLUE, width=2),
                        marker=dict(size=6, color=[
                            RED if i in [5,6,7] else (AMBER if i in [4,8] else BLUE)
                            for i in range(len(pct_df))
                        ]),
                        name="Utilities %")
        brew_fig(fig, height=260)
        fig.update_layout(title_text="UTILITIES % BY PERIOD (SEASONALITY)",
                          title_font=dict(family="Bebas Neue", size=14),
                          yaxis=dict(ticksuffix="%"),
                          xaxis=dict(tickangle=-35), showlegend=False)
        # Add summer annotation
        summer_idxs = [i for i, lbl in enumerate(pct_df["label"]) if any(x in str(lbl) for x in ["P6","P7","P8"])]
        if summer_idxs:
            mid_lbl = pct_df.iloc[summer_idxs[len(summer_idxs)//2]]["label"]
            fig.add_annotation(x=mid_lbl, y=pct_df["utilities_pct"].max()*100*1.05,
                               text="☀️ Summer Peak", showarrow=False,
                               font=dict(size=9, color=RED, family="DM Mono"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col6:
        fig2 = go.Figure()
        fig2.add_scatter(x=pct_df["label"], y=pct_df["rm_pct"] * 100,
                         mode="lines+markers+text",
                         text=pct_df["rm_pct"].map(lambda v: f"{v*100:.2f}%"),
                         textposition="top center",
                         textfont=dict(size=8),
                         fill="tozeroy",
                         fillcolor=f"rgba(232,148,10,0.08)",
                         line=dict(color=AMBER, width=2),
                         marker=dict(size=6),
                         name="R&M %")
        # Add trend line
        import numpy as np
        x_num = list(range(len(pct_df)))
        z = np.polyfit(x_num, pct_df["rm_pct"] * 100, 1)
        p = np.poly1d(z)
        fig2.add_scatter(x=pct_df["label"], y=[p(xi) for xi in x_num],
                         mode="lines", name="Trend",
                         line=dict(color=RED, dash="dot", width=1.5))
        brew_fig(fig2, height=260)
        fig2.update_layout(title_text="R&M % BY PERIOD (WITH TREND)",
                           title_font=dict(family="Bebas Neue", size=14),
                           yaxis=dict(ticksuffix="%"),
                           xaxis=dict(tickangle=-35))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Opportunity Flags ──
    st.html('<hr class="brew">')
    section("OPPORTUNITY FLAGS", "Data-driven cost reduction opportunities")

    # Find highest utility periods
    top_util = pct_df.nlargest(3, "utilities_pct")
    low_util  = pct_df.nsmallest(1, "utilities_pct").iloc[0]
    rm_trend  = pct_df["rm_pct"].iloc[-3:].mean() - pct_df["rm_pct"].iloc[:3].mean()

    opp_col1, opp_col2 = st.columns(2)
    with opp_col1:
        insight_card(
            f"☀️ Seasonal Utility Peaks: {', '.join(top_util['label'].tolist())}",
            f"Utility costs peak in summer (P6–P8) at up to {_fmt_p(top_util['utilities_pct'].max())} of net sales "
            f"vs {_fmt_p(low_util['utilities_pct'])} in the low-water period ({low_util['label']}). "
            f"Opportunity: chiller pre-maintenance before P5, LED lighting upgrades, and smart thermostat "
            f"schedules can reduce summer utility by 10–15%.",
            tag="Seasonal Opportunity", tag_cls="amber", card_cls="watch",
        )
        insight_card(
            "💧 Water & Sewer — Days-in-Period Impact",
            "Utility costs fluctuate with the number of days in a period (some 7BREW periods are 28 days, "
            "others 35+). Normalize utility expense to $/day/stand rather than % of sales for a "
            "cleaner comparison. A spike in Waste Removal % could be an overage charge, not "
            "increased volume.",
            tag="Measurement Tip", tag_cls="grey", card_cls="watch",
        )
    with opp_col2:
        rm_direction = "increasing" if rm_trend > 0 else "decreasing"
        insight_card(
            f"🔧 R&M Trend: {rm_direction.title()} Over the Dataset",
            f"R&M % has {'risen' if rm_trend > 0 else 'fallen'} by {abs(rm_trend)*100:.2f}% pts from early to recent periods. "
            f"{'This aligns with the aging equipment cycle for stands opened 2022–2023. Schedule preventive maintenance in P9–P11 before it becomes reactive.' if rm_trend > 0 else 'Positive trend — newer stands have lower R&M. Monitor as the network ages.'}",
            tag=f"Δ {'+' if rm_trend>0 else ''}{rm_trend*100:.2f}% pts", tag_cls="amber" if rm_trend > 0 else "green",
            card_cls="watch" if rm_trend > 0 else "win",
        )
        insight_card(
            "🗑 Waste Removal: 2–3x Pickup Schedule",
            "Waste Removal is typically charged per pickup (2–3x/week). If a period contains an extra pickup "
            "cycle due to calendar length or overage fees, the cost will spike. Flag any period where Waste "
            "Removal exceeds 1.5× the median value — this indicates an overage charge rather than "
            "normal operations.",
            tag="Spike Detector Active" if has_waste else "Upload P&L to Activate",
            tag_cls="green" if has_waste else "grey",
            card_cls="win" if has_waste else "watch",
        )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    # Sidebar
    with st.sidebar:
        render_sidebar()

    # Get data (base + any uploads)
    dash = get_dash()

    # Header
    st.html("""
    <div style="display:flex;align-items:center;gap:12px;padding-bottom:12px;
                border-bottom:2px solid #cd2128;margin-bottom:16px;">
      <div style="background:#cd2128;color:white;font-family:'Bebas Neue',sans-serif;
                  font-size:22px;letter-spacing:1px;padding:4px 12px;border-radius:6px;">7BREW</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:18px;letter-spacing:3px;
                  color:#5a6070;text-transform:uppercase;">Financial Performance Dashboard</div>
      <div style="margin-left:auto;font-family:'DM Mono',monospace;font-size:10px;color:#8a919e;">
        FY2025–2026 · 15 Periods · Confidential
      </div>
    </div>""")

    # Tabs
    tab_names = [
        "📊 CEO Snapshot",
        "🏠 Overview",
        "📈 Period Comparison",
        "🏪 Stand Detail",
        "🗺 Regions",
        "💡 Wins & Opportunities",
        "🔮 Forecast",
        "⚠️ Pothole Watch",
        "⚡ Utilities & R&M",
    ]
    tabs = st.tabs(tab_names)

    with tabs[0]: tab_ceo(dash)
    with tabs[1]: tab_overview(dash)
    with tabs[2]: tab_comparison(dash)
    with tabs[3]: tab_stands(dash)
    with tabs[4]: tab_regions(dash)
    with tabs[5]: tab_insights(dash)
    with tabs[6]: tab_forecast(dash)
    with tabs[7]: tab_potholes(dash)
    with tabs[8]: tab_utilities(dash)


main()
