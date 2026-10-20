# -*- coding: utf-8 -*-
"""Phase 2: product pages for the leading listings of promising keywords.

Shortlist rule: badge-based market >= MIN_YEN per month and a market price
(median of badged listings) between PRICE_LO and PRICE_HI yen.
"""
import json
import sys

import analyze as A
import scrape as S

MIN_YEN, PRICE_LO, PRICE_HI, TOPN = 8_000_000, 6000, 45000, 4

scan_path, out = sys.argv[1], sys.argv[2]
S.session_init()
scan = json.load(open(scan_path, encoding="utf-8"))
try:
    det = json.load(open(out, encoding="utf-8"))
except FileNotFoundError:
    det = {}
short = []
for kw, rec in scan.items():
    m = A.market(kw, rec)
    if m["price_med"] and PRICE_LO <= m["price_med"] <= PRICE_HI and m["market_yen"] >= MIN_YEN:
        short.append((m["market_yen"], kw, m))
short.sort(reverse=True)
print("shortlist", len(short), flush=True)
for _, kw, m in short:
    for it in m["top10"][:TOPN]:
        if it["asin"] in det:
            continue
        d = S.amazon_detail(it["asin"])
        d["kw"] = kw
        det[it["asin"]] = d
        json.dump(det, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(kw, it["asin"], d.get("ok"), d.get("weight", "")[:20], d.get("pkg", "")[:20], flush=True)
