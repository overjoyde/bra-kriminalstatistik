#!/usr/bin/env python3
"""Hämta alla serier i en DOMstat-bevakningslista (JSON) från Domstolsverket och spara en samlad CSV.

Exempel:
    python scripts/domstat_watchlist.py                              # brastat/config/watchlist_domstat.json
    python scripts/domstat_watchlist.py --config min_domstat.json
    python scripts/domstat_watchlist.py --only konkurser_tingsratt brottmal_tingsratt

En serie anges så här ("urval" använder DOMstat:s svenska texter; ovalda variabler hämtas helt):
    {"namn": "brottmal_tingsratt", "kategori": "Lagföringskedjan",
     "tabell": "AntalMal/02a_Malutveckling_per_malkategori_TR",
     "urval": {"Domstol": ["Alla tingsrätter"], "Målkategori": ["Brottmål"]}, "ar": "2010-"}

Utdata:
    data/domstat/watchlist/<serie>.csv       en fil per serie
    data/domstat/watchlist_samlad.csv        alla serier i långt format (+ kolumnerna serie, kategori)
    data/domstat/watchlist_samlad.prev.csv   förra körningen; data/domstat/snapshots/ daterade kopior
"""
import argparse
import json
import logging
from pathlib import Path

from brastat import log as blog
from brastat.domstat import FIELDS as DFIELDS
from brastat.domstat import DomstatClient
from brastat.paths import config_path, data_dir
from brastat.watchlist import save_combined, write_csv

log = logging.getLogger("brastat.domstat_watchlist")

FIELDS = ["serie", "kategori", *DFIELDS]



def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(config_path("watchlist_domstat.json")),
                    help="Bevakningslista (JSON). Standard: den medföljande DOMstat-listan")
    ap.add_argument("--only", nargs="*", help="Kör bara dessa serier (namn)")
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)

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
        log.info("- %-36s %-55s %s", s["namn"], s["tabell"], years)
        try:
            rows = dom.query(s["tabell"], s.get("urval"), years=years)
        except Exception as e:  # noqa: BLE001
            log.error("  x %s: %s", s["namn"], e)
            fel.append(s["namn"])
            continue
        for r in rows:
            r["serie"], r["kategori"] = s["namn"], s.get("kategori", "")
        write_csv(out / "watchlist" / f"{s['namn']}.csv", rows, FIELDS)
        allrows += rows
        log.info("  + %d rader", len(rows))
    path = save_combined(out, allrows, FIELDS, failed=fel)
    log.info("%d rader -> %s%s", len(allrows), path, f"  (fel: {', '.join(fel)})" if fel else "")
    if fel:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
