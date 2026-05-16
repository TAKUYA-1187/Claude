"""楽天市場 商品検索API v2 クライアント。

Docs: https://webservice.rakuten.co.jp/documentation/ichiba-item-search
1秒1リクエスト上限・30日10万req等の制限あり。
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

ENDPOINT = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

log = logging.getLogger(__name__)


class RakutenClient:
    def __init__(self, app_id: str, affiliate_id: str | None = None):
        if not app_id:
            raise ValueError("RAKUTEN_APP_ID is required")
        self.app_id = app_id
        self.affiliate_id = affiliate_id
        self._last_call = 0.0
        self._lock = threading.Lock()

    def _throttle(self):
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < 1.05:
                time.sleep(1.05 - elapsed)
            self._last_call = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
    def _get(self, params: dict) -> dict:
        self._throttle()
        r = requests.get(ENDPOINT, params=params, timeout=15)
        if r.status_code == 429:
            log.warning("Rakuten rate limited, retrying")
            raise requests.HTTPError(response=r)
        r.raise_for_status()
        return r.json()

    def min_price_by_jan(self, jan: str) -> Optional[int]:
        """JANコードで検索し、最安価格を返す。"""
        params = {
            "applicationId": self.app_id,
            "keyword": jan,
            "sort": "+itemPrice",
            "hits": 5,
            "format": "json",
            "formatVersion": 2,
        }
        if self.affiliate_id:
            params["affiliateId"] = self.affiliate_id
        try:
            data = self._get(params)
        except Exception as e:
            log.warning("Rakuten search failed for %s: %s", jan, e)
            return None

        items = data.get("Items", [])
        prices = [item.get("itemPrice") for item in items if item.get("itemPrice")]
        return min(prices) if prices else None
