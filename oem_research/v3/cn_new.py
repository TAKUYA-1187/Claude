# -*- coding: utf-8 -*-
"""China new-product proxy (Amazon China has had no web shop since 2024-01-27): 1688 listings
titled 2026新款 / 新品 in large-item categories, ranked by monthly sales."""
import json
import os
import re
import sys

import scrape as S

TERMS = ["户外家具", "庭院秋千", "冰浴桶", "冷水浴缸", "桑拿房", "汗蒸房", "隔音舱", "电竞椅", "人体工学椅", "升降桌",
         "梳妆台", "衣柜", "餐边柜", "沙发床", "懒人沙发", "智能床", "床架", "猫爬架", "狗笼", "宠物别墅", "婴儿床",
         "儿童滑梯", "儿童秋千", "蹦床", "健身器材", "动感单车", "划船机", "走步机", "综合训练器", "哑铃凳", "拳击架",
         "乒乓球桌", "台球桌", "高尔夫练习网", "帐篷", "天幕", "露营车", "折叠床", "车顶帐篷", "车载冰箱支架", "移动车库",
         "遮阳棚", "凉亭", "阳光房", "花园围栏", "烧烤炉", "披萨炉", "围炉煮茶桌", "收纳柜", "工具车", "置物架",
         "电动搬运车", "爬楼车", "鱼缸", "鸟笼", "按摩椅", "按摩床", "理发椅", "美甲桌", "麻将机", "赛车座椅", "游戏机台"]

if __name__ == "__main__":
    out = sys.argv[1]
    res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
    for t in TERMS:
        kw = "2026新款 " + t
        if kw in res:
            continue
        res[kw] = [o for o in S.m1688_market(kw) if re.search(r"2026|新款|新品", o["title"])]
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(kw, len(res[kw]), "sold", sum(o["sold"] for o in res[kw]), flush=True)
    print("DONE", flush=True)
