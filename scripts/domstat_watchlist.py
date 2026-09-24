#!/usr/bin/env python3
"""Hämta alla serier i en DOMstat-bevakningslista (JSON) från Domstolsverket och spara en samlad CSV.

Exempel:
    python scripts/domstat_watchlist.py                              # config/watchlist_domstat.json
    python scripts/domstat_watchlist.py --config config/min_domstat.json
    python scripts/domstat_watchlist.py --only konkurser_tingsratt brottmal_tingsratt

En serie anges så här ("urval" använder DOMstat:s svenska texter; ovalda variabler hämtas helt):
    {"namn": "brottmal_tingsratt", "kategori": "Lagföringskedjan",
     "tabell": "AntalMal/02a_Malutveckling_per_malkategori_TR",
     "urval": {"Domstol": ["Alla tingsrätter"], "Målkategori": ["Brottmål"]}, "ar": "2010-"}

Utdata:
    data/domstat/watchlist/<serie>.csv       en fil per serie
    data/domstat/watchlist_samlad.csv        alla serier i långt format (+ kolumnerna serie, kategori)
"""
import argparse
import csv
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from brastat.domstat import FIELDS as DFIELDS
from brastat.domstat import DomstatClient
from brastat.paths import REPO, data_dir

FIELDS = ["serie", "kategori", *DFIELDS]


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(REPO / "config" / "watchlist_domstat.json"))
    ap.add_argument("--only", nargs="*", help="Kör bara dessa serier (namn)")
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    std = cfg.get("standard", {})
    out = data_dir(a.out) / "domstat"
    dom = DomstatClient()
    allrows: list[dict] = []
    fel = []
    for s in cfg["serier"]:
        if a.only and s["namn"] not in a.only:
            continue
        years = s.get("ar") or std.get("ar") or "alla"
        print(f"- {s['namn']:36} {s['tabell']:55} {years}")
        try:
            rows = dom.query(s["tabell"], s.get("urval"), years=years)
        except Exception as e:  # noqa: BLE001
            print(f"  x {e}")
            fel.append(s["namn"])
            continue
        for r in rows:
            r["serie"], r["kategori"] = s["namn"], s.get("kategori", "")
        write(out / "watchlist" / f"{s['namn']}.csv", rows)
        allrows += rows
        print(f"  + {len(rows)} rader")
    write(out / "watchlist_samlad.csv", allrows)
    print(f"\n{len(allrows)} rader -> {out / 'watchlist_samlad.csv'}" + (f"  (fel: {', '.join(fel)})" if fel else ""))
    if fel:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
