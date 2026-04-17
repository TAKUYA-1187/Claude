"""
Amazon バイヤーへの取扱説明書自動送信スクリプト

Amazon SP-API を使用してベッドテーブル購入者に最新版取扱説明書の
OneDrive 共有リンクをメッセージで案内する。

使い方:
    python -m amazon_manual_sender.main [オプション]

オプション:
    --days N      取得対象の日数（デフォルト: 365）
    --dry-run     送信せず対象注文を表示するだけ
    --asin ASIN   商品ASIN（.env の PRODUCT_ASIN を上書き）

cron 設定例（2時間ごとに新規注文をチェック）:
    0 */2 * * * cd /home/user/Claude && python -m amazon_manual_sender.main --days 3 >> logs/amazon_manual.log 2>&1

初回一括送信（全購入者対象）:
    python -m amazon_manual_sender.main --days 365
"""
import argparse
import logging
import sys
import time

from .amazon_client import RATE_LIMIT_SLEEP, get_orders, send_manual_message
from .config import load_config
from .state import is_already_sent, load_sent_orders, save_sent_order

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run(days: int, dry_run: bool, asin_override: str | None) -> None:
    config = load_config()

    if asin_override:
        config.product_asin = asin_override

    logger.info("=" * 50)
    logger.info(f"取扱説明書自動送信 開始 (ASIN: {config.product_asin}, 過去{days}日間)")
    if dry_run:
        logger.info("[DRY RUN モード] メッセージは送信されません")
    logger.info("=" * 50)

    # 1. 注文一覧取得
    orders = get_orders(config, days_back=days)

    if not orders:
        logger.info("対象注文が見つかりませんでした。終了します。")
        return

    # 2. 未送信注文のフィルタリング
    unsent_orders = [
        o for o in orders
        if not is_already_sent(config.state_file, o["AmazonOrderId"])
    ]
    already_sent_count = len(orders) - len(unsent_orders)

    logger.info(
        f"注文合計: {len(orders)} 件 / 送信済み: {already_sent_count} 件 / 未送信: {len(unsent_orders)} 件"
    )

    if not unsent_orders:
        logger.info("未送信の注文はありません。終了します。")
        return

    # 3. メッセージ送信
    sent_count = 0
    failed_count = 0

    for order in unsent_orders:
        order_id = order["AmazonOrderId"]
        purchase_date = order.get("PurchaseDate", "不明")
        logger.info(f"処理中: 注文 {order_id} (購入日: {purchase_date})")

        success = send_manual_message(config, order_id, dry_run=dry_run)

        if success:
            if not dry_run:
                save_sent_order(config.state_file, order_id)
            sent_count += 1
        else:
            failed_count += 1

        # Rate limit 対応
        time.sleep(RATE_LIMIT_SLEEP)

    # 4. サマリー表示
    logger.info("=" * 50)
    logger.info("処理完了")
    logger.info(f"  送信成功: {sent_count} 件")
    if failed_count:
        logger.info(f"  送信失敗: {failed_count} 件")
    if dry_run:
        logger.info("  ※ DRY RUN モード - メッセージは送信されていません")
    else:
        logger.info(f"  送信済み記録: {config.state_file}")
    logger.info("=" * 50)

    print(f"\n=== 完了 ===")
    print(f"  送信成功: {sent_count} 件 / 失敗: {failed_count} 件")
    if dry_run:
        print("  ※ DRY RUN モード - ファイルは変更されていません")


def main():
    parser = argparse.ArgumentParser(
        description="Amazon バイヤーに最新版取扱説明書（OneDrive リンク）をメッセージで案内します"
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="取得対象の日数（デフォルト: .env の DAYS_BACK または 365）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="送信せず対象注文を表示するだけ"
    )
    parser.add_argument(
        "--asin", type=str, default=None,
        help="商品ASIN（.env の PRODUCT_ASIN を上書き）"
    )
    args = parser.parse_args()

    days = args.days
    if days is None:
        try:
            from .config import load_config as _lc
            days = _lc().days_back
        except Exception:
            days = 365

    try:
        run(days=days, dry_run=args.dry_run, asin_override=args.asin)
    except ValueError as e:
        logger.error(f"設定エラー: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("処理を中断しました。")
        sys.exit(0)


if __name__ == "__main__":
    main()
