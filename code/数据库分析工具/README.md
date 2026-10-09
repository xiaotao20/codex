# 数据库分析工具

一个网页版工具：连接一个数据库（**SQLite 文件** 或 **MySQL 连接**），自动读取库和表的结构，并调用 Claude 分析**每张表是干什么用的**、整个数据库的业务用途，以及表与表之间的关系。

支持使用 **API 中转站**（自定义 `base_url`）。

---

## 目录

- [功能特性](#功能特性)
- [技术选型](#技术选型)
- [环境要求](#环境要求)
- [安装与启动](#安装与启动)
- [使用方式](#使用方式)
  - [分析 SQLite](#分析-sqlite)
  - [分析 MySQL](#分析-mysql)
  - [使用中转站 API Key](#使用中转站-api-key)
- [工作原理](#工作原理)
- [API 说明](#api-说明)
- [项目结构](#项目结构)
- [安全与隐私](#安全与隐私)
- [常见问题](#常见问题)
- [限制与后续扩展](#限制与后续扩展)

---

## 功能特性

- 🗂️ **多数据库支持**：
  - **SQLite**：上传 `.db` / `.sqlite` 文件，或指定服务器本地路径。
  - **MySQL**：填写连接信息（主机/端口/用户/密码/库名）或一条连接 URL。
- 🔍 **结构自动提取**：字段（名称/类型/主键/非空）、外键关系、索引、行数、样本数据。
- 🤖 **AI 用途分析**：把结构摘要交给 Claude，得到：
  - 整个数据库的用途概述
  - 每张表的用途、分类（用户 / 业务核心 / 关联表 / 日志 / 配置 …）、关键字段、表间关系
  - 整体观察与建议
- 🔀 **支持 API 中转站**：可配置自定义 `base_url`，用中转站的 Key 调用。
- 🔌 **离线可用**：“仅读取结构”模式完全本地运行，不调用 AI、不需要 Key。
- 🎨 **零构建前端**：单个 HTML 页面，打开即用。

---

## 技术选型

| 部分 | 选型 | 说明 |
|------|------|------|
| 运行时 | **Node.js ≥ 22.5**（推荐 24） | 使用内置的 `node:sqlite` |
| 后端框架 | **Express 5** | 处理静态资源与 API 路由 |
| SQLite 读取 | **`node:sqlite`（Node 内置）** | 免去原生模块在 Windows 上的编译问题 |
| MySQL 读取 | **mysql2** | 纯 JS 驱动，无需编译；从 `information_schema` 抽取结构 |
| 文件上传 | **multer** | 处理浏览器上传的 SQLite 文件（内存暂存） |
| AI 分析 | **Anthropic Claude（`claude-opus-4-8`）** | 官方 `@anthropic-ai/sdk`，支持自定义 `baseURL`（中转站） |
| 输出稳定性 | **结构化输出（`output_config.format`）** | 用 JSON Schema 约束模型返回，保证前端可稳定渲染 |
| 前端 | **原生 HTML + CSS + JS** | 单页、无构建步骤、无框架依赖 |

**为什么需要一个后端？** 浏览器无法直接连接数据库；同时为了不把 API Key 暴露在前端，调用 Claude 也必须放在服务端。因此这个本地后端负责：读取数据库、代为调用 Claude。

---

## 环境要求

- **Node.js ≥ 22.5.0**（`node:sqlite` 从 22.5 引入；推荐 24）
- 一个 **Anthropic（或中转站）API Key**（仅“AI 分析”功能需要；“仅读取结构”不需要）
- 分析 MySQL 时，需要目标 MySQL 对运行本服务的机器**网络可达**

查看 Node 版本：

```bash
node --version
```

---

## 安装与启动

```bash
cd 数据库分析工具

# 1. 安装依赖
npm install

# 2. 配置（二选一）
#    A. 复制模板并填入 Key / base_url
#       Windows: copy .env.example .env
#       macOS/Linux: cp .env.example .env
#    B. 或者不配置，运行后在网页界面里临时填写

# 3. 启动
npm start
```

启动后打开 **http://localhost:3000**。默认端口 3000，可在 `.env` 用 `PORT=xxxx` 修改。

`.env` 可配置项：

```ini
ANTHROPIC_API_KEY=你的Key
ANTHROPIC_BASE_URL=https://你的中转站/v1   # 用中转站时填，否则留空直连官方
PORT=3000
```

---

## 使用方式

在页面顶部先选择**数据库类型**（SQLite / MySQL），下方会显示对应的输入项。

### 分析 SQLite

1. 选择「SQLite（文件）」。
2. **上传** `.db` / `.sqlite` 文件，**或**填写服务器本地绝对路径（如 `E:\data\app.sqlite`）。
3. 点「读取结构并用 AI 分析」。

### 分析 MySQL

1. 选择「MySQL（连接）」。
2. 两种填法二选一：
   - **连接 URL**：`mysql://用户名:密码@主机:3306/库名`
   - **分字段**：主机、端口（默认 3306）、用户名、密码、数据库名
3. 点「读取结构并用 AI 分析」。

> 行数为 MySQL 的估算值（InnoDB 的 `TABLE_ROWS` 近似统计），不是精确 COUNT。

### 使用中转站 API Key

如果你的 Key 来自 API 中转站，需要同时提供**中转站地址**：

- 在 `.env` 里设置 `ANTHROPIC_BASE_URL`，**或**
- 在页面的「Base URL」输入框里临时填写（形如 `https://your-relay.example.com/v1`）。

Key 同样支持 `.env`（`ANTHROPIC_API_KEY`）或页面临时填写；页面填写的都不会被保存。

---

## 工作原理

```
浏览器（选择类型 + 提供来源）
        │
        ▼
Express 后端
   1. SQLite → node:sqlite 只读打开
      MySQL  → mysql2 建立连接
   2. 提取结构：
        · 表 / 视图列表
        · 字段、主键、非空
        · 外键、索引
        · 行数、样本数据（大字段截断）
   3. 拼成紧凑摘要 → 调用 Claude（结构化输出，支持自定义 baseURL）
        │
        ▼
返回 { schema, analysis } → 前端渲染
```

---

## API 说明

两个接口均接受 `multipart/form-data`。公共字段：

| 字段 | 说明 |
|------|------|
| `dbType` | `sqlite`（默认）或 `mysql` |
| `apiKey` | 可选，覆盖 `.env` 的 Key |
| `baseUrl` | 可选，中转站地址，覆盖 `.env` 的 `ANTHROPIC_BASE_URL` |

按类型附加字段：

- **SQLite**：`dbfile`（上传文件）或 `path`（本地路径）
- **MySQL**：`mysqlUrl`（连接 URL），或分字段 `host` / `port` / `user` / `password` / `database`

### `POST /api/schema`

只提取结构，不调用 AI。响应：

```json
{ "ok": true, "schema": { "tables": [ ... ], "views": [ ... ] } }
```

### `POST /api/analyze`

提取结构并调用 Claude 分析。响应：

```json
{
  "ok": true,
  "schema": { "tables": [ ... ], "views": [ ... ] },
  "analysis": {
    "database_purpose": "……",
    "tables": [
      {
        "name": "users",
        "category": "用户",
        "purpose": "存储注册用户的账号信息",
        "key_columns": ["id 主键", "username 用户名"],
        "relationships": "被 orders.user_id 引用"
      }
    ],
    "notes": "……"
  }
}
```

未提供 API Key 时返回 `ok: false` 及错误说明，但仍会带上 `schema` 方便离线查看。

---

## 项目结构

```
数据库分析工具/
├── server.js          # 后端：SQLite/MySQL 结构提取 + Claude 调用 + 路由
├── public/
│   └── index.html     # 前端单页（含内联 CSS/JS）
├── package.json
├── .env.example       # 环境变量模板（Key / base_url / 端口）
├── .gitignore
└── README.md
```

---

## 安全与隐私

- SQLite 以**只读**方式打开；上传文件写入系统临时目录，**请求结束后立即删除**。
- MySQL 连接仅用于读取结构与样本，用完即断开；连接信息不落库、不保存。
- 页面上填写的 API Key / Base URL 仅用于当次请求，不写入磁盘。
- ⚠️ **样本数据会随结构摘要发送到所配置的 AI 接口**（官方或中转站）。若数据敏感，请改用「仅读取结构」（完全本地，不外发），并留意中转站的数据处理策略。

---

## 常见问题

**Q：启动时提示 `SQLite is an experimental feature`？**
A：`node:sqlite` 目前仍标记为实验特性，只是警告，不影响使用。

**Q：MySQL 连不上 / `ECONNREFUSED`？**
A：确认主机、端口正确，MySQL 允许该来源连接，且账号有权限；云数据库注意白名单/安全组。

**Q：中转站的 Key 报 401 / 404？**
A：检查 `base_url` 是否正确（有的中转站要带 `/v1`，有的不用），以及 Key 与该中转站是否匹配。

**Q：没有 API Key 能用吗？**
A：可以，用「仅读取结构」查看完整库表结构；AI 分析才需要 Key。

---

## 限制与后续扩展

- 目前支持 **SQLite** 与 **MySQL**。要加 PostgreSQL 等，只需引入对应驱动（如 `pg`）并补一个 `extractXxxSchema`，返回统一的 `{ tables, views }` 结构即可，前端无需改动。
- MySQL 行数为估算值；大表不做精确 COUNT，避免拖慢。
- 每张表仅抽取 3 行样本用于辅助判断，不做全量扫描。
- 分析质量取决于表名/字段名的规范程度；命名越清晰，结果越准确。
