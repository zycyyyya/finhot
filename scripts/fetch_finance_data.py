"""
finhot multi-source data fetcher
=============================
架构: 插件化多数据源聚合，每个数据源是独立的 fetcher 函数
当前数据源: 知乎搜索API (zhihu_search + global_search)
后续可扩展: 全网搜索、微信公众号、研报平台等

用法:
    python fetch_finance_data.py --mode daily        # 过去24小时
    python fetch_finance_data.py --mode all --days 7  # 最近7天
    python fetch_finance_data.py --category policy    # 按分类筛选
    python fetch_finance_data.py --source zhihu       # 指定数据源

分类体系 (与 aihot 对齐):
    policy      - 监管政策 (银保监会、央行等)
    products    - 产品发布 (保险产品、理财产品等)
    industry    - 行业动态
    research    - 研究报告
    tips        - 技巧与观点
"""

import json
import sys
import os
import argparse
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta, timezone

# ============================================================
# 配置
# ============================================================

ZHIHU_ACCESS_SECRET = os.environ.get("ZHIHU_ACCESS_SECRET", "ecc3d18e5f5df4186947a07012b25e13be5240a7")
ZHIHU_API_BASE = "https://developer.zhihu.com/api/v1/content"

# 分类关键词映射 - 每个分类对应需要搜索的关键词列表
CATEGORY_KEYWORDS = {
    "policy":    ["银保监会", "央行", "金融监管", "证监会", "监管政策", "保险法"],
    "products":  ["保险产品", "理财产品", "基金产品", "信托产品", "新品发布", "养老金"],
    "industry":  ["金融行业", "保险行业", "银行业", "证券行业", "金融科技", "金融数据"],
    "research":  ["研究报告", "行业分析", "宏观分析", "投资策略", "资产配置", "金融分析"],
    "tips":      ["金融技巧", "理财建议", "保险配置", "投资心得", "避坑指南", "保险攻略"],
}

CATEGORY_LABELS = {
    "policy":    "监管政策",
    "products":  "产品发布",
    "industry":  "行业动态",
    "research":  "研究报告",
    "tips":      "技巧与观点",
}


# ============================================================
# 数据源: 知乎搜索
# ============================================================

def fetch_zhihu_search(query, limit=10):
    """
    调用知乎 zhihu_search API
    返回: [{"title", "content_type", "url", "author", "votes", "comments", "summary", "edit_time"}, ...]
    """
    timestamp = int(time.time())
    url = f"{ZHIHU_API_BASE}/zhihu_search?{urllib.parse.urlencode({'Query': query, 'Limit': limit})}"
    
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {ZHIHU_ACCESS_SECRET}")
    req.add_header("X-Request-Timestamp", str(timestamp))
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("Code") != 0:
                print(f"  [zhihu_search] 错误: {data.get('Message')}", file=sys.stderr)
                return []
            items = data.get("Data", {}).get("Items", [])
            results = []
            for item in items:
                content_text = item.get("ContentText", "")
                # 取前200字作为摘要
                summary = content_text[:200] if content_text else ""
                results.append({
                    "title": item.get("Title", ""),
                    "content_type": item.get("ContentType", ""),
                    "url": item.get("Url", ""),
                    "author": item.get("AuthorName", ""),
                    "votes": item.get("VoteUpCount", 0),
                    "comments": item.get("CommentCount", 0),
                    "summary": summary,
                    "edit_time": item.get("EditTime", 0),
                    "source": "zhihu_search",
                })
            return results
    except urllib.error.HTTPError as e:
        print(f"  [zhihu_search] HTTP {e.code}: {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  [zhihu_search] 异常: {e}", file=sys.stderr)
        return []


def fetch_zhihu_global(query, limit=10):
    """
    调用知乎 global_search API (全网搜索)
    """
    timestamp = int(time.time())
    url = f"{ZHIHU_API_BASE}/global_search?{urllib.parse.urlencode({'Query': query, 'Limit': limit})}"
    
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {ZHIHU_ACCESS_SECRET}")
    req.add_header("X-Request-Timestamp", str(timestamp))
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("Code") != 0:
                print(f"  [global_search] 错误: {data.get('Message')}", file=sys.stderr)
                return []
            items = data.get("Data", {}).get("Items", [])
            results = []
            for item in items:
                results.append({
                    "title": item.get("Title", ""),
                    "content_type": item.get("ContentType", ""),
                    "url": item.get("Url", ""),
                    "author": item.get("AuthorName", ""),
                    "votes": item.get("VoteUpCount", 0),
                    "comments": item.get("CommentCount", 0),
                    "summary": (item.get("ContentText", "")[:200] if item.get("ContentText") else ""),
                    "edit_time": item.get("EditTime", 0),
                    "source": "zhihu_global",
                })
            return results
    except Exception as e:
        print(f"  [global_search] 异常: {e}", file=sys.stderr)
        return []


