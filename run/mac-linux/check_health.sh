#!/usr/bin/env bash
# Hälsokontroll av hämtad data (manifest, saknade tabeller, inaktuell data). Ex: ./check_health.sh --strict
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/check_health.py "$@"
