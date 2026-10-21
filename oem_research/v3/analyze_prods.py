# -*- coding: utf-8 -*-
"""Product-level screen for v4: every Amazon listing >=10,000 yen selling >=100/month.

For each product: package (page value or estimate), 160-size test, 1688 cost for the same
product type, price gap (Amazon price / 1688 cost in yen) and the real P&L at 天瞳 rates.
"""
import json
import re
import statistics as st
import sys

import analyze_v4 as A

SPEC_UP = 1.2   # our upgraded spec costs ~20% more than the 1688 median
BRAND_LOCK = ("koala", "コアラ", "ERGOTRON", "エルゴトロン", "FLEXISPOT", "イトーキ", "オカムラ", "ニトリ", "無印",
              "Coleman", "コールマン", "snow peak", "スノーピーク", "ロゴス", "LOGOS", "DARTSLIVE", "ダーツライブ",
              "Herman", "パナソニック", "フランスベッド", "シモンズ", "西川", "長谷川工業", "Hasegawa", "エアウィーヴ",
              "ルネサンス", "ワンダーコア", "ショップジャパン", "アルインコ", "ALINCO", "カリモク")


import html as _html
import os

CACHE = os.environ.get("OEM_CACHE", "")
_RX_KG = re.compile(r"(?:商品の重量|本体重量|製品重量|重量)\s*[:：]?\s*約?\s*([\d.,]+)\s*(キログラム|kg|Kg|KG|ポンド|グラム)")
_RX_PKG = re.compile(r"(?:梱包サイズ|梱包寸法|外箱サイズ|段ボールサイズ)[^\d]{0,12}([\d.]+)\s*[x×*]\s*([\d.]+)\s*[x×*]\s*([\d.]+)\s*(cm|mm)?")
_RX_PKG_KG = re.compile(r"(?:梱包重量|梱包時重量|総重量)\s*[:：]?\s*約?\s*([\d.]+)\s*(kg|KG|キログラム)")


def raw_specs(asin):
    """Weight / package size read from the cached product page text (more robust than the scraper fields)."""
    f = os.path.join(CACHE, "amz_d", f"{asin}.html")
    if not os.path.exists(f):
        return {}
    s = open(f, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", s, flags=re.S)))
    out = {}
    m = _RX_KG.search(t)
    if m:
        v = float(m.group(1).replace(",", ""))
        out["kg"] = {"グラム": v / 1000, "ポンド": v * 0.4536}.get(m.group(2), v)
    m = _RX_PKG.search(t)
    if m:
        v = sorted([float(m.group(i)) for i in (1, 2, 3)], reverse=True)
        if m.group(4) == "mm":
            v = [x / 10 for x in v]
        if 20 < v[0] < 300:
            out["pkg"] = v
    m = _RX_PKG_KG.search(t)
    if m and 0.5 < float(m.group(1)) < 150:
        out["pkg_kg"] = float(m.group(1))
    return out


def sub_rank(bsr):
    m = re.findall(r"([^\s()]+)\s*-\s*([\d,]+)位", bsr or "")
    return (m[-1][0], int(m[-1][1].replace(",", ""))) if m else (None, None)


def evaluate(scan, prods, det):
    out = []
    for a, p in prods.items():
        d = det.get(a, {})
        kw = p["kws"][0]
        rec = scan[kw]
        price = p["price"]
        rs = raw_specs(a)
        pk = None
        if rs.get("pkg") and (rs.get("pkg_kg") or rs.get("kg")):
            L, W, H = rs["pkg"]
            pk = (L, W, H, rs.get("pkg_kg") or rs["kg"] * 1.1 + 0.5, "梱包サイズ（商品ページ記載）")
        elif rs.get("kg") or d:
            dd = dict(d)
            if rs.get("kg"):
                dd["weight"] = f"{rs['kg']} キログラム"
            pk = A.package(rec["dens"], [dd])
        lo, hi = price / 1.1 / A.FX * 0.05, price / 1.1 / A.FX * 0.45
        offers = [o for o in rec.get("offers", []) if lo <= o["price"] <= hi]
        cost = st.median([o["price"] for o in offers]) if offers else None
        r = dict(asin=a, title=p["title"], price=price, bought=p["bought"], reviews=p["reviews"], rating=p["rating"],
                 kw=kw, kws=p["kws"], group=p["group"], cls=rec["fee"], cn=rec["cn"], cost=cost, n_offers=len(offers),
                 offers_sold=sum(o["sold"] for o in offers), bsr=d.get("bsr", ""), hist=d.get("hist", {}),
                 weight=d.get("weight", ""), dims=d.get("dims", ""), pkgtxt=d.get("pkg", ""),
                 brand_lock=any(b.lower() in p["title"].lower() for b in BRAND_LOCK))
        r["sub_cat"], r["sub_rank"] = sub_rank(r["bsr"])
        h = r["hist"]
        r["neg"] = (h.get("1", 0) + h.get("2", 0)) if h else None
        if pk:
            L, W, H, kg, src = pk
            r.update(L=L, W=W, H=H, kg=kg, pk_src=src, s3=L + W + H)
            r["size160"] = (L + W + H) >= 160 or kg >= 30
        if pk and cost:
            r["gap"] = price / (cost * A.FX)
            e = A.econ(price, cost * SPEC_UP, L, W, H, kg, rec["fee"])
            if e:
                r.update(e)
                r["judge"] = "GO" if e["tm"] >= 0.30 and e["r5"] >= 0.15 else ("COND" if e["tm"] >= 0.25 and e["r5"] >= 0.10 else "NO")
                r["profit_month"] = p["bought"] * e["p5"]
        out.append(r)
    return out


if __name__ == "__main__":
    scan = json.load(open(sys.argv[1], encoding="utf-8"))
    prods = json.load(open(sys.argv[2], encoding="utf-8"))
    det = json.load(open(sys.argv[3], encoding="utf-8"))
    rows = evaluate(scan, prods, det)
    json.dump(rows, open(sys.argv[4], "w", encoding="utf-8"), ensure_ascii=False)
    ok = [r for r in rows if r.get("judge") and r.get("size160")]
    ok.sort(key=lambda r: -r["profit_month"])
    print("evaluated", len(rows), "with econ", sum(1 for r in rows if r.get("judge")), "160size+", len(ok),
          "GO", sum(1 for r in ok if r["judge"] == "GO"))
    for r in ok[:120]:
        print(f"{r['judge']:4s} {r['bought']:5d}u ¥{r['price']:7.0f} pkg{r['L']:.0f}x{r['W']:.0f}x{r['H']:.0f} {r['kg']:.0f}kg "
              f"[{r['pk_src'][:2]}] cost{r['cost']:.0f}元 gap{r['gap']:.1f}x tm{r['tm']*100:4.0f}% r5{r['r5']*100:4.0f}% "
              f"月利¥{r['profit_month']/1e4:5.0f}万 {'BRAND ' if r['brand_lock'] else ''}{r['sub_cat'] or ''}{r['sub_rank'] or ''}位 | {r['title'][:44]}")
