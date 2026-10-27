# -*- coding: utf-8 -*-
"""Build the v5 workbook: the v4 workbook (data_v5) plus
  07 high-price / unopened markets, 08 US new releases not sold in Japan,
  09 China new products (1688 2026新款), 10 link list of the profitable products.

usage: OEM_DATA=<dir> OEM_DATAMOD=data_v5 python3 build_v5.py <template.xlsx> <out.xlsx>
OEM_DATA holds the v4 file names plus jp_check.json, us_det.json, cn_new.json, cn_kw.json."""
import json
import os
import re
import statistics as st
import sys
from urllib.parse import quote

os.environ.setdefault("OEM_DATAMOD", "data_v5")
import analyze_latent as LT  # noqa: E402
import build_v4 as V  # noqa: E402
from latent_concepts import CONCEPTS  # noqa: E402

B, D, put, head_row = V.B, V.D, V.put, V.head_row
YEN, PCT = V.YEN, V.PCT
AL = "https://www.alibaba.com/trade/search?SearchText="
JPC, USD = V.load("jp_check.json"), V.load("us_det.json")
CNNEW, CNKW = V.load("cn_new.json"), V.load("cn_kw.json")


def link(ws, ref, url, text=None):
    cell = put(ws, ref, text or url, B.F_LINK, align=B.LEFT_C)
    if url:
        cell.hyperlink = url
    return cell


