from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from app.media.audio import extract_audio


def prepare_media(video: dict[str, Any], base_dir: Path, run_date: str, ffmpeg_path: str) -> dict[str, Any]:
    media_dir = base_dir / "outputs" / "media" / run_date
    media_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "video_path": "",
        "audio_path": video.get("audio_path", ""),
        "source": "none",
    }

    if video.get("audio_path") and Path(video["audio_path"]).exists():
        result["audio_path"] = str(Path(video["audio_path"]).resolve())
        result["source"] = "audio_path"
        return result

    local_media_path = video.get("local_media_path", "")
    if local_media_path and Path(local_media_path).exists():
        resolved = Path(local_media_path).resolve()
        result["video_path"] = str(resolved)
        result["source"] = "local_media"
        result["audio_path"] = _maybe_extract_audio(resolved, media_dir, video["video_id"], ffmpeg_path)
        return result

    media_url = video.get("media_url", "")
    if media_url:
        extension = _guess_extension(media_url)
        target_path = media_dir / f"{video['video_id']}{extension}"
        _download_file(media_url, target_path)
        result["video_path"] = str(target_path.resolve())
        result["source"] = "download"
        result["audio_path"] = _maybe_extract_audio(target_path, media_dir, video["video_id"], ffmpeg_path)
        return result

    return result


def _download_file(media_url: str, target_path: Path) -> None:
    request = urllib.request.Request(
        media_url,
        headers={"User-Agent": os.getenv("DOUYIN_USER_AGENT", "Mozilla/5.0")},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        with target_path.open("wb") as output_file:
            shutil.copyfileobj(response, output_file)


def _maybe_extract_audio(video_path: Path, media_dir: Path, video_id: str, ffmpeg_path: str) -> str:
    audio_path = media_dir / f"{video_id}.mp3"
    if extract_audio(video_path, audio_path, ffmpeg_path):
        return str(audio_path.resolve())
    return ""


def _guess_extension(media_url: str) -> str:
    suffix = Path(media_url.split("?")[0]).suffix
    return suffix if suffix else ".mp4"
