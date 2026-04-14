"""領収書データモデルとパーサー基底クラス"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List


class ParseError(Exception):
    """メールの解析に失敗した場合に送出される例外"""
    pass


@dataclass
class ReceiptItem:
    """購入商品の明細1行"""
    name: str
    quantity: int
    unit_price: Decimal
    amount: Decimal


@dataclass
class Receipt:
    """領収書データ"""
    order_date: date
    order_id: str
    store_type: str          # "yahoo" | "rakuten" | "apple"
    store_name: str
    items: List[ReceiptItem] = field(default_factory=list)
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    shipping_cost: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    payment_method: str = ""
    raw_html: str = ""
    email_uid: int = 0

    @property
    def pdf_filename(self) -> str:
        """PDF ファイル名を生成する"""
        date_str = self.order_date.strftime("%Y%m%d")
        safe_order_id = re.sub(r"[^\w\-]", "_", self.order_id)
        total_int = int(self.total)
        return f"{date_str}_{self.store_type}_{safe_order_id}_{total_int}円.pdf"

    @property
    def pdf_subdir(self) -> str:
        """PDF 保存先サブディレクトリ (YYYY/MM)"""
        return self.order_date.strftime("%Y/%m")


class BaseParser(ABC):
    """各ショップのメールパーサー基底クラス"""

    @property
    @abstractmethod
    def store_type(self) -> str:
        """ショップ種別 ("yahoo" / "rakuten" / "apple")"""
        ...

    @property
    @abstractmethod
    def sender_domains(self) -> List[str]:
        """このパーサーが担当する送信元ドメインのリスト"""
        ...

    @abstractmethod
    def parse(self, uid: int, subject: str, html_body: str) -> Receipt:
        """
        メール HTML を解析して Receipt を返す。
        解析に失敗した場合は ParseError を送出する。
        """
        ...

    def can_handle(self, from_addr: str) -> bool:
        """送信元アドレスがこのパーサーで処理可能かどうかを返す"""
        from_lower = from_addr.lower()
        return any(domain in from_lower for domain in self.sender_domains)

    @staticmethod
    def to_decimal(text: str) -> Decimal:
        """金額文字列 (例: "¥1,234" "1234円") を Decimal に変換する"""
        cleaned = re.sub(r"[^\d]", "", text)
        if not cleaned:
            return Decimal("0")
        return Decimal(cleaned)
