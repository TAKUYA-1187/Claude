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
}
