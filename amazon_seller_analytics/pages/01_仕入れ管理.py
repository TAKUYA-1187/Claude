"""
仕入れ管理ページ
================
Yahoo Shopping / 楽天市場 / 買取商店 / WIKI からの
仕入れ履歴を管理・分析するダッシュボード。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from purchase_manager import purchase_manager
from config import APP_CONFIG

ORANGE = "#FF8C00"
DARK   = "#232F3E"
COLORS = [ORANGE, "#FF6600", DARK, "#00A8E0", "#5D3FD3", "#2ECC71", "#E74C3C", "#F39C12"]

st.set_page_config(page_title="仕入れ管理", page_icon="🛒", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 26px !important; color: #FF8C00; }
.section-header { background: linear-gradient(90deg,#FF8C00,#FF6600);
  color:white; padding:8px 16px; border-radius:6px; margin:16px 0 12px; font-weight:700; }
</style>""", unsafe_allow_html=True)

# ================================================================
# データ取得
# ================================================================
@st.cache_data(ttl=300)
def load_data():
    return purchase_manager.get_purchases()

df = load_data()
kpi = purchase_manager.get_kpi_summary(df)

# ================================================================
# ヘッダー
# ================================================================
st.markdown("""
<div style="background:linear-gradient(135deg,#232F3E,#FF8C00);
     padding:18px 24px;border-radius:10px;color:white;margin-bottom:20px">
  <h1 style="color:white;margin:0;font-size:26px">🛒 仕入れ管理</h1>
  <p style="margin:4px 0 0;opacity:.85">Yahoo Shopping / 楽天市場 / 買取商店 / WIKI の仕入れ履歴</p>
</div>""", unsafe_allow_html=True)

