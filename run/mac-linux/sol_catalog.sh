#!/usr/bin/env bash
# Exportera/sök SOL:s brottstyper och brottskoder. Ex: ./sol_catalog.sh --search penningtvätt
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/sol_catalog.py "$@"
