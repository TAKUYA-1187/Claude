"""
Amazon Seller Analytics - Configuration
========================================
SP-API認証情報の設定ファイル

必要な認証情報:
  - SELLER_ID       : Amazon セラーID (マーチャントID)
  - LWA_APP_ID      : Login with Amazon クライアントID
  - LWA_CLIENT_SECRET: Login with Amazon クライアントシークレット
  - LWA_REFRESH_TOKEN: LWAリフレッシュトークン
  - AWS_ACCESS_KEY  : AWS アクセスキー (SP-API用IAMユーザー)
  - AWS_SECRET_KEY  : AWS シークレットキー
  - AWS_ROLE_ARN    : IAMロールARN (SP-APIアクセス用)
"""

import os
from dataclasses import dataclass

@dataclass
class SPAPIConfig:
    # ---- セラー情報 ----
    seller_id: str = os.getenv("AMAZON_SELLER_ID", "A2B1UA7OXUW3IW")
    marketplace_id: str = os.getenv("AMAZON_MARKETPLACE_ID", "A1VC38T7YXB528")  # 日本 (JP)

    # ---- Login with Amazon (LWA) 認証 ----
    lwa_app_id: str = os.getenv("LWA_APP_ID", "")
    lwa_client_secret: str = os.getenv("LWA_CLIENT_SECRET", "")
    lwa_refresh_token: str = os.getenv("LWA_REFRESH_TOKEN", "")

    # ---- AWS 認証 (SigV4) ----
    aws_access_key: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_role_arn: str = os.getenv("AWS_ROLE_ARN", "")
    aws_region: str = "us-east-1"

    # ---- SP-API エンドポイント ----
    endpoint: str = "https://sellingpartnerapi-fe.amazon.com"  # 日本/Far East

    # ---- マーケットプレイスID一覧 ----
    MARKETPLACES = {
        "JP": "A1VC38T7YXB528",
        "US": "ATVPDKIKX0DER",
        "UK": "A1F83G8C2ARO7P",
        "DE": "A1PA6795UKMFR9",
    }


# デフォルト設定インスタンス
config = SPAPIConfig()

# アプリ設定
APP_CONFIG = {
    "app_title": "Amazon セラーアナリティクス",
    "currency": "JPY",
    "currency_symbol": "¥",
    "date_format": "%Y-%m-%d",
    "report_output_dir": "reports",
    "data_cache_dir": "data",
    "demo_mode": True,  # API未設定時はデモデータを使用

    # ---- 物販プラットフォーム ----
    "buy_platforms": ["Yahoo Shopping", "楽天市場", "買取商店", "WIKI", "その他"],
    "sell_platforms": ["Amazon", "Yahoo Shopping", "楽天市場", "買取商店", "WIKI"],

    # ---- 商品コンディション ----
    "conditions": ["新品", "中古A", "中古B", "中古C", "ジャンク"],

    # ---- 仕入れステータス ----
    "purchase_statuses": ["未出品", "出品中", "売却済", "返品", "廃棄"],

    # ---- Amazonカテゴリ別紹介料 (%) ----
    "amazon_referral_fees": {
        "家電・カメラ":          8.0,
        "パソコン・周辺機器":    8.0,
        "スマートフォン":        8.0,
        "おもちゃ・ホビー":     10.0,
        "スポーツ・アウトドア": 10.0,
        "ゲーム":               10.0,
        "ファッション":         10.0,
        "本・雑誌":             15.0,
        "音楽・CD":             15.0,
        "その他":               10.0,
    },

    # ---- Amazon FBA料金ティア (売価レンジ→固定手数料 JPY) ----
    "fba_fee_tiers": [
        {"max_price":  5_000, "fee":   500},
        {"max_price": 10_000, "fee":   800},
        {"max_price": 20_000, "fee": 1_200},
        {"max_price": 50_000, "fee": 1_800},
        {"max_price": 999_999, "fee": 2_500},
    ],

    # ---- 買取店名リスト (例) ----
    "buyback_shops": ["ブックオフ", "ゲオ", "ハードオフ", "WIKI買取", "なんぼや", "その他"],
}
