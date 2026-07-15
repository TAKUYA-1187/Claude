"""Amazon 刈り取り値下がりアラート - エントリポイント。

流れ:
1. Keepa Deal API で「直近24時間に新品価格が大幅下落した商品」を横断取得
2. Product API で現在価格 / 30日平均 / 新品出品者数を検証
3. 出品者3名以上 & 下落幅が閾値以上の商品を抽出
4. 未通知のものをメールで即時通知し、通知済みとして記録
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import load_config
from .deal_filter import filter_products
from .emailer import send_alert_email
from .keepa_client import KeepaClient
from .state import AlertState

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def run(dry_run: bool = False, limit: int | None = None) -> int:
    cfg = load_config()
    client = KeepaClient(cfg.keepa_api_key, cfg.domain_id)
    state = AlertState(BASE_DIR / cfg.state_file, cfg.alert_ttl_hours)

    deals = client.fetch_deals(
        min_drop_percent=cfg.min_drop_percent,
        price_range=(cfg.min_price, cfg.max_price),
        max_sales_rank=cfg.max_sales_rank,
    )
    if limit:
        deals = deals[:limit]
    if not deals:
        log.info("大幅値下がり商品なし")
        return 0

    asins = [d["asin"] for d in deals if d.get("asin")]
    products: list[dict] = []
    for i in range(0, len(asins), cfg.product_batch_size):
        products.extend(client.fetch_products(asins[i : i + cfg.product_batch_size]))

    alerts = filter_products(products, cfg)
    new_alerts = [a for a in alerts if state.should_alert(a.asin, a.current_price)]
    new_alerts = new_alerts[: cfg.max_alerts_per_run]

    log.info("通知対象: %d件 (条件合致 %d件、通知済み除外後)", len(new_alerts), len(alerts))
    for a in new_alerts:
        log.info(
            "  %s -%.1f%% ¥%s (avg ¥%s, 出品者%d) %s",
            a.asin, a.drop_percent, f"{a.current_price:,}", f"{a.avg30_price:,}",
            a.seller_count, a.title[:40],
        )

    if not new_alerts:
        return 0

    if dry_run:
        log.info("dry-run のためメール送信・状態保存をスキップ")
        return len(new_alerts)

    send_alert_email(new_alerts, cfg)
    for a in new_alerts:
        state.mark_alerted(a.asin, a.current_price)
    state.save()
    return len(new_alerts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Amazon 刈り取り値下がりアラート")
    parser.add_argument("--dry-run", action="store_true", help="メール送信せず抽出結果のみ表示")
    parser.add_argument("--limit", type=int, default=None, help="処理する候補数の上限（テスト用）")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    try:
        count = run(dry_run=args.dry_run, limit=args.limit)
    except Exception:
        log.exception("実行失敗")
        sys.exit(1)
    log.info("完了: %d件通知", count)


if __name__ == "__main__":
    main()
