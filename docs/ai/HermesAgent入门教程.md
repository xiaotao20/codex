# Hermes Agent 入门教程（中文）

> 说明：这里的 `Hermes` 指的是 **Nous Research 的 Hermes Agent**，不是 React Native 里的 Hermes JavaScript 引擎。

## 1. Hermes 是什么

如果用一句大白话来解释：

**Hermes 是一个能聊天、能调用工具、能记住事情、还能越用越顺手的 AI 代理。**

你可以把它理解成一个“长期在线的 AI 助手”，但它不只是回答问题，还可以：

- 在终端里执行命令
- 读写文件
- 连到不同的大模型提供商
- 通过技能（skills）复用经验
- 通过记忆（memory）跨会话记住你的偏好和项目背景
- 通过 Telegram、Discord、Slack 等入口和你持续交互

和普通聊天机器人相比，Hermes 更像一个“会干活的 AI 工作台”。

## 2. Hermes 和普通 AI 聊天有什么区别

普通 AI 聊天更像“一问一答”。

Hermes 的思路是：

1. 先理解你的目标
2. 必要时调用工具
3. 把经验沉淀成技能
4. 把长期有用的信息写进记忆
5. 下次继续接着干

所以它更适合做连续任务，比如：

- 写代码、改代码、查日志
- 总结资料、做研究
- 管理服务器或脚本
- 做带上下文的个人助理
- 在多个平台上作为同一个 AI 身份持续工作

## 3. 先理解几个核心概念

### Session（会话）

每次聊天都会保存下来。你下次可以继续接着之前的内容聊。

### Memory（记忆）

Hermes 会把一些长期有价值的信息留下来，比如：

- 你喜欢什么风格的回答
- 你的项目结构
- 你常用的命令
- 之前踩过的坑

### Skill（技能）

技能可以理解成“可复用的做事说明书”。

比如你经常让 Hermes 做下面这种事：

- 帮我整理 Git 提交流程
- 帮我按固定格式写 issue
- 帮我检查发布前清单

那这些经验以后可以沉淀成技能，后面直接复用。

### Profile（配置档）

一个 profile 就是一套独立的 Hermes 环境。

你可以把它理解成：

- 工作账号一套
- 个人项目一套
- 实验环境一套

它们的配置、记忆、会话、技能都可以彼此隔离。

### Gateway（网关）

这表示 Hermes 不一定只在本地终端里用。

你还可以把它接到消息平台上，比如 Telegram、Discord、Slack 等，让它通过聊天软件为你工作。

## 4. 安装前要准备什么

最少需要两样东西：

1. 一套 Hermes 运行环境
2. 一个可用的大模型提供商

常见提供商包括：

- OpenAI
- Anthropic
- OpenRouter
- DeepSeek
- 本地模型服务（如 Ollama 或兼容 OpenAI 接口的服务）

如果你是第一次用，最简单的路线通常是：

- 先装好 Hermes
- 再运行 `hermes setup` 或 `hermes model`
- 选一个你已经有 API key 的提供商

官方文档当前说明：

- Linux / macOS / WSL2 是主推荐路径
- 如果你是 Windows 用户，优先按 WSL2 路线理解和使用
- 官方仓库里也提供了 `install.ps1`，但遇到兼容问题时，直接切到 WSL2 往往更省时间

## 5. 安装 Hermes

### Linux / macOS / WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

安装完成后，重新打开终端，再检查命令是否可用：

```bash
hermes --help
```

## 6. 第一次启动：最短上手流程

### 第一步：运行初始化

```bash
hermes setup
```

如果你已经装好了，但还没配置模型，也可以直接运行：

```bash
hermes model
```

这一步通常会让你选择：

- 用哪个提供商
- 用哪个模型
- API key 放在哪里

### 第二步：开启交互式聊天

```bash
hermes
```

如果你想用新版终端界面：

```bash
hermes --tui
```

### 第三步：先试一个最简单的问题

```bash
hermes chat -q "用一句话解释什么是 Docker"
```

