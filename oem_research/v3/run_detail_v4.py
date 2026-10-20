# -*- coding: utf-8 -*-
"""v4 phase 2: product pages for the top 3 listings of every keyword whose leaders sell at
7,000 yen or more and whose badge market is at least 1.5M yen a month."""
import json
import sys

import analyze_v4 as A
import scrape as S

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
    if m["band"] and m["band"] >= 7000 and m["market_yen"] >= 1_500_000:
        short.append((m["market_yen"], kw, m))
short.sort(reverse=True)
print("shortlist", len(short), flush=True)
for _, kw, m in short:
    for it in m["top10"][:3]:
        if it["asin"] in det:
            det[it["asin"]].setdefault("kws", []).append(kw)
            continue
        d = S.amazon_detail(it["asin"])
        d["kw"] = kw
        det[it["asin"]] = d
        json.dump(det, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(kw, it["asin"], d.get("ok"), (d.get("weight") or "")[:16], (d.get("pkg") or "")[:24], flush=True)
json.dump(det, open(out, "w", encoding="utf-8"), ensure_ascii=False)
