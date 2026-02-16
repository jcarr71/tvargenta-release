# TVArgenta Repository Catalog (Working Document)

Last updated: 2026-02-16

This document catalogs the repository and explains how files work together at runtime on Raspberry Pi.

---

## 1) System Overview

TVArgenta is a Flask-based retro TV platform that runs locally on Raspberry Pi. It combines:

- A backend app (`app.py`) that serves UI pages and APIs.
- A scheduler (`scheduler.py`) for broadcast-style programming blocks.
- Media metadata background processing (`metadata_daemon.py`).
- Hardware input support (rotary encoder via `encoder_reader.c` + `tvargenta_encoder.py`).
- Optional NFC/VCR physical tape simulation (`nfc_reader.py`, `vcr_manager.py`).
- Wi-Fi/Bluetooth device management (`wifi_manager.py`, `bluetooth_manager.py`).
- Kiosk playback/UI templates (`templates/*.html`, `static/*`).

---

## 2) Runtime Architecture (How It Works Together)

### 2.1 Boot and Process Startup

1. `systemd` starts `tvargenta.service` (installed by `install.sh` or from `Config_files/.../tvargenta.service`).
2. `app.py` starts and initializes logging, state files, and defaults.
3. `app.py` launches helper/background processes:
   - `tvargenta_encoder.py` (reads encoder events from compiled `encoder_reader` binary)
   - `nfc_reader.py` (if available)
   - `metadata_daemon.py`
4. `app.py` initializes scheduler (`scheduler.initialize_scheduler()`):
   - Ensures system videos exist (e.g., test pattern)
   - Regenerates schedules if needed
   - Starts scheduler background loop
5. Flask serves routes/templates and API polling endpoints used by frontend pages (`player.html`, `splash.html`, etc).

### 2.2 Playback Path

- Frontend player (`templates/player.html`) polls APIs such as `/api/next_video`, `/api/should_reload`, `/api/played`, `/api/volumen*`, `/api/menu*`, `/api/vcr/*`, `/api/wifi/*`, `/api/bt/*`.
- `app.py` decides next content based on:
  - Active channel
  - Broadcast mode (`scheduler.py`) if channel has `series_filter`
  - VCR channel (Channel `03`)
  - fallback/no-content behavior

### 2.3 Scheduler Path

- `scheduler.py` writes/reads:
  - `content/weekly_schedule.json`
  - `content/daily_schedule.json`
  - `content/episode_cursors.json`
  - `content/schedule_meta.json`
- Daily schedule uses 3AM–3AM day model; 3AM–4AM is test pattern.
- Missing system media are generated automatically under `content/videos/system/`.

### 2.4 Metadata Path

- `metadata_daemon.py` runs continuously:
  - Phase 0: scans folders for series/commercial files
  - Phase 1: duration + thumbnails
  - Phase 2: loudness analysis (LUFS)
- It updates `content/metadata.json` with lock-protected writes.

### 2.5 Encoder/Input Path

- `encoder_reader.c` emits hardware events (`ROTARY_CW`, `ROTARY_CCW`, `BTN_PRESS`, `BTN_RELEASE`, `BTN_NEXT`).
- `tvargenta_encoder.py` interprets those events and writes trigger files in `/tmp`.
- `app.py` + frontend polling consumes those triggers to update channel, volume, menu, VCR actions.

### 2.6 VCR/NFC Path

- `nfc_reader.py` watches NFC tags (via `nfcpy`) and updates VCR state via `vcr_manager.py`.
- `vcr_manager.py` manages:
  - Runtime state in `/tmp/vcr_state.json`
  - Persistent tape registry in `content/tapes.json`
  - Position persistence and rewind logic
- `app.py` exposes VCR admin, tape registration, playback/rewind endpoints and Channel `03` behavior.

### 2.7 Network/Connectivity Path

- `wifi_manager.py` uses `nmcli` to handle AP mode, client mode, known networks, QR output.
- `bluetooth_manager.py` uses `bluetoothctl` (via sudo) for scan/pair/connect/disconnect/forget.
- `app.py` provides REST endpoints consumed by player and setup pages.

---

## 3) Data and State Files