def offer_cost(key):
    """Spec-matched 1688 offers for a concept (most sold first) and their mainstream price."""
    offers = sorted(V.FIN.get(key) or [], key=lambda o: -o["sold"])
    ps = sorted(o["price"] for o in offers)
    core = ps[len(ps) // 4: len(ps) - len(ps) // 4] or ps
    return offers, (st.median(core) if core else None)


def build_latent(ws):
    ws.title = "07_高価格で未開拓の市場"
    put(ws, "A1", "需要はあるがAmazonの価格が高くて売れていない市場（価格を下げれば開ける市場か）", B.F_TITLE, border=False)
    put(ws, "A2", "Amazon：本体の価格帯（付属品を除くため下限価格とタイトルで絞込み）。可能価格＝1688同等品の原価で天瞳表30%・実質15%を満たす最低売価。"
                  "値下げ余地＝1−可能価格÷Amazon中央値（プラスなら今より安く出せる）。", B.F_NOTE, border=False)
    head_row(ws, 4, ["市場", "Amazon本体の出品数", "Amazon中央値", "Amazon最安", "月販合計（下限）", "評価数合計", "1688同等品数", "1688原価（中央値・元）",
                     "1688月销合計", "価格差（倍）", "可能価格（天瞳30%）", "値下げ余地", "判定", "規制・注意", "Amazon代表品", "1688代表品", "Alibaba検索", "コメント"],
             [30, 8, 10, 10, 8, 8, 7, 9, 8, 7, 10, 7, 12, 22, 40, 40, 26, 50], height=40)
    r = 5
    for cid, name, kw, rx, floor, cterm, crx, cfloor, pkg, fee, reg in CONCEPTS:
        items = [x for x in V.SCAN.get(kw, {}).get("items", []) if (x.get("price") or 0) >= floor and re.search(rx, x["title"])]
        offers = [o for o in CNKW.get(cterm, []) if o["price"] >= cfloor and re.search(crx, o["title"])]
        if not items or not offers:
            continue
        med = st.median(sorted(x["price"] for x in items))
        ps = sorted(o["price"] for o in offers)
        cost = st.median(ps[len(ps) // 4: len(ps) - len(ps) // 4] or ps)
        reach, e = LT.reachable_price(cost, pkg, fee)
        disc = 1 - reach / med if reach else None
        top = max(items, key=lambda x: (x["bought"], x["reviews"] or 0))
        to = max(offers, key=lambda o: o["sold"])
        verdict = D.LATENT_VERDICT.get(cid, ("", ""))
        vals = [name, len(items), med, min(x["price"] for x in items), sum(x["bought"] for x in items),
                sum(x["reviews"] or 0 for x in items), len(offers), cost, sum(o["sold"] for o in offers), med / (cost * V.A.FX),
                reach, disc, verdict[0], reg]
        fm = [None, "0", YEN, YEN, "#,##0", "#,##0", "0", "#,##0", "#,##0", '0.0"倍"', YEN, PCT, None, None]
        for j, (v, f) in enumerate(zip(vals, fm), start=1):
            put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_BOLD if j == 13 else B.F_SMALL, fmt=f, align=B.WRAP_C if j > 1 else B.LEFT_C)
        link(ws, f"O{r}", V.AMZ + top["asin"], f"{top['title'][:40]}（¥{top['price']:,.0f}）")
        link(ws, f"P{r}", to.get("url"), f"{to['title'][:30]}（{to['price']:.0f}元・月销{to['sold']}）")
        link(ws, f"Q{r}", AL + quote(D.LATENT_EN.get(cid, cid)))
        put(ws, f"R{r}", verdict[1], B.F_SMALL, align=B.WRAP_TL)
        ws.row_dimensions[r].height = 48
        r += 1
    ws.freeze_panes = "B5"
    return ws


def build_us(ws):
    ws.title = "08_米国新商品（日本未発売）"
    put(ws, "A1", "米国Amazonで2026年に発売された新商品と、日本のAmazonでの販売状況", B.F_TITLE, border=False)
    put(ws, "A2", "米国：New Releases（新着ランキング）上位・$70以上・ASINがB0G/B0H系列（2025年末〜2026年の新規出品）。"
                  "日本：同じASINのページ（翻訳ページがあっても『在庫切れ・再入荷予定なし』は未発売）と日本語検索1ページ目の類似品。", B.F_NOTE, border=False)
    head_row(ws, 4, ["区分", "商品（米国）", "米国価格", "円換算（150円）", "米国 過去1か月購入", "米国カテゴリ", "同じ商品の日本販売", "日本の類似品 出品数",
                     "日本の類似品 月販合計", "日本の検索上位（価格・月販・参考）", "1688同等品（中央値・元）", "判定", "理由・日本での見込み",
                     "米国商品ページ", "日本の売れ筋ページ", "1688代表品", "Alibaba検索"],
             [6, 46, 9, 9, 9, 18, 18, 8, 8, 34, 10, 14, 50, 30, 30, 34, 26], height=44)
    r = 5
    for cid, jc in JPC.items():
        if jc["src"] != "US":
            continue
        us = USD.get(jc["asin"], {})
        offers, cost = offer_cost("us_" + cid)
        t = jc["top"][0] if jc["top"] else {}
        verdict = D.US_VERDICT.get(cid, ("", ""))
        vals = ["米国", jc["origin"], us.get("usd"), (us.get("usd") or 0) * 150, us.get("bought", ""), us.get("category", ""),
                jc["same_on_jp"] if isinstance(jc["same_on_jp"], str) else ("販売中" if jc["same_on_jp"] else "なし"),
                jc["n"], jc["units"], f"¥{t.get('price') or 0:,.0f}・月{t.get('bought', 0)}個 {t.get('title', '')[:30]}" if t else "",
                cost, verdict[0], verdict[1]]
        fm = [None, None, '"$"#,##0.00', YEN, None, None, None, "0", "#,##0", None, "#,##0", None, None]
        for j, (v, f) in enumerate(zip(vals, fm), start=1):
            put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_BOLD if j == 12 else B.F_SMALL, fmt=f,
                align=B.WRAP_TL if j in (2, 10, 13) else B.WRAP_C)
        link(ws, f"N{r}", f"https://www.amazon.com/dp/{jc['asin']}")
        if t:
            link(ws, f"O{r}", V.AMZ + t["asin"])
        if offers:
            link(ws, f"P{r}", offers[0].get("url"), f"{offers[0]['title'][:24]}（{offers[0]['price']:.0f}元）")
        link(ws, f"Q{r}", AL + quote(D.US_EN.get(cid, cid)))
        ws.row_dimensions[r].height = 60
        r += 1
    r += 1
    put(ws, f"A{r}", "参考：米国New Releasesの大型カテゴリ上位（$70以上・過去1か月100個以上・電気製品を除く）", B.F_SUB, border=False)
    r += 1
    head_row(ws, r, ["", "商品（米国）", "米国価格", "円換算", "過去1か月購入", "カテゴリ", "新着順位", "", "", "", "", "", "", "米国商品ページ"], None)
    import analyze_us as AU
    for x in sorted([c for c in AU.candidates(USD) if c["units"] >= 100 and not c["electric"]], key=lambda c: -c["units"]):
        r += 1
        for j, (v, f) in enumerate(zip(["", x["title"][:90], x["usd"], x["usd"] * 150, x["units"], x["category"], x["rank"]],
                                       [None, None, '"$"#,##0.00', YEN, "#,##0", None, "0"]), start=1):
            put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_SMALL, fmt=f, align=B.LEFT_C if j == 2 else B.WRAP_C)
        link(ws, f"N{r}", x["url"])
    ws.freeze_panes = "C5"


