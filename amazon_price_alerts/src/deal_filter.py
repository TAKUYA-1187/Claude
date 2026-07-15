"""刈り取り条件によるフィルタリング。

通知対象:
- 新品価格が 30 日平均から MIN_DROP_PERCENT % 以上 かつ MIN_DROP_YEN 円以上下落
- 新品出品者数が MIN_SELLERS 名以上（独占販売・メーカー直販のみの商品を除外）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .config import Config
from .keepa_client import AMAZON, COUNT_NEW, NEW, SALES_RANK, stat_value

log = logging.getLogger(__name__)


@dataclass
class Alert:
    asin: str
    title: str
    current_price: int      # 現在の新品最安値（円）
    avg30_price: int        # 30日平均の新品価格（円）
    drop_yen: int
    drop_percent: float
    seller_count: int       # 新品出品者数
    sales_rank: Optional[int]
    amazon_price: Optional[int]  # Amazon本体の価格（Noneなら本体在庫なし）

    @property
    def amazon_url(self) -> str:
        return f"https://www.amazon.co.jp/dp/{self.asin}"

    @property
    def keepa_url(self) -> str:
        return f"https://keepa.com/#!product/5-{self.asin}"


def evaluate_product(product: dict, cfg: Config) -> Optional[Alert]:
    """Keepa の product 統計を検証し、条件を満たせば Alert を返す。"""
    asin = product.get("asin", "")
    title = product.get("title") or asin

    current = stat_value(product, "current", NEW)
    avg30 = stat_value(product, "avg30", NEW)
    seller_count = stat_value(product, "current", COUNT_NEW)
    sales_rank = stat_value(product, "current", SALES_RANK)
    amazon_price = stat_value(product, "current", AMAZON)

    if current is None or avg30 is None or avg30 <= 0:
        return None

    # 独占販売の除外: 新品出品者（せどらー含む）が3名以上いる商品のみ
    if seller_count is None or seller_count < cfg.min_sellers:
        return None

    if not (cfg.min_price <= current <= cfg.max_price):
        return None

    if sales_rank is not None and sales_rank > cfg.max_sales_rank:
        return None

    drop_yen = avg30 - current
    drop_percent = drop_yen / avg30 * 100

    if drop_yen < cfg.min_drop_yen or drop_percent < cfg.min_drop_percent:
        return None

    return Alert(
        asin=asin,
        title=title,
        current_price=current,
        avg30_price=avg30,
        drop_yen=drop_yen,
        drop_percent=drop_percent,
        seller_count=seller_count,
        sales_rank=sales_rank,
        amazon_price=amazon_price,
    )


def filter_products(products: list[dict], cfg: Config) -> list[Alert]:
    alerts = []
    for product in products:
        alert = evaluate_product(product, cfg)
        if alert:
            alerts.append(alert)
    alerts.sort(key=lambda a: a.drop_percent, reverse=True)
    log.info("条件合致: %d件 / 候補 %d件", len(alerts), len(products))
    return alerts
