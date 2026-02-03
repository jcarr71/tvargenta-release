# TV-CBIA Copilot Instructions

## Big picture (where to look)
- Flask monolith: `app.py` is the hub for playback, uploads, channels, and JSON state.
- Background services: `metadata_daemon.py` (3-phase scan/metadata/loudness), `scheduler.py` (daily/weekly schedule), `nfc_reader.py` + `vcr_manager.py` (VCR/NFC tapes).
- State lives in `content/*.json` (metadata, channels, schedules, VCR state). Treat JSON files as the source of truth.

## Project-specific patterns
- **Atomic JSON writes**: write to `*.tmp` then rename; always `ensure_ascii=False` for Spanish text. See `_write_json_atomic()` in `app.py` and `metadata_daemon.py`.
- **Metadata locking**: wrap `metadata.json` reads/writes in `metadata_lock(...)` to avoid races between app and daemon.
- **Paths**: use `settings.py` `Path` objects; respect `TVARGENTA_ROOT` for system installs.
- **Multi-format video**: supported extensions are `.mp4/.mkv/.webm/.mov`. Preserve original extension and use helpers like `get_video_file_with_extension()` / `get_video_url()` (see `app.py`).
- **Channel 03 is VCR**: don't reuse it for other features; VCR mode reads `content/vcr_state.json`.

## Mods system
- Optional features live in `content/mods/<mod_id>/` with `manifest.json` + `handlers.py` (see `content/mods/README.md`).
- Core vs mod boundaries matter: VCR, scheduler, loudness are mods; WiFi/Bluetooth/metadata are core.
- Mods register routes via `get_routes()` and hooks via `get_hooks()` in handlers.py.

## Workflows & tooling
- Scheduler tests: run `python test_scheduler.py` (covers schedule edge cases with mocked time/data).
- Patch system: `patch_system.py` + `tools/generate_patch.py`, version tracked in `content/version.json`, UI in `templates/patches.html`.
- Metadata daemon: run `python metadata_daemon.py` for background processing (3 phases: scan, fast metadata, loudness).
- Individual services: run `python app.py`, `python scheduler.py`, etc. for debugging.

## Dev environment
- Windows workspace: prefer PowerShell commands and `s:\VisualStudio\tvargenta-release\` paths when running local scripts.
- Raspberry Pi target: see `INSTALL.md` for deployment; uses systemd services, ALSA audio, Chromium kiosk.
