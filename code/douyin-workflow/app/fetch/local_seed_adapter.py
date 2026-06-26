from __future__ import annotations

from datetime import date
from pathlib import Path

from app.io_utils import read_json
from app.fetch.base import FetchAdapter
from app.models import CreatorConfig, VideoMetadata


class LocalSeedAdapter(FetchAdapter):
    def __init__(self, seed_path: Path) -> None:
        self.seed_path = seed_path

    def fetch_videos(self, creators: list[CreatorConfig], run_date: date) -> list[VideoMetadata]:
        seed_items = read_json(self.seed_path, [])
        creator_index = {creator.creator_id: creator for creator in creators}
        videos: list[VideoMetadata] = []

        for item in seed_items:
            creator_id = item["creator_id"]
            if creator_id not in creator_index:
                continue
            creator = creator_index[creator_id]
            publish_time = item.get("publish_time") or f"{run_date.isoformat()}T09:00:00+08:00"
            videos.append(
                VideoMetadata(
                    creator_id=creator_id,
                    creator_name=item.get("creator_name", creator.name),
                    video_id=item["video_id"],
                    title=item["title"],
                    publish_time=publish_time,
                    video_url=item.get("video_url", ""),
                    cover_url=item.get("cover_url", ""),
                    like_count=int(item.get("like_count", 0)),
                    comment_count=int(item.get("comment_count", 0)),
                    share_count=int(item.get("share_count", 0)),
                    collect_count=int(item.get("collect_count", 0)),
                    description=item.get("description", creator.content_hint),
                    text_hint=item.get("text_hint", ""),
                    topic_tags=item.get("topic_tags", []),
                    source="local_seed",
                    media_url=item.get("media_url", ""),
                    local_media_path=item.get("local_media_path", ""),
                    audio_path=item.get("audio_path", ""),
                    transcript_hint=item.get("transcript_hint", ""),
                    raw_payload=item,
                )
            )
        return videos
