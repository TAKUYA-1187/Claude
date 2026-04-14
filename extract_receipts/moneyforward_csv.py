"""
MoneyForward クラウド確定申告 仕訳インポート CSV 生成モジュール

仕訳ルール（せどり・個人事業主・青色申告）:
  Yahoo/楽天 購入  → 借方: 仕入高 / 貸方: 未払金
  送料（別途）     → 借方: 荷造運賃 / 貸方: 未払金
  Apple Store 購入 → 借方: 消耗品費 / 貸方: 未払金
"""
import csv
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from .parsers.base import Receipt

logger = logging.getLogger(__name__)

# MoneyForward クラウド確定申告 仕訳インポート CSV ヘッダー
MF_HEADERS = [
    "取引日",
    "借方勘定科目",
    "借方補助科目",
    "借方税区分",
    "借方金額（税込）",
    "貸方勘定科目",
    "貸方補助科目",
    "貸方税区分",
    "貸方金額（税込）",
    "摘要",
]

# 税区分コード（MoneyForward クラウド確定申告）
TAX_PURCHASE_10 = "課税仕入10%"
TAX_NONE = "対象外"


def _build_description(receipt: Receipt) -> str:
    """摘要文字列を構築する"""
    store_label = {
        "yahoo": "Yahoo ショッピング",
        "rakuten": "楽天市場",
        "apple": "Apple Store",
    }.get(receipt.store_type, receipt.store_name)

    item_summary = ""
    if receipt.items:
        first_item = receipt.items[0].name[:20]
        suffix = f" 他{len(receipt.items) - 1}点" if len(receipt.items) > 1 else ""
        item_summary = f" {first_item}{suffix}"

    return f"{store_label} 注文番号:{receipt.order_id}{item_summary}"


def _receipt_to_rows(receipt: Receipt) -> List[List[str]]:
    """Receipt 1件を仕訳行（複数）に変換する"""
    rows = []
    date_str = receipt.order_date.strftime("%Y/%m/%d")
    description = _build_description(receipt)

    # --- 商品仕入の仕訳 ---
    if receipt.store_type in ("yahoo", "rakuten"):
        # せどり仕入: 仕入高 / 未払金
        purchase_amount = receipt.total - receipt.shipping_cost
        if purchase_amount > 0:
            rows.append([
                date_str,
                "仕入高",          # 借方勘定科目
                "",                # 借方補助科目
                TAX_PURCHASE_10,   # 借方税区分
                str(int(purchase_amount)),  # 借方金額（税込）
                "未払金",          # 貸方勘定科目
                "",                # 貸方補助科目
                TAX_NONE,          # 貸方税区分
                str(int(purchase_amount)),  # 貸方金額（税込）
                description,
            ])
    elif receipt.store_type == "apple":
        # Apple Store: 消耗品費 / 未払金（10万円未満）or 備品（10万円以上）
        purchase_amount = receipt.total - receipt.shipping_cost
        if purchase_amount > 0:
            debit_account = "消耗品費" if purchase_amount < Decimal("100000") else "備品"
            rows.append([
                date_str,
                debit_account,
                "",
                TAX_PURCHASE_10,
                str(int(purchase_amount)),
                "未払金",
                "",
                TAX_NONE,
                str(int(purchase_amount)),
                description,
            ])

    # --- 送料の仕訳（送料が別途計上の場合）---
    if receipt.shipping_cost > 0:
        shipping_desc = f"送料 {description}"
        rows.append([
            date_str,
            "荷造運賃",
            "",
            TAX_PURCHASE_10,
            str(int(receipt.shipping_cost)),
            "未払金",
            "",
            TAX_NONE,
            str(int(receipt.shipping_cost)),
            shipping_desc[:100],
        ])

    return rows


def export_to_csv(
    receipts: List[Receipt],
    output_path: Optional[Path] = None,
    dry_run: bool = False,
) -> Path:
    """
    Receipt リストを MoneyForward クラウド確定申告インポート用 CSV に書き出す。

    Args:
        receipts: 領収書データのリスト
        output_path: 出力先パス（省略時は自動生成）
        dry_run: True の場合はパスを返すのみでファイルを作成しない

    Returns:
        出力した CSV ファイルのパス
    """
    if output_path is None:
        today = date.today().strftime("%Y%m%d")
        output_path = Path(f"moneyforward_仕訳_{today}.csv")

    if dry_run:
        total_rows = sum(len(_receipt_to_rows(r)) for r in receipts)
        logger.info(f"[DRY RUN] MoneyForward CSV 出力: {output_path} ({total_rows} 行)")
        return output_path

    all_rows: List[List[str]] = []
    for receipt in receipts:
        try:
            rows = _receipt_to_rows(receipt)
            all_rows.extend(rows)
        except Exception as e:
            logger.warning(f"仕訳生成スキップ (UID {receipt.email_uid}): {e}")

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(MF_HEADERS)
        writer.writerows(all_rows)

    logger.info(
        f"MoneyForward CSV 出力完了: {output_path} "
        f"({len(receipts)} 件 / {len(all_rows)} 仕訳行)"
    )
    return output_path