### 3.1 Persistent (`content/`)

- `content/metadata.json`: media metadata (title, category, tags, duration, loudness, series/commercial paths).
- `content/canales.json`: channel definitions.
- `content/canal_activo.json`: currently active channel.
- `content/configuracion.json`: app-level config/preferences.
- `content/tags.json`: tags/group taxonomy.
- `content/series.json`: detected and configured series metadata.
- `content/tapes.json`: NFC tape registry + stored tape positions.
- `content/weekly_schedule.json`, `content/daily_schedule.json`, `content/episode_cursors.json`, `content/schedule_meta.json`: scheduler state.
- `content/wifi_known.json`: known Wi-Fi SSIDs metadata.
- `content/volumen.json`: persisted volume.
- `content/plays.json` (in `/srv/tvargenta/content` preferred): play counters/history.

### 3.2 Runtime (`/tmp`)

- `trigger_reload.json`: request frontend video reload.
- `tvargenta_volumen.json`, `trigger_volumen.json`: current volume + updates.
- `menu_state.json`, `trigger_menu.json`, `trigger_menu_nav.json`, `trigger_menu_select.json`: menu state/events.
- `vcr_state.json`, `trigger_vcr*.json`, `vcr_recording_state.json`: VCR runtime state/events.
- `upload_status.txt`: upload progress.
- `wifi_ap_state.json`: AP mode session state.
- splash/kiosk ping files: frontend ↔ backend liveness and intro behavior.

---

## 4) Source Catalog (Top-Level Files)

| File | Purpose | Key Behavior / Entry Points |
|---|---|---|
| `app.py` | Main Flask server and orchestrator | Defines routes/apis, launches side processes, scheduler init, kiosk control, media serving, upload and admin flows |
| `scheduler.py` | Broadcast schedule engine | Weekly/daily generation, test pattern scheduling, content lookup by timestamp, background regeneration loop |
| `settings.py` | Shared constants/config/timezone | Root/content/tmp/system paths, JSON file constants, `app_now()` timezone helper |
| `metadata_daemon.py` | Background metadata worker | Phase-based scan/duration/thumb/loudness processing with lock-safe metadata writes |
| `wifi_manager.py` | Wi-Fi orchestration | AP/client mode, scan/connect, known network persistence, QR generation |
| `bluetooth_manager.py` | Bluetooth orchestration | Adapter prep, device scan, paired listing, pair/connect/disconnect/forget |
| `vcr_manager.py` | VCR runtime/persistence logic | Tape registry, VCR state, pause/rewind/position logic, persistence timers |
| `nfc_reader.py` | NFC daemon | Detects NFC reader/tags and updates VCR state using `vcr_manager` |
| `tvargenta_encoder.py` | Encoder event interpreter | Consumes `encoder_reader` output; emits trigger files for channel/menu/volume/VCR |
| `encoder_reader.c` | GPIO rotary/button reader | Low-level event emitter binary used by `tvargenta_encoder.py` |
| `player_utils.py` | Channel helper utility | `cambiar_canal()` updates active channel and channel queue logic |
| `analyze_loudness.py` | One-off CLI utility | Backfills loudness metadata for existing files |
| `encoder_menu.py` | Encoder helper class | `EncoderHandler` wrapper around RPi.GPIO interrupts |
| `encoder_test.py` | Hardware test script | Manual GPIO loop for encoder/button verification |
| `test_scheduler.py` | Test harness for scheduler | Exercises scheduling logic, edge cases, URL mapping, test pattern behavior |
| `install.sh` | Installation/provisioning script | Modular installer (`install_app`, `setup_venv`, `build_encoder`, `install_services`, etc.) |
| `README.md` | Feature/change narrative | High-level project and fork summary |
| `README.en.md` | English setup guidance | Flash image and legacy manual setup instructions |
| `LICENSE` | License terms | Legal terms for distribution/use |
| `NOTICE` | Notice/attribution | Legal attribution/supporting notice |
| `.editorconfig` | Editor formatting defaults | Cross-editor consistency |
| `.gitattributes` | Git attributes | Line ending and file handling metadata |
| `.gitignore` | Ignore rules | Excludes generated/runtime artifacts |

