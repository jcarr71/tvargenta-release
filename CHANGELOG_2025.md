# TVArgenta 2025 Update

Recent enhancements (January 2025):

## Modular Architecture & Mod System

The application now uses a lightweight modular system for optional features.

### Core Components (Always Loaded)
- Flask web application
- WiFi Manager - Network connectivity
- Bluetooth Manager - Device pairing
- Metadata Daemon - Content indexing
- Encoder Integration - RetroPie control

### Optional Mods (GUI Installable)
Manage mods via `/mod_manager`:

1. **VCR/NFC Mod** - Physical NFC tape interaction
   - Tape position persistence
   - Rewind animations
   - QR code recording
   
2. **Audio EQ Mod** - Real-time equalizer
   - 5 presets (Flat, Warm, Bright, Bass Boost, Dialogue)
   - 3-band parametric control
   - Web Audio API processing

3. **Scheduler Mod** - Broadcast TV scheduling
   - 1990s programming authenticity
   - Time-of-day zones
   - Weekly/daily schedule generation

Each mod can be toggled on/off via the mod manager UI.

## Live Patching System

Update the application without code deployment or manual file changes.

### Creating Patches
```bash
python3 generate_patch.py version_1.0.0/ version_1.0.1/ patch.tvpatch \
  --description "Feature update"
```

### Applying Patches
- Navigate to `/patches`
- Drag & drop .tvpatch file
- Click "Apply Patch"
- App automatically restarts

### Rollback Support
- Automatic backup before applying patch
- Rollback button if backup available
- Full restoration to previous version

**See [PATCH_SYSTEM.md](PATCH_SYSTEM.md) for complete documentation**

## Key Improvements

### Code Quality
- ✅ Translated entire codebase to English
- ✅ Consistent naming conventions
- ✅ Comprehensive error handling
- ✅ Production-ready logging

### Architecture
- ✅ Optional mod system for extensibility
- ✅ Live-update capability
- ✅ Atomic file operations (safe concurrent access)
- ✅ Version tracking

### User Experience
- ✅ Mod Manager UI (`/mod_manager`)
- ✅ Patch Manager UI (`/patches`)
- ✅ Real-time status updates
- ✅ Toast notifications

## Documentation

**For Users**:
- [PATCH_QUICKSTART.py](PATCH_QUICKSTART.py) - Step-by-step examples
- [PATCH_SYSTEM.md](PATCH_SYSTEM.md) - Complete patching guide

**For Developers**:
- [MOD_SYSTEM_COMPLETE.md](MOD_SYSTEM_COMPLETE.md) - Architecture guide
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - AI agent guide
- [SESSION_COMPLETE_SUMMARY.md](SESSION_COMPLETE_SUMMARY.md) - Implementation summary

**API Endpoints**:
- `GET /api/mods` - List installed mods
- `POST /api/mods/{id}/toggle` - Enable/disable mod
- `POST /api/mods/{id}/settings` - Save mod settings
- `GET /api/version` - Get app version
- `POST /api/patches/apply` - Apply patch
- `POST /api/patches/rollback` - Rollback patch

## Testing

All new code verified to compile without errors:
- ✅ `patch_system.py` - No syntax errors
- ✅ `generate_patch.py` - No syntax errors  
- ✅ `mod_system.py` - No syntax errors
- ✅ `app.py` - No syntax errors (with patch integration)

## File Structure

```
tvargenta-release/
├── patch_system.py              (new)
├── generate_patch.py            (new)
├── mod_system.py                (existing, enhanced)
├── content/
│   ├── version.json             (new)
│   ├── backups/                 (new)
│   │   └── backup_patch_*/      (patch backups)
│   └── mods/
│       ├── vcr_mod/             (existing)
│       ├── eq_mod/              (existing)
│       └── scheduler_mod/       (existing)
├── templates/
│   ├── mod_manager.html         (existing)
│   └── patches.html             (new)
├── PATCH_SYSTEM.md              (new)
├── PATCH_QUICKSTART.py          (new)
└── SESSION_COMPLETE_SUMMARY.md  (new)
```

## Quick Start

### Access Mod Manager
```
http://localhost:5000/mod_manager
```

### Access Patch Manager
```
http://localhost:5000/patches
```

### Create a Patch
```bash
python3 generate_patch.py old_version/ new_version/ patch.tvpatch --description "Update"
```

### Apply a Patch
1. Go to `/patches`
2. Upload patch file
3. Click "Apply"
4. App restarts

### Check Version
```bash
curl http://localhost:5000/api/version | jq .
```

## Troubleshooting

See [PATCH_QUICKSTART.py](PATCH_QUICKSTART.py) troubleshooting section or [PATCH_SYSTEM.md](PATCH_SYSTEM.md) for detailed help.

Common issues:
- **Patch won't apply**: Check version compatibility (GET /api/version)
- **Rollback not available**: Patch must be applied with backup
- **App won't restart**: Check systemd: `journalctl -u tvargenta -f`

## Architecture Notes

- **Atomic Operations**: All file updates use temp → rename pattern
- **Version Tracking**: Semantic versioning in `content/version.json`
- **Error Recovery**: Automatic rollback on patch failure
- **Backward Compatibility**: All translations preserve original JSON keys

## Next Steps

1. Deploy patching system to staging
2. Create and test first patch bundle
3. Monitor patch application and rollback
4. Archive old backups periodically
5. Consider future enhancements (patch signatures, scheduled updates, etc.)

---

*For complete implementation details, see [SESSION_COMPLETE_SUMMARY.md](SESSION_COMPLETE_SUMMARY.md)*
