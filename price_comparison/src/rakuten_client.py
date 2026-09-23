"""楽天市場 商品検索API クライアント（2026年の新API基盤 openapi.rakuten.co.jp 対応）。

Docs: https://webservice.rakuten.co.jp/documentation/ichiba-item-search
旧基盤 app.rakuten.co.jp は 2026-05 に停止。新基盤では次の3点が必須:
  - 新形式のアプリID（UUID形式）と、アクセスキー（pk_ で始まる）
  - accessKey をクエリパラメータで送る
  - Referer / Origin ヘッダーに、アプリの「許可されたWebサイト」に登録したURLを入れる
短い間隔で連続照会すると 429 になるため、1.5秒間隔で呼ぶ。
"""
from __future__ import annotations

import logging
import time
from typing import Optional
from urllib.parse import urlsplit

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

OPENAPI_BASE = "https://openapi.rakuten.co.jp"
ENDPOINT = f"{OPENAPI_BASE}/ichibams/api/IchibaItem/Search/20260701"
MIN_INTERVAL_SEC = 1.5

log = logging.getLogger(__name__)


def credentials_problem(app_id: str, access_key: str) -> Optional[str]:
    """新API基盤で使えない認証情報なら、利用者向けの対処方法を返す。"""
    if not app_id:
        return None
    if app_id.strip().isdigit():
        return (
            "RAKUTEN_APP_ID が旧形式（数字のみ）です。楽天APIは2026年に新基盤へ移行し、旧IDは使えません。"
            "https://webservice.rakuten.co.jp/ でアプリを新規登録し、新しいアプリID（UUID形式）と"
            "アクセスキー（pk_で始まる）を GitHub Secrets の RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY に設定してください。"
        )
    if not access_key:
        return (
            "RAKUTEN_ACCESS_KEY が未設定です。楽天のアプリ管理画面に表示されるアクセスキー（pk_で始まる）を"
            " GitHub Secrets の RAKUTEN_ACCESS_KEY に設定してください。"
        )
    return None


def auth_params(app_id: str, access_key: str) -> dict:
    return {"applicationId": app_id, "accessKey": access_key}


def auth_headers(referer: str) -> dict:
    parts = urlsplit(referer)
    return {"Referer": referer, "Origin": f"{parts.scheme}://{parts.netloc}"}


# 連続失敗がこの回数に達したらクライアントを無効化し、残りのJANを高速スキップする
CIRCUIT_BREAKER_THRESHOLD = 10


class RakutenClient:
    def __init__(self, app_id: str, access_key: str, referer: str, affiliate_id: str | None = None):
        if not app_id:
            raise ValueError("RAKUTEN_APP_ID is required")
        self.app_id = app_id
        self.access_key = access_key
        self.referer = referer
        self.affiliate_id = affiliate_id
        self._last_call = 0.0
        self._consecutive_failures = 0
        self.dead = False

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < MIN_INTERVAL_SEC:
            time.sleep(MIN_INTERVAL_SEC - elapsed)
        self._last_call = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
    def _get(self, params: dict) -> dict:
        self._throttle()
        r = requests.get(
            ENDPOINT,
            params={**auth_params(self.app_id, self.access_key), **params},
            headers=auth_headers(self.referer),
            timeout=15,
        )
        if not r.ok:
            log.warning("Rakuten API HTTP %d: %s", r.status_code, r.text[:200])
        r.raise_for_status()
        return r.json()

    def min_price_by_jan(self, jan: str) -> Optional[int]:
        """JANコードで検索し、最安価格を返す。"""
        if self.dead:
            return None
        params = {
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
            self._consecutive_failures += 1
            if self._consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD:
                self.dead = True
                log.error(
                    "Rakuten API が %d 回連続で失敗したため以降スキップします。"
                    "RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY と、アプリの「許可されたWebサイト」に"
                    " RAKUTEN_REFERER のドメインが登録されているかを確認してください。",
                    self._consecutive_failures,
                )
            return None

        self._consecutive_failures = 0
        items = data.get("Items", [])
        prices = [item.get("itemPrice") for item in items if item.get("itemPrice")]
        return min(prices) if prices else None
