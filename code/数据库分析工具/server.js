// 数据库分析工具 — 后端
//
// 职责：
//   1. 接收数据库来源：
//        · SQLite —— 文件上传 或 服务器本地路径
//        · MySQL  —— 连接信息（主机/端口/用户/密码/库名）或连接 URL
//   2. 读取库/表结构、字段、外键、索引、行数、样本数据
//   3. 把结构摘要交给 Claude，分析每张表的用途
//
// 依赖：express、multer、mysql2、@anthropic-ai/sdk；SQLite 读取用 Node 内置的 node:sqlite。
//
// AI 调用支持自定义 base_url（用于 API 中转站）。

import express from 'express';
import multer from 'multer';
import Anthropic from '@anthropic-ai/sdk';
import mysql from 'mysql2/promise';
import { DatabaseSync } from 'node:sqlite';
import { randomUUID } from 'node:crypto';
import { writeFileSync, unlinkSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

// 读取 .env（如果存在）——手写一个极简解析，避免额外依赖
loadDotEnv();

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 512 * 1024 * 1024 } });

app.use(express.json({ limit: '2mb' }));
app.use(express.static(join(__dirname, 'public')));

const MODEL = 'claude-opus-4-8';

// ---------------------------------------------------------------------------
// 结构提取 —— SQLite
// ---------------------------------------------------------------------------

/** 打开一个只读的 SQLite 连接并抽取完整结构摘要。 */
function extractSqliteSchema(dbPath) {
  const db = new DatabaseSync(dbPath, { readOnly: true });
  try {
    const objects = db
      .prepare(
        `SELECT name, type, sql FROM sqlite_master
         WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'
         ORDER BY type, name`,
      )
      .all();

    const tables = [];
    const views = [];

    for (const obj of objects) {
      const columns = db.prepare(`PRAGMA table_info("${obj.name}")`).all().map((c) => ({
        name: c.name,
        type: c.type || '(未声明)',
        notnull: !!c.notnull,
        primaryKey: !!c.pk,
        defaultValue: c.dflt_value ?? null,
      }));

      if (obj.type === 'view') {
        views.push({ name: obj.name, columns, sql: obj.sql });
        continue;
      }

      const foreignKeys = db.prepare(`PRAGMA foreign_key_list("${obj.name}")`).all().map((fk) => ({
        column: fk.from,
        referencesTable: fk.table,
        referencesColumn: fk.to,
      }));

      const indexes = db
        .prepare(`PRAGMA index_list("${obj.name}")`)
        .all()
        .map((idx) => ({ name: idx.name, unique: !!idx.unique }));

      let rowCount = null;
      try {
        rowCount = db.prepare(`SELECT COUNT(*) AS n FROM "${obj.name}"`).get().n;
      } catch {
        rowCount = null;
      }

      let sampleRows = [];
      try {
        sampleRows = db.prepare(`SELECT * FROM "${obj.name}" LIMIT 3`).all().map(truncateRow);
      } catch {
        sampleRows = [];
      }

      tables.push({
        name: obj.name,
        columns,
        foreignKeys,
        indexes,
        rowCount,
        sampleRows,
        createSql: obj.sql,
      });
    }

    return { tables, views };
  } finally {
    db.close();
  }
}

// ---------------------------------------------------------------------------
// 结构提取 —— MySQL
// ---------------------------------------------------------------------------

