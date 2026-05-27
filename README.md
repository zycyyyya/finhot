<p align="center">
  <strong>finhot</strong><br/>
  <em>金融保险圈每日资讯 — 一句话拿简报</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.1.0-blue" alt="version"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license"/>
  <img src="https://img.shields.io/badge/data_sources-11_RSS_%2B_neodata_%2B_westock-orange" alt="sources"/>
  <img src="https://img.shields.io/badge/zero_backend-✓-success" alt="zero backend"/>
</p>

<p align="center">
  <strong>灵感来源 <a href="https://github.com/virxcase/aihot">AIHOT</a>（AI 圈） → 金融保险圈版</strong>
</p>

---

## 它是什么

finhot 是一个 Agent Skill（SKILL.md 格式），安装后你可以直接对 AI 说：

> *"今天金融圈有什么"* → 自动拉取最新资讯，分类输出简报
> *"金融日报"* → 多源聚合，生成分版块的日报
> *"平安保险最近公告"* → 结构化查询个股研报和公告

**不需要自建服务器、不需要 API Key、零部署成本。** Skill 直接在客户端调多个公开数据源，聚合后输出中文 Markdown。

## 架构

```
用户自然语言提问
        │
        ▼
  ┌─ neodata-financial-search ── 金融保险全品类自然语言查询
  │
  ├─ westock-data ──────────── 个股公告 / 研报评级 / 资金流向
  │
  ├─ RSS 聚合 ──────────────── 财新 / 华尔街见闻 / 第一财经 / 36氪 / 财联社 / 深交所
  │
  └─ Kimi WebBridge ────────── JS 渲染站点扩展
        │
        ▼
  客户端侧：去重 → 五类分类 → 时间排序 → Markdown 简报
```

## 五类分类

| 分类 | 覆盖内容 |
|:---:|---|
| 🏛 监管政策 | 国家金融监管总局 / 证监会 / 央行发文 |
| 📦 产品发布 | 新保险产品、银行理财、基金发行 |
| 📊 行业动态 | 险企人事变动、并购、业绩、市场数据 |
| 📑 研究报告 | 券商研报、行业白皮书、学术研究 |
| 💡 观点洞察 | 从业者观点、展业经验、合规提醒 |

## 快速安装

```bash
# 一键安装到 Skill 目录
curl -fsSL https://raw.githubusercontent.com/zycyyyya/finhot/main/install.sh | bash
```

或手动安装：

```bash
git clone https://github.com/zycyyyya/finhot.git ~/.workbuddy/skills/finhot
```

重启 Agent 后即可使用。

## 使用示例

| 你说 | Skill 响应 |
|---|---|
| 今天金融圈有什么 | neodata 查询 → 分类输出当日热点 |
| 金融日报 | 多源聚合 → 生成分版块日报 |
| 银保监会最近发了什么 | neodata 关键词查询 + RSS 补充 |
| 平安保险最近公告 | westock-data 个股研报 + 公告 |
| 保险板块资金流向 | westock-data 板块资金查询 |
| 最近一周监管政策 | neodata + RSS 回溯查询 |
| 看下精选条目 | neodata 精选模式 |

## RSS 数据源（2026-05-27 实测验证）

通过 RSSHub 镜像站聚合，覆盖 11 个实测可用源：

| 源 | 分类 | 条目 |
|---|---|---|
| 深交所公告 | 监管 | 20+ |
| 华尔街见闻 | 行业 | 30+ |
| 财新最新 | 行业 | 19 |
| 财新文章 | 行业 | 16 |
| 第一财经快讯 | 行业 | 实时 |
| 第一财经新闻 | 行业 | 20 |
| 财联社深度 | 研究 | 30 |
| 观察者网头条 | 研究 | 20 |
| 36氪快讯 | 观点 | 实时 |
| 36氪热榜 | 观点 | 8 |
| 财联社电报 | 观点 | 实时 |

> 镜像站 `rsshub.liumingye.cn`，rsshub.app 在国内不可达。

## 文件结构

```
finhot/
├── SKILL.md                    # Skill 主文件
├── README.md                   # 本文件
├── meta.json                   # Skill 元数据
├── install.sh                  # 一行安装脚本
└── scripts/
    ├── rss_fetcher.py          # RSS 采集器
    ├── daily_generator.py      # 日报生成器
    ├── fetch_all.py            # 全量采集入口
    ├── webbridge_fetcher.py    # WebBridge 模块
    └── webbridge_sources.json  # WebBridge 源配置
```

## 可选：离线脚本模式

环境有 Python + feedparser 时，支持离线采集 + 日报生成：

```bash
pip install feedparser

# 采集 + 生成日报
python scripts/rss_fetcher.py --output ./data --days 1
python scripts/daily_generator.py --input ./data --output ./daily --markdown
```

## License

MIT