如果这一条能正常返回，说明你的基本链路已经通了。

## 7. 最常用的几个命令

```bash
hermes
```

启动默认交互模式。

```bash
hermes --tui
```

启动更现代的终端界面。官方文档把它作为推荐的交互方式之一。

```bash
hermes chat -q "Hello"
```

单次提问，适合脚本化、快速验证、命令行临时调用。

```bash
hermes model
```

配置模型和提供商。

```bash
hermes dashboard
```

启动本地 Web 控制台。默认会在本机启动一个页面，方便查看状态、管理会话和配置。

```bash
hermes gateway setup
```

配置消息平台入口，让 Hermes 能通过 Telegram、Discord、Slack 等渠道工作。

## 8. 用例 1：把 Hermes 当成终端里的 AI 助手

这是最容易上手的用法。

### 例子：快速问答

```bash
hermes chat -q "帮我总结一下 Kubernetes 和 Docker 的区别，控制在 200 字内"
```

适合场景：

- 临时问概念
- 让它写摘要
- 让它改写一段文案

### 例子：指定提供商或模型

```bash
hermes chat --provider openrouter -q "给我一个 Bash 备份脚本示例"
```

或者：

```bash
hermes chat --model "anthropic/claude-sonnet-4" -q "解释这段日志里最可能的报错原因"
```

如果你不确定模型名，优先先用 `hermes model` 配好，再回来聊天。

## 9. 用例 2：把 Hermes 用在代码项目里

这是 Hermes 很实用的一种方式。

进入你的项目目录后，直接启动：

```bash
hermes
```

然后你可以这样说：

```text
请先阅读这个仓库，告诉我：
1. 入口文件在哪
2. 主要模块怎么分
3. 本地怎么启动
4. 最值得先看的 5 个文件
```

再进一步，你可以让它直接做任务：

```text
目标：给这个项目补一篇部署文档
约束：不要改代码，只改 docs/ 和 README
完成标准：新增文档，并在 README 里加入口链接
```

Hermes 会自动发现并加载一些项目上下文文件，例如：

- `.hermes.md`
- `AGENTS.md`
- `CLAUDE.md`
- `SOUL.md`
- `.cursorrules`

这意味着你可以像训练团队新人一样，提前把仓库规则写进这些文件里，Hermes 读到后会更稳定。

### 一个更实用的代码例子

```text
请先别改代码。
先阅读 README 和 src 目录，给我一个最小可执行方案：
1. 你理解的问题是什么
2. 你准备改哪些文件
3. 风险点是什么
4. 你会怎么验证
```

这种写法比“帮我改一下”更容易得到稳定结果。

## 10. 用例 3：把 Hermes 当成长期个人助手

Hermes 的一个特点是“跨会话记忆”。

比如你长期用它管理同一类事情：

- 写周报
- 记录研究方向
- 跟踪项目待办
- 维护固定工作流

那么它会越来越了解你常用的格式和偏好。

### 例子：固定写作助手

你可以这样说：

```text
以后我说“写周报”，都按这个结构输出：
1. 本周完成
2. 风险和问题
3. 下周计划
语气尽量简洁，不要写空话。
```

之后你再说：

```text
根据我今天的工作记录，帮我写周报
```

它就更容易按你的习惯来。

## 11. 用例 4：用 Dashboard 管理 Hermes

如果你不想总在终端里操作，可以用 Web 控制台：

```bash
hermes dashboard
```

官方文档说明，默认会在本机启动一个本地页面，默认地址是：

```text
http://127.0.0.1:9119
```

适合做的事：

- 看 Hermes 当前状态
- 管理会话
- 调整配置
- 在浏览器里使用聊天界面

如果你更喜欢图形界面，这个入口会比纯终端更友好。

## 12. 用例 5：多套环境隔离

如果你同时处理工作和个人项目，建议尽早用 profile 分开。

这样做的好处是：

- API key 分开
- 记忆分开
- 会话分开
- 技能分开

适合场景：

- 公司项目与个人项目隔离
- 正式环境与实验环境隔离
- 多个客户项目隔离

