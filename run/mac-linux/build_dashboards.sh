#!/usr/bin/env bash
# Bygger Excel- och HTML-dashboard från data/raw (kör fetch_tables.sh först).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
# Flaggor (t.ex. -q eller --help) skickas vidare till båda byggena.
"$PY" scripts/build_excel_dashboard.py "$@"
"$PY" scripts/build_html_dashboard.py "$@"
case " $* " in *" --help "*|*" -h "*) exit 0;; esac
echo "Öppna: $REPO/data/dashboard/Bra_trendbevakning_dashboard.html"
