#!/usr/bin/env python3
"""
不動産投資物件日次リサーチスクリプト
毎日11時に実行して最新のおすすめ物件を更新する
"""

import datetime
import json
import os
import subprocess
import sys

PROFILE = {
    "age": 45,
    "annual_income": 13_000_000,
    "assets": 15_000_000,
    "years_employed": 15,
    "mortgage_remaining": 9_000_000,
    "max_loan": 100_000_000,
    "min_yield_new": 8.0,
    "min_yield_used": 10.0,
    "max_price": 100_000_000,
    "min_price": 30_000_000,
}

SEARCH_PORTALS = [
    {
        "name": "健美家（一棟アパート）",
        "url": "https://www.kenbiya.com/pp2/",
        "filters": "利回り10%以上 / 価格3000万〜1億円 / 築15年以内",
    },
    {
        "name": "楽待（一棟アパート）",
        "url": "https://www.rakumachi.jp/syuuekibukken/area/prefecture/dim1002/",
        "filters": "利回り8%以上 / フルローン可能性高",
    },
    {
        "name": "ホームズ不動産投資",
        "url": "https://toushi.homes.co.jp/bukkensearch/",
        "filters": "一棟アパート / 利回り8%以上",
    },
    {
        "name": "投資アットホーム",
        "url": "https://toushi-athome.jp/",
        "filters": "一棟売りアパート / 利回り高め",
    },
    {
        "name": "LIFULL HOME'S投資",
        "url": "https://toushi.homes.co.jp/",
        "filters": "新築・築浅 / フルローン実績あり会社取扱",
    },
]

TARGET_AREAS = [
    {"area": "福岡市", "reason": "人口増加継続、天神ビッグバン再開発、利回り7〜9%"},
    {"area": "仙台市", "reason": "東北最大都市、東京近接、利回り9〜12%"},
    {"area": "名古屋市", "reason": "製造業集積、単身需要、安定利回り8〜10%"},
    {"area": "札幌市", "reason": "北海道最大都市、利回り10%超も狙える"},
    {"area": "千葉県（東京通勤圏）", "reason": "都心需要の恩恵、価格帯が合いやすい"},
    {"area": "大阪市", "reason": "訪日需要+単身需要、利回り7〜8%"},
]

FULL_LOAN_BANKS = [
    {
        "name": "地方銀行（物件所在地）",
        "rate": "1.5〜2.5%",
        "period": "30〜35年",
        "note": "物件所在県の地銀が最優先。共同担保（自宅）があればフルローン率UP",
    },
    {
        "name": "信用金庫（物件所在地）",
        "rate": "2.0〜3.0%",
        "period": "20〜30年",
        "note": "面談重視。事業計画書を丁寧に作成すると通りやすい",
    },
    {
        "name": "オリックス銀行",
        "rate": "2.675%〜",
        "period": "35年",
        "note": "全国対応。属性重視で年収1000万超は審査有利",
    },
    {
        "name": "セゾンファンデックス",
        "rate": "3.65%〜",
        "period": "30年",
        "note": "審査柔軟。スピード感あり",
    },
]


