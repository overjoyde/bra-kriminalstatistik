#!/usr/bin/env bash
# Bygger Excel- och HTML-dashboard från data/raw (kör fetch_tables.sh först).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
"$PY" scripts/build_excel_dashboard.py
"$PY" scripts/build_html_dashboard.py
echo "Öppna: $REPO/data/dashboard/Bra_trendbevakning_dashboard.html"
