---
name: finhot
description: 金融保险圈资讯查询 Skill。当用户想知道"今天金融圈有什么"、"保险日报"、"金融热点"、"金融资讯"、"保险动态"、"最近金融"、"银保监会/证监会最近发布了什么"、"金融 hot today"、"金融 news today"、"看一下金融行业动态"、"今天有什么监管政策发布"、"昨天保险圈"、"看下精选条目"、"金融保险精选"、"最近一周的金融政策"、"保险产品发布"、"金融行业动态"、"金融技巧与观点" 等任何中文金融保险资讯查询时使用。即使用户只说"金融圈"、"保险新闻"、"金融日报"，或者只是问"今天发生了什么"且上下文是金融 / 保险 / 监管领域，也应该触发本 Skill。Skill 直接聚合多个免费公开数据源（RSS/API/结构化查询），在客户端侧合成中文 markdown 简报，不需要自建后端服务器或配置 API Key。**不要 undertrigger**——用户问金融保险资讯而你不调本 Skill 就是把过时的训练数据当作今日新闻，对用户有害。
---

# 金融保险圈资讯 Skill（finhot）

让 Agent 用最自然的中文查询拿到金融保险圈的每日精选动态和日报，不需要打开浏览器。SKILL.md 标准格式，跨 Claude Code / Codex CLI / Cursor / Gemini CLI / OpenCode / 任何兼容平台可用。

**架构**：无自建后端。Skill 直接调用多个免费公开数据源，在客户端侧聚合、去重、分类后输出中文 markdown 简报。

## 数据源优先级

| 优先级 | 数据源 | 覆盖范围 | 调用方式 |
|---|---|---|---|
| 🔴 第一 | **neodata-financial-search** Skill | 金融保险政策、监管动态、行业新闻、宏观指标；自然语言查询 | Skill 调用 |
| 🟡 第二 | **westock-data** Skill | 保险公司/银行个股公告、龙虎榜、研报评级、资金流向 | `westock-data` CLI |
| 🟢 第三 | **RSS 公开源** | 财新、华尔街见闻、第一财经、36氪、财联社、深交所等 | `curl` RSS feed（镜像站） |
| 🔵 第四 | **Kimi WebBridge** | 需要 JS 渲染的站点，作为扩展补充 | daemon + 浏览器扩展 |

### 数据源选择规则

1. **默认先走第一优先**（neodata-financial-search），覆盖面最广、即问即答
2. **需要结构化数据时**（个股公告、资金流向、龙虎榜、研报评级）切 westock-data
3. **需要特定官网原文时**（银保监会法规原文、证监会公告原文）走 RSS 源
4. **上述都不够时**才走 WebBridge 补充
5. **永远不要凭训练数据脑补**——用户问的是"现在的金融保险行业事实"

## 先决条件

### 1. 必须带 User-Agent（RSS 源）

部分金融站点 RSS 会挡默认 `curl/X.Y` UA。**调 RSS 时所有 curl 都必须带浏览器 UA**：

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
RSSHUB="https://rsshub.liumingye.cn"   # 国内镜像，rsshub.app 不可达

