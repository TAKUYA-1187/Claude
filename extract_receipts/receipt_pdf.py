"""領収書 PDF 生成モジュール (reportlab)"""
import logging
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .parsers.base import Receipt

logger = logging.getLogger(__name__)

# 日本語フォント登録
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
JP_FONT = "HeiseiKakuGo-W5"

STORE_LABELS = {
    "yahoo": "Yahoo ショッピング",
    "rakuten": "楽天市場",
    "apple": "Apple Store",
}


def _get_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            fontName=JP_FONT,
            fontSize=20,
            leading=28,
            alignment=1,  # CENTER
            spaceAfter=4 * mm,
        ),
        "store": ParagraphStyle(
            "Store",
            fontName=JP_FONT,
            fontSize=12,
            leading=18,
            alignment=1,
            spaceAfter=2 * mm,
        ),
        "normal": ParagraphStyle(
            "Normal",
            fontName=JP_FONT,
            fontSize=10,
            leading=16,
        ),
        "small": ParagraphStyle(
            "Small",
            fontName=JP_FONT,
            fontSize=9,
            leading=14,
            textColor=colors.grey,
        ),
        "label": ParagraphStyle(
            "Label",
            fontName=JP_FONT,
            fontSize=10,
            leading=16,
            textColor=colors.grey,
        ),
        "total": ParagraphStyle(
            "Total",
            fontName=JP_FONT,
            fontSize=13,
            leading=20,
            textColor=colors.HexColor("#1a1a1a"),
        ),
    }


def generate_receipt_pdf(receipt: Receipt, output_dir: Path, dry_run: bool = False) -> Path:
    """
    Receipt オブジェクトから PDF ファイルを生成する。

    Args:
        receipt: 領収書データ
        output_dir: 保存先ルートディレクトリ
        dry_run: True の場合はパスを返すのみでファイルを作成しない

    Returns:
        生成した PDF ファイルのパス
    """
    subdir = output_dir / receipt.pdf_subdir
    pdf_path = subdir / receipt.pdf_filename

    if dry_run:
        logger.info(f"[DRY RUN] PDF 生成: {pdf_path}")
        return pdf_path

    subdir.mkdir(parents=True, exist_ok=True)
    _build_pdf(receipt, pdf_path)
    logger.info(f"PDF 生成完了: {pdf_path}")
    return pdf_path


def _build_pdf(receipt: Receipt, pdf_path: Path) -> None:
    """PDF を構築してファイルに書き出す"""
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = _get_styles()
    story = []

    # ---- ヘッダー ----
    store_label = STORE_LABELS.get(receipt.store_type, receipt.store_name)
    story.append(Paragraph("領　収　書", styles["title"]))
    story.append(Paragraph(store_label, styles["store"]))
    story.append(Spacer(1, 4 * mm))

    # ---- 注文情報テーブル ----
    order_info_data = [
        ["取引日", receipt.order_date.strftime("%Y年%m月%d日")],
        ["注文番号", receipt.order_id],
        ["店舗名", receipt.store_name],
        ["支払方法", receipt.payment_method or "クレジットカード"],
    ]
    info_table = Table(order_info_data, colWidths=[40 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), JP_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6 * mm))

    # ---- 商品明細テーブル ----
    if receipt.items:
        story.append(Paragraph("◆ 商品明細", styles["normal"]))
        story.append(Spacer(1, 2 * mm))

        item_data = [["品名", "数量", "単価", "金額"]]
        for item in receipt.items:
            item_data.append([
                item.name,
                str(item.quantity),
                f"¥{int(item.unit_price):,}",
                f"¥{int(item.amount):,}",
            ])

        col_widths = [90 * mm, 15 * mm, 30 * mm, 30 * mm]
        item_table = Table(item_data, colWidths=col_widths, repeatRows=1)
        item_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), JP_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 6 * mm))

    # ---- 金額サマリー ----
    summary_data = []
    if receipt.subtotal > 0:
        summary_data.append(["小計", f"¥{int(receipt.subtotal):,}"])
    if receipt.shipping_cost > 0:
        summary_data.append(["送料", f"¥{int(receipt.shipping_cost):,}"])
    if receipt.tax_amount > 0:
        summary_data.append([f"消費税（10%）", f"¥{int(receipt.tax_amount):,}"])
    summary_data.append(["合計金額", f"¥{int(receipt.total):,}"])

    summary_table = Table(summary_data, colWidths=[120 * mm, 45 * mm])
    summary_style = [
        ("FONTNAME", (0, 0), (-1, -1), JP_FONT),
        ("FONTSIZE", (0, 0), (-1, -2), 10),
        ("FONTSIZE", (0, -1), (-1, -1), 13),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 0), (0, -2), colors.grey),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#1a1a1a")),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#2c5282")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]
    summary_table.setStyle(TableStyle(summary_style))
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    # ---- フッター ----
    footer_text = (
        f"※ このPDFはGmailの購入確認メールから自動生成されました。<br/>"
        f"発行元: {store_label} / 注文番号: {receipt.order_id}"
    )
    story.append(Paragraph(footer_text, styles["small"]))

    doc.build(story)
