#!/usr/bin/env python3
"""
finhot RSS 数据采集器
从 RSSHub 等公开 RSS 源采集金融保险相关资讯，输出统一 JSON 格式。

依赖：feedparser（pip install feedparser）
用法：
    python rss_fetcher.py --output ./data --days 1
    python rss_fetcher.py --output ./data --sources regulatory,industry
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

try:
    import feedparser
except ImportError:
    print("错误：需要 feedparser 库。请运行 pip install feedparser", file=sys.stderr)
    sys.exit(1)

# ========== RSS 源配置 ==========
# 每个源定义：RSSHub 路由 + 分类 + 中文名
RSS_SOURCES: List[Dict] = [
    # 监管政策
    {"slug": "gov/cbirc/law", "name": "银保监会法规", "category": "regulatory", "base": "https://rsshub.app"},
    {"slug": "gov/csrc/announcement", "name": "证监会公告", "category": "regulatory", "base": "https://rsshub.app"},
    {"slug": "gov/pbc/gov", "name": "央行货币政策", "category": "regulatory", "base": "https://rsshub.app"},
    # 行业动态
    {"slug": "caixin/finance", "name": "财新金融", "category": "industry", "base": "https://rsshub.app"},
    {"slug": "caixin/insurance", "name": "财新保险", "category": "industry", "base": "https://rsshub.app"},
    {"slug": "21jingji/finance", "name": "21财经", "category": "industry", "base": "https://rsshub.app"},
    {"slug": "wallstreetcn/news/global", "name": "华尔街见闻", "category": "industry", "base": "https://rsshub.app"},
    {"slug": "stcn/news", "name": "证券时报", "category": "industry", "base": "https://rsshub.app"},
    {"slug": "yicai/finance", "name": "第一财经", "category": "industry", "base": "https://rsshub.app"},
    # 研究报告
    {"slug": "eeo/finance", "name": "经济观察报", "category": "research", "base": "https://rsshub.app"},
    # 技巧与观点
    {"slug": "36kr/information/fintech", "name": "36氪金融科技", "category": "insights", "base": "https://rsshub.app"},
]

# 保险行业关键词（用于从通用 RSS 中过滤保险相关内容）
INSURANCE_KEYWORDS = [
    "保险", "险企", "险资", "寿险", "财险", "健康险", "车险", "再保险",
    "银保监", "偿付", "精算", "承保", "理赔", "续保", "退保",
    "万能险", "分红险", "投连险", "年金", "养老险",
    "平安", "中国人寿", "中国太保", "新华保险", "人保", "太平",
]

# 金融监管关键词（用于分类精度提升）
FINANCIAL_KEYWORDS = [
    "银行", "信贷", "利率", "降准", "降息", "LPR", "MLF", "逆回购",
    "证监会", "央行", "外汇", "债券", "基金", "理财", "资管",
    "北交所", "科创板", "注册制", "IPO",
]


def generate_id(url: str) -> str:
    """基于 URL 生成唯一 ID"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def parse_published_at(entry) -> Optional[str]:
    """从 feedparser entry 提取发布时间，转为 ISO 8601 UTC"""
    # feedparser 会把日期解析为 time.struct_time
    for field in ["published_parsed", "created_parsed", "updated_parsed"]:
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (TypeError, ValueError):
                continue

    # 回退：尝试原始字符串
    for field in ["published", "updated", "created"]:
        val = getattr(entry, field, None)
        if val:
            return val

    return None


def classify_title(title: str, default_category: str) -> str:
    """
    基于标题关键词微调分类。
    如果标题包含保险关键词但默认分类不是 regulatory，保持默认。
    如果标题包含监管关键词，升级为 regulatory。
    """
    title_lower = title.lower() if title else ""

    # 监管关键词覆盖
    reg_kws = ["银保监", "证监会", "央行", "监管", "法规", "通知", "公告", "批复", "处罚"]
    for kw in reg_kws:
        if kw in title_lower:
            return "regulatory"

    # 产品关键词覆盖
    prod_kws = ["新产品", "产品发布", "产品上线", "新品", "首发", "升级版"]
    for kw in prod_kws:
        if kw in title_lower:
            return "products"

    return default_category


