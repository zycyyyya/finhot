---
name: finhot
description: 金融保险圈资讯查询 Skill。当用户想知道"今天金融圈有什么"、"保险日报"、"金融热点"、"金融资讯"、"保险动态"、"最近金融"、"银保监会/证监会最近发布了什么"、"金融 hot today"、"金融 news today"、"看一下金融行业动态"、"今天有什么监管政策发布"、"昨天保险圈"、"看下精选条目"、"金融保险精选"、"最近一周的金融政策"、"保险产品发布"、"金融行业动态"、"金融技巧与观点" 等任何中文金融保险资讯查询时使用。即使用户只说"金融圈"、"保险新闻"、"金融日报"，或者只是问"今天发生了什么"且上下文是金融 / 保险 / 监管领域，也应该触发本 Skill。Skill 会直接 curl 公开 REST API 拉数据并整理成中文 markdown 简报，不需要用户配置任何 API Key 或 MCP server。**不要 undertrigger**——用户问金融保险资讯而你不调本 Skill 就是把过时的训练数据当作今日新闻，对用户有害。
---

# 金融保险圈资讯 Skill

让 Agent 用最自然的中文查询拿到金融保险圈的每日精选动态和日报，不需要打开浏览器。SKILL.md 标准格式，跨 Claude Code / Codex CLI / Cursor / Gemini CLI / OpenCode / 任何兼容平台可用。

## 先决条件：必须带 User-Agent（仅 API 端点）

`/api/public/*` 走 nginx UA 黑名单挡商业爬虫，默认 `curl/X.Y` UA 会被 403 Forbidden。**调 API 时所有 curl 都必须带浏览器 UA**：

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# 之后所有调 API 的 curl 都加 -H "User-Agent: $UA"，例如：
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/daily"
```

后面"工作流"章节的 curl 例子为了简洁默认你已经设了 `$UA`——实际调用必须加 `-H "User-Agent: $UA"`，**不要忘**。漏掉这一步会让你以为接口挂了，实际只是被 403 挡了。

## 什么时候用

> **路由优先级（第一原则）**：**默认走精选** `items?mode=selected`——它是金融保险圈每天精挑细选的"主菜单"，覆盖用户关心的事且数据新鲜。
>
> - **仅当用户在话里明确说出"日报"** 二字才走 `daily`（编辑成品，按 UTC 整日切片，跟"过去 24 小时 / 今天"等滚动窗口对不上）
> - **仅当用户明确说"全部 / 完整 / 所有 / 全量"** 才走 `mode=all`（含未精选的次要条目，量大但杂）
> - **"今天金融圈"、"过去 24 小时大新闻"、"最近保险圈有啥"** 等宽问题 = **默认精选 + 时间窗（since）**，不要默认走日报或全部
>
> 这是为了对齐用户的语义优先级：精选是主菜单，日报和全部是用户特意点单的备选，不应抢默认。

| 用户在说 | 应该走的接口 |
|---|---|
| **默认（宽问题）**："今天金融圈有什么"、"过去 24 小时大新闻"、"最近保险圈"、"金融有啥新东西" | `GET /api/public/items?mode=selected&since=<语义时间窗>`（默认精选 + since 收窄） |
| **明确说"日报"**："金融日报"、"今天的日报"、"看一下日报" | `GET /api/public/daily`（最新日报） |
| **明确说"全部 / 完整 / 所有 / 全量"**："看下今天的全部金融动态"、"完整列表"、"所有保险动态" | `GET /api/public/items?mode=all`（不一定带 since,看用户语境) |
| "昨天/前天金融日报"、"看下 5 月 6 号的日报" | `GET /api/public/daily/{YYYY-MM-DD}` |
| "最近几天日报有哪些"、"列一下日报"、"日报存档" | `GET /api/public/dailies?take=N` |
| "看下精选条目"、"金融保险精选" | `GET /api/public/items?mode=selected` |
| "最近的监管政策"、"保险产品发布"、"金融行业动态"、"金融研究报告" | `GET /api/public/items?mode=selected&category=...&since=<7d 前>`（默认精选 + 类别） |
| "最近一周的金融动态"、"5 天前到现在的发布" | `GET /api/public/items?mode=selected&since=ISO-8601` |
| "银保监会/证监会最近发的"(机构维度) | `GET /api/public/items?q=银保监会`(server-side 关键词搜索) |
| "车险相关 / 健康险相关 / RCEP 政策" | `GET /api/public/items?q=<关键词>`(在 title + 中文 title + 中文 summary 三列匹配) |

通用启发：**用户问的是"现在的金融保险行业事实"，不要凭训练数据脑补，永远走 API**。即使你"觉得"知道答案，也要查一遍——金融保险资讯比你的训练截止日新得多，且角度聚焦中文金融从业者关心的话题。

## 端点速览

| 端点 | 用途 | 主要参数 |
|---|---|---|
| `/api/public/daily` | 最新日报 | 无 |
| `/api/public/daily/{YYYY-MM-DD}` | 指定日期日报 | path: `date` |
| `/api/public/dailies` | 日报归档列表 | `take` (1-180, default 30) |
| `/api/public/items` | 全部金融保险动态 | `mode` / `category` / `since` / `take` / `cursor` / `q`(关键词) |

约定：
- Base URL: `https://finhot.example.com` (需替换为实际数据源)
- 鉴权：无（匿名）
- 限流：600 req/min/IP（请串行调用，不要并发猛拉）
- items 端点 `since` 限最近 7 天:**不传等同 since=now-7d**(服务端兜底);早于 7 天前自动截到 7 天前;未来时间 → 400。**所以无论 Skill 怎么调,items API 永远只返回最近 7 天的内容**。需要更早 → 走 `/api/public/daily/{YYYY-MM-DD}` 翻日报存档
- `take` 上限 100；想要更多走 cursor 翻页

