"""Amazon PA-API 5.0 クライアント。

Docs: https://webservices.amazon.com/paapi5/documentation/
- EANs 検索で JAN から ASIN/価格を取得できる
- 1秒1リクエスト、初期は1日8640req 上限
- アソシエイト資格 (売上実績) が必要
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)


class AmazonClient:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        partner_tag: str,
        host: str = "webservices.amazon.co.jp",
        region: str = "us-west-2",
    ):
        if not (access_key and secret_key and partner_tag):
            raise ValueError("Amazon credentials are required")
        # 遅延インポート: 依存パッケージ未導入でも他のクライアントは動作可能に
        from amazon_paapi import AmazonApi  # type: ignore

        self.api = AmazonApi(access_key, secret_key, partner_tag, "JP", throttling=1.0)
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < 1.05:
            time.sleep(1.05 - elapsed)
        self._last_call = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
    def min_price_by_jan(self, jan: str) -> Optional[int]:
        self._throttle()
        try:
            result = self.api.search_items(keywords=jan, search_index="All", item_count=3)
        except Exception as e:
            log.warning("Amazon search failed for %s: %s", jan, e)
            return None

        items = getattr(result, "items", None) or []
        prices: list[int] = []
        for it in items:
            try:
                listing = it.offers.listings[0]
                amount = listing.price.amount
                if amount:
                    prices.append(int(amount))
            except (AttributeError, IndexError, TypeError):
                continue
        return min(prices) if prices else None
