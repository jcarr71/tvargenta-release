# TV-CBIA AI Coding Agent Instructions

## Project Overview
TV-CBIA (Community Broadcast Interactive Archive) is a retro TV emulation system that combines broadcast scheduling, physical NFC tape interaction, web management UI, and audio normalization. It's a Flask-based application running on Linux (primarily Raspberry Pi with RetroPie). The codebase is **100% vibe-coded with Claude** and emphasizes pragmatic solutions over complexity—this is intentional and a source of pride.

## Development Environment

**Operating System**: Windows (PowerShell)
- Always use PowerShell commands, not Linux/bash equivalents
- Use PowerShell syntax: `Get-ChildItem` instead of `ls`, `Select-String` instead of `grep`, `Test-Path` instead of `test`
- File paths use backslashes: `s:\VisualStudio\tvargenta-release\`
- Use `Test-Path` to check file existence
- Use `Get-Content` / `Set-Content` instead of `cat` / `echo`
- Use `Get-ChildItem -Recurse` instead of `find`
- Format output with `| Format-Table` or `| Out-String` for readability

**Development Context**:
- Primary editor: Visual Studio Code
- Primary shell: PowerShell (pwsh)
- Repository: `jcarr71/tvargenta-release` (GitHub) - TV-CBIA fork
- Default branch: `main`

## Major Recent Features (2025)
1. **VCR/NFC Tape System** - Physical NFC tags as mini "VHS tapes" with persistent playback position, rewind animations, and position saves every 30 seconds
2. **Broadcast TV Scheduler** - Authentic 1990s programming with weekly/daily schedule generation, time-of-day zones (Early Morning, Late Morning, Afternoon, Evening, Night)
3. **Enhanced Metadata Daemon** - 3-phase processing (directory scan → fast metadata → slow loudness analysis) with `nice`/`ionice` priority management
4. **Multi-Format Video Support** - `.mp4`, `.mkv`, `.webm`, `.mov` with dynamic extension detection and metadata storage

## Architecture

### Core Components
1. **Flask Web App** (`app.py`, 4200+ lines) - Central hub handling:
   - HTTP endpoints for video playback, channel management, uploads
   - JSON state persistence (atomic writes to prevent corruption)
   - Thread-safe metadata locking for concurrent access
   - Kiosk mode with auto-restart and Chromium integration

2. **Broadcast Scheduler** (`scheduler.py`) - Generates authentic 1990s TV programming:
   - **Weekly schedule** (Sundays 2:30 AM): Assigns series to time-of-day zones
   - **Daily schedule** (3:00 AM): Creates second-by-second playback mapping
   - **Time slots**: Early Morning (4-7am), Late Morning (7am-12pm), Afternoon (12-5pm), Evening (5-9pm), Night (9pm-3am)
   - **Episode cursor tracking**: Remembers series position for sequential playback
   - **Commercial breaks**: 3 per 30-minute block (start, middle, end)
   - Test pattern plays 3-4 AM daily
   - In-memory cache prevents disk I/O during playback

3. **Metadata Daemon** (`metadata_daemon.py`) - Background processor with 3 phases:
   - **Phase 0**: Directory scan for new series/commercial files
   - **Phase 1** (fast): Extract duration, generate thumbnails
   - **Phase 2** (slow): Analyze audio loudness (LUFS) using FFmpeg
   - Runs with `nice`/`ionice` to avoid impacting playback
   - Atomic file operations prevent race conditions with app

4. **VCR Manager** (`vcr_manager.py`) - NFC tape state management:
   - Persistent tape registry (NFC UID → video mapping)
   - Position persistence across sessions
   - Rewind speed: 45 seconds playback = 1 second rewind (formula: `position / 45`)
   - Atomic JSON writes, position saved every 30 seconds

5. **NFC Reader Daemon** (`nfc_reader.py`) - Hardware integration:
   - Monitors USB NFC reader (PN532) for tape insertion/removal
   - Updates `vcr_state.json` on tag events
   - Polls every 0.5 seconds, checks reader attachment every 5 seconds

### Data Files (in `content/` directory)
- `metadata.json` - Video info (duration, loudness, thumbnails, tags)
- `canales.json` - Channel definitions with tag filters
- `series.json` - Series metadata and time-of-day preferences
- `configuracion.json` - Global config (excluded tags, volume, timezone)
- `weekly_schedule.json` - Series→time slot assignment
- `daily_schedule.json` - Second-by-second playback map
- `episode_cursors.json` - Current position in each series
- `vcr_state.json` - NFC tape playback state
- `tapes.json` - NFC UID→video registry

## Key Workflows

### Video Upload Flow
1. Client sends multipart/form-data to `/upload`
2. Duplicate detection via client-side checksum
3. File moved to `content/videos/{category}/`
4. JSON state files updated atomically
5. Metadata daemon picks up in Phase 0 scan
6. Series detection: scans `content/videos/series/{Show Name}/Season {N}/`

### Schedule Generation
1. **Trigger**: Cron jobs at scheduled times (or manual "Rebuild Schedule" button in UI)
2. `scheduler.generate_weekly_schedule()` - maps series to time zones
3. `scheduler.generate_daily_schedule()` - creates playback sequence
4. Episode cursors incremented to track position
5. Loaded into memory at startup for fast lookup

### Tape Playback (VCR Mode)
1. NFC daemon detects tag → looks up in `tapes.json`
2. Updates `vcr_state.json` with position, pause state
3. Flask serves video from registered path
4. Position persisted every 30 seconds
5. On rewind: countdown animation, position reset, rewind audio plays

## Developer Patterns

### JSON Persistence (Critical)
```python
# ALWAYS use atomic writes to prevent corruption
def _write_json_atomic(path, data):
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)  # ensure_ascii=False for Spanish text
    tmp_path.replace(path)  # atomic on POSIX

