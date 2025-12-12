#!/usr/bin/env python3
"""
Metadata Population Daemon for TVArgenta

Background service that populates missing metadata for videos:
- loudness_lufs: Audio loudness in LUFS for volume normalization
- duracion: Video duration (if missing)

Runs with low resource priority to avoid impacting system performance.

Usage:
    python3 metadata_daemon.py

The daemon will:
1. Periodically scan for videos missing metadata
2. Process one video at a time with throttling
3. Use nice/ionice for low CPU/IO priority
4. Sleep between videos to avoid resource contention
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Configuration
CHECK_INTERVAL = 300          # Seconds between scans for new work (5 minutes)
SLEEP_BETWEEN_VIDEOS = 60     # Seconds to sleep between processing videos
NICE_LEVEL = 19               # Lowest CPU priority (19 = nicest)
IONICE_CLASS = 3              # Idle I/O class (only when disk is free)
FFMPEG_THREADS = 1            # Single-threaded FFmpeg

# Paths
ROOT_DIR = Path(__file__).parent
CONTENT_DIR = ROOT_DIR / "content"
VIDEO_DIR = CONTENT_DIR / "videos"
METADATA_FILE = CONTENT_DIR / "metadata.json"

# State
running = True


def ts():
    """Timestamp for logging."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def load_metadata():
    """Load metadata from JSON file."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    """Save metadata to JSON file."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def get_video_path(video_id, info):
    """Determine the file path for a video based on its metadata."""
    if info.get("commercials_path"):
        return VIDEO_DIR / f"{info['commercials_path']}.mp4"
    elif info.get("series_path"):
        return VIDEO_DIR / f"{info['series_path']}.mp4"
    else:
        return VIDEO_DIR / f"{video_id}.mp4"


def analyze_loudness_throttled(filepath):
    """
    Analyze audio loudness using FFmpeg with resource throttling.
    Uses nice/ionice for low priority and single-threaded processing.
    Returns integrated loudness in LUFS, or None if analysis fails.
    """
    try:
        # Build command with nice and ionice for low resource usage
        cmd = [
            "nice", "-n", str(NICE_LEVEL),
            "ionice", "-c", str(IONICE_CLASS),
            "ffmpeg",
            "-threads", str(FFMPEG_THREADS),
            "-i", str(filepath),
            "-af", "ebur128=framelog=verbose",
            "-f", "null", "-"
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600  # 10 minute timeout for very long videos
        )

        # Parse integrated loudness from stderr
        for line in result.stderr.split('\n'):
            line = line.strip()
            if line.startswith('I:') and 'LUFS' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'LUFS' and i > 0:
                        try:
                            return float(parts[i-1])
                        except ValueError:
                            continue
        return None

    except subprocess.TimeoutExpired:
        print(f"[{ts()}] [META] Timeout analyzing loudness")
        return None
    except Exception as e:
        print(f"[{ts()}] [META] Error analyzing loudness: {e}")
        return None


def get_duration_throttled(filepath):
    """
    Get video duration using ffprobe with resource throttling.
    """
    try:
        cmd = [
            "nice", "-n", str(NICE_LEVEL),
            "ionice", "-c", str(IONICE_CLASS),
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(filepath)
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        return float(result.stdout.strip())

    except (subprocess.TimeoutExpired, ValueError, Exception) as e:
        print(f"[{ts()}] [META] Error getting duration: {e}")
        return None


def find_videos_needing_metadata(metadata):
    """
    Find videos that are missing loudness_lufs or duracion.
    Returns list of (video_id, info, missing_fields) tuples.
    """
    needs_work = []

    for video_id, info in metadata.items():
        missing = []

        if info.get("loudness_lufs") is None:
            missing.append("loudness_lufs")

        if info.get("duracion") is None:
            missing.append("duracion")

        if missing:
            needs_work.append((video_id, info, missing))

    return needs_work


def process_one_video(video_id, info, missing_fields, metadata):
    """
    Process a single video to populate missing metadata.
    Returns True if any metadata was updated.
    """
    filepath = get_video_path(video_id, info)

    if not filepath.exists():
        print(f"[{ts()}] [META] File not found: {filepath}")
        return False

    updated = False
    category = info.get("category", "unknown")

    print(f"[{ts()}] [META] Processing: {video_id} ({category})")
    print(f"[{ts()}] [META]   Missing: {', '.join(missing_fields)}")

    # Get duration if missing
    if "duracion" in missing_fields:
        print(f"[{ts()}] [META]   Analyzing duration...", end=" ", flush=True)
        duration = get_duration_throttled(filepath)
        if duration is not None:
            metadata[video_id]["duracion"] = duration
            print(f"{duration:.1f}s")
            updated = True
        else:
            print("FAILED")

    # Get loudness if missing
    if "loudness_lufs" in missing_fields:
        print(f"[{ts()}] [META]   Analyzing loudness...", end=" ", flush=True)
        lufs = analyze_loudness_throttled(filepath)
        if lufs is not None:
            metadata[video_id]["loudness_lufs"] = lufs
            print(f"{lufs:.1f} LUFS")
            updated = True
        else:
            print("FAILED")

    return updated


def run_daemon():
    """Main daemon loop."""
    global running

    print(f"[{ts()}] [META] TVArgenta Metadata Daemon starting...")
    print(f"[{ts()}] [META] Configuration:")
    print(f"[{ts()}] [META]   Check interval: {CHECK_INTERVAL}s")
    print(f"[{ts()}] [META]   Sleep between videos: {SLEEP_BETWEEN_VIDEOS}s")
    print(f"[{ts()}] [META]   Nice level: {NICE_LEVEL}")
    print(f"[{ts()}] [META]   I/O class: {IONICE_CLASS} (idle)")

    while running:
        try:
            # Load current metadata
            metadata = load_metadata()

            if not metadata:
                print(f"[{ts()}] [META] No videos in metadata, sleeping...")
                time.sleep(CHECK_INTERVAL)
                continue

            # Find videos needing work
            needs_work = find_videos_needing_metadata(metadata)

            if not needs_work:
                print(f"[{ts()}] [META] All videos have metadata, sleeping {CHECK_INTERVAL}s...")
                time.sleep(CHECK_INTERVAL)
                continue

            print(f"[{ts()}] [META] Found {len(needs_work)} videos needing metadata")

            # Process one video
            video_id, info, missing_fields = needs_work[0]

            updated = process_one_video(video_id, info, missing_fields, metadata)

            if updated:
                save_metadata(metadata)
                print(f"[{ts()}] [META] Saved metadata for {video_id}")

            # Sleep before next video (or before next check)
            remaining = len(needs_work) - 1
            if remaining > 0 and running:
                print(f"[{ts()}] [META] {remaining} videos remaining, sleeping {SLEEP_BETWEEN_VIDEOS}s...")
                time.sleep(SLEEP_BETWEEN_VIDEOS)
            else:
                print(f"[{ts()}] [META] Batch complete, sleeping {CHECK_INTERVAL}s...")
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n[{ts()}] [META] Interrupted by keyboard")
            break

        except Exception as e:
            print(f"[{ts()}] [META] Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)

    print(f"[{ts()}] [META] Daemon stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global running
    print(f"\n[{ts()}] [META] Received signal {signum}, shutting down...")
    running = False


def main():
    """Entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the daemon
    run_daemon()


if __name__ == "__main__":
    main()
