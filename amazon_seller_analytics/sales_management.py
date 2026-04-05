"""
販売実績管理モジュール (統合ビュー)
=====================================
仕入れ → 出品 → 売却 の商品ライフサイクルを一元管理。
purchase_manager と profit_calculator を統合した
全体ビューを提供する。
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from purchase_manager import PurchaseManager
from profit_calculator import ProfitCalculator


class SalesManagement:

    def __init__(self):
        self._pm = PurchaseManager()
        self._pc = ProfitCalculator()

    # ================================================================
    # 統合ビュー生成
    # ================================================================
    def get_unified_view(self,
                         purchase_df: Optional[pd.DataFrame] = None,
                         sales_df:    Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        仕入れレコードと販売レコードを LEFT JOIN した統合DataFrame。
        未売在庫は sale 側カラムが NaN になる。
        """
        if purchase_df is None:
            purchase_df = self._pm.get_purchases()
        if sales_df is None:
            sales_df = self._pc.get_sales_with_profit()

        if purchase_df.empty:
            return pd.DataFrame()

        # 販売レコード側: purchase_id ごとに集計 (複数販売がある場合は合算)
        if not sales_df.empty:
            sale_agg = sales_df.groupby("purchase_id").agg(
                sale_platform=("platform", "first"),
                sale_date=("sale_date", "max"),
                sale_price_total=("sale_price", lambda s:
                    (s * sales_df.loc[s.index, "quantity_sold"]).sum()),
                quantity_sold=("quantity_sold", "sum"),
                net_profit=("net_profit", "sum"),
                total_fees=("total_fees", "sum"),
                profit_margin_pct=("profit_margin_pct", "mean"),
                roi_pct=("roi_pct", "mean"),
                days_to_sell=("days_to_sell", "mean"),
            ).reset_index()
        else:
            sale_agg = pd.DataFrame(columns=[
                "purchase_id", "sale_platform", "sale_date", "sale_price_total",
                "quantity_sold", "net_profit", "total_fees",
                "profit_margin_pct", "roi_pct", "days_to_sell"
            ])

        # LEFT JOIN
        merged = purchase_df.merge(sale_agg, on="purchase_id", how="left")

        # 未売在庫の sale_date, profit 等は NaN → 表示用デフォルト
        merged["sale_platform"]    = merged["sale_platform"].fillna("―")
        merged["sale_date"]        = pd.to_datetime(merged["sale_date"])
        merged["days_to_sell"]     = merged["days_to_sell"].fillna(
            (pd.Timestamp.now() - merged["purchase_date"]).dt.days
        )

        # ステータスラベル整理
        merged["lifecycle_status"] = merged["status"]

        # 経過日数 (仕入れからの日数)
        merged["days_since_purchase"] = (
            pd.Timestamp.now() - merged["purchase_date"]
        ).dt.days.clip(lower=0)

        return merged.sort_values("purchase_date", ascending=False).reset_index(drop=True)

    # ================================================================
    # パイプラインサマリー
    # ================================================================
    def get_pipeline_summary(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        ステータス別件数・金額サマリー。
        仕入れ → 未出品 → 出品中 → 売却済 のファネル。
        """
        if df is None:
            df = self._pm.get_purchases()
        if df.empty:
            return {}

        statuses = ["未出品", "出品中", "売却済", "返品", "廃棄"]
        result = {}
        for s in statuses:
            sub = df[df["status"] == s]
            result[s] = {
                "count":      len(sub),
                "total_cost": sub["total_cost"].sum(),
            }

        # 総投資額 vs 回収済額
        sold = df[df["status"] == "売却済"]
        unsold = df[df["status"].isin(["未出品", "出品中"])]
        result["_summary"] = {
            "total_invested":   df["total_cost"].sum(),
            "unsold_value":     unsold["total_cost"].sum(),
            "conversion_rate":  len(sold) / len(df) * 100 if len(df) > 0 else 0.0,
        }
        return result

    # ================================================================
    # 滞留在庫 (スロームーバー)
    # ================================================================
    def slow_movers(self, df: Optional[pd.DataFrame] = None,
                    threshold_days: int = 30) -> pd.DataFrame:
        """
        仕入れから threshold_days 日以上 かつ 未売 (未出品/出品中) の商品。
        """
        if df is None:
            df = self.get_unified_view()
        if df.empty:
            return pd.DataFrame()

        mask = (
            df["lifecycle_status"].isin(["未出品", "出品中"]) &
            (df["days_since_purchase"] >= threshold_days)
        )
        result = df[mask].copy()
        result["滞留日数"] = result["days_since_purchase"]
        result["機会損失推定"] = (
            result["sell_price_ref"] * result["quantity"] -
            result["total_cost"]
        ).clip(lower=0)
        return result.sort_values("滞留日数", ascending=False).reset_index(drop=True)

    # ================================================================
    # カテゴリ別パフォーマンス
    # ================================================================
    def category_performance(self, unified_df: Optional[pd.DataFrame] = None,
                              sales_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """カテゴリ別 売上・利益・回転率"""
        if sales_df is None:
            sales_df = self._pc.get_sales_with_profit()
        if sales_df.empty:
            return pd.DataFrame()

        grp = sales_df.groupby("category").agg(
            販売件数=("sale_id", "count"),
            売上合計=("sale_price", lambda s:
                (s * sales_df.loc[s.index, "quantity_sold"]).sum()),
            純利益=("net_profit", "sum"),
            平均利益率=("profit_margin_pct", "mean"),
            平均ROI=("roi_pct", "mean"),
            平均販売日数=("days_to_sell", "mean"),
        ).reset_index()
        grp["平均利益率"] = grp["平均利益率"].round(1)
        grp["平均ROI"]    = grp["平均ROI"].round(1)
        grp["平均販売日数"] = grp["平均販売日数"].round(1)
        return grp.sort_values("純利益", ascending=False).reset_index(drop=True)

    # ================================================================
    # 販売日数統計
    # ================================================================
    def turnover_stats(self, sales_df: Optional[pd.DataFrame] = None) -> Dict:
        """仕入れ〜売却の平均日数統計"""
        if sales_df is None:
            sales_df = self._pc.get_sales_with_profit()
        if sales_df.empty:
            return {}

        d = sales_df["days_to_sell"]
        return {
            "平均販売日数":   round(d.mean(), 1),
            "中央値":         round(d.median(), 1),
            "最短販売日数":   int(d.min()),
            "最長販売日数":   int(d.max()),
            "7日以内":        int((d <= 7).sum()),
            "8-30日":         int(((d > 7) & (d <= 30)).sum()),
            "31-60日":        int(((d > 30) & (d <= 60)).sum()),
            "61日以上":       int((d > 60).sum()),
        }

    # ================================================================
    # 月次統合サマリー
    # ================================================================
    def monthly_summary(self, purchase_df: Optional[pd.DataFrame] = None,
                         sales_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """月別: 仕入れ額・売上・利益の推移"""
        if purchase_df is None:
            purchase_df = self._pm.get_purchases()
        if sales_df is None:
            sales_df = self._pc.get_sales_with_profit()

        result_rows = []

        if not purchase_df.empty:
            purchase_df = purchase_df.copy()
            purchase_df["year_month"] = purchase_df["purchase_date"].dt.to_period("M")
            pm_grp = purchase_df.groupby("year_month")["total_cost"].sum()
        else:
            pm_grp = pd.Series(dtype=float)

        if not sales_df.empty:
            sales_df = sales_df.copy()
            sales_df["year_month"] = sales_df["sale_date"].dt.to_period("M")
            s_grp = sales_df.groupby("year_month").agg(
                売上=("sale_price", lambda s: (s * sales_df.loc[s.index, "quantity_sold"]).sum()),
                利益=("net_profit", "sum"),
            )
        else:
            s_grp = pd.DataFrame()

        all_periods = set()
        if not pm_grp.empty:
            all_periods.update(pm_grp.index)
        if not s_grp.empty:
            all_periods.update(s_grp.index)

        for p in sorted(all_periods):
            仕入れ = float(pm_grp.get(p, 0))
            売上   = float(s_grp.loc[p, "売上"] if p in s_grp.index else 0)
            利益   = float(s_grp.loc[p, "利益"] if p in s_grp.index else 0)
            result_rows.append({
                "year_month": p,
                "year_month_str": str(p),
                "仕入れ額": 仕入れ,
                "売上高":   売上,
                "純利益":   利益,
                "利益率":   round(利益 / 売上 * 100, 1) if 売上 > 0 else 0.0,
            })

        return pd.DataFrame(result_rows)


# シングルトンインスタンス
sales_management = SalesManagement()
