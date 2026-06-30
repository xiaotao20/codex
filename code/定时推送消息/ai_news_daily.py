from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RSS_FEEDS = [
    {
        "name": "OpenAI News",
        "focus": "模型发布",
        "url": "https://openai.com/news/rss.xml",
    },
    {
        "name": "Google AI",
        "focus": "模型发布",
        "url": "https://blog.google/innovation-and-ai/technology/ai/rss/",
    },
    {
        "name": "Hugging Face Blog",
        "focus": "开源爆款",
        "url": "https://huggingface.co/blog/feed.xml",
    },
    {
        "name": "AWS Machine Learning Blog",
        "focus": "商业机会",
        "url": "https://aws.amazon.com/blogs/machine-learning/feed/",
    },
    {
        "name": "TechCrunch AI",
        "focus": "创业信号",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "VentureBeat AI",
        "focus": "商业机会",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "name": "The Verge AI",
        "focus": "模型发布",
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    },
    {
        "name": "arXiv cs.AI",
        "focus": "开源爆款",
        "url": "https://rss.arxiv.org/rss/cs.AI",
    },
]
PLACEHOLDER_MARKERS = ("你的", "请填写", "示例", "example", "xxxx", "TODO")
SECTION_FIELDS = [
    ("model_releases", "模型发布"),
    ("business_opportunities", "商业机会"),
    ("open_source_hits", "开源爆款"),
    ("startup_signals", "创业信号"),
]


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


def get_rss_feeds() -> list[dict[str, str]]:
    raw = env_text("RSS_FEEDS")
    if not raw:
        return DEFAULT_RSS_FEEDS

    feeds: list[dict[str, str]] = []
    for part in raw.replace(",", "\n").splitlines():
        entry = part.strip()
        if not entry:
            continue

        parsed = [item.strip() for item in entry.split("|")]
        if len(parsed) == 3:
            feeds.append({"name": parsed[0], "focus": parsed[1], "url": parsed[2]})
            continue

        url = parsed[-1]
        feeds.append({"name": infer_feed_name(url), "focus": "综合", "url": url})
    return feeds or DEFAULT_RSS_FEEDS


def infer_feed_name(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or url
    return host.replace("www.", "")


def get_max_digest_items() -> int:
    return max(1, env_int("MAX_DIGEST_ITEMS", 8))


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
    for feed_config in get_rss_feeds():
        url = feed_config["url"]
        try:
            feed = feedparser.parse(url)
            source_name = feed_config["name"] or feed.feed.get("title", url)
            focus = feed_config["focus"] or "综合"
            for entry in feed.entries[:max_items]:
                items.append(
                    {
                        "source": source_name,
                        "focus": focus,
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:500],
                    }
                )
        except Exception as exc:
            print(f"抓取 {url} 失败: {exc}")
    return items


def summarize_with_claude(news_items: list[dict[str, str]]) -> dict[str, object]:
    if not news_items:
        return {
            "overview": "今天没有抓到新内容，可能是 RSS 源暂时无更新。",
            "key_observations": [],
            "sections": empty_sections(),
            "overall_impact": ["今天暂无可判断的重点影响。"],
            "action_suggestions": ["稍后重试，或检查 RSS 源是否正常更新。"],
        }

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
    return parse_digest_json("\n".join(text_blocks))


def build_prompt(news_items: list[dict[str, str]]) -> str:
    news_text = "\n\n".join(
        (
            f"来源: {item['source']}\n"
            f"来源侧重: {item['focus']}\n"
            f"标题: {item['title']}\n"
            f"摘要: {item['summary']}\n"
            f"链接: {item['link']}"
        )
        for item in news_items
    )
    reader_profile = env_text(
        "READER_PROFILE",
        "我是一位关注 AI 工具、产品机会、工作效率和商业化方向的中文读者。",
    )
    return f"""以下是今天从多个英文 AI 新闻源抓取到的原始条目。

请先筛选出真正有价值、属于“AI 行业”的新闻，过滤掉广告和明显无关内容；再面向下面这个读者画像，输出一份中文简报：
{reader_profile}

输出要求：
1. 只保留真正值得关注的新闻，总条数不超过 {get_max_digest_items()} 条；
2. 按以下四个栏目整理，某些栏目可以为空，但必须输出这四个栏目：
   - model_releases：模型发布
   - business_opportunities：商业机会
   - open_source_hits：开源爆款
   - startup_signals：创业信号
3. 每条新闻都要给出：
   - title：中文标题
   - summary：2-3 句中文总结
   - impact：这条新闻“对我有什么影响”，用 1-2 句写清楚
   - link：原文链接
4. 另外再给出：
   - overview：今天的总体判断，2-3 句
   - key_observations：3 条以内的关键信号
   - overall_impact：3 条以内“对我的整体影响”
   - action_suggestions：3 条以内可执行建议

只允许输出 JSON 对象，不要输出 Markdown，不要输出代码块，不要解释。

JSON 结构如下：
{{
  "overview": "string",
  "key_observations": ["string"],
  "sections": {{
    "model_releases": [
      {{
        "title": "string",
        "summary": "string",
        "impact": "string",
        "link": "string"
      }}
    ],
    "business_opportunities": [],
    "open_source_hits": [],
    "startup_signals": []
  }},
  "overall_impact": ["string"],
  "action_suggestions": ["string"]
}}

原始条目：
{news_text}
"""


