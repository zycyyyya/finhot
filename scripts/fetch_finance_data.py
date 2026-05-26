"""
finhot multi-source data fetcher
=============================
架构: 插件化多数据源聚合，每个数据源是独立的 fetcher 函数
当前数据源: 
  1. 知乎搜索API (zhihu_search + global_search)
  2. 东方财富妙想搜索 (mx_search) - 新增

分类体系 (与 aihot 对齐):
    policy      - 监管政策 (银保监会、央行等)
    products    - 产品发布 (保险产品、理财产品等)
    industry    - 行业动态
    research    - 研究报告
    tips        - 技巧与观点

用法:
    python fetch_finance_data.py --mode daily        # 过去24小时
    python fetch_finance_data.py --mode all --days 7  # 最近7天
    python fetch_finance_data.py --category policy    # 按分类筛选
    python fetch_finance_data.py --source zhihu       # 指定数据源
"""

import json
import sys
import os
import argparse
import time
import urllib.request
import urllib.parse
import urllib.error
import re
from datetime import datetime, timedelta, timezone

# ============================================================
# 配置
# ============================================================

ZHIHU_ACCESS_SECRET = os.environ.get("ZHIHU_ACCESS_SECRET", "ecc3d18e5f5df4186947a07012b25e13be5240a7")
ZHIHU_API_BASE = "https://developer.zhihu.com/api/v1/content"

# 东方财富妙想搜索 API Key
MX_APIKEY = os.environ.get("MX_APIKEY", "mkt_jboEXMyhzUVxCmp5Njiq0EVV5rPT7o9IJEHpHQJKAm8")

# 分类关键词映射 - 每个分类对应需要搜索的关键词列表
CATEGORY_KEYWORDS = {
    "policy":    ["银保监会", "央行", "金融监管", "证监会", "监管政策", "保险法", "金监局", "国家金融监督管理总局"],
    "products":  ["保险产品", "理财产品", "基金产品", "信托产品", "新品发布", "养老金", "年金险", "重疾险", "医疗险"],
    "industry":  ["金融行业", "保险行业", "银行业", "证券行业", "金融科技", "金融数据", "保险市场", "保费收入", "偿付能力"],
    "research":  ["研究报告", "行业分析", "宏观分析", "投资策略", "资产配置", "金融分析", "宏观经济", "投资展望", "市场研判"],
    "tips":      ["金融技巧", "理财建议", "保险配置", "投资心得", "避坑指南", "保险攻略", "投保技巧", "理赔指南", "保险科普"],
}

CATEGORY_LABELS = {
    "policy":    "监管政策",
    "products":  "产品发布",
    "industry":  "行业动态",
    "research":  "研究报告",
    "tips":      "技巧与观点",
}

