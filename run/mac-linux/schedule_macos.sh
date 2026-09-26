#!/usr/bin/env bash
# Schemalägg månadsvis körning på macOS med launchd (standard: den 15:e kl. 07:00).
#   ./schedule_macos.sh            installera
#   ./schedule_macos.sh --remove   ta bort
# OBS: launchd-jobb får inte läsa ~/Desktop, ~/Documents eller ~/Downloads (macOS TCC).
# Lägg därför repot t.ex. i ~/code/bra-kriminalstatistik innan du schemalägger.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LABEL="se.bra-kriminalstatistik.fetch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DAY="${DAY:-15}"; HOUR="${HOUR:-7}"
if [ "${1:-}" = "--remove" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"; echo "Borttaget."; exit 0
fi
case "$REPO" in
  "$HOME/Desktop"*|"$HOME/Documents"*|"$HOME/Downloads"*)
    echo "Varning: $REPO ligger i en TCC-skyddad mapp – launchd kommer att nekas åtkomst. Flytta repot först." >&2;;
esac
mkdir -p "$REPO/data/logs" "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>$REPO/run/mac-linux/fetch_all.sh</string><string>--no-pdf</string><string>--notify</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Day</key><integer>$DAY</integer><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$REPO/data/logs/fetch.log</string>
  <key>StandardErrorPath</key><string>$REPO/data/logs/fetch.log</string>
</dict></plist>
PL
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installerat: $PLIST (dag $DAY kl $HOUR:00). Logg: $REPO/data/logs/fetch.log"
echo "Testkör nu: launchctl kickstart gui/$(id -u)/$LABEL"
