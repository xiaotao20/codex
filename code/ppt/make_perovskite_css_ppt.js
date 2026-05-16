const fs = require("fs");
const path = require("path");
const bundledNodeModules = process.env.CODEX_BUNDLED_NODE_MODULES;
const PptxGenJS = bundledNodeModules
  ? require(path.join(bundledNodeModules, "pptxgenjs"))
  : require("pptxgenjs");

const outputDir = path.resolve(__dirname, "../../docs/presentations");
const outputFile = path.join(outputDir, "近距离升华制备钙钛矿.pptx");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "xiaotao";
pptx.subject = "近距离升华制备钙钛矿：方式、原理与证据链分析";
pptx.title = "近距离升华制备钙钛矿";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "PingFang SC",
  bodyFontFace: "PingFang SC",
  lang: "zh-CN",
};

const C = {
  navy: "0A1020",
  navySoft: "162039",
  paper: "F6F7FB",
  white: "FFFFFF",
  ink: "111827",
  muted: "667085",
  border: "D7DCE6",
  teal: "18B7AE",
  tealSoft: "D7F6F3",
  amber: "E9A45B",
  amberSoft: "FFF1E1",
  rose: "C86B82",
  roseSoft: "FCEAF0",
  blue: "4E7BFF",
  blueSoft: "E8EFFF",
  green: "2E9D5B",
  greenSoft: "E6F7EC",
};

const W = 13.333;
const H = 7.5;
const FONT = "PingFang SC";

function addText(slide, text, opts) {
  slide.addText(text, {
    fontFace: FONT,
    color: C.ink,
    margin: 0,
    fit: "shrink",
    ...opts,
  });
}

function addSectionHeader(slide, section, title, subtitle, pageNo) {
  slide.background = { color: C.paper };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: 0.18,
    line: { color: C.navy, transparency: 100 },
    fill: { color: C.navy },
  });
  addText(slide, section.toUpperCase(), {
    x: 0.62,
    y: 0.32,
    w: 1.8,
    h: 0.24,
    fontSize: 10,
    bold: true,
    color: C.teal,
  });
  addText(slide, String(pageNo).padStart(2, "0"), {
    x: 12.15,
    y: 0.26,
    w: 0.55,
    h: 0.3,
    fontSize: 14,
    bold: true,
    align: "right",
    color: C.navy,
  });
  addText(slide, title, {
    x: 0.62,
    y: 0.6,
    w: 8.4,
    h: 0.44,
    fontSize: 24,
    bold: true,
    color: C.navy,
  });
  if (subtitle) {
    addText(slide, subtitle, {
      x: 0.62,
      y: 1.05,
      w: 9.6,
      h: 0.32,
      fontSize: 11.5,
      color: C.muted,
    });
  }
  slide.addShape(pptx.ShapeType.line, {
    x: 0.62,
    y: 1.34,
    w: 12.1,
    h: 0,
    line: { color: C.border, width: 1 },
  });
}

function addFooter(slide, cite) {
  if (!cite) return;
  slide.addShape(pptx.ShapeType.line, {
    x: 0.62,
    y: 7.02,
    w: 12.1,
    h: 0,
    line: { color: C.border, width: 0.7 },
  });
  addText(slide, cite, {
    x: 0.66,
    y: 7.08,
    w: 11.8,
    h: 0.2,
    fontSize: 8.5,
    color: C.muted,
  });
}

function addCard(slide, x, y, w, h, options = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: {
      color: options.borderColor || C.border,
      width: options.borderWidth || 1,
    },
    fill: {
      color: options.fillColor || C.white,
      transparency: options.transparency || 0,
    },
  });
  if (options.topBarColor) {
    slide.addShape(pptx.ShapeType.rect, {
      x: x + 0.02,
      y: y + 0.02,
      w: w - 0.04,
      h: 0.08,
      line: { color: options.topBarColor, transparency: 100 },
      fill: { color: options.topBarColor },
    });
  }
}

function addBulletList(slide, x, y, w, items, opts = {}) {
  const bulletColor = opts.bulletColor || C.teal;
  const textColor = opts.color || C.ink;
  const lineGap = opts.lineGap || 0.58;
  items.forEach((item, idx) => {
    slide.addShape(pptx.ShapeType.ellipse, {
      x,
      y: y + idx * lineGap + 0.1,
      w: 0.1,
      h: 0.1,
      line: { color: bulletColor, transparency: 100 },
      fill: { color: bulletColor },
    });
    addText(slide, item, {
      x: x + 0.18,
      y: y + idx * lineGap,
      w: w - 0.18,
      h: 0.42,
      fontSize: opts.fontSize || 13,
      color: textColor,
    });
  });
}

function addMetricChip(slide, x, y, w, label, value, accentColor) {
  addCard(slide, x, y, w, 0.82, {
    fillColor: C.white,
    borderColor: accentColor,
    borderWidth: 1.3,
  });
  addText(slide, label, {
    x: x + 0.14,
    y: y + 0.12,
    w: w - 0.28,
    h: 0.18,
    fontSize: 9,
    color: C.muted,
    bold: true,
  });
  addText(slide, value, {
    x: x + 0.14,
    y: y + 0.36,
    w: w - 0.28,
    h: 0.24,
    fontSize: 15.5,
    color: accentColor,
    bold: true,
  });
}

