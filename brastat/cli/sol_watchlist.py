#!/usr/bin/env python3
"""Hämta alla serier i en bevakningslista (JSON) från SOL och spara en samlad CSV.

Exempel:
    python scripts/sol_watchlist.py                                   # brastat/config/watchlist_aml_fraud.json
    python scripts/sol_watchlist.py --config min_lista.json
    python scripts/sol_watchlist.py --only befogenhetsbedrageri penningtvatt_totalt

Utdata:
    data/sol/watchlist/<serie>.csv       en fil per serie
    data/sol/watchlist_samlad.csv        alla serier i långt format (+ kolumnerna serie, kategori)
    data/sol/watchlist_samlad.prev.csv   förra körningen (jämförs av check_health.py)
    data/sol/snapshots/                  daterade ögonblicksbilder (.csv.gz)
"""
import argparse
import json
import logging
from pathlib import Path

from brastat import log as blog
from brastat.paths import config_path, data_dir
from brastat.sol import SolClient
from brastat.watchlist import save_combined, write_csv

log = logging.getLogger("brastat.sol_watchlist")

FIELDS = ["serie", "kategori", "meny", "brott_id", "brottskod", "brott", "sokvag", "omrade", "period", "ar",
          "manad", "kvartal", "periodtyp", "preliminar", "antal", "per_100k"]



def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(config_path("watchlist_aml_fraud.json")),
                    help="Bevakningslista (JSON). Standard: den medföljande AML-/bedrägerilistan")
    ap.add_argument("--only", nargs="*", help="Kör bara dessa serier (namn)")
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)

    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    std = cfg.get("standard", {})
    out = data_dir(a.out) / "sol"
    sol = SolClient()
    allrows: list[dict] = []
    fel = []
    for s in cfg["serier"]:
        if a.only and s["namn"] not in a.only:
            continue
        monthly = "manad" in s["meny"]
        periods = s.get("perioder") or (std.get("manad_perioder") if monthly else std.get("ar_perioder")) or "senaste"
        regions = s.get("regioner") or std.get("regioner") or ["Hela landet"]
        log.info("- %-40s %-24s %s", s["namn"], s["meny"], periods)
        try:
            rows = sol.query(s["meny"], crime_ids=s.get("ids"), codes=s.get("koder"), regions=regions,
                             periods=periods)
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
