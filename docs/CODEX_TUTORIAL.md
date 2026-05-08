# Codex Tutorial

一个面向中文用户的 OpenAI Codex 入门教程，重点放在本地 CLI 工作流，同时补充 IDE、App 和 Cloud 的用法。

## 1. Codex 是什么

Codex 是 OpenAI 的编程代理。它可以在你的项目目录中读取代码、修改文件、运行命令、解释代码结构、做代码审查、定位问题，并把结果整理成可继续迭代的会话。

如果你更习惯图形界面，可以用 Codex App 或 IDE 扩展；如果你想直接在仓库根目录下完成“读代码 -> 修改 -> 测试 -> 提交”这一整条链路，CLI 通常是最直接的入口。

## 2. 三种常见使用方式

### CLI

适合：

- 在终端里直接读代码、改代码、跑命令
- 配合 Git 做本地开发
- 需要完整会话记录、可恢复会话、命令可控

### IDE 扩展

适合：

- 希望在 VS Code 等编辑器中边看代码边和 Codex 交互
- 让当前打开文件、选区自动成为上下文

### Cloud

适合：

- 让 Codex 在隔离环境里并行执行任务
- 从另一台设备继续工作
- 跑较长时间的任务

注意：Cloud 线程通常依赖远程仓库；如果要让 Codex 在云端操作你的仓库，先把代码推到 GitHub 会更顺畅。

## 3. 快速开始：CLI 版

### 安装

```bash
npm i -g @openai/codex
```

升级到最新版：

```bash
npm i -g @openai/codex@latest
```

### 启动

在你的项目目录里运行：

```bash
codex
```

第一次运行时，Codex 会提示你登录。你可以使用：

- ChatGPT 账号
- OpenAI API key

在 Windows 上，官方建议可以直接在 PowerShell 中运行 Codex，并使用 Windows sandbox；如果你需要更偏 Linux 的本地环境，也可以使用 WSL2。

## 4. 一个最实用的上手流程

假设你已经进入仓库根目录，最稳妥的上手方式通常是这 5 步。

### 第一步：先让 Codex 解释项目

```text
请先阅读这个仓库，告诉我：
1. 主要目录和职责
2. 入口文件在哪里
3. 当前项目如何启动和测试
4. 你认为最值得先看的 3 个文件
```

### 第二步：再给一个明确任务

```text
目标：为这个项目补一个最小可运行的教程文档
上下文：README.md，以及你认为相关的配置文件
约束：不要大改现有结构；文档用中文；保持内容可执行
完成标准：仓库里新增教程文件，并更新 README 链接
```

这是官方文档推荐的提示结构：把任务拆成 `Goal / Context / Constraints / Done when` 四部分。这样 Codex 更容易少猜、少跑偏，也更方便你审查结果。

### 第三步：要求它验证结果

```text
完成后请检查修改内容，确认文件链接正确，并总结你改了什么。
```

如果是代码任务，就把验证条件写清楚，例如：

```text
修复后请运行最小相关测试；如果没有测试，至少给出手工验证步骤。
```

### 第四步：查看差异

在交互会话里可以用：

```text
/diff
```

这个命令会显示 Git diff，适合在提交前审查改动。

### 第五步：提交并推送

Codex 可以帮你准备修改、检查状态，最后你可以自己提交，也可以直接要求它帮你完成：

```text
请把当前修改整理成一次清晰的 git commit，然后推送到 origin/main。
```

## 5. 最常用的 CLI 命令

### 启动交互模式

```bash
codex
```

也可以直接附带一句初始任务：

```bash
codex "Explain this codebase to me"
```

### 恢复上次会话

```bash
codex resume
codex resume --last
codex resume --all
```

如果你不想每次都重新解释项目背景，这几个命令很有用。

### 直接切换目录启动

```bash
codex --cd E:\CODEX
```

### 常用安全与执行参数

```bash
codex --ask-for-approval on-request --sandbox workspace-write
```

几个常见开关：

- `--ask-for-approval`
  - `untrusted`
  - `on-request`
  - `never`
- `--sandbox`
  - `read-only`
  - `workspace-write`
  - `danger-full-access`
- `--model`
  - 覆盖默认模型
- `--search`
  - 开启实时 web search
- `--add-dir`
  - 给工作区外的额外目录授予写权限

除非你在一个已经额外加固的环境里运行，否则不建议随便使用 `--yolo` 或全局关闭审批与沙箱。

## 6. 交互会话里最值得记住的命令

在 Codex CLI 输入 `/`，会弹出 slash command 列表。

几个最常用的：

- `/model`
  - 切换模型或推理强度
- `/permissions`
  - 动态调整审批策略
- `/agent`
  - 切换或检查子代理线程
- `/status`
  - 查看当前线程状态
- `/clear`
  - 清空界面并开始新对话
- `/copy`
  - 复制最近一次完成的输出
- `/diff`
  - 查看当前代码改动
- `/exit`
  - 退出当前 CLI 会话
- `/mention`
  - 显式附加某个文件或目录作为上下文
- `/mcp`
  - 查看已配置的 MCP 工具
- `/init`
  - 在当前目录生成 `AGENTS.md` 脚手架

如果你在任务运行过程中又想到下一步，可以先把内容输入进去并排队，等当前轮次完成后再执行。

## 7. 本地线程和云端线程的区别

### Local thread

本地线程直接在你的机器上工作：

- 读取当前目录文件
- 修改代码
- 运行命令
- 结合你现有的 Git、Shell、测试环境

官方文档强调，本地线程通常运行在 sandbox 里，以降低越界修改的风险。

### Cloud thread

云端线程运行在隔离环境里：

- 适合长时间任务
- 适合并行执行
- 适合在不同设备之间继续工作

