# -*- coding: utf-8 -*-
"""Is a US / China new product already sold on Amazon.co.jp?
For each concept: the same US ASIN on amazon.co.jp (dp page), and the Japanese search page
(relevant listings, how many sell, the best seller and its price)."""
import json
import os
import re
import sys

import scrape as S

# (id, source, origin url or note, JP search keyword, JP title regex, US ASIN or "")
CONCEPTS = [
    ("cloudsofa", "US", "Boneless Couch 96in Modular L-Shaped Cloud Sectional ($259.98, 300+/mo)", "クラウドソファ モジュール", r"クラウド|モジュール|ソファ", "B0HKDCYMFF"),
    ("reformer", "US", "Wooden Pilates Reformer Machine ($159.99, 200+/mo)", "ピラティス リフォーマー 家庭用", r"リフォーマー|ピラティス", "B0H4VT6GBY"),
    ("cardcase", "US", "Card Display Case 34x22 Large Aluminum Locking ($89.99, 200+/mo)", "トレカ ディスプレイケース 鍵付き 大型", r"ディスプレイ|ケース|ショーケース", "B0H7HTTR3Z"),
    ("woodpen", "US", "Foldable Wooden Playpen ($139.99, 200+/mo)", "ベビーサークル 木製 折りたたみ", r"サークル|ベビー", "B0HDYLVB9Y"),
    ("bedrail", "US", "Bed Rail for Toddlers 3 Pieces King Size U-Shape Base ($139.99, 1,000+/mo)", "ベッドガード 3面 ロング", r"ベッドガード|ベッドフェンス", "B0HJWKTJ2J"),
    ("romanchair", "US", "Roman Chair Back Extension Bench ($79.99, 500+/mo)", "ローマンチェア", r"ローマン|バックエクステンション|背筋", "B0H98Q7C8T"),
    ("bedsidecrib", "US", "5 in 1 Pack and Play Bedside Crib ($139.99, 600+/mo)", "添い寝 ベビーベッド ベッドサイド プレイヤード", r"ベビーベッド|ベッドサイド|プレイヤード", "B0H45GH5M7"),
    ("pantrysteel", "US", "75in Metal Pantry Cabinet with Doors ($139.99, 800+/mo)", "スチール キャビネット 扉付き 180cm 食品庫", r"キャビネット|収納庫|パントリー", "B0HJQSDBWN"),
    ("changingdresser", "US", "Kids Dresser with Changing Table ($179.99, 200+/mo)", "おむつ替え台 チェスト", r"おむつ|チェスト|オムツ", "B0HGFQ3R7S"),
    ("swivelrocker", "US", "360 Swivel Rocker Recliner Chair ($179.95, 200+/mo)", "回転 ロッキング リクライニングチェア", r"ロッキング|リクライニング|チェア", "B0HDZXQG7B"),
    ("glider", "US", "Glider Rocker with Ottoman, Corduroy ($219.99)", "グライダーチェア 授乳 オットマン", r"グライダー|ロッキング|授乳", "B0HJ54TD5W"),
    ("toyorganizer", "US", "Toy Storage Organizer with Bookshelf 9 bins ($71.99, 200+/mo)", "おもちゃ収納 ラック 絵本棚 大容量", r"おもちゃ|絵本|収納", "B0HJ65LR37"),
    ("hitchcargo", "US", "Folding Hitch Cargo Carrier 60x24 500lbs ($165.99)", "ヒッチカーゴ 折りたたみ", r"ヒッチ|カーゴ", "B0HFJG98Q8"),
    ("outdoorhoriz", "US", "Outdoor Horizontal Storage Shed 36 Cu Ft ($188.99)", "屋外収納庫 横型 大型 鍵付き", r"収納|物置|ストッカー", "B0HH8SMN7C"),
    ("picnic8ft", "US", "8 FT Folding Picnic Table ($73.95, 600+/mo)", "ピクニックテーブル 折りたたみ ベンチ一体", r"テーブル|ピクニック", "B0H9XJX6KW"),
    ("partytent", "US", "10x30 FT Party Tent ($169.99, 900+/mo)", "イベントテント 3m×9m", r"テント|タープ", "B0HHN4V2HK"),
    ("bigtallchair", "US", "Big&Tall Gaming Chair Wide Spring Seat ($149.96, 900+/mo)", "ゲーミングチェア 大きい 幅広 ポケットコイル", r"チェア", "B0HFW4RTTQ"),
    ("basketport", "US", "Portable Basketball Hoop Outdoor 54in Backboard ($199.98, 1,000+/mo)", "バスケットゴール 屋外 一般用", r"バスケット|ゴール", "B0HBQFT8Z6"),
    ("streamtank", "CN", "1688 2026新款 侧滤溪流缸 生态造景（月销128）", "渓流水槽 ストリーム 水槽 セット", r"水槽|アクアリウム", ""),
    ("floatbed", "CN", "1688 2026新款 悬浮床 碳素钢架床（月销20）", "フローティングベッド", r"ベッド", ""),
    ("dressernight", "CN", "1688 2026新款 梳妆台床头柜一体（月销351）", "ドレッサー ナイトテーブル 一体", r"ドレッサー|鏡台|化粧台", ""),
    ("steelwardrobe", "CN", "1688 2026新款 钢制衣柜 推拉门（月销125）", "スチール ワードローブ 引き戸", r"ワードローブ|クローゼット|ロッカー", ""),
    ("cloudsofabed", "CN", "1688 2026新款 云朵沙发床 折叠两用（月销20〜92）", "ソファベッド 折りたたみ 雲", r"ソファ", ""),
    ("deskbike", "CN", "1688 专利新款 带桌板磁控动感单车（月销50）", "デスクバイク フィットネスバイク 机付き", r"バイク|デスク", ""),
]

def jp_status(body):
    """'販売中' / 'ページのみ（在庫切れ・再入荷予定なし）' / 'なし'. Amazon.co.jp shows translated
    catalog pages of many US listings that cannot actually be bought in Japan."""
    if "productTitle" not in body:
        return "なし"
    if "現在在庫切れです" in body or "お取り扱いできません" in body:
        return "ページのみ（在庫切れ・再入荷予定なし）"
    return "販売中"


if __name__ == "__main__":
    out = sys.argv[1]
    res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
    S.session_init()
    for cid, src, origin, kw, rx, asin in CONCEPTS:
        if cid in res and res[cid]["same_on_jp"] not in (True, False):
            continue
        items = [x for x in S.amazon_search(kw, 1) if re.search(rx, x["title"])]
        same = None
        if asin:
            body = S._fetch(f"https://www.amazon.co.jp/dp/{asin}", os.path.join(S.CACHE, "amz_d", f"jpcheck_{asin}.html"))
            same = jp_status(body)
        top = sorted(items, key=lambda x: (-x["bought"], -(x["reviews"] or 0)))[:5]
        res[cid] = dict(src=src, origin=origin, kw=kw, asin=asin, same_on_jp=same, n=len(items),
                        units=sum(x["bought"] for x in items), n_selling=sum(1 for x in items if x["bought"] >= 50), top=top)
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        t = top[0] if top else {}
        print(cid, "sameJP", same, "n", len(items), "units", res[cid]["units"], "top", t.get("price"), t.get("bought"), (t.get("title") or "")[:40], flush=True)
