"""Apple Numbers (.numbers) を CSV に変換する。

iPhone / Mac で買取スキャナーの CSV を開いて保存すると Numbers 形式になることがあるため
（2026-09 時点の OneDrive 共有フォルダも .numbers 1件だった）、data/input の .numbers を
csv_loader が読める CSV に変換する。JAN 列を含む表だけを対象にし、見出し行は先頭数行から探す。
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path

from .csv_loader import JAN_ALIASES

log = logging.getLogger(__name__)

HEADER_SCAN_ROWS = 5


def _cell(value: object) -> str:
    if value is None:
        return ""
    # 数値セルは float で返るため、JAN や価格の「.0」を落とす
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def convert_numbers_file(path: Path, dest_dir: Path, prefix: str) -> list[Path]:
    from numbers_parser import Document

    jan_aliases = {a.lower() for a in JAN_ALIASES}
    written: list[Path] = []
    for si, sheet in enumerate(Document(str(path)).sheets, 1):
        for ti, table in enumerate(sheet.tables, 1):
            rows = [[_cell(v) for v in row] for row in table.rows(values_only=True)]
            rows = [r for r in rows if any(r)]
            header_idx = next(
                (i for i, r in enumerate(rows[:HEADER_SCAN_ROWS]) if any(c.lower() in jan_aliases for c in r)),
                None,
            )
            if header_idx is None:
                log.info("Numbers sheet %d / table %d: JAN列がないためスキップ", si, ti)
                continue
            header = rows[header_idx]
            width = max(i + 1 for i, c in enumerate(header) if c)
            dest = dest_dir / f"{prefix}_s{si}_t{ti}.csv"
            with dest.open("w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerows(r[:width] for r in rows[header_idx:])
            log.info("Numbers sheet %d / table %d -> CSV (%d rows)", si, ti, len(rows) - header_idx - 1)
            written.append(dest)
    return written


def convert_all(input_dir: Path) -> list[Path]:
    """input_dir の .numbers をすべて CSV に変換し、作った CSV のパスを返す。"""
    written: list[Path] = []
    for i, path in enumerate(sorted(input_dir.glob("*.numbers")), 1):
        try:
            written += convert_numbers_file(path, input_dir, prefix=f"numbers_{i}")
        except Exception as e:
            log.error("Numbersファイル %d の変換に失敗: %s: %s", i, type(e).__name__, e)
    return written
