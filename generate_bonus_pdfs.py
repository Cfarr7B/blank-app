#!/usr/bin/env python3
"""
generate_bonus_pdfs.py — 7BREW Stand Manager Bonus Report Generator
====================================================================
Reads a bonus Excel workbook, skips any row where Column J (Bonus Eligible)
= "N", and produces one self-contained HTML file per eligible manager.
Each HTML auto-prints when opened in a browser — save as PDF from the
print dialog.

USAGE
-----
    python generate_bonus_pdfs.py  bonus_data.xlsx  [output_folder]

    • bonus_data.xlsx  – your bonus calculation spreadsheet
    • output_folder    – where HTML files are written (default: ./bonus_reports)

EXPECTED EXCEL COLUMNS (header names, case-insensitive, any order)
-------------------------------------------------------------------
Required
  Store #          – e.g. 000129
  City             – e.g. Odessa
  State            – e.g. TX
  Stand            – e.g. 1  (the stand number suffix: "000129 Odessa, TX - 1")
  Stand Manager    – manager's full name
  Bonus Eligible   – Y = generate PDF,  N = skip entirely  ← Column J by default

Bonus metrics (pairs: Actual + Goal)
  Net Sales        – actual net sales dollars
  Net Sales Goal   – goal net sales dollars
  COGS %           – actual COGS as a decimal (0.285) or percent (28.5)
  COGS Goal        – goal COGS as a decimal or percent
  Labor %          – actual hourly labor as decimal or percent
  Labor Goal       – goal labor as decimal or percent
  EBITDA %         – actual SL EBITDA as decimal or percent
  EBITDA Goal      – goal SL EBITDA as decimal or percent

Optional
  Regional Manager – RM name  (blank if not present)
  Director         – Director of Operations name
  Period           – e.g. P3-2026 (used in the report header)

Bonus rule (can be overridden at the top of this file)
  BONUS_PER_KPI     = $250 per KPI metric hit
  STAND_MGR_BONUS   = sum of all KPI bonuses (or $0 if ANY metric missed)
  STRETCH_THRESHOLD = $150,000 net sales required for stretch bonus
  STRETCH_PCT       = 1% of Store EBITDA dollars

If COGS and Labor are "lower is better", hitting = Actual ≤ Goal.
If Net Sales and EBITDA are "higher is better", hitting = Actual ≥ Goal.
"""

import os
import sys
import re
import math
import base64
from pathlib import Path

import openpyxl

# ─── Bonus rules ────────────────────────────────────────────────────────────
BONUS_PER_KPI      = 250.0      # $ paid per KPI metric hit
STRETCH_THRESHOLD  = 150_000.0  # net sales required for stretch bonus
STRETCH_PCT        = 0.01       # 1 % of EBITDA dollars
ALL_OR_NOTHING     = False      # True → SM Bonus = $0 unless ALL 4 KPIs hit

