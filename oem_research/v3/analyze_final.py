# -*- coding: utf-8 -*-
"""v4 phase 4: re-evaluate every product with the targeted 1688 offers of its product type.

Cost (first screen): mainstream factory price of the product type = median of the middle
half of its 1688 offers. Finalists get spec-matched costs (finalists_cn.py, data_v4.py). Package: product page value, else the type's standard
export carton scaled by the listed product weight.

Usage: analyze_final.py scan_v4.json prods_v4.json detail_v4.json cn_v4.json eval_final.json
"""
import json
import sys

import analyze_prods as P
from finalists_cn import trimmed_median
import analyze_v4 as A
from type_map import KW2T, KW_PKG, REG, TYPE_PKG

GAP_MIN = 3.0   # Amazon price / 1688 cost in yen: "a real price gap"
BRAND_LOCK = P.BRAND_LOCK + ("NELL", "マニフレックス", "コクヨ", "サンワ", "オカムラ", "COFO", "山崎実業", "アイリスオーヤマ",
                              "AKRacing", "Aprica", "アップリカ")


def package(asin, t, det, kw=None):
    rs = P.raw_specs(asin)
    if rs.get("pkg") and (rs.get("pkg_kg") or rs.get("kg")):
        L, W, H = rs["pkg"]
        return L, W, H, rs.get("pkg_kg") or rs["kg"] * 1.1 + 1, "梱包サイズ（商品ページ記載）"
    std = TYPE_PKG.get(t) or KW_PKG.get(kw)
    if not std:
        return None
    L, W, H, kg = std
    k = rs.get("kg") or A.parse_kg(det.get("weight"))
    if k and 1 < k < 150:
        pk = k * 1.1 + 1
        f = min(1.25, max(0.8, (pk / kg) ** (1 / 3)))
        return L * f, W * f, H * f, pk, "推定（同種品の標準梱包×商品重量）"
    return L, W, H, kg, "推定（同種品の標準梱包）"


def run(scan, prods, det, cn):

    rows = []
    for a, p in prods.items():
        d = det.get(a, {})
        kw = p["kws"][0]
        rec = scan[kw]
        t = KW2T.get(kw)
        price = p["price"]
        offers = cn.get(t) or []
        if not offers:
            # keyword without a product type: its own 1688 market page, parts/accessories removed
            offers = [o for o in rec.get("offers") or [] if o["price"] >= price / 1.1 / A.FX * 0.05]
            offers = offers if len(offers) >= 5 else []
        r = dict(asin=a, title=p["title"], price=price, bought=p["bought"], reviews=p["reviews"], rating=p["rating"],
                 kw=kw, kws=p["kws"], group=p["group"], cls=rec["fee"], cn=rec["cn"], type=t, reg=REG.get(t, ""),
                 bsr=d.get("bsr", ""), hist=d.get("hist", {}), weight=d.get("weight", ""), dims=d.get("dims", ""),
                 brand_lock=any(b.lower() in p["title"].lower() for b in BRAND_LOCK), targeted=bool(offers))
        r["sub_cat"], r["sub_rank"] = P.sub_rank(r["bsr"])
        h = r["hist"]
        r["neg"] = (h.get("1", 0) + h.get("2", 0)) if h else None
        pk = package(a, t, d, kw)
        if pk:
            L, W, H, kg, src = pk
            r.update(L=L, W=W, H=H, kg=kg, pk_src=src, s3=L + W + H, size160=(L + W + H) >= 160 or kg >= 30)
        if offers:
            # first screen: mainstream factory price of the type = median of the middle half of its 1688 offers
            r["cost_fac"] = r["cost"] = trimmed_median([o["price"] for o in offers])
            r["n_offers"] = len(offers)
            r["offers_sold"] = sum(o["sold"] for o in offers)
        if pk and r.get("cost"):
            r["gap"] = price / (r["cost_fac"] * A.FX)
            e = A.econ(price, r["cost"], L, W, H, kg, rec["fee"])
            if e:
                r.update(e)
                r["judge"] = "GO" if e["tm"] >= 0.30 and e["r5"] >= 0.15 else ("COND" if e["tm"] >= 0.25 and e["r5"] >= 0.10 else "NO")
                r["profit_month"] = p["bought"] * e["p5"]
        r["ok_all"] = bool(r.get("judge") in ("GO", "COND") and r.get("size160") and price >= 10000
                           and r["bought"] >= 100 and (r.get("gap") or 0) >= GAP_MIN and not r["brand_lock"])
        rows.append(r)
    return rows


if __name__ == "__main__":
    a = sys.argv[1:]
    L = lambda p: json.load(open(p, encoding="utf-8"))
    rows = run(L(a[0]), L(a[1]), L(a[2]), L(a[3]))
    json.dump(rows, open(a[4], "w", encoding="utf-8"), ensure_ascii=False)
    ok = sorted([r for r in rows if r["ok_all"]], key=lambda r: -r["profit_month"])
    print("products", len(rows), "targeted", sum(r["targeted"] for r in rows), "with econ", sum(1 for r in rows if r.get("judge")),
          "all criteria", len(ok), "GO", sum(r["judge"] == "GO" for r in ok))
    for r in ok:
        print(f"{r['judge']:4s} {(r['type'] or r['kw'])[:10]:10s} {r['bought']:5d}u ¥{r['price']:7.0f} {r['L']:.0f}x{r['W']:.0f}x{r['H']:.0f} {r['kg']:.0f}kg"
              f"[{r['pk_src'][:2]}] {r['cost']:.0f}元 gap{r['gap']:.1f} dom{r['dom']:.0f}x{r['parcels']} tm{r['tm']*100:3.0f}% r5{r['r5']*100:3.0f}% "
              f"月利{r['profit_month']/1e4:4.0f}万 | {r['title'][:38]}")
