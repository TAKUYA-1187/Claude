"""設定管理モジュール - 環境変数 / .env から設定を読み込む"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 不動産の朝レポートと同じ宛先
DEFAULT_ALERT_TO = "taku.ino.19811014@gmail.com"


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    return float(raw) if raw else default


@dataclass
class Config:
    # Keepa
    keepa_api_key: str
    domain_id: int = 5  # 5 = amazon.co.jp

    # 抽出条件
    min_drop_percent: float = 30.0   # 30日平均比の下落率(%)がこれ以上
    min_drop_yen: int = 1_000        # 下落額(円)がこれ以上
    min_sellers: int = 3             # 新品出品者数がこれ以上（独占販売を除外）
    min_price: int = 1_500           # 現在価格の下限（低単価品はノイズなので除外）
    max_price: int = 300_000         # 現在価格の上限
    max_sales_rank: int = 80_000     # 売れ筋ランキング上限（回転しない商品を除外）

    # メール (Gmail SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_to: list[str] = field(default_factory=lambda: [DEFAULT_ALERT_TO])

    # 動作
    state_file: Path = Path("data/alerted_asins.json")
    alert_ttl_hours: int = 72        # 同一ASINの再通知抑制時間
    max_alerts_per_run: int = 30     # 1回の実行で通知する最大件数
    product_batch_size: int = 20     # /product 一括取得の件数

    def can_send_email(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.alert_to)


def load_config() -> Config:
    keepa_api_key = os.environ.get("KEEPA_API_KEY", "").strip()
    if not keepa_api_key:
        raise ValueError(
            "KEEPA_API_KEY を設定してください（https://keepa.com/#!api で取得）。\n"
            ".env.example を参考に .env を作成するか、GitHub Secrets に登録してください。"
        )

    alert_to_raw = os.environ.get("ALERT_EMAIL_TO", DEFAULT_ALERT_TO)
    alert_to = [a.strip() for a in alert_to_raw.split(",") if a.strip()]

    return Config(
        keepa_api_key=keepa_api_key,
        domain_id=_int_env("KEEPA_DOMAIN_ID", 5),
        min_drop_percent=_float_env("MIN_DROP_PERCENT", 30.0),
        min_drop_yen=_int_env("MIN_DROP_YEN", 1_000),
        min_sellers=_int_env("MIN_SELLERS", 3),
        min_price=_int_env("MIN_PRICE", 1_500),
        max_price=_int_env("MAX_PRICE", 300_000),
        max_sales_rank=_int_env("MAX_SALES_RANK", 80_000),
        smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=_int_env("SMTP_PORT", 587),
        smtp_user=os.environ.get("SMTP_USER", "").strip(),
        smtp_password=os.environ.get("SMTP_PASSWORD", "").strip(),
        alert_to=alert_to,
        alert_ttl_hours=_int_env("ALERT_TTL_HOURS", 72),
        max_alerts_per_run=_int_env("MAX_ALERTS_PER_RUN", 30),
    )
