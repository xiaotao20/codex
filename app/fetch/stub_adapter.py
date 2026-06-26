from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta, timezone

from app.fetch.base import FetchAdapter
from app.models import CreatorConfig, VideoMetadata


class StubFetchAdapter(FetchAdapter):
    def __init__(self, max_videos_per_creator: int = 2) -> None:
        self.max_videos_per_creator = max_videos_per_creator
        self.timezone = timezone(timedelta(hours=8))

    def fetch_videos(self, creators: list[CreatorConfig], run_date: date) -> list[VideoMetadata]:
        videos: list[VideoMetadata] = []
        for creator in creators:
            for index in range(self.max_videos_per_creator):
                seed = f"{creator.creator_id}:{run_date.isoformat()}:{index}"
                digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
                video_id = digest[:18]
                publish_time = datetime.combine(
                    run_date,
                    time(hour=9 + index * 2, minute=15),
                    tzinfo=self.timezone,
                ).isoformat(timespec="seconds")
                like_count = 800 + int(digest[0:4], 16) % 9000
                comment_count = 30 + int(digest[4:8], 16) % 1200
                share_count = 10 + int(digest[8:12], 16) % 300
                collect_count = 5 + int(digest[12:16], 16) % 200
                keywords = self._keywords_from_hint(creator.content_hint)
                title = f"{creator.name} 第 {index + 1} 条选题：{keywords[0]}怎么落地"
                text_hint = (
                    f"今天拆解一个和{keywords[0]}有关的短视频案例，"
                    f"重点讲{keywords[1]}、{keywords[2]}和执行步骤。"
                    "最后给出一个适合运营团队复用的行动建议。"
                )
                videos.append(
                    VideoMetadata(
                        creator_id=creator.creator_id,
                        creator_name=creator.name,
                        video_id=video_id,
                        title=title,
                        publish_time=publish_time,
                        video_url=f"https://example.com/videos/{video_id}",
                        cover_url=f"https://example.com/covers/{video_id}.jpg",
                        like_count=like_count,
                        comment_count=comment_count,
                        share_count=share_count,
                        collect_count=collect_count,
                        description=creator.content_hint,
                        text_hint=text_hint,
                        topic_tags=keywords,
                        raw_payload={
                            "adapter": "stub",
                            "seed": seed,
                            "homepage": creator.homepage,
                        },
                    )
                )
        return videos

    @staticmethod
    def _keywords_from_hint(content_hint: str) -> list[str]:
        base = [item.strip(" ，、") for item in content_hint.replace("和", "、").split("、") if item.strip()]
        if len(base) >= 3:
            return base[:3]
        default = ["效率工具", "AI 工作流", "复盘方法"]
        return (base + default)[:3]
