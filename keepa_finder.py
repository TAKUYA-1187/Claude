#!/usr/bin/env python3
"""
Keepa Finder API - Amazon JP商品リサーチツール
使い方: python keepa_finder.py
"""

import requests
import json
import os
import time

# APIキーは環境変数から取得（セキュリティのため直接書かない）
API_KEY = os.environ.get("KEEPA_API_KEY", "ここにAPIキーを貼り付け")

BASE_URL = "https://api.keepa.com/query"

def run_finder(filters: dict, sort: list, label: str) -> list:
    """Keepa Finder APIを実行して商品リストを返す"""
    selection = {
        "filters": filters,
        "sortBy": sort,
        "perPage": 50,  # 最大100
        "page": 0,
        "range": "g",   # global (全期間)
    }

    params = {
        "key": API_KEY,
        "domain": 5,  # 5 = Amazon.co.jp
        "selection": json.dumps(selection),
    }

    print(f"\n[{label}] APIリクエスト送信中...")
    response = requests.get(BASE_URL, params=params, timeout=30)

    if response.status_code != 200:
        print(f"  エラー: {response.status_code} - {response.text[:200]}")
        return []

    data = response.json()

    if "error" in data:
        print(f"  APIエラー: {data['error']}")
        return []

    products = data.get("asinList", [])
    print(f"  取得件数: {len(products)}件")
    return products


def get_product_details(asin_list: list) -> list:
    """ASINリストから商品詳細を取得"""
    if not asin_list:
        return []

    asins = ",".join(asin_list[:20])  # 最大20件ずつ
    params = {
        "key": API_KEY,
        "domain": 5,
        "asin": asins,
        "stats": 90,
    }

    response = requests.get("https://api.keepa.com/product", params=params, timeout=30)
    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("products", [])


def format_price(cents: int) -> str:
    """Keepaの価格（円×100）を円に変換"""
    if cents < 0:
        return "N/A"
    return f"¥{cents // 100:,}"


# ===== フィルター定義（URLから解析） =====

SEARCHES = [
    {
        "label": "検索1: BSR~50000・価格¥8000-60000・競合1-15・重量7.5kg+・評価~4.4",
        "filters": {
            "SALES_current_gte": 1,
            "SALES_current_lte": 50000,
            "BUY_BOX_SHIPPING_current_gte": 800000,   # 円×100
            "BUY_BOX_SHIPPING_current_lte": 6000000,
            "AMAZON_outOfStock": True,
            "totalOfferCount_gte": 1,
            "totalOfferCount_lte": 15,
            "packageLength_gte": 40,
            "packageWidth_gte": 10,
            "packageHeight_gte": 10,
            "packageWeight_gte": 7500,
            "RATING_current_gte": 100,
            "RATING_current_lte": 440,
            "monthlySold_gte": 80,
            "productType": [0],
            "srAvgMonth": "202511",
        },
        "sort": [{"colId": "SALES_current", "sort": "asc"},
                 {"colId": "monthlySold", "sort": "desc"}],
    },
    {
        "label": "検索2: BSR~80000・価格¥7000+・競合15+・評価~4.4",
        "filters": {
            "SALES_current_gte": 1,
            "SALES_current_lte": 80000,
            "BUY_BOX_SHIPPING_current_gte": 700000,
            "AMAZON_outOfStock": True,
            "totalOfferCount_gte": 15,
            "packageLength_gte": 30,
            "packageWidth_gte": 30,
            "packageHeight_gte": 10,
            "RATING_current_lte": 440,
            "srAvgMonth": "202511",
        },
        "sort": [{"colId": "SALES_current", "sort": "asc"}],
    },
    {
        "label": "検索3: BSR~80000・価格¥8000+・月販60+・重量7.8kg+・評価~4.2・サイズ101000+",
        "filters": {
            "SALES_current_gte": 1,
            "SALES_current_lte": 80000,
            "BUY_BOX_SHIPPING_current_gte": 800000,
            "AMAZON_outOfStock": True,
            "packageWeight_gte": 7800,
            "RATING_current_gte": 100,
            "RATING_current_lte": 420,
            "monthlySold_gte": 60,
            "itemDimension_gte": 101000,
            "productType": [0],
            "srAvgMonth": "202511",
        },
        "sort": [{"colId": "SALES_current", "sort": "asc"},
                 {"colId": "monthlySold", "sort": "desc"}],
    },
    {
        "label": "検索4: BSR~70000・価格¥8000-60000・競合1-15・月販70+・重量8kg+・評価~4.1",
        "filters": {
            "SALES_current_gte": 1,
            "SALES_current_lte": 70000,
            "BUY_BOX_SHIPPING_current_gte": 800000,
            "BUY_BOX_SHIPPING_current_lte": 6000000,
            "totalOfferCount_gte": 1,
            "totalOfferCount_lte": 15,
            "packageWeight_gte": 8000,
            "RATING_current_gte": 100,
            "RATING_current_lte": 410,
            "monthlySold_gte": 70,
            "itemDimension_gte": 86400,
            "productType": [0],
            "srAvgMonth": "202511",
        },
        "sort": [{"colId": "SALES_current", "sort": "asc"},
                 {"colId": "monthlySold", "sort": "desc"}],
    },
]


def main():
    print("=" * 60)
    print("Keepa Finder - Amazon JP商品リサーチ")
    print("=" * 60)

    if API_KEY == "ここにAPIキーを貼り付け":
        print("\nエラー: APIキーが設定されていません。")
        print("以下のいずれかの方法で設定してください:")
        print("  方法1: export KEEPA_API_KEY='あなたのAPIキー'")
        print("  方法2: スクリプト内の API_KEY 変数に直接入力")
        return

    all_asins = set()

    for search in SEARCHES:
        asins = run_finder(search["filters"], search["sort"], search["label"])
        all_asins.update(asins)
        time.sleep(13)  # 5トークン/分制限を考慮（Finderは250トークン消費）

    print(f"\n合計ユニークASIN数: {len(all_asins)}")

    # 結果をJSONで保存
    result = {
        "total_asins": len(all_asins),
        "asins": list(all_asins),
        "amazon_urls": [f"https://www.amazon.co.jp/dp/{asin}" for asin in all_asins],
        "alibaba_search": "https://www.alibaba.com/trade/search?SearchText=",
        "1688_search": "https://s.1688.com/selloffer/offer_search.htm?keywords=",
    }

    with open("keepa_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n結果を keepa_results.json に保存しました。")
    print("\nAmazon商品URL一覧:")
    for asin in list(all_asins)[:10]:
        print(f"  https://www.amazon.co.jp/dp/{asin}")

    if len(all_asins) > 10:
        print(f"  ... 他{len(all_asins) - 10}件（keepa_results.jsonを確認）")


if __name__ == "__main__":
    main()
