"""
Audio Equalizer Mod

Provides a 3-band audio equalizer using Web Audio API for real-time 
adjustment without app restart. Includes 5 preset curves.
"""

def init_mod(registry):
    """Initialize EQ mod - no special setup needed."""
    pass

def get_routes():
    """Return list of (rule, function, methods) tuples for Flask."""
    return [
        ("/api/eq/settings", get_eq_settings, ["GET"]),
        ("/api/eq/settings", save_eq_settings, ["POST"]),
        ("/api/eq/presets", get_eq_presets, ["GET"]),
    ]

def get_hooks():
    """Return list of hook registrations for inter-mod communication."""
    return [
        ("playback_started", on_playback_started),
    ]

def get_eq_settings():
    """Return current EQ settings."""
    from flask import jsonify
    import json
    from pathlib import Path
    
    eq_file = Path(__file__).parent / "manifest.json"
    
    try:
        with open(eq_file, "r") as f:
            manifest = json.load(f)
        
        settings = manifest.get("settings", {})
        return jsonify({
            "status": "ok",
            "settings": settings,
            "presets": manifest.get("presets", {})
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def save_eq_settings():
    """Save EQ settings to manifest."""
    from flask import request, jsonify
    import json
    from pathlib import Path
    
    try:
        data = request.get_json()
        eq_file = Path(__file__).parent / "manifest.json"
        
        with open(eq_file, "r") as f:
            manifest = json.load(f)
        
        # Update settings
        if "settings" in data:
            manifest["settings"].update(data["settings"])
        
        with open(eq_file, "w") as f:
            json.dump(manifest, f, indent=2)
        
        return jsonify({"status": "ok", "settings": manifest["settings"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_eq_presets():
    """Return all EQ presets."""
    from flask import jsonify
    import json
    from pathlib import Path
    
    eq_file = Path(__file__).parent / "manifest.json"
    
    try:
        with open(eq_file, "r") as f:
            manifest = json.load(f)
        
        return jsonify({
            "status": "ok",
            "presets": manifest.get("presets", {})
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def on_playback_started(video_id, metadata):
    """Hook called when playback starts - can apply EQ if needed."""
    pass