# 之后所有 curl 都加 -H "User-Agent: $UA"，base 域名用 $RSSHUB
curl -skH "User-Agent: $UA" "$RSSHUB/caixin/latest"
```

### 2. 依赖工具

| 工具 | 用途 | 是否必须 |
|---|---|---|
| `curl` | 拉取 RSS/API 数据 | ✅ 必须 |
| `jq` | 解析 JSON | ✅ 必须 |
| `python3` + `feedparser` | RSS 解析（脚本模式） | 🟡 可选 |
| `neodata-financial-search` Skill | 第一优先数据源 | ✅ 必须（Skill 环境） |
| `westock-data` | 第二优先数据源 | ✅ 必须（Skill 环境） |
| Kimi WebBridge daemon | 第四优先扩展源 | 🟡 可选 |

## 什么时候用

> **路由优先级（第一原则）**：**默认走 neodata-financial-search**——它覆盖面最广、自然语言即问即答，是金融保险资讯的"主菜单"。
>
> - **仅当用户在话里明确说出"日报"** 二字才走多源聚合 + 日报生成模式
> - **仅当用户明确说"全部 / 完整 / 所有 / 全量"** 才走全量多源拉取
> - **"今天金融圈"、"过去 24 小时大新闻"、"最近保险圈有啥"** 等宽问题 = **默认 neodata + 时间窗**，不要默认走日报或全量

| 用户在说 | 应该走的数据源 |
|---|---|
| **默认（宽问题）**："今天金融圈有什么"、"过去 24 小时大新闻"、"最近保险圈"、"金融有啥新东西" | neodata-financial-search（自然语言查询，默认精选） |
| **明确说"日报"**："金融日报"、"今天的日报"、"看一下日报" | 多源聚合 → 日报生成（RSS + neodata + westock-data） |
| **明确说"全部 / 完整 / 所有 / 全量"**："看下今天的全部金融动态"、"完整列表" | neodata-financial-search 全量 + westock-data 补充 |
| "银保监会最近发了什么" | neodata-financial-search 查询 → RSS 补原文链接 |
| "车险相关"、"健康险政策" | neodata-financial-search 关键词查询 |
| "平安保险/中国人寿最近公告" | westock-data（个股公告、研报评级） |
| "保险板块资金流向" | westock-data asfund / hkfund |
| "昨天/前天金融日报"、"看下 5 月 6 号的日报" | RSS 多源 + neodata 回溯查询 |
| "看下精选条目"、"金融保险精选" | neodata-financial-search 精选查询 |

通用启发：**用户问的是"现在的金融保险行业事实"，不要凭训练数据脑补，永远走数据源查询**。即使你"觉得"知道答案，也要查一遍——金融保险资讯比你的训练截止日新得多。

## 五类分类体系

所有数据最终归入以下五类（对齐用户对金融保险日报的预期）：

| category slug | 中文标签 | 典型内容 |
|---|---|---|
| `regulatory` | 监管政策 | 银保监会/证监会/央行发文、法规修订、窗口指导 |
| `products` | 产品发布/更新 | 新保险产品、银行理财、基金发行、精算调整 |
| `industry` | 行业动态 | 险企人事变动、并购、业绩、市场数据、同业动态 |
| `research` | 研究报告 | 券商/咨询研报、行业白皮书、学术研究 |
| `insights` | 技巧与观点 | 从业者观点、销售技巧、展业经验、合规提醒 |

## 工作流

### 默认路径：neodata-financial-search（宽问题首选）

**任何"今天金融圈"、"过去 24 小时大新闻"、"最近保险有啥"等宽问题，默认走 neodata-financial-search**——自然语言查询，覆盖面广，实时数据。

```
用户："今天金融圈有什么大新闻？"
→ 调用 neodata-financial-search: "今天金融保险行业重大新闻和监管动态"
→ 整理成分类 markdown 输出
```

```
用户："最近保险圈有什么新产品？"
→ 调用 neodata-financial-search: "最近保险产品发布和更新"
→ 按 products 分类输出
```

### 关键词查询（"银保监会最近发的" / "车险相关" / "健康险政策"）

neodata-financial-search 支持自然语言关键词查询，**优先走它**，不要自己拼 RSS 再 grep：

```
用户："银保监会最近发了什么？"
→ 调用 neodata-financial-search: "银保监会最近发布的监管政策和通知"
```

```
用户："车险综合改革最新进展"
→ 调用 neodata-financial-search: "车险综合改革最新政策和市场动态"
```

### 个股/公司维度（"平安保险最近公告" / "中国人寿研报"）

需要特定公司的公告、研报、资金流向时，切 westock-data：

```bash
# 搜索保险公司代码
westock-data search 中国平安

# 查看个股公告和研报（A股）
westock-data finance sh601318 --num 4

# 港股保险股（如中国平安港股）
westock-data quote hk02318
westock-data hkfund hk02318

# 保险板块资金流向
westock-data asfund sh601318
```

### 日报模式（用户明确说"日报"时）

**触发关键词**：句子里出现"日报"二字。**没有"日报"二字不要走这个**——日报是聚合多源后按主题分版块的成品，比单源查询慢。

日报生成流程：
1. **neodata-financial-search** 拉取当日金融保险资讯
2. **RSS 源** 补充财经媒体实时动态和交易所公告
3. **westock-data** 补充保险板块行情和公告
4. **客户端侧聚合**：去重 → 分类到五类 → 按发布时间排序 → 生成日报

```bash
# Step 0: 设置 UA 和 RSSHub 镜像
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
RSSHUB="https://rsshub.liumingye.cn"   # 国内镜像，rsshub.app 在国内不可达