def fetch_rss(source: Dict, max_entries: int = 30, request_delay: float = 1.0) -> List[Dict]:
    """从单个 RSS 源采集数据"""
    base = source.get("base", "https://rsshub.app")
    slug = source["slug"]
    url = f"{base}/{slug}"

    print(f"[RSS] 正在采集 {source['name']} ...", end=" ", flush=True)

    try:
        feed = feedparser.parse(url, request_headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

        if feed.bozo and not feed.entries:
            print(f"❌ 解析失败: {feed.bozo_exception}")
            return []

        items = []
        for entry in feed.entries[:max_entries]:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()

            if not title or not link:
                continue

            published_at = parse_published_at(entry)
            default_cat = source.get("category", "industry")
            category = classify_title(title, default_cat)

            # 提取摘要
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary.strip()[:500]
            elif hasattr(entry, "description"):
                summary = entry.description.strip()[:500]

            items.append({
                "id": generate_id(link),
                "title": title,
                "url": link,
                "source": source["name"],
                "publishedAt": published_at,
                "summary": summary if summary else None,
                "category": category,
            })

        print(f"✅ {len(items)} 条")
        time.sleep(request_delay)  # 尊重源站限流
        return items

    except Exception as e:
        print(f"❌ 错误: {e}")
        return []


def filter_by_time(items: List[Dict], days: int) -> List[Dict]:
    """按时间窗口过滤条目"""
    if days <= 0:
        return items

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    filtered = []
    for item in items:
        published_at = item.get("publishedAt")
        if not published_at:
            # 没有发布时间的条目保留（可能很新）
            filtered.append(item)
            continue

        try:
            # 尝试解析 ISO 格式
            if isinstance(published_at, str):
                dt_str = published_at.replace("Z", "+00:00")
                dt = datetime.fromisoformat(dt_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= cutoff:
                    filtered.append(item)
            else:
                filtered.append(item)
        except (ValueError, TypeError):
            # 解析失败则保留
            filtered.append(item)

    return filtered


def filter_insurance_related(items: List[Dict]) -> List[Dict]:
    """过滤出保险相关条目（标题或摘要含保险关键词）"""
    filtered = []
    for item in items:
        text = (item.get("title", "") + " " + (item.get("summary") or "")).lower()
        for kw in INSURANCE_KEYWORDS + FINANCIAL_KEYWORDS:
            if kw.lower() in text:
                filtered.append(item)
                break
    return filtered


def deduplicate(items: List[Dict]) -> List[Dict]:
    """按 URL 去重"""
    seen_urls = set()
    unique = []
    for item in items:
        url = item.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)
    return unique


def main():
    parser = argparse.ArgumentParser(description="finhot RSS 数据采集器")
    parser.add_argument("--output", "-o", required=True, help="输出目录")
    parser.add_argument("--days", "-d", type=int, default=1, help="采集最近 N 天的数据（默认 1 天）")
    parser.add_argument("--sources", "-s", default=None, help="只采集指定分类的源，逗号分隔（如 regulatory,industry）")
    parser.add_argument("--all", action="store_true", help="不过滤保险相关，保留所有金融条目")
    parser.add_argument("--max-entries", type=int, default=30, help="每个源最多采集条目数（默认 30）")
    parser.add_argument("--delay", type=float, default=1.0, help="源间请求延迟秒数（默认 1.0）")
    args = parser.parse_args()

    # 筛选源
    sources = RSS_SOURCES
    if args.sources:
        cats = set(args.sources.split(","))
        sources = [s for s in sources if s["category"] in cats]

    print(f"=== finhot RSS 采集器 ===")
    print(f"源数量: {len(sources)} | 时间窗口: {args.days} 天")
    print()

    # 采集所有源
    all_items = []
    for source in sources:
        items = fetch_rss(source, max_entries=args.max_entries, request_delay=args.delay)
        all_items.extend(items)

    print(f"\n原始采集: {len(all_items)} 条")

    # 去重
    all_items = deduplicate(all_items)
    print(f"去重后: {len(all_items)} 条")

    # 时间过滤
    all_items = filter_by_time(all_items, args.days)
    print(f"时间过滤后: {len(all_items)} 条")

    # 保险相关过滤（除非 --all）
    if not args.all:
        all_items = filter_insurance_related(all_items)
        print(f"保险/金融相关: {len(all_items)} 条")

    # 按发布时间排序
    all_items.sort(
        key=lambda x: x.get("publishedAt") or "",
        reverse=True
    )

    # 保存
    os.makedirs(args.output, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(args.output, f"rss_data_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(all_items),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_type": "rss",
            "days": args.days,
            "items": all_items,
        }, f, ensure_ascii=False, indent=2)

    # 同时保存 latest 文件
    latest_file = os.path.join(args.output, "latest_rss_data.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(all_items),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_type": "rss",
            "days": args.days,
            "items": all_items,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存:")
    print(f"   {output_file}")
    print(f"   {latest_file}")


if __name__ == "__main__":
    main()
