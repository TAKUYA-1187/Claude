# -*- coding: utf-8 -*-
"""v7 (2026-11-08): re-research of the 26 candidates the user listed for quotations.

  amazon : current Amazon.co.jp product pages of every candidate and rival ASIN, plus the
           comparable searches the user asked about (pilates, dresser, baby bed, 5WAY sofa bed,
           floor bed, card case, 2-seat sofa ...)
  cn     : spec-matched 1688 market searches per candidate (detail.1688.com is not reachable
           for automated access: the desktop host resets the connection and the mobile host
           answers with a slider captcha, so SKU prices are not read and nothing is bypassed)

usage: OEM_CACHE=<dir> OEM_DELAY=8 python3 v7_research.py amazon|cn <out_dir>
"""
import json
import os
import re
import sys

import scrape as S

# candidate id -> (Amazon ASINs to re-read, 1688 queries, regexes that ALL must match, exclude regex, yuan floor)
C7 = {
    "chair":     (["B0DQY63XXP", "B0GSQW89GZ"], ["人体工学椅 头枕 腰托 网布 4D扶手", "人体工学椅 4D扶手 头枕 脚托", "人体工学椅 衣架 头枕 网椅",
                                               "人体工学椅", "人体工学椅 头枕 4D"],
                  [r"人体工学|工学椅|办公椅|电脑椅|电竞椅", r"头枕|头靠|护颈|4D|3D|6D"], r"配件|椅套|气杆|椅垫$", 180),
    "petcart":   (["B0DPKLVZQY", "B0D9K3YKZT"], ["宠物推车 分离 大型犬 折叠", "宠物推车 折叠 大号 可拆"], [r"宠物", r"推车"], r"配件|雨罩", 120),
    "spinbike":  (["B0DT45QJ82", "B0FT74PG4F"], ["动感单车 磁控 家用 静音 app", "动感单车 家用 飞轮 磁控"], [r"单车"], r"配件|座垫|坐垫", 280),
    "pullup":    (["B09K3QQBKH", "B0FT7RDYXL"], ["引体向上 单杠 落地 折叠", "室内单杠 落地 折叠 家用"], [r"单杠|引体"], r"门框|儿童|配件", 120),
    "cupboard":  (["B0F1T4QMVT", "B0F7XMW9ZF"], ["厨房 电器柜 微波炉柜 推拉", "餐边柜 推拉板 电器柜 高柜"], [r"柜", r"推拉|抽板|拉板|微波炉"], r"配件|拉手", 200),
    "golfnet":   (["B0BVM96YM5", "B09P14XTCQ"], ["高尔夫练习网 大型 打击网 3米", "高尔夫练习笼 户外 打击网"], [r"高尔夫", r"网|笼"], r"推杆|果岭|球包|配件", 150),
    "mirrorcab": (["B0956R3T3L"], ["全身镜 首饰柜 落地 旋转", "穿衣镜 首饰收纳柜 带灯", "落地镜 收纳柜 首饰 LED"], [r"镜", r"首饰|收纳"], r"挂墙|壁挂", 200),
    "reformer":  (["B0FX9PQK6X", "B0FY2F85WW"], ["普拉提核心床 家用 折叠", "普拉提床 家用 折叠 收纳"], [r"普拉提"], r"弹簧配件|绳|垫子|瑜伽垫", 300),
    "dresser":   (["B0CRRB9DY4", "B0D25T97DS"], ["梳妆台 带led镜 翻盖", "梳妆台 带灯 镜子 收纳凳", "化妆台 led灯 镜子 抽屉 凳子"], [r"梳妆|化妆台|化妆桌", r"灯|led|LED"], r"配件|镜灯", 150),
    "babycrib":  (["B0GVQQFB1Q", "B0CKBF6PYH"], ["婴儿床 折叠 便携 游戏床", "婴儿床 可折叠 带尿布台 欧式"], [r"婴儿床|游戏床"], r"蚊帐|床围|床品|床垫", 200),
    "woodreformer": ([], ["普拉提核心床 木质 枫木 折叠", "实木普拉提床 家用"], [r"普拉提", r"木"], r"垫子|瑜伽垫", 300),
    "sofabed5":  ([], ["五合一 折叠沙发床 无骨架 压缩", "模块沙发 压缩 折叠 沙发床", "懒人沙发床 折叠 两用 压缩"], [r"沙发"], r"沙发套|垫子|配件", 200),
    "floorbed":  ([], ["儿童地床 围栏 落地床", "蒙特梭利 儿童床 围栏 地床", "儿童床 带护栏 落地 软包"], [r"床"], r"床垫|床围|蚊帐|婴儿床", 150),
    "cardcase":  ([], ["卡牌展示柜 铝合金 带锁 展会", "球星卡展示盒 铝框 带锁", "卡牌展示箱 带锁 铝合金"], [r"展示", r"锁"], r"卡砖|卡套|单格", 60),
    "sofa3":     (["B0BBVL8G36"], ["三人位沙发 布艺 弹簧 1.8米", "布艺沙发 三人 弹簧坐垫 小户型"], [r"沙发", r"三人|3人|1\.8|180|1\.9|2米"], r"沙发套|沙发床|懒人|单人", 300),
    "sofa2":     (["B0CL8VR5Y7", "B07P4N3SCF"], ["双人沙发 布艺 弹簧 1.5米", "双人位沙发 小户型 弹簧坐垫"], [r"沙发", r"双人|2人|二人|1\.5|150|1\.6|1\.7"], r"沙发套|沙发床|懒人|单人", 200),
    "treadmill": (["B0D4DCK3MN"], ["跑步机 家用 折叠 扶手 静音", "跑步机 家用 可折叠 带扶手 电动"], [r"跑步机"], r"配件|跑带|腰带|甩脂|按摩", 600),
    "walkpad":   (["B0FT2WVSJT"], ["走步机 家用 静音 宽跑带", "平板走步机 家用 静音 遥控"], [r"走步机|平板|跑步机"], r"配件|跑带|腰带|甩脂|按摩", 350),
    "tent2":     (["B08P5811G7"], ["双人帐篷 铝杆 遮光 户外", "2人帐篷 铝合金杆 防雨 黑胶"], [r"帐篷", r"双人|2人|二人|铝"], r"单人|地垫|天幕|配件", 60),
    "cooler":    (["B07BDX6TMJ"], ["拉杆保温箱 大容量 户外 滚轮", "户外冷藏箱 带轮 大号 保冰"], [r"保温箱|冷藏箱|冰桶|保冷箱", r"轮|拉杆"], r"泡沫|快递|食品级|配件", 60),
    "cattower":  (["B0FMJXRHFY"], ["猫爬架 实木 大型 原木", "猫爬架 实木 多层 大型 太空舱"], [r"猫爬架|猫树|猫架", r"实木|原木|木质"], r"配件|剑麻柱", 150),
    "catcage":   (["B0BBVX5LBH"], ["实木猫笼 双层 猫别墅", "木质猫笼 两层 带厕所"], [r"猫笼|猫别墅|猫柜|猫屋"], r"铁|配件", 200),
    "dogcage":   (["B0DQ176V5F"], ["实木狗笼 室内 木质", "木质狗笼 狗屋 室内 门"], [r"狗笼|狗屋|宠物笼|犬笼", r"木"], r"铁笼|方管|配件", 150),
    "stepstool": (["B006B9ZDCY"], ["铝合金 工作平台 折叠 马凳", "折叠马凳 铝合金 装修平台"], [r"平台|马凳|梯"], r"配件|脚手架管", 80),
    "screen":    (["B076J4R897"], ["投影幕布 支架 落地 100寸", "移动投影幕 支架 便携 落地"], [r"幕布|投影幕", r"支架|落地|移动|便携"], r"挂墙|壁挂|电动|配件", 60),
    "onepole":   (["B0B77BFNC3"], ["金字塔帐篷 4米 户外 露营", "印第安帐篷 4米 棉布 露营", "尖顶帐篷 大型 露营 4米"], [r"帐篷", r"金字塔|印第安|尖顶|蒙古包|钟形|铃铛"], r"单人|儿童|配件|地垫", 150),
}

