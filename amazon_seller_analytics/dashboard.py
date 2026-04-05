"""
Amazon 物販アナリティクス — ホームダッシュボード
=================================================
Streamlit Multi-Page App のエントリポイント。

起動方法:
    streamlit run dashboard.py

ページ一覧 (サイドバーから遷移):
    🏠 ホーム          (このページ) Amazon売上・在庫分析
    🛒 仕入れ管理      Yahoo Shopping / 楽天市場 / 買取商店 / WIKI
    💰 利益計算        仕入れ〜販売の損益・ROI分析
    📊 販売実績管理     商品ライフサイクル統合ビュー
    ⚖️  出口比較        Amazon vs 買取の最適出口推奨エンジン
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from config import APP_CONFIG, config
from sales_analytics import analytics
from inventory_manager import inventory_manager
from report_generator import report_gen

# ================================================================
# ページ設定
# ================================================================
st.set_page_config(
    page_title="Amazon セラーアナリティクス",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

AMAZON_ORANGE = "#FF8C00"
AMAZON_DARK = "#232F3E"
CHART_COLORS = ["#FF8C00", "#FF6600", "#232F3E", "#00A8E0", "#5D3FD3", "#2ECC71", "#E74C3C"]

# ================================================================
# CSS カスタムスタイル
# ================================================================
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 28px !important; color: #FF8C00; }
[data-testid="stMetricLabel"] { font-size: 13px !important; }
.stAlert { border-radius: 8px; }
div[data-testid="stSidebar"] { background-color: #232F3E; }
div[data-testid="stSidebar"] * { color: white !important; }
h1, h2, h3 { color: #232F3E; }
.section-header { background: linear-gradient(90deg, #FF8C00, #FF6600);
                  color: white; padding: 8px 16px; border-radius: 6px;
                  margin: 16px 0 12px 0; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# データ取得 (キャッシュ付き)
# ================================================================
@st.cache_data(ttl=300)
def load_data(days: int):
    df = analytics.fetch_orders_df(days=days)
    return df

@st.cache_data(ttl=300)
def load_inventory():
    return inventory_manager.fetch_inventory_df()


# ================================================================
# サイドバー
# ================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
             width=120)
    st.markdown(f"### セラーID\n`{config.seller_id}`")
    st.markdown("---")

    st.markdown("#### 分析期間")
    period = st.selectbox(
        "期間選択",
        options=[30, 60, 90, 180, 365],
        index=2,
        format_func=lambda x: f"過去 {x} 日間"
    )

    st.markdown("---")

    # ページナビゲーション案内
    st.markdown("#### ページ一覧")
    st.markdown("""
🏠 **Amazon売上分析** (このページ)
🛒 **仕入れ管理**
💰 **利益計算**
📊 **販売実績管理**
⚖️ **出口比較**

← サイドバーのリンクから遷移
""")

    st.markdown("---")
    api_status = "🟡 デモモード" if not config.lwa_app_id else "🟢 SP-API 接続済"
    st.markdown(f"**API状態:** {api_status}")

    if not config.lwa_app_id:
        st.info("SP-API認証情報を設定すると\nリアルタイムデータが取得できます")
        with st.expander("設定方法"):
            st.code("""# .env ファイルに設定:
LWA_APP_ID=amzn1.application-oa2-client.xxx
LWA_CLIENT_SECRET=xxx
LWA_REFRESH_TOKEN=Atzr|xxx
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxx
AWS_ROLE_ARN=arn:aws:iam::...""", language="bash")

    st.markdown("---")
    generate_report = st.button("📥 全データ Excelレポート生成", use_container_width=True)


# ================================================================
# メインコンテンツ
# ================================================================
st.markdown(f"""
<div style="background:linear-gradient(135deg,#232F3E,#FF8C00);
     padding:20px 28px;border-radius:10px;color:white;margin-bottom:24px">
  <h1 style="color:white;margin:0;font-size:28px">📦 Amazon 物販アナリティクス</h1>
  <p style="margin:4px 0 0;opacity:.85">
    セラーID: {config.seller_id} | マーケット: 日本 (JP) |
    最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}
  </p>
  <p style="margin:6px 0 0;opacity:.7;font-size:13px">
    🛒 仕入れ管理 | 💰 利益計算 | 📊 販売実績管理 | ⚖️ 出口比較
    — サイドバーから各ページへ遷移できます
  </p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
with st.spinner("データを取得中..."):
    orders_df = load_data(period)
    inventory_df = load_inventory()

if orders_df.empty:
    st.error("注文データを取得できませんでした。")
    st.stop()

