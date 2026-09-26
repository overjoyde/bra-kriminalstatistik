#!/usr/bin/env python3
"""Exportera SOL:s urvalslistor (brottstyper, brottskoder, områden, perioder) till CSV.

Användbart för att hitta rätt brotts-id / brottskod innan man gör uttag med sol_query.py.

Exempel:
    python scripts/sol_catalog.py                          # standardmenyerna -> data/sol/katalog/
    python scripts/sol_catalog.py --menus brottskod-ar-region
    python scripts/sol_catalog.py --search penningtvätt    # sök i brottstyper och brottskoder
    python scripts/sol_catalog.py --list-menus
"""
import argparse
import csv
import logging

from brastat import log as blog
from brastat.paths import data_dir
from brastat.sol import MENUS, SolClient

log = logging.getLogger("brastat.sol_catalog")

DEFAULT_MENUS = ["brottstyp-ar-region", "brottskod-ar-region", "brottstyp-manad-region"]


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig -> öppnas rätt i Excel
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        w.writerows(rows)
    log.info("  + %s (%d rader)", path, len(rows))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--menus", nargs="+", choices=list(MENUS), default=DEFAULT_MENUS)
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    ap.add_argument("--search", help="Skriv ut brott vars namn eller kod innehåller texten (skriver inga filer)")
    ap.add_argument("--list-menus", action="store_true")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)

    if a.list_menus:
        for k, v in MENUS.items():
            print(f"{k:26} menyid={v['id']:<4} {v['desc']}")
        return

    sol = SolClient()
    out = data_dir(a.out) / "sol" / "katalog"
    for menu in a.menus:
        print(f"\n[{menu}] {MENUS[menu]['desc']}")
        cat = sol.catalog(menu)
        if a.search:
            q = a.search.lower()
            for c in cat.crimes:
                if q in c.name.lower() or q in c.path.lower():
                    print(f"  id={c.id:<6} kod={c.code or '-':<5} {'  ' * c.depth}{c.label}   [{c.path}]")
            continue
        tree = {i: n for i, n, _ in cat.tree}
        write_csv(out / f"{menu}_brott.csv", ["brott_id", "brottskod", "namn", "niva", "grupp_id", "grupp", "sokvag"],
                  [[c.id, c.code, c.label, c.depth, c.parent_id, tree.get(c.parent_id, ""), c.path] for c in cat.crimes])
        write_csv(out / f"{menu}_trad.csv", ["grupp_id", "namn", "niva"], [[i, n, d] for i, n, d in cat.tree])
        write_csv(out / f"{menu}_omraden.csv", ["omrade_id", "namn"], [[v, k] for k, v in cat.regions.items()])
        write_csv(out / f"{menu}_perioder.csv", ["period_id", "nyckel", "namn", "ar", "typ", "preliminar"],
                  [[p.id, p.key, p.name, p.year, p.kind, p.prel] for p in cat.periods])


if __name__ == "__main__":
    main()
