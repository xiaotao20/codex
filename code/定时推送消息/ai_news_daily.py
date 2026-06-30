from __future__ import annotations

import argparse
import datetime
import json
import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path

import feedparser
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
]
PLACEHOLDER_MARKERS = ("你的", "请填写", "示例", "example", "xxxx", "TODO")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(line)
        if not parsed:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)


def parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip().lstrip("\ufeff")
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def env_text(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_int(name: str, default: int) -> int:
    raw = env_text(name)
    if not raw:
        return default
    return int(raw)


def looks_configured(value: str) -> bool:
    if not value:
        return False
    lowered = value.strip().lower()
    return not any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS)


def get_rss_feeds() -> list[str]:
    raw = env_text("RSS_FEEDS")
    if not raw:
        return DEFAULT_RSS_FEEDS

    feeds = []
    for part in raw.replace(",", "\n").splitlines():
        url = part.strip()
        if url:
            feeds.append(url)
    return feeds or DEFAULT_RSS_FEEDS


def get_messages_url() -> str:
    exact_url = env_text("ANTHROPIC_MESSAGES_URL")
    if exact_url:
        return exact_url

    base_url = env_text("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    return f"{base_url}/v1/messages"


def validate_config(skip_email: bool) -> None:
    required = {
        "ANTHROPIC_API_KEY": env_text("ANTHROPIC_API_KEY"),
    }
    if not skip_email:
        required.update(
            {
                "SMTP_HOST": env_text("SMTP_HOST", "smtp.qq.com"),
                "SENDER_EMAIL": env_text("SENDER_EMAIL"),
                "SENDER_AUTH_CODE": env_text("SENDER_AUTH_CODE"),
                "RECEIVER_EMAIL": env_text("RECEIVER_EMAIL"),
            }
        )

    missing = [name for name, value in required.items() if not looks_configured(value)]
    if missing:
        joined = "、".join(missing)
        raise SystemExit(f"配置不完整，请先补齐同目录 .env 中的: {joined}")


def fetch_news() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    max_items = env_int("MAX_ITEMS_PER_FEED", 5)
    for url in get_rss_feeds():
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", url)
            for entry in feed.entries[:max_items]:
                items.append(
                    {
                        "source": source_name,
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:500],
                    }
                )
        except Exception as exc:
            print(f"抓取 {url} 失败: {exc}")
    return items


def summarize_with_claude(news_items: list[dict[str, str]]) -> str:
    if not news_items:
        return "今天没有抓到新内容，可能是 RSS 源暂时无更新。"

    prompt = build_prompt(news_items)
    headers = {
        "x-api-key": env_text("ANTHROPIC_API_KEY"),
        "anthropic-version": env_text("ANTHROPIC_VERSION", "2023-06-01"),
        "content-type": "application/json",
    }
    body = {
        "system": "你是 AI 行业资讯编辑。只输出最终中文日报，不要展示思考过程、筛选分析或推理步骤。",
        "model": env_text("ANTHROPIC_MODEL", "claude-opus-4-8"),
        "max_tokens": env_int("ANTHROPIC_MAX_TOKENS", 4096),
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(
        get_messages_url(),
        headers=headers,
        data=json.dumps(body),
        timeout=env_int("REQUEST_TIMEOUT_SECONDS", 60),
    )
    response.raise_for_status()
    payload = response.json()
    text_blocks = [block["text"] for block in payload.get("content", []) if block.get("type") == "text"]
    thinking_blocks = [block["thinking"] for block in payload.get("content", []) if block.get("type") == "thinking"]
    if not text_blocks:
        if thinking_blocks and payload.get("stop_reason") == "max_tokens":
            raise RuntimeError("API 只返回了 thinking 内容且被 max_tokens 截断，请增大 ANTHROPIC_MAX_TOKENS 或更换模型。")
        raise RuntimeError(f"总结生成失败，请检查 API 返回: {json.dumps(payload, ensure_ascii=False)}")
    return "\n".join(text_blocks)


def build_prompt(news_items: list[dict[str, str]]) -> str:
    news_text = "\n\n".join(
        f"来源: {item['source']}\n标题: {item['title']}\n摘要: {item['summary']}\n链接: {item['link']}"
        for item in news_items
    )
    return f"""以下是今天从多个英文 AI 新闻源抓取到的原始条目。请你：
1. 筛选出真正有价值、属于“AI 行业”的新闻，过滤掉广告和无关内容；
2. 把标题和要点翻译成中文，每条新闻用 2-3 句话总结；
3. 按重要性排序，最多保留 8 条；
4. 输出格式为纯文本，每条新闻包含：中文标题、一句话总结、原文链接。

原始条目：
{news_text}
"""


def send_email(content: str) -> None:
    today = datetime.date.today().strftime("%Y-%m-%d")
    subject = f"AI 行业新闻日报 {today}"
    sender_email = env_text("SENDER_EMAIL")
    receiver_email = env_text("RECEIVER_EMAIL")

    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL(env_text("SMTP_HOST", "smtp.qq.com"), env_int("SMTP_PORT", 465)) as server:
        server.login(sender_email, env_text("SENDER_AUTH_CODE"))
        server.sendmail(sender_email, [receiver_email], msg.as_string())

    print(f"邮件已发送至 {receiver_email}")


def run(skip_email: bool) -> None:
    print("开始抓取新闻...")
    news_items = fetch_news()
    print(f"共抓取到 {len(news_items)} 条原始新闻，开始总结...")

    digest = summarize_with_claude(news_items)
    print("总结完成。")

    if skip_email:
        print("当前为仅预览模式，摘要如下：\n")
        print(digest)
        return

    print("开始发送邮件...")
    send_email(digest)
    print("完成。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI 行业新闻日报")
    parser.add_argument("--skip-email", action="store_true", help="只生成摘要，不发送邮件")
    return parser.parse_args()


def main() -> None:
    load_env_file(SCRIPT_DIR / ".env")
    args = parse_args()
    validate_config(skip_email=args.skip_email)
    run(skip_email=args.skip_email)


if __name__ == "__main__":
    main()