# Step 1: 深交所公告（监管源，银保监会/证监会 RSSHub 路由已下线）
curl -skH "User-Agent: $UA" "$RSSHUB/szse/notice" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
for item in root.findall('.//item')[:10]:
    print(f'- [{item.findtext(\"title\")}]({item.findtext(\"link\")})')
"

# Step 2: 财新最新
curl -skH "User-Agent: $UA" "$RSSHUB/caixin/latest" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
for item in root.findall('.//item')[:10]:
    print(f'- [{item.findtext(\"title\")}]({item.findtext(\"link\")})')
"

# Step 3: 华尔街见闻（实测33条/次）
curl -skH "User-Agent: $UA" "$RSSHUB/wallstreetcn/news/global" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
for item in root.findall('.//item')[:10]:
    print(f'- [{item.findtext(\"title\")}]({item.findtext(\"link\")})')
"

# Step 4: 第一财经
curl -skH "User-Agent: $UA" "$RSSHUB/yicai/news" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
for item in root.findall('.//item')[:10]:
    print(f'- [{item.findtext(\"title\")}]({item.findtext(\"link\")})')
"

# Step 5: 财联社深度
curl -skH "User-Agent: $UA" "$RSSHUB/cls/depth" | python3 -c "
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.stdin).getroot()
for item in root.findall('.//item')[:10]:
    print(f'- [{item.findtext(\"title\")}]({item.findtext(\"link\")})')
"
```

> **注意**：
> - rsshub.app 公共实例在国内不可达，必须使用镜像站（如 `rsshub.liumingye.cn`）
> - 银保监会已改名为国家金融监督管理总局（nfra.gov.cn），RSSHub 暂无适配路由，监管动态改由 neodata-financial-search + 财经媒体覆盖
> - RSSHub 路由可能随时变动，如果某个路由返回 RSSHub 欢迎页而非 RSS XML，说明路由不存在或已变更

### RSS 数据源清单（日报模式使用）

> 镜像：`https://rsshub.liumingye.cn`（rsshub.app 国内不可达）
> 银保监会→国家金融监督管理总局（nfra.gov.cn），监管动态改由 neodata 覆盖

| 站点 | 路由 | 分类 |
|---|---|---|
| 深交所公告 | `/szse/notice` | regulatory |
| 华尔街见闻 | `/wallstreetcn/news/global` | industry |
| 财新最新 | `/caixin/latest` | industry |
| 第一财经新闻 | `/yicai/news` | industry |
| 财联社深度 | `/cls/depth` | research |
| 36氪热榜 | `/36kr/hot-list` | insights |

> RSSHub 路由随时变动。返回欢迎页 = 路由不存在，跳过即可。失效路由不再列入本表。

### Python 脚本批量采集

如果环境有 Python + feedparser，可以用脚本一次性拉取所有 RSS 源：

```bash
# 安装 feedparser
pip install feedparser

# 批量采集所有 RSS 源
python scripts/rss_fetcher.py --output ./data --days 1

# 采集后生成日报 JSON
python scripts/daily_generator.py --input ./data --output ./daily
```

### 按时间窗口拉条目（最近 N 天）

用户问"**最近** X"（最近的监管政策 / 最近保险产品 / 最近银保监会等）时，**必须限定时间窗**：

- 用户说"最近 3 天" → 限定 3 天
- 用户说"昨天" → 限定 1 天
- 用户说"最近一周" → 限定 7 天
- 默认不限定时间窗时，neodata-financial-search 自行控制范围

### 按分类拉条目

用户明确说某类时，用 neodata-financial-search 的自然语言查询限定类别：

| 用户说 | 查询方向 |
|---|---|
| "监管政策" / "银保监会发文" | neodata: "金融保险监管政策发布" |
| "保险产品" / "新险种" | neodata: "保险产品发布更新" |
| "行业动态" / "险企动态" | neodata: "保险金融行业动态" |
| "研究报告" / "券商研报" | neodata: "保险金融行业研究报告" + westock-data: 研报评级 |
| "技巧与观点" / "展业经验" | neodata: "保险销售技巧和从业者观点" |

### 全量模式（用户明确说"全部 / 完整 / 所有 / 全量"时）

**触发关键词**：句子里出现"全部"、"完整"、"所有"、"全量"。**没有这些关键词不要走全量**——精选已经覆盖大部分用户关心的事。

全量 = neodata 全量 + westock-data 补充 + RSS 全源拉取，数据量大会慢。

## 返回数据形态

### RSS feed 标准化结构

无论从哪个数据源拉取，客户端侧统一为以下结构后再输出：