# extra leads from re-screening the v6 data with the stricter P&L (2026-11-08)
X7 = {
    "highchair": (["ハイチェア 木製", "ベビーチェア 木製 成長"], ["实木成长椅 儿童 可调节 餐椅", "儿童成长椅 实木 宝宝餐椅 可升降"],
                  [r"椅"], r"配件|坐垫|餐盘$", 60),
    "widecot":   (["コット ワイド", "キャンプ コット"], ["行军床 加宽 折叠 户外 2way", "折叠行军床 宽80 户外 高低两用"],
                  [r"床"], r"配件|床垫|睡袋", 80),
    "motodolly": (["バイクドーリー", "バイクリフト"], ["摩托车 前轮 固定架 移车器", "摩托车 移车器 挪车 前轮"],
                  [r"摩托|电动车|移车"], r"配件|轮胎$", 60),
    "dryrack":   (["物干し 屋外 ステンレス"], ["不锈钢 晾衣架 户外 落地 庭院", "户外晾衣架 不锈钢 落地 双杆"],
                  [r"晾衣|晒"], r"配件|夹子|袜子", 60),
    "stairgate": (["ベビーゲート 階段上", "ベビーゲート 木製"], ["楼梯口护栏 实木 婴儿 安全门", "婴儿安全门 实木 楼梯 免打孔"],
                  [r"护栏|围栏|安全门|门栏"], r"配件|床围", 60),
}

