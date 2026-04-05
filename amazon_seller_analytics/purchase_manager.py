"""
仕入れ管理モジュール
====================
Yahoo Shopping / 楽天市場 / 買取商店 / WIKI などからの
仕入れ (購入) 履歴を管理・分析するモジュール。

デモデータ: 70件 (2025-07-01 〜 2026-03-31, seed=42)
"""

import random
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List
from config import APP_CONFIG

random.seed(42)

# ---- 商品マスタ (12品) ----
PRODUCTS = [
    {"name": "ワイヤレスイヤホン Pro",        "asin": "B08XYZ001", "category": "家電・カメラ",
     "buy_range": (4_000, 6_000),  "sell_price": 8_800},
    {"name": "スマートウォッチ SE",            "asin": "B08XYZ002", "category": "家電・カメラ",
     "buy_range": (7_000, 10_000), "sell_price": 15_800},
    {"name": "USBハブ 7ポート",               "asin": "B08XYZ003", "category": "パソコン・周辺機器",
     "buy_range": (1_500, 2_200),  "sell_price": 3_200},
    {"name": "メカニカルキーボード",           "asin": "B08XYZ004", "category": "パソコン・周辺機器",
     "buy_range": (6_000, 9_000),  "sell_price": 12_800},
    {"name": "ノイズキャンセリングヘッドホン", "asin": "B08XYZ005", "category": "家電・カメラ",
     "buy_range": (10_000, 14_000),"sell_price": 22_000},
    {"name": "ポータブルSSD 1TB",             "asin": "B08XYZ006", "category": "パソコン・周辺機器",
     "buy_range": (4_500, 6_500),  "sell_price": 9_800},
    {"name": "LEDデスクライト",               "asin": "B08XYZ007", "category": "家電・カメラ",
     "buy_range": (2_000, 3_000),  "sell_price": 4_500},
    {"name": "Webカメラ 4K",                  "asin": "B08XYZ008", "category": "パソコン・周辺機器",
     "buy_range": (3_500, 5_000),  "sell_price": 7_800},
    {"name": "ゲームコントローラー",           "asin": "B08XYZ009", "category": "ゲーム",
     "buy_range": (3_000, 5_500),  "sell_price": 9_500},
    {"name": "Bluetoothスピーカー",           "asin": "B08XYZ010", "category": "家電・カメラ",
     "buy_range": (2_500, 4_000),  "sell_price": 7_200},
    {"name": "アクションカメラ",              "asin": "B08XYZ011", "category": "家電・カメラ",
     "buy_range": (8_000, 13_000), "sell_price": 19_800},
    {"name": "電動歯ブラシ",                  "asin": "B08XYZ012", "category": "その他",
     "buy_range": (2_800, 4_500),  "sell_price": 8_500},
]

# プラットフォーム重み (合計 = 100)
_PLATFORM_WEIGHTS = {
    "Yahoo Shopping": 30, "楽天市場": 25,
    "買取商店": 25, "WIKI": 15, "その他": 5,
}
_PLATFORMS = list(_PLATFORM_WEIGHTS.keys())
_WEIGHTS   = list(_PLATFORM_WEIGHTS.values())

_CONDITIONS       = APP_CONFIG["conditions"]         # 新品/中古A/中古B/中古C/ジャンク
_COND_WEIGHTS     = [25, 35, 25, 10, 5]

# ステータス割り当て (売却済45, 出品中15, 未出品7, 返品2, 廃棄1)
_STATUS_POOL = (["売却済"] * 45 + ["出品中"] * 15 +
                ["未出品"] * 7 + ["返品"] * 2 + ["廃棄"] * 1)


def _random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


