#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-TVArgenta-NC-Attribution-Consult-First
# NFC Reader Daemon for VHS Tape Playback
# Monitors PN532 USB NFC reader for NDEF text records containing video UUIDs

import os
import sys
import json
import time
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# State file path - frontend polls this for tape status
VHS_STATE_PATH = "/tmp/vhs_state.json"
LOG_DIR = Path("/srv/tvargenta/logs") if Path("/srv/tvargenta").exists() else Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logger = logging.getLogger("nfc_reader")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _h = RotatingFileHandler(str(LOG_DIR / "nfc_reader.log"), maxBytes=1_000_000, backupCount=3)
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    _h.setFormatter(_fmt)
    logger.addHandler(_h)

    sh = logging.StreamHandler()
    sh.setFormatter(_fmt)
    logger.addHandler(sh)


def write_state(inserted: bool, video_id: str = None):
    """Write current NFC/VHS state to temp file for frontend polling."""
    state = {
        "inserted": inserted,
        "video_id": video_id,
        "timestamp": time.time()
    }
    try:
        tmp_path = VHS_STATE_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(state, f)
        os.replace(tmp_path, VHS_STATE_PATH)
    except Exception as e:
        logger.error(f"Failed to write state: {e}")


def read_ndef_text(tag) -> str:
    """Extract text record from NDEF data on tag."""
    try:
        if not tag.ndef:
            logger.debug("Tag has no NDEF data")
            return None

        for record in tag.ndef.records:
            # Check for text record (TNF=1, type='T')
            if record.type == 'urn:nfc:wkt:T' or (hasattr(record, 'text')):
                text = record.text if hasattr(record, 'text') else str(record.data)
                logger.info(f"Found NDEF text record: {text}")
                return text.strip()

        logger.debug("No text records found in NDEF data")
        return None
    except Exception as e:
        logger.error(f"Error reading NDEF: {e}")
        return None


def is_valid_uuid(text: str) -> bool:
    """Check if text looks like a valid UUID."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(text)) if text else False


def main_loop_nfcpy():
    """Main loop using nfcpy library for PN532."""
    import nfc

    # Try common USB paths for PN532
    usb_paths = [
        'usb:072f:2200',  # ACR122U (common)
        'usb:04cc:2533',  # PN532 USB
        'usb:04e6:5591',  # SCL3711
        'usb',            # Auto-detect USB
        'tty:USB0:pn532', # Serial PN532
        'tty:AMA0:pn532', # Raspberry Pi UART
    ]

    clf = None
    for path in usb_paths:
        try:
            logger.info(f"Trying NFC reader at: {path}")
            clf = nfc.ContactlessFrontend(path)
            logger.info(f"Connected to NFC reader: {clf}")
            break
        except Exception as e:
            logger.debug(f"Failed to connect to {path}: {e}")
            continue

    if not clf:
        logger.error("Could not connect to any NFC reader. Exiting.")
        sys.exit(1)

    current_video_id = None
    last_tag_uid = None
    tag_present = False

    logger.info("NFC reader ready. Waiting for tags...")
    write_state(False, None)

    try:
        while True:
            # Poll for tag with short timeout
            tag = clf.connect(
                rdwr={'on-connect': lambda tag: False},  # Return immediately
                terminate=lambda: False
            )

            if tag:
                tag_uid = tag.identifier.hex()

                if not tag_present or tag_uid != last_tag_uid:
                    # New tag detected
                    logger.info(f"Tag detected: UID={tag_uid}")
                    tag_present = True
                    last_tag_uid = tag_uid

                    # Read NDEF text record
                    video_id = read_ndef_text(tag)

                    if video_id and is_valid_uuid(video_id):
                        current_video_id = video_id
                        logger.info(f"VHS tape inserted: {video_id}")
                        write_state(True, video_id)
                    else:
                        logger.warning(f"Tag has no valid video UUID. NDEF text: {video_id}")
                        write_state(False, None)
            else:
                # No tag present
                if tag_present:
                    logger.info(f"Tag removed (was: {current_video_id})")
                    tag_present = False
                    last_tag_uid = None
                    current_video_id = None
                    write_state(False, None)

            time.sleep(0.1)  # 100ms polling interval

    except KeyboardInterrupt:
        logger.info("Shutting down NFC reader...")
    finally:
        clf.close()
        write_state(False, None)


def main_loop_simulation():
    """Simulation mode for testing without hardware."""
    logger.info("Running in SIMULATION mode (no NFC hardware)")
    write_state(False, None)

    # For testing: create a file to simulate tape insertion
    SIM_FILE = "/tmp/vhs_simulate.json"

    logger.info(f"To simulate tape insertion, create {SIM_FILE} with content:")
    logger.info('{"video_id": "your-uuid-here"}')
    logger.info("Delete the file to simulate tape removal.")

    current_video_id = None

    try:
        while True:
            if os.path.exists(SIM_FILE):
                try:
                    with open(SIM_FILE, "r") as f:
                        data = json.load(f)
                    video_id = data.get("video_id")

                    if video_id and video_id != current_video_id:
                        logger.info(f"[SIM] Tape inserted: {video_id}")
                        current_video_id = video_id
                        write_state(True, video_id)
                except Exception as e:
                    logger.error(f"[SIM] Error reading simulation file: {e}")
            else:
                if current_video_id is not None:
                    logger.info(f"[SIM] Tape removed (was: {current_video_id})")
                    current_video_id = None
                    write_state(False, None)

            time.sleep(0.2)

    except KeyboardInterrupt:
        logger.info("Shutting down NFC simulation...")
    finally:
        write_state(False, None)


def main():
    logger.info("=" * 50)
    logger.info("TVArgenta NFC Reader starting...")
    logger.info("=" * 50)

    # Try to import nfcpy
    try:
        import nfc
        logger.info("nfcpy library found, using hardware mode")
        main_loop_nfcpy()
    except ImportError:
        logger.warning("nfcpy not installed. Running in simulation mode.")
        logger.warning("Install with: pip install nfcpy")
        main_loop_simulation()


if __name__ == "__main__":
    main()
