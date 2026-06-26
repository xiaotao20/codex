from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from app.io_utils import write_json


def build_report(records: list[dict[str, Any]], run_date: str, top_n: int) -> dict[str, Any]:
    completed = [item for item in records if item.get("analysis_status") == "completed"]
    keyword_counter = Counter()
    creator_counter = Counter()

    for item in completed:
        creator_counter[item["video"]["creator_name"]] += 1
        keyword_counter.update(item.get("analysis", {}).get("keywords", []))

    top_like = sorted(
        completed,
        key=lambda item: item["video"].get("like_count", 0),
        reverse=True,
    )[:top_n]
    top_comment = sorted(
        completed,
        key=lambda item: item["video"].get("comment_count", 0),
        reverse=True,
    )[:top_n]

    return {
        "run_date": run_date,
        "video_count": len(completed),
        "creator_breakdown": dict(creator_counter),
        "top_like_videos": [_item_digest(item) for item in top_like],
        "top_comment_videos": [_item_digest(item) for item in top_comment],
        "top_keywords": [{"keyword": key, "count": count} for key, count in keyword_counter.most_common(top_n)],
        "videos": [_item_digest(item, include_detail=True) for item in completed],
    }


def write_report(report: dict[str, Any], markdown_path: Path, json_path: Path) -> None:
    write_json(json_path, report)
    markdown = _to_markdown(report)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8", newline="\n")


def _item_digest(item: dict[str, Any], include_detail: bool = False) -> dict[str, Any]:
    payload = {
        "video_id": item["video_id"],
        "creator_name": item["video"]["creator_name"],
        "title": item["video"]["title"],
        "publish_time": item["video"]["publish_time"],
        "like_count": item["video"]["like_count"],
        "comment_count": item["video"]["comment_count"],
        "share_count": item["video"]["share_count"],
        "summary": item.get("analysis", {}).get("summary", ""),
    }
    if include_detail:
        payload["keywords"] = item.get("analysis", {}).get("keywords", [])
        payload["key_points"] = item.get("analysis", {}).get("key_points", [])
        payload["clean_copy"] = item.get("analysis", {}).get("clean_copy", "")
    return payload


def _to_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 抖音视频日报 - {report['run_date']}",
        "",
        f"- 新增完成分析视频数：{report['video_count']}",
        "",
        "## 博主分布",
        "",
    ]
    if report["creator_breakdown"]:
        for creator_name, count in report["creator_breakdown"].items():
            lines.append(f"- {creator_name}：{count} 条")
    else:
        lines.append("- 暂无数据")

    lines.extend(["", "## 点赞 Top", ""])
    if report["top_like_videos"]:
        for index, item in enumerate(report["top_like_videos"], start=1):
            lines.append(
                f"{index}. {item['creator_name']} | {item['title']} | 点赞 {item['like_count']} | {item['summary']}"
            )
    else:
        lines.append("1. 暂无数据")

    lines.extend(["", "## 评论 Top", ""])
    if report["top_comment_videos"]:
        for index, item in enumerate(report["top_comment_videos"], start=1):
            lines.append(
                f"{index}. {item['creator_name']} | {item['title']} | 评论 {item['comment_count']} | {item['summary']}"
            )
    else:
        lines.append("1. 暂无数据")

    lines.extend(["", "## 高频关键词", ""])
    if report["top_keywords"]:
        for item in report["top_keywords"]:
            lines.append(f"- {item['keyword']}：{item['count']}")
    else:
        lines.append("- 暂无数据")

    lines.extend(["", "## 视频摘要", ""])
    if report["videos"]:
        for item in report["videos"]:
            lines.append(f"### {item['creator_name']} - {item['title']}")
            lines.append("")
            lines.append(f"- 点赞：{item['like_count']}")
            lines.append(f"- 评论：{item['comment_count']}")
            lines.append(f"- 总结：{item['summary']}")
            lines.append(f"- 关键词：{'、'.join(item.get('keywords', []))}")
            lines.append("")
    else:
        lines.append("- 暂无已分析视频")

    lines.append("")
    return "\n".join(lines)