## 工作流

### 默认路径：拉精选 + 时间窗（宽问题首选）

精选 = 金融保险圈每天精挑细选的"主菜单"——覆盖所有用户关心的金融保险大事，按发布时间倒序。**任何"今天金融圈"、"过去 24 小时大新闻"、"最近保险有啥"等宽问题，默认走这个**——比起日报：① 时间窗自由（24 小时 / 3 天 / 1 周想多窄就多窄，跟用户语义对齐）② 数据新鲜（实时滚动而非按 UTC 整日切片）③ 质量仍高（`selected=true` 的池子，不含次要条目）。

```bash
# 拉最近 24 小时精选（用户问"过去 24 小时大新闻"）
since=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&since=$since&take=50"

# 拉最近 50 条精选（用户问"看下精选" / 不带明确时间窗）
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&take=50" \
  | jq '.items[] | {title, source, publishedAt, url}'
```

### 拉日报（用户明确说"日报"时）

**触发关键词**：句子里出现"日报"二字（"金融日报"、"今天的日报"、"看下日报"、"5 月 6 号的日报"）。**没有"日报"二字不要走这个**——日报是 UTC 0 点切片的固定一日成品，跟"过去 24 小时 / 今天"等滚动时间窗对不上。

日报是金融保险圈的"标题层"——每天北京时间 08:00 自动生成，按主题分版块（5 个固定版块）。已有"主编点评"导语段落，是按主题打包后的成品。

```bash
# 拉今日（或最新可用的）日报
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/daily" \
  | jq '{date, lead: .lead.title, sections: [.sections[] | {label, n: (.items | length)}]}'
```

### 拉指定日期日报

```bash
# YYYY-MM-DD，UTC 0 点为基准
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/daily/2026-05-07"
```

### 列日报归档（discovery）

不知道有哪些日期可查时，先看归档：

```bash
# 最近 N 天日报索引（不含正文，只有日期 + 头条标题）
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/dailies?take=14" \
  | jq '.items[] | {date, leadTitle}'
```

### 拉全部（用户明确说"全部 / 完整 / 所有 / 全量"时）

