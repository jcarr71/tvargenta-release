#!/usr/bin/env python3
"""
TVArgenta Patch System - Quick Start Guide

This document provides step-by-step examples for using the patching system.
"""

# ==============================================================================
# 1. CREATING A PATCH
# ==============================================================================

"""
Command-line usage:

    python3 generate_patch.py <from_dir> <to_dir> <output_file> [--description "..."]

Example:

    python3 generate_patch.py \
        /path/to/tvargenta-v1.0.0 \
        /path/to/tvargenta-current \
        patch_feature_update.tvpatch \
        --description "Implement new scheduler algorithm"

What happens:
1. Scans both directories for .py, .html, .js, .css, .json, .md, .sh files
2. Compares files and generates unified diffs
3. Computes SHA256 checksums of new files
4. Creates manifest.json with metadata
5. Packages into .tvpatch (tar.gz) bundle

Output:
    $ python3 generate_patch.py v1.0.0 v1.0.1 patch.tvpatch
    Generating patch from /path/to/v1.0.0 to /path/to/v1.0.1
    Output: /path/to/patch.tvpatch
    Generated diff with 5 changed files
    Patch bundle created: patch.tvpatch
    Bundle size: 12345 bytes
    Patch generated successfully: 5 files changed
"""

# ==============================================================================
# 2. APPLYING A PATCH VIA WEB UI
# ==============================================================================

"""
Step-by-step web UI workflow:

1. Navigate to patch manager:
   http://localhost:5000/patches

2. See current system status:
   - Version: 1.0.0
   - Build Number: 1
   - Rollback Available: No
   - Patch History: [] (empty)

3. Upload patch:
   - Drag patch_feature_update.tvpatch into upload area
   OR
   - Click "Browse Files" and select patch

4. Verify file info appears:
   - Selected File: patch_feature_update.tvpatch
   - File Size: 12.34 KB

5. Click "Apply Patch" button

6. System performs:
   - Extract patch bundle
   - Verify version compatibility
   - Validate SHA256 checksums
   - Create backup: backup_patch_feature_update_20250131_143022
   - Apply unified diffs
   - Update version.json
   - Display success toast

7. Click "Restart" button (or auto-restart after 5s)

8. App restarts and loads new version

Post-patch system status:
   - Version: 1.0.1 (updated)
   - Build Number: 2 (incremented)
   - Rollback Available: Yes (backup exists)
   - Patch History: ["patch_feature_update"]
"""

# ==============================================================================
# 3. ROLLING BACK A PATCH
# ==============================================================================

"""
To revert to previous version:

1. Navigate to /patches

2. Check "Rollback Available" indicator
   - Shows "●  Available" in green if rollback possible
   - Shows "○  Not available" in gray if no backup

3. Click "Rollback" button

4. Confirm in dialog:
   "Are you sure you want to rollback? This will restore the previous version."

5. System performs:
   - Locate backup directory
   - Restore all files from backup
   - Update version.json
   - Clear rollback_available flag
   - Display success toast

6. App restarts

Post-rollback system status:
   - Version: 1.0.0 (reverted)
   - Build Number: 1 (reverted)
   - Rollback Available: No (backup consumed)
   - Patch History: [] (cleared)
"""

# ==============================================================================
# 4. CHECKING VERSION VIA API
# ==============================================================================

"""
Get version info programmatically:

    GET /api/version

curl example:
    curl http://localhost:5000/api/version | jq .

Response:
    {
      "version": "1.0.0",
      "build_number": 1,
      "patches": ["patch_id_1", "patch_id_2"],
      "rollback_available": true
    }

Direct file access:
    cat content/version.json | jq .

Output:
    {
      "version": "1.0.1",
      "build_date": "2025-01-31T14:30:22.123456",
      "build_number": 2,
      "app_name": "TVArgenta",
      "release_channel": "stable",
      "patches_applied": ["patch_feature_update"],
      "rollback_available": true,
      "last_rollback": "backup_patch_feature_update_20250131_143022"
    }
"""

# ==============================================================================
# 5. API ENDPOINTS
# ==============================================================================