# 分析実行
kpi = analytics.get_kpi_summary(orders_df)
daily_df = analytics.daily_sales(orders_df)
monthly_df = analytics.monthly_sales(orders_df)
weekly_df = analytics.weekly_sales(orders_df)
product_df = analytics.product_sales_ranking(orders_df, top_n=10)
fulfillment_df = analytics.fulfillment_analysis(orders_df)
dow_df = analytics.day_of_week_analysis(orders_df)

# 在庫分析
if not inventory_df.empty:
    inventory_df = inventory_manager.add_sales_velocity(inventory_df, orders_df)
    inv_stats = inventory_manager.inventory_summary_stats(inventory_df)
    inv_alerts = inventory_manager.get_alerts(inventory_df)
else:
    inv_stats = {}
    inv_alerts = {}

# ================================================================
# KPI カード
# ================================================================
st.markdown('<div class="section-header">📊 KPI サマリー</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("総売上", f"¥{kpi.get('total_revenue', 0):,.0f}")
with c2:
    st.metric("総注文数", f"{kpi.get('total_orders', 0):,} 件")
with c3:
    st.metric("平均注文金額", f"¥{kpi.get('avg_order_value', 0):,.0f}")
with c4:
    mom = kpi.get("mom_growth_pct", 0)
    st.metric("今月売上", f"¥{kpi.get('this_month_revenue', 0):,.0f}",
              delta=f"{mom:+.1f}% 前月比")
with c5:
    alert_count = (len(inv_alerts.get("out_of_stock", [])) +
                   len(inv_alerts.get("critical", []))) if inv_alerts else 0
    st.metric("在庫アラート", f"{alert_count} 件",
              delta="要対応" if alert_count > 0 else "問題なし",
              delta_color="inverse" if alert_count > 0 else "off")

st.markdown("---")

# ================================================================
# 売上トレンドチャート
# ================================================================
st.markdown('<div class="section-header">📈 売上トレンド</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["日次", "週次", "月次"])

with tab1:
    if not daily_df.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=daily_df["date"], y=daily_df["revenue"],
            name="日次売上", marker_color=AMAZON_ORANGE, opacity=0.7
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=daily_df["date"], y=daily_df["revenue_ma7"],
            name="7日移動平均", line=dict(color="#232F3E", width=2.5)
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=daily_df["date"], y=daily_df["orders"],
            name="注文数", line=dict(color="#00A8E0", width=1.5, dash="dot"),
            mode="lines"
        ), secondary_y=True)
        fig.update_layout(height=380, hovermode="x unified",
                          legend=dict(orientation="h", y=1.02),
                          plot_bgcolor="white")
        fig.update_yaxes(title_text="売上 (¥)", secondary_y=False, tickprefix="¥")
        fig.update_yaxes(title_text="注文数", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    if not weekly_df.empty:
        weekly_df_plot = weekly_df.copy()
        weekly_df_plot["week_label"] = weekly_df_plot["year_week"].astype(str)
        fig = px.bar(weekly_df_plot, x="week_label", y="revenue",
                     color_discrete_sequence=[AMAZON_ORANGE],
                     labels={"week_label": "週", "revenue": "売上"},
                     title="週次売上")
        fig.update_layout(height=360, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not monthly_df.empty:
        monthly_df_plot = monthly_df.copy()
        monthly_df_plot["month_label"] = monthly_df_plot["year_month"].astype(str)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=monthly_df_plot["month_label"], y=monthly_df_plot["revenue"],
            name="月次売上", marker_color=AMAZON_ORANGE
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=monthly_df_plot["month_label"],
            y=monthly_df_plot["revenue_growth"],
            name="前月比(%)", mode="lines+markers",
            line=dict(color="#E74C3C", width=2),
            marker=dict(size=8)
        ), secondary_y=True)
        fig.update_layout(height=380, hovermode="x unified",
                          legend=dict(orientation="h", y=1.02),
                          plot_bgcolor="white")
        fig.update_yaxes(title_text="売上 (¥)", secondary_y=False, tickprefix="¥")
        fig.update_yaxes(title_text="成長率 (%)", secondary_y=True, ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# 商品分析 & フルフィルメント分析
# ================================================================
st.markdown('<div class="section-header">🛍️ 商品別分析</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2])

with col_left:
    if not product_df.empty:
        fig = px.bar(
            product_df.head(8).sort_values("revenue"),
            x="revenue", y="product_name",
            orientation="h",
            color="revenue",
            color_continuous_scale=["#FFE0B2", AMAZON_ORANGE, "#E65100"],
            labels={"revenue": "売上", "product_name": "商品名"},
            title="商品別売上ランキング TOP8"
        )
        fig.update_layout(height=400, showlegend=False,
                          coloraxis_showscale=False, plot_bgcolor="white")
        fig.update_xaxes(tickprefix="¥")
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    if not fulfillment_df.empty:
        fig = px.pie(
            fulfillment_df, values="revenue", names="fulfillment_label",
            color_discrete_sequence=[AMAZON_ORANGE, AMAZON_DARK],
            title="FBA / FBM 売上比率",
            hole=0.4
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# 商品ランキングテーブル
with st.expander("商品別売上詳細テーブル"):
    if not product_df.empty:
        display_df = product_df.copy()
        display_df.index = range(1, len(display_df) + 1)
        display_df["revenue"] = display_df["revenue"].apply(lambda x: f"¥{x:,.0f}")
        display_df["avg_price"] = display_df["avg_price"].apply(lambda x: f"¥{x:,.0f}")
        display_df["revenue_share"] = display_df["revenue_share"].apply(lambda x: f"{x:.1f}%")
        display_df.columns = ["商品名", "ASIN", "売上", "販売数", "注文数", "平均価格", "売上シェア"]
        st.dataframe(display_df, use_container_width=True)

# ================================================================
# 曜日別分析
# ================================================================
if not dow_df.empty:
    st.markdown('<div class="section-header">📅 曜日別売上分析</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(dow_df, x="day_name", y="revenue",
                     color="revenue",
                     color_continuous_scale=["#FFE0B2", AMAZON_ORANGE, "#E65100"],
                     title="曜日別 総売上",
                     labels={"day_name": "曜日", "revenue": "売上"})
        fig.update_layout(height=320, showlegend=False,
                          coloraxis_showscale=False, plot_bgcolor="white")
        fig.update_yaxes(tickprefix="¥")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(dow_df, x="day_name", y="avg_order_value",
                     color="avg_order_value",
                     color_continuous_scale=["#E3F2FD", "#00A8E0", "#01579B"],
                     title="曜日別 平均注文金額",
                     labels={"day_name": "曜日", "avg_order_value": "平均注文額"})
        fig.update_layout(height=320, showlegend=False,
                          coloraxis_showscale=False, plot_bgcolor="white")
        fig.update_yaxes(tickprefix="¥")
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# 在庫ダッシュボード
# ================================================================
st.markdown('<div class="section-header">📦 在庫管理ダッシュボード</div>',
            unsafe_allow_html=True)

if not inventory_df.empty and inv_stats:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("管理SKU数", f"{inv_stats.get('total_skus', 0)} 件")
    with c2:
        st.metric("販売可能在庫 合計", f"{inv_stats.get('total_fulfillable', 0):,} 個")
    with c3:
        st.metric("入荷予定", f"{inv_stats.get('total_inbound', 0):,} 個")
    with c4:
        avg_days = inv_stats.get("avg_days_of_stock")
        st.metric("平均在庫日数",
                  f"{avg_days:.0f} 日" if avg_days else "N/A",
                  delta="要補充" if avg_days and avg_days < 14 else "問題なし",
                  delta_color="inverse" if avg_days and avg_days < 14 else "off")

    # アラート表示
    out_of_stock = inv_alerts.get("out_of_stock", pd.DataFrame())
    critical = inv_alerts.get("critical", pd.DataFrame())
    low_stock = inv_alerts.get("low_stock", pd.DataFrame())

    if not out_of_stock.empty:
        st.error(f"🚨 在庫切れ: {len(out_of_stock)} 件")
        st.dataframe(
            out_of_stock[["product_name", "seller_sku", "fulfillable_qty"]].rename(
                columns={"product_name": "商品名", "seller_sku": "SKU",
                         "fulfillable_qty": "在庫数"}
            ), use_container_width=True
        )

    if not critical.empty:
        st.warning(f"⚠️ 在庫危険水準 ({inventory_manager.CRITICAL_STOCK}個以下): {len(critical)} 件")

    if not low_stock.empty:
        st.info(f"ℹ️ 低在庫 ({inventory_manager.LOW_STOCK}個以下): {len(low_stock)} 件")

    # 在庫状況チャート
    col1, col2 = st.columns(2)
    with col1:
        if "stock_status" in inventory_df.columns:
            status_counts = inventory_df["stock_status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            color_map = {"正常": "#2ECC71", "低在庫": "#F39C12",
                         "危険水準": "#E74C3C", "在庫切れ": "#8B0000", "不明": "#95A5A6"}
            fig = px.pie(status_counts, values="count", names="status",
                         color="status", color_discrete_map=color_map,
                         title="在庫状態別 SKU数", hole=0.35)
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            inventory_df.sort_values("fulfillable_qty", ascending=False),
            x="product_name", y="fulfillable_qty",
            color="fulfillable_qty",
            color_continuous_scale=["#FFCDD2", "#FF8C00", "#2ECC71"],
            title="商品別 販売可能在庫数",
            labels={"product_name": "商品", "fulfillable_qty": "在庫数"}
        )
        fig.update_xaxes(tickangle=30)
        fig.update_layout(height=360, showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    # 在庫詳細テーブル
    with st.expander("在庫詳細テーブル"):
        display_cols = ["product_name", "seller_sku", "asin", "fulfillable_qty",
                        "inbound_working", "inbound_shipped", "reserved_total"]
        extra = [c for c in ["stock_status", "days_of_stock", "reorder_qty",
                              "daily_sales_velocity"]
                 if c in inventory_df.columns]
        display_cols += extra

        disp = inventory_df[[c for c in display_cols if c in inventory_df.columns]].copy()
        disp.columns = [
            {"product_name": "商品名", "seller_sku": "SKU", "asin": "ASIN",
             "fulfillable_qty": "販売可能", "inbound_working": "入荷作業中",
             "inbound_shipped": "輸送中", "reserved_total": "予約済",
             "stock_status": "在庫状態", "days_of_stock": "在庫日数",
             "reorder_qty": "補充推奨数", "daily_sales_velocity": "日次販売数"
             }.get(c, c) for c in disp.columns
        ]
        st.dataframe(disp, use_container_width=True)

# ================================================================
# 売上予測
# ================================================================
st.markdown('<div class="section-header">🔮 売上予測</div>', unsafe_allow_html=True)

forecast_df = analytics.simple_forecast(daily_df, forecast_days=30)
if not forecast_df.empty and not daily_df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_df["date"], y=daily_df["revenue"],
        name="実績売上", line=dict(color=AMAZON_ORANGE, width=2)
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["date"], y=forecast_df["forecast_revenue"],
        name="予測売上", line=dict(color="#5D3FD3", width=2, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"], forecast_df["date"].iloc[::-1]]),
        y=pd.concat([forecast_df["upper_bound"], forecast_df["lower_bound"].iloc[::-1]]),
        fill="toself", fillcolor="rgba(93,63,211,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="予測範囲"
    ))
    fig.add_vline(
        x=daily_df["date"].max().timestamp() * 1000,
        line_dash="dot", line_color="gray", annotation_text="予測開始"
    )
    fig.update_layout(height=380, hovermode="x unified",
                      legend=dict(orientation="h", y=1.02),
                      plot_bgcolor="white")
    fig.update_yaxes(tickprefix="¥")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"予測手法: 過去30日間の移動平均 | 予測売上: "
               f"¥{forecast_df['forecast_revenue'].mean():,.0f}/日")

# ================================================================
# レポート生成 (9シート Excel + HTML)
# ================================================================
if generate_report:
    with st.spinner("全データのレポートを生成中 (Amazon売上 + 仕入れ + 利益計算)..."):
        try:
            html_path = report_gen.export_html(
                kpi, daily_df, monthly_df, product_df, inventory_df
            )
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.download_button(
                "📄 HTMLレポートをダウンロード",
                data=html_content,
                file_name=os.path.basename(html_path),
                mime="text/html",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"HTMLレポート生成エラー: {e}")

        try:
            excel_path = report_gen.export_excel(
                kpi, daily_df, monthly_df, product_df, inventory_df
            )
            with open(excel_path, "rb") as f:
                excel_content = f.read()
            st.download_button(
                "📊 Excelレポート (9シート) をダウンロード",
                data=excel_content,
                file_name=os.path.basename(excel_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success("""レポート生成完了!
**含まれるシート (9枚):**
1. KPIサマリー 2. 月次売上 3. 商品別ランキング
4. 在庫状況 5. 日次売上 6. 仕入れ履歴
7. 利益計算表 8. 商品別損益 9. プラットフォーム別""")
        except Exception as e:
            st.warning(f"Excelレポートにはopenpyxlが必要です: pip install openpyxl")

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#aaa;font-size:12px'>"
    f"Amazon 物販アナリティクス | セラーID: {config.seller_id} | "
    f"Powered by Amazon SP-API | "
    f"仕入れ先: Yahoo Shopping / 楽天市場 / 買取商店 / WIKI</div>",
    unsafe_allow_html=True
)
