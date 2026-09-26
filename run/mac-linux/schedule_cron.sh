#!/usr/bin/env bash
# Schemalägg månadsvis körning med cron (Linux, fungerar även på macOS).
#   ./schedule_cron.sh            lägg till (den 15:e kl. 07:00)
#   ./schedule_cron.sh --remove   ta bort
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TAG="# bra-kriminalstatistik"
LINE="0 7 15 * * /bin/bash \"$REPO/run/mac-linux/fetch_all.sh\" --no-pdf --notify >> \"$REPO/data/logs/fetch.log\" 2>&1 $TAG"
mkdir -p "$REPO/data/logs"
CUR="$(crontab -l 2>/dev/null | grep -v "$TAG" || true)"
if [ "${1:-}" = "--remove" ]; then
  printf '%s\n' "$CUR" | crontab -; echo "Borttaget."; exit 0
fi
printf '%s\n%s\n' "$CUR" "$LINE" | sed '/^$/d' | crontab -
echo "Tillagt i crontab:"; echo "  $LINE"
