# Changelog

All notable changes to this project are documented in this file.

## 2026-02-16

### Added
- Repository architecture and file catalog document at [docs/REPO_CATALOG.md](docs/REPO_CATALOG.md).
- Keyboard controls in [templates/player.html](templates/player.html) for menu navigation, channel switching, volume, and VCR pause toggle.
- Bottom button controls in [templates/vertele.html](templates/vertele.html) for previous channel, forced next video, and next channel.
- Global broadcast mode API in [app.py](app.py): `GET/POST /api/broadcast_mode`.

### Changed
- Updated [app.py](app.py) `/api/next_video` to support `force=1` and skip ahead in scheduled broadcast blocks when forced.
- Updated [app.py](app.py) playback selection flow to respect global `broadcast_mode_enabled` setting.
- Implemented channel submenu handling in [templates/player.html](templates/player.html) for both “Predefined Channels” and “My Channels”.
- Improved channel cycling behavior in [templates/vertele.html](templates/vertele.html) with deterministic ordering and wrap-around.

### Fixed
- Resolved channel menu items not showing selectable channels in [templates/player.html](templates/player.html).
- Fixed watch-page channel wrap behavior and next-video button flow in [templates/vertele.html](templates/vertele.html).
- Added localization keys for broadcast mode in [templates/i18n/en.json](templates/i18n/en.json), [templates/i18n/es.json](templates/i18n/es.json), and [templates/i18n/de.json](templates/i18n/de.json).
