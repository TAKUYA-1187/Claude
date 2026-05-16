"""価格比較 & 利益商品抽出のオーケストレーター。

使い方:
  python -m src.main            # data/input/*.csv を読んで data/output へ出力
  python -m src.main --limit 10 # 先頭10件だけ処理 (テスト用)
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from .config import config
from .csv_loader import load_all
from .onedrive_fetcher import fetch_folder
from .profit_calculator import PriceRow, compute, is_profitable
from .rakuten_client import RakutenClient
from .yahoo_client import YahooClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("main")


def build_clients():
    rakuten = None
    yahoo = None
    amazon = None
    if config.rakuten_app_id:
        rakuten = RakutenClient(config.rakuten_app_id, config.rakuten_affiliate_id or None)
    else:
        log.warning("RAKUTEN_APP_ID not set; skipping Rakuten")
    if config.yahoo_app_id:
        yahoo = YahooClient(config.yahoo_app_id)
    else:
        log.warning("YAHOO_APP_ID not set; skipping Yahoo")
    if config.amazon_access_key and config.amazon_secret_key and config.amazon_partner_tag:
        try:
            from .amazon_client import AmazonClient

            amazon = AmazonClient(
                config.amazon_access_key,
                config.amazon_secret_key,
                config.amazon_partner_tag,
                config.amazon_host,
                config.amazon_region,
            )
        except Exception as e:
            log.warning("Amazon client init failed: %s", e)
    else:
        log.warning("Amazon credentials not set; skipping Amazon")

    if not (rakuten or yahoo or amazon):
        log.error("No EC site API configured. Set at least one in .env")
        sys.exit(2)
    return amazon, rakuten, yahoo


def run(limit: int | None = None, skip_fetch: bool = False):
    if not skip_fetch and config.onedrive_share_url:
        log.info("Fetching CSV from OneDrive share...")
        try:
            fetched = fetch_folder(config.onedrive_share_url, config.input_dir)
            log.info("Fetched %d CSV file(s) from OneDrive", len(fetched))
        except Exception as e:
            log.error("OneDrive fetch failed: %s", e)
            # 既存CSVがあれば続行、なければ致命的
    log.info("Enabled shops: %s", config.enabled_shops)
    products = load_all(config.input_dir, config.enabled_shops)
    if not products:
        log.error(
            "対象商品が見つかりません。CSV を %s に配置し、ENABLED_SHOPS (%s) の列が含まれているか確認してください。",
            config.input_dir,
            config.enabled_shops,
        )
        sys.exit(1)
    if limit:
        products = products[:limit]

    amazon, rakuten, yahoo = build_clients()

    def fetch_one(p):
        """1商品分のAPI呼び出しを並列実行（Amazon・楽天・Yahoo を同時取得）。"""
        with ThreadPoolExecutor(max_workers=3) as ex:
            fut_amz = ex.submit(amazon.min_price_by_jan, p.jan) if amazon else None
            fut_rak = ex.submit(rakuten.min_price_by_jan, p.jan) if rakuten else None
            fut_yho = ex.submit(yahoo.min_price_by_jan, p.jan) if yahoo else None

            def safe_result(fut):
                try:
                    return fut.result() if fut else None
                except Exception as e:
                    log.warning("Price fetch error for %s: %s", p.jan, e)
                    return None

            amz = safe_result(fut_amz)
            rak = safe_result(fut_rak)
            yho = safe_result(fut_yho)

        pr = PriceRow(p.jan, p.name, p.buy_price, p.buy_shop, amz, rak, yho)
        return compute(pr, config)

    rows: list = []
    total = len(products)
    done = 0

    # 商品単位で並列処理。各クライアントは内部ロックでレート制限を保証する。
    max_workers = min(5, total) if total > 0 else 1
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_product = {pool.submit(fetch_one, p): p for p in products}
        for fut in as_completed(future_to_product):
            done += 1
            p = future_to_product[fut]
            try:
                profit_row = fut.result()
            except Exception as e:
                log.warning("Failed to process %s: %s", p.jan, e)
                profit_row = None
            if profit_row is None:
                log.debug("No price found for %s", p.jan)
            else:
                rows.append(profit_row)
            if done % 50 == 0:
                log.info("Processed %d / %d", done, total)
    log.info("Processed %d / %d (complete)", done, total)

    profitable = sorted(
        (r for r in rows if is_profitable(r, config)),
        key=lambda r: r.profit,
        reverse=True,
    )
    log.info("Total: %d, Profitable: %d", len(rows), len(profitable))

    config.output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = config.output_dir / f"profitable_{ts}.csv"
    json_path = config.output_dir / f"profitable_{ts}.json"
    latest_csv = config.output_dir / "profitable_latest.csv"
    latest_json = config.output_dir / "profitable_latest.json"

    if profitable:
        fieldnames = list(profitable[0].as_dict().keys())
        for target in (csv_path, latest_csv):
            with target.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for r in profitable:
                    w.writerow(r.as_dict())
        for target in (json_path, latest_json):
            target.write_text(
                json.dumps([r.as_dict() for r in profitable], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        log.info("Wrote %s and %s", csv_path, json_path)
    else:
        log.info("No profitable products this run")
        # 前回のlatestを上書きしないよう、空ファイルは出力しない


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument(
        "--skip-fetch",
        action="store_true",
        help="OneDrive からの取得をスキップし、ローカルCSVのみ使用",
    )
    args = ap.parse_args()
    run(limit=args.limit, skip_fetch=args.skip_fetch)


if __name__ == "__main__":
    main()
