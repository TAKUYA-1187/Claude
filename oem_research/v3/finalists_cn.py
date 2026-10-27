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
    # v5 additions
    "firepit":   (["火盆桌 户外 带盖", "户外火盆桌 取暖 烧烤", "庭院火盆 方形 带盖"], [r"火盆|火炉|篝火"], 120),
    "golfnet":   (["高尔夫练习网 大型 打击网", "高尔夫练习笼 户外"], [r"高尔夫"], 150),
    "biketrailer": (["自行车拖车 载货 折叠", "自行车拖车 挂车 购物"], [r"拖车|挂车"], 120),
    "screen":    (["投影幕布 支架 落地 100寸", "移动投影幕 支架 便携"], [r"幕布|投影幕"], 60),
    "crosstrainer": (["椭圆机 家用 静音 磁控", "椭圆机 太空漫步机 家用"], [r"椭圆机|漫步机"], 400),
    "kidsbar":   (["儿童单杠 室内 折叠 宝宝", "儿童单杠 家用 可调节"], [r"单杠"], 60),
    "petcart":   (["宠物推车 大型犬 分离", "宠物推车 折叠 大号"], [r"推车"], 120),
    "dolly":     (["摩托车 移动器 前轮 支架", "摩托车 驻车架 前轮"], [r"摩托"], 60),
    "carbed":    (["海狮 床板 车载床", "车载床 后备箱 折叠床板"], [r"床"], 100),
    "woodstove": (["户外柴火炉 带玻璃 烟囱", "帐篷炉 柴火炉 不锈钢 玻璃"], [r"炉"], 150),
    "tentsauna": (["桑拿帐篷 带炉", "户外桑拿帐篷 套装 炉"], [r"桑拿|汗蒸"], 300),
    "horse":     (["骑马机 家用 健身", "骑马机 室内 减肥"], [r"骑马"], 150),
    "pizza":     (["户外披萨炉 木炭 便携", "披萨炉 燃气 户外"], [r"披萨|比萨"], 150),
    "plunge":    (["冰浴桶 折叠 成人", "冷水浴桶 户外 保温"], [r"浴桶|浴缸|冰浴"], 60),
    "smartbike": (["智能动感单车 app 磁控", "动感单车 FTMS 智能"], [r"单车"], 300),
    # US / China new products (08, 09 sheets)
    "us_cloudsofa": (["云朵沙发 模块 组合 L型", "压缩沙发 模块 云朵"], [r"沙发"], 300),
    "us_reformer": (["普拉提核心床 木质 家用 折叠", "普拉提床 家用 折叠"], [r"普拉提"], 300),
    "us_cardcase": (["卡牌展示柜 铝合金 带锁 展会", "球星卡展示盒 铝框 带锁"], [r"展示|卡"], 60),
    "us_woodpen": (["实木游戏围栏 折叠 婴儿", "木质宝宝围栏 折叠 可调"], [r"围栏|护栏"], 150),
    "us_bedrail": (["床围栏 三面 加长 防摔", "床护栏 宝宝 加高 三面套装"], [r"围栏|护栏"], 60),
    "us_romanchair": (["罗马椅 山羊挺身 家用", "罗马凳 背部训练"], [r"罗马"], 80),
    "us_pantry": (["钢制储物柜 高柜 带门 厨房", "铁皮柜 厨房 高柜 带门"], [r"柜"], 200),
    "us_glider": (["哺乳椅 摇椅 脚凳", "摇摇椅 单人 布艺 带脚凳"], [r"摇椅|哺乳"], 200),
    "cn_streamtank": (["溪流缸 侧滤", "溪流缸 生态 造景 全套"], [r"溪流"], 100),
    "cn_floatbed": (["悬浮床 碳素钢 架床", "悬浮床 铁艺 无床头"], [r"悬浮"], 300),
    "cn_dressernight": (["梳妆台 床头柜 一体", "化妆桌 床头柜一体"], [r"梳妆|化妆"], 150),
    "cn_steelwardrobe": (["钢制衣柜 推拉门 家用", "金属衣柜 推拉门 奶油风"], [r"衣柜"], 400),
    "cn_cloudsofabed": (["云朵沙发床 折叠两用", "沙发床 折叠 两用 云朵"], [r"沙发床"], 200),
    "cn_deskbike": (["动感单车 带桌板 磁控", "办公 健身车 带桌板"], [r"单车|健身车"], 300),
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
