import json, sys, analyze as A
scan=json.load(open(sys.argv[1],encoding='utf-8'))
rows=[A.market(kw,rec) for kw,rec in scan.items()]
rows.sort(key=lambda m:-m['market_yen'])
for m in rows:
    t=m['top1']
    if not t: continue
    print(f"{m['kw'][:16]:16s} n={m['n']:3d} b={m['n_badged']:2d} U={m['market_u']:5d} ¥{m['market_yen']/1e6:5.1f}M pmed={m['price_med'] or 0:7.0f} #1={t['bought']:4d}u ¥{t['price']:6.0f} rv{t['reviews']:5d} ★{t['rating']} cost={m['cost']} JP={m['bigjp_top10']} | {t['title'][:34]}")
