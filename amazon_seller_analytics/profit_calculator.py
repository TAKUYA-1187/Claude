"""
利益計算エンジン
================
仕入れレコードと販売レコードを結合し、
全費用を考慮した純利益・利益率・ROIを計算する。

デモデータ: purchase_manager.py の PUR-001〜PUR-070 と整合した
            50件の販売レコード (売却済ステータスのもの)
"""

import random
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List
from config import APP_CONFIG
from purchase_manager import PurchaseManager, PRODUCTS

_rng = random.Random(42)


def _calc_referral_fee(sale_price: float, category: str) -> float:
    rate = APP_CONFIG["amazon_referral_fees"].get(category,
           APP_CONFIG["amazon_referral_fees"]["その他"])
    return round(sale_price * rate / 100, 0)


def _calc_fba_fee(sale_price: float) -> float:
    for tier in APP_CONFIG["fba_fee_tiers"]:
        if sale_price <= tier["max_price"]:
            return float(tier["fee"])
    return float(APP_CONFIG["fba_fee_tiers"][-1]["fee"])


class ProfitCalculator:

    _demo_df: pd.DataFrame = None

    # ================================================================
    # デモデータ生成 (purchase_managerのデモと整合)
    # ================================================================
    @classmethod
    def _build_demo(cls) -> pd.DataFrame:
        pm = PurchaseManager()
        purchases = pm.get_purchases()
        sold = purchases[purchases["status"] == "売却済"].copy()

        rows = []
        sale_idx = 1
        for _, p in sold.iterrows():
            # 仕入れから5〜45日後に売れる
            days_later = _rng.randint(5, 45)
            sale_date  = p["purchase_date"] + pd.Timedelta(days=days_later)

            # 販売数量 (仕入れ数量以下)
            qty_sold   = _rng.randint(1, int(p["quantity"]))

            # 販売プラットフォーム (主にAmazon、稀に他)
            platform   = _rng.choices(
                ["Amazon", "買取商店", "WIKI"],
                weights=[85, 10, 5], k=1
            )[0]

            # 売価: 参考売価 ± 数%のブレ
            ref_price  = p["sell_price_ref"]
            variance   = _rng.uniform(-0.05, 0.08)
            sale_price = round(ref_price * (1 + variance) / 100) * 100

            unit_cost  = float(p["unit_cost"])
            total_cost = unit_cost * qty_sold
            category   = p["category"]

            # Amazonフィー計算
            if platform == "Amazon":
                referral_fee = _calc_referral_fee(sale_price, category) * qty_sold
                fba_fee      = _calc_fba_fee(sale_price) * qty_sold
                shipping     = 0.0  # FBA
                other_costs  = round(_rng.uniform(0, 300), 0)  # 梱包・ラベル等
            else:
                # 買取店・WIKI: フィーなし、ただし売価が低い
                sale_price   = round(sale_price * _rng.uniform(0.45, 0.65) / 100) * 100
                referral_fee = 0.0
                fba_fee      = 0.0
                shipping     = 0.0
                other_costs  = 0.0

            total_fees   = referral_fee + fba_fee + shipping + other_costs
            gross_profit = sale_price * qty_sold - total_cost
            net_profit   = gross_profit - total_fees
            margin_pct   = (net_profit / (sale_price * qty_sold) * 100
                            if sale_price > 0 else 0.0)
            roi_pct      = (net_profit / total_cost * 100
                            if total_cost > 0 else 0.0)
            days_to_sell = days_later

            rows.append({
                "sale_id":             f"SAL-{sale_idx:03d}",
                "purchase_id":         p["purchase_id"],
                "platform":            platform,
                "sale_date":           sale_date,
                "amazon_order_id":     (f"503-{_rng.randint(1000000,9999999)}-"
                                        f"{_rng.randint(1000000,9999999)}"
                                        if platform == "Amazon" else ""),
                "product_name":        p["product_name"],
                "asin":                p["asin"],
                "category":            category,
                "condition":           p["condition"],
                "buy_platform":        p["platform"],
                "quantity_sold":       qty_sold,
                "sale_price":          float(sale_price),
                "unit_sale_price":     float(sale_price),
                "unit_cost":           unit_cost,
                "total_cost":          total_cost,
                "amazon_referral_fee": referral_fee,
                "fba_fee":             fba_fee,
                "shipping_cost":       shipping,
                "other_costs":         other_costs,
                "total_fees":          total_fees,
                "gross_profit":        round(gross_profit, 0),
                "net_profit":          round(net_profit, 0),
                "profit_margin_pct":   round(margin_pct, 1),
                "roi_pct":             round(roi_pct, 1),
                "days_to_sell":        days_to_sell,
                "exit_channel":        platform,
            })
            sale_idx += 1

        df = pd.DataFrame(rows)
        df["sale_date"]     = pd.to_datetime(df["sale_date"])
        df["purchase_date"] = pd.to_datetime(
            purchases.set_index("purchase_id").loc[df["purchase_id"], "purchase_date"].values
        )
        return df.sort_values("sale_date").reset_index(drop=True)

    def get_sales_with_profit(self) -> pd.DataFrame:
        """利益計算済み販売DataFrameを取得"""
        if ProfitCalculator._demo_df is None:
            ProfitCalculator._demo_df = self._build_demo()
        return ProfitCalculator._demo_df.copy()

    # ================================================================
    # KPI
    # ================================================================
    def get_profit_kpi(self, df: pd.DataFrame) -> Dict:
        if df.empty:
            return {}

        total_revenue    = df["sale_price"].sum() * df["quantity_sold"].sum() / len(df) if len(df) else 0
        # 修正: sale_price はすでに1個あたり or 合計かを確認
        total_revenue    = (df["sale_price"] * df["quantity_sold"]).sum()
        total_cost       = df["total_cost"].sum()
        total_fees       = df["total_fees"].sum()
        total_net_profit = df["net_profit"].sum()
        avg_margin       = df["profit_margin_pct"].mean()
        avg_roi          = df["roi_pct"].mean()
        loss_count       = int((df["net_profit"] < 0).sum())

        best_row = df.loc[df["net_profit"].idxmax()] if not df.empty else None
        best_product = best_row["product_name"] if best_row is not None else "―"
        best_profit  = float(best_row["net_profit"]) if best_row is not None else 0.0

        # 月平均利益
        if not df.empty:
            months = max(1, df["sale_date"].dt.to_period("M").nunique())
            monthly_avg_profit = total_net_profit / months
        else:
            monthly_avg_profit = 0.0

        return {
            "total_revenue":       total_revenue,
            "total_cost":          total_cost,
            "total_fees":          total_fees,
            "total_net_profit":    total_net_profit,
            "avg_margin_pct":      round(avg_margin, 1),
            "avg_roi_pct":         round(avg_roi, 1),
            "loss_count":          loss_count,
            "best_product":        best_product,
            "best_profit":         best_profit,
            "monthly_avg_profit":  round(monthly_avg_profit, 0),
            "total_sales_count":   len(df),
        }

    # ================================================================
    # 分析メソッド
    # ================================================================
    def product_pl(self, df: pd.DataFrame) -> pd.DataFrame:
        """商品別損益表"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby(["asin", "product_name", "category"]).agg(
            販売件数=("sale_id", "count"),
            販売数量=("quantity_sold", "sum"),
            売上合計=("sale_price", lambda s: (s * df.loc[s.index, "quantity_sold"]).sum()),
            仕入れ総額=("total_cost", "sum"),
            手数料合計=("total_fees", "sum"),
            純利益=("net_profit", "sum"),
            平均利益率=("profit_margin_pct", "mean"),
            平均ROI=("roi_pct", "mean"),
        ).reset_index()
        grp["平均利益率"] = grp["平均利益率"].round(1)
        grp["平均ROI"]    = grp["平均ROI"].round(1)
        return grp.sort_values("純利益", ascending=False).reset_index(drop=True)

    def monthly_profit(self, df: pd.DataFrame) -> pd.DataFrame:
        """月次利益推移"""
        if df.empty:
            return pd.DataFrame()
        d = df.copy()
        d["year_month"] = d["sale_date"].dt.to_period("M")
        grp = d.groupby("year_month").agg(
            売上=("sale_price", lambda s: (s * df.loc[s.index, "quantity_sold"]).sum()),
            仕入れ額=("total_cost", "sum"),
            手数料=("total_fees", "sum"),
            純利益=("net_profit", "sum"),
            件数=("sale_id", "count"),
        ).reset_index()
        grp["利益率"] = (grp["純利益"] / grp["売上"] * 100).round(1)
        grp["year_month_str"] = grp["year_month"].astype(str)
        return grp

    def platform_profit(self, df: pd.DataFrame) -> pd.DataFrame:
        """仕入れプラットフォーム別利益比較"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("buy_platform").agg(
            件数=("sale_id", "count"),
            仕入れ総額=("total_cost", "sum"),
            純利益=("net_profit", "sum"),
            平均利益率=("profit_margin_pct", "mean"),
            平均ROI=("roi_pct", "mean"),
        ).reset_index()
        grp["平均利益率"] = grp["平均利益率"].round(1)
        grp["平均ROI"]    = grp["平均ROI"].round(1)
        return grp.sort_values("純利益", ascending=False).reset_index(drop=True)

    def loss_items(self, df: pd.DataFrame) -> pd.DataFrame:
        """損失商品リスト"""
        if df.empty:
            return pd.DataFrame()
        return df[df["net_profit"] < 0].sort_values("net_profit").copy()

    def best_roi_items(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """ROIランキング TOP N"""
        if df.empty:
            return pd.DataFrame()
        return df.nlargest(top_n, "roi_pct")[
            ["product_name", "buy_platform", "unit_cost", "sale_price",
             "net_profit", "roi_pct", "profit_margin_pct", "days_to_sell"]
        ].reset_index(drop=True)

    def fee_breakdown_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """手数料内訳サマリー"""
        if df.empty:
            return pd.DataFrame()
        return pd.DataFrame({
            "費用項目": ["Amazon紹介料", "FBA手数料", "送料", "その他費用"],
            "合計金額": [
                df["amazon_referral_fee"].sum(),
                df["fba_fee"].sum(),
                df["shipping_cost"].sum(),
                df["other_costs"].sum(),
            ]
        })

    def condition_profit(self, df: pd.DataFrame) -> pd.DataFrame:
        """コンディション別利益比較"""
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("condition").agg(
            件数=("sale_id", "count"),
            純利益=("net_profit", "sum"),
            平均利益率=("profit_margin_pct", "mean"),
            平均ROI=("roi_pct", "mean"),
        ).reset_index()
        return grp.sort_values("平均ROI", ascending=False).reset_index(drop=True)


# シングルトンインスタンス
profit_calculator = ProfitCalculator()
