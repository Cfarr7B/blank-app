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
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# DESIGN TOKENS & THEME
# ─────────────────────────────────────────────
RED    = "#AC2430"   # 7BREW primary brand red  (172, 36, 48)
PINK   = "#FFBDBD"   # light red tint           (255, 189, 189)
GREEN  = "#12a06e"
BLUE   = "#1d6fcf"
DARK   = "#1A1919"   # near black               (26, 25, 25)
MID    = "#595959"   # mid gray                 (89, 89, 89)
MUTED  = "#C5BEBE"   # warm light gray          (197, 190, 190)
AMBER  = "#e8940a"
BORDER = "#e2e4e9"
BODY   = "#1A1919"   # near black body text     (26, 25, 25)
SUB    = "#595959"
BG     = "#ffffff"
BG2    = "#f5f6f8"
GRID   = "rgba(0,0,0,0.055)"

REGION_COLORS = {
    # Full region names (current)
    "North Central TX":   "#1d6fcf",
    "South Central TX":   "#2980b9",
    "FL Panhandle East":  "#12a06e",
    "FL Panhandle West":  "#1a8c5c",
    "FL West Coast":      "#0e7a6e",
    "Middle Earth":       "#7c3aed",
    "NM":                 "#c2410c",
    "CO":                 "#a16207",
    "North OK":           "#AC2430",
    "Central OK":         "#9b1a1f",
    "South OK":           "#7f1d1d",
    "Permian Basin":      "#e8940a",
    "West TX":            "#d97706",
    # Legacy abbreviations (backward compat)
    "CTX-N": "#1d6fcf", "CTX-S": "#2980b9", "FL-P": "#12a06e",
    "FL-P1": "#1a8c5c", "FL-SW": "#0e7a6e",
    "OKC-N": "#AC2430", "OKC-S": "#9b1a1f", "WTX": "#d97706",
}

# Inject Google Fonts + minimal custom component styling
st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  /* Global font family */
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
  h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px; }

  /* KPI cards (custom HTML) */
  .kpi-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
  .kpi-card {
    background: white; border: 1px solid #e2e4e9; border-radius: 10px;
    padding: 16px 18px; flex: 1 1 170px; min-width: 160px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05); position: relative; overflow: hidden;
  }
  .kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; }
  .kpi-card.red::before { background:#AC2430; }
  .kpi-card.green::before { background:#12a06e; }
  .kpi-card.blue::before { background:#1d6fcf; }
  .kpi-card.amber::before { background:#e8940a; }
  .kpi-card.grey::before { background:#595959; }
  .kpi-label { font-size:17px; font-weight:700; letter-spacing:1px;
    text-transform:uppercase; color:#595959; margin-bottom:6px; }
  .kpi-value { font-family:'Bebas Neue',sans-serif; font-size:39px;
    line-height:1; color:#1A1919; letter-spacing:1px; }
  .kpi-value.good { color:#12a06e; }
  .kpi-value.bad { color:#AC2430; }
  .kpi-value.warn { color:#e8940a; }
  .kpi-sub { font-family:'DM Mono',monospace; font-size:17px; color:#C5BEBE; margin-top:4px; }
  .kpi-delta { display:inline-block; font-family:'DM Mono',monospace;
    font-size:17px; font-weight:600; padding:2px 7px; border-radius:10px; margin-top:5px; }
  .kpi-delta.up { background:rgba(18,160,110,0.1); color:#12a06e; }
  .kpi-delta.down { background:rgba(172,36,48,0.1); color:#AC2430; }
  .kpi-delta.neut { background:rgba(29,111,207,0.1); color:#1d6fcf; }

  /* Section headers */
  .section-hdr {
    font-family:'Bebas Neue',sans-serif; font-size:34px; letter-spacing:3px;
    color:#1A1919; margin-bottom:2px; margin-top:8px;
    display:flex; align-items:center; gap:8px;
  }
  .section-hdr::before { content:''; width:6px; height:6px; border-radius:50%;
    background:#AC2430; display:inline-block; flex-shrink:0; }
  .section-sub { font-family:'DM Mono',monospace; font-size:14px;
    color:#C5BEBE; margin-bottom:16px; margin-left:14px; }
  .red-rule { width:36px; height:3px; background:#AC2430;
    border-radius:2px; margin-bottom:18px; margin-left:14px; }

  /* Insight / alert cards */
  .insight-card {
    background:white; border:1px solid #e2e4e9; border-radius:10px;
    padding:16px 18px; margin-bottom:10px; border-left: 4px solid #AC2430;
  }
  .insight-card.win { border-left-color: #12a06e; }
  .insight-card.watch { border-left-color: #e8940a; }
  .insight-card .ic-title { font-weight:700; font-size:17px; color:#1A1919; margin-bottom:4px; }
  .insight-card .ic-body { font-size:16px; color:#595959; line-height:1.6; }
  .insight-card .ic-tag { display:inline-block; font-family:'DM Mono',monospace;
    font-size:17px; padding:2px 8px; border-radius:10px; margin-top:6px; }
  .ic-tag.red { background:rgba(172,36,48,0.1); color:#AC2430; }
  .ic-tag.green { background:rgba(18,160,110,0.1); color:#12a06e; }
  .ic-tag.amber { background:rgba(232,148,10,0.1); color:#e8940a; }
  .ic-tag.grey { background:rgba(90,96,112,0.1); color:#595959; }

  /* Utility / R&M info box */
  .info-box {
    background:#f5f6f8; border:1px solid #e2e4e9; border-radius:10px;
    padding:14px 18px; font-size:16px; color:#595959; margin-bottom:16px;
  }
  .info-box strong { color:#1A1919; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #f5f6f8 !important;
    border-right: 1px solid #e2e4e9;
    display: block !important;
    visibility: visible !important;
  }

  /* Divider */
  hr.brew { border:none; border-top:1px solid #e2e4e9; margin:20px 0; }

  /* Story block */
  .story-block {
    background:white; border:1px solid #e2e4e9; border-radius:10px;
    padding:20px 24px; margin-bottom:16px; box-shadow:0 1px 4px rgba(0,0,0,0.04);
  }
  .story-label { font-family:'DM Mono',monospace; font-size:17px;
    text-transform:uppercase; letter-spacing:1px; color:#C5BEBE; margin-bottom:6px; }
  .story-headline { font-family:'Bebas Neue',sans-serif; font-size:34px;
    letter-spacing:1.5px; color:#AC2430; margin-bottom:8px; }
  .story-body { font-size:17px; color:#595959; line-height:1.7; }

  /* ── Navigation Tabs ─────────────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f5f6f8;
    border: 1px solid #e2e4e9;
    border-radius: 12px;
    padding: 5px 6px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 15px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 9px 20px !important;
    border-radius: 8px !important;
    color: #595959 !important;
    background: transparent !important;
    border: none !important;
    white-space: nowrap !important;
    height: auto !important;
    line-height: 1.2 !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: #1A1919 !important;
    background: rgba(0,0,0,0.05) !important;
  }
  .stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: white !important;
    color: #AC2430 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.10) !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
  .stTabs [data-baseweb="tab-border"]    { display: none !important; }

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

def _fmt_d_short(v):
    """Abbreviated dollar format for KPI cards where space is tight.
    ≥ $1M → $X.XM  |  ≥ $1K → $X.XK  |  otherwise full
    """
    if v is None: return "—"
    v = abs(float(v))
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

def _fmt_p(v, dec=1):
    if v is None: return "—"
    return f"{float(v)*100:.{dec}f}%"

def _fmt_bps(delta):
    b = round(float(delta) * 10000)
    return ("+"+str(b) if b >= 0 else str(b)) + " bps"

def brew_fig(fig, height=320, show_legend=True, margin=None):
    m = margin or dict(t=60, b=60, l=8, r=8)
    # Use title dict with explicit text="" to avoid Plotly rendering "undefined"
    # on charts that never receive a title_text. Individual update_layout calls
    # below will override the text when a real title is needed.
    existing_title = (fig.layout.title.text or "") if fig.layout.title.text is not None else ""
    fig.update_layout(
        height=height, paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", color=BODY, size=15),
        margin=m, showlegend=show_legend,
        legend=dict(font=dict(size=13, color=MID, family="DM Mono")),
        title=dict(
            text=existing_title,
            font=dict(size=16, color=BODY, family="Bebas Neue, sans-serif"),
        ),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=BORDER,
                     tickfont=dict(size=13, color=MID, family="DM Mono"),
                     title_font=dict(size=14, color=BODY))
    fig.update_yaxes(gridcolor=GRID, linecolor=BORDER,
                     tickfont=dict(size=13, color=MID, family="DM Mono"),
                     title_font=dict(size=14, color=BODY))
    # Make data labels larger
    for trace in fig.data:
        if hasattr(trace, 'textfont'):
            trace.textfont = dict(size=12, family="DM Mono")
    return fig

def period_multiselect(periods_df, key, label="Select Period(s)"):
    """Render a multi-select period picker with quarterly preset buttons.
    Returns (list_of_period_keys, aggregated_series_or_None).
    If one period selected, returns that period's row as a Series.
    If multiple, returns a weighted-average aggregation."""

    all_labels = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {lbl: pk for lbl, pk in all_labels}

    selected_labels = st.multiselect(label, [l for l, _ in all_labels],
                                     default=[all_labels[0][0]], key=key)

    selected_keys = [label_to_key[lbl] for lbl in selected_labels if lbl in label_to_key]

    if not selected_keys:
        return [], None, label_to_key

    if len(selected_keys) == 1:
        pk = selected_keys[0]
        ps = periods_df[periods_df["period_key"] == pk].iloc[0]
        return selected_keys, ps, label_to_key

    # Aggregate multiple periods
    subset = periods_df[periods_df["period_key"].isin(selected_keys)].copy()
    total_sales = subset["net_sales"].sum()
    agg = {}
    agg["period_key"] = "+".join(selected_keys)
    agg["label"] = ", ".join(subset["label"].tolist())
    agg["year"] = subset["year"].max()
    agg["period_num"] = subset["period_num"].max()
    agg["stands"] = int(subset["stands"].mean())
    agg["net_sales"] = total_sales
    agg["avg_sales"] = total_sales / subset["stands"].mean() if subset["stands"].mean() > 0 else 0
    agg["ebitda"] = subset["ebitda"].sum()

    # Weighted average for pct columns
    pct_cols = [c for c in subset.columns if c.endswith("_pct")]
    for col in pct_cols:
        if col in subset.columns and total_sales > 0:
            agg[col] = (subset[col] * subset["net_sales"]).sum() / total_sales
        else:
            agg[col] = 0

    return selected_keys, pd.Series(agg), label_to_key

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

def render_table(df, max_rows=None, height=None):
    """Render a pandas DataFrame as a styled HTML table via st.components.v1.html with explicit height."""
    import streamlit.components.v1 as components

    if df.empty:
        st.info("No data to display")
        return

    if max_rows:
        df = df.head(max_rows)

    display_df = df.reset_index(drop=True)

    # Calculate height: header(44px) + rows(37px each) + padding(20px)
    calc_h = height or min(600, 44 + len(display_df) * 37 + 20)

    # Build full HTML document with inline styles
    html = """<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'DM Sans',sans-serif; background:#ffffff; color:#1A1919; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th { background:#f5f6f8; color:#1A1919; padding:10px 12px; text-align:left;
       border-bottom:2px solid #e2e4e9; font-weight:600; white-space:nowrap;
       position:sticky; top:0; z-index:1; }
  td { padding:8px 12px; border-bottom:1px solid #e2e4e9; color:#1A1919; }
  tr:nth-child(even) { background:#fafbfc; }
  tr:nth-child(odd) { background:#ffffff; }
  tr:hover { background:#f0f1f3; }
  .wrap { width:100%; overflow:auto; }
</style>
</head><body><div class="wrap"><table>
<thead><tr>"""

    for col in display_df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"

    for _, row in display_df.iterrows():
        html += "<tr>"
        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"

    html += "</tbody></table></div></body></html>"

    components.html(html, height=calc_h, scrolling=True)

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

def get_upload_dir():
    """Return path to persistent upload storage folder, creating it if needed."""
    upload_dir = Path(__file__).parent / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

def save_uploaded_period(parsed_result):
    """Save a single parsed period as a JSON file for persistence."""
    upload_dir = get_upload_dir()
    pk = parsed_result["period_key"]
    filepath = upload_dir / f"{pk}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(parsed_result, f, default=str)
    return filepath

def load_saved_uploads():
    """Load all previously saved uploaded periods from disk."""
    upload_dir = get_upload_dir()
    saved = []
    for fp in sorted(upload_dir.glob("*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                saved.append(json.load(f))
        except Exception:
            pass
    return saved

def delete_saved_uploads():
    """Remove all saved upload files."""
    upload_dir = get_upload_dir()
    for fp in upload_dir.glob("*.json"):
        fp.unlink()

def save_to_base_data(merged_dash):
    """Permanently write merged data to data.json so it becomes the new base."""
    data_path = Path(__file__).parent / "data.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(merged_dash, f, indent=2, default=str)
    # Clear the cache so load_base_data picks up the new file
    load_base_data.clear()
    # Clear upload temp files since they're now in the base
    delete_saved_uploads()

def get_dash():
    """Return base dashboard data. New periods are added via build_base_data.py."""
    return load_base_data()

QUARTER_MAP = {1: "Q1", 2: "Q1", 3: "Q1", 4: "Q2", 5: "Q2", 6: "Q2",
               7: "Q3", 8: "Q3", 9: "Q3", 10: "Q4", 11: "Q4", 12: "Q4", 13: "Q4"}

def _build_quarterly_summaries(periods_df):
    """Build quarterly roll-up rows from individual period summaries."""
    if periods_df.empty:
        return pd.DataFrame()

    df = periods_df.copy()
    df["quarter"] = df["period_num"].map(QUARTER_MAP)
    df["q_key"] = df["year"].astype(str) + "_" + df["quarter"]

    # Percentage columns are weighted by net_sales
    pct_cols = [c for c in df.columns if c.endswith("_pct")]
    sum_cols = ["net_sales", "ebitda", "stands"]

    quarterly_rows = []
    for q_key, grp in df.groupby("q_key", sort=False):
        year = grp["year"].iloc[0]
        quarter = grp["quarter"].iloc[0]
        total_sales = grp["net_sales"].sum()
        row = {
            "period_key": f"{year}_{quarter}",
            "year": year,
            "period": quarter,
            "label": f"{quarter} '{str(year)[-2:]}",
            "stands": int(grp["stands"].mean()),
            "net_sales": total_sales,
            "avg_sales": total_sales / grp["stands"].mean() if grp["stands"].mean() > 0 else 0,
            "ebitda": grp["ebitda"].sum(),
            "period_num": {"Q1": 100, "Q2": 200, "Q3": 300, "Q4": 400}[quarter],
        }
        # Weighted average for pct columns
        for col in pct_cols:
            if col in grp.columns:
                row[col] = (grp[col] * grp["net_sales"]).sum() / total_sales if total_sales > 0 else 0
        quarterly_rows.append(row)

    return pd.DataFrame(quarterly_rows)

def _build_quarterly_stands(stands_df):
    """Build quarterly aggregated stand records."""
    if stands_df.empty:
        return pd.DataFrame()

    df = stands_df.copy()
    df["period_num"] = df["Period_Key"].apply(lambda x: int(x.split("_P")[1]))
    df["year"] = df["Period_Key"].apply(lambda x: int(x.split("_")[0]))
    df["quarter"] = df["period_num"].map(QUARTER_MAP)
    df["Q_Key"] = df["year"].astype(str) + "_" + df["quarter"]

    # Sum dollar columns, weighted-avg pct columns
    dollar_cols = [c for c in df.columns if c in ["Net_Sales", "Store_EBITDA", "Electricity",
                   "Water_Sewer", "Waste_Removal", "Landscaping", "RM_Equipment", "RM_Building"]]
    pct_cols = [c for c in df.columns if c.endswith("_pct")]

    rows = []
    for (q_key, stand), grp in df.groupby(["Q_Key", "Stand"]):
        row = {"Period_Key": q_key, "Stand": stand}
        # Copy non-numeric fields from first row
        for col in ["Region", "Age_Bucket", "Open_Date"]:
            if col in grp.columns:
                row[col] = grp[col].iloc[0]
        # Sum dollar columns
        for col in dollar_cols:
            if col in grp.columns:
                row[col] = grp[col].sum()
        # Weighted avg pct columns by Net_Sales
        total_sales = grp["Net_Sales"].sum() if "Net_Sales" in grp.columns else 1
        for col in pct_cols:
            if col in grp.columns and total_sales > 0:
                row[col] = (grp[col] * grp["Net_Sales"]).sum() / total_sales
        rows.append(row)

    return pd.DataFrame(rows)

def _build_quarterly_regions(dash):
    """Build quarterly aggregated region data."""
    region_by_period = dash.get("region_by_period", {})
    if not region_by_period:
        return {}

    # Group period keys by quarter
    q_groups = {}
    for pk in region_by_period:
        parts = pk.split("_P")
        if len(parts) != 2:
            continue
        year = int(parts[0])
        pnum = int(parts[1])
        q = QUARTER_MAP.get(pnum)
        if q:
            q_key = f"{year}_{q}"
            if q_key not in q_groups:
                q_groups[q_key] = []
            q_groups[q_key].extend(region_by_period[pk])

    # Aggregate by region within each quarter
    quarterly_regions = {}
    for q_key, rows in q_groups.items():
        rdf = pd.DataFrame(rows)
        if rdf.empty:
            continue
        dollar_cols = [c for c in rdf.columns if c in ["net_sales", "ebitda", "ebitda_total"]]
        pct_cols = [c for c in rdf.columns if c.endswith("_pct")]

        agg_rows = []
        for region, grp in rdf.groupby("region"):
            row = {"region": region}
            total_sales = grp["net_sales"].sum() if "net_sales" in grp.columns else 1
            for col in dollar_cols:
                if col in grp.columns:
                    row[col] = grp[col].sum()
            for col in pct_cols:
                if col in grp.columns and total_sales > 0:
                    row[col] = (grp[col] * grp["net_sales"]).sum() / total_sales
            if "stands" in grp.columns:
                row["stands"] = int(grp["stands"].mean())
            agg_rows.append(row)
        quarterly_regions[q_key] = agg_rows

    return quarterly_regions

def get_periods_df(dash, include_quarters=False):
    df = pd.DataFrame(dash["period_summaries"])
    df["period_num"] = df["period_key"].apply(lambda x: int(x.split("_P")[1]) if "_P" in x else 0)
    df["year"] = df["period_key"].apply(lambda x: int(x.split("_")[0]))
    df.sort_values(["year", "period_num"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    if include_quarters:
        q_df = _build_quarterly_summaries(df)
        if not q_df.empty:
            combined = pd.concat([df, q_df], ignore_index=True)
            combined.sort_values(["year", "period_num"], inplace=True)
            combined.reset_index(drop=True, inplace=True)
            return combined

    return df

def _period_end_date(period_key):
    """Return the end date of a fiscal period (each period = 28 days).
    P1 start dates: 2024 → Jan 1 2024 | 2025 → Dec 30 2024 | 2026 → Dec 29 2025
    """
    import datetime
    P1_STARTS = {
        2024: datetime.date(2024,  1,  1),
        2025: datetime.date(2024, 12, 30),
        2026: datetime.date(2025, 12, 29),
    }
    try:
        year, pnum = int(period_key.split("_")[0]), int(period_key.split("_P")[1])
        p1 = P1_STARTS.get(year)
        if p1 is None:
            return None
        return p1 + datetime.timedelta(days=(pnum - 1) * 28 + 27)  # last day of the period
    except Exception:
        return None

def _assign_age_bucket(open_date_str, period_key):
    """Calculate age bucket from open date and period."""
    import datetime
    if not open_date_str or open_date_str in ("", "nan", "None"):
        return "Unknown"
    try:
        open_date = pd.to_datetime(open_date_str).date()
        period_end = _period_end_date(period_key)
        if period_end is None:
            return "Unknown"
        age_days = (period_end - open_date).days
        if age_days < 0:
            return "Unknown"
        elif age_days < 182:
            return "New (<6mo)"
        elif age_days < 365:
            return "Young (6-12mo)"
        elif age_days < 730:
            return "Developing (1-2yr)"
        else:
            return "Mature (2yr+)"
    except Exception:
        return "Unknown"

def _age_yrs_from_period(open_date_str, period_key):
    """Return numeric age in years for a stand at a given period end. Returns None on failure."""
    try:
        open_dt    = pd.to_datetime(str(open_date_str)).date()
        period_end = _period_end_date(str(period_key))
        if period_end is None:
            return None
        return max(0.0, (period_end - open_dt).days / 365.25)
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def get_stands_df(dash, period_key=None):
    df = pd.DataFrame(dash["stand_records"])

    # Compute Age_Bucket dynamically from Open Date + Period_Key
    # (stand_meta.json has Open_Date but Age_Bucket was never stored)
    if "Open Date" in df.columns and "Period_Key" in df.columns:
        mask = df["Age_Bucket"].isin(["Unknown", "", None]) | df["Age_Bucket"].isna()
        if mask.any():
            df.loc[mask, "Age_Bucket"] = df[mask].apply(
                lambda r: _assign_age_bucket(str(r["Open Date"]), r["Period_Key"]), axis=1
            )

    if period_key and "_Q" in period_key:
        q_stands = _build_quarterly_stands(df)
        return q_stands[q_stands["Period_Key"] == period_key] if not q_stands.empty else pd.DataFrame()
    return df

def get_regions_df(dash, period_key):
    if "_Q" in period_key:
        q_regions = _build_quarterly_regions(dash)
        rows = q_regions.get(period_key, [])
    else:
        rows = dash.get("region_by_period", {}).get(period_key, [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# Logo base64 — used in sidebar and page header
_LOGO_B64 = "/9j/4AAQSkZJRgABAQEAlgCWAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAJJApcDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9U6KKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAoorH8XeLdL8DeHb3XNZuls9OtELySt+gHqT0ApNpK7LhCVSShBXb0SNimGVAcF1B9Ca/N34xft1+MPF+ozW3hSZ/DWkKxEbxc3Egz1Zu2R2A4rwi6+Kfi69vEupvEWoyToSVc3DZBPXvXi1M1pRdoK5+r4Lw6x9emp4mrGm301b+dtPxZ+zYIIyDke1LX5CaJ+0h8SfD20WPi/Uo0BzsaXcp+oNeneGv2/PiRo21L3+z9WizyZ4Cr/8AfQP9KcM1ov4k0Z4nw5zOlrRqQn82n+K/U/S2iviLRv8AgpLCsMa6p4Qd5P4pLW6AH5Ff612Gmf8ABRDwNc7ftmlalaZGTtUPg+nFdccfhpfbPm6vB+eUd8M36NP8mfVtFfOtp+3p8KLjyw97qUDN132LYX6mtmx/bQ+FF/I6L4hMRUZzNCyg/StViqD2mvvPNnw/m9P4sLNf9us9xoryax/aq+Ft+rFfF1lFtOP3zbc/StK0/aM+Gd4GKeNtHXb18y5VP51oq1J7SX3nHLKsfD4qE1/26/8AI9Horg4Pjx8OrmVYovGuiSSMcBVvUyf1q7/wt7wR/wBDXpH/AIFp/jVe0h/MjB4HFR3pS/8AAX/kdfRXKQfFfwbcyiOLxRpUkh6Kt2hJ/Wrn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FRbDTLe3Cp0G2NRx+VdXSABQABgDoBS0AFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABXget/sL/BbxT431XxXrvgy11vVtTmNxcG9YsjOep2jFe+UUAee+Ff2fPhr4ISNdD8EaLpyx/dEVopx+ea7m30yzs8eRaQQY6eXGF/kKs0UAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQB4N+2n4+/wCEI+B+qQQyhL3ViLGNc87W++R9B/OvyzY5JNfWH/BQj4hnXfiPY+GYJN1rpEAdwp481+oPuAo/Ovk6vjcxq+0rtLZaH9ScEZd9QyeE5L3qnvP0e34a/MKKKK8w+/CiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKAJrO3e7uooYxueRwqj1JNfsF8CPAqfDn4UeHdEEflTxWyvcDGMysMufzr83P2S/h3/wsT41aHbTQCewsnN7dKemxP8A7IrX6w19JlNKylVfofhPiRmN50cvi9vefz0X6/eNdgilmOABkmv52/2yvGtr8Qf2nfiHrdjKJrGfVJFgcd0XC/zBr9xP2ufi1H8FP2e/GPif7QLe8is3gsif4rhwVRR+Ofyr+di6uXvLmWeU7pJXLsT3JOTX0J+JEVFFFABXtf7F2mJrH7Ufw6tHcxq+qIdy9RhSf6V4pXvH7C3/ACdn8Nv+wmP/AEBqAP6FqKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAqhrurwaBot9qV1IIre1haZ3Y8AAZq/Xzx+3F8Q18G/Ba802KVVvtbcWioThjH1cj8h+dY1qipU5TfQ9PLMFLMcbSwkN5yS+XV/JH5y/EjxfP488c61r9ycy39y8xGegJ4H5VzVKTkmkr4FtybbP7Mp040oRpwVkkkvRBRRRSNAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiirOm2MupahbWkC75ppFjRfUk4AoE2lqz73/AOCdnw6/s7wrrPjC4iXzb+X7JbP38tCd/wD49j8q+xq434P+CI/h18NdA0BYliktbVBMF7ykZc/nmuvmlWCJ5HOERSzH0Ar7zDUvY0YwP49z/MHmmZ1sVfRvT0Wi/A/MT/gst8YBHY+E/hxZ3GWkZtTv4Q3QDAhyP++zX5X17j+2r8WG+Mv7SfjLX0m8+xS6azsmzn9xGSE/rXh1dJ8+FFFFABXtf7F2qLo/7Ufw6u3QyKmqINq9TlSP614pXc/A3Wj4d+MfgvUAzJ5OrWxJXrgyAH+dAH9KtFICGAIOQehFLQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFfnD/wAFB/G0+tfFe10HkWmk2q7fd5OWP6Cv0erwD9oL9kPRPjlrUOtLqMmi6wqCKWdI/MWVR93K5HI9c15+OpVK1Fwp7n2vCOY4PK80WJxukbNJ2vZvrZa7XXzPy4or7o/4dqxf9Dsf/Bf/APbKP+HasX/Q7H/wX/8A2yvm/wCz8T/L+KP3b/XbIf8AoI/8ln/8ifC9FfdH/DtWL/odj/4L/wD7ZR/w7Vi/6HY/+C//AO2Uf2fif5fxQf67ZD/0Ef8Aks//AJE+F6K9o/aQ+A+l/AbVNO0uDxINb1G4Qyywrb+X5KdsnceT6V4vXFUpypScJbo+rweLo4+hHE4d3hLZ2av8nZhRRRWZ2hRRRQAUUUUAFFFKBkgUAJRX1p8Hv2EZfiZ8PtL8SXniQ6RJfKZFtTZmTCZ+U53jqOeldp/w7Vi/6HY/+C//AO2V3xwGIklJR0fofG1uMMkw9WVGpXtKLafuyeq9FY+F6K+6P+HasX/Q7H/wX/8A2yj/AIdqxf8AQ7H/AMF//wBsqv7PxP8AL+KMf9dsh/6CP/JZ/wDyJ8L0V90f8O1Yv+h2P/gv/wDtlH/DtWL/AKHY/wDgv/8AtlH9n4n+X8UH+u2Q/wDQR/5LP/5E+F690/Y2+Hv/AAnnxt0gyxCWy0zN9OpHBC8KP++mH5V7r/w7Vi/6HY/+C/8A+2V9Afs//s46H8BNMuVsp31HVbsAXF9Ku0kDoqjsK6cNl9ZVYuorJHgZ7xrlksvq08DV5qklZaNWvo3dpdPxPXa8H/bf+Lg+C/7NXjDXIbn7Lqc1sbGwf1nk4Uflur3ivyp/4LKfGVrjWPC3w1srj91bodT1CH/bbiH9Nxr6s/nM/MmSRpZGdjlmJJPqabRRQAUUUUAFXNHvjpmr2N4OtvOkw/4CwP8ASqdFAH9MPwk8Qr4s+F3hPWUcOt/pdtcBh33Rqf611tfLX/BNX4gDx9+yd4XZ5A9zpbS6dImclRG2F/MV9S0AFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFZXirxJZ+EPDmo6zfyCO0soHnck4yAM4HuelatfGP/BQf4wf2do9h4E0+fE13i5v9pziMH5EPoSRn6VzYisqFJzZ7uSZXPOMfTwcdm9X2it3934nxl8UvHl78SvHer+Ib5y8t5OzKD/Cg4RfwUCuUoor4SUnJuT3Z/YNKlChTjSpq0YpJLyWwUUUUjUKKKKACiiigArY8H6HL4l8UaVpcEbSyXdzHCFUZPLDP6ZrHr6K/YX8EjxX8b7K9cAw6PC96wI4z91f1b9K2o0/a1Iw7s8zM8YsvwVbFP7EW/n0/E/Snw1ocPhnw9puk24AgsrdLdMDHCqB/StOiivvkrKyP4xlJzk5S3YUUV+fHx9/4Kpy/A/4w+KPA8vgJr/+xro263Ru9nnLgENjHGc0yT9B6K/Lj/h9V/1Tg/8Agd/9asGb/gtF4iMrmPwJZLHn5Q07EgUAfrLRX5Mf8PofEv8A0I1h/wB/2rl/Gn/BYv4m6vbSQaBoGjaKHQqZ5UaaRT6r8wAP50Afpz+0h+0T4Z/Zt+HN94l1+6j+0BCllYBh5t1Nj5VUenqfSv5+vjD8Vtc+NnxF1nxj4huDPqOpTNIVz8sSZ+WNfRVHApPih8YPGPxm8QvrXjLX7vXL9uFa4fKxjsFXoAOlcbQAUUUUAFFFFABRRRQB+nH/AARl+LC2ur+Mfh7cy83SJqlortwCnyuq/XcD+FfqtX84v7MHxdn+B/xz8J+LYmb7PZ3irdRhsCSFvlYH2wc/hX9F2kataa7pdpqNjMtxZXcSzQyoch0YZBH4GgC5RRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRXJ/Ev4peGPhB4abX/Fuqw6RpQlSAzzHje7AAfmaAOsoqtp2o22r2Fve2U8d1aXEayxTRNuV0IyCD6EVZoAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKAM3xHr1p4X0HUNXvnEdnZQPPK3+yoyf5V+O/xT8dXfxI8e6z4gvJDJJeXDOgPG1Bwi47YUCvun/goD8VP+Eb8B2fhK0l23msN5k+1sMsCkfoxyPwr86ycmvl81r801SXT8z+hfDzKfq+EnmNRe9U0X+Ff5v8hKKKK8I/XgooooAKKKKACiiigAr9A/8AgnP4PFj4N8QeIZYcS3lytvDJjqij5v8Ax6vz+QbmA9TX64/sw+D/APhCfgf4XsCMSS2wu39cy/Pz/wB9V7GV0+avzdkfmPiDjPq+UqgnrUkl8lq/0PU6KKK+tP5qCvw//wCCsfhNfDf7VdzdxqRHqumwXhbGAXyyt/IfnX7gV+Xn/BaXwUq2/wAP/FMUOWZ57GeQDoAFZMn8TQB+WlFFFABRRRQAUUUUAFFFFABRRRQAUUUUAHSv2k/4JVftLL8UfhI3gLV7pW8Q+F0WOAOw3T2fRCB1OzofqK/FuvRf2f8A416z+z98VNF8Z6K5M1lKBPbkkLcQkjfG2OxH6gUAf0k0Vx/wj+Keh/Gj4e6N4w8O3K3OmalCJFwwLRN/FG3owPBFdhQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFQX19baZZz3d5PHa2sCGSWaVgqIoGSST0FAEOta1ZeHNIvNU1K5js7CziaeeeU4WNFGSSa/Cr9vn9se9/ac+ITWGlTSQeBtHkaOwtwcfaH6GZx3J7e1el/wDBRH9v6T40Xtz8PvAd1JB4MtJit5qETFW1J1PQf9Mh6d/pXwRQB+gP/BOv9v65+FOq2Xw6+IGotN4Nun8uw1C4Ys2nSHopP/PMn8s+lfsRbXMN7bRXFvKk8Eqh45Y2DK6kZBBHUEV/LtX6O/8ABOD9v/8A4Qaa1+GfxG1KSTQ5nEWkarctn7Gx6ROT/AT0PagD9caKZDNHcRJLE6yROoZXQ5DA8gg9xT6ACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKRmCKWYhVAySegpa8m/ak+IR+G/wW1/UYmK3dxH9itypwQ8gKhh9OtROapxc30OvB4aeNxFPDU/im0l82fnV+078S2+J/xf1vUUlZ7CCX7LaK38MacfqcmvJ6fNI00ruxLMxJJPemV8BObqSc3uz+zcJhqeDw8MNSXuwSS+QUUUVB1hRRRQAUUUUAFFFFAG74F0dvEHjLRNNVDJ9qvIYioGeC4z+ma/Z/TLCPStNtbKHiK3iWJPooAH8q/Lf9i/w4fEHx98PlofNgtDJcyccDCED9SK/VKvp8phanKfdn8/eJOK58ZQwy+zFv5yf+S/EKKKK94/HQr5R/4Ka/DpviB+yf4jkhiDXWjSR6mr4yVSM5f8xX1dWH458K23jnwbrfh68ANrqlnLaSgjI2upU/zoA/mNorofiF4UuvA3jnXtAvImgudOvZbdo2GCNrHH6YNc9QAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQB9afsCfto3f7MXjY6Vrc81x4C1aQC8twS32WToJkHb3A61+4/hvxJpni/QrLWdGvYdQ0y8jE0FzAwZHUjgg1/MJX1t+xX+334j/Zk1KDQ9XMuueAZpP31iWzJaZ6vCT/AOg9DQB+7FFcf8Lfi34U+M3hS18Q+EtXt9W06dQ2Ym+eM/3XXqpHvXYUAFFFFABRRRQAUUUUAFFFFABRRRQAUUV5R8fv2mvAf7OHhmXVvFurxRXG0/Z9MhYNdXLY4VU7fU4FAHoviLxHpnhLRrvVtZvoNN021QyTXNy4REUepNfjr+3t/wAFFLz42y3vgXwBPJYeB45NlxqCErLqeP1WP27968k/a3/bo8a/tRatJaSyvofg2FybbRbdyFf0eUj77H0PA7V80UAFFFFABSgkHI4NJRQB+n//AATg/wCCgkOmwad8K/iNfMse7ytI1q5cnGTxDIT0HZT+FfqcrB1DKQykZBHQ1/LojtG6ujFWU5DKcEGv1e/4Jyf8FCR4jXS/hX8R70LqigW+j61O2BcAfdhlP97sG796AP0uooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACvg/8A4KM+PzPq+geEYXYC2jN7OFPDF+EB+m0193OwRGY9AMmvyF/aL8c/8LD+MPiPV0kMls1yYrfJ+7GvAH8/zrx80q8lHkXU/T/D7AfWs1eJktKSv83ov1fyPNaKKK+SP6UCiiigAooooAKKKKACiiigD7M/4JweGzP4q8Ta26gxwWq2yH0dmBP6Cvvqvlf/AIJ5+G20n4TanqLoQdSvy6sR1CLt4/KvqivtcBDkw8fPU/lHjLE/Wc8ru+kWo/ckvzCiiivQPigooooA/Er/AIKvfBz/AIV7+0U/iW0gddO8UwC8eXGF+0D5XUfgFP418TV+6n/BTj4Gv8YP2cL/AFCxtxNrXhlzqVue/lADzgP+AD9K/CwjBxQAlFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFAHo/wS/aC8c/s+eJk1rwXrUunSk/vrZjut7gekkZ4av1a/Zt/wCCrXgH4lwW2leP1XwT4gICm5kO6ylPAGH6qSexGOa/F6igD+oHSNa0/X7GO8029gv7SRQyTW0gdSD05FXa/m++FX7SnxK+Cs8beEfFuoaXbo+82YlLW7n0ZDwRX2f8Lf8Agsp4u0mOO38d+FbLXgSA17p7/ZnUeuzBB/OgD9cqK+K/Bn/BWf4I+JFij1GXVtAuSPnF3agxqfZw39K9g0P9uP4E+IVT7L8TNCWVgT5M0+xxj1BFAHulFec2P7Rvww1O3E9r460OaEnAdbtcVBqX7TXwp0coL3x/oVuXzt3Xa80Aem0V86eJP+ChHwC8N27yn4iabqTL1i04mZ/y4rwz4g/8FifhlocUqeFdC1fxFcpkA3CC2jY+xyTj3xQB9/Vx3xG+MHgv4SaPJqni/wASWGhWaHBa6lAYnsAo5P5V+Pvxa/4Ky/F7x4t1aeHVsfBumzrtAtE8y5T/AHZTgj8q+QvGHjvxF8QNWfU/EmtXut37/euL2ZpGP50AfpP+0p/wV9ZkuNG+EGnFGyUbXtTjBx1BMcXIIPYmvzZ8b+PPEHxI8Q3OueJtWutZ1S4OXubuQu3XoM9APQVgUUAFFFFABRRRQAUUUUAFSW9xLaTxzwyNFNGwdJEOGVgcgg9jUdFAH6+f8E5f+CgR+JMFn8NPiJfKviWBAmmatM2PtyDgRuT/AMtB2Pev0Sr+XixvrjTLyC7tJ5La6gcSRTRMVZGByCCOhr9lP+Cdn7esHxm0a38BeOtQSLxvZoFtLqYhRqMQHHP/AD0Hf1oA+86KKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKAPO/2gvGo8AfB/xNrCy+TcJaPHbtnGZGGFFfkDcStPPJI7bnZiSfU1+gH/AAUW8bnT/BmheGYnBN/ObmZQeQseNv6t+lfn3XyWaVOetydkf0n4e4H6vlcsTJa1ZN/JaL8bhRRRXjn6gFFFFABRRRQAUUUUAFKoywFJU1nC1xdwxICWdwoAGeScUBotz9ZP2UNCbw98BPC1s6FJHhadge5dy39a9crn/h9p66V4E8O2aoEEOn26FQMciNc/rmugr9ApR5KcY9kj+LMwrvE4ytXf2pSf3thRRRWp54UUUUAQX1jBqdlPaXUSz208bRSxOMq6kYIP4V/PV+2X8Brv9nr49eIfDzxv/Zc8pvdNmYYEsDnIx9Dlfwr+hyvi7/gp5+zIfjX8HG8UaNaCXxR4YVrhNg+ee26yJn/ZGWA9qAPxCopSCCQeCKSgAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigB6zSIMLIwHoCaRpXfG52bHqc02igAooooAKKKKACiiigAooooAKKKKACiiigAooooAKuaRq97oGp22o6ddS2V9bSCWG4gYq8bA5BBFU6KAP25/4J/wD7eOm/tA+HrTwd4ruks/iFYQhcysAupIB/rE/2/Vfxr7Vr+YLw74h1HwnrllrGkXkthqVlKs8FxCxVkdTkEGv3K/YH/bXt/wBqfwnPpOrQG08b6LAjX6op8q4QnaJlPYk9V9aAPrOiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKo63qUWjaPe307iOK3heVmPYAE0npqVGLk1Fbs/Mz9uTxl/wlPx11G1jcmDSoksgpPAdclz+ZH5V89Vt+NNfn8U+K9V1a5YvNeXMkzEnP3mJrEr4GtP2tSU+7P7OyzCLAYKjhV9iKXztr+IUUUViemFFFFABRRRQAUUUUAFdB8P7QX/jnw/bEAibULeMg9DmVR/WufrufgfbLd/FvwlG0ZlU6lASo9mB/pVwV5peZy4ufs8PUn2i3+B+xFrAtrbQwqMLGgQAegGKloor9CP4nbvqFFFFAgooooAKZLEk8TxyIskbgqyMMhgeoIp9FAH4Yf8FHf2TZP2e/irJr2j25/wCEN8RytPalV+W3nOS8J/HJHsa+QK/pJ+PvwR0H9oL4Zat4P1+FWhuk3W9xty1vMPuSKe2D+Yr+fP43/BfxH8BPiNqvhDxNatBe2chEc2P3dxF/BIh7gjB9ulAHBUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRUtrazX1zFb28Tz3ErBI4o1LM7E4AAHU0AaPhPwrqvjjxHp+haJZyX+qX8ywW9vEMl2Y4H/AOuv3v8A2KP2T9L/AGW/hdb2LLHdeK9RVZ9WvwvJcj/Vqeu1en1zXkH/AATn/YUj+BWhQ+PPGdqkvjnUYs29s4DDTYWAIH/XQ9z24FfdFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFeNftd+LP8AhEvgJ4llD+XNeRiyibPIZ/T8Aa9lr4z/AOCjvixrTw54a8PI2RdTPdSKD2QbQf8Ax6uPFz9nQnLyPp+GcJ9dzjD0XtzJv0jq/wAj4GY5JpKKK+GP68CiiigAooooAKKKKACiiigAr1H9mUZ+OHhPv/pi/wAjXl1d78CLtrL4weEpFk8o/wBowru+rY/rWtF2qRfmjzsyi5YKvFdYy/Jn7E0UUV+gH8WhRRRQAUUUUAFFFFABXzN+29+xvpP7VHgNmthFY+NdMjZtM1Bhw/cwvj+Fv0OK+maKAP5ivGHhDV/AXiXUNA12xl07VbCVoZ7eZSrKwOO/Ueh71jV+7H7dH7Cuj/tO+HX1vRY4dL+IFjEfs13jal4o/wCWUvr7N1H0r8RvHfgTXfhp4r1Dw54k06bStYsJTFPbTrggg9R6g9iKAMCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiir2iaHqHiXVrXTNKs5tQ1C6kEUNtboXd2PQACgCta2s19cxW9vE888rBI4o1LMzHgAAdTX68/wDBPL/gnnD8Obax+I/xGsVn8TyqJdO0mdQy2KkZDuO8h/StX9g3/gnFY/B+Gy8c/Ea1i1DxowElppzfPFp3oSOjSfyr77oAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAK/NH9vvxS2tfGttOV91vptpHGo9Gblv5Cv0sdxGjMxwqjJNfj/8AtB+IP+En+Mviy/WUyxSX8qxsf7gYhR+QrxM1naio92fq/hzhva5lUrtfBD8W0vyued0UUV8qf0YFFFFABRRRQAUUUUAFFFFABW34I1AaV4x0O9J2i3voJScZxtkU/wBKxKfCxWVCOCDTTs7kSgqkXB9dPvP27067W/0+1uUOVmiWQH2IB/rViuT+E9++p/DLwtcyDDvpsGec5IjAz+ldZX6FF80Uz+Ja9P2VWVPs2vuYUUUVRiFFFFABRRRQAUUUUAFfPP7Wf7F3gz9qfw85v4V0vxXbxkWWtwL+8U44WT++nsenavoaigD+cL4+fs3+OP2cfFk2ieLtKkgTcRbajEpa2ulH8SN/Q815dX9L/wAUfhP4U+MvhS58OeL9Ht9Y0ucfcmUFo27OjdVYdiK/JX9rD/glj4s+F0t74g+G6zeLPC65kaxHN7aryTx/GoA+919qAPgqiprq0nsbh4LmGS3njO145VKsp9CD0qGgAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAop8UTzyLHGjSSMcKqjJJ9hX21+yh/wTD8a/Gh7TXvGqzeD/AAk22RVlTF3drwfkQ/dUjjcfyoA+Y/gr8CfGXx+8X2/h7wdpE2oXLn97PtIht07vI/QAZ+tftR+x7+wX4Q/Zg0mDUrpIvEHjmVQbjV5Y8rAf7kIP3QORu6mvbPhD8FfB3wM8Kw+H/BujQ6VYoBvZADLOw/ikfqx9zXc0AFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFAGT4r1BNJ8MateSNtSC1kcn6Ka/FnU7uS/1C4uZW3SSuZGPqScn+dfrj+0nqraL8CvGd2jbZEsGC4OOSQP61+QrdTXzOby9+ET998NaFsNia/eSX3K/6iUUUV4B+zBRRRQAUUUUAFFFFABRRRQAVd0bTZ9Z1azsbVDJcXMyQxoB1ZmAH86bp2l3er3cVrZW8lzcSNtSKJSzMfYCvuf9kX9kC/8ADerWvjTxpbrBcRLvsdMcZZGP8cnoR2FdWHw88RNRitOp8/nWdYbJMNKvXkua3ux6t9NPzZ9ceBtFPhzwZoelsu17Syhhcf7SoA365rcoor7pKysj+P6k3Um5y3buFFFFMgKKKKACiiigAooooAKKKKACkIBGDyKWigD5u/aM/YJ+F37RST3t/pY0PxIynZrGmgRuzdjIvRx7V+W37QH/AATV+LPwUe4vrDT/APhMPDyOdl7pYLSog/ikj6r+tfu1SModSrAEHgg96AP5dri2ltJminieGVDhkkUqwPoQajr+hj43fsT/AAk+PSTy+IfDEFtq0gx/aumgQXI/EDB/EV8D/GL/AII3+KdKluLv4deJLTW7csTHp+pfuJUX08zofyFAH5v0V6b8Tf2aviZ8H7iVPFXg/U9NhRtouzAzQP7q4GCK8zIKnBGD70AJRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFbPhbwZrvjjVI9N8P6Reazfyfdt7KFpHP4AV9f/BL/glL8WPiWsF74l8jwNpMgzm+G+5+nlDBH4mgD4oVSxAAJJ6AV9Ifs9fsD/FX9oOW3u7HR20Pw85DNq+qKYo2XuYweXPtX6pfAf8A4Ju/CH4K+RfT6T/wlmvR7X+3aviRY5B3jTGF/HNfU8EEVrEsUMaRRKMKiKFUD2AoA+Vv2Z/+CdHw0/Z9W21O6tV8W+K48MdT1CMFImHeKM5C/XmvqwAKAAAAOABS0UAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQB4T+2rqJsPgBrijb/pDRxHPuc8flX5YHqa/TH9v0kfAk4OM6hD/AOzV+Zx618lmrvXS8j+k/DyCjlEpd5v8kJRRRXjn6gFFFFABRRSgZoASpbe2lu5khhjaWVyFVEGSx9AK9x+BP7JPiv4ySRX0kZ0Xw/nLX10hBkHpGvU59elfffwn/Zq8D/CK0Qabpkd7qO3Emo3qh5X/AKL+Ar0sPgKtf3noj4LO+McvydulF+0qr7K2Xq+npqz4J+Gf7F/xE+IYhuJbBdA05z81xqOVYD1Ef3jX054E/wCCe3g/REhm8Q6ld63dIcskeIoW/DGf1r6vor6Cll1CnurvzPxnMeOM4xzapz9lHtHf79/yOQ8G/CLwb8Poynh/w7Y6cTyXSPc5PruOTXX0UV6MYqKtFWPhatarXm6laTlJ9W7v8QoooqjEKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigCve6fa6lCYru2huoj/AATxh1/I14j8SP2IPgr8UWnn1fwLp0V/KMG+slMMo+m04/SvdqKAPzk+If8AwRn8H6mrv4N8X6ho0rZIj1JBcRqf+AgHFfPHjb/gj/8AGDQZD/YGoaL4mjGfmWb7KSPo5r9oqKAP56vF/wCwx8cPBcjJefD/AFS62kgtp8X2gf8Ajua8v1v4V+MvDRYar4W1jTivUXNlImO3cV/TLVK90XT9Tz9ssLa7z/z3hV/5igD+YB0aNyrKVZTgqRgg02v6YNT+EXgfWU23vhDRLgZz81hFnP1C1xGrfsc/BfXFAvPh3osoDbhiErz+BFAH861Ff0D3n/BPr9n2+naaX4aaZ5jddksyj8g4FZWo/wDBNv8AZ8v3Rk8Bw2e0YIt7mUA/XLGgD8DaK/eb/h2Z+z//ANCe3/gXJ/jV/Tv+Cb/7PdgjK/gC3vCTndcXMxI+mHFAH4FUV/Qlpn7B3wE0gKLb4a6Su1t4LmRzn/gTGu90H4AfDfwzj+zfBGh25GSD9iRzz/vA0Afzp6D8OfFXihgNH8OapqZJAH2W0kkznp0Fev8Agb9gn45+P3AsfAd/ZA/xaoPso/8AH8V+/lh4f0vSv+PLTbOz/wCveBE/kK0KAPx8+H3/AARt+IWsiOXxZ4n0rw6gwXt7dTdOfUBlIA+tfVfww/4JN/BzwS8Vzrq3/i+6A+eO/lCwE+yqAf1r7YooA5bwT8LvCPw406Gx8M+HNO0W2hGI1tbdVIH+91/WupoooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKAPmv8Ab9GfgSf+whD/AOzV+Zx61+qn7Z+jtq37P/iB1UN9k2XByOgDAf1r8qz1NfJZqrV0/I/pPw7mpZRKK6Tf5ISiiivHP1AKKKfFE88qxxqXdiFVVGSSegAoAIYZLiVIokaSRyFVVGSSegAr7p/Zi/YkihhtPE/xAtvMlbbLbaO/RR1DS+/+z+dbv7IP7JUfhC0g8X+MrJJdZmAksrGZci1XqGYf3z+lfXtfSYHL0kqtZei/zPwji3jSUpSwGWSslpKa6+UX27vr0I7e2is4I4IIkhhjG1I41Cqo9AB0qSiivoT8UbvqwooooEFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAcl8WvDS+MPhp4k0dgCLqykXB9QMj9RX41TxmGZkYYZTgg+tfuBJGssbIwyrAgj1Ffl1+1v8A9Q+FXj681G0tnk8N6nK09tOi/LEScmNvQjPHrXz+bUXKMaqW25+0eHGZU6VStgKkrOdpR82tGvW1vuPAKKXpQqljgAk+1fNH72GM19wfsUfsurKLbx94rssp9/TLOdfvekrA/p+dcj+yT+yPceOry28WeLrV7fw9C4ktrSQYa8YHIJHZP51+iEMMdtDHFEixxRqFRFGAoHAAFfQZfgrtVqq9F+p+K8a8VqnGWWYCXvPScl0/urz79tu4+iiivpT8GCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKztf8AD2m+KdKn03V7GDUbCddslvcIGVh9K0aKTSejKjKUJKUXZo+ZPE/7APw71m4efTpL/SGd9zRxy70HsoI4FdF4B/Ys+GvgW/ivzp8us3kf3TqD+ZGD2ITGM17zRXKsJQT5lBXPoanEecVaXsZ4mbj6/ruMiiSGNY40WONRhVUYAHoBT6KK6z5wKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigD/2Q=="

# ─────────────────────────────────────────────
# SIDEBAR: Minimal branding only
# ─────────────────────────────────────────────
def render_sidebar():
    _logo = _LOGO_B64  # module-level constant
    st.html(
        '<div style="padding:12px 4px;">'
        '<div style="text-align:center;margin-bottom:10px;background:#fff;border-radius:8px;padding:8px 4px;">'
        f'<img src="data:image/jpeg;base64,{_logo}" style="max-width:145px;height:auto;display:inline-block;" />'
        '</div>'
        '<div style="font-family:DM Mono,monospace;font-size:11px;color:#C5BEBE;'
        'text-align:center;letter-spacing:1px;text-transform:uppercase;">'
        'Financial Performance Dashboard</div>'
        '<hr style="border:none;border-top:1px solid #e2e4e9;margin:16px 0;">'
        '<div style="font-family:DM Mono,monospace;font-size:10px;color:#c0c4cc;'
        'text-align:center;letter-spacing:1px;">CONFIDENTIAL · INTERNAL USE ONLY</div>'
        '</div>'
    )

# ─────────────────────────────────────────────
# TAB: CEO SNAPSHOT
# ─────────────────────────────────────────────
def tab_ceo(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)

    # ── Time Frame Selector ──
    available_years = sorted(periods_df["year"].unique().tolist())
    all_labels = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]

    sel_col1, sel_col2 = st.columns([1, 4])
    with sel_col1:
        sel_year = st.selectbox("Fiscal Year", available_years, index=len(available_years)-1, key="ceo_year")

    year_periods = periods_df[periods_df["year"] == sel_year]
    period_labels = year_periods["label"].tolist()

    # Clear stale selections when year changes
    if "ceo_periods" in st.session_state:
        st.session_state["ceo_periods"] = [l for l in st.session_state["ceo_periods"] if l in period_labels]

    with sel_col2:
        q_presets = {"Q1 (P1–3)": [1, 2, 3], "Q2 (P4–6)": [4, 5, 6],
                     "Q3 (P7–9)": [7, 8, 9], "Q4 (P10–13)": [10, 11, 12, 13], "All": list(range(1, 14))}
        qcols = st.columns(5)
        for i, (q_name, p_nums) in enumerate(q_presets.items()):
            with qcols[i]:
                if st.button(q_name, key=f"ceo_q_{q_name}", use_container_width=True):
                    matching = year_periods[year_periods["period_num"].isin(p_nums)]["label"].tolist()
                    if matching:
                        st.session_state["ceo_periods"] = matching
                    st.rerun()

    selected_periods = st.session_state.get("ceo_periods", [])

    # Filter to selected periods (or all periods for selected year)
    if selected_periods:
        filtered_df = year_periods[year_periods["label"].isin(selected_periods)]
    else:
        filtered_df = year_periods.copy()

    if filtered_df.empty:
        filtered_df = year_periods.copy()

    latest = filtered_df.iloc[-1]
    prev   = periods_df.iloc[-2] if len(periods_df) > 1 else None
    first  = periods_df.iloc[0]

    period_range = f"{filtered_df.iloc[0]['label']} – {filtered_df.iloc[-1]['label']}" if len(filtered_df) > 1 else latest['label']

    # ── System KPIs ──
    section("CEO SNAPSHOT", f"{period_range} · {int(latest['stands'])} active stands · FY{sel_year}")

    total_revenue_ytd = filtered_df["net_sales"].sum()
    total_ebitda_ytd  = filtered_df["ebitda"].sum()
    growth_rate       = dash.get("yoy_growth", 1.0) - 1.0
    avg_ebitda_pct    = (filtered_df["ebitda_pct"] * filtered_df["net_sales"]).sum() / total_revenue_ytd if total_revenue_ytd > 0 else 0

    year_label = f"FY{sel_year}"
    n_periods = len(filtered_df)

    kpi_row([
        {"label": f"{year_label} Total Revenue",     "value": f"${total_revenue_ytd/1e6:.1f}M",  "sub": f"{n_periods}-period total",   "color": "red"},
        {"label": "YoY Revenue Growth",       "value": f"+{growth_rate*100:.1f}%",        "sub": "vs prior year class",         "color": "green",
         "valcls": "good"},
        {"label": f"{year_label} Total EBITDA",      "value": f"${total_ebitda_ytd/1e6:.1f}M",  "sub": "after rent",                  "color": "blue"},
        {"label": f"{year_label} Avg EBITDA%",       "value": _fmt_p(avg_ebitda_pct),             "sub": "sales-weighted average",      "color": "green",
         "valcls": "good" if avg_ebitda_pct >= 0.18 else "warn"},
        {"label": f"{latest['label']} Stands","value": str(int(latest["stands"])),        "sub": "active this period",          "color": "grey"},
        {"label": f"{latest['label']} Avg Sales","value": _fmt_d(latest["avg_sales"]),    "sub": "per stand",                   "color": "amber"},
    ])

    # Pre-compute filtered stands (needed by narrative AND cohort sections below)
    filtered_pks    = filtered_df["period_key"].tolist()
    filtered_stands = stands_df[stands_df["Period_Key"].isin(filtered_pks)]

    # ── Annual Goals Tracker (shown when a goal year is selected) ─────────────
    ANNUAL_GOALS = {
        2026: {
            "net_sales":  205_646_328,
            "cogs_pct":   0.276,
            "labor_pct":  0.236,   # all-in
            "ebitda":     39_857_275,
            # Per-period goals — P1 through P13 (reflects stand-count ramp)
            "net_sales_by_period": [
                 9_130_515, 11_159_651, 12_790_640, 13_664_652, 15_126_988,
                15_496_441, 16_407_317, 17_458_962, 17_984_433, 18_758_183,
                18_843_634, 19_135_068, 19_689_843,
            ],
            "ebitda_by_period": [
                1_507_851, 1_966_287, 2_410_946, 2_658_865, 3_107_604,
                3_067_255, 3_196_020, 3_404_142, 3_487_614, 3_668_610,
                3_722_240, 3_808_510, 3_851_330,
            ],
        },
        # Add future years here as goals are set
    }

    if sel_year in ANNUAL_GOALS:
        goals       = ANNUAL_GOALS[sel_year]
        goal_ebitda_pct = goals["ebitda"] / goals["net_sales"]

        # Always use full-year periods (not the filtered sub-selection) for YTD pacing
        ytd_df      = year_periods.copy()
        n_completed = len(ytd_df)            # periods completed so far this year
        pct_elapsed = n_completed / 13       # fraction of year elapsed

        ytd_sales  = ytd_df["net_sales"].sum()
        ytd_ebitda = ytd_df["ebitda"].sum()
        ytd_cogs_pct   = ((ytd_df["cogs_pct"]  * ytd_df["net_sales"]).sum() / ytd_sales
                          if ytd_sales > 0 and "cogs_pct"  in ytd_df.columns else None)
        ytd_labor_pct  = ((ytd_df["labor_pct"] * ytd_df["net_sales"]).sum() / ytd_sales
                          if ytd_sales > 0 and "labor_pct" in ytd_df.columns else None)

        # Period-specific YTD goal: sum of goals for completed periods only
        # (accounts for stand-count ramp — early periods have lower goals than later)
        has_period_goals = ("net_sales_by_period" in goals and
                            "ebitda_by_period"    in goals)
        if has_period_goals and n_completed > 0:
            pace_sales  = sum(goals["net_sales_by_period"][:n_completed])
            pace_ebitda = sum(goals["ebitda_by_period"][:n_completed])
        else:
            # Fallback to linear pace if per-period arrays not defined
            pace_sales  = goals["net_sales"] * pct_elapsed
            pace_ebitda = goals["ebitda"]    * pct_elapsed

        def _goal_card(label, actual_fmt, goal_fmt, progress_pct, status, status_color,
                       detail="", bar_color=None):
            """Render a goal-tracker card with progress bar."""
            bar_color  = bar_color or BLUE
            bar_w      = min(max(progress_pct * 100, 0), 100)
            pace_line  = f'<div style="font-size:11px;color:{status_color};font-weight:700;margin-top:4px;">{status}</div>'
            return f"""
            <div style="background:white;border:1px solid #e2e4e9;border-radius:10px;
                        padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);">
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#C5BEBE;
                          text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">{label}</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:28px;
                          color:#1A1919;line-height:1;">{actual_fmt}</div>
              <div style="font-size:11px;color:#C5BEBE;margin-bottom:8px;">
                goal: <strong style="color:#595959;">{goal_fmt}</strong>
                {(" · " + detail) if detail else ""}
              </div>
              <div style="background:#f0f1f3;border-radius:4px;height:6px;overflow:hidden;">
                <div style="background:{bar_color};width:{bar_w:.1f}%;height:100%;
                            border-radius:4px;transition:width .3s;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:4px;">
                <span style="font-size:10px;color:#C5BEBE;">{bar_w:.0f}% of goal</span>
                {pace_line}
              </div>
            </div>"""

        def _pace_status(actual, pace_target, tolerance=0.03):
            """Return (status_text, color) based on actual vs on-pace target."""
            if pace_target == 0:
                return "—", MID
            ratio = actual / pace_target
            delta_pct = (ratio - 1) * 100
            if ratio >= 1 + tolerance:
                return f"▲ AHEAD  (+{delta_pct:.0f}% vs pace)", GREEN
            elif ratio >= 1 - tolerance:
                return f"→ ON PACE ({delta_pct:+.0f}% vs pace)", BLUE
            else:
                return f"▼ BEHIND  ({delta_pct:.0f}% vs pace)", RED

        def _pct_status(actual, target, lower_is_better=False):
            """Return (status_text, color) for a % metric."""
            if actual is None:
                return "No data yet", MID
            delta = (actual - target) * 100
            better = delta < 0 if lower_is_better else delta > 0
            on_target = abs(delta) <= 0.3
            if on_target:
                return f"→ ON TARGET ({actual*100:.1f}%)", BLUE
            elif better:
                return f"▲ {'BELOW' if lower_is_better else 'ABOVE'} TARGET ({delta:+.1f}pts)", GREEN
            else:
                return f"▼ {'ABOVE' if lower_is_better else 'BELOW'} TARGET ({delta:+.1f}pts)", RED

        ytd_sales_goal_fmt  = f"${pace_sales/1e6:.1f}M"  if n_completed > 0 else "—"
        ytd_ebitda_goal_fmt = f"${pace_ebitda/1e6:.1f}M" if n_completed > 0 else "—"
        st.html(f"""
        <div style="font-family:'Bebas Neue',sans-serif;font-size:22px;letter-spacing:3px;
                    color:#1A1919;margin:16px 0 4px;display:flex;align-items:center;gap:10px;">
          <span style="width:6px;height:6px;border-radius:50%;background:#AC2430;
                       display:inline-block;flex-shrink:0;"></span>
          FY{sel_year} GOALS TRACKER
          <span style="font-family:'DM Mono',monospace;font-size:12px;font-weight:400;
                       color:#C5BEBE;letter-spacing:1px;margin-left:8px;">
            P1–P{n_completed} of 13 complete · YTD Sales Goal: {ytd_sales_goal_fmt} · YTD EBITDA Goal: {ytd_ebitda_goal_fmt}
          </span>
        </div>""")

        # Sales status
        sales_status, sales_color = _pace_status(ytd_sales, pace_sales)
        # EBITDA $ status
        ebi_status, ebi_color = _pace_status(ytd_ebitda, pace_ebitda)
        # COGs % status
        cogs_status, cogs_color = _pct_status(ytd_cogs_pct, goals["cogs_pct"], lower_is_better=True)
        # Labor % status
        labor_status, labor_color = _pct_status(ytd_labor_pct, goals["labor_pct"], lower_is_better=True)

        g1, g2, g3, g4 = st.columns(4)
        with g1:
            st.html(_goal_card(
                label="Net Sales (YTD)",
                actual_fmt=f"${ytd_sales/1e6:.1f}M",
                goal_fmt=f"${goals['net_sales']/1e6:.1f}M",
                progress_pct=ytd_sales / goals["net_sales"],
                status=sales_status, status_color=sales_color,
                detail=f"YTD goal: ${pace_sales/1e6:.1f}M",
                bar_color=sales_color,
            ))
        with g2:
            st.html(_goal_card(
                label="EBITDA (YTD)",
                actual_fmt=f"${ytd_ebitda/1e6:.1f}M",
                goal_fmt=f"${goals['ebitda']/1e6:.1f}M",
                progress_pct=ytd_ebitda / goals["ebitda"] if goals["ebitda"] else 0,
                status=ebi_status, status_color=ebi_color,
                detail=f"YTD goal: ${pace_ebitda/1e6:.1f}M",
                bar_color=ebi_color,
            ))
        with g3:
            cogs_actual_fmt = f"{ytd_cogs_pct*100:.1f}%" if ytd_cogs_pct is not None else "—"
            cogs_prog = max(0, 1 - (ytd_cogs_pct - goals["cogs_pct"]) * 10) if ytd_cogs_pct else 0.5
            st.html(_goal_card(
                label="COGs % (YTD avg)",
                actual_fmt=cogs_actual_fmt,
                goal_fmt=f"{goals['cogs_pct']*100:.1f}%",
                progress_pct=min(cogs_prog, 1.0),
                status=cogs_status, status_color=cogs_color,
                detail="lower is better",
                bar_color=cogs_color,
            ))
        with g4:
            labor_actual_fmt = f"{ytd_labor_pct*100:.1f}%" if ytd_labor_pct is not None else "—"
            labor_prog = max(0, 1 - (ytd_labor_pct - goals["labor_pct"]) * 10) if ytd_labor_pct else 0.5
            st.html(_goal_card(
                label="Labor % All-In (YTD avg)",
                actual_fmt=labor_actual_fmt,
                goal_fmt=f"{goals['labor_pct']*100:.1f}%",
                progress_pct=min(labor_prog, 1.0),
                status=labor_status, status_color=labor_color,
                detail="lower is better",
                bar_color=labor_color,
            ))

        # ── Period-by-Period Actual vs Goal Chart ─────────────────────────────
        if has_period_goals and n_completed > 0:
            st.html("""
            <div style="font-family:'DM Mono',monospace;font-size:10px;color:#C5BEBE;
                        text-transform:uppercase;letter-spacing:1.5px;margin:8px 0 4px;">
              PERIOD-BY-PERIOD: ACTUAL VS GOAL
            </div>""")

            period_labels = [f"P{i+1}" for i in range(13)]

            # Build per-period actuals from ytd_df (match on period number)
            # ytd_df is sorted by period; we index it by position
            actual_sales_by_period  = [None] * 13
            actual_ebitda_by_period = [None] * 13
            actual_ebitda_pct_by_p  = [None] * 13

            # Map period_key -> index (P1=0 … P13=12)
            for i, row in enumerate(ytd_df.itertuples()):
                if i < 13:
                    actual_sales_by_period[i]  = row.net_sales
                    actual_ebitda_by_period[i] = row.ebitda
                    ep = row.ebitda / row.net_sales if row.net_sales else None
                    actual_ebitda_pct_by_p[i]  = ep

            goal_ebitda_pct_by_p = [
                g_e / g_s if g_s else None
                for g_e, g_s in zip(goals["ebitda_by_period"],
                                    goals["net_sales_by_period"])
            ]

            ch1, ch2 = st.columns(2)
            with ch1:
                fig_g = go.Figure()
                # Goal bars (all 13, lighter)
                fig_g.add_bar(
                    x=period_labels,
                    y=[v/1e6 for v in goals["net_sales_by_period"]],
                    name="Goal", marker_color=BORDER,
                    marker_line_color=BORDER, marker_line_width=1,
                )
                # Actual bars (completed periods only)
                act_vals = [v/1e6 if v is not None else None
                            for v in actual_sales_by_period]
                fig_g.add_bar(
                    x=period_labels[:n_completed],
                    y=[v for v in act_vals[:n_completed] if v is not None],
                    name="Actual", marker_color=BLUE, opacity=0.85,
                )
                fig_g.update_layout(
                    barmode="overlay",
                    yaxis=dict(tickprefix="$", ticksuffix="M", tickformat=".1f",
                               title_font=dict(size=9, color=MID)),
                    legend=dict(orientation="h", y=1.12, x=0,
                                font=dict(size=9)),
                    margin=dict(t=24, b=28, l=0, r=0),
                    height=250,
                    xaxis=dict(tickfont=dict(size=9)),
                )
                brew_fig(fig_g, height=250)
                st.plotly_chart(fig_g, config={"displayModeBar": False},
                                use_container_width=True)
                st.caption("Net Sales — Actual vs Goal by Period")

            with ch2:
                fig_e = go.Figure()
                # Goal EBITDA% line (all 13)
                fig_e.add_scatter(
                    x=period_labels,
                    y=[v * 100 if v is not None else None
                       for v in goal_ebitda_pct_by_p],
                    name="Goal %", mode="lines",
                    line=dict(color=MUTED, width=1.5, dash="dot"),
                )
                # Actual EBITDA% (completed periods)
                fig_e.add_scatter(
                    x=period_labels[:n_completed],
                    y=[v * 100 if v is not None else None
                       for v in actual_ebitda_pct_by_p[:n_completed]],
                    name="Actual %", mode="lines+markers",
                    line=dict(color=RED, width=2.5),
                    marker=dict(size=6),
                )
                # PE target reference
                fig_e.add_hline(
                    y=goal_ebitda_pct * 100,
                    line_dash="dash", line_color=GREEN, line_width=1,
                    annotation_text=f"FY Goal {goal_ebitda_pct*100:.1f}%",
                    annotation_font=dict(size=9, color=GREEN),
                    annotation_position="top right",
                )
                # Dynamic Y-axis range — pad 20% above max so actuals beating goal stay visible
                _ebitda_vals = (
                    [v * 100 for v in goal_ebitda_pct_by_p if v is not None] +
                    [v * 100 for v in actual_ebitda_pct_by_p[:n_completed] if v is not None] +
                    [goal_ebitda_pct * 100]
                )
                _ebitda_max = max(_ebitda_vals) if _ebitda_vals else 30
                fig_e.update_layout(
                    yaxis=dict(ticksuffix="%", tickformat=".1f",
                               range=[0, _ebitda_max * 1.22],
                               title_font=dict(size=9, color=MID)),
                    legend=dict(orientation="h", y=1.12, x=0,
                                font=dict(size=9)),
                    margin=dict(t=24, b=28, l=0, r=0),
                    height=250,
                    xaxis=dict(tickfont=dict(size=9)),
                )
                brew_fig(fig_e, height=250)
                st.plotly_chart(fig_e, config={"displayModeBar": False},
                                use_container_width=True)
                st.caption("EBITDA % — Actual vs Goal by Period")

        st.html('<hr class="brew">')

    else:
        goal_ebitda_pct = 0.20   # fallback PE benchmark for non-goal years

    # ── Revenue + EBITDA Trend (all periods) ──
    col1, col2 = st.columns([3, 2])
    with col1:
        st.html(f'<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;color:#1A1919;margin-bottom:4px;">REVENUE & EBITDA TREND — {period_range}</div>')
        fig = go.Figure()
        fig.add_bar(x=filtered_df["label"], y=filtered_df["avg_sales"],
                    name="Avg Sales/Stand", marker_color=BLUE, opacity=0.7,
                    yaxis="y1")
        fig.add_scatter(x=filtered_df["label"], y=filtered_df["ebitda_pct"] * 100,
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
        st.plotly_chart(fig, config={"displayModeBar": False})

        # ── Labor % & COGs % Trend ────────────────────────────────────────
        st.html(f'<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;color:#1A1919;margin-bottom:4px;">LABOR % & COGS % TREND — {period_range}</div>')
        fig_lc = go.Figure()
        if "labor_pct" in filtered_df.columns:
            fig_lc.add_scatter(
                x=filtered_df["label"], y=filtered_df["labor_pct"] * 100,
                name="Total Labor %", mode="lines+markers",
                line=dict(color=AMBER, width=2.5), marker=dict(size=6),
            )
        if "cogs_pct" in filtered_df.columns:
            fig_lc.add_scatter(
                x=filtered_df["label"], y=filtered_df["cogs_pct"] * 100,
                name="COGs %", mode="lines+markers",
                line=dict(color=BLUE, width=2.5), marker=dict(size=6),
            )
        fig_lc.update_layout(
            xaxis=dict(tickangle=-35),
            yaxis=dict(ticksuffix="%", tickformat=".1f"),
            legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11)),
        )
        brew_fig(fig_lc, height=280)
        st.plotly_chart(fig_lc, config={"displayModeBar": False})

    with col2:
        # ── Board Narrative — computed from live data ──────────────────────

        # Use the actual company goal if defined for this year, otherwise 20% PE benchmark
        PE_TARGET = goal_ebitda_pct if sel_year in ANNUAL_GOALS else 0.20

        # Trend: first-third vs last-third of selected range
        n_f = len(filtered_df)
        seg = max(n_f // 3, 1)
        rev_trend    = (filtered_df.iloc[-seg:]["avg_sales"].mean() /
                        filtered_df.iloc[:seg]["avg_sales"].mean() - 1) if n_f >= 2 else 0
        ebitda_trend = (filtered_df.iloc[-seg:]["ebitda_pct"].mean() -
                        filtered_df.iloc[:seg]["ebitda_pct"].mean()) if n_f >= 2 else 0

        # Network growth across selected range
        first_stand_cnt = int(filtered_df.iloc[0]["stands"])
        last_stand_cnt  = int(latest["stands"])
        net_new_stands  = last_stand_cnt - first_stand_cnt

        # Gap to PE target
        gap_pts = (avg_ebitda_pct - PE_TARGET) * 100   # positive = above target

        # Best / worst region for the latest period
        latest_reg_df = get_regions_df(dash, latest["period_key"])
        best_reg  = worst_reg = None
        if not latest_reg_df.empty and "ebitda_pct" in latest_reg_df.columns:
            best_reg  = latest_reg_df.loc[latest_reg_df["ebitda_pct"].idxmax()]
            worst_reg = latest_reg_df.loc[latest_reg_df["ebitda_pct"].idxmin()]

        # Mature-stand premium over system
        mature_premium_txt = ""
        if "Age_Bucket" in filtered_stands.columns:
            mature = filtered_stands[filtered_stands["Age_Bucket"] == "Mature (2yr+)"]
            if not mature.empty and mature["Store_EBITDA_pct"].notna().any():
                mat_ebitda = mature["Store_EBITDA_pct"].mean()
                delta_pts   = (mat_ebitda - avg_ebitda_pct) * 100
                mature_premium_txt = (
                    f"Mature stands avg <strong>{_fmt_p(mat_ebitda)}</strong> "
                    f"({delta_pts:+.1f}pts vs system)."
                )

        # Headline + color
        if gap_pts >= 0:
            hl_color = GREEN
            hl_text  = f"ON TARGET · {_fmt_p(avg_ebitda_pct)} EBITDA · ${total_revenue_ytd/1e6:.1f}M"
        elif gap_pts >= -2:
            hl_color = AMBER
            hl_text  = f"NEAR TARGET · {_fmt_p(avg_ebitda_pct)} EBITDA · {abs(gap_pts):.1f}PTS BELOW 20%"
        else:
            hl_color = RED
            hl_text  = f"BELOW TARGET · {_fmt_p(avg_ebitda_pct)} EBITDA · {abs(gap_pts):.1f}PTS GAP"

        # EBITDA trend phrase
        if abs(ebitda_trend * 100) < 0.3:
            ebitda_phrase = "margins are <strong>holding steady</strong>"
        elif ebitda_trend > 0:
            ebitda_phrase = f"margins are <strong>expanding +{ebitda_trend*100:.1f}pts</strong>"
        else:
            ebitda_phrase = f"margins are <strong>compressing {ebitda_trend*100:.1f}pts</strong>"

        # Revenue trend phrase
        rev_arrow  = "▲" if rev_trend > 0.005 else ("▼" if rev_trend < -0.005 else "→")
        rev_color  = GREEN if rev_trend > 0 else (RED if rev_trend < -0.01 else MID)
        ebi_arrow  = "▲" if ebitda_trend > 0.001 else ("▼" if ebitda_trend < -0.001 else "→")
        ebi_color  = GREEN if ebitda_trend > 0 else (RED if ebitda_trend < -0.005 else AMBER)
        net_color  = GREEN if net_new_stands > 0 else MID
        gap_color  = GREEN if gap_pts >= 0 else (AMBER if gap_pts >= -2 else RED)

        # Key lever sentence
        if gap_pts < 0:
            lever = (f"Closing the {abs(gap_pts):.1f}pt gap requires ~${abs(gap_pts)/100 * total_revenue_ytd/n_f/1e3:.0f}k "
                     f"EBITDA improvement per period — achievable through labor scheduling "
                     f"discipline and utility cost control at underperforming stands.")
        else:
            lever = ("Margin is on target. Sustaining performance as new stands ramp "
                     "and protecting labor% during peak seasons are the primary risks.")

        # Regional spread
        reg_html = ""
        if best_reg is not None and worst_reg is not None and best_reg["region"] != worst_reg["region"]:
            spread_pts = (best_reg["ebitda_pct"] - worst_reg["ebitda_pct"]) * 100
            reg_html = (f'<div style="font-size:12px;color:{MID};margin-top:6px;line-height:1.5;">'
                        f'<strong>{best_reg["region"]}</strong> leads at {_fmt_p(best_reg["ebitda_pct"])} · '
                        f'<strong>{worst_reg["region"]}</strong> lags at {_fmt_p(worst_reg["ebitda_pct"])} · '
                        f'{spread_pts:.1f}pt regional spread</div>')

        st.html(f"""
        <div class="story-block" style="height:100%;">
          <div class="story-label">BOARD NARRATIVE · {period_range}</div>
          <div class="story-headline" style="font-size:20px;color:{hl_color};line-height:1.2;margin-bottom:12px;">
            {hl_text}
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">

            <div style="background:#f5f6f8;border-radius:8px;padding:10px 12px;">
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#C5BEBE;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Avg Sales / Stand</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:#1A1919;">{_fmt_d(latest['avg_sales'])}</div>
              <div style="font-size:11px;color:{rev_color};font-weight:600;">{rev_arrow} {rev_trend*100:+.1f}% over period</div>
            </div>

            <div style="background:#f5f6f8;border-radius:8px;padding:10px 12px;">
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#C5BEBE;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">EBITDA Margin</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:#1A1919;">{_fmt_p(avg_ebitda_pct)}</div>
              <div style="font-size:11px;color:{gap_color};font-weight:600;">{gap_pts:+.1f}pts vs 20% target {ebi_arrow}</div>
            </div>

            <div style="background:#f5f6f8;border-radius:8px;padding:10px 12px;">
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#C5BEBE;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">Network Size</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:#1A1919;">{last_stand_cnt} Stands</div>
              <div style="font-size:11px;color:{net_color};font-weight:600;">+{net_new_stands} added · {n_periods} periods shown</div>
            </div>

            <div style="background:#f5f6f8;border-radius:8px;padding:10px 12px;">
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#C5BEBE;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;">EBITDA Trend</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:{ebi_color};">{ebitda_trend*100:+.1f}pts</div>
              <div style="font-size:11px;color:{MID};">first → last third of range</div>
            </div>

          </div>

          {reg_html}

          <div style="font-size:12px;color:#595959;line-height:1.6;margin-top:10px;border-top:1px solid #e2e4e9;padding-top:10px;">
            Over {period_range}, {ebitda_phrase} while avg sales/stand
            {"improved" if rev_trend > 0.005 else ("softened" if rev_trend < -0.005 else "held flat")}
            at {_fmt_d(latest['avg_sales'])}.
            {mature_premium_txt}
            <br>{lever}
          </div>
        </div>""")

    st.html('<hr class="brew">')

    # ── Cohort Analysis — filtered by selected periods ──
    col3, col4 = st.columns(2)
    with col3:
        section("COHORT PERFORMANCE", f"EBITDA% & Labor% by stand maturity — {period_range}")

        age_buckets = ["New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        age_colors  = [RED, AMBER, BLUE, GREEN]

        cohort_rows = []
        for bkt in age_buckets:
            sub = filtered_stands[filtered_stands["Age_Bucket"] == bkt] if "Age_Bucket" in filtered_stands.columns else pd.DataFrame()
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
            st.plotly_chart(fig2, config={"displayModeBar": False})

    with col4:
        # Aggregate regions across selected periods
        section("REGIONAL PERFORMANCE", f"EBITDA% by region — {period_range}")
        reg_frames = [get_regions_df(dash, k) for k in filtered_pks]
        valid_reg_frames = [r for r in reg_frames if not r.empty]
        reg_all = pd.concat(valid_reg_frames, ignore_index=True) if valid_reg_frames else pd.DataFrame()
        if not reg_all.empty:
            pct_cols_r = [c for c in reg_all.columns if c.endswith("_pct")]
            reg_agg = reg_all.groupby("region").agg({"net_sales": "sum"}).reset_index()
            for c in pct_cols_r:
                if c in reg_all.columns:
                    reg_agg[c] = reg_all.groupby("region").apply(
                        lambda g: (g[c] * g["net_sales"]).sum() / g["net_sales"].sum() if g["net_sales"].sum() > 0 else 0
                    ).values
            reg_df = reg_agg.sort_values("ebitda_pct", ascending=False) if "ebitda_pct" in reg_agg.columns else reg_agg
            if "ebitda_pct" in reg_df.columns:
                fig3 = go.Figure(go.Bar(
                    x=reg_df["region"], y=reg_df["ebitda_pct"] * 100,
                    marker_color=[REGION_COLORS.get(r, MID) for r in reg_df["region"]],
                    text=reg_df["ebitda_pct"].map(lambda v: f"{v*100:.1f}%"),
                    textposition="outside",
                ))
                fig3.add_hline(y=avg_ebitda_pct * 100, line_dash="dot",
                               line_color=MID, annotation_text="Sys avg",
                               annotation_font_size=9,
                               annotation_position="top right")
                brew_fig(fig3, height=320)
                fig3.update_layout(yaxis=dict(ticksuffix="%"), showlegend=False)
                st.plotly_chart(fig3, config={"displayModeBar": False}, use_container_width=True)

    st.html('<hr class="brew">')

    # ── Regional Heatmap — filtered by selected periods ──
    section("REGIONAL EBITDA HEATMAP", f"EBITDA% by region × period — {period_range}")
    all_regions = sorted(set(r for pk in filtered_pks for r in [x["region"] for x in dash.get("region_by_period", {}).get(pk, [])]))
    heat_data = []
    for pk in filtered_pks:
        regs = {r["region"]: r["ebitda_pct"] for r in dash.get("region_by_period", {}).get(pk, [])}
        lbl = filtered_df.loc[filtered_df["period_key"]==pk, "label"].values
        row = {"Period": lbl[0] if len(lbl) else pk}
        for reg in all_regions:
            row[reg] = round(regs.get(reg, float("nan")) * 100, 1) if reg in regs else None
        heat_data.append(row)

    if heat_data:
        heat_df = pd.DataFrame(heat_data).set_index("Period")
        fig4 = go.Figure(go.Heatmap(
            z=heat_df.values,
            x=heat_df.columns.tolist(),
            y=heat_df.index.tolist(),
            colorscale=[[0, "#AC2430"], [0.5, "#e8940a"], [1, "#12a06e"]],
            zmid=18, zmin=5, zmax=30,
            text=[[f"{v:.1f}%" if v is not None else "—" for v in row] for row in heat_df.values],
            texttemplate="%{text}",
            textfont=dict(size=9, family="DM Mono"),
            hoverongaps=False,
            colorbar=dict(ticksuffix="%", tickfont=dict(size=9)),
        ))
        brew_fig(fig4, height=max(200, 60 + len(heat_data) * 35))
        fig4.update_layout(xaxis=dict(tickangle=-35))
        st.plotly_chart(fig4, config={"displayModeBar": False})

    st.html('<hr class="brew">')

    # ── Seasonal Watch — data-driven alerts based on upcoming periods ──
    section("SEASONAL WATCH", "Data-driven alerts based on historical patterns and upcoming period trends")

    # Determine what's "next" — look at the period after the latest selected
    latest_pnum = int(latest["period_num"])
    latest_year = int(latest["year"])
    next_periods = list(range(latest_pnum + 1, min(latest_pnum + 4, 14)))  # Next 3 periods

    # Build seasonal pattern from historical data (all periods, not just filtered)
    seasonal_alerts = []

    # Compare current trajectory to same periods in prior year
    prior_year = latest_year - 1
    prior_data = periods_df[periods_df["year"] == prior_year]

    if not prior_data.empty and len(filtered_df) >= 2:
        # Labor trend
        labor_trend = filtered_df["labor_pct"].iloc[-1] - filtered_df["labor_pct"].iloc[0]
        if labor_trend > 0.01:
            seasonal_alerts.append({
                "title": f"📈 Labor Trending Up (+{labor_trend*100:.1f}% pts across selected periods)",
                "body": f"Labor has increased from {_fmt_p(filtered_df['labor_pct'].iloc[0])} to {_fmt_p(filtered_df['labor_pct'].iloc[-1])}. "
                        f"If this trend continues, EBITDA compression of ~{abs(labor_trend)*100:.0f}bps is likely in the next 2–3 periods. "
                        f"Review scheduling compliance and overtime at high-labor stands.",
                "cls": "watch", "tag_cls": "amber",
            })

        # COGS trend
        cogs_trend = filtered_df["cogs_pct"].iloc[-1] - filtered_df["cogs_pct"].iloc[0]
        if cogs_trend > 0.005:
            seasonal_alerts.append({
                "title": f"📦 COGS Creeping Up (+{cogs_trend*100:.1f}% pts)",
                "body": f"COGS moved from {_fmt_p(filtered_df['cogs_pct'].iloc[0])} to {_fmt_p(filtered_df['cogs_pct'].iloc[-1])}. "
                        f"Check vendor pricing, waste rates, and portion control. Even 50bps of COGS savings = ~${filtered_df['net_sales'].mean() * 0.005 / 1000:.0f}k/period.",
                "cls": "watch", "tag_cls": "amber",
            })

        # Utility seasonality alert
        for np_num in next_periods:
            prior_match = prior_data[prior_data["period_num"] == np_num]
            if not prior_match.empty:
                prior_util = prior_match.iloc[0]["utilities_pct"]
                current_util = filtered_df["utilities_pct"].iloc[-1]
                if prior_util > current_util + 0.003:
                    p_label = f"P{np_num}"
                    seasonal_alerts.append({
                        "title": f"⚡ Utility Spike Expected in {p_label}",
                        "body": f"Last year {p_label} hit {_fmt_p(prior_util)} utilities vs current {_fmt_p(current_util)}. "
                                f"{'Summer HVAC load drives this — schedule chiller maintenance before P5.' if np_num in [6,7,8] else 'Seasonal pattern suggests cost increase. Pre-negotiate contracts where possible.'}",
                        "cls": "watch", "tag_cls": "amber",
                    })
                    break  # Only show the nearest one

        # EBITDA momentum
        ebitda_trend = filtered_df["ebitda_pct"].iloc[-1] - filtered_df["ebitda_pct"].iloc[-2] if len(filtered_df) >= 2 else 0
        if ebitda_trend > 0.01:
            seasonal_alerts.append({
                "title": f"🟢 EBITDA Momentum: +{ebitda_trend*10000:.0f}bps period-over-period",
                "body": f"System EBITDA improved from {_fmt_p(filtered_df['ebitda_pct'].iloc[-2])} to {_fmt_p(filtered_df['ebitda_pct'].iloc[-1])}. "
                        f"Protect this by maintaining current labor scheduling and vendor pricing discipline.",
                "cls": "win", "tag_cls": "green",
            })
        elif ebitda_trend < -0.015:
            seasonal_alerts.append({
                "title": f"🔴 EBITDA Slipping: {ebitda_trend*10000:.0f}bps period-over-period",
                "body": f"System EBITDA dropped from {_fmt_p(filtered_df['ebitda_pct'].iloc[-2])} to {_fmt_p(filtered_df['ebitda_pct'].iloc[-1])}. "
                        f"Identify the top 3 contributors — likely labor overrun at ramping stands or seasonal volume softness.",
                "cls": "watch", "tag_cls": "red",
            })

        # Region-specific leakage detection
        if not reg_all.empty and "ebitda_pct" in reg_all.columns:
            # Check for regions losing ground vs prior periods
            for region in reg_all["region"].unique():
                reg_periods = reg_all[reg_all["region"] == region].copy()
                if len(reg_periods) >= 2:
                    # Get region data across the filtered periods and check trend
                    first_ebitda = reg_periods.iloc[0].get("ebitda_pct", 0)
                    last_ebitda = reg_periods.iloc[-1].get("ebitda_pct", 0)
                    if first_ebitda - last_ebitda > 0.03:  # >3% pts decline
                        seasonal_alerts.append({
                            "title": f"📍 {region}: EBITDA declining ({_fmt_p(first_ebitda)} → {_fmt_p(last_ebitda)})",
                            "body": f"This region has dropped {(first_ebitda - last_ebitda)*100:.0f}bps across the selected periods. "
                                    f"Investigate whether this is volume-driven (seasonal) or cost-driven (labor/R&M creep).",
                            "cls": "watch", "tag_cls": "red",
                        })

    if not seasonal_alerts:
        seasonal_alerts.append({
            "title": "✅ No Major Alerts",
            "body": "System metrics are stable across the selected periods. Continue monitoring labor scheduling and vendor pricing.",
            "cls": "win", "tag_cls": "green",
        })

    for alert in seasonal_alerts:
        insight_card(alert["title"], alert["body"],
                     tag=alert.get("cls", "").upper(), tag_cls=alert.get("tag_cls", "amber"),
                     card_cls=alert.get("cls", "watch"))



# ─────────────────────────────────────────────
# TAB: OVERVIEW
# ─────────────────────────────────────────────
def tab_overview(dash):
    periods_df = get_periods_df(dash)
    section("SYSTEM OVERVIEW", "Select period(s) to view performance KPIs and cost structure")

    selected_keys, ps, label_to_key = period_multiselect(periods_df, key="ov_period", label="View Period(s)")

    if not selected_keys or ps is None:
        st.info("Select at least one period above")
        return

    pk = selected_keys[0]  # Primary period key (for region lookups when single)

    # Compare To selector
    all_labels = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    cmp_lbl = st.selectbox("Compare To", [l for l, _ in all_labels][1:] + [all_labels[-1][0]], key="ov_compare")
    pkB = label_to_key.get(cmp_lbl, periods_df.iloc[-2]["period_key"])
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

    # Row 1 — Sales & Cost metrics
    kpi_row([
        {"label": "Total Net Sales",     "value": _fmt_d_short(ps["net_sales"]), "sub": f"{int(ps['stands'])} stands",  "color": "red"},
        {"label": "Avg Sales / Stand",   "value": _fmt_d_short(ps["avg_sales"]), "sub": "per-stand average",            "color": "red",  "delta": avg_delta},
        {"label": "COGS %",              "value": _fmt_p(ps["cogs_pct"]),        "sub": "% of net sales",               "color": "blue", "delta": d(ps["cogs_pct"], psB["cogs_pct"] if psB is not None else 0, inv=True)},
        {"label": "Hourly Labor %",      "value": _fmt_p(ps["hourly_pct"]),      "sub": "wages only",                   "color": "amber",
         "valcls": "good" if ps["hourly_pct"] <= 0.18 else ("bad" if ps["hourly_pct"] > 0.22 else ""),
         "delta": d(ps["hourly_pct"], psB["hourly_pct"] if psB is not None else 0, inv=True)},
        {"label": "Total Labor & Ben %", "value": _fmt_p(ps["labor_pct"]),       "sub": "incl. mgmt & benefits",        "color": "amber",
         "delta": d(ps["labor_pct"], psB["labor_pct"] if psB is not None else 0, inv=True)},
        {"label": "R&M %",               "value": _fmt_p(ps["rm_pct"]),          "sub": "repair & maintenance",         "color": "grey",
         "valcls": "good" if ps["rm_pct"] <= 0.012 else ("bad" if ps["rm_pct"] >= 0.02 else ""),
         "delta": d(ps["rm_pct"], psB["rm_pct"] if psB is not None else 0, inv=True)},
    ])
    # Row 2 — EBITDA & profitability metrics
    kpi_row([
        {"label": "Store EBITDA $",      "value": _fmt_d_short(ps["ebitda"]),    "sub": "total portfolio",              "color": "green"},
        {"label": "Store EBITDA %",      "value": _fmt_p(ps["ebitda_pct"]),      "sub": "% of net sales",               "color": "green",
         "valcls": "good" if ps["ebitda_pct"] >= 0.20 else ("warn" if ps["ebitda_pct"] >= 0.15 else "bad"),
         "delta": d(ps["ebitda_pct"], psB["ebitda_pct"] if psB is not None else 0)},
        {"label": "Unit EBITDAR %",      "value": _fmt_p(ps["ebitdar_pct"]),     "sub": "before rent",                  "color": "green", "valcls": "good"},
        {"label": "Rent %",              "value": _fmt_p(ps["rent_pct"]),        "sub": "occupancy cost",               "color": "grey"},
    ])

    # Charts row 1 — aggregate regions if multi-period
    if len(selected_keys) > 1:
        reg_frames = [get_regions_df(dash, k) for k in selected_keys]
        valid_reg_frames = [r for r in reg_frames if not r.empty]
        reg_all = pd.concat(valid_reg_frames, ignore_index=True) if valid_reg_frames else pd.DataFrame()
        if not reg_all.empty:
            pct_cols = [c for c in reg_all.columns if c.endswith("_pct")]
            # Build agg_dict only for columns that actually exist
            agg_dict = {}
            for col in ["net_sales", "ebitda_total", "ebitda", "avg_sales"]:
                if col in reg_all.columns:
                    agg_dict[col] = "sum" if col != "avg_sales" else "mean"
            if "stands" in reg_all.columns:
                agg_dict["stands"] = "mean"
            if not agg_dict:
                reg_df = pd.DataFrame()
            else:
                reg_df = reg_all.groupby("region").agg(agg_dict).reset_index()
            # Recompute pct from totals
            for c in pct_cols:
                if c in reg_all.columns:
                    reg_df[c] = reg_all.groupby("region").apply(
                        lambda g: (g[c] * g["net_sales"]).sum() / g["net_sales"].sum() if g["net_sales"].sum() > 0 else 0
                    ).values
        else:
            reg_df = pd.DataFrame()
    else:
        reg_df = get_regions_df(dash, pk)

    # ── Cost Structure (donut) + P&L Bridge (waterfall) ─────────────────────
    _cs_other = max(0, 1 - ps["cogs_pct"] - ps["labor_pct"] - ps["rent_pct"] - ps["ebitda_pct"])
    cs_left, cs_right = st.columns(2)
    with cs_left:
        fig_cs = go.Figure(go.Pie(
            labels=["COGS", "Total Labor", "Rent", "Other OpEx", "EBITDA"],
            values=[ps["cogs_pct"], ps["labor_pct"], ps["rent_pct"], _cs_other, ps["ebitda_pct"]],
            hole=0.55,
            marker_colors=[BLUE, AMBER, MID, MUTED, GREEN],
            textinfo="label+percent",
            textfont=dict(size=11, family="DM Mono"),
        ))
        brew_fig(fig_cs, height=360)
        fig_cs.update_layout(title_text="COST STRUCTURE", legend=dict(font=dict(size=10)))
        st.plotly_chart(fig_cs, config={"displayModeBar": False}, use_container_width=True)
    with cs_right:
        bridge_labels = ["Net Sales", "− COGS", "− Labor", "− Rent", "− Other OpEx", "EBITDA"]
        bridge_values = [100, -ps["cogs_pct"]*100, -ps["labor_pct"]*100,
                         -ps["rent_pct"]*100, -_cs_other*100, ps["ebitda_pct"]*100]
        fig_bridge = go.Figure(go.Waterfall(
            orientation="v", measure=["absolute","relative","relative","relative","relative","total"],
            x=bridge_labels, y=bridge_values,
            text=[f"{abs(v):.1f}%" for v in bridge_values], textposition="outside",
            connector=dict(line=dict(color=BORDER, width=1)),
            increasing=dict(marker_color=BLUE), decreasing=dict(marker_color=RED),
            totals=dict(marker_color=GREEN),
        ))
        brew_fig(fig_bridge, height=360)
        fig_bridge.update_layout(title_text="P&L BRIDGE",
                                 yaxis=dict(ticksuffix="%", range=[0, 115]), showlegend=False)
        st.plotly_chart(fig_bridge, config={"displayModeBar": False}, use_container_width=True)

    # ── Region drill-down selector ───────────────────────────────────────────
    all_stands_df = get_stands_df(dash)
    available_regions = sorted(all_stands_df["Region"].dropna().unique().tolist())
    sel_region = st.selectbox(
        "Drill Down by Region",
        ["All Regions"] + available_regions,
        key="ov_region",
    )

    if sel_region == "All Regions":
        # ── System-level regional charts ─────────────────────────────────────
        if not reg_df.empty:
            reg_sorted = reg_df.sort_values("net_sales", ascending=False)
            fig = go.Figure(go.Bar(
                x=reg_sorted["region"], y=reg_sorted["net_sales"],
                marker_color=[REGION_COLORS.get(r, MID) for r in reg_sorted["region"]],
                text=reg_sorted["net_sales"].map(lambda v: f"${v/1000:.0f}k"),
                textposition="outside",
            ))
            brew_fig(fig, height=320)
            fig.update_layout(title_text="NET SALES BY REGION",
                              yaxis=dict(tickprefix="$", tickformat=",.0f"), showlegend=False)
            st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)

            reg_ebi = reg_df.sort_values("ebitda_pct", ascending=False)
            fig2 = go.Figure(go.Bar(
                x=reg_ebi["region"], y=reg_ebi["ebitda_pct"] * 100,
                marker_color=[REGION_COLORS.get(r, MID) for r in reg_ebi["region"]],
                text=reg_ebi["ebitda_pct"].map(lambda v: f"{v*100:.1f}%"),
                textposition="outside",
            ))
            fig2.add_hline(y=ps["ebitda_pct"] * 100, line_dash="dot", line_color=MID,
                           annotation_text="Sys avg", annotation_font_size=9,
                           annotation_position="top right")
            brew_fig(fig2, height=320)
            fig2.update_layout(title_text="EBITDA % BY REGION",
                               yaxis=dict(ticksuffix="%"), showlegend=False)
            st.plotly_chart(fig2, config={"displayModeBar": False}, use_container_width=True)

            if "cogs_pct" in reg_df.columns:
                reg_cogs = reg_df.sort_values("cogs_pct", ascending=False)
                fig_cogs = go.Figure(go.Bar(
                    x=reg_cogs["region"], y=reg_cogs["cogs_pct"] * 100,
                    marker_color=[REGION_COLORS.get(r, MID) for r in reg_cogs["region"]],
                    text=reg_cogs["cogs_pct"].map(lambda v: f"{v*100:.1f}%"),
                    textposition="outside",
                ))
                fig_cogs.add_hline(y=ps["cogs_pct"] * 100, line_dash="dot", line_color=MID,
                                   annotation_text="Sys avg", annotation_font_size=9,
                                   annotation_position="top right")
                brew_fig(fig_cogs, height=320)
                fig_cogs.update_layout(title_text="COGS % BY REGION",
                                       yaxis=dict(ticksuffix="%"), showlegend=False)
                st.plotly_chart(fig_cogs, config={"displayModeBar": False}, use_container_width=True)

            if "labor_pct" in reg_df.columns:
                reg_labor = reg_df.sort_values("labor_pct", ascending=False)
                fig_labor = go.Figure(go.Bar(
                    x=reg_labor["region"], y=reg_labor["labor_pct"] * 100,
                    marker_color=[REGION_COLORS.get(r, MID) for r in reg_labor["region"]],
                    text=reg_labor["labor_pct"].map(lambda v: f"{v*100:.1f}%"),
                    textposition="outside",
                ))
                fig_labor.add_hline(y=ps["labor_pct"] * 100, line_dash="dot", line_color=MID,
                                    annotation_text="Sys avg", annotation_font_size=9,
                                    annotation_position="top right")
                brew_fig(fig_labor, height=320)
                fig_labor.update_layout(title_text="TOTAL LABOR % BY REGION",
                                        yaxis=dict(ticksuffix="%"), showlegend=False)
                st.plotly_chart(fig_labor, config={"displayModeBar": False}, use_container_width=True)

    else:
        # ── Stand-level drill-down for selected region ────────────────────────
        region_color = REGION_COLORS.get(sel_region, BLUE)

        # Aggregate stand data across selected periods for this region
        region_stands = all_stands_df[
            (all_stands_df["Region"] == sel_region) &
            (all_stands_df["Period_Key"].isin(selected_keys))
        ].copy()

        if region_stands.empty:
            st.info(f"No stand data found for {sel_region} in the selected period(s).")
        else:
            # Aggregate across periods if multiple selected
            stand_agg = region_stands.groupby("Stand").agg(
                Net_Sales=("Net_Sales", "sum"),
                Store_EBITDA_pct=("Store_EBITDA_pct", "mean"),
                Total_COGS_pct=("Total_COGS_pct", "mean"),
                Total_Labor_pct=("Total_Labor_pct", "mean"),
            ).reset_index()

            sys_ebitda_avg = ps["ebitda_pct"] * 100
            sys_cogs_avg   = ps["cogs_pct"]   * 100
            sys_labor_avg  = ps["labor_pct"]  * 100

            # Net Sales by Stand
            s_sales = stand_agg.sort_values("Net_Sales", ascending=False)
            fig_s1 = go.Figure(go.Bar(
                x=s_sales["Stand"], y=s_sales["Net_Sales"],
                marker_color=region_color,
                text=s_sales["Net_Sales"].map(lambda v: f"${v/1000:.0f}k"),
                textposition="outside",
            ))
            brew_fig(fig_s1, height=340)
            fig_s1.update_layout(
                title_text=f"NET SALES BY STAND — {sel_region}",
                yaxis=dict(tickprefix="$", tickformat=",.0f"),
                xaxis=dict(tickangle=-40),
                showlegend=False,
            )
            st.plotly_chart(fig_s1, config={"displayModeBar": False}, use_container_width=True)

            # EBITDA % by Stand
            s_ebi = stand_agg.sort_values("Store_EBITDA_pct", ascending=False)
            fig_s2 = go.Figure(go.Bar(
                x=s_ebi["Stand"], y=s_ebi["Store_EBITDA_pct"] * 100,
                marker_color=region_color,
                text=s_ebi["Store_EBITDA_pct"].map(lambda v: f"{v*100:.1f}%"),
                textposition="outside",
            ))
            fig_s2.add_hline(y=sys_ebitda_avg, line_dash="dot", line_color=MID,
                             annotation_text="Sys avg", annotation_font_size=9,
                             annotation_position="top right")
            brew_fig(fig_s2, height=340)
            fig_s2.update_layout(
                title_text=f"EBITDA % BY STAND — {sel_region}",
                yaxis=dict(ticksuffix="%"),
                xaxis=dict(tickangle=-40),
                showlegend=False,
            )
            st.plotly_chart(fig_s2, config={"displayModeBar": False}, use_container_width=True)

            # COGs % by Stand
            s_cogs = stand_agg.sort_values("Total_COGS_pct", ascending=False)
            fig_s3 = go.Figure(go.Bar(
                x=s_cogs["Stand"], y=s_cogs["Total_COGS_pct"] * 100,
                marker_color=region_color,
                text=s_cogs["Total_COGS_pct"].map(lambda v: f"{v*100:.1f}%"),
                textposition="outside",
            ))
            fig_s3.add_hline(y=sys_cogs_avg, line_dash="dot", line_color=MID,
                             annotation_text="Sys avg", annotation_font_size=9,
                             annotation_position="top right")
            brew_fig(fig_s3, height=340)
            fig_s3.update_layout(
                title_text=f"COGS % BY STAND — {sel_region}",
                yaxis=dict(ticksuffix="%"),
                xaxis=dict(tickangle=-40),
                showlegend=False,
            )
            st.plotly_chart(fig_s3, config={"displayModeBar": False}, use_container_width=True)

            # Labor % by Stand
            s_labor = stand_agg.sort_values("Total_Labor_pct", ascending=False)
            fig_s4 = go.Figure(go.Bar(
                x=s_labor["Stand"], y=s_labor["Total_Labor_pct"] * 100,
                marker_color=region_color,
                text=s_labor["Total_Labor_pct"].map(lambda v: f"{v*100:.1f}%"),
                textposition="outside",
            ))
            fig_s4.add_hline(y=sys_labor_avg, line_dash="dot", line_color=MID,
                             annotation_text="Sys avg", annotation_font_size=9,
                             annotation_position="top right")
            brew_fig(fig_s4, height=340)
            fig_s4.update_layout(
                title_text=f"TOTAL LABOR % BY STAND — {sel_region}",
                yaxis=dict(ticksuffix="%"),
                xaxis=dict(tickangle=-40),
                showlegend=False,
            )
            st.plotly_chart(fig_s4, config={"displayModeBar": False}, use_container_width=True)

    # ── Performance by Stand Maturity ─────────────────────────────────────────
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
        brew_fig(fig3, height=320)
        fig3.update_layout(title_text="PERFORMANCE BY STAND MATURITY",
                           yaxis=dict(ticksuffix="%"))
        st.plotly_chart(fig3, config={"displayModeBar": False}, use_container_width=True)


# ─────────────────────────────────────────────
# TAB: PERIOD COMPARISON
# ─────────────────────────────────────────────
def tab_comparison(dash):
    periods_df = get_periods_df(dash)
    section("PERIOD COMPARISON", "Head-to-head breakdown — sales, costs, EBITDA, and stand-level distribution")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}

    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        lbl_a = st.selectbox("Period A", [l for l, _ in all_options], key="cmp_a")
    with c2:
        st.html('<div style="text-align:center;font-family:Bebas Neue,sans-serif;font-size:28px;'
                'color:#AC2430;padding-top:26px;letter-spacing:2px;">VS</div>')
    with c3:
        lbl_b = st.selectbox("Period B", [l for l, _ in all_options][1:], key="cmp_b")

    pka = label_to_key[lbl_a]
    pkb = label_to_key.get(lbl_b)
    psA = periods_df[periods_df["period_key"] == pka].iloc[0]
    psB = periods_df[periods_df["period_key"] == pkb].iloc[0] if pkb else None

    if psB is None:
        st.warning("Select a second period to compare.")
        return

    # ── Scorecard row ─────────────────────────────────────────────────────────
    metrics_def = [
        ("Avg Sales/Stand", "avg_sales",   True,  True),
        ("Store EBITDA %",  "ebitda_pct",  False, True),
        ("Total Labor %",   "labor_pct",   False, False),
        ("COGS %",          "cogs_pct",    False, False),
        ("Discount %",      "discount_pct",False, False),
        ("R&M %",           "rm_pct",      False, False),
    ]
    score_cols = st.columns(len(metrics_def))
    for i, (m_label, field, is_dollar, higher_good) in enumerate(metrics_def):
        va = float(psA.get(field, 0) or 0)
        vb = float(psB.get(field, 0) or 0)
        delta = va - vb
        is_better = (delta > 0) if higher_good else (delta < 0)
        arrow   = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        a_color = GREEN if is_better else RED
        fmt_va  = _fmt_d(va) if is_dollar else _fmt_p(va)
        fmt_vb  = _fmt_d(vb) if is_dollar else _fmt_p(vb)
        fmt_d   = (f"+${abs(delta)/1000:.1f}k" if delta >= 0 else f"-${abs(delta)/1000:.1f}k") if is_dollar else _fmt_bps(delta)
        with score_cols[i]:
            st.html(f"""
            <div style="background:#f8f8f8;border-radius:10px;padding:14px 10px;text-align:center;
                        border-top:3px solid {a_color};margin-bottom:8px;">
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#595959;
                          text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{m_label}</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:20px;color:#1A1919;">{fmt_va}</div>
              <div style="font-family:'DM Mono',monospace;font-size:10px;color:#595959;margin:2px 0;">
                vs {fmt_vb}
              </div>
              <div style="font-family:'DM Mono',monospace;font-size:12px;font-weight:bold;color:{a_color};">
                {arrow} {fmt_d}
              </div>
            </div>""")

    # ── Biggest Movers ────────────────────────────────────────────────────────
    all_metrics = [
        ("Avg Net Sales",       "avg_sales",        True,  True),
        ("Store EBITDA %",      "ebitda_pct",       False, True),
        ("Unit EBITDAR %",      "ebitdar_pct",      False, True),
        ("Total Labor %",       "labor_pct",        False, False),
        ("Hourly Labor %",      "hourly_pct",       False, False),
        ("COGS %",              "cogs_pct",         False, False),
        ("Rent %",              "rent_pct",         False, False),
        ("Discount %",          "discount_pct",     False, False),
        ("R&M %",               "rm_pct",           False, False),
        ("Utilities %",         "utilities_pct",    False, False),
        ("Controllable %",      "controllable_pct", False, False),
        ("Marketing %",         "marketing_pct",    False, False),
    ]
    mover_rows = []
    for m_label, field, is_dollar, higher_good in all_metrics:
        va = float(psA.get(field, 0) or 0)
        vb = float(psB.get(field, 0) or 0)
        if va == 0 and vb == 0:
            continue
        delta = va - vb
        is_positive = (delta > 0) if higher_good else (delta < 0)
        magnitude = abs(delta)
        mover_rows.append({
            "label": m_label, "field": field, "is_dollar": is_dollar,
            "higher_good": higher_good, "va": va, "vb": vb,
            "delta": delta, "is_positive": is_positive, "magnitude": magnitude
        })
    mover_rows.sort(key=lambda x: x["magnitude"], reverse=True)
    top_improvements = [r for r in mover_rows if r["is_positive"]][:3]
    top_concerns     = [r for r in mover_rows if not r["is_positive"]][:3]

    mv_col1, mv_col2 = st.columns(2)
    with mv_col1:
        st.html(f'<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;'
                f'color:{GREEN};margin:12px 0 6px;">▲ BIGGEST IMPROVEMENTS — {psA["label"]} vs {psB["label"]}</div>')
        for r in top_improvements:
            fmt_d = (f"+${r['delta']/1000:.1f}k" if r["is_dollar"] else _fmt_bps(r["delta"]))
            insight_card(
                f"↑ {r['label']}: {_fmt_d(r['va']) if r['is_dollar'] else _fmt_p(r['va'])}",
                f"Up from {_fmt_d(r['vb']) if r['is_dollar'] else _fmt_p(r['vb'])} in {psB['label']} — a {fmt_d} improvement.",
                tag=fmt_d, tag_cls="green", card_cls="win",
            )
    with mv_col2:
        st.html(f'<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;'
                f'color:{RED};margin:12px 0 6px;">▼ BIGGEST DECLINES — {psA["label"]} vs {psB["label"]}</div>')
        for r in top_concerns:
            fmt_d = _fmt_bps(r["delta"]) if not r["is_dollar"] else f"-${abs(r['delta'])/1000:.1f}k"
            insight_card(
                f"↓ {r['label']}: {_fmt_d(r['va']) if r['is_dollar'] else _fmt_p(r['va'])}",
                f"Down from {_fmt_d(r['vb']) if r['is_dollar'] else _fmt_p(r['vb'])} in {psB['label']} — a {fmt_d} move.",
                tag=fmt_d, tag_cls="red",
            )

    # ── Radar chart + Regional EBITDA side-by-side ────────────────────────────
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        # Radar: normalize each metric to 0–1 scale for visual comparison
        radar_fields = ["ebitda_pct", "ebitdar_pct", "labor_pct", "cogs_pct", "discount_pct", "rm_pct"]
        radar_labels = ["EBITDA %", "EBITDAR %", "Labor %", "COGS %", "Discount %", "R&M %"]
        # For cost metrics (lower=better), invert so "bigger is better" on radar
        invert = [False, False, True, True, True, True]
        vals_a, vals_b = [], []
        for fld, inv in zip(radar_fields, invert):
            va_r = float(psA.get(fld, 0) or 0) * 100
            vb_r = float(psB.get(fld, 0) or 0) * 100
            all_v = [float(periods_df[fld].max()) * 100, float(periods_df[fld].min()) * 100]
            rng = (max(all_v) - min(all_v)) or 1
            na = (va_r - min(all_v)) / rng
            nb = (vb_r - min(all_v)) / rng
            vals_a.append(1 - na if inv else na)
            vals_b.append(1 - nb if inv else nb)
        # close the polygon
        vals_a += [vals_a[0]]
        vals_b += [vals_b[0]]
        lbl_loop = radar_labels + [radar_labels[0]]
        fig_radar = go.Figure()
        fig_radar.add_scatterpolar(r=vals_a, theta=lbl_loop, fill="toself", name=psA["label"],
                                   line=dict(color=RED, width=2), opacity=0.5)
        fig_radar.add_scatterpolar(r=vals_b, theta=lbl_loop, fill="toself", name=psB["label"],
                                   line=dict(color=BLUE, width=2), opacity=0.4)
        brew_fig(fig_radar, height=340)
        fig_radar.update_layout(
            title_text="PERFORMANCE RADAR",
            polar=dict(radialaxis=dict(visible=False, range=[0, 1])),
            legend=dict(orientation="h", y=-0.12),
        )
        st.plotly_chart(fig_radar, config={"displayModeBar": False}, use_container_width=True)

    with col_r2:
        reg_a = pd.DataFrame(dash["region_by_period"].get(pka, []))
        reg_b = pd.DataFrame(dash["region_by_period"].get(pkb, []))
        if not reg_a.empty and not reg_b.empty:
            merged = reg_a.merge(reg_b, on="region", suffixes=("_a", "_b"))
            merged = merged.sort_values("ebitda_pct_a", ascending=False)
            fig_reg = go.Figure()
            fig_reg.add_bar(x=merged["region"], y=merged["ebitda_pct_a"] * 100,
                            name=psA["label"], marker_color=RED, opacity=0.85)
            fig_reg.add_bar(x=merged["region"], y=merged["ebitda_pct_b"] * 100,
                            name=psB["label"], marker_color=BLUE, opacity=0.65)
            brew_fig(fig_reg, height=340)
            fig_reg.update_layout(title_text="EBITDA % BY REGION",
                                  barmode="group", yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig_reg, config={"displayModeBar": False}, use_container_width=True)

    # ── Side-by-side P&L Bridge ───────────────────────────────────────────────
    st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;'
            'color:#1A1919;margin:16px 0 4px;">P&L BRIDGE COMPARISON</div>')
    bridge_col1, bridge_col2 = st.columns(2)
    for col, ps_x, color, lbl_x in [(bridge_col1, psA, RED, psA["label"]),
                                      (bridge_col2, psB, BLUE, psB["label"])]:
        with col:
            _oth = max(0, 1 - ps_x["cogs_pct"] - ps_x["labor_pct"] - ps_x["rent_pct"] - ps_x["ebitda_pct"])
            bv = [100, -ps_x["cogs_pct"]*100, -ps_x["labor_pct"]*100,
                  -ps_x["rent_pct"]*100, -_oth*100, ps_x["ebitda_pct"]*100]
            fig_b = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute","relative","relative","relative","relative","total"],
                x=["Net Sales","− COGS","− Labor","− Rent","− Other","EBITDA"],
                y=bv,
                text=[f"{abs(v):.1f}%" for v in bv], textposition="outside",
                connector=dict(line=dict(color=BORDER, width=1)),
                increasing=dict(marker_color=color),
                decreasing=dict(marker_color=RED),
                totals=dict(marker_color=GREEN),
            ))
            brew_fig(fig_b, height=300)
            fig_b.update_layout(title_text=f"P&L BRIDGE — {lbl_x}",
                                yaxis=dict(ticksuffix="%", range=[0, 115]), showlegend=False)
            st.plotly_chart(fig_b, config={"displayModeBar": False}, use_container_width=True)

    # ── Stand distribution comparison ─────────────────────────────────────────
    stands_df = get_stands_df(dash)
    sa = stands_df[stands_df["Period_Key"] == pka]
    sb = stands_df[stands_df["Period_Key"] == pkb]

    st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;'
            'color:#1A1919;margin:16px 0 4px;">STAND-LEVEL DISTRIBUTION</div>')
    dist_col1, dist_col2 = st.columns(2)
    with dist_col1:
        if not sa.empty and not sb.empty:
            fig_lh = go.Figure()
            fig_lh.add_histogram(x=sa["Total_Labor_pct"]*100, name=psA["label"],
                                 marker_color=RED, opacity=0.65, nbinsx=12)
            fig_lh.add_histogram(x=sb["Total_Labor_pct"]*100, name=psB["label"],
                                 marker_color=BLUE, opacity=0.55, nbinsx=12)
            brew_fig(fig_lh, height=260)
            fig_lh.update_layout(title_text="LABOR % — STAND DISTRIBUTION",
                                 barmode="overlay", xaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig_lh, config={"displayModeBar": False}, use_container_width=True)
    with dist_col2:
        if not sa.empty and not sb.empty:
            fig_eh = go.Figure()
            fig_eh.add_histogram(x=sa["Store_EBITDA_pct"]*100, name=psA["label"],
                                 marker_color=RED, opacity=0.65, nbinsx=12)
            fig_eh.add_histogram(x=sb["Store_EBITDA_pct"]*100, name=psB["label"],
                                 marker_color=BLUE, opacity=0.55, nbinsx=12)
            brew_fig(fig_eh, height=260)
            fig_eh.update_layout(title_text="EBITDA % — STAND DISTRIBUTION",
                                 barmode="overlay", xaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig_eh, config={"displayModeBar": False}, use_container_width=True)

    # ── Region & Stand Drill-Down ─────────────────────────────────────────────
    st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;'
            'color:#1A1919;margin:20px 0 6px;">REGION & STAND DRILL-DOWN</div>')
    dd_c1, dd_c2, dd_c3 = st.columns([2, 2, 2])
    with dd_c1:
        avail_regions = sorted(sa["Region"].dropna().unique().tolist()) if not sa.empty else []
        sel_cmp_region = st.selectbox("Filter by Region", ["All Regions"] + avail_regions, key="cmp_region")
    with dd_c2:
        sort_metric = st.selectbox("Compare by Metric",
            ["EBITDA %", "Labor %", "COGS %", "Net Sales", "Discount %", "R&M %"],
            key="cmp_sort_metric")
    with dd_c3:
        sort_asc = st.radio("Sort Order", ["High → Low", "Low → High"],
                            key="cmp_sort_dir", horizontal=True) == "Low → High"

    _metric_map = {
        "EBITDA %":    ("Store_EBITDA_pct", False),
        "Labor %":     ("Total_Labor_pct",  False),
        "COGS %":      ("Total_COGS_pct",   False),
        "Net Sales":   ("Net_Sales",        True),
        "Discount %":  ("Discounts_pct",    False),
        "R&M %":       ("Total_RM_pct",     False),
    }
    _scol, _is_dollar = _metric_map[sort_metric]

    sa_drill = sa[sa["Region"] == sel_cmp_region].copy() if sel_cmp_region != "All Regions" else sa.copy()
    sb_drill = sb[sb["Region"] == sel_cmp_region].copy() if sel_cmp_region != "All Regions" else sb.copy()

    if not sa_drill.empty and _scol in sa_drill.columns:
        _ms = sa_drill[["Stand", _scol]].merge(
            sb_drill[["Stand", _scol]], on="Stand", suffixes=("_a", "_b"), how="outer"
        ).sort_values(f"{_scol}_a", ascending=sort_asc, na_position="last")
        _ms["_label"] = _ms["Stand"].str.split(",").str[0]
        _mult = 1 if _is_dollar else 100
        _tick_sfx = "" if _is_dollar else "%"
        _tick_pfx = "$" if _is_dollar else ""

        fig_drill = go.Figure()
        fig_drill.add_bar(x=_ms["_label"], y=_ms[f"{_scol}_a"] * _mult,
                          name=psA["label"], marker_color=RED, opacity=0.88,
                          text=(_ms[f"{_scol}_a"] * _mult).map(
                              lambda v: f"${v:,.0f}" if _is_dollar else f"{v:.1f}%"),
                          textposition="outside", textfont=dict(size=9))
        fig_drill.add_bar(x=_ms["_label"], y=_ms[f"{_scol}_b"] * _mult,
                          name=psB["label"], marker_color=BLUE, opacity=0.65,
                          text=(_ms[f"{_scol}_b"] * _mult).map(
                              lambda v: f"${v:,.0f}" if _is_dollar else f"{v:.1f}%"),
                          textposition="outside", textfont=dict(size=9))
        _title_region = sel_cmp_region if sel_cmp_region != "All Regions" else "ALL REGIONS"
        brew_fig(fig_drill, height=340)
        fig_drill.update_layout(
            title_text=f"{sort_metric.upper()} BY STAND — {_title_region}",
            barmode="group",
            xaxis=dict(tickangle=-40, tickfont=dict(size=9)),
            yaxis=dict(ticksuffix=_tick_sfx, tickprefix=_tick_pfx,
                       tickformat=",.0f" if _is_dollar else ".1f"),
            legend=dict(orientation="h", y=1.1, x=0),
        )
        st.plotly_chart(fig_drill, config={"displayModeBar": False}, use_container_width=True)
    else:
        st.info("No stand data available for the selected filters.")

    # ── Full metric table (collapsible) ───────────────────────────────────────
    with st.expander("Full Metric Table"):
        rows = []
        for m_label, field, is_dollar, higher_good in all_metrics:
            va = float(psA.get(field, 0) or 0)
            vb = float(psB.get(field, 0) or 0)
            delta = va - vb
            good = (delta > 0) if higher_good else (delta < 0)
            rows.append({
                "Metric": m_label,
                f"{psA['label']} (A)": _fmt_d(va) if is_dollar else _fmt_p(va),
                f"{psB['label']} (B)": _fmt_d(vb) if is_dollar else _fmt_p(vb),
                "Δ A − B": (f"+${delta/1000:.1f}k" if is_dollar else _fmt_bps(delta)),
                "Signal": "↑ Better" if good else "↓ Worse",
            })
        render_table(pd.DataFrame(rows))


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
        try:
            if "Region" in stands_df.columns and len(stands_df) > 0:
                regions = ["All Regions"] + sorted(stands_df["Region"].dropna().unique().tolist())
            else:
                regions = ["All Regions"]
        except (KeyError, TypeError, AttributeError):
            regions = ["All Regions"]
        sel_reg = st.selectbox("Region", regions, key="std_region")
    with c3:
        ages = ["All Ages", "New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        sel_age = st.selectbox("Age Bucket", ages, key="std_age")
    with c4:
        search = st.text_input("Search Stands", placeholder="Type stand name...", key="std_search")

    pk = label_to_key[sel_lbl]
    df = stands_df[stands_df["Period_Key"] == pk].copy()
    if sel_reg != "All Regions" and "Region" in df.columns:
        df = df[df["Region"] == sel_reg]
    if sel_age != "All Ages" and "Age_Bucket" in df.columns:
        df = df[df["Age_Bucket"] == sel_age]
    if search and "Stand" in df.columns:
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
    # Only select columns that exist in the dataframe
    available_cols = [col for col in display_cols.keys() if col in df.columns]
    disp = df[available_cols].rename(columns={k: v for k, v in display_cols.items() if k in available_cols}).copy()
    for col in ["COGS%", "Hourly%", "Labor%", "R&M%", "Ctrl%", "Util%",
                "Fixed%", "EBITDAR%", "Rent%", "EBITDA%", "Disc%"]:
        if col in disp.columns:
            disp[col] = disp[col].map(lambda v: f"{v*100:.1f}%" if pd.notna(v) else "—")
    disp["Net Sales"] = disp["Net Sales"].map(lambda v: f"${v:,.0f}" if pd.notna(v) else "—")

    render_table(disp)


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

    # Drill-down: Show stands by selected region
    section("STANDS BY REGION", "Click on a region below to view its stands")
    region_list = sorted(reg_df["region"].unique().tolist())
    sel_region = st.selectbox("Select Region to Drill Down", region_list, key="region_drilldown")

    if sel_region:
        region_stands = stands_df[(stands_df["Period_Key"] == pk) & (stands_df["Region"] == sel_region)].copy()
        if not region_stands.empty:
            st.caption(f"**{sel_region}** - {len(region_stands)} stands")
            # Display stands in selected region
            display_cols_region = ["Stand", "Net_Sales", "Store_EBITDA_pct", "Total_COGS_pct", "Total_Labor_pct"]
            display_cols_region = [c for c in display_cols_region if c in region_stands.columns]
            tbl = region_stands[display_cols_region].copy()
            if "Net_Sales" in tbl.columns:
                tbl["Net_Sales"] = tbl["Net_Sales"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
            for pct_col in ["Store_EBITDA_pct", "Total_COGS_pct", "Total_Labor_pct"]:
                if pct_col in tbl.columns:
                    tbl[pct_col] = tbl[pct_col].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
            render_table(tbl.reset_index(drop=True))
        else:
            st.info(f"No stand data available for {sel_region} in this period.")

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
        fig.update_layout(title_text="LABOR% vs EBITDA% (bubble = sales volume)",
                          xaxis=dict(ticksuffix="%", title="Total Labor %"),
                          yaxis=dict(ticksuffix="%", title="EBITDA %"),
                          showlegend=False)
        brew_fig(fig, height=420)
        st.plotly_chart(fig, config={"displayModeBar": False})

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
        fig2.update_layout(title_text="COST STACK BY REGION",
                           barmode="stack", yaxis=dict(ticksuffix="%"))
        brew_fig(fig2, height=420, margin=dict(t=60, b=100, l=8, r=8))
        st.plotly_chart(fig2, config={"displayModeBar": False})

    # ── STAND DETAIL ──────────────────────────────────────────────────────────
    st.html('<hr class="brew">')
    section("STAND DETAIL", f"Filter, sort, and drill into individual stand performance · {sel_lbl}")

    sd_c1, sd_c2, sd_c3 = st.columns([1.5, 1.5, 2])
    with sd_c1:
        try:
            if "Region" in stands_df.columns and len(stands_df) > 0:
                sd_regions = ["All Regions"] + sorted(stands_df["Region"].dropna().unique().tolist())
            else:
                sd_regions = ["All Regions"]
        except Exception:
            sd_regions = ["All Regions"]
        sd_reg = st.selectbox("Region", sd_regions, key="reg_sd_region")
    with sd_c2:
        sd_ages = ["All Ages", "New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        sd_age  = st.selectbox("Age Bucket", sd_ages, key="reg_sd_age")
    with sd_c3:
        sd_search = st.text_input("Search Stands", placeholder="Type stand name...", key="reg_sd_search")

    sd_df = stands_df[stands_df["Period_Key"] == pk].copy()
    if sd_reg != "All Regions" and "Region" in sd_df.columns:
        sd_df = sd_df[sd_df["Region"] == sd_reg]
    if sd_age != "All Ages" and "Age_Bucket" in sd_df.columns:
        sd_df = sd_df[sd_df["Age_Bucket"] == sd_age]
    if sd_search and "Stand" in sd_df.columns:
        sd_df = sd_df[sd_df["Stand"].str.contains(sd_search, case=False, na=False)]

    st.caption(f"Showing {len(sd_df)} stands")

    display_cols = {
        "Stand": "Stand", "Region": "Region", "Age_Bucket": "Age",
        "Net_Sales": "Net Sales", "Total_COGS_pct": "COGS%",
        "Total_Hourly_pct": "Hourly%", "Total_Labor_pct": "Labor%",
        "Total_RM_pct": "R&M%", "Controllable_pct": "Ctrl%",
        "Total_Utilities_pct": "Util%", "Total_Fixed_pct": "Fixed%",
        "Unit_EBITDAR_pct": "EBITDAR%", "Total_Rent_pct": "Rent%",
        "Store_EBITDA_pct": "EBITDA%", "Discounts_pct": "Disc%",
    }
    avail = [c for c in display_cols if c in sd_df.columns]
    disp  = sd_df[avail].rename(columns={k: v for k, v in display_cols.items() if k in avail}).copy()
    for col in ["COGS%","Hourly%","Labor%","R&M%","Ctrl%","Util%",
                "Fixed%","EBITDAR%","Rent%","EBITDA%","Disc%"]:
        if col in disp.columns:
            disp[col] = disp[col].map(lambda v: f"{v*100:.1f}%" if pd.notna(v) else "—")
    if "Net Sales" in disp.columns:
        disp["Net Sales"] = disp["Net Sales"].map(lambda v: f"${v:,.0f}" if pd.notna(v) else "—")
    render_table(disp)

    # ── 🌱 Store Cohort / Ramp Analysis ─────────────────────────────────────
    st.html('<hr class="brew">')
    period_lbl = ps["label"] if hasattr(ps, "__getitem__") else str(pk)
    section("🌱 STORE COHORT ANALYSIS",
            f"Avg performance by stand maturity — {period_lbl} · uses the period selected above")

    # ── Opening-year filter ───────────────────────────────────────────────────
    # Derive the opening year for every stand from its "Open Date" field
    all_period_stands = stands_df[stands_df["Period_Key"] == pk].copy()
    all_period_stands = all_period_stands[
        all_period_stands["Age_Bucket"].notna() & all_period_stands["Net_Sales"].notna()
    ]
    if "Open Date" in all_period_stands.columns:
        all_period_stands["_open_year"] = (
            pd.to_datetime(all_period_stands["Open Date"], errors="coerce").dt.year
        )
    else:
        all_period_stands["_open_year"] = None

    open_years = sorted([
        y for y in all_period_stands["_open_year"].dropna().unique().astype(int)
    ])
    year_options = ["All"] + [str(y) for y in open_years]

    dc1, dc2 = st.columns([1, 3])
    with dc1:
        sel_open_yr = st.selectbox(
            "Filter by opening year",
            year_options,
            index=0,
            key="cohort_open_year",
            help="Show only stands that first opened in the selected year",
        )

    if sel_open_yr == "All":
        period_stands = all_period_stands.copy()
        yr_label = "all opening years"
    else:
        period_stands = all_period_stands[
            all_period_stands["_open_year"] == int(sel_open_yr)
        ].copy()
        yr_label = f"opened {sel_open_yr}"

    # Ramp curve needs all periods to trace the opening-week trajectory
    # (also apply the same year filter so the ramp reflects that cohort only)
    ramp_all = stands_df[stands_df["Age_Bucket"].notna() & stands_df["Net_Sales"].notna()].copy()
    if "Open Date" in ramp_all.columns:
        ramp_all["_open_year"] = pd.to_datetime(ramp_all["Open Date"], errors="coerce").dt.year
    if sel_open_yr == "All":
        ramp_stands = ramp_all.copy()
    else:
        ramp_stands = ramp_all[ramp_all["_open_year"] == int(sel_open_yr)].copy()

    bucket_order  = ["New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
    bucket_colors = {"New (<6mo)": "#FF6B00", "Young (6-12mo)": "#F5A623",
                     "Developing (1-2yr)": "#4A90E2", "Mature (2yr+)": "#12a06e"}

    # ── Cohort KPI strip ─────────────────────────────────────────────────────
    cohort_agg = (period_stands.groupby("Age_Bucket")
                  .agg(avg_sales=("Net_Sales","mean"),
                       avg_ebitda=("Store_EBITDA_pct","mean"),
                       avg_labor=("Total_Labor_pct","mean"),
                       n_stands=("Stand","nunique"))
                  .reindex(bucket_order).reset_index())

    mature_row  = cohort_agg[cohort_agg["Age_Bucket"] == "Mature (2yr+)"]
    blend_avg   = period_stands["Net_Sales"].mean()
    mature_avg  = mature_row["avg_sales"].values[0] if not mature_row.empty else blend_avg
    dilution    = mature_avg - blend_avg

    ck1, ck2, ck3, ck4 = st.columns(4)
    ck1.metric("Mature Store Avg Sales", f"${mature_avg:,.0f}",
               help=f"Avg net sales for 2yr+ stands in {period_lbl}")
    ck2.metric(f"{period_lbl} System Avg", f"${blend_avg:,.0f}",
               delta=f"${dilution:+,.0f} vs mature",
               delta_color="inverse" if dilution < 0 else "normal",
               help="Blended average across all stands this period — matches Period Summary above")
    if not mature_row.empty:
        ck3.metric("Mature Store Avg EBITDA%",
                   f"{mature_row['avg_ebitda'].values[0]*100:.1f}%",
                   help="EBITDA margin for 2yr+ stands this period")
        new_row = cohort_agg[cohort_agg["Age_Bucket"] == "New (<6mo)"]
        ck4.metric("New Stand Avg EBITDA%",
                   f"{new_row['avg_ebitda'].mean()*100:.1f}%" if not new_row.empty else "—",
                   help="EBITDA margin for stands in first 6 months this period")

    st.caption(f"All metrics above reflect {period_lbl} · {yr_label}. Mature stores run at higher margins because labor is fully trained, volume is established, and pre-opening costs are absorbed.")

    # ── Side-by-side cohort charts ────────────────────────────────────────────
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown(f"**Avg Net Sales by Cohort** *({period_lbl} · {yr_label})*")
        fig_sales = go.Figure()
        for _, crow in cohort_agg.dropna(subset=["avg_sales"]).iterrows():
            bkt = crow["Age_Bucket"]
            fig_sales.add_bar(
                x=[bkt], y=[crow["avg_sales"]],
                name=bkt, marker_color=bucket_colors.get(bkt, "#999"),
                text=[f"${crow['avg_sales']:,.0f}<br>({int(crow['n_stands'])} stands)"],
                textposition="outside", showlegend=False,
            )
        fig_sales.add_hline(y=blend_avg, line_dash="dash",
                            line_color="rgba(255,255,255,0.4)",
                            annotation_text=f"Period avg ${blend_avg:,.0f}",
                            annotation_position="top right",
                            annotation_font_color="rgba(255,255,255,0.5)")
        fig_sales.update_layout(template="plotly_dark", height=300,
                                margin=dict(t=30,b=20,l=0,r=0),
                                yaxis_title="Avg Net Sales ($)", bargap=0.35)
        st.plotly_chart(fig_sales, use_container_width=True)

    with ch2:
        st.markdown(f"**Avg EBITDA% & Labor% by Cohort** *({period_lbl} · {yr_label})*")
        fig_pct = go.Figure()
        for _, crow in cohort_agg.dropna(subset=["avg_ebitda"]).iterrows():
            bkt = crow["Age_Bucket"]
            fig_pct.add_bar(
                x=[bkt], y=[crow["avg_ebitda"] * 100],
                name="EBITDA%", marker_color=bucket_colors.get(bkt, "#999"),
                opacity=0.9, showlegend=False,
                text=[f"{crow['avg_ebitda']*100:.1f}%"], textposition="outside",
            )
        fig_pct.add_scatter(
            x=cohort_agg.dropna(subset=["avg_labor"])["Age_Bucket"].tolist(),
            y=(cohort_agg.dropna(subset=["avg_labor"])["avg_labor"] * 100).tolist(),
            name="Labor%", mode="lines+markers",
            line=dict(color="#F5A623", width=2),
            showlegend=True,
        )
        fig_pct.update_layout(template="plotly_dark", height=300,
                              margin=dict(t=30,b=20,l=0,r=0),
                              yaxis_title="% of Net Sales",
                              legend=dict(orientation="h", y=1.1), bargap=0.35)
        st.plotly_chart(fig_pct, use_container_width=True)

    # ── Revenue ramp curve (all-time — needs multiple periods to trace trajectory) ──
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        st.markdown(f"**Revenue Ramp Curve** — Average net sales by period since opening *({yr_label})*")
    with rc2:
        ramp_view = st.selectbox(
            "Break out by",
            ["System Average", "By State", "Individual Stands"],
            key="ramp_view_mode",
            label_visibility="collapsed",
        )

    # Compute periods-since-open for all ramp stands
    ramp_stands["age_yrs_num"] = ramp_stands.apply(
        lambda r: _age_yrs_from_period(r.get("Open Date", ""), r.get("Period_Key", "")), axis=1
    )
    ramp_stands["periods_since_open"] = (
        ramp_stands["age_yrs_num"].fillna(0) * 13
    ).round().astype(int).clip(0, 39)

    # Derive state from Region column (FL / OK / TX)
    def _state_from_region(region):
        r = str(region).upper()
        if "FL" in r or "FLORIDA" in r or "PANHANDLE" in r or "WEST COAST" in r:
            return "FL"
        if "OK" in r or "OKLAHOMA" in r:
            return "OK"
        if "TX" in r or "TEXAS" in r or "CENTRAL" in r or "PERMIAN" in r or "MIDDLE EARTH" in r:
            return "TX"
        return "Other"

    if "Region" in ramp_stands.columns:
        ramp_stands["_state"] = ramp_stands["Region"].apply(_state_from_region)
    else:
        ramp_stands["_state"] = "Unknown"

    # System-average curve (used as reference line in all views)
    sys_curve = (ramp_stands.groupby("periods_since_open")
                 .agg(avg_sales=("Net_Sales","mean"), stand_count=("Stand","nunique"))
                 .reset_index())
    sys_curve = sys_curve[sys_curve["periods_since_open"] <= 30]

    # State color palette
    state_colors = {"TX": "#F5A623", "FL": "#12a06e", "OK": "#AC2430", "Other": "#888888"}

    fig_ramp = go.Figure()

    # Background age-zone shading
    for x0, x1, color, label in [
        (0,   6.5, "rgba(255,107,0,0.08)",  "New (<6mo)"),
        (6.5, 13,  "rgba(245,166,35,0.06)", "Young"),
        (13,  26,  "rgba(74,144,226,0.05)", "Developing"),
    ]:
        fig_ramp.add_vrect(x0=x0, x1=x1, fillcolor=color, line_width=0,
                           annotation_text=label, annotation_position="top left",
                           annotation_font_color=color.replace("0.0", "0.7").replace("0.08","0.7").replace("0.06","0.7").replace("0.05","0.7"))

    if ramp_view == "System Average":
        fig_ramp.add_scatter(
            x=sys_curve["periods_since_open"], y=sys_curve["avg_sales"],
            mode="lines+markers", name="System Avg",
            line=dict(color="#12a06e", width=2.5), marker=dict(size=5),
            customdata=sys_curve["stand_count"],
            hovertemplate="Period %{x}<br>Avg Sales: $%{y:,.0f}<br>Stands: %{customdata}<extra></extra>",
        )

    elif ramp_view == "By State":
        for state, scolor in state_colors.items():
            sub = ramp_stands[ramp_stands["_state"] == state]
            if sub.empty:
                continue
            sc = (sub.groupby("periods_since_open")
                  .agg(avg_sales=("Net_Sales","mean"), stand_count=("Stand","nunique"))
                  .reset_index())
            sc = sc[sc["periods_since_open"] <= 30]
            fig_ramp.add_scatter(
                x=sc["periods_since_open"], y=sc["avg_sales"],
                mode="lines+markers", name=state,
                line=dict(color=scolor, width=2.5), marker=dict(size=5),
                customdata=sc["stand_count"],
                hovertemplate=f"{state} · Period %{{x}}<br>Avg Sales: $%{{y:,.0f}}<br>Stands: %{{customdata}}<extra></extra>",
            )
        # System avg as a dashed reference
        fig_ramp.add_scatter(
            x=sys_curve["periods_since_open"], y=sys_curve["avg_sales"],
            mode="lines", name="System Avg",
            line=dict(color="rgba(255,255,255,0.25)", width=1.5, dash="dot"),
            hoverinfo="skip",
        )

    else:  # Individual Stands
        # Identify the stand name (first token before city name)
        stand_ids = ramp_stands["Stand"].unique()
        for sid in sorted(stand_ids):
            sdf = ramp_stands[ramp_stands["Stand"] == sid].sort_values("periods_since_open")
            if len(sdf) < 2:
                continue
            state = sdf["_state"].iloc[0]
            scolor = state_colors.get(state, "#888")
            # Extract a short label (RSH-XXXXX)
            short_lbl = str(sid).split(" ")[0] if " " in str(sid) else str(sid)
            city_lbl  = str(sid).split(" ", 1)[1] if " " in str(sid) else ""
            fig_ramp.add_scatter(
                x=sdf["periods_since_open"], y=sdf["Net_Sales"],
                mode="lines", name=short_lbl,
                line=dict(color=scolor, width=1),
                opacity=0.45,
                legendgroup=state,
                legendgrouptitle_text=state if sdf.index[0] == ramp_stands[ramp_stands["_state"]==state].index[0] else None,
                hovertemplate=f"{short_lbl} {city_lbl}<br>Period %{{x}} since open<br>Sales: $%{{y:,.0f}}<extra></extra>",
                showlegend=False,
            )
        # Bold system average on top
        fig_ramp.add_scatter(
            x=sys_curve["periods_since_open"], y=sys_curve["avg_sales"],
            mode="lines", name="System Avg",
            line=dict(color="#ffffff", width=2.5, dash="dash"),
            hovertemplate="System Avg · Period %{x}<br>$%{y:,.0f}<extra></extra>",
        )
        # Add one visible legend entry per state so user knows the colors
        for state, scolor in state_colors.items():
            if not ramp_stands[ramp_stands["_state"] == state].empty:
                fig_ramp.add_scatter(
                    x=[None], y=[None], mode="lines", name=state,
                    line=dict(color=scolor, width=2), showlegend=True,
                )

    fig_ramp.update_layout(
        template="plotly_dark",
        height=340 if ramp_view == "Individual Stands" else 300,
        margin=dict(t=20, b=40, l=0, r=0),
        xaxis_title="Periods Since Opening (1 period ≈ 4 weeks)",
        yaxis_title="Net Sales ($)" if ramp_view == "Individual Stands" else "Avg Net Sales ($)",
        xaxis=dict(dtick=2),
        legend=dict(orientation="v", x=1.01, y=1),
    )
    st.plotly_chart(fig_ramp, use_container_width=True)

    caption_map = {
        "System Average": "Each point = average net sales across all matching stands at that exact period-since-opening. The ramp plateau shows when a typical 7BREW stand reaches full volume.",
        "By State":        "Each line = state average ramp. Dashed white = system average. Useful for spotting whether FL, TX, or OK stands ramp faster.",
        "Individual Stands": "Each thin line = one stand's actual weekly-period trajectory. White dashed = system average. Hover any line for stand details.",
    }
    st.caption(caption_map[ramp_view])


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

    # ── Separate stands by maturity ──
    ramping_buckets = ["New (<6mo)"]
    mature_buckets  = ["Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]

    if "Age_Bucket" in ps_stands.columns:
        ramping = ps_stands[ps_stands["Age_Bucket"].isin(ramping_buckets)]
        mature  = ps_stands[ps_stands["Age_Bucket"].isin(mature_buckets)]
        # Stands without age data go into mature (conservative)
        unclassified = ps_stands[~ps_stands["Age_Bucket"].isin(ramping_buckets + mature_buckets)]
        mature = pd.concat([mature, unclassified], ignore_index=True)
    else:
        ramping = pd.DataFrame()
        mature  = ps_stands

    n_ramping = len(ramping)
    n_mature  = len(mature)

    # Maturity-aware benchmarks
    # Ramping stands: higher labor/COGS is expected, don't flag unless extreme
    MATURE_LABOR_THRESHOLD = 0.25    # Flag mature stands >25%
    RAMPING_LABOR_THRESHOLD = 0.35   # Only flag ramping stands >35% (expected to be 28-32%)
    MATURE_EBITDA_FLOOR = 0.10       # Flag mature stands <10%
    RAMPING_EBITDA_FLOOR = 0.0       # Only flag ramping stands if negative EBITDA

    # Show ramp-up context
    if n_ramping > 0:
        avg_ramp_labor = ramping["Total_Labor_pct"].mean() if "Total_Labor_pct" in ramping.columns else 0
        avg_ramp_ebitda = ramping["Store_EBITDA_pct"].mean() if "Store_EBITDA_pct" in ramping.columns else 0
        avg_ramp_sales = ramping["Net_Sales"].mean() if "Net_Sales" in ramping.columns else 0
        avg_mature_labor = mature["Total_Labor_pct"].mean() if len(mature) and "Total_Labor_pct" in mature.columns else 0
        avg_mature_ebitda = mature["Store_EBITDA_pct"].mean() if len(mature) and "Store_EBITDA_pct" in mature.columns else 0

        st.html(f"""
        <div class="info-box">
          <strong>📊 Ramp-Up Context:</strong> {n_ramping} of {len(ps_stands)} stands are in ramp-up phase (open &lt;6 months).
          Ramping stands naturally carry higher labor ({_fmt_p(avg_ramp_labor)} avg vs {_fmt_p(avg_mature_labor)} mature)
          and lower EBITDA ({_fmt_p(avg_ramp_ebitda)} avg vs {_fmt_p(avg_mature_ebitda)} mature) as they build volume.
          The analysis below uses <strong>maturity-adjusted benchmarks</strong> so new locations aren't flagged for normal ramp behavior.
        </div>""")

    # Auto-generate wins
    wins = []
    opps = []

    # Win: Top performers (from mature stands — true operational excellence)
    if len(mature) >= 3:
        top_ebitda = mature.nlargest(3, "Store_EBITDA_pct")
        wins.append({
            "title": f"🏆 Top Performers: {', '.join(top_ebitda['Stand'].str.split(',').str[0].tolist())}",
            "body": f"These mature stands achieved {_fmt_p(top_ebitda['Store_EBITDA_pct'].mean())} average EBITDA — {_fmt_bps(top_ebitda['Store_EBITDA_pct'].mean() - ps['ebitda_pct'])} above system avg. Best-in-class labor efficiency ({_fmt_p(top_ebitda['Total_Labor_pct'].mean())}) drives the margin.",
            "tag": f"Avg EBITDA: {_fmt_p(top_ebitda['Store_EBITDA_pct'].mean())}", "tag_cls": "green",
        })

    # Win: Ramping stands beating expectations
    if n_ramping > 0:
        fast_ramp = ramping[ramping["Store_EBITDA_pct"] > 0.15]
        if len(fast_ramp):
            wins.append({
                "title": f"🚀 Fast Ramp: {len(fast_ramp)} new stand(s) already >15% EBITDA",
                "body": f"These new locations are ahead of the typical ramp curve: {', '.join(fast_ramp['Stand'].str.split(',').str[0].tolist()[:3])}. Average EBITDA of {_fmt_p(fast_ramp['Store_EBITDA_pct'].mean())} in the first year signals strong market fit and hiring execution.",
                "tag": "Ahead of Ramp", "tag_cls": "green",
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

    # ── Opportunities — maturity-adjusted ──
    # High labor: only flag MATURE stands above mature threshold, and ramping stands above ramping threshold
    mature_high_labor = mature[mature["Total_Labor_pct"] > MATURE_LABOR_THRESHOLD].nlargest(3, "Total_Labor_pct") if len(mature) else pd.DataFrame()
    ramp_high_labor = ramping[ramping["Total_Labor_pct"] > RAMPING_LABOR_THRESHOLD].nlargest(3, "Total_Labor_pct") if n_ramping else pd.DataFrame()

    if len(mature_high_labor):
        opps.append({
            "title": f"⚠️ High Labor — Mature Stands ({len(mature_high_labor)} > 25%)",
            "body": f"Top: {mature_high_labor.iloc[0]['Stand'].split(',')[0]} at {_fmt_p(mature_high_labor.iloc[0]['Total_Labor_pct'])} labor. These are established locations where labor should be optimized. Pull scheduling data and compare with similar-volume stands.",
            "tag": "Labor Risk", "tag_cls": "red",
        })

    if len(ramp_high_labor):
        opps.append({
            "title": f"🔶 Extreme Labor — Ramping Stands ({len(ramp_high_labor)} > 35%)",
            "body": f"While elevated labor is expected during ramp, these stands are well above the 28–32% ramp range: {', '.join(ramp_high_labor['Stand'].str.split(',').str[0].tolist()[:3])}. Verify minimum staffing isn't being exceeded and training timelines are on track.",
            "tag": "Ramp Watch", "tag_cls": "amber",
        })

    high_disc = ps_stands.nlargest(3, "Discounts_pct")
    if high_disc.iloc[0]["Discounts_pct"] > 0.04:
        opps.append({
            "title": f"💸 Discount Rate Alert: {high_disc.iloc[0]['Stand'].split(',')[0]}",
            "body": f"Discount rate of {_fmt_p(high_disc.iloc[0]['Discounts_pct'])} is {_fmt_p(high_disc.iloc[0]['Discounts_pct'] - 0.028)} above the 2.8% system avg. Investigate POS config and unauthorized promotion use.",
            "tag": "Discount Risk", "tag_cls": "red",
        })

    # Low EBITDA: use different floors for mature vs ramping
    mature_low = mature[mature["Store_EBITDA_pct"] < MATURE_EBITDA_FLOOR] if len(mature) else pd.DataFrame()
    ramp_low = ramping[ramping["Store_EBITDA_pct"] < RAMPING_EBITDA_FLOOR] if n_ramping else pd.DataFrame()

    if len(mature_low):
        opps.append({
            "title": f"🔴 Below-Floor EBITDA — Mature ({len(mature_low)} stands < 10%)",
            "body": f"These established stands should be profitable. Avg labor at {_fmt_p(mature_low['Total_Labor_pct'].mean())} and avg sales at {_fmt_d(mature_low['Net_Sales'].mean())} suggest cost structure or volume issues requiring attention.",
            "tag": "<10% EBITDA", "tag_cls": "red",
        })

    if len(ramp_low):
        opps.append({
            "title": f"🔶 Negative EBITDA — Ramping ({len(ramp_low)} stands)",
            "body": f"These new stands are losing money: {', '.join(ramp_low['Stand'].str.split(',').str[0].tolist()[:3])}. Some loss is expected during ramp, but negative EBITDA beyond 90 days warrants a review of staffing model and local market conditions.",
            "tag": "Ramp Risk", "tag_cls": "amber",
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
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#AC2430;margin-bottom:10px;">⚠ OPPORTUNITIES</div>')
        for o in opps:
            insight_card(o["title"], o["body"], o.get("tag",""), o.get("tag_cls","red"))

    # ── Ramp-Up Tracker — charts ──────────────────────────────────────────────
    if n_ramping > 0:
        st.html('<hr class="brew">')
        section("RAMP-UP TRACKER", f"{n_ramping} stand(s) in first 6 months · actual vs system benchmark · split FL / Non-FL")

        # Benchmarks — all use system average for this period
        _sys_sales  = float(ps.get("avg_sales", 0))
        _sys_ebitda = float(ps.get("ebitda_pct", 0)) * 100
        _sys_labor  = float(ps.get("labor_pct", 0)) * 100
        _sys_cogs   = float(ps.get("cogs_pct", 0)) * 100

        def _ramp_charts(subset, group_label, accent_color):
            """Render 4 ramp tracker charts (each full-width row) for a given subset."""
            if subset.empty:
                st.info(f"No new stands in {group_label} this period.")
                return
            # Sort oldest → newest so left-to-right reads as maturity progression
            if "Open Date" in subset.columns:
                subset = subset.copy()
                subset["_open_dt"] = pd.to_datetime(subset["Open Date"], errors="coerce")
                subset = subset.sort_values("_open_dt", ascending=True).drop(columns=["_open_dt"])
            names = subset["Stand"].str.split(",").str[0].tolist()
            n = len(names)

            def _rc(fig, title, yaxis_opts):
                brew_fig(fig, height=360)
                fig.update_layout(
                    title_text=title,
                    barmode="group",
                    xaxis=dict(tickangle=-30, tickfont=dict(size=13)),
                    yaxis=dict(**yaxis_opts, tickfont=dict(size=13)),
                    legend=dict(orientation="h", y=1.08, x=0, font=dict(size=13)),
                    bargap=0.25,
                )
                st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)

            # Chart 1 — Net Sales vs System Avg
            sv = subset["Net_Sales"].fillna(0).tolist()
            f1 = go.Figure()
            f1.add_bar(x=names, y=sv, name="Actual", marker_color=accent_color, opacity=0.88,
                       text=[f"${v:,.0f}" for v in sv],
                       textposition="outside", textfont=dict(size=12))
            f1.add_bar(x=names, y=[_sys_sales]*n, name="System Avg", marker_color=MUTED, opacity=0.55,
                       text=[f"${_sys_sales:,.0f}"]*n,
                       textposition="outside", textfont=dict(size=12))
            _rc(f1, f"NET SALES — {group_label}", dict(tickprefix="$", tickformat=",.0f"))

            # Chart 2 — EBITDA % vs System Avg
            ev = (subset["Store_EBITDA_pct"].fillna(0) * 100).tolist()
            f2 = go.Figure()
            f2.add_bar(x=names, y=ev, name="Actual EBITDA %",
                       marker_color=[GREEN if v >= _sys_ebitda else AMBER if v >= _sys_ebitda * 0.6 else RED
                                     for v in ev],
                       opacity=0.88, text=[f"{v:.1f}%" for v in ev],
                       textposition="outside", textfont=dict(size=12))
            f2.add_bar(x=names, y=[_sys_ebitda]*n, name=f"Sys Avg ({_sys_ebitda:.1f}%)",
                       marker_color=MUTED, opacity=0.55,
                       text=[f"{_sys_ebitda:.1f}%"]*n,
                       textposition="outside", textfont=dict(size=12))
            _rc(f2, f"EBITDA % — {group_label}", dict(ticksuffix="%", tickformat=".1f"))

            # Chart 3 — Labor % vs System Avg
            lv = (subset["Total_Labor_pct"].fillna(0) * 100).tolist()
            f3 = go.Figure()
            f3.add_bar(x=names, y=lv, name="Actual Labor %",
                       marker_color=[GREEN if v <= _sys_labor else AMBER if v <= _sys_labor + 5 else RED
                                     for v in lv],
                       opacity=0.88, text=[f"{v:.1f}%" for v in lv],
                       textposition="outside", textfont=dict(size=12))
            f3.add_bar(x=names, y=[_sys_labor]*n, name=f"Sys Avg ({_sys_labor:.1f}%)",
                       marker_color=MUTED, opacity=0.55,
                       text=[f"{_sys_labor:.1f}%"]*n,
                       textposition="outside", textfont=dict(size=12))
            _rc(f3, f"LABOR % — {group_label}", dict(ticksuffix="%", tickformat=".1f"))

            # Chart 4 — COGS % vs System Avg
            cv = (subset["Total_COGS_pct"].fillna(0) * 100).tolist()
            f4 = go.Figure()
            f4.add_bar(x=names, y=cv, name="Actual COGS %",
                       marker_color=[GREEN if v <= _sys_cogs else AMBER if v <= _sys_cogs + 3 else RED
                                     for v in cv],
                       opacity=0.88, text=[f"{v:.1f}%" for v in cv],
                       textposition="outside", textfont=dict(size=12))
            f4.add_bar(x=names, y=[_sys_cogs]*n, name=f"Sys Avg ({_sys_cogs:.1f}%)",
                       marker_color=MUTED, opacity=0.55,
                       text=[f"{_sys_cogs:.1f}%"]*n,
                       textposition="outside", textfont=dict(size=12))
            _rc(f4, f"COGS % — {group_label}", dict(ticksuffix="%", tickformat=".1f"))

        # Split Florida vs Non-Florida by Region name (FL regions start with "FL")
        if "Region" in ramping.columns:
            fl_mask    = ramping["Region"].str.startswith("FL", na=False)
            ramp_fl    = ramping[fl_mask].copy()
            ramp_nonfl = ramping[~fl_mask].copy()
        else:
            ramp_fl    = pd.DataFrame()
            ramp_nonfl = ramping.copy()

        has_fl    = not ramp_fl.empty
        has_nonfl = not ramp_nonfl.empty

        if has_fl and has_nonfl:
            # Both groups present — use tabs to keep it clean
            fl_tab, nonfl_tab = st.tabs([
                f"🌴 Florida  ({len(ramp_fl)} stand{'s' if len(ramp_fl)>1 else ''})",
                f"📍 Non-Florida  ({len(ramp_nonfl)} stand{'s' if len(ramp_nonfl)>1 else ''})",
            ])
            with fl_tab:
                _ramp_charts(ramp_fl, "FLORIDA", BLUE)
            with nonfl_tab:
                _ramp_charts(ramp_nonfl, "NON-FLORIDA", RED)
        elif has_fl:
            _ramp_charts(ramp_fl, "FLORIDA", BLUE)
        else:
            _ramp_charts(ramp_nonfl, "NON-FLORIDA", RED)

    # ── CRITICAL ISSUES + FORWARD-LOOKING RISKS ───────────────────────────────
    st.html('<hr class="brew">')

    # Alias maturity buckets to match pothole variable names
    est_stands  = mature
    new_stands  = ramping
    n_new       = n_ramping
    n_est       = n_mature
    NEW_BUCKETS = ["New (<6mo)"]
    EST_BUCKETS = ["Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]

    if n_new > 0:
        avg_new_labor = new_stands["Total_Labor_pct"].mean() if "Total_Labor_pct" in new_stands.columns else 0
        avg_est_labor = est_stands["Total_Labor_pct"].mean() if n_est and "Total_Labor_pct" in est_stands.columns else 0
        st.html(f"""
        <div style="background:#fff8e1;border-left:4px solid #e8940a;border-radius:6px;
                    padding:12px 16px;margin-bottom:14px;font-family:'DM Mono',monospace;font-size:12px;">
          <strong>📋 Maturity Filter Active:</strong> {n_new} new stand(s) (&lt;6 months) are excluded from Critical Issues
          — their elevated labor ({_fmt_p(avg_new_labor)} avg) and lower EBITDA are expected during ramp.
          Established stands ({n_est}) avg labor: {_fmt_p(avg_est_labor)}.
        </div>""")

    pot_col1, pot_col2 = st.columns(2)

    with pot_col1:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;'
                'color:#AC2430;margin-bottom:10px;">🚨 CRITICAL ISSUES — ESTABLISHED STANDS</div>')

        if est_stands.empty:
            st.info("No established stands in this period.")
        else:
            top_disc  = ps_stands.nlargest(1, "Discounts_pct").iloc[0]
            disc_age  = top_disc.get("Age_Bucket", "")
            disc_note = f" ({disc_age})" if disc_age else ""
            insight_card(
                f"🚨 Highest Discount: {top_disc['Stand'].split(',')[0]}{disc_note}",
                f"{_fmt_p(top_disc['Discounts_pct'])} discount rate — "
                f"{top_disc['Discounts_pct']/0.028:.1f}× the 2.8% system avg. "
                f"Discount issues aren't ramp-related — check POS config and promo authorization.",
                tag=_fmt_p(top_disc['Discounts_pct']), tag_cls="red",
            )

            top_labor    = est_stands.nlargest(1, "Total_Labor_pct").iloc[0]
            avg_sys_labor = ps["labor_pct"]
            labor_gap    = top_labor["Total_Labor_pct"] - avg_sys_labor
            insight_card(
                f"🚨 High Labor (Est.): {top_labor['Stand'].split(',')[0]}",
                f"{_fmt_p(top_labor['Total_Labor_pct'])} Total Labor — "
                f"{_fmt_bps(labor_gap)} above the {_fmt_p(avg_sys_labor)} system avg. "
                f"This stand is past ramp — scheduling inefficiency or staffing model issue. "
                f"EBITDA: {_fmt_p(top_labor['Store_EBITDA_pct'])}.",
                tag=_fmt_p(top_labor['Total_Labor_pct']), tag_cls="red",
            )

            worst_ebi = est_stands.nsmallest(1, "Store_EBITDA_pct").iloc[0]
            insight_card(
                f"🚨 Lowest EBITDA (Est.): {worst_ebi['Stand'].split(',')[0]}",
                f"{_fmt_p(worst_ebi['Store_EBITDA_pct'])} EBITDA on {_fmt_d(worst_ebi['Net_Sales'])} sales. "
                f"This is an established location — underperformance is a real issue, not ramp noise. "
                f"Labor {_fmt_p(worst_ebi['Total_Labor_pct'])}, COGS {_fmt_p(worst_ebi['Total_COGS_pct'])}.",
                tag=_fmt_p(worst_ebi['Store_EBITDA_pct']), tag_cls="red",
            )

            top_rm = est_stands.nlargest(1, "Total_RM_pct").iloc[0]
            if top_rm["Total_RM_pct"] > 0.02:
                insight_card(
                    f"🚨 High R&M (Est.): {top_rm['Stand'].split(',')[0]}",
                    f"{_fmt_p(top_rm['Total_RM_pct'])} R&M — {top_rm['Total_RM_pct']/0.011:.1f}× system avg. "
                    f"Established stands with high R&M signal equipment aging or deferred maintenance. "
                    f"Schedule a condition audit.",
                    tag=_fmt_p(top_rm['Total_RM_pct']), tag_cls="amber",
                )

            multi_issue = est_stands[
                (est_stands["Total_Labor_pct"] > 0.27) &
                (est_stands["Store_EBITDA_pct"] < 0.12)
            ]
            if len(multi_issue) > 1:
                names = ", ".join(multi_issue["Stand"].str.split(",").str[0].tolist()[:4])
                insight_card(
                    f"🚨 Multi-Issue Cluster: {len(multi_issue)} Established Stands",
                    f"These stands have both high labor (>27%) AND low EBITDA (<12%): {names}. "
                    f"Cluster pattern suggests a systemic issue — staffing model, market, or management.",
                    tag=f"{len(multi_issue)} Stands", tag_cls="red",
                )

    with pot_col2:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;'
                'color:#e8940a;margin-bottom:10px;">⚠ FORWARD-LOOKING RISKS</div>')

        reg_df_pot = get_regions_df(dash, pk)
        high_labor_regions = []
        if not reg_df_pot.empty and "labor_pct" in reg_df_pot.columns:
            sys_labor = float(ps.get("labor_pct", 0))
            for _, rrow in reg_df_pot.iterrows():
                if rrow.get("labor_pct", 0) > sys_labor + 0.04:
                    high_labor_regions.append((rrow["region"], rrow["labor_pct"]))
        if high_labor_regions:
            reg_list = ", ".join(f"{r} ({_fmt_p(l)})" for r, l in sorted(high_labor_regions, key=lambda x: -x[1]))
            insight_card(
                f"⚠ Regional Labor Gap: {len(high_labor_regions)} Region(s) 400bps+ Above Avg",
                f"{reg_list} are running 400bps+ above system avg labor. "
                f"Regional labor creep compounds quickly — investigate scheduling and staffing ratios.",
                tag="Labor Risk", tag_cls="amber", card_cls="watch",
            )

        low_sales = est_stands[est_stands["Net_Sales"] < est_stands["Net_Sales"].quantile(0.15)]
        if len(low_sales) >= 2:
            names = ", ".join(low_sales.nsmallest(3, "Net_Sales")["Stand"].str.split(",").str[0].tolist())
            insight_card(
                f"⚠ Low-Volume Established Stands ({len(low_sales)} in bottom 15%)",
                f"Bottom performers by sales: {names}. "
                f"For established locations, low volume may indicate market saturation, location issues, "
                f"or operational problems — not just ramp lag.",
                tag="Volume Risk", tag_cls="amber", card_cls="watch",
            )

        for title, body, tag, tag_cls in [
            ("⚠ Summer Labor P6–P8",
             "Historical data shows P6–P8 EBITDA compresses 300–500bps vs spring. Vacation coverage, "
             "call-outs, and training overlap for summer new opens create labor creep. Build the schedule now.",
             "Seasonal Risk", "amber"),
            ("⚠ P12–P13 Year-End Pattern",
             "P12–P13 historically run 600–900bps below peak EBITDA. Holiday fixed cost absorption + "
             "traffic slowdown. No deferred expenses into year-end — plan cost controls in P11.",
             "Seasonal Risk", "amber"),
            ("⚠ New Stand Pipeline Dilution",
             "Each new opening carries 25–35% labor for 60–90 days and compresses system EBITDA% by "
             "~150–200bps per cohort. Factor into board-level EBITDA guidance.",
             "~150–200bps dilution", "grey"),
            ("⚠ Aging Equipment — 2022–2023 Vintage",
             "Stands opened 2022–2023 are now 2–4 years old. R&M% tends to spike after year 3. "
             "Any stand over 2.0% R&M should get a proactive equipment condition audit before P6.",
             "Equipment Risk", "grey"),
        ]:
            insight_card(title, body, tag, tag_cls, "watch")


# ─────────────────────────────────────────────
# TAB PASSWORD GATE
# ─────────────────────────────────────────────
_TAB_PASSWORD = "7brew2026"   # ← change this to whatever you want

def _require_password(tab_key: str) -> bool:
    """
    Show a password prompt for a work-in-progress tab.
    Returns True if the user is authenticated (content should render),
    False if the gate should block rendering.
    """
    auth_key = f"_auth_{tab_key}"
    if st.session_state.get(auth_key):
        return True

    st.markdown("")
    cc = st.columns([1, 2, 1])
    with cc[1]:
        st.markdown(
            '<div style="text-align:center;padding:40px 0 10px;">'
            '<span style="font-size:48px;">🔒</span><br>'
            '<span style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;'
            'letter-spacing:2px;color:#1A1919;">WORK IN PROGRESS</span><br>'
            '<span style="font-size:13px;color:#888;">This tab is still being built. '
            'Enter the access code to preview.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        pw = st.text_input("Access code", type="password", key=f"_pw_{tab_key}",
                           label_visibility="collapsed", placeholder="Enter access code…")
        if st.button("Unlock", key=f"_btn_{tab_key}", use_container_width=True):
            if pw == _TAB_PASSWORD:
                st.session_state[auth_key] = True
                st.rerun()
            else:
                st.error("Incorrect code — try again.")
    return False


# ─────────────────────────────────────────────
# TAB: SPEED OF SERVICE
# ─────────────────────────────────────────────

# SOS benchmarks by stand age (in minutes).
# Goals are based on full 28-day periods completed AFTER the opening partial
# period.  The opening partial period (< 28 days open) is "Period 0" and is
# excluded from goal calculations — the first FULL 28-day period is P1.
_SOS_GOALS = {
    "P1  (1st full period, days 28–55)":  5.00,   # 5:00
    "P2  (2nd full period, days 56–83)":  5.00,   # 5:00
    "P3  (3rd full period, days 84–111)": 4.50,   # 4:30
    "P4  (4th full period, days 112–139)":4.00,   # 4:00
    "P5  (5th full period, days 140–167)":3.75,   # 3:45
    "P6+ (6th period & on, days 168+)":   3.50,   # 3:30
}

_PERIOD_DAYS = 28   # one 7Brew accounting period
_P0_DAYS     = 28   # stands open < 28 days are in "Period 0" (opening partial period)

# Add one entry per period as new CSVs become available.
# midpoint is used to compute stand age → goal tier.
_SOS_PERIODS = {
    # ── Q1 2026 : P1 · P2 · P3 ──────────────────────────────────────────────
    "P1 2026 (Dec 29 – Jan 25)": {
        "file":     "sos_p1_2026.csv",
        "midpoint": "2026-01-12",
        "quarter":  "Q1 2026",
    },
    "P2 2026 (Jan 26 – Feb 22)": {
        "file":     "sos_p2_2026.csv",
        "midpoint": "2026-02-09",
        "quarter":  "Q1 2026",
    },
    "P3 2026 (Feb 23 – Mar 22)": {
        "file":     "sos_p3_2026.csv",
        "midpoint": "2026-03-07",
        "quarter":  "Q1 2026",
    },
    # ── Q2 2026 : P4 · P5 · P6 ──────────────────────────────────────────────
    # "P4 2026 (Mar 23 – Apr 19)": {"file": "sos_p4_2026.csv", "midpoint": "2026-04-05", "quarter": "Q2 2026"},
    # "P5 2026 (Apr 20 – May 17)": {"file": "sos_p5_2026.csv", "midpoint": "2026-05-03", "quarter": "Q2 2026"},
    # "P6 2026 (May 18 – Jun 14)": {"file": "sos_p6_2026.csv", "midpoint": "2026-06-01", "quarter": "Q2 2026"},
    # ── Q3 2026 : P7 · P8 · P9 ──────────────────────────────────────────────
    # "P7 2026 (Jun 15 – Jul 12)": {"file": "sos_p7_2026.csv", "midpoint": "2026-06-29", "quarter": "Q3 2026"},
    # "P8 2026 (Jul 13 – Aug  9)": {"file": "sos_p8_2026.csv", "midpoint": "2026-07-27", "quarter": "Q3 2026"},
    # "P9 2026 (Aug 10 – Sep  6)": {"file": "sos_p9_2026.csv", "midpoint": "2026-08-24", "quarter": "Q3 2026"},
    # ── Q4 2026 : P10 · P11 · P12 · P13 ────────────────────────────────────
    # "P10 2026 (Sep  7 – Oct  4)": {"file": "sos_p10_2026.csv", "midpoint": "2026-09-21", "quarter": "Q4 2026"},
    # "P11 2026 (Oct  5 – Nov  1)": {"file": "sos_p11_2026.csv", "midpoint": "2026-10-19", "quarter": "Q4 2026"},
    # "P12 2026 (Nov  2 – Nov 29)": {"file": "sos_p12_2026.csv", "midpoint": "2026-11-16", "quarter": "Q4 2026"},
    # "P13 2026 (Nov 30 – Dec 27)": {"file": "sos_p13_2026.csv", "midpoint": "2026-12-14", "quarter": "Q4 2026"},
}

def _print_button(label: str = "🖨️  Print / Save as PDF", landscape: bool = True):
    """Inject print-friendly CSS + a one-click print/PDF button for the current tab.

    Uses window.parent.print() because st.components renders inside an iframe.
    Print CSS hides Streamlit chrome (sidebar, header, toolbar, tab nav) so only
    the tab content lands on the page.
    """
    import streamlit.components.v1 as _comp
    page_size = "landscape" if landscape else "portrait"
    st.markdown(f"""
    <style>
    @media print {{
        /* ── Hide all Streamlit UI chrome ───────────────────────────── */
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stDeployButton"],
        [data-testid="stStatusWidget"],
        [data-testid="stBottom"],
        .stTabs [data-baseweb="tab-list"],
        footer, header {{ display: none !important; }}

        /* ── Full-width content area ─────────────────────────────────── */
        .main .block-container {{
            max-width: 100% !important;
            padding: 0.5rem 1rem !important;
        }}

        /* ── Avoid splitting charts/tables across pages ──────────────── */
        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="element-container"],
        .stMetric {{
            break-inside: avoid;
            page-break-inside: avoid;
        }}

        /* ── Page setup ──────────────────────────────────────────────── */
        @page {{ margin: 0.65in; size: {page_size}; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    _comp.html(f"""
    <button
      onclick="window.parent.print()"
      title="Print this tab or save as PDF using your browser's print dialog"
      style="
        background: #FF6B00;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 7px 16px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        font-family: sans-serif;
        letter-spacing: 0.02em;
      "
    >{label}</button>
    """, height=42)


def _fmt_sos(minutes) -> str:
    """Convert decimal minutes to M:SS format.  4.5 → '4:30',  3.75 → '3:45'."""
    try:
        total_sec = round(float(minutes) * 60)
        m, s = divmod(abs(total_sec), 60)
        sign = "-" if total_sec < 0 else ""
        return f"{sign}{m}:{s:02d}"
    except Exception:
        return "—"

@st.cache_data
def _load_sos_data(csv_filename: str):
    """Load and parse the Speed of Service CSV. csv_filename is the bare filename."""
    import os
    sos_path = os.path.join(os.path.dirname(__file__), csv_filename)
    df = pd.read_csv(sos_path)

    # Parse Site: "000087 - Big Spring, TX - 1"
    df["Store_Num"]   = df["Site"].str.extract(r"^(\d+)").fillna("")
    df["City_State"]  = df["Site"].str.extract(r"^\d+\s*-\s*(.+?)\s*-\s*\d+$").fillna(df["Site"])
    # Unique stand label: store number + city (handles multi-stand cities)
    df["Stand_Label"] = df["Store_Num"] + " — " + df["City_State"]

    # Business Date
    df["Business Date"] = pd.to_datetime(df["Business Date"], errors="coerce")
    df["Date"]      = df["Business Date"].dt.date
    df["DayOfWeek"] = df["Business Date"].dt.day_name()
    df["DayNum"]    = df["Business Date"].dt.dayofweek   # 0=Mon … 6=Sun
    df["WeekLabel"] = df["Business Date"].dt.to_period("W").astype(str)
    df["IsWeekend"] = df["DayNum"].isin([5, 6])

    # Parse Time: "07:00AM - 08:00AM" → integer hour (0-23)
    if "Time" in df.columns:
        time_start = df["Time"].str.extract(r"^(\d+:\d+[AP]M)", expand=False)
        df["Hour"] = pd.to_datetime(time_start, format="%I:%M%p", errors="coerce").dt.hour
    else:
        df["Hour"] = None

    # SOS column – convert seconds → minutes
    sos_col = "SOS: Order Created to Served"
    if sos_col in df.columns:
        df["SOS_sec"] = pd.to_numeric(df[sos_col], errors="coerce")
        df["SOS_min"] = df["SOS_sec"] / 60.0
    else:
        df["SOS_sec"] = None
        df["SOS_min"] = None

    # State from City_State
    df["State"] = df["City_State"].str.extract(r",\s*([A-Z]{2})$").fillna("Unknown")

    # Prime-time flag: weekday 7–9am, weekend 9am–12pm  (vectorized — no apply)
    _h = df["Hour"]
    df["IsPrimeTime"] = (
        _h.notna() & (
            (~df["IsWeekend"] & _h.between(7, 9)) |
            ( df["IsWeekend"] & _h.between(9, 12))
        )
    )

    # Filter valid SOS rows (exclude 0 and extreme outliers >10 min)
    df = df[df["SOS_min"].notna() & (df["SOS_min"] > 0) & (df["SOS_min"] <= 10)].copy()

    return df


def _sos_goal_for_period(days_since_open):
    """Return SOS goal (float, minutes) based on days open.

    Stands open < _P0_DAYS days are in 'Period 0' (opening partial period);
    returns None so those rows are excluded from At-Goal calculations.
    P1 = first FULL 28-day period (days 28–55), P2 = days 56–83, etc.
    """
    try:
        d = int(days_since_open)
    except (TypeError, ValueError):
        return 3.50   # default to mature goal if unknown
    if d < _P0_DAYS:
        return None   # Period 0 — opening partial period, no goal assigned
    p = (d - _P0_DAYS) // _PERIOD_DAYS   # 0 = P1, 1 = P2, 2 = P3 …
    if p < 1:   return _SOS_GOALS["P1  (1st full period, days 28–55)"]
    if p < 2:   return _SOS_GOALS["P2  (2nd full period, days 56–83)"]
    if p < 3:   return _SOS_GOALS["P3  (3rd full period, days 84–111)"]
    if p < 4:   return _SOS_GOALS["P4  (4th full period, days 112–139)"]
    if p < 5:   return _SOS_GOALS["P5  (5th full period, days 140–167)"]
    return             _SOS_GOALS["P6+ (6th period & on, days 168+)"]

def _goal_tier_label(days_since_open) -> str:
    """Human-readable tier label for a stand's age (P0 = opening partial period)."""
    try:
        d = int(days_since_open)
    except (TypeError, ValueError):
        return "P6+"
    if d < _P0_DAYS:
        return "P0"
    p = (d - _P0_DAYS) // _PERIOD_DAYS
    if p < 1:   return "P1"
    if p < 2:   return "P2"
    if p < 3:   return "P3"
    if p < 4:   return "P4"
    if p < 5:   return "P5"
    return "P6+"

# Keep old name as alias for any remaining call sites
_sos_goal_for_age = _sos_goal_for_period


@st.cache_data
def _load_all_sos_periods_raw() -> dict:
    """Return {period_label: df} for every period CSV that exists on disk."""
    import os
    result = {}
    for label, meta in _SOS_PERIODS.items():
        path = os.path.join(os.path.dirname(__file__), meta["file"])
        if os.path.exists(path):
            try:
                result[label] = _load_sos_data(meta["file"])
            except Exception:
                pass
    return result


@st.cache_data(show_spinner=False)
def _sos_period_kpis(plabel: str, stands_info_json: str) -> dict | None:
    """Compute SOS summary stats for one period label.  Cached for performance.

    Extracts: sys_avg, prime_avg, pct_at, n_beating, n_missing, display strings.
    stands_info_json is a stable JSON string built from dash['stand_records'].
    """
    import json as _json
    if plabel not in _SOS_PERIODS:
        return None
    all_data = _load_all_sos_periods_raw()
    if plabel not in all_data:
        return None

    stands_info = _json.loads(stands_info_json)
    pmeta = _SOS_PERIODS[plabel]
    pmid  = pd.to_datetime(pmeta["midpoint"]).date()
    pdata = all_data[plabel].copy()

    # Age-based goals
    def _days_open_p(sn):
        od = stands_info.get(sn, {}).get("Open Date", "")
        try:
            return max(0, (pmid - pd.to_datetime(od).date()).days)
        except Exception:
            return None

    pdata["Stand_Goal"] = pdata["Store_Num"].map(
        lambda sn: _sos_goal_for_period(_days_open_p(sn) or 999)
    )
    pdata["Is_P0"] = pdata["Stand_Goal"].isna()

    p_sys   = pdata["SOS_min"].mean()
    p_prime = pdata[pdata["IsPrimeTime"]]["SOS_min"].mean() if pdata["IsPrimeTime"].any() else float("nan")

    p_goal_rows = pdata[~pdata["Is_P0"]]
    p_pct = (p_goal_rows["SOS_min"].le(p_goal_rows["Stand_Goal"]).sum()
             / len(p_goal_rows) * 100) if len(p_goal_rows) > 0 else 0.0

    s_avg    = pdata.groupby("Stand_Label")["SOS_min"].mean()
    s_goal   = pdata.groupby("Stand_Label")["Stand_Goal"].first()
    s_is_p0  = pdata.groupby("Stand_Label")["Is_P0"].first()
    n_at     = sum(s_avg[s] <= s_goal[s]
                   for s in s_avg.index
                   if s in s_goal.index and not s_is_p0.get(s, True))
    n_with_g = sum(1 for s in s_avg.index if not s_is_p0.get(s, True))
    pr_prime = pdata[pdata["IsPrimeTime"]]["SOS_min"]

    return {
        # Raw numerics for KPI deltas
        "sys_avg":    p_sys,
        "prime_avg":  pr_prime.mean() if len(pr_prime) > 0 else float("nan"),
        "pct_at":     p_pct,
        "n_beating":  n_at,
        "n_missing":  n_with_g - n_at,
        # Formatted display strings for trend table
        "Period":              plabel,
        "_sys":                p_sys,
        "_prime":              float("nan") if pd.isna(p_prime) else p_prime,
        "_pct":                p_pct,
        "System Avg":          _fmt_sos(p_sys),
        "Prime Time Avg":      _fmt_sos(p_prime),
        "Txns At Goal":        f"{p_pct:.1f}%",
        "Stands Meeting Goal": n_at,
        "Stands Over Goal":    n_with_g - n_at,
    }


def tab_sos(dash):
    # ── Period / Quarter selector ─────────────────────────────────────────────
    period_options = list(_SOS_PERIODS.keys())

    # Build quarter groupings from the "quarter" key in _SOS_PERIODS
    qtr_groups = {}   # {"Q1 2026": ["P1 2026 ...", ...], ...}
    for plabel, pmeta in _SOS_PERIODS.items():
        q = pmeta.get("quarter", "")
        if q:
            qtr_groups.setdefault(q, []).append(plabel)

    # Year selector (derived from available quarters)
    avail_years = sorted({q.split()[-1] for q in qtr_groups}, reverse=True)
    scol1, scol2 = st.columns([1, 5])
    with scol1:
        sel_year = st.selectbox("Year", avail_years, key="sos_year_sel")

    # Q preset buttons — only show quarters that belong to the selected year
    year_qtrs = {q: plist for q, plist in qtr_groups.items() if q.endswith(sel_year)}
    with scol2:
        btn_cols = st.columns(len(year_qtrs) + 1)   # +1 for "All"
        for i, (qname, qperiods) in enumerate(year_qtrs.items()):
            with btn_cols[i]:
                if st.button(qname, key=f"sos_q_{qname}", use_container_width=True):
                    # Keep only periods that exist in _SOS_PERIODS
                    st.session_state["sos_sel_periods"] = [
                        p for p in qperiods if p in period_options
                    ]
                    st.rerun()
        with btn_cols[len(year_qtrs)]:
            if st.button("All", key="sos_q_all", use_container_width=True):
                st.session_state["sos_sel_periods"] = [
                    p for p in period_options if any(p in pl for pl in year_qtrs.values())
                ]
                st.rerun()

    # Fine-grained multi-select (syncs with button state)
    year_period_options = [
        p for p in period_options
        if any(p in pl for pl in year_qtrs.values())
    ] or period_options   # fallback: show all if no year grouping

    default_sel = st.session_state.get("sos_sel_periods", [year_period_options[-1]])
    # Ensure defaults are valid for current year
    default_sel = [p for p in default_sel if p in year_period_options] or [year_period_options[-1]]

    sel_periods = st.multiselect(
        "View Period(s)",
        year_period_options,
        default=default_sel,
        key="sos_period_sel",
    )
    # Sync back so buttons stay consistent
    st.session_state["sos_sel_periods"] = sel_periods

    if not sel_periods:
        st.info("Select at least one period above.")
        return

    # "Compare To" dropdown — all periods NOT in the current selection
    cmp_options = [p for p in period_options if p not in sel_periods]
    if cmp_options:
        # Default: period immediately before the earliest selected one
        sorted_sel = [p for p in period_options if p in sel_periods]
        earliest_idx_for_cmp = period_options.index(sorted_sel[0]) if sorted_sel else 0
        prior_candidates = [p for p in cmp_options if period_options.index(p) < earliest_idx_for_cmp]
        default_cmp = prior_candidates[-1] if prior_candidates else cmp_options[0]
        default_cmp_idx = cmp_options.index(default_cmp)
        cmp_to_key = st.selectbox(
            "Compare To",
            cmp_options,
            index=default_cmp_idx,
            key="sos_cmp_to",
        )
    else:
        cmp_to_key = None
        st.caption("ℹ️ All periods selected — no comparison period available.")

    # Sort in dict-insertion order
    sel_periods = [p for p in period_options if p in sel_periods]

    # Header label: "P3 2026" for single, "Q1 2026 (P1 + P2 + P3)" for multi
    p_short = [p.split(" (")[0] for p in sel_periods]
    if len(sel_periods) == 1:
        sel_label = p_short[0]
    else:
        # Check if selection matches a named quarter
        matched_q = next((q for q, pl in qtr_groups.items()
                          if sorted(pl) == sorted(sel_periods)), None)
        sel_label = f"{matched_q} ({' + '.join(p_short)})" if matched_q else " + ".join(p_short)

    # ── Print / PDF button ────────────────────────────────────────────────────
    _print_button("🖨️  Print / Save as PDF")

    section(f"⏱️ SPEED OF SERVICE — {sel_label}",
            f"Source: 7Brew SOS Report · {len(sel_periods)} period{'s' if len(sel_periods) > 1 else ''} selected")

    # Load & concatenate all selected periods
    frames = []
    for pk in sel_periods:
        try:
            frames.append(_load_sos_data(_SOS_PERIODS[pk]["file"]))
        except Exception as e:
            st.error(f"Could not load {pk}: {e}")
            return
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if df.empty:
        st.warning("No SOS data found for the selected period(s).")
        return

    # ── Stand metadata & age-based goals ─────────────────────────────────────
    # Use midpoint of the LAST selected period for age-based goal assignment
    period_meta = _SOS_PERIODS[sel_periods[-1]]
    period_mid  = pd.to_datetime(period_meta["midpoint"]).date()

    stands_info = {}
    for rec in dash.get("stand_records", []):
        # stand_records uses Store_ID (int, e.g. 134) — zero-pad to match SOS Store_Num ("000134")
        sn = str(rec.get("Store_ID", rec.get("Store Number", ""))).strip().zfill(6)
        if sn and sn != "000000":
            stands_info[sn] = {
                "Region":     rec.get("Region", "Unknown"),
                "Age_Bucket": rec.get("Age_Bucket", "Unknown"),
                "Open Date":  rec.get("Open Date", ""),
            }

    # Stable JSON key for the cached period-summary function
    import json as _json
    _stands_info_json = _json.dumps(stands_info, sort_keys=True)

    def _days_open(store_num, as_of=None):
        """Days the stand had been open as of 'as_of' date (defaults to period_mid)."""
        od = stands_info.get(store_num, {}).get("Open Date", "")
        ref = as_of or period_mid
        try:
            open_dt = pd.to_datetime(od).date()
            return max(0, (ref - open_dt).days)
        except Exception:
            return None

    def _stand_goal(store_num, as_of=None):
        d = _days_open(store_num, as_of)
        return _sos_goal_for_period(d if d is not None else 999)

    def _stand_tier(store_num, as_of=None):
        d = _days_open(store_num, as_of)
        return _goal_tier_label(d if d is not None else 999)

    df["Region"]     = df["Store_Num"].map(lambda s: stands_info.get(s, {}).get("Region",     "Unknown"))
    df["Cohort"]     = df["Store_Num"].map(lambda s: stands_info.get(s, {}).get("Age_Bucket", "Unknown"))
    df["Stand_Goal"] = df["Store_Num"].map(_stand_goal)   # None for P0 stands
    df["Goal_Tier"]  = df["Store_Num"].map(_stand_tier)   # "P0" for opening partial period
    # At_Goal: False for P0 rows (Stand_Goal is None/NaN → comparison returns False)
    df["At_Goal"]    = df["SOS_min"] <= df["Stand_Goal"]
    df["Is_P0"]      = df["Goal_Tier"] == "P0"

    # ── Shared helpers ────────────────────────────────────────────────────────
    _sos_ticks      = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
    _sos_ticklabels = [_fmt_sos(v) for v in _sos_ticks]
    day_order       = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def _apply_sos_yaxis(fig, title="Avg SOS"):
        fig.update_yaxes(tickvals=_sos_ticks, ticktext=_sos_ticklabels, title_text=title)
        return fig

    def _fmt_hour(h):
        return f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"

    def _colour_sos_cell(val):
        try:
            parts = str(val).lstrip("-+").split(":")
            m = int(parts[0]) + int(parts[1]) / 60
            return "color: #12a06e; font-weight:bold" if m < 3.5 else "color: #AC2430; font-weight:bold"
        except Exception:
            return ""

    def _vs_goal_str(avg, goal):
        delta = avg - goal
        sign  = "+" if delta >= 0 else "-"
        return f"{sign}{_fmt_sos(abs(delta))}"

    # ── Per-stand goal map (for aggregated comparisons) ───────────────────────
    stand_goal_map = (
        df.groupby("Stand_Label")["Stand_Goal"].first()
    )   # one goal per stand

    # ═════════════════════════════════════════════════════════════════════════
    # Load all period data early — needed for PoP deltas in KPI strip
    # ═════════════════════════════════════════════════════════════════════════
    all_period_data   = _load_all_sos_periods_raw()
    # Filter to keys that exist in the current _SOS_PERIODS dict —
    # guards against stale @st.cache_data returning old period labels
    available_periods = [p for p in all_period_data.keys() if p in _SOS_PERIODS]

    # ── Identify comparison period for PoP deltas ────────────────────────────
    # Uses the "Compare To" selectbox selection (set by user at top of tab).
    period_order = list(_SOS_PERIODS.keys())
    prior_key    = cmp_to_key  # driven by the "Compare To" dropdown

    # Module-level cached function computes prior period stats
    prior = _sos_period_kpis(prior_key, _stands_info_json) if prior_key else None
    prior_lbl = (prior_key.split("(")[0].strip()         # e.g. "P2 2026"
                 if prior_key else "prior period")

    def _sos_d(curr, prev, lbl):
        """Delta badge for SOS time metrics — lower is better (green = faster)."""
        try:
            diff = float(curr) - float(prev)
        except (TypeError, ValueError):
            return None
        sign = "+" if diff > 0 else ""
        return {"str": f"{sign}{_fmt_sos(diff)} vs {lbl}", "cls": "up" if diff < 0 else "down"}

    def _pct_d(curr, prev, lbl):
        """Delta badge for percentage metrics — higher is better."""
        try:
            diff = float(curr) - float(prev)
        except (TypeError, ValueError):
            return None
        sign = "+" if diff > 0 else ""
        return {"str": f"{sign}{diff:.1f}% vs {lbl}", "cls": "up" if diff > 0 else "down"}

    def _cnt_d(curr, prev, lbl, higher_better=True):
        """Delta badge for count metrics."""
        try:
            diff = int(curr) - int(prev)
        except (TypeError, ValueError):
            return None
        sign = "+" if diff > 0 else ""
        good = (diff > 0) == higher_better
        return {"str": f"{sign}{diff} vs {lbl}", "cls": "up" if good else "down"}

    # ═════════════════════════════════════════════════════════════════════════
    # KPI STRIP
    # ═════════════════════════════════════════════════════════════════════════
    sys_avg      = df["SOS_min"].mean()
    prime_df     = df[df["IsPrimeTime"]].copy()
    offpeak_df   = df[~df["IsPrimeTime"]].copy()
    prime_avg    = prime_df["SOS_min"].mean() if len(prime_df) > 0 else sys_avg

    by_stand     = df.groupby("Stand_Label")["SOS_min"].mean()
    best_label   = by_stand.idxmin()
    worst_label  = by_stand.idxmax()
    best_val     = by_stand.min()
    worst_val    = by_stand.max()

    # Exclude P0 rows (opening partial period) from goal-based metrics
    df_goal = df[~df["Is_P0"]]
    n_goal_rows = len(df_goal)
    pct_at_goal  = (df_goal["At_Goal"].sum() / n_goal_rows * 100) if n_goal_rows > 0 else 0.0
    stand_avgs   = df.groupby("Stand_Label")["SOS_min"].mean()
    # For meeting/over goal, only count stands that have a goal (not P0)
    stand_tiers  = df.groupby("Stand_Label")["Goal_Tier"].first()
    n_p0_stands  = (stand_tiers == "P0").sum()
    n_beating    = sum(stand_avgs[s] <= stand_goal_map[s]
                       for s in stand_avgs.index
                       if s in stand_goal_map and stand_goal_map[s] is not None)
    n_missing    = (len(stand_avgs) - n_p0_stands) - n_beating

    kpi_row([
        {"label": "SYSTEM AVG",       "value": _fmt_sos(sys_avg),
         "sub": "all hours · all stands",   "color": "blue",
         "delta": _sos_d(sys_avg,   prior["sys_avg"],   prior_lbl) if prior else None},
        {"label": "PRIME TIME AVG",   "value": _fmt_sos(prime_avg),
         "sub": "peak hours only",           "color": "amber",
         "delta": _sos_d(prime_avg, prior["prime_avg"], prior_lbl) if prior else None},
        {"label": "BEST STAND",       "value": _fmt_sos(best_val),
         "sub": best_label,                  "color": "green"},
        {"label": "WORST STAND",      "value": _fmt_sos(worst_val),
         "sub": worst_label,                 "color": "red"},
        {"label": "TXNS AT/UNDER GOAL", "value": f"{pct_at_goal:.1f}%",
         "sub": "P1+ stands · excl. P0 opening period",
         "color": "green" if pct_at_goal >= 50 else "amber",
         "delta": _pct_d(pct_at_goal, prior["pct_at"], prior_lbl) if prior else None},
    ])
    kpi_row([
        {"label": "STANDS MEETING GOAL", "value": str(n_beating),
         "sub": "avg SOS ≤ their goal (excl. P0)",   "color": "green",
         "delta": _cnt_d(n_beating, prior["n_beating"], prior_lbl, higher_better=True) if prior else None},
        {"label": "STANDS OVER GOAL",    "value": str(n_missing),
         "sub": "avg SOS > their goal (excl. P0)",   "color": "red",
         "delta": _cnt_d(n_missing, prior["n_missing"], prior_lbl, higher_better=False) if prior else None},
        {"label": "STANDS IN DATASET",   "value": str(len(stand_avgs)),
         "sub": f"{n_p0_stands} P0 (opening) · {len(stand_avgs) - n_p0_stands} with goals",
         "color": "grey"},
    ])

    st.markdown("---")

    # ── Goals reference ───────────────────────────────────────────────────────
    with st.expander("📋 SOS Goals by Stand Age (P0 = opening partial period, excluded from goal calc)"):
        st.caption("P0 = stand open < 28 days (opening partial period) — no goal assigned. "
                   "P1 = first full 28-day period, P2 = second, … P6+ = 6th period onward.")
        goal_cols = st.columns(len(_SOS_GOALS))
        for i, (label, target) in enumerate(_SOS_GOALS.items()):
            goal_cols[i].metric(label.split("(")[0].strip(), _fmt_sos(target),
                                help=label)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 0 — PERIOD-OVER-PERIOD TREND
    # ═════════════════════════════════════════════════════════════════════════
    st.subheader("📈 Period-over-Period Trend")
    # Period summaries computed via module-level @st.cache_data function (_sos_period_kpis)

    # ── Head-to-head picker (only when 2+ periods loaded) ────────────────────
    if len(available_periods) >= 2:
        st.caption("Comparing periods head-to-head — use the selectors above to change.")
        # Default Period A = first selected period; Period B = "Compare To" selection
        _default_a = sel_periods[0] if sel_periods[0] in available_periods else available_periods[0]
        _default_b = (cmp_to_key if cmp_to_key and cmp_to_key in available_periods
                      else available_periods[-1])
        _idx_a = available_periods.index(_default_a) if _default_a in available_periods else 0
        _idx_b = available_periods.index(_default_b) if _default_b in available_periods else len(available_periods) - 1
        cA, cVS, cB = st.columns([5, 1, 5])
        with cA:
            lbl_a = st.selectbox("Period A", available_periods,
                                 index=_idx_a, key="sos_cmp_a")
        with cVS:
            st.html('<div style="text-align:center;font-family:\'Bebas Neue\',sans-serif;'
                    'font-size:28px;color:#AC2430;padding-top:26px;letter-spacing:2px;">VS</div>')
        with cB:
            lbl_b = st.selectbox("Period B", available_periods,
                                 index=_idx_b, key="sos_cmp_b")

        sA = _sos_period_kpis(lbl_a, _stands_info_json)
        sB = _sos_period_kpis(lbl_b, _stands_info_json)

        # Scorecard: 5 metrics side by side, coloured border = improvement direction
        GREEN, RED, GREY = "#12a06e", "#AC2430", "#595959"
        metrics = [
            ("System Avg",          "_sys",   False),  # lower is better
            ("Prime Time Avg",      "_prime", False),
            ("Txns At Goal",        "_pct",   True),   # higher is better
            ("Stands Meeting Goal", None,     True),
            ("Stands Over Goal",    None,     False),
        ]
        score_cols = st.columns(len(metrics))
        for col, (m_label, raw_key, higher_good) in zip(score_cols, metrics):
            if raw_key:
                va, vb = sA[raw_key], sB[raw_key]
            else:
                va = float(sA[m_label])
                vb = float(sB[m_label])
            try:
                delta     = va - vb
                is_better = (delta < 0) if not higher_good else (delta > 0)
                color     = GREEN if is_better else (RED if delta != 0 else GREY)
                arrow     = ("▲" if delta > 0 else "▼") if delta != 0 else "—"
                fmt_delta = f"{arrow} {_fmt_sos(abs(delta))}" if raw_key in ("_sys", "_prime") else \
                            f"{arrow} {abs(delta):.1f}%" if raw_key == "_pct" else \
                            f"{arrow} {abs(int(delta))}"
            except Exception:
                color, fmt_delta = GREY, "—"
            with col:
                st.html(f"""
                <div style="background:#f8f8f8;border-radius:10px;padding:14px 10px;
                            text-align:center;border-top:3px solid {color};margin-bottom:8px;">
                  <div style="font-family:'DM Mono',monospace;font-size:10px;color:#595959;
                              text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    {m_label}</div>
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:22px;color:#1A1919;">
                    {sA[m_label]}</div>
                  <div style="font-family:'DM Mono',monospace;font-size:10px;color:#595959;margin:2px 0;">
                    vs {sB[m_label]}</div>
                  <div style="font-family:'DM Mono',monospace;font-size:11px;
                              color:{color};font-weight:600;margin-top:4px;">
                    {fmt_delta}</div>
                </div>""")

        st.markdown("")   # spacer

    # ── Trend chart + table (all available periods) ───────────────────────────
    if available_periods:
        trend_rows = [r for p in available_periods
                      if (r := _sos_period_kpis(p, _stands_info_json)) is not None]
        if not trend_rows:
            st.info("No period data available.")
            return
        trend_df = pd.DataFrame(trend_rows)

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df["Period"], y=trend_df["_sys"],
            mode="lines+markers+text", name="System Avg",
            line=dict(color="#4C78A8", width=2),
            text=trend_df["System Avg"], textposition="top center",
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_df["Period"], y=trend_df["_prime"],
            mode="lines+markers+text", name="Prime Time Avg",
            line=dict(color="#F58518", width=2),
            text=trend_df["Prime Time Avg"], textposition="bottom center",
        ))
        fig_trend.add_hline(y=3.5, line_dash="dot", line_color="green",
                            annotation_text="3:30 Mature Goal")
        fig_trend.update_yaxes(
            tickvals=[2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
            ticktext=[_fmt_sos(v) for v in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]],
            title_text="Avg SOS",
        )
        fig_trend.update_layout(
            title="System-wide SOS Trend — All Periods",
            height=360, legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.dataframe(
            trend_df[["Period", "System Avg", "Prime Time Avg",
                       "Txns At Goal", "Stands Meeting Goal", "Stands Over Goal"]],
            use_container_width=True, hide_index=True,
        )

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 0b — GOAL TIER BREAKDOWN (current period)
    # ═════════════════════════════════════════════════════════════════════════
    st.subheader("🎯 Goal Tier Breakdown — Current Period")
    st.caption("Each stand's goal is set by its age at the period midpoint (28-day periods).")

    tier_order = ["P1–P2", "P3", "P4", "P5", "P6+"]
    tier_goals = {"P1–P2": 5.0, "P3": 4.5, "P4": 4.0, "P5": 3.75, "P6+": 3.5}

    # One row per stand — vectorized prime avg (no cross-df lambda)
    _prime_by_stand = (
        df[df["IsPrimeTime"]].groupby("Stand_Label")["SOS_min"].mean()
    )
    stand_tier_df = (
        df.groupby("Stand_Label")
        .agg(
            _avg  =("SOS_min",    "mean"),
            _goal =("Stand_Goal", "first"),
            _tier =("Goal_Tier",  "first"),
        )
        .reset_index()
    )
    stand_tier_df["_prime"] = stand_tier_df["Stand_Label"].map(_prime_by_stand)

    tier_rows = []
    for tier in tier_order:
        sub = stand_tier_df[stand_tier_df["_tier"] == tier]
        if sub.empty:
            continue
        goal      = tier_goals[tier]
        n_stands  = len(sub)
        n_meeting = (sub["_avg"] <= goal).sum()
        n_missing = n_stands - n_meeting
        avg_sos   = sub["_avg"].mean()
        tier_rows.append({
            "Tier":          tier,
            "Goal":          _fmt_sos(goal),
            "# Stands":      n_stands,
            "Avg SOS":       _fmt_sos(avg_sos),
            "vs Goal":       ("+" if avg_sos - goal >= 0 else "-") + _fmt_sos(abs(avg_sos - goal)),
            "✅ Meeting":    n_meeting,
            "❌ Missing":    n_missing,
            "% Meeting":     f"{n_meeting / n_stands * 100:.0f}%",
        })

    if tier_rows:
        tier_summary_df = pd.DataFrame(tier_rows)

        # Bar chart: avg SOS per tier vs their goal
        fig_tier = go.Figure()
        for _, row in tier_summary_df.iterrows():
            goal_val = tier_goals[row["Tier"]]
            avg_val  = stand_tier_df[stand_tier_df["_tier"] == row["Tier"]]["_avg"].mean()
            colour   = "#12a06e" if avg_val <= goal_val else "#AC2430"
            fig_tier.add_trace(go.Bar(
                name=row["Tier"],
                x=[row["Tier"]],
                y=[avg_val],
                marker_color=colour,
                text=[_fmt_sos(avg_val)],
                textposition="outside",
                showlegend=False,
            ))
            # Goal line for this tier
            fig_tier.add_shape(type="line",
                x0=row["Tier"], x1=row["Tier"],
                y0=0, y1=goal_val,
                line=dict(color="white", dash="dash", width=2),
            )

        fig_tier.update_yaxes(
            tickvals=[2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
            ticktext=[_fmt_sos(v) for v in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]],
            title_text="Avg SOS",
        )
        fig_tier.update_layout(
            title="Avg SOS vs Goal — by Tier",
            height=360, barmode="overlay",
        )
        st.plotly_chart(fig_tier, use_container_width=True)

        st.dataframe(tier_summary_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 1 — PRIME TIME BY DAY
    # ═════════════════════════════════════════════════════════════════════════
    st.subheader("🕐 Prime Time by Day of Week")
    st.caption("Mon–Fri prime: 7–10am · Sat–Sun prime: 9am–1pm")

    if len(prime_df) > 0:
        # Per-day prime time avg and worst hour
        rows = []
        for day in day_order:
            day_prime = prime_df[prime_df["DayOfWeek"] == day]
            if day_prime.empty:
                continue
            avg_sos   = day_prime["SOS_min"].mean()
            is_wkend  = day in ["Saturday", "Sunday"]
            prime_s, prime_e = (9, 13) if is_wkend else (7, 10)

            # worst and best hour during prime window
            hr_avg    = day_prime.groupby("Hour")["SOS_min"].mean()
            worst_hr  = int(hr_avg.idxmax()) if not hr_avg.empty else None
            best_hr   = int(hr_avg.idxmin()) if not hr_avg.empty else None

            # # stands at/over their goal during this day's prime time
            stand_day_prime = day_prime.groupby("Stand_Label")["SOS_min"].mean()
            n_at   = sum(stand_day_prime[s] <= stand_goal_map.get(s, 3.5) for s in stand_day_prime.index)
            n_over = len(stand_day_prime) - n_at

            rows.append({
                "Day":           day,
                "_avg":          avg_sos,
                "Prime Avg SOS": _fmt_sos(avg_sos),
                "Worst Hour":    _fmt_hour(worst_hr) if worst_hr is not None else "—",
                "Best Hour":     _fmt_hour(best_hr)  if best_hr  is not None else "—",
                "✅ At Goal":    n_at,
                "❌ Over Goal":  n_over,
            })

        if rows:
            prime_day_df = pd.DataFrame(rows)

            # Bar chart
            fig_pd = px.bar(
                prime_day_df, x="Day", y="_avg",
                category_orders={"Day": day_order},
                title="Prime Time Avg SOS by Day of Week",
                color="_avg",
                color_continuous_scale="RdYlGn_r",
                range_color=[3.0, 5.5],
            )
            fig_pd.add_hline(y=3.5, line_dash="dash", line_color="green",
                             annotation_text="3:30 Mature Goal", annotation_position="bottom right")
            _apply_sos_yaxis(fig_pd)
            fig_pd.update_layout(height=360, coloraxis_showscale=False)
            fig_pd.update_traces(
                hovertemplate="<b>%{x}</b><br>Prime Avg: %{customdata}<extra></extra>",
                customdata=prime_day_df["Prime Avg SOS"],
            )
            st.plotly_chart(fig_pd, use_container_width=True)

            # Summary table
            worst_day = prime_day_df.loc[prime_day_df["_avg"].idxmax(), "Day"]
            best_day  = prime_day_df.loc[prime_day_df["_avg"].idxmin(), "Day"]
            bc1, bc2 = st.columns(2)
            bc1.metric("🔴 Worst Prime-Time Day", worst_day,
                       _fmt_sos(prime_day_df["_avg"].max()))
            bc2.metric("🟢 Best Prime-Time Day", best_day,
                       _fmt_sos(prime_day_df["_avg"].min()))

            st.dataframe(
                prime_day_df[["Day", "Prime Avg SOS", "Worst Hour", "Best Hour",
                               "✅ At Goal", "❌ Over Goal"]],
                use_container_width=True, hide_index=True,
            )

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 2 — DAY-OF-WEEK HOURLY PATTERN (averaged across all weeks)
    # ═════════════════════════════════════════════════════════════════════════
    st.subheader("📅 Day-of-Week SOS Pattern — averaged across all weeks")
    st.caption("Blends every instance of that day in the period into one curve.")

    dow_sel = st.selectbox("Day of week", day_order, index=5, key="sos_dow_sel")
    dow_df  = df[df["DayOfWeek"] == dow_sel].groupby("Hour")["SOS_min"].mean().reset_index()
    dow_df.columns = ["Hour", "SOS_min"]

    if not dow_df.empty:
        n_days     = df[df["DayOfWeek"] == dow_sel]["Date"].nunique()
        is_wkend   = dow_sel in ["Saturday", "Sunday"]
        prime_s, prime_e = (9, 13) if is_wkend else (7, 10)
        # system goal for that day (most stands mature, so 3:30 as reference line)
        st.caption(f"Based on {n_days} {dow_sel}(s) in the data.")

        fig_dow = px.line(
            dow_df, x="Hour", y="SOS_min",
            title=f"Average SOS by Hour — {dow_sel} (n={n_days})",
            labels={"SOS_min": "Avg SOS", "Hour": "Hour of Day"},
            markers=True,
        )
        fig_dow.add_hline(y=3.5, line_dash="dash", line_color="green",
                          annotation_text="3:30 Mature Goal", annotation_position="bottom right")
        fig_dow.add_vrect(
            x0=prime_s - 0.5, x1=prime_e - 0.5,
            fillcolor="orange", opacity=0.10,
            annotation_text="Prime Time", annotation_position="top left",
        )
        _apply_sos_yaxis(fig_dow)
        fig_dow.update_layout(height=400)
        st.plotly_chart(fig_dow, use_container_width=True)

        dow_table = dow_df.copy()
        dow_table["Time Slot"]  = dow_table["Hour"].apply(_fmt_hour)
        dow_table["Avg SOS"]    = dow_table["SOS_min"].apply(_fmt_sos)
        dow_table["vs 3:30"]    = dow_table["SOS_min"].apply(
            lambda v: ("+" if v - 3.5 >= 0 else "-") + _fmt_sos(abs(v - 3.5))
        )
        dow_table["Prime Time"] = dow_table["Hour"].apply(
            lambda h: "⏰" if (prime_s <= h < prime_e) else ""
        )
        st.dataframe(
            dow_table[["Time Slot", "Avg SOS", "vs 3:30", "Prime Time"]]
            .style.map(_colour_sos_cell, subset=["Avg SOS"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info(f"No hourly data for {dow_sel}.")

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 3 — HEATMAP Day × Hour
    # ═════════════════════════════════════════════════════════════════════════
    st.subheader("🌡️ Heatmap — Hour of Day × Day of Week")
    st.caption("Darker red = slower. Prime time: Mon–Fri 7–10am · Sat–Sun 9am–1pm.")

    heat_df    = df.groupby(["DayOfWeek", "Hour"])["SOS_min"].mean().reset_index()
    heat_pivot = heat_df.pivot(index="DayOfWeek", columns="Hour", values="SOS_min").reindex(day_order)
    fig_h = px.imshow(
        heat_pivot,
        color_continuous_scale="RdYlGn_r",
        zmin=2.5, zmax=5.5,
        labels={"color": "Avg SOS", "x": "Hour", "y": "Day of Week"},
        title="Avg SOS — Hour × Day of Week",
        aspect="auto",
    )
    fig_h.update_traces(
        hovertemplate="<b>%{y} — %{x}:00</b><br>Avg SOS: %{z:.2f} min<extra></extra>"
    )
    fig_h.update_layout(height=380, coloraxis_colorbar=dict(
        tickvals=_sos_ticks, ticktext=_sos_ticklabels, title="Avg SOS",
    ))
    st.plotly_chart(fig_h, use_container_width=True)

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 4 — TREND VIEWS (Hourly / Daily / Weekly)
    # ═════════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns(2)
    view_mode  = c1.selectbox("View",     ["Hourly", "Daily", "Weekly"], key="sos_view")
    group_mode = c2.selectbox("Group by", ["Stand", "State", "Region", "Cohort"], key="sos_group")

    def _group_col():
        mapping = {"Stand": "Stand_Label", "State": "State",
                   "Region": "Region", "Cohort": "Cohort"}
        return mapping.get(group_mode, "Stand_Label")

    gcol = _group_col()
    st.subheader(f"{view_mode} SOS — by {group_mode}")

    if view_mode == "Hourly":
        hour_df = df.groupby([gcol, "Hour"])["SOS_min"].mean().reset_index()
        hour_df.columns = [gcol, "Hour", "SOS_min"]
        fig = px.line(hour_df, x="Hour", y="SOS_min", color=gcol,
                      title=f"Avg SOS by Hour — {group_mode}",
                      labels={"SOS_min": "Avg SOS", "Hour": "Hour"})
        fig.add_hline(y=3.5, line_dash="dash", line_color="green",
                      annotation_text="3:30 Goal", annotation_position="bottom right")
        _apply_sos_yaxis(fig)
        fig.update_layout(height=440, legend_title=group_mode)
        st.plotly_chart(fig, use_container_width=True)

    elif view_mode == "Daily":
        day_df = df.groupby([gcol, "Date"])["SOS_min"].mean().reset_index()
        day_df.columns = [gcol, "Date", "SOS_min"]
        day_df["Date"] = pd.to_datetime(day_df["Date"])
        fig = px.line(day_df, x="Date", y="SOS_min", color=gcol,
                      title=f"Daily Avg SOS — {group_mode}",
                      labels={"SOS_min": "Avg SOS", "Date": "Date"})
        fig.add_hline(y=3.5, line_dash="dash", line_color="green",
                      annotation_text="3:30 Goal", annotation_position="bottom right")
        _apply_sos_yaxis(fig)
        fig.update_layout(height=440, legend_title=group_mode)
        st.plotly_chart(fig, use_container_width=True)

    elif view_mode == "Weekly":
        wk_df = df.groupby([gcol, "WeekLabel"])["SOS_min"].mean().reset_index()
        wk_df.columns = [gcol, "Week", "SOS_min"]
        fig = px.bar(wk_df, x="Week", y="SOS_min", color=gcol, barmode="group",
                     title=f"Weekly Avg SOS — {group_mode}",
                     labels={"SOS_min": "Avg SOS", "Week": "Week"})
        fig.add_hline(y=3.5, line_dash="dash", line_color="green",
                      annotation_text="3:30 Goal", annotation_position="bottom right")
        _apply_sos_yaxis(fig)
        fig.update_layout(height=440, legend_title=group_mode)
        st.plotly_chart(fig, use_container_width=True)

    # ── Ranking table (age-based goals) ──────────────────────────────────────
    st.subheader(f"📊 {group_mode} Ranking — Avg SOS vs Age-Based Goal")
    rank_df = df.groupby(gcol).agg(
        _avg_raw=("SOS_min", "mean"),
        _med_raw=("SOS_min", "median"),
        Transactions=("SOS_min", "count"),
        _goal=("Stand_Goal", "first") if gcol == "Stand_Label" else ("Stand_Goal", "mean"),
    ).reset_index()
    rank_df = rank_df.sort_values("_avg_raw")
    rank_df.insert(0, "Rank", range(1, len(rank_df) + 1))
    rank_df["Avg SOS"]    = rank_df["_avg_raw"].apply(_fmt_sos)
    rank_df["Median SOS"] = rank_df["_med_raw"].apply(_fmt_sos)
    rank_df["Goal"]       = rank_df["_goal"].apply(_fmt_sos)
    rank_df["vs Goal"]    = rank_df.apply(lambda r: _vs_goal_str(r["_avg_raw"], r["_goal"]), axis=1)
    rank_df["Status"]     = rank_df.apply(
        lambda r: "✅ At Goal" if r["_avg_raw"] <= r["_goal"] else "❌ Over Goal", axis=1
    )

    disp_cols = ["Rank", gcol, "Goal", "Avg SOS", "Median SOS", "vs Goal", "Status", "Transactions"]
    st.dataframe(
        rank_df[disp_cols].style.map(_colour_sos_cell, subset=["Avg SOS"]),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 5 — WINS & OPPORTUNITIES
    # ═════════════════════════════════════════════════════════════════════════
    st.subheader("🏆 Wins & Opportunities")

    op_avg  = offpeak_df["SOS_min"].mean() if len(offpeak_df) > 0 else None

    wc1, wc2 = st.columns(2)
    wc1.metric("Prime Time Avg SOS",  _fmt_sos(prime_avg))
    wc2.metric("Off-Peak Avg SOS",    _fmt_sos(op_avg) if op_avg else "—")

    if op_avg:
        delta_str = _fmt_sos(abs(prime_avg - op_avg))
        direction = "slower" if prime_avg > op_avg else "faster"
        colour    = "#AC2430" if prime_avg > op_avg else "#12a06e"
        st.markdown(
            f"<span style='color:{colour};font-weight:bold'>"
            f"Prime time is {delta_str} {direction} than off-peak system-wide."
            f"</span>",
            unsafe_allow_html=True,
        )

    if df["Hour"].notna().any():
        hour_sys = df.groupby("Hour")["SOS_min"].mean()
        worst_hr_num = int(hour_sys.idxmax())
        best_hr_num  = int(hour_sys.idxmin())
        wo1, wo2 = st.columns(2)
        wo1.metric("🔴 Slowest Hour", _fmt_sos(hour_sys[worst_hr_num]),
                   help=f"System-wide avg — {_fmt_hour(worst_hr_num)}")
        wo1.caption(f"{_fmt_hour(worst_hr_num)}")
        wo2.metric("🟢 Fastest Hour", _fmt_sos(hour_sys[best_hr_num]),
                   help=f"System-wide avg — {_fmt_hour(best_hr_num)}")
        wo2.caption(f"{_fmt_hour(best_hr_num)}")

    # Top / Bottom prime time — vs each stand's age-based goal
    st.markdown("#### Top 5 Stands — Prime Time vs Their Goal 🟢")
    if len(prime_df) > 0:
        pt_by_stand = prime_df.groupby("Stand_Label")["SOS_min"].mean()
        pt_goal     = df.groupby("Stand_Label")["Stand_Goal"].first()
        pt_delta    = (pt_by_stand - pt_goal).sort_values()   # most negative = furthest under goal

        top5 = pt_delta.head(5).reset_index()
        top5.columns = ["Stand", "_delta"]
        top5["Goal"]          = top5["Stand"].map(pt_goal).apply(_fmt_sos)
        top5["Prime Time SOS"]= top5["Stand"].map(pt_by_stand).apply(_fmt_sos)
        top5["vs Goal"]       = top5.apply(
            lambda r: _vs_goal_str(
                pt_by_stand.get(r["Stand"], float("nan")),
                pt_goal.get(r["Stand"], float("nan")),
            ), axis=1
        )
        top5.insert(0, "Rank", range(1, 6))
        st.dataframe(
            top5[["Rank", "Stand", "Goal", "Prime Time SOS", "vs Goal"]]
            .style.map(_colour_sos_cell, subset=["Prime Time SOS"]),
            use_container_width=True, hide_index=True,
        )

    st.markdown("#### Bottom 5 Stands — Prime Time vs Their Goal 🔴")
    if len(prime_df) > 0:
        bot5 = pt_delta.tail(5).sort_values(ascending=False).reset_index()
        bot5.columns = ["Stand", "_delta"]
        bot5["Goal"]          = bot5["Stand"].map(pt_goal).apply(_fmt_sos)
        bot5["Prime Time SOS"]= bot5["Stand"].map(pt_by_stand).apply(_fmt_sos)
        bot5["vs Goal"]       = bot5.apply(
            lambda r: _vs_goal_str(
                pt_by_stand.get(r["Stand"], float("nan")),
                pt_goal.get(r["Stand"], float("nan")),
            ), axis=1
        )
        bot5.insert(0, "Rank", range(1, 6))
        st.dataframe(
            bot5[["Rank", "Stand", "Goal", "Prime Time SOS", "vs Goal"]]
            .style.map(_colour_sos_cell, subset=["Prime Time SOS"]),
            use_container_width=True, hide_index=True,
        )

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 6 — INDIVIDUAL STAND DETAIL
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🔍 Individual Stand Detail")
    stand_options = sorted(df["Stand_Label"].dropna().unique().tolist())
    sel_stand     = st.selectbox("Select stand", stand_options, key="sos_stand_sel")
    stand_df      = df[df["Stand_Label"] == sel_stand].copy()

    if not stand_df.empty:
        this_sn       = stand_df["Store_Num"].iloc[0]
        this_goal     = stand_df["Stand_Goal"].iloc[0]
        this_tier     = stand_df["Goal_Tier"].iloc[0]
        this_days     = _days_open(this_sn)
        age_str       = f"{this_days} days open ({this_tier})" if this_days is not None else "age unknown"
        prime_stand   = stand_df[stand_df["IsPrimeTime"]]["SOS_min"].mean()

        st.caption(f"Stand age at period midpoint: {age_str} · Goal: {_fmt_sos(this_goal)}")

        sa, sb, sc, sd = st.columns(4)
        sa.metric("Avg SOS (all hours)", _fmt_sos(stand_df["SOS_min"].mean()))
        sb.metric("Prime Time Avg",      _fmt_sos(prime_stand) if not pd.isna(prime_stand) else "—")
        sc.metric("Age-Based Goal",      _fmt_sos(this_goal))
        sd.metric("Transactions",        f"{len(stand_df):,}")

        # Daily trend with goal line
        daily_stand = stand_df.groupby("Date")["SOS_min"].mean().reset_index()
        daily_stand["Date"] = pd.to_datetime(daily_stand["Date"])
        detail_fig = px.line(daily_stand, x="Date", y="SOS_min",
                             title=f"Daily SOS — {sel_stand}", markers=True)
        detail_fig.add_hline(y=this_goal, line_dash="dash", line_color="green",
                             annotation_text=f"Goal {_fmt_sos(this_goal)}")
        _apply_sos_yaxis(detail_fig)
        detail_fig.update_layout(height=320)
        st.plotly_chart(detail_fig, use_container_width=True)

        # Hourly bar chart with goal line
        if stand_df["Hour"].notna().any():
            hr_stand = stand_df.groupby("Hour")["SOS_min"].mean().reset_index()
            hr_stand.columns = ["Hour", "SOS_min"]
            fig_hr = px.bar(hr_stand, x="Hour", y="SOS_min",
                            title=f"Hourly Profile — {sel_stand}",
                            color="SOS_min",
                            color_continuous_scale="RdYlGn_r",
                            range_color=[2.5, 5.5])
            fig_hr.add_hline(y=this_goal, line_dash="dash", line_color="green",
                             annotation_text=f"Goal {_fmt_sos(this_goal)}")
            _apply_sos_yaxis(fig_hr)
            fig_hr.update_layout(height=300, coloraxis_showscale=False)
            st.plotly_chart(fig_hr, use_container_width=True)


# ─────────────────────────────────────────────
# TAB: FORECAST
# ─────────────────────────────────────────────
def tab_forecast(dash):
    if not _require_password("forecast"):
        return
    section("FORECAST P4–P13 2026 (Draft)", "P1–P3 actuals locked · P4–P13 projected · 3 scenarios · Seasonal watch notes")

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
        st.plotly_chart(fig, config={"displayModeBar": False})

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
                               yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig2, config={"displayModeBar": False})

    # Forecast table
    st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#1A1919;margin:16px 0 8px;">PERIOD-BY-PERIOD FORECAST TABLE</div>')
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
    fc_cols = ["Type", "Period", "Prior Yr Sales", "Prior Yr EBITDA%",
               "Base Sales", "Base EBITDA%", "Opt EBITDA%", "Risk EBITDA%", "Watch Note"]
    render_table(fc_display[fc_cols].reset_index(drop=True))


# ─────────────────────────────────────────────
# TAB: POTHOLE WATCH
# ─────────────────────────────────────────────
def tab_potholes(dash):
    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash)
    section("⚠ POTHOLE WATCH", "Maturity-adjusted risks — established stands only · new stands tracked separately")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}
    sel_lbl = st.selectbox("Analyze Period", [l for l, _ in all_options], key="pot_period")
    pk = label_to_key[sel_lbl]
    ps_stands = stands_df[stands_df["Period_Key"] == pk]
    if ps_stands.empty:
        st.info("No data for this period.")
        return

    ps = periods_df[periods_df["period_key"] == pk].iloc[0]

    # ── Separate by maturity ──────────────────────────────────────────────────
    NEW_BUCKETS = ["New (<6mo)"]
    EST_BUCKETS = ["Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
    if "Age_Bucket" in ps_stands.columns:
        new_stands  = ps_stands[ps_stands["Age_Bucket"].isin(NEW_BUCKETS)]
        est_stands  = ps_stands[ps_stands["Age_Bucket"].isin(EST_BUCKETS)]
        # Unclassified treated as established (conservative — avoids false flagging)
        unclass = ps_stands[~ps_stands["Age_Bucket"].isin(NEW_BUCKETS + EST_BUCKETS)]
        est_stands = pd.concat([est_stands, unclass], ignore_index=True)
    else:
        new_stands = pd.DataFrame()
        est_stands = ps_stands

    n_new = len(new_stands)
    n_est = len(est_stands)

    # Show maturity context banner
    if n_new > 0:
        avg_new_labor  = new_stands["Total_Labor_pct"].mean() if "Total_Labor_pct" in new_stands else 0
        avg_est_labor  = est_stands["Total_Labor_pct"].mean() if n_est and "Total_Labor_pct" in est_stands else 0
        st.html(f"""
        <div style="background:#fff8e1;border-left:4px solid #e8940a;border-radius:6px;
                    padding:12px 16px;margin-bottom:14px;font-family:'DM Mono',monospace;font-size:12px;">
          <strong>📋 Maturity Filter Active:</strong> {n_new} new stand(s) (&lt;6 months) are excluded from Critical Issues
          — their elevated labor ({_fmt_p(avg_new_labor)} avg) and lower EBITDA are expected during ramp.
          Established stands ({n_est}) avg labor: {_fmt_p(avg_est_labor)}.
          New stands are reviewed separately in the Ramp-Up section below.
        </div>""")

    col1, col2 = st.columns(2)

    # ── Critical Issues — established stands only ─────────────────────────────
    with col1:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;'
                'color:#AC2430;margin-bottom:10px;">🚨 CRITICAL ISSUES — ESTABLISHED STANDS</div>')

        if est_stands.empty:
            st.info("No established stands in this period.")
        else:
            # Highest discount (ALL stands — discount anomalies aren't maturity-driven)
            top_disc = ps_stands.nlargest(1, "Discounts_pct").iloc[0]
            disc_age = top_disc.get("Age_Bucket", "")
            disc_note = f" ({disc_age})" if disc_age else ""
            insight_card(
                f"🚨 Highest Discount: {top_disc['Stand'].split(',')[0]}{disc_note}",
                f"{_fmt_p(top_disc['Discounts_pct'])} discount rate — "
                f"{top_disc['Discounts_pct']/0.028:.1f}× the 2.8% system avg. "
                f"Discount issues aren't ramp-related — check POS config and promo authorization.",
                tag=_fmt_p(top_disc['Discounts_pct']), tag_cls="red",
            )

            # High labor — established stands only
            top_labor = est_stands.nlargest(1, "Total_Labor_pct").iloc[0]
            avg_sys_labor = ps["labor_pct"]
            labor_gap = top_labor["Total_Labor_pct"] - avg_sys_labor
            insight_card(
                f"🚨 High Labor (Est.): {top_labor['Stand'].split(',')[0]}",
                f"{_fmt_p(top_labor['Total_Labor_pct'])} Total Labor — "
                f"{_fmt_bps(labor_gap)} above the {_fmt_p(avg_sys_labor)} system avg. "
                f"This stand is past ramp — scheduling inefficiency or staffing model issue. "
                f"EBITDA: {_fmt_p(top_labor['Store_EBITDA_pct'])}.",
                tag=_fmt_p(top_labor['Total_Labor_pct']), tag_cls="red",
            )

            # Worst EBITDA — established stands only
            worst_ebi = est_stands.nsmallest(1, "Store_EBITDA_pct").iloc[0]
            insight_card(
                f"🚨 Lowest EBITDA (Est.): {worst_ebi['Stand'].split(',')[0]}",
                f"{_fmt_p(worst_ebi['Store_EBITDA_pct'])} EBITDA on {_fmt_d(worst_ebi['Net_Sales'])} sales. "
                f"This is an established location — underperformance is a real issue, not ramp noise. "
                f"Labor {_fmt_p(worst_ebi['Total_Labor_pct'])}, COGS {_fmt_p(worst_ebi['Total_COGS_pct'])}.",
                tag=_fmt_p(worst_ebi['Store_EBITDA_pct']), tag_cls="red",
            )

            # R&M — established stands disproportionately affected by aging equipment
            top_rm = est_stands.nlargest(1, "Total_RM_pct").iloc[0]
            if top_rm["Total_RM_pct"] > 0.02:
                insight_card(
                    f"🚨 High R&M (Est.): {top_rm['Stand'].split(',')[0]}",
                    f"{_fmt_p(top_rm['Total_RM_pct'])} R&M — {top_rm['Total_RM_pct']/0.011:.1f}× system avg. "
                    f"Established stands with high R&M signal equipment aging or deferred maintenance. "
                    f"Schedule a condition audit.",
                    tag=_fmt_p(top_rm['Total_RM_pct']), tag_cls="amber",
                )

            # Multi-issue stands: high labor AND low EBITDA
            multi_issue = est_stands[
                (est_stands["Total_Labor_pct"] > 0.27) &
                (est_stands["Store_EBITDA_pct"] < 0.12)
            ]
            if len(multi_issue) > 1:
                names = ", ".join(multi_issue["Stand"].str.split(",").str[0].tolist()[:4])
                insight_card(
                    f"🚨 Multi-Issue Cluster: {len(multi_issue)} Established Stands",
                    f"These stands have both high labor (>27%) AND low EBITDA (<12%): {names}. "
                    f"Cluster pattern suggests a systemic issue — staffing model, market, or management.",
                    tag=f"{len(multi_issue)} Stands", tag_cls="red",
                )

    # ── Forward-looking watch items ───────────────────────────────────────────
    with col2:
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;'
                'color:#e8940a;margin-bottom:10px;">⚠ FORWARD-LOOKING RISKS</div>')

        # Dynamic: flag regions with consistently high labor in this period
        reg_df = get_regions_df(dash, pk)
        high_labor_regions = []
        if not reg_df.empty and "labor_pct" in reg_df.columns:
            sys_labor = float(ps.get("labor_pct", 0))
            for _, rrow in reg_df.iterrows():
                if rrow.get("labor_pct", 0) > sys_labor + 0.04:
                    high_labor_regions.append((rrow["region"], rrow["labor_pct"]))
        if high_labor_regions:
            reg_list = ", ".join(f"{r} ({_fmt_p(l)})" for r, l in sorted(high_labor_regions, key=lambda x: -x[1]))
            insight_card(
                f"⚠ Regional Labor Gap: {len(high_labor_regions)} Region(s) 400bps+ Above Avg",
                f"{reg_list} are running 400bps+ above system avg labor. "
                f"Regional labor creep compounds quickly — investigate scheduling and staffing ratios.",
                tag="Labor Risk", tag_cls="amber", card_cls="watch",
            )

        # Dynamic: stands with declining sales trend (this period vs system avg)
        low_sales = est_stands[est_stands["Net_Sales"] < est_stands["Net_Sales"].quantile(0.15)]
        if len(low_sales) >= 2:
            names = ", ".join(low_sales.nsmallest(3, "Net_Sales")["Stand"].str.split(",").str[0].tolist())
            insight_card(
                f"⚠ Low-Volume Established Stands ({len(low_sales)} in bottom 15%)",
                f"Bottom performers by sales: {names}. "
                f"For established locations, low volume may indicate market saturation, location issues, "
                f"or operational problems — not just ramp lag.",
                tag="Volume Risk", tag_cls="amber", card_cls="watch",
            )

        # Seasonal / structural watch items
        watch_items = [
            ("⚠ Summer Labor P6–P8",
             "Historical data shows P6–P8 EBITDA compresses 300–500bps vs spring. Vacation coverage, "
             "call-outs, and training overlap for summer new opens create labor creep. Build the schedule now.",
             "Seasonal Risk", "amber"),
            ("⚠ P12–P13 Year-End Pattern",
             "P12–P13 historically run 600–900bps below peak EBITDA. Holiday fixed cost absorption + "
             "traffic slowdown. No deferred expenses into year-end — plan cost controls in P11.",
             "Seasonal Risk", "amber"),
            ("⚠ New Stand Pipeline Dilution",
             "Each new opening carries 25–35% labor for 60–90 days and compresses system EBITDA% by "
             "~150–200bps per cohort. Factor into board-level EBITDA guidance.",
             "~150–200bps dilution", "grey"),
            ("⚠ Aging Equipment — 2022–2023 Vintage",
             "Stands opened 2022–2023 are now 2–4 years old. R&M% tends to spike after year 3. "
             "Any stand over 2.0% R&M should get a proactive equipment condition audit before P6.",
             "Equipment Risk", "grey"),
        ]
        for title, body, tag, tag_cls in watch_items:
            insight_card(title, body, tag, tag_cls, "watch")

    # ── New Stand Ramp-Up Watch ───────────────────────────────────────────────
    if n_new > 0:
        st.html('<hr class="brew">')
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;'
                'color:#e8940a;margin:8px 0 6px;">🆕 NEW STAND RAMP-UP WATCH</div>')
        st.html('<div style="font-family:DM Mono,monospace;font-size:12px;color:#595959;margin-bottom:12px;">'
                'Excluded from Critical Issues above — benchmarks adjusted for ramp-phase norms</div>')

        ramp_col1, ramp_col2 = st.columns(2)
        with ramp_col1:
            # New stands above extreme thresholds (35%+ labor or negative EBITDA)
            extreme_labor = new_stands[new_stands["Total_Labor_pct"] > 0.35]
            negative_ebi  = new_stands[new_stands["Store_EBITDA_pct"] < 0.0]
            fast_ramp     = new_stands[new_stands["Store_EBITDA_pct"] > 0.15]

            if len(extreme_labor):
                names = ", ".join(extreme_labor["Stand"].str.split(",").str[0].tolist()[:3])
                insight_card(
                    f"🔶 Extreme Labor — {len(extreme_labor)} New Stand(s) >35%",
                    f"{names}. Normal ramp is 28–32% labor — these are well above. "
                    f"Verify minimum staffing compliance and training timelines.",
                    tag=">35% Labor", tag_cls="amber",
                )
            if len(negative_ebi):
                names = ", ".join(negative_ebi["Stand"].str.split(",").str[0].tolist()[:3])
                insight_card(
                    f"🔶 Negative EBITDA — {len(negative_ebi)} New Stand(s)",
                    f"{names}. Some loss is expected in first 30–60 days but "
                    f"persistent negative EBITDA after that warrants a staffing model review.",
                    tag="Negative EBITDA", tag_cls="amber",
                )
            if len(fast_ramp):
                names = ", ".join(fast_ramp["Stand"].str.split(",").str[0].tolist()[:3])
                insight_card(
                    f"🚀 Fast Ramp — {len(fast_ramp)} New Stand(s) Already >15% EBITDA",
                    f"{names}. These new opens are ahead of curve — strong market fit and execution.",
                    tag="Ahead of Ramp", tag_cls="green",
                )
            if not len(extreme_labor) and not len(negative_ebi):
                insight_card("✅ New Stands Within Ramp Norms",
                             f"All {n_new} new stand(s) are within expected ramp ranges for labor and EBITDA. "
                             f"No action needed this period.", tag="On Track", tag_cls="green")

        with ramp_col2:
            # Ramp table
            ramp_cols = ["Stand", "Net_Sales", "Total_Labor_pct", "Total_COGS_pct",
                         "Store_EBITDA_pct", "Age_Bucket"]
            ramp_show = new_stands[[c for c in ramp_cols if c in new_stands.columns]].copy()
            ramp_show["Net_Sales"] = ramp_show["Net_Sales"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
            for pct_col in ["Total_Labor_pct", "Total_COGS_pct", "Store_EBITDA_pct"]:
                if pct_col in ramp_show.columns:
                    ramp_show[pct_col] = ramp_show[pct_col].apply(
                        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
            ramp_show.columns = [c.replace("Total_","").replace("_pct"," %")
                                  .replace("Store_EBITDA","EBITDA").replace("Net_Sales","Sales")
                                  for c in ramp_show.columns]
            render_table(ramp_show.reset_index(drop=True))


# ─────────────────────────────────────────────
# TAB: UTILITIES & R&M
# ─────────────────────────────────────────────
def tab_utilities(dash):
    import numpy as np

    periods_df = get_periods_df(dash)
    stands_df  = get_stands_df(dash).copy()
    section("UTILITIES & R&M", "Filter by period · region · stand for detailed diagnosis")

    # ── Detect available sub-columns ──────────────────────────────────────────
    sub_avail = {
        "Electricity":   "Electricity"   in stands_df.columns and stands_df["Electricity"].fillna(0).sum() > 0,
        "Water_Sewer":   "Water_Sewer"   in stands_df.columns and stands_df["Water_Sewer"].fillna(0).sum() > 0,
        "Waste_Removal": "Waste_Removal" in stands_df.columns and stands_df["Waste_Removal"].fillna(0).sum() > 0,
        "RM_Equipment":  "RM_Equipment"  in stands_df.columns and stands_df["RM_Equipment"].fillna(0).sum() > 0,
        "RM_Building":   "RM_Building"   in stands_df.columns and stands_df["RM_Building"].fillna(0).sum() > 0,
        "Landscaping":   "Landscaping"   in stands_df.columns and stands_df["Landscaping"].fillna(0).sum() > 0,
    }
    has_detail = any(sub_avail.values())

    # Compute Total_Utilities and Total_RM per stand from components
    util_comp = [c for c in ["Electricity", "Water_Sewer", "Waste_Removal"] if c in stands_df.columns]
    rm_comp   = [c for c in ["RM_Equipment", "RM_Building"] if c in stands_df.columns]
    if "Total_Utilities" not in stands_df.columns or stands_df["Total_Utilities"].fillna(0).sum() == 0:
        stands_df["Total_Utilities"] = stands_df[util_comp].fillna(0).sum(axis=1) if util_comp else 0
    if "Total_RM" not in stands_df.columns or stands_df["Total_RM"].fillna(0).sum() == 0:
        stands_df["Total_RM"] = stands_df[rm_comp].fillna(0).sum(axis=1) if rm_comp else 0

    # ── FILTER BAR ───────────────────────────────────────────────────────────
    all_options  = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}

    fil_col1, fil_col2, fil_col3 = st.columns([2, 2, 3])
    with fil_col1:
        sel_lbl = st.selectbox("Period", [l for l, _ in all_options], key="util_period")
        pk      = label_to_key[sel_lbl]

    period_stands = stands_df[stands_df["Period_Key"] == pk].copy()
    all_regions   = ["All Regions"] + sorted(period_stands["Region"].dropna().unique().tolist())

    with fil_col2:
        sel_region = st.selectbox("Region", all_regions, key="util_region")

    pool       = period_stands[period_stands["Region"] == sel_region] if sel_region != "All Regions" else period_stands
    stand_names = ["All Stands"] + sorted(pool["Stand"].dropna().unique().tolist())

    with fil_col3:
        sel_stand = st.selectbox("Stand", stand_names, key="util_stand")

    st.html('<hr class="brew">')

    # ── SECTION 1: Company-Level PoP Charts (with entity overlay) ────────────
    section("COMPANY OVERVIEW", "System-wide trend — selected entity shown as dashed overlay")

    PERIOD_DAYS = 28   # all 7BREW periods are exactly 4 weeks

    pct_df = periods_df.copy()
    pct_df["util_$"] = pct_df["utilities_pct"] * pct_df["net_sales"]
    pct_df["rm_$"]   = pct_df["rm_pct"]        * pct_df["net_sales"]

    # Stand count per period (for $/stand/day normalization)
    stand_cnt_map = stands_df.groupby("Period_Key")["Stand"].nunique()
    pct_df["stand_count"] = pct_df["period_key"].map(stand_cnt_map).fillna(1).astype(float)
    pct_df["util_per_std_day"] = pct_df["util_$"] / (pct_df["stand_count"] * PERIOD_DAYS)
    pct_df["rm_per_std_day"]   = pct_df["rm_$"]   / (pct_df["stand_count"] * PERIOD_DAYS)

    # Build per-period overlay for selected region or stand
    # Tracks both % of sales and $/stand/day
    overlay_label        = None
    overlay_util_map     = {}   # period_key -> util fraction of sales
    overlay_rm_map       = {}
    overlay_util_day_map = {}   # period_key -> util $/stand/day
    overlay_rm_day_map   = {}
    overlay_waste_map    = {}   # period_key -> waste fraction of sales
    overlay_land_map     = {}   # period_key -> landscaping fraction of sales

    if sel_stand != "All Stands":
        overlay_label = sel_stand
        for pk_iter, grp in stands_df[stands_df["Stand"] == sel_stand].groupby("Period_Key"):
            s = grp["Net_Sales"].sum()
            if s > 0:
                u = grp["Total_Utilities"].sum()
                r = grp["Total_RM"].sum()
                overlay_util_map[pk_iter]     = u / s
                overlay_rm_map[pk_iter]       = r / s
                overlay_util_day_map[pk_iter] = u / PERIOD_DAYS          # 1 stand
                overlay_rm_day_map[pk_iter]   = r / PERIOD_DAYS
                if "Waste_Removal" in grp.columns:
                    overlay_waste_map[pk_iter] = grp["Waste_Removal"].fillna(0).sum() / s
                if "Landscaping" in grp.columns:
                    overlay_land_map[pk_iter]  = grp["Landscaping"].fillna(0).sum() / s
    elif sel_region != "All Regions":
        overlay_label = sel_region
        for pk_iter, grp in stands_df[stands_df["Region"] == sel_region].groupby("Period_Key"):
            s = grp["Net_Sales"].sum()
            n = max(grp["Stand"].nunique(), 1)
            if s > 0:
                u = grp["Total_Utilities"].sum()
                r = grp["Total_RM"].sum()
                overlay_util_map[pk_iter]     = u / s
                overlay_rm_map[pk_iter]       = r / s
                overlay_util_day_map[pk_iter] = u / (n * PERIOD_DAYS)
                overlay_rm_day_map[pk_iter]   = r / (n * PERIOD_DAYS)
                if "Waste_Removal" in grp.columns:
                    overlay_waste_map[pk_iter] = grp["Waste_Removal"].fillna(0).sum() / s
                if "Landscaping" in grp.columns:
                    overlay_land_map[pk_iter]  = grp["Landscaping"].fillna(0).sum() / s

    ov_labels, ov_util, ov_rm = [], [], []
    ov_util_day, ov_rm_day    = [], []
    for _, row in pct_df.iterrows():
        if row["period_key"] in overlay_util_map:
            ov_labels.append(row["label"])
            ov_util.append(overlay_util_map[row["period_key"]] * 100)
            ov_rm.append(overlay_rm_map[row["period_key"]] * 100)
            ov_util_day.append(overlay_util_day_map.get(row["period_key"], 0))
            ov_rm_day.append(overlay_rm_day_map.get(row["period_key"], 0))

    has_util_ov     = bool(ov_labels) and any(v > 0 for v in ov_util)
    has_rm_ov       = bool(ov_labels) and any(v > 0 for v in ov_rm)
    has_util_day_ov = bool(ov_labels) and any(v > 0 for v in ov_util_day)
    has_rm_day_ov   = bool(ov_labels) and any(v > 0 for v in ov_rm_day)
    title_sfx       = f" · {overlay_label}" if overlay_label else ""

    # Chart 1: Total Utilities PoP
    fig = go.Figure()
    fig.add_bar(x=pct_df["label"], y=pct_df["util_$"] / 1000,
                name="System Utilities ($k)", marker_color=BLUE, opacity=0.7)
    fig.add_scatter(x=pct_df["label"], y=pct_df["utilities_pct"] * 100,
                    name="System Util %", mode="lines+markers",
                    line=dict(color=BLUE, width=2), marker=dict(size=5), yaxis="y2")
    if has_util_ov:
        fig.add_scatter(x=ov_labels, y=ov_util,
                        name=f"{overlay_label} Util %", mode="lines+markers",
                        line=dict(color=RED, width=2, dash="dot"),
                        marker=dict(size=7, symbol="diamond"), yaxis="y2")
    fig.update_layout(
        yaxis=dict(title="Total Utilities ($k)", tickprefix="$", ticksuffix="k"),
        yaxis2=dict(title="% of Net Sales", overlaying="y", side="right",
                    ticksuffix="%", tickfont=dict(size=9, color=BLUE)),
    )
    brew_fig(fig, height=350)
    fig.update_layout(title_text=f"TOTAL UTILITIES — PERIOD OVER PERIOD{title_sfx}",
                      xaxis=dict(tickangle=-35))
    st.plotly_chart(fig, config={"displayModeBar": False})

    # Chart 2: Total R&M PoP
    fig2 = go.Figure()
    fig2.add_bar(x=pct_df["label"], y=pct_df["rm_$"] / 1000,
                 name="System R&M ($k)", marker_color=AMBER, opacity=0.7)
    fig2.add_scatter(x=pct_df["label"], y=pct_df["rm_pct"] * 100,
                     name="System R&M %", mode="lines+markers",
                     line=dict(color=AMBER, width=2), marker=dict(size=5), yaxis="y2")
    if has_rm_ov:
        fig2.add_scatter(x=ov_labels, y=ov_rm,
                         name=f"{overlay_label} R&M %", mode="lines+markers",
                         line=dict(color=RED, width=2, dash="dot"),
                         marker=dict(size=7, symbol="diamond"), yaxis="y2")
    fig2.update_layout(
        yaxis=dict(title="Total R&M ($k)", tickprefix="$", ticksuffix="k"),
        yaxis2=dict(title="% of Net Sales", overlaying="y", side="right",
                    ticksuffix="%", tickfont=dict(size=9, color=AMBER)),
    )
    brew_fig(fig2, height=350)
    fig2.update_layout(title_text=f"TOTAL R&M — PERIOD OVER PERIOD{title_sfx}",
                       xaxis=dict(tickangle=-35))
    st.plotly_chart(fig2, config={"displayModeBar": False})

    # Chart 3: $/Stand/Day — removes both network-size and sales-volume effects
    has_day_data = pct_df["util_per_std_day"].sum() > 0 or pct_df["rm_per_std_day"].sum() > 0
    if has_day_data:
        fig3 = go.Figure()
        fig3.add_scatter(x=pct_df["label"], y=pct_df["util_per_std_day"],
                         name="System Util $/Stand/Day", mode="lines+markers",
                         line=dict(color=BLUE, width=2), marker=dict(size=5))
        fig3.add_scatter(x=pct_df["label"], y=pct_df["rm_per_std_day"],
                         name="System R&M $/Stand/Day", mode="lines+markers",
                         line=dict(color=AMBER, width=2), marker=dict(size=5),
                         yaxis="y2")
        if has_util_day_ov:
            fig3.add_scatter(x=ov_labels, y=ov_util_day,
                             name=f"{overlay_label} Util $/Std/Day", mode="lines+markers",
                             line=dict(color=BLUE, width=2, dash="dot"),
                             marker=dict(size=7, symbol="diamond"))
        if has_rm_day_ov:
            fig3.add_scatter(x=ov_labels, y=ov_rm_day,
                             name=f"{overlay_label} R&M $/Std/Day", mode="lines+markers",
                             line=dict(color=AMBER, width=2, dash="dot"),
                             marker=dict(size=7, symbol="diamond"), yaxis="y2")
        fig3.update_layout(
            yaxis=dict(title="Utility $/Stand/Day", tickprefix="$"),
            yaxis2=dict(title="R&M $/Stand/Day", overlaying="y", side="right",
                        tickprefix="$", tickfont=dict(size=9, color=AMBER)),
        )
        brew_fig(fig3, height=350)
        fig3.update_layout(
            title_text=f"UTILITY & R&M $/STAND/DAY{title_sfx}",
            xaxis=dict(tickangle=-35),
        )
        st.plotly_chart(fig3, config={"displayModeBar": False})
        st.html("""
        <div class="info-box">
          <strong>💡 Why $/Stand/Day?</strong>
          All 7BREW periods are exactly 28 days, so this metric removes two confounders from % of Sales:
          (1) <strong>Network growth</strong> — as you open more stands, total utility $ climbs even if
          per-stand efficiency is flat. (2) <strong>Sales volume swings</strong> — in a slow period,
          utility % of sales rises even if the actual electricity bill didn't change.
          Divergence between % of Sales and $/Stand/Day is where your real cost story lives.
        </div>""")

    st.html('<hr class="brew">')

    # ── SECTION 2: Region Summary Table ──────────────────────────────────────
    section("REGION SUMMARY", f"Utility & R&M breakdown by region · {sel_lbl}")

    if period_stands.empty:
        st.info("No stand data available for this period.")
    else:
        agg_dict = {"Net_Sales": "sum"}
        for col in ["Total_Utilities", "Total_RM", "Electricity", "Water_Sewer",
                    "Waste_Removal", "RM_Equipment", "RM_Building"]:
            if col in period_stands.columns:
                agg_dict[col] = "sum"

        reg_agg = period_stands.groupby("Region").agg(agg_dict).reset_index()
        stand_counts = period_stands.groupby("Region")["Stand"].nunique().rename("Stands")
        reg_agg = reg_agg.merge(stand_counts, on="Region")
        reg_agg = reg_agg[reg_agg["Net_Sales"] > 0].copy()

        tbl_rows = []
        for _, row in reg_agg.iterrows():
            s    = row["Net_Sales"]
            n    = int(row["Stands"])
            r    = {"Region": row["Region"], "Stands": n}
            # % of sales columns
            for col, lbl in [("Total_Utilities", "Util %"), ("Electricity", "Elec %"),
                              ("Water_Sewer", "Water %"), ("Waste_Removal", "Waste %"),
                              ("RM_Equipment", "R&M Eq %"), ("RM_Building", "R&M Bldg %"),
                              ("Total_RM", "R&M %")]:
                if col in row.index and pd.notna(row[col]) and row[col] > 0:
                    r[lbl] = round(row[col] / s * 100, 2)
            # $/stand/day columns (28-day periods)
            if "Total_Utilities" in row.index and pd.notna(row["Total_Utilities"]) and row["Total_Utilities"] > 0:
                r["Util $/Std/Day"] = round(row["Total_Utilities"] / (n * PERIOD_DAYS), 2)
            if "Total_RM" in row.index and pd.notna(row["Total_RM"]) and row["Total_RM"] > 0:
                r["R&M $/Std/Day"] = round(row["Total_RM"] / (n * PERIOD_DAYS), 2)
            tbl_rows.append(r)

        reg_tbl  = pd.DataFrame(tbl_rows).fillna(0)
        pct_cols = [c for c in reg_tbl.columns if c.endswith("%")]
        day_cols = [c for c in reg_tbl.columns if "$/Std/Day" in c]
        sort_col = "Util %" if "Util %" in pct_cols else ("R&M %" if "R&M %" in pct_cols else "Region")
        if sort_col != "Region":
            reg_tbl = reg_tbl.sort_values(sort_col, ascending=False)
        reg_tbl = reg_tbl.reset_index(drop=True)

        def _util_color(v):
            try:
                f = float(v)
            except Exception:
                return ""
            if f > 4.0: return "background-color:#ffd5d5"
            if f > 3.0: return "background-color:#fff3cd"
            if f > 0:   return "background-color:#d4edda"
            return ""

        def _rm_color(v):
            try:
                f = float(v)
            except Exception:
                return ""
            if f > 1.5: return "background-color:#ffd5d5"
            if f > 1.0: return "background-color:#fff3cd"
            if f > 0:   return "background-color:#d4edda"
            return ""

        fmt = {c: "{:.2f}%" for c in pct_cols}
        fmt.update({c: "${:.2f}" for c in day_cols})

        if pct_cols or day_cols:
            styled = reg_tbl.style.format(fmt)
            for col in pct_cols:
                fn = _rm_color if "R&M" in col else _util_color
                styled = styled.map(fn, subset=[col])
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            render_table(reg_tbl)

    st.html('<hr class="brew">')

    # ── SECTION 3: Stand Detail Drill-Down ───────────────────────────────────
    if sel_stand != "All Stands":
        drill_title  = sel_stand
        drill_stands = period_stands[period_stands["Stand"] == sel_stand].copy()
    elif sel_region != "All Regions":
        drill_title  = sel_region
        drill_stands = period_stands[period_stands["Region"] == sel_region].copy()
    else:
        drill_title  = "All Regions"
        drill_stands = period_stands.copy()

    section("STAND DETAIL", f"Ranked by cost · {sel_lbl} · {drill_title}")

    if drill_stands.empty:
        st.info("No stand data for this selection.")
    elif has_detail:
        ds = drill_stands[drill_stands["Net_Sales"] > 0].copy()
        sys_util_avg = (
            period_stands["Total_Utilities"].sum() / period_stands["Net_Sales"].sum() * 100
            if period_stands["Net_Sales"].sum() > 0 else 0
        )
        sys_rm_avg = (
            period_stands["Total_RM"].sum() / period_stands["Net_Sales"].sum() * 100
            if period_stands["Net_Sales"].sum() > 0 else 0
        )

        # Utilities ranked bar
        if ds["Total_Utilities"].sum() > 0:
            ds["util_pct_val"] = ds["Total_Utilities"] / ds["Net_Sales"] * 100
            ds_u = ds.sort_values("util_pct_val", ascending=True)
            colors_u = [
                RED if v > sys_util_avg * 1.2 else (AMBER if v > sys_util_avg else GREEN)
                for v in ds_u["util_pct_val"]
            ]
            fig_u = go.Figure()
            fig_u.add_bar(
                y=ds_u["Stand"], x=ds_u["util_pct_val"], orientation="h",
                marker_color=colors_u,
                text=ds_u["util_pct_val"].map(lambda v: f"{v:.2f}%"),
                textposition="outside", name="Util %",
            )
            if sys_util_avg > 0:
                fig_u.add_vline(x=sys_util_avg, line_dash="dot", line_color=DARK, line_width=1.5,
                                annotation_text=f"Sys Avg {sys_util_avg:.2f}%",
                                annotation_position="top right", annotation_font_size=9)
            brew_fig(fig_u, height=max(320, len(ds_u) * 22 + 80))
            fig_u.update_layout(
                title_text=f"UTILITIES % BY STAND — {drill_title}",
                xaxis=dict(ticksuffix="%", title="Utilities % of Net Sales"),
                yaxis=dict(title=""), showlegend=False,
                margin=dict(t=60, b=40, l=8, r=90),
            )
            st.plotly_chart(fig_u, config={"displayModeBar": False})

        # R&M ranked bar
        if ds["Total_RM"].sum() > 0:
            ds["rm_pct_val"] = ds["Total_RM"] / ds["Net_Sales"] * 100
            ds_r = ds.sort_values("rm_pct_val", ascending=True)
            colors_r = [
                RED if v > sys_rm_avg * 1.2 else (AMBER if v > sys_rm_avg else GREEN)
                for v in ds_r["rm_pct_val"]
            ]
            fig_r = go.Figure()
            fig_r.add_bar(
                y=ds_r["Stand"], x=ds_r["rm_pct_val"], orientation="h",
                marker_color=colors_r,
                text=ds_r["rm_pct_val"].map(lambda v: f"{v:.2f}%"),
                textposition="outside", name="R&M %",
            )
            if sys_rm_avg > 0:
                fig_r.add_vline(x=sys_rm_avg, line_dash="dot", line_color=DARK, line_width=1.5,
                                annotation_text=f"Sys Avg {sys_rm_avg:.2f}%",
                                annotation_position="top right", annotation_font_size=9)
            brew_fig(fig_r, height=max(320, len(ds_r) * 22 + 80))
            fig_r.update_layout(
                title_text=f"R&M % BY STAND — {drill_title}",
                xaxis=dict(ticksuffix="%", title="R&M % of Net Sales"),
                yaxis=dict(title=""), showlegend=False,
                margin=dict(t=60, b=40, l=8, r=90),
            )
            st.plotly_chart(fig_r, config={"displayModeBar": False})

        # Single-stand KPI breakdown
        if sel_stand != "All Stands" and not ds.empty:
            stand_row = ds.iloc[0]
            sales = float(stand_row.get("Net_Sales", 0))
            if sales > 0:
                st.html(f'<div style="font-family:Bebas Neue,sans-serif;font-size:16px;letter-spacing:2px;color:#1A1919;margin:12px 0 8px;">COST BREAKDOWN — {sel_stand}</div>')
                items = [
                    (col, lbl) for col, lbl in [
                        ("Electricity", "Electricity"), ("Water_Sewer", "Water & Sewer"),
                        ("Waste_Removal", "Waste Removal"), ("RM_Equipment", "R&M Equipment"),
                        ("RM_Building", "R&M Building"),
                    ]
                    if col in stand_row.index and pd.notna(stand_row[col]) and float(stand_row[col]) > 0
                ]
                if items:
                    met_cols = st.columns(len(items))
                    for i, (col, lbl) in enumerate(items):
                        with met_cols[i]:
                            val = float(stand_row[col])
                            st.metric(lbl, f"${val:,.0f}", f"{val/sales*100:.2f}% of sales")
    else:
        st.caption("Upload P&L files to activate stand-level utility drill-down.")
        if not drill_stands.empty:
            disp = drill_stands[["Stand", "Net_Sales"]].copy()
            disp["Net_Sales"] = disp["Net_Sales"].apply(lambda v: f"${v:,.0f}" if pd.notna(v) else "—")
            render_table(disp.reset_index(drop=True))

    st.html('<hr class="brew">')

    # ── SECTION 4: Trend Analysis ─────────────────────────────────────────────
    trend_label = (sel_stand if sel_stand != "All Stands"
                   else (sel_region if sel_region != "All Regions" else "Company"))
    section("TREND ANALYSIS", f"Utilities & R&M over all periods — {trend_label} vs system average")

    fig_t = go.Figure()
    fig_t.add_scatter(x=pct_df["label"], y=pct_df["utilities_pct"] * 100,
                      name="System Avg Util %", mode="lines+markers",
                      line=dict(color=BLUE, width=2), marker=dict(size=5))
    fig_t.add_scatter(x=pct_df["label"], y=pct_df["rm_pct"] * 100,
                      name="System Avg R&M %", mode="lines+markers",
                      line=dict(color=AMBER, width=2), marker=dict(size=5))
    if has_util_ov:
        fig_t.add_scatter(x=ov_labels, y=ov_util,
                          name=f"{overlay_label} Util %", mode="lines+markers",
                          line=dict(color=RED, width=2, dash="dot"),
                          marker=dict(size=7, symbol="diamond"))
    if has_rm_ov:
        fig_t.add_scatter(x=ov_labels, y=ov_rm,
                          name=f"{overlay_label} R&M %", mode="lines+markers",
                          line=dict(color=MID, width=2, dash="dot"),
                          marker=dict(size=7, symbol="diamond"))
    # Highlight the selected period (annotation separate — add_vline annotation_position
    # fails on categorical string axes in newer Plotly)
    fig_t.add_vline(x=sel_lbl, line_dash="dash", line_color=RED, line_width=1)
    fig_t.add_annotation(x=sel_lbl, y=1, yref="paper", text=sel_lbl,
                          showarrow=False, xanchor="left", yanchor="top",
                          font=dict(size=9, color=RED, family="DM Mono"))
    brew_fig(fig_t, height=380)
    fig_t.update_layout(
        title_text=f"UTILITIES & R&M TREND — {trend_label} vs System Avg",
        yaxis=dict(ticksuffix="%"),
        xaxis=dict(tickangle=-35),
    )
    st.plotly_chart(fig_t, config={"displayModeBar": False})

    st.html('<hr class="brew">')

    # ── SEASONALITY ANALYSIS ──────────────────────────────────────────────────
    section("SEASONALITY ANALYSIS", "How period of year drives utility & R&M costs")

    fig_s1 = go.Figure()
    fig_s1.add_scatter(x=pct_df["label"], y=pct_df["utilities_pct"] * 100,
                       mode="lines+markers+text",
                       text=pct_df["utilities_pct"].map(lambda v: f"{v*100:.1f}%"),
                       textposition="top center", textfont=dict(size=8),
                       fill="tozeroy", fillcolor="rgba(29,111,207,0.08)",
                       line=dict(color=BLUE, width=2),
                       marker=dict(size=6, color=[
                           RED if i in [5, 6, 7] else (AMBER if i in [4, 8] else BLUE)
                           for i in range(len(pct_df))
                       ]), name="Utilities %")
    brew_fig(fig_s1, height=350)
    fig_s1.update_layout(title_text="UTILITIES % BY PERIOD (SEASONALITY)",
                         yaxis=dict(ticksuffix="%"),
                         xaxis=dict(tickangle=-35), showlegend=False)
    summer_idxs = [i for i, lbl in enumerate(pct_df["label"]) if any(x in str(lbl) for x in ["P6", "P7", "P8"])]
    if summer_idxs:
        mid_lbl = pct_df.iloc[summer_idxs[len(summer_idxs) // 2]]["label"]
        fig_s1.add_annotation(x=mid_lbl, y=pct_df["utilities_pct"].max() * 100 * 1.05,
                               text="☀️ Summer Peak", showarrow=False,
                               font=dict(size=9, color=RED, family="DM Mono"))
    st.plotly_chart(fig_s1, config={"displayModeBar": False})

    fig_s2 = go.Figure()
    fig_s2.add_scatter(x=pct_df["label"], y=pct_df["rm_pct"] * 100,
                       mode="lines+markers+text",
                       text=pct_df["rm_pct"].map(lambda v: f"{v*100:.2f}%"),
                       textposition="top center", textfont=dict(size=8),
                       fill="tozeroy", fillcolor="rgba(232,148,10,0.08)",
                       line=dict(color=AMBER, width=2), marker=dict(size=6),
                       name="R&M %")
    x_num  = list(range(len(pct_df)))
    z      = np.polyfit(x_num, pct_df["rm_pct"] * 100, 1)
    p_fit  = np.poly1d(z)
    fig_s2.add_scatter(x=pct_df["label"], y=[p_fit(xi) for xi in x_num],
                       mode="lines", name="Trend",
                       line=dict(color=RED, dash="dot", width=1.5))
    brew_fig(fig_s2, height=350)
    fig_s2.update_layout(title_text="R&M % BY PERIOD (WITH TREND)",
                         yaxis=dict(ticksuffix="%"),
                         xaxis=dict(tickangle=-35))
    st.plotly_chart(fig_s2, config={"displayModeBar": False})

    # ── WASTE REMOVAL CHART ───────────────────────────────────────────────────
    if sub_avail.get("Waste_Removal", False):
        st.html('<hr class="brew">')
        _waste_title_sfx = f" · {overlay_label}" if overlay_label else ""
        section("WASTE REMOVAL", f"Period-over-period cost trend · % of Net Sales{_waste_title_sfx}")

        # Build per-period system-wide waste aggregates
        waste_rows = []
        for _, row in pct_df.iterrows():
            pk_w   = row["period_key"]
            grp_w  = stands_df[stands_df["Period_Key"] == pk_w]
            sales_w = grp_w["Net_Sales"].sum()
            waste_w = grp_w["Waste_Removal"].fillna(0).sum() if "Waste_Removal" in grp_w.columns else 0
            n_w     = max(grp_w["Stand"].nunique(), 1)
            waste_rows.append({
                "label":      row["label"],
                "period_key": pk_w,
                "waste_$":    waste_w,
                "waste_pct":  (waste_w / sales_w * 100) if sales_w > 0 else 0,
                "waste_per_std_day": (waste_w / (n_w * PERIOD_DAYS)) if n_w > 0 else 0,
            })
        waste_df = pd.DataFrame(waste_rows)

        # Build overlay series
        ov_waste_labels, ov_waste_pct = [], []
        for _, row in waste_df.iterrows():
            if row["period_key"] in overlay_waste_map:
                ov_waste_labels.append(row["label"])
                ov_waste_pct.append(overlay_waste_map[row["period_key"]] * 100)

        if waste_df["waste_$"].sum() > 0:
            fig_w = go.Figure()
            fig_w.add_bar(
                x=waste_df["label"], y=waste_df["waste_$"] / 1000,
                name="System Waste ($k)", marker_color="#6c757d", opacity=0.7,
            )
            fig_w.add_scatter(
                x=waste_df["label"], y=waste_df["waste_pct"],
                name="System Waste %", mode="lines+markers+text",
                text=waste_df["waste_pct"].map(lambda v: f"{v:.2f}%"),
                textposition="top center", textfont=dict(size=8),
                line=dict(color=RED, width=2), marker=dict(size=6),
                yaxis="y2",
            )
            if ov_waste_labels:
                fig_w.add_scatter(
                    x=ov_waste_labels, y=ov_waste_pct,
                    name=f"{overlay_label} Waste %", mode="lines+markers",
                    line=dict(color=AMBER, width=2, dash="dot"),
                    marker=dict(size=7, symbol="diamond"),
                    yaxis="y2",
                )
            fig_w.update_layout(
                yaxis=dict(title="Waste Removal ($k)", tickprefix="$", ticksuffix="k"),
                yaxis2=dict(title="% of Net Sales", overlaying="y", side="right",
                            ticksuffix="%", tickfont=dict(size=9, color=RED)),
            )
            brew_fig(fig_w, height=350)
            fig_w.update_layout(
                title_text=f"WASTE REMOVAL — PERIOD OVER PERIOD{_waste_title_sfx}",
                xaxis=dict(tickangle=-35),
            )
            st.plotly_chart(fig_w, config={"displayModeBar": False})

            # Spike detector — flag any period > 1.5× median
            waste_median = waste_df["waste_$"].median()
            spikes = waste_df[waste_df["waste_$"] > waste_median * 1.5]
            if not spikes.empty:
                spike_lbls = ", ".join(spikes["label"].tolist())
                st.html(
                    f'<div style="background:rgba(172,36,48,0.07);border-left:4px solid #AC2430;'
                    f'border-radius:6px;padding:8px 14px;font-family:DM Mono,monospace;font-size:13px;'
                    f'color:#595959;margin-bottom:8px;">'
                    f'⚠ <strong>Waste Spike Detected:</strong> {spike_lbls} ran >1.5× median '
                    f'(${waste_median:,.0f}). Likely extra pickup cycle or overage fee — verify invoice.'
                    f'</div>'
                )

    # ── LANDSCAPING CHART ─────────────────────────────────────────────────────
    if sub_avail.get("Landscaping", False):
        st.html('<hr class="brew">')
        _land_title_sfx = f" · {overlay_label}" if overlay_label else ""
        section("LANDSCAPING", f"Period-over-period cost trend · % of Net Sales · under Total R&M{_land_title_sfx}")

        land_rows = []
        for _, row in pct_df.iterrows():
            pk_l    = row["period_key"]
            grp_l   = stands_df[stands_df["Period_Key"] == pk_l]
            sales_l = grp_l["Net_Sales"].sum()
            land_l  = grp_l["Landscaping"].fillna(0).sum()
            n_l     = max(grp_l["Stand"].nunique(), 1)
            land_rows.append({
                "label":      row["label"],
                "period_key": pk_l,
                "land_$":     land_l,
                "land_pct":   (land_l / sales_l * 100) if sales_l > 0 else 0,
                "land_per_std_day": (land_l / (n_l * PERIOD_DAYS)) if n_l > 0 else 0,
            })
        land_df = pd.DataFrame(land_rows)

        # Build overlay series
        ov_land_labels, ov_land_pct = [], []
        for _, row in land_df.iterrows():
            if row["period_key"] in overlay_land_map:
                ov_land_labels.append(row["label"])
                ov_land_pct.append(overlay_land_map[row["period_key"]] * 100)

        if land_df["land_$"].sum() > 0:
            fig_l = go.Figure()
            fig_l.add_bar(
                x=land_df["label"], y=land_df["land_$"] / 1000,
                name="System Landscaping ($k)", marker_color="#2e7d32", opacity=0.7,
            )
            fig_l.add_scatter(
                x=land_df["label"], y=land_df["land_pct"],
                name="System Landscaping %", mode="lines+markers+text",
                text=land_df["land_pct"].map(lambda v: f"{v:.2f}%"),
                textposition="top center", textfont=dict(size=8),
                line=dict(color=GREEN, width=2), marker=dict(size=6),
                yaxis="y2",
            )
            if ov_land_labels:
                fig_l.add_scatter(
                    x=ov_land_labels, y=ov_land_pct,
                    name=f"{overlay_label} Landscaping %", mode="lines+markers",
                    line=dict(color=AMBER, width=2, dash="dot"),
                    marker=dict(size=7, symbol="diamond"),
                    yaxis="y2",
                )
            fig_l.update_layout(
                yaxis=dict(title="Landscaping ($k)", tickprefix="$", ticksuffix="k"),
                yaxis2=dict(title="% of Net Sales", overlaying="y", side="right",
                            ticksuffix="%", tickfont=dict(size=9, color=GREEN)),
            )
            brew_fig(fig_l, height=350)
            fig_l.update_layout(
                title_text=f"LANDSCAPING — PERIOD OVER PERIOD{_land_title_sfx}",
                xaxis=dict(tickangle=-35),
            )
            st.plotly_chart(fig_l, config={"displayModeBar": False})

            # Seasonal spike alert
            land_median = land_df["land_$"].median()
            spikes_l = land_df[land_df["land_$"] > land_median * 1.75]
            if not spikes_l.empty:
                spike_lbls_l = ", ".join(spikes_l["label"].tolist())
                st.html(
                    f'<div style="background:rgba(18,160,110,0.07);border-left:4px solid #12a06e;'
                    f'border-radius:6px;padding:8px 14px;font-family:DM Mono,monospace;font-size:13px;'
                    f'color:#595959;margin-bottom:8px;">'
                    f'🌿 <strong>Seasonal Spike:</strong> {spike_lbls_l} ran >1.75× median '
                    f'(${land_median:,.0f}). Typical for spring/summer mowing & trimming cycles — '
                    f'verify against contract schedule.'
                    f'</div>'
                )

    # ── OPPORTUNITY FLAGS ─────────────────────────────────────────────────────
    st.html('<hr class="brew">')
    section("OPPORTUNITY FLAGS", "Data-driven cost reduction opportunities")

    top_util     = pct_df.nlargest(3, "utilities_pct")
    low_util     = pct_df.nsmallest(1, "utilities_pct").iloc[0]
    rm_trend_val = pct_df["rm_pct"].iloc[-3:].mean() - pct_df["rm_pct"].iloc[:3].mean()
    has_waste    = sub_avail.get("Waste_Removal", False)

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
            "Utility costs fluctuate with the number of days in a period. Normalize utility expense "
            "to $/day/stand rather than % of sales for a cleaner comparison. A spike in Waste Removal "
            "% could be an overage charge, not increased volume.",
            tag="Measurement Tip", tag_cls="grey", card_cls="watch",
        )
    with opp_col2:
        rm_dir = "increasing" if rm_trend_val > 0 else "decreasing"
        insight_card(
            f"🔧 R&M Trend: {rm_dir.title()} Over the Dataset",
            f"R&M % has {'risen' if rm_trend_val > 0 else 'fallen'} by {abs(rm_trend_val)*100:.2f}% pts "
            f"from early to recent periods. "
            f"{'This aligns with the aging equipment cycle for stands opened 2022–2023. Schedule preventive maintenance in P9–P11 before it becomes reactive.' if rm_trend_val > 0 else 'Positive trend — newer stands have lower R&M. Monitor as the network ages.'}",
            tag=f"Δ {'+' if rm_trend_val > 0 else ''}{rm_trend_val*100:.2f}% pts",
            tag_cls="amber" if rm_trend_val > 0 else "green",
            card_cls="watch" if rm_trend_val > 0 else "win",
        )
        insight_card(
            "🗑 Waste Removal: 2–3x Pickup Schedule",
            "Waste Removal is typically charged per pickup (2–3x/week). If a period contains an extra pickup "
            "cycle due to calendar length or overage fees, the cost will spike. Flag any period where Waste "
            "Removal exceeds 1.5× the median value — this indicates an overage charge rather than normal operations.",
            tag="Spike Detector Active" if has_waste else "Upload P&L to Activate",
            tag_cls="green" if has_waste else "grey",
            card_cls="win" if has_waste else "watch",
        )

    # ── 🔩 R&M vs Stand Age ──────────────────────────────────────────────────
    st.html('<hr class="brew">')
    section("🔩 R&M vs STAND AGE",
            "Identifies whether maintenance costs cluster at predictable age milestones — "
            "a spike at 18–24 months often signals warranty expiry on equipment")

    rm_df = get_stands_df(dash).copy()
    # Compute numeric stand age in years from Open Date + Period_Key
    rm_df["age_yrs"] = rm_df.apply(
        lambda r: _age_yrs_from_period(r.get("Open Date", ""), r.get("Period_Key", "")), axis=1
    )
    rm_df = rm_df[rm_df["Total_RM"].notna() & rm_df["age_yrs"].notna()
                  & (rm_df["Net_Sales"].fillna(0) > 0)].copy()
    rm_df["RM_pct_display"] = rm_df["Total_RM_pct"].fillna(
        rm_df["Total_RM"] / rm_df["Net_Sales"])

    # ── KPI strip ────────────────────────────────────────────────────────────
    ra1, ra2, ra3, ra4 = st.columns(4)
    bucket_rm = (rm_df.groupby("Age_Bucket")["RM_pct_display"]
                 .mean().reindex(["New (<6mo)","Young (6-12mo)","Developing (1-2yr)","Mature (2yr+)"]))

    new_rm      = bucket_rm.get("New (<6mo)", 0) or 0
    young_rm    = bucket_rm.get("Young (6-12mo)", 0) or 0
    dev_rm      = bucket_rm.get("Developing (1-2yr)", 0) or 0
    mature_rm   = bucket_rm.get("Mature (2yr+)", 0) or 0

    warranty_cliff = dev_rm - young_rm   # positive = R&M rose in 1-2yr bracket

    ra1.metric("Avg R&M% — New Stands",   f"{new_rm*100:.2f}%",   help="<6 months open")
    ra2.metric("Avg R&M% — Young Stands", f"{young_rm*100:.2f}%", help="6-12 months open")
    ra3.metric("Avg R&M% — Developing",   f"{dev_rm*100:.2f}%",
               delta=f"{warranty_cliff*100:+.2f}% vs young",
               delta_color="inverse" if warranty_cliff > 0 else "normal",
               help="1-2 years open — warranty expiry zone")
    ra4.metric("Avg R&M% — Mature",       f"{mature_rm*100:.2f}%", help="2+ years open")

    if warranty_cliff > 0.002:
        st.warning(f"⚠️ R&M% rises {warranty_cliff*100:.2f}pp from Young → Developing stands — consistent with equipment warranty expiry around the 12–24 month mark. Consider a preventive maintenance program at the 12-month mark.")
    else:
        st.success("✅ R&M% is stable across age cohorts — no evidence of a warranty-cliff pattern.")

    # ── Scatter: Age vs R&M% ──────────────────────────────────────────────────
    sc1, sc2 = st.columns([3, 2])

    with sc1:
        st.markdown("**R&M% vs Stand Age — All Stand-Period Records**")
        # Use the most recent record per stand for the scatter to avoid overplotting
        latest_rm = rm_df.sort_values("Period_Key").groupby("Stand").last().reset_index()
        fig_scatter = px.scatter(
            latest_rm.dropna(subset=["age_yrs", "RM_pct_display", "Region"]),
            x="age_yrs", y="RM_pct_display",
            color="Region",
            hover_data={"Stand": True, "Total_RM": ":$,.0f",
                        "Net_Sales": ":$,.0f", "age_yrs": ":.2f"},
            labels={"age_yrs": "Stand Age (Years)",
                    "RM_pct_display": "R&M % of Net Sales",
                    "Region": "Region"},
            color_discrete_map={k: v for k, v in {
                "North Central TX":"#1d6fcf","South Central TX":"#2980b9",
                "FL Panhandle East":"#12a06e","FL Panhandle West":"#1a8c5c",
                "FL West Coast":"#0e7a6e","Middle Earth":"#7c3aed",
                "West TX":"#e8940a","Permian Basin":"#d4600a",
                "Central OK":"#AC2430","North OK":"#c0392b","South OK":"#922b21",
            }.items()},
        )
        # Highlight 1–2 year zone
        fig_scatter.add_vrect(x0=1.0, x1=2.0,
                              fillcolor="rgba(255,200,0,0.08)", line_width=0,
                              annotation_text="Warranty zone (1-2yr)",
                              annotation_position="top left",
                              annotation_font_color="rgba(255,200,0,0.7)")
        fig_scatter.update_layout(
            template="plotly_dark", height=340,
            margin=dict(t=20,b=40,l=0,r=0),
            yaxis_tickformat=".1%",
            legend=dict(orientation="v", x=1.01, y=1),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with sc2:
        st.markdown("**Avg R&M% by Age Cohort**")
        bucket_order_rm = ["New (<6mo)", "Young (6-12mo)", "Developing (1-2yr)", "Mature (2yr+)"]
        bucket_colors_rm = {"New (<6mo)": "#FF6B00", "Young (6-12mo)": "#F5A623",
                            "Developing (1-2yr)": "#4A90E2", "Mature (2yr+)": "#12a06e"}
        fig_bar_rm = go.Figure()
        for bkt in bucket_order_rm:
            val = bucket_rm.get(bkt, 0) or 0
            fig_bar_rm.add_bar(
                x=[bkt.split(" (")[0]], y=[val * 100],
                name=bkt, marker_color=bucket_colors_rm.get(bkt, "#999"),
                text=[f"{val*100:.2f}%"], textposition="outside",
                showlegend=False,
            )
        fig_bar_rm.update_layout(
            template="plotly_dark", height=340,
            margin=dict(t=20,b=60,l=0,r=0),
            yaxis_title="Avg R&M % of Sales",
            xaxis_tickangle=-20, bargap=0.35,
        )
        st.plotly_chart(fig_bar_rm, use_container_width=True)

    st.caption(
        "Scatter uses each stand's most recent period. A cluster of high-R&M points in the 1–2 year zone "
        "suggests equipment warranty expiry is driving cost. Outliers above 3% in any cohort warrant investigation."
    )


# ─────────────────────────────────────────────
# PIPELINE TAB
# ─────────────────────────────────────────────

# City-level coordinates for map rendering
_CITY_COORDS = {
    # Texas
    ("Lubbock","TX"):(33.5779,-101.8552),("Odessa","TX"):(31.8457,-102.3676),
    ("Midland","TX"):(31.9973,-102.0779),("Amarillo","TX"):(35.2220,-101.8313),
    ("Big Spring","TX"):(32.2504,-101.4788),("Wichita Falls","TX"):(33.9137,-98.4934),
    ("San Angelo","TX"):(31.4638,-100.4370),("Abilene","TX"):(32.4487,-99.7331),
    ("Brownwood","TX"):(31.7093,-98.9912),("Gainesville","TX"):(33.6262,-97.1333),
    ("Dumas","TX"):(35.8659,-101.9746),("Levelland","TX"):(33.5874,-102.3779),
    ("Plainview","TX"):(34.1845,-101.7068),("Andrews","TX"):(32.3182,-102.5449),
    ("Pampa","TX"):(35.5362,-100.9601),("Canyon","TX"):(34.9801,-101.9183),
    ("Snyder","TX"):(32.7179,-100.9181),("Granbury","TX"):(32.4418,-97.7939),
    ("Burleson","TX"):(32.5418,-97.3208),("Beverly Hills","TX"):(31.5556,-97.1303),
    ("Waco","TX"):(31.5493,-97.1467),("Killeen","TX"):(31.1171,-97.7278),
    ("Belton","TX"):(31.0557,-97.4641),("Temple","TX"):(31.0982,-97.3428),
    ("Bryan","TX"):(30.6744,-96.3698),("Stephenville","TX"):(32.2207,-98.2023),
    ("Gatesville","TX"):(31.4360,-97.7436),("Copperas Cove","TX"):(31.1218,-97.9081),
    ("Mineral Wells","TX"):(32.8087,-98.1120),("Decatur","TX"):(33.2348,-97.5839),
    ("Benbrook","TX"):(32.6815,-97.4625),("Cleburne","TX"):(32.3501,-97.3861),
    ("Springtown","TX"):(32.9612,-97.6834),("Weatherford","TX"):(32.7588,-97.7975),
    ("Garland","TX"):(32.9126,-96.6389),("Mesquite","TX"):(32.7668,-96.5992),
    ("Dallas","TX"):(32.7767,-96.7970),("Bellmead","TX"):(31.5854,-97.1000),
    # Oklahoma
    ("Oklahoma City","OK"):(35.4676,-97.5164),("Yukon","OK"):(35.5067,-97.7625),
    ("Norman","OK"):(35.2226,-97.4395),("Edmond","OK"):(35.6528,-97.4781),
    ("Enid","OK"):(36.3956,-97.8784),("Lawton","OK"):(34.6084,-98.3909),
    ("Ardmore","OK"):(34.1743,-97.1436),("Ada","OK"):(34.7745,-96.6781),
    ("Duncan","OK"):(34.5023,-97.9578),("Weatherford","OK"):(35.5268,-98.7076),
    ("Altus","OK"):(34.6381,-99.3337),("El Reno","OK"):(35.5323,-97.9553),
    ("Mustang","OK"):(35.3840,-97.7242),("Choctaw","OK"):(35.4973,-97.2703),
    # New Mexico
    ("Roswell","NM"):(33.3943,-104.5230),("Hobbs","NM"):(32.7026,-103.1360),
    ("Clovis","NM"):(34.4048,-103.2052),("Carlsbad","NM"):(32.4207,-104.2288),
    ("Artesia","NM"):(32.8415,-104.4032),
    # Colorado
    ("Alamosa","CO"):(37.4695,-105.8700),("Montrose","CO"):(38.4783,-107.8762),
    # Florida - West Coast / Central
    ("Bradenton","FL"):(27.4989,-82.5748),("Leesburg","FL"):(28.8114,-81.8779),
    ("Tampa","FL"):(27.9506,-82.4572),("Port Charlotte","FL"):(26.9756,-82.0906),
    ("Belleview","FL"):(29.0563,-82.0609),("Spring Hill","FL"):(28.4788,-82.5143),
    ("Holiday","FL"):(28.1908,-82.7368),("Ocala","FL"):(29.1872,-82.1401),
    ("North Port","FL"):(27.0442,-82.1360),("Port Richey","FL"):(28.2703,-82.7196),
    ("Fort Myers","FL"):(26.6406,-81.8723),("Winter Haven","FL"):(28.0222,-81.7329),
    ("Palmetto","FL"):(27.5231,-82.5768),("Haines City","FL"):(28.1136,-81.6270),
    ("Mulberry","FL"):(27.8939,-81.9829),("Largo","FL"):(27.9095,-82.7873),
    ("Brooksville","FL"):(28.5553,-82.3882),("Punta Gorda","FL"):(26.9342,-82.0457),
    ("Lehigh Acres","FL"):(26.6117,-81.6484),("Seminole","FL"):(27.8409,-82.7876),
    ("Cape Coral","FL"):(26.5629,-81.9495),("Davenport","FL"):(28.1611,-81.6015),
    ("Hudson","FL"):(28.3625,-82.6962),("St. Petersburg","FL"):(27.7676,-82.6403),
    ("Arcadia","FL"):(27.2170,-81.8587),("Sebring","FL"):(27.4975,-81.4509),
    ("Belton","FL"):(27.3156,-81.4370),
    # Florida - Panhandle West
    ("Pensacola","FL"):(30.4213,-87.2169),("Gulf Breeze","FL"):(30.3574,-87.1637),
    ("Milton","FL"):(30.6327,-87.0397),("Pace","FL"):(30.5985,-87.1614),
    ("Mary Esther","FL"):(30.4124,-86.6650),
    # Florida - Panhandle East
    ("Crestview","FL"):(30.7460,-86.5703),("Niceville","FL"):(30.5188,-86.4780),
    ("Fort Walton Beach","FL"):(30.4052,-86.6194),("Navarre","FL"):(30.4017,-86.8636),
    ("Panama City","FL"):(30.1588,-85.6602),("Lynn Haven","FL"):(30.2466,-85.6483),
    ("Panama City Beach","FL"):(30.1766,-85.8055),("Freeport","FL"):(30.5001,-86.1333),
    ("Destin","FL"):(30.3935,-86.4958),("Gainesville","FL"): (29.6516,-82.3248),
}

# Pipeline: phases 2–5 (upcoming openings). Source: Drew Deagan weekly report, Mar 26 2026.
# Regions mapped from spreadsheet abbreviations to full names used throughout the dashboard.
_PIPELINE_UPCOMING = [
    # ── Phase 5: Construction ──────────────────────────────────────────────────
    # RSH-00075 Cleburne TX and RSH-00066 Pampa TX opened 03/30/26 → moved to _PIPELINE_OPEN_PDF
    {"rsh":"RSH-00068","store":"000711","phase":"5. Construction","address":"1540 N Valley Mills Drive","city":"Waco","state":"TX","region":"South Central TX","cs":"11/03/25","bd":"12/03/25","open":"04/13/26"},
    {"rsh":"RSH-00082","store":"000987","phase":"5. Construction","address":"3617 Classen Blvd","city":"Norman","state":"OK","region":"Central OK","cs":"12/01/25","bd":"03/04/26","open":"04/13/26"},
    {"rsh":"RSH-00097","store":"000878","phase":"5. Construction","address":"2105 MLK Blvd","city":"Panama City","state":"FL","region":"FL Panhandle East","cs":"11/19/25","bd":"03/06/26","open":"04/20/26"},
    {"rsh":"RSH-00096","store":"000968","phase":"5. Construction","address":"6518 NW Cache Road","city":"Lawton","state":"OK","region":"South OK","cs":"02/02/26","bd":"03/19/26","open":"05/18/26"},
    {"rsh":"RSH-00091","store":"001122","phase":"5. Construction","address":"3008 W Stan Schlueter Loop","city":"Killeen","state":"TX","region":"South Central TX","cs":"02/18/26","bd":"03/27/26","open":"05/18/26"},
    {"rsh":"RSH-00101","store":"001238","phase":"5. Construction","address":"1707 S Valley Mills Dr","city":"Beverly Hills","state":"TX","region":"South Central TX","cs":"02/23/26","bd":"04/01/26","open":"05/18/26"},
    {"rsh":"RSH-00081","store":"000986","phase":"5. Construction","address":"490 Mary Esther Blvd","city":"Mary Esther","state":"FL","region":"FL Panhandle East","cs":"01/26/26","bd":"02/26/26","open":"06/01/26"},
    {"rsh":"RSH-00095","store":"000518","phase":"5. Construction","address":"1420 Ohio Avenue","city":"Lynn Haven","state":"FL","region":"FL Panhandle East","cs":"01/22/26","bd":"02/18/26","open":"06/01/26"},
    {"rsh":"RSH-00109","store":"001234","phase":"5. Construction","address":"2415 S Country Club Rd","city":"El Reno","state":"OK","region":"North OK","cs":"02/23/26","bd":"04/08/26","open":"06/08/26"},
    {"rsh":"RSH-00071","store":"000520","phase":"5. Construction","address":"1194 Broad St","city":"Brooksville","state":"FL","region":"FL West Coast","cs":"01/12/26","bd":"03/11/26","open":"06/08/26"},
    {"rsh":"RSH-00079","store":"000547","phase":"5. Construction","address":"833 W. Edmond Rd","city":"Edmond","state":"OK","region":"North OK","cs":"02/16/26","bd":"03/17/26","open":"06/15/26"},
    {"rsh":"RSH-00069","store":"000571","phase":"5. Construction","address":"801 Beal Pkwy N","city":"Fort Walton Beach","state":"FL","region":"FL Panhandle East","cs":"12/17/25","bd":"03/04/26","open":"06/22/26"},
    {"rsh":"RSH-00116","store":"001119","phase":"5. Construction","address":"210 23rd St","city":"Canyon","state":"TX","region":"West TX","cs":"03/02/26","bd":"04/16/26","open":"06/22/26"},
    {"rsh":"RSH-00078","store":"000674","phase":"5. Construction","address":"1937 US 19 Hwy","city":"Holiday","state":"FL","region":"FL West Coast","cs":"03/25/26","bd":"04/22/26","open":"08/10/26"},
    {"rsh":"RSH-00089","store":"000327","phase":"5. Construction","address":"401 Gulf Breeze Pkwy","city":"Gulf Breeze","state":"FL","region":"FL Panhandle West","cs":"01/05/26","bd":"Stick Build","open":"08/10/26"},
    # ── Phase 4: Permitting ────────────────────────────────────────────────────
    {"rsh":"RSH-00106","store":"001236","phase":"4. Permitting","address":"12902 Indiana Ave","city":"Lubbock","state":"TX","region":"West TX","cs":"04/06/26","bd":"05/13/26","open":"07/27/26"},
    {"rsh":"RSH-00123","store":"001332","phase":"4. Permitting","address":"108 Sequoyah Ln","city":"Altus","state":"OK","region":"South OK","cs":"04/13/26","bd":"05/13/26","open":"08/03/26"},
    {"rsh":"RSH-00102","store":"001118","phase":"4. Permitting","address":"3700 College Ave","city":"Snyder","state":"TX","region":"Middle Earth","cs":"04/13/26","bd":"Stick Build","open":"08/10/26"},
    {"rsh":"RSH-00114","store":"001154","phase":"4. Permitting","address":"8106 N Davis Hwy","city":"Pensacola","state":"FL","region":"FL Panhandle West","cs":"04/06/26","bd":"05/06/26","open":"08/10/26"},
    {"rsh":"RSH-00110","store":"001156","phase":"4. Permitting","address":"955 US-377","city":"Granbury","state":"TX","region":"North Central TX","cs":"04/13/26","bd":"05/20/26","open":"08/10/26"},
    {"rsh":"RSH-00133","store":"001333","phase":"4. Permitting","address":"2917 SW 104th St","city":"Oklahoma City","state":"OK","region":"North OK","cs":"04/20/26","bd":"05/27/26","open":"08/10/26"},
    {"rsh":"RSH-00092","store":"000428","phase":"4. Permitting","address":"9101 College Pkwy","city":"Fort Myers","state":"FL","region":"FL West Coast","cs":"04/06/26","bd":"05/06/26","open":"08/17/26"},
    {"rsh":"RSH-00084","store":"000380","phase":"4. Permitting","address":"1225 Tamiami Trail","city":"Punta Gorda","state":"FL","region":"FL West Coast","cs":"04/27/26","bd":"05/27/26","open":"09/28/26"},
    {"rsh":"RSH-00087","store":"000883","phase":"4. Permitting","address":"1603 3rd St","city":"Winter Haven","state":"FL","region":"FL West Coast","cs":"04/16/26","bd":"05/20/26","open":"09/14/26"},
    {"rsh":"RSH-00094","store":"000757","phase":"4. Permitting","address":"4102 Cleveland Ave","city":"Fort Myers","state":"FL","region":"FL West Coast","cs":"04/13/26","bd":"05/20/26","open":"09/28/26"},
    {"rsh":"RSH-00088","store":"000404","phase":"4. Permitting","address":"1201 Homestead Rd N","city":"Lehigh Acres","state":"FL","region":"FL West Coast","cs":"05/06/26","bd":"06/03/26","open":"10/19/26"},
    {"rsh":"RSH-00086","store":"000414","phase":"4. Permitting","address":"3100 SW College Rd","city":"Ocala","state":"FL","region":"FL West Coast","cs":"05/25/26","bd":"07/08/26","open":"11/02/26"},
    {"rsh":"RSH-00229","store":"001344","phase":"4. Permitting","address":"4615 Mobile Hwy","city":"Pensacola","state":"FL","region":"FL Panhandle West","cs":"06/15/26","bd":"07/22/26","open":"11/02/26"},
    {"rsh":"RSH-00139","store":"001383","phase":"4. Permitting","address":"1811 24th Ave NW","city":"Norman","state":"OK","region":"Central OK","cs":"07/06/26","bd":"08/05/26","open":"11/02/26"},
    {"rsh":"RSH-00083","store":"000874","phase":"4. Permitting","address":"7236 Northwest Expy","city":"Oklahoma City","state":"OK","region":"North OK","cs":"07/27/26","bd":"09/09/26","open":"11/09/26"},
    {"rsh":"RSH-00113","store":"001120","phase":"4. Permitting","address":"1289 S Sumter Blvd","city":"North Port","state":"FL","region":"FL West Coast","cs":"08/24/26","bd":"09/23/26","open":"12/07/26"},
    {"rsh":"RSH-00100","store":"000966","phase":"4. Permitting","address":"3001 W University Blvd","city":"Odessa","state":"TX","region":"Permian Basin","cs":"08/31/26","bd":"09/30/26","open":"01/18/27"},
    {"rsh":"RSH-00077","store":"000607","phase":"4. Permitting","address":"160 Mariner Blvd","city":"Spring Hill","state":"FL","region":"FL West Coast","cs":"09/21/26","bd":"10/21/26","open":"02/22/27"},
    {"rsh":"RSH-00117","store":"000967","phase":"4. Permitting","address":"9305 US-19","city":"Port Richey","state":"FL","region":"FL West Coast","cs":"09/14/26","bd":"10/14/26","open":"02/22/27"},
    {"rsh":"RSH-00146","store":"001368","phase":"4. Permitting","address":"7725 Moccasin Wallow Road","city":"Palmetto","state":"FL","region":"FL West Coast","cs":"09/28/26","bd":"09/09/26","open":"03/01/27"},
    {"rsh":"RSH-00231","store":"001323","phase":"4. Permitting","address":"19017 S Tamiami Trl","city":"Fort Myers","state":"FL","region":"FL West Coast","cs":"11/30/26","bd":"01/13/27","open":"05/03/27"},
    # ── Phase 3: Design ────────────────────────────────────────────────────────
    {"rsh":"RSH-00112","store":"001241","phase":"4. Permitting","address":"100 S New Rd","city":"Waco","state":"TX","region":"South Central TX","cs":"06/22/26","bd":"07/15/26","open":"10/05/26"},
    {"rsh":"RSH-00134","store":"001686","phase":"4. Permitting","address":"855 NE Alsbury Blvd","city":"Burleson","state":"TX","region":"South Central TX","cs":"07/20/26","bd":"08/26/26","open":"11/09/26"},
    {"rsh":"RSH-00103","store":"001713","phase":"3. Design","address":"736 Hewitt Dr","city":"Waco","state":"TX","region":"South Central TX","cs":"08/10/26","bd":"Retrofit","open":"11/30/26"},
    {"rsh":"RSH-00149","store":"001673","phase":"3. Design","address":"1020 E State Hwy 152","city":"Mustang","state":"OK","region":"Central OK","cs":"09/07/26","bd":"10/07/26","open":"01/04/27"},
    {"rsh":"RSH-00129","store":"001714","phase":"3. Design","address":"4227 East US Hwy 377","city":"Granbury","state":"TX","region":"North Central TX","cs":"08/10/26","bd":"09/16/26","open":"12/07/26"},
    {"rsh":"RSH-00104","store":"001693","phase":"4. Permitting","address":"13500 N Rockwell Ave","city":"Oklahoma City","state":"OK","region":"Central OK","cs":"09/07/26","bd":"Retrofit","open":"01/25/27"},
    {"rsh":"RSH-00180","store":"001404","phase":"4. Permitting","address":"2602 50th St Suite 300","city":"Lubbock","state":"TX","region":"West TX","cs":"08/31/26","bd":"09/30/26","open":"01/25/27"},
    {"rsh":"RSH-00528","store":"TBD","phase":"3. Design","address":"2401 Henney Rd","city":"Choctaw","state":"OK","region":"Central OK","cs":"09/21/26","bd":"11/04/26","open":"02/01/27"},
    {"rsh":"RSH-00111","store":"TBD","phase":"3. Design","address":"35910 US-27","city":"Haines City","state":"FL","region":"FL West Coast","cs":"09/21/26","bd":"10/21/26","open":"02/22/27"},
    {"rsh":"RSH-00127","store":"TBD","phase":"3. Design","address":"Covell and Sooner","city":"Edmond","state":"OK","region":"North OK","cs":"01/06/27","bd":"02/10/27","open":"05/24/27"},
    {"rsh":"RSH-00147","store":"001405","phase":"4. Permitting","address":"10581 Colonial Blvd","city":"Fort Myers","state":"FL","region":"FL West Coast","cs":"11/04/26","bd":"12/09/26","open":"04/19/27"},
    {"rsh":"RSH-00273","store":"001341","phase":"3. Design","address":"6875 N Church Ave","city":"Mulberry","state":"FL","region":"FL West Coast","cs":"11/30/26","bd":"01/06/27","open":"05/03/27"},
    {"rsh":"RSH-00115","store":"001280","phase":"3. Design","address":"1159 Missouri Ave N","city":"Largo","state":"FL","region":"FL West Coast","cs":"01/25/27","bd":"03/03/27","open":"06/14/27"},
    {"rsh":"RSH-00099","store":"000990","phase":"3. Design","address":"NWC Alf Coleman & Hwy 98","city":"Panama City Beach","state":"FL","region":"FL Panhandle East","cs":"01/11/27","bd":"04/16/27","open":"08/16/27"},
    {"rsh":"RSH-00239","store":"001724","phase":"3. Design","address":"82 & Blackstone","city":"Fort Myers","state":"FL","region":"FL West Coast","cs":"03/22/27","bd":"06/16/27","open":"11/01/27"},
    # ── Phase 2: Due Diligence ─────────────────────────────────────────────────
    {"rsh":"RSH-00151","store":"TBD","phase":"2. Due Diligence","address":"3514 E Interstate Drive","city":"Amarillo","state":"TX","region":"West TX","cs":"08/03/26","bd":"09/02/26","open":"12/07/26"},
    {"rsh":"RSH-00592","store":"TBD","phase":"2. Due Diligence","address":"1080 Fort Hood St","city":"Killeen","state":"TX","region":"South Central TX","cs":"12/02/26","bd":"01/13/27","open":"04/19/27"},
    {"rsh":"RSH-00617","store":"001723","phase":"2. Due Diligence","address":"390 TX-199","city":"Springtown","state":"TX","region":"North Central TX","cs":"12/02/26","bd":"01/06/27","open":"05/03/27"},
    {"rsh":"RSH-00606","store":"TBD","phase":"2. Due Diligence","address":"2215 N Big Spring St","city":"Midland","state":"TX","region":"Permian Basin","cs":"12/14/26","bd":"01/27/27","open":"05/03/27"},
    {"rsh":"RSH-00205","store":"TBD","phase":"2. Due Diligence","address":"2159 W 9 Mile Rd","city":"Pensacola","state":"FL","region":"FL Panhandle West","cs":"12/14/26","bd":"02/03/27","open":"05/10/27"},
    {"rsh":"RSH-00266","store":"TBD","phase":"2. Due Diligence","address":"116 Sebring Square","city":"Sebring","state":"FL","region":"FL West Coast","cs":"01/06/27","bd":"02/10/27","open":"05/24/27"},
    {"rsh":"RSH-00582","store":"TBD","phase":"2. Due Diligence","address":"Cottonwood & Hwy 27","city":"Davenport","state":"FL","region":"FL West Coast","cs":"01/25/27","bd":"03/10/27","open":"06/14/27"},
    {"rsh":"RSH-00211","store":"001337","phase":"2. Due Diligence","address":"12720 U.S. Hwy 19","city":"Hudson","state":"FL","region":"FL West Coast","cs":"02/01/27","bd":"03/10/27","open":"06/28/27"},
    {"rsh":"RSH-00108","store":"TBD","phase":"2. Due Diligence","address":"4801 Cortez Blvd","city":"Bradenton","state":"FL","region":"FL West Coast","cs":"02/22/27","bd":"03/24/27","open":"07/19/27"},
    {"rsh":"RSH-00610","store":"TBD","phase":"2. Due Diligence","address":"16564 US-331","city":"Freeport","state":"FL","region":"FL Panhandle East","cs":"03/01/27","bd":"04/01/27","open":"07/26/27"},
    {"rsh":"RSH-00579","store":"TBD","phase":"2. Due Diligence","address":"1325 E Oak St","city":"Arcadia","state":"FL","region":"FL West Coast","cs":"03/01/27","bd":"04/01/27","open":"07/26/27"},
    {"rsh":"RSH-00584","store":"TBD","phase":"2. Due Diligence","address":"1405 W Buckingham Rd","city":"Garland","state":"TX","region":"North Central TX","cs":"05/31/27","bd":"07/07/27","open":"08/30/27"},
    {"rsh":"RSH-00596","store":"TBD","phase":"2. Due Diligence","address":"6051 Skillman St","city":"Dallas","state":"TX","region":"North Central TX","cs":"05/10/27","bd":"06/16/27","open":"09/20/27"},
    {"rsh":"RSH-00601","store":"TBD","phase":"2. Due Diligence","address":"1738 N Town E Blvd","city":"Mesquite","state":"TX","region":"North Central TX","cs":"05/03/27","bd":"06/09/27","open":"09/20/27"},
    {"rsh":"RSH-00208","store":"TBD","phase":"2. Due Diligence","address":"2511 Thomas Dr","city":"Panama City Beach","state":"FL","region":"FL Panhandle East","cs":"05/31/27","bd":"10/28/26","open":"10/18/27"},
    {"rsh":"RSH-00575","store":"TBD","phase":"2. Due Diligence","address":"2805 S 14th St","city":"Abilene","state":"TX","region":"Middle Earth","cs":"05/17/27","bd":"06/21/27","open":"10/18/27"},
    {"rsh":"RSH-00126","store":"TBD","phase":"2. Due Diligence","address":"3900 E 15th St","city":"Edmond","state":"OK","region":"North OK","cs":"05/17/27","bd":"06/21/27","open":"10/18/27"},
    {"rsh":"RSH-00233","store":"TBD","phase":"2. Due Diligence","address":"15201 N Cleveland Ave","city":"Fort Myers","state":"FL","region":"FL West Coast","cs":"06/14/27","bd":"07/14/27","open":"11/01/27"},
    {"rsh":"RSH-00622","store":"TBD","phase":"2. Due Diligence","address":"1751 66th St N","city":"St. Petersburg","state":"FL","region":"FL West Coast","cs":"05/17/27","bd":"07/14/27","open":"11/01/27"},
    {"rsh":"RSH-00217","store":"TBD","phase":"2. Due Diligence","address":"7603 Seminole Blvd","city":"Seminole","state":"FL","region":"FL West Coast","cs":"05/17/27","bd":"06/23/27","open":"11/08/27"},
    {"rsh":"RSH-00634","store":"TBD","phase":"2. Due Diligence","address":"983 US-98","city":"Destin","state":"FL","region":"FL Panhandle East","cs":"05/24/27","bd":"07/07/27","open":"11/08/27"},
    {"rsh":"RSH-00119","store":"001121","phase":"2. Due Diligence","address":"SWC of Nine Mile & University","city":"Pensacola","state":"FL","region":"FL Panhandle West","cs":"04/26/27","bd":"03/31/27","open":"11/22/27"},
    {"rsh":"RSH-00630","store":"TBD","phase":"2. Due Diligence","address":"201 SW Pine Island Rd","city":"Cape Coral","state":"FL","region":"FL West Coast","cs":"06/28/27","bd":"08/19/27","open":"12/06/27"},
    {"rsh":"RSH-00666","store":"TBD","phase":"2. Due Diligence","address":"1048 S Pine Ave","city":"Ocala","state":"FL","region":"FL West Coast","cs":"06/21/27","bd":"08/04/27","open":"12/06/27"},
]

# Phase 6 open stands (from Drew's Mar 26 report) — used for map only where not in data.json
# Phase 6 open stands per Apr 2, 2026 Drew report — 12 total
_PIPELINE_OPEN_PDF = [
    {"store":"000570","city":"Belleview",     "state":"FL","region":"FL West Coast",    "open":"01/19/26","address":"5530 SE Abshier Blvd"},
    {"store":"000875","city":"Weatherford",   "state":"OK","region":"Central OK",        "open":"01/19/26","address":"945 E Main St"},
    {"store":"000356","city":"Bradenton",     "state":"FL","region":"FL West Coast",    "open":"01/19/26","address":"685 Cortez Rd W"},
    {"store":"000872","city":"Oklahoma City", "state":"OK","region":"North OK",          "open":"01/26/26","address":"9281 N May Ave"},
    {"store":"000882","city":"Gainesville",   "state":"TX","region":"North Central TX",  "open":"01/26/26","address":"403 W US HWY 82"},
    {"store":"001117","city":"Midland",       "state":"TX","region":"Permian Basin",     "open":"01/26/26","address":"6403 W Hwy 158"},
    {"store":"000877","city":"Pensacola",     "state":"FL","region":"FL Panhandle West", "open":"02/09/26","address":"300 E Nine Mile"},
    {"store":"000394","city":"Bradenton",     "state":"FL","region":"FL West Coast",    "open":"02/23/26","address":"5787 Manatee Ave W"},
    {"store":"000573","city":"Spring Hill",   "state":"FL","region":"FL West Coast",    "open":"03/09/26","address":"1321 Commercial Way"},
    {"store":"000758","city":"Belton",        "state":"TX","region":"South Central TX",  "open":"03/09/26","address":"2304 N Main St"},
    # Newly opened Apr 2 report
    {"store":"000516","city":"Cleburne",      "state":"TX","region":"North Central TX",  "open":"03/30/26","address":"1211 W Henderson St"},
    {"store":"000709","city":"Pampa",         "state":"TX","region":"West TX",           "open":"03/30/26","address":"1050 N Hobart St"},
]

# Count of Phase 6 (open) stands per the latest Drew report — used for summary metric
_PIPELINE_OPEN_COUNT_FROM_REPORT = 12

# ── Weekly snapshot tracking ──────────────────────────────────────────────────
# Each entry lists every report date key in chronological order.
# The Schedule Intelligence section uses this to build the date-drift table.
_REPORT_SNAPSHOTS = [
    {"key": "jan15", "label": "Jan 15"},
    {"key": "mar26", "label": "Mar 26"},
    {"key": "apr2",  "label": "Apr 2"},
]

# ── Open-date history: Jan 15 baseline → weekly snapshots ────────────────────
# Only 2026 opens are tracked (2027 dates are soft/indicative).
# delta_days = apr2 vs jan15 (cumulative drift from baseline)
# Stands that bounced back to jan15 in a later report are still included
# so the full oscillation history is preserved.
_DATE_SHIFTS = [
    # ── Opening imminently — no shift from Jan 15 ─────────────────────────────
    {"rsh":"RSH-00082","city":"Norman",         "state":"OK","store":"000987","jan15":"04/13/26","mar26":"04/13/26","apr2":"04/13/26","delta_days":   0},
    # ── Still pushed out vs Jan 15 ────────────────────────────────────────────
    {"rsh":"RSH-00102","city":"Snyder",        "state":"TX","store":"001118","jan15":"06/15/26","mar26":"08/10/26","apr2":"08/10/26","delta_days":  56},
    {"rsh":"RSH-00094","city":"Fort Myers",    "state":"FL","store":"000757","jan15":"08/03/26","mar26":"09/28/26","apr2":"09/28/26","delta_days":  56},
    {"rsh":"RSH-00068","city":"Waco",          "state":"TX","store":"000711","jan15":"02/23/26","mar26":"04/13/26","apr2":"04/13/26","delta_days":  49},
    {"rsh":"RSH-00088","city":"Lehigh Acres",  "state":"FL","store":"000404","jan15":"09/07/26","mar26":"10/19/26","apr2":"10/19/26","delta_days":  42},
    {"rsh":"RSH-00112","city":"Waco",          "state":"TX","store":"001241","jan15":"08/24/26","mar26":"10/05/26","apr2":"10/05/26","delta_days":  42},
    {"rsh":"RSH-00134","city":"Burleson",      "state":"TX","store":"001686","jan15":"09/28/26","mar26":"11/09/26","apr2":"11/09/26","delta_days":  42},
    {"rsh":"RSH-00103","city":"Waco",          "state":"TX","store":"001713","jan15":"10/19/26","mar26":"11/30/26","apr2":"11/30/26","delta_days":  42},
    {"rsh":"RSH-00084","city":"Punta Gorda",   "state":"FL","store":"000380","jan15":"08/17/26","mar26":"08/31/26","apr2":"09/28/26","delta_days":  42},
    {"rsh":"RSH-00079","city":"Edmond",        "state":"OK","store":"000547","jan15":"05/18/26","mar26":"06/15/26","apr2":"06/15/26","delta_days":  28},
    {"rsh":"RSH-00078","city":"Holiday",       "state":"FL","store":"000674","jan15":"07/06/26","mar26":"08/03/26","apr2":"08/10/26","delta_days":  35},
    {"rsh":"RSH-00106","city":"Lubbock",       "state":"TX","store":"001236","jan15":"06/29/26","mar26":"07/27/26","apr2":"07/27/26","delta_days":  28},
    {"rsh":"RSH-00092","city":"Fort Myers",    "state":"FL","store":"000428","jan15":"07/20/26","mar26":"08/17/26","apr2":"08/17/26","delta_days":  28},
    {"rsh":"RSH-00087","city":"Winter Haven",  "state":"FL","store":"000883","jan15":"08/17/26","mar26":"09/14/26","apr2":"09/14/26","delta_days":  28},
    {"rsh":"RSH-00110","city":"Granbury",      "state":"TX","store":"001156","jan15":"07/20/26","mar26":"08/10/26","apr2":"08/10/26","delta_days":  21},
    {"rsh":"RSH-00116","city":"Canyon",        "state":"TX","store":"001119","jan15":"06/08/26","mar26":"06/22/26","apr2":"06/22/26","delta_days":  14},
    {"rsh":"RSH-00083","city":"Oklahoma City", "state":"OK","store":"000874","jan15":"10/26/26","mar26":"11/09/26","apr2":"11/09/26","delta_days":  14},
    {"rsh":"RSH-00086","city":"Ocala",         "state":"FL","store":"000414","jan15":"10/19/26","mar26":"11/02/26","apr2":"11/02/26","delta_days":  14},
    # ── Still pulled in vs Jan 15 ─────────────────────────────────────────────
    {"rsh":"RSH-00114","city":"Pensacola",     "state":"FL","store":"001154","jan15":"09/07/26","mar26":"08/10/26","apr2":"08/10/26","delta_days": -28},
    {"rsh":"RSH-00229","city":"Pensacola",     "state":"FL","store":"001344","jan15":"11/30/26","mar26":"11/02/26","apr2":"11/02/26","delta_days": -28},
    {"rsh":"RSH-00113","city":"North Port",    "state":"FL","store":"001120","jan15":"12/14/26","mar26":"12/07/26","apr2":"12/07/26","delta_days":  -7},
    # ── Bounced back to Jan 15 (net zero drift but oscillated) ────────────────
    {"rsh":"RSH-00069","city":"Fort Walton Beach","state":"FL","store":"000571","jan15":"06/22/26","mar26":"04/27/26","apr2":"06/22/26","delta_days":   0},
    {"rsh":"RSH-00081","city":"Mary Esther",   "state":"FL","store":"000986","jan15":"06/01/26","mar26":"05/18/26","apr2":"06/01/26","delta_days":   0},
    {"rsh":"RSH-00089","city":"Gulf Breeze",   "state":"FL","store":"000327","jan15":"08/10/26","mar26":"07/13/26","apr2":"08/10/26","delta_days":   0},
    {"rsh":"RSH-00091","city":"Killeen",       "state":"TX","store":"001122","jan15":"05/18/26","mar26":"06/01/26","apr2":"05/18/26","delta_days":   0},
    {"rsh":"RSH-00101","city":"Beverly Hills", "state":"TX","store":"001238","jan15":"05/18/26","mar26":"06/15/26","apr2":"05/18/26","delta_days":   0},
]

# ── Already-opened 2026 stands — complete schedule shift picture ─────────────
# These stands have opened but may have slipped vs the Jan 15 baseline.
# UPDATE the "jan15" field for each stand using Drew's Jan 15 report;
# the delta_days will auto-calculate from the display code.
# Format: actual open date goes in mar26/apr2; Jan 15 projected date in jan15.
# Stands where jan15 == actual open = no slip; where jan15 < actual open = slipped.
_OPENED_SHIFTS = [
    # store    city                state  jan15 (fill from Jan 15 report) actual open
    {"store":"000570","city":"Belleview",     "state":"FL","jan15":"01/19/26","actual_open":"01/19/26"},  # ← fill jan15
    {"store":"000875","city":"Weatherford",   "state":"OK","jan15":"01/19/26","actual_open":"01/19/26"},  # ← fill jan15
    {"store":"000356","city":"Bradenton",     "state":"FL","jan15":"01/19/26","actual_open":"01/19/26"},  # ← fill jan15
    {"store":"000872","city":"Oklahoma City", "state":"OK","jan15":"01/26/26","actual_open":"01/26/26"},  # ← fill jan15
    {"store":"000882","city":"Gainesville",   "state":"TX","jan15":"01/26/26","actual_open":"01/26/26"},  # ← fill jan15
    {"store":"001117","city":"Midland",       "state":"TX","jan15":"01/26/26","actual_open":"01/26/26"},  # ← fill jan15
    {"store":"000877","city":"Pensacola",     "state":"FL","jan15":"02/09/26","actual_open":"02/09/26"},  # ← fill jan15
    {"store":"000394","city":"Bradenton",     "state":"FL","jan15":"02/23/26","actual_open":"02/23/26"},  # ← fill jan15
    {"store":"000573","city":"Spring Hill",   "state":"FL","jan15":"03/09/26","actual_open":"03/09/26"},  # ← fill jan15
    {"store":"000758","city":"Belton",        "state":"TX","jan15":"03/09/26","actual_open":"03/09/26"},  # ← fill jan15
    {"store":"000516","city":"Cleburne",      "state":"TX","jan15":"03/30/26","actual_open":"03/30/26"},  # ← fill jan15
    {"store":"000709","city":"Pampa",         "state":"TX","jan15":"03/30/26","actual_open":"03/30/26"},  # ← fill jan15
]

# Stands new to pipeline since Jan 15 report
_NEW_SINCE_JAN15 = [
    "RSH-00104","RSH-00617","RSH-00233","RSH-00622","RSH-00592","RSH-00606",
    "RSH-00610","RSH-00579","RSH-00584","RSH-00217","RSH-00601","RSH-00575",
    "RSH-00126","RSH-00634","RSH-00666","RSH-00630",
]


_PIPELINE_JSON_PATH = os.path.join(os.path.dirname(__file__), "pipeline_data.json")


@st.cache_data(show_spinner=False)
def _load_pipeline_data(_mtime: float) -> dict:
    """Load pipeline_data.json once and cache it.

    _mtime is the file's modification timestamp — passing it as a parameter
    means the cache automatically invalidates the moment you drop a new file
    in, so the weekly update workflow is: replace pipeline_data.json → done.
    """
    import json as _j
    with open(_PIPELINE_JSON_PATH) as f:
        return _j.load(f)


@st.cache_data(show_spinner=False)
def _get_pipeline_dfs(_mtime: float):
    """Return pre-parsed pipeline DataFrames — built once, cached until file changes."""
    data = _load_pipeline_data(_mtime)
    df = pd.DataFrame(data["upcoming"])
    df["open_dt"] = pd.to_datetime(df["open"], format="%m/%d/%y", errors="coerce")
    df["cs_dt"]   = pd.to_datetime(df["cs"],   format="%m/%d/%y", errors="coerce")
    df = df.sort_values("open_dt").reset_index(drop=True)
    shifts_df = pd.DataFrame(data["date_shifts"])
    return df, shifts_df


def _pipeline_mtime() -> float:
    """Return pipeline_data.json modification time, or 0 if file not found."""
    try:
        return os.path.getmtime(_PIPELINE_JSON_PATH)
    except FileNotFoundError:
        return 0.0


def _pl_coords(city, state):
    """Return (lat, lon) or None from the city/state lookup."""
    return _CITY_COORDS.get((city, state))


def _phase_color_hex(phase):
    if "5." in phase:   return "#FF6B00"   # orange
    if "4." in phase:   return "#F5A623"   # amber
    if "3." in phase:   return "#4A90E2"   # blue
    if "2." in phase:   return "#9B59B6"   # purple
    return "#27AE60"                         # green (open)


def _phase_label(phase):
    mapping = {
        "5. Construction": "🔨 Under Construction",
        "4. Permitting":   "📋 Permitting",
        "3. Design":       "📐 Design",
        "2. Due Diligence":"🔍 Due Diligence",
    }
    return mapping.get(phase, phase)


@st.cache_data(show_spinner=False)
def _build_pipeline_map_html(upcoming_rows, open_rows, existing_stands):
    """Build a self-contained Leaflet.js HTML map with clickable legend toggles."""
    import json as _json

    markers = []

    # Store IDs already represented by upcoming_rows — these win over open markers
    upcoming_store_ids = {r.get("store","") for r in upcoming_rows
                         if r.get("store","") not in ("TBD", "")}

    # Track every store ID plotted so far to prevent any cross-source duplicates
    plotted_store_ids = set()

    # ── Existing open stands from data.json ───────────────────────────────────
    seen_stand_names = set()
    for s in existing_stands:
        raw = s.get("Stand", "")
        if raw in seen_stand_names:
            continue
        seen_stand_names.add(raw)
        parts = raw.split(" ", 1)
        if len(parts) < 2:
            continue
        store_id = parts[0].strip()          # e.g. "000356"
        loc = parts[1]                        # e.g. "Bradenton, FL - 2"
        loc_parts = loc.split(",")
        if len(loc_parts) < 2:
            continue
        city = loc_parts[0].strip()
        st_part = loc_parts[1].strip().split()[0] if loc_parts[1].strip() else ""
        # Skip if this store is shown as an upcoming (colored) marker
        if store_id in upcoming_store_ids:
            continue
        if store_id in plotted_store_ids:
            continue
        plotted_store_ids.add(store_id)
        coords = _pl_coords(city, st_part)
        if not coords:
            continue
        lat, lon = coords
        markers.append({
            "lat": round(lat + (hash(raw) % 100) * 0.003, 5),
            "lon": round(lon + (hash(raw) % 73)  * 0.003, 5),
            "color": "#27AE60", "radius": 7, "group": "Open",
            "popup": f"<b>{raw.split(' - ')[0].strip()}</b><br>{city}, {st_part}<br><i>Currently Open</i>",
        })

    # ── Phase-6 stands from PDF not yet in data.json ─────────────────────────
    # (skip any store already plotted above or reserved for upcoming layer)
    for r in open_rows:
        sid = r.get("store", "")
        if sid in upcoming_store_ids:
            continue
        if sid in plotted_store_ids:
            continue
        coords = _pl_coords(r["city"], r["state"])
        if not coords:
            continue
        plotted_store_ids.add(sid)
        lat, lon = coords
        markers.append({
            "lat": round(lat + (hash(sid)       % 50) * 0.004, 5),
            "lon": round(lon + (hash(sid + "x") % 50) * 0.004, 5),
            "color": "#27AE60", "radius": 7, "group": "Open",
            "popup": (f"<b>#{sid}</b> · {r['city']}, {r['state']}<br>"
                      f"{r['address']}<br>Region: {r.get('region','')}<br>"
                      f"Opened: {r.get('open','')}"),
        })

    # Upcoming stands (phases 2–5)
    for r in upcoming_rows:
        coords = _pl_coords(r["city"], r["state"])
        if not coords:
            continue
        lat, lon = coords
        sid = r.get("store", "TBD")
        color = _phase_color_hex(r["phase"])
        label = _phase_label(r["phase"])
        # strip emoji for group key so JS object key stays clean
        group_key = label.split(" ", 1)[1] if " " in label else label
        markers.append({
            "lat": round(lat + (hash(sid + "u") % 80) * 0.004, 5),
            "lon": round(lon + (hash(sid + "v") % 80) * 0.004, 5),
            "color": color, "radius": 9, "group": group_key,
            "popup": (f"<b>{r['city']}, {r['state']}</b> — #{sid}<br>"
                      f"{r['address']}<br>Region: {r.get('region','')}<br>"
                      f"Phase: {label}<br>"
                      f"Const. Start: {r.get('cs','—')}<br>"
                      f"Building Drop: {r.get('bd','—')}<br>"
                      f"<b>Est. Opening: {r.get('open','—')}</b>"),
        })

    markers_json = _json.dumps(markers)

    # Legend items: [label, hex-color, group-key]
    legend_items = [
        ["Open",                "#27AE60", "Open"],
        ["Under Construction",  "#FF6B00", "Under Construction"],
        ["Permitting",          "#F5A623", "Permitting"],
        ["Design",              "#4A90E2", "Design"],
        ["Due Diligence",       "#9B59B6", "Due Diligence"],
    ]
    legend_json = _json.dumps(legend_items)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body{{height:100%;margin:0;padding:0;background:#1a1a2e;}}
  #map{{height:100%;width:100%;}}
  .legend-box{{
    background:rgba(15,15,30,0.93);color:#e8e8e8;
    padding:12px 16px;border-radius:10px;
    font-family:sans-serif;font-size:13px;
    box-shadow:0 2px 8px rgba(0,0,0,0.5);
    min-width:180px;
  }}
  .legend-box b{{font-size:14px;display:block;margin-bottom:6px;color:#fff;}}
  .leg-row{{
    display:flex;align-items:center;gap:8px;
    padding:5px 8px;border-radius:6px;
    cursor:pointer;user-select:none;
    transition:background 0.15s;
    margin-bottom:2px;
  }}
  .leg-row:hover{{background:rgba(255,255,255,0.08);}}
  .leg-row.off{{opacity:0.35;}}
  .leg-dot{{
    flex-shrink:0;width:14px;height:14px;
    border-radius:50%;border:2px solid rgba(255,255,255,0.3);
  }}
  .leg-label{{flex:1;}}
  .leg-count{{font-size:11px;color:#aaa;}}
</style>
</head>
<body>
<div id="map"></div>
<script>
var map = L.map('map',{{zoomControl:true}}).setView([32.5,-95],5);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
  attribution:'&copy; OpenStreetMap &amp; CARTO',maxZoom:19
}}).addTo(map);

var allMarkers = {markers_json};
var legendDefs  = {legend_json};

// Build a LayerGroup per category
var groups = {{}};
legendDefs.forEach(function(d){{ groups[d[2]] = L.layerGroup().addTo(map); }});

// Count per group for the legend badge
var counts = {{}};
legendDefs.forEach(function(d){{ counts[d[2]] = 0; }});

allMarkers.forEach(function(m){{
  var grp = groups[m.group];
  if(!grp) return;
  counts[m.group] = (counts[m.group]||0) + 1;
  var circle = L.circleMarker([m.lat,m.lon],{{
    radius:m.radius, color:m.color, fillColor:m.color,
    fillOpacity:0.85, weight:2, opacity:1
  }});
  circle.bindPopup(m.popup,{{maxWidth:260}});
  grp.addLayer(circle);
}});

// Custom clickable legend — uses data-key to avoid quoting issues with spaced keys
var visibility = {{}};
legendDefs.forEach(function(d){{ visibility[d[2]] = true; }});

var legend = L.control({{position:'bottomleft'}});
legend.onAdd = function(){{
  var div = L.DomUtil.create('div','legend-box');
  var html = '<b>7BREW Locations</b>';
  legendDefs.forEach(function(d){{
    var label=d[0], color=d[1], key=d[2];
    var cnt = counts[key]||0;
    // Use data-key attribute — avoids any JS string-quoting issues
    html += '<div class="leg-row" data-key="' + key + '" title="Click to show/hide">' +
            '<div class="leg-dot" style="background:' + color + ';"></div>' +
            '<span class="leg-label">' + label + '</span>' +
            '<span class="leg-count">' + cnt + '</span>' +
            '</div>';
  }});
  div.innerHTML = html;
  // Single delegated click listener — works for any key regardless of spaces
  div.addEventListener('click', function(e){{
    var row = e.target.closest('.leg-row');
    if(row){{ toggleGroup(row.getAttribute('data-key')); }}
  }});
  L.DomEvent.disableClickPropagation(div);
  return div;
}};
legend.addTo(map);

function toggleGroup(key){{
  var grp = groups[key];
  if(!grp) return;
  visibility[key] = !visibility[key];
  if(visibility[key]){{ grp.addTo(map); }} else {{ map.removeLayer(grp); }}
  // Find the row by data-key and toggle the .off class
  var row = document.querySelector('.leg-row[data-key="' + key + '"]');
  if(row){{
    if(visibility[key]) row.classList.remove('off');
    else                row.classList.add('off');
  }}
}}
</script>
</body>
</html>"""
    return html


@st.cache_data(show_spinner=False)
def _build_gantt_fig(gantt_df_json: str, today_str: str):
    """Build the construction timeline Gantt chart — cached until data or filter changes."""
    import json as _jg
    import pandas as _pdg
    import plotly.express as _pxg

    _gantt_df = _pdg.DataFrame(_jg.loads(gantt_df_json))
    if _gantt_df.empty:
        return None
    # Restore datetimes (serialised as ISO strings)
    _gantt_df["open_dt"] = _pdg.to_datetime(_gantt_df["open_dt"])
    _gantt_df["cs_dt"]   = _pdg.to_datetime(_gantt_df["cs_dt"])

    phase_colors = {
        "5. Construction": "#FF6B00",
        "4. Permitting":   "#F5A623",
        "3. Design":       "#4A90E2",
    }
    fig = _pxg.timeline(
        _gantt_df,
        x_start="cs_dt", x_end="open_dt",
        y="Label", color="phase",
        color_discrete_map=phase_colors,
        labels={"phase": "Phase", "Label": "Stand"},
        category_orders={"Label": _gantt_df["Label"].tolist()},
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        template="plotly_dark",
        height=max(350, len(_gantt_df) * 22 + 80),
        margin=dict(t=20, b=40, l=0, r=0),
        legend=dict(orientation="h", y=1.02),
        xaxis_title="",
    )
    import datetime as _dtg
    _today = _dtg.date.fromisoformat(today_str)
    import pandas as _pdg2
    fig.add_vline(
        x=_pdg2.Timestamp(_today).value / 1e6,
        line_dash="dash",
        line_color="rgba(255,255,255,0.4)", line_width=1.5,
        annotation_text="Today", annotation_position="top right",
        annotation_font_color="rgba(255,255,255,0.6)",
    )
    return fig


@st.cache_data(show_spinner=False)
def _build_milestone_fig(ms_rows_json: str):
    """Build the process leakage milestone drift chart — cached until data or filter changes."""
    import json as _jm
    import pandas as _pdm
    import plotly.graph_objects as _gom

    ms_rows = _jm.loads(ms_rows_json)
    if not ms_rows:
        return None, None

    milestone_labels = {
        "permit_sub":  "Permit Submission",
        "permit_appr": "Permit Approval",
        "cs":          "Construction Start",
        "open":        "Open Date",
    }
    milestone_colors = {
        "Permit Submission":  "#9B59B6",
        "Permit Approval":    "#E74C3C",
        "Construction Start": "#FF6B00",
        "Open Date":          "#4A90E2",
    }

    bar_data = {"Stand": [], "Milestone": [], "Days Drifted": [], "Label": []}
    for r in ms_rows:
        stand = f"{r['city']}, {r['state']}"
        for key, label in milestone_labels.items():
            delta = r.get(f"{key}_delta")
            if delta is None:
                continue
            bar_data["Stand"].append(stand)
            bar_data["Milestone"].append(label)
            bar_data["Days Drifted"].append(delta)
            sign = f"+{delta}d" if delta > 0 else (f"{delta}d" if delta < 0 else "±0")
            bar_data["Label"].append(
                f"{label}: {sign}<br>"
                f"Jan 15: {r.get(key+'_jan15','?')} → Apr 2: {r.get(key+'_apr2','?')}"
            )

    ms_df = _pdm.DataFrame(bar_data)
    stand_order = (
        ms_df[ms_df["Milestone"] == "Open Date"]
        .sort_values("Days Drifted", ascending=True)["Stand"]
        .tolist()
    )
    all_stands = list(dict.fromkeys(stand_order + ms_df["Stand"].tolist()))

    fig = _gom.Figure()
    for label, color in milestone_colors.items():
        sub = ms_df[ms_df["Milestone"] == label]
        if sub.empty:
            continue
        fig.add_bar(
            x=sub["Days Drifted"],
            y=sub["Stand"],
            name=label,
            orientation="h",
            marker_color=[color if d >= 0 else "#27AE60" for d in sub["Days Drifted"]],
            customdata=sub["Label"],
            hovertemplate="%{customdata}<extra></extra>",
        )

    fig.add_vline(x=0, line_color="white", line_width=1, opacity=0.4)
    fig.update_layout(
        template="plotly_dark",
        barmode="group",
        height=max(320, len(ms_rows) * 28 + 100),
        margin=dict(t=20, b=40, l=0, r=20),
        xaxis=dict(title="Days Drifted vs Jan 15 (+ = slipped, − = earlier)",
                   zeroline=True, zerolinecolor="white", zerolinewidth=1),
        yaxis=dict(categoryorder="array", categoryarray=all_stands, title=""),
        legend=dict(orientation="h", y=1.04, x=0),
        bargap=0.25, bargroupgap=0.05,
    )
    return fig, ms_df


def tab_pipeline(dash):
    if not _require_password("pipeline"):
        return
    import streamlit.components.v1 as components

    st.markdown("### 🏗️ Stand Pipeline *(Draft)*")

    # ── Load pipeline data (cached until pipeline_data.json changes) ──────────
    _pmtime = _pipeline_mtime()
    _pdata  = _load_pipeline_data(_pmtime)
    df, shifts_df_base = _get_pipeline_dfs(_pmtime)

    _last_updated = _pdata.get("_last_updated", "unknown")
    st.caption(
        f"**Data source:** Drew Deagan's weekly opening schedule (last updated **{_last_updated}**). "
        "To refresh: replace `pipeline_data.json` with the latest export. "
        "Jan 15, 2026 used as baseline for schedule shift analysis · 2027 dates are soft/indicative · $45K avg revenue/week assumed."
    )

    # ── Print / PDF button ────────────────────────────────────────────────────
    _print_button("🖨️  Print / Save as PDF")

    AVG_REV_PER_WEEK = 45_000   # $ per stand per week

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([1, 1, 1])
    with fc1:
        phase_opts = ["All Phases", "5. Construction", "4. Permitting", "3. Design", "2. Due Diligence"]
        sel_phase = st.selectbox("Phase", phase_opts, key="pipe_phase")
    with fc2:
        state_opts = ["All States"] + sorted(df["state"].unique().tolist())
        sel_state = st.selectbox("State", state_opts, key="pipe_state")
    with fc3:
        region_opts = ["All Regions"] + sorted(df["region"].dropna().unique().tolist())
        sel_region = st.selectbox("Region", region_opts, key="pipe_region")

    dff = df.copy()
    if sel_phase != "All Phases":  dff = dff[dff["phase"] == sel_phase]
    if sel_state != "All States":  dff = dff[dff["state"] == sel_state]
    if sel_region != "All Regions": dff = dff[dff["region"] == sel_region]

    # Pre-load existing open stands (used for open count + map at bottom)
    stands_df_pipe = get_stands_df(dash)
    existing_rows  = stands_df_pipe.to_dict("records") if not stands_df_pipe.empty else []
    open_store_ids = set()
    for row in existing_rows:
        raw = row.get("Stand", "")
        parts = raw.split(" ", 1)
        if parts:
            open_store_ids.add(parts[0].strip())
    for r in _pdata["open_pdf"]:
        open_store_ids.add(r.get("store", ""))
    total_open = len(open_store_ids)

    # ── Summary metrics ───────────────────────────────────────────────────────
    mc = st.columns(6)
    mc[0].metric("✅ Stands Open", total_open, help="Open stands in data.json + Mar 26 report")
    mc[1].metric("Total Pipeline", len(dff))
    mc[2].metric("🔨 Under Construction", len(dff[dff["phase"] == "5. Construction"]))
    mc[3].metric("📋 Permitting",          len(dff[dff["phase"] == "4. Permitting"]))
    mc[4].metric("📐 Design",              len(dff[dff["phase"] == "3. Design"]))
    mc[5].metric("🔍 Due Diligence",       len(dff[dff["phase"] == "2. Due Diligence"]))

    import datetime as _dt
    today = _dt.date.today()

    # ── Schedule Intelligence: weekly date-drift tracker ─────────────────────
    st.divider()
    _report_snapshots = _pdata["report_snapshots"]
    snap_labels = [s["label"] for s in _report_snapshots]
    latest_snap = _report_snapshots[-1]
    st.markdown(f"#### 📅 Schedule Intelligence — Opening Date Tracker  *(2026 opens · indexed to Jan 15 baseline)*")
    st.caption(f"Tracks how opening dates move week-over-week vs the Jan 15 baseline. Latest report: **{latest_snap['label']}**. 2027 dates excluded.")

    shifts_df = shifts_df_base.copy()
    # Exclude any stand whose latest open date has slipped into 2027
    _curr_key = _pdata["report_snapshots"][-1]["key"]
    def _is_2026_open(row):
        import datetime as _dt2
        v = str(row.get(_curr_key, "") or "")
        if not v or v in ("nan", "None", ""):
            return True   # no date → keep
        for _fs in ["%m/%d/%y", "%m/%d/%Y"]:
            try:
                return _dt2.datetime.strptime(v, _fs).year == 2026
            except Exception:
                pass
        return True   # unparseable → keep
    shifts_df = shifts_df[shifts_df.apply(_is_2026_open, axis=1)]
    if sel_state != "All States":
        shifts_df = shifts_df[shifts_df["state"] == sel_state]
    dff_rshs = set(dff["rsh"].tolist())
    _new_since_jan15 = _pdata["new_since_jan15"]
    filtered_new_since = [r for r in _new_since_jan15 if r in dff_rshs]

    # Compute week-over-week delta (latest vs previous snapshot)
    prev_snap = _report_snapshots[-2]["key"] if len(_report_snapshots) >= 2 else "jan15"
    curr_snap = latest_snap["key"]
    def _parse_d(s):
        if not s or str(s) in ("","nan","None"): return None
        for fmt in ["%m/%d/%y","%m/%d/%Y"]:
            try:
                import datetime as _dt
                return _dt.datetime.strptime(str(s), fmt).date()
            except: pass
        return None

    def _wow(row):
        d_prev = _parse_d(row.get(prev_snap,""))
        d_curr = _parse_d(row.get(curr_snap,""))
        if d_prev and d_curr: return (d_curr - d_prev).days
        return 0

    shifts_df["_wow"] = shifts_df.apply(_wow, axis=1)

    pushed  = shifts_df[shifts_df["delta_days"] > 0].sort_values("delta_days", ascending=False)
    pulled  = shifts_df[shifts_df["delta_days"] < 0].sort_values("delta_days")
    bounced = shifts_df[shifts_df["delta_days"] == 0]
    new_count = len(filtered_new_since)

    # ── Compute opened-stand slippage for metrics ─────────────────────────────
    import datetime as _dt_mod
    def _parse_d_simple(s):
        if not s or str(s) in ("","nan","None"): return None
        for fmt in ["%m/%d/%y","%m/%d/%Y"]:
            try:
                return _dt_mod.datetime.strptime(str(s), fmt).date()
            except: pass
        return None

    opened_rows_calc = []
    for o in _pdata["opened_shifts"]:
        d_jan15  = _parse_d_simple(o.get("jan15",""))
        d_actual = _parse_d_simple(o.get("actual_open",""))
        if d_jan15 and d_actual:
            delta = (d_actual - d_jan15).days
        else:
            delta = 0
        opened_rows_calc.append({**o, "delta_days": delta})

    opened_late  = [r for r in opened_rows_calc if r["delta_days"] > 0]
    opened_early = [r for r in opened_rows_calc if r["delta_days"] < 0]
    opened_ontime= [r for r in opened_rows_calc if r["delta_days"] == 0]
    opened_slip_days  = sum(r["delta_days"] for r in opened_late)
    opened_slip_weeks = opened_slip_days / 7
    opened_rev_lost   = opened_slip_weeks * AVG_REV_PER_WEEK

    si1, si2, si3, si4, si5 = st.columns(5)
    total_slip_days  = pushed["delta_days"].sum()
    total_slip_weeks = total_slip_days / 7
    total_rev_risk   = total_slip_weeks * AVG_REV_PER_WEEK
    wow_movers = shifts_df[shifts_df["_wow"] != 0]
    si1.metric("Stands Pushed Out (vs Jan 15)",  len(pushed),   delta=f"+{len(pushed)} delayed",   delta_color="inverse")
    si2.metric("Stands Pulled In (vs Jan 15)",   len(pulled),   delta=f"{len(pulled)} accelerated", delta_color="normal")
    si3.metric(f"Moved This Week ({snap_labels[-2]}→{snap_labels[-1]})", len(wow_movers),
               help="Stands whose date changed since the previous report")
    si4.metric("Revenue at Risk (cumulative delay)", f"${total_rev_risk/1e6:.2f}M",
               help=f"Total weeks pushed out ({total_slip_weeks:.1f} wks) × $45K avg weekly revenue vs Jan 15 baseline")
    si5.metric("Opened Late (2026 YTD)", len(opened_late),
               delta=f"{opened_slip_weeks:.1f} wks lost · ${opened_rev_lost/1e3:.0f}K" if opened_late else "All on time",
               delta_color="inverse" if opened_late else "normal",
               help=f"{len(opened_rows_calc)} total opened · {len(opened_ontime)} on time · {len(opened_early)} early")

    # ── Full date history table ───────────────────────────────────────────────
    st.markdown("**📋 Full Date History** — every snapshot vs Jan 15 baseline")
    st.caption("🔴 pushed out · 🟢 pulled in · ⬜ no change · ↕ bounced back to baseline")

    def _fmt_cell(snap_key, row, jan15_date):
        """Return display string with movement indicator."""
        val  = row.get(snap_key, "")
        if not val or str(val) in ("","nan","None"):
            return "—"
        d_val  = _parse_d(val)
        d_jan15 = _parse_d(jan15_date)
        if not d_val or not d_jan15:
            return str(val)
        delta = (d_val - d_jan15).days
        wks = delta // 7
        if delta > 0:   arrow = f" 🔴+{wks}wk" if wks else f" 🔴+{delta}d"
        elif delta < 0: arrow = f" 🟢{wks}wk"  if wks else f" 🟢{delta}d"
        else:           arrow = ""
        return f"{val}{arrow}"

    # Sort selector — parse actual dates so Oct/Nov sort after Jan, not before
    sort_col1, sort_col2 = st.columns([2, 4])
    with sort_col1:
        sort_opt = st.selectbox(
            "Sort by",
            ["Opening Date (earliest first)", "Opening Date (latest first)",
             "Slippage (most delayed first)", "Stand Name (A–Z)"],
            key="si_sort_opt",
        )

    def _parse_open_date(r):
        """Return a sortable date from the latest snapshot open date field."""
        import datetime as _dt3
        v = str(r.get(curr_snap, "") or "")
        for fs in ["%m/%d/%y", "%m/%d/%Y"]:
            try: return _dt3.datetime.strptime(v, fs).date()
            except: pass
        # fallback: parse jan15 date
        v2 = str(r.get("jan15","") or "")
        for fs in ["%m/%d/%y", "%m/%d/%Y"]:
            try: return _dt3.datetime.strptime(v2, fs).date()
            except: pass
        import datetime as _dt3
        return _dt3.date(9999, 1, 1)  # unknown dates sort last

    if sort_opt == "Opening Date (earliest first)":
        shifts_sorted = shifts_df.copy()
        shifts_sorted["_sort_dt"] = shifts_sorted.apply(_parse_open_date, axis=1)
        shifts_sorted = shifts_sorted.sort_values("_sort_dt", ascending=True)
    elif sort_opt == "Opening Date (latest first)":
        shifts_sorted = shifts_df.copy()
        shifts_sorted["_sort_dt"] = shifts_sorted.apply(_parse_open_date, axis=1)
        shifts_sorted = shifts_sorted.sort_values("_sort_dt", ascending=False)
    elif sort_opt == "Slippage (most delayed first)":
        shifts_sorted = shifts_df.sort_values("delta_days", ascending=False)
    else:  # Stand Name A–Z
        shifts_sorted = shifts_df.sort_values("city", ascending=True)

    hist_rows = []
    for _, r in shifts_sorted.iterrows():
        row_dict = {
            "Stand": f"{r['city']}, {r['state']}",
            "Store": r.get("store",""),
        }
        for snap in _report_snapshots:
            row_dict[snap["label"]] = _fmt_cell(snap["key"], r, r.get("jan15",""))
        # Week-over-week badge
        wow = r["_wow"]
        wow_wks = wow // 7
        if wow > 0:   row_dict["vs Last Wk"] = f"🔴 +{wow_wks}wk" if wow_wks else f"🔴 +{wow}d"
        elif wow < 0: row_dict["vs Last Wk"] = f"🟢 {wow_wks}wk"  if wow_wks else f"🟢 {wow}d"
        else:         row_dict["vs Last Wk"] = "—"
        net = r["delta_days"]
        net_wks = net // 7
        row_dict["Net vs Jan 15"] = (
            f"+{net_wks}wk" if net > 0
            else (f"{net_wks}wk" if net < 0 else "±0")
        )
        hist_rows.append(row_dict)

    if hist_rows:
        hist_df = pd.DataFrame(hist_rows)
        st.dataframe(hist_df, use_container_width=True, hide_index=True,
                     height=min(60 + len(hist_df) * 35, 520))

    # ── Section print button — builds standalone HTML and opens in new tab ────
    # opened_display_rows is populated below; declare early so print button can reference it
    opened_display_rows = []

    # ── Already-opened 2026 stands ────────────────────────────────────────────
    st.markdown("**✅ Already Opened 2026 — Schedule Performance**")
    st.caption(
        "Shows every stand that opened in 2026 vs the Jan 15 baseline. "
        "🔴 = opened late · 🟢 = opened early · ⬜ = on time.  "
        "*Update the `jan15` dates in `pipeline_data.json → opened_shifts` from Drew's Jan 15 report to see true slippage.*"
    )

    opened_display_rows = []
    for r in sorted(opened_rows_calc, key=lambda x: x["delta_days"], reverse=True):
        delta = r["delta_days"]
        wks   = abs(delta) // 7
        days_rem = abs(delta) % 7
        if delta > 0:
            slip_str = f"🔴 +{wks}wk" if wks else f"🔴 +{delta}d"
        elif delta < 0:
            slip_str = f"🟢 -{wks}wk" if wks else f"🟢 {delta}d"
        else:
            slip_str = "⬜ On Time"
        opened_display_rows.append({
            "Stand": f"{r['city']}, {r['state']}",
            "Store #": r.get("store",""),
            "Jan 15 Projected": r.get("jan15",""),
            "Actual Open": r.get("actual_open",""),
            "vs Jan 15": slip_str,
        })

    if opened_display_rows:
        opened_df = pd.DataFrame(opened_display_rows)
        st.dataframe(opened_df, use_container_width=True, hide_index=True,
                     height=min(60 + len(opened_df) * 35, 480))
        if all(r["delta_days"] == 0 for r in opened_rows_calc):
            st.info("⚠️ Jan 15 dates not yet filled in — all deltas show 0. Update `opened_shifts[].jan15` in `pipeline_data.json` with the actual projected dates from Drew's Jan 15 report.")

    # ── Section print button — both tables now fully built, safe to reference ──
    if hist_rows or opened_display_rows:
        report_date  = _pdata.get("_last_updated", "")
        snap_str     = "  ·  ".join(s["label"] for s in _report_snapshots)
        latest_label = _report_snapshots[-1]["label"] if _report_snapshots else ""

        # ── Metric cards ──────────────────────────────────────────────────────
        def _metric_card(label, value, sub="", color="#FF6B00"):
            sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
            return (f"<div class='kpi'>"
                    f"<div class='kpi-val' style='color:{color}'>{value}</div>"
                    f"<div class='kpi-lbl'>{label}</div>"
                    f"{sub_html}"
                    f"</div>")

        rev_risk_fmt   = f"${total_rev_risk/1e6:.2f}M"
        opened_rev_fmt = f"${opened_rev_lost/1e3:.0f}K lost" if opened_late else "All on time"
        metrics_html = (
            _metric_card("Pushed Out vs Jan 15",   len(pushed),        f"+{len(pushed)} delayed",      "#c0392b") +
            _metric_card("Pulled In vs Jan 15",    len(pulled),        f"{len(pulled)} accelerated",   "#27ae60") +
            _metric_card(f"Moved This Week",        len(wow_movers),    f"since last report",           "#e67e22") +
            _metric_card("Revenue at Risk",         rev_risk_fmt,       f"{total_slip_weeks:.1f} wks × $45K", "#c0392b") +
            _metric_card("Opened Late (2026 YTD)", len(opened_late),   opened_rev_fmt,                 "#8e44ad" if opened_late else "#27ae60")
        )

        # ── Build table rows with row-level color coding ───────────────────
        def _si_table(rows, caption, net_col="Net vs Jan 15"):
            if not rows: return ""
            cols = list(rows[0].keys())
            hdr  = "".join(f"<th>{c}</th>" for c in cols)
            body = ""
            for r in rows:
                net = str(r.get(net_col, ""))
                if net.startswith("+"):    row_cls = " class='pushed'"
                elif net.startswith("-"):  row_cls = " class='pulled'"
                else:                     row_cls = ""
                cells = ""
                for c in cols:
                    v = str(r.get(c, ""))
                    # Cell-level coloring for snapshot date cells
                    if "🔴" in v:   td = f"<td class='red'>{v}</td>"
                    elif "🟢" in v: td = f"<td class='grn'>{v}</td>"
                    elif c == net_col and row_cls == " class='pushed'":
                        td = f"<td><strong style='color:#c0392b'>{v}</strong></td>"
                    elif c == net_col and row_cls == " class='pulled'":
                        td = f"<td><strong style='color:#27ae60'>{v}</strong></td>"
                    else:           td = f"<td>{v}</td>"
                    cells += td
                body += f"<tr{row_cls}>{cells}</tr>"
            return (f"<h3 class='tbl-cap'>{caption}</h3>"
                    f"<table><thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table>")

        upcoming_tbl = _si_table(
            hist_rows,
            f"📋 Upcoming 2026 Openings — Date History vs Jan 15 Baseline  ({len(hist_rows)} stands · as of {latest_label})"
        )
        opened_tbl = _si_table(
            opened_display_rows,
            f"✅ Already Opened 2026 — Schedule Performance  ({len(opened_display_rows)} stands)",
            net_col="vs Jan 15"
        )

        html_doc = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<title>7BREW Schedule Intelligence — {report_date}</title>
<style>
  *      {{ box-sizing:border-box; margin:0; padding:0; }}
  body   {{ font-family:Arial,sans-serif; font-size:11.5px; color:#111;
            background:#fff; padding:0.4in 0.5in; }}
  /* ── Header ── */
  .hdr   {{ background:#FF6B00; color:#fff; padding:10px 14px;
            border-radius:6px; margin-bottom:14px; display:flex;
            justify-content:space-between; align-items:center; }}
  .hdr h1{{ font-size:16px; font-weight:700; }}
  .hdr p {{ font-size:10px; opacity:.85; margin-top:3px; }}
  .hdr-right {{ text-align:right; font-size:10px; opacity:.85; }}
  /* ── KPI strip ── */
  .kpi-row {{ display:flex; gap:10px; margin-bottom:16px; }}
  .kpi   {{ flex:1; border:1px solid #ddd; border-radius:5px;
            padding:8px 10px; background:#fafafa; }}
  .kpi-val{{ font-size:20px; font-weight:700; line-height:1.1; }}
  .kpi-lbl{{ font-size:9px; color:#555; margin-top:2px; text-transform:uppercase;
             letter-spacing:.03em; }}
  .kpi-sub{{ font-size:9px; color:#888; margin-top:1px; }}
  /* ── Tables ── */
  .tbl-cap{{ font-size:12px; font-weight:700; margin:18px 0 5px;
             padding-bottom:4px; border-bottom:2px solid #FF6B00; }}
  table  {{ border-collapse:collapse; width:100%; margin-bottom:6px; }}
  thead tr{{ background:#2c2c2c; color:#fff; }}
  th     {{ padding:5px 7px; font-size:10px; text-align:left;
            white-space:nowrap; font-weight:600; }}
  td     {{ padding:4px 7px; border-bottom:1px solid #e8e8e8;
            white-space:nowrap; }}
  tr.pushed td {{ background:#fff5f5; }}
  tr.pulled td  {{ background:#f0fff4; }}
  tr:hover td   {{ background:#fffbf0; }}
  td.red {{ color:#c0392b; font-weight:600; }}
  td.grn {{ color:#27ae60; font-weight:600; }}
  /* ── Legend ── */
  .legend{{ font-size:9.5px; color:#666; margin-top:4px; margin-bottom:14px; }}
  /* ── Footer ── */
  .footer{{ font-size:9px; color:#aaa; margin-top:20px;
            border-top:1px solid #eee; padding-top:6px; }}
  /* ── Print ── */
  @media print {{
    @page {{ margin:0.4in; size:landscape; }}
    tr.pushed td {{ background:#fff5f5 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    tr.pulled td  {{ background:#f0fff4 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    thead tr      {{ background:#2c2c2c !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    .kpi          {{ background:#fafafa !important; border:1px solid #ddd !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    .hdr          {{ background:#FF6B00 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  }}
</style>
</head><body>
<div class='hdr'>
  <div>
    <h1>🏗️ 7BREW — Schedule Intelligence Report</h1>
    <p>Opening date tracker · 2026 opens · indexed to Jan 15 baseline · {snap_str}</p>
  </div>
  <div class='hdr-right'>Data as of {report_date}<br>🔴 pushed out · 🟢 pulled in</div>
</div>
<div class='kpi-row'>{metrics_html}</div>
<div class='legend'>
  <span style='background:#fff5f5;padding:2px 6px;border:1px solid #fcc;border-radius:3px'>🔴 Row = pushed out vs Jan 15</span>
  &nbsp;
  <span style='background:#f0fff4;padding:2px 6px;border:1px solid #c3e6cb;border-radius:3px'>🟢 Row = pulled in vs Jan 15</span>
  &nbsp; Cell indicators show movement relative to Jan 15 baseline.
</div>
{upcoming_tbl}
{opened_tbl}
<div class='footer'>Generated from 7BREW Pipeline Dashboard · {report_date}</div>
<script>window.onload = function(){{ window.print(); }}</script>
</body></html>"""

        # st.download_button is the most reliable cross-browser approach:
        # the HTML file is served by Streamlit directly (no popup/iframe issues).
        # The report already contains window.onload = window.print() so the
        # browser print dialog opens automatically when the file is opened.
        _fname = f"7BREW_Schedule_Intelligence_{report_date.replace('/','')}.html"
        st.download_button(
            label="🖨️  Download Schedule Intelligence Report",
            data=html_doc.encode("utf-8"),
            file_name=_fname,
            mime="text/html",
            help="Downloads an HTML report — open it in your browser and the print dialog will appear automatically. Save as PDF to share.",
            type="primary",
        )

    # ── New stands since Jan 15 ───────────────────────────────────────────────
    if filtered_new_since:
        st.markdown("**🆕 New to Pipeline Since Jan 15**")
        new_stands_info = [r for r in _pdata["upcoming"] if r["rsh"] in filtered_new_since]
        if new_stands_info:
            new_df = pd.DataFrame(new_stands_info)[["city","state","phase","open"]].copy()
            new_df.columns = ["City","State","Phase","Est. Opening"]
            st.dataframe(new_df, use_container_width=True, hide_index=True)

    # ── Gantt chart ───────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 📊 Construction Timeline — Phases 3–5")

    gantt_df = dff[dff["phase"].isin(["5. Construction","4. Permitting","3. Design"])].copy()
    gantt_df = gantt_df[gantt_df["open_dt"].notna() & gantt_df["cs_dt"].notna()].copy()
    if not gantt_df.empty:
        gantt_df["Label"] = gantt_df.apply(
            lambda r: f"{r['city']}, {r['state']}" + (f" #{r['store']}" if r["store"] != "TBD" else ""),
            axis=1)
        gantt_df = gantt_df.sort_values("open_dt", ascending=False)
        # Serialise to JSON so the cached builder can hash inputs efficiently
        import json as _json_g
        _gantt_json = _json_g.dumps(
            gantt_df[["cs_dt","open_dt","Label","phase","store"]].astype(str).to_dict("records")
        )
        fig_gantt = _build_gantt_fig(_gantt_json, str(today))
        if fig_gantt is not None:
            st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.info("No stands with both Construction Start and Open Date in current filter.")

    # ── Milestone Drift Chart ─────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 🔍 Process Leakage — Milestone Drift vs Jan 15 Baseline")
    st.caption(
        "Shows how each milestone date moved between the Jan 15 and Apr 2 reports. "
        "🔴 bar = slipped later · 🟢 bar = moved earlier. "
        "If Permit Approval consistently leads all other bars, permitting is the bottleneck. "
        "If Construction Start leads, the issue is post-permit execution."
    )

    _ms_data = _pdata.get("milestone_shifts", [])

    # Phase filter — default to Construction, allow expanding
    ms_phase_opts = ["5. Construction", "4. Permitting", "3. Design", "All Phases"]
    ms_phase = st.selectbox("Show Phase", ms_phase_opts, key="ms_phase_sel")

    # Filter milestone data to match current state filter + phase selection
    ms_rows = [
        r for r in _ms_data
        if (ms_phase == "All Phases" or r["phase"] == ms_phase)
        and (sel_state == "All States" or r["state"] == sel_state)
        and any(r.get(f"{k}_delta") is not None
                for k in ["permit_sub","permit_appr","cs","open"])
    ]

    if not ms_rows:
        st.info("No milestone data available for the current filter selection.")
    else:
        import json as _json_ms
        _ms_json = _json_ms.dumps(ms_rows)
        fig_ms, ms_df = _build_milestone_fig(_ms_json)
        if fig_ms is not None:
            st.plotly_chart(fig_ms, use_container_width=True)

        # Summary insight callout
        if ms_df is not None and not ms_df.empty:
            avg_by_milestone = ms_df.groupby("Milestone")["Days Drifted"].mean().sort_values(ascending=False)
            worst_milestone = avg_by_milestone.index[0]
            worst_avg = avg_by_milestone.iloc[0]
            open_avg  = avg_by_milestone.get("Open Date", 0)
            if isinstance(open_avg, pd.Series): open_avg = open_avg.iloc[0]
            if worst_avg > 0:
                st.info(
                    f"📊 **Process insight:** Across the {len(ms_rows)} stands shown, "
                    f"**{worst_milestone}** has the largest average drift at **+{worst_avg:.0f} days** vs Jan 15. "
                    f"Average open date drift is **+{open_avg:.0f} days**."
                )

    # ── Upcoming openings table ────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 📋 Upcoming Openings")
    table_df = dff[["phase","address","city","state","region","cs","bd","open","store","rsh"]].copy()
    table_df.columns = ["Phase","Address","City","State","Region",
                        "Const. Start","Building Drop","Est. Opening","Store #","RSH"]
    table_df["Phase"]   = table_df["Phase"].map(_phase_label)
    table_df["Store #"] = table_df["Store #"].apply(lambda x: x if x != "TBD" else "—")
    # Flag shifted stands
    shifted_rsh = set(shifts_df["rsh"].tolist())
    table_df["⚑ Shifted"] = table_df["RSH"].apply(lambda r: "↑ Pushed" if r in set(
        pushed["rsh"].tolist()) else ("↓ Pulled" if r in set(pulled["rsh"].tolist()) else
        ("🆕 New" if r in set(_new_since_jan15) else "")))

    def _row_style(row):
        if "Construction" in row["Phase"]: bg = "rgba(255,107,0,0.08)"
        elif "Permitting"  in row["Phase"]: bg = "rgba(245,166,35,0.08)"
        elif "Design"      in row["Phase"]: bg = "rgba(74,144,226,0.08)"
        else: bg = "rgba(155,89,182,0.08)"
        return [f"background-color:{bg}"] * len(row)

    st.dataframe(
        table_df.style.apply(_row_style, axis=1),
        use_container_width=True, hide_index=True,
        height=min(50 + len(table_df) * 35, 500),
    )

    # ── Delay sensitivity ─────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### ⚠️ Opening Date Delay Sensitivity")
    st.caption("Revenue impact per stand if opening slips beyond current estimate")

    sense_df = dff[dff["open_dt"].notna()].copy()
    sense_df = sense_df[sense_df["open_dt"].dt.date >= today].head(20)
    if not sense_df.empty:
        sense_df["Stand"] = sense_df.apply(lambda r: f"{r['city']}, {r['state']} (#{r['store']})", axis=1)
        sense_df["Est. Open"] = sense_df["open"].astype(str)
        sense_df["+4 Wks"]  = f"${4  * AVG_REV_PER_WEEK:,.0f}"
        sense_df["+8 Wks"]  = f"${8  * AVG_REV_PER_WEEK:,.0f}"
        sense_df["+12 Wks"] = f"${12 * AVG_REV_PER_WEEK:,.0f}"
        sense_df["+26 Wks"] = f"${26 * AVG_REV_PER_WEEK:,.0f}"
        st.dataframe(
            sense_df[["Stand","Est. Open","+4 Wks","+8 Wks","+12 Wks","+26 Wks"]],
            use_container_width=True, hide_index=True,
            height=min(50 + len(sense_df) * 35, 400),
        )

    # Revenue Projection and Map removed for performance — can be re-enabled if needed


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
                border-bottom:2px solid #AC2430;margin-bottom:16px;">
      <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAlgCWAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAJJApcDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9U6KKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAoorH8XeLdL8DeHb3XNZuls9OtELySt+gHqT0ApNpK7LhCVSShBXb0SNimGVAcF1B9Ca/N34xft1+MPF+ozW3hSZ/DWkKxEbxc3Egz1Zu2R2A4rwi6+Kfi69vEupvEWoyToSVc3DZBPXvXi1M1pRdoK5+r4Lw6x9emp4mrGm301b+dtPxZ+zYIIyDke1LX5CaJ+0h8SfD20WPi/Uo0BzsaXcp+oNeneGv2/PiRo21L3+z9WizyZ4Cr/8AfQP9KcM1ov4k0Z4nw5zOlrRqQn82n+K/U/S2iviLRv8AgpLCsMa6p4Qd5P4pLW6AH5Ff612Gmf8ABRDwNc7ftmlalaZGTtUPg+nFdccfhpfbPm6vB+eUd8M36NP8mfVtFfOtp+3p8KLjyw97qUDN132LYX6mtmx/bQ+FF/I6L4hMRUZzNCyg/StViqD2mvvPNnw/m9P4sLNf9us9xoryax/aq+Ft+rFfF1lFtOP3zbc/StK0/aM+Gd4GKeNtHXb18y5VP51oq1J7SX3nHLKsfD4qE1/26/8AI9Horg4Pjx8OrmVYovGuiSSMcBVvUyf1q7/wt7wR/wBDXpH/AIFp/jVe0h/MjB4HFR3pS/8AAX/kdfRXKQfFfwbcyiOLxRpUkh6Kt2hJ/Wrn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FRbDTLe3Cp0G2NRx+VdXSABQABgDoBS0AFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABXget/sL/BbxT431XxXrvgy11vVtTmNxcG9YsjOep2jFe+UUAee+Ff2fPhr4ISNdD8EaLpyx/dEVopx+ea7m30yzs8eRaQQY6eXGF/kKs0UAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQB4N+2n4+/wCEI+B+qQQyhL3ViLGNc87W++R9B/OvyzY5JNfWH/BQj4hnXfiPY+GYJN1rpEAdwp481+oPuAo/Ovk6vjcxq+0rtLZaH9ScEZd9QyeE5L3qnvP0e34a/MKKKK8w+/CiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKAJrO3e7uooYxueRwqj1JNfsF8CPAqfDn4UeHdEEflTxWyvcDGMysMufzr83P2S/h3/wsT41aHbTQCewsnN7dKemxP8A7IrX6w19JlNKylVfofhPiRmN50cvi9vefz0X6/eNdgilmOABkmv52/2yvGtr8Qf2nfiHrdjKJrGfVJFgcd0XC/zBr9xP2ufi1H8FP2e/GPif7QLe8is3gsif4rhwVRR+Ofyr+di6uXvLmWeU7pJXLsT3JOTX0J+JEVFFFABXtf7F2mJrH7Ufw6tHcxq+qIdy9RhSf6V4pXvH7C3/ACdn8Nv+wmP/AEBqAP6FqKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAqhrurwaBot9qV1IIre1haZ3Y8AAZq/Xzx+3F8Q18G/Ba802KVVvtbcWioThjH1cj8h+dY1qipU5TfQ9PLMFLMcbSwkN5yS+XV/JH5y/EjxfP488c61r9ycy39y8xGegJ4H5VzVKTkmkr4FtybbP7Mp040oRpwVkkkvRBRRRSNAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiirOm2MupahbWkC75ppFjRfUk4AoE2lqz73/AOCdnw6/s7wrrPjC4iXzb+X7JbP38tCd/wD49j8q+xq4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AUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAcl8WvDS+MPhp4k0dgCLqykXB9QMj9RX41TxmGZkYYZTgg+tfuBJGssbIwyrAgj1Ffl1+1v8A9Q+FXj681G0tnk8N6nK09tOi/LEScmNvQjPHrXz+bUXKMaqW25+0eHGZU6VStgKkrOdpR82tGvW1vuPAKKXpQqljgAk+1fNH72GM19wfsUfsurKLbx94rssp9/TLOdfvekrA/p+dcj+yT+yPceOry28WeLrV7fw9C4ktrSQYa8YHIJHZP51+iEMMdtDHFEixxRqFRFGAoHAAFfQZfgrtVqq9F+p+K8a8VqnGWWYCXvPScl0/urz79tu4+iiivpT8GCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKztf8AD2m+KdKn03V7GDUbCddslvcIGVh9K0aKTSejKjKUJKUXZo+ZPE/7APw71m4efTpL/SGd9zRxy70HsoI4FdF4B/Ys+GvgW/ivzp8us3kf3TqD+ZGD2ITGM17zRXKsJQT5lBXPoanEecVaXsZ4mbj6/ruMiiSGNY40WONRhVUYAHoBT6KK6z5wKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigD/2Q==" style="height:40px;width:auto;display:inline-block;vertical-align:middle;" />
      <div style="font-family:'Bebas Neue',sans-serif;font-size:18px;letter-spacing:3px;
                  color:#595959;text-transform:uppercase;">Financial Performance Dashboard</div>
      <div style="margin-left:auto;font-family:'DM Mono',monospace;font-size:17px;color:#C5BEBE;">
        FY2025–2026 · 15 Periods · Confidential
      </div>
    </div>""")

    # Data info line
    base_keys = sorted([p["period_key"] for p in dash.get("period_summaries", [])])
    if base_keys:
        st.caption(f"📊 {len(base_keys)} periods · {base_keys[0]} – {base_keys[-1]} · {len(dash.get('stand_records', []))} stand records")

    # Tabs
    tab_names = [
        "📊 CEO Snapshot",
        "🏠 Overview",
        "📈 Period Comparison",
        "🗺 Regions & Stands",
        "💡 Wins & Opportunities",
        "⚡ Utilities & R&M",
        "🏗️ Pipeline (Draft)",
        "🔮 Forecast (Draft)",
        "⏱️ Speed of Service",
    ]
    tabs = st.tabs(tab_names)

    with tabs[0]: tab_ceo(dash)
    with tabs[1]: tab_overview(dash)
    with tabs[2]: tab_comparison(dash)
    with tabs[3]: tab_regions(dash)
    with tabs[4]: tab_insights(dash)
    with tabs[5]: tab_utilities(dash)
    with tabs[6]: tab_pipeline(dash)
    with tabs[7]: tab_forecast(dash)
    with tabs[8]: tab_sos(dash)


main()
