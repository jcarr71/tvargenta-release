# TV-CBIA Installation Guide

This guide provides step-by-step instructions for installing TV-CBIA (Community Broadcast Interactive Archive) on a fresh Raspberry Pi running Debian/Raspbian.

## Prerequisites

- Raspberry Pi 4 or higher
- Debian/Raspbian Linux OS (tested on Raspberry Pi OS)
- Network connectivity (WiFi or Ethernet)
- HiFiBerry DAC+ (optional but recommended for audio)
- NFC reader PN532 (optional, for VCR tape mode)
- USB Chromium-compatible display
- Sudo/root access

## Installation Overview

The installation process follows these steps:

1. **Clone the repository**
2. **Configure bootloader** (optional but recommended)
3. **Set up power-on experience** (splash screen)
4. **Install Python application**
5. **Configure Python virtual environment**
6. **Build C encoder reader** (optional)
7. **Install systemd services**
8. **Configure audio system** (ALSA/HiFiBerry DAC)
9. **Configure display** (X11 autologin)

You can run each step individually or use `all` to run everything.

---

## Quick Start (Full Installation)

```bash
# Clone the repository
git clone https://github.com/jcarr71/tvargenta-release.git ~/tv-cbia
cd ~/tv-cbia

# Run complete installation
sudo bash install.sh all
```

---

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone https://github.com/jcarr71/tvargenta-release.git ~/tv-cbia
cd ~/tv-cbia
```

### 2. Configure Bootloader (Optional)

Configures `/boot/firmware/config.txt` for TVArgenta hardware:
- Disables onboard audio (if using HiFiBerry DAC)
- Switches to legacy KMS video mode
- Enables I2S audio interface
- Disables onboard Bluetooth

```bash
sudo bash install.sh bootloader
```

**What it modifies:**
- `/boot/firmware/config.txt` - Adds HiFiBerry, audio, and display settings
- `/boot/firmware/cmdline.txt` - Optimizes kernel parameters

### 3. Power-On Experience Setup

Creates a black splash screen and configures boot sequence:

```bash
sudo bash install.sh poweron_experience
```

**Creates:**
- `/etc/systemd/system/splash.service` - Black splash at boot
- `/opt/splash/` - Splash screen assets

### 4. Install Application

Clones TVArgenta to `/srv/tvargenta` (system location) or allows custom path:

```bash
sudo bash install.sh install_app
```

**Installs to:**
- `/srv/tvargenta/` (default system location)

**Directory structure:**
```
/srv/tvargenta/
├── app.py                 # Main Flask application
├── scheduler.py           # Broadcast schedule generator
├── metadata_daemon.py     # Video metadata processor
├── nfc_reader.py          # NFC tape reader daemon
├── vcr_manager.py         # VCR state management
├── patch_system.py        # Patch deployment system
├── patch_system_core.py   # Core patch logic
├── settings.py            # Configuration
├── templates/             # HTML templates
│   ├── base.html
│   ├── patches.html       # Patch manager UI
│   ├── mod_manager.html   # Mod management UI
│   ├── upload.html        # Upload UI
│   ├── vertele.html       # Watch TV UI
│   ├── canales.html       # Channels UI
│   └── ...
├── static/                # CSS, JavaScript
├── tools/                 # Utility scripts
│   ├── generate_patch.py  # Patch bundle generator
│   └── mod_system.py      # Mod management utilities
├── patches/               # Distributed patch bundles
│   └── complete-navigation.tvpatch
├── content/               # Runtime data (runtime-created)
│   ├── metadata.json
│   ├── canales.json
│   ├── version.json
│   ├── videos/
│   ├── logs/
│   └── mods/
└── Config_files/          # Configuration templates
```

### 5. Setup Python Virtual Environment

Creates and configures Python venv with required packages:

```bash
sudo bash install.sh setup_venv
```

**Installs packages:**
- flask
- nfcpy (NFC support)
- ffmpeg-python (audio/video processing)
- All dependencies listed in requirements.txt (if present)

### 6. Build C Encoder Reader (Optional)

Compiles C encoder reader for hardware hotkey detection:

```bash
sudo bash install.sh build_encoder
```

**Compiles:**
- `encoder_reader.c` → `/srv/tvargenta/encoder_reader` binary

Required if using RetroPie encoder integration.

### 7. Install Systemd Services

Creates and enables system services:

```bash
sudo bash install.sh install_services
```

**Services created:**
- `tvargenta.service` - Main Flask application (ENABLED by default)
- `emulationstation-session.service` - Gaming session
- `encoder-hotkey.service` - Encoder input monitoring
- `enter-gaming.service` - Enter game mode
- `return-tvargenta.service` - Return from gaming
- `watch-emustation.service` - Gaming mode watcher

**Key services:**
- Only `tvargenta.service` is auto-enabled
- Other services available for optional gaming features

**Service files installed to:**
- `/etc/systemd/system/`

### 8. Configure Audio System

Sets up ALSA and HiFiBerry DAC audio (if present):

```bash
sudo bash install.sh setup_audio
```

**Configures:**
- `/etc/asound.conf` - ALSA configuration for HiFiBerry
- Audio routing and device setup
- Volume levels

**Supports:**
- HiFiBerry DAC+ / DAC+ Pro
- Standard Raspberry Pi audio jack
- USB audio devices

### 9. Configure Display

Sets up X11 autologin and Chromium kiosk mode:

```bash
sudo bash install.sh setup_display
```

**Configures:**
- `/etc/lightdm/` - Autologin settings
- X11 session initialization
- Chromium launch at boot
- Kiosk mode settings

---

## Verification

After installation, verify everything is working:

### Check Application

```bash
# Navigate to app directory
cd /srv/tvargenta

