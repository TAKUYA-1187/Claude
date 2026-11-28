"""朝レポート取込のテスト（鮮度ガード・冪等性・除外・中古除外）"""
import csv
import os
import shutil
import tempfile
import unittest

import import_kaitori_report as imp
import ledger

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.relpath(os.path.join(HERE, "..", "data", "output", "kaitorishouten_all_latest.csv"))  # 相対パスでも判定できること
COLS = ["jan", "ec_name", "kaitori_name", "kaitori_price", "yahoo_price", "shipping", "profit", "profit_rate",
        "point_rate", "effective_cost", "effective_profit", "effective_profit_rate", "note", "kaitori_url", "category"]


def make_report(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


SAMPLE = [  # 【テスト】表記のテスト用データ
    {"jan": "4902370552683", "kaitori_name": "【テスト】除外品", "kaitori_price": "50000", "yahoo_price": "40000",
     "shipping": "600", "point_rate": "0.05"},
    {"jan": "4948872017084", "kaitori_name": "【テスト】中古品", "kaitori_price": "34500", "yahoo_price": "27580",
     "shipping": "600", "point_rate": "0.05", "note": "要確認: 中古"},
    {"jan": "4549995429213", "kaitori_name": "【テスト】新品", "kaitori_price": "21500", "yahoo_price": "20000",
     "shipping": "600", "point_rate": "0.05"},
    {"jan": "4549995429213", "kaitori_name": "【テスト】新品（重複行）", "kaitori_price": "21500", "yahoo_price": "20000",
     "shipping": "600", "point_rate": "0.05"},
]


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.led = os.path.join(self.d, "ledger")
        os.makedirs(self.led)
        shutil.copy(os.path.join(HERE, "..", "ledger_data", "excluded.csv"), self.led)
        self.rep = os.path.join(self.d, "report.csv")
        make_report(self.rep, SAMPLE)

    def test_real_report_is_stale_and_refused(self):
        # リポジトリ上のデータを、生成から36時間を超えた時点で取り込もうとすると拒否される
        try:
            code = imp.main(["--report", REPORT, "--ledger-dir", self.led, "--now", "2027-01-31T12:00:00+09:00"])
        except SystemExit as e:
            code = 2 if "取込中止" in str(e.code) else e.code
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(os.path.join(self.led, "master.csv")))

    def test_fresh_import_idempotent_excluded_and_used(self):
        args = ["--report", self.rep, "--ledger-dir", self.led]
        imp.main(args)
        m1 = read(os.path.join(self.led, "master.csv"))
        h1 = read(os.path.join(self.led, "history.csv"))
        imp.main(args)  # 同じレポートを再取込
        m2 = read(os.path.join(self.led, "master.csv"))
        h2 = read(os.path.join(self.led, "history.csv"))
        self.assertEqual(len(m1), 1)          # 除外品・中古品は入らず、重複行は1行に統合
        self.assertEqual(m1, m2)
        self.assertEqual(len(h1), len(h2))
        row = m1[0]
        self.assertEqual(row["JANコード"], "4549995429213")
        self.assertEqual(row["基準判定"], "未確認（暫定）")   # 仕入送料・その他経費・在庫が未確認
        self.assertEqual(row["現金利益"], "")                 # 0で埋めて計算しない
        self.assertIn("データ日時", row["情報源"])

    def _status(self, status, generated):
        import json
        with open(os.path.join(self.d, "kaitori_run_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": status, "data_generated_at": generated, "reasons": []}, f, ensure_ascii=False)

    def test_status_failure_refused(self):
        self._status("取得失敗", "2026-11-28 09:00:00")
        self.assertEqual(imp.main(["--report", self.rep, "--ledger-dir", self.led,
                                   "--now", "2026-11-28T10:00:00+09:00"]), 2)

    def test_status_stale_refused_and_fresh_accepted(self):
        self._status("部分成功", "2026-11-26 09:00:00")
        self.assertEqual(imp.main(["--report", self.rep, "--ledger-dir", self.led,
                                   "--now", "2026-11-28T10:00:00+09:00"]), 2)
        self._status("部分成功", "2026-11-28 09:00:00")
        self.assertIn(imp.main(["--report", self.rep, "--ledger-dir", self.led,
                                "--now", "2026-11-28T10:00:00+09:00"]), (0, 1))
        self.assertEqual(len(read(os.path.join(self.led, "master.csv"))), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
