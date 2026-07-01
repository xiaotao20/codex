# AI 日报微信推送接入方案

## 1. 文档目的

本文档用于说明如何在现有日报脚本基础上，增加“微信推送”能力。

当前项目中已有的日报脚本位于：

- `E:\CODEX\code\定时推送消息\ai_news_daily.py`

该脚本已经具备以下能力：

- 抓取 AI 风口相关 RSS 新闻
- 调用模型整理为四个栏目：`模型发布 / 商业机会 / 开源爆款 / 创业信号`
- 输出纯文本摘要
- 输出 HTML 邮件正文
- 通过 SMTP 发送 HTML 邮件

本方案的目标是在此基础上，增加一个新的发送通道：

- 邮件继续保留
- 新增微信侧推送
- 两边共用同一份日报内容

## 2. 当前代码结构

当前日报脚本的主流程如下：

1. `fetch_news()`：抓取 RSS 新闻原始条目
2. `summarize_with_claude()`：调用模型输出结构化 JSON
3. `build_plaintext_digest()`：生成纯文本摘要
4. `build_html_digest()`：生成 HTML 邮件内容
5. `send_email()`：通过 SMTP 发邮件
6. `run()`：总调度入口

如果要接入微信，最合适的改法不是改动模型层，而是在发送层新增一个统一入口，例如：

```python
def send_notifications(plain_text: str, html_content: str, digest: dict[str, object]) -> None:
    send_email(plain_text, html_content)
    send_wechat(plain_text, html_content, digest)
```

这样做的好处是：

- 模型输出只生成一次
- 邮件和微信共用同一份数据
- 以后新增更多通知渠道也容易扩展

## 3. 推荐结论

如果目标是“发到个人微信”，推荐顺序如下：

1. `pushplus`
2. `WxPusher`
3. `企业微信群机器人`
4. `企业微信应用消息`

原因很直接：

- `pushplus` 最接近“直接发到自己个人微信”，实现最轻
- `WxPusher` 也适合个人使用，但微信通道约束更多
- `企业微信群机器人` 更适合发到一个群，不是点对点发给个人微信
- `企业微信应用消息` 更适合团队或企业内部账号体系

因此，本项目建议优先落地：

- 第一阶段：接入 `pushplus`
- 第二阶段：如有需要，再补 `企业微信群机器人`

## 4. 统一设计方案

建议在现有脚本上增加一层“通知发送器”。

### 4.1 统一环境变量

建议在 `.env` 中新增以下配置：

```env
# 通知总开关
ENABLE_WECHAT=true
WECHAT_PROVIDER=pushplus

# pushplus
PUSHPLUS_TOKEN=请填写 pushplus token
PUSHPLUS_TEMPLATE=html
PUSHPLUS_CHANNEL=wechat
PUSHPLUS_TO=

# WxPusher
WXPUSHER_APP_TOKEN=请填写 appToken
WXPUSHER_UID=请填写接收者 UID

# 企业微信群机器人
WECOM_BOT_WEBHOOK=

# 企业微信应用消息
WECOM_CORPID=
WECOM_CORPSECRET=
WECOM_AGENTID=
WECOM_TOUSER=
```

### 4.2 统一发送入口

建议新增以下函数：

```python
def send_wechat(plain_text: str, html_content: str, digest: dict[str, object]) -> None:
    if env_text("ENABLE_WECHAT", "false").lower() != "true":
        return

    provider = env_text("WECHAT_PROVIDER", "pushplus").lower()
    if provider == "pushplus":
        send_wechat_via_pushplus(plain_text, html_content, digest)
        return
    if provider == "wxpusher":
        send_wechat_via_wxpusher(plain_text, html_content, digest)
        return
    if provider == "wecom_bot":
        send_wechat_via_wecom_bot(plain_text, digest)
        return
    if provider == "wecom_app":
        send_wechat_via_wecom_app(plain_text, digest)
        return

    raise RuntimeError(f"不支持的微信推送渠道: {provider}")
```

### 4.3 微信内容渲染建议

建议不要把邮件 HTML 原样丢给所有微信通道，而是按通道能力分别渲染：

- `pushplus`：优先复用现有 `html_content`
- `WxPusher`：优先发简化版 HTML 或 markdown
- `企业微信群机器人`：发 markdown
- `企业微信应用消息`：发 markdown 或 template card

建议新增两个渲染函数：

```python
def build_wechat_markdown_digest(digest: dict[str, object]) -> str:
    ...

def build_wechat_html_digest(digest: dict[str, object]) -> str:
    ...
```

## 5. 方案一：pushplus

## 5.1 适用场景

适合个人使用，目标是把日报直接发到自己的微信里。

这是最推荐先接入的方案，因为：

- 不需要企业微信环境
- 接入成本低
- 能直接复用现有 HTML 日报内容

## 5.2 配置步骤

### 第一步：注册并获取 token

在 pushplus 控制台获取个人 `token`。

### 第二步：在 `.env` 中填写

