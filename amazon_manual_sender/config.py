"""設定管理モジュール - .env ファイルから Amazon SP-API 設定を読み込む"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    lwa_client_id: str
    lwa_client_secret: str
    lwa_refresh_token: str
    seller_id: str
    marketplace_id: str
    product_asin: str
    manual_url: str
    state_file: Path
    days_back: int


def load_config() -> Config:
    lwa_client_id = os.environ.get("SP_LWA_CLIENT_ID", "")
    lwa_client_secret = os.environ.get("SP_LWA_CLIENT_SECRET", "")
    lwa_refresh_token = os.environ.get("SP_LWA_REFRESH_TOKEN", "")
    seller_id = os.environ.get("SP_SELLER_ID", "")
    marketplace_id = os.environ.get("SP_MARKETPLACE_ID", "A1VC38T7YXB528")
    product_asin = os.environ.get("PRODUCT_ASIN", "")
    manual_url = os.environ.get("MANUAL_URL", "")
    state_file = Path(os.environ.get("STATE_FILE", "sent_orders.json"))
    days_back = int(os.environ.get("DAYS_BACK", "365"))

    missing = []
    if not lwa_client_id:
        missing.append("SP_LWA_CLIENT_ID")
    if not lwa_client_secret:
        missing.append("SP_LWA_CLIENT_SECRET")
    if not lwa_refresh_token:
        missing.append("SP_LWA_REFRESH_TOKEN")
    if not seller_id:
        missing.append("SP_SELLER_ID")
    if not product_asin:
        missing.append("PRODUCT_ASIN")
    if not manual_url:
        missing.append("MANUAL_URL")

    if missing:
        raise ValueError(
            f"以下の環境変数が設定されていません: {', '.join(missing)}\n"
            ".env.example を参考に .env ファイルを作成してください。\n\n"
            "SP-API 認証情報の取得方法:\n"
            "  Seller Central → アプリと連携 → アプリの開発\n\n"
            "OneDrive 共有リンクの作成方法:\n"
            "  OneDrive → ファイルを右クリック → リンクのコピー\n"
            "  → 「リンクを知っているすべてのユーザー」を選択"
        )

    return Config(
        lwa_client_id=lwa_client_id,
        lwa_client_secret=lwa_client_secret,
        lwa_refresh_token=lwa_refresh_token,
        seller_id=seller_id,
        marketplace_id=marketplace_id,
        product_asin=product_asin,
        manual_url=manual_url,
        state_file=state_file,
        days_back=days_back,
    )
