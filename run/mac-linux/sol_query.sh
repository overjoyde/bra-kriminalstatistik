#!/usr/bin/env bash
# Eget SOL-uttag. Ex:
#   ./sol_query.sh --menu brottskod-manad-region --codes 0950 0951 --periods 2024-01..2026-08 --all-regions
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/sol_query.py "$@"