**触发关键词**：句子里出现"全部"、"完整"、"所有"、"全量"、"包括老的"——用户主动想看精选之外的次要条目（被精选筛掉但仍相关的内容）。**没有这些关键词不要走 mode=all**——精选已经覆盖大部分用户关心的事，全部池子量大但杂。

```bash
# 拉最近 24 小时全部金融动态（用户问"看下今天全部的金融动态"）
since=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=all&since=$since&take=100"
```

### 按分类拉条目

5 个 category(items API 用英文 slug,daily API 看到的 section label 是中文):

| `items?category=` | `daily.sections[].label` |
|---|---|
| `regulatory` | 监管政策 |
| `products` | 产品发布/更新 |
| `industry` | 行业动态 |
| `research` | 研究报告 |
| `insights` | 技巧与观点 |

```bash
# 例：拉最近 50 条监管政策（默认精选 + regulatory 类别）
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&category=regulatory&take=50" \
  | jq '.items[] | {title, source, publishedAt, url}'

# 例：精选里的保险产品发布
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&category=products&take=20"

# 例外：用户明确说"全部监管政策 / 所有产品发布"才走 mode=all
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=all&category=regulatory&take=100"
```

### 按时间窗口拉条目（最近 N 天）

> **关键规则**:用户问"**最近** X"(最近的监管政策 / 最近保险产品 / 最近银保监会等)时,需要带 `since` 参数把窗口收窄到用户实际意图(说"最近 3 天" 就 3d,"昨天" 就 1d,"最近一周" 就 7d)。
>
> **服务端兜底**:items API 服务端默认 `since=now-7d`(硬上限,保护服务器),所以即使 Skill 完全不带 since 也只会返回最近 7 天的内容,不会拉到几个月前的老条目。但**仍建议显式带 since**:① 用户问"最近 3 天" 时显式 3d 比让服务端默认 7d 更精确 ② 输出元信息可以写人话级时间窗 ③ 跟用户公开宣传的"最长 7 天"对齐意图清晰。

```bash
# 拉最近 7 天的精选监管政策(用户问"最近的监管政策")
since=$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&category=regulatory&since=$since&take=100"

# 拉最近 3 天的精选动态(用户明确说"最近 3 天")
since=$(date -u -v-3d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '3 days ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&since=$since&take=100"
```

**例外**:用户明确说"**全量 / 所有 / 完整列表 / 包括老的**" → mode 切到 `all`,可以不带 since;用户问"**看下精选**"(看精选池而非时间窗)mode 保持 `selected` 也可以不带 since。但只要句子里有"最近 / 最新 / 这两天 / 这周",**默认带 since + mode=selected**。

### 翻页（cursor）

`/api/public/items` 响应里有 `nextCursor`（opaque token），下次请求把它原样塞进 `cursor` 参数即可。

```bash
# 第 1 页
resp1=$(curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=all&take=100")
echo "$resp1" | jq '.items | length'   # 100

# 第 2 页
cursor=$(echo "$resp1" | jq -r '.nextCursor')
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=all&take=100&cursor=$cursor"
```

`hasNext = false` 或 `nextCursor = null` 时停止翻页。**cursor 是不透明 token,视作黑盒,不要尝试解析、递增、或跨端点复用**。

### 关键词搜索（"银保监会最近发的" / "车险相关" / "健康险政策"）

API 直接支持 server-side 关键词搜索 — `q` 参数在 `title` + 中文 `title` + 中文 `summary` 三列上 ILIKE 匹配,走 PostgreSQL pg_trgm GIN 索引(2-6ms)。**不要再走"拉一批 + 客户端 jq grep"模式** — 那只能看到前 100 条池子里的命中,关键词若在 100 条外完全找不到。

```bash
# 找银保监会最近发的(覆盖全池,不仅前 100)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?q=银保监会&take=30"

# 找车险相关的所有金融动态(任何包含车险的标题或摘要)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?q=车险"

# 找健康险政策(category 限定 + 关键词)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?category=regulatory&q=健康险&take=30"

# 关键词 + 时间窗(证监会最近 3 天的精选)
SINCE=$(date -u -v-3d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '3 days ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://finhot.example.com/api/public/items?mode=selected&q=证监会&since=$SINCE"
```

