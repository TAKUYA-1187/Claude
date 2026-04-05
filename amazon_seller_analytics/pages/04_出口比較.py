"""
出口比較ページ
==============
Amazon vs 買取商店・WIKI の最適出口戦略を比較分析。
リアルタイム推奨エンジン付き。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from buyback_manager import buyback_manager
from profit_calculator import profit_calculator
from config import APP_CONFIG
from purchase_manager import PRODUCTS

ORANGE = "#FF8C00"
DARK   = "#232F3E"
GREEN  = "#2ECC71"
RED    = "#E74C3C"
BLUE   = "#00A8E0"
COLORS = [ORANGE, BLUE, GREEN, "#5D3FD3", RED, "#F39C12"]

st.set_page_config(page_title="出口比較", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 26px !important; color: #FF8C00; }
.section-header { background: linear-gradient(90deg,#FF8C00,#FF6600);
  color:white; padding:8px 16px; border-radius:6px; margin:16px 0 12px; font-weight:700; }
.rec-amazon { background:#E8F5E9;border-left:5px solid #2ECC71;padding:16px;border-radius:8px; }
.rec-buyback { background:#E3F2FD;border-left:5px solid #00A8E0;padding:16px;border-radius:8px; }
.rec-neutral { background:#FFF9C4;border-left:5px solid #F39C12;padding:16px;border-radius:8px; }
</style>""", unsafe_allow_html=True)

# ================================================================
# データ取得
# ================================================================
@st.cache_data(ttl=300)
def load_data():
    buyback_df = buyback_manager.get_buyback_records()
    sales_df   = profit_calculator.get_sales_with_profit()
    return buyback_df, sales_df

buyback_df, sales_df = load_data()
kpi = buyback_manager.get_kpi_summary(buyback_df)

# ================================================================
# ヘッダー
# ================================================================
st.markdown("""
<div style="background:linear-gradient(135deg,#232F3E,#00A8E0);
     padding:18px 24px;border-radius:10px;color:white;margin-bottom:20px">
  <h1 style="color:white;margin:0;font-size:26px">⚖️ 出口比較 — Amazon vs 買取</h1>
  <p style="margin:4px 0 0;opacity:.85">最適な出口戦略を選択: Amazon販売 / 買取商店 / WIKI</p>
</div>""", unsafe_allow_html=True)

