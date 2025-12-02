# VCR + NFC Mini VHS Tape Implementation Plan

This document describes the implementation plan for adding mini VHS tape playback support via NFC to TVArgenta. The experience should mimic using a VCR in the 90s: tune to Channel 3, insert a tape, and it starts playing.

## Requirements Summary

| Aspect | Specification |
|--------|---------------|
| **Tape content** | Single video per tape |
| **NFC reader** | PN532 via USB-C (using `nfcpy` library) |
| **Tape registration** | Admin web UI |
| **Background playback** | Silent - track elapsed time even when not on Channel 3 |
| **Position persistence** | Saved to disk, survives restarts |

### Channel 3 Behavior

| State | Display |
|-------|---------|
| No NFC reader attached | White noise with "03" overlay |
| NFC reader attached, no tape | Blue screen with "INSERT TAPE" |
| Tape inserted, playing | Video playback with VCR position counter |
| Tape inserted, paused | Video frozen with "PAUSED" OSD |
| Rewinding | Blue screen with VCR rewind animation |

### Controls (when on Channel 3 with tape)

| Action | Behavior |
|--------|----------|
| Encoder button tap | Toggle pause/play |
| Encoder button hold 3s | Start rewind (with countdown OSD) |
| Rewind duration | 2 minutes to fully rewind |
| Channel change away | Tape continues "playing" in background (position increments) |
| Tape removal | Save position, show blue "INSERT TAPE" screen |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          New Components                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  nfc_reader.py   │    │  vcr_manager.py  │    │   tapes.json     │  │
│  │  ─────────────   │    │  ─────────────   │    │  ─────────────   │  │
│  │  • USB NFC poll  │    │  • State mgmt    │    │  • NFC UID map   │  │
│  │  • Tape insert   │───▶│  • Position track│◀───│  • video_id      │  │
│  │  • Tape remove   │    │  • Rewind logic  │    │  • positions     │  │
│  │  • Reader detect │    │  • Persistence   │    │                  │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Existing Components (Modified)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  app.py                      tvargenta_encoder.py     player.html       │
│  ───────                     ───────────────────      ───────────       │
│  • /api/vcr/* endpoints      • VCR pause/rewind      • VCR channel UI   │
│  • Background position       • Hold detection        • Blue screen      │
│    tracking thread           • 3-sec countdown       • White noise      │
│  • /vcr_admin route                                  • Rewind graphics  │
│                                                      • Position counter │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Files to Create

### 1. `nfc_reader.py` - NFC Reader Daemon

**Location:** `/Users/lester/Code/TVArgenta-Release/nfc_reader.py`

**Purpose:** Monitor PN532 USB NFC reader for tape inserts/removes

**Key Functions:**
- `detect_reader()` - Check if PN532 USB device is connected
- `poll_for_tag()` - Non-blocking tag detection using nfcpy
- `on_tag_connect(tag)` - Read UID, load tape info, update vcr_state
- `on_tag_release()` - Save current position, update vcr_state
- `main_loop()` - Continuous monitoring with reconnection logic

**IPC Files Written:**
- `/tmp/vcr_state.json` - Current VCR state
- `/tmp/trigger_vcr.json` - Trigger for frontend to detect changes

### 2. `vcr_manager.py` - VCR State Manager

**Location:** `/Users/lester/Code/TVArgenta-Release/vcr_manager.py`

**Purpose:** Centralized VCR state and tape management

**Key Functions:**
- `load_vcr_state()` / `save_vcr_state()` - Runtime state in /tmp
- `load_tapes()` / `save_tapes()` - Persistent tape registry
- `register_tape(uid, video_id, title)` - Add new tape mapping
- `get_tape_info(uid)` - Look up tape by NFC UID
- `get_tape_position(uid)` / `save_tape_position(uid, pos)` - Position persistence
- `increment_position(seconds)` - Called by background thread
- `start_rewind()` / `is_rewind_complete()` - Rewind state machine

### 3. `content/tapes.json` - Tape Registry

**Location:** `/Users/lester/Code/TVArgenta-Release/content/tapes.json`

**Structure:**
```json
{
  "tapes": {
    "04:A3:2B:1C:5D:80:00": {
      "video_id": "jurassic_park",
      "title": "Jurassic Park",
      "registered_at": "2025-01-15T10:00:00Z"
    }
  },
  "positions": {
    "04:A3:2B:1C:5D:80:00": {
      "position_sec": 3456.7,
      "updated_at": "2025-01-15T14:30:00Z"
    }
  }
}
```

### 4. `/tmp/vcr_state.json` - Runtime State

**Structure:**
```json
{
  "reader_attached": true,
  "tape_inserted": true,
  "tape_uid": "04:A3:2B:1C:5D:80:00",
  "video_id": "jurassic_park",
  "title": "Jurassic Park",
  "duration_sec": 7620.0,
  "position_sec": 1234.5,
  "is_paused": false,
  "is_rewinding": false,
  "rewind_started_at": null,
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### 5. `templates/vcr_admin.html` - Tape Admin Page

**Location:** `/Users/lester/Code/TVArgenta-Release/templates/vcr_admin.html`

**Features:**
- List all registered tapes with video titles
- "Scan New Tape" button that polls NFC reader for unknown tag
- Dropdown to select video from library
- Edit/Delete tape mappings

---

## Files to Modify

### 1. `settings.py`

Add VCR-related paths:
```python
# VCR / NFC paths
VCR_STATE_FILE = TMP_DIR / "vcr_state.json"
VCR_TRIGGER_FILE = TMP_DIR / "trigger_vcr.json"
TAPES_FILE = CONTENT_DIR / "tapes.json"
```

### 2. `app.py`

**New API Endpoints:**
```python
# VCR State
GET  /api/vcr/state          # Current VCR state for frontend
POST /api/vcr/pause          # Toggle pause
POST /api/vcr/rewind         # Start rewind
POST /api/vcr/seek           # Seek to position (for admin/debug)

# Tape Management
GET  /api/vcr/tapes          # List all registered tapes
POST /api/vcr/tapes/register # Register new tape (uid, video_id)
DELETE /api/vcr/tapes/<uid>  # Remove tape mapping
GET  /api/vcr/tapes/scan     # Get currently detected but unregistered tape

# Admin Page
GET  /vcr_admin              # Tape management page
```

**Background Thread:**
```python
def vcr_position_tracker():
    """Increment tape position every second when playing (not paused, not rewinding)"""
    while True:
        state = vcr_manager.load_vcr_state()
        if (state.get('tape_inserted') and
            not state.get('is_paused') and
            not state.get('is_rewinding')):
            vcr_manager.increment_position(1.0)

        # Check if rewind complete
        if state.get('is_rewinding'):
            vcr_manager.check_rewind_complete()

        time.sleep(1)
```

**Startup Modifications:**
- Launch `nfc_reader.py` as subprocess (similar to encoder)
- Start `vcr_position_tracker` background thread

### 3. `tvargenta_encoder.py`

**New VCR-specific button handling:**

When on Channel 03 (VCR channel) with tape inserted:
- `BTN_PRESS` → Start hold timer, begin countdown display
- `BTN_RELEASE` before 3s → Toggle pause
- Hold reaches 3s → Trigger rewind

**New IPC files:**
- `/tmp/trigger_vcr_pause.json` - Pause toggle
- `/tmp/trigger_vcr_rewind.json` - Start rewind
- `/tmp/trigger_vcr_countdown.json` - Countdown OSD (3, 2, 1...)

**State additions:**
```python
vcr_btn_press_time = 0.0  # When button was pressed on VCR channel
vcr_countdown_active = False
```

### 4. `templates/player.html`

**New HTML elements:**
```html
<!-- VCR White Noise (no reader) -->
<canvas id="vcr-noise" class="vcr-fullscreen hidden"></canvas>

<!-- VCR Blue Screen (reader attached, no tape / rewinding) -->
<div id="vcr-blue-screen" class="vcr-fullscreen hidden">
  <div id="vcr-blue-text">INSERT TAPE</div>
</div>

<!-- VCR Position Counter -->
<div id="vcr-counter" class="vcr-osd hidden">
  <span id="vcr-time">00:00:00</span>
</div>

<!-- VCR Paused Indicator -->
<div id="vcr-paused" class="vcr-osd hidden">PAUSED</div>

<!-- VCR Rewind Countdown -->
<div id="vcr-countdown" class="vcr-osd hidden">
  Rewind in <span id="vcr-countdown-num">3</span>...
</div>

<!-- VCR Rewind Animation -->
<div id="vcr-rewind-screen" class="vcr-fullscreen hidden">
  <div class="vcr-rewind-bars"></div>
  <div class="vcr-rewind-text">◀◀ REWIND</div>
</div>
```

**New JavaScript:**
```javascript
// Poll VCR state when on channel 03
let vcrPollInterval = null;

function startVcrPolling() {
  if (vcrPollInterval) return;
  vcrPollInterval = setInterval(pollVcrState, 500);
}

function stopVcrPolling() {
  if (vcrPollInterval) {
    clearInterval(vcrPollInterval);
    vcrPollInterval = null;
  }
}

async function pollVcrState() {
  const resp = await fetch('/api/vcr/state');
  const state = await resp.json();
  updateVcrDisplay(state);
}

function updateVcrDisplay(state) {
  if (!state.reader_attached) {
    showWhiteNoise();
  } else if (!state.tape_inserted) {
    showBlueScreen("INSERT TAPE");
  } else if (state.is_rewinding) {
    showRewindScreen(state);
  } else {
    showVcrPlayback(state);
  }
}

function renderWhiteNoise(canvas) {
  const ctx = canvas.getContext('2d');
  const imageData = ctx.createImageData(canvas.width, canvas.height);
  // Fill with random grayscale values
  for (let i = 0; i < imageData.data.length; i += 4) {
    const v = Math.random() * 255;
    imageData.data[i] = v;     // R
    imageData.data[i+1] = v;   // G
    imageData.data[i+2] = v;   // B
    imageData.data[i+3] = 255; // A
  }
  ctx.putImageData(imageData, 0, 0);
}

function formatVcrTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
}
```

### 5. `content/canales.json`

Add Channel 03 as VCR input:
```json
{
  "03": {
    "nombre": "VCR",
    "descripcion": "Video Cassette Recorder",
    "tipo": "vcr_input",
    "icono": "vcr.png"
  }
}
```

---

## Control Flow Diagrams

### Tape Insert Flow

```
NFC Reader detects tag
       │
       ▼
nfc_reader.py reads UID
       │
       ▼
Look up UID in tapes.json
       │
       ├─── Not found ──▶ Write to vcr_state: unknown_tape_uid = UID
       │                  (Admin UI can then prompt to register)
       │
       ▼ Found
Load saved position from tapes.json
       │
       ▼
Get video duration from metadata.json
       │
       ▼
Write to /tmp/vcr_state.json:
  tape_inserted: true
  tape_uid: UID
  video_id: ...
  position_sec: saved_position
       │
       ▼
Touch /tmp/trigger_vcr.json
       │
       ▼
Frontend (if on Ch 03) polls /api/vcr/state
       │
       ▼
Seek video to position_sec, start playback
```

### Rewind Flow

```
User holds encoder button on Ch 03
       │
       ▼
tvargenta_encoder.py detects BTN_PRESS
       │
       ▼
Write countdown to /tmp/trigger_vcr_countdown.json
  {"countdown": 3}
       │
       ▼
Frontend shows "Rewind in 3..."
       │
       ├─── Button released before 3s ──▶ Cancel countdown
       │                                   Write {"countdown": null}
       │                                   Toggle pause instead
       │
       ▼ 3 seconds elapsed, still held
Write /tmp/trigger_vcr_rewind.json
       │
       ▼
vcr_manager.start_rewind() called:
  is_rewinding: true
  rewind_started_at: now()
       │
       ▼
Frontend shows blue rewind screen with animation
       │
       ▼
Background thread decrements position over 2 minutes
       │
       ▼ After 2 minutes (or position reaches 0)
vcr_manager sets:
  is_rewinding: false
  position_sec: 0
       │
       ▼
Frontend shows blue "INSERT TAPE" screen
(tape still physically present, but "rewound" to start)
User can press play to start from beginning
```

### Background Position Tracking

```
vcr_position_tracker thread (runs every 1 second)
       │
       ▼
Load /tmp/vcr_state.json
       │
       ├─── No tape inserted ──▶ Sleep, continue
       │
       ├─── Tape paused ──▶ Sleep, continue
       │
       ├─── Tape rewinding ──▶ Check if 2 min elapsed
       │                       If yes: set position=0, is_rewinding=false
       │                       Sleep, continue
       │
       ▼ Tape playing
Increment position_sec by 1.0
       │
       ▼
Check if position >= video duration
       │
       ├─── Yes ──▶ Video ended, could loop or stop
       │
       ▼ No
Save updated position to vcr_state.json
       │
       ▼
Every 30 seconds: persist position to tapes.json
(so it survives restarts)
```

---

## Implementation Order

1. **`vcr_manager.py`** - State management module (no external deps)
2. **`nfc_reader.py`** - NFC daemon (requires nfcpy)
3. **`settings.py`** - Add VCR paths
4. **`app.py`** - Add VCR API endpoints and background thread
5. **`canales.json`** - Add Channel 03
6. **`tvargenta_encoder.py`** - Add VCR button handling
7. **`player.html`** - Add VCR UI states
8. **`vcr_admin.html`** - Admin page for tape registration
9. **`static/css/vcr.css`** - VCR-specific styles

---

## Dependencies

```bash
# Python package for PN532 NFC reader
pip install nfcpy

# System packages (may be needed)
sudo apt-get install libusb-1.0-0-dev
```

---

## Testing Checklist

- [ ] NFC reader detection (plugged/unplugged)
- [ ] Tape detection (insert/remove)
- [ ] Position persistence across tape remove/insert
- [ ] Position persistence across app restart
- [ ] Background position tracking when not on Ch 03
- [ ] Pause/resume functionality
- [ ] Rewind countdown and cancellation
- [ ] Full rewind (2 minute duration)
- [ ] White noise display (no reader)
- [ ] Blue screen display (reader, no tape)
- [ ] Video playback with position counter
- [ ] Tape registration via admin UI
- [ ] Channel 03 in channel rotation
