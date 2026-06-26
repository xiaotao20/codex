from app.fetch.douyin_yt_dlp_adapter import (
    _pick_candidate_url,
    build_video_metadata,
    normalize_publish_time,
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