`q` 约束:
- 至少 2 个字符(单字符 GIN trigram 退化为全表扫,服务端会视作不搜索)
- 最长 200 字(超出自动截断)
- 跟其它参数(mode/category/since/take/cursor)正交叠加,可以"按精选 + 监管政策 + 关键词 + 7 天内"组合
- 跟其它请求共享 600r/m 限流

## 返回数据形态

### `/api/public/daily` 返回

```json
{
  "date": "2026-05-07",
  "generatedAt": "2026-05-07T00:01:23.456Z",
  "windowStart": "2026-05-06T00:00:00.000Z",
  "windowEnd":   "2026-05-07T00:00:00.000Z",
  "lead": { "title": "...", "leadParagraph": "..." },
  "sections": [
    {
      "label": "监管政策",
      "items": [
        {
          "title": "...",
          "summary": "...",
          "sourceUrl": "https://...",
          "sourceName": "银保监会官网"
        }
      ]
    }
  ],
  "flashes": [
    { "title": "...", "sourceName": "...", "sourceUrl": "...", "publishedAt": "..." }
  ]
}
```

`sections[].label` 固定 5 个："监管政策" / "产品发布/更新" / "行业动态" / "研究报告" / "技巧与观点"。`lead` 极少数日报为 `null`。

### `/api/public/dailies` 返回

```json
{
  "count": 14,
  "items": [
    { "date": "2026-05-07", "generatedAt": "...", "leadTitle": "..." }
  ]
}
```

### `/api/public/items` 返回

```json
{
  "count": 50,
  "hasNext": true,
  "nextCursor": "eyJhIjoxNzE0OTk1MjAwMDAwLCJpIjoiY205eHl6MTIzIn0",
  "items": [
    {
      "id": "cm9abc456def789ghi012jkl3",
      "title": "中文标题（normalize 过）",
      "title_en": "原英文标题（仅当与 title 不同时存在，否则 null）",
      "url": "https://...",
      "source": "银保监会官网",
      "publishedAt": "2026-05-07T15:30:00.000Z",
      "summary": "中文摘要（LLM 生成）",
      "category": "regulatory"
    }
  ]
}
```

字段不变量：

- 必有：`id` / `title` / `url` / `source`
- 可空：`title_en` / `summary` / `publishedAt` / `category`
- `category` 取值集：`regulatory` / `products` / `industry` / `research` / `insights` / `null`
- `publishedAt`：ISO 8601 UTC（带 `Z`）
- `id`：cuid 字符串（25 字符），**不要假设是数字**

## 给用户的输出格式

> ⚠️ **核心原则**：这一节是**直接展示给用户的最终内容**——必须 markdown 格式 + 排版好 + **普通人能看得懂的人话**。用户多数是非技术金融从业者 / 保险代理人 / 普通读者，看到的应该是中文金融保险资讯简报，**不是 API 调试日志**。
>
> 所有"端点路径 / `mode=selected` 这种 raw 参数 / 限流 / nginx 缓存 / cursor / hasNext"等基础设施细节**都不能出现**在用户看到的输出里。**人话**级元数据（时间窗 / 条数 / "按发布时间倒序"）可以保留——判断标准：用户能直接看懂吗？能 → 保留；不能 → 删掉。

### 日报式输出（用 daily / daily/{date} 端点时）

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

## 快讯（如果 flashes 有内容）
- <flash.title> — <flash.source>（<flash.publishedAt 转人话>）
```

**编号贯穿全文**（1, 2, 3 ... N），不在每个 ## 内重新计数——这样用户能一眼数到"今天 27 条"。

### 列表式输出（用 items 端点时）

**默认按 category 分组 + 全局编号**——用户对"监管政策/产品/行业/研究/观点"五版块结构已经形成预期（来自日报），混合 category 时这个结构最自然：

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

3. ...

## 行业动态
4. ...
```

**只有 1 个 category** 时（用户明确说"监管政策"/"保险产品"等），用扁平编号列表：

