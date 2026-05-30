#!/usr/bin/env python3
"""
Keepa商品詳細取得 + 中国サイト比較リンク生成
使い方: python3 keepa_detail.py
"""

import requests
import json
import os
import time
from urllib.parse import quote

API_KEY = os.environ.get("KEEPA_API_KEY", "ここにAPIキーを貼り付け")

def get_product_details(asin_list):
    """ASINリストから商品詳細を取得（10件ずつ）"""
    all_products = []
    for i in range(0, len(asin_list), 10):
        chunk = asin_list[i:i+10]
        params = {
            "key": API_KEY,
            "domain": 5,
            "asin": ",".join(chunk),
            "stats": 90,
        }
        print(f"  商品詳細取得中... {i+1}〜{min(i+10, len(asin_list))}件目")
        r = requests.get("https://api.keepa.com/product", params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            all_products.extend(data.get("products", []))
        time.sleep(13)  # トークン制限対策
    return all_products

def keepa_price_to_yen(val):
    if val is None or val < 0:
        return None
    return val // 100

def main():
    # keepa_results.jsonを読み込む
    json_path = os.path.expanduser("~/Downloads/keepa_results.json")
    if not os.path.exists(json_path):
        print("エラー: ~/Downloads/keepa_results.json が見つかりません。")
        print("先に keepa_finder.py を実行してください。")
        return

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    asin_list = data["asins"]
    print(f"対象ASIN数: {len(asin_list)}件\n")
    print("商品詳細を取得中（1〜2分かかります）...")

    products = get_product_details(asin_list)

    results = []
    for p in products:
        asin = p.get("asin", "")
        title = p.get("title", "不明")
        # 現在のBuyBox価格（円×100）
        csv = p.get("csv", [])
        # index 18 = BUY_BOX_SHIPPING
        price_raw = None
        if len(csv) > 18 and csv[18]:
            vals = csv[18]
            # 最新値は末尾
            for v in reversed(vals):
                if v and v > 0:
                    price_raw = v
                    break

        price_jpy = keepa_price_to_yen(price_raw) if price_raw else None
        half_price = price_jpy // 2 if price_jpy else None

        # カテゴリ・評価
        rating = p.get("stats", {}).get("current", [None]*10)
        rating_val = None
        if isinstance(rating, list) and len(rating) > 9:
            r = rating[9]
            if r and r > 0:
                rating_val = r / 10

        results.append({
            "asin": asin,
            "title": title[:60],
            "price_jpy": price_jpy,
            "half_price_target": half_price,
            "rating": rating_val,
            "amazon_url": f"https://www.amazon.co.jp/dp/{asin}",
            "alibaba_url": f"https://www.alibaba.com/trade/search?SearchText={quote(title[:30])}",
            "1688_url": f"https://s.1688.com/selloffer/offer_search.htm?keywords={quote(title[:20])}",
            "temu_url": f"https://www.temu.com/search_result.html?search_key={quote(title[:30])}",
        })

    # 価格順でソート
    results.sort(key=lambda x: x["price_jpy"] or 0)

    # HTML形式でレポート出力
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Amazon JP - 中国仕入れ候補リスト</title>
<style>
body { font-family: sans-serif; font-size: 13px; padding: 20px; }
table { border-collapse: collapse; width: 100%; }
th { background: #2c3e50; color: white; padding: 8px; text-align: left; }
td { border: 1px solid #ddd; padding: 6px; vertical-align: top; }
tr:nth-child(even) { background: #f9f9f9; }
a { color: #2980b9; text-decoration: none; }
a:hover { text-decoration: underline; }
.price { font-weight: bold; color: #e74c3c; }
.target { color: #27ae60; }
</style>
</head>
<body>
<h2>Amazon JP → 中国仕入れ候補リスト（全{count}件）</h2>
<p>目標: Amazon販売価格の<strong>半額以下</strong>で中国から仕入れられる商品を探す</p>
<table>
<tr>
  <th>#</th>
  <th>商品名</th>
  <th>Amazon価格</th>
  <th>目標仕入値(半額)</th>
  <th>評価</th>
  <th>Amazon</th>
  <th>Alibaba</th>
  <th>1688</th>
  <th>Temu</th>
</tr>
""".replace("{count}", str(len(results)))

    for i, r in enumerate(results, 1):
        price_str = f"¥{r['price_jpy']:,}" if r['price_jpy'] else "不明"
        half_str = f"¥{r['half_price_target']:,}" if r['half_price_target'] else "-"
        rating_str = str(r['rating']) if r['rating'] else "-"
        html += f"""<tr>
  <td>{i}</td>
  <td>{r['title']}</td>
  <td class="price">{price_str}</td>
  <td class="target">{half_str}以下</td>
  <td>{rating_str}</td>
  <td><a href="{r['amazon_url']}" target="_blank">Amazon</a></td>
  <td><a href="{r['alibaba_url']}" target="_blank">検索</a></td>
  <td><a href="{r['1688_url']}" target="_blank">検索</a></td>
  <td><a href="{r['temu_url']}" target="_blank">検索</a></td>
</tr>
"""

    html += "</table></body></html>"

    out_path = os.path.expanduser("~/Downloads/comparison_report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # JSONも保存
    json_out = os.path.expanduser("~/Downloads/comparison_results.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n完了！")
    print(f"HTMLレポート: ~/Downloads/comparison_report.html")
    print(f"JSONデータ:   ~/Downloads/comparison_results.json")
    print(f"\nHTMLをブラウザで開くには:")
    print(f"  open ~/Downloads/comparison_report.html")

if __name__ == "__main__":
    main()
