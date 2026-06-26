from __future__ import annotations

import os
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.fetch.base import FetchAdapter
from app.models import CreatorConfig, VideoMetadata

ASIA_SHANGHAI = timezone(timedelta(hours=8))


class DouyinYtDlpAdapter(FetchAdapter):
    def __init__(self, max_videos_per_creator: int, cookie_file: str = "", base_dir: Path | None = None) -> None:
        self.max_videos_per_creator = max_videos_per_creator
        self.cookie_file = cookie_file
        self.base_dir = base_dir or Path.cwd()

    def fetch_videos(self, creators: list[CreatorConfig], run_date) -> list[VideoMetadata]:
        try:
            from yt_dlp import YoutubeDL
        except ImportError as exc:
            raise RuntimeError("未安装 yt-dlp，请先执行 pip install -r requirements.txt") from exc

        videos: list[VideoMetadata] = []
        for creator in creators:
            entries = self._extract_creator_entries(YoutubeDL, creator)
            for entry in entries[: self.max_videos_per_creator]:
                detail = self._extract_video_detail(YoutubeDL, entry)
                if not detail:
                    continue
                videos.append(build_video_metadata(creator, detail))
        return videos

    def _extract_creator_entries(self, ydl_class, creator: CreatorConfig) -> list[dict[str, Any]]:
        options = self._build_ydl_options(flat=True)
        options["playlistend"] = self.max_videos_per_creator
        with ydl_class(options) as ydl:
            info = ydl.extract_info(creator.homepage, download=False)
        if not info:
            error_message = build_homepage_fetch_error(creator.homepage)
            if error_message:
                raise RuntimeError(error_message)
            return []
        if info.get("_type") == "playlist":
            return [entry for entry in info.get("entries", []) if entry]
        return [info]

    def _extract_video_detail(self, ydl_class, entry: dict[str, Any]) -> dict[str, Any] | None:
        candidate_url = _pick_candidate_url(entry)
        if not candidate_url:
            return entry

        with ydl_class(self._build_ydl_options(flat=False)) as ydl:
            return ydl.extract_info(candidate_url, download=False)

    def _build_ydl_options(self, flat: bool) -> dict[str, Any]:
        options: dict[str, Any] = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "extract_flat": "in_playlist" if flat else False,
            "http_headers": self._build_headers(),
        }
        cookie_file = self._resolve_cookie_file()
        if cookie_file:
            options["cookiefile"] = str(cookie_file)
        return options

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        user_agent = os.getenv("DOUYIN_USER_AGENT", "").strip()
        cookie = os.getenv("DOUYIN_COOKIE", "").strip()
        if user_agent:
            headers["User-Agent"] = user_agent
        if cookie:
            headers["Cookie"] = cookie
        return headers

    def _resolve_cookie_file(self) -> Path | None:
        env_cookie_file = os.getenv("DOUYIN_COOKIE_FILE", "").strip()
        candidate = env_cookie_file or self.cookie_file
        if not candidate:
            return None
        path = Path(candidate)
        if not path.is_absolute():
            path = (self.base_dir / path).resolve()
        return path if path.exists() else None


def build_video_metadata(creator: CreatorConfig, detail: dict[str, Any]) -> VideoMetadata:
    video_id = str(detail.get("id") or detail.get("aweme_id") or "")
    publish_time = normalize_publish_time(detail)
    tags = [tag for tag in detail.get("tags", []) if isinstance(tag, str)]
    thumbnails = detail.get("thumbnails") or []
    thumbnail_url = detail.get("thumbnail") or (thumbnails[0].get("url") if thumbnails else "")
    media_url = detail.get("url") or _pick_media_url(detail)
    title = detail.get("title") or f"{creator.name} 视频 {video_id}"

    return VideoMetadata(
        creator_id=creator.creator_id,
        creator_name=detail.get("uploader") or detail.get("channel") or creator.name,
        video_id=video_id,
        title=title,
        publish_time=publish_time,
        video_url=detail.get("webpage_url") or detail.get("original_url") or creator.homepage,
        cover_url=thumbnail_url,
        like_count=int(detail.get("like_count") or 0),
        comment_count=int(detail.get("comment_count") or 0),
        share_count=int(detail.get("repost_count") or detail.get("share_count") or 0),
        collect_count=int(detail.get("collect_count") or 0),
        description=detail.get("description") or "",
        text_hint=detail.get("description") or title,
        topic_tags=tags,
        source="douyin_yt_dlp",
        media_url=media_url,
        transcript_hint="",
        duration_seconds=float(detail.get("duration") or 0.0),
        raw_payload={
            "extractor": detail.get("extractor"),
            "extractor_key": detail.get("extractor_key"),
            "channel_id": detail.get("channel_id"),
            "availability": detail.get("availability"),
        },
    )


def normalize_publish_time(detail: dict[str, Any]) -> str:
    timestamp = detail.get("timestamp") or detail.get("release_timestamp")
    if timestamp:
        return datetime.fromtimestamp(int(timestamp), tz=ASIA_SHANGHAI).isoformat(timespec="seconds")

    upload_date = str(detail.get("upload_date") or "").strip()
    if len(upload_date) == 8 and upload_date.isdigit():
        parsed = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=ASIA_SHANGHAI)
        return parsed.isoformat(timespec="seconds")

    return datetime.now(ASIA_SHANGHAI).isoformat(timespec="seconds")


def _pick_media_url(detail: dict[str, Any]) -> str:
    formats = detail.get("formats") or []
    for item in formats:
        if item.get("url"):
            return item["url"]
    return ""


def _pick_candidate_url(entry: dict[str, Any]) -> str:
    for key in ("webpage_url", "original_url", "url"):
        value = str(entry.get(key) or "").strip()
        if value.startswith("http://") or value.startswith("https://"):
            return value

    video_id = str(entry.get("id") or "").strip()
    if video_id:
        return f"https://www.douyin.com/video/{video_id}"
    return ""


def build_homepage_fetch_error(homepage: str) -> str:
    parsed = urlparse(homepage)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    if host.endswith("douyin.com") and path.startswith("/user/"):
        return "当前 douyin_yt_dlp 适配器只支持单视频链接，不支持抖音博主页。请改用单条视频链接，或继续开发主页抓取适配器。"

    if host.endswith("iesdouyin.com") and path.startswith("/share/user/"):
        return "当前 douyin_yt_dlp 适配器不支持抖音博主页分享链接。请改用单条视频链接，或继续开发主页抓取适配器。"

    if host == "v.douyin.com":
        return "当前 douyin_yt_dlp 适配器暂不支持抖音主页短链。请改用单条视频链接，或继续开发主页抓取适配器。"

    return ""