def parse_digest_json(raw_text: str) -> dict[str, object]:
    normalized = raw_text.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        if normalized.startswith("json"):
            normalized = normalized[4:].strip()

    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError:
        start = normalized.find("{")
        end = normalized.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError(f"模型没有返回可解析的 JSON：{raw_text}")
        payload = json.loads(normalized[start : end + 1])

    if not isinstance(payload, dict):
        raise RuntimeError(f"模型返回的内容不是 JSON 对象：{raw_text}")

    return {
        "overview": str(payload.get("overview") or "").strip(),
        "key_observations": clean_string_list(payload.get("key_observations"), limit=3),
        "sections": normalize_sections(payload),
        "overall_impact": clean_string_list(payload.get("overall_impact"), limit=3),
        "action_suggestions": clean_string_list(payload.get("action_suggestions"), limit=3),
    }


def empty_sections() -> dict[str, list[dict[str, str]]]:
    return {field: [] for field, _title in SECTION_FIELDS}


def normalize_sections(payload: dict[str, object]) -> dict[str, list[dict[str, str]]]:
    sections_payload = payload.get("sections")
    fallback_items = payload.get("items")
    normalized = empty_sections()
    total_limit = get_max_digest_items()
    current_total = 0

    if isinstance(sections_payload, dict):
        for field, _title in SECTION_FIELDS:
            section_items = sections_payload.get(field)
            if not isinstance(section_items, list):
                continue
            for item in section_items:
                if current_total >= total_limit:
                    return normalized
                normalized[field].append(normalize_digest_item(item))
                current_total += 1
        return normalized

    if isinstance(fallback_items, list):
        for item in fallback_items:
            if current_total >= total_limit:
                break
            normalized["model_releases"].append(normalize_digest_item(item))
            current_total += 1
        return normalized

    raise RuntimeError(f"模型返回缺少 sections 结构：{payload}")


