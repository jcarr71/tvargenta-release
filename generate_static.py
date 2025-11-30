#!/usr/bin/env python3
"""
Generate white noise static video for VHS "no tape" / "tape ended" state.
Uses ffmpeg to create a looping static video with authentic TV noise.
"""

import subprocess
import os
import sys
from pathlib import Path

# Output paths
SCRIPT_DIR = Path(__file__).parent
STATIC_DIR = SCRIPT_DIR / "static" / "videos"
OUTPUT_FILE = STATIC_DIR / "vhs_static.mp4"

# Video parameters
DURATION = 10  # seconds (will loop)
WIDTH = 1920
HEIGHT = 1080
FPS = 30


def generate_static_video():
    """Generate white noise static video using ffmpeg."""

    # Ensure output directory exists
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg.")
        sys.exit(1)

    print(f"Generating {DURATION}s static video at {WIDTH}x{HEIGHT}...")

    # ffmpeg command to generate TV static noise
    # Uses noise source with high/low frequency mix for authentic CRT look
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-f", "lavfi",
        "-i", f"nullsrc=size={WIDTH}x{HEIGHT}:rate={FPS}:duration={DURATION},"
              f"geq=random(1)*255:128:128,"  # Random luma, neutral chroma
              f"format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg stderr: {result.stderr}")
            # Try alternative approach with simpler noise
            print("Trying alternative noise generation...")
            generate_static_alternative()
            return

        print(f"SUCCESS: Static video created at {OUTPUT_FILE}")
        print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"ERROR: {e}")
        print("Trying alternative method...")
        generate_static_alternative()


def generate_static_alternative():
    """Alternative method using noise filter."""

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=gray:size={WIDTH}x{HEIGHT}:rate={FPS}:duration={DURATION}",
        "-vf", "noise=alls=100:allf=t,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg stderr: {result.stderr}")
            raise Exception("Alternative method also failed")

        print(f"SUCCESS: Static video created at {OUTPUT_FILE}")
        print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"ERROR with alternative method: {e}")
        # Last resort: create a very simple static image sequence
        generate_static_simple()


def generate_static_simple():
    """Simplest method - just random noise frames."""

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"nullsrc=s={WIDTH}x{HEIGHT}:r={FPS}:d={DURATION}",
        "-vf", "geq=lum='random(1)*255':cb=128:cr=128",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        str(OUTPUT_FILE)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"All methods failed. ffmpeg stderr: {result.stderr}")
            print("\nManual fallback: Please create a static video manually and place it at:")
            print(f"  {OUTPUT_FILE}")
            sys.exit(1)

        print(f"SUCCESS: Static video created at {OUTPUT_FILE}")
        print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"FINAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_static_video()
