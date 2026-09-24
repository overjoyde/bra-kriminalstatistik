#!/usr/bin/env bash
# Eget uttag ur Domstolsverkets DOMstat. Ex:
#   ./domstat_query.sh --table AntalMal/09_Konkurser_TR --select "Domstol=Alla tingsrätter" --years 2015-
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/domstat_query.py "$@"