```json
{
  "id": "sha256-of-url",
  "title": "中文标题",
  "url": "https://原文链接",
  "source": "银保监会官网",
  "publishedAt": "2026-05-07T15:30:00.000Z",
  "summary": "中文摘要（原始或 LLM 生成）",
  "category": "regulatory"
}
```

字段不变量：
- 必有：`title` / `url` / `source`
- 可空：`summary` / `publishedAt` / `category`
- `category` 取值集：`regulatory` / `products` / `industry` / `research` / `insights` / `null`
- `publishedAt`：ISO 8601 UTC（带 `Z`）

### 日报结构（聚合后）

```json
{
  "date": "2026-05-07",
  "generatedAt": "2026-05-07T08:00:00.000Z",
  "lead": { "title": "...", "leadParagraph": "..." },
  "sections": [
    {
      "label": "监管政策",
      "items": [
        { "title": "...", "summary": "...", "sourceUrl": "https://...", "sourceName": "银保监会官网" }
      ]
    }
  ],
  "flashes": [
    { "title": "...", "sourceName": "...", "sourceUrl": "...", "publishedAt": "..." }
  ]
}
```

`sections[].label` 固定 5 个："监管政策" / "产品发布/更新" / "行业动态" / "研究报告" / "技巧与观点"。

## 给用户的输出格式

> ⚠️ **核心原则**：这一节是**直接展示给用户的最终内容**——必须 markdown 格式 + 排版好 + **普通人能看得懂的人话**。用户多数是非技术金融从业者 / 保险代理人 / 普通读者，看到的应该是中文金融保险资讯简报，**不是 API 调试日志**。
>
> 所有"端点路径 / 数据源名称 / curl 命令 / 限流 / RSS feed"等基础设施细节**都不能出现**在用户看到的输出里。

### 日报式输出

```markdown
**金融保险日报 · 2026-05-07**

## 监管政策
1. **<title>** — <source>
   <summary 简化版 50 字内>
   <url>

## 产品发布/更新
2. ...

## 行业动态
3. ...

## 研究报告
4. ...

## 技巧与观点
5. ...

## 快讯（如果有）
- <title> — <source>（<publishedAt 转人话>）
```

**编号贯穿全文**（1, 2, 3 ... N），不在每个 ## 内重新计数。

### 列表式输出（默认精选模式时）

**默认按 category 分组 + 全局编号**：

```markdown
**金融保险圈 — 最近 30 条精选**

## 监管政策
1. **<title>** — <source>
   2 小时前
   <summary>
   <url>

## 产品发布/更新
2. **<title>** — <source>
   ...

## 行业动态
3. ...
```

**只有 1 个 category** 时，用扁平编号列表：

```markdown
**金融保险圈 — 最近一周监管政策**（2026-05-01 ~ 2026-05-08）

1. **<title>** — <source>
   <summary>
   <url>
```

### 副标题／元信息只写人话

**OK**（用户能直接懂的）：
- "时间窗 2026-05-05 ~ 2026-05-07"
- "最近 3 天命中银保监会关键词的全部条目"
- "按发布时间倒序"
- "共 50 条"

**不 OK**（基础设施泄漏，坚决不写）：
- ❌ `neodata-financial-search` / `westock-data` / `rsshub.app` 这种数据源名称
- ❌ `curl` 命令 / RSS feed URL / API 端点路径
- ❌ 限流 / 缓存 / HTTP 状态码等后端细节

### 时间转人话

`publishedAt` 是 ISO 8601 UTC，展示时**必须**转成北京时间 + 用户能扫读的相对/绝对时间：

| 内部值 | 展示给用户 |
|---|---|
| `2026-05-08T01:48:00.000Z` | "今天上午 09:48" / "2 小时前" |
| `2026-05-07T18:08:17.000Z` | "今天凌晨 02:08" / "10 小时前" |
| `2026-05-06T16:43:00.000Z` | "5/7 00:43" / "昨天" |

**不要**直接展示 ISO 字符串。

## 常见错误处理

