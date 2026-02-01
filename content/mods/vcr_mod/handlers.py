#!/usr/bin/env python3
"""
VCR/NFC Tape System Module for TVArgenta

Handles all VCR-related functionality:
- NFC tape detection and management
- Tape position persistence
- Rewind animations
- Recording functionality
"""

import json
import logging
from flask import jsonify, request, render_template
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("tvargenta.mods.vcr")

# These will be set during mod initialization
app = None
vcr_manager = None
METADATA_FILE = None
TAPES_FILE = None
VCR_STATE_FILE = None
VCR_TRIGGER_FILE = None
VCR_PAUSE_TRIGGER = None
VCR_REWIND_TRIGGER = None
VCR_COUNTDOWN_TRIGGER = None
VCR_RECORDING_STATE_FILE = None


def init_mod(registry):
    """Initialize VCR mod with app context"""
    global app, vcr_manager, METADATA_FILE, TAPES_FILE
    global VCR_STATE_FILE, VCR_TRIGGER_FILE, VCR_PAUSE_TRIGGER
    global VCR_REWIND_TRIGGER, VCR_COUNTDOWN_TRIGGER, VCR_RECORDING_STATE_FILE
    
    # Import here to avoid circular imports
    import app as app_module
    import vcr_manager as vcr_mod
    
    app = app_module.app
    vcr_manager = vcr_mod
    
    # Import path settings
    from settings import (
        METADATA_FILE as mf, TAPES_FILE as tf,
        VCR_STATE_FILE as vsf, VCR_TRIGGER_FILE as vtf,
        VCR_PAUSE_TRIGGER as vpt, VCR_REWIND_TRIGGER as vrt,
        VCR_COUNTDOWN_TRIGGER as vct, VCR_RECORDING_STATE_FILE as vrsf
    )
    
    METADATA_FILE = mf
    TAPES_FILE = tf
    VCR_STATE_FILE = vsf
    VCR_TRIGGER_FILE = vtf
    VCR_PAUSE_TRIGGER = vpt
    VCR_REWIND_TRIGGER = vrt
    VCR_COUNTDOWN_TRIGGER = vct
    VCR_RECORDING_STATE_FILE = vrsf
    
    logger.info("VCR mod initialized")


def get_routes():
    """Return Flask routes for VCR mod"""
    return [
        ('/api/vcr/state', api_vcr_state, ['GET']),
        ('/api/vcr/pause', api_vcr_pause, ['POST']),
        ('/api/vcr/rewind', api_vcr_rewind, ['POST']),
        ('/api/vcr/check_pause_trigger', api_vcr_check_pause_trigger, ['GET']),
        ('/api/vcr/check_rewind_trigger', api_vcr_check_rewind_trigger, ['GET']),
        ('/api/vcr/seek', api_vcr_seek, ['POST']),
        ('/api/vcr/tapes', api_vcr_tapes, ['GET']),
        ('/api/vcr/tapes/register', api_vcr_tapes_register, ['POST']),
        ('/api/vcr/tapes/delete/<uid>', api_vcr_tapes_delete, ['POST']),
        ('/api/vcr/tapes/scan', api_vcr_tapes_scan, ['POST']),
        ('/api/vcr/trigger', api_vcr_trigger, ['GET']),
        ('/api/vcr/countdown_trigger', api_vcr_countdown_trigger, ['GET']),
        ('/api/vcr/videos', api_vcr_videos, ['GET']),
        ('/api/vcr/empty_tape_qr', api_vcr_empty_tape_qr, ['GET']),
        ('/vcr_admin', vcr_admin, ['GET']),
        ('/api/vcr/record_progress', api_vcr_record_progress, ['GET']),
        ('/api/vcr/record/start', api_vcr_record_start, ['POST']),
        ('/api/vcr/record/stop', api_vcr_record_stop, ['POST']),
        ('/vcr_record', vcr_record, ['GET']),
    ]


