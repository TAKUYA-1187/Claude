"""買取スキャナー『全データCSV保存』で出力したCSVを読み込む。

買取スキャナーのCSVは店舗ごとに買取価格列が並ぶ構造（例: 「買取商店」「ウィキ」「ブックオフ」…）。
`ENABLED_SHOPS` に指定された店舗の列だけ見て、**そのいずれかで買取価格が付いている商品** に絞り込む。
買取価格は指定店舗中の最高値を採用し、どの店舗が付けたかを `buy_shop` に記録する。
"""
from __future__ import annotations

import glob
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

log = logging.getLogger(__name__)


JAN_ALIASES = ["JAN", "JANコード", "jan", "jan_code", "barcode", "バーコード"]
NAME_ALIASES = ["商品名", "title", "name", "product_name", "タイトル"]
CATEGORY_ALIASES = ["カテゴリ", "category", "ジャンル"]
ASIN_ALIASES = ["ASIN", "asin"]


@dataclass
class Product:
    jan: str
    name: str
    buy_price: float
    buy_shop: str  # 最高値を付けた店舗名
    category: str | None = None
    asin: str | None = None


def _pick(df: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    for a in aliases:
        if a in df.columns:
            return a
    lowered = {c.strip().lower(): c for c in df.columns}
    for a in aliases:
        if a.strip().lower() in lowered:
            return lowered[a.strip().lower()]
    return None


PRICE_HINTS = ("買取価格", "価格")


def _shop_aliases(shop: str) -> list[str]:
    """買取スキャナーは店名を略すことがある（例: 買取商店 → 「商店_買取価格」）。"""
    aliases = [shop]
    if shop.startswith("買取") and len(shop) > 2:
        aliases.append(shop[2:])
    return aliases


def _find_shop_columns(columns: list[str], shop_names: list[str]) -> dict[str, list[str]]:
    """各店舗の買取価格列を探す。

    買取スキャナーの全データCSVは「店名_商品名 / 店名_買取価格 / 店名_取得日時 / 店名_メインカテゴリ」
    の形なので、店名の列のうち「価格」を含む列だけを価格として使う（商品名中の数字や取得日時を
    価格と誤読しないため）。価格列がなければ、店名そのものの列（例: 「ウィキ」）を使う。
    """
    result: dict[str, list[str]] = {}
    for shop in shop_names:
        aliases = _shop_aliases(shop)
        matching = []
        for col in columns:
            c = col.strip()
            if "_" in c:
                if c.split("_", 1)[0] in aliases:
                    matching.append(col)
            elif any(a in c for a in aliases):
                matching.append(col)
        priced = [col for col in matching if any(h in col for h in PRICE_HINTS)]
        result[shop] = priced or [col for col in matching if col.strip() in aliases]
    return result


def _shop_name_column(columns: list[str], shop_cols: list[str]) -> str | None:
    """「店名_買取価格」に対応する「店名_商品名」列。"""
    for col in shop_cols:
        prefix = col.strip().split("_", 1)[0]
        candidate = f"{prefix}_商品名"
        if candidate in columns:
            return candidate
    return None


_NUM_RE = re.compile(r"-?\d+")


def _to_price(val: object) -> float | None:
    if val is None:
        return None
    s = str(val).replace(",", "").replace("円", "").strip()
    if not s or s in {"-", "ー", "―", "nan", "None", "0"}:
        return None
    m = _NUM_RE.search(s)
    if not m:
        return None
    try:
        p = float(m.group())
    except ValueError:
        return None
    return p if p > 0 else None


def load_csv(path: Path, shop_names: list[str]) -> list[Product]:
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            df = pd.read_csv(path, encoding=enc, dtype=str).fillna("")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Failed to decode CSV: {path}")

    log.info("CSV %s: %d rows, columns=%s", path.name, len(df), list(df.columns))

    jan_col = _pick(df, JAN_ALIASES)
    name_col = _pick(df, NAME_ALIASES)
    cat_col = _pick(df, CATEGORY_ALIASES)
    asin_col = _pick(df, ASIN_ALIASES)

    if not jan_col:
        raise ValueError(f"CSV {path.name} に JAN列が見つかりません。列: {list(df.columns)}")

    shop_cols = _find_shop_columns(list(df.columns), shop_names)
    matched = {s: cols for s, cols in shop_cols.items() if cols}
    if not matched:
        raise ValueError(
            f"CSV {path.name} に対象店舗 {shop_names} の列が見つかりません。列: {list(df.columns)}"
        )
    log.info(
        "Shop columns: %s",
        ", ".join(f"{s}={cols}" for s, cols in matched.items()),
    )
    shop_name_cols = {s: _shop_name_column(list(df.columns), cols) for s, cols in matched.items()}

    products: list[Product] = []
    for _, row in df.iterrows():
        jan = str(row[jan_col]).strip()
        if not jan or not jan.isdigit():
            continue

        best_shop: str | None = None
        best_price: float = 0.0
        best_name = ""
        for shop, cols in matched.items():
            for col in cols:
                p = _to_price(row[col])
                if p is not None and p > best_price:
                    best_price = p
                    best_shop = shop
                    shop_name_col = shop_name_cols.get(shop)
                    best_name = str(row[shop_name_col]).strip() if shop_name_col else ""
        if best_shop is None:
            continue  # 対象店舗いずれにも買取価格がない → スキップ

        products.append(
            Product(
                jan=jan,
                name=str(row[name_col]).strip() if name_col else best_name,
                buy_price=best_price,
                buy_shop=best_shop,
                category=str(row[cat_col]).strip() if cat_col else None,
                asin=str(row[asin_col]).strip() if asin_col else None,
            )
        )
    log.info("Loaded %d products from %s (after shop filter)", len(products), path.name)
    return products


def load_all(input_dir: Path, shop_names: list[str]) -> list[Product]:
    files = sorted(glob.glob(str(input_dir / "*.csv")))
    if not files:
        log.warning("No CSV found in %s", input_dir)
        return []

    merged: dict[str, Product] = {}
    for f in files:
        try:
            loaded = load_csv(Path(f), shop_names)
        except Exception as e:
            log.error("CSV %s の読み込みに失敗したためスキップ: %s", Path(f).name, e)
            continue
        for p in loaded:
            existing = merged.get(p.jan)
            if existing is None or p.buy_price > existing.buy_price:
                merged[p.jan] = p
    log.info("Merged %d unique products from %d CSV(s)", len(merged), len(files))
    return list(merged.values())