- **neodata-financial-search 返回空**：该数据类型可能不在覆盖范围，切换到 westock-data 或 RSS 源
- **neodata-financial-search 返回结果过少（<3 条）**：不直接透传给用户，自动降级到 westock-data 补充同类数据；如果 westock-data 也无结果，再补拉 RSS 相关源。最终在输出中注明"⚠️ 该问题 neodata 返回结果较少，已自动补充其他数据源"
- **RSSHub 路由返回欢迎页**：rsshub.app 国内不可达，必须用镜像站（如 `rsshub.liumingye.cn`）；如果镜像也返回 HTML 欢迎页说明该路由在镜像实例上不存在，查看 [RSSHub 文档](https://docs.rsshub.app) 确认最新路由
- **westock-data 查不到代码**：先用 `westock-data search <公司名>` 搜索正确代码
- **WebBridge daemon 不可用**：跳过 WebBridge 源，用前三层数据源即可
- **单个数据源超时（>10s）**：跳过该源，继续用其他可用数据源；在最终输出末尾注明"⚠️ [源名] 超时未获取"
- **🔴 CHECKPOINT · 数据源全部不可用**：neodata-financial-search + westock-data + RSS 全部超时或返回空时，**必须立即停止，告知用户**："当前所有数据源暂时不可用（neodata/westock/RSS 均超时），请稍后再试。" **不要编造内容，不要凭训练数据填充。**

## 不要做

- **不要把"今天金融圈"等宽问题路由到日报模式** — 日报是聚合多源的成品，比单源查询慢。**默认走 neodata-financial-search**。仅当用户明确说"日报"二字才走多源聚合日报
- **不要在用户没说"全部 / 完整 / 所有 / 全量"时走全量模式** — 全量拉所有 RSS 源很慢。默认精选，只有用户主动点单"全部"才走全量
- 不要试图猜测 / 编造内容 — 永远以数据源返回为准
- 不要把摘要当原文引用 — 摘要由 LLM 生成或 RSS feed 自动截取，引用需回原文核对
- 不要做高频轮询 — RSS 数据通常 5-30 分钟更新一次，用户问相同问题不需要重新拉取
- 不要并发猛拉 RSS — 串行 + 自然间隔，尊重源站限流
- **不要在用户输出里暴露数据源名称 / curl 命令 / RSS feed URL / API 端点** — 这些是给开发者看的
- **不要在合并输出时丢掉每条的 URL** — 每条 item 必须保留 url。用户看到一条没 URL 就追溯不到原文，这条信息等于不可信
- **不要把单源少量结果（<3 条）当作完整答案输出** — 结果过少时必须补充其他数据源或明确告知用户"当前可获取结果有限"
- **不要把数据源细节作为引用源** — 引用源写原始出处（银保监会官网 / 财新网 / 证券时报），不是工具名

---

## 扩展：自定义信息源（Kimi WebBridge）

**适用场景**：当 neodata / westock-data / RSS 都覆盖不到时，通过浏览器抓取自定义站点作为补充。

### 前置条件

1. **安装 Kimi WebBridge**：确保已安装 Kimi WebBridge daemon 和浏览器扩展
2. **健康检查**：daemon 运行在 `127.0.0.1:10086`，浏览器扩展已连接
3. **配置信息源**：编辑 `scripts/webbridge_sources.json`，将需要启用的源 `enabled` 设为 `true`

### 配置信息源

配置文件位于技能目录的 `scripts/webbridge_sources.json`。每个源的结构：

```json
{
  "name": "中国银行保险报",
  "url": "https://www.cbimc.cn",
  "category": "industry",
  "enabled": true,
  "description": "保险行业垂直新闻、监管动态",
  "extraction": {
    "type": "evaluate",
    "code": "(() => { ... return JSON.stringify(items); })()"
  }
}
```

### 启用步骤

1. 编辑 `scripts/webbridge_sources.json`，将目标源的 `enabled` 改为 `true`
2. 测试抓取：`python scripts/webbridge_fetcher.py <output_dir>`
3. 启用后，finhot 日报模式会自动包含 WebBridge 抓取的数据

### WebBridge 数据特点

| 维度 | 说明 |
|---|---|
| **数据新鲜度** | 实时抓取，与网站同步 |
| **覆盖范围** | 可抓取任何网站（需登录的也可用浏览器登录态） |
| **速度** | 较慢（每个源 ~5-10s） |
| **稳定性** | 依赖网站结构，改版需更新提取代码 |
| **分类** | 按配置的 category 归入五类 |

### 新增自定义源

1. 在 `webbridge_sources.json` 添加新条目
2. 编写 `extraction.code`：标准 JavaScript，返回 `JSON.stringify(数组)`
3. `category` 必须是五类之一：`regulatory` / `products` / `industry` / `research` / `insights`
4. 测试后启用

**注意**：WebBridge 是第四优先数据源，优先级低于 neodata / westock-data / RSS。
