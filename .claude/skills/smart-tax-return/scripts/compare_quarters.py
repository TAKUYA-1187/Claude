#!/usr/bin/env python3
"""前四半期と今四半期のDrive棚卸しを突き合わせ、不足・重複・不整合を洗い出す。

入力は2つのJSON。フォルダのパスをキー、その中のファイル名リストを値にした辞書。
Driveをブラウザで列挙した結果をそのまま貼り付けて作る（scripts/drive_inventory.js 参照）。

    {
      "02.クレカ/ANA AMEX TAKUYA": ["2026-04ANA AMEX TAKUYA.pdf", "2026-05..."],
      "02.クレカ/三井住友Visa Infinite": [],
      "03.PayPay履歴": ["PAYPAY4218_20260401-20260630.csv", ...]
    }

使い方:
    python3 compare_quarters.py prev.json curr.json
    python3 compare_quarters.py prev.json curr.json --months 4 5 6
    python3 compare_quarters.py prev.json curr.json --json   # 機械可読で出す

月次の抜けを見るには --months で今四半期の対象月を指定する。
省略した場合はファイル名から自動推定する。
"""

import argparse
import json
import re
import sys
from collections import defaultdict

# 楽天カードのように「ファイル名の月 = 請求月 = 利用月+1」となるカード。
# 部分一致で判定する。
MONTH_OFFSET = {
    "楽天カード": 1,
    "enavi": 1,
}

# 提出物ではない指示ファイルを弾く
def is_instruction_file(name: str) -> bool:
    return name.startswith(".")


def normalize(name: str) -> str:
    """末尾の種別表記（"CSV" "PDF" "共有フォルダ" 等）を落として比較しやすくする。"""
    n = name.strip()
    for suffix in (
        " CSV", " PDF", " Text", " テキスト", " バイナリ", " Unknown",
        " iWork Numbers", " 共有フォルダ", " Shared folder",
        " Google ドキュメント", " Google Docs",
    ):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    return n.strip()


EN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# 20260401-20260630 や 202604-202606 のような期間表記
RANGE_RE = re.compile(r"20(\d{2})(\d{2})(?:\d{2})?\s*[-〜~]\s*20(\d{2})(\d{2})(?:\d{2})?")


def extract_months(name: str):
    """ファイル名から対象月を拾う。

    対応する書き方:
      202604 / 2026-04 / 20260401     … 単月
      202604-202606 / 20260401-20260630 … 期間（間の月も埋める）
      2026AprMonthlySummary            … 英語の月名

    期間表記を両端だけの2ヶ月と誤読すると、間の月が「抜け」として誤検出されるので
    先に期間を処理して該当月をすべて展開する。
    """
    months = set()
    consumed = name

    for m in RANGE_RE.finditer(name):
        y1, m1, y2, m2 = (int(m.group(1)), int(m.group(2)),
                          int(m.group(3)), int(m.group(4)))
        if not (1 <= m1 <= 12 and 1 <= m2 <= 12):
            continue
        start, end = y1 * 12 + m1, y2 * 12 + m2
        if start <= end and end - start < 24:  # 常識的な範囲だけ展開する
            for t in range(start, end + 1):
                months.add((t - 1) % 12 + 1)
        consumed = consumed.replace(m.group(0), " ")

    for m in re.finditer(r"20(\d{2})[-_]?(\d{2})", consumed):
        mm = int(m.group(2))
        if 1 <= mm <= 12:
            months.add(mm)

    lowered = name.lower()
    for word, num in EN_MONTHS.items():
        if re.search(rf"\b{word}|20\d{{2}}{word}", lowered):
            months.add(num)

    return months


def offset_for(folder: str) -> int:
    for key, off in MONTH_OFFSET.items():
        if key in folder or key.lower() in folder.lower():
            return off
    return 0


def account_numbers(name: str):
    """口座番号・カード番号らしき数字列を拾う（重複検出用）。

    日付・年の並びを口座番号と誤認しないよう、先に潰してから探す。
    「2026」のような裸の年を口座番号扱いすると、同じフォルダの全ファイルが
    同一キーになって重複が大量に誤検出される。
    """
    cleaned = re.sub(r"20\d{6}", " ", name)              # 20260401
    cleaned = re.sub(r"20\d{4}", " ", cleaned)           # 202604
    cleaned = re.sub(r"\b(19|20)\d{2}\b", " ", cleaned)  # 裸の年
    return set(re.findall(r"\d{4,}", cleaned))


