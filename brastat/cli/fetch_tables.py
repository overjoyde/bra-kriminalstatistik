#!/usr/bin/env python3
"""Hämta Brås färdiga tabeller (Excel), diagramdata, rapporter och metoddokument från bra.se.

Exempel:
    python scripts/fetch_tables.py                       # alla grupper, hoppar över befintliga filer
    python scripts/fetch_tables.py --force               # hämta om allt
    python scripts/fetch_tables.py --groups anmalda misstankta
    python scripts/fetch_tables.py --last-year 2025 --years 5 --out D:/bra-data

Grupper: anmalda, misstankta, lagforda, handlagda, malsagare, enkater, amnessidor, rapporter, metod.
Resultatet hamnar i <out>/raw (tabeller), <out>/docs (PDF) och <out>/manifest.csv.
"""
import argparse

from brastat import log as blog
from brastat.paths import data_dir
from brastat.tabeller import GROUPS, TableFetcher


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    ap.add_argument("--groups", nargs="+", choices=GROUPS, help="Välj grupper (standard: alla)")
    ap.add_argument("--force", action="store_true", help="Hämta om filer som redan finns")
    ap.add_argument("--last-year", type=int, help="Senaste år med slutlig statistik (standard: automatiskt)")
    ap.add_argument("--years", type=int, default=10, help="Antal år bakåt för årstabeller (standard 10)")
    ap.add_argument("--no-pdf", action="store_true", help="Hoppa över rapporter och metoddokument (PDF)")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)
    groups = a.groups or [g for g in GROUPS if not (a.no_pdf and g in ("rapporter", "metod"))]
    TableFetcher(data_dir(a.out), force=a.force, last_full_year=a.last_year, years=a.years).run(groups)


if __name__ == "__main__":
    main()
