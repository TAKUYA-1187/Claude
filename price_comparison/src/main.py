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
from datetime import datetime
from pathlib import Path

from .config import config
from .csv_loader import load_all
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


def run(limit: int | None = None):
    products = load_all(config.input_dir)
    if not products:
        log.error(
            "CSV が見つかりません。買取スキャナー『全データCSV保存』で出力したCSVを %s に置いてください。",
            config.input_dir,
        )
        sys.exit(1)
    if limit:
        products = products[:limit]

    amazon, rakuten, yahoo = build_clients()

    rows: list = []
    for i, p in enumerate(products, 1):
        amz = amazon.min_price_by_jan(p.jan) if amazon else None
        rak = rakuten.min_price_by_jan(p.jan) if rakuten else None
        yho = yahoo.min_price_by_jan(p.jan) if yahoo else None
        pr = PriceRow(p.jan, p.name, p.buy_price, amz, rak, yho)
        profit_row = compute(pr, config)
        if profit_row is None:
            log.debug("No price found for %s", p.jan)
            continue
        rows.append(profit_row)
        if i % 50 == 0:
            log.info("Processed %d / %d", i, len(products))

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
    args = ap.parse_args()
    run(limit=args.limit)


if __name__ == "__main__":
    main()
