"""買取スキャナー『全データCSV保存』で出力したCSVを読み込む。

買取スキャナーのCSVは列名が日本語で出力され、リリースにより揺れがあるため、
複数の候補名にマッチさせて正規化する。
"""
from __future__ import annotations

import glob
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

log = logging.getLogger(__name__)


JAN_ALIASES = ["JAN", "JANコード", "jan", "jan_code", "barcode", "バーコード"]
NAME_ALIASES = ["商品名", "title", "name", "product_name"]
BUY_PRICE_ALIASES = [
    "買取価格",
    "買取金額",
    "買取上限",
    "買取",
    "buy_price",
    "kaitori",
]
CATEGORY_ALIASES = ["カテゴリ", "category", "ジャンル"]
ASIN_ALIASES = ["ASIN", "asin"]


@dataclass
class Product:
    jan: str
    name: str
    buy_price: float
    category: str | None = None
    asin: str | None = None


def _pick(df: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    for a in aliases:
        if a in df.columns:
            return a
    # 前後の空白・大文字小文字を無視して探索
    lowered = {c.strip().lower(): c for c in df.columns}
    for a in aliases:
        if a.strip().lower() in lowered:
            return lowered[a.strip().lower()]
    return None


def load_csv(path: Path) -> list[Product]:
    # 買取スキャナーのCSVは UTF-8 / Shift_JIS 両方のケースがある
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            df = pd.read_csv(path, encoding=enc, dtype=str).fillna("")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Failed to decode CSV: {path}")

    jan_col = _pick(df, JAN_ALIASES)
    name_col = _pick(df, NAME_ALIASES)
    price_col = _pick(df, BUY_PRICE_ALIASES)
    cat_col = _pick(df, CATEGORY_ALIASES)
    asin_col = _pick(df, ASIN_ALIASES)

    if not (jan_col and price_col):
        raise ValueError(
            f"CSV {path.name} に JAN列/買取価格列が見つかりません。列: {list(df.columns)}"
        )

    products: list[Product] = []
    for _, row in df.iterrows():
        jan = str(row[jan_col]).strip()
        if not jan or not jan.isdigit():
            continue
        try:
            price = float(str(row[price_col]).replace(",", "").replace("円", "").strip() or 0)
        except ValueError:
            continue
        if price <= 0:
            continue
        products.append(
            Product(
                jan=jan,
                name=str(row[name_col]).strip() if name_col else "",
                buy_price=price,
                category=str(row[cat_col]).strip() if cat_col else None,
                asin=str(row[asin_col]).strip() if asin_col else None,
            )
        )
    log.info("Loaded %d products from %s", len(products), path.name)
    return products


def load_all(input_dir: Path) -> list[Product]:
    """input_dir 配下の最新CSVを読み込む。複数ある場合はマージ。"""
    files = sorted(glob.glob(str(input_dir / "*.csv")))
    if not files:
        log.warning("No CSV found in %s", input_dir)
        return []

    merged: dict[str, Product] = {}
    for f in files:
        for p in load_csv(Path(f)):
            # 同一JANは買取価格が高い方を採用
            existing = merged.get(p.jan)
            if existing is None or p.buy_price > existing.buy_price:
                merged[p.jan] = p
    log.info("Merged %d unique products from %d CSV(s)", len(merged), len(files))
    return list(merged.values())
