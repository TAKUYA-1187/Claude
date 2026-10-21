# -*- coding: utf-8 -*-
"""Review mining per product type: frequency of complaint themes in 1-3 star reviews and
praise themes in 4-5 star reviews shown on the leaders' product pages."""
import collections
import re

THEMES = [
    ("組立が大変・説明書が不親切", r"組み?立て?|説明書|取説|ネジ穴|穴が合わ|部品"),
    ("部品欠品・ネジ不足", r"欠品|足りな|不足|入って(い)?な"),
    ("初期傷・破損・凹み", r"傷|キズ|破損|割れ|凹み|へこみ|欠け|ひび|壊れて届"),
    ("ぐらつき・強度不足", r"ぐらつ|グラグラ|ぐらぐら|揺れ|強度|たわ|歪|ゆが|安定しな|しなる"),
    ("すぐ壊れた・耐久性", r"壊れ|故障|折れ|外れ|取れ|破れ|劣化|錆|サビ|さび|穴が開|空気が抜"),
    ("臭い", r"臭|におい|匂い"),
    ("音・きしみ", r"音|きし|ギシ|キシ|うるさ"),
    ("サイズ・寸法が想定と違う", r"小さ|狭|大き|サイズ|寸法|高さが|低い|短い"),
    ("質感・色が写真と違う", r"安っぽ|チープ|写真と|画像と|色が|質感|作りが雑|雑な"),
    ("座り心地・寝心地・硬さ", r"硬|固|柔らか|へた|沈|腰|痛"),
    ("扉・引出し・ロックの不具合", r"扉|引き?出し|ロック|鍵|蝶番|ヒンジ|開閉|閉ま"),
    ("配送・梱包の問題", r"配送|梱包|箱|届いた時|置き配"),
    ("サポート・返品対応", r"対応|返品|返金|問い合わせ|連絡|サポート"),
    ("重い・移動しにくい", r"重い|重たい|運べ|移動"),
    ("ライト・電装の不具合", r"ライト|LED|電池|点灯|充電|リモコン"),
]
PRAISE = [
    ("組立が簡単", r"簡単|かんたん|すぐ組"), ("しっかり・頑丈", r"しっかり|頑丈|丈夫|安定"),
    ("コスパが良い", r"コスパ|値段の割|価格以上|安い"), ("見た目・おしゃれ", r"おしゃれ|オシャレ|可愛|かわい|高級感|見た目"),
    ("収納力・大容量", r"収納|容量|たっぷり"), ("快適・使いやすい", r"快適|使いやす|楽|便利|気持ち"),
]


def mine(reviews):
    """reviews: list of (stars, text). Returns (complaint counter, praise counter, examples)."""
    neg, pos, ex = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    for s, t in reviews:
        if s <= 3:
            for name, rx in THEMES:
                if re.search(rx, t):
                    neg[name] += 1
                    if len(ex[name]) < 3:
                        ex[name].append(t[:140])
        else:
            for name, rx in PRAISE:
                if re.search(rx, t):
                    pos[name] += 1
    return neg, pos, ex
