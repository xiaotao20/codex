from __future__ import annotations

import json
import os
from collections import Counter

from app.models import AnalysisResult

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "clean_copy": {"type": "string"},
        "hooks": {"type": "array", "items": {"type": "string"}},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "tone": {"type": "string"},
        "cta": {"type": "string"},
        "content_type": {"type": "string"},
        "risk_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary",
        "clean_copy",
        "hooks",
        "key_points",
        "keywords",
        "tone",
        "cta",
        "content_type",
        "risk_notes",
    ],
    "additionalProperties": False,
}


def analyze_video(video: dict, transcript: dict) -> AnalysisResult:
    force_mock = os.getenv("PIPELINE_FORCE_MOCK_AI", "false").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if api_key and not force_mock:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            model = os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-4.1-mini")
            prompt = _build_prompt(video, transcript)
            response = client.responses.create(
                model=model,
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "douyin_video_analysis",
                        "schema": ANALYSIS_SCHEMA,
                        "strict": True,
                    }
                },
            )
            payload = json.loads(response.output_text)
            return AnalysisResult(video_id=video["video_id"], source="openai", **payload)
        except Exception:
            pass

    return _mock_analysis(video, transcript)


def _build_prompt(video: dict, transcript: dict) -> str:
    return (
        "请基于以下抖音视频信息输出结构化 JSON，不要臆造没有出现过的事实。\n"
        f"标题：{video.get('title', '')}\n"
        f"发布时间：{video.get('publish_time', '')}\n"
        f"点赞：{video.get('like_count', 0)}\n"
        f"评论：{video.get('comment_count', 0)}\n"
        f"分享：{video.get('share_count', 0)}\n"
        f"收藏：{video.get('collect_count', 0)}\n"
        f"话题标签：{'、'.join(video.get('topic_tags', []))}\n"
        f"转写文本：{transcript.get('transcript_clean', '')}\n"
    )


def _mock_analysis(video: dict, transcript: dict) -> AnalysisResult:
    transcript_text = transcript.get("transcript_clean", "")
    keywords = _extract_keywords(video, transcript_text)
    title = video.get("title", "")
    summary = f"{video.get('creator_name', '博主')}围绕“{keywords[0]}”给出了一条可直接执行的短视频经验。"
    hooks = [
        f"{keywords[0]}为什么总是做不出来结果？",
        f"先把{keywords[1]}想清楚，内容效率会高很多。",
    ]
    key_points = [
        f"先明确主题，围绕{keywords[0]}组织标题与开头。",
        f"用{keywords[1]}和{keywords[2]}补足正文信息密度。",
        "结尾补上动作建议，方便团队复用到下一条视频。",
    ]
    clean_copy = (
        f"{title}。{transcript_text} 核心做法是先统一选题，再补充案例和执行动作，"
        "把一条视频整理成可复用的工作模版。"
    )
    return AnalysisResult(
        video_id=video["video_id"],
        summary=summary,
        clean_copy=clean_copy,
        hooks=hooks,
        key_points=key_points,
        keywords=keywords,
        tone="干货",
        cta="收藏这条内容，按同样结构复盘下一条视频。",
        content_type="知识分享",
        risk_notes=["当前为占位分析结果，接入真实模型后可获得更细的表达。"],
        source="mock",
    )


def _extract_keywords(video: dict, transcript_text: str) -> list[str]:
    tags = [tag.strip() for tag in video.get("topic_tags", []) if tag.strip()]
    if len(tags) >= 3:
        return tags[:3]

    pieces = [
        token.strip("，。！？：；、 ")
        for token in transcript_text.replace("\n", " ").split(" ")
        if token.strip()
    ]
    counter = Counter(token for token in pieces if len(token) >= 2)
    keywords = tags + [item for item, _count in counter.most_common(3)]
    defaults = ["效率工具", "AI 工作流", "复盘方法"]
    merged = keywords + defaults
    return merged[:3]
