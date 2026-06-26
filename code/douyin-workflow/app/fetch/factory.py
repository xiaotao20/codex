from __future__ import annotations

from app.fetch.base import FetchAdapter
from app.fetch.douyin_yt_dlp_adapter import DouyinYtDlpAdapter
from app.fetch.local_seed_adapter import LocalSeedAdapter
from app.fetch.stub_adapter import StubFetchAdapter
from app.models import AppSettings


def build_fetch_adapter(settings: AppSettings, base_dir) -> FetchAdapter:
    if settings.fetch_adapter == "stub":
        return StubFetchAdapter(max_videos_per_creator=settings.max_videos_per_creator)
    if settings.fetch_adapter == "local_seed":
        return LocalSeedAdapter(seed_path=(base_dir / settings.local_seed_file).resolve())
    if settings.fetch_adapter in {"douyin", "douyin_yt_dlp"}:
        return DouyinYtDlpAdapter(
            max_videos_per_creator=settings.max_videos_per_creator,
            cookie_file=settings.douyin_cookie_file,
            base_dir=base_dir,
        )
    raise ValueError(f"不支持的采集适配器: {settings.fetch_adapter}")
