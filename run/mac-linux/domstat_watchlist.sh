#!/usr/bin/env bash
# Hämtar alla serier i brastat/config/watchlist_domstat.json från Domstolsverkets DOMstat. Ex: ./domstat_watchlist.sh --only konkurser_tingsratt
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/domstat_watchlist.py "$@"
