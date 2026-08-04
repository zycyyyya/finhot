<p align="center">
  <strong>finhot</strong><br/>
  <em>金融保险圈每日精选资讯引擎</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.3.0-blue" alt="version"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license"/>
  <img src="https://img.shields.io/badge/data_sources-9_RSS_→_多源容错-orange" alt="sources"/>
  <img src="https://img.shields.io/badge/AI-SenseNova_DeeepSeek_V4-purple" alt="AI"/>
</p>

<p align="center">
  <strong>灵感来源 <a href="https://github.com/virxcase/aihot">AIHOT</a>（AI 圈） → 金融保险圈版</strong>
</p>

---

## 它是什么

finhot 是一个面向保险运营、二级市场投教和私募销售运营从业者的自动资讯聚合与分析引擎。每日从多个公开信源采集行业动态，经过去重、来源分层、AI 证据化分析和三场景独立评分后，输出结构化数据驱动静态前端站点 [finhot-web](https://github.com/zycyyyya/finhot-web)。

核心能力：

- **多源采集** — 9 条 RSS（RSSHub 多实例容错 + 直连 RSS），单源自适应 30→50 条，触顶监控
- **AI Schema 2.0** — SenseNova DeepSeek-v4-Flash 两段式生成，所有结论绑定原文证据 ID，无效结论自动剔除
- **三场景评分** — 保险运营 / 私募销售运营 / 二级市场投教独立 0-100 适配度
- **业务选稿** — 唯一主场景分配 + 24 条场景配额精选（保险 6 / 私募 7 / 投教 11）
- **事件聚类** — 中文双字 + 主题词相似度聚类，跨日稳定事件 ID，120 天持久化
- **来源健康** — 逐来源可用/失败/陈旧/触顶状态，覆盖率自动监控，失败不发布
- **质量门** — URL 安全、时间校验、标题去重、近似标题去重、字段完整性、证据悬空检测
- **自动运行** — GitHub Actions 北京时间 08:15 主运行 + 12:17/16:19/20:21 错峰保底
- **自动告警** — 连续失败、低覆盖率、数据陈旧、调度延迟、连续触顶和 AI 回退均自动创建 Issue

## 架构

```
RSSHub 多实例 + 直连 RSS (9 源)
        │
        ▼
  采集与清洗（URL 规范化 / 标题去重 / 时间校验 / 乱码过滤）
        │
        ▼
  AI Schema 2.0 分析（两段 LLM，独立容错，429 退避重试）
        │
        ▼
  三场景评分 + 业务选稿（唯一主场景 / 场景配额精选）
        │
        ▼
  事件聚类 + 证据校验（稳定事件 ID / 历史证据库 / 证据悬空检测）
        │
        ▼
  data.js → GitHub Pages 纯静态部署
```

## 数据源

| 源 | 分类 | 采集方式 | 来源层级 |
|---|---|---|---|
| 中国证监会 | 监管 | RSSHub | S0 原始源 |
| 深圳证券交易所 | 监管 | RSSHub | S0 原始源 |
| 财新网 | 行业 | RSSHub | S2 专业媒体 |
| 华尔街见闻 | 行业 | RSSHub | S2 专业媒体 |
| 第一财经 | 行业 | RSSHub | S2 专业媒体 |
| 财联社快讯 | 行业 | RSSHub | S3 快讯线索 |
| 财联社深度 | 研究 | RSSHub | S2 专业媒体 |
| 36氪 | 观点 | RSSHub | S3 观点线索 |
| 英为财情 | 行业 | Direct RSS | S2 专业媒体 |

> RSSHub 实例：`rsshub.rssforever.com` 优先，`rsshub-balancer.virworks.moe` 兜底；自动检测陈旧缓存并回退。

## AI 分析说明

- **模型**：SenseNova `deepseek-v4-flash`（OpenAI 兼容接口）
- **调用策略**：两段分别生成（摘要+趋势 / 话术），独立容错，429 限流时 10/20 秒退避重试
- **校验层**：结构校验、枚举校验、长度校验、证据 ID 校验；无有效证据的结论自动剔除
- **回退机制**：任何一段失败时仅回退该段对应板块为规则分析，另一段成功结果保留
- **Cached 模式**：错峰保底运行复用上次 AI 内容，但仍执行字段校验和错误清理

## 文件结构

```
finhot/
├── scripts/
│   ├── fetch.js           # 主采集引擎（RSS 抓取 + AI 分析 + 数据输出）
│   ├── core.js            # 共享安全、质量和去重模块
│   ├── analysis.js        # AI 分析、评分、事件聚类、业务选稿
│   ├── health.js          # 来源健康监控与发布质量门
│   ├── history.js         # 90 天历史证据库 + 120 天事件库
│   ├── alerts.js          # 自动告警（GitHub Issues）
│   ├── schedule-watch.js  # 调度延迟监控
│   ├── health-summary.js  # Actions 运行摘要
│   └── health-view.js     # 关于页健康状态
├── tests/                 # 6 组单元测试（core / analysis / health / history / alerts / frontend）
├── .github/workflows/
│   ├── update.yml         # 主采集 workflow（4 个 cron + 手动触发）
│   └── watchdog.yml       # 独立调度监控
├── data/
│   ├── history.json       # 历史证据库（≤5,000 条 / 90 天）
│   ├── events.json        # 持久事件库（≤1,000 个 / 120 天）
│   └── alert-state.json   # 告警去重状态
├── data.js                # 前端数据（150 条精选资讯）
├── index.html             # 首页（五栏目 + 双层筛选）
├── daily.html             # AI 日报页
├── about.html             # 关于页（含数据健康状态）
├── styles.css             # 全站深色主题样式
└── package.json           # Node.js 依赖与测试脚本
```

## 本地运行

```bash
npm ci
npm run fetch    # 采集 + AI 分析 + 生成 data.js
npm test         # 运行全部测试
npm run check    # 语法检查 + 全部测试
```

环境变量：

| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | SenseNova API 密钥（AI 分析必需） |
| `FINHOT_TRIGGER_EVENT` | GitHub Actions 触发事件 |
| `FINHOT_SCHEDULE` | 当前 cron 表达式 |
| `FINHOT_ANALYSIS_MODE` | `full` 或 `cached` |

## License

MIT
