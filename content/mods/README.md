# TVArgenta Modular System

TVArgenta now supports a lightweight mod/plugin system that allows optional features to be installed and enabled/disabled via a GUI.

## Architecture

### Core vs Mods

**Core** (always loaded):
- Basic playback (`/tv`, `/play`)
- Channel management  
- File discovery and metadata
- Settings and internationalization
- WiFi Manager - network connectivity (system infrastructure)
- Bluetooth Manager - hardware interface
- Encoder Reader - RetroPie integration
- Metadata Daemon - content scanning and analysis

**Mods** (optional, can be enabled/disabled):
- VCR/NFC Tape System - Physical NFC interaction
- Broadcast Scheduler - Daily/weekly schedule generation, episode tracking
- Loudness Analyzer - Audio normalization
- Audio Equalizer - 3-band EQ with presets (Bass, Mid, Treble)

## Mod Structure

Each mod lives in `content/mods/{mod_name}/`:

```
content/mods/my_mod/
├── manifest.json          # Mod metadata and settings
├── __init__.py           # Package marker
├── handlers.py           # Route handlers and logic
├── static/               # CSS, JS, images
└── templates/            # HTML templates (optional)
```

### manifest.json

```json
{
  "id": "my_mod",
  "name": "My Custom Mod",
  "version": "1.0.0",
  "enabled": true,
  "description": "What this mod does",
  "entry_point": "my_mod.handlers",
  "author": "Your Name",
  "dependencies": [],
  "settings": {}
}
```

## Creating a Mod

### 1. Create mod directory structure

```bash
mkdir -p content/mods/my_mod
touch content/mods/my_mod/__init__.py
touch content/mods/my_mod/manifest.json
touch content/mods/my_mod/handlers.py
```

### 2. Define manifest.json

```json
{
  "id": "my_mod",
  "name": "My Feature",
  "version": "1.0.0",
  "enabled": true,
  "description": "Adds cool feature X",
  "entry_point": "my_mod.handlers"
}
```

### 3. Implement handlers.py

```python
def init_mod(registry):
    """Called when mod is loaded"""
    print("My mod is initializing!")

def get_routes():
    """Return Flask routes"""
    return [
        ('/my_route', my_handler, ['GET', 'POST']),
    ]

def get_hooks():
    """Return hook callbacks"""
    return {
        'channel_changed': on_channel_changed,
    }

def my_handler():
    """Route handler"""
    from flask import jsonify
    return jsonify({"message": "Hello from my mod!"})

def on_channel_changed(channel_id):
    """Hook callback - called when channel changes"""
    print(f"Channel changed to {channel_id}")
```

### 4. Optional: __init__.py

```python
__version__ = '1.0.0'
from . import handlers

__all__ = ['handlers']
```

## Managing Mods

### Via Python API

```python
from mod_system import ModRegistry
from settings import CONTENT_DIR

registry = ModRegistry(CONTENT_DIR / 'mods')
registry.load_mods()

# List all mods
registry.list_mods()  # ['vcr_mod', 'my_mod']

# Get a specific mod
mod = registry.get_mod('vcr_mod')

# Enable/disable (requires app restart)
registry.enable_mod('my_mod')
registry.disable_mod('my_mod')
```

### Via GUI (Future)

A web interface will allow users to:
- View installed mods
- Enable/disable mods
- Configure mod settings
- Install new mods from a repository

## Hook System

Mods can register callbacks for system events:

```python
def get_hooks():
    return {
        'channel_changed': on_channel_changed,
        'video_loaded': on_video_loaded,
        'playback_stopped': on_playback_stopped,
    }
```

**Available hooks:**
- `channel_changed(channel_id)` - Channel was changed
- `video_loaded(video_id, info)` - Video metadata loaded  
- `playback_started(video_id)` - Video playback started
- `playback_stopped(video_id)` - Video playback stopped
- `metadata_updated()` - Metadata refreshed

## Best Practices

1. **Keep mods self-contained** - Don't rely on internal app state
2. **Use atomic file writes** - Like the core app does
3. **Add logging** - `logger = logging.getLogger("tvargenta.mods.my_mod")`
4. **Handle missing dependencies** - Check if required packages are installed
5. **Don't modify core state** - Use hooks instead of direct state changes
6. **Document configuration** - Include settings in manifest.json

## VCR Mod Example

The VCR/NFC tape system has been refactored as a mod:

- **Location:** `content/mods/vcr_mod/`
- **Routes:** `/api/vcr/*`, `/vcr_admin`, `/vcr_record`
- **Files:** `vcr_manager.py`, `nfc_reader.py` (unchanged)
- **Status:** Fully functional as optional mod

## Troubleshooting

### Mod not loading?

1. Check manifest.json is valid JSON
2. Check entry_point module exists
3. Check app logs: `tail -f content/logs/tvargenta.log`
4. Verify `init_mod()` function exists in handlers.py

### Routes not registered?

1. Ensure `get_routes()` returns list of tuples: `[(rule, function, methods), ...]`
2. Check Flask route conflicts with other mods
3. Restart app after enabling mod

## Future Improvements

- GUI mod manager (enable/disable without restart)
- Mod marketplace/repository
- Configuration UI for mod settings
- Mod dependencies resolution
- Hot reload (restart-free mod loading)