# ALWAYS use metadata locking when reading/writing metadata.json
with metadata_lock(timeout=30):
    data = json.load(METADATA_FILE)
    # ... modify ...
    save_metadata(data)
```

**Critical Detail**: The codebase uses UTF-8 with Spanish support—always include `ensure_ascii=False` in `json.dump()` calls to preserve accents and special characters.

### Settings & Paths
- `settings.py` defines all paths as `Path` objects
- Environment variable `TVARGENTA_ROOT` overrides default location
- Respect `/srv/tv-cbia` for persistent system data vs `ROOT_DIR` for repo code
- Use `app_now()` for timezone-aware datetime (respects config timezone)

### User Configuration
- **No hardcoded usernames in code** - The app detects the current user via `getpass.getuser()`
- Environment variable `TVARGENTA_USER` can override user detection if needed
- `install.sh` dynamically generates systemd services with the correct user (via `${SUDO_USER:-$USER}`)
- Template service files in `Config_files/` use placeholder `<TVARGENTA_USER>` and should never be copied directly
- Always use `install.sh` for proper setup on new systems

### Logging
- Use standard Python `logging` module
- Log to `content/logs/` directory (rotating file handler)
- Include request context with `_hdr()` helper in web endpoints
- Use `logger.info()` for state changes, `logger.error()` for failures

### Multi-Format Video Support
- **Supported formats**: `.mp4`, `.mkv`, `.webm`, `.mov` (defined in `SUPPORTED_VIDEO_FORMATS` constant)
- **Extension handling**: All modules store/check file extensions via metadata `"extension"` field
- **Helper functions**:
  - `get_video_file_with_extension(video_id, base_dir)` - Find file with any supported format
  - `get_video_url(video_id, series_path)` - Generate correct URL with actual extension
- **Upload**: Preserves original file extension during upload (no forced `.mp4`)
- **Playback**: Dynamic URL generation ensures correct extension for series/commercials/regular videos
- **Metadata daemon**: Scans with `iterdir()` + suffix check, stores extension in metadata
- **Analyzer**: Uses stored extension field with fallback to `.mp4` for legacy metadata

### Thread Safety
- Metadata changes protected by file-based locking (fcntl)
- Episode cursors use atomic updates
- VCR state JSON writes are atomic
- Avoid shared mutable state; use JSON files as source of truth

## Testing
- Run `python3 test_scheduler.py` for scheduler validation (27+ test cases)
- Tests use temporary directories to avoid filesystem pollution
- Patch `settings.py` paths before importing modules under test
- Test data in memory (no external dependencies)
- Key test pattern: Use `tempfile.TemporaryDirectory()` + `monkeypatch.setattr()` for path isolation

## Critical Implementation Details

### Audio Processing
- Target loudness: `-16 LUFS` (fixed target for normalized volume)
- Daemon analyzes 30-second samples (not entire files) every 5 minutes
- Uses `ffmpeg -af loudnorm` for volume adjustment in playback
- Commercial volume matched to content volume

### Series Detection Convention
Directory structure: `content/videos/series/{Show Name}/Season {N}/{filename}`
- Show name extracted from folder (underscores become spaces for display)
- Season number extracted from folder name
- Filenames parsed for episode info: S or s followed by season number, E or e followed by episode number
- Invalid episodes logged but don't block other series

### Channel System
- Channels filter by tags (inclusion + exclusion)
- Special handling: Series-only channels have empty tag filters
- Categories: `tv_episode`, `pelicula`, `comercial`, `corto`
- Channel 03 reserved for VCR (physical NFC tape input)

### Broadcast Zones (Time-of-Day Programming)
- Series configured with preferred zone: `"time_of_day": "evening"`
- Scheduler distributes series proportionally by zone size
- "any" zone: series can play in any time slot
- Ensures authentic 1990s programming feel (cartoons morning, prime time evening)

## Common Tasks

### Mod vs System Component (Architecture Decision)

**What becomes a MOD** (optional, can be toggled on/off):
- **VCR/NFC Tape System** - Physical NFC tape interaction; can be disabled if reader not present
- **Broadcast Scheduler** - Optional daily/weekly schedule generation; can skip for direct video playback
- **Loudness Analyzer** - Optional audio normalization; performance trade-off on low-power devices

**What stays CORE** (always loaded):
- **WiFi Manager** - System infrastructure for network connectivity (essential)
- **Bluetooth Manager** - Hardware interface for connectivity
- **Encoder Reader** - RetroPie integration for game mode switching
- **Metadata Daemon** - Content discovery and file analysis (foundational)
- **Settings/Config** - Core configuration system

**Philosophy**: Mods are optional *features* the user can disable; core components are infrastructure that must always work.

### Add Feature Affecting Metadata
1. Update metadata schema in code
2. Add migration in `_bootstrap_config_from_tags_if_empty()`
3. Daemon Phase 1/2 handles retroactive population
4. Test with `test_scheduler.py` pattern (tempdir, path patching)

### Modify Scheduler Logic
1. Edit `scheduler.py` constants or functions
2. Run `test_scheduler.py` (covers edge cases: short eps, long eps, zone balancing)
3. Manual test: call `scheduler.generate_weekly_schedule()` from Flask endpoint

### Debug Playback Issues
1. Check `daily_schedule.json` generated correctly
2. Verify metadata has `duracion` field (daemon Phase 1)
3. Log video paths with `logger.info()` in `/play` endpoint
4. Check ALSA configuration in `Config_files/` for audio artifacts

### Profile Performance
- Metadata daemon uses sampling (30 sec every 5 min) not full analysis
- Schedule cached in memory at startup (load from `daily_schedule.json`)
- Reduce disk I/O: all state files must fit in `/tmp` or memory

## Setup & Running
```bash
# Install dependencies
pip install flask nfcpy

