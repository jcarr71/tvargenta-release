# TVArgenta Repository - Archive Analysis

**Generated:** February 3, 2026  
**Purpose:** Identify files and directories that can be moved to archive

---

## 📊 Repository Overview

**Total Files (excluding venv/.git):** ~95 files  
**Project Size:** ~350 MB (mostly venv directory)  
**Active Source Code:** ~30 MB

### File Type Distribution
| Type | Count | Use |
|------|-------|-----|
| `.json` | 36 | Config, metadata, schedules |
| `.py` | 27 | Core application, mods, tools |
| `.html` | 21 | Web UI templates |
| `.md` | 9 | Documentation |
| `.tvpatch` | 4 | OTA patch bundles |
| `.service` | 6 | Systemd services |
| `.sh` | 5 | Install/deploy scripts |

---

## 📦 Archive Candidates

### 🟥 **HIGH PRIORITY - Archive Immediately**

#### 1. **`patches/` Directory** (2 duplicates + 1 outdated)
- **Files:** 3 patch bundles (57 KB total)
  - `spanish_to_english_translation.tvpatch` (27 KB) - Also at root level
  - `complete_translation_and_patch_system.tvpatch` (27 KB) - Appears superseded
  - `complete-navigation.tvpatch` (3 KB) - Navigation-specific patch

**Recommendation:** 
- Create `archive/applied-patches/` folder
- Move all `.tvpatch` files there with manifest of applied dates
- Keep one reference copy in root if actively used; otherwise move to archive
- **Rationale:** Applied patches from development; historical record useful but clutters root

**Action:**
```bash
mkdir -p archive/applied-patches
mv patches/*.tvpatch archive/applied-patches/
# Update version.json to reference archive location
```

#### 2. **`install.sh.orig`** (12 KB)
- Old backup of install script before modifications
- Current version: `install.sh` (32 KB) is active

**Recommendation:** Archive or delete
- **Archive:** Keep if tracking install evolution needed for debugging old deployments
- **Delete:** If confident current version is stable
- **Rationale:** Backup versioning belongs in git history, not filesystem

**Action:**
```bash
mkdir -p archive/old-scripts
mv install.sh.orig archive/old-scripts/
```

#### 2a. **Windows Setup Files - ARCHIVED ✓**
- ✅ `setup_windows.bat` (2 KB)
- ✅ `fix_encoding.ps1` (PowerShell script)
- ✅ `README_Windows.md` (2 KB)
- **Status:** Moved to `archive/windows-setup/`
- **Rationale:** Project targets Raspberry Pi; Windows dev setup is legacy

#### 3. **`Config_files/` Directory** (System/services templates - 30+ files)
- **Contents:**
  - `audio_keepalive/` - Audio ALSA configuration
  - `servicios_y_scripts_toggle_tva_games/` - RetroPie integration (GAMES mode toggle)
- **Status:** Appears to be Pi deployment templates
- **Updated:** Unknown (likely outdated or Pi-specific)

**Recommendation:** 
- Create `archive/deployment-templates/` or `deployment-configs/`
- Move entire `Config_files/` there with README explaining each subsystem
- **Rationale:** These are deployment-specific files, not core application code. Keep as reference but separate from active source.

**Action:**
```bash
mkdir -p archive/deployment-templates
mv Config_files archive/deployment-templates/
# Create archive/deployment-templates/README.md explaining each:
# - audio_keepalive: ALSA keepalive config for Pi audio
# - servicios_y_scripts_toggle_tva_games: RetroPie games mode integration
```

#### 4. **Duplicate Root Files**
- `spanish_to_english_translation.tvpatch` (27 KB)
  - Also in `patches/` directory
  - Should be moved to archive with patches

**Action:** Move to `archive/applied-patches/` with other patches

---

### 🟨 **MEDIUM PRIORITY - Consider Archiving**

#### 5. **Obsolete/Test Scripts** (Tool scripts)
- **Files:**
  - `rename_canales.py` (4 KB) - Data migration utility
  - `encoder_menu.py` (1 KB) - UI menu, possibly test
  - `encoder_test.py` (1 KB) - Test file
  - `tvargenta_encoder.py` (15 KB) - Encoder integration

**Recommendation:**
- Keep `tvargenta_encoder.py` if actively used (15 KB, appears significant)
- Archive `rename_canales.py`, `encoder_test.py`, `encoder_menu.py` unless needed for migrations
- **Rationale:** Utility scripts that may not be needed for ongoing operation

**Action:**
```bash
mkdir -p archive/utility-scripts
mv rename_canales.py encoder_menu.py encoder_test.py archive/utility-scripts/
# Create README explaining each script's purpose and when it was used
```

#### 6. **Documentation Files** (Audit/Historical)
- `NAVIGATION_AUDIT.md` (7 KB) - Navigation audit documentation
- `INDEX.md` (12 KB) - File index (appears outdated, consider auto-generating)

**Recommendation:**
- Keep `NAVIGATION_AUDIT.md` as reference for navigation design
- Archive if navigation has stabilized
- **Rationale:** Historical audit documentation; check if still referenced

**Action:** (Optional)
```bash
mkdir -p archive/documentation
cp NAVIGATION_AUDIT.md archive/documentation/  # Keep reference copy
```

#### 7. **Test/Encoder Files**
- `encoder_reader.c` (9 KB) - C encoder implementation
- `fix_encoding.ps1` (PowerShell script) - Windows encoding fix
- `analyze_loudness.py` (6 KB) - Audio analysis utility