def shape_of(name: str) -> str:
    """数字と拡張子を落とした「型」。命名パターンが同じかどうかの判定に使う。

    2026AprMonthlySummary.pdf     -> aprmonthlysummary
    2026AprMonthlyTransaction.csv -> aprmonthlytransaction   （別物）
    PAYPAY9999_20260401-...numbers-> paypay
    PAYPAY079999_20260401-...csv  -> paypay                  （同型）

    同一月の CSV と PDF が両方必要なフォルダ（10.売上[Amazonセラー] など）を
    重複と誤判定しないために、拡張子ではなく命名の型で見る。
    """
    base = re.sub(r"\.[A-Za-z0-9]{1,10}$", "", name)
    base = re.sub(r"\d+", "", base)
    return re.sub(r"[\s_\-()（）＿.]+", "", base).lower()


def load(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for folder, files in raw.items():
        out[folder.strip()] = [
            normalize(f) for f in files if not is_instruction_file(normalize(f))
        ]
    return out


def guess_months(inv):
    counts = defaultdict(int)
    for files in inv.values():
        for f in files:
            for m in extract_months(f):
                counts[m] += 1
    if not counts:
        return []
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
    return sorted(m for m, _ in top)


def analyze(prev, curr, target_months):
    findings = {
        "empty_now": [],        # 前はあったのに今回空
        "missing_folder": [],   # 前はあったフォルダが今回無い
        "new_folder": [],       # 今回増えたフォルダ
        "month_gaps": [],       # 月次の抜け
        "cross_quarter_dupes": [],  # 前四半期と同名のファイル
        "intra_folder_dupes": [],   # 同フォルダ内で同一口座・同一月が重複
    }

    prev_files = {f for files in prev.values() for f in files}

    for folder in sorted(set(prev) | set(curr)):
        p = prev.get(folder)
        c = curr.get(folder)

        if p is not None and c is None:
            findings["missing_folder"].append({"folder": folder, "prev_count": len(p)})
            continue
        if p is None and c is not None:
            findings["new_folder"].append({"folder": folder, "count": len(c)})

        if c is None:
            continue

        if not c and p:
            findings["empty_now"].append({"folder": folder, "prev_files": p})
            continue
        if not c:
            continue

        # 期間跨ぎ重複
        for f in c:
            if f in prev_files:
                findings["cross_quarter_dupes"].append({"folder": folder, "file": f})

        # 月次の抜け（対象月が分かっていて、かつファイル名に月が入っている場合のみ）
        if target_months:
            off = offset_for(folder)
            expected = {((m - 1 + off) % 12) + 1 for m in target_months}
            present = set()
            for f in c:
                present |= extract_months(f)
            if present:  # 月が読めないフォルダは判定しない
                gaps = sorted(expected - present)
                if gaps:
                    findings["month_gaps"].append({
                        "folder": folder,
                        "present": sorted(present),
                        "missing": gaps,
                        "offset_applied": off,
                    })

        # --- フォルダ内重複 ---------------------------------------------
        # 2つの経路で見る。片方だけだと取りこぼす／誤検出するため。

        def add_dupe(files, reason):
            uniq = sorted(set(files))
            if len(uniq) < 2:
                return
            entry = {"folder": folder, "files": uniq, "reason": reason}
            if entry not in findings["intra_folder_dupes"]:
                findings["intra_folder_dupes"].append(entry)

        # ここは「見逃し」より「誤検出」の方が有害。
        # 同一月の PDF と CSV を両方出すのは正常な運用（MARRIOTT AMEX、10.売上Amazon など）
        # なので、形式違いを一律に重複扱いすると毎回ノイズが出て信用されなくなる。
        # そのため、確度の高い2つの signal に絞る。

        # (a) 口座番号の下4桁が一致するのに表記が違う。
        #     91079999 が "9999" と "079999" で別ファイルになっていた例がある。
        by_tail = defaultdict(set)
        for f in c:
            for num in account_numbers(f):
                by_tail[num[-4:]].add((num, f))
        for _tail, pairs in by_tail.items():
            if len({num for num, _ in pairs}) > 1:
                add_dupe([f for _, f in pairs], "同一口座の表記ゆれ（下4桁一致）")

        # (b) コピーの痕跡が名前に残っている。
        #     「のコピー」「(1)」「copy」は、DLし直した／二重に入れた強い兆候。
        for f in c:
            if re.search(r"のコピー|\(\d+\)\s*\.|[ _-]copy\b", f, re.IGNORECASE):
                stem = re.sub(r"のコピー|\(\d+\)|[ _-]copy", "", f, flags=re.IGNORECASE)
                siblings = [
                    g for g in c
                    if g != f and shape_of(g) == shape_of(stem)
                    and extract_months(g) == extract_months(f)
                ]
                if siblings:
                    add_dupe([f] + siblings, "コピーとみられるファイル名")

    return findings


def render(findings, target_months):
    out = []
    a = out.append

    a("# 四半期比較レポート")
    if target_months:
        a(f"\n対象月: {', '.join(str(m) + '月' for m in target_months)}")

    a("\n## 🔴 至急対応が必要（空のまま）\n")
    if findings["empty_now"]:
        a("| フォルダ | 前四半期の中身 |")
        a("|---|---|")
        for e in findings["empty_now"]:
            sample = "、".join(e["prev_files"][:3])
            more = f" ほか{len(e['prev_files']) - 3}件" if len(e["prev_files"]) > 3 else ""
            a(f"| {e['folder']} | {sample}{more} |")
    else:
        a("なし")

    if findings["missing_folder"]:
        a("\n**前四半期にあったフォルダが今回存在しない:**\n")
        for e in findings["missing_folder"]:
            a(f"- {e['folder']}（前四半期は{e['prev_count']}件）")

    a("\n## 🟡 月次の抜け\n")
    if findings["month_gaps"]:
        a("| フォルダ | 今ある月 | 足りない月 |")
        a("|---|---|---|")
        for e in findings["month_gaps"]:
            note = "（請求月ベース）" if e["offset_applied"] else ""
            a(f"| {e['folder']}{note} | {'、'.join(f'{m}月' for m in e['present'])} "
              f"| **{'、'.join(f'{m}月' for m in e['missing'])}** |")
    else:
        a("なし")

    a("\n## ⚠️ 要確認（重複・不整合）\n")
    n = 0
    for e in findings["cross_quarter_dupes"]:
        n += 1
        a(f"{n}. **期間跨ぎ重複** — `{e['file']}` が前四半期と `{e['folder']}` の両方にある")
    for e in findings["intra_folder_dupes"]:
        n += 1
        a(f"{n}. **フォルダ内重複の疑い** — `{e['folder']}` に "
          f"{'、'.join(f'`{f}`' for f in e['files'])}（{e['reason']}）")
    if findings["new_folder"]:
        n += 1
        names = "、".join(e["folder"] for e in findings["new_folder"])
        a(f"{n}. **今四半期で増えたフォルダ** — {names}"
          f"（チェックリストに載っているか確認）")
    if n == 0:
        a("なし")

    a("\n---")
    a("\n> このスクリプトは口座番号・カード番号の変更、請求月と利用月のずれ、")
    a("> フォルダ構造の差までは判定できません。SKILL.md の「目視で確認するもの」も併せて確認してください。")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prev", help="前四半期の棚卸しJSON")
    ap.add_argument("curr", help="今四半期の棚卸しJSON")
    ap.add_argument("--months", nargs="*", type=int,
                    help="今四半期の対象月（例: --months 4 5 6）")
    ap.add_argument("--json", action="store_true", help="Markdownでなく生JSONで出力")
    args = ap.parse_args()

    prev = load(args.prev)
    curr = load(args.curr)

    months = args.months if args.months else guess_months(curr)
    findings = analyze(prev, curr, months)

    if args.json:
        json.dump({"target_months": months, "findings": findings},
                  sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(render(findings, months))


if __name__ == "__main__":
    main()
