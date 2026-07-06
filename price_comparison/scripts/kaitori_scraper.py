"""買取商店 (kaitorishouten-co.jp) の買取価格を JAN 検索で取得し、
収集済みの Yahoo!ショッピング価格と突合して利益商品を抽出する。

サイトの検索フォーム (POST /products/list/keyword, name=商品名 or JANコード) を利用。
1件ずつ丁寧にレート制限しながら照会する。

入力:  data/collected/collected_latest.csv (jan, name, price, source, category)
出力:  data/output/kaitorishouten_all_latest.csv       … 買取価格が付いた全商品
       data/output/kaitorishouten_profitable_latest.csv … 利益商品のみ (profit降順)
       data/recon/sample_result_*.html                  … パース検証用サンプル
"""
from __future__ import annotations

import csv
import html as html_mod
import logging
import os
import re
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("kaitori")

BASE = "https://www.kaitorishouten-co.jp"
SEARCH_URL = f"{BASE}/products/list/keyword"
ROOT = Path(__file__).resolve().parent.parent
COLLECTED = ROOT / "data" / "collected" / "collected_latest.csv"
OUT_DIR = ROOT / "data" / "output"
RECON_DIR = ROOT / "data" / "recon"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) price-research/1.0"}
THROTTLE_SEC = 1.2
SHIPPING_COST = int(os.getenv("SHIPPING_COST", "600"))
MIN_PROFIT = int(os.getenv("MIN_PROFIT", "1"))  # 「利益が出るもの全て」なので1円から
LIMIT = int(os.getenv("SCRAPE_LIMIT", "0")) or None

# 商品ブロック抽出用の正規表現 (EC-CUBE系の一覧ページを想定した複数パターン)
PRICE_RE = re.compile(r"([0-9][0-9,]{2,})\s*円")
# <a href="/products/detail/123"> ... 商品名 ... 価格円 ... </a> のようなカード単位
CARD_RE = re.compile(
    r'<a[^>]+href="(?P<url>[^"]*/products/detail/\d+[^"]*)"[^>]*>(?P<body>.*?)</a>',
    re.S,
)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return html_mod.unescape(TAG_RE.sub(" ", s)).strip()


def parse_results(page: str) -> list[dict]:
    """検索結果ページから (商品名, 買取価格, URL) を抽出する。"""
    items: list[dict] = []
    seen = set()
    for m in CARD_RE.finditer(page):
        body = m.group("body")
        prices = [int(p.replace(",", "")) for p in PRICE_RE.findall(body)]
        if not prices:
            continue
        text = strip_tags(body)
        # 価格表記や空白を除いた先頭部分を商品名として扱う
        name = re.sub(r"\s+", " ", text)[:120]
        url = m.group("url")
        key = (url, max(prices))
        if key in seen:
            continue
        seen.add(key)
        items.append({"name": name, "price": max(prices), "url": url})
    if items:
        return items

    # フォールバック: カード構造が違う場合、ページ全体の「◯◯円」を商品名候補と共に拾う
    for m in PRICE_RE.finditer(page):
        start = max(0, m.start() - 300)
        ctx = strip_tags(page[start : m.start()])
        name = re.sub(r"\s+", " ", ctx)[-80:]
        items.append({"name": name, "price": int(m.group(1).replace(",", "")), "url": ""})
    return items


class KaitoriClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(UA)
        self._last = 0.0
        self.consecutive_errors = 0

    def _throttle(self):
        elapsed = time.time() - self._last
        if elapsed < THROTTLE_SEC:
            time.sleep(THROTTLE_SEC - elapsed)
        self._last = time.time()

    def search(self, keyword: str) -> tuple[str, int]:
        """検索して HTML とステータスを返す。POST が駄目なら GET も試す。"""
        self._throttle()
        try:
            r = self.session.post(
                SEARCH_URL,
                data={
                    "page_type": "1",
                    "tag_id": "",
                    "last_category_id": "",
                    "category_id": "",
                    "name": keyword,
                },
                timeout=30,
            )
            if r.ok:
                self.consecutive_errors = 0
                return r.text, r.status_code
            log.warning("POST search HTTP %d for %s", r.status_code, keyword)
        except Exception as e:
            log.warning("POST search error for %s: %s", keyword, e)

        self._throttle()
        try:
            r = self.session.get(
                f"{BASE}/products/list", params={"name": keyword}, timeout=30
            )
            if r.ok:
                self.consecutive_errors = 0
                return r.text, r.status_code
            log.warning("GET search HTTP %d for %s", r.status_code, keyword)
        except Exception as e:
            log.warning("GET search error for %s: %s", keyword, e)
        self.consecutive_errors += 1
        return "", 0


def load_collected() -> list[dict]:
    rows = []
    with COLLECTED.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("jan") and row.get("price"):
                rows.append(row)
    return rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECON_DIR.mkdir(parents=True, exist_ok=True)
    products = load_collected()
    if LIMIT:
        products = products[:LIMIT]
    log.info("Target products: %d", len(products))

    client = KaitoriClient()
    all_rows: list[dict] = []
    samples_saved = 0
    no_hit = 0

    for i, p in enumerate(products, 1):
        jan = p["jan"].strip()
        page, status = client.search(jan)
        if client.consecutive_errors >= 10:
            log.error("連続エラーのため中断 (処理済み %d 件)", i)
            break
        if not page:
            continue
        hits = parse_results(page)
        if samples_saved < 3 and (hits or samples_saved == 0):
            (RECON_DIR / f"sample_result_{samples_saved}.html").write_text(
                page[:150_000], encoding="utf-8"
            )
            samples_saved += 1
        if not hits:
            no_hit += 1
            continue
        best = max(hits, key=lambda h: h["price"])
        ec_price = int(float(p["price"]))
        profit = best["price"] - ec_price - SHIPPING_COST
        all_rows.append(
            {
                "jan": jan,
                "ec_name": p.get("name", ""),
                "kaitori_name": best["name"],
                "kaitori_price": best["price"],
                "yahoo_price": ec_price,
                "shipping": SHIPPING_COST,
                "profit": profit,
                "profit_rate": round(profit / ec_price, 4) if ec_price else 0,
                "kaitori_url": (BASE + best["url"]) if best["url"].startswith("/") else best["url"],
                "category": p.get("category", ""),
            }
        )
        if i % 25 == 0:
            log.info("Processed %d/%d (matched=%d, no_hit=%d)", i, len(products), len(all_rows), no_hit)

    log.info("Done. matched=%d, no_hit=%d", len(all_rows), no_hit)

    fieldnames = [
        "jan", "ec_name", "kaitori_name", "kaitori_price", "yahoo_price",
        "shipping", "profit", "profit_rate", "kaitori_url", "category",
    ]

    def write(path: Path, rows: list[dict]):
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        log.info("Wrote %s (%d rows)", path, len(rows))

    all_rows.sort(key=lambda r: r["profit"], reverse=True)
    write(OUT_DIR / "kaitorishouten_all_latest.csv", all_rows)
    profitable = [r for r in all_rows if r["profit"] >= MIN_PROFIT]
    write(OUT_DIR / "kaitorishouten_profitable_latest.csv", profitable)


if __name__ == "__main__":
    main()
