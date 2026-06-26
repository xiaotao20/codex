from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.fetch.base import FetchAdapter
from app.models import CreatorConfig, VideoMetadata

ASIA_SHANGHAI = timezone(timedelta(hours=8))


class DouyinYtDlpAdapter(FetchAdapter):
    def __init__(self, max_videos_per_creator: int, cookie_file: str = "", base_dir: Path | None = None) -> None:
        self.max_videos_per_creator = max_videos_per_creator
        self.cookie_file = cookie_file
        self.base_dir = base_dir or Path.cwd()

    def fetch_videos(self, creators: list[CreatorConfig], run_date) -> list[VideoMetadata]:
        videos: list[VideoMetadata] = []
        ydl_class = None
        for creator in creators:
            if _should_use_browser_fetch(creator.homepage):
                videos.extend(self._fetch_videos_via_browser(creator))
                continue

            if ydl_class is None:
                try:
                    from yt_dlp import YoutubeDL
                except ImportError as exc:
                    raise RuntimeError("未安装 yt-dlp，请先执行 pip install -r requirements.txt") from exc
                ydl_class = YoutubeDL

            entries = self._extract_creator_entries(ydl_class, creator)
            for entry in entries[: self.max_videos_per_creator]:
                detail = self._extract_video_detail(ydl_class, entry)
                if not detail:
                    continue
                videos.append(build_video_metadata(creator, detail))
        return videos

    def _fetch_videos_via_browser(self, creator: CreatorConfig) -> list[VideoMetadata]:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("未安装 playwright，请先执行 pip install -r requirements.txt") from exc

        with sync_playwright() as playwright:
            browser = self._launch_browser(playwright)
            context = browser.new_context(
                user_agent=os.getenv(
                    "DOUYIN_USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                ),
                locale="zh-CN",
                viewport={"width": 1280, "height": 720},
            )
            cookies = self._load_browser_cookies()
            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()
            page.set_default_timeout(60_000)

            profile_responses: list[Any] = []
            post_responses: list[Any] = []
            seen_post_urls: set[str] = set()

            def on_response(response) -> None:
                if response.status != 200:
                    return
                if "aweme/v1/web/user/profile/other/" in response.url:
                    profile_responses.append(response)
                    return
                if "aweme/v1/web/aweme/post/" in response.url and response.url not in seen_post_urls:
                    seen_post_urls.add(response.url)
                    post_responses.append(response)

            page.on("response", on_response)
            try:
                page.goto(creator.homepage, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(4_000)

                profile_payload = _read_latest_json_payload(profile_responses, "user") or {}
                aweme_items = self._collect_aweme_items(page, post_responses)
                if not aweme_items:
                    aweme_items = self._fetch_aweme_items_from_video_pages(page)

                videos = [
                    build_video_metadata_from_aweme(creator, aweme, profile_payload)
                    for aweme in aweme_items[: self.max_videos_per_creator]
                ]
                if not videos:
                    raise RuntimeError("未从抖音主页提取到视频数据，请检查主页地址、网络环境或登录态。")
                return videos
            except PlaywrightError as exc:
                raise RuntimeError(f"浏览器抓取抖音主页失败: {exc}") from exc
            finally:
                context.close()
                browser.close()

    def _extract_creator_entries(self, ydl_class, creator: CreatorConfig) -> list[dict[str, Any]]:
        options = self._build_ydl_options(flat=True)
        options["playlistend"] = self.max_videos_per_creator
        with ydl_class(options) as ydl:
            info = ydl.extract_info(creator.homepage, download=False)
        if not info:
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

    def _launch_browser(self, playwright):
        candidates: list[dict[str, Any]] = []
        browser_channel = os.getenv("DOUYIN_BROWSER_CHANNEL", "").strip()
        if browser_channel:
            candidates.append({"channel": browser_channel})
        elif os.name == "nt":
            candidates.extend([{"channel": "msedge"}, {"channel": "chrome"}])
        candidates.append({})

        last_error: Exception | None = None
        for options in _dedupe_launch_options(candidates):
            try:
                return playwright.chromium.launch(headless=True, **options)
            except Exception as exc:  # noqa: PERF203
                last_error = exc

        raise RuntimeError(f"启动浏览器失败，请先安装 Playwright 浏览器或配置 DOUYIN_BROWSER_CHANNEL。{last_error}")

    def _load_browser_cookies(self) -> list[dict[str, Any]]:
        raw_cookie = os.getenv("DOUYIN_COOKIE", "").strip()
        if raw_cookie:
            return parse_cookie_string(raw_cookie)

        cookie_file = self._resolve_cookie_file()
        if cookie_file:
            return parse_netscape_cookie_file(cookie_file)

        return []

    def _collect_aweme_items(self, page, post_responses: list[Any]) -> list[dict[str, Any]]:
        aweme_items: list[dict[str, Any]] = []
        seen_aweme_ids: set[str] = set()
        processed = 0
        has_more = True
        scroll_round = 0

        while True:
            while processed < len(post_responses):
                payload = _safe_response_json(post_responses[processed])
                processed += 1
                has_more = bool(payload.get("has_more"))
                for item in payload.get("aweme_list", []):
                    aweme_id = str(item.get("aweme_id") or "")
                    if not aweme_id or aweme_id in seen_aweme_ids:
                        continue
                    seen_aweme_ids.add(aweme_id)
                    aweme_items.append(item)

            if len(aweme_items) >= self.max_videos_per_creator or not has_more or scroll_round >= 5:
                break

            before_count = len(post_responses)
            page.mouse.wheel(0, 20_000)
            page.wait_for_timeout(2_000)
            if len(post_responses) == before_count:
                scroll_round += 1
            else:
                scroll_round = 0

        return aweme_items

    def _fetch_aweme_items_from_video_pages(self, page) -> list[dict[str, Any]]:
        video_urls = page.eval_on_selector_all(
            "a",
            """
            anchors => Array.from(new Set(
              anchors
                .map(anchor => anchor.href)
                .filter(href => href && href.includes('/video/'))
            ))
            """,
        )
        aweme_items: list[dict[str, Any]] = []
        for video_url in video_urls[: self.max_videos_per_creator]:
            detail = self._fetch_video_detail_with_browser(page.context, video_url)
            if detail:
                aweme_items.append(detail)
        return aweme_items

    def _fetch_video_detail_with_browser(self, context, video_url: str) -> dict[str, Any] | None:
        detail_page = context.new_page()
        detail_page.set_default_timeout(60_000)
        try:
            with detail_page.expect_response(
                lambda response: "aweme/v1/web/aweme/detail/" in response.url and response.status == 200,
                timeout=60_000,
            ) as detail_info:
                detail_page.goto(video_url, wait_until="domcontentloaded", timeout=60_000)

            payload = detail_info.value.json()
            aweme_detail = payload.get("aweme_detail") or {}
            if aweme_detail:
                return aweme_detail

            detail_page.wait_for_timeout(4_000)
            video_elements = detail_page.eval_on_selector_all(
                "video",
                "nodes => nodes.map(node => node.currentSrc || node.src).filter(Boolean)",
            )
            if not video_elements:
                return None

            aweme_id = _extract_video_id_from_url(video_url)
            return {
                "aweme_id": aweme_id,
                "desc": detail_page.title().replace(" - 抖音", "").strip(),
                "video": {
                    "play_addr": {"url_list": video_elements},
                },
            }
        finally:
            detail_page.close()


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


def build_video_metadata_from_aweme(
    creator: CreatorConfig,
    aweme: dict[str, Any],
    profile_payload: dict[str, Any] | None = None,
) -> VideoMetadata:
    profile_payload = profile_payload or {}
    author = aweme.get("author") or {}
    statistics = aweme.get("statistics") or {}
    video = aweme.get("video") or {}
    aweme_id = str(aweme.get("aweme_id") or aweme.get("id") or "")
    sec_uid = (
        str(author.get("sec_uid") or "")
        or str(profile_payload.get("sec_uid") or "")
        or str(profile_payload.get("uid") or "")
    )
    creator_name = author.get("nickname") or profile_payload.get("nickname") or creator.name
    description = str(aweme.get("desc") or "").strip()
    tags = _extract_topic_tags(aweme, description)
    cover_url = _pick_aweme_cover_url(video)
    media_url = _pick_aweme_media_url(video)
    create_time = aweme.get("create_time")
    publish_time = normalize_publish_time({"timestamp": create_time}) if create_time else datetime.now(ASIA_SHANGHAI).isoformat(timespec="seconds")

    profile_url = ""
    if sec_uid:
        profile_url = f"https://www.douyin.com/user/{sec_uid}"

    duration = float(video.get("duration") or 0.0)
    if duration > 1000:
        duration = duration / 1000.0

    return VideoMetadata(
        creator_id=creator.creator_id,
        creator_name=creator_name,
        video_id=aweme_id,
        title=description or f"{creator_name} 视频 {aweme_id}",
        publish_time=publish_time,
        video_url=f"https://www.douyin.com/video/{aweme_id}" if aweme_id else profile_url or creator.homepage,
        cover_url=cover_url,
        like_count=int(statistics.get("digg_count") or 0),
        comment_count=int(statistics.get("comment_count") or 0),
        share_count=int(statistics.get("share_count") or 0),
        collect_count=int(statistics.get("collect_count") or 0),
        description=description,
        text_hint=description,
        topic_tags=tags,
        source="douyin_playwright",
        media_url=media_url,
        transcript_hint="",
        duration_seconds=duration,
        raw_payload={
            "aweme_id": aweme_id,
            "author_uid": author.get("uid") or profile_payload.get("uid"),
            "sec_uid": sec_uid,
            "profile_url": profile_url,
        },
    )


def parse_cookie_string(raw_cookie: str) -> list[dict[str, Any]]:
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    cookies: list[dict[str, Any]] = []
    for morsel in cookie.values():
        cookies.append(
            {
                "name": morsel.key,
                "value": morsel.value,
                "domain": ".douyin.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
            }
        )
    return cookies


def parse_netscape_cookie_file(path: Path) -> list[dict[str, Any]]:
    cookies: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split("\t")
        if len(fields) != 7:
            continue
        domain, _include_subdomains, cookie_path, secure_flag, expires, name, value = fields
        cookie_payload = {
            "name": name,
            "value": value,
            "domain": domain or ".douyin.com",
            "path": cookie_path or "/",
            "httpOnly": False,
            "secure": secure_flag.upper() == "TRUE",
        }
        if expires.isdigit():
            cookie_payload["expires"] = int(expires)
        cookies.append(cookie_payload)
    return cookies


def _should_use_browser_fetch(homepage: str) -> bool:
    parsed = urlparse(homepage)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    if host.endswith("douyin.com") and path.startswith("/user/"):
        return True

    if host.endswith("iesdouyin.com") and path.startswith("/share/user/"):
        return True

    if host == "v.douyin.com":
        return True

    return False


def _extract_topic_tags(aweme: dict[str, Any], description: str) -> list[str]:
    tags: list[str] = []
    for item in aweme.get("text_extra") or []:
        hashtag = str(item.get("hashtag_name") or "").strip()
        if hashtag and hashtag not in tags:
            tags.append(hashtag)

    for match in re.findall(r"#([^\s#]+)", description):
        cleaned = match.strip()
        if cleaned and cleaned not in tags:
            tags.append(cleaned)

    return tags


def _pick_aweme_cover_url(video: dict[str, Any]) -> str:
    for key in ("cover", "origin_cover", "dynamic_cover", "animated_cover", "raw_cover"):
        payload = video.get(key) or {}
        urls = payload.get("url_list") or []
        if urls:
            return str(urls[0])
    return ""


def _pick_aweme_media_url(video: dict[str, Any]) -> str:
    candidates: list[str] = []
    for key in ("play_addr_h264", "play_addr", "play_addr_265"):
        payload = video.get(key) or {}
        candidates.extend(payload.get("url_list") or [])

    direct_urls = [url for url in candidates if "/aweme/v1/play/" not in url]
    if direct_urls:
        return direct_urls[0]
    if candidates:
        return candidates[0]
    return ""


def _extract_video_id_from_url(video_url: str) -> str:
    matched = re.search(r"/video/(\d+)", video_url)
    return matched.group(1) if matched else ""


def _safe_response_json(response) -> dict[str, Any]:
    try:
        payload = response.json()
        return payload if isinstance(payload, dict) else {}
    except Exception:
        try:
            payload = json.loads(response.text())
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}


def _read_latest_json_payload(responses: list[Any], key: str) -> dict[str, Any]:
    for response in reversed(responses):
        payload = _safe_response_json(response)
        nested = payload.get(key)
        if isinstance(nested, dict):
            return nested
    return {}


def _dedupe_launch_options(options_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[tuple[str, Any], ...]] = set()
    unique: list[dict[str, Any]] = []
    for options in options_list:
        marker = tuple(sorted(options.items()))
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(options)
    return unique
