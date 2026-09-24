#!/usr/bin/env bash
# Hela kedjan: färdiga tabeller + SOL-bevakningslista + dashboards.
# Flaggor skickas vidare, t.ex. --no-pdf, --skip-dashboards, --only-sol, --force
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/fetch_all.py "$@"
