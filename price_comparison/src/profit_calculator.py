"""買取せどりの利益を計算する。

前提フロー:
  ① ECサイト (Amazon / 楽天 / Yahoo) で最安値で仕入れる
  ② 買取店 (買取スキャナーが参照している店舗) に送って買い取ってもらう
  利益 = 買取価格 − 仕入れ価格 − 送料 − その他コスト
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import Config


@dataclass
class PriceRow:
    jan: str
    name: str
    buy_price: float  # 買取店が支払う金額
    amazon_price: Optional[int]
    rakuten_price: Optional[int]
    yahoo_price: Optional[int]

    @property
    def min_sell_price(self) -> Optional[int]:
        prices = [p for p in (self.amazon_price, self.rakuten_price, self.yahoo_price) if p]
        return min(prices) if prices else None

    @property
    def min_sell_source(self) -> Optional[str]:
        price = self.min_sell_price
        if price is None:
            return None
        for src, val in (
            ("amazon", self.amazon_price),
            ("rakuten", self.rakuten_price),
            ("yahoo", self.yahoo_price),
        ):
            if val == price:
                return src
        return None


@dataclass
class ProfitRow:
    jan: str
    name: str
    buy_price: float
    purchase_price: int  # ECでの仕入れ価格
    purchase_source: str
    amazon_price: Optional[int]
    rakuten_price: Optional[int]
    yahoo_price: Optional[int]
    shipping: float
    profit: float
    profit_rate: float

    def as_dict(self) -> dict:
        return {
            "jan": self.jan,
            "name": self.name,
            "buy_price": int(self.buy_price),
            "purchase_price": self.purchase_price,
            "purchase_source": self.purchase_source,
            "amazon_price": self.amazon_price,
            "rakuten_price": self.rakuten_price,
            "yahoo_price": self.yahoo_price,
            "shipping": int(self.shipping),
            "profit": int(round(self.profit)),
            "profit_rate": round(self.profit_rate, 4),
        }


def compute(row: PriceRow, cfg: Config) -> Optional[ProfitRow]:
    sell = row.min_sell_price
    source = row.min_sell_source
    if sell is None or source is None:
        return None

    shipping = cfg.shipping_cost
    profit = row.buy_price - sell - shipping
    profit_rate = profit / sell if sell else 0.0

    return ProfitRow(
        jan=row.jan,
        name=row.name,
        buy_price=row.buy_price,
        purchase_price=sell,
        purchase_source=source,
        amazon_price=row.amazon_price,
        rakuten_price=row.rakuten_price,
        yahoo_price=row.yahoo_price,
        shipping=shipping,
        profit=profit,
        profit_rate=profit_rate,
    )


def is_profitable(r: ProfitRow, cfg: Config) -> bool:
    return r.profit >= cfg.min_profit and r.profit_rate >= cfg.min_profit_rate