**Recommendation:**
- `analyze_loudness.py`: Evaluate if still used (can be in tools/)
- `encoder_reader.c` & `fix_encoding.ps1`: Archive unless actively maintained
- **Rationale:** These are support utilities that may not be core to operation

---

### 🟢 **LOW PRIORITY - Keep in Root**

#### 8. **Active Application Files** (DO NOT ARCHIVE)
- ✅ `app.py` (173 KB) - Core Flask application
- ✅ `scheduler.py` (49 KB) - Broadcast scheduler
- ✅ `metadata_daemon.py` (25 KB) - Background metadata processing
- ✅ `settings.py` (6 KB) - Configuration management
- ✅ `test_scheduler.py` (48 KB) - Scheduler tests
- ✅ `wifi_manager.py` (28 KB) - WiFi management
- ✅ `vcr_manager.py` (16 KB) - VCR/NFC interface
- ✅ `patch_system.py` (12 KB) - OTA patch system
- ✅ `bluetooth_manager.py` (14 KB) - Bluetooth interface
- ✅ `nfc_reader.py` (10 KB) - NFC/RFID reader

**Rationale:** Core application; actively maintained and deployed

#### 9. **Install & Deployment** (DO NOT ARCHIVE)
- ✅ `install.sh` (32 KB) - Active install script
- ✅ `setup_windows.bat` (2 KB) - Windows dev setup
- ✅ `requirements.txt` - Python dependencies

#### 10. **Core Configuration & Metadata** (DO NOT ARCHIVE)
- ✅ `content/` - Runtime data (metadata, channels, series, videos)
- ✅ `.github/` - GitHub workflows & CI/CD
- ✅ `templates/` - Flask HTML templates (21 files)
- ✅ `static/` - CSS, JS, assets (sortable, tailwind)
- ✅ `assets/` - Fonts and media

#### 11. **Documentation** (KEEP - Reference)
- ✅ `PATCH_SYSTEM.md` (8 KB) - Patch system documentation
- ✅ `README.md` / `README.en.md` (12 KB) - Project readme
- ✅ `INSTALL.md` (10 KB) - Installation guide
- ✅ `.github/copilot-instructions.md` - AI agent instructions

---

## 🗂️ Recommended Archive Structure

```
tvargenta-release/
├── archive/
│   ├── applied-patches/
│   │   ├── spanish_to_english_translation.tvpatch
│   │   ├── complete_translation_and_patch_system.tvpatch
│   │   ├── complete-navigation.tvpatch
│   │   └── MANIFEST.md (when applied, by whom, why)
│   │
│   ├── deployment-templates/
│   │   ├── Config_files/
│   │   │   ├── audio_keepalive/
│   │   │   ├── servicios_y_scripts_toggle_tva_games/
│   │   │   └── README.md
│   │   └── old-scripts/
│   │       ├── install.sh.orig
│   │       └── README.md
│   │
│   ├── utility-scripts/
│   │   ├── rename_canales.py (data migration)
│   │   ├── encoder_menu.py
│   │   ├── encoder_test.py
│   │   ├── analyzer_loudness.py
│   │   └── README.md (when/why each was used)
│   │
│   └── documentation/
│       ├── NAVIGATION_AUDIT.md
│       └── INDEX.md
│
└── [active source - unchanged]
```

---

## 📋 Archive Implementation Checklist

### Phase 1: Patches & Backups (5 min)
- [ ] Create `archive/` directory structure
- [ ] Move all `.tvpatch` files → `archive/applied-patches/`
- [ ] Move `install.sh.orig` → `archive/old-scripts/`
- [ ] Create manifest documenting each patch

### Phase 2: Deployment Configs (5 min)
- [ ] Move `Config_files/` → `archive/deployment-templates/`
- [ ] Create `archive/deployment-templates/README.md` explaining each:
  - audio_keepalive purpose & when to use
  - servicios_y_scripts_toggle_tva_games for RetroPie games mode
- [ ] Update `.gitignore` if needed

### Phase 3: Utility Scripts (5 min)
- [ ] Create `archive/utility-scripts/`
- [ ] Move `rename_canales.py`, `encoder_test.py`, `encoder_menu.py`
- [ ] Create `archive/utility-scripts/README.md` with:
  - Purpose of each script
  - When/how it was used
  - Last known good version/date

### Phase 4: Git Commit
```bash
git add archive/
git commit -m "Organize archive: move patches, deployment configs, utility scripts to archive/"
git push origin main
```

### Phase 5: Optional - Documentation
- [ ] Update `README.md` to reference archive
- [ ] Consider auto-generating `INDEX.md` from tree

---

## 🎯 Expected Outcomes

| Metric | Before | After |
|--------|--------|-------|
| Root-level files | 40+ | ~25 |
| Clutter | High | Low |
| Clarity | Confusing | Clear |
| Archival completeness | N/A | Documented |

---

## ⚠️ Important Notes

1. **DO NOT archive `content/` directory** - Contains runtime data and user videos
2. **DO NOT archive `templates/` or `static/`** - Active UI
3. **Backup before archiving** - Git history is preserved, but filesystem moves are one-time
4. **Test on Windows first** - Then verify on Pi after sync
5. **Update deployment docs** - If Pi scripts reference old locations

---

## Questions/Decisions Needed

1. **`rename_canales.py`** - Is this still used for data migrations?
2. **`Config_files/servicios_y_scripts_toggle_tva_games`** - Is RetroPie games mode still supported?
3. **`encoder_reader.c`** - Is C encoder still active or replaced by Python version?
4. **`NAVIGATION_AUDIT.md`** - Should this be kept or archived?
5. **Version control strategy** - Use git branches for archive, or separate archive repo?