如果要让它直接处理你的仓库，通常先把代码推到 GitHub。

## 8. 如何写出更稳定的提示词

对于大多数工程任务，最有效的写法不是“帮我修一下”，而是把目标、上下文、约束、完成标准写清楚。

一个通用模板：

```text
Goal:
实现一个新的导出功能，支持 JSON 输出

Context:
- 相关文件：src/cli.ts, src/formatter.ts
- 现在只有 text 输出
- 现有测试在 tests/cli.test.ts

Constraints:
- 不要改动现有 text 输出格式
- 尽量少改 public API
- 如果能补测试就补最小回归测试

Done when:
- CLI 支持 --json
- 现有功能不回退
- 最小相关测试通过
```

几个实用原则：

- 给出可复现步骤，而不是只描述“有 bug”
- 给出怀疑文件，比让 Codex 漫游整个仓库更高效
- 复杂任务先让它出计划，再动手实现
- 要求它说明如何验证，而不是只说“已经改好了”

## 9. 用 AGENTS.md 固定团队规则

如果你每次都要重复告诉 Codex：

- 先跑什么测试
- 用什么包管理器
- 哪些目录不能动
- 文档放哪
- 提交前要做哪些检查

那就应该把这些规则写进 `AGENTS.md`。

官方文档说明，Codex 会在开始工作前读取 `AGENTS.md`。它会把全局和项目内的多个 `AGENTS.md` 按路径层级拼起来，越靠近当前工作目录的文件优先级越高。

一个简单例子：

```md
# AGENTS.md

## Repository expectations

- Run `npm run lint` before opening a pull request.
- Document public utilities in `docs/` when behavior changes.
- Ask before adding new production dependencies.
```

你也可以在子目录再放一份 `AGENTS.md` 或 `AGENTS.override.md`，让某个模块使用更具体的规则。

## 10. 用 config.toml 固定个人偏好

Codex 会从多个位置读取配置：

- 用户级：`~/.codex/config.toml`
- 项目级：`.codex/config.toml`

项目级配置只会在你信任该项目时加载。

一个实用的起点配置可以是：

```toml
model = "gpt-5.5"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
default_permissions = ":workspace"
```

配置优先级中，命令行参数最高，其次是 profile，再往下才是项目和用户配置。所以临时覆盖行为时，直接在命令行上加参数通常最省事。

## 11. 什么时候该用技能、MCP、子代理

### Skills

适合把重复工作打包成“可复用流程”。例如：

- 发布前检查
- 安全审查清单
- 数据迁移步骤

### MCP

适合把 Codex 接到外部系统，比如：

- 文档中心
- 工单系统
- 内部平台
- 第三方工具

### Subagents

适合拆并行任务，例如：

- 一个代理读后端
- 一个代理读前端
- 一个代理专门做代码审查

官方文档说明，子代理只有在你明确要求时才会被创建，而且会继承当前的审批和沙箱策略。并行很好用，但不要让两个线程同时修改同一批文件。

## 12. 几个很实用的工作流

### 场景 A：读懂陌生仓库

```text
请先阅读这个仓库。重点看 @README.md 和你认为最关键的代码入口。
输出：
1. 系统结构图（文字版）
2. 启动方式
3. 核心模块
4. 修改时最容易踩坑的两处
```

### 场景 B：修一个可复现的 bug

```text
Bug:
点击保存后提示成功，但刷新页面后数据没有持久化

Repro:
1. npm run dev
2. 打开 /settings
3. 修改开关
4. 点击 Save
5. 刷新页面，修改丢失

Context:
我怀疑问题在 @src/settings.ts 和 @src/api.ts

Constraints:
不要改 API 结构
修复尽量最小

Done when:
问题可复现、可修复，并给出验证步骤；如果合适就加一个最小回归测试
```

### 场景 C：让 Codex 先出计划

```text
先不要写代码。先阅读相关文件，给我一个最小可执行计划：
1. 你理解的问题是什么
2. 你打算改哪些文件
3. 风险点是什么
4. 你会如何验证
```

## 13. 新手最容易犯的 6 个错误

1. 只说“帮我修一下”，不给复现步骤
2. 不告诉它哪些文件最相关
3. 让两个并行线程同时修改同一批文件
4. 一开始就开太大的权限
5. 不看 diff 就直接提交
6. 不把团队规范写进 `AGENTS.md`

## 14. 一个适合长期使用的最小习惯

你可以把 Codex 当作一个“默认会行动的工程搭档”，但前提是你要给它边界：

1. 在仓库根目录启动
2. 明确写出目标、上下文、约束、完成标准
3. 先小范围改动，再逐步扩大
4. 让它自己验证
5. 你亲自看 diff
6. 再提交、推送

这样比把 Codex 当作单次问答工具更稳定，也更接近官方建议的使用方式。

## 15. 官方参考

- Quickstart: https://developers.openai.com/codex/quickstart
- Codex CLI: https://developers.openai.com/codex/cli
- CLI Features: https://developers.openai.com/codex/cli/features
- CLI Reference: https://developers.openai.com/codex/cli/reference
- Slash Commands: https://developers.openai.com/codex/cli/slash-commands
- Prompting: https://developers.openai.com/codex/prompting
- Workflows: https://developers.openai.com/codex/workflows
- Best Practices: https://developers.openai.com/codex/learn/best-practices
- AGENTS.md Guide: https://developers.openai.com/codex/guides/agents-md
- Config Basics: https://developers.openai.com/codex/config-basic
- Customization: https://developers.openai.com/codex/concepts/customization

---

如果你希望把这份教程继续扩成“团队内部规范版”，下一步最值得补的是：

1. 本仓库专用 `AGENTS.md`
2. 本仓库的 `.codex/config.toml`
3. 常用任务的提示词模板
