"""EC サイトから JAN コード付き商品を収集する。

「全商品のJAN」を網羅的に取得することは各社APIの仕様・利用規約上できないため、
売れ筋順のサンプリングで実用的な母集団を作る:

- Yahoo!ショッピング: itemSearch v3 が janCode を返す。キーワード or ジャンルIDで
  売れ筋順に COLLECT_PAGES ページずつ取得。
- 楽天: 楽天市場APIは JAN を返さないため、JAN/ISBN を返す楽天ブックス総合検索APIを
  キーワード検索で利用 (CD/DVD/ゲーム/本など)。
- Amazon: PA-API の SearchItems から EAN (=JAN) を取得 (認証情報がある場合のみ)。

収集結果は data/collected/collected_latest.csv に保存され、メインの利益判定
パイプラインの母集団にマージされる。
"""
from __future__ import annotations

import csv
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

YAHOO_ENDPOINT = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
RAKUTEN_BOOKS_ENDPOINT = (
    "https://app.rakuten.co.jp/services/api/BooksTotal/Search/20170404"
)


@dataclass
class CollectedItem:
    jan: str
    name: str
    price: Optional[int]  # 収集時に見えた販売価格 (参考値)
    source: str  # yahoo / rakuten_books / amazon
    category: str = ""


def _valid_jan(code: str) -> bool:
    return code.isdigit() and len(code) in (8, 12, 13)


class YahooJanCollector:
    def __init__(self, app_id: str):
        self.app_id = app_id
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
        self._last_call = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
    def _get(self, params: dict) -> dict:
        self._throttle()
        r = requests.get(YAHOO_ENDPOINT, params=params, timeout=15)
        if r.status_code == 429:
            raise requests.HTTPError(response=r)
        r.raise_for_status()
        return r.json()

    def collect(
        self,
        keywords: list[str],
        genre_ids: list[str],
        pages: int,
        per_page: int = 50,
    ) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        targets: list[dict] = [{"query": kw} for kw in keywords]
        targets += [{"genre_category_id": g} for g in genre_ids]
        for target in targets:
            label = next(iter(target.values()))
            for page in range(pages):
                params = {
                    "appid": self.app_id,
                    "results": per_page,
                    "start": page * per_page + 1,
                    "sort": "-sold",  # 売れ筋順
                    "in_stock": "true",
                    **target,
                }
                try:
                    data = self._get(params)
                except Exception as e:
                    log.warning("Yahoo collect failed (%s p%d): %s", label, page + 1, e)
                    break
                hits = data.get("hits", []) or []
                if not hits:
                    break
                for h in hits:
                    jan = str(h.get("janCode") or "").strip()
                    if not _valid_jan(jan):
                        continue
                    genre = ""
                    gc = h.get("genreCategory") or {}
                    if isinstance(gc, dict):
                        genre = str(gc.get("name") or "")
                    items.append(
                        CollectedItem(
                            jan=jan,
                            name=str(h.get("name") or ""),
                            price=h.get("price") or None,
                            source="yahoo",
                            category=genre,
                        )
                    )
        log.info("Yahoo collector: %d items with JAN", len(items))
        return items


