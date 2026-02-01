#!/usr/bin/env python3
"""
TVArgenta Patch Generator

Creates patch bundles from version differences.
Usage: python3 generate_patch.py <from_version_dir> <to_version_dir> <output_patch_file> [--description "..."]
"""

import argparse
import json
import hashlib
import tarfile
import tempfile
import difflib
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("patch_generator")

# Python files to include in patches
PATCHABLE_EXTENSIONS = {'.py', '.html', '.js', '.css', '.json', '.md', '.sh'}

# Directories to skip
SKIP_DIRS = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', '*.egg-info'}


def compute_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum"""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Checksum error for {filepath}: {e}")
        return ""


def should_include_file(filepath: Path, root: Path) -> bool:
    """Determine if file should be included in patch"""
    # Skip directories
    for skip in SKIP_DIRS:
        if skip.replace('*', '') in str(filepath):
            return False
    
    # Include if matches extension
    return filepath.suffix in PATCHABLE_EXTENSIONS


def get_file_list(directory: Path) -> List[Path]:
    """Get list of patchable files"""
    files = []
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return files
    
    for filepath in directory.rglob('*'):
        if filepath.is_file() and should_include_file(filepath, directory):
            files.append(filepath)
    
    return sorted(files)


def generate_unified_diff(from_file: Path, to_file: Path, from_dir: Path, to_dir: Path, relpath: Path) -> str:
    """Generate unified diff between two files"""
    
    # Use passed-in relpath to avoid calling relative_to() on non-existent files
    relative_path_str = str(relpath).replace('\\', '/')
    
    try:
        # Read file contents
        from_lines = []
        if from_file.exists():
            with open(from_file, 'r', encoding='utf-8', errors='ignore') as f:
                from_lines = f.readlines()
        
        to_lines = []
        if to_file.exists():
            with open(to_file, 'r', encoding='utf-8', errors='ignore') as f:
                to_lines = f.readlines()
        
        # Generate diff with standard a/ b/ prefixes for -p1 compatibility
        diff = difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f'a/{relative_path_str}',
            tofile=f'b/{relative_path_str}',
            lineterm='\n'
        )
        
        # Join without adding extra newlines (difflib already includes them)
        return ''.join(diff)
    
    except Exception as e:
        logger.error(f"Diff generation error for {relative_path_str}: {e}")
        return ""


def generate_patch(from_dir: Path, to_dir: Path, output_file: Path, description: str = "") -> Tuple[bool, str]:
    """
    Generate a patch bundle from two versions.
    Returns (success, message)
    """
    
    try:
        from_dir = Path(from_dir).resolve()
        to_dir = Path(to_dir).resolve()
        output_file = Path(output_file)
        
        logger.info(f"Generating patch from {from_dir} to {to_dir}")
        logger.info(f"Output: {output_file}")
        
        # Get file lists
        from_files = {f.relative_to(from_dir): f for f in get_file_list(from_dir)}
        to_files = {f.relative_to(to_dir): f for f in get_file_list(to_dir)}
        
        # Collect all changed files
        all_files = set(from_files.keys()) | set(to_files.keys())
        changed_files = []
        checksums = {}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            patch_dir = tmpdir / "patch_content"
            patch_dir.mkdir()
            
            # Generate unified diff
            diff_lines = []
            
            for relpath in sorted(all_files):
                from_file = from_files.get(relpath)
                to_file = to_files.get(relpath)
                
                # Skip if file didn't change
                if from_file and to_file:
                    if from_file.read_bytes() == to_file.read_bytes():
                        continue
                
                # Generate diff
                file_diff = generate_unified_diff(
                    from_file if from_file else to_file,
                    to_file if to_file else from_file,
                    from_dir,
                    to_dir,
                    relpath
                )
                
                if file_diff.strip():
                    diff_lines.append(file_diff)
                    # Normalize path to use forward slashes (Unix style)
                    relpath_str = str(relpath).replace('\\', '/')
                    changed_files.append(relpath_str)
                    
                    if to_file and to_file.exists():
                        checksums[relpath_str] = compute_checksum(to_file)
            
            if not diff_lines:
                return False, "No changes found between versions"
            
            # Write combined diff
            patch_file = patch_dir / "patch.diff"
            with open(patch_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(diff_lines))
            
            logger.info(f"Generated diff with {len(changed_files)} changed files")
            
            # Create manifest
            manifest = {
                "id": output_file.stem,
                "version_from": "1.0.0",
                "version_to": "1.0.1",
                "description": description or "Patch generated on " + datetime.now().isoformat(),
                "created_date": datetime.now().isoformat(),
                "files": changed_files,
                "checksums": checksums
            }
            
            manifest_file = patch_dir / "manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            # Create tar.gz bundle
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(output_file, 'w:gz') as tar:
                tar.add(patch_dir, arcname='.')
            
            logger.info(f"Patch bundle created: {output_file}")
            logger.info(f"Bundle size: {output_file.stat().st_size} bytes")
            
            return True, f"Patch generated successfully: {len(changed_files)} files changed"
    
    except Exception as e:
        logger.error(f"Patch generation failed: {e}")
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description='Generate TVArgenta patch bundles')
    parser.add_argument('from_dir', help='Source directory (current version)')
    parser.add_argument('to_dir', help='Target directory (new version)')
    parser.add_argument('output', help='Output patch file (.tvpatch)')
    parser.add_argument('--description', '-d', default='', help='Patch description')
    
    args = parser.parse_args()
    
    success, message = generate_patch(
        Path(args.from_dir),
        Path(args.to_dir),
        Path(args.output),
        args.description
    )
    
    logger.info(message)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