# Test Flask app directly (Ctrl+C to stop)
python3 app.py

# Should display:
# * Running on http://0.0.0.0:5000
```

### Check Services

```bash
# View all TVArgenta services
systemctl list-units | grep tvargenta

# Check service status
systemctl status tvargenta.service

# View logs
journalctl -u tvargenta.service -f

# View application logs
tail -f /srv/tvargenta/content/logs/app.log
```

### Access Web UI

From another computer on the network:

```
http://<pi-ip>:5000
```

You should see the TV-CBIA interface with:
- Mod Manager (📦)
- Patches (📋)
- Uploads (📤)
- Watch TV (📺)
- Channels (📡)

---

## Running Individual Services

Each service can be run independently for development/debugging:

```bash
# Start main application
python3 /srv/tvargenta/app.py

# Start metadata daemon
python3 /srv/tvargenta/metadata_daemon.py

# Start NFC reader daemon
python3 /srv/tvargenta/nfc_reader.py
```

---

## Configuration

### Environment Variables

```bash
# Custom installation directory
export TVARGENTA_ROOT=/custom/path

# Custom user (for multi-user setups)
export TVARGENTA_USER=customuser

# Then run install.sh
```

### Settings File

After installation, configure `/srv/tvargenta/content/configuracion.json`:

```json
{
  "excluded_tags": [],
  "volume_default": 50,
  "timezone": "America/Argentina/Buenos_Aires",
  "kiosk_mode": true
}
```

---

## Troubleshooting

### Permission Denied

Ensure you have sudo privileges:

```bash
sudo bash install.sh <command>
```

### Python Module Not Found

If Python dependencies fail, manually install:

```bash
cd /srv/tvargenta
source venv/bin/activate
pip install flask nfcpy
```

### Services Won't Start

Check service logs:

```bash
journalctl -u tvargenta.service -n 50
```

Check application logs:

```bash
tail -f /srv/tvargenta/content/logs/app.log
```

### Audio Not Working

Verify HiFiBerry configuration:

```bash
aplay -l  # List audio devices
```

Reconfigure audio:

```bash
sudo bash install.sh setup_audio
```

---

## Post-Installation

### Upload Content

1. Navigate to `http://<pi-ip>:5000/upload`
2. Upload video files (mp4, mkv, webm, mov)
3. Organize into:
   - Series: `/content/videos/series/{Show Name}/Season {N}/`
   - Commercials: `/content/videos/comercials/`
   - Regular videos: `/content/videos/`

### Manage Patches

1. Navigate to `http://<pi-ip>:5000/patches`
2. Upload `.tvpatch` files
3. Track patch history and rollback

### Configure Mods

1. Navigate to `http://<pi-ip>:5000/mod_manager`
2. Enable/disable optional features
3. Configure mod settings

---

## Architecture Overview

**Core Components:**

- **app.py** - Flask web server, REST API, web UI
- **scheduler.py** - Broadcast schedule generation (1990s TV emulation)
- **metadata_daemon.py** - Background video metadata processor
- **nfc_reader.py** - NFC tape reader for VCR mode
- **vcr_manager.py** - VCR playback state tracking
- **patch_system.py** - Patch bundle creation and application
- **settings.py** - Configuration and paths

**Data Files (in content/):**

- `metadata.json` - Video information and thumbnails
- `canales.json` - Channel definitions
- `version.json` - Version tracking and patch history
- `weekly_schedule.json` - Series-to-timeslot assignments
- `daily_schedule.json` - Second-by-second playback map
- `vcr_state.json` - NFC tape playback state

---

## Support & Development

- **Repository**: https://github.com/jcarr71/tvargenta-release
- **Issues**: https://github.com/jcarr71/tvargenta-release/issues
- **Documentation**: See [PATCH_SYSTEM.md](PATCH_SYSTEM.md) for patch system details

---

## License

See [LICENSE](LICENSE) for terms.
