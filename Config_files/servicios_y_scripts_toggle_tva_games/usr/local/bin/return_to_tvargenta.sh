#!/bin/bash
set -euo pipefail
LOG=/tmp/volver-tvargenta.log
IMG="/srv/tvargenta/Splash/splash.png"
FBIDX=0
SPL=""

echo "[$(date)] volver-tvargenta: start uid=$(id -u)" >> "$LOG"

# splash
if [ -f "$IMG" ]; then
  fbv -d "$FBIDX" -n -f "$IMG" >/dev/null 2>&1 &
  SPL=$!
fi

echo "[$(date)] volver-tvargenta: stopping encoder-hotkey.service" >> "$LOG"
systemctl stop encoder-hotkey.service || true

echo "[$(date)] volver-tvargenta: starting tvargenta.service" >> "$LOG"
systemctl start tvargenta.service || true

if [ -n "$SPL" ]; then
  kill "$SPL" 2>/dev/null || true
fi

echo "[$(date)] volver-tvargenta: done" >> "$LOG"
exit 0

