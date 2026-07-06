import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def _parse_shops() -> list[str]:
    raw = os.getenv("ENABLED_SHOPS", "買取商店,ウィキ")
    return [s.strip() for s in raw.split(",") if s.strip()]


DEFAULT_COLLECT_KEYWORDS = (
    "Nintendo Switch,プレイステーション5,ポケモンカード,ワイヤレスイヤホン,"
    "美容家電,炊飯器,掃除機,ゲームソフト,フィギュア,レゴ"
)


def _parse_csv_env(name: str, default: str = "") -> list[str]:
    # 空文字で設定されている場合もデフォルトにフォールバックする
    raw = os.getenv(name) or default
    return [s.strip() for s in raw.split(",") if s.strip()]


@dataclass(frozen=True)
class Config:
    amazon_access_key: str = os.getenv("AMAZON_ACCESS_KEY", "")
    amazon_secret_key: str = os.getenv("AMAZON_SECRET_KEY", "")
    amazon_partner_tag: str = os.getenv("AMAZON_PARTNER_TAG", "")
    amazon_host: str = os.getenv("AMAZON_HOST", "webservices.amazon.co.jp")
    amazon_region: str = os.getenv("AMAZON_REGION", "us-west-2")

    rakuten_app_id: str = os.getenv("RAKUTEN_APP_ID", "")
    rakuten_affiliate_id: str = os.getenv("RAKUTEN_AFFILIATE_ID", "")

    yahoo_app_id: str = os.getenv("YAHOO_APP_ID", "")

    onedrive_share_url: str = os.getenv("ONEDRIVE_SHARE_URL", "")

    amazon_fee_rate: float = float(os.getenv("AMAZON_REFERRAL_FEE_RATE", "0.10"))
    amazon_fba_fee: float = float(os.getenv("AMAZON_FBA_FEE", "500"))
    amazon_fee_tax_rate: float = float(os.getenv("AMAZON_FEE_TAX_RATE", "0.10"))
    amazon_inbound_cost: float = float(os.getenv("AMAZON_INBOUND_COST", "200"))
    rakuten_fee_rate: float = float(os.getenv("RAKUTEN_FEE_RATE", "0.10"))
    yahoo_fee_rate: float = float(os.getenv("YAHOO_FEE_RATE", "0.08"))
    shipping_cost: float = float(os.getenv("SHIPPING_COST", "600"))

    min_profit: float = float(os.getenv("MIN_PROFIT", "500"))
    min_profit_rate: float = float(os.getenv("MIN_PROFIT_RATE", "0.15"))

    input_dir: Path = ROOT / os.getenv("INPUT_CSV_DIR", "data/input")
    output_dir: Path = ROOT / os.getenv("OUTPUT_DIR", "data/output")
    collected_dir: Path = ROOT / os.getenv("COLLECTED_DIR", "data/collected")

    enabled_shops: list[str] = field(default_factory=_parse_shops)

    # === JAN 収集 (jan_collector) ===
    collect_keywords: list[str] = field(
        default_factory=lambda: _parse_csv_env("COLLECT_KEYWORDS", DEFAULT_COLLECT_KEYWORDS)
    )
    collect_yahoo_genres: list[str] = field(
        default_factory=lambda: _parse_csv_env("COLLECT_YAHOO_GENRES")
    )
    collect_pages: int = int(os.getenv("COLLECT_PAGES", "3"))


config = Config()
