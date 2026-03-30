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

    # Quarter presets
    q_presets = {"Q1 (P1–P3)": [1, 2, 3], "Q2 (P4–P6)": [4, 5, 6],
                 "Q3 (P7–P9)": [7, 8, 9], "Q4 (P10–P13)": [10, 11, 12, 13]}

    sel_col, btn_col = st.columns([3, 2])
    with sel_col:
        selected_labels = st.multiselect(label, [l for l, _ in all_labels],
                                         default=[all_labels[0][0]], key=key)
    with btn_col:
        st.caption("Quick select:")
        bcols = st.columns(4)
        for i, (q_name, p_nums) in enumerate(q_presets.items()):
            with bcols[i]:
                if st.button(q_name, key=f"{key}_{q_name}", use_container_width=True):
                    # Find matching periods for the latest year in the data
                    latest_year = periods_df["year"].max()
                    matching = []
                    for _, row in periods_df.iterrows():
                        if row["year"] == latest_year and row["period_num"] in p_nums:
                            matching.append(row["label"])
                    if matching:
                        st.session_state[key] = matching

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
                   "Water_Sewer", "Waste_Removal", "RM_Equipment", "RM_Building"]]
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
        dollar_cols = [c for c in rdf.columns if c in ["net_sales", "ebitda"]]
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

def get_stands_df(dash, period_key=None):
    df = pd.DataFrame(dash["stand_records"])
    if period_key and "_Q" in period_key:
        # Build quarterly stand data on the fly
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

