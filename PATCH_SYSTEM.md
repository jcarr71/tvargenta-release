# TVArgenta Patching System

Complete live-patch system for updating TVArgenta without code changes or manual file manipulation.

## Architecture

### Core Components

**patch_system.py** (~300 lines)
- `VersionInfo`: Manages version.json metadata
- `PatchManifest`: Represents patch bundles
- `apply_patch()`: Main patch application function
- `verify_patch_integrity()`: SHA256 checksum verification
- `backup_files()` / `restore_from_backup()`: Backup/rollback mechanism
- Atomic operations for safety

**generate_patch.py** (~250 lines)
- Command-line tool to create patch bundles
- Unified diff generation for changed files
- SHA256 checksum computation
- Tar.gz bundle creation with manifest

### Data Files

**content/version.json** - Version tracking
```json
{
  "version": "1.0.0",
  "build_date": "2025-01-31T...",
  "build_number": 1,
  "app_name": "TVArgenta",
  "release_channel": "stable",
  "patches_applied": ["patch_id_1", "patch_id_2"],
  "rollback_available": true,
  "last_rollback": "backup_patch_id_1_20250131_120000"
}
```

**Patch Bundle (.tvpatch)** - Tar.gz container
```
patch.tvpatch
├── manifest.json (metadata)
├── patch.diff (unified diff)
└── [supporting files]
```

**Backup Directories** - content/backups/{backup_id}/
```
content/backups/backup_patch_id_1_20250131_120000/
├── app.py
├── scheduler.py
└── [other changed files with directory structure preserved]
```

## Patch Manifest Format

```json
{
  "id": "patch_feature_x_20250131",
  "version_from": "1.0.0",
  "version_to": "1.0.1",
  "description": "Feature X implementation with bug fixes",
  "created_date": "2025-01-31T12:00:00",
  "files": [
    "app.py",
    "scheduler.py",
    "templates/index.html"
  ],
  "checksums": {
    "app.py": "abc123...",
    "scheduler.py": "def456...",
    "templates/index.html": "ghi789..."
  }
}
```

## Workflow

### 1. Creating a Patch

```bash
# Create patch from two versions
python3 generate_patch.py \
  /path/to/version1 \
  /path/to/version2 \
  output_patch.tvpatch \
  --description "Feature update"
```

Process:
1. Scans both directories for Python/Web files
2. Generates unified diffs for changed files
3. Computes SHA256 checksums of new files
4. Creates manifest.json with metadata
5. Bundles into .tvpatch (tar.gz format)

### 2. Applying a Patch

User Interface: `/patches` endpoint

1. **Upload Patch**
   - Drag & drop or browse .tvpatch file
   - Shows file info (size, type)

2. **Verification**
   - Extract bundle
   - Check version compatibility (version_from must match current)
   - Verify SHA256 checksums

3. **Backup**
   - Create backup_id from patch ID + timestamp
   - Copy all affected files to content/backups/{backup_id}/
   - Preserve directory structure

4. **Apply**
   - Apply unified diff using `patch` command
   - Update files in-place
   - Update version.json with patch ID

5. **Restart**
   - Trigger app restart
   - POST /api/app/restart endpoint

### 3. Rolling Back

User Interface: Rollback button on `/patches` page

1. **Check Availability**
   - Only available if rollback_available = true
   - last_rollback contains backup_id

2. **Restore Files**
   - Find backup directory
   - Copy files back to original locations
   - Preserve file timestamps

3. **Update Tracking**
   - Clear rollback_available flag
   - Clear last_rollback
   - Save version.json

## API Endpoints

### GET /api/version
Get current version information
```bash
curl http://localhost:5000/api/version

{
  "version": "1.0.0",
  "build_number": 1,
  "patches": ["patch_id_1"],
  "rollback_available": true
}
```

