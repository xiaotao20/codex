from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CreatorConfig:
    creator_id: str
    name: str
    homepage: str
    enabled: bool = True
    content_hint: str = ""


@dataclass
class AppSettings:
    fetch_adapter: str = "stub"
    report_top_n: int = 10
    max_videos_per_creator: int = 2


@dataclass
class VideoMetadata:
    creator_id: str
    creator_name: str
    video_id: str
    title: str
    publish_time: str
    video_url: str
    cover_url: str
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collect_count: int = 0
    description: str = ""
    text_hint: str = ""
    topic_tags: list[str] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TranscriptResult:
    video_id: str
    transcript_raw: str
    transcript_clean: str
    language: str = "zh"
    duration_seconds: float = 0.0
    segments: list[dict[str, Any]] = field(default_factory=list)
    source: str = "mock"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    video_id: str
    summary: str
    clean_copy: str
    hooks: list[str]
    key_points: list[str]
    keywords: list[str]
    tone: str
    cta: str
    content_type: str
    risk_notes: list[str]
    source: str = "mock"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineConfig:
    settings: AppSettings
    creators: list[CreatorConfig]
