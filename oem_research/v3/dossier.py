import json, sys, analyze as A
scan=json.load(open(sys.argv[1],encoding='utf-8')); det=json.load(open(sys.argv[2],encoding='utf-8'))
kws=sys.argv[3].split(',')
for kw in kws:
    m=A.market(kw,scan[kw])
    print(f"\n######## {kw}  market≈{m['market_u']}u/月 ¥{m['market_yen']/1e6:.1f}M  pmed¥{m['price_med']}  1688cost={m['cost']}元 ({m['n_offers']} offers, 月销{m['offers_sold']})")
    for x in m['top10'][:8]:
        d=det.get(x['asin'],{})
        h=d.get('hist',{}); neg=(h.get('1',0)+h.get('2',0)) if h else None
        print(f" {x['bought']:5d}u ¥{x['price']:7.0f} ★{x['rating']} rv{x['reviews']:6d} {x['asin']} | {x['title'][:70]}")
        if d: print(f"        kg={d.get('weight','')[:18]} dims={d.get('dims','')[:45]} pkg={d.get('pkg','')[:30]} | BSR={d.get('bsr','')[:90]} | 1-2★={neg}%")
    offs=[o for o in scan[kw]['offers']]
    lo=(m['price_med'] or 0)/1.1/23.5*0.06; hi=(m['price_med'] or 0)/1.1/23.5*0.5
    print("  1688:", '; '.join(f"¥{o['price']}/{o['sold']} {o['title'][-26:]}" for o in offs if lo<=o['price']<=hi)[:900])
