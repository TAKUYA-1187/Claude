# -*- coding: utf-8 -*-
"""Phase 1: Amazon search pages 1-2 and the 1688 market page for every keyword."""
import json
import os
import sys

import scrape as S
from keywords import KEYWORDS

out = sys.argv[1]
print("JP address set:", S.session_init(), flush=True)
res = {}
if os.path.exists(out):
    res = json.load(open(out, encoding="utf-8"))
for i, (grp, kw, cn, fee) in enumerate(KEYWORDS):
    if kw in res and res[kw].get("items"):
        continue
    items = S.amazon_search(kw, 1) + S.amazon_search(kw, 2)
    seen, uniq = set(), []
    for it in items:
        if it["asin"] not in seen:
            seen.add(it["asin"])
            uniq.append(it)
    offers = S.m1688_market(cn)
    res[kw] = dict(group=grp, cn=cn, fee=fee, items=uniq, offers=offers)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{i+1}/{len(KEYWORDS)} {kw}: {len(uniq)} items, badges={sum(x['bought'] for x in uniq)}, 1688 offers={len(offers)}", flush=True)