"""
Complete API reference:

GET /api/version
    Get current version information
    
    Response: JSON with version, build_number, patches, rollback_available

POST /api/patches/apply
    Apply a patch bundle
    
    Request:
        Content-Type: multipart/form-data
        Body: patch file
    
    Response: JSON with success, message, backup_id, restart_required

POST /api/patches/rollback
    Rollback to previous version
    
    Request:
        (empty body, POST to endpoint)
    
    Response: JSON with success, message, restart_required

Examples using curl:

    # Check version
    curl http://localhost:5000/api/version

    # Apply patch
    curl -X POST -F "patch=@patch.tvpatch" http://localhost:5000/api/patches/apply

    # Rollback
    curl -X POST http://localhost:5000/api/patches/rollback
"""

# ==============================================================================
# 6. ERROR SCENARIOS AND RECOVERY
# ==============================================================================

"""
Common error scenarios and recovery:

SCENARIO 1: Checksum Mismatch
    Error: "Integrity check failed: Checksum mismatch for app.py"
    Cause: Patch corrupted or modified after creation
    Recovery:
    1. Patch not applied (automatic abort)
    2. No files modified
    3. Re-download patch from source
    4. Retry apply

SCENARIO 2: Version Incompatibility
    Error: "Patch incompatible: expected 1.0.0, got 1.0.1"
    Cause: Patch created for different version
    Recovery:
    1. Patch not applied
    2. Create new patch for current version
    3. Or rollback to matching version first

SCENARIO 3: Patch Application Failure
    Error: "Patch application failed: hunk FAILED"
    Cause: Code changes conflict with local modifications
    Recovery:
    1. Automatic rollback triggered
    2. Files restored from backup
    3. Version.json not updated
    4. Manual merge required for custom code

SCENARIO 4: Backup Creation Failed
    Error: "Backup failed: Permission denied"
    Cause: Insufficient write permissions
    Recovery:
    1. Patch not applied (pre-check)
    2. Check file permissions: ls -la content/
    3. Fix permissions: chmod 755 content/
    4. Retry patch

SCENARIO 5: Rollback Not Available
    Error: "No rollback available"
    Cause: No backup exists (patch already applied and committed)
    Recovery:
    1. Manual restore required
    2. Or create new patch to revert changes
    3. Maintain backup of important states
"""

# ==============================================================================
# 7. BACKUP AND RESTORE DETAILS
# ==============================================================================

"""
Backup mechanism details:

Backup Directory Structure:
    content/backups/
    └── backup_patch_feature_update_20250131_143022/
        ├── app.py
        ├── scheduler.py
        ├── templates/
        │   ├── index.html
        │   └── mod_manager.html
        └── content/
            └── config/
                └── settings.json

Key points:
- Backup ID format: backup_{patch_id}_{YYYYMMDD}_{HHMMSS}
- Directory structure preserved (relative paths)
- File timestamps preserved with copy
- Only modified files backed up (space efficient)
- Backup cleanup (manual or via cleanup script)

To manually list backups:
    ls -la content/backups/

To manually restore a backup:
    cp -r content/backups/backup_id/* /app/

To remove old backups:
    rm -rf content/backups/backup_old_patch_*
"""

# ==============================================================================
# 8. PRODUCTION DEPLOYMENT
# ==============================================================================

"""
Best practices for production:

1. Pre-release testing:
   - Create patch in staging environment
   - Apply and test all functionality
   - Verify rollback works
   - Document any custom configurations

2. Patch creation:
   - Always use generate_patch.py tool
   - Specify meaningful --description
   - Create from stable baseline version
   - Test on similar hardware if possible

3. Deployment workflow:
   - Version current app: backup app directory
   - Upload patch via /patches UI
   - Monitor application after patch
   - Verify patch history in /api/version
   - Keep backup until confirmed stable

4. Monitoring:
   - Check app.log for patch-related errors
   - Monitor performance after patch
   - Check disk space (backups can accumulate)
   - Periodically cleanup old backups

5. Communication:
   - Notify users of patch schedule
   - Document patch contents
   - Provide rollback instructions to users
   - Log all patch activities

6. Backup management:
   - Keep at least 1 complete backup
   - Archive critical versions
   - Consider off-site backup for critical systems
   - Test restore procedures regularly
"""

# ==============================================================================
# 9. TROUBLESHOOTING
# ==============================================================================

