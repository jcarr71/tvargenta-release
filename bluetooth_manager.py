import subprocess
import time
import re
import traceback

# --------------------------
# Helpers internos
# --------------------------

def _log(msg):
    # Todo lo que pase por acá termina en journalctl -u tvargenta.service -f
    print(f"[BT] {msg}")

# Patron para lineas "Device XX:XX:.. Nombre Bonito"
_device_re = re.compile(r"Device\s+([0-9A-Fa-f:]{17})\s+(.+)$")


def _run_bt_cmd(args, timeout=5, check=True):
    """
    Ejecuta bluetoothctl y devuelve stdout completo.
    Si check=True levanta excepción si el exit code !=0 (como antes).
    """
    full_cmd = ["sudo", "-n", "/usr/bin/bluetoothctl"] + args
    _log(f"RUN {full_cmd}")
    proc = subprocess.run(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        text=True,
        check=check
    )
    out = proc.stdout
    _log(f"OUT {args[0]} -> {out.strip()}")
    return out

def _fire_and_forget(args):
    """
    Lanza un bluetoothctl que no esperamos que termine rápido
    (ej: 'scan on') y no bloqueamos.
    """
    full_cmd = ["sudo", "-n", "/usr/bin/bluetoothctl"] + args
    _log(f"FIRE {full_cmd}")
    subprocess.Popen(
        full_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # no return; esto no bloquea, no revienta



def _parse_devices_list(raw_text):
    """
    Devuelve lista [{ 'mac': 'XX:..', 'name': 'Algo' }, ...]
    a partir de líneas bluetoothctl tipo 'Device XX:XX... Nombre'.
    """
    found = []
    for line in raw_text.splitlines():
        line = line.strip()
        m = _device_re.search(line)
        if m:
            mac = m.group(1).upper()
            name = m.group(2).strip()
            found.append({
                "mac": mac,
                "name": name
            })
    return found


# --------------------------
# Funciones expuestas
# --------------------------

def ensure_adapter_on():
    _log("ensure_adapter_on: BEGIN")
    status = {
        "power_cmd_ok": False,
        "powered": None,
        "agent_set": False,
        "default_agent_ok": False,
        "err": None,
    }

    # 1. intentar power on
    try:
        out_power = _run_bt_cmd(["power", "on"], timeout=2, check=True)
        _log(f"OUT power -> {out_power.strip()}")
        status["power_cmd_ok"] = True
    except subprocess.CalledProcessError as e:
        status["err"] = f"power on FAILED: {e}"
        # capturá igual salida parcial si existe (para log)
        _log(f"ensure_adapter_on: power on FAILED {e}")
        # seguimos, pero marcamos que falló

    # 1b. chequeo del adaptador de verdad
    try:
        # bluetoothctl show te dice Powered: yes/no
        out_show = _run_bt_cmd(["show"], timeout=2, check=False)
        # parse Powered:
        powered = None
        for line in out_show.splitlines():
            line = line.strip()
            if line.startswith("Powered:"):
                powered = "yes" in line
        status["powered"] = powered
        _log(f"ensure_adapter_on: adapter Powered={powered}")
    except Exception as e:
        _log(f"ensure_adapter_on: show FAILED {e}")
        if status["powered"] is None:
            status["powered"] = False  # ni idea → asumimos off

    # 2. agent on
    try:
        out_agent = _run_bt_cmd(["agent", "on"], timeout=2, check=False)
        _log(f"OUT agent -> {out_agent.strip()}")
        status["agent_set"] = True
    except Exception as e:
        _log(f"agent on FAILED {e}")

    # 3. default-agent (puede fallar SIEMPRE en tu placa, eso ya lo vimos; no lo tratemos como fatal)
    try:
        out_def = _run_bt_cmd(["default-agent"], timeout=2, check=False)
        _log(f"OUT default-agent -> {out_def.strip()}")
        status["default_agent_ok"] = True
    except Exception as e:
        _log(f"default-agent WARN {e}")

    _log(f"ensure_adapter_on: END -> {status}")
    return status



def get_paired_devices():
    """
    Devuelve lista de dispositivos emparejados conocidos por BlueZ.
    Formato:
    [
      { "mac": "AA:BB:CC:DD:EE:FF",
        "name": "Pro Controller",
        "connected": True/False,
        "trusted": True/False
      },
      ...
    ]
    """
    _log("get_paired_devices: BEGIN")

    devices = []
    
    show_before = _run_bt_cmd(["show"], timeout=2, check=False)
    _log(f"get_paired_devices: adapter show -> {show_before.strip()}")
    raw_list = _run_bt_cmd(["devices"], timeout=2, check=False)
    _log(f"OUT devices -> {raw_list.strip()}")

    # 1. Pedimos la lista general de dispositivos que bluez conoce
    # Ejemplo de raw_list:
    # "Device E4:17:D8:E2:63:A7 Pro Controller\nDevice 4C:B9:EA:41:A1:17 j715840\n..."

    for line in raw_list.splitlines():
        line = line.strip()
        # buscamos líneas tipo:
        # Device XX:XX:XX:XX:XX:XX Name Here
        if not line.startswith("Device "):
            continue
        parts = line.split(" ", 2)
        # parts[0] = "Device"
        # parts[1] = MAC
        # parts[2] = nombre (puede faltar => usamos MAC después)
        if len(parts) < 2:
            continue
        mac = parts[1].strip()
        name = parts[2].strip() if len(parts) >= 3 else mac

        # 2. Para cada device, pedimos info detallada
        raw_info = _run_bt_cmd(["info", mac], timeout=3, check=False)
        # ahora parseamos flags del info:
        paired = False
        trusted = False
        connected = False

        for iline in raw_info.splitlines():
            iline = iline.strip()
            if iline.startswith("Paired:"):
                # ej "Paired: yes"
                paired = "yes" in iline
            elif iline.startswith("Bonded:"):
                # algunos mandos usan "Bonded: yes" en vez de Paired
                if "yes" in iline:
                    paired = True
            elif iline.startswith("Trusted:"):
                trusted = "yes" in iline
            elif iline.startswith("Connected:"):
                connected = "yes" in iline
            elif iline.startswith("Name:"):
                # forzamos name más humano si lo vemos acá
                # ej "Name: Pro Controller"
                n = iline.split(":", 1)[1].strip()
                if n:
                    name = n

        if paired:
            devices.append({
                "mac": mac,
                "name": name,
                "trusted": trusted,
                "connected": connected,
            })

    _log(f"get_paired_devices: END -> {len(devices)} devices => {devices}")
    return devices




def scan_new_devices(timeout_s=5):
    _log(f"scan_new_devices: BEGIN ({timeout_s}s)")
    cycle = {"adapter_ok": False, "err": None}

    st = ensure_adapter_on()
    if not st["powered"]:
        cycle["err"] = "adapter not powered"
        _log(f"scan_new_devices: adapter not powered -> {st}")
        return {
            "ok": False,
            "adapter_down": True,
            "devices": [],
            "debug": st,
        }

    # arrancamos el scan en background (no bloqueante)
    _log("FIRE ['scan', 'on']")
    try:
        _run_bt_cmd(["scan", "on"], timeout=1, check=False)
    except Exception as e:
        cycle["err"] = f"scan on failed: {e}"
        _log(f"scan_new_devices: scan on FAILED {e}")

    # esperamos timeout_s
    time.sleep(timeout_s)

    # listamos devices
    raw_list = _run_bt_cmd(["devices"], timeout=2, check=False)
    _log(f"OUT devices -> {raw_list.strip()}")

    # apagamos scan
    _log("FIRE ['scan', 'off']")
    try:
        _run_bt_cmd(["scan", "off"], timeout=1, check=False)
    except Exception as e:
        _log(f"scan_new_devices: scan off WARN {e}")

    # parseamos
    found = []
    for line in raw_list.splitlines():
        line = line.strip()
        if not line.startswith("Device "):
            continue
        parts = line.split(" ", 2)
        if len(parts) >= 2:
            mac = parts[1].strip()
            name = parts[2].strip() if len(parts) >= 3 else mac
            found.append({"mac": mac, "name": name})

    cycle["adapter_ok"] = True
    _log(f"scan_new_devices: END -> {len(found)} devices, cycle={cycle}")
    return {
        "ok": True,
        "adapter_down": False,
        "devices": found,
        "debug": st,
    }


def get_unpaired_devices():
    """
    Devuelve los escaneados que NO están todavía emparejados.
    """
    _log("get_unpaired_devices: BEGIN")
    try:
        scan_res = scan_new_devices(timeout_s=5)
    except Exception as e:
        _log(f"get_unpaired_devices: scan_new_devices ERROR {e}")
        return []

    paired_list = get_paired_devices()
    paired_macs = {d["mac"] for d in paired_list}

    # scan_res viene como {"ok":..., "devices":[...]}
    fresh = [
        d for d in scan_res.get("devices", [])
        if d["mac"] not in paired_macs
    ]

    _log(f"get_unpaired_devices: END -> {len(fresh)} new devices (excluding {len(paired_macs)} paired)")
    return fresh



def connect_device(mac):
    """
    Conecta un dispositivo ya emparejado (ej. reconectar auriculares).
    """
    _log(f"connect_device: BEGIN {mac}")
    try:
        out = _run_bt_cmd(["connect", mac], timeout=6)
        ok = ("Connection successful" in out) or ("Connected: yes" in out)
        _log(f"connect_device: END ok={ok}")
        return {"ok": ok, "raw": out}
    except Exception as e:
        _log(f"connect_device FAILED {e}")
        _log(traceback.format_exc())
        return {"ok": False, "err": str(e)}


def disconnect_device(mac):
    _log(f"disconnect_device: BEGIN {mac}")
    try:
        out = _run_bt_cmd(["disconnect", mac], timeout=6)
        ok = ("Successful disconnected" in out) or ("Connected: no" in out)
        _log(f"disconnect_device: END ok={ok}")
        return {"ok": ok, "raw": out}
    except Exception as e:
        _log(f"disconnect_device FAILED {e}")
        _log(traceback.format_exc())
        return {"ok": False, "err": str(e)}


def forget_device(mac):
    """
    Borra el bonding/record del sistema.
    """
    _log(f"forget_device: BEGIN {mac}")
    try:
        out = _run_bt_cmd(["remove", mac], timeout=6)
        ok = ("Device has been removed" in out) or ("not available" not in out)
        _log(f"forget_device: END ok={ok}")
        return {"ok": ok, "raw": out}
    except Exception as e:
        _log(f"forget_device FAILED {e}")
        _log(traceback.format_exc())
        return {"ok": False, "err": str(e)}


def pair_and_connect(mac):
    _log(f"pair_and_connect: BEGIN {mac}")
    log_lines = []

    def run(args, timeout=8, check=False):
        out = _run_bt_cmd(args, timeout=timeout, check=check)
        log_lines.append(f"$ bluetoothctl {' '.join(args)}\n{out}")
        return out

    ok = True
    err = None
    paired = False
    trusted = False
    connected = False

    # 1. power on y agente NoInputNoOutput (best effort)
    run(["power", "on"], check=False)
    run(["agent", "NoInputNoOutput"], check=False)
    run(["default-agent"], check=False)  # puede fallar, no importa

    # 2. mirar estado actual del device antes de tocar nada
    info_before = run(["info", mac], check=False)
    already_paired   = ("Paired: yes"   in info_before) or ("Bonded: yes" in info_before)
    already_trusted  = ("Trusted: yes"  in info_before)
    already_connected= ("Connected: yes" in info_before)

    _log(f"pair_and_connect: info_before for {mac} -> paired={already_paired} trusted={already_trusted} connected={already_connected}")

    # Si ya está conectado, listo
    if already_connected:
        paired = already_paired
        trusted = already_trusted
        connected = True
        result = {
            "ok": True,
            "paired": paired,
            "trusted": trusted,
            "connected": connected,
            "err": None,
            "log": log_lines,
        }
        _log(f"pair_and_connect: END (already connected) -> {result}")
        return result

    # 3. Si no estaba paired, intentamos pair
    if not already_paired:
        out_pair = run(["pair", mac], check=False)
        if ("Pairing successful" in out_pair or
            "Paired: yes" in out_pair or
            "Bonded: yes" in out_pair):
            paired = True
        else:
            # si pair falla posta, cortamos temprano
            if "Failed" in out_pair or "not available" in out_pair or "Authentication Failed" in out_pair:
                ok = False
                err = "pair_failed"
                result = {
                    "ok": ok,
                    "paired": paired,
                    "trusted": trusted,
                    "connected": connected,
                    "err": err,
                    "log": log_lines,
                }
                _log(f"pair_and_connect: END (pair failed) -> {result}")
                return result
        # si no marcó explícitamente failed, asumimos paired=True igual.
        if not paired:
            paired = True

    else:
        paired = True

    # 4. Trust si hace falta
    if not already_trusted:
        out_trust = run(["trust", mac], check=False)
        if ("trust succeeded" in out_trust or "Trusted: yes" in out_trust):
            trusted = True
        else:
            trusted = already_trusted
    else:
        trusted = True

    # 5. Intentar connect hasta 2 veces
    if not already_connected:
        for attempt in [1, 2]:
            out_conn = run(["connect", mac], timeout=8, check=False)
            if ("Connection successful" in out_conn or "Connected: yes" in out_conn):
                connected = True
                break
            _log(f"pair_and_connect: connect attempt {attempt} for {mac} got: {out_conn.strip()}")

    result = {
        "ok": connected or paired,  # si al menos quedó emparejado lo damos por ok-ish
        "paired": paired,
        "trusted": trusted,
        "connected": connected,
        "err": err,
        "log": log_lines,
    }

    _log(f"pair_and_connect: END -> {result}")
    return result