```env
ENABLE_WECHAT=true
WECHAT_PROVIDER=pushplus
PUSHPLUS_TOKEN=你的 pushplus token
PUSHPLUS_TEMPLATE=html
PUSHPLUS_CHANNEL=wechat
PUSHPLUS_TO=
```

说明：

- `PUSHPLUS_TEMPLATE=html` 表示直接发送 HTML 内容
- `PUSHPLUS_CHANNEL=wechat` 表示走微信通道
- `PUSHPLUS_TO` 为空时，通常表示发给自己

## 5.3 接口调用方式

推荐新增函数：

```python
def send_wechat_via_pushplus(plain_text: str, html_content: str, digest: dict[str, object]) -> None:
    payload = {
        "token": env_text("PUSHPLUS_TOKEN"),
        "title": f"AI 行业新闻日报 {datetime.date.today():%Y-%m-%d}",
        "content": html_content,
        "template": env_text("PUSHPLUS_TEMPLATE", "html"),
        "channel": env_text("PUSHPLUS_CHANNEL", "wechat"),
    }

    to_value = env_text("PUSHPLUS_TO")
    if to_value:
        payload["to"] = to_value

    response = requests.post(
        "http://www.pushplus.plus/send",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
```

## 5.4 优点

- 最接近“发到个人微信”
- 对现有脚本改动最小
- 可以直接复用 HTML 日报

## 5.5 风险与注意点

- 依赖第三方服务
- 微信通道的最终呈现效果取决于服务端支持
- 如果后续服务策略变化，需要同步调整

## 6. 方案二：WxPusher

## 6.1 适用场景

适合个人通知、多设备同步提醒。

如果你不介意同时使用它自己的客户端能力，可以作为个人提醒备选。

## 6.2 配置步骤

### 第一步：注册应用

获取：

- `appToken`
- 接收者 `UID`

### 第二步：在 `.env` 中填写

```env
ENABLE_WECHAT=true
WECHAT_PROVIDER=wxpusher
WXPUSHER_APP_TOKEN=你的 appToken
WXPUSHER_UID=你的 UID
```

## 6.3 接口调用方式

推荐新增函数：

```python
def send_wechat_via_wxpusher(plain_text: str, html_content: str, digest: dict[str, object]) -> None:
    payload = {
        "appToken": env_text("WXPUSHER_APP_TOKEN"),
        "content": build_wechat_markdown_digest(digest),
        "summary": f"AI 行业新闻日报 {datetime.date.today():%Y-%m-%d}",
        "contentType": 3,
        "uids": [env_text("WXPUSHER_UID")],
    }

    response = requests.post(
        "https://wxpusher.zjiecode.com/api/send/message",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
```

说明：

- `contentType=3` 一般可用于 HTML
- 若微信通道对 HTML 展示不好，可改为 markdown 或纯文本

## 6.4 优点

- 适合个人长期提醒
- API 清晰
- 支持发给指定用户

## 6.5 风险与注意点

- 微信通道可能存在条数或激活限制
- 长消息展示不如邮件自然
- 更适合“提醒”和“摘要”，不如邮件适合长文阅读

## 7. 方案三：企业微信群机器人

## 7.1 适用场景

适合把日报同步发到企业微信群。

如果你后面想把日报发到一个“自己的提醒群”或者小团队群，这个方案很稳。

## 7.2 配置步骤

### 第一步：创建机器人

在企业微信群里添加机器人，获取 webhook。

### 第二步：在 `.env` 中填写

```env
ENABLE_WECHAT=true
WECHAT_PROVIDER=wecom_bot
WECOM_BOT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx
```

## 7.3 接口调用方式

推荐发 markdown 内容：

```python
def send_wechat_via_wecom_bot(plain_text: str, digest: dict[str, object]) -> None:
    markdown_text = build_wechat_markdown_digest(digest)
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_text,
        },
    }

    response = requests.post(
        env_text("WECOM_BOT_WEBHOOK"),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
```

## 7.4 内容格式建议

建议内容压缩成：

- 今日判断
- 4 个栏目各 1-2 条
- 对我的整体影响
- 阅读全文请看邮件

不要把完整长 HTML 直接塞给机器人。

## 7.5 优点

- 官方方案，稳定
- 群内共享方便
- 配置简单

## 7.6 风险与注意点

- 不是个人微信聊天框
- 长文阅读体验一般
- 更适合作为“提醒版”和“摘要版”

## 8. 方案四：企业微信应用消息

## 8.1 适用场景

适合：

- 团队内部正式推送
- 后续要区分不同接收人
- 想做更完整的企业微信通知体系

## 8.2 配置步骤

### 第一步：创建自建应用

获取以下参数：

- `corpid`
- `corpsecret`
- `agentid`
- 接收人 `userid`

### 第二步：在 `.env` 中填写

```env
ENABLE_WECHAT=true
WECHAT_PROVIDER=wecom_app
WECOM_CORPID=你的 corpid
WECOM_CORPSECRET=你的 corpsecret
WECOM_AGENTID=你的 agentid
WECOM_TOUSER=你的 userid
```

## 8.3 实现步骤

### 1. 获取 access token

