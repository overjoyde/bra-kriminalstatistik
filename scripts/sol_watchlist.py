#!/usr/bin/env python3
"""Hämta alla serier i en bevakningslista (JSON) från SOL och spara en samlad CSV.

Exempel:
    python scripts/sol_watchlist.py                                   # config/watchlist_aml_fraud.json
    python scripts/sol_watchlist.py --config config/min_lista.json
    python scripts/sol_watchlist.py --only befogenhetsbedrageri penningtvatt_totalt

Utdata:
    data/sol/watchlist/<serie>.csv       en fil per serie
    data/sol/watchlist_samlad.csv        alla serier i långt format (+ kolumnerna serie, kategori)
"""
import argparse
import csv
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from brastat.paths import REPO, data_dir
from brastat.sol import SolClient

FIELDS = ["serie", "kategori", "meny", "brott_id", "brottskod", "brott", "sokvag", "omrade", "period", "ar",
          "manad", "kvartal", "periodtyp", "preliminar", "antal", "per_100k"]


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(REPO / "config" / "watchlist_aml_fraud.json"))
    ap.add_argument("--only", nargs="*", help="Kör bara dessa serier (namn)")
    ap.add_argument("--out", help="Datakatalog (standard: ./data eller BRA_DATA_DIR)")
    a = ap.parse_args()

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
        print(f"- {s['namn']:40} {s['meny']:24} {periods}")
        try:
            rows = sol.query(s["meny"], crime_ids=s.get("ids"), codes=s.get("koder"), regions=regions,
                             periods=periods)
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