# ================================================================
# KPIカード
# ================================================================
st.markdown('<div class="section-header">📊 仕入れ KPI</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("総投資額", f"¥{kpi.get('total_invested', 0):,.0f}")
with c2:
    st.metric("仕入れ件数 (累計)", f"{kpi.get('total_records', 0):,} 件")
with c3:
    st.metric("未売在庫", f"{kpi.get('unsold_count', 0)} 件",
              delta=f"¥{kpi.get('unsold_value', 0):,.0f} 拘束中",
              delta_color="inverse")
with c4:
    st.metric("平均仕入れ単価", f"¥{kpi.get('avg_unit_cost', 0):,.0f}")

st.markdown("---")

# ================================================================
# プラットフォーム別 & 月次トレンド
# ================================================================
st.markdown('<div class="section-header">📈 仕入れ分析</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    platform_df = purchase_manager.platform_breakdown(df)
    if not platform_df.empty:
        fig = px.pie(platform_df, values="総仕入れ額", names="platform",
                     color_discrete_sequence=COLORS,
                     title="プラットフォーム別 仕入れ金額",
                     hole=0.4)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    monthly_df = purchase_manager.monthly_purchase_trend(df)
    if not monthly_df.empty:
        fig = px.bar(monthly_df, x="year_month_str", y="総仕入れ額",
                     color_discrete_sequence=[ORANGE],
                     title="月次仕入れ推移",
                     labels={"year_month_str": "年月", "総仕入れ額": "仕入れ金額"})
        fig.update_yaxes(tickprefix="¥")
        fig.update_xaxes(tickangle=30)
        fig.update_layout(height=380, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

# コンディション別 & ステータス別
col3, col4 = st.columns(2)

with col3:
    cond_df = purchase_manager.condition_breakdown(df)
    if not cond_df.empty:
        fig = px.bar(cond_df, x="件数", y="condition", orientation="h",
                     color="件数",
                     color_continuous_scale=["#FFE0B2", ORANGE, "#E65100"],
                     title="コンディション別 仕入れ件数",
                     labels={"condition": "コンディション", "件数": "件数"})
        fig.update_layout(height=320, showlegend=False,
                          coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

with col4:
    status_df = purchase_manager.status_summary(df)
    if not status_df.empty:
        STATUS_COLOR = {
            "売却済": "#2ECC71", "出品中": "#00A8E0",
            "未出品": ORANGE, "返品": "#E74C3C", "廃棄": "#95A5A6",
        }
        fig = px.pie(status_df, values="件数", names="status",
                     color="status", color_discrete_map=STATUS_COLOR,
                     title="ステータス別 構成",
                     hole=0.35)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# プラットフォーム別詳細テーブル
# ================================================================
st.markdown('<div class="section-header">📋 プラットフォーム別集計</div>', unsafe_allow_html=True)
if not platform_df.empty:
    disp = platform_df.copy()
    disp["総仕入れ額"] = disp["総仕入れ額"].apply(lambda x: f"¥{x:,.0f}")
    disp["平均仕入れ単価"] = disp["平均仕入れ単価"].apply(lambda x: f"¥{x:,.0f}")
    disp["構成比"] = disp["構成比"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ================================================================
# フィルタ付き 仕入れ履歴一覧
# ================================================================
st.markdown('<div class="section-header">📑 仕入れ履歴一覧</div>', unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    sel_platform = st.multiselect(
        "プラットフォーム", options=df["platform"].unique().tolist(),
        default=df["platform"].unique().tolist()
    )
with col_f2:
    sel_status = st.multiselect(
        "ステータス", options=df["status"].unique().tolist(),
        default=df["status"].unique().tolist()
    )
with col_f3:
    sel_cond = st.multiselect(
        "コンディション", options=df["condition"].unique().tolist(),
        default=df["condition"].unique().tolist()
    )

filtered = df[
    df["platform"].isin(sel_platform) &
    df["status"].isin(sel_status) &
    df["condition"].isin(sel_cond)
].copy()

display_cols = ["purchase_id", "purchase_date", "product_name", "platform",
                "condition", "quantity", "unit_cost", "total_cost",
                "category", "status", "listing_price"]
col_labels = {
    "purchase_id": "仕入れID", "purchase_date": "仕入れ日", "product_name": "商品名",
    "platform": "仕入れ先", "condition": "コンディション", "quantity": "数量",
    "unit_cost": "単価(¥)", "total_cost": "総仕入れ額(¥)",
    "category": "カテゴリ", "status": "ステータス", "listing_price": "出品価格(¥)",
}
disp2 = filtered[[c for c in display_cols if c in filtered.columns]].copy()
disp2["purchase_date"] = disp2["purchase_date"].dt.strftime("%Y-%m-%d")
disp2.columns = [col_labels.get(c, c) for c in disp2.columns]
st.dataframe(disp2, use_container_width=True, hide_index=True)
st.caption(f"表示件数: {len(filtered):,} / 全{len(df):,} 件")

# ================================================================
# 未売在庫一覧
# ================================================================
unsold = purchase_manager.get_unsold_inventory(df)
if not unsold.empty:
    st.markdown('<div class="section-header">⚠️ 未売在庫一覧 (未出品 + 出品中)</div>',
                unsafe_allow_html=True)
    unsold_disp = unsold[["purchase_id", "purchase_date", "product_name",
                           "platform", "condition", "quantity",
                           "unit_cost", "total_cost", "status",
                           "sell_price_ref"]].copy()
    unsold_disp["purchase_date"] = unsold_disp["purchase_date"].dt.strftime("%Y-%m-%d")
    unsold_disp["機会損失推定"] = (
        (unsold_disp["sell_price_ref"] - unsold_disp["unit_cost"]) *
        unsold_disp["quantity"]
    ).clip(lower=0)
    unsold_disp.columns = [
        "仕入れID", "仕入れ日", "商品名", "仕入れ先",
        "コンディション", "数量", "単価(¥)", "総仕入れ額(¥)",
        "ステータス", "参考売価(¥)", "機会損失推定(¥)"
    ]
    st.dataframe(unsold_disp, use_container_width=True, hide_index=True)
    total_opportunity = unsold["total_cost"].sum()
    st.info(f"未売在庫 合計投資額: **¥{total_opportunity:,.0f}**")
