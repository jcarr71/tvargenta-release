# SPDX-License-Identifier: LicenseRef-TVArgenta-NC-Attribution-Consult-First
# Proyecto: TVArgenta — Retro TV
# Autor: Ricardo Sappia (rsflightronics@gmail.com)
# Gestión WiFi para TVArgenta (Bookworm + NetworkManager)
#
# Requiere:
#   - network-manager instalado y manejando wlan0
#   - nmcli disponible
#
# Nota:
#   - Las contraseñas quedan gestionadas por NetworkManager.
#   - En wifi_known.json solo se guarda la lista de SSID conocidos + metadatos,
#     no secretos.

import os
import json
import time
import random
import string
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone,timedelta

from settings import CONTENT_DIR, TMP_DIR
import io
import base64
import qrcode

WIFI_IFACE = os.environ.get("TVARGENTA_WIFI_IFACE", "wlan0")

AP_CON_NAME = os.environ.get("TVARGENTA_AP_CON_NAME", "tvargenta-ap")
AP_SSID_PREFIX = os.environ.get("TVARGENTA_AP_SSID_PREFIX", "TVArgenta-Setup-")
AP_PASSWORD_LEN = int(os.environ.get("TVARGENTA_AP_PASSLEN", "8"))

WIFI_KNOWN_FILE = Path(CONTENT_DIR) / "wifi_known.json"
AP_STATE_FILE = Path(TMP_DIR) / "wifi_ap_state.json"

NMCLI_BIN = "/usr/bin/nmcli"
USE_SUDO = True  # activamos sudo para nmcli

log = logging.getLogger("tvargenta.wifi")


# ---------- helpers JSON ----------

def _read_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ---------- helpers nmcli ----------

def _run_nmcli(args, timeout=15):
    """
    Ejecuta nmcli (con sudo si USE_SUDO=True) y devuelve (rc, out, err).
    """
    if USE_SUDO:
        cmd = ["sudo", NMCLI_BIN] + list(args)
    else:
        cmd = [NMCLI_BIN] + list(args)

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        rc, out, err = p.returncode, p.stdout.strip(), p.stderr.strip()
        log.debug(f"[nmcli] rc={rc} cmd={' '.join(cmd)} out={out!r} err={err!r}")
        return rc, out, err
    except subprocess.TimeoutExpired as e:
        log.error(f"[nmcli] TIMEOUT cmd={' '.join(cmd)} err={e}")
        return 124, "", f"timeout: {e}"

def _parse_iso(s: str):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------- redes conocidas ----------

def _load_known() -> dict:
    d = _read_json(WIFI_KNOWN_FILE, {})
    return d if isinstance(d, dict) else {}


def _save_known(d: dict):
    _write_json(WIFI_KNOWN_FILE, d)


def get_known_networks():
    """
    Devuelve lista de SSID conocidos (solo redes reales del usuario).
    Combina:
      - wifi_known.json
      - la red WiFi actualmente activa (auto-import)
    Ignora:
      - Cualquier SSID que empiece con AP_SSID_PREFIX (TVArgenta-Setup-)
    """
    known = _load_known()

    # 0) Limpiar entradas viejas de AP propio
    removed = []
    for s in list(known.keys()):
        if s.startswith(AP_SSID_PREFIX):
            removed.append(s)
            known.pop(s, None)
    if removed:
        log.info(f"[WiFi] get_known_networks: limpiando AP internos de known: {removed}")

    # 1) Detectar WiFi activo en wlan0 y auto-agregarlo si no es AP propio
    rc, out, _ = _run_nmcli(
        ["-t", "-f", "ACTIVE,SSID,DEVICE", "device", "wifi"],
        timeout=5
    )
    if rc == 0 and out:
        for line in out.splitlines():
            parts = line.split(":", 2)
            if len(parts) != 3:
                continue
            active, ssid, dev = parts
            ssid = ssid.strip()
            if (
                active == "yes"
                and dev == WIFI_IFACE
                and ssid
                and not ssid.startswith(AP_SSID_PREFIX)
            ):
                info = known.get(ssid, {})
                info.setdefault("priority", 0)
                info.setdefault("auto_imported", True)
                info["last_used"] = _now_iso()
                known[ssid] = info

    _save_known(known)

    # 2) Devolver solo SSIDs que no son de AP propio
    result = sorted(s for s in known.keys() if not s.startswith(AP_SSID_PREFIX))
    log.info(f"[WiFi] get_known_networks -> {result}")
    return result



