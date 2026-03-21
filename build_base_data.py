"""
build_base_data.py
------------------
One-time script to parse all historical P&L Excel files and bake them
permanently into data.json.

Usage (run from the blank-app folder):
    python build_base_data.py --folder "C:/path/to/your/pl_files"

All .xlsx files in that folder will be parsed and merged into data.json.
Commit and push data.json afterwards — done forever.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

# ── Make sure we can import pl_parser from the same directory ──────────────
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from pl_parser import parse_pl_file, merge_into_dash, load_stand_metadata

DATA_JSON    = script_dir / "data.json"
STAND_META   = script_dir / "stand_meta.json"


def load_base():
    if not DATA_JSON.exists():
        print(f"ERROR: {DATA_JSON} not found. Make sure you run this from the blank-app folder.")
        sys.exit(1)
    with open(DATA_JSON, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Merge historical P&L files into data.json")
    parser.add_argument(
        "--folder",
        required=True,
        help="Path to folder containing .xlsx P&L files (e.g. C:/Users/Chris/PL_Files/2024)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse files and report what would be added, but don't write data.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-parse and overwrite periods already in data.json (use when fixing region data)",
    )
    args = parser.parse_args()

    pl_folder = Path(args.folder)
    if not pl_folder.exists():
        print(f"ERROR: Folder not found: {pl_folder}")
        sys.exit(1)

    xlsx_files = sorted(pl_folder.glob("*.xlsx"))
    if not xlsx_files:
        print(f"No .xlsx files found in {pl_folder}")
        sys.exit(1)

    print(f"Found {len(xlsx_files)} file(s) in {pl_folder}\n")

    # Load stand metadata so parser can assign correct regions
    if STAND_META.exists():
        load_stand_metadata(str(STAND_META))
        print(f"Loaded stand metadata from {STAND_META.name}\n")
    else:
        print(f"WARNING: {STAND_META.name} not found — regions will show as 'Unknown'\n")

    base = load_base()
    existing_keys = {p["period_key"] for p in base.get("period_summaries", [])}
    print(f"Existing base data: {len(existing_keys)} periods → {sorted(existing_keys)}\n")

    dash = copy.deepcopy(base)
    parsed = []
    skipped = []
    errors = []

    for xlsx in xlsx_files:
        print(f"  Parsing: {xlsx.name} ...", end=" ", flush=True)
        try:
            # Pass the real path directly so the parser reads the correct filename
            result = parse_pl_file(str(xlsx))

            if result and result.get("stands"):
                pk = result["period_key"]
                stands = len(result["stands"])
                if pk in existing_keys and not args.force:
                    print(f"SKIP (already in base: {pk})")
                    skipped.append(pk)
                else:
                    print(f"OK → {pk} ({stands} stands)")
                    parsed.append(result)
            else:
                print("SKIP (no stands found)")
                skipped.append(xlsx.name)
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(f"{xlsx.name}: {e}")

    print(f"\n{'─'*60}")
    print(f"  Parsed successfully : {len(parsed)} period(s)")
    print(f"  Skipped (duplicate) : {len(skipped)}")
    print(f"  Errors              : {len(errors)}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  ✗ {e}")

    if not parsed:
        print("\nNothing new to add — data.json unchanged.")
        return

    if args.dry_run:
        print("\n[DRY RUN] Would add these periods:")
        for r in parsed:
            print(f"  + {r['period_key']} ({len(r['stands'])} stands)")
        print("\nRe-run without --dry-run to write data.json.")
        return

    # Merge and write
    print(f"\nMerging {len(parsed)} new period(s) into data.json ...")
    updated = merge_into_dash(dash, parsed)

    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, default=str)

    new_keys = {p["period_key"] for p in updated.get("period_summaries", [])}
    added = sorted(new_keys - existing_keys)
    print(f"\n✅ data.json updated — {len(new_keys)} total periods")
    print(f"   Added: {added}")
    print(f"\nNext step: commit and push data.json to GitHub")
    print(f"   git add data.json")
    print(f"   git commit -m \"Add historical P&L data: {', '.join(added)}\"")
    print(f"   git push")


if __name__ == "__main__":
    main()