```markdown
**金融保险圈 — 最近一周监管政策**（2026-05-01 ~ 2026-05-08）

1. **<title>** — <source>
   <summary>
   <url>

2. ...
```

### 副标题／元信息只写人话

**OK**（用户能直接懂的）：

- "时间窗 2026-05-05 ~ 2026-05-07"
- "最近 3 天命中银保监会关键词的全部条目"
- "按发布时间倒序"
- "共 50 条"
- "今天 5/8 日报北京时间 08:00 后才生成，先看 5/7 这期"

**不 OK**（基础设施泄漏，坚决不写）：

- ❌ `mode=selected` / `category=regulatory` / `take=30` 这种 raw 参数名
- ❌ 端点路径 `/api/public/items?since=2026-04-30T18:39:31Z&take=50`
- ❌ "限流 600 req/min" / "nginx 缓存 60s" / "x-nginx-cache: HIT"
- ❌ "cursor" / "hasNext=true" / "需 cursor 翻页或缩小 since 窗口"
- ❌ 任何 HTTP 状态码 / cache 状态 / 后端机制描述

数据源最多写一句：**"数据来自金融保险资讯平台"**，要么干脆不提（用户在用 skill 时已经知道源头）。

### 时间转人话

`publishedAt` 是 ISO 8601 UTC，展示时**必须**转成北京时间 + 用户能扫读的相对/绝对时间：

| 内部值 | 展示给用户 |
|---|---|
| `2026-05-08T01:48:00.000Z` | "今天上午 09:48" / "2 小时前" |
| `2026-05-07T18:08:17.000Z` | "今天凌晨 02:08" / "10 小时前" |
| `2026-05-06T16:43:00.000Z` | "5/7 00:43" / "昨天" |

**不要**直接展示 `2026-05-07T15:30:00.000Z` 这种 ISO 字符串——用户看不懂。

### title vs title_en

默认输出 `title`（中文 normalize 过的）。`title_en` 只在以下场景才用：

- 用户明确要求英文版（"用英文给我看一下"）
- `title` 为空（极少见）

**不要**两个都展示。

## 常见错误处理

- `{"error":"No daily report available yet."}`（HTTP 404）：当天日报还没生成（北京时间 08:00 之前）。建议给用户：拉昨天日报 `curl /api/public/daily/{昨天日期}`
- `{"error":"Invalid date format..."}`（HTTP 400）：date 必须是 `YYYY-MM-DD`，UTC 基准
- items 端点常见 400：
  - `"invalid mode (must be 'selected' or 'all')"`
  - `"invalid category (must be one of: regulatory, products, industry, research, insights)"`
  - `"invalid since (must be ISO date, not in future)"`
  - `"invalid take (must be integer 1-100)"`
- HTTP 429（限流）：单 IP 超 600 req/min。串行调用 + 翻页加 200ms 间隔即可

## 不要做

- **不要把"今天金融圈"、"过去 24 小时大新闻"、"最近保险圈有啥"等宽问题路由到 daily** — 这些是滚动时间窗，daily 是 UTC 0 点切片（5/6-5/7 一整天）的固定一日成品，时间精度对不上。**默认走 `mode=selected + since=<语义窗>`**。仅当用户在话里明确说"日报"二字才走 `daily`
- **不要在用户没说"全部 / 完整 / 所有 / 全量"时默认走 `mode=all`** — 精选已经覆盖大部分用户关心的事，全部池子量大但杂含未精选次要条目。默认 `mode=selected`，只有用户主动点单"全部"才切到 `mode=all`
- 不要试图猜测 / 编造内容 — 永远以 API 返回为准
- 不要把摘要（`summary`）当原文引用 — 摘要由 LLM 生成，引用需要回 `url` / `sourceUrl` 核对
- 不要做高频轮询 — 日报每天 08:00 才更新一次，items 端点 5 分钟服务端缓存，用户问相同问题时不需要重新调 API
- 不要并发猛拉翻页 — 串行 + 自然间隔
- 不要尝试解析 / 递增 / 跨端点复用 cursor — 它是不透明 token,内部编码格式不稳定,改了不通知
- 机构维度 / 关键词查询用 server-side `?q=<词>`,不要走"拉一批 + 客户端 jq grep"(那只能看到前 100 条池子,会漏)
- **用户问"最近 N 天 X" 时显式带 `since=<N天前>`**(意图明确 + 元信息能写人话时间窗)。不带 since 服务端默认 7d 兜底,所以不会拉到老条目,但用户问"最近 3 天" 时让服务端默认 7d 会多带 4 天的内容
- **不要在用户输出里暴露端点路径 / raw 参数 / 限流 / 缓存 TTL / cursor / hasNext 等基础设施细节** — 这些是给开发者看的，用户看不懂。详见上方"给用户的输出格式 → 副标题／元信息只写人话"
- **不要在压缩 / 跨日 / 跨版块合并输出时丢掉每条的 sourceUrl** — 即使你为篇幅把 3 个日报合并成 5 类总结，每条 item 也必须保留 url（标题后或单独一行）。用户看到一条没 URL 就追溯不到原文，这条信息等于不可信
- **不要把"端点路径 / 调用细节"作为输出的引用源** — 引用源就写 `<source>`（银保监会官网 / 证监会官网 / 财新网 这种），不是 `GET /api/public/items?...`

