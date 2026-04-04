"""
売上分析モジュール
==================
注文データを多角的に分析:
  - 期間別売上集計 (日次/週次/月次)
  - 商品別売上ランキング
  - フルフィルメント別分析 (FBA/FBM)
  - 注文ステータス分析
  - 前期比較・成長率
  - KPIサマリー
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sp_api_client import client
from config import APP_CONFIG


class SalesAnalytics:

    def __init__(self):
        self.currency_symbol = APP_CONFIG["currency_symbol"]

    def fetch_orders_df(self, days: int = 90) -> pd.DataFrame:
        """注文データをDataFrameとして取得"""
        start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
        raw = client.get_orders(created_after=start)
        orders = raw.get("payload", {}).get("Orders", [])
        return self._parse_orders(orders)

    def _parse_orders(self, orders: List[Dict]) -> pd.DataFrame:
        rows = []
        for o in orders:
            total_str = o.get("OrderTotal", {}).get("Amount", "0")
            try:
                total = float(total_str)
            except (ValueError, TypeError):
                total = 0.0

            purchase_date = o.get("PurchaseDate", "")
            try:
                dt = datetime.strptime(purchase_date, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                dt = datetime.utcnow()

            items = o.get("Items", [])
            if items:
                for item in items:
                    item_price_str = item.get("ItemPrice", {}).get("Amount", "0")
                    try:
                        item_price = float(item_price_str)
                    except (ValueError, TypeError):
                        item_price = 0.0

                    rows.append({
                        "order_id": o.get("AmazonOrderId", ""),
                        "date": dt,
                        "year": dt.year,
                        "month": dt.month,
                        "week": dt.isocalendar()[1],
                        "day_of_week": dt.weekday(),
                        "order_status": o.get("OrderStatus", ""),
                        "fulfillment": o.get("FulfillmentChannel", ""),
                        "total_amount": total,
                        "asin": item.get("ASIN", ""),
                        "product_name": item.get("Title", "不明"),
                        "quantity": item.get("QuantityOrdered", 1),
                        "item_price": item_price,
                        "items_count": o.get("NumberOfItemsShipped", 1),
                    })
            else:
                rows.append({
                    "order_id": o.get("AmazonOrderId", ""),
                    "date": dt,
                    "year": dt.year,
                    "month": dt.month,
                    "week": dt.isocalendar()[1],
                    "day_of_week": dt.weekday(),
                    "order_status": o.get("OrderStatus", ""),
                    "fulfillment": o.get("FulfillmentChannel", ""),
                    "total_amount": total,
                    "asin": "",
                    "product_name": "不明",
                    "quantity": o.get("NumberOfItemsShipped", 1),
                    "item_price": total,
                    "items_count": o.get("NumberOfItemsShipped", 1),
                })

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df

    # ================================================================
    # KPI サマリー
    # ================================================================
    def get_kpi_summary(self, df: pd.DataFrame) -> Dict:
        """主要KPIの計算"""
        if df.empty:
            return {}

        # 注文レベルに集約
        orders = df.groupby("order_id").agg(
            date=("date", "first"),
            total_amount=("total_amount", "first"),
            order_status=("order_status", "first"),
        ).reset_index()

        shipped = orders[orders["order_status"].isin(["Shipped", "Delivered"])]
        pending = orders[orders["order_status"] == "Pending"]

        total_revenue = shipped["total_amount"].sum()
        total_orders = len(orders)
        shipped_orders = len(shipped)
        pending_orders = len(pending)
        avg_order_value = shipped["total_amount"].mean() if not shipped.empty else 0
        max_order = shipped["total_amount"].max() if not shipped.empty else 0

        # 前月比
        now = orders["date"].max()
        this_month_start = now.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        this_month = shipped[shipped["date"] >= this_month_start]["total_amount"].sum()
        last_month = shipped[
            (shipped["date"] >= last_month_start) & (shipped["date"] < this_month_start)
        ]["total_amount"].sum()

        mom_growth = ((this_month - last_month) / last_month * 100) if last_month > 0 else 0

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "shipped_orders": shipped_orders,
            "pending_orders": pending_orders,
            "avg_order_value": avg_order_value,
            "max_order": max_order,
            "this_month_revenue": this_month,
            "last_month_revenue": last_month,
            "mom_growth_pct": mom_growth,
        }

    # ================================================================
    # 時系列分析
    # ================================================================
    def daily_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """日次売上集計"""
        if df.empty:
            return pd.DataFrame()
        orders = df.groupby(["date", "order_id"]).agg(
            total_amount=("total_amount", "first"),
            order_status=("order_status", "first"),
        ).reset_index()
        shipped = orders[orders["order_status"].isin(["Shipped", "Delivered"])]
        daily = shipped.groupby(shipped["date"].dt.date).agg(
            revenue=("total_amount", "sum"),
            orders=("order_id", "count"),
        ).reset_index()
        daily.columns = ["date", "revenue", "orders"]
        daily["date"] = pd.to_datetime(daily["date"])
        daily["avg_order_value"] = daily["revenue"] / daily["orders"]
        daily["revenue_ma7"] = daily["revenue"].rolling(7, min_periods=1).mean()
        return daily

    def monthly_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """月次売上集計"""
        if df.empty:
            return pd.DataFrame()
        orders = df.groupby(["date", "order_id"]).agg(
            total_amount=("total_amount", "first"),
            order_status=("order_status", "first"),
        ).reset_index()
        shipped = orders[orders["order_status"].isin(["Shipped", "Delivered"])]
        shipped = shipped.copy()
        shipped["year_month"] = shipped["date"].dt.to_period("M")
        monthly = shipped.groupby("year_month").agg(
            revenue=("total_amount", "sum"),
            orders=("order_id", "count"),
        ).reset_index()
        monthly["avg_order_value"] = monthly["revenue"] / monthly["orders"]
        monthly["revenue_growth"] = monthly["revenue"].pct_change() * 100
        return monthly

    def weekly_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """週次売上集計"""
        if df.empty:
            return pd.DataFrame()
        orders = df.groupby(["date", "order_id"]).agg(
            total_amount=("total_amount", "first"),
            order_status=("order_status", "first"),
        ).reset_index()
        shipped = orders[orders["order_status"].isin(["Shipped", "Delivered"])]
        shipped = shipped.copy()
        shipped["year_week"] = shipped["date"].dt.to_period("W")
        weekly = shipped.groupby("year_week").agg(
            revenue=("total_amount", "sum"),
            orders=("order_id", "count"),
        ).reset_index()
        weekly["avg_order_value"] = weekly["revenue"] / weekly["orders"]
        return weekly

    def day_of_week_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """曜日別売上分析"""
        if df.empty:
            return pd.DataFrame()
        day_names = ["月", "火", "水", "木", "金", "土", "日"]
        orders = df.groupby(["date", "order_id"]).agg(
            total_amount=("total_amount", "first"),
            order_status=("order_status", "first"),
            day_of_week=("day_of_week", "first"),
        ).reset_index()
        shipped = orders[orders["order_status"].isin(["Shipped", "Delivered"])]
        dow = shipped.groupby("day_of_week").agg(
            revenue=("total_amount", "sum"),
            orders=("order_id", "count"),
        ).reset_index()
        dow["day_name"] = dow["day_of_week"].map(lambda x: day_names[x])
        dow["avg_order_value"] = dow["revenue"] / dow["orders"]
        return dow

    # ================================================================
    # 商品別分析
    # ================================================================
    def product_sales_ranking(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """商品別売上ランキング"""
        if df.empty:
            return pd.DataFrame()
        shipped = df[df["order_status"].isin(["Shipped", "Delivered"])].copy()
        product = shipped.groupby(["asin", "product_name"]).agg(
            revenue=("item_price", "sum"),
            quantity=("quantity", "sum"),
            orders=("order_id", "nunique"),
        ).reset_index()
        product["avg_price"] = product["revenue"] / product["quantity"]
        product["revenue_share"] = product["revenue"] / product["revenue"].sum() * 100
        product = product.sort_values("revenue", ascending=False).reset_index(drop=True)
        product.index += 1
        return product.head(top_n)

    def product_trend(self, df: pd.DataFrame, asin: str) -> pd.DataFrame:
        """特定商品の月次トレンド"""
        if df.empty:
            return pd.DataFrame()
        prod_df = df[(df["asin"] == asin) &
                     df["order_status"].isin(["Shipped", "Delivered"])].copy()
        if prod_df.empty:
            return pd.DataFrame()
        prod_df["year_month"] = prod_df["date"].dt.to_period("M")
        trend = prod_df.groupby("year_month").agg(
            revenue=("item_price", "sum"),
            quantity=("quantity", "sum"),
        ).reset_index()
        return trend

    # ================================================================
    # フルフィルメント分析
    # ================================================================
    def fulfillment_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """FBA/FBM別分析"""
        if df.empty:
            return pd.DataFrame()
        orders = df.groupby(["order_id", "fulfillment"]).agg(
            total_amount=("total_amount", "first"),
            order_status=("order_status", "first"),
        ).reset_index()
        shipped = orders[orders["order_status"].isin(["Shipped", "Delivered"])]
        fulf = shipped.groupby("fulfillment").agg(
            revenue=("total_amount", "sum"),
            orders=("order_id", "count"),
        ).reset_index()
        fulf["avg_order_value"] = fulf["revenue"] / fulf["orders"]
        fulf["share_pct"] = fulf["revenue"] / fulf["revenue"].sum() * 100
        fulf["fulfillment_label"] = fulf["fulfillment"].map(
            {"AFN": "FBA (Amazon配送)", "MFN": "FBM (自社配送)"}
        ).fillna(fulf["fulfillment"])
        return fulf

    # ================================================================
    # 注文ステータス分析
    # ================================================================
    def order_status_breakdown(self, df: pd.DataFrame) -> pd.DataFrame:
        """注文ステータス別集計"""
        if df.empty:
            return pd.DataFrame()
        orders = df.groupby(["order_id", "order_status"]).agg(
            total_amount=("total_amount", "first"),
        ).reset_index()
        status = orders.groupby("order_status").agg(
            count=("order_id", "count"),
            revenue=("total_amount", "sum"),
        ).reset_index()
        status["pct"] = status["count"] / status["count"].sum() * 100
        return status.sort_values("count", ascending=False)

    # ================================================================
    # 売上予測 (単純移動平均)
    # ================================================================
    def simple_forecast(self, daily_df: pd.DataFrame, forecast_days: int = 30) -> pd.DataFrame:
        """過去データから単純な売上予測"""
        if daily_df.empty or len(daily_df) < 7:
            return pd.DataFrame()

        avg_daily = daily_df["revenue"].tail(30).mean()
        std_daily = daily_df["revenue"].tail(30).std()

        last_date = daily_df["date"].max()
        future_dates = [last_date + timedelta(days=i + 1) for i in range(forecast_days)]

        forecast = pd.DataFrame({
            "date": future_dates,
            "forecast_revenue": avg_daily,
            "lower_bound": max(0, avg_daily - std_daily),
            "upper_bound": avg_daily + std_daily,
        })
        return forecast


# シングルトンインスタンス
analytics = SalesAnalytics()