# ─────────────────────────────────────────────
# SIDEBAR: Minimal branding only
# ─────────────────────────────────────────────
def render_sidebar():
    st.html("""
    <div style="padding:12px 4px;">
      <div style="background:#AC2430;color:white;font-family:'Bebas Neue',sans-serif;
                  font-size:26px;letter-spacing:2px;padding:8px 14px;border-radius:8px;
                  text-align:center;margin-bottom:12px;">7BREW</div>
      <div style="font-family:'DM Mono',monospace;font-size:11px;color:#C5BEBE;
                  text-align:center;letter-spacing:1px;text-transform:uppercase;">
        Financial Performance Dashboard
      </div>
      <hr style="border:none;border-top:1px solid #e2e4e9;margin:16px 0;">
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#c0c4cc;
                  text-align:center;letter-spacing:1px;">
        CONFIDENTIAL · INTERNAL USE ONLY
      </div>
    </div>""")

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
            if ratio >= 1 + tolerance:
                return f"▲ AHEAD  ({ratio*100:.0f}% of pace)", GREEN
            elif ratio >= 1 - tolerance:
                return f"→ ON PACE ({ratio*100:.0f}% of pace)", BLUE
            else:
                return f"▼ BEHIND  ({ratio*100:.0f}% of pace)", RED

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
                fig_e.update_layout(
                    yaxis=dict(ticksuffix="%", tickformat=".1f",
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
                "title": f"🟢 EBITDA Momentum: +{ebitda_trend*100:.0f}bps period-over-period",
                "body": f"System EBITDA improved from {_fmt_p(filtered_df['ebitda_pct'].iloc[-2])} to {_fmt_p(filtered_df['ebitda_pct'].iloc[-1])}. "
                        f"Protect this by maintaining current labor scheduling and vendor pricing discipline.",
                "cls": "win", "tag_cls": "green",
            })
        elif ebitda_trend < -0.015:
            seasonal_alerts.append({
                "title": f"🔴 EBITDA Slipping: {ebitda_trend*100:.0f}bps period-over-period",
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
            agg_dict = {"net_sales": "sum", "ebitda": "sum"}
            if "stands" in reg_all.columns:
                agg_dict["stands"] = "mean"
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

    if not reg_df.empty:
        # ── Net Sales by Region ──────────────────────────────────────────────
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

        # ── EBITDA % by Region ───────────────────────────────────────────────
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

        # ── COGs % by Region ─────────────────────────────────────────────────
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

        # ── Labor % by Region ────────────────────────────────────────────────
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

    # ── Cost Structure (donut) + P&L Bridge (waterfall) side by side ─────────
    c_left, c_right = st.columns(2)
    with c_left:
        other = max(0, 1 - ps["cogs_pct"] - ps["labor_pct"] - ps["rent_pct"] - ps["ebitda_pct"])
        fig4 = go.Figure(go.Pie(
            labels=["COGS", "Total Labor", "Rent", "Other OpEx", "EBITDA"],
            values=[ps["cogs_pct"], ps["labor_pct"], ps["rent_pct"], other, ps["ebitda_pct"]],
            hole=0.55,
            marker_colors=[BLUE, AMBER, MID, MUTED, GREEN],
            textinfo="label+percent",
            textfont=dict(size=11, family="DM Mono"),
        ))
        brew_fig(fig4, height=360)
        fig4.update_layout(title_text="COST STRUCTURE",
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig4, config={"displayModeBar": False}, use_container_width=True)

    with c_right:
        # P&L Bridge: shows how Net Sales flows down to EBITDA
        bridge_labels = ["Net Sales", "− COGS", "− Labor", "− Rent", "− Other OpEx", "EBITDA"]
        bridge_values = [
             100,
            -ps["cogs_pct"]  * 100,
            -ps["labor_pct"] * 100,
            -ps["rent_pct"]  * 100,
            -other           * 100,
             ps["ebitda_pct"]* 100,
        ]
        bridge_measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
        fig5 = go.Figure(go.Waterfall(
            orientation="v",
            measure=bridge_measure,
            x=bridge_labels,
            y=bridge_values,
            text=[f"{abs(v):.1f}%" for v in bridge_values],
            textposition="outside",
            connector=dict(line=dict(color=BORDER, width=1)),
            increasing=dict(marker_color=BLUE),
            decreasing=dict(marker_color=RED),
            totals=dict(marker_color=GREEN),
        ))
        brew_fig(fig5, height=360)
        fig5.update_layout(
            title_text="P&L BRIDGE",
            yaxis=dict(ticksuffix="%", range=[0, 115]),
            showlegend=False,
        )
        st.plotly_chart(fig5, config={"displayModeBar": False}, use_container_width=True)

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
    section("PERIOD COMPARISON", "Compare any two periods across all key metrics")

    all_options = [(row["label"], row["period_key"]) for _, row in periods_df.iloc[::-1].iterrows()]
    label_to_key = {l: pk for l, pk in all_options}

    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        lbl_a = st.selectbox("Period A", [l for l, _ in all_options], key="cmp_a")
    with c2:
        st.html('<div style="text-align:center;font-family:Bebas Neue;font-size:24px;color:#595959;padding-top:28px;">VS</div>')
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
    render_table(cmp_df)

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
        fig.update_layout(title_text="AVG SALES COMPARISON",
                          yaxis=dict(tickprefix="$", tickformat=",.0f"), showlegend=False)
        st.plotly_chart(fig, config={"displayModeBar": False})

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
            fig2.update_layout(title_text="EBITDA % BY REGION",
                               barmode="group", yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig2, config={"displayModeBar": False})

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
                           xaxis=dict(ticksuffix="%"), showlegend=False)
        st.plotly_chart(fig3, config={"displayModeBar": False})
    with col4:
        fig4 = go.Figure(go.Histogram(x=sa["Total_COGS_pct"] * 100, nbinsx=10,
                                       marker_color=BLUE, opacity=0.8))
        brew_fig(fig4, height=240)
        fig4.update_layout(title_text=f"COGS % DISTRIBUTION — {psA['label']}",
                           xaxis=dict(ticksuffix="%"), showlegend=False)
        st.plotly_chart(fig4, config={"displayModeBar": False})


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

    # ── Ramp-Up Tracker ──
    if n_ramping > 0:
        st.html('<hr class="brew">')
        section("RAMP-UP TRACKER", f"{n_ramping} stands in first 6 months — expected higher labor & COGS, lower sales")
        ramp_display = ramping[["Stand", "Net_Sales", "Total_Labor_pct", "Total_COGS_pct", "Store_EBITDA_pct"]].copy()
        if "Age_Bucket" in ramping.columns:
            ramp_display.insert(1, "Stage", ramping["Age_Bucket"])
        ramp_display["Net_Sales"] = ramp_display["Net_Sales"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        for col in ["Total_Labor_pct", "Total_COGS_pct", "Store_EBITDA_pct"]:
            if col in ramp_display.columns:
                ramp_display[col] = ramp_display[col].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
        ramp_display.columns = [c.replace("_pct", " %").replace("Total_", "").replace("Store_", "").replace("Net_", "") for c in ramp_display.columns]
        render_table(ramp_display.reset_index(drop=True))


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
        st.html('<div style="font-family:Bebas Neue,sans-serif;font-size:18px;letter-spacing:2px;color:#AC2430;margin-bottom:10px;">🚨 CRITICAL ISSUES</div>')

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
      <div style="background:#AC2430;color:white;font-family:'Bebas Neue',sans-serif;
                  font-size:22px;letter-spacing:1px;padding:4px 12px;border-radius:6px;">7BREW</div>
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
