"""Apple Store 領収書メールパーサー"""
import logging
import re
from datetime import date
from decimal import Decimal
from typing import List

from bs4 import BeautifulSoup

from .base import BaseParser, ParseError, Receipt, ReceiptItem

logger = logging.getLogger(__name__)


class AppleParser(BaseParser):
    """Apple Store の領収書メールを解析する"""

    @property
    def store_type(self) -> str:
        return "apple"

    @property
    def sender_domains(self) -> List[str]:
        return [
            "email.apple.com",
            "apple.com",
        ]

    def parse(self, uid: int, subject: str, html_body: str) -> Receipt:
        """Apple Store の領収書メールを解析して Receipt を返す"""
        soup = BeautifulSoup(html_body, "lxml")
        text = soup.get_text(separator="\n", strip=True)

        order_id = self._extract_order_id(text, soup)
        order_date = self._extract_order_date(text, soup)
        items = self._extract_items(soup, text)
        subtotal, tax_amount, shipping_cost, total = self._extract_amounts(text, soup)

        return Receipt(
            order_date=order_date,
            order_id=order_id,
            store_type=self.store_type,
            store_name="Apple Store",
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total=total,
            payment_method=self._extract_payment_method(text),
            raw_html=html_body,
            email_uid=uid,
        )

    def _extract_order_id(self, text: str, soup: BeautifulSoup) -> str:
        patterns = [
            r"注文番号[：:\s]*([A-Z0-9]+)",
            r"Order\s*(?:ID|Number|#)[：:\s#]*([A-Z0-9\-]+)",
            r"M\d{9,}",          # Apple の注文番号形式 (例: M123456789)
            r"W\d{9,}",          # Web 注文番号形式
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return (m.group(1) if m.lastindex else m.group(0)).strip()

        # Apple のレシートに含まれるドキュメント番号
        m = re.search(r"Document\s*No\.?\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if m:
            return m.group(1)

        raise ParseError("Apple: 注文番号を抽出できませんでした")

    def _extract_order_date(self, text: str, soup: BeautifulSoup) -> date:
        # 英語形式: "January 1, 2024"
        months_en = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        m = re.search(
            r"(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
            text, re.IGNORECASE,
        )
        if m:
            month = months_en[m.group(1).lower()]
            return date(int(m.group(3)), month, int(m.group(2)))

        # 日本語形式
        patterns = [
            r"(\d{4})[年/](\d{1,2})[月/](\d{1,2})",
            r"購入日[：:\s]*(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

        raise ParseError("Apple: 注文日を抽出できませんでした")

    def _extract_items(self, soup: BeautifulSoup, text: str) -> List[ReceiptItem]:
        items = []

        # Apple のレシートは商品ごとに行が分かれていることが多い
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            row_text = " ".join(c.get_text(strip=True) for c in cells)

            # ¥X,XXX 形式の金額を含む行
            price_match = re.search(r"¥\s*([\d,]+)", row_text)
            if price_match and len(row_text) > 5:
                name = cells[0].get_text(strip=True)[:80]
                # ヘッダー行などをスキップ
                if any(h in name for h in ["品目", "金額", "小計", "合計", "Item"]):
                    continue
                amount = self.to_decimal(price_match.group(1))
                items.append(ReceiptItem(
                    name=name,
                    quantity=1,
                    unit_price=amount,
                    amount=amount,
                ))

        # テーブルから取得できない場合はテキストから抽出
        if not items:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if re.search(r"¥[\d,]+", line) and len(line) > 10:
                    m = re.search(r"¥([\d,]+)", line)
                    if m:
                        name = re.sub(r"¥[\d,]+", "", line).strip()[:80]
                        if name and not any(h in name for h in ["小計", "合計", "消費税", "送料"]):
                            amount = self.to_decimal(m.group(1))
                            items.append(ReceiptItem(
                                name=name,
                                quantity=1,
                                unit_price=amount,
                                amount=amount,
                            ))

        return items

    def _extract_amounts(self, text: str, soup: BeautifulSoup) -> tuple:
        subtotal = self._find_amount(text, ["小計", "Subtotal"])
        tax_amount = self._find_amount(text, ["消費税", "Tax", "税"])
        shipping_cost = self._find_amount(text, ["送料", "Shipping"])
        total = self._find_amount(text, [
            "合計", "Total", "お支払い金額", "ご請求金額"
        ])

        if total == Decimal("0"):
            total = subtotal + tax_amount + shipping_cost

        return subtotal, tax_amount, shipping_cost, total

    def _find_amount(self, text: str, labels: List[str]) -> Decimal:
        for label in labels:
            pattern = rf"{label}[^\d¥]*¥?\s*([\d,]+)"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return self.to_decimal(m.group(1))
        return Decimal("0")

    def _extract_payment_method(self, text: str) -> str:
        patterns = [
            r"(?:お支払い|支払い?)方法[：:\s]*(.+)",
            r"(?:Payment\s*Method)[：:\s]*(.+)",
            r"(Apple\s*Pay|クレジットカード|Visa|Mastercard|AMEX|JCB)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:30]
        return "クレジットカード"