"""
Troubleshooting guide:

Problem: Patch won't apply
    Check:
    1. Version matches: GET /api/version -> compare version_from in patch
    2. Patch file integrity: check file size reasonable
    3. File permissions: ls -la app.py (should be readable/writable)
    4. Disk space: df -h (ensure content/ has space)
    5. App logs: tail -f content/logs/tvargenta.log

Problem: Rollback not available
    Check:
    1. Patch applied successfully: check /api/version
    2. Backup exists: ls -la content/backups/
    3. Backup ID matches: grep last_rollback content/version.json
    4. File permissions: ls -la content/backups/

Problem: App crashes after patch
    Check:
    1. App logs: tail -f content/logs/tvargenta.log
    2. Syntax errors: python3 -m py_compile app.py
    3. Import errors: grep import app.py | head -20
    4. System resources: top (CPU, memory, disk)
    5. Rollback: POST /api/patches/rollback

Problem: Patch applies but features not working
    Check:
    1. App restarted: check service status
    2. Configuration updates: compare config files
    3. Dependencies installed: pip list
    4. Database migrations: check metadata.json
    5. Service restart: sudo systemctl restart tvargenta

Problem: Backup directory too large
    Check:
    1. Number of backups: ls -1 content/backups/ | wc -l
    2. Backup sizes: du -sh content/backups/*/
    3. Age of backups: ls -lt content/backups/
    4. Cleanup: rm -rf content/backups/backup_*  (keep recent)
    5. Archive: tar -czf backups_archive.tar.gz content/backups/

Logs to check:
    - /app/content/logs/tvargenta.log (app errors)
    - systemd log: journalctl -u tvargenta -f
    - Patch operations: grep -i patch content/logs/tvargenta.log
"""

# ==============================================================================
# 10. ADVANCED USAGE
# ==============================================================================

"""
Advanced scenarios:

Creating patches programmatically:
    import subprocess
    result = subprocess.run([
        'python3', 'generate_patch.py',
        'v1.0.0', 'v1.0.1', 'patch.tvpatch',
        '--description', 'Auto-generated patch'
    ])

Scripted patch application:
    import requests
    with open('patch.tvpatch', 'rb') as f:
        files = {'patch': f}
        response = requests.post(
            'http://localhost:5000/api/patches/apply',
            files=files
        )
        print(response.json())

Scheduled patches via cron:
    # /etc/cron.d/tvargenta_patches
    0 3 * * 0 /usr/local/bin/apply_patch.sh /path/to/patch.tvpatch

Patch signing (future enhancement):
    - Add GPG signature to manifest.json
    - Verify signature before apply
    - Track trusted signers

Chained patches:
    - Apply multiple patches in sequence
    - Update version incrementally
    - Each patch has rollback point

Custom patch preprocessing:
    - Run database migrations
    - Update configuration files
    - Execute initialization scripts
"""

# ==============================================================================
# 11. FILE LOCATIONS
# ==============================================================================

"""
Important file locations:

Core patch system:
    patch_system.py             - Patch logic implementation
    generate_patch.py           - Patch creation tool
    templates/patches.html      - Web UI

Configuration and tracking:
    content/version.json        - Current version info
    content/backups/            - Backup directories
    content/patches/            - Downloaded patches (optional)

Documentation:
    PATCH_SYSTEM.md             - Complete documentation
    PATCH_IMPLEMENTATION_COMPLETE.md - Implementation guide
    .github/copilot-instructions.md  - AI agent instructions

Logs and history:
    content/logs/tvargenta.log  - Application logs
    grep PATCH content/logs/tvargenta.log  - Patch operations
"""

# ==============================================================================
# 12. SUPPORT AND DOCUMENTATION
# ==============================================================================

"""
Further resources:

Documentation files:
    - PATCH_SYSTEM.md - Complete system documentation
    - PATCH_IMPLEMENTATION_COMPLETE.md - Implementation details
    - .github/copilot-instructions.md - Developer guide

API documentation:
    - GET /api/version - Version information
    - POST /api/patches/apply - Apply patch
    - POST /api/patches/rollback - Rollback

Web interface:
    - /patches - Patch manager UI
    - /mod_manager - Mod manager (related)

Code references:
    - patch_system.py - VersionInfo, PatchManifest, apply_patch()
    - generate_patch.py - generate_patch()
    - app.py - Endpoints and integration

Support:
    1. Check troubleshooting section above
    2. Review application logs
    3. Consult documentation files
    4. Check API responses for detailed errors
"""

if __name__ == "__main__":
    print("TVArgenta Patch System - Quick Start Guide")
    print("")
    print("See inline documentation above for:")
    print("  1. Creating patches")
    print("  2. Applying patches via web UI")
    print("  3. Rolling back patches")
    print("  4. API usage")
    print("  5. Error recovery")
    print("  6. Troubleshooting")
    print("")
    print("For complete documentation, see PATCH_SYSTEM.md")
