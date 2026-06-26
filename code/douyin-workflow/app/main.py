from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.ai.analyze import analyze_video
from app.ai.transcribe import transcribe_video
from app.config import load_config
from app.environment import load_project_env
from app.fetch.factory import build_fetch_adapter
from app.io_utils import ensure_directory, write_json
from app.logging_setup import setup_logging
from app.media.downloader import prepare_media
from app.report.daily_report import build_report, write_report
from app.storage import StateStore


ASIA_SHANGHAI = timezone(timedelta(hours=8))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抖音博主视频采集与总结工作流")
    parser.add_argument(
        "--mode",
        choices=["all", "fetch", "media", "transcribe", "analyze", "report"],
        default="all",
    )
    parser.add_argument("--config", default="config/creators.yaml")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--run-date", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    load_project_env(base_dir)
    config_path = (base_dir / args.config).resolve()
    run_date = date.fromisoformat(args.run_date) if args.run_date else datetime.now(ASIA_SHANGHAI).date()
    run_date_str = run_date.isoformat()
    outputs_dir = base_dir / "outputs"
    log_path = outputs_dir / "logs" / f"pipeline_{run_date_str}.log"
    logger = setup_logging(log_path)
    logger.info("开始执行工作流，模式=%s，日期=%s", args.mode, run_date_str)

    for relative in ["raw", "media", "transcripts", "analysis", "reports", "logs", "state"]:
        ensure_directory(outputs_dir / relative)

    pipeline_config = load_config(config_path)
    state_store = StateStore(outputs_dir / "state" / "processed.json")

    if args.mode in {"all", "fetch"}:
        execute_fetch(base_dir, pipeline_config, state_store, run_date, logger)
        state_store.save()

    if args.mode in {"all", "media"}:
        execute_media(base_dir, pipeline_config, state_store, run_date_str, logger)
        state_store.save()

    if args.mode in {"all", "transcribe"}:
        execute_transcribe(base_dir, state_store, run_date_str, logger)
        state_store.save()

    if args.mode in {"all", "analyze"}:
        execute_analyze(base_dir, state_store, run_date_str, logger)
        state_store.save()

    if args.mode in {"all", "report"}:
        execute_report(
            base_dir,
            state_store,
            run_date_str,
            pipeline_config.settings.report_top_n,
            logger,
        )

    logger.info("工作流执行完成，模式=%s，日期=%s", args.mode, run_date_str)
    return 0


def execute_fetch(base_dir: Path, pipeline_config, state_store: StateStore, run_date: date, logger) -> None:
    adapter = build_fetch_adapter(pipeline_config.settings, base_dir)
    fetched_at = StateStore.now_iso()
    videos = adapter.fetch_videos(pipeline_config.creators, run_date)
    raw_payload = [video.to_dict() for video in videos]
    raw_dir = base_dir / "outputs" / "raw" / run_date.isoformat()
    write_json(raw_dir / "videos.json", raw_payload)
    for video in videos:
        state_store.upsert_video(video, run_date.isoformat(), fetched_at)
    logger.info("采集完成，博主数=%s，视频数=%s", len(pipeline_config.creators), len(videos))


def execute_media(base_dir: Path, pipeline_config, state_store: StateStore, run_date: str, logger) -> None:
    pending = state_store.list_pending_media(run_date)
    logger.info("待准备媒体视频数=%s", len(pending))
    for record in pending:
        video = record["video"]
        try:
            media = prepare_media(
                video=video,
                base_dir=base_dir,
                run_date=run_date,
                ffmpeg_path=pipeline_config.settings.ffmpeg_path,
            )
            if media.get("audio_path") or media.get("video_path"):
                state_store.mark_media_success(video["video_id"], media, StateStore.now_iso())
                logger.info("媒体准备完成，video_id=%s，source=%s", video["video_id"], media["source"])
            else:
                state_store.mark_media_skipped(video["video_id"], "未提供媒体文件，使用文本直出模式", StateStore.now_iso())
                logger.info("媒体准备跳过，video_id=%s", video["video_id"])
        except Exception as exc:
            state_store.mark_media_failure(video["video_id"], str(exc))
            logger.exception("媒体准备失败，video_id=%s", video["video_id"])


def execute_transcribe(base_dir: Path, state_store: StateStore, run_date: str, logger) -> None:
    pending = state_store.list_pending_transcripts(run_date)
    logger.info("待转写视频数=%s", len(pending))
    for record in pending:
        video = record["video"]
        try:
            transcript = transcribe_video(video, base_dir / "outputs" / "transcripts" / run_date)
            transcript_path = base_dir / "outputs" / "transcripts" / run_date / f"{video['video_id']}.json"
            write_json(transcript_path, transcript.to_dict())
            state_store.mark_transcript_success(
                video_id=video["video_id"],
                transcript=transcript,
                transcript_path=transcript_path,
                processed_at=StateStore.now_iso(),
            )
            logger.info("转写完成，video_id=%s，source=%s", video["video_id"], transcript.source)
        except Exception as exc:
            state_store.mark_transcript_failure(video["video_id"], str(exc))
            logger.exception("转写失败，video_id=%s", video["video_id"])


def execute_analyze(base_dir: Path, state_store: StateStore, run_date: str, logger) -> None:
    pending = state_store.list_pending_analysis(run_date)
    logger.info("待分析视频数=%s", len(pending))
    for record in pending:
        video = record["video"]
        transcript = record.get("transcript") or {}
        try:
            analysis = analyze_video(video, transcript)
            analysis_path = base_dir / "outputs" / "analysis" / run_date / f"{video['video_id']}.json"
            write_json(analysis_path, analysis.to_dict())
            state_store.mark_analysis_success(
                video_id=video["video_id"],
                analysis=analysis,
                analysis_path=analysis_path,
                processed_at=StateStore.now_iso(),
            )
            logger.info("分析完成，video_id=%s，source=%s", video["video_id"], analysis.source)
        except Exception as exc:
            state_store.mark_analysis_failure(video["video_id"], str(exc))
            logger.exception("分析失败，video_id=%s", video["video_id"])


def execute_report(base_dir: Path, state_store: StateStore, run_date: str, top_n: int, logger) -> None:
    records = state_store.list_records_for_run(run_date)
    report = build_report(records, run_date, top_n)
    reports_dir = base_dir / "outputs" / "reports"
    markdown_path = reports_dir / f"report_{run_date}.md"
    json_path = reports_dir / f"report_{run_date}.json"
    write_report(report, markdown_path, json_path)
    summary_path = reports_dir / "latest_summary.json"
    write_json(summary_path, _build_run_summary(records, report))
    logger.info("日报生成完成，文件=%s", markdown_path.as_posix())


def _build_run_summary(records: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(ASIA_SHANGHAI).isoformat(timespec="seconds"),
        "video_records": len(records),
        "completed_analysis": report["video_count"],
        "top_keyword": report["top_keywords"][0]["keyword"] if report["top_keywords"] else "",
    }


if __name__ == "__main__":
    raise SystemExit(main())