# comparables the user questioned (search page 1)
JP_SEARCH = ["ピラティス リフォーマー", "ピラティスマシン 家庭用", "ドレッサー スツール 収納", "ドレッサー LED ミラー",
             "ベビーベッド 折りたたみ", "ソファベッド 5way", "ソファベッド 折りたたみ 圧縮", "フロアベッド 柵 子供",
             "トレカ ケース 鍵", "トレカ ディスプレイケース 大型", "全身鏡 ジュエリー 収納 回転", "ゴルフネット 大型",
             "ソファ 2人掛け", "ソファ 3人掛け",
             # current purchase badges of each candidate market (search cards; product-page badges are often missing)
             "オフィスチェア メッシュ", "ペットカート", "フィットネスバイク", "スピンバイク", "ぶら下がり健康器", "懸垂マシン",
             "食器棚", "レンジ台", "ゴルフ練習ネット", "ベビーベッド", "ドレッサー", "ジュエリー キャビネット スタンドミラー",
             "ソファ 4人掛け", "ルームランナー", "ウォーキングパッド", "ワンタッチテント", "ワンポールテント 大型",
             "クーラーボックス 大型", "猫 ケージ 2段 木製", "キャットタワー 木製 大型", "犬 ケージ 木製", "脚立 足場台 大型",
             "プロジェクタースクリーン 自立式",
             # follow-ups (2026-11-08): products the first searches did not reach
             "フロアベッド 子供 柵付き", "キッズベッド 床置き 柵", "トレカ ディスプレイケース 鍵付き", "カード ディスプレイケース 鍵 アルミ"]
EXTRA_ASINS = ["B07P4N3SCF", "B0H3K9ND5C", "B0F2YZ38QG", "B0GYHY51T3", "B0H5WQXLQ6", "B0FQTHPT2B", "B0BY84DW8B"]


def run_amazon(out):
    S.session_init()
    asins = list(dict.fromkeys([a for v in C7.values() for a in v[0]] + EXTRA_ASINS))
    det_p, srch_p = os.path.join(out, "jp_det.json"), os.path.join(out, "jp_search.json")
    det = json.load(open(det_p, encoding="utf-8")) if os.path.exists(det_p) else {}
    for a in asins:
        if det.get(a, {}).get("ok"):
            continue
        det[a] = S.amazon_detail(a)
        json.dump(det, open(det_p, "w", encoding="utf-8"), ensure_ascii=False)
        print("dp", a, det[a].get("ok"), det[a].get("price"), det[a].get("bought"), det[a].get("title", "")[:40], flush=True)
    srch = json.load(open(srch_p, encoding="utf-8")) if os.path.exists(srch_p) else {}
    for kw in JP_SEARCH:
        if srch.get(kw):
            continue
        srch[kw] = S.amazon_search(kw)
        json.dump(srch, open(srch_p, "w", encoding="utf-8"), ensure_ascii=False)
        print("s", kw, len(srch[kw]), flush=True)
    print("DONE", flush=True)


def matched(offers, musts, excl, floor):
    out, seen = [], set()
    for o in offers:
        t = o["title"]
        if o["price"] < floor or (excl and re.search(excl, t)) or not all(re.search(m, t) for m in musts):
            continue
        if o["id"] in seen:
            continue
        seen.add(o["id"])
        out.append(o)
    return out


def run_cn(out):
    p = os.path.join(out, "cn7.json")
    res = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    for k, (_, qs, musts, excl, floor) in C7.items():
        allo = []
        for q in qs:
            allo += S.m1688_market(q)
        m = matched(allo, musts, excl, floor)
        res[k] = dict(n_all=len(allo), offers=sorted(m, key=lambda o: -o["sold"]))
        json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        print(k, len(allo), len(m), flush=True)
    print("DONE", flush=True)


def run_extra(out):
    S.session_init()
    p = os.path.join(out, "extra7.json")
    res = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    for k, (kws, qs, musts, excl, floor) in X7.items():
        if res.get(k):
            continue
        allo = []
        for q in qs:
            allo += S.m1688_market(q)
        res[k] = dict(cn=sorted(matched(allo, musts, excl, floor), key=lambda o: -o["sold"]),
                      amazon={kw: S.amazon_search(kw) for kw in kws})
        json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        print(k, len(allo), len(res[k]["cn"]), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    {"amazon": run_amazon, "cn": run_cn, "extra": run_extra}[mode](out)
