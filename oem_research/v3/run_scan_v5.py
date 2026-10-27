# -*- coding: utf-8 -*-
"""v5 phase 1, run as two processes in parallel (different hosts):
  run_scan_v5.py amazon out_amazon.json   - Amazon.co.jp search pages 1-2 for every keyword
  run_scan_v5.py 1688   out_1688.json     - 1688 market page for every keyword's Chinese term
merge_scan() joins them into the scan dict used by analyze_final (keyword -> items + offers)."""
import json
import os
import sys

from keywords_v5 import K


def merge_scan(amazon_path, cn_path):
    am = json.load(open(amazon_path, encoding="utf-8"))
    cn = json.load(open(cn_path, encoding="utf-8"))
    out = {}
    for grp, kw, c, fee, dens, rel in K:
        if kw in am:
            out[kw] = dict(group=grp, cn=c, fee=fee, dens=dens, rel=rel, items=am[kw], offers=cn.get(c, []))
    return out


if __name__ == "__main__":
    import scrape as S
    mode, out = sys.argv[1], sys.argv[2]
    res = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
    if mode == "amazon":
        print("JP address set:", S.session_init(), flush=True)
    for i, (grp, kw, cn, fee, dens, rel) in enumerate(K):
        key = kw if mode == "amazon" else cn
        if res.get(key):
            continue
        if mode == "amazon":
            seen, uniq = set(), []
            first = S.amazon_search(kw, 1)
            # page 2 only where page 1 shows a selling listing of 8,000 yen or more (halves the requests)
            more = S.amazon_search(kw, 2) if any((x["price"] or 0) >= 8000 and x["bought"] >= 50 for x in first) else []
            for it in first + more:
                if it["asin"] not in seen:
                    seen.add(it["asin"])
                    uniq.append(it)
            res[key] = uniq
            msg = f"{len(uniq)} items, badges={sum(x['bought'] for x in uniq)}"
        else:
            res[key] = S.m1688_market(cn)
            msg = f"{len(res[key])} offers"
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{i + 1}/{len(K)} {key}: {msg}", flush=True)
    print("DONE", flush=True)
