#!/usr/bin/env python3
"""
朝レポート（買取商店×Yahoo!）の出力CSVを商品管理台帳へ取り込む

  python3 import_kaitori_report.py \
      --report ../data/output/kaitorishouten_all_latest.csv \
      --ledger-dir ../ledger_data \
      [--max-age-hours 36] [--run-date 2026-11-28]

方針（Muse作業指示書 2026-11-28）:
  - データの日時を必ず特定し、古いデータ（既定36時間超）は取り込まない（終了コード2）
  - 取込は ledger.py のルール（名寄せ・変化時のみ履歴・利益再計算・未確認は0で埋めない）を通す
  - 除外リスト掲載品は復活させない（ledger.py 側で判定）
  - 新品でない（中古）行は抽出基準外のため取り込まず、件数だけ報告する
  - 同じレポートを何度取り込んでも重複しない（ledger.py の冪等性に依存）
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger  # noqa: E402

JST = timezone(timedelta(hours=9))
NOT_NEW_MARKERS = ("中古",)


def data_time(report_path: str) -> tuple[datetime, str]:
    """
    データの生成日時を特定する。
      1) gitで未変更なら、そのファイルの最終コミット日時（＝前回の取得日時）
      2) 変更あり（このワークフローで今回生成された）なら、ファイルの更新日時
    """
    path = os.path.abspath(report_path)
    d = os.path.dirname(path)
    def git(*args):
        return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True)
    tracked = git("ls-files", "--error-unmatch", "--", path).returncode == 0
    if tracked and git("rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        # 浅いクローン（GitHub Actionsの既定）ではコミット日時が実際のデータ日時を表さない
        raise SystemExit("取込中止: 浅いクローンのためデータ日時を特定できません（実行状態ファイルが必要）")
    if tracked:
        if git("status", "--porcelain", "--", path).stdout.strip() == "":
            iso = git("log", "-1", "--format=%cI", "--", path).stdout.strip()
            if not iso:
                # 履歴が取れない（浅いクローン等）のに未変更 → 日時を特定できないので安全側で止める
                raise SystemExit("取込中止: データ日時を特定できません（git履歴なし）")
            return datetime.fromisoformat(iso).astimezone(JST), "gitの最終コミット日時"
    return datetime.fromtimestamp(os.path.getmtime(report_path), JST), "ファイル更新日時"


def to_ledger_rows(report_path: str, survey_time: str, source_note: str) -> tuple[list[dict], dict]:
    rows, stats = [], {"total": 0, "not_new": 0, "caution": 0}
    with open(report_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            stats["total"] += 1
            note = (r.get("note") or "").strip()
            if any(m in note for m in NOT_NEW_MARKERS):
                stats["not_new"] += 1
                continue
            if note:
                stats["caution"] += 1
            point_rate = r.get("point_rate") or ""
            yahoo = ledger.to_yen(r.get("yahoo_price"))
            point = round(yahoo * float(point_rate)) if (yahoo is not None and point_rate) else ""
            rows.append({
                "調査日時": r.get("yahoo_fetched_at") or survey_time,
                "商品名": r.get("kaitori_name") or r.get("ec_name") or "",
                "JANコード": r.get("jan") or "",
                "仕入先": "Yahoo!ショッピング",
                "仕入価格": r.get("yahoo_price") or "",
                "獲得ポイント": str(point),                 # レポートの既定還元率（会員状況で変動）
                "仕入URL": r.get("yahoo_url") or "",
                "仕入送料": "0" if "送料無料" in (r.get("yahoo_shipping") or "") else "",   # 送料無料表記のみ0、他は未確認
                "販売先": "買取商店",
                "販売URL": r.get("kaitori_url") or "",
                "買取価格": r.get("kaitori_price") or "",
                "販売手数料": "0",                          # 買取は販売手数料なし
                "発送費用": r.get("shipping") or "",        # レポートの買取店への送料
                "その他経費": "",                           # 振込手数料等は未確認
                "在庫状況": "在庫あり" if r.get("yahoo_fetched_at") else "",   # 復旧版はin_stock=trueで検索
                "検証状況": "未検証候補" + (f"（{note}）" if note else ""),
                "価格変動リスク": "",
                "情報源": source_note + f" ／ 買取取得{r.get('kaitori_fetched_at') or '不明'}"
                          f" ／ Yahoo取得{r.get('yahoo_fetched_at') or '不明'} {r.get('yahoo_store') or ''}"
                          f" ／ EC商品名: {r.get('ec_name') or ''}",
            })
    return rows, stats


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--ledger-dir", required=True)
    p.add_argument("--max-age-hours", type=float, default=36)
    p.add_argument("--run-date", default=datetime.now(JST).strftime("%Y-%m-%d"))
    p.add_argument("--now", help="テスト用：現在時刻（ISO8601）")
    a = p.parse_args(argv)

    now = datetime.fromisoformat(a.now).astimezone(JST) if a.now else datetime.now(JST)
    status_path = os.path.join(os.path.dirname(os.path.abspath(a.report)), "kaitori_run_status.json")
    run_status = None
    if os.path.exists(status_path):
        with open(status_path, encoding="utf-8") as f:
            run_status = json.load(f)
        print(f"実行状態: {run_status.get('status')} ／ " + " / ".join(run_status.get("reasons") or []))
        if run_status.get("status") == "取得失敗":
            print("取込中止: 直近の実行は取得失敗。出力ファイルは前回のものなので取り込みません。")
            return 2
        if not run_status.get("data_generated_at"):
            print("取込中止: データ生成日時が記録されていません。")
            return 2
        dt = datetime.strptime(run_status["data_generated_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
        how = "実行状態ファイルのデータ生成日時"
    else:
        dt, how = data_time(a.report)
    age_h = (now - dt).total_seconds() / 3600
    dt_s = dt.strftime("%Y-%m-%d %H:%M")
    differs = dt.strftime("%Y-%m-%d") != a.run_date
    source = (f"朝レポート 実行日{a.run_date} ／ データ日時{dt_s}（{how}）"
              + ("※データ日時は実行日と異なる" if differs else ""))

    print(f"データ日時: {dt_s} JST（{how}）／ 経過 {age_h:.1f} 時間")
    if age_h > a.max_age_hours:
        print(f"取込中止（古いデータ使用）: データが{a.max_age_hours:.0f}時間より古いため、最新として台帳に取り込みません。")
        return 2

    rows, stats = to_ledger_rows(a.report, dt_s, source)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8-sig", newline="") as t:
        w = csv.DictWriter(t, fieldnames=ledger.MASTER_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        tmp = t.name
    try:
        r = ledger.merge(a.ledger_dir, tmp)
    finally:
        os.unlink(tmp)

    print(f"レポート {stats['total']}件 ／ 中古のため対象外 {stats['not_new']}件 ／ 取込対象 {len(rows)}件"
          f"（うち要確認の注記あり {stats['caution']}件）")
    ledger.print_report(r)
    return 1 if r["rejected"] or r["conflicts"] else 0


if __name__ == "__main__":
    sys.exit(main())
