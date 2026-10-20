# -*- coding: utf-8 -*-
"""v4 phase 1: Amazon search pages 1-2 + 1688 market page for every keyword in keywords_v4."""
import json
import os
import sys

import scrape as S
from keywords_v4 import K

out = sys.argv[1]
res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
print("JP address set:", S.session_init(), flush=True)
for i, (grp, kw, cn, fee, dens, rel) in enumerate(K):
    if kw in res and res[kw].get("items"):
        continue
    items = S.amazon_search(kw, 1) + S.amazon_search(kw, 2)
    seen, uniq = set(), []
    for it in items:
        if it["asin"] not in seen:
            seen.add(it["asin"])
            uniq.append(it)
    offers = S.m1688_market(cn)
    res[kw] = dict(group=grp, cn=cn, fee=fee, dens=dens, rel=rel, items=uniq, offers=offers)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{i+1}/{len(K)} {kw}: {len(uniq)} items, badges={sum(x['bought'] for x in uniq)}, 1688={len(offers)}", flush=True)
