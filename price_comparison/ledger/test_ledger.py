"""テスト用データ（実在商品の価格ではない。すべて【テスト】表記）で台帳処理を検証"""
import csv
import os
import tempfile
import unittest

import ledger

BASE = {
    "販売先": "Amazon", "仕入送料": "0", "販売手数料": "1000", "発送費用": "500",
    "その他経費": "0", "推定月間販売数": "120", "在庫状況": "在庫あり", "出品制限": "なし",
}


def write(path, rows):
    cols = ledger.MASTER_COLS
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**BASE, **r})


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.inp = os.path.join(self.d, "in.csv")

    def run_merge(self, rows):
        write(self.inp, rows)
        return ledger.merge(self.d, self.inp)

    def test_profit_and_pass(self):
        r = self.run_merge([{"調査日時": "2026-11-28 09:00", "商品名": "【テスト】A",
                             "JANコード": "4902370552683", "ASIN": "B0TEST0001",
                             "仕入価格": "10000", "販売価格": "13000", "獲得ポイント": "500"}])
        m = read(os.path.join(self.d, "master.csv"))[0]
        self.assertEqual(m["現金利益"], "1500")          # 13000-10000-1000-500
        self.assertEqual(m["ポイント込み利益"], "2000")
        self.assertEqual(m["利益率"], "11.5")
        self.assertEqual(m["基準判定"], "合格")
        self.assertEqual(r["passed_total"], 1)

    def test_shortfall_reason(self):
        # Liberty 5 のような「500円に44円不足」を正しく不合格にする
        self.run_merge([{"調査日時": "2026-11-28 09:00", "商品名": "【テスト】B", "JANコード": "4902370552683",
                         "ASIN": "B0TEST0001", "仕入価格": "10000", "販売価格": "11956"}])
        m = read(os.path.join(self.d, "master.csv"))[0]
        self.assertEqual(m["現金利益"], "456")
        self.assertEqual(m["基準判定"], "不合格")
        self.assertIn("44円不足", m["基準未達・未確認の理由"])

    def test_missing_values_are_unconfirmed_not_zero(self):
        self.run_merge([{"調査日時": "2026-11-28 09:00", "商品名": "【テスト】C", "型番": "XYZ-1",
                         "仕入価格": "1000", "販売価格": "3000", "販売手数料": "", "推定月間販売数": ""}])
        m = read(os.path.join(self.d, "master.csv"))[0]
        self.assertEqual(m["現金利益"], "")
        self.assertEqual(m["基準判定"], "未確認（暫定）")
        self.assertIn("販売手数料", m["基準未達・未確認の理由"])

    def test_dedup_by_asin_and_model_and_history(self):
        a = {"商品名": "【テスト】D", "ASIN": "B0TEST0002", "型番": "ab-100", "仕入価格": "5000", "販売価格": "8000"}
        self.run_merge([{**a, "調査日時": "2026-11-27 09:00"},
                        {**a, "調査日時": "2026-11-28 09:00", "型番": "AB100"},            # 表記揺れ・変化なし
                        {**a, "調査日時": "2026-11-28 12:00", "仕入価格": "4800"},        # 値下がり
                        {**a, "調査日時": "2026-11-28 15:00", "仕入価格": "5000"}])       # 元の価格に戻る
        master = read(os.path.join(self.d, "master.csv"))
        hist = read(os.path.join(self.d, "history.csv"))
        self.assertEqual(len(master), 1)
        self.assertEqual(master[0]["仕入価格"], "5000")
        self.assertEqual([h["仕入価格"] for h in hist], ["5000", "4800", "5000"])
        # 同じ調査を再取込しても履歴は増えない
        self.run_merge([{**a, "調査日時": "2026-11-28 15:00", "仕入価格": "5000"}])
        self.assertEqual(len(read(os.path.join(self.d, "history.csv"))), 3)

    def test_excluded_not_readded(self):
        with open(os.path.join(self.d, "excluded.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ledger.EXCLUDED_COLS)
            w.writeheader()
            w.writerow({"商品キー": "JAN:4902370552683", "JANコード": "4902370552683",
                        "商品名": "【テスト】除外品", "除外理由": "購入条件を満たさない", "除外日": "2026-11-28", "判断者": "Inoue"})
        r = self.run_merge([{"調査日時": "2026-11-28 09:00", "商品名": "【テスト】E", "JANコード": "4902370552683",
                             "仕入価格": "1", "販売価格": "99999"}])
        self.assertEqual(r["skipped_excluded"], ["【テスト】E"])
        self.assertEqual(read(os.path.join(self.d, "master.csv")), [])

    def test_conflicting_model_is_held(self):
        base = {"商品名": "【テスト】F", "JANコード": "4902370552683", "仕入価格": "1000", "販売価格": "3000"}
        self.run_merge([{**base, "調査日時": "2026-11-28 09:00", "型番": "COLOR-BLACK"}])
        r = self.run_merge([{**base, "調査日時": "2026-11-28 10:00", "型番": "COLOR-WHITE", "仕入価格": "900"}])
        self.assertEqual(len(r["conflicts"]), 1)
        self.assertEqual(read(os.path.join(self.d, "master.csv"))[0]["仕入価格"], "1000")

    def test_invalid_jan_rejected(self):
        r = self.run_merge([{"調査日時": "2026-11-28 09:00", "商品名": "【テスト】G", "JANコード": "4902370552684",
                             "仕入価格": "1", "販売価格": "2"}])
        self.assertEqual(len(r["rejected"]), 1)

    def test_kaitori_route(self):
        # 買取差益：販売価格なし・買取価格あり。月間販売数とASINは不要
        self.run_merge([{"調査日時": "2026-11-28 09:00", "商品名": "【テスト】H", "JANコード": "4902370552683",
                         "販売先": "買取商店", "仕入価格": "20000", "買取価格": "21500", "販売手数料": "0",
                         "発送費用": "600", "推定月間販売数": "", "出品制限": ""}])
        m = read(os.path.join(self.d, "master.csv"))[0]
        self.assertEqual(m["現金利益"], "900")
        self.assertEqual(m["基準判定"], "合格")


if __name__ == "__main__":
    unittest.main(verbosity=1)
