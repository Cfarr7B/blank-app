"""Apply a weekly 7Crew Pipeline Report to pipeline_data.json (+ stand_meta.json for stands that opened).

Usage:
    python tools/apply_pipeline_report.py <report.xlsx | report.txt> <report date YYYY-MM-DD> [--dry-run]

The input is either the .xlsx from Drew's "INTERNAL Pipeline Email" or the plain-text dump of that
attachment (tab-separated, dates as Excel serial numbers) that the Microsoft 365 connector returns.
Prints a JSON summary of what changed (opened / removed / added / moved) for the update notification.
"""
import json, sys, re, datetime as dt, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = {"phase": "Project Phase", "store": "Store #", "address": "Address", "city": "City", "state": "State",
          "permit_sub": "Permit Submission", "permit_appr": "Permit Approval Date", "cs": "Construction Start",
          "bd": "Building Drop Date", "open": "Open Date", "notes": "Notes for Corporate", "gc": "General Contractor"}
EPOCH = dt.date(1899, 12, 30)


def md(x):
    """Any report date value → 'M/D/YY' (as stored in pipeline_data.json); text that isn't a date passes through."""
    if isinstance(x, dt.datetime):
        x = x.date()
    if isinstance(x, dt.date):
        return f"{x.month}/{x.day}/{x.year % 100}"
    s = "" if x is None else str(x).strip()
    if re.fullmatch(r"\d{5}(\.\d+)?", s):
        return md(EPOCH + dt.timedelta(days=int(float(s))))
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s)
    if m:
        y = int(m[3]) % 100
        return f"{int(m[1])}/{int(m[2])}/{y}"
    return s


def pdate(s):
    m, d, y = s.split("/")
    return dt.date(2000 + int(y), int(m), int(d))


def read_report(path):
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        import openpyxl
        rows = list(openpyxl.load_workbook(path, data_only=True).worksheets[0].iter_rows(values_only=True))
        head = [str(h).strip() for h in rows[0]]
        recs = [dict(zip(head, r)) for r in rows[1:] if r[0]]
    else:
        lines = path.read_text(encoding="utf-8").splitlines()
        lines = [l for l in lines if not l.startswith("=== Sheet:")]
        end = next((i for i, l in enumerate(lines) if l.startswith("=== Sheet:")), len(lines))
        head = lines[0].split("\t")
        joined = []
        for l in lines[1:end]:
            if re.match(r"RSH-\d{5}\t", l):
                joined.append(l)
            elif joined:                       # a cell with a line break continues the previous row
                joined[-1] += " " + l
        recs = [dict(zip(head, l.split("\t"))) for l in joined]
    return {str(r["Project ID"]).strip(): r for r in recs if str(r.get("Project ID", "")).startswith("RSH-")}


