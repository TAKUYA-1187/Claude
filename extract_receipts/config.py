"""設定管理モジュール - .env ファイルから設定を読み込む"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    credentials_file: str
    receipt_output_dir: Path
    days_back: int


def load_config() -> Config:
    credentials_file = os.environ.get("CREDENTIALS_FILE", "credentials.json")
    receipt_output_dir = Path(os.environ.get("RECEIPT_OUTPUT_DIR", "receipts"))
    days_back = int(os.environ.get("DAYS_BACK", "30"))

    return Config(
        credentials_file=credentials_file,
        receipt_output_dir=receipt_output_dir,
        days_back=days_back,
    )
