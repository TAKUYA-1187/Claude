# -*- coding: utf-8 -*-
"""Fetch US product pages (size, weight, BSR, past-month purchases) for a selection file
{asin: new-release item} written from us_nr.json (see us_cats.BIG_CATS)."""
import json
import os
import sys

import us_scrape as U

sel, out = sys.argv[1], sys.argv[2]
best = json.load(open(sel, encoding="utf-8"))
res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
for i, (a, x) in enumerate(sorted(best.items(), key=lambda kv: (kv[1]["rank"] or 99))):
    if a in res:
        continue
    res[a] = dict(x, **U.product(a))
    if i % 10 == 0:
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(i, a, res[a].get("date"), res[a].get("bought"), flush=True)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("DONE", flush=True)
