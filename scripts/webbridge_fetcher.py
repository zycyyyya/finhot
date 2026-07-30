#!/usr/bin/env python3
"""
Kimi WebBridge 数据采集模块
通过浏览器 daemon 抓取自定义金融/保险资讯站点，作为 finhot 的扩展数据源。

依赖：Kimi WebBridge daemon 运行在 127.0.0.1:10086，浏览器扩展已连接。
仅使用标准库（urllib），不依赖 pip 第三方包。
"""

import urllib.request
import json
import time
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse

DAEMON_URL = "http://127.0.0.1:10086/command"
VALID_CATEGORIES = {"regulatory", "products", "industry", "research", "insights"}
MAX_FIELD_LENGTH = 5000


def _call_daemon(action: str, args: Optional[dict] = None, session: str = "finhot-webbridge") -> dict:
    """调用 Kimi WebBridge daemon API"""
    payload = json.dumps({
        "action": action,
        "args": args or {},
        "session": session
    }).encode("utf-8")

    req = urllib.request.Request(
        DAEMON_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode("utf-8"))


def health_check() -> dict:
    """检查 daemon 健康状态"""
    url = "http://127.0.0.1:10086/status"
    resp = urllib.request.urlopen(url, timeout=5)
    return json.loads(resp.read().decode("utf-8"))


def is_safe_http_url(value: str) -> bool:
    """仅允许 http/https，阻止 javascript/file/data 等危险协议。"""
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_published_at(value) -> Optional[str]:
    """返回规范 UTC ISO 时间；缺失或无法解析时返回 None。"""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return None


def navigate(url: str, session: str = "finhot-webbridge") -> bool:
    """导航到经过协议校验的目标 URL。"""
    if not is_safe_http_url(url):
        return False
    result = _call_daemon("navigate", {"url": url, "newTab": True}, session)
    return result.get("ok", False) and result.get("data", {}).get("success", False)


def evaluate(code: str, session: str = "finhot-webbridge") -> Optional[str]:
    """在页面执行 JS 并返回结果"""
    result = _call_daemon("evaluate", {"code": code}, session)
    if result.get("ok"):
        return result.get("data", {}).get("value")
    return None


def load_sources_config(config_path: Optional[str] = None) -> dict:
    """加载信息源配置文件"""
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "webbridge_sources.json")

    if not os.path.exists(config_path):
        return {"sources": []}

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_from_source(source: dict, session: str = "finhot-webbridge") -> List[Dict]:
    """
    从单个信息源抓取数据。
    source 结构：
    {
        "name": "源名称",
        "url": "https://...",
        "category": "regulatory|products|industry|research|insights",
        "enabled": true,
        "extraction": {
            "type": "evaluate",
            "code": "JS 代码，返回 JSON 字符串数组"
        }
    }
    """
    name = source.get("name", "未知来源")
    url = source.get("url", "")
    category = source.get("category", "industry")
    if category not in VALID_CATEGORIES:
        category = "industry"
    extraction = source.get("extraction", {})

    results = []

    try:
        if not navigate(url, session):
            print(f"[WebBridge] {name}: 导航失败 {url}")
            return results

        time.sleep(2)  # 等待页面加载

        code = extraction.get("code", "")
        if not code:
            print(f"[WebBridge] {name}: 未配置提取代码")
            return results

        raw = evaluate(code, session)
        if not raw:
            print(f"[WebBridge] {name}: 提取结果为空")
            return results

        items = json.loads(raw)
        if not isinstance(items, list):
            raise ValueError("提取结果必须是 JSON 数组")

        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        for raw_item in items[:50]:
            if isinstance(raw_item, str):
                item = {"title": raw_item, "url": url}
            elif isinstance(raw_item, dict):
                item = dict(raw_item)
            else:
                continue

            title = str(item.get("title", "")).strip()[:500]
            item_url = item.get("url") or url
            if len(title) < 4 or not is_safe_http_url(item_url):
                continue

            published_at = normalize_published_at(item.get("publishedAt"))
            summary = str(item.get("summary", "")).strip()[:MAX_FIELD_LENGTH]
            results.append({
                "title": title,
                "url": item_url,
                "summary": summary,
                "source": name,
                "category": category,
                "publishedAt": published_at,
                "fetchedAt": fetched_at,
                "timeConfidence": "source" if published_at else "unknown",
            })

        print(f"[WebBridge] {name}: 获取 {len(results)} 条")

    except Exception as e:
        print(f"[WebBridge] {name}: 错误 - {e}")

    return results


def fetch_all(sources: Optional[List[dict]] = None, config_path: Optional[str] = None) -> List[Dict]:
    """
    从所有启用的信息源抓取数据。
    若不传 sources，则从配置文件加载。
    """
    if sources is None:
        config = load_sources_config(config_path)
        sources = [s for s in config.get("sources", []) if s.get("enabled", False)]

    all_data = []

    # 健康检查
    try:
        status = health_check()
        if not status.get("extension_connected"):
            print("[WebBridge] 浏览器扩展未连接，跳过 WebBridge 数据源")
            return all_data
        print(f"[WebBridge] daemon v{status.get('version')} 已连接，开始采集...")
    except Exception as e:
        print(f"[WebBridge] daemon 不可用: {e}")
        return all_data

    for i, source in enumerate(sources):
        # 各源用独立 session 避免冲突
        items = fetch_from_source(source, f"finhot-wb-{i}")
        all_data.extend(items)

    return all_data


def save_to_json(data: List[Dict], output_path: str):
    """保存数据到 JSON 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(data),
            "items": data,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_type": "webbridge"
        }, f, ensure_ascii=False, indent=2)
    print(f"[WebBridge] 数据已保存: {output_path} ({len(data)} 条)")


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python webbridge_fetcher.py <output_dir> [config_path]")
        sys.exit(1)

    output_dir = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else None

    os.makedirs(output_dir, exist_ok=True)

    data = fetch_all(config_path=config_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"webbridge_data_{timestamp}.json")
    save_to_json(data, output_file)


if __name__ == "__main__":
    main()