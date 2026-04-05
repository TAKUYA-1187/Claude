"""
買取管理モジュール
==================
買取商店・WIKI への売却実績管理と
Amazon vs 買取出口 の最適出口比較ツール。

デモデータ: 20件の買取見積・売却レコード
"""

import random
import pandas as pd
from datetime import date, timedelta
from typing import Dict, Optional
from config import APP_CONFIG
from purchase_manager import PurchaseManager, PRODUCTS
from profit_calculator import _calc_referral_fee, _calc_fba_fee

_rng = random.Random(99)


def _random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=_rng.randint(0, delta))


class BuybackManager:

    _demo_df: pd.DataFrame = None

    # ================================================================
    # デモデータ生成
    # ================================================================
    @classmethod
    def _build_demo(cls) -> pd.DataFrame:
        pm = PurchaseManager()
        purchases = pm.get_purchases()
        # 買取商店やWIKIを仕入れ先とした商品 + Amazon売却済みの一部
        candidates = purchases[
            purchases["platform"].isin(["買取商店", "WIKI", "Yahoo Shopping", "楽天市場"])
        ].head(20).copy()

        shops = APP_CONFIG["buyback_shops"]
        rows = []
        for i, (_, p) in enumerate(candidates.iterrows()):
            ref_price = p["sell_price_ref"]
            # 買取価格 = 参考Amazon売価の 40〜65%
            buyback_rate = _rng.uniform(0.40, 0.65)
            buyback_price = round(ref_price * buyback_rate / 100) * 100

            q_date = _random_date(date(2025, 8, 1), date(2026, 3, 31))
            status = _rng.choices(["売却済", "見積中", "辞退"], weights=[55, 25, 20], k=1)[0]
            shop   = _rng.choice(shops)

            # Amazon想定利益計算
            amazon_referral = _calc_referral_fee(ref_price, p["category"])
            amazon_fba      = _calc_fba_fee(ref_price)
            amazon_other    = 200
            amazon_net_profit = (
                ref_price - p["unit_cost"] -
                amazon_referral - amazon_fba - amazon_other
            )

            # 買取利益 = 買取価格 - 仕入れ単価
            buyback_profit = buyback_price - p["unit_cost"]

            diff = amazon_net_profit - buyback_profit
            if diff > 500:
                recommendation = "Amazon推奨"
                reason = f"Amazon販売が¥{diff:,.0f}有利"
            elif diff < -500:
                recommendation = "買取推奨"
                reason = f"買取が¥{abs(diff):,.0f}有利 (在庫リスク回避)"
            else:
                recommendation = "どちらでも可"
                reason = f"差額¥{abs(diff):,.0f} (誤差範囲)"

            rows.append({
                "buyback_id":         f"BB-{i+1:03d}",
                "purchase_id":        p["purchase_id"],
                "product_name":       p["product_name"],
                "asin":               p["asin"],
                "category":           p["category"],
                "condition":          p["condition"],
                "buyback_shop":       shop,
                "quotation_date":     pd.Timestamp(q_date),
                "buyback_price":      float(buyback_price),
                "quantity":           1,
                "status":             status,
                "unit_cost":          float(p["unit_cost"]),
                # Amazon比較
                "amazon_ref_price":   float(ref_price),
                "amazon_referral_fee":float(amazon_referral),
                "amazon_fba_fee":     float(amazon_fba),
                "amazon_net_profit":  round(amazon_net_profit, 0),
                # 買取比較
                "buyback_profit":     round(buyback_profit, 0),
                "price_diff":         round(diff, 0),
                "recommendation":     recommendation,
                "reason":             reason,
            })

        df = pd.DataFrame(rows)
        df["quotation_date"] = pd.to_datetime(df["quotation_date"])
        return df.sort_values("quotation_date", ascending=False).reset_index(drop=True)

    def get_buyback_records(self) -> pd.DataFrame:
        """買取レコード取得"""
        if BuybackManager._demo_df is None:
            BuybackManager._demo_df = self._build_demo()
        return BuybackManager._demo_df.copy()

    # ================================================================
    # KPI
    # ================================================================
    def get_kpi_summary(self, df: pd.DataFrame) -> Dict:
        if df.empty:
            return {}
        sold = df[df["status"] == "売却済"]
        return {
            "total_records":        len(df),
            "sold_count":           len(sold),
            "pending_count":        int((df["status"] == "見積中").sum()),
            "declined_count":       int((df["status"] == "辞退").sum()),
            "total_buyback_revenue":sold["buyback_price"].sum(),
            "total_buyback_profit": sold["buyback_profit"].sum(),
            "avg_buyback_profit":   sold["buyback_profit"].mean() if not sold.empty else 0.0,
            "amazon_recommended":   int((df["recommendation"] == "Amazon推奨").sum()),
            "buyback_recommended":  int((df["recommendation"] == "買取推奨").sum()),
        }

    # ================================================================
    # 出口比較
    # ================================================================
    def exit_comparison(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Amazon vs 買取 の利益比較表"""
        if df is None:
            df = self.get_buyback_records()
        if df.empty:
            return pd.DataFrame()

        cols = [
            "product_name", "condition", "unit_cost",
            "amazon_ref_price", "amazon_net_profit",
            "buyback_shop", "buyback_price", "buyback_profit",
            "price_diff", "recommendation", "reason",
        ]
        return df[cols].copy()

    def recommendation_engine(self,
                              product_name: str,
                              unit_cost: float,
                              amazon_price: float,
                              buyback_price: float,
                              category: str = "その他",
                              is_fba: bool = True) -> Dict:
        """
        リアルタイム出口推奨エンジン。
        商品名・仕入れ価格・Amazon売価・買取価格を入力して最適出口を返す。
        """
        # Amazon利益計算
        ref_fee  = _calc_referral_fee(amazon_price, category)
        fba_fee  = _calc_fba_fee(amazon_price) if is_fba else 0
        ship_fee = 0 if is_fba else 600  # FBM時の送料概算
        amazon_profit = amazon_price - unit_cost - ref_fee - fba_fee - ship_fee - 200

        # 買取利益
        bb_profit = buyback_price - unit_cost

        diff = amazon_profit - bb_profit

        if diff > 1000:
            decision = "Amazon販売を推奨"
            icon = "Amazon"
        elif diff < -500:
            decision = "買取を推奨"
            icon = "buyback"
        else:
            decision = "どちらでも可"
            icon = "neutral"

        return {
            "product_name":      product_name,
            "unit_cost":         unit_cost,
            "amazon_price":      amazon_price,
            "amazon_referral":   ref_fee,
            "amazon_fba":        fba_fee,
            "amazon_shipping":   ship_fee,
            "amazon_other":      200,
            "amazon_profit":     round(amazon_profit, 0),
            "amazon_margin_pct": round(amazon_profit / amazon_price * 100, 1) if amazon_price > 0 else 0,
            "buyback_price":     buyback_price,
            "buyback_profit":    round(bb_profit, 0),
            "buyback_margin_pct":round(bb_profit / buyback_price * 100, 1) if buyback_price > 0 else 0,
            "profit_diff":       round(diff, 0),
            "decision":          decision,
            "icon":              icon,
        }

    # ================================================================
    # 月次買取実績
    # ================================================================
    def monthly_buyback_trend(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if df is None:
            df = self.get_buyback_records()
        if df.empty:
            return pd.DataFrame()

        sold = df[df["status"] == "売却済"].copy()
        if sold.empty:
            return pd.DataFrame()

        sold["year_month"] = sold["quotation_date"].dt.to_period("M")
        grp = sold.groupby("year_month").agg(
            件数=("buyback_id", "count"),
            買取売上=("buyback_price", "sum"),
            買取利益=("buyback_profit", "sum"),
        ).reset_index()
        grp["year_month_str"] = grp["year_month"].astype(str)
        return grp

    # ================================================================
    # 店舗別集計
    # ================================================================
    def shop_breakdown(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if df is None:
            df = self.get_buyback_records()
        if df.empty:
            return pd.DataFrame()

        grp = df.groupby("buyback_shop").agg(
            件数=("buyback_id", "count"),
            売却済=("status", lambda s: (s == "売却済").sum()),
            平均買取価格=("buyback_price", "mean"),
            平均利益=("buyback_profit", "mean"),
        ).reset_index()
        return grp.sort_values("件数", ascending=False).reset_index(drop=True)


# シングルトンインスタンス
buyback_manager = BuybackManager()