---

## 5) UI Templates Catalog (`templates/`)

### 5.1 Core Layout and Playback

| File | Purpose |
|---|---|
| `templates/base.html` | Shared layout shell for management pages |
| `templates/player.html` | Main TV playback UI, overlays, polling logic, VCR visual modes |
| `templates/splash.html` | Boot/intro splash playback and transition logic |
| `templates/kiosk_boot.html` | Kiosk boot-related UI page |
| `templates/video.html` | Individual video view |
| `templates/vertele.html` | TV view/legacy viewing flow |

### 5.2 Library/Channel/Admin Pages

| File | Purpose |
|---|---|
| `templates/index.html` | Main management dashboard/library view |
| `templates/edit.html` | Edit metadata/tags for a video |
| `templates/canales.html` | Channel management page |
| `templates/series.html` | TV series management page |
| `templates/upload.html` | Generic upload page |
| `templates/upload_series.html` | Series upload workflow |
| `templates/upload_commercials.html` | Commercials upload workflow |
| `templates/wifi_setup.html` | Wi-Fi AP/client setup UI |
| `templates/vcr_admin.html` | VCR tape admin/registration UI |
| `templates/vcr_record.html` | VCR recording assignment/flow UI |

### 5.3 Observed Route-Template Mismatch

- `app.py` contains render calls for `tags.html` and `configuracion.html`.
- Those files are not present in current tree snapshot.
- Action item: confirm if those templates are intentionally removed or missing.

---

## 6) Internationalization Files (`templates/i18n/`)

Each JSON file contains localized UI strings used by corresponding pages/features.

### 6.1 Global Language Dictionaries

- `templates/i18n/es.json`
- `templates/i18n/en.json`
- `templates/i18n/de.json`

### 6.2 Page-Specific Dictionaries

- `templates/i18n/index_es.json`, `index_en.json`, `index_de.json`
- `templates/i18n/canales_es.json`, `canales_en.json`, `canales_de.json`
- `templates/i18n/configuracion_es.json`, `configuracion_en.json`, `configuracion_de.json`
- `templates/i18n/tags_es.json`, `tags_en.json`, `tags_de.json`
- `templates/i18n/upload_es.json`, `upload_en.json`, `upload_de.json`
- `templates/i18n/vertele_es.json`, `vertele_en.json`, `vertele_de.json`
- `templates/i18n/wifi_setup_es.json`, `wifi_setup_en.json`, `wifi_setup_de.json`

---

## 7) Static/UI Assets Catalog (`static/`, `Splash/`, `assets/`)

### 7.1 Static Assets (`static/`)

| File | Purpose |
|---|---|
| `static/tailwind.css` | Main CSS bundle for management UI |
| `static/sortable.min.js` | Sortable list helper JS |
| `static/css/tvargenta-wifi.css` | Wi-Fi setup page styling |
| `static/vcr_static.mp4` | VCR channel no-tape/static visual media |
| `static/vcr_rewind.mp3` | Rewind audio effect |
| `static/no_signal.png` | No signal fallback graphic |
| `static/background.png` | Background image asset |
| `static/logo_tvar.png`, `static/logo_tvar_2.png` | Branding logos |

### 7.2 Splash Assets (`Splash/`)

| File | Purpose |
|---|---|
| `Splash/splash_1.png` ... `Splash/splash_5.png` | Static splash images |
| `Splash/splash_screen_TVA.mp4` | Splash/intro media |
| `Splash/videos/splash_1.mp4` ... `splash_5.mp4` | Rotating splash intro clips |

### 7.3 Font Assets (`assets/`)

| File | Purpose |
|---|---|
| `assets/fuentes/perfect_dos_vga_437.ttf` | Pixel/retro font resource |

---

## 8) Deployment and System Integration Files (`Config_files/`)

### 8.1 Audio Keepalive

| File | Purpose |
|---|---|
| `Config_files/audio_keepalive/README.txt` | Audio config notes |
| `Config_files/audio_keepalive/etc/asound.conf` | ALSA config used for HiFiBerry/dmix behavior |

### 8.2 Gaming Toggle Services and Scripts