def get_hooks():
    """Return hook registrations for VCR mod"""
    return {
        # Hook for when a channel changes - could trigger VCR updates
        'channel_changed': on_channel_changed,
    }


# ============================================================================
# VCR Route Handlers
# ============================================================================

def api_vcr_state():
    """Get current VCR state"""
    try:
        state = vcr_manager._read_json(VCR_STATE_FILE, {})
        return jsonify(state)
    except Exception as e:
        logger.error(f"Error getting VCR state: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_pause():
    """Toggle VCR pause state"""
    try:
        data = request.get_json() or {}
        pause = data.get('pause', True)
        
        state = vcr_manager._read_json(VCR_STATE_FILE, {})
        state['paused'] = pause
        vcr_manager._write_json_atomic(VCR_STATE_FILE, state)
        
        return jsonify({"success": True, "paused": pause})
    except Exception as e:
        logger.error(f"Error toggling VCR pause: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_rewind():
    """Trigger VCR rewind"""
    try:
        state = vcr_manager._read_json(VCR_STATE_FILE, {})
        position = state.get('position', 0)
        
        # Rewind to beginning
        state['position'] = 0
        state['rewind_triggered'] = True
        vcr_manager._write_json_atomic(VCR_STATE_FILE, state)
        
        return jsonify({"success": True, "position": 0})
    except Exception as e:
        logger.error(f"Error rewinding VCR: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_check_pause_trigger():
    """Check if pause was triggered via hardware button"""
    try:
        if Path(VCR_PAUSE_TRIGGER).exists():
            Path(VCR_PAUSE_TRIGGER).unlink()
            return jsonify({"pause_triggered": True})
        return jsonify({"pause_triggered": False})
    except Exception as e:
        logger.error(f"Error checking pause trigger: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_check_rewind_trigger():
    """Check if rewind was triggered via hardware button"""
    try:
        if Path(VCR_REWIND_TRIGGER).exists():
            Path(VCR_REWIND_TRIGGER).unlink()
            return jsonify({"rewind_triggered": True})
        return jsonify({"rewind_triggered": False})
    except Exception as e:
        logger.error(f"Error checking rewind trigger: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_seek():
    """Seek to specific position in tape"""
    try:
        data = request.get_json() or {}
        position = data.get('position', 0)
        
        state = vcr_manager._read_json(VCR_STATE_FILE, {})
        state['position'] = position
        vcr_manager._write_json_atomic(VCR_STATE_FILE, state)
        
        return jsonify({"success": True, "position": position})
    except Exception as e:
        logger.error(f"Error seeking VCR: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_tapes():
    """List all registered tapes"""
    try:
        tapes = vcr_manager._read_json(TAPES_FILE, {})
        return jsonify(tapes)
    except Exception as e:
        logger.error(f"Error listing tapes: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_tapes_register():
    """Register a new NFC tape"""
    try:
        data = request.get_json() or {}
        uid = data.get('uid')
        video_path = data.get('video_path')
        
        if not uid or not video_path:
            return jsonify({"error": "Missing uid or video_path"}), 400
        
        tapes = vcr_manager._read_json(TAPES_FILE, {})
        tapes[uid] = {
            'video_path': video_path,
            'registered_at': datetime.now().isoformat(),
            'label': data.get('label', 'Tape')
        }
        vcr_manager._write_json_atomic(TAPES_FILE, tapes)
        
        return jsonify({"success": True, "uid": uid})
    except Exception as e:
        logger.error(f"Error registering tape: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_tapes_delete(uid):
    """Delete a registered tape"""
    try:
        tapes = vcr_manager._read_json(TAPES_FILE, {})
        if uid in tapes:
            del tapes[uid]
            vcr_manager._write_json_atomic(TAPES_FILE, tapes)
            return jsonify({"success": True})
        return jsonify({"error": "Tape not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting tape: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_tapes_scan():
    """Scan for new NFC tapes"""
    try:
        # This would be implemented by nfc_reader daemon
        # For now, just return success
        return jsonify({"success": True, "scanned": True})
    except Exception as e:
        logger.error(f"Error scanning tapes: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_trigger():
    """Check for VCR tape trigger (NFC detection)"""
    try:
        if Path(VCR_TRIGGER_FILE).exists():
            with open(VCR_TRIGGER_FILE, 'r', encoding='utf-8') as f:
                trigger_data = json.load(f)
            Path(VCR_TRIGGER_FILE).unlink()
            return jsonify(trigger_data)
        return jsonify({"triggered": False})
    except Exception as e:
        logger.error(f"Error checking VCR trigger: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_countdown_trigger():
    """Check for rewind countdown trigger"""
    try:
        if Path(VCR_COUNTDOWN_TRIGGER).exists():
            Path(VCR_COUNTDOWN_TRIGGER).unlink()
            return jsonify({"countdown": True})
        return jsonify({"countdown": False})
    except Exception as e:
        logger.error(f"Error checking countdown trigger: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_videos():
    """Get list of videos that can be registered to tapes"""
    try:
        metadata = vcr_manager._read_json(METADATA_FILE, {})
        videos = {}
        
        for video_id, info in metadata.items():
            if info.get('series_path'):
                videos[video_id] = {
                    'path': info['series_path'],
                    'title': info.get('title', video_id)
                }
        
        return jsonify(videos)
    except Exception as e:
        logger.error(f"Error getting VCR videos: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_empty_tape_qr():
    """Get QR code for empty tape (recording flow)"""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        qr_url = f"http://{local_ip}:5000/vcr_record"
        
        return jsonify({"url": qr_url, "ip": local_ip})
    except Exception as e:
        logger.error(f"Error getting empty tape QR: {e}")
        return jsonify({"error": str(e)}), 500


def vcr_admin():
    """VCR admin interface template"""
    return render_template('vcr_admin.html')


def vcr_record():
    """VCR record/upload interface"""
    return render_template('vcr_record.html')


def api_vcr_record_progress():
    """Get recording progress"""
    try:
        state = _vcr_recording_state_read()
        return jsonify(state)
    except Exception as e:
        logger.error(f"Error getting recording progress: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_record_start():
    """Start recording to a tape"""
    try:
        data = request.get_json() or {}
        tape_uid = data.get('tape_uid')
        
        state = {
            'recording': True,
            'started_at': datetime.now().isoformat(),
            'tape_uid': tape_uid,
            'bytes_uploaded': 0
        }
        _vcr_recording_state_write(state)
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error starting recording: {e}")
        return jsonify({"error": str(e)}), 500


def api_vcr_record_stop():
    """Stop recording to a tape"""
    try:
        _vcr_recording_state_clear()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error stopping recording: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# VCR Helper Functions
# ============================================================================

def _vcr_recording_state_write(state: dict) -> None:
    """Write VCR recording state atomically"""
    try:
        vcr_manager._write_json_atomic(VCR_RECORDING_STATE_FILE, state)
    except Exception as e:
        logger.error(f"Error writing recording state: {e}")


def _vcr_recording_state_read() -> dict:
    """Read current VCR recording state"""
    try:
        return vcr_manager._read_json(VCR_RECORDING_STATE_FILE, {})
    except Exception as e:
        logger.error(f"Error reading recording state: {e}")
        return {}


def _vcr_recording_state_clear() -> None:
    """Clear VCR recording state"""
    try:
        if Path(VCR_RECORDING_STATE_FILE).exists():
            Path(VCR_RECORDING_STATE_FILE).unlink()
    except Exception as e:
        logger.error(f"Error clearing recording state: {e}")


# ============================================================================
# Hook Callbacks
# ============================================================================

def on_channel_changed(channel_id):
    """Called when user changes channel"""
    # Could be used to pause VCR playback when switching away from channel 03
    logger.info(f"VCR mod: Channel changed to {channel_id}")