# Configure environment (optional)
export TVARGENTA_ROOT=/path/to/tvargenta

# Start app
python3 app.py

# Start daemons (systemd managed in production)
python3 metadata_daemon.py &
python3 nfc_reader.py &
```

See `install.sh` and `Config_files/` for systemd service definitions.

## Important Notes
- **No transcoding**: Videos moved directly, format must be compatible with playback
- **Supported formats**: `.mp4`, `.mkv`, `.webm`, `.mov` - all formats handled with dynamic extension detection
- **Extension storage**: Metadata stores actual file extension in `"extension"` field for correct playback
- **Helper functions**: Use `get_video_url()` and `get_video_file_with_extension()` for correct video path resolution
- **No external APIs**: Everything is file-based JSON state
- **Backwards compatible**: Metadata migrations must not break existing installs
- **Atomic > Perfect**: Prefer atomic writes that might lose a transaction over partial state
- **Low resource**: Runs on Raspberry Pi 4; respect `nice`/`ionice` levels

## Patching System (2025)

**Purpose**: Live-update capability without code changes or manual file management.

### Components
- `patch_system.py` - Core patch logic (VersionInfo, PatchManifest, apply/rollback)
- `generate_patch.py` - Command-line tool to create .tvpatch bundles
- `content/version.json` - Version tracking with patch history
- `templates/patches.html` - Web UI for applying/rolling back patches
- `/api/version`, `/api/patches/apply`, `/api/patches/rollback` - API endpoints

### Key Features
1. **Unified Diff Format** - Human-readable patches with hunk structure
2. **SHA256 Verification** - Checksum validation before application
3. **Automatic Backup** - Pre-patch backups with timestamp
4. **Rollback Support** - Full restoration to previous version
5. **Version Tracking** - Records all applied patches in version.json
6. **Atomic Operations** - Temp file → rename pattern for safety

### Workflow
```bash
# Generate patch from two versions
python3 generate_patch.py version1/ version2/ output.tvpatch --description "Update"

# Apply via web UI: /patches endpoint
# - Upload .tvpatch file
# - Verify compatibility (version_from must match current)
# - Backup changed files
# - Apply unified diffs
# - Trigger restart
```

### Error Recovery
- Patch checksum fails → Abort before changes
- Version mismatch → Reject with clear message
- Application fails → Automatic rollback from backup
- All errors logged with context for debugging

### Integration Points
- Core system (always loaded, not a mod)
- GET /api/version → App.py integration
- POST /api/patches/apply → Triggers restart via app restart handler
- Version tracking persisted across restarts

### Common Tasks
- **Create patch**: `python3 generate_patch.py old/ new/ patch.tvpatch`
- **Apply patch**: Upload via `/patches` UI or POST /api/patches/apply
- **Rollback**: Click Rollback button on `/patches` page
- **Check version**: GET /api/version or check content/version.json

See `PATCH_SYSTEM.md` for complete documentation.
