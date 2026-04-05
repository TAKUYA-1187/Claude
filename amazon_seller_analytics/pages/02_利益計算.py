"""
利益計算ページ
==============
販売実績に基づく詳細な利益・ROI・手数料分析。
商品別 / 月次 / 仕入れ先別の多角的な損益計算表。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from profit_calculator import profit_calculator
from config import APP_CONFIG

ORANGE  = "#FF8C00"
DARK    = "#232F3E"
GREEN   = "#2ECC71"
RED     = "#E74C3C"
BLUE    = "#00A8E0"
PURPLE  = "#5D3FD3"
COLORS  = [ORANGE, DARK, BLUE, GREEN, PURPLE, "#F39C12", RED, "#95A5A6"]

st.set_page_config(page_title="利益計算", page_icon="💰", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 26px !important; color: #FF8C00; }
.section-header { background: linear-gradient(90deg,#FF8C00,#FF6600);
  color:white; padding:8px 16px; border-radius:6px; margin:16px 0 12px; font-weight:700; }
.profit-positive { color: #2ECC71; font-weight: 700; }
.profit-negative { color: #E74C3C; font-weight: 700; }
</style>""", unsafe_allow_html=True)

# ================================================================
# データ取得
# ================================================================
@st.cache_data(ttl=300)
def load_data():
    return profit_calculator.get_sales_with_profit()

df = load_data()
kpi = profit_calculator.get_profit_kpi(df)

# ================================================================
# ヘッダー
# ================================================================
st.markdown("""
<div style="background:linear-gradient(135deg,#232F3E,#2ECC71);
     padding:18px 24px;border-radius:10px;color:white;margin-bottom:20px">
  <h1 style="color:white;margin:0;font-size:26px">💰 利益計算表</h1>
  <p style="margin:4px 0 0;opacity:.85">仕入れコスト・Amazon手数料を考慮した実質利益・ROI分析</p>
</div>""", unsafe_allow_html=True)

# ================================================================
# KPIカード
# ================================================================
st.markdown('<div class="section-header">📊 利益 KPI</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    profit = kpi.get("total_net_profit", 0)
    st.metric("総純利益", f"¥{profit:,.0f}",
              delta=f"月平均 ¥{kpi.get('monthly_avg_profit', 0):,.0f}")
with c2:
    st.metric("平均利益率", f"{kpi.get('avg_margin_pct', 0):.1f}%")
with c3:
    st.metric("平均ROI", f"{kpi.get('avg_roi_pct', 0):.1f}%")
with c4:
    loss = kpi.get("loss_count", 0)
    st.metric("損失件数", f"{loss} 件",
              delta="要注意" if loss > 0 else "損失なし",
              delta_color="inverse" if loss > 0 else "off")

st.markdown("---")

# ================================================================
# 月次利益推移
# ================================================================
st.markdown('<div class="section-header">📈 月次利益推移</div>', unsafe_allow_html=True)

monthly_df = profit_calculator.monthly_profit(df)
if not monthly_df.empty:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=monthly_df["year_month_str"], y=monthly_df["売上"],
        name="売上高", marker_color=ORANGE, opacity=0.7
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=monthly_df["year_month_str"], y=monthly_df["仕入れ額"],
        name="仕入れ額", marker_color=DARK, opacity=0.7
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=monthly_df["year_month_str"], y=monthly_df["純利益"],
        name="純利益", mode="lines+markers",
        line=dict(color=GREEN, width=3),
        marker=dict(size=9)
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=monthly_df["year_month_str"], y=monthly_df["利益率"],
        name="利益率(%)", mode="lines+markers",
        line=dict(color=PURPLE, width=2, dash="dot"),
        marker=dict(size=7)
    ), secondary_y=True)
    fig.update_layout(height=400, hovermode="x unified",
                      legend=dict(orientation="h", y=1.02),
                      barmode="group", plot_bgcolor="white")
    fig.update_yaxes(title_text="金額 (¥)", secondary_y=False, tickprefix="¥")
    fig.update_yaxes(title_text="利益率 (%)", secondary_y=True, ticksuffix="%")
    fig.update_xaxes(tickangle=30)
    st.plotly_chart(fig, use_container_width=True)