def mark_known(ssid: str):
    if not ssid:
        return
    
    # No marcar nunca los AP propios como "conocidos"
    if ssid.startswith(AP_SSID_PREFIX):
        log.info(f"[WiFi] mark_known: ignorando SSID interno de AP {ssid!r}")
        return
        
    known = _load_known()
    info = known.get(ssid, {})
    info["last_used"] = _now_iso()
    # campo reservado para futuro (prioridades, etc.)
    info.setdefault("priority", 0)
    known[ssid] = info
    _save_known(known)


def forget_network(ssid: str):
    log.info(f"[WiFi] forget_network {ssid!r}")
    """
    Olvida un SSID:
      - lo borra de wifi_known.json
      - intenta borrar conexiones wifi asociadas en NM (best-effort)
    """
    ssid = (ssid or "").strip()
    if not ssid:
        return {"ok": False, "error": "missing_ssid"}

    known = _load_known()
    if ssid in known:
        known.pop(ssid, None)
        _save_known(known)

    # Intentar borrar conexiones con ese SSID
    rc, out, _ = _run_nmcli(["-t", "-f", "NAME,UUID,TYPE", "connection", "show"])
    if rc == 0 and out:
        for line in out.splitlines():
            name, uuid, ctype = (line.split(":", 2) + ["", "", ""])[:3]
            if ctype != "802-11-wireless":
                continue
            # preguntar SSID de ese profile
            rc2, ssid_out, _ = _run_nmcli(
                ["-s", "-g", "802-11-wireless.ssid", "connection", "show", uuid],
                timeout=5,
            )
            if rc2 == 0 and ssid_out.strip() == ssid:
                _run_nmcli(["connection", "delete", "uuid", uuid], timeout=5)

    log.info(f"[WiFi] forget_network OK ssid={ssid}")
    return {"ok": True, "ssid": ssid}