/** 连接 MySQL，从 information_schema 抽取结构摘要。 */
async function extractMysqlSchema(cfg) {
  const conn = await mysql.createConnection({
    host: cfg.host,
    port: cfg.port,
    user: cfg.user,
    password: cfg.password,
    database: cfg.database,
    connectTimeout: 10000,
  });
  try {
    const dbName = cfg.database;

    const [objs] = await conn.query(
      `SELECT TABLE_NAME AS name, TABLE_TYPE AS type, TABLE_ROWS AS approxRows
       FROM information_schema.TABLES
       WHERE TABLE_SCHEMA = ?
       ORDER BY TABLE_TYPE, TABLE_NAME`,
      [dbName],
    );

    const tables = [];
    const views = [];

    for (const obj of objs) {
      const [colsRaw] = await conn.query(
        `SELECT COLUMN_NAME AS name, COLUMN_TYPE AS type, IS_NULLABLE AS nullable,
                COLUMN_KEY AS colKey, COLUMN_DEFAULT AS dflt
         FROM information_schema.COLUMNS
         WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
         ORDER BY ORDINAL_POSITION`,
        [dbName, obj.name],
      );
      const columns = colsRaw.map((c) => ({
        name: c.name,
        type: c.type || '(未知)',
        notnull: c.nullable === 'NO',
        primaryKey: c.colKey === 'PRI',
        defaultValue: c.dflt ?? null,
      }));

      // information_schema 里视图类型为 'VIEW'，基础表为 'BASE TABLE'
      if (obj.type === 'VIEW') {
        views.push({ name: obj.name, columns, sql: null });
        continue;
      }

      const [fksRaw] = await conn.query(
        `SELECT COLUMN_NAME AS col, REFERENCED_TABLE_NAME AS refTable, REFERENCED_COLUMN_NAME AS refCol
         FROM information_schema.KEY_COLUMN_USAGE
         WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND REFERENCED_TABLE_NAME IS NOT NULL`,
        [dbName, obj.name],
      );
      const foreignKeys = fksRaw.map((f) => ({
        column: f.col,
        referencesTable: f.refTable,
        referencesColumn: f.refCol,
      }));

      const [idxRaw] = await conn.query(
        `SELECT DISTINCT INDEX_NAME AS name, NON_UNIQUE AS nonUnique
         FROM information_schema.STATISTICS
         WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?`,
        [dbName, obj.name],
      );
      const indexes = idxRaw.map((i) => ({ name: i.name, unique: i.nonUnique === 0 }));

      // 抽 3 行样本。表名做反引号转义，防止特殊字符出错
      const safeName = '`' + String(obj.name).replace(/`/g, '``') + '`';
      let sampleRows = [];
      try {
        const [rows] = await conn.query(`SELECT * FROM ${safeName} LIMIT 3`);
        sampleRows = rows.map(truncateRow);
      } catch {
        sampleRows = [];
      }

      tables.push({
        name: obj.name,
        columns,
        foreignKeys,
        indexes,
        rowCount: obj.approxRows ?? null, // TABLE_ROWS 为估算值（InnoDB 近似）
        sampleRows,
        createSql: null,
      });
    }

    return { tables, views };
  } finally {
    await conn.end();
  }
}

/** 把一行数据里过长的字段截断，防止请求体过大。 */
function truncateRow(row) {
  const out = {};
  for (const [k, v] of Object.entries(row)) {
    if (typeof v === 'string' && v.length > 120) {
      out[k] = v.slice(0, 120) + '…';
    } else if (v instanceof Uint8Array || Buffer.isBuffer(v)) {
      out[k] = `<二进制 ${v.length} 字节>`;
    } else if (v instanceof Date) {
      out[k] = v.toISOString();
    } else {
      out[k] = v;
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Claude 分析
// ---------------------------------------------------------------------------

const ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    database_purpose: { type: 'string', description: '整个数据库的整体用途概述（中文，2-4 句）' },
    tables: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          category: {
            type: 'string',
            description: '分类，例如：用户、业务核心、关联表、日志、配置、缓存、其它',
          },
          purpose: { type: 'string', description: '这张表是干什么用的（中文，1-3 句）' },
          key_columns: { type: 'array', items: { type: 'string' }, description: '几个关键字段及其含义' },
          relationships: { type: 'string', description: '与其它表的关系；没有则写“无”' },
        },
        required: ['name', 'category', 'purpose', 'key_columns', 'relationships'],
        additionalProperties: false,
      },
    },
    notes: { type: 'string', description: '整体观察、潜在问题或建议（中文）；没有则写“无”' },
  },
  required: ['database_purpose', 'tables', 'notes'],
  additionalProperties: false,
};

async function analyzeWithClaude(schema, apiKey, baseUrl) {
  const opts = { apiKey };
  if (baseUrl) opts.baseURL = baseUrl; // 支持 API 中转站
  const client = new Anthropic(opts);

  const summary = schema.tables
    .map((t) => {
      const cols = t.columns
        .map((c) => `${c.name} ${c.type}${c.primaryKey ? ' PK' : ''}${c.notnull ? ' NOT NULL' : ''}`)
        .join(', ');
      const fks = t.foreignKeys.length
        ? '\n  外键: ' + t.foreignKeys.map((f) => `${f.column} → ${f.referencesTable}.${f.referencesColumn}`).join('; ')
        : '';
      const sample = t.sampleRows.length ? '\n  样本: ' + JSON.stringify(t.sampleRows) : '';
      return `表 ${t.name}（约 ${t.rowCount ?? '?'} 行）\n  字段: ${cols}${fks}${sample}`;
    })
    .join('\n\n');

  const viewSummary = schema.views.length
    ? '\n\n视图:\n' + schema.views.map((v) => `- ${v.name}（${v.columns.map((c) => c.name).join(', ')}）`).join('\n')
    : '';

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 16000,
    thinking: { type: 'adaptive' },
    output_config: { format: { type: 'json_schema', schema: ANALYSIS_SCHEMA } },
    system:
      '你是一位资深的数据库分析专家。给定一个数据库的结构（表、字段、外键、样本数据），' +
      '你需要推断整个数据库以及每一张表的实际业务用途。基于命名、字段类型、外键关系和样本数据进行判断，' +
      '用简洁准确的中文回答。不要臆造字段里没有的信息。',
    messages: [
      {
        role: 'user',
        content: `请分析下面这个数据库的用途，以及每张表分别是做什么的：\n\n${summary}${viewSummary}`,
      },
    ],
  });

  const textBlock = response.content.find((b) => b.type === 'text');
  if (!textBlock) throw new Error('模型未返回文本结果');
  return JSON.parse(textBlock.text);
}

