#!/bin/bash
set -euo pipefail
LOG=/tmp/watch-emustation.log

ts() { date "+[%a %d %b %H:%M:%S %Z %Y]"; }

echo "$(ts) [watch] ==== watcher start ====" >> "$LOG"

# función que espera a que el servicio deje de estar activo
wait_until_dead() {
    echo "$(ts) [watch] entrando en modo 'seguir hasta que muera ES'..." >> "$LOG"
    while systemctl is-active --quiet emulationstation-session.service; do
        sleep 1
    done
    echo "$(ts) [watch] detecté que ES terminó" >> "$LOG"
}

# 1. ¿EmulationStation ya está activa cuando arranca el watcher?
if systemctl is-active --quiet emulationstation-session.service; then
    echo "$(ts) [watch] ES ya estaba ACTIVA al iniciar watcher" >> "$LOG"
    wait_until_dead
else
    echo "$(ts) [watch] ES todavía NO está activa, espero que arranque..." >> "$LOG"

    # esperamos hasta 10s a que se active (para cubrir la "carrera" de arranque)
    limit=$((SECONDS+10))
    while ! systemctl is-active --quiet emulationstation-session.service; do
        if [ $SECONDS -ge $limit ]; then
            echo "$(ts) [watch] timeout esperando que ES arranque. Me voy." >> "$LOG"
            exit 0
        fi
        sleep 0.5
    done

    echo "$(ts) [watch] ES se activó dentro de la ventana -> ahora sigo hasta que muera" >> "$LOG"
    wait_until_dead
fi

# 2. Si llegamos acá es porque ES murió. Volvemos a TVArgenta.
echo "$(ts) [watch] lanzando return-tvargenta.service" >> "$LOG"
systemctl start return-tvargenta.service || true
echo "$(ts) [watch] watcher done, bye" >> "$LOG"

