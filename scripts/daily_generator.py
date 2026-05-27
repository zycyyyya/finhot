#!/usr/bin/env python3
"""
finhot 日报生成器
聚合多源数据（RSS + neodata + westock-data），生成按五类分版的日报 JSON。

用法：
    python daily_generator.py --input ./data --output ./daily
    python daily_generator.py --date 2026-05-07 --output ./daily
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


# 五类分类关键词映射
CATEGORY_RULES = {
    "regulatory": {
        "label": "监管政策",
        "keywords": ["银保监", "证监会", "央行", "监管", "法规", "通知", "公告", "批复",
                      "处罚", "行政许可", "窗口指导", "偿付能力", "整改", "合规", "资管新规",
                      "注册制", "IPO", "北交所", "科创板", "降准", "降息", "LPR"],
    },
    "products": {
        "label": "产品发布/更新",
        "keywords": ["新产品", "产品发布", "产品上线", "新品", "首发", "升级版",
                      "新险种", "增额终身寿", "养老年金", "惠民保", "百万医疗",
                      "新基金", "理财产品", "信托产品"],
    },
    "industry": {
        "label": "行业动态",
        "keywords": ["业绩", "营收", "净利润", "保费", "赔付", "综合成本率",
                      "并购", "入股", "增资", "人事变动", "高管", "辞职", "任职",
                      "上市", "发行", "规模", "市场份额", "排名", "同比", "环比"],
    },
    "research": {
        "label": "研究报告",
        "keywords": ["研报", "研究报告", "白皮书", "行业报告", "策略报告",
                      "分析师", "评级", "增持", "减持", "目标价", "券商",
                      "中金", "中信", "华泰", "国泰君安", "招商证券"],
    },
    "insights": {
        "label": "技巧与观点",
        "keywords": ["观点", "技巧", "经验", "建议", "如何", "方法论", "展业",
                      "话术", "获客", "转介绍", "续期", "培训", "考核"],
    },
}


def classify_item(title: str, summary: str = "", default_category: str = "industry") -> str:
    """基于规则对条目进行分类"""
    text = f"{title} {summary}".lower()

    # 按优先级逐类匹配
    for cat_slug, cat_info in CATEGORY_RULES.items():
        for kw in cat_info["keywords"]:
            if kw.lower() in text:
                return cat_slug

    return default_category


def generate_lead(sections: List[Dict]) -> Dict:
    """生成日报导语（主编点评）"""
    total_items = sum(len(s.get("items", [])) for s in sections)
    active_sections = [s for s in sections if s.get("items")]

    if not active_sections:
        return {"title": "暂无重大动态", "leadParagraph": "今日金融保险行业暂无重大动态更新。"}

    # 统计各类条目数
    section_summary = "、".join(
        f"{s['label']}{len(s['items'])}条" for s in active_sections
    )

    # 找出最热门的分类
    top_section = max(active_sections, key=lambda s: len(s["items"]))

    lead_title = f"今日金融保险圈共{total_items}条动态，{top_section['label']}最活跃"
    lead_paragraph = f"今日金融保险圈共收录{total_items}条动态，涉及{section_summary}。重点关注{top_section['label']}板块。"

    return {"title": lead_title, "leadParagraph": lead_paragraph}


def load_rss_data(input_dir: str) -> List[Dict]:
    """从 RSS 采集结果加载数据"""
    latest_file = os.path.join(input_dir, "latest_rss_data.json")
    if not os.path.exists(latest_file):
        # 尝试找最新的 rss_data_*.json
        files = [f for f in os.listdir(input_dir) if f.startswith("rss_data_") and f.endswith(".json")]
        if files:
            files.sort(reverse=True)
            latest_file = os.path.join(input_dir, files[0])
        else:
            print(f"[日报] 未找到 RSS 数据文件在 {input_dir}")
            return []

    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("items", [])


def merge_data(rss_items: List[Dict], extra_items: Optional[List[Dict]] = None) -> List[Dict]:
    """合并多个数据源的条目，按 URL 去重"""
    seen_urls = set()
    merged = []

    for item in rss_items:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            merged.append(item)

    if extra_items:
        for item in extra_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)
            elif not url:
                merged.append(item)

    return merged


def build_daily(items: List[Dict], date_str: Optional[str] = None) -> Dict:
    """将条目列表构建为日报结构"""
    # 确定日期
    if date_str:
        target_date = date_str
    else:
        # 北京时间
        now_bj = datetime.now(timezone(timedelta(hours=8)))
        target_date = now_bj.strftime("%Y-%m-%d")

    # 分类到五版块
    sections = []
    for cat_slug, cat_info in CATEGORY_RULES.items():
        cat_items = [item for item in items if item.get("category") == cat_slug]
        if cat_items:
            section_items = []
            for item in cat_items:
                section_items.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", "")[:200] if item.get("summary") else "",
                    "sourceUrl": item.get("url", ""),
                    "sourceName": item.get("source", ""),
                })
            sections.append({
                "label": cat_info["label"],
                "items": section_items,
            })

    # 确保5个版块都存在（即使为空）
    existing_labels = {s["label"] for s in sections}
    for cat_slug, cat_info in CATEGORY_RULES.items():
        if cat_info["label"] not in existing_labels:
            sections.append({"label": cat_info["label"], "items": []})

    # 按固定顺序排列
    label_order = [info["label"] for info in CATEGORY_RULES.values()]
    sections.sort(key=lambda s: label_order.index(s["label"]) if s["label"] in label_order else 99)

    # 生成导语
    lead = generate_lead(sections)

    # 快讯（取行业动态的前5条，格式简化）
    flashes = []
    industry_section = next((s for s in sections if s["label"] == "行业动态"), None)
    if industry_section:
        for item in industry_section.get("items", [])[:5]:
            flashes.append({
                "title": item["title"],
                "sourceName": item["sourceName"],
                "sourceUrl": item["sourceUrl"],
                "publishedAt": "",
            })

    daily = {
        "date": target_date,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "windowStart": f"{target_date}T00:00:00.000Z",
        "windowEnd": f"{target_date}T23:59:59.999Z",
        "lead": lead,
        "sections": sections,
        "flashes": flashes,
    }

    return daily


def daily_to_markdown(daily: Dict) -> str:
    """将日报 JSON 转为 Markdown 格式"""
    lines = []
    lines.append(f"**金融保险日报 · {daily['date']}**")
    lines.append("")

    # 导语
    if daily.get("lead"):
        lead = daily["lead"]
        if lead.get("title"):
            lines.append(f"> {lead['title']}")
            lines.append(">")
            if lead.get("leadParagraph"):
                lines.append(f"> {lead['leadParagraph']}")
            lines.append("")

    # 各版块
    counter = 1
    for section in daily.get("sections", []):
        items = section.get("items", [])
        if not items:
            continue

        lines.append(f"## {section['label']}")
        for item in items:
            title = item.get("title", "")
            source = item.get("sourceName", "")
            summary = item.get("summary", "")
            url = item.get("sourceUrl", "")

            line = f"{counter}. **{title}** — {source}"
            lines.append(line)

            if summary:
                # 截取50字内
                short_summary = summary[:50] + ("..." if len(summary) > 50 else "")
                lines.append(f"   {short_summary}")

            if url:
                lines.append(f"   {url}")

            counter += 1

        lines.append("")

    # 快讯
    flashes = daily.get("flashes", [])
    if flashes:
        lines.append("## 快讯")
        for flash in flashes:
            title = flash.get("title", "")
            source = flash.get("sourceName", "")
            url = flash.get("sourceUrl", "")
            lines.append(f"- **{title}** — {source}")
            if url:
                lines.append(f"  {url}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="finhot 日报生成器")
    parser.add_argument("--input", "-i", default="./data", help="RSS 数据目录")
    parser.add_argument("--output", "-o", default="./daily", help="日报输出目录")
    parser.add_argument("--date", "-d", default=None, help="指定日报日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--extra", "-e", default=None, help="额外数据 JSON 文件路径")
    parser.add_argument("--markdown", "-m", action="store_true", help="同时输出 Markdown 格式")
    args = parser.parse_args()

    # 加载 RSS 数据
    rss_items = load_rss_data(args.input)
    print(f"[日报] 加载 RSS 数据: {len(rss_items)} 条")

    # 加载额外数据
    extra_items = []
    if args.extra and os.path.exists(args.extra):
        with open(args.extra, "r", encoding="utf-8") as f:
            extra_data = json.load(f)
            extra_items = extra_data.get("items", [])
        print(f"[日报] 加载额外数据: {len(extra_items)} 条")

    # 合并去重
    all_items = merge_data(rss_items, extra_items)
    print(f"[日报] 合并去重后: {len(all_items)} 条")

    # 重新分类（确保一致性）
    for item in all_items:
        if "category" not in item or not item["category"]:
            item["category"] = classify_item(
                item.get("title", ""),
                item.get("summary", "")
            )

    # 构建日报
    daily = build_daily(all_items, args.date)

    # 统计
    total = sum(len(s.get("items", [])) for s in daily["sections"])
    print(f"[日报] 生成日报: {daily['date']}, 共 {total} 条")

    # 保存 JSON
    os.makedirs(args.output, exist_ok=True)
    json_file = os.path.join(args.output, f"daily_{daily['date']}.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(daily, f, ensure_ascii=False, indent=2)
    print(f"[日报] JSON 已保存: {json_file}")

    # 保存最新日报
    latest_file = os.path.join(args.output, "latest_daily.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(daily, f, ensure_ascii=False, indent=2)

    # 保存 Markdown
    if args.markdown:
        md_content = daily_to_markdown(daily)
        md_file = os.path.join(args.output, f"daily_{daily['date']}.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[日报] Markdown 已保存: {md_file}")

    print(f"\n✅ 日报生成完成: {total} 条动态, {len(daily['sections'])} 个版块")


if __name__ == "__main__":
    main()
