# finhot — 金融保险圈资讯 Skill

基于 AIHOT 架构改造的金融保险私募板块信息聚合 Skill。**无需自建后端**，直接调用多个免费公开数据源，在客户端侧聚合、去重、分类后输出中文 markdown 简报。

## 架构

```
用户提问
  ↓
SKILL.md 路由逻辑
  ↓
┌─────────────────────────────────────────┐
│ 数据源优先级（自动选择，无需用户关心）      │
│                                         │
│ 🔴 neodata-financial-search  ← 第一优先 │
│    金融保险政策、监管动态、行业新闻        │
│                                         │
│ 🟡 westock-data              ← 第二优先 │
│    保险公司/银行个股公告、研报评级         │
│                                         │
│ 🟢 RSS 公开源                ← 第三优先 │
│    财新/华尔街见闻/36氪/财联社/深交所      │
│                                         │
│ 🔵 Kimi WebBridge            ← 第四优先 │
│    需要 JS 渲染的站点，扩展补充           │
└─────────────────────────────────────────┘
  ↓
客户端侧聚合：去重 → 分类五类 → 排序
  ↓
中文 Markdown 简报输出
```

### 五类分类体系

| 分类 | 中文 | 典型内容 |
|---|---|---|
| `regulatory` | 监管政策 | 国家金融监管总局/证监会/央行发文 |
| `products` | 产品发布/更新 | 新保险产品、银行理财、基金发行 |
| `industry` | 行业动态 | 险企人事变动、并购、业绩 |
| `research` | 研究报告 | 券商研报、行业白皮书 |
| `insights` | 技巧与观点 | 从业者观点、展业经验 |

## 文件结构

```
finhot/
├── SKILL.md                          # Skill 主文件（路由逻辑 + 数据源 + 输出格式）
├── README.md                          # 本文件
├── meta.json                          # Skill 元数据
├── install.sh                         # 一行安装脚本
├── .gitignore
├── LICENSE
└── scripts/
    ├── rss_fetcher.py                 # RSS 数据采集器（feedparser）
    ├── daily_generator.py             # 日报生成器（聚合 → 五类 → 日报 JSON/MD）
    ├── fetch_all.py                   # 全量采集入口（RSS + WebBridge 合并）
    ├── webbridge_fetcher.py           # WebBridge 采集模块
    └── webbridge_sources.json         # WebBridge 信息源配置
```

## 快速开始

### 一行安装（Skill 环境）

```bash
curl -fsSL https://raw.githubusercontent.com/zycyyyya/finhot/main/install.sh | bash
```

### 手动安装

1. 克隆仓库到 Skill 目录：
```bash
git clone https://github.com/zycyyyya/finhot.git ~/.workbuddy/skills/finhot
```

2. （可选）安装 Python 依赖用于脚本模式：
```bash
pip install feedparser
```

3. 重启 Agent，即可使用

### 使用示例

| 你说 | Skill 做什么 |
|---|---|
| "今天金融圈有什么" | neodata 查询 → 分类输出 |
| "金融日报" | 多源聚合 → 日报生成 |
| "银保监会最近发了什么" | neodata 关键词查询 |
| "平安保险最近公告" | westock-data 个股查询 |
| "保险板块资金流向" | westock-data asfund |
| "最近一周监管政策" | neodata + RSS 监管源 |

### 脚本模式（离线采集 + 日报生成）

```bash
# Step 1: 采集 RSS 数据
python scripts/rss_fetcher.py --output ./data --days 1

# Step 2: 生成日报
python scripts/daily_generator.py --input ./data --output ./daily --markdown

# 一步到位：全量采集
python scripts/fetch_all.py --output ./data --days 1 --with-webbridge
```

## 数据源说明

### neodata-financial-search（第一优先）
- 自然语言查询金融保险数据
- 覆盖股票、基金、宏观、行业新闻
- 无需 API Key

### westock-data（第二优先）
- 腾讯自选股结构化行情数据
- 覆盖个股公告、研报评级、资金流向
- 支持 A股/港股/美股

### RSS 公开源（第三优先）
- 通过 RSSHub 镜像站聚合财新、华尔街见闻、第一财经、36氪、财联社、深交所等
- **注意**：rsshub.app 在国内不可达，需使用镜像站（如 `rsshub.liumingye.cn`）
- 银保监会/证监会/央行等政府站 RSSHub 路由已下线，监管动态改由 neodata 覆盖
- 数据延迟通常 5-30 分钟

### Kimi WebBridge（第四优先）
- 通过浏览器 daemon 抓取 JS 渲染站点
- 配置在 `scripts/webbridge_sources.json`
- 需要额外安装 Kimi WebBridge

## 与 AIHOT 的区别

| 维度 | AIHOT | finhot |
|---|---|---|
| 领域 | AI 行业 | 金融保险 |
| 后端 | 自建 API 服务器 | 无后端，客户端多源聚合 |
| 数据源 | 自有爬虫 + DB | neodata + westock-data + RSS + WebBridge |
| 分类 | 模型/产品/行业/论文/技巧 | 监管/产品/行业/研究/观点 |
| 部署 | 需要服务器 | 零部署 |

## License

MIT