def restore_network_state():
    """
    Restaura condiciones normales después del modo AP.
    - Elimina la conexión AP si persiste.
    - Normaliza perfiles WiFi activos (ipv4 auto, sin ipv6 si así se desea).
    - Reafirma parámetros útiles para mDNS/LLMNR.
    - Reinicia solo Avahi (no NetworkManager) para no cortar WiFi.
    """
    try:
        log.info("[WiFi] restore_network_state() INICIO")

        # 1) Borrar conexión AP (si sigue existiendo)
        _run_nmcli(["connection", "delete", AP_CON_NAME], timeout=5)

        # 2) Detectar conexiones wifi activas (excepto el AP)
        rc, out, err = _run_nmcli(
            ["-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
            timeout=5,
        )
        if rc == 0 and out:
            for line in out.splitlines():
                name, ctype, dev = (line.split(":", 2) + ["", "", ""])[:3]
                if ctype != "802-11-wireless":
                    continue
                if name == AP_CON_NAME:
                    continue
                if dev != WIFI_IFACE:
                    continue

                log.info(f"[WiFi] restore_network_state: normalizando perfil activo '{name}'")

                # IPv4 por DHCP normal
                _run_nmcli(["connection", "modify", name, "ipv4.method", "auto"], timeout=5)

                # Si querés matar IPv6 por diseño de TVArgenta, dejá esto:
                _run_nmcli(["connection", "modify", name, "ipv6.method", "ignore"], timeout=5)

                # Hints para mDNS/LLMNR (algunos NM los ignoran, pero no molestan)
                _run_nmcli([
                    "connection", "modify", name,
                    "connection.mdns", "yes",
                    "connection.llmnr", "yes",
                ], timeout=5)

        # 3) Reiniciar sólo Avahi para refrescar anuncios mDNS
        try:
            subprocess.run(
                ["sudo", "systemctl", "restart", "avahi-daemon"],
                check=False
            )
            log.info("[WiFi] restore_network_state: avahi-daemon reiniciado")
        except Exception as e:
            log.warning(f"[WiFi] restore_network_state: no se pudo reiniciar avahi-daemon: {e}")

        log.info("[WiFi] restore_network_state() FIN OK")

    except Exception as e:
        log.error(f"[WiFi] restore_network_state: ERROR {e}")


# ---------- estado actual ----------

def get_status():
    """
    Devuelve:
      - mode: "ap" | "client" | "disconnected" | "error"
      - ssid: SSID actual (o None)
      - iface: interfaz WiFi usada
    """
    log.info("[WiFi] get_status()")

    # 1) Ver estado de dispositivos
    rc_dev, out_dev, err_dev = _run_nmcli(
        ["-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"]
    )
    if rc_dev != 0:
        log.error(f"[WiFi] get_status: nmcli device rc={rc_dev} err={err_dev!r}")
        return {"mode": "error", "ssid": None, "iface": WIFI_IFACE}

    wifi_state = None
    wifi_con = None

    for line in out_dev.splitlines():
        if not line.strip():
            continue
        parts = line.split(":", 3)
        if len(parts) < 3:
            continue
        dev, typ, state = parts[0], parts[1], parts[2]
        con = parts[3] if len(parts) > 3 else ""
        if dev == WIFI_IFACE and typ == "wifi":
            wifi_state = state
            wifi_con = con
            break

    # 2) Ver SSID activo (si lo hay)
    ssid = None
    rc_wifi, out_wifi, err_wifi = _run_nmcli(
        ["-t", "-f", "ACTIVE,SSID,DEVICE", "device", "wifi"]
    )
    if rc_wifi == 0:
        for line in out_wifi.splitlines():
            if not line.strip():
                continue
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            active, s, dev = parts
            if active == "yes" and dev == WIFI_IFACE:
                ssid = s or None
                break
    else:
        log.warning(f"[WiFi] get_status: nmcli device wifi rc={rc_wifi} err={err_wifi!r}")

    # 3) Determinar modo
    # AP detectado: SSID TVArgenta-Setup-XXXX o conexión tvargenta-ap activa
    is_ap = False
    if ssid and ssid.startswith("TVArgenta-Setup-"):
        is_ap = True
    elif wifi_con == AP_CON_NAME:
        is_ap = True

    if is_ap:
        log.info(f"[WiFi] get_status -> mode=ap ssid={ssid!r} iface={WIFI_IFACE}")
        return {"mode": "ap", "ssid": ssid, "iface": WIFI_IFACE}

    # Cliente conectado
    if wifi_state and wifi_state.startswith("connected") and ssid:
        log.info(f"[WiFi] get_status -> mode=client ssid={ssid!r} iface={WIFI_IFACE}")
        return {"mode": "client", "ssid": ssid, "iface": WIFI_IFACE}

    # Nada conectado
    log.info(f"[WiFi] get_status -> mode=disconnected iface={WIFI_IFACE}")
    return {"mode": "disconnected", "ssid": None, "iface": WIFI_IFACE}


# ---------- escaneo y mejor conocida ----------

def scan_networks():
    log.info("[WiFi] scan_networks()")
    """
    Devuelve lista de redes:
      [{"ssid": "...", "signal": 0-100}, ...]
    """
    # trigger rescan (no importa si falla)
    _run_nmcli(["device", "wifi", "rescan", "ifname", WIFI_IFACE], timeout=10)

    rc, out, err = _run_nmcli(
        ["-t", "-f", "SSID,SIGNAL", "device", "wifi", "list", "ifname", WIFI_IFACE],
        timeout=10,
    )
    if rc != 0:
        return []

    nets = []
    for line in out.splitlines():
        if not line:
            continue
        ssid, sig = (line.split(":", 1) + ["", ""])[:2]
        ssid = ssid.strip()
        if not ssid:
            continue
        if ssid.startswith(AP_SSID_PREFIX):
            continue  # no listar nuestro propio AP en el selector
        try:
            signal = int(sig or "0")
        except ValueError:
            signal = 0
        nets.append({"ssid": ssid, "signal": signal})
    # eliminar duplicados quedándose con mejor señal
    dedup = {}
    for n in nets:
        cur = dedup.get(n["ssid"])
        if not cur or n["signal"] > cur["signal"]:
            dedup[n["ssid"]] = n
    log.info(f"[WiFi] scan_networks -> {len(dedup)} networks")
    return sorted(dedup.values(), key=lambda x: x["signal"], reverse=True)
    

def _wait_for_ip(iface=WIFI_IFACE, timeout=25, interval=1.5):
    """
    Espera hasta timeout a que NM asigne IP al iface.
    Devuelve (ip4, ip6) o (None, None).
    """
    deadline = time.time() + timeout
    got4 = None
    got6 = None

    while time.time() < deadline:
        rc4, out4, err4 = _run_nmcli(
            ["-g", "IP4.ADDRESS", "device", "show", iface],
            timeout=3,
        )
        rc6, out6, err6 = _run_nmcli(
            ["-g", "IP6.ADDRESS", "device", "show", iface],
            timeout=3,
        )

        if rc4 == 0 and out4.strip():
            first = out4.splitlines()[0].strip()
            got4 = (first.split("/", 1)[0] or "").strip() or None

        if rc6 == 0 and out6.strip():
            first6 = out6.splitlines()[0].strip()
            got6 = (first6.split("/", 1)[0] or "").strip() or None

        log.info(f"[WiFi] wait_ip: ip4={got4} ip6={got6}")

        if got4 or got6:
            break

        time.sleep(interval)

    return got4, got6



def choose_best_known_and_connect():
    log.info("[WiFi] choose_best_known_and_connect()")

    known = _load_known()
    if not known:
        log.info("[WiFi] apply_best: no hay redes conocidas en wifi_known.json")
        return {"ok": False, "error": "no_known"}

    # 1) Escanear visibles
    scan = scan_networks()
    visible_by_ssid = {n["ssid"]: n for n in scan if n.get("ssid")}

    # 2) Mapear perfiles WiFi por SSID real (modo compatible)
    rc, out, err = _run_nmcli(
        ["-t", "-f", "NAME,UUID,TYPE", "connection", "show"]
    )
    if rc != 0:
        log.error(
            "[WiFi] apply_best: nmcli connection show fallo rc=%s err=%r",
            rc, err
        )
        return {"ok": False, "error": "nmcli_failed"}

    profiles_by_ssid = {}

    for line in out.splitlines():
        if not line.strip():
            continue
        name, uuid, ctype = (line.split(":", 2) + ["", "", ""])[:3]
        if ctype != "802-11-wireless":
            continue

        # pedir SSID de ese perfil
        rc2, pssid, err2 = _run_nmcli(
            ["-s", "-g", "802-11-wireless.ssid", "connection", "show", uuid],
            timeout=3,
        )
        if rc2 != 0:
            # algunas conexiones pueden no tener este campo, las ignoramos
            log.debug(
                "[WiFi] apply_best: no pude leer SSID de perfil %s (%s): rc=%s err=%r",
                name, uuid, rc2, err2
            )
            continue

        pssid = (pssid or "").strip()
        if not pssid:
            continue
        if pssid.startswith(AP_SSID_PREFIX):
            continue

        profiles_by_ssid.setdefault(pssid, []).append((name, uuid))

    # 3) Candidatos = conocidos + visibles + con perfil
    candidates = []
    for ssid, meta in known.items():
        if ssid in visible_by_ssid and ssid in profiles_by_ssid:
            strength = visible_by_ssid[ssid].get("signal", 0)
            prio = meta.get("priority", 0)
            candidates.append((prio, strength, ssid))

    if not candidates:
        log.info("[WiFi] apply_best: no hay redes conocidas visibles con perfil válido")
        return {"ok": False, "error": "no_known_visible"}

    # ordenar por prioridad y señal descendente
    candidates.sort(key=lambda x: (-x[0], -x[1]))

    for prio, strength, ssid in candidates:
        for name, uuid in profiles_by_ssid.get(ssid, []):
            log.info(
                "[WiFi] apply_best: intentando ssid=%r via perfil '%s' (%s), prio=%s signal=%s",
                ssid, name, uuid, prio, strength
            )
            rc_up, out_up, err_up = _run_nmcli(["connection", "up", "uuid", uuid])
            if rc_up != 0:
                log.warning(
                    "[WiFi] apply_best: fallo levantar '%s' rc=%s err=%r",
                    name, rc_up, err_up
                )
                continue

            ip4, ip6 = _wait_for_ip()
            if ip4 or ip6:
                log.info("[WiFi] apply_best: conectado a %r ip4=%s ip6=%s", ssid, ip4, ip6)
                mark_known(ssid)
                return {"ok": True, "ssid": ssid, "ip4": ip4, "ip6": ip6}

            log.warning(
                "[WiFi] apply_best: sin IP tras levantar '%s', probando siguiente",
                name
            )

    log.error("[WiFi] apply_best: ninguna red conocida obtuvo IP")
    return {"ok": False, "error": "no_ip_assigned"}


# ---------- modo AP (hotspot) ----------

def _random_password(length=AP_PASSWORD_LEN):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def stop_ap_mode():
    """
    Apaga el modo AP si está activo y limpia estado.
    NO intenta decidir a qué WiFi conectarse: eso lo hace
    connect_with_credentials o choose_best_known_and_connect().
    """
    log.info("[WiFi] stop_ap_mode()")

    # 1) Best-effort: bajar y borrar la conexión AP
    _run_nmcli(["connection", "down", AP_CON_NAME], timeout=10)
    _run_nmcli(["connection", "delete", AP_CON_NAME], timeout=5)

    # 2) Borrar estado persistente del AP
    try:
        AP_STATE_FILE.unlink()
    except FileNotFoundError:
        pass
    except Exception as e:
        log.warning(f"[WiFi] stop_ap_mode: no pude borrar AP_STATE_FILE: {e}")

    # 3) Normalizar parámetros
    restore_network_state()

    # 4) Nada más acá. No llamamos device connect / apply_best automáticamente.
    return {"ok": True}



def cleanup_ap_if_stale(max_age_seconds: int = 180):
    """
    Si hay un AP registrado en AP_STATE_FILE pero:
      - tiene más de max_age_seconds, o
      - nmcli ya no muestra la conexión AP activa,
    se limpia para evitar quedar clavado en modo AP.
    """
    info = _read_json(AP_STATE_FILE, {})
    if not info:
        return

    # ¿sigue activa la conexión AP?
    rc, out, _ = _run_nmcli(
        ["-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
        timeout=5,
    )
    ap_active = False
    if rc == 0 and out:
        for line in out.splitlines():
            name, ctype, dev = (line.split(":", 2) + ["", "", ""])[:3]
            if name == AP_CON_NAME and dev == WIFI_IFACE:
                ap_active = True
                break

    started = _parse_iso(info.get("started_at", ""))

    if not ap_active:
        log.info("[WiFi] cleanup_ap_if_stale: AP_CON_NAME no activo -> stop_ap_mode()")
        stop_ap_mode()
        return

    if started:
        age = (datetime.now(timezone.utc) - started).total_seconds()
        if age > max_age_seconds:
            log.info(f"[WiFi] cleanup_ap_if_stale: AP viejo ({age:.0f}s) -> stop_ap_mode()")
            stop_ap_mode()


def start_ap_mode():
    log.info("[WiFi] start_ap_mode() requested")
    """
    Sube un AP propio para onboarding:
      - baja conexiones wifi previas en WIFI_IFACE
      - crea/levanta conexión AP_CON_NAME
      - guarda info en AP_STATE_FILE
    Devuelve:
      {"ap_ssid": "...", "ap_password": "...", "qr": "WIFI:...;"}
    """
    # bajar conexiones activas de ese iface (best-effort)
    _run_nmcli(["device", "disconnect", WIFI_IFACE], timeout=10)

    # limpiar conexión previa AP si existe
    _run_nmcli(["connection", "down", AP_CON_NAME], timeout=5)
    _run_nmcli(["connection", "delete", AP_CON_NAME], timeout=5)

    ssid = f"{AP_SSID_PREFIX}{random.randint(1000, 9999)}"
    #password = _random_password()
    password = "TVA123456"

    # crear conexión tipo AP
    rc, out, err = _run_nmcli([
        "connection", "add",
        "type", "wifi",
        "ifname", WIFI_IFACE,
        "mode", "ap",
        "con-name", AP_CON_NAME,
        "ssid", ssid,
    ], timeout=10)
    if rc != 0:
        return {"ok": False, "error": f"nmcli add failed: {err or out}"}

    # configurar seguridad + NAT compartida
    _run_nmcli([
        "connection", "modify", AP_CON_NAME,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "ipv4.method", "shared",
        "ipv6.method", "ignore",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", password,
    ], timeout=10)

    rc_up, out_up, err_up = _run_nmcli(
        ["connection", "up", AP_CON_NAME],
        timeout=20,
    )
    if rc_up != 0:
        # limpieza si falla
        _run_nmcli(["connection", "delete", AP_CON_NAME], timeout=5)
        return {"ok": False, "error": f"ap_up_failed: {err_up or out_up}"}
        
    # obtener ip del AP (ej: 10.42.0.1 u otra)
    ap_ip = _get_iface_ipv4_addr(WIFI_IFACE) or "10.42.0.1"       

    data = {
        "ssid": ssid,
        "password": password,
        "started_at": _now_iso(),
        "ap_ip": ap_ip
    }
    _write_json(AP_STATE_FILE, data)

    qr_text_wifi = f"WIFI:T:WPA;S:{ssid};P:{password};;"
    # URL a la cual queremos que vaya el celular una vez conectado:
    ap_url = f"http://{ap_ip}:5000/wifi_setup"  # <-- tu template wifi_setup.html
    # QR para la URL (para abrir la página de configuración)
    qr_url_data = _make_qr_data_url(ap_url) if qrcode else None

    # QR para la configuración WIFI (WIFI:... - para que el celu lo agregue automáticamente)
    qr_wifi_data = _make_qr_data_url(qr_text_wifi) if qrcode else None

    log.info(f"[WiFi] AP up ssid={ssid} pass={password} ip={ap_ip}")

    return {
        "ok": True,
        "ap_ssid": ssid,
        "ap_password": password,
        "ap_ip": ap_ip,
        "ap_url": ap_url,
        "qr_ap_url": qr_url_data,   # data URL PNG para abrir la página (http)
        "qr_wifi": qr_wifi_data,    # data URL PNG con WIFI:... (para que el celu lo guarde)
        "qr_text_wifi": qr_text_wifi
    }


def connect_with_credentials(ssid: str, password: str | None):
    log.info(f"[WiFi] connect_with_credentials ssid={ssid!r} has_pass={bool(password)}")

    ssid = (ssid or "").strip()
    if not ssid:
        return {"ok": False, "error": "missing_ssid"}

    # 1) Apagar AP si estaba activo (best-effort)
    _run_nmcli(["connection", "down", AP_CON_NAME], timeout=10)
    _run_nmcli(["connection", "delete", AP_CON_NAME], timeout=5)
    try:
        AP_STATE_FILE.unlink()
    except FileNotFoundError:
        pass

    con_name = f"TVA_{ssid}"

    # 2) Limpiar perfil previo con mismo nombre
    _run_nmcli(["connection", "delete", con_name], timeout=5)

    # 3) Intentar conectar usando nmcli dev wifi connect (modo directo)
    args = ["device", "wifi", "connect", ssid, "ifname", WIFI_IFACE, "name", con_name]
    if password:
        args += ["password", password]

    rc, out, err = _run_nmcli(args, timeout=30)
    msg = (err or out or "").lower()
    log.info(f"[WiFi] nmcli connect rc={rc} out={out!r} err={err!r}")

    if rc != 0 and "activation was enqueued" not in msg:
        # Si la red no se ve, creamos perfil manualmente para uso futuro
        if "no network with ssid" in msg:
            log.warning(
                "[WiFi] connect_with_credentials: SSID no visible, creando perfil persistente para %r",
                ssid
            )

            # Crear perfil tipo wifi sin requerir que esté visible
            rc_add, out_add, err_add = _run_nmcli([
                "connection", "add",
                "type", "wifi",
                "ifname", WIFI_IFACE,
                "con-name", con_name,
                "ssid", ssid,
            ], timeout=10)

            if rc_add == 0:
                if password:
                    _run_nmcli([
                        "connection", "modify", con_name,
                        "wifi-sec.key-mgmt", "wpa-psk",
                        "wifi-sec.psk", password,
                    ], timeout=10)
                else:
                    # red abierta
                    _run_nmcli([
                        "connection", "modify", con_name,
                        "wifi-sec.key-mgmt", "none",
                    ], timeout=10)

                mark_known(ssid)
                log.info(
                    "[WiFi] connect_with_credentials: perfil creado para %r aunque no se pudo conectar ahora",
                    ssid
                )
                # Devolvemos error de conexión pero perfil listo
                return {
                    "ok": False,
                    "error": "network_not_visible_profile_saved",
                    "ssid": ssid,
                }

            log.error(
                "[WiFi] connect_with_credentials: fallo crear perfil manual rc=%s out=%r err=%r",
                rc_add, out_add, err_add
            )

        log.error("[WiFi] connect_with_credentials FAILED rc=%s out=%r err=%r", rc, out, err)
        return {"ok": False, "error": err or "nmcli_failed"}

    if "activation was enqueued" in msg:
        log.warning("[WiFi] connect_with_credentials: activation enqueued; espero como async")

    # 4) Esperar IP
    ip4, ip6 = _wait_for_ip()

    if not ip4 and not ip6:
        log.error(
            f"[WiFi] connect_with_credentials: sin IP para {ssid!r} tras timeout "
            f"(ip4={ip4}, ip6={ip6})"
        )
        # dejamos el perfil creado para futuros apply_best()
        mark_known(ssid)
        return {
            "ok": False,
            "error": "no_ip_assigned",
            "ssid": ssid,
            "ip4": ip4,
            "ip6": ip6,
        }

    # 5) Éxito
    log.info(f"[WiFi] connect_with_credentials OK ssid={ssid}, ip4={ip4}, ip6={ip6}")

    try:
        AP_STATE_FILE.unlink()
    except FileNotFoundError:
        pass

    restore_network_state()
    mark_known(ssid)

    return {"ok": True, "ssid": ssid, "ip4": ip4, "ip6": ip6}


# -------------------------QR Helpers-------------------------    
def _get_iface_ipv4_addr(iface=WIFI_IFACE):
    """
    Intenta obtener la IP IPv4 asignada al iface. Primero con nmcli, luego con ip.
    Devuelve string ip o None.
    """
    try:
        rc, out, err = _run_nmcli(["-g", "IP4.ADDRESS", "device", "show", iface], timeout=3)
        if rc == 0 and out:
            # nmcli puede devolver '192.168.x.x/24' o múltiples entradas
            first = out.splitlines()[0].strip()
            ip = first.split("/")[0].strip()
            if ip:
                return ip
    except Exception:
        pass

    # fallback a comando ip
    try:
        p = subprocess.run(["/sbin/ip", "-4", "addr", "show", iface], capture_output=True, text=True, timeout=3)
        out = p.stdout or ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                ip = line.split()[1].split("/")[0]
                return ip
    except Exception:
        pass
    return None


def _make_qr_data_url(text: str, box_size=6, border=2):
    """
    Genera un PNG data URL con el contenido text. Requiere qrcode + pillow.
    Si no está la librería devuelve None.
    """
    if not qrcode:
        log.warning("[WiFi] qrcode library not available, QR data URL won't be generated.")
        return None
    try:
        qr = qrcode.QRCode(box_size=box_size, border=border, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        b64 = base64.b64encode(bio.read()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        log.exception(f"[WiFi] _make_qr_data_url failed: {e}")
        return None

    
# --- fin de helpers y funciones Wi-Fi ---

# Intentar no quedar pegado en AP entre reinicios
try:
    cleanup_ap_if_stale(max_age_seconds=180)
except Exception as e:
    log.warning(f"[WiFi] cleanup_ap_if_stale on import failed: {e}")

