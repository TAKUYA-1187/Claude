"""Amazon出品時の手数料と利益見込みを概算する簡易料金シミュレーター。

公式の料金シミュレーター (https://sellercentral.amazon.co.jp/revcalpublic?lang=ja_JP)
と同じ考え方で以下を差し引いて手取りを計算する:

  手取り = 販売価格 − 販売手数料 − カテゴリー成約料 − FBA配送代行料 − 手数料への消費税

- 販売手数料率はカテゴリで変動する (8〜15%)。カテゴリ名のキーワードから推定し、
  不明な場合は AMAZON_REFERRAL_FEE_RATE (デフォルト10%) を使う。
- カテゴリー成約料はメディア商品のみ (本80円 / CD・DVD等140円)。
- FBA配送代行料は商品サイズ・重量で変動するため、AMAZON_FBA_FEE で一律の概算値を
  設定する (デフォルト500円 = 標準サイズ相当)。
- 手数料には消費税 (AMAZON_FEE_TAX_RATE、デフォルト10%) が上乗せされる。

あくまで概算のため、仕入れ前の最終確認は公式シミュレーターで行うこと。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# カテゴリ名キーワード → 販売手数料率 (2025年時点の日本の料率の概算)
CATEGORY_REFERRAL_RATES: list[tuple[str, float]] = [
    # メディア (15%)
    ("本", 0.15), ("書籍", 0.15), ("雑誌", 0.15), ("コミック", 0.15),
    ("CD", 0.15), ("ミュージック", 0.15), ("レコード", 0.15),
    ("DVD", 0.15), ("ブルーレイ", 0.15), ("Blu-ray", 0.15), ("ビデオ", 0.15),
    ("ゲーム", 0.15), ("テレビゲーム", 0.15),
    # 家電・カメラ・PC (8%)
    ("家電", 0.08), ("カメラ", 0.08), ("AV機器", 0.08), ("オーディオ", 0.08),
    ("パソコン", 0.08), ("PC", 0.08), ("周辺機器", 0.08),
    # その他主要カテゴリ
    ("おもちゃ", 0.10), ("ホビー", 0.10), ("フィギュア", 0.10),
    ("腕時計", 0.15), ("時計", 0.15), ("ジュエリー", 0.15),
    ("ドラッグストア", 0.10), ("ビューティー", 0.10), ("コスメ", 0.10), ("化粧", 0.10),
    ("食品", 0.10), ("飲料", 0.10),
    ("スポーツ", 0.10), ("アウトドア", 0.10),
    ("文房具", 0.15), ("オフィス", 0.15),
    ("ホーム", 0.15), ("キッチン", 0.15), ("インテリア", 0.15),
    ("ファッション", 0.15), ("シューズ", 0.15), ("バッグ", 0.15), ("服", 0.15),
    ("楽器", 0.10),
]

# メディア商品のカテゴリー成約料 (円)
CATEGORY_CLOSING_FEES: list[tuple[str, int]] = [
    ("本", 80), ("書籍", 80), ("雑誌", 80), ("コミック", 80),
    ("CD", 140), ("ミュージック", 140), ("レコード", 140),
    ("DVD", 140), ("ブルーレイ", 140), ("Blu-ray", 140), ("ビデオ", 140),
]

SIMULATOR_URL = "https://sellercentral.amazon.co.jp/revcalpublic?lang=ja_JP"


@dataclass
class FeeEstimate:
    sell_price: int
    referral_rate: float
    referral_fee: int
    closing_fee: int
    fba_fee: int
    fee_tax: int

    @property
    def total_fees(self) -> int:
        return self.referral_fee + self.closing_fee + self.fba_fee + self.fee_tax

    @property
    def net_proceeds(self) -> int:
        """Amazonから入金される手取り額。"""
        return self.sell_price - self.total_fees


def _match(category: Optional[str], table: list[tuple[str, float]] | list[tuple[str, int]]):
    if not category:
        return None
    for keyword, value in table:
        if keyword.lower() in category.lower():
            return value
    return None


def estimate_fees(
    sell_price: int,
    category: Optional[str] = None,
    default_referral_rate: float = 0.10,
    fba_fee: float = 500,
    fee_tax_rate: float = 0.10,
) -> FeeEstimate:
    rate = _match(category, CATEGORY_REFERRAL_RATES)
    if rate is None:
        rate = default_referral_rate
    referral = int(round(sell_price * rate))
    closing = _match(category, CATEGORY_CLOSING_FEES) or 0
    fba = int(round(fba_fee))
    tax = int(round((referral + closing + fba) * fee_tax_rate))
    return FeeEstimate(
        sell_price=sell_price,
        referral_rate=rate,
        referral_fee=referral,
        closing_fee=int(closing),
        fba_fee=fba,
        fee_tax=tax,
    )
