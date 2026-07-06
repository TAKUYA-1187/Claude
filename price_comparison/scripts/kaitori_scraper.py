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

# 検索結果は <tr id="ex-product-NNN" class="price_list_item ..."> の表構造。
# 商品名は名前セルの先頭テキスト、JANは product-code-default スパン、
# 買取価格は item-price div (「新品買取額」列)。
ROW_RE = re.compile(r'<tr id="ex-product-\d+"[^>]*>(?P<body>.*?)</tr>', re.S)
PRICE_DIV_RE = re.compile(r'class="item-price[^"]*"[^>]*>\s*([0-9][0-9,]*)\s*円', re.S)
JAN_SPAN_RE = re.compile(r'class="product-code-default"[^>]*>\s*(\d{8,13})\s*<')
NAME_TD_RE = re.compile(r'<td class="align-middle">\s*(?!<img)(.*?)<div class="item-desc">', re.S)
PRICE_RE = re.compile(r"([0-9][0-9,]{2,})\s*円")
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return html_mod.unescape(TAG_RE.sub(" ", s)).strip()


def parse_results(page: str) -> list[dict]:
    """検索結果ページから (商品名, JAN, 買取価格) を抽出する。"""
    items: list[dict] = []
    for m in ROW_RE.finditer(page):
        body = m.group("body")
        prices = [int(p.replace(",", "")) for p in PRICE_DIV_RE.findall(body)]
        if not prices:
            continue
        name_m = NAME_TD_RE.search(body)
        name = re.sub(r"\s+", " ", strip_tags(name_m.group(1)))[:120] if name_m else ""
        jan_m = JAN_SPAN_RE.search(body)
        items.append(
            {
                "name": name,
                "jan": jan_m.group(1) if jan_m else "",
                "price": max(prices),
                "url": "",
            }
        )
    if items:
        return items

    # フォールバック: 行構造が変わった場合はページ全体から価格らしき表記を拾う
    for m in PRICE_RE.finditer(page):
        start = max(0, m.start() - 300)
        ctx = strip_tags(page[start : m.start()])
        name = re.sub(r"\s+", " ", ctx)[-80:]
        items.append({"name": name, "jan": "", "price": int(m.group(1).replace(",", "")), "url": ""})
    return items


class KaitoriClient:
    """トップページの検索フォームは jQuery の $.ajax で POST し、
    返ってきた HTML 断片を #search-content に挿入する仕組みのため、
    X-Requested-With ヘッダとセッション Cookie を付けて同じリクエストを再現する。
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(UA)
        self._last = 0.0
        self.consecutive_errors = 0
        # セッション Cookie を得るためトップページへ一度アクセス
        try:
            r = self.session.get(f"{BASE}/", timeout=30)
            log.info("Warmup GET / -> HTTP %d (cookies: %s)", r.status_code, list(self.session.cookies.keys()))
        except Exception as e:
            log.warning("Warmup failed: %s", e)

    def _throttle(self):
        elapsed = time.time() - self._last
        if elapsed < THROTTLE_SEC:
            time.sleep(THROTTLE_SEC - elapsed)
        self._last = time.time()

    def search(self, keyword: str) -> tuple[str, int]:
        """検索して HTML とステータスを返す。ステータスが 404 でも
        本文に中身があればパース対象として返す (0件時に404を返す実装がある)。"""
        ajax_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE}/",
            "Origin": BASE,
        }
        data = {
            "page_type": "1",
            "tag_id": "",
            "last_category_id": "",
            "name": keyword,
        }
        last_text, last_status = "", 0
        # category_id 空 → デフォルト値 7 の順に試す
        for cat in ("", "7"):
            self._throttle()
            try:
                r = self.session.post(
                    SEARCH_URL,
                    data={**data, "category_id": cat},
                    headers=ajax_headers,
                    timeout=30,
                )
                last_text, last_status = r.text, r.status_code
                if r.ok:
                    self.consecutive_errors = 0
                    return r.text, r.status_code
                log.warning("POST(cat=%r) HTTP %d for %s (len=%d)", cat, r.status_code, keyword, len(r.text))
            except Exception as e:
                log.warning("POST(cat=%r) error for %s: %s", cat, keyword, e)

        if len(last_text) > 500:
            # エラーステータスでも本文があれば結果ページの可能性があるので返す
            self.consecutive_errors = 0
            return last_text, last_status
        self.consecutive_errors += 1
        return last_text, last_status


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

    # 制御用: 確実にヒットするはずのキーワードで検索機能の生存確認
    page, status = client.search("iPhone")
    control_hits = parse_results(page) if page else []
    log.info("Control search 'iPhone': HTTP %d, len=%d, parsed hits=%d", status, len(page), len(control_hits))
    if page:
        (RECON_DIR / "sample_control.html").write_text(page[:150_000], encoding="utf-8")
    client.consecutive_errors = 0

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
        # JAN が取れている行は完全一致のみ採用 (部分一致の誤マッチ防止)
        exact = [h for h in hits if h.get("jan") == jan]
        if not exact and all(h.get("jan") for h in hits):
            no_hit += 1
            continue
        best = max(exact or hits, key=lambda h: h["price"])
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
                "kaitori_url": f"{BASE}/?s={jan}",
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