# ================================================================
# 商品別利益ランキング & 仕入れ先別ROI
# ================================================================
st.markdown('<div class="section-header">🏆 商品別 & 仕入れ先別 分析</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    product_df = profit_calculator.product_pl(df)
    if not product_df.empty:
        top8 = product_df.head(8).copy()
        top8_sorted = top8.sort_values("純利益")
        colors = [GREEN if v >= 0 else RED for v in top8_sorted["純利益"]]
        fig = go.Figure(go.Bar(
            x=top8_sorted["純利益"], y=top8_sorted["product_name"],
            orientation="h", marker_color=colors,
            text=[f"¥{v:,.0f}" for v in top8_sorted["純利益"]],
            textposition="outside",
        ))
        fig.update_layout(height=400, plot_bgcolor="white",
                          title="商品別 純利益ランキング",
                          xaxis_title="純利益 (¥)")
        fig.update_xaxes(tickprefix="¥")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    platform_df = profit_calculator.platform_profit(df)
    if not platform_df.empty:
        fig = px.bar(
            platform_df, x="buy_platform", y="平均ROI",
            color="平均ROI",
            color_continuous_scale=["#FFCDD2", ORANGE, GREEN],
            title="仕入れ先別 平均ROI",
            labels={"buy_platform": "仕入れ先", "平均ROI": "ROI (%)"},
            text="平均ROI",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(height=400, showlegend=False,
                          coloraxis_showscale=False, plot_bgcolor="white")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# Amazonフィー内訳
# ================================================================
st.markdown('<div class="section-header">💸 Amazon手数料内訳</div>', unsafe_allow_html=True)

fee_df = profit_calculator.fee_breakdown_summary(df)
if not fee_df.empty:
    col3, col4 = st.columns([2, 3])
    with col3:
        fig = px.pie(fee_df, values="合計金額", names="費用項目",
                     color_discrete_sequence=[RED, ORANGE, BLUE, "#95A5A6"],
                     title="手数料構成",
                     hole=0.35)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        total_fees = kpi.get("total_fees", 0)
        total_revenue = kpi.get("total_revenue", 1)
        st.markdown(f"""
        **手数料サマリー**
        | 項目 | 金額 |
        |------|------|
        | 総売上 | ¥{kpi.get('total_revenue', 0):,.0f} |
        | 総仕入れ費用 | ¥{kpi.get('total_cost', 0):,.0f} |
        | 総手数料 | ¥{total_fees:,.0f} |
        | 総純利益 | ¥{kpi.get('total_net_profit', 0):,.0f} |
        | 手数料率 | {total_fees / total_revenue * 100:.1f}% |
        | 純利益率 | {kpi.get('avg_margin_pct', 0):.1f}% |
        """)

# ================================================================
# 商品別損益表 (全件)
# ================================================================
st.markdown('<div class="section-header">📑 商品別損益表</div>', unsafe_allow_html=True)

product_df = profit_calculator.product_pl(df)
if not product_df.empty:
    disp = product_df.copy()
    disp.index = range(1, len(disp) + 1)

    def fmt_profit(v):
        sign = "+" if v >= 0 else ""
        color = "#2ECC71" if v >= 0 else "#E74C3C"
        return f'<span style="color:{color};font-weight:700">{sign}¥{v:,.0f}</span>'

    st.dataframe(
        disp.rename(columns={
            "asin": "ASIN", "product_name": "商品名", "category": "カテゴリ",
            "販売件数": "販売件数", "販売数量": "販売数量",
            "売上合計": "売上合計(¥)", "仕入れ総額": "仕入れ総額(¥)",
            "手数料合計": "手数料(¥)", "純利益": "純利益(¥)",
            "平均利益率": "利益率(%)", "平均ROI": "ROI(%)",
        }),
        use_container_width=True
    )

# ================================================================
# 損失商品リスト
# ================================================================
loss_df = profit_calculator.loss_items(df)
if not loss_df.empty:
    st.markdown('<div class="section-header">🚨 損失商品リスト</div>', unsafe_allow_html=True)
    st.error(f"損失が発生している取引が {len(loss_df)} 件あります")

    loss_disp = loss_df[[
        "product_name", "buy_platform", "condition", "unit_cost",
        "sale_price", "total_fees", "net_profit", "roi_pct", "days_to_sell"
    ]].copy()
    loss_disp.columns = [
        "商品名", "仕入れ先", "コンディション", "仕入れ単価(¥)",
        "売価(¥)", "手数料(¥)", "純利益(¥)", "ROI(%)", "販売日数"
    ]
    st.dataframe(loss_disp, use_container_width=True, hide_index=True)

# ================================================================
# ROI ランキング TOP10
# ================================================================
st.markdown('<div class="section-header">⭐ ROI ランキング TOP10</div>', unsafe_allow_html=True)
roi_df = profit_calculator.best_roi_items(df, top_n=10)
if not roi_df.empty:
    roi_df.index = range(1, len(roi_df) + 1)
    disp_roi = roi_df.copy()
    disp_roi.columns = [
        "商品名", "仕入れ先", "仕入れ単価(¥)", "売価(¥)",
        "純利益(¥)", "ROI(%)", "利益率(%)", "販売日数"
    ]
    st.dataframe(disp_roi, use_container_width=True)
