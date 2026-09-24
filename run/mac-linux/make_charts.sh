#!/usr/bin/env bash
# Exempelgrafer (PNG) + årstabell till data/charts/ (kräver sol_watchlist + fetch_tables först).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/make_charts.py "$@"
