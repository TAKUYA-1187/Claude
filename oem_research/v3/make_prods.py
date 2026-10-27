# -*- coding: utf-8 -*-
"""Merge the v5 scans and list every relevant Amazon listing >= 10,000 yen with a >= 50/month badge (100+ is the target line).

usage: make_prods.py amazon.json cn_kw.json scan_out.json prods_out.json"""
import json
import re
import sys

from run_scan_v5 import merge_scan

am, cn, scan_out, prods_out = sys.argv[1:5]
scan = merge_scan(am, cn)
prods = {}
for kw, rec in scan.items():
    rx = re.compile(rec["rel"])
    for x in rec["items"]:
        if (x.get("price") or 0) >= 10000 and x["bought"] >= 50 and rx.search(x["title"]):
            p = prods.setdefault(x["asin"], dict(title=x["title"], price=x["price"], bought=x["bought"],
                                                 reviews=x["reviews"], rating=x["rating"], kws=[], group=rec["group"]))
            p["kws"].append(kw)
json.dump(scan, open(scan_out, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(prods, open(prods_out, "w", encoding="utf-8"), ensure_ascii=False)
print("keywords", len(scan), "products", len(prods))
