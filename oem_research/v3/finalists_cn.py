# -*- coding: utf-8 -*-
"""v4 phase 5: spec-matched 1688 searches for the finalist products.

Each entry: id -> (1688 keywords, list of regexes that ALL must match the offer title, yuan floor).
The cost used for a finalist is the median of the matched offers after trimming the top and
bottom quartile (cheap parts and premium/custom listings), so it reflects the mainstream spec.
"""
import json
import re
import statistics as st
import sys

import scrape as S

T2 = {
    "sauna":     (["桑拿帐篷 带炉子 套装", "帐篷桑拿 柴火炉 套装", "户外桑拿帐篷 柴火炉 烟囱"], [r"桑拿|汗蒸", r"炉"], 400),
    "chair":     (["人体工学椅 头枕 腰托 网布", "人体工学椅 4D扶手 头枕", "人体工学椅 衣架 头枕 网椅"], [r"人体工学", r"头枕|头靠"], 180),
    "showcase":  (["手办展示柜 led 玻璃门", "玻璃展示柜 带灯 手办 多层", "展示柜 led灯 玻璃 收藏 家用"], [r"展示柜|手办柜|收藏柜|陈列柜", r"灯|led|LED"], 200),
    "garage":    (["车库帐篷 3x6", "停车棚 3*6 镀锌", "户外车棚 帐篷 3x6米"], [r"车库|车棚|停车棚|车篷", r"3[x\*×X]6|6米|6m|3米"], 300),
    "swing":     (["户外秋千 双人 带顶棚", "庭院秋千椅 铁艺 三人", "秋千 户外 带遮阳棚"], [r"秋千"], 250),
    "spinbike":  (["动感单车 磁控 家用 静音", "动感单车 家用 飞轮 磁控"], [r"单车"], 280),
    "cycleport": (["自行车棚 户外 2辆", "自行车收纳棚 户外 防雨"], [r"车棚|收纳棚|自行车"], 150),
    "cupboard":  (["厨房 电器柜 微波炉柜 推拉", "餐边柜 推拉板 电器柜", "厨房收纳柜 微波炉 推拉 抽板"], [r"柜|架", r"推拉|抽板|拉板|微波炉"], 200),
    "benchpress":(["哑铃凳 可调节 商用", "哑铃凳 健身椅 可调 家用"], [r"哑铃凳|健身椅|卧推凳|健身凳"], 150),
    "pullup":    (["引体向上 单杠 落地 折叠", "室内单杠 落地 折叠 家用"], [r"单杠|引体"], 120),
    "jack":      (["卧式千斤顶 3吨 双泵", "卧式千斤顶 3t 低位 快速"], [r"千斤顶", r"3吨|3T|3t|3顿"], 150),
    "parcelbox": (["快递柜 户外 带信报箱", "快递箱 户外 大容量 信箱", "包裹箱 户外 带锁 信报箱"], [r"快递|包裹|信报|信箱"], 150),
    "catTower":  (["猫爬架 实木 大型 原木", "猫爬架 实木 多层 大型"], [r"猫爬架|猫树|猫架", r"实木|原木"], 150),
    "desk":      (["电竞桌 升降 手摇", "游戏桌 电竞 升降"], [r"桌"], 150),
    "mattress":  (["独立袋装弹簧床垫 1.5米 压缩", "弹簧床垫 压缩卷 1.4", "袋装弹簧床垫 卷包 双人"], [r"床垫", r"弹簧"], 200),
    "dresser":   (["梳妆台 带led镜 翻盖", "梳妆台 带灯 镜子 收纳 卧室", "化妆台 led灯 镜子 抽屉"], [r"梳妆|化妆台|化妆桌", r"灯|led|LED"], 150),
    "wardrobe":  (["衣柜 烤漆 亮光 卧室", "衣柜 高光 烤漆 两门", "衣柜 亮光 推拉门 现代"], [r"衣柜|衣橱", r"烤漆|亮光|高光"], 300),
    "babycrib":  (["婴儿床 折叠 便携 游戏床", "婴儿床 可折叠 带尿布台 欧式"], [r"婴儿床|游戏床"], 200),
    "kotatsu":   (["日式暖桌 被炉 套装", "取暖桌 暖脚 电暖 桌被"], [r"暖桌|被炉|取暖桌"], 200),
    "ladder":    (["伸缩梯 铝合金 直梯 8米", "铝合金伸缩梯 多功能 人字梯 直梯"], [r"梯"], 150),
}


def trimmed_median(xs):
    xs = sorted(xs)
    n = len(xs)
    core = xs[n // 4: n - n // 4] if n >= 4 else xs
    return st.median(core) if core else None


if __name__ == "__main__":
    out = sys.argv[1]
    try:
        res = json.load(open(out, encoding="utf-8"))
    except FileNotFoundError:
        res = {}
    for fid, (kws, rxs, floor) in T2.items():
        if fid in res:
            continue
        seen, offers = set(), []
        for kw in kws:
            try:
                for o in S.m1688_market(kw):
                    key = (o["title"], o["price"])
                    if key in seen or o["price"] < floor or not all(re.search(x, o["title"]) for x in rxs):
                        continue
                    seen.add(key)
                    o["kw"] = kw
                    offers.append(o)
            except Exception as e:
                print("ERR", fid, kw, e, flush=True)
        res[fid] = offers
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(fid, len(offers), "trimmed median", trimmed_median([o["price"] for o in offers]),
              "sold", sum(o["sold"] for o in offers), flush=True)