function addProgressRow(slide, x, y, label, level, valueText, color) {
  addText(slide, label, {
    x,
    y,
    w: 1.8,
    h: 0.22,
    fontSize: 11.5,
    color: C.ink,
    bold: true,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 1.9,
    y: y + 0.04,
    w: 3.2,
    h: 0.12,
    line: { color: C.border, transparency: 100 },
    fill: { color: "E5E7EB" },
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 1.9,
    y: y + 0.04,
    w: 3.2 * level,
    h: 0.12,
    line: { color, transparency: 100 },
    fill: { color },
  });
  addText(slide, valueText, {
    x: x + 5.25,
    y: y - 0.02,
    w: 1.4,
    h: 0.25,
    fontSize: 11,
    color: C.muted,
    align: "right",
  });
}

function addTimelineCard(slide, x, y, title, body, accent, year, up) {
  const cardY = up ? y - 1.55 : y + 0.18;
  addCard(slide, x - 0.98, cardY, 1.96, 1.28, {
    fillColor: C.white,
    borderColor: accent,
    borderWidth: 1.2,
    topBarColor: accent,
  });
  slide.addShape(pptx.ShapeType.line, {
    x,
    y: up ? y - 0.27 : y + 0.01,
    w: 0,
    h: up ? -0.44 : 0.44,
    line: { color: accent, width: 1.1 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x - 0.07,
    y: y - 0.07,
    w: 0.14,
    h: 0.14,
    line: { color: accent, width: 1, transparency: 0 },
    fill: { color: accent },
  });
  addText(slide, year, {
    x: x - 0.34,
    y: up ? y - 0.05 : y + 0.13,
    w: 0.68,
    h: 0.18,
    fontSize: 9.5,
    bold: true,
    color: accent,
    align: "center",
  });
  addText(slide, title, {
    x: x - 0.85,
    y: cardY + 0.14,
    w: 1.7,
    h: 0.26,
    fontSize: 10.3,
    bold: true,
    color: C.ink,
    align: "center",
  });
  addText(slide, body, {
    x: x - 0.84,
    y: cardY + 0.46,
    w: 1.68,
    h: 0.62,
    fontSize: 9.4,
    color: C.muted,
    align: "center",
    valign: "mid",
  });
}

function addCoverDecoration(slide) {
  slide.background = { color: C.navy };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    line: { color: C.navy, transparency: 100 },
    fill: { color: C.navy },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 8.9,
    y: -0.8,
    w: 4.8,
    h: 4.8,
    line: { color: C.teal, transparency: 100 },
    fill: { color: C.teal, transparency: 84 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 9.8,
    y: 3.5,
    w: 3.2,
    h: 3.2,
    line: { color: C.amber, transparency: 100 },
    fill: { color: C.amber, transparency: 88 },
  });
  for (let i = 0; i < 6; i += 1) {
    slide.addShape(pptx.ShapeType.line, {
      x: 8.25 + i * 0.48,
      y: 1.6 + (i % 2) * 0.42,
      w: 0.9,
      h: 0.55,
      line: { color: "4AE2D8", width: 0.8, transparency: 45 },
    });
  }
  const sourceX = 8.18;
  slide.addShape(pptx.ShapeType.roundRect, {
    x: sourceX,
    y: 2.05,
    w: 3.4,
    h: 0.6,
    line: { color: "5EDFD6", width: 1.2 },
    fill: { color: "15253E" },
  });
  addText(slide, "有机卤化物源 / 可复用 pellet", {
    x: sourceX + 0.2,
    y: 2.18,
    w: 3,
    h: 0.22,
    fontSize: 11,
    color: C.white,
    align: "center",
  });
  slide.addShape(pptx.ShapeType.line, {
    x: sourceX + 0.22,
    y: 3.05,
    w: 2.96,
    h: 0,
    line: { color: "7C8AAA", width: 1.1 },
  });
  addText(slide, "近距离 gap + 低真空", {
    x: sourceX + 0.82,
    y: 2.72,
    w: 1.8,
    h: 0.18,
    fontSize: 10,
    color: "B7C4E0",
    align: "center",
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: sourceX + 0.22,
    y: 3.26,
    w: 2.96,
    h: 0.52,
    line: { color: C.amber, width: 1.1 },
    fill: { color: "1C2431" },
  });
  addText(slide, "PbX2 骨架 / 受热基底", {
    x: sourceX + 0.42,
    y: 3.39,
    w: 2.56,
    h: 0.2,
    fontSize: 11,
    color: C.white,
    align: "center",
  });
  [8.58, 9.25, 9.92, 10.59].forEach((x) => {
    slide.addShape(pptx.ShapeType.line, {
      x,
      y: 2.7,
      w: 0,
      h: 0.42,
      line: { color: C.teal, width: 1.2 },
    });
  });
}

