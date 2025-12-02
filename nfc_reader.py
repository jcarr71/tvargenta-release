#!/usr/bin/env python3
"""
NFC Reader Daemon for TVArgenta VCR Feature

Monitors a PN532 USB NFC reader for mini VHS tape tags.
When a tape is inserted/removed, updates VCR state accordingly.

Usage:
    python3 nfc_reader.py

Requires:
    pip install nfcpy

The daemon will:
1. Detect if NFC reader is attached
2. Poll for NFC tags continuously
3. On tag detected: look up in tapes.json, update vcr_state
4. On tag removed: save position, update vcr_state
5. Reconnect if reader is disconnected
"""

import sys
import time
import signal
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import vcr_manager

# Try to import nfcpy
try:
    import nfc
    NFC_AVAILABLE = True
except ImportError:
    NFC_AVAILABLE = False
    print("[NFC] Warning: nfcpy not installed. Install with: pip install nfcpy")

# Configuration
POLL_INTERVAL = 0.5  # Seconds between tag polls
READER_CHECK_INTERVAL = 5.0  # Seconds between reader attachment checks
USB_DEVICE_PATH = "usb"  # nfcpy device path for USB readers

# State
running = True
current_tag_uid = None
last_reader_check = 0.0


def ts():
    """Timestamp for logging."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def uid_to_string(uid_bytes) -> str:
    """Convert UID bytes to colon-separated hex string."""
    return ":".join(f"{b:02X}" for b in uid_bytes)


def check_reader_attached() -> bool:
    """
    Check if a USB NFC reader is attached.
    Uses lsusb to look for common NFC reader vendor IDs.
    """
    try:
        # Common USB Vendor IDs for NFC readers
        # PN532 boards often use FTDI (0403) or CH340 (1a86) for USB serial
        # ACR122U uses ACS (072f)
        # Some PN532 modules have their own VID
        result = subprocess.run(
            ["lsusb"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout.lower()

        # Check for common NFC reader identifiers
        nfc_indicators = [
            "072f:",  # ACS (ACR122U)
            "04e6:",  # SCM Microsystems
            "04cc:",  # ST-Ericsson
            "0403:",  # FTDI (many PN532 boards)
            "1a86:",  # CH340 (some PN532 boards)
            "nfc",
            "pn532",
            "acr122",
            "contactless",
        ]

        for indicator in nfc_indicators:
            if indicator in output:
                return True

        return False

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # lsusb not available or timed out - assume reader might be there
        return True


def find_nfc_device():
    """
    Attempt to find and connect to an NFC device.
    Returns the device path string or None.
    """
    if not NFC_AVAILABLE:
        return None

    # Try common device paths for PN532
    device_paths = [
        "usb",           # Auto-detect USB
        "usb:072f",      # ACS ACR122U
        "usb:04e6",      # SCM
        "tty:USB0:pn532",  # Serial PN532 on /dev/ttyUSB0
        "tty:USB1:pn532",  # Serial PN532 on /dev/ttyUSB1
        "tty:AMA0:pn532",  # Serial PN532 on /dev/ttyAMA0 (Pi GPIO)
    ]

    for path in device_paths:
        try:
            clf = nfc.ContactlessFrontend(path)
            clf.close()
            print(f"[{ts()}] [NFC] Found device at: {path}")
            return path
        except Exception:
            continue

    return None


class NFCTagHandler:
    """Handler for NFC tag connect/release events."""

    def __init__(self):
        self.tag_uid = None

    def on_connect(self, tag):
        """Called when a tag is detected."""
        global current_tag_uid

        try:
            uid = uid_to_string(tag.identifier)
            self.tag_uid = uid
            current_tag_uid = uid
            print(f"[{ts()}] [NFC] Tag detected: {uid}")

            # Look up tape in registry
            tape_info = vcr_manager.get_tape_info(uid)

            if tape_info:
                # Known tape - load video
                video_id = tape_info["video_id"]
                title = tape_info["title"]
                position = tape_info.get("position_sec", 0.0)

                # Get video duration from metadata
                duration = vcr_manager.get_video_duration(video_id)

                print(f"[{ts()}] [NFC] Tape: {title} ({video_id})")
                print(f"[{ts()}] [NFC] Position: {position:.1f}s / {duration:.1f}s")

                vcr_manager.set_tape_inserted(
                    uid=uid,
                    video_id=video_id,
                    title=title,
                    duration_sec=duration,
                    position_sec=position,
                )
            else:
                # Unknown tape - signal for registration
                print(f"[{ts()}] [NFC] Unknown tape: {uid}")
                vcr_manager.set_unknown_tape(uid)

            # Return True to stay connected and detect removal
            return True

        except Exception as e:
            print(f"[{ts()}] [NFC] Error processing tag: {e}")
            return False

    def on_release(self, tag):
        """Called when a tag is removed."""
        global current_tag_uid

        uid = self.tag_uid or current_tag_uid
        print(f"[{ts()}] [NFC] Tag removed: {uid}")

        # Save position and clear state
        vcr_manager.set_tape_removed()

        self.tag_uid = None
        current_tag_uid = None

        # Return True to continue polling for new tags
        return True


def poll_with_nfcpy(device_path: str) -> bool:
    """
    Poll for NFC tags using nfcpy.
    Returns False if reader disconnected.
    """
    if not NFC_AVAILABLE:
        return False

    try:
        clf = nfc.ContactlessFrontend(device_path)
    except Exception as e:
        print(f"[{ts()}] [NFC] Cannot open device: {e}")
        return False

    handler = NFCTagHandler()

    try:
        # Sense for a tag
        # rdwr: read/write mode
        # on-connect: called when tag found
        # on-release: called when tag removed
        # terminate: check function to stop polling

        tag = clf.connect(
            rdwr={
                "on-connect": handler.on_connect,
                "on-release": handler.on_release,
            },
            terminate=lambda: not running,
        )

        return True

    except nfc.clf.CommunicationError as e:
        print(f"[{ts()}] [NFC] Communication error: {e}")
        return False

    except Exception as e:
        print(f"[{ts()}] [NFC] Error during poll: {e}")
        return True  # Keep trying

    finally:
        try:
            clf.close()
        except Exception:
            pass


def run_daemon():
    """Main daemon loop."""
    global running, last_reader_check

    print(f"[{ts()}] [NFC] TVArgenta NFC Reader Daemon starting...")

    if not NFC_AVAILABLE:
        print(f"[{ts()}] [NFC] ERROR: nfcpy not available!")
        print(f"[{ts()}] [NFC] Install with: pip install nfcpy")
        print(f"[{ts()}] [NFC] Running in stub mode (no actual NFC support)")

    device_path = None
    reader_was_attached = False

    while running:
        try:
            now = time.time()

            # Periodically check if reader is attached
            if now - last_reader_check >= READER_CHECK_INTERVAL:
                last_reader_check = now
                attached = check_reader_attached()

                if attached != reader_was_attached:
                    reader_was_attached = attached
                    vcr_manager.set_reader_attached(attached)

                    if attached:
                        print(f"[{ts()}] [NFC] Reader attached")
                        # Try to find the device
                        if NFC_AVAILABLE:
                            device_path = find_nfc_device()
                    else:
                        print(f"[{ts()}] [NFC] Reader detached")
                        device_path = None

            # If we have a device, poll for tags
            if device_path and NFC_AVAILABLE:
                if not poll_with_nfcpy(device_path):
                    # Reader may have disconnected
                    print(f"[{ts()}] [NFC] Reader disconnected, will retry...")
                    device_path = None
                    time.sleep(1)

            else:
                # No device - just wait
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n[{ts()}] [NFC] Interrupted by keyboard")
            break

        except Exception as e:
            print(f"[{ts()}] [NFC] Unexpected error: {e}")
            time.sleep(1)

    print(f"[{ts()}] [NFC] Daemon stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global running
    print(f"\n[{ts()}] [NFC] Received signal {signum}, shutting down...")
    running = False


def main():
    """Entry point."""
    global running

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize VCR state
    state = vcr_manager.load_vcr_state()
    if not state:
        vcr_manager.save_vcr_state(vcr_manager.get_default_vcr_state())

    # Run the daemon
    run_daemon()


if __name__ == "__main__":
    main()
