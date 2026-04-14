"""設定管理モジュール - .env ファイルから設定を読み込む"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str
    receipt_output_dir: Path
    days_back: int


def load_config() -> Config:
    imap_host = os.environ.get("IMAP_HOST", "imap.gmail.com")
    imap_port = int(os.environ.get("IMAP_PORT", "993"))
    imap_user = os.environ.get("IMAP_USER", "")
    imap_password = os.environ.get("IMAP_PASSWORD", "")
    receipt_output_dir = Path(os.environ.get("RECEIPT_OUTPUT_DIR", "receipts"))
    days_back = int(os.environ.get("DAYS_BACK", "30"))

    if not imap_user or not imap_password:
        raise ValueError(
            "IMAP_USER と IMAP_PASSWORD を .env に設定してください。\n"
            ".env.example を参考に .env ファイルを作成してください。"
        )

    return Config(
        imap_host=imap_host,
        imap_port=imap_port,
        imap_user=imap_user,
        imap_password=imap_password,
        receipt_output_dir=receipt_output_dir,
        days_back=days_back,
    )
