# FinHot Skill

让 Agent 调用知乎 API + 扩展数据源，聚合金融保险圈资讯，整理成中文 markdown 简报。

## skill 根目录

> 执行本 skill 中的任何命令时，请使用绝对路径。示例：
> ```
> cd <temp目录>; python <skill根目录>/scripts/fetch_finance_data.py --mode daily --output <output目录>/result.json
> ```

## 先决条件

1. **知乎 API**：使用 Bearer 鉴权，Access Secret 内置于脚本。调用频率：每天 1000 次（zhihu_search + global_search 各有 1000 次配额）。
2. **东方财富妙想搜索**：需要设置 `MX_APIKEY` 环境变量，密钥格式为 `mkt_...`。调用频率：单次请求间隔 0.5s 以上，避免触发限流。

## 触发关键词

| 用户说 | 路由 |
|---|---|
| "今天金融圈有什么"、"金融日报"、"金融资讯"、"金融热点"、"金融圈动态" | 默认：**全分类精选**（过去 24 小时） |
| "保险行业新闻"、"保险最新政策"、"保险资讯" | 默认：全分类 + 保险关键词偏好 |
| "银保监会最近"、"央行最新政策"、"监管动态" | `--category policy` |
| "保险产品发布"、"理财产品新发"、"金融产品" | `--category products` |
| "金融行业动态"、"保险行业趋势"、"银行动态" | `--category industry` |
| "研究报告"、"投研观点"、"宏观分析"、"投资策略" | `--category research` |
| "理财技巧"、"保险怎么买"、"投资心得"、"避坑" | `--category tips` |

## 数据源 (可扩展架构)

### 1. 知乎搜索 (`zhihu_search`)
- **接口**: `GET https://developer.zhihu.com/api/v1/content/zhihu_search`
- **特点**: 知乎站内问答和文章，高质量深度内容
- **鉴权**: Bearer Token
- **配额**: 1000 次/天

### 2. 知乎全网搜索 (`zhihu_global`)
- **接口**: `GET https://developer.zhihu.com/api/v1/content/global_search`
- **特点**: 全网内容搜索，含新闻、官网等外部源
- **配额**: 1000 次/天

### 3. 东方财富妙想搜索 (`mx_search`)
- **接口**: `POST https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search`
- **特点**: 东方财富官方金融资讯搜索，含公告、研报、新闻、评级等
- **鉴权**: API Key (`MX_APIKEY` 环境变量)
- **分类策略**: 每个分类预定义 7 个专业搜索词，精准匹配金融保险领域
- **限流**: 单次请求间隔 0.5s 以上，避免触发 112 错误码

### 扩展规划
后续可通过以下方式新增数据源：
1. 在 `scripts/fetch_finance_data.py` 的 `DATA_SOURCES` 字典中注册新的 fetcher 函数
2. 为新数据源实现独立的 `fetch_xxx()` 函数
3. 无需修改核心聚合逻辑

## 分类体系

| 英文 slug | 中文标签 | 搜索关键词 |
|---|---|---|
| `policy` | 监管政策 | 银保监会、央行、金融监管、证监会、监管政策、保险法 |
| `products` | 产品发布 | 保险产品、理财产品、基金产品、信托产品、新品发布、养老金 |
| `industry` | 行业动态 | 金融行业、保险行业、银行业、证券行业、金融科技、金融数据 |
| `research` | 研究报告 | 研究报告、行业分析、宏观分析、投资策略、资产配置、金融分析 |
| `tips` | 技巧与观点 | 金融技巧、理财建议、保险配置、投资心得、避坑指南、保险攻略 |

## 命令行用法

```bash
# 基础用法
python scripts/fetch_finance_data.py --mode daily --output result.json

# 按分类
python scripts/fetch_finance_data.py --mode daily --category policy

# 指定数据源
python scripts/fetch_finance_data.py --mode daily --source zhihu_search --source zhihu_global

# 全量（最近N天）
python scripts/fetch_finance_data.py --mode all --days 7 --output all.json

# 格式化输出
python scripts/fetch_finance_data.py --mode daily --pretty
```

## 返回数据格式

```json
{
  "generated_at": "2026-05-26T04:00:00.000Z",
  "mode": "daily",
  "total": 50,
  "sources_used": ["zhihu_search"],
  "categories": {
    "policy": {
      "label": "监管政策",
      "count": 10,
      "items": [
        {
          "title": "...",
          "content_type": "Answer",
          "url": "https://...",
          "author": "...",
          "votes": 100,
          "comments": 10,
          "summary": "...",
          "edit_time": 1779600000,
          "source": "zhihu_search",
          "category": "policy"
        }
      ]
    }
  }
}
```

## 输出格式规范

### 多分类输出 (默认)

按 category 分组 + 全局编号：

```markdown
**FinHot · 金融保险圈 — 过去 24 小时精选**

## 监管政策
1. **<title>** — <author>
   <summary 简化版 50 字内 >
   <url>

## 产品发布
2. ...

## 行业动态
3. ...

## 研究报告
4. ...

## 技巧与观点
5. ...
```

### 单分类输出

```markdown
**FinHot — 最近 7 天监管政策**

1. **<title>** — <author>
   <summary>
   <url>

2. ...
```

### 时间转人话

`edit_time` 是 Unix 秒级时间戳，展示时必须转成北京时间相对时间：

| 差距 | 展示 |
|---|---|
| < 1 小时 | "X 分钟前" |
| < 24 小时 | "X 小时前" |
| < 7 天 | "X 天前" |
| >= 7 天 | "YYYY-MM-DD" |

### 输出约束

- 不要暴露 API 端点路径 / raw 参数 / 限流细节
- 数据源仅写一句："数据来自知乎"
- 每条必须有 url，否则用户无法追溯原文
- 全局编号贯穿全文，不在每个 ## 内重新计数
- 只展示 title，不展示 title_en（除非为空）

## 错误处理

- 知乎 API 返回 `Code: 20001` (Authorization failed)：Access Secret 失效，提示用户更新
- HTTP 429：触发限流，脚本自带 0.3s 间隔，自动减速
- 数据源暂时不可用：静默跳过，在 stderr 输出警告

## 不要做

- 不要编造或猜测内容 — 永远以 API 返回为准
- 不要在用户输出里暴露 `mode=selected` / `category=policy` 等 raw 参数
- 不要并发猛拉 — 串行 + 间隔
- 不要把摘要当原文引用 — 摘要由 LLM 生成，引用需回 url 核对
- 不要用训练数据替代实时数据 — 金融保险政策变化快，训练数据可能已过时