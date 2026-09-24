#!/usr/bin/env bash
# Gemensamt: hitta repo-roten och rätt Python (projektets .venv om den finns).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -x "$REPO/.venv/bin/python" ]; then
  PY="$REPO/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "Python 3 saknas. Installera: macOS 'brew install python', Debian/Ubuntu 'sudo apt install python3 python3-venv'." >&2
  exit 1
fi
cd "$REPO"
