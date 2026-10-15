"""Build kpi_goals.json — per-stand, per-period goals for the Overview scorecard.

Source: a WoW Report workbook, sheet 'Weekly Goals' (one row per stand, one column per week):
  row 5 = end-of-week date, row 7 = period ("P10"), row 9 = year; row 12 = section headers
  Net Sales (weekly $, summed to the period), COGS % and Hourly Labor % (one rate per period).

Usage:  python build_kpi_goals.py "<path to WoW Report.xlsx>"   →  kpi_goals.json (next to this file)
Re-run when a newer WoW report changes goals.
"""
import json
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def main(wow_path):
    wb = openpyxl.load_workbook(wow_path, read_only=True, data_only=True)
    g = list(wb["Weekly Goals"].iter_rows(values_only=True))
    per, yr, hdr = g[6], g[8], g[11]
    starts = {name: i for i, name in enumerate(hdr) if name in ("Net Sales", "COGS %", "Hourly Labor %", "SOS Times")}
    ns0, cg0, hr0, end = starts["Net Sales"], starts["COGS %"], starts["Hourly Labor %"], starts["SOS Times"]

    def period_cols(a, b):
        out = {}
        for c in range(a, b):
            if per[c] and yr[c]:
                out.setdefault(f"{int(yr[c])}_{per[c]}", []).append(c)
        return out

    NS, CG, HR = period_cols(ns0, cg0), period_cols(cg0, hr0), period_cols(hr0, end)
    periods = {}
    for r in g[12:]:
        sid = r[3]
        if not isinstance(sid, int):
            continue
        for pk, cols in NS.items():
            ns = [r[c] for c in cols if num(r[c])]
            ns_goal = round(sum(ns), 2) if ns and sum(ns) > 0 else None
            cogs = next((r[c] for c in CG.get(pk, []) if num(r[c]) and r[c] > 0), None)
            hrly = next((r[c] for c in HR.get(pk, []) if num(r[c]) and r[c] > 0), None)
            if ns_goal or cogs or hrly:
                periods.setdefault(pk, {})[str(sid)] = {
                    "ns": ns_goal,
                    "cogs": round(cogs, 4) if cogs else None,
                    "hourly": round(hrly, 4) if hrly else None,
                }
    key = lambda pk: (int(pk.split("_")[0]), int(pk.split("_P")[1]))
    out = {"_source": f"{os.path.basename(wow_path)} > Weekly Goals",
           "periods": {pk: dict(sorted(periods[pk].items(), key=lambda kv: int(kv[0])))
                       for pk in sorted(periods, key=key)}}
    with open(os.path.join(HERE, "kpi_goals.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    for pk, v in out["periods"].items():
        print(pk, len(v), "stands", f"NS goal ${sum(x['ns'] or 0 for x in v.values()):,.0f}")


if __name__ == "__main__":
    main(sys.argv[1])
