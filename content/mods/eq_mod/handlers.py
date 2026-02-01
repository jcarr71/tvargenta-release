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
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            eq_html = f.read()
        
        # Remove display:none to show the panel and position it normally for standalone page
        eq_html = eq_html.replace('style="display: none;"', 'style="display: block;"')
        eq_html = eq_html.replace('position: fixed;', 'position: static;')
        eq_html = eq_html.replace('bottom: 100px;', '')
        eq_html = eq_html.replace('right: 20px;', '')
        
        # Create a wrapper page with the EQ panel
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Audio Equalizer Settings</title>
            <style>
                * {{
                    box-sizing: border-box;
                }}
                body {{
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #e0e0e0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }}
                .page-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 30px;
                }}
                .page-header h1 {{
                    margin: 0;
                }}
                .back-btn {{
                    background: rgba(0, 212, 255, 0.3);
                    border: 1px solid rgba(0, 212, 255, 0.6);
                    color: #00d4ff;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1em;
                    transition: all 0.2s;
                }}
                .back-btn:hover {{
                    background: rgba(0, 212, 255, 0.5);
                }}
                .eq-wrapper {{
                    max-width: 500px;
                    margin: 0 auto;
                }}
                /* Override eq-panel styling for standalone */
                .eq-panel {{
                    position: static !important;
                    bottom: auto !important;
                    right: auto !important;
                    width: 100% !important;
                    margin: 0 !important;
                }}
            </style>
        </head>
        <body>
            <div class="page-header">
                <h1>🎚️ Audio Equalizer</h1>
                <button class="back-btn" onclick="window.location.href = document.referrer || '/'">← Back</button>
            </div>
            <div class="eq-wrapper">
                {eq_html}
            </div>
            <script>
                // Standalone EQ controller for settings page (no audio processing)
                class StandaloneEQController {{
                    constructor() {{
                        this.settings = {{
                            bass_gain: 0,
                            mid_gain: 0,
                            treble_gain: 0,
                            active_preset: 'flat'
                        }};
                        this.presets = {{}};
                        this.init();
                    }}
                    
                    async init() {{
                        try {{
                            // Load presets
                            const presetResp = await fetch('/api/eq/presets');
                            if (presetResp.ok) {{
                                const data = await presetResp.json();
                                this.presets = data.presets || {{}};
                            }}
                            
                            // Load current settings
                            const settingsResp = await fetch('/api/eq/settings');
                            if (settingsResp.ok) {{
                                const data = await settingsResp.json();
                                this.settings = data.settings || this.settings;
                            }}
                            
                            this.setupUI();
                        }} catch (e) {{
                            console.error('[EQ] Init failed:', e);
                        }}
                    }}
                    
                    setupUI() {{
                        // Set slider values
                        document.getElementById('bassSlider').value = this.settings.bass_gain;
                        document.getElementById('midSlider').value = this.settings.mid_gain;
                        document.getElementById('trebleSlider').value = this.settings.treble_gain;
                        this.updateValues();
                        
                        // Slider handlers
                        document.getElementById('bassSlider').addEventListener('input', (e) => {{
                            this.settings.bass_gain = parseInt(e.target.value);
                            this.updateValues();
                            this.saveSettings();
                        }});
                        document.getElementById('midSlider').addEventListener('input', (e) => {{
                            this.settings.mid_gain = parseInt(e.target.value);
                            this.updateValues();
                            this.saveSettings();
                        }});
                        document.getElementById('trebleSlider').addEventListener('input', (e) => {{
                            this.settings.treble_gain = parseInt(e.target.value);
                            this.updateValues();
                            this.saveSettings();
                        }});
                        
                        // Preset buttons
                        document.querySelectorAll('.eq-preset-btn').forEach(btn => {{
                            btn.addEventListener('click', () => {{
                                const preset = btn.dataset.preset;
                                this.applyPreset(preset);
                            }});
                        }});
                        
                        // Reset button
                        document.getElementById('eqReset').addEventListener('click', () => {{
                            this.reset();
                        }});
                        
                        // Apply button
                        const applyBtn = document.getElementById('eqApply');
                        if (applyBtn) {{
                            applyBtn.addEventListener('click', () => {{
                                this.applySettings();
                            }});
                        }}
                        
                        this.updatePresetButtons(this.settings.active_preset);
                    }}
                    
                    applyPreset(presetName) {{
                        const preset = this.presets[presetName];
                        if (!preset) return;
                        
                        this.settings.bass_gain = preset.bass_gain || 0;
                        this.settings.mid_gain = preset.mid_gain || 0;
                        this.settings.treble_gain = preset.treble_gain || 0;
                        this.settings.active_preset = presetName;
                        
                        // Update UI
                        document.getElementById('bassSlider').value = this.settings.bass_gain;
                        document.getElementById('midSlider').value = this.settings.mid_gain;
                        document.getElementById('trebleSlider').value = this.settings.treble_gain;
                        this.updateValues();
                        this.updatePresetButtons(presetName);
                        this.saveSettings();
                    }}
                    
                    reset() {{
                        this.settings.bass_gain = 0;
                        this.settings.mid_gain = 0;
                        this.settings.treble_gain = 0;
                        this.settings.active_preset = 'flat';
                        
                        document.getElementById('bassSlider').value = 0;
                        document.getElementById('midSlider').value = 0;
                        document.getElementById('trebleSlider').value = 0;
                        this.updateValues();
                        this.updatePresetButtons('flat');
                        this.saveSettings();
                    }}
                    
                    updateValues() {{
                        const format = (v) => v > 0 ? '+' + v : v;
                        document.getElementById('bassValue').textContent = format(this.settings.bass_gain);
                        document.getElementById('midValue').textContent = format(this.settings.mid_gain);
                        document.getElementById('trebleValue').textContent = format(this.settings.treble_gain);
                    }}
                    
                    updatePresetButtons(activePreset) {{
                        document.querySelectorAll('.eq-preset-btn').forEach(btn => {{
                            if (btn.dataset.preset === activePreset) {{
                                btn.classList.add('active');
                            }} else {{
                                btn.classList.remove('active');
                            }}
                        }});
                    }}
                    
                    async saveSettings() {{
                        try {{
                            await fetch('/api/eq/settings', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{settings: this.settings}})
                            }});
                        }} catch (e) {{
                            console.error('[EQ] Save failed:', e);
                        }}
                    }}
                    
                    async applySettings() {{
                        try {{
                            // Save settings
                            await this.saveSettings();
                            
                            // Visual feedback - highlight Apply button
                            const applyBtn = document.getElementById('eqApply');
                            if (applyBtn) {{
                                applyBtn.classList.add('applied');
                                
                                // Create notification
                                const notification = document.createElement('div');
                                notification.style.cssText = `
                                    position: fixed;
                                    top: 50%;
                                    left: 50%;
                                    transform: translate(-50%, -50%);
                                    background: rgba(76, 175, 80, 0.95);
                                    color: white;
                                    padding: 20px 40px;
                                    border-radius: 8px;
                                    font-size: 1.1em;
                                    font-weight: bold;
                                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                                    z-index: 10000;
                                    animation: fadeInOut 2s ease-in-out forwards;
                                `;
                                
                                // Add animation
                                const style = document.createElement('style');
                                style.textContent = `
                                    @keyframes fadeInOut {{
                                        0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.8); }}
                                        10% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
                                        90% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
                                        100% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.8); }}
                                    }}
                                `;
                                document.head.appendChild(style);
                                
                                notification.textContent = '✓ EQ Settings Applied!';
                                document.body.appendChild(notification);
                                
                                setTimeout(() => {{
                                    notification.remove();
                                    applyBtn.classList.remove('applied');
                                }}, 2000);
                            }}
                        }} catch (e) {{
                            console.error('[EQ] Apply failed:', e);
                        }}
                    }}
                }}
                
                // Initialize on page load
                document.addEventListener('DOMContentLoaded', () => {{
                    window.eqController = new StandaloneEQController();
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        import traceback
        return f"<h1>Error loading EQ panel: {e}</h1><pre>{traceback.format_exc()}</pre>", 500

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