function makeSlides() {
  let page = 1;

  {
    const slide = pptx.addSlide();
    addCoverDecoration(slide);
    addText(slide, "PEROVSKITE PROCESS NOTE", {
      x: 0.72,
      y: 0.68,
      w: 2.9,
      h: 0.18,
      fontSize: 10,
      color: C.teal,
      bold: true,
    });
    addText(slide, "近距离升华制备钙钛矿", {
      x: 0.72,
      y: 1.08,
      w: 6.4,
      h: 0.46,
      fontSize: 28,
      bold: true,
      color: C.white,
    });
    addText(slide, "方式、原理与证据链分析", {
      x: 0.72,
      y: 1.58,
      w: 4.7,
      h: 0.28,
      fontSize: 16,
      color: "D4D9E6",
    });
    addText(slide, "把 CSS 视作“受控近场供料 + 固相转化”问题，而不是简单把钙钛矿当成传统共蒸发材料来处理。", {
      x: 0.72,
      y: 2.16,
      w: 5.9,
      h: 0.7,
      fontSize: 16,
      color: C.white,
      breakLine: false,
      bold: false,
      valign: "mid",
    });
    addMetricChip(slide, 0.72, 5.56, 1.98, "代表结果", "18.7% · 10 mbar", C.teal);
    addMetricChip(slide, 2.92, 5.56, 1.98, "大面积结果", "18.8% · 1 mbar", C.amber);
    addMetricChip(slide, 5.12, 5.56, 1.98, "串联趋势", "24.3% · tandem", C.blue);
    addText(slide, "基于 2020-2026 代表性论文整理；正文为中文，参考文献放在最后一页。", {
      x: 0.74,
      y: 6.72,
      w: 6.2,
      h: 0.2,
      fontSize: 9,
      color: "9FB0D1",
    });
    addText(slide, "01", {
      x: 12.1,
      y: 6.66,
      w: 0.6,
      h: 0.24,
      fontSize: 14,
      color: "9FB0D1",
      bold: true,
      align: "right",
    });
    addFooter(slide, "证据来源：[1] Rodkey 2024；[4] Gomar-Fernández 2025；[6] Diercks 2026（KITopen / Nature Energy 预印本记录）");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Executive summary", "先说判断", "这页只回答一个问题：CSS 值不值得做，以及它的本质是什么。", page);
    addCard(slide, 0.78, 1.68, 4.3, 4.78, {
      fillColor: C.navy,
      borderColor: C.navy,
      topBarColor: C.teal,
    });
    addText(slide, "作者判断", {
      x: 1.04,
      y: 1.98,
      w: 1.2,
      h: 0.2,
      fontSize: 10.5,
      color: C.teal,
      bold: true,
    });
    addText(slide, "CSS 对钙钛矿更像\n“受控近场供料 + 固相转化”", {
      x: 1.02,
      y: 2.34,
      w: 3.54,
      h: 1.25,
      fontSize: 22,
      color: C.white,
      bold: true,
      valign: "mid",
    });
    addText(slide, "如果把它当成简单蒸发，会只盯沉积速率；\n如果把它当成转化问题，才会真正重视 source chemistry、反应前沿和带隙稳定性。", {
      x: 1.02,
      y: 4.02,
      w: 3.4,
      h: 1.05,
      fontSize: 13,
      color: "D4D9E6",
      valign: "mid",
    });
    const cards = [
      {
        x: 5.44,
        y: 1.7,
        w: 3.28,
        h: 1.9,
        color: C.teal,
        title: "为什么值得看",
        body: "较低工作压强、较高材料传输、几何简单，天然带着工业薄膜工艺的味道。",
      },
      {
        x: 8.94,
        y: 1.7,
        w: 3.28,
        h: 1.9,
        color: C.amber,
        title: "最现实的路线",
        body: "“无机骨架 + 挥发性有机卤化物源”是当前文献里最可信、也最可扩展的工艺范式。",
      },
      {
        x: 5.44,
        y: 3.92,
        w: 3.28,
        h: 1.9,
        color: C.blue,
        title: "已经证明的上限",
        body: "单结器件已有 18.7% 与 18.8%，宽带隙串联路线已做到 24.3%。",
      },
      {
        x: 8.94,
        y: 3.92,
        w: 3.28,
        h: 1.9,
        color: C.rose,
        title: "真正的难点",
        body: "难点不是“能不能蒸”，而是有机源稳定性、相组成控制和反应窗口管理。",
      },
    ];
    cards.forEach((item) => {
      addCard(slide, item.x, item.y, item.w, item.h, {
        fillColor: C.white,
        borderColor: item.color,
        borderWidth: 1.3,
        topBarColor: item.color,
      });
      addText(slide, item.title, {
        x: item.x + 0.18,
        y: item.y + 0.18,
        w: item.w - 0.36,
        h: 0.22,
        fontSize: 13,
        bold: true,
        color: C.ink,
      });
      addText(slide, item.body, {
        x: item.x + 0.18,
        y: item.y + 0.52,
        w: item.w - 0.36,
        h: 1.0,
        fontSize: 11.6,
        color: C.muted,
        valign: "mid",
      });
    });
    addFooter(slide, "证据来源：[1][3][4][5][6]。其中“作者判断”为基于这些论文结果的综合归纳。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Positioning", "CSS 在制备路线中的位置", "不是所有干法都一样。CSS 的独特性在于“近场几何 + 中等真空 + 高传质”。", page);
    const routes = [
      {
        x: 0.82,
        title: "溶液法",
        accent: C.blue,
        lines: [
          "供料：液相前驱体 + 溶剂",
          "优点：实验室效率最高、化学空间宽",
          "难点：干燥/结晶窗口窄，大面积一致性难",
        ],
      },
      {
        x: 4.52,
        title: "共蒸发",
        accent: C.amber,
        lines: [
          "供料：多热源、较高真空、同步蒸发",
          "优点：洁净、可与真空线兼容",
          "难点：源数多、配比与蒸发速率控制负担大",
        ],
      },
      {
        x: 8.22,
        title: "近距离升华 CSS",
        accent: C.teal,
        lines: [
          "供料：近场 gap + 挥发性源 + 骨架转化",
          "优点：高材料传输、低工作压强、几何简单",
          "难点：source chemistry、反应前沿、带隙漂移",
        ],
      },
    ];
    routes.forEach((route) => {
      addCard(slide, route.x, 1.74, 3.05, 4.4, {
        fillColor: C.white,
        borderColor: route.accent,
        borderWidth: 1.3,
        topBarColor: route.accent,
      });
      addText(slide, route.title, {
        x: route.x + 0.18,
        y: 1.98,
        w: 2.7,
        h: 0.28,
        fontSize: 16,
        bold: true,
        color: C.ink,
        align: "center",
      });
      addBulletList(slide, route.x + 0.18, 2.54, 2.68, route.lines, {
        bulletColor: route.accent,
        fontSize: 12.1,
        lineGap: 0.9,
        color: C.muted,
      });
    });
    addCard(slide, 0.82, 6.34, 10.45, 0.46, {
      fillColor: C.navySoft,
      borderColor: C.navySoft,
    });
    addText(slide, "一句话定位：CSS 用更低的设备复杂度，换取更高的近场供料效率；但必须接受它是一个强依赖化学计量与转化动力学的工艺。", {
      x: 1.06,
      y: 6.46,
      w: 9.95,
      h: 0.18,
      fontSize: 12.4,
      color: C.white,
      align: "center",
    });
    addFooter(slide, "CSS 优势与行业适配性的直接证据见 [1] 和 [4]；本页对三类路线的对比包含作者概括。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Method", "近距离升华到底怎么做", "对钙钛矿而言，CSS 最常见的不是“一步全蒸发”，而是围绕骨架转化组织流程。", page);
    addCard(slide, 0.82, 1.72, 5.0, 4.95, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.teal,
    });
    addText(slide, "设备与空间构型", {
      x: 1.04,
      y: 1.96,
      w: 2.0,
      h: 0.24,
      fontSize: 15,
      bold: true,
      color: C.ink,
    });
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 1.18,
      y: 2.56,
      w: 4.2,
      h: 0.65,
      line: { color: C.teal, width: 1.2 },
      fill: { color: C.tealSoft },
    });
    addText(slide, "挥发性有机卤化物源 / mixed-halide source", {
      x: 1.3,
      y: 2.78,
      w: 3.96,
      h: 0.2,
      fontSize: 12,
      bold: true,
      color: C.ink,
      align: "center",
    });
    slide.addShape(pptx.ShapeType.line, {
      x: 1.5,
      y: 3.55,
      w: 3.56,
      h: 0,
      line: { color: C.border, width: 1.2 },
    });
    addText(slide, "小间距 / 粗真空（文献常见 1–10 mbar）", {
      x: 1.6,
      y: 3.2,
      w: 3.36,
      h: 0.2,
      fontSize: 11,
      color: C.muted,
      align: "center",
    });
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 1.42,
      y: 3.82,
      w: 3.72,
      h: 0.62,
      line: { color: C.amber, width: 1.2 },
      fill: { color: C.amberSoft },
    });
    addText(slide, "受热无机骨架 / 底电极 / 纹理硅上表面", {
      x: 1.56,
      y: 4.02,
      w: 3.44,
      h: 0.18,
      fontSize: 12,
      bold: true,
      color: C.ink,
      align: "center",
    });
    [2.0, 2.8, 3.6, 4.4].forEach((x) => {
      slide.addShape(pptx.ShapeType.line, {
        x,
        y: 3.25,
        w: 0,
        h: 0.45,
        line: { color: C.teal, width: 1.2 },
      });
    });
    addText(slide, "气相供料 + 表面吸附 + 相转化", {
      x: 1.6,
      y: 4.78,
      w: 3.4,
      h: 0.2,
      fontSize: 12.5,
      color: C.navy,
      bold: true,
      align: "center",
    });
    addText(slide, "泛化反应：PbX2(s) + AX(g) → APbX3(s)", {
      x: 1.36,
      y: 5.3,
      w: 3.84,
      h: 0.24,
      fontSize: 13,
      color: C.ink,
      bold: true,
      align: "center",
    });

    addCard(slide, 6.06, 1.72, 6.44, 4.95, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.blue,
    });
    addText(slide, "典型工艺顺序", {
      x: 6.3,
      y: 1.96,
      w: 2.0,
      h: 0.24,
      fontSize: 15,
      bold: true,
      color: C.ink,
    });
    const steps = [
      ["01", "先做无机骨架", "常见是 PbI2 / PbBr2 或可转化的含铅卤化物前驱层。"],
      ["02", "把有机源放进近场", "如 FAI pellet、MABr 源或 mixed-halide organic source。"],
      ["03", "控制 gap、温度与压强", "CSS 的核心变量不是一个，而是几何、热场与 source chemistry 的联立。"],
      ["04", "受控供料并触发表面反应", "真正决定是否得到目标相的，是反应前沿能否均匀推进。"],
      ["05", "后续稳定化/集成", "包括温度应力、纹理硅兼容性和带隙保持。"],
    ];
    steps.forEach((step, idx) => {
      const y = 2.42 + idx * 0.8;
      slide.addShape(pptx.ShapeType.ellipse, {
        x: 6.3,
        y,
        w: 0.34,
        h: 0.34,
        line: { color: C.blue, width: 1.2 },
        fill: { color: C.blueSoft },
      });
      addText(slide, step[0], {
        x: 6.34,
        y: y + 0.07,
        w: 0.26,
        h: 0.12,
        fontSize: 8.5,
        bold: true,
        color: C.blue,
        align: "center",
      });
      addText(slide, step[1], {
        x: 6.78,
        y: y - 0.02,
        w: 1.75,
        h: 0.2,
        fontSize: 12.5,
        color: C.ink,
        bold: true,
      });
      addText(slide, step[2], {
        x: 8.55,
        y: y - 0.04,
        w: 3.55,
        h: 0.34,
        fontSize: 11.1,
        color: C.muted,
      });
    });
    addFooter(slide, "工艺路线与代表案例来源：[1][2][4][6]。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Principle I", "原理一：近场传质为什么有效", "短 gap 不只是“离得近”，而是显著改变了局部供料、分压与输运阻力。", page);
    addCard(slide, 0.82, 1.72, 4.84, 5.0, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.teal,
    });
    addText(slide, "概念图", {
      x: 1.06,
      y: 1.98,
      w: 1.1,
      h: 0.22,
      fontSize: 14.5,
      bold: true,
      color: C.ink,
    });
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 1.22,
      y: 2.45,
      w: 3.95,
      h: 0.56,
      line: { color: C.teal, width: 1.2 },
      fill: { color: C.tealSoft },
    });
    addText(slide, "源侧分压 Psource", {
      x: 2.12,
      y: 2.63,
      w: 2.1,
      h: 0.18,
      fontSize: 12.5,
      bold: true,
      color: C.ink,
      align: "center",
    });
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 1.42,
      y: 4.22,
      w: 3.55,
      h: 0.54,
      line: { color: C.amber, width: 1.2 },
      fill: { color: C.amberSoft },
    });
    addText(slide, "表面分压 Psurface / 转化界面", {
      x: 1.76,
      y: 4.4,
      w: 2.88,
      h: 0.18,
      fontSize: 12,
      bold: true,
      color: C.ink,
      align: "center",
    });
    slide.addShape(pptx.ShapeType.line, {
      x: 1.55,
      y: 3.45,
      w: 3.18,
      h: 0,
      line: { color: C.border, width: 1.2 },
    });
    addText(slide, "gap ↓  →  传质阻力 ↓", {
      x: 2.06,
      y: 3.12,
      w: 2.1,
      h: 0.2,
      fontSize: 12,
      color: C.muted,
      align: "center",
    });
    [2.0, 2.82, 3.64, 4.46].forEach((x) => {
      slide.addShape(pptx.ShapeType.line, {
        x,
        y: 3.0,
        w: 0,
        h: 0.96,
        line: { color: C.teal, width: 1.1 },
      });
    });
    addCard(slide, 1.2, 5.2, 4.1, 1.1, {
      fillColor: C.navySoft,
      borderColor: C.navySoft,
    });
    addText(slide, "经验上可把它理解为：\nΔP = Psource − Psurface；gap 越短，局部供料越充足。", {
      x: 1.42,
      y: 5.46,
      w: 3.66,
      h: 0.5,
      fontSize: 12.4,
      color: C.white,
      align: "center",
      valign: "mid",
    });

    addCard(slide, 5.98, 1.72, 6.54, 5.0, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.blue,
    });
    addText(slide, "从文献里可以比较稳地读出三件事", {
      x: 6.24,
      y: 1.98,
      w: 3.1,
      h: 0.24,
      fontSize: 14.5,
      bold: true,
      color: C.ink,
    });
    addBulletList(slide, 6.26, 2.48, 5.82, [
      "CSS 在钙钛矿论文中反复被描述为具有高材料传输与低工作压强优势。",
      "1 mbar 与 10 mbar 两类代表结果都已给出有效器件，说明 CSS 不依赖超高真空才成立。",
      "到 2026 年的宽带隙工作里，机制分析已明确提示：CSS 过程可进入 substitution-reaction-limited regime。",
    ], {
      bulletColor: C.blue,
      fontSize: 12.4,
      lineGap: 0.86,
      color: C.muted,
    });
    addCard(slide, 6.26, 5.28, 5.96, 0.92, {
      fillColor: C.blueSoft,
      borderColor: C.blueSoft,
    });
    addText(slide, "因此，整体速率更适合写成：voverall = min(vtransport, vreaction)。\n对钙钛矿来说，真正限制上限的常常不是“能否到达”，而是“到达后能否稳定转化”。", {
      x: 6.52,
      y: 5.5,
      w: 5.48,
      h: 0.42,
      fontSize: 12.1,
      color: C.navy,
      bold: true,
      align: "center",
    });
    addFooter(slide, "直接证据：[1] 10 mbar 粗真空器件；[4] 1 mbar 大面积 CSS；[6] substitution-reaction-limited 机制表述。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Principle II", "原理二：钙钛矿不是只靠“蒸”，更靠“转化”", "把 CSS 当成“气相供料 + 固相反应”问题，很多现象会突然变得合理。", page);
    addCard(slide, 0.82, 1.72, 5.24, 5.0, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.amber,
    });
    addText(slide, "转化链条", {
      x: 1.08,
      y: 1.98,
      w: 1.1,
      h: 0.22,
      fontSize: 14.5,
      bold: true,
      color: C.ink,
    });
    const boxes = [
      { x: 1.16, y: 2.48, w: 1.18, h: 0.72, t: "无机骨架", c: C.amberSoft },
      { x: 2.6, y: 2.48, w: 1.18, h: 0.72, t: "有机源供料", c: C.tealSoft },
      { x: 4.04, y: 2.48, w: 1.18, h: 0.72, t: "反应前沿推进", c: C.blueSoft },
      { x: 2.6, y: 3.82, w: 1.18, h: 0.72, t: "晶粒长大", c: C.roseSoft },
      { x: 4.04, y: 3.82, w: 1.18, h: 0.72, t: "目标相钙钛矿", c: C.greenSoft },
    ];
    boxes.forEach((box) => {
      addCard(slide, box.x, box.y, box.w, box.h, {
        fillColor: box.c,
        borderColor: C.border,
      });
      addText(slide, box.t, {
        x: box.x + 0.08,
        y: box.y + 0.22,
        w: box.w - 0.16,
        h: 0.24,
        fontSize: 11.5,
        bold: true,
        color: C.ink,
        align: "center",
      });
    });
    [
      [2.34, 2.84, 0.22, 0],
      [3.78, 2.84, 0.22, 0],
      [3.18, 3.2, 0, 0.58],
      [4.62, 4.18, 0.22, 0],
    ].forEach(([x, y, w, h]) => {
      slide.addShape(pptx.ShapeType.line, {
        x,
        y,
        w,
        h,
        line: { color: C.navy, width: 1.2 },
      });
    });
    addCard(slide, 1.14, 5.18, 4.76, 0.96, {
      fillColor: C.navySoft,
      borderColor: C.navySoft,
    });
    addText(slide, "这也是为什么 source chemistry、界面状态与相组成控制会比“单纯提高蒸发速率”更重要。", {
      x: 1.42,
      y: 5.46,
      w: 4.2,
      h: 0.3,
      fontSize: 12.2,
      color: C.white,
      bold: true,
      align: "center",
    });

    addCard(slide, 6.32, 1.72, 6.2, 5.0, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.teal,
    });
    addText(slide, "证据怎么支持这个判断", {
      x: 6.56,
      y: 1.98,
      w: 2.5,
      h: 0.22,
      fontSize: 14.5,
      bold: true,
      color: C.ink,
    });
    addBulletList(slide, 6.58, 2.44, 5.5, [
      "2020 的 MAPbBr3 工作采用“PbBr2 先成层、再用 MABr 近场供料”的两步 CSS 路线，本身就说明转化是主线。[2]",
      "2024 ACS Energy Letters 用可多次复用的 FAI pellet 做有机源，核心解决的是 source stability，而不是单纯的蒸发装置问题。[1]",
      "2022 close-space annealing 表明，即便不走 sublimation，只要把中间相置于受限空间中，也能显著放大晶粒、提升结晶与延长寿命。[5]",
      "2026 的宽带隙 CSS 进一步把这一点说清：它已进入 substitution-reaction-limited 语境。[6]",
    ], {
      bulletColor: C.teal,
      fontSize: 11.8,
      lineGap: 0.82,
      color: C.muted,
    });
    addFooter(slide, "关键支持文献：[1][2][5][6]。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Evidence", "代表性文献证据", "把重要结果按时间铺开，比只看一篇 paper 更容易判断这条路线到底是“偶然有效”还是“持续变好”。", page);
    slide.addShape(pptx.ShapeType.line, {
      x: 1.12,
      y: 4.06,
      w: 11.0,
      h: 0,
      line: { color: C.border, width: 1.3 },
    });
    addTimelineCard(slide, 1.7, 4.06, "MAPbBr3", "两步 CSS；3 μm 膜厚；\n粗糙度 118→6 nm。", C.amber, "2020", true);
    addTimelineCard(slide, 3.96, 4.06, "CsFA 碘化物", "10 mbar；18.7%；\nFAI pellet 可复用。", C.teal, "2024", false);
    addTimelineCard(slide, 6.22, 4.06, "CsPbBr3", "单相薄膜；10 μm/min；\n利用率最高 98%。", C.blue, "2024", true);
    addTimelineCard(slide, 8.48, 4.06, "大面积 MAPI", "1 mbar；18.8%；\n1000 h 后保留 90%。", C.green, "2025", false);
    addTimelineCard(slide, 10.74, 4.06, "WBG / Tandem", "1.64 eV；18.5% 单结；\n24.3% 串联。", C.rose, "2026", true);
    addCard(slide, 0.96, 5.9, 11.36, 0.62, {
      fillColor: C.navySoft,
      borderColor: C.navySoft,
    });
    addText(slide, "时间线给出的结论很一致：CSS 已经从“能成膜”走到“能做效率、能做稳定性、能做纹理硅串联”。", {
      x: 1.24,
      y: 6.1,
      w: 10.82,
      h: 0.22,
      fontSize: 13,
      color: C.white,
      bold: true,
      align: "center",
    });
    addFooter(slide, "文献来源依次为：[2][1][3][4][6]。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Synthesis", "这些结果说明了什么", "如果只看效率，很容易误判；把膜质、器件和工艺三层放到一起看，路线判断会更稳。", page);
    const columns = [
      {
        x: 0.82,
        title: "膜质层面",
        accent: C.teal,
        items: [
          "大晶粒、均匀覆盖、厚膜能力已被多篇工作验证。",
          "MAPbBr3 粗糙度显著下降，说明后续压实/界面处理也有空间。",
          "close-space 气氛对晶化动力学的调节作用并非个例。",
        ],
      },
      {
        x: 4.46,
        title: "器件层面",
        accent: C.blue,
        items: [
          "18.7% 和 18.8% 说明 CSS 单结已进入“高可用”区间。",
          "宽带隙 1.64 eV 与 24.3% 串联说明它不仅能做薄膜，还能接入 tandem 架构。",
          "热应力与长时照射稳定性结果已经开始具备工程意义。",
        ],
      },
      {
        x: 8.1,
        title: "制造层面",
        accent: C.amber,
        items: [
          "1–10 mbar 的工作区间意味着真空门槛并不极端。",
          "多次复用有机源和 98% 利用率，直接指向材料成本与 throughput。",
          "对 planar / nano / micro-textured Si 的适配性是串联工业化信号。",
        ],
      },
    ];
    columns.forEach((col) => {
      addCard(slide, col.x, 1.72, 3.05, 3.64, {
        fillColor: C.white,
        borderColor: col.accent,
        borderWidth: 1.2,
        topBarColor: col.accent,
      });
      addText(slide, col.title, {
        x: col.x + 0.18,
        y: 1.96,
        w: 2.68,
        h: 0.22,
        fontSize: 14,
        bold: true,
        color: C.ink,
        align: "center",
      });
      addBulletList(slide, col.x + 0.18, 2.42, 2.68, col.items, {
        bulletColor: col.accent,
        fontSize: 11.45,
        lineGap: 0.82,
        color: C.muted,
      });
    });
    addCard(slide, 0.82, 5.68, 6.18, 0.92, {
      fillColor: C.white,
      borderColor: C.border,
      topBarColor: C.rose,
    });
    addText(slide, "综合成熟度判断", {
      x: 1.08,
      y: 5.92,
      w: 1.8,
      h: 0.22,
      fontSize: 14,
      color: C.ink,
      bold: true,
    });
    addProgressRow(slide, 1.08, 6.2, "单结效率竞争力", 0.62, "中高", C.rose);
    addProgressRow(slide, 1.08, 6.48, "工艺扩展性", 0.88, "高", C.teal);

    addCard(slide, 7.26, 5.68, 5.26, 0.92, {
      fillColor: C.navySoft,
      borderColor: C.navySoft,
    });
    addText(slide, "一句话归纳：CSS 现在最强的不是“天花板效率”，而是“效率、稳定性、纹理兼容性与规模潜力”一起出现。", {
      x: 7.58,
      y: 5.96,
      w: 4.64,
      h: 0.32,
      fontSize: 12.5,
      color: C.white,
      bold: true,
      align: "center",
    });
    addFooter(slide, "综合证据：[1][3][4][5][6]。成熟度判断为作者归纳。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "Process window", "关键工艺旋钮与失效模式", "做 CSS 的重点不是把设备搭起来，而是把窗口守住。", page);
    const knobs = [
      { x: 0.82, y: 1.8, color: C.teal, title: "有机源组成", low: "偏低：转化不完全", ok: "合适：带隙稳定", high: "偏高：相分离/漂移" },
      { x: 4.26, y: 1.8, color: C.blue, title: "源温与供料强度", low: "偏低：到达量不足", ok: "合适：供料平稳", high: "偏高：副反应/分解" },
      { x: 7.7, y: 1.8, color: C.amber, title: "基底温度", low: "偏低：晶化不足", ok: "合适：反应前沿推进", high: "偏高：重蒸发/损伤" },
      { x: 2.54, y: 4.26, color: C.rose, title: "压强与 gap", low: "偏低：设备负担增大", ok: "合适：近场传质有效", high: "偏高：输运变钝化" },
      { x: 5.98, y: 4.26, color: C.green, title: "表面/骨架状态", low: "偏差：核化与反应不均", ok: "合适：均匀转化", high: "失控：二次相与 pinhole" },
    ];
    knobs.forEach((knob) => {
      addCard(slide, knob.x, knob.y, 2.82, 1.82, {
        fillColor: C.white,
        borderColor: knob.color,
        borderWidth: 1.2,
        topBarColor: knob.color,
      });
      addText(slide, knob.title, {
        x: knob.x + 0.16,
        y: knob.y + 0.18,
        w: 2.5,
        h: 0.22,
        fontSize: 12.8,
        bold: true,
        color: C.ink,
        align: "center",
      });
      addText(slide, knob.low, {
        x: knob.x + 0.2,
        y: knob.y + 0.56,
        w: 2.38,
        h: 0.2,
        fontSize: 10.8,
        color: C.muted,
      });
      addText(slide, knob.ok, {
        x: knob.x + 0.2,
        y: knob.y + 0.92,
        w: 2.38,
        h: 0.2,
        fontSize: 10.8,
        color: C.navy,
        bold: true,
      });
      addText(slide, knob.high, {
        x: knob.x + 0.2,
        y: knob.y + 1.28,
        w: 2.38,
        h: 0.2,
        fontSize: 10.8,
        color: C.muted,
      });
    });
    addCard(slide, 9.18, 4.26, 3.34, 1.82, {
      fillColor: C.navySoft,
      borderColor: C.navySoft,
    });
    addText(slide, "最容易的误判", {
      x: 9.46,
      y: 4.5,
      w: 1.8,
      h: 0.22,
      fontSize: 13,
      color: C.teal,
      bold: true,
    });
    addText(slide, "只盯蒸发速率，不盯反应前沿。\n对钙钛矿 CSS 来说，后者往往更决定成败。", {
      x: 9.44,
      y: 4.92,
      w: 2.82,
      h: 0.66,
      fontSize: 12.6,
      color: C.white,
      bold: true,
      align: "center",
      valign: "mid",
    });
    addFooter(slide, "风险与窗口判断主要基于 [1][2][4][6] 的工艺描述与结果归纳。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    slide.background = { color: C.navy };
    slide.addShape(pptx.ShapeType.ellipse, {
      x: 9.1,
      y: 0.2,
      w: 3.6,
      h: 3.6,
      line: { color: C.teal, transparency: 100 },
      fill: { color: C.teal, transparency: 88 },
    });
    addText(slide, "Conclusion", {
      x: 0.78,
      y: 0.74,
      w: 1.6,
      h: 0.18,
      fontSize: 10.5,
      color: C.teal,
      bold: true,
    });
    addText(slide, "我的结论：\nCSS 值得做，但要按“工艺平台”来做", {
      x: 0.78,
      y: 1.14,
      w: 6.4,
      h: 0.92,
      fontSize: 26,
      color: C.white,
      bold: true,
    });
    addBulletList(slide, 0.88, 2.46, 6.1, [
      "如果目标是溶剂自由、大面积、真空线兼容与纹理硅串联，CSS 很有吸引力。",
      "如果目标是最快拿到实验室单结纪录，CSS 目前还不是最直接的路径。",
      "最应该投入的不是“再多加一个热源”，而是 source chemistry、反应动力学与在线过程窗口控制。",
    ], {
      bulletColor: C.teal,
      fontSize: 14,
      lineGap: 0.92,
      color: "D4D9E6",
    });
    addCard(slide, 7.84, 1.5, 4.44, 4.6, {
      fillColor: "111A2F",
      borderColor: C.teal,
      borderWidth: 1.2,
      topBarColor: C.teal,
    });
    addText(slide, "更适合 CSS 的场景", {
      x: 8.1,
      y: 1.82,
      w: 1.96,
      h: 0.22,
      fontSize: 14.5,
      bold: true,
      color: C.white,
    });
    addBulletList(slide, 8.1, 2.28, 3.72, [
      "宽带隙 / tandem 前电池",
      "纹理硅兼容路线",
      "多基底同时处理",
      "强调材料利用率与稳定性的 pilot line",
    ], {
      bulletColor: C.amber,
      fontSize: 12.5,
      lineGap: 0.72,
      color: "D4D9E6",
    });
    addText(slide, "不宜直接期待", {
      x: 8.1,
      y: 4.62,
      w: 1.6,
      h: 0.2,
      fontSize: 12.8,
      color: C.teal,
      bold: true,
    });
    addText(slide, "“只靠设备升级就自然追平最优解法纪录效率”", {
      x: 8.1,
      y: 4.96,
      w: 3.84,
      h: 0.36,
      fontSize: 13.4,
      color: C.white,
      bold: true,
      align: "center",
      valign: "mid",
    });
    addFooter(slide, "本页为作者基于 [1][4][6] 的综合判断；原始数据与文献见最后一页。");
    page += 1;
  }

  {
    const slide = pptx.addSlide();
    addSectionHeader(slide, "References", "参考文献", "正文引用编号与这里一一对应。", page);
    const refs = [
      "[1] Rodkey N., Gomar-Fernández I., Ventosinos F., Roldán-Carmona C., Koster L. J. A., Bolink H. J. Close-Space Sublimation as a Scalable Method for Perovskite Solar Cells. ACS Energy Letters, 2024. DOI: 10.1021/acsenergylett.3c02794.",
      "[2] Martínez-Falomir G. G., Lopez-Lazcano C. A., Almaral-Sánchez J. L. Pressure effect on MAPbBr3 perovskite films deposited by close space sublimation for PIN diode and its possible application in radiation detector. Materials Science in Semiconductor Processing, 2020. DOI: 10.1016/j.mssp.2020.104965.",
      "[3] Ihrenberger J., Roux F., Lédée F., Emieux F., Anglade C., Lemercier T., Lorin G., Verilhac J.-M., Gros-d’Aillon E., Grenet L. Solution-Free Growth of CsPbBr3 Perovskite Films Using a Fast and Scalable Close Space Sublimation Method. Crystal Growth & Design, 2024. DOI: 10.1021/acs.cgd.4c00249.",
      "[4] Gomar-Fernández I., Gil-Escrig L., Rodkey N., Ventosinos F., Senno M., Roldán-Carmona C., Held V., Sessolo M., Bolink H. J. Large-area close-space sublimation enables the fabrication of efficient and stable perovskite solar cells. EES Solar, 2025. DOI: 10.1039/D5EL00145E.",
      "[5] Wang C., Zhao Y., Ma T., An Y., He R., Zhu J., Chen C., Ren S., Fu F., Zhao D., Li X. A universal close-space annealing strategy towards high-quality perovskite absorbers enabling efficient all-perovskite tandem solar cells. Nature Energy, 2022. DOI: 10.1038/s41560-022-01076-9.",
      "[6] Diercks A., Chozas-Barrientos S., Gil-Escrig L., Gomar-Fernández I., Roldán-Carmona C., Rodkey N., Zhao T., Petermann J., Senno M., Held V., Carroy P., Muñoz D., Fassl P., Sessolo M., Paetzold U. W., Bolink H. J. Close Space Sublimation as a Versatile Deposition Process for Efficient Perovskite Silicon Tandem Solar Cells. Nature Energy, 2026（KITopen 预印本记录）. DOI: 10.5445/IR/1000192146.",
    ];
    refs.forEach((ref, idx) => {
      addCard(slide, 0.86, 1.72 + idx * 0.82, 11.92, 0.66, {
        fillColor: idx % 2 === 0 ? C.white : "F9FAFC",
        borderColor: C.border,
      });
      addText(slide, ref, {
        x: 1.08,
        y: 1.88 + idx * 0.82,
        w: 11.44,
        h: 0.34,
        fontSize: 10.1,
        color: C.ink,
        valign: "mid",
      });
    });
  }
}

fs.mkdirSync(outputDir, { recursive: true });
makeSlides();

pptx.writeFile({ fileName: outputFile }).then(() => {
  console.log(`PPT generated: ${outputFile}`);
}).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