# ================================================================
# KPIカード
# ================================================================
st.markdown('<div class="section-header">📊 買取 KPI</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("買取総件数", f"{kpi.get('total_records', 0)} 件")
with c2:
    st.metric("売却済", f"{kpi.get('sold_count', 0)} 件",
              delta=f"¥{kpi.get('total_buyback_revenue', 0):,.0f} 回収")
with c3:
    st.metric("Amazon推奨", f"{kpi.get('amazon_recommended', 0)} 件")
with c4:
    st.metric("買取推奨", f"{kpi.get('buyback_recommended', 0)} 件")

st.markdown("---")

# ================================================================
# 出口別 平均利益比較
# ================================================================
st.markdown('<div class="section-header">📊 出口別 利益比較</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Amazon vs 買取 利益分布
    comparison_data = []
    if not sales_df.empty:
        amazon_profit = sales_df[sales_df["platform"] == "Amazon"]["net_profit"]
        if not amazon_profit.empty:
            comparison_data.append({
                "出口": "Amazon", "平均純利益": amazon_profit.mean(),
                "中央値利益": amazon_profit.median(),
                "件数": len(amazon_profit)
            })
    if not buyback_df.empty:
        bb_sold = buyback_df[buyback_df["status"] == "売却済"]
        if not bb_sold.empty:
            comparison_data.append({
                "出口": "買取商店",
                "平均純利益": bb_sold["buyback_profit"].mean(),
                "中央値利益": bb_sold["buyback_profit"].median(),
                "件数": len(bb_sold)
            })

    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        fig = px.bar(comp_df, x="出口", y="平均純利益",
                     color="出口", color_discrete_sequence=[ORANGE, BLUE],
                     title="出口別 平均純利益",
                     text="平均純利益")
        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
        fig.update_layout(height=360, showlegend=False, plot_bgcolor="white")
        fig.update_yaxes(tickprefix="¥")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # 推奨分布
    if not buyback_df.empty:
        rec_counts = buyback_df["recommendation"].value_counts().reset_index()
        rec_counts.columns = ["推奨", "件数"]
        REC_COLOR = {
            "Amazon推奨": ORANGE,
            "買取推奨": BLUE,
            "どちらでも可": "#F39C12"
        }
        fig = px.pie(rec_counts, values="件数", names="推奨",
                     color="推奨", color_discrete_map=REC_COLOR,
                     title="推奨出口の分布", hole=0.4)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# 月次買取実績チャート
# ================================================================
monthly_bb = buyback_manager.monthly_buyback_trend(buyback_df)
if not monthly_bb.empty:
    st.markdown('<div class="section-header">📈 月次買取実績</div>', unsafe_allow_html=True)
    fig = make_subplots = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_bb["year_month_str"], y=monthly_bb["買取売上"],
        name="買取売上", marker_color=BLUE, opacity=0.8
    ))
    fig.add_trace(go.Scatter(
        x=monthly_bb["year_month_str"], y=monthly_bb["買取利益"],
        name="買取利益", mode="lines+markers",
        line=dict(color=GREEN, width=3), marker=dict(size=9)
    ))
    fig.update_layout(height=320, hovermode="x unified",
                      legend=dict(orientation="h"), plot_bgcolor="white")
    fig.update_yaxes(tickprefix="¥")
    fig.update_xaxes(tickangle=30)
    st.plotly_chart(fig, use_container_width=True)

# ================================================================
# Amazon vs 買取 比較表
# ================================================================
st.markdown('<div class="section-header">📋 Amazon vs 買取 比較表</div>',
            unsafe_allow_html=True)

