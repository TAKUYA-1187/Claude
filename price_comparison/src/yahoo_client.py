"""Yahoo!ショッピング 商品検索(v3) クライアント。

Docs: https://developer.yahoo.co.jp/webapi/shopping/v3/itemsearch.html
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

ENDPOINT = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"

log = logging.getLogger(__name__)


class YahooClient:
    def __init__(self, app_id: str):
        if not app_id:
            raise ValueError("YAHOO_APP_ID is required")
        self.app_id = app_id
        self._last_call = 0.0

    def _throttle(self):
        # 1req/sec 程度に抑制
        elapsed = time.time() - self._last_call
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
        self._last_call = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
    def _get(self, params: dict) -> dict:
        self._throttle()
        r = requests.get(ENDPOINT, params=params, timeout=15)
        if r.status_code == 429:
            raise requests.HTTPError(response=r)
        r.raise_for_status()
        return r.json()

    def min_price_by_jan(self, jan: str) -> Optional[int]:
        params = {
            "appid": self.app_id,
            "jan_code": jan,
            "sort": "+price",
            "results": 5,
            "in_stock": "true",
        }
        try:
            data = self._get(params)
        except Exception as e:
            log.warning("Yahoo search failed for %s: %s", jan, e)
            return None

        hits = data.get("hits", []) or []
        prices = [h.get("price") for h in hits if h.get("price")]
        return min(prices) if prices else None
