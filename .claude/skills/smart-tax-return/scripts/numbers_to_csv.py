#!/usr/bin/env python3
"""フォルダ内の .numbers を CSV に変換する。

スマート確定申告は Numbers 形式を受け付けない。Macで明細を開いて保存すると .numbers に
なってしまうため、提出前に CSV へ揃える必要がある。

    pip install numbers-parser --break-system-packages

元の .numbers は消さない。提出物の削除は取り返しがつかないので、
CSV を作ったうえで Drive 側では .numbers を「不要データ」へ移す運用にする。

出力名のルール:
    202604infinite TAKUYA.numbers            -> 202604infinite TAKUYA.csv
    PAYPAY6396_20260401-20260630.csv.numbers -> PAYPAY6396_20260401-20260630.csv
    （元が CSV だったものは .csv.numbers になるので二重拡張子を潰す）

使い方:
    python3 numbers_to_csv.py <フォルダ>            # 再帰的に変換
    python3 numbers_to_csv.py <フォルダ> --dry-run  # 変換せず対象だけ表示
"""

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

try:
    from numbers_parser import Document
except ImportError:
    sys.exit("numbers-parser が必要です:\n"
             "  pip install numbers-parser --break-system-packages")


def fmt(v):
    """セル値をCSV向けに整える。

    金額が 144800.0 のように .0 付きで出るのを嫌って int に落とす。
    日時はスマート確定申告側の他ファイルに合わせて YYYY/MM/DD 形式にする。
    """
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else str(v)
    if isinstance(v, dt.datetime):
        return v.strftime("%Y/%m/%d %H:%M:%S")
    if isinstance(v, dt.date):
        return v.strftime("%Y/%m/%d")
    return str(v)


def out_name(p: Path) -> Path:
    stem = p.name[: -len(".numbers")].rstrip()
    if stem.lower().endswith(".csv"):
        stem = stem[: -len(".csv")]
    return p.with_name(stem + ".csv")


def convert(p: Path):
    doc = Document(str(p))
    rows, tables = [], 0
    for sheet in doc.sheets:
        for table in sheet.tables:
            data = table.rows(values_only=True)
            if not data:
                continue
            if rows:
                rows.append([])  # 表が複数あるときの区切り
            rows.extend([fmt(c) for c in row] for row in data)
            tables += 1

    dest = out_name(p)
    # Excelで開いても日本語が化けないよう BOM 付きで書く
    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
    return dest, len(rows), tables


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="変換対象のフォルダ（再帰的に探す）")
    ap.add_argument("--dry-run", action="store_true", help="変換せず対象を表示するだけ")
    args = ap.parse_args()

    root = Path(args.folder)
    if not root.is_dir():
        sys.exit(f"フォルダが見つかりません: {root}")

    targets = sorted(root.rglob("*.numbers"))
    if not targets:
        sys.exit("変換対象の .numbers が見つかりません")

    print(f"{len(targets)} 件の .numbers を検出\n")
    done = skipped = failed = 0

    for p in targets:
        dest = out_name(p)
        rel = p.relative_to(root)

        # 元CSVが既にあるなら変換不要（Numbersで開いただけのもの）
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  skip  {rel}\n        -> 既に {dest.name} あり")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  (dry) {rel}\n        -> {dest.name}")
            done += 1
            continue

        try:
            d, nrows, ntables = convert(p)
            print(f"  OK    {rel}\n        -> {d.name}  ({nrows}行 / 表{ntables})")
            done += 1
        except Exception as e:
            print(f"  FAIL  {rel}: {e}")
            failed += 1

    print(f"\n変換 {done} 件 / スキップ {skipped} 件 / 失敗 {failed} 件")
    if not args.dry_run and done:
        print("\n元の .numbers は残しています。Drive側では「不要データ」へ移してください。")


if __name__ == "__main__":
    main()
