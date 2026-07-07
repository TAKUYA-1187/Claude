"""Amazon広告 検索用語レポート最適化ツール。

使い方:
    python main.py 検索用語レポート.xlsx --target-acos 0.20

複数レポート（検索用語＋ターゲティング）をまとめて渡すこともできる:
    python main.py search_terms.xlsx targeting.xlsx

出力:
    output/ 以下に推奨アクションのCSV4種と、コンソールにサマリー。
"""

import argparse
import csv
from dataclasses import asdict, fields
from pathlib import Path

from config import Settings
from optimizer import Action, analyze
from report_loader import load_report

TITLES = {
    "negatives": "除外キーワード候補（ネガティブ完全一致に追加）",
    "harvests": "刈り取り候補（完全一致キャンペーンへ移管）",
    "bid_up": "入札 引き上げ候補",
    "bid_down": "入札 引き下げ候補",
}


def write_csv(path: Path, items: list[Action]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[fld.name for fld in fields(Action)])
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", help="検索用語/ターゲティングレポート (.xlsx/.csv)")
    parser.add_argument("--target-acos", type=float, default=0.20,
                        help="目標ACOS（デフォルト 0.20 = 20%%）")
    parser.add_argument("--negative-clicks", type=int, default=10,
                        help="注文0でも除外候補にするクリック数の閾値（デフォルト 10）")
    parser.add_argument("--output-dir", default="output", help="CSV出力先")
    args = parser.parse_args()

    settings = Settings(
        target_acos=args.target_acos,
        negative_click_threshold=args.negative_clicks,
    )

    rows = []
    for report in args.reports:
        loaded = load_report(report)
        print(f"読み込み: {report}（{len(loaded)}行）")
        rows.extend(loaded)

    total_spend = sum(r.spend for r in rows)
    total_sales = sum(r.sales for r in rows)
    print(f"\n合計: 費用 ¥{total_spend:,.0f} / 売上 ¥{total_sales:,.0f}"
          f" / ACOS {total_spend / total_sales:.1%}" if total_sales else "")

    actions = analyze(rows, settings)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, items in actions.items():
        path = out_dir / f"{key}.csv"
        write_csv(path, items)
        print(f"\n■ {TITLES[key]}: {len(items)}件 → {path}")
        for item in items[:5]:
            print(f"  - [{item.campaign}] {item.target}: {item.reason}")
        if len(items) > 5:
            print(f"  … 残り{len(items) - 5}件はCSVを参照")


if __name__ == "__main__":
    main()
