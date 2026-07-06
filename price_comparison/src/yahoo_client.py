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


# 連続失敗がこの回数に達したらクライアントを無効化し、残りのJANを高速スキップする
CIRCUIT_BREAKER_THRESHOLD = 10


class YahooClient:
    def __init__(self, app_id: str):
        if not app_id:
            raise ValueError("YAHOO_APP_ID is required")
        self.app_id = app_id
        self._last_call = 0.0
        self._consecutive_failures = 0
        self.dead = False

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
        if not r.ok:
            log.warning("Yahoo API HTTP %d: %s", r.status_code, r.text[:200])
        r.raise_for_status()
        return r.json()

    def min_price_by_jan(self, jan: str) -> Optional[int]:
        if self.dead:
            return None
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
            self._consecutive_failures += 1
            if self._consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD:
                self.dead = True
                log.error(
                    "Yahoo API が %d 回連続で失敗したため以降スキップします。"
                    "YAHOO_APP_ID が有効か確認してください。",
                    self._consecutive_failures,
                )
            return None

        self._consecutive_failures = 0
        hits = data.get("hits", []) or []
        prices = [h.get("price") for h in hits if h.get("price")]
        return min(prices) if prices else None
