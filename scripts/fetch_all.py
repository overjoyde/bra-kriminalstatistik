#!/usr/bin/env python3
"""Kör hela kedjan: färdiga tabeller -> SOL-bevakningslista -> dashboards.

    python scripts/fetch_all.py                 # allt (PDF:er hämtas bara första gången)
    python scripts/fetch_all.py --no-pdf        # hoppa över rapporter/metod-PDF
    python scripts/fetch_all.py --skip-dashboards
    python scripts/fetch_all.py --only-sol      # bara SOL-bevakningslistan

Används av run/mac-linux/*.sh och run/windows/*.ps1 samt schemalagda körningar.
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def step(name: str, args: list[str]) -> bool:
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run([sys.executable, str(HERE / args[0]), *args[1:]])
    if r.returncode != 0:
        print(f"!!! {name} avslutades med kod {r.returncode}", flush=True)
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--skip-dashboards", action="store_true")
    ap.add_argument("--only-sol", action="store_true")
    ap.add_argument("--force", action="store_true", help="Hämta om färdiga tabeller")
    a = ap.parse_args()

    ok = True
    if not a.only_sol:
        args = ["fetch_tables.py"] + (["--no-pdf"] if a.no_pdf else []) + (["--force"] if a.force else [])
        ok &= step("Färdiga tabeller från bra.se", args)
    ok &= step("SOL-bevakningslista", ["sol_watchlist.py"])
    if not (a.skip_dashboards or a.only_sol):
        try:
            import openpyxl  # noqa: F401
            import pandas  # noqa: F401
        except ImportError:
            print("\n(pandas/openpyxl saknas – hoppar över dashboards. Kör setup-skriptet först.)")
        else:
            ok &= step("Excel-dashboard", ["build_excel_dashboard.py"])
            ok &= step("HTML-dashboard", ["build_html_dashboard.py"])
    print("\nKLART" if ok else "\nKLART MED FEL – se loggen ovan")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
