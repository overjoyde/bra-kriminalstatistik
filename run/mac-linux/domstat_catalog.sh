#!/usr/bin/env bash
# Lista/sök tabeller i Domstolsverkets DOMstat. Ex: ./domstat_catalog.sh --search brottmål
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/domstat_catalog.py "$@"