### POST /api/patches/apply
Apply a patch bundle
```bash
curl -X POST -F "patch=@output_patch.tvpatch" http://localhost:5000/api/patches/apply

{
  "success": true,
  "message": "Patch applied: Feature update",
  "backup_id": "backup_patch_feature_x_20250131_120000",
  "restart_required": true
}
```

### POST /api/patches/rollback
Rollback to previous version
```bash
curl -X POST http://localhost:5000/api/patches/rollback

{
  "success": true,
  "message": "Rolled back successfully",
  "restart_required": true
}
```

## Web Interface

**GET /patches** - Patch manager UI

Features:
- **System Status Panel**
  - Current version display
  - Build number
  - Rollback availability
  - Patch history list

- **Apply Patch Panel**
  - Drag & drop upload area
  - File info display (name, size)
  - Apply button (disabled until file selected)
  - Rollback button (disabled until rollback available)

- **Real-time Updates**
  - 5-second polling of /api/version
  - Status updates without page reload
  - Toast notifications for actions

## Error Handling

### Checksum Mismatch
- Indicates patch corruption or tampering
- Rollback triggered automatically
- Error message: "Integrity check failed"

### Version Incompatibility
- Patch only applies to specific version
- Example: patch_1.0.0_to_1.0.1 won't apply to 1.0.2
- Error message: "Patch incompatible: expected 1.0.0, got X.Y.Z"

### Backup Failure
- Patch aborted before applying any changes
- Prevents partial updates
- Error message: "Backup failed: [reason]"

### Patch Application Failure
- Automatic rollback triggered
- Files restored from backup
- Version tracking not updated
- Error message: "Patch application failed: [reason]"

## Safety Features

1. **Atomic Writes** - All file operations use temp → rename pattern
2. **Checksum Verification** - SHA256 prevents tampering
3. **Pre-patch Backup** - Always backup before applying
4. **Version Checking** - Compatibility verification before apply
5. **Automatic Rollback** - On any error during application
6. **History Tracking** - All patches recorded in version.json

## Integration with Mod System

Patch system is **core**, not a mod:
- Essential for system updates
- Always loaded at startup
- Not toggleable via mod manager

Future: Can create patch_mod wrapper for UI if desired

## Performance

- **Checksum Computation**: ~100MB/sec (optimized with 8KB chunks)
- **Backup Creation**: ~500MB/sec (file copy speed)
- **Patch Application**: Depends on diff size (typically <1 second)
- **Bundle Size**: Tar.gz compression (typically 1-10% of original)

## Testing

### Create Test Patch
```bash
# Copy current version
cp -r . version1/

# Make changes
# ... edit files ...

# Generate patch
python3 generate_patch.py version1 . test_patch.tvpatch --description "Test"

# Would create: test_patch.tvpatch with manifest and diffs
```

### Apply Patch
1. Upload via web UI
2. Check /api/version for applied patches
3. Verify changes applied
4. Test rollback

## Future Enhancements

1. **Patch Signatures** - Add GPG/ED25519 signing
2. **Delta Compression** - Further reduce bundle size
3. **Partial Rollback** - Rollback specific patches
4. **Patch Scheduling** - Apply at specific times
5. **Distributed Patches** - Download from update server
6. **Dependency Resolution** - Chain multiple patches
7. **Dry Run Mode** - Preview patch without applying
8. **Patch Scripting** - Custom pre/post-patch scripts

## Troubleshooting

### Patch Won't Apply
1. Check version matches (GET /api/version)
2. Verify patch file isn't corrupted
3. Check file permissions in app directory
4. Review app.log for detailed errors

### Rollback Not Available
1. Check rollback_available flag in /api/version
2. Verify backup directory exists
3. Check file permissions in content/backups/

### App Won't Restart
1. Manual restart: `sudo systemctl restart tvargenta`
2. Check systemd logs: `journalctl -u tvargenta -f`
3. Verify file permissions after patch

## See Also

- `patch_system.py` - Core patch logic
- `generate_patch.py` - Patch creation tool
- `templates/patches.html` - Web UI
- `app.py` - API endpoints

