from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.io_utils import read_json, write_json
from app.models import AnalysisResult, TranscriptResult, VideoMetadata


ASIA_SHANGHAI = timezone(timedelta(hours=8))


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: dict[str, dict[str, Any]] = read_json(path, {})

    def save(self) -> None:
        write_json(self.path, self.records)

    def upsert_video(self, video: VideoMetadata, run_date: str, fetched_at: str) -> dict[str, Any]:
        record = self.records.get(video.video_id, {})
        fetch_runs = record.get("fetch_runs", [])
        if run_date not in fetch_runs:
            fetch_runs.append(run_date)

        transcript_status = record.get("transcript_status", "pending")
        analysis_status = record.get("analysis_status", "pending")
        if video.video_id not in self.records:
            transcript_status = "pending"
            analysis_status = "pending"

        updated = {
            "video_id": video.video_id,
            "video": video.to_dict(),
            "first_seen_at": record.get("first_seen_at", fetched_at),
            "last_seen_at": fetched_at,
            "fetch_runs": fetch_runs,
            "transcript_status": transcript_status,
            "analysis_status": analysis_status,
            "transcript": record.get("transcript"),
            "analysis": record.get("analysis"),
            "last_error": record.get("last_error"),
        }
        self.records[video.video_id] = updated
        return updated

    def list_records(self) -> list[dict[str, Any]]:
        return sorted(self.records.values(), key=lambda item: item["video"]["publish_time"], reverse=True)

    def list_records_for_run(self, run_date: str) -> list[dict[str, Any]]:
        records = [item for item in self.list_records() if run_date in item.get("fetch_runs", [])]
        return records or self.list_records()

    def list_pending_transcripts(self, run_date: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self.list_records_for_run(run_date)
            if item.get("transcript_status") != "completed"
        ]

    def list_pending_analysis(self, run_date: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self.list_records_for_run(run_date)
            if item.get("transcript_status") == "completed" and item.get("analysis_status") != "completed"
        ]

    def mark_transcript_success(
        self,
        video_id: str,
        transcript: TranscriptResult,
        transcript_path: Path,
        processed_at: str,
    ) -> None:
        record = self.records[video_id]
        record["transcript_status"] = "completed"
        record["transcript"] = {
            **transcript.to_dict(),
            "path": transcript_path.as_posix(),
            "processed_at": processed_at,
        }
        record["last_error"] = None

    def mark_transcript_failure(self, video_id: str, error_message: str) -> None:
        record = self.records[video_id]
        record["transcript_status"] = "failed"
        record["last_error"] = error_message

    def mark_analysis_success(
        self,
        video_id: str,
        analysis: AnalysisResult,
        analysis_path: Path,
        processed_at: str,
    ) -> None:
        record = self.records[video_id]
        record["analysis_status"] = "completed"
        record["analysis"] = {
            **analysis.to_dict(),
            "path": analysis_path.as_posix(),
            "processed_at": processed_at,
        }
        record["last_error"] = None

    def mark_analysis_failure(self, video_id: str, error_message: str) -> None:
        record = self.records[video_id]
        record["analysis_status"] = "failed"
        record["last_error"] = error_message

    @staticmethod
    def now_iso() -> str:
        return datetime.now(ASIA_SHANGHAI).isoformat(timespec="seconds")
