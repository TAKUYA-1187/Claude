#!/usr/bin/env python3
"""提出フォルダ内の重複を「中身」で検出する。

会計士から「ファイルが重複しているようです」と指摘されたときに使う。
ファイル名だけで判断すると、下4桁が同じ別口座を誤って重複扱いしてしまう
（PAYPAY9999＝TAKUYA559999 と PAYPAY079999＝TAKUYA91079999 は別物だった。数字は例）。
逆に、名前が全然違うのに中身が同じこともある（ANA PASMO と JCB の明細が一致した例）。

だから中身を見る。検出するのは4種類:

  1. 完全一致        本文が1バイトも違わない
  2. 取引番号の重なり 別ファイルなのに同じ取引が入っている（集計の二重計上になる）
  3. 同一資料の別形式 .csv と .numbers など、同じ内容を2形式で提出
  4. コピーの痕跡    「のコピー」「(1)」など

使い方:
    python3 check_duplicates.py <フォルダ>
    python3 check_duplicates.py <フォルダ> --ext csv    # 対象拡張子を絞る

PDFも対象にしたい場合は --pdf を付ける（pypdf が必要。本文テキストで比較する）。
"""

import argparse
import csv
import hashlib
import itertools
import re
import sys
from collections import defaultdict
from pathlib import Path

COPY_MARKER = re.compile(r"のコピー|\(\d+\)\s*\.|[ _-]copy\b", re.IGNORECASE)


def shape_of(name: str) -> str:
    """数字と拡張子を落とした「型」。命名パターンが同じかを見る。"""
    base = re.sub(r"\.[A-Za-z0-9]{1,10}$", "", name)
    base = re.sub(r"\d+", "", base)
    return re.sub(r"[\s_\-()（）＿.]+", "", base).lower()


def read_csv_body(p: Path):
    """ヘッダを除く本文を行のタプルで返す。"""
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(p, encoding=enc, newline="") as f:
                rows = list(csv.reader(f))
            return [tuple(r) for r in rows[1:]], (rows[0] if rows else [])
        except UnicodeDecodeError:
            continue
    return None, []


def read_pdf_text(p: Path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        t = "".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
        return re.sub(r"\s+", "", t)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--ext", default="csv", help="対象拡張子（既定: csv）")
    ap.add_argument("--pdf", action="store_true", help="PDFも本文テキストで比較する")
    args = ap.parse_args()

    root = Path(args.folder)
    if not root.is_dir():
        sys.exit(f"フォルダが見つかりません: {root}")

    files = sorted(p for p in root.rglob(f"*.{args.ext}") if p.is_file())
    pdfs = sorted(root.rglob("*.pdf")) if args.pdf else []

    if not files and not pdfs:
        sys.exit("対象ファイルがありません")

    bodies, txcols, headers = {}, {}, {}
    for p in files:
        body, header = read_csv_body(p)
        if body is None:
            print(f"  ! 読めません: {p.name}")
            continue
        bodies[p.name] = body
        headers[p.name] = header
        # 取引番号らしき列を拾う
        for col in ("取引番号", "取引ID", "注文番号", "ご請求番号"):
            if col in header:
                i = header.index(col)
                txcols[p.name] = {r[i] for r in body
                                  if len(r) > i and r[i] not in ("", "-")}
                break

    for p in pdfs:
        t = read_pdf_text(p)
        if t:
            bodies[p.name] = [(t,)]

    findings = []

    # 1. 完全一致
    by_hash = defaultdict(list)
    for name, body in bodies.items():
        by_hash[hashlib.md5(repr(body).encode()).hexdigest()].append(name)

    identical = set()  # 完全一致と判明したペア（取引番号での再報告を抑える）
    for names in by_hash.values():
        if len(names) > 1:
            findings.append(("完全一致（中身が同一）", sorted(names)))
            identical.update(itertools.combinations(sorted(names), 2))

    # 2. 取引番号の重なり
    #    完全一致のペアは 1 で報告済みなので出さない。
    #    ここで拾いたいのは「別ファイルなのに一部の取引が被っている」ケース。
    for a, b in itertools.combinations(sorted(txcols), 2):
        if tuple(sorted((a, b))) in identical:
            continue
        ov = txcols[a] & txcols[b]
        if ov:
            share = len(ov) / min(len(txcols[a]), len(txcols[b]))
            note = "ほぼ同一" if share > 0.8 else "一部が重複"
            findings.append((
                f"取引番号が {len(ov)} 件重複（{note}・二重計上のおそれ）", [a, b]))

    # 3. 同一資料の別形式（型と行数が一致し拡張子だけ違う）
    by_shape = defaultdict(list)
    for name, body in bodies.items():
        by_shape[(shape_of(name), len(body))].append(name)
    for (_s, _n), names in by_shape.items():
        exts = {Path(n).suffix.lower() for n in names}
        if len(names) > 1 and len(exts) > 1:
            findings.append(("同じ資料を別形式で提出", sorted(names)))

    # 4. コピーの痕跡
    for name in sorted(bodies):
        if COPY_MARKER.search(name):
            stem = COPY_MARKER.sub(".", name)
            sib = [n for n in bodies
                   if n != name and shape_of(n) == shape_of(stem)]
            if sib:
                findings.append(("コピーとみられる名前", sorted([name] + sib)))

    # 重複した指摘を潰す
    seen, uniq = set(), []
    for reason, names in findings:
        key = (reason, tuple(names))
        if key not in seen:
            seen.add(key)
            uniq.append((reason, names))

    print(f"対象 {len(bodies)} ファイル\n")
    if not uniq:
        print("重複は見つかりませんでした。")
    else:
        print(f"=== 要確認 {len(uniq)} 件 ===\n")
        for i, (reason, names) in enumerate(uniq, 1):
            print(f"{i}. {reason}")
            for n in names:
                print(f"     {n}")
            print()

    print("---")
    print("下4桁が同じでも別口座のことがあります。提出状況報告シートの")
    print("口座一覧と突き合わせてから判断してください。")
    print("重複と確定したものは削除せず「不要データ」フォルダへ移します。")


if __name__ == "__main__":
    main()
