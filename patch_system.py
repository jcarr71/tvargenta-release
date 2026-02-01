#!/usr/bin/env python3
"""
TVArgenta Patch System

Provides functionality to:
- Apply patches to the application
- Verify patch integrity
- Rollback to previous versions
- Track version history
"""

import json
import hashlib
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import tarfile
import tempfile

logger = logging.getLogger("tvargenta.patches")

# Paths
CONTENT_DIR = Path(__file__).parent.parent / "content"
VERSION_FILE = CONTENT_DIR / "version.json"
PATCHES_DIR = CONTENT_DIR / "patches"
BACKUPS_DIR = CONTENT_DIR / "backups"

# Create directories if needed
PATCHES_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


class VersionInfo:
    """Manages version.json file"""
    
    def __init__(self, version_file: Path = VERSION_FILE):
        self.path = version_file
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load version.json"""
        try:
            if self.path.exists():
                with open(self.path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load version file: {e}")
        
        # Default version
        return {
            "version": "1.0.0",
            "build_date": datetime.now().isoformat(),
            "build_number": 1,
            "app_name": "TVArgenta",
            "release_channel": "stable",
            "patches_applied": [],
            "rollback_available": False,
            "last_rollback": None
        }
    
    def save(self):
        """Save version.json"""
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved version: {self.data['version']}")
        except Exception as e:
            logger.error(f"Failed to save version file: {e}")
            raise
    
    @property
    def version(self) -> str:
        return self.data.get("version", "1.0.0")
    
    @property
    def build_number(self) -> int:
        return self.data.get("build_number", 1)
    
    @property
    def patches(self) -> List[str]:
        return self.data.get("patches_applied", [])
    
    def add_patch(self, patch_id: str):
        """Record a patch application"""
        if patch_id not in self.data["patches_applied"]:
            self.data["patches_applied"].append(patch_id)
            self.save()
    
    def update_version(self, new_version: str, build_number: int = None):
        """Update version number"""
        self.data["version"] = new_version
        if build_number:
            self.data["build_number"] = build_number
        self.data["build_date"] = datetime.now().isoformat()
        self.save()


class PatchManifest:
    """Represents a patch manifest"""
    
    def __init__(self, manifest_dict: Dict[str, Any]):
        self.data = manifest_dict
    
    @property
    def patch_id(self) -> str:
        return self.data.get("id", "unknown")
    
    @property
    def version_from(self) -> str:
        return self.data.get("version_from", "1.0.0")
    
    @property
    def version_to(self) -> str:
        return self.data.get("version_to", "1.0.0")
    
    @property
    def description(self) -> str:
        return self.data.get("description", "")
    
    @property
    def files(self) -> Dict[str, str]:
        """Dict of filename -> checksum"""
        return self.data.get("files", {})
    
    @property
    def checksums(self) -> Dict[str, str]:
        """Dict of filename -> expected checksum"""
        return self.data.get("checksums", {})
    
    def is_compatible_with(self, current_version: str) -> bool:
        """Check if patch is compatible with current version"""
        return self.version_from == current_version


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file"""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {filepath}: {e}")
        return ""


def backup_files(file_list: List[Path], backup_id: str) -> Path:
    """Create backup of files before patching"""
    backup_dir = BACKUPS_DIR / backup_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        for filepath in file_list:
            if filepath.exists():
                # Preserve directory structure
                relative_path = filepath.relative_to(Path(__file__).parent.parent)
                backup_path = backup_dir / relative_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(filepath, backup_path)
                logger.info(f"Backed up: {relative_path}")
        
        return backup_dir
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise


