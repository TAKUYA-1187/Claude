# -*- coding: utf-8 -*-
"""Fetch product pages for every listing priced >=10,000 yen with a >=100/month badge."""
import json
import sys

import scrape as S

prods = json.load(open(sys.argv[1], encoding="utf-8"))
out = sys.argv[2]
try:
    det = json.load(open(out, encoding="utf-8"))
except FileNotFoundError:
    det = {}
S.session_init()
for i, (a, p) in enumerate(sorted(prods.items(), key=lambda kv: -kv[1]["bought"] * kv[1]["price"])):
    if a in det and det[a].get("ok"):
        continue
    d = S.amazon_detail(a)
    det[a] = d
    if i % 10 == 0:
        json.dump(det, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(i, a, d.get("ok"), (d.get("weight") or "")[:14], (d.get("pkg") or "")[:20], flush=True)
json.dump(det, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("DONE", flush=True)
