# -*- coding: utf-8 -*-
"""Unmet needs from Amazon.co.jp product pages: wishes in reviews ("…があれば", "もう少し…",
"サイズ展開が…") and the mixed points of Amazon's review summary ("…については意見が分かれています").

usage: needs.py scan.json prods.json detail.json out.json [max_pages]
Picks the best-selling listing (>= 10,000 yen) of every keyword market, fetches missing
product pages slowly, and extracts the wish sentences per market."""
import html
import json
import os
import re
import sys

WISH = re.compile(r"[^。！!？?\n]{0,60}(あれば|あったら|欲しい|ほしい|だったら|なら良|ならよ|もう少し|もっと|残念|惜しい|"
                  r"サイズ展開|サイズ違い|色違い|大きいサイズ|小さいサイズ|幅広|ロング|高さが足り|低すぎ|高すぎ|狭い|小さ|大き|"
                  r"付いていな|ついていな|別売|無いので|ないので)[^。！!？?\n]{0,60}")
THEME = [
    ("サイズ・寸法の不足（大きい/小さい/高さ/幅の展開）", r"サイズ|大き|小さ|高さ|低|幅|狭|奥行|長さ|ロング|ワイド"),
    ("付属品・機能が欲しい（別売・付いていない）", r"付いてい|ついてい|別売|付属|欲しい|ほしい|あれば|あったら"),
    ("色・デザインの選択肢", r"色|カラー|デザイン|木目|白|黒"),
    ("強度・耐久・ぐらつき", r"強度|耐久|壊れ|ぐらつ|グラグラ|しな|折れ|錆"),
    ("組立・説明書", r"組立|組み立|説明書|取説|ネジ"),
    ("重さ・移動", r"重|移動|運"),
    ("音・臭い・快適性", r"音|臭|におい|硬|柔|蒸れ|暑"),
]


def page_text(path):
    s = open(path, encoding="utf-8", errors="ignore").read()
    return s, re.sub(r"\s+", " ", html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", s, flags=re.S)))


def ai_summary(t):
    """Amazon's generated review summary on the product page (customers say …)."""
    i = t.find("お客様の投稿に基づきAIで生成されたものです")
    if i < 0:
        return ""
    j = max(t.rfind("お客様のご意見", 0, i), t.rfind("お客様は", 0, i) - 5, i - 700)
    return t[j:i].strip()


def wishes(texts):
    out = []
    for t in texts:
        for m in WISH.finditer(t):
            w = m.group(0).strip(" 、")
            if 8 <= len(w) <= 120:
                out.append(w)
    return out


def themes(ws):
    c = {}
    for w in ws:
        for name, rx in THEME:
            if re.search(rx, w):
                c[name] = c.get(name, 0) + 1
    return sorted(c.items(), key=lambda kv: -kv[1])


def pick(scan, prods):
    """Best-selling listing >= 10,000 yen per keyword market (one per ASIN)."""
    best = {}
    for a, p in prods.items():
        kw = p["kws"][0]
        if kw not in best or (p["bought"], p["reviews"] or 0) > (prods[best[kw]]["bought"], prods[best[kw]]["reviews"] or 0):
            best[kw] = a
    return best


if __name__ == "__main__":
    import scrape as S
    scan_p, prods_p, det_p, out_p = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 9999
    scan = json.load(open(scan_p, encoding="utf-8"))
    prods = json.load(open(prods_p, encoding="utf-8"))
    det = json.load(open(det_p, encoding="utf-8"))
    best = pick(scan, prods)
    order = sorted(best.items(), key=lambda kv: -prods[kv[1]]["bought"] * prods[kv[1]]["price"])[:limit]
    S.session_init()
    res = json.load(open(out_p, encoding="utf-8")) if os.path.exists(out_p) else {}
    for kw, a in order:
        if a not in det or not det[a].get("ok"):
            det[a] = S.amazon_detail(a)
            json.dump(det, open(det_p, "w", encoding="utf-8"), ensure_ascii=False)
        f = os.path.join(S.CACHE, "amz_d", f"{a}.html")
        if not os.path.exists(f):
            continue
        _, t = page_text(f)
        revs = [r[1] for r in det[a].get("reviews_txt") or []]
        w = wishes(revs)
        res[kw] = dict(asin=a, title=prods[a]["title"], price=prods[a]["price"], bought=prods[a]["bought"],
                       reviews=prods[a]["reviews"], summary=ai_summary(t)[:700], wishes=w[:12], themes=themes(w),
                       hist=det[a].get("hist"))
        json.dump(res, open(out_p, "w", encoding="utf-8"), ensure_ascii=False)
        print(kw, a, len(revs), len(w), flush=True)
    print("DONE", flush=True)
