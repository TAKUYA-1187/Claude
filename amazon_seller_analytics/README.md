# Amazon セラーアナリティクス

Amazonセラーの売上・在庫・商品データをリアルタイム分析するダッシュボードツール。

## 機能一覧

| カテゴリ | 機能 |
|----------|------|
| **売上分析** | 日次/週次/月次売上集計、前月比成長率 |
| **商品分析** | 商品別売上ランキング、売上シェア、価格分析 |
| **フルフィルメント** | FBA/FBM別売上・注文比率 |
| **曜日分析** | 曜日別売上・平均注文額のヒートマップ |
| **在庫管理** | 在庫日数・在庫不足アラート・補充推奨数 |
| **売上予測** | 移動平均ベースの30日先予測 |
| **レポート出力** | Excel (5シート)・HTML・CSV |

## セットアップ

```bash
cd amazon_seller_analytics
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env を編集して認証情報を入力

# ダッシュボード起動
streamlit run dashboard.py
```

## API連携の設定

### 必要な認証情報

1. **Amazon Seller Central** でのアプリ登録
   - `Seller Central > アプリと連携 > デベロッパーセントラル`
   - LWA App ID と Client Secret を取得

2. **SP-API へのアクセス申請**
   - `Seller Central > アプリと連携 > アプリの管理` でSP-API申請
   - LWA Refresh Token を取得

3. **AWS IAM** の設定
   - SP-API用IAMユーザーを作成
   - `AmazonSellingPartnerAPIRole` ポリシーをアタッチ
   - Access Key / Secret Key を取得

### デモモード

API認証情報が未設定の場合、自動的にデモデータで動作します。  
実際のAPIを使用しない状態でも、ダッシュボードの全機能を確認できます。

## ファイル構成

```
amazon_seller_analytics/
├── config.py            # 認証設定・定数
├── sp_api_client.py     # SP-API クライアント (LWA + SigV4)
├── sales_analytics.py   # 売上分析モジュール
├── inventory_manager.py # 在庫管理モジュール
├── report_generator.py  # レポート生成 (Excel/HTML/CSV)
├── dashboard.py         # Streamlit ダッシュボード
├── requirements.txt     # 依存パッケージ
└── .env.example         # 環境変数サンプル
```

## セラーID

このツールはセラーID `A2B1UA7OXUW3IW` で設定されています。  
`config.py` または `.env` の `AMAZON_SELLER_ID` で変更できます。
