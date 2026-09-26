#!/usr/bin/env bash
# Skapar .venv och installerar beroenden. Kör en gång: ./run/mac-linux/setup.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
command -v python3 >/dev/null || { echo "Python 3 saknas (macOS: brew install python)"; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip >/dev/null
# Låsta versioner (reproducerbart) + paketet brastat i redigerbart läge.
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m unittest discover -s tests
echo "Klart. Testa: ./run/mac-linux/sol_watchlist.sh"