comp_table = buyback_manager.exit_comparison(buyback_df)
if not comp_table.empty:
    REC_COLOR_MAP = {
        "Amazon推奨": f"background-color: #E8F5E9",
        "買取推奨":   f"background-color: #E3F2FD",
        "どちらでも可": f"background-color: #FFF9C4",
    }
    disp = comp_table.copy()
    disp.columns = [
        "商品名", "コンディション", "仕入れ単価(¥)",
        "Amazon参考売価(¥)", "Amazon純利益(¥)",
        "買取店", "買取価格(¥)", "買取利益(¥)",
        "差額(¥)", "推奨", "理由"
    ]
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ================================================================
# 店舗別買取集計
# ================================================================
shop_df = buyback_manager.shop_breakdown(buyback_df)
if not shop_df.empty:
    st.markdown('<div class="section-header">🏪 買取店舗別集計</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        fig = px.bar(shop_df, x="buyback_shop", y="平均買取価格",
                     color_discrete_sequence=[BLUE],
                     title="店舗別 平均買取価格",
                     labels={"buyback_shop": "店舗名", "平均買取価格": "平均買取価格(¥)"},
                     text="平均買取価格")
        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
        fig.update_layout(height=320, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        st.dataframe(shop_df.rename(columns={
            "buyback_shop": "店舗名", "件数": "件数",
            "売却済": "売却済", "平均買取価格": "平均買取価格(¥)",
            "平均利益": "平均利益(¥)"
        }), use_container_width=True, hide_index=True)

st.markdown("---")

# ================================================================
# リアルタイム推奨エンジン
# ================================================================
st.markdown('<div class="section-header">🤖 出口推奨エンジン (リアルタイム計算)</div>',
            unsafe_allow_html=True)

st.markdown("商品情報と買取提示額を入力すると、Amazon販売と買取のどちらが有利かを計算します。")

product_names = [p["name"] for p in PRODUCTS]
categories    = list(APP_CONFIG["amazon_referral_fees"].keys())

col_a, col_b, col_c = st.columns(3)
with col_a:
    sel_product = st.selectbox("商品名", ["カスタム入力"] + product_names)
    if sel_product == "カスタム入力":
        product_name = st.text_input("商品名を入力", "")
    else:
        product_name = sel_product

with col_b:
    sel_cat = st.selectbox("カテゴリ (Amazon紹介料計算用)", categories,
                            index=categories.index("家電・カメラ") if "家電・カメラ" in categories else 0)

with col_c:
    is_fba = st.checkbox("FBA利用 (Amazonフルフィルメント)", value=True)

# デフォルト価格をプリセット
default_cost  = 5000
default_price = 10000
if sel_product != "カスタム入力":
    for p in PRODUCTS:
        if p["name"] == sel_product:
            default_cost  = int((p["buy_range"][0] + p["buy_range"][1]) / 2)
            default_price = p["sell_price"]
            break

col_d, col_e, col_f = st.columns(3)
with col_d:
    unit_cost = st.number_input("仕入れ単価 (¥)", min_value=0, value=default_cost, step=100)
with col_e:
    amazon_price = st.number_input("Amazon想定売価 (¥)", min_value=0, value=default_price, step=100)
with col_f:
    buyback_price = st.number_input("買取提示額 (¥)", min_value=0,
                                     value=int(default_price * 0.55), step=100)

if st.button("推奨出口を計算", type="primary", use_container_width=True):
    result = buyback_manager.recommendation_engine(
        product_name=product_name or "未入力商品",
        unit_cost=float(unit_cost),
        amazon_price=float(amazon_price),
        buyback_price=float(buyback_price),
        category=sel_cat,
        is_fba=is_fba,
    )

    # 結果表示
    icon = result["icon"]
    if icon == "Amazon":
        css_class = "rec-amazon"
        emoji = "🟠"
        header = "Amazon販売を推奨"
    elif icon == "buyback":
        css_class = "rec-buyback"
        emoji = "🔵"
        header = "買取を推奨"
    else:
        css_class = "rec-neutral"
        emoji = "🟡"
        header = "どちらでも可"

    st.markdown(f"""
    <div class="{css_class}">
      <h3>{emoji} {header}</h3>
      <p><b>{result['decision']}</b> (差額: ¥{result['profit_diff']:,.0f})</p>
    </div>
    """, unsafe_allow_html=True)

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.markdown(f"""
        **🟠 Amazon販売シミュレーション**
        | 項目 | 金額 |
        |------|------|
        | Amazon売価 | ¥{result['amazon_price']:,.0f} |
        | 仕入れ単価 | -¥{result['unit_cost']:,.0f} |
        | Amazon紹介料 | -¥{result['amazon_referral']:,.0f} |
        | FBA手数料 | -¥{result['amazon_fba']:,.0f} |
        | 送料 | -¥{result['amazon_shipping']:,.0f} |
        | その他 | -¥{result['amazon_other']:,.0f} |
        | **純利益** | **¥{result['amazon_profit']:,.0f}** |
        | 利益率 | {result['amazon_margin_pct']:.1f}% |
        """)
    with col_res2:
        st.markdown(f"""
        **🔵 買取シミュレーション**
        | 項目 | 金額 |
        |------|------|
        | 買取価格 | ¥{result['buyback_price']:,.0f} |
        | 仕入れ単価 | -¥{result['unit_cost']:,.0f} |
        | 手数料 | ¥0 |
        | 送料 | ¥0 |
        | その他 | ¥0 |
        | **純利益** | **¥{result['buyback_profit']:,.0f}** |
        | 利益率 | {result['buyback_margin_pct']:.1f}% |
        """)
        st.info("💡 買取のメリット: 在庫リスクなし・即現金化")