# ─── Column aliases (all lower-case) ────────────────────────────────────────
_ALIASES = {
    "store":            ["store #", "store#", "store number", "store num", "storeno"],
    "city":             ["city"],
    "state":            ["state"],
    "stand":            ["stand", "stand #", "stand#", "stand num", "unit"],
    "manager":          ["stand manager", "manager", "manager name", "sm", "sm name"],
    "rm":               ["regional manager", "rm", "region manager", "reg manager"],
    "director":         ["director", "director of operations", "doo", "do"],
    "period":           ["period", "period name", "bonus period", "p period"],
    "eligible":         ["bonus eligible", "eligible", "eligibility", "bonus eligibility",
                         "bonus elig", "elig", "column j", "col j"],
    # ── metric actuals
    "net_sales":        ["net sales", "net sales actual", "sales", "sales actual", "revenue"],
    "cogs_pct":         ["cogs %", "cogs%", "cogs pct", "cogs actual", "cogs"],
    "labor_pct":        ["labor %", "labor%", "hourly labor %", "hourly labor%",
                         "labor pct", "labor actual", "hourly labor"],
    "ebitda_pct":       ["ebitda %", "ebitda%", "sl ebitda %", "sl ebitda%",
                         "ebitda pct", "ebitda actual", "store ebitda %", "store ebitda%"],
    # ── metric goals
    "net_sales_goal":   ["net sales goal", "sales goal", "revenue goal", "net sales target"],
    "cogs_goal":        ["cogs goal", "cogs target", "cogs % goal", "cogs% goal"],
    "labor_goal":       ["labor goal", "labor target", "labor % goal", "labor% goal",
                         "hourly labor goal", "hourly labor target"],
    "ebitda_goal":      ["ebitda goal", "ebitda target", "ebitda % goal", "ebitda% goal",
                         "sl ebitda goal", "sl ebitda target"],
    # ── dollar EBITDA (used for stretch calc if pct form not sufficient)
    "ebitda_dollars":   ["store ebitda", "ebitda $", "ebitda dollars", "ebitda dollar",
                         "sl ebitda $", "sl ebitda dollars"],
}

# ─── Logo embedding ──────────────────────────────────────────────────────────
def _logo_b64(script_dir: Path) -> str:
    for name in ["ICON LOGO.jpg", "ICON LOGO.png", "logo.jpg", "logo.png"]:
        p = script_dir / name
        if p.exists():
            ext = "jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "png"
            return f"data:image/{ext};base64," + base64.b64encode(p.read_bytes()).decode()
    return ""

# ─── Helpers ─────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())

def _pct(v) -> float:
    """Return value as a fraction (0-1). Handles 0.285 and 28.5 both → 0.285."""
    try:
        f = float(v)
        return f / 100.0 if abs(f) > 1.5 else f
    except (TypeError, ValueError):
        return 0.0

def _dollar(v) -> float:
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return 0.0

def _fmt_dollar(v: float) -> str:
    return f"${v:,.2f}"

def _fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"

def _hit_badge(hit: bool) -> str:
    color = "#27ae60" if hit else "#e74c3c"
    letter = "Y" if hit else "N"
    return (f"<span style='color:{color};font-weight:700;font-size:15px;'>{letter}</span>")

# ─── Excel column mapper ──────────────────────────────────────────────────────
def _map_columns(headers: list) -> dict:
    """Map logical field names → column index (0-based)."""
    norm_headers = [_norm(h) for h in headers]
    mapping = {}
    for field, aliases in _ALIASES.items():
        for idx, nh in enumerate(norm_headers):
            if nh in aliases:
                mapping[field] = idx
                break
    return mapping

