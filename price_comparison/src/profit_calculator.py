"""せどりの利益を計算する。

ルートA (買取店ルート):
  ① ECサイト (Amazon / 楽天 / Yahoo) で最安値で仕入れる
  ② 買取店 (買取スキャナーが参照している店舗) に送って買い取ってもらう
  利益 = 買取価格 − 仕入れ価格 − 送料 − その他コスト

ルートB (Amazon販売ルート):
  ① 楽天 / Yahoo で最安値で仕入れる (Amazon仕入れ→Amazon販売は除外)
  ② Amazon で現在の最安値相当で販売する (FBA想定)
  利益 = Amazon手取り (手数料控除後) − 仕入れ価格 − FBA納品送料
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .amazon_fee_simulator import estimate_fees
from .config import Config


@dataclass
class PriceRow:
    jan: str
    name: str
    buy_price: float  # 買取店が支払う金額
    buy_shop: str
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
    buy_shop: str
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
            "buy_shop": self.buy_shop,
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
        buy_shop=row.buy_shop,
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


@dataclass
class AmazonProfitRow:
    """ルートB: 楽天/Yahoo で仕入れて Amazon で販売する場合の利益。"""

    jan: str
    name: str
    category: str
    amazon_sell_price: int  # Amazonでの想定販売価格 (現在の最安値)
    purchase_price: int  # 仕入れ価格 (楽天/Yahooの最安値)
    purchase_source: str  # rakuten / yahoo
    rakuten_price: Optional[int]
    yahoo_price: Optional[int]
    referral_fee: int  # 販売手数料
    closing_fee: int  # カテゴリー成約料
    fba_fee: int  # FBA配送代行料 (概算)
    fee_tax: int  # 手数料への消費税
    inbound_cost: int  # FBA納品送料 (概算)
    net_proceeds: int  # Amazonからの手取り
    profit: float
    profit_rate: float
    buyback_price: Optional[int] = None  # 参考: 買取店の買取価格
    buyback_shop: str = ""

    def as_dict(self) -> dict:
        return {
            "jan": self.jan,
            "name": self.name,
            "category": self.category,
            "amazon_sell_price": self.amazon_sell_price,
            "purchase_price": self.purchase_price,
            "purchase_source": self.purchase_source,
            "rakuten_price": self.rakuten_price,
            "yahoo_price": self.yahoo_price,
            "referral_fee": self.referral_fee,
            "closing_fee": self.closing_fee,
            "fba_fee": self.fba_fee,
            "fee_tax": self.fee_tax,
            "inbound_cost": self.inbound_cost,
            "net_proceeds": self.net_proceeds,
            "profit": int(round(self.profit)),
            "profit_rate": round(self.profit_rate, 4),
            "buyback_price": self.buyback_price,
            "buyback_shop": self.buyback_shop,
        }


def compute_amazon(
    jan: str,
    name: str,
    category: str,
    amazon_price: Optional[int],
    rakuten_price: Optional[int],
    yahoo_price: Optional[int],
    cfg: Config,
    buyback_price: Optional[int] = None,
    buyback_shop: str = "",
) -> Optional[AmazonProfitRow]:
    """Amazon販売ルートの利益を計算する。価格が揃わない場合は None。"""
    if not amazon_price:
        return None
    purchase_candidates = [
        (p, src)
        for p, src in ((rakuten_price, "rakuten"), (yahoo_price, "yahoo"))
        if p
    ]
    if not purchase_candidates:
        return None
    purchase_price, purchase_source = min(purchase_candidates)

    fees = estimate_fees(
        sell_price=amazon_price,
        category=category,
        default_referral_rate=cfg.amazon_fee_rate,
        fba_fee=cfg.amazon_fba_fee,
        fee_tax_rate=cfg.amazon_fee_tax_rate,
    )
    inbound = int(round(cfg.amazon_inbound_cost))
    profit = fees.net_proceeds - purchase_price - inbound
    profit_rate = profit / purchase_price if purchase_price else 0.0

    return AmazonProfitRow(
        jan=jan,
        name=name,
        category=category,
        amazon_sell_price=amazon_price,
        purchase_price=purchase_price,
        purchase_source=purchase_source,
        rakuten_price=rakuten_price,
        yahoo_price=yahoo_price,
        referral_fee=fees.referral_fee,
        closing_fee=fees.closing_fee,
        fba_fee=fees.fba_fee,
        fee_tax=fees.fee_tax,
        inbound_cost=inbound,
        net_proceeds=fees.net_proceeds,
        profit=profit,
        profit_rate=profit_rate,
        buyback_price=int(buyback_price) if buyback_price else None,
        buyback_shop=buyback_shop,
    )


def is_amazon_profitable(r: AmazonProfitRow, cfg: Config) -> bool:
    return r.profit >= cfg.min_profit and r.profit_rate >= cfg.min_profit_rate
