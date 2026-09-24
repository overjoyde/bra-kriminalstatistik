#!/usr/bin/env python3
"""Gör ett eget uttag ur Brås statistikdatabas SOL och spara som CSV (långt format).

Exempel:
    # Befogenhetsbedrägeri mot äldre (kod 0950+0951) per månad, hela landet + Stockholm
    python scripts/sol_query.py --menu brottskod-manad-region --codes 0950 0951 \
        --regions "Hela landet" Stockholm --periods 2024-01..2026-08

    # Penningtvätt (brottstyp-id 13092) per år 2015–2025, alla polisregioner, antal + per 100 000
    python scripts/sol_query.py --menu brottstyp-ar-region --ids 13092 --periods 2015-2025 --all-regions

    # Senaste året för terrorfinansieringskoderna
    python scripts/sol_query.py --menu brottskod-ar-region --codes 7035 7036 7037 --periods senaste

Periodspecifikation: 'senaste', 'alla', '2015-2025', '2024,2025' eller (månad) '2024-01..2026-08'.
Brotts-id och koder hittar du med: python scripts/sol_catalog.py --search <text>
"""
import argparse
import csv
import sys
from datetime import datetime

import _bootstrap  # noqa: F401
from brastat.paths import data_dir
from brastat.sol import MENUS, SolClient

POLICE_REGIONS = ["Region Nord", "Region Mitt", "Region Stockholm", "Region Öst", "Region Väst",
                  "Region Syd", "Region Bergslagen"]
FIELDS = ["meny", "brott_id", "brottskod", "brott", "sokvag", "omrade", "period", "ar", "manad", "kvartal",
          "periodtyp", "preliminar", "antal", "per_100k"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--menu", required=True, choices=list(MENUS))
    ap.add_argument("--ids", nargs="*", default=[], help="Brotts-id (brottstyp eller kod-id från katalogen)")
    ap.add_argument("--codes", nargs="*", default=[], help="Fyrsiffriga brottskoder (endast brottskod-menyer)")
    ap.add_argument("--regions", nargs="*", default=["Hela landet"], help='Områden, t.ex. "Hela landet" Stockholm')
    ap.add_argument("--all-regions", action="store_true", help="Hela landet + de 7 polisregionerna")
    ap.add_argument("--periods", default="senaste")
    ap.add_argument("--no-per100k", action="store_true", help="Hämta bara antal")
    ap.add_argument("--out", help="CSV-fil (standard: data/sol/uttag_<meny>_<tid>.csv). Använd '-' för stdout.")
    a = ap.parse_args()

    regions = ["Hela landet"] + POLICE_REGIONS if a.all_regions else a.regions
    rows = SolClient().query(a.menu, crime_ids=a.ids, codes=a.codes, regions=regions,
                             periods=a.periods, per_100k=not a.no_per100k)
    if a.out == "-":
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDS, delimiter=";")
        w.writeheader()
        w.writerows(rows)
        return
    path = a.out or data_dir() / "sol" / f"uttag_{a.menu}_{datetime.now():%Y%m%d_%H%M%S}.csv"
    from pathlib import Path
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rader -> {path}")


if __name__ == "__main__":
    main()
