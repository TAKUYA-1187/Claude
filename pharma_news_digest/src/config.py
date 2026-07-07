"""環境変数からの設定読み込み。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv 未導入でも動作させる
    pass

# 既定の配信先（担当者本人の 2 アドレス）
DEFAULT_RECIPIENTS = [
    "taku.ino.19811014@gmail.com",
    "takuya.inoue@novartis.com",
]


@dataclass
class Config:
    sender_email: str = ""
    sender_password: str = ""
    recipients: List[str] = field(default_factory=lambda: list(DEFAULT_RECIPIENTS))
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    ncbi_api_key: str = ""  # 任意。あれば PubMed のレート制限が緩和される
    # 収集ウィンドウ
    news_lookback_hours: int = 30  # 毎日実行のため直近 30 時間分のニュース
    paper_lookback_days: int = 14  # 論文は新着が少ないため 2 週間
    max_items_per_section: int = 12

    @property
    def email_configured(self) -> bool:
        return bool(self.sender_email and self.sender_password)


def _split(value: str, fallback: List[str]) -> List[str]:
    items = [v.strip() for v in value.replace("\n", ",").split(",") if v.strip()]
    return items or list(fallback)


def load_config() -> Config:
    cfg = Config()
    cfg.sender_email = os.getenv("SENDER_EMAIL", "").strip()
    cfg.sender_password = os.getenv("SENDER_APP_PASSWORD", "").strip()
    cfg.recipients = _split(os.getenv("RECIPIENTS", ""), DEFAULT_RECIPIENTS)
    cfg.smtp_host = os.getenv("SMTP_HOST", cfg.smtp_host).strip()
    cfg.smtp_port = int(os.getenv("SMTP_PORT", cfg.smtp_port))
    cfg.ncbi_api_key = os.getenv("NCBI_API_KEY", "").strip()
    cfg.news_lookback_hours = int(os.getenv("NEWS_LOOKBACK_HOURS", cfg.news_lookback_hours))
    cfg.paper_lookback_days = int(os.getenv("PAPER_LOOKBACK_DAYS", cfg.paper_lookback_days))
    cfg.max_items_per_section = int(
        os.getenv("MAX_ITEMS_PER_SECTION", cfg.max_items_per_section)
    )
    return cfg
