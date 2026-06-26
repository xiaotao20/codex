from pathlib import Path

from app.media.audio import extract_audio


def test_extract_audio_returns_false_when_ffmpeg_is_missing(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    audio_path = tmp_path / "audio.mp3"
    video_path.write_bytes(b"fake-video")

    assert extract_audio(video_path, audio_path, "ffmpeg-not-found") is False
