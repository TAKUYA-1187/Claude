# -*- coding: utf-8 -*-
"""v4 analysis with 天瞳's published rates (送料・保管料一覧表 2024.1.6版, 2024/8/1〜).

Domestic (Sagawa, packing material and handling included):
  60cm/2kg 690, 80/5 740, 100/10 920, 140/20 1,100, 160/30 1,400, 170/50 2,000, 180/50 2,500,
  200/50 3,200, 220/50 3,800, 240/50 5,050, 260/50 6,500 (120 size not listed -> 140 rate).
Sea freight per m3: 0-2m3 33,000 / 2-20m3 17,325 / >=20m3 13,125 / 40ft container 10,450.
Storage: 77 yen per m3 per day.
"""
import re
import statistics as st

FX = 23.5
SAGAWA = [(60, 2, 690), (80, 5, 740), (100, 10, 920), (140, 20, 1100), (160, 30, 1400), (170, 50, 2000),
          (180, 50, 2500), (200, 50, 3200), (220, 50, 3800), (240, 50, 5050), (260, 50, 6500)]
FR_TEMPLATE = 17325          # template / small orders (2-20 m3)
FR_SCALE = 13125             # orders of 20 m3 or more (a large-item business at scale)
STORAGE_DAY = 77
STORAGE_DAYS = 45
BIG_JP = ("アイリスオーヤマ", "アイリスプラザ", "IRIS", "山善", "YAMAZEN", "ニトリ", "リッチェル", "パナソニック",
          "無印", "天馬", "JEJ", "ドウシシャ", "コクヨ", "LIXIL", "YKK", "日本育児", "タンスのゲン", "萩原",
          "不二貿易", "ぼん家具", "LOWYA", "ベルメゾン", "大塚家具", "カリモク")


def ship_one(s3, kg):
    for up, mkg, rate in SAGAWA:
        if s3 <= up and kg <= mkg:
            return rate
    return None  # over 260cm or 50kg


def ship(L, W, H, kg):
    """Domestic rate; splits into 2-3 parcels when one parcel exceeds 260cm / 50kg."""
    for n in (1, 2, 3):
        r = ship_one(L / n + W + H, kg / n) if n > 1 else ship_one(L + W + H, kg)
        if r:
            return r * n, n
    return None, 0


def fee(price, cls):
    if cls == "F":
        return 0.154 * min(price, 20000) + 0.104 * max(0, price - 20000)
    return price * (0.154 if cls == "A" else 0.104)


def econ(price, cny, L, W, H, kg, cls, va=500, ad=0.05, fr=FR_SCALE):
    cbm = L * W * H / 1e6
    dom, n = ship(L, W, H, kg)
    if dom is None:
        return None
    J = cny * FX
    tq = price - J - dom - price * 0.165 - J * 0.2 - FR_TEMPLATE * cbm
    rev = price / 1.1
    landed = J * 1.08 + va + fr * cbm
    base = rev - fee(price, cls) - dom - rev * 0.04 - cbm * STORAGE_DAY * STORAGE_DAYS - landed
    return dict(tm=tq / price, r10=(base - rev * 0.10) / rev, r5=(base - rev * ad) / rev,
                p5=base - rev * ad, p10=base - rev * 0.10, dom=dom, parcels=n, cbm=cbm, landed=landed)


def parse_kg(w):
    m = re.search(r"([\d.,]+)\s*(キログラム|kg|Kg|KG|ポンド|グラム|g)\b", w or "")
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return {"グラム": v / 1000, "g": v / 1000, "ポンド": v * 0.4536}.get(m.group(2), v)


def parse_dims(t):
    m = re.search(r"([\d.]+)\s*(?:[^\d\sx×*]{0,4})\s*[x×*]\s*([\d.]+)\s*(?:[^\d\sx×*]{0,4})\s*[x×*]\s*([\d.]+)\s*(cm|mm|センチ)?", t or "")
    if not m:
        return None
    v = [float(m.group(i)) for i in (1, 2, 3)]
    if m.group(4) == "mm":
        v = [x / 10 for x in v]
    if max(v) > 400 or min(v) <= 0:
        return None
    return sorted(v, reverse=True)


def market(kw, rec, min_price=4000):
    rx = re.compile(rec["rel"])
    items = [x for x in rec["items"] if x.get("price") and x["price"] >= min_price and rx.search(x["title"])]
    badged = [x for x in items if x["bought"] >= 50]
    ranked = sorted(items, key=lambda x: (x["bought"], x["reviews"]), reverse=True)
    top = ranked[:10]
    top1 = ranked[0] if ranked else None
    leaders = [x for x in top[:5] if x["bought"] >= 50] or top[:3]
    band = st.median([x["price"] for x in leaders]) if leaders else None
    cost = None
    offers_in = []
    if band:
        lo, hi = band / 1.1 / FX * 0.05, band / 1.1 / FX * 0.45
        offers_in = [o for o in rec.get("offers", []) if lo <= o["price"] <= hi]
        if offers_in:
            cost = st.median([o["price"] for o in offers_in])
    return dict(kw=kw, group=rec["group"], cls=rec["fee"], dens=rec["dens"], cn=rec["cn"], n=len(items),
                n_badged=len(badged), market_u=sum(x["bought"] for x in items),
                market_yen=sum(x["bought"] * x["price"] for x in items), band=band, top1=top1, top10=top,
                top1_u=top1["bought"] if top1 else 0,
                top10_rating=st.mean([x["rating"] for x in top if x["rating"]]) if top and any(x["rating"] for x in top) else None,
                bigjp=sum(1 for x in top if any(b in x["title"] for b in BIG_JP)),
                cost=cost, n_offers=len(offers_in), offers_sold=sum(o["sold"] for o in offers_in),
                gap=(band / (cost * FX)) if band and cost else None)


def package(rec_dens, details):
    """Package (L, W, H, kg, source) from product pages of the market leaders."""
    kgs, pk, dims = [], [], []
    for d in details:
        k = parse_kg(d.get("weight"))
        if k and 0.5 < k < 150:
            kgs.append(k)
        p = parse_dims(d.get("pkg"))
        if p:
            pk.append(p)
        q = parse_dims(d.get("dims"))
        if q:
            dims.append(q)
    kg = st.median(kgs) * 1.1 + 0.5 if kgs else None
    if pk and kg:
        L, W, H = [st.median([p[i] for p in pk]) for i in range(3)]
        return L, W, H, kg, "梱包サイズ（商品ページ記載）"
    if kg:
        cbm = kg / rec_dens
        longest = st.median([d[0] for d in dims]) if dims else (cbm * 1e6) ** (1 / 3) * 1.6
        L = max(40.0, min(longest + 5, 200.0))
        H = (cbm * 1e6 / L / 4) ** 0.5
        W = 4 * H
        if W > L:
            W = H = (cbm * 1e6 / L) ** 0.5
        return L, W, H, kg, "推定（重量÷密度・製品寸法）"
    return None