def restore_from_backup(backup_id: str) -> bool:
    """Restore files from backup"""
    backup_dir = BACKUPS_DIR / backup_id
    
    if not backup_dir.exists():
        logger.error(f"Backup not found: {backup_id}")
        return False
    
    try:
        app_root = Path(__file__).parent.parent
        
        for backup_file in backup_dir.rglob('*'):
            if backup_file.is_file():
                relative_path = backup_file.relative_to(backup_dir)
                target_path = app_root / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, target_path)
                logger.info(f"Restored: {relative_path}")
        
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def apply_patch_file(patch_path: Path, target_dir: Path) -> Tuple[bool, str]:
    """
    Apply a .patch file using patch command.
    Returns (success, message)
    """
    try:
        # Read patch file
        with open(patch_path, 'r', encoding='utf-8') as f:
            patch_content = f.read()
        
        # Write to temporary file for patch command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False, encoding='utf-8') as tmp:
            tmp.write(patch_content)
            tmp_path = tmp.name
        
        try:
            # Apply patch
            result = subprocess.run(
                ['patch', '-p1', '-i', tmp_path],
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Patch applied successfully: {patch_path}")
                return True, "Patch applied successfully"
            else:
                msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Patch application failed: {msg}")
                return False, msg
        finally:
            Path(tmp_path).unlink()
    
    except Exception as e:
        logger.error(f"Failed to apply patch: {e}")
        return False, str(e)


def extract_patch_bundle(bundle_path: Path, extract_dir: Path) -> Tuple[bool, Optional[PatchManifest]]:
    """
    Extract .tvpatch bundle (tar.gz format).
    Returns (success, manifest)
    """
    try:
        if not bundle_path.exists():
            return False, None
        
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(bundle_path, 'r:gz') as tar:
            tar.extractall(path=extract_dir)
        
        # Load manifest
        manifest_path = extract_dir / 'manifest.json'
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            return True, PatchManifest(manifest_data)
        
        return False, None
    
    except Exception as e:
        logger.error(f"Failed to extract patch bundle: {e}")
        return False, None


def verify_patch_integrity(manifest: PatchManifest, patch_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify patch bundle integrity using checksums.
    Returns (valid, list of errors)
    """
    errors = []
    
    try:
        for filename, expected_checksum in manifest.checksums.items():
            file_path = patch_dir / filename
            
            if not file_path.exists():
                errors.append(f"Missing file: {filename}")
                continue
            
            actual_checksum = compute_file_checksum(file_path)
            if actual_checksum != expected_checksum:
                errors.append(
                    f"Checksum mismatch for {filename}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )
        
        if errors:
            logger.error(f"Patch integrity check failed: {errors}")
            return False, errors
        
        logger.info("Patch integrity verified successfully")
        return True, []
    
    except Exception as e:
        logger.error(f"Integrity verification failed: {e}")
        return False, [str(e)]


def apply_patch(bundle_path: Path, current_version: str) -> Tuple[bool, str, Optional[str]]:
    """
    Apply a patch bundle.
    Returns (success, message, backup_id)
    """
    backup_id = None
    
    try:
        # Extract patch bundle
        with tempfile.TemporaryDirectory() as tmpdir:
            extract_dir = Path(tmpdir) / "patch"
            success, manifest = extract_patch_bundle(bundle_path, extract_dir)
            
            if not success or not manifest:
                return False, "Failed to extract patch bundle", None
            
            logger.info(f"Applying patch {manifest.patch_id}: {manifest.version_from} -> {manifest.version_to}")
            
            # Check compatibility
            if not manifest.is_compatible_with(current_version):
                msg = f"Patch incompatible: expected {manifest.version_from}, got {current_version}"
                logger.error(msg)
                return False, msg, None
            
            # Verify integrity
            valid, errors = verify_patch_integrity(manifest, extract_dir)
            if not valid:
                return False, f"Integrity check failed: {', '.join(errors)}", None
            
            # Create backup
            app_root = Path(__file__).parent.parent
            files_to_backup = []
            for filename in manifest.files.keys():
                file_path = app_root / filename
                if file_path.exists():
                    files_to_backup.append(file_path)
            
            backup_id = f"backup_{manifest.patch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                backup_files(files_to_backup, backup_id)
            except Exception as e:
                return False, f"Backup failed: {e}", None
            
            # Apply patch files
            patch_file = extract_dir / "patch.diff"
            if patch_file.exists():
                success, msg = apply_patch_file(patch_file, app_root)
                if not success:
                    # Rollback
                    restore_from_backup(backup_id)
                    return False, f"Patch application failed: {msg}", backup_id
            
            logger.info(f"Patch {manifest.patch_id} applied successfully")
            return True, f"Patch applied: {manifest.description}", backup_id
    
    except Exception as e:
        logger.error(f"Patch application error: {e}")
        if backup_id:
            restore_from_backup(backup_id)
        return False, str(e), backup_id
