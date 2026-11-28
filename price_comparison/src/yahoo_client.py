"""Yahoo!ショッピング 商品検索(v3) クライアント。

Docs: https://developer.yahoo.co.jp/webapi/shopping/v3/itemsearch.html
"""
from __future__ import annotations

import logging
from typing import Optional

from .yahoo_budget import BudgetExhausted, RateLimited, YahooBudget

log = logging.getLogger(__name__)


class YahooClient:
    """JANで最安値を引く。利用量は YahooBudget で一元管理し、同じJANは1実行で1回だけ問い合わせる。"""

    def __init__(self, app_id: str, budget: YahooBudget | None = None):
        if not app_id:
            raise ValueError("YAHOO_APP_ID is required")
        self.app_id = app_id
        self.budget = budget or YahooBudget.shared()
        self._cache: dict[str, Optional[int]] = {}
        self.dead = False

    def min_price_by_jan(self, jan: str) -> Optional[int]:
        if jan in self._cache:            # 重複問い合わせの排除
            return self._cache[jan]
        if self.dead:
            return None
        params = {"appid": self.app_id, "jan_code": jan, "sort": "+price",
                  "results": 5, "in_stock": "true", "condition": "new"}
        try:
            data = self.budget.get(params)
        except (RateLimited, BudgetExhausted) as e:
            self.dead = True
            log.error("Yahoo検索を停止: %s", e)
            return None
        except Exception as e:
            log.warning("Yahoo search failed for %s: %s", jan, e)
            return None
        hits = [h for h in (data.get("hits") or []) if str(h.get("janCode") or "") == jan]
        prices = [h.get("price") for h in hits if h.get("price")]
        self._cache[jan] = min(prices) if prices else None
        return self._cache[jan]
