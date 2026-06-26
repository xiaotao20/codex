from __future__ import annotations

import os
from pathlib import Path

from app.models import TranscriptResult


def transcribe_video(
    video: dict,
    output_path: Path,
) -> TranscriptResult:
    force_mock = os.getenv("PIPELINE_FORCE_MOCK_AI", "false").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    audio_path = Path(video.get("audio_path", "")) if video.get("audio_path") else None

    if api_key and not force_mock and audio_path and audio_path.exists():
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
            with audio_path.open("rb") as audio_file:
                response = client.audio.transcriptions.create(model=model, file=audio_file)
            transcript_text = getattr(response, "text", "").strip()
            if transcript_text:
                return TranscriptResult(
                    video_id=video["video_id"],
                    transcript_raw=transcript_text,
                    transcript_clean=transcript_text,
                    duration_seconds=0.0,
                    source="openai",
                )
        except Exception:
            pass

    transcript_text = _build_mock_transcript(video)
    return TranscriptResult(
        video_id=video["video_id"],
        transcript_raw=transcript_text,
        transcript_clean=transcript_text,
        duration_seconds=0.0,
        source="mock",
    )


def _build_mock_transcript(video: dict) -> str:
    text_hint = video.get("text_hint") or ""
    description = video.get("description") or ""
    topic_tags = "、".join(video.get("topic_tags", []))
    parts = [
        video.get("title", ""),
        text_hint,
        f"补充信息：{description}" if description else "",
        f"关键词：{topic_tags}" if topic_tags else "",
    ]
    return "".join(part for part in parts if part)