# ─── HTML template ───────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>7BREW Bonus — {store} {city} {state} - {stand}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600;700&family=DM+Mono&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'DM Sans',sans-serif;background:#fff;color:#222;
        padding:28px 40px;max-width:820px;margin:0 auto;font-size:14px}}
  /* ── Header ── */
  .hdr{{display:flex;flex-direction:column;align-items:center;
         border-bottom:3px solid #AC2430;padding-bottom:14px;margin-bottom:18px}}
  .hdr img{{height:62px;width:auto;margin-bottom:8px}}
  .hdr h1{{font-family:'Bebas Neue',sans-serif;font-size:30px;letter-spacing:1px;
            color:#222;margin:0}}
  /* ── People table ── */
  .people{{width:100%;border-collapse:collapse;margin-bottom:6px}}
  .people th{{font-size:10px;letter-spacing:1px;text-transform:uppercase;
               color:#888;padding:4px 8px;text-align:center;font-weight:600}}
  .people td{{font-size:14px;font-weight:700;padding:6px 8px;text-align:center;
               border-top:1px solid #e0e0e0}}
  .period-line{{text-align:center;font-size:12px;color:#666;margin-bottom:16px}}
  /* ── Big bonus boxes ── */
  .bonus-row{{display:flex;gap:16px;margin:18px 0}}
  .bonus-box{{flex:1;border:1px solid #ddd;border-radius:6px;padding:18px 16px;
               text-align:center}}
  .bonus-box .label{{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;
                      color:#888;font-weight:600;margin-bottom:8px}}
  .bonus-box .amount{{font-family:'Bebas Neue',sans-serif;font-size:42px;color:#AC2430;
                       line-height:1}}
  /* ── Section headers ── */
  .section-hdr{{background:#333;color:#fff;font-family:'Bebas Neue',sans-serif;
                 font-size:14px;letter-spacing:1.5px;padding:8px 12px;
                 margin:20px 0 0 0;border-radius:3px 3px 0 0}}
  /* ── Performance table ── */
  table.perf{{width:100%;border-collapse:collapse;margin-bottom:20px}}
  table.perf th{{font-size:11px;letter-spacing:.8px;text-transform:uppercase;
                  background:#f5f5f5;padding:8px 10px;border:1px solid #ddd;
                  text-align:center;font-weight:700;color:#444}}
  table.perf th:first-child{{text-align:left}}
  table.perf td{{padding:9px 10px;border:1px solid #e8e8e8;text-align:center;
                  font-size:13px;font-family:'DM Mono',monospace}}
  table.perf td:first-child{{text-align:left;font-family:'DM Sans',sans-serif;
                               font-size:13px}}
  table.perf tr:hover td{{background:#fffaf0}}
  .bonus-amt{{color:#27ae60;font-weight:700}}
  .miss-amt{{color:#999}}
  /* ── How it works table ── */
  table.how{{width:100%;border-collapse:collapse}}
  table.how th{{font-size:11px;letter-spacing:.8px;text-transform:uppercase;
                 background:#f5f5f5;padding:8px 10px;border:1px solid #ddd;
                 text-align:center;font-weight:700;color:#444}}
  table.how th:first-child{{width:140px;text-align:left}}
  table.how td{{padding:9px 10px;border:1px solid #e8e8e8;font-size:13px;
                 vertical-align:top}}
  table.how td:first-child{{font-weight:600}}
  /* ── Footer ── */
  .footer{{font-size:10px;color:#aaa;text-align:center;
            margin-top:24px;border-top:1px solid #eee;padding-top:8px}}
  /* ── Print ── */
  @media print{{
    @page{{size:letter portrait;margin:.5in}}
    body{{padding:0;max-width:100%}}
    .bonus-box .amount{{color:#AC2430!important;-webkit-print-color-adjust:exact;
                         print-color-adjust:exact}}
    .section-hdr{{background:#333!important;-webkit-print-color-adjust:exact;
                   print-color-adjust:exact}}
    table.perf th,table.how th{{background:#f5f5f5!important;
      -webkit-print-color-adjust:exact;print-color-adjust:exact}}
  }}
</style>
</head>
<body>
<div class="hdr">
  {logo_tag}
  <h1>Stand Manager Bonus Results</h1>
</div>

<table class="people">
  <tr>
    <th>Stand Manager</th>
    <th>Regional Manager</th>
    <th>Director of Operations</th>
  </tr>
  <tr>
    <td>{manager}</td>
    <td>{rm}</td>
    <td>{director}</td>
  </tr>
</table>
<p class="period-line">{period} &nbsp;·&nbsp; {store} {city}, {state} - {stand}</p>

<div class="bonus-row">
  <div class="bonus-box">
    <div class="label">Stand Manager Bonus</div>
    <div class="amount">{sm_bonus_fmt}</div>
  </div>
  <div class="bonus-box">
    <div class="label">Stretch Bonus</div>
    <div class="amount">{stretch_fmt}</div>
  </div>
</div>

<div class="section-hdr">Performance Detail</div>
<table class="perf">
  <tr>
    <th>Metric</th><th>Actual</th><th>Goal</th><th>Hit?</th><th>Bonus</th>
  </tr>
  {perf_rows}
</table>

<div class="section-hdr">How Your Bonus Works</div>
<table class="how">
  <tr>
    <th>Metric</th><th>What It Measures</th>
  </tr>
  <tr><td>Net Sales</td>
    <td>Total revenue your stand brought in — higher is better</td></tr>
  <tr><td>COGS %</td>
    <td>Cost of goods as % of sales (product waste &amp; usage) — lower is better</td></tr>
  <tr><td>Hourly Labor %</td>
    <td>Labor cost as % of sales — keep scheduling efficient — lower is better</td></tr>
  <tr><td>SL EBITDA %</td>
    <td>Store-level profit margin — the bottom line — higher is better</td></tr>
  <tr><td>Stretch Bonus</td>
    <td>Exceed ${stretch_threshold:,.0f} in sales and hit your KPIs — earn {stretch_pct:.0f}% of your EBITDA</td></tr>
</table>

<div class="footer">7 Crew Enterprises · Confidential · {period} Bonus Results</div>
<script>window.onload = function(){{ window.print(); }}</script>
</body>
</html>"""

# ─── Per-row bonus calculator ─────────────────────────────────────────────────
def calc_bonus(row: dict) -> dict:
    """
    Returns dict with all bonus amounts and hit flags.
    row keys: net_sales, net_sales_goal, cogs_pct, cogs_goal,
              labor_pct, labor_goal, ebitda_pct, ebitda_goal,
              ebitda_dollars (optional)
    """
    ns     = _dollar(row.get("net_sales", 0))
    ns_g   = _dollar(row.get("net_sales_goal", 0))
    cogs   = _pct(row.get("cogs_pct", 0))
    cogs_g = _pct(row.get("cogs_goal", 0))
    lab    = _pct(row.get("labor_pct", 0))
    lab_g  = _pct(row.get("labor_goal", 0))
    ebi    = _pct(row.get("ebitda_pct", 0))
    ebi_g  = _pct(row.get("ebitda_goal", 0))

    hit_ns   = ns   >= ns_g   if ns_g   > 0 else False
    hit_cogs = cogs <= cogs_g if cogs_g > 0 else False   # lower is better
    hit_lab  = lab  <= lab_g  if lab_g  > 0 else False   # lower is better
    hit_ebi  = ebi  >= ebi_g  if ebi_g  > 0 else False

    all_hit = hit_ns and hit_cogs and hit_lab and hit_ebi

    if ALL_OR_NOTHING:
        sm_ns   = BONUS_PER_KPI if all_hit else 0.0
        sm_cogs = BONUS_PER_KPI if all_hit else 0.0
        sm_lab  = BONUS_PER_KPI if all_hit else 0.0
        sm_ebi  = BONUS_PER_KPI if all_hit else 0.0
    else:
        sm_ns   = BONUS_PER_KPI if hit_ns   else 0.0
        sm_cogs = BONUS_PER_KPI if hit_cogs else 0.0
        sm_lab  = BONUS_PER_KPI if hit_lab  else 0.0
        sm_ebi  = BONUS_PER_KPI if hit_ebi  else 0.0

    sm_total = sm_ns + sm_cogs + sm_lab + sm_ebi

    # Stretch bonus: net sales > threshold AND any KPI hit
    ebi_dollars = _dollar(row.get("ebitda_dollars", 0))
    if ebi_dollars == 0 and ns > 0 and ebi > 0:
        ebi_dollars = ns * ebi   # derive from pct if not given directly
    stretch_hit = (ns >= STRETCH_THRESHOLD)
    stretch_amt = ebi_dollars * STRETCH_PCT if stretch_hit else 0.0

    return {
        "ns": ns, "ns_g": ns_g, "hit_ns": hit_ns, "sm_ns": sm_ns,
        "cogs": cogs, "cogs_g": cogs_g, "hit_cogs": hit_cogs, "sm_cogs": sm_cogs,
        "lab": lab, "lab_g": lab_g, "hit_lab": hit_lab, "sm_lab": sm_lab,
        "ebi": ebi, "ebi_g": ebi_g, "hit_ebi": hit_ebi, "sm_ebi": sm_ebi,
        "sm_total": sm_total, "all_hit": all_hit,
        "stretch_hit": stretch_hit, "stretch_amt": stretch_amt,
        "ebi_dollars": ebi_dollars,
    }

# ─── HTML builder ─────────────────────────────────────────────────────────────
def build_html(record: dict, logo_uri: str) -> str:
    b = calc_bonus(record)

    logo_tag = (f"<img src='{logo_uri}' alt='7BREW' "
                f"style='height:60px;width:auto;margin-bottom:8px'>"
                if logo_uri else "")

    def _perf_row(metric, actual_fmt, goal_fmt, hit, bonus_amt):
        ba_cls = "bonus-amt" if bonus_amt > 0 else "miss-amt"
        return (f"<tr><td>{metric}</td>"
                f"<td>{actual_fmt}</td>"
                f"<td>{goal_fmt}</td>"
                f"<td>{_hit_badge(hit)}</td>"
                f"<td class='{ba_cls}'>{_fmt_dollar(bonus_amt)}</td></tr>")

    stretch_note = ""
    if b["stretch_hit"] and b["ebi_dollars"] > 0:
        stretch_note = (f" <small style='color:#888;font-size:11px;'>"
                        f"({STRETCH_PCT*100:.0f}% of {_fmt_dollar(b['ebi_dollars'])})"
                        f"</small>")

    perf_rows = (
        _perf_row("Net Sales",
                  _fmt_dollar(b["ns"]), _fmt_dollar(b["ns_g"]),
                  b["hit_ns"], b["sm_ns"]) +
        _perf_row("COGS %",
                  _fmt_pct(b["cogs"]), _fmt_pct(b["cogs_g"]),
                  b["hit_cogs"], b["sm_cogs"]) +
        _perf_row("Hourly Labor %",
                  _fmt_pct(b["lab"]), _fmt_pct(b["lab_g"]),
                  b["hit_lab"], b["sm_lab"]) +
        _perf_row("SL EBITDA %",
                  _fmt_pct(b["ebi"]), _fmt_pct(b["ebi_g"]),
                  b["hit_ebi"], b["sm_ebi"]) +
        f"<tr><td>Stretch Bonus</td>"
        f"<td>{_fmt_dollar(b['ns'])}</td>"
        f"<td>{_fmt_dollar(STRETCH_THRESHOLD)}</td>"
        f"<td>{_hit_badge(b['stretch_hit'])}</td>"
        f"<td class='{'bonus-amt' if b['stretch_amt']>0 else 'miss-amt'}'>"
        f"{_fmt_dollar(b['stretch_amt'])}{stretch_note}</td></tr>"
    )

    store   = str(record.get("store", "")).zfill(6) if record.get("store") else ""
    city    = str(record.get("city", ""))
    state   = str(record.get("state", ""))
    stand   = str(record.get("stand", "1"))
    manager = str(record.get("manager", ""))
    rm      = str(record.get("rm", ""))
    director= str(record.get("director", ""))
    period  = str(record.get("period", ""))

    return HTML_TEMPLATE.format(
        logo_tag         = logo_tag,
        store            = store,
        city             = city,
        state            = state,
        stand            = stand,
        manager          = manager,
        rm               = rm,
        director         = director,
        period           = period,
        sm_bonus_fmt     = _fmt_dollar(b["sm_total"]),
        stretch_fmt      = _fmt_dollar(b["stretch_amt"]),
        perf_rows        = perf_rows,
        stretch_threshold= STRETCH_THRESHOLD,
        stretch_pct      = STRETCH_PCT * 100,
    )

# ─── Excel reader ─────────────────────────────────────────────────────────────
def _col_val(row_values: list, idx) -> str:
    if idx is None or idx >= len(row_values):
        return ""
    v = row_values[idx]
    return "" if v is None else str(v)

def read_bonus_excel(path: str) -> list[dict]:
    """
    Read the bonus Excel and return a list of row dicts.
    Skips rows where the 'eligible' column = 'N' (case-insensitive).
    Also skips rows where 'eligible' column = 'n'.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)

    # Find header row — first row that has at least 5 non-empty cells
    header_row = None
    col_map    = {}
    data_rows  = []

    for raw_row in rows_iter:
        non_empty = [c for c in raw_row if c is not None and str(c).strip()]
        if len(non_empty) >= 5 and header_row is None:
            # Try to map columns
            trial_map = _map_columns([str(c) if c is not None else "" for c in raw_row])
            if "eligible" in trial_map or "manager" in trial_map:
                header_row = raw_row
                col_map    = trial_map
                continue
        if header_row is not None and any(c is not None for c in raw_row):
            data_rows.append(list(raw_row))

    if not header_row:
        raise ValueError(
            "Could not find a header row. Make sure row 1 contains column names "
            "like 'Stand Manager', 'Bonus Eligible', 'Net Sales', etc."
        )

    # Fall back: if 'eligible' not mapped, assume Column J (index 9)
    if "eligible" not in col_map:
        print("⚠️  'Bonus Eligible' column not found by name — assuming Column J (index 9).")
        col_map["eligible"] = 9

    records = []
    skipped_n = 0
    skipped_blank = 0

    for rv in data_rows:
        elig_raw = _col_val(rv, col_map.get("eligible")).strip().upper()
        if elig_raw == "N":
            skipped_n += 1
            continue
        if elig_raw not in ("Y", "YES", "1", "TRUE"):
            # Skip blank/header-like rows silently
            skipped_blank += 1
            continue

        rec = {}
        for field in _ALIASES:
            idx = col_map.get(field)
            rec[field] = _col_val(rv, idx) if idx is not None else ""

        records.append(rec)

    print(f"  ✅ Eligible managers found : {len(records)}")
    print(f"  ⛔ Skipped (Column J = N)  : {skipped_n}")
    if skipped_blank:
        print(f"  ⬜ Skipped (blank/other)   : {skipped_blank}")

    return records

# ─── Safe filename ────────────────────────────────────────────────────────────
def _safe_name(s: str) -> str:
    return re.sub(r"[^\w\-]", "_", s)

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    excel_path = sys.argv[1]
    out_dir    = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("bonus_reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    script_dir = Path(__file__).parent
    logo_uri   = _logo_b64(script_dir)

    print(f"\n📂 Reading: {excel_path}")
    records = read_bonus_excel(excel_path)

    if not records:
        print("\n⚠️  No eligible managers found. Nothing to generate.")
        return

    print(f"\n🖨️  Generating {len(records)} bonus report(s) → {out_dir}/\n")

    for rec in records:
        store  = str(rec.get("store", "")).strip().zfill(6) if rec.get("store") else "XXXXX"
        city   = str(rec.get("city", "")).strip().replace(" ", "_")
        state  = str(rec.get("state", "")).strip()
        stand  = str(rec.get("stand", "1")).strip()
        period = str(rec.get("period", "BONUS")).strip().replace(" ", "")

        fname = f"{period}_Bonus_{store}_{city}_{state}_-_{stand}.html"
        out_path = out_dir / _safe_name(fname)

        html = build_html(rec, logo_uri)
        out_path.write_text(html, encoding="utf-8")
        manager = rec.get("manager", "Unknown")
        print(f"  ✔  {fname}  ({manager})")

    print(f"\n✅ Done! Open any HTML file in Chrome and print → Save as PDF.\n")


if __name__ == "__main__":
    main()
