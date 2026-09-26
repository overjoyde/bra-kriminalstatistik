#!/usr/bin/env python3
"""Hälsokontroll av hämtad data – flaggar fel, saknade tabeller, inaktuell och oväntat reviderad data.

Läser data/manifest.csv och bevakningslistorna (och jämför dem med förra körningen). Körs sist i
fetch_all.py så att ett ändrat URL-mönster hos Brå syns direkt i stället för som tysta luckor.

    python scripts/check_health.py                  # text, avslutskod 1 vid fel
    python scripts/check_health.py --strict         # avslutskod 1 även vid varningar
    python scripts/check_health.py --verify         # kontrollera även sha256 mot filerna
    python scripts/check_health.py --json           # maskinläsbart
    python scripts/check_health.py --notify         # avisera vid fel (skrivbord, webhook, e-post)

Aviseringar konfigureras med miljövariabler, se brastat/notify.py:
    BRASTAT_NOTIFY_WEBHOOK, BRASTAT_NOTIFY_EMAIL + BRASTAT_SMTP_HOST, BRASTAT_NOTIFY_DESKTOP=0

Avslutskoder: 0 = inga fel, 1 = fel (eller varningar med --strict).
"""
import argparse
import json
import sys

from brastat import log as blog
from brastat.health import run_all, summarize
from brastat.notify import TITLE, notify
from brastat.paths import data_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", help="Datakatalog (standard: data/ eller BRA_DATA_DIR)")
    ap.add_argument("--max-age-days", type=int, default=40,
                    help="Varna om manifest.csv är äldre än så (standard 40; schemat kör månadsvis)")
    ap.add_argument("--max-lag-months", type=int, default=3,
                    help="Varna om senaste SOL-månaden ligger längre bak (standard 3)")
    ap.add_argument("--verify", action="store_true", help="Räkna om sha256 för varje fil")
    ap.add_argument("--strict", action="store_true", help="Behandla varningar som fel")
    ap.add_argument("--json", action="store_true", help="Skriv fynden som JSON")
    ap.add_argument("--notify", action="store_true", help="Skicka avisering om kontrollen misslyckas")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)

    data = data_dir(a.data_dir, create=False)
    findings = run_all(data, verify=a.verify, max_age_days=a.max_age_days, max_lag_months=a.max_lag_months)
    by = summarize(findings)
    errors, warnings = by.get("error", []), by.get("warning", [])
    failed = bool(errors or (a.strict and warnings))
    if a.json:
        json.dump({"errors": len(errors), "warnings": len(warnings), "findings": [f.as_dict() for f in findings]},
                  sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        for f in errors:
            print(f"  FEL     [{f.check}] {f.message}")
        for f in warnings:
            print(f"  VARNING [{f.check}] {f.message}")
        print(f"\nHälsokontroll: {len(errors)} fel, {len(warnings)} varningar"
              + (" – allt ser bra ut" if not findings else ""))
    if failed and a.notify:
        lines = [f"{'FEL' if f.level == 'error' else 'VARNING'}: {f.message}" for f in errors + warnings]
        notify(f"{TITLE}: hälsokontrollen hittade {len(errors)} fel",
               "\n".join(lines[:15]) + (f"\n… och {len(lines) - 15} till" if len(lines) > 15 else "")
               + f"\nData: {data}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
