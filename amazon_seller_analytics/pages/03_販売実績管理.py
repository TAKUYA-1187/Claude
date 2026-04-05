"""
販売実績管理ページ
==================
仕入れ → 出品 → 売却 の全ライフサイクルを一元管理。
パイプラインサマリー・滞留在庫アラート・カテゴリ別パフォーマンス。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from sales_management import sales_management
from profit_calculator import profit_calculator
from purchase_manager import purchase_manager
from config import APP_CONFIG

ORANGE = "#FF8C00"
DARK   = "#232F3E"
GREEN  = "#2ECC71"
RED    = "#E74C3C"
BLUE   = "#00A8E0"
COLORS = [ORANGE, DARK, BLUE, GREEN, "#5D3FD3", "#F39C12", RED]

st.set_page_config(page_title="販売実績管理", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 26px !important; color: #FF8C00; }
.section-header { background: linear-gradient(90deg,#FF8C00,#FF6600);
  color:white; padding:8px 16px; border-radius:6px; margin:16px 0 12px; font-weight:700; }
.pipeline-card { text-align:center; padding:16px; border-radius:8px; }
</style>""", unsafe_allow_html=True)

# ================================================================
# データ取得
# ================================================================
@st.cache_data(ttl=300)
def load_data():
    purchase_df = purchase_manager.get_purchases()
    sales_df    = profit_calculator.get_sales_with_profit()
    unified_df  = sales_management.get_unified_view(purchase_df, sales_df)
    return purchase_df, sales_df, unified_df

purchase_df, sales_df, unified_df = load_data()
pipeline = sales_management.get_pipeline_summary(purchase_df)
monthly_df = sales_management.monthly_summary(purchase_df, sales_df)
turnover   = sales_management.turnover_stats(sales_df)

# ================================================================
# ヘッダー
# ================================================================
st.markdown("""
<div style="background:linear-gradient(135deg,#232F3E,#5D3FD3);
     padding:18px 24px;border-radius:10px;color:white;margin-bottom:20px">
  <h1 style="color:white;margin:0;font-size:26px">📊 販売実績管理</h1>
  <p style="margin:4px 0 0;opacity:.85">仕入れから売却まで — 商品ライフサイクル全体を管理</p>
</div>""", unsafe_allow_html=True)

# ================================================================
# パイプラインサマリー (ファネル表示)
# ================================================================
st.markdown('<div class="section-header">🔄 販売パイプライン</div>', unsafe_allow_html=True)

summary = pipeline.get("_summary", {})
conv_rate = summary.get("conversion_rate", 0)

