# -*- coding: utf-8 -*-
"""Markets with demand but few sales because the Amazon price is high.

For each keyword: the price band of relevant listings, how many actually sell (purchase
badges), interest signals (review counts in Japan, monthly sales of the same product on 1688)
and the 1688 mainstream cost. The 'reachable price' is the lowest price at which our product
still makes 30% on the template formula and 15% real margin at 天瞳 rates; when it is far
below what Amazon sellers charge, a cheaper entry can open the market."""
import re
import statistics as st

import analyze_v4 as A
from finalists_cn import trimmed_median


def reachable_price(cny, pkg, cls, va=500):
    """Lowest price (yen, step 100) that gives template >= 30% and real (ads 5%) >= 15%."""
    L, W, H, kg = pkg
    for p in range(5000, 400001, 100):
        e = A.econ(p, cny, L, W, H, kg, cls, va=va)
        if e and e["tm"] >= 0.30 and e["r5"] >= 0.15:
            return p, e
    return None, None


def latent(kw, rec, pkg, type_offers=None):
    rx = re.compile(rec["rel"])
    items = [x for x in rec["items"] if x.get("price") and x["price"] >= 4000 and rx.search(x["title"])]
    offers = (rec.get("offers") or []) + (type_offers or [])
    if len(items) < 5 or len(offers) < 5 or not pkg:
        return None
    prices = sorted(x["price"] for x in items)
    med = st.median(prices)
    # drop parts / accessories: offers under 5% of the Amazon median (net, in yuan)
    offers = [o for o in offers if o["price"] >= med / 1.1 / A.FX * 0.05]
    if len(offers) < 5:
        return None
    cost = trimmed_median([o["price"] for o in offers])
    units = sum(x["bought"] for x in items)
    reviews = sum(x["reviews"] or 0 for x in items)
    p, e = reachable_price(cost, pkg, rec["fee"])
    if not p:
        return None
    sellers_below = sum(1 for x in items if x["price"] <= p * 1.1)
    return dict(kw=kw, group=rec["group"], n=len(items), units=units, n_badged=sum(1 for x in items if x["bought"] >= 50),
                reviews=reviews, cn_sold=sum(o["sold"] for o in offers), cost=cost, med=med, p25=prices[len(prices) // 4],
                low=prices[0], reach=p, gap=med / (cost * A.FX), discount=1 - p / med, sellers_below=sellers_below, econ=e,
                top=max(items, key=lambda x: (x["bought"], x["reviews"] or 0)),
                cheapest=min(items, key=lambda x: x["price"]),
                offers=sorted(offers, key=lambda o: -o["sold"])[:5])


def is_latent(m):
    """High Amazon price, few sales, but interest exists and we can sell far cheaper."""
    return (m["med"] >= 15000 and m["units"] < 500 and m["discount"] >= 0.30 and m["sellers_below"] <= 3
            and (m["reviews"] >= 300 or m["cn_sold"] >= 1000))