def clean_string_list(value: object, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value:
        text = str(item).strip()
        if text:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def normalize_digest_item(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        return {"title": "", "summary": "", "impact": "", "link": ""}
    return {
        "title": str(item.get("title") or "").strip(),
        "summary": str(item.get("summary") or "").strip(),
        "impact": str(item.get("impact") or "").strip(),
        "link": str(item.get("link") or "").strip(),
    }


def build_plaintext_digest(digest: dict[str, object]) -> str:
    lines: list[str] = []
    overview = str(digest.get("overview") or "").strip()
    if overview:
        lines.extend(["今日判断", overview, ""])

    observations = digest.get("key_observations") or []
    if observations:
        lines.append("关键信号")
        lines.extend(f"- {item}" for item in observations)
        lines.append("")

    sections = digest.get("sections") or empty_sections()
    for field, title in SECTION_FIELDS:
        items = sections.get(field) or []
        if not items:
            continue
        lines.append(title)
        for index, item in enumerate(items, start=1):
            lines.append(f"{index}. {item['title']}")
            lines.append(f"   摘要：{item['summary']}")
            lines.append(f"   对我的影响：{item['impact']}")
            lines.append(f"   链接：{item['link']}")
        lines.append("")

    overall_impact = digest.get("overall_impact") or []
    if overall_impact:
        lines.append("对我的整体影响")
        lines.extend(f"- {item}" for item in overall_impact)
        lines.append("")

    action_suggestions = digest.get("action_suggestions") or []
    if action_suggestions:
        lines.append("建议动作")
        lines.extend(f"- {item}" for item in action_suggestions)

    return "\n".join(lines).strip()


def build_html_digest(digest: dict[str, object]) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    overview = html.escape(str(digest.get("overview") or "").strip())
    observations = "".join(
        f"<li>{html.escape(item)}</li>" for item in (digest.get("key_observations") or [])
    )
    section_blocks = "".join(
        render_news_section(title, digest.get("sections", {}).get(field) or [])
        for field, title in SECTION_FIELDS
    )
    overall_impact = "".join(
        f"<li>{html.escape(item)}</li>" for item in (digest.get("overall_impact") or [])
    )
    action_suggestions = "".join(
        f"<li>{html.escape(item)}</li>" for item in (digest.get("action_suggestions") or [])
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>AI 行业新闻日报 {today}</title>
  </head>
  <body style="margin:0;padding:24px;background:#f3f6fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;color:#1f2937;">
    <div style="max-width:880px;margin:0 auto;">
      <div style="background:#111827;color:#ffffff;padding:28px 32px;border-radius:14px;">
        <div style="font-size:13px;opacity:0.75;">AI 行业新闻日报</div>
        <h1 style="margin:8px 0 0;font-size:28px;line-height:1.3;">{today}</h1>
        <p style="margin:16px 0 0;font-size:15px;line-height:1.8;color:#d1d5db;">{overview}</p>
      </div>

      {render_section("关键信号", f"<ul style='margin:0;padding-left:20px;line-height:1.9;'>{observations}</ul>" if observations else "<p style='margin:0;color:#6b7280;'>今天没有额外提炼到明显信号。</p>")}

      {render_section("风口栏目", section_blocks or "<p style='margin:0;color:#6b7280;'>今天没有可展示的重点新闻。</p>")}

      {render_section("对我的整体影响", f"<ul style='margin:0;padding-left:20px;line-height:1.9;'>{overall_impact}</ul>" if overall_impact else "<p style='margin:0;color:#6b7280;'>今天暂无明确整体影响判断。</p>")}

      {render_section("建议动作", f"<ul style='margin:0;padding-left:20px;line-height:1.9;'>{action_suggestions}</ul>" if action_suggestions else "<p style='margin:0;color:#6b7280;'>今天暂无建议动作。</p>")}
    </div>
  </body>
</html>"""


def render_section(title: str, body: str) -> str:
    return (
        "<section style='margin-top:18px;background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;padding:24px 28px;'>"
        f"<h2 style='margin:0 0 16px;font-size:20px;color:#111827;'>{html.escape(title)}</h2>"
        f"{body}"
        "</section>"
    )


def render_news_section(title: str, items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    cards = "".join(render_news_card(index, item) for index, item in enumerate(items, start=1))
    return (
        "<div style='margin-bottom:20px;'>"
        f"<h3 style='margin:0 0 14px;font-size:18px;color:#111827;'>{html.escape(title)}</h3>"
        f"{cards}"
        "</div>"
    )


def render_news_card(index: int, item: dict[str, str]) -> str:
    title = html.escape(item.get("title", ""))
    summary = html.escape(item.get("summary", ""))
    impact = html.escape(item.get("impact", ""))
    link = html.escape(item.get("link", ""))
    link_html = (
        f"<a href=\"{link}\" style=\"color:#2563eb;text-decoration:none;word-break:break-all;\">查看原文</a>"
        if link
        else "<span style='color:#9ca3af;'>无原文链接</span>"
    )
    return f"""
      <article style="padding:18px 20px;border:1px solid #e5e7eb;border-radius:12px;background:#f8fafc;margin-bottom:14px;">
        <div style="display:inline-block;font-size:12px;font-weight:700;color:#2563eb;background:#dbeafe;border-radius:999px;padding:4px 10px;">重点 {index}</div>
        <h3 style="margin:12px 0 10px;font-size:18px;line-height:1.5;color:#111827;">{title}</h3>
        <p style="margin:0 0 12px;font-size:14px;line-height:1.85;color:#374151;"><strong>摘要：</strong>{summary}</p>
        <div style="margin:0 0 14px;padding:12px 14px;background:#eef2ff;border-radius:10px;font-size:14px;line-height:1.8;color:#312e81;">
          <strong>对我的影响：</strong>{impact}
        </div>
        <div style="font-size:14px;line-height:1.7;">{link_html}</div>
      </article>"""


def send_email(plain_text: str, html_content: str) -> None:
    today = datetime.date.today().strftime("%Y-%m-%d")
    subject = f"AI 行业新闻日报 {today}"
    sender_email = env_text("SENDER_EMAIL")
    receiver_email = env_text("RECEIVER_EMAIL")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP_SSL(env_text("SMTP_HOST", "smtp.qq.com"), env_int("SMTP_PORT", 465)) as server:
        server.login(sender_email, env_text("SENDER_AUTH_CODE"))
        server.sendmail(sender_email, [receiver_email], msg.as_string())

    print(f"邮件已发送至 {receiver_email}")


def run(skip_email: bool) -> None:
    print("开始抓取新闻...")
    news_items = fetch_news()
    print(f"共抓取到 {len(news_items)} 条原始新闻，开始总结...")

    digest = summarize_with_claude(news_items)
    plain_text = build_plaintext_digest(digest)
    html_content = build_html_digest(digest)
    print("总结完成。")

    if skip_email:
        print("当前为仅预览模式，摘要如下：\n")
        print(plain_text)
        return

    print("开始发送邮件...")
    send_email(plain_text, html_content)
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