def build_cn(ws):
    ws.title = "09_中国新商品（2026新款）"
    put(ws, "A1", "中国の新商品（1688『2026新款』で月销のある大型品）と日本での販売状況", B.F_TITLE, border=False)
    put(ws, "A2", "中国Amazon（amazon.cn）は2024年1月27日でPCでの販売を終了しているため、1688の2026新款出品で代替。"
                  "上段：注目テーマ（日本のAmazonで類似品を確認）。下段：2026新款の大型品（150元以上・月销20以上）。", B.F_NOTE, border=False)
    head_row(ws, 4, ["区分", "テーマ（中国）", "日本の類似品 出品数", "日本の類似品 月販合計", "日本の検索上位（価格・月販・参考）", "1688同等品（中央値・元）",
                     "判定", "理由・日本での見込み", "日本の売れ筋ページ", "1688代表品", "Alibaba検索"],
             [6, 44, 9, 9, 36, 10, 14, 50, 30, 34, 26], height=44)
    r = 5
    for cid, jc in JPC.items():
        if jc["src"] != "CN":
            continue
        offers, cost = offer_cost("cn_" + cid)
        t = jc["top"][0] if jc["top"] else {}
        verdict = D.CN_VERDICT.get(cid, ("", ""))
        vals = ["中国", jc["origin"], jc["n"], jc["units"], f"¥{t.get('price') or 0:,.0f}・月{t.get('bought', 0)}個 {t.get('title', '')[:30]}" if t else "",
                cost, verdict[0], verdict[1]]
        for j, v in enumerate(vals, start=1):
            put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_BOLD if j == 7 else B.F_SMALL, fmt="#,##0" if j in (3, 4, 6) else None,
                align=B.WRAP_TL if j in (2, 5, 8) else B.WRAP_C)
        if t:
            link(ws, f"I{r}", V.AMZ + t["asin"])
        if offers:
            link(ws, f"J{r}", offers[0].get("url"), f"{offers[0]['title'][:24]}（{offers[0]['price']:.0f}元・月销{offers[0]['sold']}）")
        link(ws, f"K{r}", AL + quote(D.CN_EN.get(cid, cid)))
        ws.row_dimensions[r].height = 60
        r += 1
    r += 1
    put(ws, f"A{r}", "1688 2026新款の大型品（月销順）", B.F_SUB, border=False)
    r += 1
    head_row(ws, r, ["", "出品タイトル", "価格（元）", "月销", "検索テーマ", "出品者", "", "", "", "1688商品ページ"], None)
    rows = []
    for k, v in CNNEW.items():
        term = k.split(" ", 1)[1]
        for o in v:
            if o["price"] >= 150 and o["sold"] >= 20 and term[-2:] in o["title"]:
                rows.append((o, term))
    for o, term in sorted(rows, key=lambda t: -t[0]["sold"]):
        r += 1
        for j, (v, f) in enumerate(zip(["", o["title"], o["price"], o["sold"], term, o.get("shop", "")],
                                       [None, None, "#,##0.0", "#,##0", None, None]), start=1):
            put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_SMALL, fmt=f, align=B.LEFT_C if j == 2 else B.WRAP_C)
        link(ws, f"J{r}", o.get("url"))
    ws.freeze_panes = "C5"


def build_links(ws):
    ws.title = "10_利益商品リンク集"
    put(ws, "A1", "利益商品（最終候補）の商品ページリンク：Amazon（競合）・1688（原価の根拠）・Alibaba", B.F_TITLE, border=False)
    put(ws, "A2", "1688は仕様が一致する出品を月销の多い順に5件。価格は掲載価格（少量）で、50個以上の発注では1〜2割下がることが多い。", B.F_NOTE, border=False)
    head_row(ws, 4, ["商品", "判定", "区分", "リンク先", "価格", "月販／月销", "URL"], [36, 8, 12, 60, 10, 10, 60], height=30)
    r = 5
    for f in D.FINALISTS:
        first = r
        for i, a in enumerate(f["rivals"]):
            x = V.EVA.get(a, {})
            vals = [f["name"] if r == first else "", f["role"] if r == first else "", f"Amazon 競合{i + 1}",
                    (x.get("title") or V.DET.get(a, {}).get("title", ""))[:70], x.get("price"), x.get("bought")]
            for j, v in enumerate(vals, start=1):
                put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_SMALL, fmt=YEN if j == 5 else ("#,##0" if j == 6 else None),
                    align=B.LEFT_C if j in (1, 4) else B.WRAP_C)
            link(ws, f"G{r}", V.AMZ + a)
            r += 1
        for o in V.evidence(f, 5):
            vals = ["", "", "1688", o["title"][:70], o["price"], o["sold"]]
            for j, v in enumerate(vals, start=1):
                put(ws, f"{B.get_column_letter(j)}{r}", v, B.F_SMALL, fmt="#,##0.0" if j == 5 else ("#,##0" if j == 6 else None),
                    align=B.LEFT_C if j == 4 else B.WRAP_C)
            link(ws, f"G{r}", o.get("url"))
            r += 1
        put(ws, f"C{r}", "Alibaba", B.F_SMALL, align=B.WRAP_C)
        put(ws, f"D{r}", f"検索：{f.get('en', '')}", B.F_SMALL, align=B.LEFT_C)
        link(ws, f"G{r}", AL + quote(f.get("en", "")))
        r += 2
    ws.freeze_panes = "A5"


def extra(wb):
    out = []
    for fn in (build_latent, build_us, build_cn, build_links):
        ws = wb.create_sheet("tmp")
        fn(ws)
        out.append(ws)
    return out


if __name__ == "__main__":
    V.main(sys.argv[1], sys.argv[2], extra=extra)
