# -*- coding: utf-8 -*-
"""Score each keyword market for a realistic 'become No.1' OEM launch.

profit_at_no1 = No.1's monthly units (badge) x our unit profit at the No.1 price band
                (real P&L, ads 5%). Our cost = 1688 band median x 1.25 for the upgraded spec.
"""
import json
import statistics as st

import analyze as A

SPEC_UP = 1.25


def score_all(scan, det):
    by_kw = {}
    for d in det.values():
        by_kw.setdefault(d.get("kw"), []).append(d)
    out = []
    for kw, rec in scan.items():
        m = A.market(kw, rec)
        if not m["top1"]:
            continue
        details = by_kw.get(kw, [])
        pk = A.pack_estimate(m["group"], details) if details else None
        top5 = [x for x in m["top10"][:5] if x["bought"] >= 50] or m["top10"][:3]
        band = st.median([x["price"] for x in top5]) if top5 else m["price_med"]
        hist = [d["hist"] for d in details if d.get("hist")]
        neg = st.mean([(h.get(1, 0) + h.get(2, 0)) for h in hist]) if hist else None
        r = dict(m)
        r.update(band=band, pk=pk, neg=neg, details=details)
        if pk and m["cost"]:
            cbm = pk["L"] * pk["W"] * pk["H"] / 1e6
            cny = m["cost"] * SPEC_UP
            e = A.econ(band, cny, cbm, pk["L"] + pk["W"] + pk["H"], pk["kg"], m["fee"])
            r.update(cbm=cbm, cny=cny, **e)
            r["profit_no1"] = m["top1_u"] * e["p5"]
            r["rev_no1"] = m["top1_u"] * band
            judge = "GO" if e["tm"] >= 0.30 and e["r5"] >= 0.15 else ("COND" if e["tm"] >= 0.25 and e["r5"] >= 0.10 else "NO")
            r["judge"] = judge
        else:
            r.update(judge="データ不足", profit_no1=None, rev_no1=None)
        out.append(r)
    return out


if __name__ == "__main__":
    import sys
    scan = json.load(open(sys.argv[1], encoding="utf-8"))
    det = json.load(open(sys.argv[2], encoding="utf-8"))
    rows = score_all(scan, det)
    rows = [r for r in rows if r.get("profit_no1") is not None]
    rows.sort(key=lambda r: -r["profit_no1"])
    for r in rows:
        pk = r["pk"]
        print(f"{r['judge']:4s} {r['kw'][:14]:14s} band¥{r['band']:6.0f} #1 {r['top1_u']:4d}u rv{r['top1']['reviews']:6d} ★{r['top10_rating'] or 0:.2f} neg{(r['neg'] or 0):3.0f}% "
              f"cost{r['cny']:5.0f}元 pkg{pk['L']:.0f}x{pk['W']:.0f}x{pk['H']:.0f} {pk['kg']:.1f}kg dom{r['dom']} tm{r['tm']*100:5.1f}% r5{r['r5']*100:5.1f}% p5¥{r['p5']:6.0f} "
              f"No1月利¥{r['profit_no1']/1e4:6.1f}万 No1月商¥{r['rev_no1']/1e4:6.0f}万 JP{r['bigjp_top10']} [{pk['src'][:2]}]")