```python
def get_wecom_access_token() -> str:
    response = requests.get(
        "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        params={
            "corpid": env_text("WECOM_CORPID"),
            "corpsecret": env_text("WECOM_CORPSECRET"),
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token", "")
    if not token:
        raise RuntimeError(f"获取企业微信 access_token 失败: {payload}")
    return token
```

### 2. 发送应用消息

```python
def send_wechat_via_wecom_app(plain_text: str, digest: dict[str, object]) -> None:
    access_token = get_wecom_access_token()
    payload = {
        "touser": env_text("WECOM_TOUSER"),
        "msgtype": "markdown",
        "agentid": int(env_int("WECOM_AGENTID", 0)),
        "markdown": {
            "content": build_wechat_markdown_digest(digest),
        },
        "safe": 0,
    }

    response = requests.post(
        "https://qyapi.weixin.qq.com/cgi-bin/message/send",
        params={"access_token": access_token},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
```

## 8.4 优点

- 官方能力最完整
- 可以精细控制接收对象
- 更适合后续扩团队

## 8.5 风险与注意点

- 配置最重
- 需要企业微信应用环境
- 对个人微信需求来说，不是最短路径

## 9. 推荐实施路线

建议按以下顺序推进：

### 第一阶段：接入 pushplus

目标：

- 先把“个人微信提醒”跑通
- 复用现有 HTML 内容
- 控制代码改动在单文件内完成

改造范围：

- `ai_news_daily.py`
- `.env.example`

新增函数建议：

- `send_wechat()`
- `send_wechat_via_pushplus()`
- `build_wechat_markdown_digest()`

在 `run()` 中的发送顺序建议为：

```python
send_email(plain_text, html_content)
send_wechat(plain_text, html_content, digest)
```

### 第二阶段：补企业微信群机器人

目标：

- 保留个人微信通知
- 额外发一份到团队群

适合后续扩展为：

- 个人看完整日报
- 群里看精简摘要

## 10. 推荐的代码改造清单

建议在当前脚本中做以下修改：

### 10.1 校验配置

在 `validate_config()` 中增加微信配置校验：

```python
def validate_wechat_config() -> None:
    provider = env_text("WECHAT_PROVIDER").lower()
    if not provider:
        return

    if provider == "pushplus" and not looks_configured(env_text("PUSHPLUS_TOKEN")):
        raise SystemExit("缺少 PUSHPLUS_TOKEN")
    if provider == "wxpusher" and not looks_configured(env_text("WXPUSHER_APP_TOKEN")):
        raise SystemExit("缺少 WXPUSHER_APP_TOKEN")
    if provider == "wecom_bot" and not looks_configured(env_text("WECOM_BOT_WEBHOOK")):
        raise SystemExit("缺少 WECOM_BOT_WEBHOOK")
```

### 10.2 run 函数增加微信发送

```python
if skip_email:
    print(plain_text)
    return

send_email(plain_text, html_content)
send_wechat(plain_text, html_content, digest)
```

### 10.3 增加微信专用渲染函数

邮件 HTML 和微信展示并不完全一致，建议单独做微信版内容。

建议输出结构：

- 标题
- 今日判断
- 四个栏目每栏最多 1-2 条
- 对我的整体影响
- 一句结尾说明

## 11. 测试方案

建议按以下顺序测试：

### 第一步：只跑摘要，不发邮件

```powershell
python ai_news_daily.py --skip-email
```

目的：

- 验证新闻抓取是否正常
- 验证模型输出是否正常

### 第二步：本地单独测试微信发送函数

例如先临时写一个小入口，只发一段固定文本。

目的：

- 验证 token、webhook、uid 等配置是否正确
- 验证消息格式是否可显示

### 第三步：联调完整流程

执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\CODEX\code\定时推送消息\run_ai_news_daily.ps1"
```

检查：

- 邮件是否收到
- 微信是否收到
- 日志中是否有报错

## 12. 故障排查建议

### pushplus 失败

优先检查：

- `PUSHPLUS_TOKEN` 是否正确
- `template` 是否与内容类型匹配
- 返回 JSON 中的 `code` 和 `msg`

### WxPusher 失败

优先检查：

- `appToken` 是否正确
- `UID` 是否正确
- 微信通道是否已激活

### 企业微信群机器人失败

优先检查：

- webhook 是否完整
- markdown 内容是否过长
- 群机器人是否被删除

### 企业微信应用消息失败

优先检查：

- `corpid / corpsecret / agentid` 是否正确
- `touser` 是否存在
- `access_token` 是否拿到

## 13. 最终建议

如果只做一版、并且目标明确是“发到个人微信”，建议直接按下面路线推进：

1. 在现有脚本中新增 `pushplus` 通道
2. 复用现有 `html_content`
3. 保留邮件发送不变
4. 让 `.env` 中通过 `WECHAT_PROVIDER=pushplus` 控制是否启用

这样最少改动就能把“邮件日报”升级成“邮件 + 微信双通道日报”。

如果后续还想扩展团队场景，再补企业微信群机器人即可。