class PurchaseManager:

    _demo_df: pd.DataFrame = None  # クラスレベルキャッシュ

    # ================================================================
    # デモデータ生成
    # ================================================================
    @classmethod
    def _build_demo(cls) -> pd.DataFrame:
        rng = random.Random(42)
        start = date(2025, 7, 1)
        end   = date(2026, 3, 31)
        statuses = _STATUS_POOL.copy()
        rng.shuffle(statuses)

        rows = []
        for i in range(70):
            prod     = rng.choice(PRODUCTS)
            platform = rng.choices(_PLATFORMS, weights=_WEIGHTS, k=1)[0]
            cond     = rng.choices(_CONDITIONS, weights=_COND_WEIGHTS, k=1)[0]
            pdate    = _random_date(start, end)
            qty      = rng.randint(1, 3)
            unit_cost = rng.randint(*prod["buy_range"])
            # 中古は仕入れ価格を下げる
            if cond == "中古B":
                unit_cost = int(unit_cost * 0.80)
            elif cond in ("中古C", "ジャンク"):
                unit_cost = int(unit_cost * 0.55)

            status   = statuses[i % len(statuses)]
            listing  = prod["sell_price"] if status in ("出品中", "売却済") else 0

            rows.append({
                "purchase_id":   f"PUR-{i+1:03d}",
                "platform":      platform,
                "purchase_date": pdate,
                "product_name":  prod["name"],
                "asin":          prod["asin"],
                "sku":           f"{platform[:2].upper()}-{pdate.strftime('%Y%m%d')}-{i+1:03d}",
                "quantity":      qty,
                "unit_cost":     unit_cost,
                "total_cost":    unit_cost * qty,
                "category":      prod["category"],
                "condition":     cond,
                "status":        status,
                "listing_price": listing,
                "sell_price_ref":prod["sell_price"],  # 参考Amazon売価
                "notes":         "",
            })

        df = pd.DataFrame(rows)
        df["purchase_date"] = pd.to_datetime(df["purchase_date"])
        return df.sort_values("purchase_date").reset_index(drop=True)

    def get_purchases(self) -> pd.DataFrame:
        """仕入れ一覧DataFrame取得 (デモまたは実データ)"""
        if PurchaseManager._demo_df is None:
            PurchaseManager._demo_df = self._build_demo()
        return PurchaseManager._demo_df.copy()

    # ================================================================
    # KPI サマリー
    # ================================================================
    def get_kpi_summary(self, df: pd.DataFrame) -> Dict:
        if df.empty:
            return {}

        today = pd.Timestamp.now().normalize()
        this_month_start = today.replace(day=1)

        total_invested  = df["total_cost"].sum()
        this_month_cnt  = int(df[df["purchase_date"] >= this_month_start].shape[0])
        unsold_cnt      = int(df[df["status"].isin(["未出品", "出品中"])].shape[0])
        unsold_value    = df[df["status"].isin(["未出品", "出品中"])]["total_cost"].sum()
        avg_unit_cost   = df["unit_cost"].mean()
        total_items     = int(df["quantity"].sum())

        sold_df = df[df["status"] == "売却済"]
        avg_roi = 0.0
        if not sold_df.empty:
            avg_roi = ((sold_df["sell_price_ref"] - sold_df["unit_cost"]) /
                       sold_df["unit_cost"] * 100).mean()

        return {
            "total_invested":   total_invested,
            "total_items":      total_items,
            "this_month_count": this_month_cnt,
            "unsold_count":     unsold_cnt,
            "unsold_value":     unsold_value,
            "avg_unit_cost":    avg_unit_cost,
            "avg_roi_estimate": avg_roi,
            "total_records":    len(df),
        }

    # ================================================================
    # 分析メソッド
    # ================================================================
    def platform_breakdown(self, df: pd.DataFrame) -> pd.DataFrame:
        """プラットフォーム別集計"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("platform").agg(
            件数=("purchase_id", "count"),
            総仕入れ額=("total_cost", "sum"),
            平均仕入れ単価=("unit_cost", "mean"),
        ).reset_index()
        grp["構成比"] = grp["総仕入れ額"] / grp["総仕入れ額"].sum() * 100
        grp["平均仕入れ単価"] = grp["平均仕入れ単価"].round(0)
        return grp.sort_values("総仕入れ額", ascending=False).reset_index(drop=True)

    def condition_breakdown(self, df: pd.DataFrame) -> pd.DataFrame:
        """コンディション別集計"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("condition").agg(
            件数=("purchase_id", "count"),
            総仕入れ額=("total_cost", "sum"),
            平均単価=("unit_cost", "mean"),
        ).reset_index()
        # コンディション順にソート
        order = {c: i for i, c in enumerate(_CONDITIONS)}
        grp["_ord"] = grp["condition"].map(order)
        return grp.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)

    def monthly_purchase_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        """月次仕入れトレンド"""
        if df.empty:
            return pd.DataFrame()
        df = df.copy()
        df["year_month"] = df["purchase_date"].dt.to_period("M")
        grp = df.groupby("year_month").agg(
            件数=("purchase_id", "count"),
            総仕入れ額=("total_cost", "sum"),
            平均単価=("unit_cost", "mean"),
        ).reset_index()
        grp["year_month_str"] = grp["year_month"].astype(str)
        return grp

    def status_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """ステータス別集計"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("status").agg(
            件数=("purchase_id", "count"),
            総仕入れ額=("total_cost", "sum"),
        ).reset_index()
        order = {s: i for i, s in enumerate(APP_CONFIG["purchase_statuses"])}
        grp["_ord"] = grp["status"].map(order).fillna(99)
        return grp.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)

    def get_unsold_inventory(self, df: pd.DataFrame) -> pd.DataFrame:
        """未売在庫一覧 (未出品 + 出品中)"""
        if df.empty:
            return pd.DataFrame()
        return df[df["status"].isin(["未出品", "出品中"])].copy()

    def category_breakdown(self, df: pd.DataFrame) -> pd.DataFrame:
        """カテゴリ別仕入れ集計"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("category").agg(
            件数=("purchase_id", "count"),
            総仕入れ額=("total_cost", "sum"),
            平均単価=("unit_cost", "mean"),
        ).reset_index()
        return grp.sort_values("総仕入れ額", ascending=False).reset_index(drop=True)

    def platform_condition_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """プラットフォーム × コンディション クロス集計"""
        if df.empty:
            return pd.DataFrame()
        pivot = df.pivot_table(
            index="platform", columns="condition",
            values="purchase_id", aggfunc="count", fill_value=0
        )
        return pivot


# シングルトンインスタンス
purchase_manager = PurchaseManager()