// ---------------------------------------------------------------------------
// 输入解析：根据 dbType 分派到 SQLite / MySQL
// ---------------------------------------------------------------------------

/** 统一入口：读取请求里的数据库来源并返回结构 { tables, views }。 */
async function getSchema(req) {
  const dbType = (req.body?.dbType || 'sqlite').toLowerCase();

  if (dbType === 'mysql') {
    return extractMysqlSchema(resolveMysqlInput(req));
  }

  // 默认 SQLite
  const src = resolveSqliteInput(req);
  try {
    return extractSqliteSchema(src.path);
  } finally {
    cleanup(src.tmpPath);
  }
}

/** SQLite：文件上传（dbfile）或本地路径（path）。 */
function resolveSqliteInput(req) {
  if (req.file) {
    const tmpPath = join(tmpdir(), `sqlite-analyzer-${randomUUID()}.db`);
    writeFileSync(tmpPath, req.file.buffer);
    return { path: tmpPath, tmpPath };
  }
  const p = (req.body?.path || '').trim();
  if (!p) throw new Error('请上传一个 SQLite 文件，或提供服务器上的数据库文件路径。');
  if (!existsSync(p)) throw new Error(`找不到文件：${p}`);
  return { path: p, tmpPath: null };
}

/** MySQL：连接 URL（mysqlUrl）或分字段（host/port/user/password/database）。 */
function resolveMysqlInput(req) {
  const b = req.body || {};
  const url = (b.mysqlUrl || '').trim();

  if (url) {
    let u;
    try {
      u = new URL(url);
    } catch {
      throw new Error('MySQL 连接 URL 格式不正确，应形如 mysql://user:pass@host:3306/dbname');
    }
    const database = decodeURIComponent(u.pathname.replace(/^\//, ''));
    if (!u.hostname || !database) throw new Error('连接 URL 里缺少主机或数据库名。');
    return {
      host: u.hostname,
      port: u.port ? Number(u.port) : 3306,
      user: decodeURIComponent(u.username),
      password: decodeURIComponent(u.password),
      database,
    };
  }

  const host = (b.host || '').trim();
  const database = (b.database || '').trim();
  if (!host || !database) throw new Error('请填写 MySQL 主机和数据库名（或提供完整连接 URL）。');
  return {
    host,
    port: b.port ? Number(b.port) : 3306,
    user: (b.user || '').trim(),
    password: b.password || '',
    database,
  };
}

function cleanup(tmpPath) {
  if (tmpPath) {
    try {
      unlinkSync(tmpPath);
    } catch {
      /* ignore */
    }
  }
}

// ---------------------------------------------------------------------------
// 路由
// ---------------------------------------------------------------------------

// 仅提取结构（不调用 AI），用于快速预览
app.post('/api/schema', upload.single('dbfile'), async (req, res) => {
  try {
    const schema = await getSchema(req);
    res.json({ ok: true, schema });
  } catch (err) {
    res.status(400).json({ ok: false, error: String(err.message || err) });
  }
});

// 提取结构 + 调用 Claude 分析
app.post('/api/analyze', upload.single('dbfile'), async (req, res) => {
  try {
    const schema = await getSchema(req);

    if (schema.tables.length === 0) {
      return res.status(400).json({ ok: false, error: '这个数据库里没有找到任何表。' });
    }

    const apiKey = (req.body?.apiKey || '').trim() || process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      return res.status(400).json({
        ok: false,
        error: '缺少 API Key。请在 .env 里配置 ANTHROPIC_API_KEY，或在页面上临时填写。',
        schema,
      });
    }

    const baseUrl = (req.body?.baseUrl || '').trim() || process.env.ANTHROPIC_BASE_URL || undefined;

    const analysis = await analyzeWithClaude(schema, apiKey, baseUrl);
    res.json({ ok: true, schema, analysis });
  } catch (err) {
    res.status(500).json({ ok: false, error: String(err.message || err) });
  }
});

// ---------------------------------------------------------------------------

function loadDotEnv() {
  try {
    const envPath = join(process.cwd(), '.env');
    if (!existsSync(envPath)) return;
    const text = readFileSync(envPath, 'utf8');
    for (const line of text.split('\n')) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
      if (!m) continue;
      const key = m[1];
      let val = m[2].trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!(key in process.env) || !process.env[key]) process.env[key] = val;
    }
  } catch {
    /* .env 可选，读取失败就忽略 */
  }
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n  数据库分析工具已启动 → http://localhost:${PORT}\n`);
  if (!process.env.ANTHROPIC_API_KEY) {
    console.log('  提示：未检测到 ANTHROPIC_API_KEY，可在网页界面临时填写 API Key。\n');
  }
});
