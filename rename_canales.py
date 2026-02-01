#!/usr/bin/env python3
"""
Bulk rename script: replace canales/canal with channels/channel
"""
import os
import re
from pathlib import Path

# Patterns to replace
PATTERNS = [
    # Function names
    (r'def load_canales', 'def load_channels'),
    (r'def save_canales', 'def save_channels'),
    (r'def api_canales', 'def api_channels'),
    (r'def api_set_canal_activo', 'def api_set_channel_active'),
    (r'def canales\(\)', 'def channels()'),
    (r'def get_canal_numero', 'def get_channel_number'),
    
    # Variable names (careful with context)
    (r'canales_data', 'channels_data'),
    (r'canales_list', 'channels_list'),
    (r'ALL_CANALES', 'ALL_CHANNELS'),
    (r'DEFAULT_CANALES', 'DEFAULT_CHANNELS'),
    (r'CANAL_ACTIVO', 'CHANNEL_ACTIVE'),
    
    # Route names
    (r'@app.route\("/canales"\)', '@app.route("/channels")'),
    (r'@app.route\("/api/canales"\)', '@app.route("/api/channels")'),
    (r'@app.route\("/api/rebuild_schedule/<canal_id>"\)', '@app.route("/api/rebuild_schedule/<channel_id>")'),
    (r'@app.route\("/canales/editar"\)', '@app.route("/channels/edit")'),
    (r'@app.route\("/canales/guardar"\)', '@app.route("/channels/save")'),
    (r'@app.route\("/canales/eliminar"\)', '@app.route("/channels/delete")'),
    
    # URL redirects
    (r'url_for\("canales"\)', 'url_for("channels")'),
    (r'redirect\(url_for\("canales"\)\)', 'redirect(url_for("channels"))'),
    
    # Template rendering
    (r'render_template\("canales\.html"', 'render_template("channels.html"'),
]

VARIABLE_PATTERNS = [
    # Parameters and local variables - be more careful
    (r'\bcanales\s*=\s*load_canales\(\)', 'channels = load_channels()'),
    (r'\bcanales\s*=\s*load_channels\(\)', 'channels = load_channels()'),  # in case already renamed
    (r'\bfor\s+\w+,\s*canal\s+in\s+canales\.items\(\)', 'for key, channel in channels.items()'),
    (r'\bcanal_id\b', 'channel_id'),
    (r'\bcanal_activo\b', 'channel_active'),
    (r'\bcanal\s*=\s*canales\[', 'channel = channels['),
    (r'canales\[canal_id\]', 'channels[channel_id]'),
    (r'canales\.get\(canal_id', 'channels.get(channel_id'),
]

def rename_file(filepath):
    """Rename patterns in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply patterns
        for pattern, replacement in PATTERNS:
            content = re.sub(pattern, replacement, content)
        
        for pattern, replacement in VARIABLE_PATTERNS:
            content = re.sub(pattern, replacement, content)
        
        # Write back if changed
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, len(re.findall(r'canales|canal', original)) - len(re.findall(r'canales|canal', content))
        return False, 0
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, 0

def main():
    # Files to process
    files_to_rename = [
        'app.py',
        'templates/channels.html',
        'templates/upload.html',
        'templates/edit.html',
        'templates/series.html',
        'templates/upload_series.html',
        'templates/upload_commercials.html',
        'templates/vertele.html',
        'templates/video.html',
        'templates/vcr_admin.html',
        'templates/mod_manager.html',
        'templates/patches.html',
        'templates/base.html',
    ]
    
    root = Path('.')
    total_changed = 0
    
    for filepath in files_to_rename:
        full_path = root / filepath
        if full_path.exists():
            changed, count = rename_file(str(full_path))
            if changed:
                print(f"✓ {filepath} - {count} replacements made")
                total_changed += count
            else:
                print(f"  {filepath} - no changes")
        else:
            print(f"✗ {filepath} - not found")
    
    print(f"\nTotal replacements: {total_changed}")

if __name__ == '__main__':
    main()
