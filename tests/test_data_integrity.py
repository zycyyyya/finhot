import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DailyGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daily = load_module("daily_generator", ROOT / "scripts" / "daily_generator.py")

    def test_beijing_date_filter_and_window(self):
        items = [
            {
                "title": "北京时间七月三十日早间资讯",
                "url": "https://example.com/1",
                "source": "测试源",
                "summary": "摘要",
                "category": "industry",
                "publishedAt": "2026-07-29T16:30:00Z",
            },
            {
                "title": "北京时间七月三十一日资讯",
                "url": "https://example.com/2",
                "source": "测试源",
                "summary": "摘要",
                "category": "industry",
                "publishedAt": "2026-07-30T16:30:00Z",
            },
            {
                "title": "缺少时间的历史线索",
                "url": "https://example.com/3",
                "source": "测试源",
                "summary": "摘要",
                "category": "industry",
                "publishedAt": None,
            },
        ]
        result = self.daily.build_daily(items, "2026-07-30")
        industry = next(section for section in result["sections"] if section["label"] == "行业动态")
        self.assertEqual([item["title"] for item in industry["items"]], ["北京时间七月三十日早间资讯"])
        self.assertEqual(result["windowStart"], "2026-07-29T16:00:00Z")
        self.assertEqual(result["windowEnd"], "2026-07-30T16:00:00Z")
        self.assertEqual(industry["items"][0]["publishedAt"], "2026-07-29T16:30:00Z")

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            self.daily.build_daily([], "2026-99-99")


class WebBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.webbridge = load_module("webbridge_fetcher", ROOT / "scripts" / "webbridge_fetcher.py")

    def test_url_protocol_allowlist(self):
        self.assertTrue(self.webbridge.is_safe_http_url("https://example.com/a"))
        self.assertFalse(self.webbridge.is_safe_http_url("javascript:alert(1)"))
        self.assertFalse(self.webbridge.is_safe_http_url("file:///tmp/test"))

    def test_invalid_time_is_unknown(self):
        self.assertIsNone(self.webbridge.normalize_published_at("bad-date"))
        self.assertEqual(
            self.webbridge.normalize_published_at("2026-07-30T08:00:00Z"),
            "2026-07-30T08:00:00Z",
        )


if __name__ == "__main__":
    unittest.main()