| File | Purpose |
|---|---|
| `Config_files/servicios_y_scripts_toggle_tva_games/README.txt` | Overview of service/script integration |
| `Config_files/servicios_y_scripts_toggle_tva_games/servicios_y_scripts_toggle_tva_games.rar` | Archived bundle of service/script files |
| `.../etc/systemd/system/tvargenta.service` | Main TVArgenta systemd unit template |
| `.../etc/systemd/system/emulationstation-session.service` | Starts EmulationStation session |
| `.../etc/systemd/system/enter-gaming.service` | Switch into gaming mode |
| `.../etc/systemd/system/return-tvargenta.service` | Return from gaming mode |
| `.../etc/systemd/system/watch-emustation.service` | Watches emulation session exit |
| `.../etc/systemd/system/encoder-hotkey.service` | Encoder long-press hotkey service |
| `.../usr/local/bin/launch-es` | Launch helper |
| `.../usr/local/bin/enter-gaming-wrapper.sh` | Gaming entry wrapper script |
| `.../usr/local/bin/return_to_tvargenta.sh` | Return-to-TV wrapper script |
| `.../usr/local/bin/watch-emustation.sh` | Emulation watcher script |
| `.../usr/local/bin/encoder-hotkey-loop.sh` | Encoder hotkey loop script |
| `.../srv/tvargenta/encoder_reader` | Prebuilt encoder binary artifact |
| `.../opt/retropie/configs/all/retroarch.cfg` | RetroArch config payload |

---

## 9) Documentation Catalog (`docs/`)

| File | Purpose |
|---|---|
| `docs/VCR_NFC_IMPLEMENTATION_PLAN.md` | Design and rollout plan for VCR/NFC feature set |
| `docs/REPO_CATALOG.md` | This architecture and file responsibility working document |

---

## 10) External Dependencies and Tools

### 10.1 Python Libraries

- Flask / Werkzeug / Jinja2
- websockets
- Pillow
- qrcode
- av
- gpiozero
- RPi.GPIO
- dbus-python
- python-dotenv
- psutil
- python-uinput
- nfcpy

### 10.2 System Binaries and Services

- `ffmpeg`, `ffprobe`
- `nmcli` (NetworkManager)
- `bluetoothctl`
- `chromium` / browser kiosk process
- `systemctl`, `pkill`, `shutdown`
- `gcc`, `libgpiod` headers/runtime
- `wget` or `curl` (scheduler system-media generation)

---

## 11) File-to-Feature Crosswalk

| Feature | Primary Files |
|---|---|
| Core web app/API | `app.py`, `templates/*`, `static/*` |
| Broadcast scheduling | `scheduler.py`, `test_scheduler.py` |
| Metadata automation | `metadata_daemon.py`, `analyze_loudness.py` |
| VCR/NFC tapes | `vcr_manager.py`, `nfc_reader.py`, `templates/vcr_*.html`, `docs/VCR_NFC_IMPLEMENTATION_PLAN.md` |
| Hardware encoder controls | `encoder_reader.c`, `tvargenta_encoder.py`, `player_utils.py`, `encoder_*` scripts |
| Wi-Fi onboarding | `wifi_manager.py`, `templates/wifi_setup.html`, `static/css/tvargenta-wifi.css` |
| Bluetooth pairing | `bluetooth_manager.py`, `app.py` BT API routes |
| Pi installation/deployment | `install.sh`, `Config_files/**`, `README.en.md` |

---

## 12) Known Gaps / Follow-Up Items

1. Confirm missing templates referenced in routes (`tags.html`, `configuracion.html`) versus current tree.
2. Decide whether to keep both generated and templated service definitions (`install.sh` creates services dynamically, while `Config_files/.../systemd` contains static templates).
3. Consider adding a machine-readable manifest (e.g., `docs/repo_index.json`) for future automated audits.

---

## 13) Maintenance Notes (How to Keep This Current)

- Update this file whenever:
  - New top-level modules are added.
  - New templates/routes are introduced.
  - New runtime state files in `/tmp` or `content/` are added.
  - Service/deployment scripts are modified.
- For each new file, include:
  - Purpose
  - Primary callers/callees
  - Data files read/written
  - External dependencies (if any)