class RakutenBooksCollector:
    """楽天ブックス総合検索API。CD/DVD/ゲーム等は jan、本は isbn (=JAN) を返す。"""

    def __init__(self, app_id: str):
        self.app_id = app_id
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < 1.05:
            time.sleep(1.05 - elapsed)
        self._last_call = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
    def _get(self, params: dict) -> dict:
        self._throttle()
        r = requests.get(RAKUTEN_BOOKS_ENDPOINT, params=params, timeout=15)
        if r.status_code == 429:
            raise requests.HTTPError(response=r)
        r.raise_for_status()
        return r.json()

    def collect(self, keywords: list[str], pages: int) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        for kw in keywords:
            for page in range(1, pages + 1):
                params = {
                    "applicationId": self.app_id,
                    "keyword": kw,
                    "hits": 30,
                    "page": page,
                    "sort": "sales",
                    "format": "json",
                    "formatVersion": 2,
                    "availability": 1,
                }
                try:
                    data = self._get(params)
                except Exception as e:
                    log.warning("Rakuten Books collect failed (%s p%d): %s", kw, page, e)
                    break
                hits = data.get("Items", []) or []
                if not hits:
                    break
                for h in hits:
                    jan = str(h.get("jan") or h.get("isbn") or "").strip()
                    if not _valid_jan(jan):
                        continue
                    items.append(
                        CollectedItem(
                            jan=jan,
                            name=str(h.get("title") or ""),
                            price=h.get("itemPrice") or None,
                            source="rakuten_books",
                            category=str(h.get("booksGenreId") or ""),
                        )
                    )
        log.info("Rakuten Books collector: %d items with JAN", len(items))
        return items


class AmazonJanCollector:
    """PA-API SearchItems の ExternalIds (EAN) から JAN を取得する。"""

    def __init__(self, amazon_client):
        self.client = amazon_client  # AmazonClient (api 属性を利用)

    def collect(self, keywords: list[str], pages: int) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        for kw in keywords:
            for page in range(1, min(pages, 10) + 1):  # PA-API は item_page 最大10
                try:
                    result = self.client.api.search_items(
                        keywords=kw, search_index="All", item_count=10, item_page=page
                    )
                except Exception as e:
                    log.warning("Amazon collect failed (%s p%d): %s", kw, page, e)
                    break
                found = getattr(result, "items", None) or []
                if not found:
                    break
                for it in found:
                    jan = ""
                    try:
                        eans = it.item_info.external_ids.ea_ns.display_values
                        jan = str(eans[0]).strip() if eans else ""
                    except (AttributeError, IndexError, TypeError):
                        pass
                    if not _valid_jan(jan):
                        continue
                    price = None
                    try:
                        price = int(it.offers.listings[0].price.amount)
                    except (AttributeError, IndexError, TypeError):
                        pass
                    name = ""
                    try:
                        name = str(it.item_info.title.display_value)
                    except (AttributeError, TypeError):
                        pass
                    items.append(
                        CollectedItem(jan=jan, name=name, price=price, source="amazon")
                    )
        log.info("Amazon collector: %d items with JAN", len(items))
        return items


def collect_all(
    keywords: list[str],
    yahoo_genres: list[str],
    pages: int,
    yahoo_app_id: str = "",
    rakuten_app_id: str = "",
    amazon_client=None,
) -> dict[str, CollectedItem]:
    """設定済みの全ソースから収集し、JANでユニーク化して返す。"""
    merged: dict[str, CollectedItem] = {}

    def _merge(new_items: list[CollectedItem]):
        for it in new_items:
            existing = merged.get(it.jan)
            if existing is None or (not existing.name and it.name):
                merged[it.jan] = it

    if yahoo_app_id:
        _merge(YahooJanCollector(yahoo_app_id).collect(keywords, yahoo_genres, pages))
    else:
        log.info("YAHOO_APP_ID 未設定のため Yahoo からの収集をスキップ")
    if rakuten_app_id:
        _merge(RakutenBooksCollector(rakuten_app_id).collect(keywords, pages))
    else:
        log.info("RAKUTEN_APP_ID 未設定のため 楽天ブックスからの収集をスキップ")
    if amazon_client is not None:
        _merge(AmazonJanCollector(amazon_client).collect(keywords, pages))

    log.info("Collected %d unique JAN codes", len(merged))
    return merged


def save_collected(items: dict[str, CollectedItem], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "collected_latest.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["jan", "name", "price", "source", "category"])
        for it in items.values():
            w.writerow([it.jan, it.name, it.price or "", it.source, it.category])
    log.info("Wrote %s", path)
    return path