---

## 扩展：自定义信息源（Kimi WebBridge）

**适用场景**：当 API 覆盖的源不足时，通过浏览器抓取自定义站点（如雪球、36氪、中国银行保险报等）作为补充数据源。

### 前置条件

1. **安装 Kimi WebBridge**：确保已安装 Kimi WebBridge daemon 和浏览器扩展
2. **健康检查**：daemon 运行在 `127.0.0.1:10086`，浏览器扩展已连接
3. **配置信息源**：编辑 `scripts/webbridge_sources.json`，将需要启用的源 `enabled` 设为 `true`

### 配置信息源

配置文件位于技能目录的 `scripts/webbridge_sources.json`，包含以下字段：

```json
{
  "sources": [
    {
      "name": "雪球",
      "url": "https://xueqiu.com",
      "category": "industry",
      "enabled": true,
      "description": "投资者社区，个股讨论、机构观点、市场情绪",
      "extraction": {
        "type": "evaluate",
        "code": "JavaScript 代码，返回 JSON.stringify([...])"
      }
    }
  ]
}
```

### 启用步骤

1. **编辑配置文件**：将目标源的 `enabled` 改为 `true`
2. **测试抓取**：运行 `python scripts/webbridge_fetcher.py <output_dir>` 验证
3. **finhot 自动集成**：启用后，finhot 查询时会自动包含 WebBridge 抓取的数据

### WebBridge 数据特点

| 维度 | 说明 |
|---|---|
| **数据新鲜度** | 实时抓取，与网站同步 |
| **覆盖范围** | 可抓取任何网站（需登录的也可用浏览器登录态） |
| **速度** | 较慢（每个源 ~5-10s） |
| **稳定性** | 依赖网站结构，改版需更新提取代码 |
| **分类** | 按配置的 category 归入 finhot 五类 |

### 多 Agent 共享

- **同一设备**：daemon 单例，Marvis 和 Work Buddy 可共用
- **隔离机制**：通过 `session` 参数隔离，互不干扰
- **并发限制**：daemon 串行处理请求，建议错峰调用

### 故障排查

| 现象 | 检查 |
|---|---|
| daemon 未运行 | `~/.kimi-webbridge/bin/kimi-webbridge status` |
| 扩展未连接 | 打开浏览器，检查扩展是否启用 |
| 抓取超时 | 增加 `time.sleep()` 等待页面加载 |
| 提取代码失效 | 网站改版，需更新 CSS 选择器 |

### 新增自定义源

1. 在 `webbridge_sources.json` 添加新条目
2. 编写 `extraction.code`：使用标准 JavaScript，返回 `JSON.stringify(数组)`
3. 设置合适的 `category`（regulatory/products/industry/research/insights）
4. 测试后启用

**注意**：WebBridge 数据作为 API 数据的补充，优先级低于 API 返回的精选条目。