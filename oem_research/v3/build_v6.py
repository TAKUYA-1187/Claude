# -*- coding: utf-8 -*-
"""Build the v6 workbook: v5 plus 11 market needs and improvements (what the best sellers'
reviews ask for but no listing offers: sizes, accessories, functions, added value).

usage: OEM_DATA=<dir> OEM_DATAMOD=data_v6 python3 build_v6.py <template.xlsx> <out.xlsx>
OEM_DATA holds the v5 files plus needs.json (needs.py)."""
import os
import re
import sys
from urllib.parse import quote

os.environ.setdefault("OEM_DATAMOD", "data_v6")
import build_v5 as W  # noqa: E402

V, B, D, put, head_row, link = W.V, W.B, W.D, W.put, W.head_row, W.link
NEEDS = V.load("needs.json")
MIXED = re.compile(r"一方|ただし|しかし|反面|不満|意見が分かれ|指摘")


def mixed_part(summary):
    """The part of Amazon's review summary that lists complaints or split opinions."""
    m = MIXED.search(summary or "")
    return summary[m.start():].strip() if m else ""


def ref_offer_kw(kw):
    rec = V.SCAN.get(kw, {})
    x = dict(type=V.KW2T.get(kw), kw=kw, cost=None)
    o = V.ref_offer(x)
    return o or (max(rec.get("offers") or [{}], key=lambda o: o.get("sold", 0)) if rec.get("offers") else None)


def build_needs(ws):
    ws.title = "11_市場ニーズと改良点"
    put(ws, "A1", "市場ニーズがあるのに商品がない／サイズ展開がない／付加価値をつければ売れる：売れ筋1位のレビューから", B.F_TITLE, border=False)
    put(ws, "A2", f"{len(NEEDS)}市場の売れ筋1位（¥1万以上）の商品ページから、Amazonのレビュー要約（不満・意見が分かれる点）と、"
                  "レビュー本文の要望（『〜があれば』『もう少し〜』『別売』『サイズ』等）を抽出。上段＝改良案を書いた市場、下段＝全市場の抽出結果。",
        B.F_NOTE, border=False)
    head_row(ws, 4, ["評価", "市場（検索語）", "売れ筋1位（Amazon）", "価格", "月販（下限）", "評価数", "足りないもの（分類）",
                     "改良すべき点・商品化案", "Amazonレビュー要約（不満・意見が分かれる点）", "お客様の声（要望の抜粋）",
                     "1688参考出品", "Alibaba検索"],
             [6, 20, 40, 9, 8, 8, 22, 56, 56, 56, 34, 22], height=36)
    manual = D.NEEDS
    rank = {"◎": 0, "○": 1, "△": 2}
    keys = sorted(NEEDS, key=lambda k: (k not in manual, rank.get(manual.get(k, ("",))[0], 3),
                                         -(NEEDS[k]["bought"] * NEEDS[k]["price"])))
    r = 5
    for k in keys:
        v = NEEDS[k]
        mixed = mixed_part(v.get("summary"))
        if k not in manual and not (mixed or v.get("wishes")):
            continue
        ev, gap, plan, en = manual.get(k, ("", "", "", ""))
        vals = [ev, k, None, v["price"], v["bought"], v["reviews"], gap, plan, mixed[:400],
                "\n".join("・" + w[:90] for w in v.get("wishes", [])[:3])]
        for j, val in enumerate(vals, start=1):
            put(ws, f"{B.get_column_letter(j)}{r}", val, B.F_BOLD if j in (1, 8) and k in manual else B.F_SMALL,
                fmt=V.YEN if j == 4 else ("#,##0" if j in (5, 6) else None), align=B.WRAP_TL if j >= 7 else B.WRAP_C)
        link(ws, f"C{r}", V.AMZ + v["asin"], v["title"][:50])
        o = ref_offer_kw(k)
        if o and o.get("url"):
            link(ws, f"K{r}", o["url"], f"{o['title'][:22]}（{o['price']:.0f}元・月销{o['sold']}）")
        if en or V.KW2T.get(k) in getattr(D, "TYPE_EN", {}):
            link(ws, f"L{r}", W.AL + quote(en or D.TYPE_EN[V.KW2T[k]]))
        ws.row_dimensions[r].height = 90 if k in manual else 60
        r += 1
    ws.freeze_panes = "C5"
    for txt, fill in (("◎", B.FILL_GO), ("○", B.FILL_COND)):
        ws.conditional_formatting.add(f"A5:A{r}", V.CellIsRule(operator="equal", formula=[f'"{txt}"'], fill=fill))


def extra(wb):
    out = W.extra(wb)
    ws = wb.create_sheet("tmp")
    build_needs(ws)
    return out + [ws]


if __name__ == "__main__":
    V.main(sys.argv[1], sys.argv[2], extra=extra)
