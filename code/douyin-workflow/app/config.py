from __future__ import annotations

from pathlib import Path

import yaml

from app.models import AppSettings, CreatorConfig, PipelineConfig


def load_config(path: Path) -> PipelineConfig:
    with path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}

    settings_payload = payload.get("settings", {})
    creators_payload = payload.get("creators", [])

    settings = AppSettings(
        fetch_adapter=settings_payload.get("fetch_adapter", "stub"),
        report_top_n=int(settings_payload.get("report_top_n", 10)),
        max_videos_per_creator=int(settings_payload.get("max_videos_per_creator", 2)),
        local_seed_file=settings_payload.get("local_seed_file", "seeds/example_videos.json"),
        ffmpeg_path=settings_payload.get("ffmpeg_path", "ffmpeg"),
    )
    creators = [
        CreatorConfig(
            creator_id=item["creator_id"],
            name=item["name"],
            homepage=item["homepage"],
            enabled=bool(item.get("enabled", True)),
            content_hint=item.get("content_hint", ""),
        )
        for item in creators_payload
        if item.get("enabled", True)
    ]
    return PipelineConfig(settings=settings, creators=creators)