# ============================================================
# 数据源注册表 - 新增数据源在此注册
# ============================================================

DATA_SOURCES = {
    "zhihu_search": {
        "name": "知乎搜索",
        "fetcher": fetch_zhihu_search,
        "description": "知乎站内问答和文章",
    },
    "zhihu_global": {
        "name": "知乎全网搜索",
        "fetcher": fetch_zhihu_global,
        "description": "知乎全网内容搜索 (含新闻、官网等)",
    },
    # 后续扩展:
    # "web_news": {
    #     "name": "全网新闻",
    #     "fetcher": fetch_web_news,
    #     "description": "百度/谷歌新闻搜索",
    # },
    # "wechat_mp": {
    #     "name": "微信公众号",
    #     "fetcher": fetch_wechat_mp,
    #     "description": "微信公众号文章",
    # },
}


# ============================================================
# 核心聚合逻辑
# ============================================================

def classify_item(item, category):
    """
    尝试将条目归类。规则:
    - 基于搜索时的 category 做初步归类
    - 可根据 title/summary 做二次分类 (后续扩展)
    """
    item["category"] = category
    return item


def deduplicate(items):
    """按 URL 去重"""
    seen = set()
    unique = []
    for item in items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
    return unique


def fetch_category(category, sources=None, limit_per_query=5):
    """
    拉取某个分类下所有数据源的内容
    """
    if sources is None:
        sources = list(DATA_SOURCES.keys())
    
    keywords = CATEGORY_KEYWORDS.get(category, [category])
    all_items = []
    
    for source_name in sources:
        if source_name not in DATA_SOURCES:
            print(f"  未知数据源: {source_name}", file=sys.stderr)
            continue
        
        source = DATA_SOURCES[source_name]
        fetcher = source["fetcher"]
        
        # 每个关键词搜索 limit_per_query 条
        for kw in keywords:
            print(f"  [{source['name']}] 搜索: {kw}", file=sys.stderr)
            items = fetcher(kw, limit=limit_per_query)
            for item in items:
                classify_item(item, category)
            all_items.extend(items)
            time.sleep(0.3)  # 避免触发限流
    
    return all_items


def run(mode="daily", category=None, sources=None, days=1):
    """
    主入口
    mode:
        - "daily": 过去24小时
        - "all": 按 days 参数控制天数
    category:
        - None: 所有分类
        - 指定分类 slug: policy / products / industry / research / tips
    sources:
        - None: 所有已注册数据源
        - 列表: 指定数据源
    """
    categories = [category] if category else list(CATEGORY_KEYWORDS.keys())
    sources = sources or list(DATA_SOURCES.keys())
    
    print(f"finhot 数据采集", file=sys.stderr)
    print(f"  模式: {mode}", file=sys.stderr)
    print(f"  分类: {', '.join(categories)}", file=sys.stderr)
    print(f"  数据源: {', '.join(sources)}", file=sys.stderr)
    print(f"  天数: {days}", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    
    all_items = []
    for cat in categories:
        print(f"\n📂 {CATEGORY_LABELS.get(cat, cat)}", file=sys.stderr)
        items = fetch_category(cat, sources, limit_per_query=5)
        all_items.extend(items)
    
    # 去重
    unique = deduplicate(all_items)
    print(f"\n✅ 共采集 {len(unique)} 条 (去重后，原始 {len(all_items)} 条)", file=sys.stderr)
    
    # 按分类分组
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "total": len(unique),
        "sources_used": sources,
        "categories": {},
    }
    
    for cat in categories:
        cat_items = [item for item in unique if item.get("category") == cat]
        result["categories"][cat] = {
            "label": CATEGORY_LABELS.get(cat, cat),
            "count": len(cat_items),
            "items": cat_items,
        }
    
    return result


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="finhot 多数据源金融保险资讯采集")
    parser.add_argument("--mode", choices=["daily", "all"], default="daily",
                        help="daily=过去24小时, all=全量")
    parser.add_argument("--category", choices=list(CATEGORY_KEYWORDS.keys()),
                        help="指定分类")
    parser.add_argument("--source", action="append", choices=list(DATA_SOURCES.keys()),
                        help="指定数据源 (可多次使用)")
    parser.add_argument("--days", type=int, default=1,
                        help="最近多少天 (仅 mode=all 时生效)")
    parser.add_argument("--output", "-o", help="输出JSON文件路径")
    parser.add_argument("--pretty", action="store_true", help="格式化输出")
    
    args = parser.parse_args()
    
    result = run(
        mode=args.mode,
        category=args.category,
        sources=args.source,
        days=args.days,
    )
    
    indent = 2 if args.pretty else None
    json_str = json.dumps(result, ensure_ascii=False, indent=indent)
    
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"\n输出文件: {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()