#!/usr/bin/env python3
"""Kör hela kedjan: färdiga tabeller -> SOL -> DOMstat -> dashboards och grafer -> hälsokontroll.

    python scripts/fetch_all.py                 # allt (PDF:er hämtas bara första gången)
    python scripts/fetch_all.py --no-pdf        # hoppa över rapporter/metod-PDF
    python scripts/fetch_all.py --skip-dashboards
    python scripts/fetch_all.py --only-sol      # bara SOL-bevakningslistan
    python scripts/fetch_all.py --no-domstat    # hoppa över Domstolsverkets DOMstat
    python scripts/fetch_all.py --skip-health   # hoppa över hälsokontrollen
    python scripts/fetch_all.py --notify        # avisera (skrivbord/webhook) om hälsokontrollen hittar fel

Används av run/mac-linux/*.sh och run/windows/*.ps1 samt schemalagda körningar (som skickar --notify).
Varje steg körs som en egen process (python -m brastat.…), så att ett fel i ett steg inte stoppar resten.
"""
import argparse
import logging
import subprocess
import sys

from brastat import log as blog

log = logging.getLogger("brastat.fetch_all")


def step(name: str, module: str, args: list[str] | None = None) -> bool:
    log.info("=== %s ===", name)
    r = subprocess.run([sys.executable, "-m", module, *(args or [])])
    if r.returncode != 0:
        log.error("!!! %s avslutades med kod %d", name, r.returncode)
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--skip-dashboards", action="store_true")
    ap.add_argument("--only-sol", action="store_true")
    ap.add_argument("--force", action="store_true", help="Hämta om färdiga tabeller")
    ap.add_argument("--no-domstat", action="store_true", help="Hoppa över Domstolsverkets DOMstat")
    ap.add_argument("--skip-health", action="store_true", help="Hoppa över hälsokontrollen (check_health.py)")
    ap.add_argument("--notify", action="store_true",
                    help="Skicka avisering om hälsokontrollen hittar fel (se check_health.py --help)")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)

    ok = True
    if not a.only_sol:
        args = (["--no-pdf"] if a.no_pdf else []) + (["--force"] if a.force else [])
        ok &= step("Färdiga tabeller från bra.se", "brastat.cli.fetch_tables", args)
    ok &= step("SOL-bevakningslista", "brastat.cli.sol_watchlist")
    if not (a.no_domstat or a.only_sol):
        ok &= step("DOMstat-bevakningslista (Domstolsverket)", "brastat.cli.domstat_watchlist")
    if not (a.skip_dashboards or a.only_sol):
        try:
            import openpyxl  # noqa: F401
            import pandas  # noqa: F401
        except ImportError:
            log.warning("pandas/openpyxl saknas – hoppar över dashboards. Kör setup-skriptet först.")
        else:
            ok &= step("Excel-dashboard", "brastat.analysis.excel_dashboard")
            ok &= step("HTML-dashboard", "brastat.analysis.html_dashboard")
            try:
                import matplotlib  # noqa: F401
            except ImportError:
                log.warning("matplotlib saknas – hoppar över exempelgrafer")
            else:
                ok &= step("Exempelgrafer", "brastat.analysis.charts")
    if not a.skip_health:
        ok &= step("Hälsokontroll", "brastat.cli.check_health", ["--notify"] if a.notify else [])
    log.info("KLART" if ok else "KLART MED FEL – se loggen ovan")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
