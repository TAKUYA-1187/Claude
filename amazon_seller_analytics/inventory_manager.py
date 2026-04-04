"""
在庫管理モジュール
==================
FBA在庫データの取得・分析:
  - 在庫サマリー (fulfillable / reserved / inbound)
  - 在庫不足アラート (低在庫 / 在庫切れ)
  - 在庫回転率・在庫日数の推定
  - 補充推奨数量の計算
  - カテゴリ別在庫分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from sp_api_client import client
from sales_analytics import analytics


class InventoryManager:

    # 在庫アラート閾値
    CRITICAL_STOCK = 5       # 在庫切れ危険水準
    LOW_STOCK = 15           # 低在庫警告水準
    REORDER_DAYS = 14        # 補充リードタイム (日)

    def fetch_inventory_df(self) -> pd.DataFrame:
        """在庫データをDataFrameとして取得"""
        raw = client.get_inventory_summaries()
        items = raw.get("payload", {}).get("inventorySummaries", [])
        return self._parse_inventory(items)

    def _parse_inventory(self, items: List[Dict]) -> pd.DataFrame:
        rows = []
        for item in items:
            details = item.get("inventoryDetails", {})
            reserved = details.get("reservedQuantity", {})
            rows.append({
                "asin": item.get("asin", ""),
                "fn_sku": item.get("fnSku", ""),
                "seller_sku": item.get("sellerSku", ""),
                "product_name": item.get("productName", "不明"),
                "fulfillable_qty": details.get("fulfillableQuantity", 0),
                "inbound_working": details.get("inboundWorkingQuantity", 0),
                "inbound_shipped": details.get("inboundShippedQuantity", 0),
                "reserved_total": reserved.get("totalReservedQuantity", 0),
            })

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["total_qty"] = (df["fulfillable_qty"] + df["inbound_working"] +
                           df["inbound_shipped"])
        return df

    def add_sales_velocity(self, inventory_df: pd.DataFrame,
                           sales_df: pd.DataFrame) -> pd.DataFrame:
        """売上速度 (日次平均販売数) を在庫DFに追加"""
        if inventory_df.empty or sales_df.empty:
            if not inventory_df.empty:
                inventory_df["daily_sales_velocity"] = 0.0
                inventory_df["days_of_stock"] = 999.0
                inventory_df["reorder_qty"] = 0
                inventory_df["stock_status"] = "不明"
            return inventory_df

        # ASINごとの日次平均販売数
        shipped = sales_df[sales_df["order_status"].isin(["Shipped", "Delivered"])].copy()
        if shipped.empty:
            inventory_df["daily_sales_velocity"] = 0.0
            inventory_df["days_of_stock"] = 999.0
        else:
            days_range = max(1, (shipped["date"].max() - shipped["date"].min()).days)
            velocity = shipped.groupby("asin")["quantity"].sum() / days_range
            inventory_df["daily_sales_velocity"] = inventory_df["asin"].map(velocity).fillna(0.0)

        # 在庫日数 = 販売可能在庫 / 日次販売数
        inventory_df["days_of_stock"] = inventory_df.apply(
            lambda r: (r["fulfillable_qty"] / r["daily_sales_velocity"]
                       if r["daily_sales_velocity"] > 0 else 999.0),
            axis=1
        ).round(1)

        # 補充推奨数 = リードタイム * 日次販売数 - 現在在庫
        inventory_df["reorder_qty"] = inventory_df.apply(
            lambda r: max(0, int(
                self.REORDER_DAYS * r["daily_sales_velocity"] - r["fulfillable_qty"]
            )),
            axis=1
        )

        # 在庫ステータス
        inventory_df["stock_status"] = inventory_df["fulfillable_qty"].apply(
            self._classify_stock
        )

        return inventory_df

    def _classify_stock(self, qty: int) -> str:
        if qty == 0:
            return "在庫切れ"
        elif qty <= self.CRITICAL_STOCK:
            return "危険水準"
        elif qty <= self.LOW_STOCK:
            return "低在庫"
        else:
            return "正常"

    def get_alerts(self, inventory_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """在庫アラート一覧を返す"""
        if inventory_df.empty or "stock_status" not in inventory_df.columns:
            return {"out_of_stock": pd.DataFrame(), "critical": pd.DataFrame(),
                    "low_stock": pd.DataFrame(), "reorder_needed": pd.DataFrame()}

        out_of_stock = inventory_df[inventory_df["stock_status"] == "在庫切れ"]
        critical = inventory_df[inventory_df["stock_status"] == "危険水準"]
        low_stock = inventory_df[inventory_df["stock_status"] == "低在庫"]
        reorder = inventory_df[inventory_df["reorder_qty"] > 0].sort_values(
            "reorder_qty", ascending=False
        )
        return {
            "out_of_stock": out_of_stock,
            "critical": critical,
            "low_stock": low_stock,
            "reorder_needed": reorder,
        }

    def inventory_summary_stats(self, inventory_df: pd.DataFrame) -> Dict:
        """在庫サマリー統計"""
        if inventory_df.empty:
            return {}
        return {
            "total_skus": len(inventory_df),
            "total_fulfillable": int(inventory_df["fulfillable_qty"].sum()),
            "total_inbound": int(
                inventory_df["inbound_working"].sum() +
                inventory_df["inbound_shipped"].sum()
            ),
            "total_reserved": int(inventory_df["reserved_total"].sum()),
            "out_of_stock_count": int(
                (inventory_df.get("stock_status", pd.Series()) == "在庫切れ").sum()
            ),
            "low_stock_count": int(
                inventory_df.get("stock_status", pd.Series()).isin(
                    ["危険水準", "低在庫"]
                ).sum()
            ),
            "avg_days_of_stock": round(
                inventory_df.get("days_of_stock", pd.Series(dtype=float))
                .replace(999.0, np.nan).mean(), 1
            ) if "days_of_stock" in inventory_df.columns else None,
        }

    def turnover_rate(self, inventory_df: pd.DataFrame,
                      sales_df: pd.DataFrame, period_days: int = 90) -> pd.DataFrame:
        """在庫回転率の計算 (期間販売数 / 平均在庫数)"""
        if inventory_df.empty or sales_df.empty:
            return inventory_df.copy()

        shipped = sales_df[sales_df["order_status"].isin(["Shipped", "Delivered"])].copy()
        total_sold = shipped.groupby("asin")["quantity"].sum()

        df = inventory_df.copy()
        df["total_sold_period"] = df["asin"].map(total_sold).fillna(0)
        df["avg_inventory"] = df["fulfillable_qty"]  # 簡易的に現在庫を使用
        df["turnover_rate"] = df.apply(
            lambda r: round(r["total_sold_period"] / r["avg_inventory"], 2)
            if r["avg_inventory"] > 0 else 0.0,
            axis=1
        )
        return df

    def stranded_inventory_risk(self, inventory_df: pd.DataFrame,
                                sales_df: pd.DataFrame,
                                no_sales_days: int = 30) -> pd.DataFrame:
        """販売停滞リスク商品の特定 (一定期間売上ゼロ)"""
        if inventory_df.empty or sales_df.empty:
            return pd.DataFrame()

        recent_cutoff = sales_df["date"].max() - pd.Timedelta(days=no_sales_days)
        recent_sold_asins = set(
            sales_df[sales_df["date"] >= recent_cutoff]["asin"].unique()
        )
        stranded = inventory_df[
            (inventory_df["fulfillable_qty"] > 0) &
            (~inventory_df["asin"].isin(recent_sold_asins))
        ].copy()
        stranded["risk_level"] = "停滞リスク"
        return stranded


# シングルトンインスタンス
inventory_manager = InventoryManager()
