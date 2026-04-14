"""
領収書自動抽出・仕訳システム メインスクリプト

Gmail から Yahoo ショッピング・楽天市場・Apple Store の購入確認メールを取得し、
PDF 領収書を保存して MoneyForward クラウド確定申告用の仕訳 CSV を生成する。

使い方:
    python -m extract_receipts.main [オプション]

オプション:
    --days N        過去 N 日分のメールを処理 (デフォルト: .env の DAYS_BACK)
    --dry-run       内容を表示するだけでファイルを作成しない
    --no-pdf        PDF 生成をスキップ
    --ledger-only   MoneyForward CSV の代わりに Excel 仕訳帳のみ生成
    --both          MoneyForward CSV と Excel 仕訳帳の両方を生成
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List

from .config import load_config
from .email_client import fetch_purchase_emails, mark_as_processed
from .ledger import export_to_excel
from .moneyforward_csv import export_to_csv
from .parsers import AppleParser, RakutenParser, Receipt, YahooParser
from .parsers.base import ParseError
from .receipt_pdf import generate_receipt_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

PARSERS = [YahooParser(), RakutenParser(), AppleParser()]


def parse_emails(emails, dry_run: bool) -> List[Receipt]:
    """メールリストを解析して Receipt リストを返す"""
    receipts: List[Receipt] = []
    skipped = 0

    for msg in emails:
        parser = None
        for p in PARSERS:
            if p.can_handle(msg.from_addr):
                parser = p
                break

        if parser is None:
            logger.debug(f"UID {msg.uid}: 対応パーサーなし ({msg.from_addr})")
            skipped += 1
            continue

        try:
            receipt = parser.parse(msg.uid, msg.subject, msg.html_body)
            receipts.append(receipt)
            logger.info(
                f"UID {msg.uid}: 解析成功 [{receipt.store_type}] "
                f"{receipt.order_date} 注文{receipt.order_id} "
                f"合計¥{int(receipt.total):,}"
            )
        except ParseError as e:
            logger.warning(f"UID {msg.uid}: 解析スキップ - {e}")
            skipped += 1
        except Exception as e:
            logger.error(f"UID {msg.uid}: 予期しないエラー - {e}", exc_info=True)
            skipped += 1

    logger.info(
        f"解析結果: 成功 {len(receipts)} 件 / スキップ {skipped} 件"
    )
    return receipts


def run(
    days: int,
    dry_run: bool,
    no_pdf: bool,
    ledger_only: bool,
    both: bool,
) -> None:
    """メイン処理"""
    config = load_config()

    # 1. メール取得
    logger.info(f"=== 領収書抽出開始 (過去{days}日間) ===")
    emails = fetch_purchase_emails(
        host=config.imap_host,
        port=config.imap_port,
        user=config.imap_user,
        password=config.imap_password,
        days_back=days,
    )

    if not emails:
        logger.info("対象メールが見つかりませんでした。終了します。")
        return

    # 2. メール解析
    receipts = parse_emails(emails, dry_run=dry_run)

    if not receipts:
        logger.info("解析できた領収書がありませんでした。終了します。")
        return

    # 3. PDF 生成
    if not no_pdf:
        logger.info(f"=== PDF 生成 ({len(receipts)} 件) ===")
        pdf_count = 0
        for receipt in receipts:
            try:
                pdf_path = generate_receipt_pdf(
                    receipt=receipt,
                    output_dir=config.receipt_output_dir,
                    dry_run=dry_run,
                )
                if not dry_run:
                    pdf_count += 1
            except Exception as e:
                logger.error(f"PDF 生成エラー (注文 {receipt.order_id}): {e}")
        if not dry_run:
            logger.info(f"PDF {pdf_count} 件を {config.receipt_output_dir} に保存しました。")

    # 4. 仕訳出力
    logger.info("=== 仕訳データ出力 ===")
    if not ledger_only:
        csv_path = export_to_csv(receipts, dry_run=dry_run)
        if not dry_run:
            print(f"\n✓ MoneyForward CSV: {csv_path}")
            print("  → MoneyForward クラウド確定申告: 帳簿 → 仕訳帳 → インポート → CSV")

    if ledger_only or both:
        xlsx_path = export_to_excel(receipts, dry_run=dry_run)
        if not dry_run:
            print(f"✓ Excel 仕訳帳: {xlsx_path}")

    # 5. 処理済み UID を記録
    if not dry_run:
        for receipt in receipts:
            mark_as_processed(receipt.email_uid)

    # 6. サマリー表示
    total = sum(r.total for r in receipts)
    print(f"\n=== 処理完了 ===")
    print(f"  取得件数 : {len(receipts)} 件")
    print(f"  仕入合計 : ¥{int(total):,}")
    if not no_pdf and not dry_run:
        print(f"  PDF 保存先: {config.receipt_output_dir}/")
    if dry_run:
        print("  ※ DRY RUN モード - ファイルは作成されていません")


def main():
    parser = argparse.ArgumentParser(
        description="Gmail から購入確認メールを取得して領収書 PDF と仕訳データを生成します"
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="取得対象の日数（省略時は .env の DAYS_BACK を使用）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="内容を表示するだけでファイルを作成しない"
    )
    parser.add_argument(
        "--no-pdf", action="store_true",
        help="PDF 生成をスキップ"
    )
    parser.add_argument(
        "--ledger-only", action="store_true",
        help="MoneyForward CSV の代わりに Excel 仕訳帳のみ生成"
    )
    parser.add_argument(
        "--both", action="store_true",
        help="MoneyForward CSV と Excel 仕訳帳の両方を生成"
    )
    args = parser.parse_args()

    # days が指定されていない場合は config から取得
    days = args.days
    if days is None:
        from .config import load_config as _lc
        try:
            days = _lc().days_back
        except Exception:
            days = 30

    try:
        run(
            days=days,
            dry_run=args.dry_run,
            no_pdf=args.no_pdf,
            ledger_only=args.ledger_only,
            both=args.both,
        )
    except ValueError as e:
        logger.error(f"設定エラー: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("処理を中断しました。")
        sys.exit(0)


if __name__ == "__main__":
    main()
