from app.fetch.douyin_yt_dlp_adapter import (
    _pick_candidate_url,
    _extract_detail_text_meta,
    _parse_count_text,
    _should_use_browser_fetch,
    build_video_metadata_from_aweme,
    build_video_metadata,
    normalize_publish_time,
    parse_cookie_string,
)
from app.models import CreatorConfig


def test_build_video_metadata_maps_core_fields() -> None:
    creator = CreatorConfig(
        creator_id="creator_1",
        name="测试博主",
        homepage="https://www.douyin.com/user/test",
    )
    detail = {
        "id": "7480000000000000000",
        "title": "测试标题",
        "timestamp": 1782435600,
        "webpage_url": "https://www.douyin.com/video/7480000000000000000",
        "thumbnail": "https://example.com/cover.jpg",
        "like_count": 123,
        "comment_count": 45,
        "repost_count": 6,
        "description": "一段描述",
        "tags": ["标签1", "标签2"],
        "uploader": "测试博主",
        "duration": 18,
        "url": "https://example.com/media.mp4",
        "extractor": "TikTok",
        "extractor_key": "TikTok",
    }

    video = build_video_metadata(creator, detail)

    assert video.video_id == "7480000000000000000"
    assert video.creator_name == "测试博主"
    assert video.like_count == 123
    assert video.comment_count == 45
    assert video.share_count == 6
    assert video.media_url == "https://example.com/media.mp4"
    assert video.topic_tags == ["标签1", "标签2"]
    assert video.source == "douyin_yt_dlp"


def test_normalize_publish_time_uses_upload_date_when_timestamp_missing() -> None:
    publish_time = normalize_publish_time({"upload_date": "20260626"})
    assert publish_time.startswith("2026-06-26T00:00:00+08:00")


def test_pick_candidate_url_falls_back_to_video_page() -> None:
    assert _pick_candidate_url({"id": "7499999999999999999"}) == "https://www.douyin.com/video/7499999999999999999"


def test_build_video_metadata_from_aweme_maps_core_fields() -> None:
    creator = CreatorConfig(
        creator_id="creator_1",
        name="测试博主",
        homepage="https://www.douyin.com/user/MS4wLjABAAAA123",
    )
    aweme = {
        "aweme_id": "7652732962794346609",
        "desc": "AI做PPT零基础教学！#PPT #Codex",
        "create_time": 1782435600,
        "author": {
            "nickname": "知雪",
            "sec_uid": "MS4wLjABAAAA123",
            "uid": "7569807853663470641",
        },
        "statistics": {
            "digg_count": 1974,
            "comment_count": 123,
            "share_count": 45,
            "collect_count": 67,
        },
        "video": {
            "duration": 18500,
            "cover": {"url_list": ["https://example.com/cover.jpg"]},
            "play_addr": {
                "url_list": [
                    "https://example.com/video.mp4",
                    "https://www.douyin.com/aweme/v1/play/?video_id=1",
                ]
            },
        },
        "text_extra": [
            {"hashtag_name": "PPT"},
            {"hashtag_name": "Codex"},
        ],
    }

    video = build_video_metadata_from_aweme(creator, aweme)

    assert video.video_id == "7652732962794346609"
    assert video.creator_name == "知雪"
    assert video.like_count == 1974
    assert video.comment_count == 123
    assert video.share_count == 45
    assert video.collect_count == 67
    assert video.cover_url == "https://example.com/cover.jpg"
    assert video.media_url == "https://example.com/video.mp4"
    assert video.topic_tags == ["PPT", "Codex"]
    assert video.duration_seconds == 18.5
    assert video.source == "douyin_playwright"


def test_parse_cookie_string_builds_browser_cookie_payload() -> None:
    cookies = parse_cookie_string("sessionid=abc123; sid_guard=xyz")
    assert cookies[0]["name"] == "sessionid"
    assert cookies[0]["value"] == "abc123"
    assert cookies[0]["domain"] == ".douyin.com"
    assert cookies[1]["name"] == "sid_guard"


def test_should_use_browser_fetch_supports_homepage_and_short_link() -> None:
    assert _should_use_browser_fetch("https://www.douyin.com/user/MS4wLjABAAAA123") is True
    assert _should_use_browser_fetch("https://www.iesdouyin.com/share/user/MS4wLjABAAAA123") is True
    assert _should_use_browser_fetch("https://v.douyin.com/xlCnV5lTBeo/") is True
    assert _should_use_browser_fetch("https://www.douyin.com/video/7480000000000000000") is False


def test_parse_count_text_supports_wan_suffix() -> None:
    assert _parse_count_text("9.4万") == 94000
    assert _parse_count_text("2464") == 2464


def test_extract_detail_text_meta_parses_statistics_and_publish_time() -> None:
    body_text = "\n".join(
        [
            "Codex零基础使用教程",
            "9.4万",
            "2464",
            "8.5万",
            "1.7万",
            "举报",
            "发布时间：2026-06-11 01:34",
        ]
    )

    meta = _extract_detail_text_meta(body_text)

    assert meta["statistics"] == {
        "digg_count": 94000,
        "comment_count": 2464,
        "share_count": 85000,
        "collect_count": 17000,
    }
    assert meta["create_time"] > 0