# 东方财富妙想搜索分类策略
MX_CATEGORY_STRATEGIES = {
    "policy": [
        "银保监会监管政策", "央行货币政策", "金融监管政策", "保险监管新规",
        "偿付能力监管", "资本充足率要求", "保险资金运用监管"
    ],
    "products": [
        "保险新产品发布", "理财产品上市", "年金险新品", "重疾险产品",
        "医疗险创新", "保险产品设计", "保险产品费率"
    ],
    "industry": [
        "保险行业动态", "金融行业新闻", "保险市场数据", "保费收入增长",
        "保险科技发展", "保险数字化转型", "保险行业并购"
    ],
    "research": [
        "保险行业研究报告", "金融行业分析", "宏观经济研报", "投资策略分析",
        "保险资产配置", "保险投资展望", "保险市场趋势"
    ],
    "tips": [
        "保险购买技巧", "理财规划建议", "保险理赔指南", "保险配置策略",
        "保险避坑指南", "保险科普知识", "保险投资心得"
    ],
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
# 数据源: 东方财富妙想搜索
# ============================================================

class MXSearchClient:
    """妙想资讯搜索客户端 (使用标准库 urllib, 无需额外依赖)"""
    
    BASE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or MX_APIKEY
        if not self.api_key:
            raise ValueError("MX_APIKEY 环境变量未设置")
    
    def search(self, query: str) -> dict:
        """搜索金融资讯"""
        post_data = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(
            self.BASE_URL,
            data=post_data,
            headers={
                "Content-Type": "application/json",
                "apikey": self.api_key
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"  [MXSearch] HTTP {e.code}: {err_body[:200]}", file=sys.stderr)
            raise
    
    @staticmethod
    def extract_items(result: dict) -> list:
        """从 API 响应中提取资讯条目"""
        status = result.get("status")
        if status != 0:
            print(f"  [MXSearch] 错误状态码: {status} - {result.get('message', '')}", file=sys.stderr)
            return []
        
        data = result.get("data", {})
        inner_data = data.get("data", {})
        search_response = inner_data.get("llmSearchResponse", {})
        items = search_response.get("data", [])
        
        return items


def fetch_mx_search(query: str, limit: int = 10) -> list:
    """
    调用东方财富妙想搜索 API
    返回: [{"title", "summary", "content_preview", "date", "source", ...}, ...]
    """
    try:
        if not MX_APIKEY:
            print(f"  [MXSearch] 错误: MX_APIKEY 环境变量未设置", file=sys.stderr)
            return []
        
        client = MXSearchClient(MX_APIKEY)
        result = client.search(query)
        items = client.extract_items(result)
        
        if not items:
            print(f"  [MXSearch] 未找到相关资讯: {query}", file=sys.stderr)
            return []
        
        formatted_items = []
        for item in items[:limit]:
            title = item.get("title", "无标题")
            content = item.get("content", "")
            date = item.get("date", "")
            ins_name = item.get("insName", "")
            info_type = item.get("informationType", "")
            rating = item.get("rating", "")
            entity_name = item.get("entityFullName", "")
            
            # 类型映射
            type_map = {
                "REPORT": "研报",
                "NEWS": "新闻",
                "ANNOUNCEMENT": "公告"
            }
            type_cn = type_map.get(info_type, info_type)
            
            # 构建摘要
            summary_parts = []
            if entity_name:
                summary_parts.append(f"证券: {entity_name}")
            if ins_name:
                summary_parts.append(f"机构: {ins_name}")
            if type_cn:
                summary_parts.append(f"类型: {type_cn}")
            if rating:
                summary_parts.append(f"评级: {rating}")
            
            summary = " | ".join(summary_parts)
            
            # 内容预览
            if content:
                clean_content = re.sub(r'\s+', ' ', content.strip())
                content_preview = clean_content[:300] + ("..." if len(clean_content) > 300 else "")
            else:
                content_preview = ""
            
            formatted_items.append({
                "title": title,
                "summary": summary,
                "content_preview": content_preview,
                "date": date,
                "source": "mx_search",
                "source_name": "东方财富妙想搜索",
                "info_type": info_type,
                "entity_name": entity_name,
                "ins_name": ins_name,
                "rating": rating,
                "query": query,
            })
        
        print(f"  [MXSearch] 搜索 '{query}': 找到 {len(formatted_items)} 条", file=sys.stderr)
        return formatted_items
        
    except urllib.error.HTTPError as e:
        print(f"  [MXSearch] HTTP错误 {e.code}: {e.reason}", file=sys.stderr)
        return []
    except urllib.error.URLError as e:
        print(f"  [MXSearch] 网络错误: {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  [MXSearch] 异常: {e}", file=sys.stderr)
        return []


def _mx_search_fetcher_factory(category: str, limit: int = 5):
    """工厂函数：创建适配 DATA_SOURCES 注册表的 fetcher"""
    def fetcher(query="", limit=limit):
        # 如果 query 为空，使用分类关键词搜索
        search_queries = MX_CATEGORY_STRATEGIES.get(category, [category])
        all_items = []
        for query in search_queries[:3]:  # 每个分类最多用前3个搜索词
            items = fetch_mx_search(query, limit=limit)
            all_items.extend(items)
            time.sleep(0.5)  # 避免触发限流
        return all_items[:limit*2]  # 限制总条数
    
    fetcher.__name__ = f"fetch_mx_search_{category}"
    return fetcher


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
    # 东方财富妙想搜索 - 按分类注册
    "mx_policy": {
        "name": "东方财富监管政策",
        "fetcher": _mx_search_fetcher_factory("policy", limit=5),
        "description": "东方财富妙想搜索 - 监管政策类资讯",
    },
    "mx_products": {
        "name": "东方财富产品发布",
        "fetcher": _mx_search_fetcher_factory("products", limit=5),
        "description": "东方财富妙想搜索 - 产品发布类资讯",
    },
    "mx_industry": {
        "name": "东方财富行业动态",
        "fetcher": _mx_search_fetcher_factory("industry", limit=5),
        "description": "东方财富妙想搜索 - 行业动态类资讯",
    },
    "mx_research": {
        "name": "东方财富研究报告",
        "fetcher": _mx_search_fetcher_factory("research", limit=5),
        "description": "东方财富妙想搜索 - 研究报告类资讯",
    },
    "mx_tips": {
        "name": "东方财富技巧观点",
        "fetcher": _mx_search_fetcher_factory("tips", limit=5),
        "description": "东方财富妙想搜索 - 技巧观点类资讯",
    },
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
    """按标题和摘要去重"""
    seen = set()
    unique = []
    for item in items:
        # 使用标题+摘要前50字符作为去重键
        key = (item.get("title", ""), item.get("summary", "")[:50])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def fetch_category(category, sources=None, limit_per_query=5):
    """
    拉取某个分类下所有数据源的内容。
    对于 mx_ 类数据源：每个分类只用匹配的 mx_ 源，避免全量请求触发限流。
    """
    if sources is None:
        sources = list(DATA_SOURCES.keys())
    
    # MX 源与分类的映射，确保每个分类只调自己的 MX 源
    mx_category_map = {
        "policy": "mx_policy",
        "products": "mx_products",
        "industry": "mx_industry",
        "research": "mx_research",
        "tips": "mx_tips",
    }
    
    keywords = CATEGORY_KEYWORDS.get(category, [category])
    all_items = []
    
    for source_name in sources:
        if source_name not in DATA_SOURCES:
            print(f"  未知数据源: {source_name}", file=sys.stderr)
            continue
        
        # MX 源：只在该源匹配当前分类时才调用
        if source_name.startswith("mx_"):
            if source_name != mx_category_map.get(category):
                continue  # 跳过不匹配的 MX 源
            
            source = DATA_SOURCES[source_name]
            fetcher = source["fetcher"]
            print(f"  [{source['name']}] 搜索分类: {category}", file=sys.stderr)
            items = fetcher("", limit=limit_per_query)
            for item in items:
                classify_item(item, category)
            all_items.extend(items)
            
        elif source_name.startswith("zhihu"):
            # 知乎搜索：按关键词搜索
            source = DATA_SOURCES[source_name]
            fetcher = source["fetcher"]
            for kw in keywords:
                print(f"  [{source['name']}] 搜索: {kw}", file=sys.stderr)
                items = fetcher(kw, limit=limit_per_query)
                for item in items:
                    classify_item(item, category)
                all_items.extend(items)
                time.sleep(0.5)  # 避免触发限流
    
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