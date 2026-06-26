from __future__ import annotations

from app.fetch.base import FetchAdapter
from app.fetch.stub_adapter import StubFetchAdapter
from app.models import AppSettings


def build_fetch_adapter(settings: AppSettings) -> FetchAdapter:
    if settings.fetch_adapter == "stub":
        return StubFetchAdapter(max_videos_per_creator=settings.max_videos_per_creator)
    if settings.fetch_adapter == "douyin":
        raise NotImplementedError("真实抖音适配器将在下一阶段接入，请先使用 stub 验证工作流。")
    raise ValueError(f"不支持的采集适配器: {settings.fetch_adapter}")
