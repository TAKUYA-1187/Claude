"""Keepa API クライアント。

Docs: https://keepa.com/#!discuss/t/request-deals/412
      https://keepa.com/#!discuss/t/request-products/110

- Deal API で「直近で価格が大きく下がった商品」を横断検索する
  （Amazon 全商品の価格履歴は Keepa が常時トラッキングしている）
- Product API で候補 ASIN の統計（現在価格 / 30日平均 / 出品者数）を検証する
- 料金はトークン制。無料枠は無く、API プラン（月額）の契約が必要
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

API_BASE = "https://api.keepa.com"

# Keepa 価格タイプのインデックス
AMAZON = 0        # Amazon 本体の価格
NEW = 1           # 新品最安値
SALES_RANK = 3    # 売れ筋ランキング
COUNT_NEW = 11    # 新品出品者数


class KeepaError(RuntimeError):
    pass


class RetryableKeepaError(KeepaError):
    pass


class KeepaClient:
    def __init__(self, api_key: str, domain_id: int = 5):
        self.api_key = api_key
        self.domain_id = domain_id
        self.tokens_left: Optional[int] = None

    @retry(
        retry=retry_if_exception_type(RetryableKeepaError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(min=2, max=30),
    )
    def _request(self, path: str, params: dict[str, Any]) -> dict:
        params = {"key": self.api_key, **params}
        resp = requests.get(f"{API_BASE}/{path}", params=params, timeout=60)
        if resp.status_code == 429:
            raise RetryableKeepaError("Keepa token quota exhausted (429)")
        if resp.status_code >= 500:
            raise RetryableKeepaError(f"Keepa server error {resp.status_code}")
        if resp.status_code != 200:
            raise KeepaError(f"Keepa API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        self.tokens_left = data.get("tokensLeft")
        return data

    def fetch_deals(
        self,
        min_drop_percent: float,
        price_range: tuple[int, int],
        max_sales_rank: int,
        page: int = 0,
    ) -> list[dict]:
        """直近24時間で新品価格が大幅下落した商品を取得する。

        価格・下落率での一次フィルタは Deal API 側で行い、
        出品者数など細かい条件は fetch_products の結果で二次フィルタする。
        """
        selection = {
            "page": page,
            "domainId": self.domain_id,
            "priceTypes": [NEW],
            "dateRange": 0,  # 0 = 直近1日 (刈り取りは鮮度が命)
            "deltaPercentRange": [int(min_drop_percent), 100],
            "currentRange": [price_range[0], price_range[1]],
            "salesRankRange": [0, max_sales_rank],
            "isRangeEnabled": True,
            "isFilterEnabled": False,
            "filterErotic": True,
            "sortType": 4,  # 下落率順
        }
        data = self._request("deal", {"selection": json.dumps(selection)})
        deals = (data.get("deals") or {}).get("dr") or []
        log.info("Keepa deals: %d件 (page=%d, tokensLeft=%s)", len(deals), page, self.tokens_left)
        return deals

    def fetch_products(self, asins: list[str], stats_days: int = 30) -> list[dict]:
        """ASIN リストの商品統計を取得する（現在値・平均値・出品者数）。"""
        if not asins:
            return []
        data = self._request(
            "product",
            {
                "domain": self.domain_id,
                "asin": ",".join(asins),
                "stats": stats_days,
                "history": 0,
            },
        )
        return data.get("products") or []


def stat_value(product: dict, stat_name: str, price_type: int) -> Optional[int]:
    """product['stats'] から値を取り出す。-1 / None は「データなし」として None を返す。"""
    stats = product.get("stats") or {}
    arr = stats.get(stat_name) or []
    if price_type >= len(arr):
        return None
    value = arr[price_type]
    if value is None or value < 0:
        return None
    return value
