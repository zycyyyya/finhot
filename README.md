<p align="center">
  <strong>finhot</strong><br/>
  <em>金融保险圈资讯查询 Skill</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.3.0-blue" alt="version"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license"/>
  <img src="https://img.shields.io/badge/type-Agent_Skill-orange" alt="type"/>
  <img src="https://img.shields.io/badge/runtime-Python_3-lightgrey" alt="runtime"/>
</p>

---

## 它是什么

finhot 是一个面向金融、保险和监管资讯查询的 Agent Skill。它根据用户意图在结构化金融数据、公开 RSS 和可选 WebBridge 信息源之间选择查询路径，在客户端完成聚合、去重、分类和中文 Markdown 简报生成，无需自建后端。

本仓库与 [finhot-web](https://github.com/zycyyyya/finhot-web) 相互独立：

- **finhot**：供 Agent 调用的资讯查询 Skill，并提供可选的 Python 离线采集与日报生成脚本
- **finhot-web**：集成 Node.js 自动采集、AI 分析、数据质量门和 GitHub Pages 展示的静态资讯站点

## 核心能力

- **意图路由**：区分默认精选、日报、全量、关键词、公司公告及行情查询
- **可信分层**：S0 权威原始源、S1 结构化数据源、S2 专业财经媒体、S3 快讯/观点线索
- **多源容错**：结构化查询、RSSHub 多实例、直连 RSS 与可选 WebBridge 扩展
- **五类整理**：监管政策、产品发布/更新、行业动态、研究报告、技巧与观点
- **从业价值评分**：按行业相关性、来源权威性、业务影响、时效性、内容深度和可行动性评估
- **可追溯输出**：保留原文 URL，不以训练数据替代实时事实，不把摘要冒充原文
- **北京时间日报**：可按北京时间自然日筛选并生成 JSON 或 Markdown 日报
- **安全与完整性校验**：校验 URL 协议、必填字段、分类枚举、时间格式和危险文本片段

## 查询策略

| 用户意图 | 默认处理方式 |
|---|---|
| 今天金融圈、最近保险动态等宽问题 | 优先使用结构化金融搜索，返回精选结果 |
| 明确要求“日报” | 聚合结构化数据、RSS 与补充来源，生成五类日报 |
| 明确要求“全部/完整/全量” | 扩大查询范围并执行多源补充 |
| 公司公告、研报、资金流向 | 使用对应的结构化证券数据能力 |
| 监管原文 | 优先追溯监管机构、交易所等 S0 原始出处 |
| 常规来源覆盖不足 | 可选用 WebBridge 扩展自定义站点 |

完整触发规则、数据源优先级、输出格式和降级策略见 [`SKILL.md`](./SKILL.md)。

## 可选 Python 工具

仓库提供离线采集和日报生成脚本，用于没有完整 Skill 运行环境时的补充工作流。

```bash
python -m venv .venv
.venv/Scripts/python -m pip install feedparser

# RSS 采集
.venv/Scripts/python scripts/rss_fetcher.py --output ./data --days 1

# RSS + 可选 WebBridge 合并采集
.venv/Scripts/python scripts/fetch_all.py --output ./data --days 1

# 生成日报 JSON 和 Markdown
.venv/Scripts/python scripts/daily_generator.py --input ./data --output ./daily
```

在 Linux/macOS 中将 `.venv/Scripts/python` 替换为 `.venv/bin/python`。

## 数据源

Python RSS 采集器当前配置 9 个源：

| 来源 | 方式 | 默认分类 |
|---|---|---|
| 深交所公告 | RSSHub | 监管政策 |
| 华尔街见闻 | RSSHub | 行业动态 |
| 财新网 | RSSHub | 行业动态 |
| 第一财经 | RSSHub | 行业动态 |
| 财联社深度 | RSSHub | 研究报告 |
| 财联社电报 | RSSHub | 行业动态 |
| 36氪快讯 | RSSHub | 技巧与观点 |
| 英为财情新闻 | Direct RSS | 行业动态 |
| 英为财情技术分析 | Direct RSS | 研究报告 |

RSSHub 按 `rsshub.rssforever.com`、`rsshub.liumingye.cn` 顺序容错，并在 feed 整体超过 7 天未更新时尝试下一实例。

## 文件结构

```text
finhot/
├── SKILL.md                         # Agent 触发、路由、查询与输出规范
├── meta.json                        # Skill 元数据与版本
├── install.sh                       # 安装到用户级或项目级 Skill 目录
├── scripts/
│   ├── rss_fetcher.py               # RSS 采集、时间过滤与基础分类
│   ├── fetch_all.py                 # RSS + WebBridge 合并入口
│   ├── daily_generator.py           # 北京时间日报 JSON/Markdown 生成
│   ├── webbridge_fetcher.py         # 可选 WebBridge 采集器
│   └── webbridge_sources.json       # 自定义来源配置
└── tests/
    └── test_data_integrity.py       # URL、字段、时间和日报完整性测试
```

## 安装

```bash
# 用户级安装（默认 ~/.workbuddy/skills/finhot）
bash install.sh

# 指定安装目录
bash install.sh /path/to/skills/finhot
```

安装脚本只复制 Skill 文件，不会安装 Python 第三方依赖。仅在使用离线 RSS 脚本时需要单独安装 `feedparser`。

## 测试

```bash
python -m unittest discover -s tests -v
```

## License

MIT