def main():
    src, rdate = sys.argv[1], dt.date.fromisoformat(sys.argv[2])
    dry = "--dry-run" in sys.argv
    key = rdate.strftime("%b").lower() + str(rdate.day)          # e.g. oct29
    label = f"{rdate.strftime('%b')} {rdate.day}"
    pf, mf, rf = ROOT / "pipeline_data.json", ROOT / "stand_meta.json", ROOT / "cluster_roster.json"
    p = json.loads(pf.read_text(encoding="utf-8"))
    sm = json.loads(mf.read_text(encoding="utf-8"))
    roster = json.loads(rf.read_text(encoding="utf-8"))
    if any(s.get("key") == key for s in p["report_snapshots"]):
        print(json.dumps({"skipped": f"snapshot {key} already applied"}))
        return
    prev = p["report_snapshots"][-1]["key"]
    R = read_report(src)
    log = collections.defaultdict(list)
    is_open = lambda r: str(r.get("Project Phase", "")).strip().startswith("8")

    # upcoming: refresh fields, drop removed, move opened → open_pdf
    keep = []
    for u in p["upcoming"]:
        r = R.get(u["rsh"])
        if r is None:
            log["removed"].append({"rsh": u["rsh"], "city": u["city"], "state": u["state"], "open": u.get("open", ""), "phase": u["phase"]})
            continue
        for k, h in FIELDS.items():
            v = md(r.get(h))
            if k == "notes" and not v:
                continue
            u[k] = v
        (p["open_pdf"] if is_open(r) else keep).append(u)
        if is_open(r):
            log["opened"].append(u)
    known = {u["rsh"] for u in keep} | {u["rsh"] for u in p["open_pdf"]}
    for rsh, r in R.items():                                     # new stands
        if rsh in known or is_open(r):
            continue
        u = {k: md(r.get(h)) for k, h in FIELDS.items()}
        u = {"rsh": rsh, **u, "region": "", "cluster": p["city_clusters"].get(f"{u['city']}|{u['state']}", "")}
        keep.append(u)
        log["added"].append({"rsh": rsh, "city": u["city"], "state": u["state"], "open": u["open"], "phase": u["phase"],
                             "region": u["cluster"] or "UNMAPPED — needs a region"})
    p["upcoming"] = keep
    p["open_count_from_report"] = sum(1 for r in R.values() if is_open(r))

    # opened stands → opened_shifts, store_clusters, stand_meta
    ds = {r["rsh"]: r for r in p["date_shifts"]}

    def rm_of(c, seen=()):
        x = roster["clusters"].get(c, {})
        if x.get("rm"):
            return x["rm"]
        w = x.get("covered_with")
        return rm_of(w, seen + (c,)) if w and w not in seen else ""

    for u in log["opened"]:
        b = ds.get(u["rsh"], {})
        p["opened_shifts"].append({"rsh": u["rsh"], "snapshot": key, "store": u["store"], "city": u["city"], "state": u["state"],
                                   "dec18": b.get("dec18", ""), "jan8": b.get("jan8", ""), "jan15": b.get("jan15", ""),
                                   "actual_open": u["open"], "cluster": u["cluster"]})
        sid = u["store"].lstrip("0")
        if sid:
            p["store_clusters"][sid] = u["cluster"]
            if sid not in sm:
                n = sum(1 for m in sm.values() if re.fullmatch(re.escape(u["city"]) + r"( \d+)?", m.get("Display_Name", "")))
                sm[sid] = {"Display_Name": u["city"] + (f" {n + 1}" if n else ""),
                           "Region": p["clusters"].get(u["cluster"], {}).get("market", ""),
                           "Open_Date": pdate(u["open"]).isoformat(), "Store_ID": sid, "State": u["state"],
                           "RM": rm_of(u["cluster"]), "Age_Bucket": "New"}

    # date_shifts: new snapshot column, carry forward, delta vs earliest baseline
    removed = {x["rsh"] for x in log["removed"]}
    for rsh in [x["rsh"] for x in log["added"]]:
        u = next(u for u in p["upcoming"] if u["rsh"] == rsh)
        p["date_shifts"].append({"rsh": rsh, "city": u["city"], "state": u["state"], "store": u["store"], "delta_days": 0,
                                 "cluster": u["cluster"]})
    for r in p["date_shifts"]:
        rp = R.get(r["rsh"])
        if r["rsh"] in removed:
            r[key] = "REMOVED"
        elif rp is not None and (not is_open(rp) or r["rsh"] in {u["rsh"] for u in log["opened"]}):
            r[key] = md(rp.get("Open Date"))
            old = r.get(prev, "")
            if old[:1].isdigit() and r[key][:1].isdigit() and old != r[key]:
                log["moved"].append({"rsh": r["rsh"], "city": r["city"], "state": r["state"], "region": r.get("cluster", ""),
                                     "from": old, "to": r[key], "weeks": round((pdate(r[key]) - pdate(old)).days / 7, 1)})
        else:
            r[key] = r.get(prev, "")
        base = r.get("dec18") or r.get("jan8") or r.get("jan15")
        if base and r[key][:1].isdigit():
            r["delta_days"] = (pdate(r[key]) - pdate(base)).days
    p["report_snapshots"].append({"key": key, "label": label, "date": rdate.isoformat()})
    p["_last_updated"] = label
    p["_source"] = f"7Crew Pipeline Report_{rdate.month}.{rdate.day}.{rdate.year}.xlsx"

    if not dry:
        pf.write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")
        mf.write_text(json.dumps(sm, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "snapshot": key, "dry_run": dry,
        "opened": [{"rsh": u["rsh"], "store": u["store"], "city": u["city"], "state": u["state"], "open": u["open"],
                    "region": u["cluster"], "name": sm.get(u["store"].lstrip("0"), {}).get("Display_Name", "")} for u in log["opened"]],
        "removed": log["removed"], "added": log["added"],
        "moved": sorted(log["moved"], key=lambda m: -abs(m["weeks"])),
        "totals": {"open_stands": len(p["store_clusters"]), "pipeline": len(p["upcoming"])},
    }
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