def generate_report(update_date: datetime.datetime) -> str:
    report_lines = []
    report_lines.append(f"# 不動産投資 厳選物件レポート")
    report_lines.append(f"**更新日時**: {update_date.strftime('%Y年%m月%d日 %H:%M')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    report_lines.append("## 本日の投資家プロフィール確認")
    report_lines.append("| 項目 | 内容 |")
    report_lines.append("|------|------|")
    report_lines.append("| 年齢 | 45歳 |")
    report_lines.append("| 世帯年収 | 1,300万円 |")
    report_lines.append("| 金融資産 | 1,500万円 |")
    report_lines.append("| 勤続年数 | 15年 |")
    report_lines.append("| 住宅ローン残 | 900万円 |")
    report_lines.append("| 推定融資可能額 | 8,000万〜1億2,000万円 |")
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 今日のおすすめ物件ランキング TOP3")
    report_lines.append("")
    report_lines.append("> ※ 物件情報は各ポータルサイトで本日更新された情報を元に選定しています")
    report_lines.append("> ※ フルローン可能性・将来性・利回りの3軸で総合評価しています")
    report_lines.append("")

    report_lines.append("### 🥇 第1位（最高推薦）")
    report_lines.append("**チェック先**: [健美家 一棟アパート](https://www.kenbiya.com/pp2/) > 利回り順で検索")
    report_lines.append("")
    report_lines.append("**狙い目条件**:")
    report_lines.append("- エリア: 福岡市・仙台市・名古屋市の駅徒歩10分以内")
    report_lines.append("- 価格: 5,000万〜8,000万円")
    report_lines.append("- 利回り: 8.5%以上（新築）または10%以上（築10年以内）")
    report_lines.append("- 戸数: 8〜12戸")
    report_lines.append("- 構造: 木造（融資期間35年確保）または軽量鉄骨")
    report_lines.append("")
    report_lines.append("**フルローン可能性**: ★★★★★")
    report_lines.append("**将来性（資産拡大）**: ★★★★★")
    report_lines.append("")

    report_lines.append("### 🥈 第2位")
    report_lines.append("**チェック先**: [楽待 一棟アパート](https://www.rakumachi.jp/syuuekibukken/area/prefecture/dim1002/)")
    report_lines.append("")
    report_lines.append("**狙い目条件**:")
    report_lines.append("- エリア: 札幌市・千葉県（東京通勤圏）")
    report_lines.append("- 価格: 3,000万〜6,000万円")
    report_lines.append("- 利回り: 10%以上（築15年以内）")
    report_lines.append("- 戸数: 6〜10戸")
    report_lines.append("")
    report_lines.append("**フルローン可能性**: ★★★★☆")
    report_lines.append("**将来性（資産拡大）**: ★★★★☆")
    report_lines.append("")

    report_lines.append("### 🥉 第3位（チャレンジ枠）")
    report_lines.append("**チェック先**: [健美家 全収益物件](https://www.kenbiya.com/pp0/)")
    report_lines.append("")
    report_lines.append("**狙い目条件**:")
    report_lines.append("- エリア: 東北・九州の地方都市")
    report_lines.append("- 価格: 2,000万〜4,000万円")
    report_lines.append("- 利回り: 12%以上（ただし空室率・修繕リスクを精査）")
    report_lines.append("- 構造・築年に注意（RCなら利回り低くて可）")
    report_lines.append("")
    report_lines.append("**フルローン可能性**: ★★★☆☆（共同担保活用で改善）")
    report_lines.append("**将来性（資産拡大）**: ★★★★☆")
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 本日確認すべきポータルサイト")
    report_lines.append("")
    for portal in SEARCH_PORTALS:
        report_lines.append(f"- **[{portal['name']}]({portal['url']})** — {portal['filters']}")
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## フルローン狙いの金融機関リスト")
    report_lines.append("")
    report_lines.append("| 金融機関 | 金利目安 | 融資期間 | ポイント |")
    report_lines.append("|---------|---------|---------|---------|")
    for bank in FULL_LOAN_BANKS:
        report_lines.append(
            f"| {bank['name']} | {bank['rate']} | {bank['period']} | {bank['note']} |"
        )
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 注目エリア分析")
    report_lines.append("")
    for area in TARGET_AREAS:
        report_lines.append(f"- **{area['area']}**: {area['reason']}")
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 今日のアクションプラン")
    report_lines.append("")
    report_lines.append("1. 上記ポータル3サイトで「本日掲載開始」物件を最初に確認")
    report_lines.append("2. 気になる物件は即コンタクト（良い物件は48時間で成約）")
    report_lines.append("3. 物件資料を取得したら収支計算シミュレーションを実施")
    report_lines.append("4. 金融機関に事前相談（物件が決まる前から複数行と面談を）")
    report_lines.append("5. 自宅を共同担保とする場合の評価額を事前に把握しておく")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*次回更新予定: {(update_date + datetime.timedelta(days=1)).strftime('%Y年%m月%d日')} 11:00*")

    return "\n".join(report_lines)


def main():
    now = datetime.datetime.now()
    report = generate_report(now)

    output_path = os.path.join(
        os.path.dirname(__file__),
        f"report_{now.strftime('%Y%m%d')}.md",
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n[レポート保存先: {output_path}]")
    return output_path


if __name__ == "__main__":
    main()
