#!/usr/bin/env bash
# Snabbt livetest mot SOL, DOMstat och bra.se. Ex: ./smoke_live.sh --only sol
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
exec "$PY" scripts/smoke_live.py "$@"
