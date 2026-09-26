#!/usr/bin/env python3
"""Snabbt livetest mot källorna – upptäcker när Brå eller Domstolsverket ändrat något.

Gör tre små anrop (några sekunder, ingenting sparas):

1. SOL: anmälda penningtvättsbrott, hela landet, senaste året
2. DOMstat: inkomna konkursärenden, alla tingsrätter, senaste året
3. bra.se: att periodlistan för preliminär månadsstatistik går att läsa och att en tabell hittas

Körs varje vecka i GitHub Actions (.github/workflows/scheduled.yml) och kan köras lokalt:

    python scripts/smoke_live.py
    python scripts/smoke_live.py --only sol

Avslutskod 1 om något test misslyckas.
"""
import argparse
import logging
import sys
import time

from brastat import log as blog

log = logging.getLogger("brastat.smoke_live")


def check_sol() -> str:
    from brastat.sol import SolClient

    rows = SolClient().query("brottstyp-ar-region", crime_ids=["13092"], regions=["Hela landet"], periods="senaste")
    values = [r["antal"] for r in rows if r.get("antal") is not None]
    if not values:
        raise AssertionError(f"inga värden i svaret ({len(rows)} rader)")
    return f"{rows[0]['brott']} {rows[0]['period']}: {values[0]:g}"


def check_domstat() -> str:
    from brastat.domstat import DomstatClient

    rows = DomstatClient().query("AntalMal/09_Konkurser_TR", {"Domstol": "Alla tingsrätter"}, years="senaste")
    values = [r for r in rows if r.get("varde") is not None]
    if not values:
        raise AssertionError(f"inga värden i svaret ({len(rows)} rader)")
    return f"{values[0]['variabel']} {values[0]['ar']}: {values[0]['varde']:g}"


def check_bra_tables() -> str:
    import tempfile
    from pathlib import Path

    from brastat.tabeller import ANM, TableFetcher

    with tempfile.TemporaryDirectory() as d:
        tf = TableFetcher(Path(d))
        months = tf.latest_options(ANM, "P1")
        if not months:
            raise AssertionError("hittade ingen periodlista för preliminär månadsstatistik (P1)")
        latest = months[0]
        url = tf.resolve_statpage(f"P1/{latest.split('-')[1]}/P1La{latest}")
        if not url:
            raise AssertionError(f"tabellsidan för {latest} saknar nedladdningslänk")
    return f"senaste månad {latest}: {url.rsplit('/', 1)[1]}"


CHECKS = {"sol": check_sol, "domstat": check_domstat, "bra": check_bra_tables}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", choices=list(CHECKS), help="Kör bara dessa test")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)
    failed = []
    for name in a.only or CHECKS:
        t0 = time.monotonic()
        try:
            info = CHECKS[name]()
        except Exception as e:  # noqa: BLE001 – rapportera alla test, inte bara det första
            log.error("FEL  %-8s %s", name, e)
            failed.append(name)
        else:
            log.info("OK   %-8s %s (%.1f s)", name, info, time.monotonic() - t0)
    if failed:
        log.error("Livetest misslyckades: %s", ", ".join(failed))
        sys.exit(1)
    log.info("Alla livetest OK")


if __name__ == "__main__":
    main()
