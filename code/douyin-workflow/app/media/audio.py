from __future__ import annotations

import subprocess
from pathlib import Path


def extract_audio(video_path: Path, audio_path: Path, ffmpeg_path: str) -> bool:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "mp3",
        str(audio_path),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return False
    return completed.returncode == 0 and audio_path.exists()
