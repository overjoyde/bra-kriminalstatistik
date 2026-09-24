#!/usr/bin/env bash
# Hämtar alla serier i config/watchlist_aml_fraud.json från SOL. Ex: ./sol_watchlist.sh --only penningtvatt_totalt
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/sol_watchlist.py "$@"
