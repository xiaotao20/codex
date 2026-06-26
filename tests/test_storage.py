from pathlib import Path

from app.models import VideoMetadata
from app.storage import StateStore


def test_state_store_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "processed.json"
    store = StateStore(state_path)
    video = VideoMetadata(
        creator_id="creator_1",
        creator_name="测试博主",
        video_id="video_1",
        title="测试标题",
        publish_time="2026-06-26T09:00:00+08:00",
        video_url="https://example.com/video_1",
        cover_url="https://example.com/video_1.jpg",
    )

    store.upsert_video(video, "2026-06-26", "2026-06-26T09:00:00+08:00")
    store.save()

    reloaded = StateStore(state_path)
    assert "video_1" in reloaded.records
    assert reloaded.records["video_1"]["video"]["title"] == "测试标题"
