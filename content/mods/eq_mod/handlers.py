"""
Audio Equalizer Mod

Provides a 3-band audio equalizer using Web Audio API for real-time 
adjustment without app restart. Includes 5 preset curves.
"""

def init_mod(registry):
    """Initialize EQ mod - no special setup needed."""
    pass

def get_eq_panel():
    """Serve the EQ control panel page."""
    from flask import render_template_string
    from pathlib import Path
    
    # Load eq_panel.html template
    template_path = Path(__file__).parent / "templates" / "eq_panel.html"
    eq_js_path = Path(__file__).parent / "static" / "eq.js"
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            eq_html = f.read()
        
        with open(eq_js_path, "r", encoding="utf-8") as f:
            eq_js = f.read()
        
        # Create a wrapper page with the EQ panel
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Audio Equalizer</title>
            <style>
                body {{
                    background: #1a1a1a;
                    color: #e0e0e0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .eq-container {{
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .back-btn {{
                    background: rgba(0, 212, 255, 0.3);
                    border: 1px solid rgba(0, 212, 255, 0.6);
                    color: #00d4ff;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-bottom: 20px;
                }}
                .back-btn:hover {{
                    background: rgba(0, 212, 255, 0.5);
                }}
            </style>
        </head>
        <body>
            <button class="back-btn" onclick="window.history.back()">← Back</button>
            <h1>🎚️ Audio Equalizer</h1>
            <div class="eq-container">
                {eq_html}
            </div>
            <script>
                {eq_js}
            </script>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        return f"<h1>Error loading EQ panel: {e}</h1>", 500

def get_routes():
    """Return list of (rule, function, methods) tuples for Flask."""
    return [
        ("/eq", get_eq_panel, ["GET"]),
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
