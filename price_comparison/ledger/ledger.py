#!/usr/bin/env python3
"""
せどり商品管理台帳 — 重複排除・価格履歴・利益再計算ツール

使い方:
  python3 ledger.py merge --ledger-dir ./data --input 新規調査.csv
  python3 ledger.py check --ledger-dir ./data      # 台帳の整合性チェックのみ

ファイル構成（--ledger-dir 内）:
  master.csv     … 1商品1行。最新の条件を保持（同一JAN/ASIN/型番は統合）
  history.csv    … 追記専用。調査ごとの価格・条件の変化を保存（値に変化がない再調査は記録しない）
  excluded.csv   … 除外リスト。ここに載った商品は master に再登録しない（再提案防止）

原則:
  - 入力にない数値は推測で埋めない（空欄のまま、判定は「未確認」）
  - 利益はスクリプトが必ず再計算する（入力側の利益値は信用しない）
  - 抽出基準を満たさない商品も削除しない。判定列で区別する
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

# ---- 台帳の列（指示書 第9章に準拠） -------------------------------------
MASTER_COLS = [
    "商品キー", "調査日時", "商品名", "JANコード", "ASIN", "型番",
    "仕入先", "仕入URL", "仕入価格", "クーポン", "獲得ポイント", "仕入送料",
    "販売先", "販売URL", "販売価格", "買取価格",
    "販売手数料", "発送費用", "その他経費",
    "現金利益", "ポイント込み利益", "利益率",
    "推定月間販売数", "在庫状況", "出品制限", "価格変動リスク",
    "推奨仕入数量", "総合評価", "検証状況", "仕入判断",
    "基準判定", "基準未達・未確認の理由", "情報源", "初回登録日時", "更新回数",
]
# 履歴に残す「変化を追う」列
HISTORY_VALUE_COLS = [
    "仕入先", "仕入URL", "仕入価格", "クーポン", "獲得ポイント", "仕入送料",
    "販売先", "販売価格", "買取価格", "販売手数料", "発送費用", "その他経費",
    "推定月間販売数", "在庫状況", "出品制限",
]
HISTORY_COLS = ["商品キー", "調査日時", "商品名"] + HISTORY_VALUE_COLS + [
    "現金利益", "ポイント込み利益", "利益率", "基準判定", "変化した項目", "行ハッシュ",
]
EXCLUDED_COLS = ["商品キー", "JANコード", "ASIN", "型番", "商品名", "除外理由", "除外日", "判断者"]

# ---- 抽出基準（指示書 第5章）。緩めないこと --------------------------------
MIN_PROFIT_YEN = 500
MIN_MARGIN_PCT = 3.0
MIN_MONTHLY_SALES = 50
REQUIRED_STOCK = "在庫あり"


# ---- 正規化・検証 ---------------------------------------------------------
def norm(s: str | None) -> str:
    if s is None:
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip()


def norm_code(s: str | None) -> str:
    """型番・ASIN用：全角→半角、大文字化、空白とハイフン類を除去"""
    s = norm(s).upper()
    return re.sub(r"[\s\-‐－―ー_/]", "", s)


def valid_jan(jan: str) -> bool:
    """JAN-13 / JAN-8 のチェックデジット検証"""
    if not re.fullmatch(r"\d{8}|\d{13}", jan):
        return False
    digits = [int(c) for c in jan]
    body, check = digits[:-1], digits[-1]
    # 右端（チェックデジットの直前）から奇数位置に重み3
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def valid_asin(asin: str) -> bool:
    return bool(re.fullmatch(r"B0[0-9A-Z]{8}|\d{9}[\dX]", asin))


def to_yen(s: str | None) -> float | None:
    """「1,980円」「¥1980」等を数値に。空欄・不明は None（0にしない）"""
    s = norm(s)
    if s in ("", "未確認", "不明", "-", "—"):
        return None
    s = re.sub(r"[円¥,\s]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def fmt_num(x: float | None) -> str:
    if x is None:
        return ""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.1f}"


# ---- 利益計算（指示書 第6章・連携文書 共通式） ------------------------------
def calc_profit(row: dict) -> tuple[float | None, float | None, float | None, list[str]]:
    """
    現金利益 = 販売価格 − 仕入総額（仕入価格 − クーポン + 仕入送料）− 販売関連経費
    ポイント込み利益 = 現金利益 + 獲得ポイント
    利益率 = 現金利益 ÷ 販売価格 × 100
    販売価格の代わりに買取価格がある場合（買取差益）は買取価格を使う。
    必須の数値が欠けていれば None を返し、欠けている項目を列挙する。
    """
    missing = []
    sell = to_yen(row.get("販売価格"))
    if sell is None:
        sell = to_yen(row.get("買取価格"))
    if sell is None:
        missing.append("販売価格/買取価格")
    buy = to_yen(row.get("仕入価格"))
    if buy is None:
        missing.append("仕入価格")
    # 経費類：空欄は「未確認」扱い。0円が確定なら入力側で 0 と明記する運用
    fee_cols = ["仕入送料", "販売手数料", "発送費用", "その他経費"]
    fees = {}
    for c in fee_cols:
        v = to_yen(row.get(c))
        if v is None:
            missing.append(c)
        fees[c] = v
    coupon = to_yen(row.get("クーポン")) or 0.0
    point = to_yen(row.get("獲得ポイント")) or 0.0

    if missing:
        return None, None, None, missing
    cash = sell - (buy - coupon + fees["仕入送料"]) - (fees["販売手数料"] + fees["発送費用"] + fees["その他経費"])
    with_point = cash + point
    margin = cash / sell * 100 if sell else None
    return cash, with_point, margin, []


def judge(row: dict, cash, margin, missing: list[str]) -> tuple[str, str]:
    """基準判定: 合格 / 不合格 / 未確認（暫定）"""
    reasons_fail, reasons_unknown = [], []
    if missing:
        reasons_unknown.append("未入力: " + "・".join(missing))
    else:
        if cash < MIN_PROFIT_YEN:
            reasons_fail.append(f"現金利益{fmt_num(cash)}円（基準{MIN_PROFIT_YEN}円に{fmt_num(MIN_PROFIT_YEN - cash)}円不足）")
        if margin is not None and margin < MIN_MARGIN_PCT:
            reasons_fail.append(f"利益率{margin:.1f}%（基準{MIN_MARGIN_PCT}%）")

    is_kaitori = to_yen(row.get("販売価格")) is None and to_yen(row.get("買取価格")) is not None
    if not is_kaitori:  # 月間販売数はAmazon販売のみの基準
        sales = to_yen(row.get("推定月間販売数"))
        if sales is None:
            reasons_unknown.append("推定月間販売数（Keepa）")
        elif sales < MIN_MONTHLY_SALES:
            reasons_fail.append(f"月間販売数{fmt_num(sales)}個（基準{MIN_MONTHLY_SALES}個）")

    if norm(row.get("在庫状況")) != REQUIRED_STOCK:
        (reasons_fail if norm(row.get("在庫状況")) == "在庫なし" else reasons_unknown).append("在庫確認")
    if not norm(row.get("JANコード")):
        reasons_unknown.append("JAN")
    if not is_kaitori and not norm(row.get("ASIN")):
        reasons_unknown.append("ASIN")
    if not is_kaitori and norm(row.get("出品制限")) in ("", "要確認", "未確認"):
        reasons_unknown.append("出品制限")

    if reasons_fail:
        return "不合格", " / ".join(reasons_fail + (["未確認: " + "・".join(reasons_unknown)] if reasons_unknown else []))
    if reasons_unknown:
        return "未確認（暫定）", "未確認: " + "・".join(reasons_unknown)
    return "合格", ""


# ---- 同一商品の特定 ----------------------------------------------------------
def identity_keys(row: dict) -> list[str]:
    keys = []
    jan = norm_code(row.get("JANコード"))
    asin = norm_code(row.get("ASIN"))
    model = norm_code(row.get("型番"))
    if jan:
        keys.append("JAN:" + jan)
    if asin:
        keys.append("ASIN:" + asin)
    if model:
        keys.append("MODEL:" + model)
    return keys


def primary_key(row: dict) -> str:
    """商品キー：JAN > ASIN > 型番 の優先順"""
    ks = identity_keys(row)
    return ks[0] if ks else ""


def row_hash(row: dict) -> str:
    payload = "|".join(norm(row.get(c)) for c in ["商品キー", "調査日時"] + HISTORY_VALUE_COLS)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


# ---- 入出力 ---------------------------------------------------------------
def read_csv(path: str, cols: list[str]) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{c: (r.get(c) or "") for c in cols} for r in csv.DictReader(f)]


def write_csv(path: str, cols: list[str], rows: list[dict]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)  # 途中で落ちても既存台帳を壊さない


# ---- メイン処理 -------------------------------------------------------------
def validate_row(row: dict) -> list[str]:
    errs = []
    jan = norm_code(row.get("JANコード"))
    if jan and not valid_jan(jan):
        errs.append(f"JAN不正({jan})")
    asin = norm_code(row.get("ASIN"))
    if asin and not valid_asin(asin):
        errs.append(f"ASIN不正({asin})")
    if not identity_keys(row):
        errs.append("JAN・ASIN・型番がすべて空")
    if not norm(row.get("調査日時")):
        errs.append("調査日時が空")
    return errs


def merge(ledger_dir: str, input_path: str, now: datetime | None = None) -> dict:
    now = now or datetime.now(JST)
    os.makedirs(ledger_dir, exist_ok=True)
    mpath, hpath, xpath = (os.path.join(ledger_dir, n) for n in ("master.csv", "history.csv", "excluded.csv"))
    master = read_csv(mpath, MASTER_COLS)
    history = read_csv(hpath, HISTORY_COLS)
    excluded = read_csv(xpath, EXCLUDED_COLS)
    incoming = read_csv(input_path, MASTER_COLS)

    # 既存の識別キー → master行 の索引（JAN/ASIN/型番いずれかが一致すれば同一商品）
    index: dict[str, dict] = {}
    for m in master:
        for k in identity_keys(m):
            index[k] = m
    excluded_keys = set()
    for x in excluded:
        excluded_keys.update(identity_keys(x))
    seen_hashes = {h["行ハッシュ"] for h in history}

    report = {"added": [], "updated": [], "unchanged": [], "skipped_excluded": [], "rejected": [], "conflicts": []}

    # 調査日時の古い順に処理（同一バッチ内の重複も時系列で履歴化）
    incoming.sort(key=lambda r: norm(r.get("調査日時")))
    for row in incoming:
        name = norm(row.get("商品名")) or "(商品名なし)"
        errs = validate_row(row)
        if errs:
            report["rejected"].append(f"{name}: " + "、".join(errs))
            continue
        keys = identity_keys(row)
        if any(k in excluded_keys for k in keys):
            report["skipped_excluded"].append(name)
            continue

        hits = {id(index[k]): index[k] for k in keys if k in index}
        if len(hits) > 1:
            # 例: JANは商品Aと一致、ASINは商品Bと一致 → 自動統合せず人の確認へ
            report["conflicts"].append(f"{name}: 複数の既存商品に一致（" + "、".join(m["商品キー"] for m in hits.values()) + "）")
            continue
        existing = next(iter(hits.values()), None)

        cash, wp, margin, missing = calc_profit(row)
        verdict, reason = judge(row, cash, margin, missing)
        row["現金利益"], row["ポイント込み利益"] = fmt_num(cash), fmt_num(wp)
        row["利益率"] = f"{margin:.1f}" if margin is not None else ""
        row["基準判定"], row["基準未達・未確認の理由"] = verdict, reason

        if existing is None:
            row["商品キー"] = primary_key(row)
            row["初回登録日時"] = norm(row.get("調査日時"))
            row["更新回数"] = "0"
            row.setdefault("検証状況", "")
            row["検証状況"] = norm(row.get("検証状況")) or "未検証候補"
            master.append(row)
            for k in keys:
                index[k] = row
            changed = ["新規"]
            report["added"].append(name)
        else:
            # 型番違い等の衝突：JAN同一でも型番が異なれば保留（色・容量違いの取り違え防止）
            mismatch = next((col for col in ("JANコード", "ASIN", "型番")
                             if norm_code(existing.get(col)) and norm_code(row.get(col))
                             and norm_code(existing.get(col)) != norm_code(row.get(col))), None)
            if mismatch:
                report["conflicts"].append(
                    f"{name}: {mismatch}が既存と不一致（既存{norm_code(existing.get(mismatch))} / "
                    f"新規{norm_code(row.get(mismatch))}）→ 統合は保留")
                continue
            changed = [c for c in HISTORY_VALUE_COLS if norm(row.get(c)) and norm(row.get(c)) != norm(existing.get(c))]
            if not changed:
                existing["調査日時"] = norm(row.get("調査日時"))  # 最終確認日時のみ更新
                report["unchanged"].append(name)
                continue
            # 入力で空欄の項目は既存値を残す（空欄で上書きしない）
            for c in MASTER_COLS:
                v = norm(row.get(c))
                if v and c not in ("商品キー", "初回登録日時", "更新回数", "現金利益", "ポイント込み利益",
                                   "利益率", "基準判定", "基準未達・未確認の理由"):
                    existing[c] = v
            cash, wp, margin, missing = calc_profit(existing)
            verdict, reason = judge(existing, cash, margin, missing)
            existing["現金利益"], existing["ポイント込み利益"] = fmt_num(cash), fmt_num(wp)
            existing["利益率"] = f"{margin:.1f}" if margin is not None else ""
            existing["基準判定"], existing["基準未達・未確認の理由"] = verdict, reason
            existing["更新回数"] = str(int(existing.get("更新回数") or 0) + 1)
            row = existing
            report["updated"].append(f"{name}（{'・'.join(changed)}）")

        h = {c: norm(row.get(c)) for c in HISTORY_COLS}
        h["変化した項目"] = "・".join(changed)
        h["行ハッシュ"] = row_hash(row)
        if h["行ハッシュ"] not in seen_hashes:
            history.append(h)
            seen_hashes.add(h["行ハッシュ"])

    master.sort(key=lambda r: ({"合格": 0, "未確認（暫定）": 1, "不合格": 2}.get(r.get("基準判定"), 3),
                               -(to_yen(r.get("現金利益")) or -1e9)))
    write_csv(mpath, MASTER_COLS, master)
    write_csv(hpath, HISTORY_COLS, history)
    if not os.path.exists(xpath):
        write_csv(xpath, EXCLUDED_COLS, excluded)
    report["passed_total"] = sum(1 for m in master if m.get("基準判定") == "合格")
    return report


def print_report(r: dict) -> None:
    print(f"新規 {len(r['added'])}件 / 更新 {len(r['updated'])}件 / 変化なし {len(r['unchanged'])}件 / "
          f"除外リスト該当 {len(r['skipped_excluded'])}件 / 取込不可 {len(r['rejected'])}件 / 要確認 {len(r['conflicts'])}件")
    print(f"基準合格の累計: {r['passed_total']}件（5件で定例報告）")
    for label, key in [("更新", "updated"), ("除外リスト該当", "skipped_excluded"),
                       ("取込不可", "rejected"), ("要確認（自動統合せず）", "conflicts")]:
        for item in r[key]:
            print(f"  [{label}] {item}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="せどり商品管理台帳ツール")
    sub = p.add_subparsers(dest="cmd", required=True)
    pm = sub.add_parser("merge", help="新規調査CSVを台帳に統合")
    pm.add_argument("--ledger-dir", required=True)
    pm.add_argument("--input", required=True)
    pc = sub.add_parser("check", help="台帳の整合性チェック")
    pc.add_argument("--ledger-dir", required=True)
    a = p.parse_args(argv)

    if a.cmd == "merge":
        r = merge(a.ledger_dir, a.input)
        print_report(r)
        return 1 if r["rejected"] or r["conflicts"] else 0

    master = read_csv(os.path.join(a.ledger_dir, "master.csv"), MASTER_COLS)
    problems, seen = [], {}
    for m in master:
        for e in validate_row(m):
            problems.append(f"{m['商品名']}: {e}")
        for k in identity_keys(m):
            if k in seen and seen[k] is not m:
                problems.append(f"重複: {k}（{seen[k]['商品名']} と {m['商品名']}）")
            seen[k] = m
    print("問題なし" if not problems else "\n".join(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
