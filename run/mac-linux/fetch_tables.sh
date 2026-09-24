#!/usr/bin/env bash
# Brås färdiga Excel-tabeller, diagramdata, rapporter. Ex: ./fetch_tables.sh --groups anmalda misstankta
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/fetch_tables.py "$@"
