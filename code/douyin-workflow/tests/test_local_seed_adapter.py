from datetime import date
from pathlib import Path

from app.fetch.local_seed_adapter import LocalSeedAdapter
from app.models import CreatorConfig


def test_local_seed_adapter_reads_seed_file(tmp_path: Path) -> None:
    seed_path = tmp_path / "videos.json"
    seed_path.write_text(
        """
[
  {
    "creator_id": "creator_1",
    "video_id": "video_1",
    "title": "标题",
    "transcript_hint": "转写提示"
  }
]
""".strip(),
        encoding="utf-8",
    )

    adapter = LocalSeedAdapter(seed_path)
    creators = [CreatorConfig(creator_id="creator_1", name="博主", homepage="https://example.com")]
    videos = adapter.fetch_videos(creators, date(2026, 6, 26))

    assert len(videos) == 1
    assert videos[0].video_id == "video_1"
    assert videos[0].source == "local_seed"
    assert videos[0].transcript_hint == "转写提示"
