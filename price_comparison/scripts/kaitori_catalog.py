"""買取商店 (kaitorishouten-co.jp) の全カテゴリページを巡回して
買取価格表を取得し、収集済みの Yahoo!ショッピング価格と突合する。

JAN 個別検索はカテゴリによってヒットしないため (iPhone 等)、
sitemap.xml の /category/... ページを直接巡回する方が網羅性が高い。

出力:
  data/output/kaitorishouten_catalog_latest.csv    … 買取商店の全取得商品 (JAN・買取価格)
  data/output/kaitorishouten_all_latest.csv        … Yahoo価格と両方あるもの (差額つき)
  data/output/kaitorishouten_profitable_latest.csv … 利益商品のみ (profit降順)
"""
from __future__ import annotations

import csv
import logging
import os
import re
import time
from pathlib import Path

import requests

# 検索結果と同じ商品テーブル構造を想定してパーサーを再利用
from kaitori_scraper import parse_results  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("catalog")

BASE = "https://www.kaitorishouten-co.jp"
ROOT = Path(__file__).resolve().parent.parent
COLLECTED = ROOT / "data" / "collected" / "collected_latest.csv"
OUT_DIR = ROOT / "data" / "output"
RECON_DIR = ROOT / "data" / "recon"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) price-research/1.0"}
THROTTLE_SEC = float(os.getenv("CRAWL_THROTTLE", "1.2"))
SHIPPING_COST = int(os.getenv("SHIPPING_COST", "600"))
MIN_PROFIT = int(os.getenv("MIN_PROFIT", "1"))
MAX_PAGES_PER_CATEGORY = int(os.getenv("MAX_PAGES_PER_CATEGORY", "20"))

_last_call = 0.0
session = requests.Session()
session.headers.update(UA)


def fetch(url: str) -> str:
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < THROTTLE_SEC:
        time.sleep(THROTTLE_SEC - elapsed)
    _last_call = time.time()
    try:
        r = session.get(url, timeout=30)
        if not r.ok:
            log.warning("GET %s -> HTTP %d", url, r.status_code)
            return ""
        return r.text
    except Exception as e:
        log.warning("GET %s error: %s", url, e)
        return ""


def category_urls() -> list[str]:
    xml = fetch(f"{BASE}/sitemap.xml")
    urls = re.findall(r"<loc>([^<]+/category/[^<]+)</loc>", xml)
    log.info("Sitemap categories: %d", len(urls))
    return urls


def crawl_category(url: str) -> list[dict]:
    items: list[dict] = []
    seen_first: str | None = None
    for page_no in range(1, MAX_PAGES_PER_CATEGORY + 1):
        page_url = url if page_no == 1 else f"{url}?pageno={page_no}"
        html = fetch(page_url)
        if not html:
            break
        rows = [r for r in parse_results(html) if r.get("jan")]
        if not rows:
            break
        # ページングが効かず同じ内容が返る場合は打ち切り
        if page_no > 1 and rows and rows[0]["jan"] == seen_first:
            break
        if page_no == 1:
            seen_first = rows[0]["jan"] if rows else None
        items.extend(rows)
        # 次ページへのリンクが無ければ終了
        if f"pageno={page_no + 1}" not in html:
            break
    return items


def load_yahoo() -> dict[str, dict]:
    result: dict[str, dict] = {}
    if not COLLECTED.exists():
        log.warning("collected_latest.csv がありません")
        return result
    with COLLECTED.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("jan") and row.get("price"):
                result[row["jan"]] = row
    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECON_DIR.mkdir(parents=True, exist_ok=True)

    catalog: dict[str, dict] = {}  # jan -> {name, price, category_url}
    urls = category_urls()
    for i, url in enumerate(urls, 1):
        rows = crawl_category(url)
        for r in rows:
            existing = catalog.get(r["jan"])
            if existing is None or r["price"] > existing["price"]:
                catalog[r["jan"]] = {
                    "name": r["name"],
                    "price": r["price"],
                    "category_url": url,
                }
        if i % 25 == 0:
            log.info("Categories %d/%d, catalog=%d items", i, len(urls), len(catalog))
    log.info("Catalog complete: %d unique JAN items", len(catalog))

    # 買取カタログを保存
    with (OUT_DIR / "kaitorishouten_catalog_latest.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        w = csv.writer(f)
        w.writerow(["jan", "name", "kaitori_price", "category_url"])
        for jan, it in sorted(catalog.items(), key=lambda x: -x[1]["price"]):
            w.writerow([jan, it["name"], it["price"], it["category_url"]])
    log.info("Wrote kaitorishouten_catalog_latest.csv (%d rows)", len(catalog))

    # Yahoo 価格と突合
    yahoo = load_yahoo()
    both = []
    for jan, it in catalog.items():
        y = yahoo.get(jan)
        if not y:
            continue
        yp = int(float(y["price"]))
        profit = it["price"] - yp - SHIPPING_COST
        both.append(
            {
                "jan": jan,
                "ec_name": y.get("name", ""),
                "kaitori_name": it["name"],
                "kaitori_price": it["price"],
                "yahoo_price": yp,
                "shipping": SHIPPING_COST,
                "profit": profit,
                "profit_rate": round(profit / yp, 4) if yp else 0,
                "kaitori_url": it["category_url"],
                "category": y.get("category", ""),
            }
        )
    both.sort(key=lambda r: r["profit"], reverse=True)

    fieldnames = [
        "jan", "ec_name", "kaitori_name", "kaitori_price", "yahoo_price",
        "shipping", "profit", "profit_rate", "kaitori_url", "category",
    ]
    for name, rows in (
        ("kaitorishouten_all_latest.csv", both),
        ("kaitorishouten_profitable_latest.csv", [r for r in both if r["profit"] >= MIN_PROFIT]),
    ):
        with (OUT_DIR / name).open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        log.info("Wrote %s (%d rows)", name, len(rows))

    log.info(
        "Summary: catalog=%d, matched_with_yahoo=%d, profitable=%d",
        len(catalog), len(both), sum(1 for r in both if r["profit"] >= MIN_PROFIT),
    )


if __name__ == "__main__":
    main()