简单理解就是：**别把所有事情都塞进同一个 Hermes 脑子里。**

## 13. Hermes 好用的地方，到底在哪里

用通俗的话说，Hermes 的优势主要有 5 个：

### 1. 不绑死在单一模型上

你可以切换不同提供商，不需要把整套使用方式推倒重来。

### 2. 不只是聊天

它能接工具、技能、终端、消息平台，而不是只停留在问答层面。

### 3. 会留下长期上下文

它不是每次都“重新认识你”。

### 4. 适合长期工作流

重复任务做多了，Hermes 更容易变成你的固定搭档。

### 5. 支持安全边界

官方文档说明 Hermes 对危险命令有审批机制，默认会在高风险操作前请求确认。做自动化时这一点很重要。

## 14. 新手最容易踩的坑

### 坑 1：一上来就让它做很大、很模糊的任务

错误示例：

```text
帮我把这个系统重构一下
```

更好的写法：

```text
目标：给登录模块补一个最小修改
约束：不要改数据库结构
完成标准：登录失败时返回明确错误，并补最小测试
```

### 坑 2：没有先配模型

如果 provider 或 model 没配好，Hermes 本身装好了也没法正常工作。

先跑：

```bash
hermes model
```

### 坑 3：工作和个人任务混在一起

这会让记忆和配置越来越乱。长期使用时尽量拆 profile。

### 坑 4：在 Windows 上遇到环境问题却硬扛

如果你在 Windows 上反复遇到终端、路径、编码或依赖问题，优先改走 WSL2，通常比继续硬调 PowerShell 更省事。

## 15. 一个建议的学习顺序

如果你是第一次接触 Hermes，建议按这个顺序来：

1. 先装好 Hermes
2. 运行 `hermes setup`
3. 用 `hermes chat -q` 试一次单问单答
4. 用 `hermes` 或 `hermes --tui` 试交互聊天
5. 用 `hermes dashboard` 看本地控制台
6. 把它放进一个真实项目目录里试一次
7. 再去研究 skills、memory、gateway、profiles

这样上手最稳，不容易一开始就被功能面吓住。

## 16. 一份最小可用教程：从零到能用

下面给你一个可以直接照着走的最小流程。

### 步骤 1：安装

Linux / macOS / WSL2：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Windows PowerShell：

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

### 步骤 2：配置模型

```bash
hermes setup
```

或者：

```bash
hermes model
```

### 步骤 3：验证基础聊天

```bash
hermes chat -q "用 3 句话介绍一下 Hermes Agent"
```

### 步骤 4：进入交互模式

```bash
hermes --tui
```

### 步骤 5：试一个真实任务

```text
请帮我做一个学习计划：
目标：两周内学会 Hermes 的基本用法
要求：每天投入 30 分钟
输出：按天列计划
```

### 步骤 6：进入项目目录再试一次

```bash
cd your-project
hermes
```

输入：

```text
请先读这个项目，然后告诉我最小上手路径。
```

做到这里，你就已经真正开始在用 Hermes 了。

## 17. 参考资料

以下是我写这篇教程时优先参考的官方资料：

- Hermes Agent Docs: https://hermes-agent.nousresearch.com/docs/
- Quickstart: https://hermes-agent.nousresearch.com/docs/getting-started/quickstart/
- Installation: https://hermes-agent.nousresearch.com/docs/getting-started/installation/
- CLI Commands Reference: https://hermes-agent.nousresearch.com/docs/reference/cli-commands/
- Slash Commands Reference: https://hermes-agent.nousresearch.com/docs/reference/slash-commands/
- Profiles: https://hermes-agent.nousresearch.com/docs/user-guide/profiles/
- Features Overview: https://hermes-agent.nousresearch.com/docs/user-guide/features/overview/
- Security: https://hermes-agent.nousresearch.com/docs/user-guide/security/

---

如果你只记住一句话，那就是：

**Hermes 不是“再一个聊天窗口”，而是一套可以长期陪你工作的 AI 代理系统。**
