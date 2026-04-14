"""楽天市場 注文確認メールパーサー"""
import logging
import re
from datetime import date
from decimal import Decimal
from typing import List

from bs4 import BeautifulSoup

from .base import BaseParser, ParseError, Receipt, ReceiptItem

logger = logging.getLogger(__name__)


class RakutenParser(BaseParser):
    """楽天市場の注文確認メールを解析する"""

    @property
    def store_type(self) -> str:
        return "rakuten"

    @property
    def sender_domains(self) -> List[str]:
        return [
            "rakuten.co.jp",
            "mail.rakuten.co.jp",
        ]

    def parse(self, uid: int, subject: str, html_body: str) -> Receipt:
        """楽天市場の注文確認メールを解析して Receipt を返す"""
        soup = BeautifulSoup(html_body, "lxml")
        text = soup.get_text(separator="\n", strip=True)

        order_id = self._extract_order_id(text, soup)
        order_date = self._extract_order_date(text, soup)
        store_name = self._extract_store_name(text, soup)
        items = self._extract_items(soup, text)
        subtotal, tax_amount, shipping_cost, total = self._extract_amounts(text, soup)
        payment_method = self._extract_payment_method(text)

        return Receipt(
            order_date=order_date,
            order_id=order_id,
            store_type=self.store_type,
            store_name=store_name,
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total=total,
            payment_method=payment_method,
            raw_html=html_body,
            email_uid=uid,
        )

    def _extract_order_id(self, text: str, soup: BeautifulSoup) -> str:
        patterns = [
            r"注文番号[：:\s]*(\d{3}-\d{7}-\d{7})",   # 楽天典型形式
            r"注文番号[：:\s]*([A-Za-z0-9\-]+)",
            r"ご注文番号[：:\s]*([A-Za-z0-9\-]+)",
            r"orderNumber[=:]([A-Za-z0-9\-]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        # URL から抽出
        for a in soup.find_all("a", href=True):
            m = re.search(r"orderNumber=([A-Za-z0-9\-]+)", a["href"])
            if m:
                return m.group(1)

        raise ParseError("楽天: 注文番号を抽出できませんでした")

    def _extract_order_date(self, text: str, soup: BeautifulSoup) -> date:
        patterns = [
            r"注文日[：:\s]*(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})",
            r"ご注文日時[：:\s]*(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})",
            r"(\d{4})[年/](\d{1,2})[月/](\d{1,2})日",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

        raise ParseError("楽天: 注文日を抽出できませんでした")

    def _extract_store_name(self, text: str, soup: BeautifulSoup) -> str:
        patterns = [
            r"店舗名[：:\s]*(.+)",
            r"ショップ名[：:\s]*(.+)",
            r"販売店舗[：:\s]*(.+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1).strip()[:50]
        return "楽天市場"

    def _extract_items(self, soup: BeautifulSoup, text: str) -> List[ReceiptItem]:
        items = []
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            row_text = " ".join(c.get_text(strip=True) for c in cells)
            price_match = re.search(r"([\d,]+)円\s*[×x×]\s*(\d+)", row_text)
            if price_match:
                unit_price = self.to_decimal(price_match.group(1))
                quantity = int(price_match.group(2))
                name = cells[0].get_text(strip=True)[:80]
                items.append(ReceiptItem(
                    name=name,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=unit_price * quantity,
                ))

        if not items:
            # テキストから商品名を抽出（フォールバック）
            m = re.search(r"【商品名】(.+?)(?:\n|【)", text, re.DOTALL)
            if m:
                items.append(ReceiptItem(
                    name=m.group(1).strip()[:80],
                    quantity=1,
                    unit_price=Decimal("0"),
                    amount=Decimal("0"),
                ))

        return items

    def _extract_amounts(self, text: str, soup: BeautifulSoup) -> tuple:
        subtotal = self._find_amount(text, ["商品合計", "小計", "商品代金"])
        tax_amount = self._find_amount(text, ["消費税", "税額", "内消費税"])
        shipping_cost = self._find_amount(text, ["送料", "配送料", "送料合計"])
        total = self._find_amount(text, [
            "お支払い合計", "合計金額", "ご請求金額", "総合計", "お支払総額"
        ])

        if total == Decimal("0"):
            total = subtotal + tax_amount + shipping_cost

        return subtotal, tax_amount, shipping_cost, total

    def _find_amount(self, text: str, labels: List[str]) -> Decimal:
        for label in labels:
            pattern = rf"{label}[^\d]*?([\d,]+)円?"
            m = re.search(pattern, text)
            if m:
                return self.to_decimal(m.group(1))
        return Decimal("0")

    def _extract_payment_method(self, text: str) -> str:
        patterns = [
            r"お支払い方法[：:\s]*(.+)",
            r"決済方法[：:\s]*(.+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1).strip()[:30]
        return "クレジットカード"
