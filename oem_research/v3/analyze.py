# -*- coding: utf-8 -*-
"""Turn the raw scan into market metrics, unit economics and a #1-opportunity score.

Definitions (all per Amazon search keyword, pages 1-2, sponsored copies removed):
  bought      Amazon's "過去1か月でN点以上購入" badge = lower bound of monthly units
  market_u    sum of badges of all listed products (lower bound of keyword demand)
  market_yen  sum of badge x price
  top1        listing with the largest badge (ties -> more reviews) = current No.1
  cost        median 1688 price of offers priced within 6-50% of the Amazon market price
"""
import re
import statistics as st

from keywords import MIN_PRICE, REL

FX = 23.5
FR = 17325
SIZE = [(60, 650), (80, 750), (100, 900), (120, 1050), (140, 1250), (160, 1450), (170, 1900),
        (180, 2200), (200, 2700), (220, 3300), (240, 3900), (260, 4600), (99999, 7000)]
WEIGHT = [(2, 1), (5, 2), (10, 3), (15, 4), (20, 5), (30, 6), (50, 7), (1e9, 13)]
DENSITY = {"ペット": 170, "家具・収納": 210, "屋外": 190, "スポーツ": 220, "オフィス": 210,
           "キッズ": 140, "車・業務": 210}
BIG_JP = ("アイリスオーヤマ", "IRIS", "山善", "YAMAZEN", "ニトリ", "リッチェル", "パナソニック",
          "サンワ", "無印", "天馬", "JEJ", "ドウシシャ", "コクヨ", "LIXIL", "YKK", "日本育児", "タンスのゲン")


def ship(s, kg):
    si = next(i for i, (u, _) in enumerate(SIZE) if s <= u) + 1
    wi = next(idx for u, idx in WEIGHT if kg <= u)
    return SIZE[max(si, wi) - 1][1]


def econ(price, cny, cbm, s3, kg, fee, va=400, ad=0.05):
    J = cny * FX
    dom = ship(s3, kg)
    tq = price - J - dom - price * 0.165 - J * 0.2 - FR * cbm
    rev = price / 1.1
    landed = J * 1.08 + va + FR * cbm
    base = rev - price * fee - dom - rev * 0.04 - cbm * 3000 * 1.5 - 300 - landed
    return dict(tm=tq / price, r10=(base - rev * 0.10) / rev, r5=(base - rev * ad) / rev,
                p5=base - rev * ad, p10=base - rev * 0.10, dom=dom, landed=landed)


def parse_kg(w):
    m = re.search(r"([\d.,]+)\s*(キログラム|kg|Kg|KG|グラム|g)", w or "")
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return v / 1000 if m.group(2) in ("グラム", "g") else v


def parse_dims(t):
    m = re.search(r"([\d.]+)\s*(?:奥行き|幅|高さ|長さ)?\s*[x×]\s*([\d.]+)\s*(?:奥行き|幅|高さ|長さ)?\s*[x×]\s*([\d.]+)\s*(?:奥行き|幅|高さ|長さ)?\s*(cm|mm|センチ)?", t or "")
    if not m:
        return None
    v = [float(m.group(i)) for i in (1, 2, 3)]
    if m.group(4) == "mm":
        v = [x / 10 for x in v]
    return sorted(v, reverse=True)


def market(kw, rec):
    rx = re.compile(REL.get(kw, re.escape(kw.split()[0])))
    items = [x for x in rec["items"] if x.get("price") and x["price"] >= MIN_PRICE and rx.search(x["title"])]
    badged = [x for x in items if x["bought"] >= 50]
    mu = sum(x["bought"] for x in items)
    my = sum(x["bought"] * x["price"] for x in items)
    ranked = sorted(items, key=lambda x: (x["bought"], x["reviews"]), reverse=True)
    top = ranked[:10]
    top1 = ranked[0] if ranked else None
    pm = st.median([x["price"] for x in badged]) if badged else (st.median([x["price"] for x in items]) if items else None)
    # 1688 cost band
    cost = None
    offers_in = []
    if pm:
        lo, hi = pm / 1.1 / FX * 0.06, pm / 1.1 / FX * 0.50
        offers_in = [o for o in rec.get("offers", []) if lo <= o["price"] <= hi]
        if offers_in:
            cost = st.median([o["price"] for o in offers_in])
    bigjp = sum(1 for x in top if any(b in x["title"] for b in BIG_JP))
    return dict(kw=kw, group=rec["group"], fee=0.154 if rec["fee"] == "A" else 0.104, cn=rec["cn"],
                n=len(items), n_badged=len(badged), market_u=mu, market_yen=my, price_med=pm,
                top1=top1, top10=top, top1_u=top1["bought"] if top1 else 0,
                top3_reviews=st.median([x["reviews"] for x in top[:3]]) if top else 0,
                top10_rating=st.mean([x["rating"] for x in top if x["rating"]]) if top else None,
                bigjp_top10=bigjp, cost=cost, n_offers=len(offers_in),
                offers_sold=sum(o["sold"] for o in offers_in))


def pack_estimate(group, details):
    """Median package (sorted dims, kg) from product pages; flagged estimate when needed."""
    kgs, dims, pk = [], [], []
    for d in details:
        k = parse_kg(d.get("weight"))
        if k and 0.3 < k < 120:
            kgs.append(k)
        p = parse_dims(d.get("pkg"))
        if p and p[0] < 300:
            pk.append(p)
        q = parse_dims(d.get("dims"))
        if q and q[0] < 400:
            dims.append(q)
    kg = st.median(kgs) * 1.1 + 0.5 if kgs else None
    if pk:
        L, W, H = [st.median([p[i] for p in pk]) for i in range(3)]
        return dict(L=L, W=W, H=H, kg=kg, src="梱包サイズ（商品ページ記載）")
    if kg and dims:
        cbm = kg / DENSITY.get(group, 200)
        longest = st.median([d[0] for d in dims])
        L = max(40.0, min(longest * 0.95 + 5, 180.0))
        H = (cbm * 1e6 / L / 3) ** 0.5
        W = 3 * H
        if W > L:
            W = H = (cbm * 1e6 / L) ** 0.5
        return dict(L=L, W=W, H=H, kg=kg, src="推定（重量÷密度・製品寸法から）")
    return None
