#!/bin/bash
set -euo pipefail
LOG=/tmp/encoder-hotkey-loop.log
READER_BIN="/srv/tvargenta/encoder_reader"

HOLD_SEC=2

echo "[$(date)] [hotkey] start loop" >> "$LOG"

press_t0=""

$READER_BIN | while read -r ev; do
    now_ts=$(date +%s)

    case "$ev" in
        BTN_NEXT)
            echo "[$(date)] [hotkey] BTN_NEXT -> stop emulationstation-session.service" >> "$LOG"
            systemctl stop emulationstation-session.service || true
            break
            ;;
        BTN_PRESS)
            press_t0=$now_ts
            ;;
        BTN_RELEASE)
            if [ -n "$press_t0" ]; then
                dur=$(( now_ts - press_t0 ))
                echo "[$(date)] [hotkey] BTN_RELEASE dur=${dur}s" >> "$LOG"
                if [ "$dur" -ge "$HOLD_SEC" ]; then
                    echo "[$(date)] [hotkey] hold largo (${dur}s) -> stop emulationstation-session.service" >> "$LOG"
                    systemctl stop emulationstation-session.service || true
                    break
                fi
                press_t0=""
            fi
            ;;
        *)
            ;;
    esac
done

echo "[$(date)] [hotkey] loop terminado, bye" >> "$LOG"
exit 0

