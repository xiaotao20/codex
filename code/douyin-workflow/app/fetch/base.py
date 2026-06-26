from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.models import CreatorConfig, VideoMetadata


class FetchAdapter(ABC):
    @abstractmethod
    def fetch_videos(self, creators: list[CreatorConfig], run_date: date) -> list[VideoMetadata]:
        raise NotImplementedError
