#!/usr/bin/env python3
"""Gör ett uttag ur Domstolsverkets statistikdatabas DOMstat och spara som CSV (långt format).

Exempel:
    # Konkurser per tingsrätt, alla år
    python scripts/domstat_query.py --table AntalMal/09_Konkurser_TR

    # Brottmål vid alla tingsrätter (summa) 2015–, inkomna/avgjorda/balans
    python scripts/domstat_query.py --table AntalMal/02a_Malutveckling_per_malkategori_TR \
        --select "Domstol=Alla tingsrätter" "Målkategori=Brottmål" --years 2015-

    # Skuldsanering och företagsrekonstruktioner senaste 5 åren, direkt till skärmen
    python scripts/domstat_query.py --table AntalMal/02b_Malutveckling_per_malkategori_arenden_TR \
        --select "Domstol=Alla tingsrätter" "Målkategori=Skuldsanering,Företagsrekonstruktioner" \
        --years senaste:5 --out -

--select tar VARIABEL=värde[,värde…] med de svenska texterna (skiftlägesokänsligt; ett unikt
delord räcker). Ovalda variabler hämtas i sin helhet. Tabeller och värden hittar du med
    python scripts/domstat_catalog.py --search <text>   /   --table <tabell>
Årsurval: 'alla' (standard), 'senaste', 'senaste:5', '2015-2025', '2015-', '2024,2025'.
"""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import _bootstrap  # noqa: F401
from brastat.domstat import FIELDS, DomstatClient
from brastat.paths import data_dir


def parse_select(items: list[str]) -> dict[str, list[str]]:
    sel: dict[str, list[str]] = {}
    for it in items:
        if "=" not in it:
            raise SystemExit(f"--select måste vara VARIABEL=värde, fick: {it}")
        k, v = it.split("=", 1)
        sel[k.strip()] = [x.strip() for x in v.split(",") if x.strip()]
    return sel


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True, help="Tabell, t.ex. AntalMal/09_Konkurser_TR")
    ap.add_argument("--select", nargs="*", default=[], help='T.ex. "Domstol=Alla tingsrätter" "Målkategori=Brottmål"')
    ap.add_argument("--years", default="alla")
    ap.add_argument("--out", help="CSV-fil (standard: data/domstat/uttag_<tabell>_<tid>.csv). '-' = stdout.")
    a = ap.parse_args()

    rows = DomstatClient().query(a.table, parse_select(a.select), years=a.years)
    if a.out == "-":
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDS, delimiter=";")
        w.writeheader()
        w.writerows(rows)
        return
    name = a.table.strip("/").removesuffix(".px").replace("/", "_")
    path = Path(a.out or data_dir() / "domstat" / f"uttag_{name}_{datetime.now():%Y%m%d_%H%M%S}.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rader -> {path}")


if __name__ == "__main__":
    main()