c1, c2, c3, c4, c5 = st.columns(5)
statuses_display = [
    ("未出品", "🏷️", "#F39C12"),
    ("出品中", "🔵", BLUE),
    ("売却済", "✅", GREEN),
    ("返品",   "↩️", RED),
    ("廃棄",   "🗑️", "#95A5A6"),
]
cols = [c1, c2, c3, c4, c5]
for col, (status, icon, color) in zip(cols, statuses_display):
    data = pipeline.get(status, {})
    with col:
        st.markdown(f"""
        <div style="background:{color}18;border:2px solid {color};border-radius:10px;
             padding:14px;text-align:center">
          <div style="font-size:24px">{icon}</div>
          <div style="font-weight:700;color:{color};font-size:18px">{data.get('count', 0)}</div>
          <div style="color:#666;font-size:12px">{status}</div>
          <div style="color:{color};font-size:12px">¥{data.get('total_cost', 0):,.0f}</div>
        </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#F5F5F5;border-radius:8px;padding:12px 16px;margin-top:12px">
  総投資額: <b>¥{summary.get('total_invested', 0):,.0f}</b> |
  未売在庫: <b>¥{summary.get('unsold_value', 0):,.0f}</b> |
  売却転換率: <b>{conv_rate:.1f}%</b>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ================================================================
# 月次 売上・仕入れ・利益 推移
# ================================================================
st.markdown('<div class="section-header">📈 月次推移 (売上 / 仕入れ / 利益)</div>',
            unsafe_allow_html=True)

if not monthly_df.empty:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=monthly_df["year_month_str"], y=monthly_df["売上高"],
        name="売上高", marker_color=ORANGE, opacity=0.8
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=monthly_df["year_month_str"], y=monthly_df["仕入れ額"],
        name="仕入れ額", marker_color=DARK, opacity=0.7
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=monthly_df["year_month_str"], y=monthly_df["純利益"],
        name="純利益", mode="lines+markers",
        line=dict(color=GREEN, width=3), marker=dict(size=9)
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=monthly_df["year_month_str"], y=monthly_df["利益率"],
        name="利益率(%)", mode="lines+markers",
        line=dict(color="#5D3FD3", width=2, dash="dot"), marker=dict(size=7)
    ), secondary_y=True)
    fig.update_layout(height=400, hovermode="x unified", barmode="group",
                      legend=dict(orientation="h", y=1.02), plot_bgcolor="white")
    fig.update_yaxes(title_text="金額 (¥)", secondary_y=False, tickprefix="¥")
    fig.update_yaxes(title_text="利益率 (%)", secondary_y=True, ticksuffix="%")
    fig.update_xaxes(tickangle=30)
    st.plotly_chart(fig, use_container_width=True)

# ================================================================
# 販売日数分析 & カテゴリ別パフォーマンス
# ================================================================
st.markdown('<div class="section-header">⏱️ 販売スピード & カテゴリ分析</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if not sales_df.empty:
        fig = px.histogram(
            sales_df, x="days_to_sell", nbins=20,
            color_discrete_sequence=[ORANGE],
            title="販売日数分布",
            labels={"days_to_sell": "仕入れ〜売却 日数", "count": "件数"},
        )
        fig.update_layout(height=360, plot_bgcolor="white")
        fig.add_vline(x=turnover.get("平均販売日数", 20),
                      line_dash="dash", line_color=RED,
                      annotation_text=f"平均 {turnover.get('平均販売日数', 0):.0f}日")
        st.plotly_chart(fig, use_container_width=True)

        # 販売日数統計
        if turnover:
            st.markdown(f"""
            | 指標 | 値 |
            |------|-----|
            | 平均販売日数 | {turnover.get('平均販売日数', 0)} 日 |
            | 中央値 | {turnover.get('中央値', 0)} 日 |
            | 最短 | {turnover.get('最短販売日数', 0)} 日 |
            | 最長 | {turnover.get('最長販売日数', 0)} 日 |
            | 7日以内 | {turnover.get('7日以内', 0)} 件 |
            | 8〜30日 | {turnover.get('8-30日', 0)} 件 |
            | 31〜60日 | {turnover.get('31-60日', 0)} 件 |
            | 61日以上 | {turnover.get('61日以上', 0)} 件 |
            """)

with col2:
    cat_df = sales_management.category_performance(sales_df=sales_df)
    if not cat_df.empty:
        fig = px.scatter(
            cat_df, x="売上合計", y="平均利益率",
            size="販売件数", color="category",
            color_discrete_sequence=COLORS,
            title="カテゴリ別パフォーマンス (売上 × 利益率 × 件数)",
            labels={"売上合計": "売上合計(¥)", "平均利益率": "平均利益率(%)",
                    "category": "カテゴリ"},
            hover_data=["純利益", "平均ROI", "平均販売日数"],
        )
        fig.update_layout(height=400, plot_bgcolor="white")
        fig.update_xaxes(tickprefix="¥")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# 統合販売実績テーブル
# ================================================================
st.markdown('<div class="section-header">📑 統合販売実績テーブル</div>',
            unsafe_allow_html=True)

if not unified_df.empty:
    display_cols = [
        "purchase_id", "product_name", "platform", "purchase_date",
        "unit_cost", "condition", "quantity", "status",
        "sale_platform", "sale_date", "net_profit", "profit_margin_pct",
        "days_since_purchase",
    ]
    col_labels = {
        "purchase_id": "仕入れID", "product_name": "商品名",
        "platform": "仕入れ先", "purchase_date": "仕入れ日",
        "unit_cost": "仕入れ単価(¥)", "condition": "コンディション",
        "quantity": "数量", "status": "ステータス",
        "sale_platform": "販売先", "sale_date": "売却日",
        "net_profit": "純利益(¥)", "profit_margin_pct": "利益率(%)",
        "days_since_purchase": "経過日数",
    }
    disp = unified_df[[c for c in display_cols if c in unified_df.columns]].copy()
    disp["purchase_date"] = disp["purchase_date"].dt.strftime("%Y-%m-%d")
    disp["sale_date"] = pd.to_datetime(disp["sale_date"]).dt.strftime("%Y-%m-%d").replace("NaT", "―")
    disp.columns = [col_labels.get(c, c) for c in disp.columns]
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ================================================================
# 滞留在庫アラート
# ================================================================
slow_df = sales_management.slow_movers(unified_df, threshold_days=30)
if not slow_df.empty:
    st.markdown('<div class="section-header">⚠️ 滞留在庫アラート (30日以上 未売)</div>',
                unsafe_allow_html=True)
    st.warning(f"仕入れから30日以上売れていない商品: **{len(slow_df)} 件**")

    slow_disp = slow_df[[
        "product_name", "platform", "purchase_date", "condition",
        "unit_cost", "sell_price_ref", "滞留日数", "機会損失推定"
    ]].copy()
    slow_disp["purchase_date"] = slow_disp["purchase_date"].dt.strftime("%Y-%m-%d")
    slow_disp.columns = [
        "商品名", "仕入れ先", "仕入れ日", "コンディション",
        "仕入れ単価(¥)", "参考売価(¥)", "滞留日数", "機会損失推定(¥)"
    ]
    st.dataframe(slow_disp, use_container_width=True, hide_index=True)
    total_opp = slow_df["機会損失推定"].sum()
    st.info(f"滞留商品の機会損失推定合計: **¥{total_opp:,.0f}**")
