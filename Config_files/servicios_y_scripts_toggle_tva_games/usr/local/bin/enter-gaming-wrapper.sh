#!/bin/bash
set -euo pipefail
LOG=/tmp/enter-gaming-wrapper.log
IMG="/srv/tvargenta/Splash/splash.png"
FBIDX=0
SPL=""

echo "[$(date)] [enter] start enter-gaming-wrapper" >> "$LOG"

# splash temporal
if [ -f "$IMG" ]; then
  fbv -d "$FBIDX" -n -f "$IMG" >/dev/null 2>&1 &
  SPL=$!
fi

# apagar TVArgenta
echo "[$(date)] [enter] stopping tvargenta.service" >> "$LOG"
systemctl stop tvargenta.service || true

# matar procesos de encoder del modo TV
pkill -TERM -f '/srv/tvargenta/encoder_reader' 2>/dev/null || true
pkill -TERM -f 'tvargenta_encoder.py' 2>/dev/null || true

# levantar listener del botón
echo "[$(date)] [enter] starting encoder-hotkey.service" >> "$LOG"
systemctl start encoder-hotkey.service || true

# lanzar EmulationStation
echo "[$(date)] [enter] starting emulationstation-session.service" >> "$LOG"
systemctl start emulationstation-session.service || true

# lanzar watcher que detecta cuando ES termina
echo "[$(date)] [enter] starting watch-emustation.service" >> "$LOG"
systemctl start watch-emustation.service || true

# sacar splash
if [ -n "$SPL" ]; then
  kill "$SPL" 2>/dev/null || true
fi

echo "[$(date)] [enter] done enter-gaming-wrapper" >> "$LOG"
exit 0

