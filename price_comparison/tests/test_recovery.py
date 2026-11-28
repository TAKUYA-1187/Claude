"""復旧版の取得処理テスト（ネットワークはすべてモック）"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import yahoo_budget as yb  # noqa: E402


class Resp:
    def __init__(self, code=200, data=None):
        self.status_code, self._d = code, data or {}
        self.ok = code < 400
        self.text = json.dumps(self._d)

    def json(self):
        return self._d

    def raise_for_status(self):
        if not self.ok:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


class BudgetTest(unittest.TestCase):
    def setUp(self):
        self.state = Path(tempfile.mkdtemp()) / "u.json"
        os.environ["YAHOO_MIN_INTERVAL"] = "0"

    def test_429_stops_immediately_without_retry_and_persists(self):
        b = yb.YahooBudget(self.state)
        with mock.patch("requests.get", return_value=Resp(429)) as g:
            with self.assertRaises(yb.RateLimited):
                b.get({"x": 1})
            with self.assertRaises(yb.RateLimited):   # 2回目は通信すらしない
                b.get({"x": 2})
        self.assertEqual(g.call_count, 1)
        b2 = yb.YahooBudget(self.state)               # 同じ日の別実行でも止まったまま
        self.assertIsNotNone(b2.stopped_reason)
        self.assertEqual(b2.remaining(), 0)
        os.environ["YAHOO_COOLDOWN_MIN"] = "0"           # 冷却期間が過ぎれば再開できる
        try:
            self.assertIsNone(yb.YahooBudget(self.state).stopped_reason)
        finally:
            del os.environ["YAHOO_COOLDOWN_MIN"]

    def test_run_budget(self):
        os.environ["YAHOO_RUN_BUDGET"] = "2"
        try:
            b = yb.YahooBudget(self.state)
            with mock.patch("requests.get", return_value=Resp(200, {"hits": []})):
                b.get({}); b.get({})
                with self.assertRaises(yb.BudgetExhausted):
                    b.get({})
        finally:
            del os.environ["YAHOO_RUN_BUDGET"]

    def test_client_dedup_and_jan_match(self):
        from src.yahoo_client import YahooClient
        b = yb.YahooBudget(self.state)
        hits = {"hits": [{"janCode": "4549995429213", "price": 1000}, {"janCode": "9999999999999", "price": 10}]}
        with mock.patch("requests.get", return_value=Resp(200, hits)) as g:
            c = YahooClient("id", b)
            self.assertEqual(c.min_price_by_jan("4549995429213"), 1000)   # 別JANの安値は採用しない
            self.assertEqual(c.min_price_by_jan("4549995429213"), 1000)
        self.assertEqual(g.call_count, 1)


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        os.environ.update(YAHOO_MIN_INTERVAL="0", CRAWL_THROTTLE="0", YAHOO_APP_ID="id", KAITORI_MIN_ITEMS="1")
        import importlib
        import kaitori_catalog as kc
        self.kc = importlib.reload(kc)
        self.kc.OUT_DIR, self.kc.STATE_DIR = self.tmp / "out", self.tmp / "state"
        self.kc.CACHE_FILE = self.kc.STATE_DIR / "c.json"
        self.kc.ROTATION_FILE = self.kc.STATE_DIR / "r.json"
        self.kc.STATUS_FILE = self.kc.OUT_DIR / "s.json"
        yb.YahooBudget._instance = yb.YahooBudget(self.tmp / "u.json")

    def kaitori_pages(self, items_per_page):
        pages = []
        total = sum(len(p) for p in items_per_page)
        for i, items in enumerate(items_per_page, 1):
            pages.append(Resp(200, {"items": items, "page": i, "per_page": 100, "total": total}))
        return pages

    def test_end_to_end_and_cache_diff(self):
        items = [{"id": 1, "name": "【テスト】新品あり", "jan": "4549995429213", "price_new": {"amount": 21500}},
                 {"id": 2, "name": "【テスト】中古のみ", "jan": "4549995429220", "price_new": None,
                  "price_old": {"amount": 79000}},
                 {"id": 3, "name": "【テスト】JANなし", "jan": "", "price_new": {"amount": 5000}}]
        yahoo = Resp(200, {"hits": [{"janCode": "4549995429213", "price": 20000, "name": "【テスト】Y", "url": "u",
                                     "shipping": {"name": "送料無料"}}]})
        sess = mock.Mock()
        sess.headers = {}
        sess.get.side_effect = self.kaitori_pages([items])
        with mock.patch("requests.Session", return_value=sess), mock.patch("requests.get", return_value=yahoo) as g:
            self.kc.main()
        st = json.loads(self.kc.STATUS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(st["kaitori"]["unique_jan_new_price"], 1)
        self.assertEqual(st["yahoo"]["queried"], 1)
        self.assertEqual(st["status"], "正常終了")
        self.assertEqual(g.call_count, 1)
        import csv
        rows = list(csv.DictReader(open(self.kc.OUT_DIR / "kaitorishouten_all_latest.csv", encoding="utf-8-sig")))
        self.assertEqual(rows[0]["profit"], "900")          # 21500-20000-600
        # 2回目：キャッシュが新しいのでYahooに問い合わせない（差分取得）
        sess.get.side_effect = self.kaitori_pages([items])
        with mock.patch("requests.Session", return_value=sess), mock.patch("requests.get", return_value=yahoo) as g2:
            self.kc.main()
        self.assertEqual(g2.call_count, 0)

    def test_zero_items_is_failure_and_keeps_outputs(self):
        self.kc.OUT_DIR.mkdir(parents=True)
        (self.kc.OUT_DIR / "kaitorishouten_all_latest.csv").write_text("old", encoding="utf-8")
        sess = mock.Mock()
        sess.headers = {}
        sess.get.side_effect = self.kaitori_pages([[]])
        with mock.patch("requests.Session", return_value=sess):
            self.kc.main()
        st = json.loads(self.kc.STATUS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(st["status"], "取得失敗")
        self.assertEqual((self.kc.OUT_DIR / "kaitorishouten_all_latest.csv").read_text(encoding="utf-8"), "old")

    def test_rotation_oldest_first_and_429_partial(self):
        cache = {"4549995429213": {"checked_at": "2026-11-01 00:00:00", "price": 1},
                 "4549995429206": {"checked_at": "2026-11-20 00:00:00", "price": 1}}
        order = []

        def fake(url, params=None, timeout=None):
            order.append(params["jan_code"])
            return Resp(429)
        with mock.patch("requests.get", side_effect=fake):
            st = self.kc.refresh_yahoo(["4549995429206", "4549995429213", "4549995429220"], cache,
                                       yb.YahooBudget._instance)
        self.assertEqual(order, ["4549995429220"])    # 未調査が最優先、429で即停止
        self.assertIn("429", st["stopped_reason"])

    def test_category_round_robin_and_rotation(self):
        catalog = {"1": {"category": "A", "price": 100}, "2": {"category": "A", "price": 900},
                   "3": {"category": "B", "price": 50}, "4": {"category": "C", "price": 70}}
        order, cats = self.kc.prioritize(list(catalog), catalog, {})
        self.assertEqual(order, ["2", "3", "4", "1"])     # A(高額)→B→C→A の順に1件ずつ
        self.kc.save_rotation(cats, ["2", "3"], catalog)  # Bまで調べた → 次回はCから
        order2, _ = self.kc.prioritize(list(catalog), catalog, {})
        self.assertEqual(order2[0], "4")

    def test_store_caution(self):
        self.assertIn("ストア名にアウトレット", self.kc.caution_note("SONY α7R V", "秋葉原 アウトレットプラザ"))
        self.assertEqual(self.kc.caution_note("SONY α7R V", "ヨドバシ"), "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
