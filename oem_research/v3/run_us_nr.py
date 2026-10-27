# -*- coding: utf-8 -*-
"""Crawl Amazon.com New Releases: root categories and their sub-categories (breadth first,
depth 3, pages 1-2). Writes {path: {cat, items}}."""
import json
import os
import sys

import us_scrape as U

ROOTS = ["home-garden", "sporting-goods", "hi", "lawn-garden", "baby-products", "pet-supplies", "automotive",
         "toys-and-games", "office-products", "kitchen", "musical-instruments", "hpc", "appliances"]
out, max_pages = sys.argv[1], int(sys.argv[2])
res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
queue = [(r, 0) for r in ROOTS]
seen = set()
while queue and len(seen) < max_pages:
    path, depth = queue.pop(0)
    if path in seen:
        continue
    seen.add(path)
    items, kids, cat = U.new_releases(path, 1)
    more, _, _ = U.new_releases(path, 2)
    res[path] = dict(cat=cat, depth=depth, items=items + more)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    big = sum(1 for x in items + more if (x["usd"] or 0) >= 70)
    print(f"{len(seen)} d{depth} {path} {cat}: {len(items + more)} items, >=$70: {big}, kids {len(kids)}", flush=True)
    if depth < 3:
        queue += [(k, depth + 1) for k in kids if k not in seen]
print("DONE", flush=True)
