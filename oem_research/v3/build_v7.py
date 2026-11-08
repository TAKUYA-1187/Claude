# -*- coding: utf-8 -*-
"""Build the v7 workbook: profit estimates for the 26 candidates of the user's quotation list,
on the user's own 天瞳 research template (リサーチ表), with 天瞳's rate sheet.

usage: OEM_V7=<dir with jp_det/jp_search/cn7 .json> OEM_V5=<v5 data dir> \
       python3 build_v7.py <template.xlsx> <out.xlsx>

Inputs (price, 1688 cost, tariff, added value) live in 01_利益見込み一覧, parcels in 02_梱包・送料,
rates in 前提条件. Each candidate sheet is a copy of the template (its formulas untouched) with the
competitor in block 1, our plan in block 2, and the real P&L below it; 01 reads the results back.
"""
import json
import math
import os
import re
import statistics as st
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2"))
import build_v2 as B  # noqa: E402
import analyze_v4 as A  # noqa: E402
import data_v6 as D6  # noqa: E402
import data_v7 as D  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from openpyxl.formatting.rule import CellIsRule, FormulaRule  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter as CL  # noqa: E402

put, head_row, merge_put, link_sheet = B.put, B.head_row, B.merge_put, B.link_sheet
YEN, PCT, CNY, KG, CM = B.YEN, B.PCT, B.CNY, B.KG, B.CM
M3 = '0.000"m³"'
AMZ, AMZ_US = "https://www.amazon.co.jp/dp/", "https://www.amazon.com/dp/"
DET1688 = "https://detail.1688.com/offer/{}.html"
AL = "https://www.alibaba.com/trade/search?SearchText="
DATE = "2026-11-08"


def _load(d, name):
    return json.load(open(os.path.join(d, name), encoding="utf-8"))


V7, V5 = os.environ["OEM_V7"], os.environ["OEM_V5"]
DET, SRCH, CN7 = _load(V7, "jp_det.json"), _load(V7, "jp_search.json"), _load(V7, "cn7.json")
US, NEEDS = _load(V5, "us_det.json"), _load(V5, "needs.json")
CN_OLD = {}
for fn in ("cn_kw.json", "cn_types.json", "cn_fin.json"):
    for k, offers in _load(V5, fn).items():
        for o in offers if isinstance(offers, list) else []:
            CN_OLD.setdefault(str(o.get("id")), o)

USER_AMZ = dict(P1="B0DQY63XXP", P2="B0DPKLVZQY", P3="B0DT45QJ82", P4="B09K3QQBKH", P5="B0F1T4QMVT", P6="B0BVM96YM5",
                Q1="B0956R3T3L", Q2="B0FX9PQK6X", Q3="B0CRRB9DY4", Q4="B0GVQQFB1Q", I1="B0BBVL8G36", I2="B07P4N3SCF",
                I3="B0D4DCK3MN", I4="B0FT2WVSJT", I5="B08P5811G7", I6="B07BDX6TMJ", I7="B0FMJXRHFY", I8="B0BBVX5LBH",
                I9="B0DQ176V5F", I10="B006B9ZDCY", I11="B076J4R897", I12="B0B77BFNC3")
USER_US = dict(N1="B0H4VT6GBY", N2="B0HK78CFR2", N3="B0H8SNLTLP", N4="B0H7HTTR3Z")

# ---------------------------------------------------------------------------------------------- 前提条件
AS = "'前提条件'"
P = {k: f"{AS}!$B${r}" for k, r in dict(
    fx=4, tfee=5, tvat=6, tduty=7, fr_t=8, fr_s=9, fr_b=10, fr_40=11,
    feeA=13, feeB=14, fth=15, ad10=16, ad5=17, ret=18, stor=19, sdays=20, cn=21, tax=22, fr=23,
    ret_c=24, dimf=25, kgf=26, sdays_c=27, lo=29, hi=30, dmin=31).items()}
SG = dict(up=f"{AS}!$B$35:$B$45", kg=f"{AS}!$C$35:$C$45", rate=f"{AS}!$D$35:$D$45")
PV = dict(fx=23.5, tfee=0.165, tvat=0.10, tduty=0.10, fr_t=17325, fr_b=13125, feeA=0.154, feeB=0.104, fth=20000,
          ad10=0.10, ad5=0.05, ret=0.04, stor=77, sdays=45, cn=0.08, tax=0.10, fr=17325, ret_c=0.06, dimf=1.05,
          kgf=1.10, sdays_c=60, lo=0.05, hi=0.15, dmin=100)


def build_assumptions(ws):
    ws.title = "前提条件"
    ws.column_dimensions["A"].width = 50
    for col, w in zip("BCDE", (14, 12, 12, 70)):
        ws.column_dimensions[col].width = w
    put(ws, "A1", "前提条件（天瞳 送料・保管料一覧表 2024.1.6版／2024年8月1日以降の料金。アップロードいただいた料金表と照合済み）", B.F_TITLE, border=False)
    put(ws, "A2", "黄色セル＝入力値。変えると01〜03シートと各候補シートが再計算されます。", B.F_NOTE, border=False)
    put(ws, "A3", "① 天瞳リサーチ表（テンプレート）の計算パラメータ・国際送料（料金表：注文した1m³あたり）", B.F_SUB, border=False)
    rows = [
        (4, "人民元レート（円/元）", 23.5, "0.00", "テンプレートI7と同じ"),
        (5, "Amazon手数料（テンプレート）", 0.165, PCT, "テンプレートL7と同じ16.5%"),
        (6, "消費税（輸入・仕入原価×）", 0.10, PCT, "テンプレートM7と同じ。実質試算では仕入税額控除で戻るため費用に含めない"),
        (7, "関税（テンプレート・仕入原価×）", 0.10, PCT, "テンプレートN7と同じ。実質試算は品目ごとの実行税率（01シートN列）"),
        (8, "海上運賃 2〜20m³（円/m³）", 17325, YEN, "料金表：法人 2m³-20m³。1品50〜100個の初回発注はこの区分"),
        (9, "海上運賃 0〜2m³（円/m³）", 33000, YEN, "料金表：0〜2m³（テスト発注）"),
        (10, "海上運賃 20m³以上（円/m³）", 13125, YEN, "料金表：20m³以上。複数商品を混載して20m³を超えた場合"),
        (11, "40フィートコンテナ（円/m³換算）", 10450, YEN, "料金表：40fコンテナ"),
    ]
    rows2 = [
        (13, "販売手数料A（ペット・ベビー・オフィス・DIY等）", 0.154, PCT, "2026年4月改定後（税抜）。手数料の消費税は仕入税額控除"),
        (14, "販売手数料B（スポーツ・アウトドア・ホビー）", 0.104, PCT, "同上"),
        (15, "家具（区分F）：15.4%が適用される上限額", 20000, YEN, "家具は売価2万円までの部分15.4%、超える部分10.4%"),
        (16, "広告費（立ち上げ期）売上比", 0.10, PCT, "判定はこの広告10%で行う"),
        (17, "広告費（定着後）売上比", 0.05, PCT, ""),
        (18, "返品・破損 売上比（基準）", 0.04, PCT, "大型品の配送破損・返品"),
        (19, "保管料（円/m³/日）", 77, YEN, "料金表：1CBM/日 77円（SKUごとに小数点切上げ）"),
        (20, "平均保管日数（基準）", 45, "0", "入庫から出荷まで。発注サイクル1.5か月"),
        (21, "中国側諸費用（検品・国内運送・代行）仕入原価比", 0.08, PCT, ""),
        (22, "消費税率（売上）", 0.10, PCT, "売上の消費税は納税。輸入消費税は仕入税額控除で戻る"),
        (23, "国際送料（実質試算で使う単価）", f"={P['fr_t']}", YEN, "初回は2〜20m³の17,325円。混載で20m³を超えればB10（13,125円）に変更可"),
        (24, "返品・破損 売上比（慎重）", 0.06, PCT, ""),
        (25, "梱包寸法の倍率（慎重）", 1.05, "0.00", "三辺それぞれ+5%（体積+16%）。佐川サイズも再判定"),
        (26, "梱包重量の倍率（慎重）", 1.10, "0.00", ""),
        (27, "平均保管日数（慎重）", 60, "0", ""),
    ]
    for r, label, v, fmt, note in rows + rows2:
        put(ws, f"A{r}", label)
        put(ws, f"B{r}", v, fmt=fmt, fill=B.FILL_IN)
        put(ws, f"C{r}", note, B.F_NOTE, align=B.LEFT_C, border=False)
    put(ws, "A12", "② 実質試算の追加パラメータ", B.F_SUB, border=False)
    put(ws, "A28", "③ 判定基準（広告10%・国際送料17,325円/m³の実質利益率で判定）", B.F_SUB, border=False)
    for r, label, v, fmt in ((29, "B（条件付き）：実質利益率（税抜売上比）の下限＝『5%以上』", 0.05, PCT),
                             (30, "A（見積依頼）：実質利益率の下限", 0.15, PCT),
                             (31, "需要：競合1位の月販（下限）の目安", 100, "#,##0")):
        put(ws, f"A{r}", label)
        put(ws, f"B{r}", v, fmt=fmt, fill=B.FILL_IN)
    put(ws, "C29", "A＝利益率15%以上かつ競合の月販100個以上。B＝5%以上（需要が未確認なら15%以上でもB）。C＝5%未満、または5〜15%で需要未確認。",
        B.F_NOTE, align=B.LEFT_C, border=False)
    put(ws, "A33", "④ 国内送料（佐川急便・天瞳料金表。備品代・手数料込み）", B.F_SUB, border=False)
    for col, h in zip("ABCD", ("サイズ", "三辺合計（以下）cm", "重量（以下）kg", "送料（円/個口）")):
        put(ws, f"{col}34", h, B.F_HEAD, fill=B.FILL_HEAD, align=B.WRAP_C)
    names = ["60", "80", "100", "140（料金表に120の記載なし→140扱い）", "160", "170", "180", "200", "220", "240", "260"]
    for i, ((up, kg, rate), nm) in enumerate(zip(A.SAGAWA, names)):
        r = 35 + i
        put(ws, f"A{r}", nm + "サイズ")
        put(ws, f"B{r}", up)
        put(ws, f"C{r}", kg)
        put(ws, f"D{r}", rate, fmt=YEN, fill=B.FILL_IN)
    notes = [
        "・三辺合計260cm超・50kg超は1個口で送れない（料金表『特大サイズ』：2〜3個口に分けて発送できるように）。分割できない商品（鏡・長いスクリーンケース等）は天瞳の佐川便では出荷不可。",
        "・保管料は外箱の体積で1日77円/m³（SKUごとに切上げ）。返品分は1パレット/週5,000円。サンプル：航空便1,500円/kg（容積重量 縦×横×高÷5000）、船便15,000円/m³。",
        "・テンプレ利益率（天瞳リサーチ表と同じ）＝売価−原価−国内送料−手数料16.5%−輸入消費税10%−関税10%−国際送料17,325円/m³。広告・返品・保管・売上の消費税を含まない。",
        "・実質利益＝税抜売上−販売手数料−国内送料−返品・破損−保管料−仕入原価×1.08−関税（実行税率）−付加価値費−国際送料−広告費。利益率は税抜売上に対する比率（税込売価×利益率ではない）。",
        "・関税：中国は一般特恵（GSP）の対象外。WTO協定税率で計算（RCEP原産地証明があればさらに下がる）。家具（94類）・運動用具（9506）・手押し車（8716.80）・スクリーン（9010.60）は無税。",
        "・月販は商品ページ／検索カードの『過去1か月でN点以上購入』の下限値。",
    ]
    for i, t in enumerate(notes):
        r = 47 + i
        ws.merge_cells(f"A{r}:E{r}")
        put(ws, f"A{r}", t, B.F_SMALL, align=B.WRAP_TL, border=False)
        ws.row_dimensions[r].height = 30
    ws.freeze_panes = "A4"


# ---------------------------------------------------------------------------------------------- data helpers
def amz(asin):
    """Product page + the best search-card data for an Amazon.co.jp ASIN."""
    d = dict(DET.get(asin) or {})
    cards = [x for items in SRCH.values() for x in items if x.get("asin") == asin]
    d["bought_page"] = d.get("bought") or 0
    d["bought_search"] = max([x.get("bought") or 0 for x in cards] or [0])
    d["bought_max"] = max(d["bought_page"], d["bought_search"])
    if not d.get("price") and cards:
        d["price"] = next((x["price"] for x in cards if x.get("price")), None)
    if not d.get("title") and cards:
        d["title"] = cards[0]["title"]
    if not d.get("reviews") and cards:
        d["reviews"] = max(x.get("reviews") or 0 for x in cards)
    if not d.get("rating") and cards:
        d["rating"] = next((x["rating"] for x in cards if x.get("rating")), None)
    d["search_price"] = next((x["price"] for x in cards if x.get("price")), None)
    return d


def market(kws, n=6, min_price=6000):
    seen, out = set(), []
    items = [x for kw in kws for x in SRCH.get(kw, []) if (x.get("price") or 0) >= min_price]
    for x in sorted(items, key=lambda x: (-(x.get("bought") or 0), -(x.get("reviews") or 0))):
        if x["asin"] not in seen:
            seen.add(x["asin"])
            out.append(x)
    return out[:n]


def offers(key):
    return [o for o in CN7.get(key, {}).get("offers", []) if not o.get("ad")]


def offer(oid):
    if not oid:
        return None
    for v in CN7.values():
        for o in v.get("offers", []):
            if o["id"] == oid:
                return o
    return CN_OLD.get(oid)


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def hexgbk(s):
    return "".join("%02X" % b for b in s.encode("gbk"))


# ---------------------------------------------------------------------------------------------- python mirror
def ship(boxes, f=1.0, fk=1.0):
    tot = 0
    for L, W, H, kg in boxes:
        s3, k = (L + W + H) * f, kg * fk
        r = next((rate for up, mkg, rate in A.SAGAWA if s3 <= up and k <= mkg), None)
        if r is None:
            return None
        tot += r
    return tot


def fee(price, cls):
    if cls == "F":
        return PV["feeA"] * min(price, PV["fth"]) + PV["feeB"] * max(0, price - PV["fth"])
    return price * (PV["feeA"] if cls == "A" else PV["feeB"])


def econ7(c):
    p, cbm = c["price"], sum(L * W * H for L, W, H, _ in c["boxes"]) / 1e6
    S = p / (1 + PV["tax"])
    dom, dom_c = ship(c["boxes"]), ship(c["boxes"], PV["dimf"], PV["kgf"])
    cbm_c = cbm * PV["dimf"] ** 3

    def prof(cny, d, cb, ret, days, ad):
        if d is None:
            return None
        J = cny * PV["fx"]
        return (S - fee(p, c["fee"]) - d - S * ret - cb * PV["stor"] * days - J * (1 + PV["cn"])
                - (J + PV["fr"] * cb) * c["duty"] - c["va"] - PV["fr"] * cb - S * ad)
    J = c["cny"] * PV["fx"]
    tm = (p - J - dom - p * PV["tfee"] - J * PV["tvat"] - J * PV["tduty"] - PV["fr_t"] * cbm) / p if dom else None
    p5 = prof(c["cny"], dom, cbm, PV["ret"], PV["sdays"], PV["ad5"])
    p10 = prof(c["cny"], dom, cbm, PV["ret"], PV["sdays"], PV["ad10"])
    pc = prof(c["cny_c"], dom_c, cbm_c, PV["ret_c"], PV["sdays_c"], PV["ad10"])
    k = PV["fx"] * (1 + PV["cn"]) + PV["fx"] * c["duty"]
    return dict(S=S, cbm=cbm, dom=dom, dom_c=dom_c, tm=tm, p5=p5, p10=p10, pc=pc, m10=p10 / S, mc=(pc / S if pc is not None else None),
                cap5=c["cny"] + (p10 - PV["lo"] * S) / k, cap15=c["cny"] + (p10 - PV["hi"] * S) / k,
                n10=math.ceil(100000 / p10) if p10 > 0 else None, n5=math.ceil(100000 / p5) if p5 > 0 else None)


def need_price(c, m=0.05):
    """Lowest selling price (100-yen steps) at which the ad-10% margin reaches m (python mirror)."""
    for p in range(5000, 300000, 100):
        e = econ7(dict(c, price=p))
        if e["p10"] is not None and e["m10"] >= m:
            return p
    return None


EXTRA = _load(V7, "extra7.json") if os.path.exists(os.path.join(V7, "extra7.json")) else {}


def verdict(c, e, dem):
    if e["m10"] >= PV["hi"]:
        return "A 見積依頼" if dem >= PV["dmin"] else "B 需要確認"
    if e["m10"] >= PV["lo"]:
        return "B 条件付き" if dem >= PV["dmin"] else "C 需要未確認"
    return "C 見送り"


# ---------------------------------------------------------------------------------------------- 02 parcels
def build_parcels(ws, rows):
    ws.title = "02_梱包・送料"
    put(ws, "A1", "梱包・国内送料（天瞳・佐川急便）― 個口ごとに三辺合計と重量から料金表のサイズを判定", B.F_TITLE, border=False)
    put(ws, "A2", "黄色＝入力（cm・kg）。青字＝推定（工場の実測値に置き換えてください）。慎重＝三辺×1.05・重量×1.10で再判定。"
                  "『不可』＝三辺260cm超または50kg超（その個口は分割が必要）。", B.F_NOTE, border=False)
    heads = ["No", "商品", "梱包の根拠"]
    for i in (1, 2, 3):
        heads += [f"箱{i} 長", f"箱{i} 幅", f"箱{i} 高", f"箱{i} kg", f"箱{i} 三辺", f"箱{i} 送料"]
    heads += ["個口", "総重量", "CBM（基準）", "国内送料（基準）", "CBM（慎重）", "国内送料（慎重）", "他社便（手入力）"]
    head_row(ws, 4, heads, [6, 30, 34] + [6, 6, 6, 6, 7, 9] * 3 + [6, 8, 10, 11, 10, 11, 11], height=36)
    for c, r in rows:
        put(ws, f"A{r}", c["id"], B.F_BOLD, align=B.WRAP_C)
        put(ws, f"B{r}", c["name"][:40], B.F_SMALL, align=B.WRAP_TL)
        put(ws, f"C{r}", c["box_src"], B.F_NOTE, align=B.WRAP_TL)
        est = "推定" in c["box_src"]
        for i in range(3):
            col = 4 + i * 6
            Lc, Wc, Hc, Kc, Sc, Rc = [CL(col + j) for j in range(6)]
            if i < len(c["boxes"]):
                for j, v in enumerate(c["boxes"][i]):
                    put(ws, f"{CL(col + j)}{r}", v, B.F_EST if est else B.F_BASE, fmt="0.0" if j == 3 else "0", fill=B.FILL_IN, align=B.WRAP_C)
            else:
                for j in range(4):
                    put(ws, f"{CL(col + j)}{r}", None, fill=B.FILL_IN)
            put(ws, f"{Sc}{r}", f'=IF({Lc}{r}="","",{Lc}{r}+{Wc}{r}+{Hc}{r})', B.F_SMALL, fmt="0", align=B.WRAP_C)
            put(ws, f"{Rc}{r}", f'=IF({Lc}{r}="","",IF(OR({Sc}{r}>260,{Kc}{r}>50),"不可",'
                                f'_xlfn.MINIFS({SG["rate"]},{SG["up"]},">="&{Sc}{r},{SG["kg"]},">="&{Kc}{r})))', B.F_SMALL, fmt=YEN, align=B.WRAP_C)
        put(ws, f"V{r}", f"=COUNT(D{r},J{r},P{r})", fmt="0", align=B.WRAP_C)
        put(ws, f"W{r}", f"=SUM(G{r},M{r},S{r})", fmt=KG, align=B.WRAP_C)
        put(ws, f"X{r}", f"=(N(D{r})*N(E{r})*N(F{r})+N(J{r})*N(K{r})*N(L{r})+N(P{r})*N(Q{r})*N(R{r}))/1000000", B.F_BOLD, fmt=M3)
        put(ws, f"Y{r}", f'=IF(AB{r}<>"",AB{r},IF(COUNTIF(D{r}:U{r},"不可")>0,"不可",SUM(I{r},O{r},U{r})))', B.F_BOLD, fmt=YEN)
        put(ws, f"Z{r}", f"=X{r}*{P['dimf']}^3", fmt=M3)
        bad = ",".join(f'AND(N({a}{r})>0,OR(N({s}{r})*{P["dimf"]}>260,N({k}{r})*{P["kgf"]}>50))' for a, s, k in (("D", "H", "G"), ("J", "N", "M"), ("P", "T", "S")))
        parts = "+".join(f'IF(N({a}{r})=0,0,_xlfn.MINIFS({SG["rate"]},{SG["up"]},">="&N({s}{r})*{P["dimf"]},{SG["kg"]},">="&N({k}{r})*{P["kgf"]}))'
                         for a, s, k in (("D", "H", "G"), ("J", "N", "M"), ("P", "T", "S")))
        put(ws, f"AA{r}", f'=IF(AB{r}<>"",AB{r},IF(OR({bad}),"不可",{parts}))', B.F_BOLD, fmt=YEN)
        put(ws, f"AB{r}", c.get("dom_override"), fill=B.FILL_IN, fmt=YEN)
        ws.row_dimensions[r].height = 30
    ws.freeze_panes = "D5"


# ---------------------------------------------------------------------------------------------- product sheets
S0 = 77  # first row of the real P&L block


def qs(name):
    return f"'{name}'"


def build_product(wb, tpl, c, r1, r2, e):
    ws = wb.copy_worksheet(tpl)
    ws.title = c["sheet"]
    B.copy_conditional_formatting(tpl, ws)
    O1, O2 = qs("01_利益見込み一覧"), qs("02_梱包・送料")
    ws["A1"].value = f"リサーチ｜{c['id']} {c['name']}"
    ws["A1"].font = Font(name=B.FONT, size=18, bold=True)
    rv = amz(c["rival"])
    pr = rv.get("price") or rv.get("search_price") or 0
    L, W, H, kg = c["boxes"][0]
    tot_kg = sum(b[3] for b in c["boxes"])
    multi = len(c["boxes"]) > 1
    dims = A.parse_dims(rv.get("dims")) or ["", "", ""]
    est = "推定" in c["box_src"]
    for blk, (name, url, maker, note) in zip(B.BLOCKS, (
            (rv.get("title", "")[:120], AMZ + c["rival"], (rv.get("brand") or "").split(" ")[0] or rv.get("seller", ""),
             f"¥{pr:,.0f}（{DATE}・月{rv['bought_max']}個以上購入・評価{rv.get('reviews') or 0:,}件 ★{rv.get('rating') or '-'}）"),
            ("自社企画：" + c["name"], DET1688.format(c["alt1688"]) if c.get("alt1688") else "", "OEM（1688の工場）",
             f"計画売価 ¥{c['price']:,}（税込）・原価 基準{c['cny']}元／慎重{c['cny_c']}元"))):
        put(ws, blk["name"], name, B.F_BASE, align=B.LEFT_C, border=False)
        cell = put(ws, blk["site"], url, B.F_URL, align=B.LEFT_C, border=False)
        if url:
            cell.hyperlink = url
        put(ws, blk["maker"], maker, B.F_BASE, align=B.WRAP_C, border=False)
        put(ws, blk["price"], note, B.F_BASE, align=B.WRAP_C, border=False)
        for ref, v in zip(blk["pkg"], (L, W, H)):
            put(ws, ref, v, B.F_EST if est else B.F_BASE, fmt=CM, align=B.WRAP_C, border=False)
        put(ws, blk["pkg_kg"], tot_kg, B.F_EST if est else B.F_BASE, fmt=KG, align=B.WRAP_C, border=False)
        for ref, v in zip(blk["prod"], dims):
            put(ws, ref, v, B.F_SMALL, fmt=CM if not isinstance(v, str) else None, align=B.WRAP_C, border=False)
        put(ws, blk["prod_kg"], (rv.get("weight") or "")[:16], B.F_SMALL, align=B.WRAP_C, border=False)
        put(ws, blk["wcheck"], f"=IF(MAX({','.join(str(b[3]) for b in c['boxes'])})<=50,\"OK\",\"50kg超→分割\")", B.F_SMALL, align=B.WRAP_C, border=False)
        if multi:  # template CBM uses one box; replace it with the total of all parcels
            cbm_ref = f"N{int(blk['pkg'][0][1:]) + 1}"
            put(ws, cbm_ref, f"={O2}!X{r2}", B.F_BASE, fmt="0.000", border=False)
        boxes_txt = "／".join(f"{a:g}×{b:g}×{h:g}cm {k:g}kg" for a, b, h, k in c["boxes"])
        put(ws, blk["note"], f"梱包（{len(c['boxes'])}個口）：{boxes_txt}。{c['box_src']}。国内送料＝02シートの個口別の天瞳料金の合計。"
                             f"{'CBMは全個口の合計に置換。' if multi else ''}", B.F_NOTE, align=B.WRAP_TL, border=False)
    F12 = Font(name="Arial", size=12)
    for blk, asin, price_f, units in ((B.BLOCKS[0], c["rival"], pr, rv["bought_max"]), (B.BLOCKS[1], "自社企画", f"={O1}!J{r1}", f"=IF(ISNUMBER({O1}!AB{r1}),{O1}!AB{r1},0)")):
        r = blk["vrow"]
        put(ws, blk["asin"], asin, B.F_SMALL, align=B.WRAP_C, border=False)
        put(ws, f"G{r}", price_f, B.F_BASE, fmt='"¥"#,##0_);[Red]\\("¥"#,##0\\)', border=False)
        put(ws, f"H{r}", f"={O1}!L{r1}", B.F_EST, fmt=CNY, border=False)
        put(ws, f"I{r}", f"={P['fx']}", F12, align=B.WRAP_C, border=False)
        put(ws, f"K{r}", f"={O2}!Y{r2}", F12, fmt='"¥"#,##0', border=False)
        put(ws, f"O{r}", f"={P['fr_t']}", F12, fmt="#,##0", border=False)
        put(ws, f"T{r}", units, F12, fmt="#,##0", align=Alignment(horizontal="right"), border=False)
        put(ws, f"W{r}", c["qty"], F12, align=Alignment(horizontal="right"), border=False)
    put(ws, "V7", re.sub(r"\s*\(.*?\)\s*", " ", rv.get("bsr") or "")[:40], B.F_SMALL, align=B.WRAP_C, border=False)
    put(ws, "V15", "販売目標＝月10万円に必要な個数", B.F_SMALL, align=B.WRAP_C, border=False)
    ws["E9"].value = (f"上段＝競合1位（Amazon {DATE} 実データ。原価は自社企画と同じ1688原価を当てた場合）／下段＝自社企画（計画売価）。"
                      "ランキング30/60/90日平均はKeepa等で取得してください。青字＝推定（要実測・要見積）。")
    ws["E9"].font = B.F_NOTE
    # template text areas
    need = NEEDS.get(c.get("need", ""), {})
    gap_plan = D6.NEEDS.get(c.get("need", ""))
    merits = c.get("merits") or ("【Amazonレビュー要約】" + (need.get("summary") or "")[:400])
    demerits = c.get("demerits") or ("【不満・要望（レビュー本文）】\n" + "\n".join("・" + w[:100] for w in (need.get("wishes") or [])[:5]))
    ours = c.get("ours") or (f"【改良点】{gap_plan[1]}\n{gap_plan[2]}" if gap_plan else "")
    latent = c.get("latent") or ("【お客様の声（要望）】" + " ／ ".join(w[:60] for w in (need.get("wishes") or [])[5:9]))
    for ref, txt in (("B31", merits), ("B36", demerits), ("B41", ours), ("B47", latent)):
        cell = ws[ref]
        cell.value = txt
        cell.font = Font(name=B.FONT, size=10)
        cell.alignment = B.WRAP_TL
    ws["A54"].value = (f"【Claude所見 {DATE}】判定：{verdict(c, e, rv['bought_max'])}（広告10%の実質利益率 {e['m10'] * 100:.1f}%・利益 ¥{e['p10']:,.0f}/個）。"
                       f"\n利益率5%を確保できる1688単価の上限 {e['cap5']:.0f}元、15%なら {e['cap15']:.0f}元（基準梱包・広告10%）。"
                       f"\n今の原価のまま利益率5%にするには売価¥{need_price(c) or 0:,}以上が必要。\n確定に必要な確認：{c['confirm']}")
    ws["A54"].font = Font(name=B.FONT, size=10)
    ws["A54"].alignment = B.WRAP_TL
    ws["Y1"].value = (f"【判断メモ】\n{c['cny_note']}\n\n関税：{c['duty_note']}\n付加価値費：¥{c['va']:,}（{c['va_note']}）\n\n規制・注意：{c['reg'] or '特になし'}"
                      + (f"\n\n旧試算：売価¥{c['old_price']:,}・利益¥{c['old_profit']:,}/個" if c.get("old_profit") else "")
                      + (f"\n旧試算：{c['old_note']}" if c.get("old_note") else ""))
    ws["Y1"].font = Font(name=B.FONT, size=10)
    ws["Y1"].alignment = B.WRAP_TL
    for col in ("Y", "Z", "AA", "AB"):
        ws.column_dimensions[col].width = 16
    pl_block(ws, c, r1, r2)
    evidence_block(ws, c, rv)
    return ws


def pl_block(ws, c, r1, r2):
    s = S0
    O1, O2 = qs("01_利益見込み一覧"), qs("02_梱包・送料")
    blue = PatternFill("solid", fgColor="BDD7EE")
    merge_put(ws, f"A{s}:O{s}", "【実質の収益試算（天瞳の実料金）】基準＝1688原価の基準値・推定梱包／慎重＝高仕様SKUの原価・梱包+5%・返品6%・保管60日・広告10%",
              B.F_BOLD, fill=blue, align=B.LEFT_C)
    for col, h in (("A", "項目"), ("G", "基準（広告5%）"), ("H", "基準（広告10%）"), ("I", "慎重"), ("J", "計算方法")):
        if col == "A":
            ws.merge_cells(f"A{s + 1}:F{s + 1}")
        if col == "J":
            ws.merge_cells(f"J{s + 1}:O{s + 1}")
        put(ws, f"{col}{s + 1}", h, B.F_HEAD, fill=B.FILL_HEAD, align=B.WRAP_C)
    S_ = lambda col: f"{col}{s + 3}"  # noqa: E731
    cbm, cbm_c = f"{O2}!X{r2}", f"{O2}!Z{r2}"
    price = f"{O1}!J{r1}"
    feef = (f'=IF({O1}!K{r1}="F",{P["feeA"]}*MIN({price},{P["fth"]})+{P["feeB"]}*MAX(0,{price}-{P["fth"]}),'
            f'{price}*IF({O1}!K{r1}="A",{P["feeA"]},{P["feeB"]}))')
    lines = [
        ("売価（税込）", [f"={price}"] * 3, "01シートJ列（入力）"),
        ("税抜売上", [f"={col}{s + 2}/(1+{P['tax']})" for col in "GHI"], "売価÷1.1（売上の消費税は納税）"),
        ("販売手数料（カテゴリ別・税抜）", [feef] * 3, "A 15.4%／B 10.4%／F 2万円まで15.4%＋超過分10.4%"),
        ("国内送料（天瞳・佐川）", [f"={O2}!Y{r2}"] * 2 + [f"={O2}!AA{r2}"], "02シート（個口別の料金表の合計）"),
        ("返品・破損", [f"={S_(col)}*{P['ret']}" for col in "GH"] + [f"={S_('I')}*{P['ret_c']}"], "税抜売上×4%（慎重6%）"),
        ("保管料", [f"={cbm}*{P['stor']}*{P['sdays']}"] * 2 + [f"={cbm_c}*{P['stor']}*{P['sdays_c']}"], "CBM×77円×45日（慎重60日）"),
        ("仕入原価（中国側諸費用8%込）", [f"={O1}!L{r1}*{P['fx']}*(1+{P['cn']})"] * 2 + [f"={O1}!M{r1}*{P['fx']}*(1+{P['cn']})"],
         "1688単価（元）×23.5×1.08"),
        ("関税（実行税率）", [f"=({O1}!L{r1}*{P['fx']}+{P['fr']}*{cbm})*{O1}!N{r1}"] * 2 + [f"=({O1}!M{r1}*{P['fx']}+{P['fr']}*{cbm_c})*{O1}!N{r1}"],
         "（原価＋国際送料）×関税率"),
        ("付加価値費", [f"={O1}!O{r1}"] * 3, "説明書・付属品・認証費の1個あたり"),
        ("国際送料（海上）", [f"={P['fr']}*{cbm}"] * 2 + [f"={P['fr']}*{cbm_c}"], "CBM×17,325円（2〜20m³）"),
        ("広告費", [f"={S_('G')}*{P['ad5']}", f"={S_('H')}*{P['ad10']}", f"={S_('I')}*{P['ad10']}"], "税抜売上×5%／10%"),
    ]
    for i, (label, fs, how) in enumerate(lines):
        r = s + 2 + i
        ws.merge_cells(f"A{r}:F{r}")
        put(ws, f"A{r}", label, B.F_SMALL, fill=B.FILL_SUB, align=B.LEFT_C)
        for col, f in zip("GHI", fs):
            put(ws, f"{col}{r}", f, B.F_BASE, fmt=YEN)
        ws.merge_cells(f"J{r}:O{r}")
        put(ws, f"J{r}", how, B.F_NOTE, align=B.LEFT_C)
    rp = s + 2 + len(lines)  # profit row
    rows = [
        (rp, "利益／個", [f'=IF(ISNUMBER({col}{s + 5}),{col}{s + 3}-SUM({col}{s + 4}:{col}{s + 12}),"送料不可")' for col in "GHI"], YEN,
         "税抜売上−上記の費用"),
        (rp + 1, "利益率（税抜売上比）", [f'=IFERROR({col}{rp}/{col}{s + 3},"-")' for col in "GHI"], PCT, "判定に使う利益率"),
        (rp + 2, "利益率（税込売価比・参考）", [f'=IFERROR({col}{rp}/{col}{s + 2},"-")' for col in "GHI"], PCT, "旧試算の『利益率×税込売価』はこの比率の考え方"),
        (rp + 3, "参考：テンプレート式の利益率（上の自社企画ブロック R15）", ["=R15", "", ""], PCT, "広告・返品・保管を含まない天瞳表の式"),
        (rp + 4, "参考：混載20m³以上（13,125円/m³）なら利益／個", [f"=G{rp}+({P['fr']}-{P['fr_b']})*{cbm}*(1+{O1}!N{r1})",
                                                         f"=H{rp}+({P['fr']}-{P['fr_b']})*{cbm}*(1+{O1}!N{r1})", ""], YEN, "国際送料の単価差×CBM"),
        (rp + 5, "利益率5%を確保できる1688単価の上限（元）", ["", f"=IFERROR({O1}!L{r1}+(H{rp}-0.05*H{s + 3})/({P['fx']}*(1+{P['cn']})+{P['fx']}*{O1}!N{r1}),\"-\")",
                                                  f"=IFERROR({O1}!M{r1}+(I{rp}-0.05*I{s + 3})/({P['fx']}*(1+{P['cn']})+{P['fx']}*{O1}!N{r1}),\"-\")"], '0"元"',
         "この単価以下の見積なら、梱包が推定どおりで広告10%でも利益率5%以上（慎重列＝慎重条件）"),
        (rp + 6, "利益率15%を確保できる1688単価の上限（元）", ["", f"=IFERROR({O1}!L{r1}+(H{rp}-{P['hi']}*H{s + 3})/({P['fx']}*(1+{P['cn']})+{P['fx']}*{O1}!N{r1}),\"-\")", ""],
         '0"元"', "見積の目標単価"),
        (rp + 7, "月10万円の利益に必要な個数", [f'=IF(G{rp}>0,ROUNDUP(100000/G{rp},0),"赤字")', f'=IF(H{rp}>0,ROUNDUP(100000/H{rp},0),"赤字")', ""], "#,##0",
         "競合1位の月販（上のT7）と比べる"),
    ]
    for r, label, fs, fmt, how in rows:
        ws.merge_cells(f"A{r}:F{r}")
        put(ws, f"A{r}", label, B.F_BOLD if r in (rp, rp + 1, rp + 5) else B.F_SMALL, fill=B.FILL_SUB, align=B.LEFT_C)
        for col, f in zip("GHI", fs):
            put(ws, f"{col}{r}", f if f else None, B.F_BOLD if r in (rp, rp + 1, rp + 5, rp + 6) else B.F_BASE, fmt=fmt)
        ws.merge_cells(f"J{r}:O{r}")
        put(ws, f"J{r}", how, B.F_NOTE, align=B.LEFT_C)
    ws.conditional_formatting.add(f"G{rp}:I{rp + 1}", CellIsRule(operator="lessThan", formula=["0"], fill=B.FILL_NO, font=Font(color="C00000", bold=True)))
    return rp


PL_ROWS = dict(p=S0 + 13, m=S0 + 14, cap5=S0 + 18, cap15=S0 + 19, n=S0 + 20)


def evidence_block(ws, c, rv):
    s = S0 + 23
    blue = PatternFill("solid", fgColor="BDD7EE")
    merge_put(ws, f"A{s}:O{s}", f"【Amazon.co.jp の実勢（{DATE} 取得：商品ページ・検索結果の月販バッジ）】", B.F_BOLD, fill=blue, align=B.LEFT_C)
    head = [("A", "ASIN"), ("C", "価格"), ("D", "月販"), ("E", "評価数"), ("F", "商品名（クリックでAmazon）")]
    for col, h in head:
        put(ws, f"{col}{s + 1}", h, B.F_HEAD, fill=B.FILL_HEAD, align=B.WRAP_C)
    ws.merge_cells(f"A{s + 1}:B{s + 1}")
    ws.merge_cells(f"F{s + 1}:O{s + 1}")
    items = []
    ua = USER_AMZ.get(c["id"])
    for asin, tag in ((c["rival"], "競合（試算の比較先）"), (ua, "ご提示のASIN")):
        if asin:
            d = amz(asin)
            items.append(dict(asin=asin, price=d.get("price") or d.get("search_price"), bought=d["bought_max"], reviews=d.get("reviews"),
                              title=f"【{tag}】" + (d.get("title") or "")))
    for x in market(c["market_kws"]):
        if x["asin"] not in {c["rival"], ua}:
            items.append(dict(x, title="【市場上位】" + x["title"]))
    for i, x in enumerate(items[:9]):
        r = s + 2 + i
        ws.merge_cells(f"A{r}:B{r}")
        put(ws, f"A{r}", x["asin"], B.F_SMALL, align=B.WRAP_C)
        put(ws, f"C{r}", x.get("price"), B.F_SMALL, fmt=YEN)
        put(ws, f"D{r}", x.get("bought") or 0, B.F_SMALL, fmt='#,##0"+"')
        put(ws, f"E{r}", x.get("reviews") or 0, B.F_SMALL, fmt="#,##0")
        ws.merge_cells(f"F{r}:O{r}")
        cell = put(ws, f"F{r}", x["title"][:110], B.F_LINK, align=B.LEFT_C)
        cell.hyperlink = AMZ + x["asin"]
    s2 = s + 12
    merge_put(ws, f"A{s2}:O{s2}", f"【1688 仕様一致品（{DATE}・検索ページのカード価格＝最安SKUの価格・月销の多い順）】", B.F_BOLD, fill=blue, align=B.LEFT_C)
    for col, h in (("A", "価格（元）"), ("B", "月销"), ("C", "累計"), ("D", "商品名（クリックで1688）")):
        put(ws, f"{col}{s2 + 1}", h, B.F_HEAD, fill=B.FILL_HEAD, align=B.WRAP_C)
    ws.merge_cells(f"D{s2 + 1}:O{s2 + 1}")
    rows = []
    uo = offer(c.get("user1688"))
    if c.get("user1688"):
        rows.append((uo or {"id": c["user1688"], "title": "", "price": None, "sold": None}, f"【ご提示のリンク：{c['user1688_check']}】"))
    rows += [(o, "") for o in offers(c["key"])[:8]]
    for i, (o, tag) in enumerate(rows):
        r = s2 + 2 + i
        put(ws, f"A{r}", o.get("price"), B.F_SMALL, fmt=CNY)
        put(ws, f"B{r}", o.get("sold"), B.F_SMALL, fmt="#,##0")
        put(ws, f"C{r}", o.get("total"), B.F_SMALL, fmt="#,##0")
        ws.merge_cells(f"D{r}:O{r}")
        cell = put(ws, f"D{r}", (tag + o.get("title", ""))[:120], B.F_LINK, align=B.LEFT_C)
        cell.hyperlink = DET1688.format(o["id"])
    s3 = s2 + 12
    merge_put(ws, f"A{s3}:O{s3}", "【確定に必要な確認・検索リンク】", B.F_BOLD, fill=blue, align=B.LEFT_C)
    ws.merge_cells(f"A{s3 + 1}:O{s3 + 2}")
    put(ws, f"A{s3 + 1}", c["confirm"], B.F_SMALL, align=B.WRAP_TL)
    ws.row_dimensions[s3 + 1].height = 30
    ws.row_dimensions[s3 + 2].height = 30
    for i, (label, url) in enumerate((
            (f"▶ 1688で検索：{c['kw_cn']}", f"https://www.1688.com/market/-{hexgbk(c['kw_cn'])}.html"),
            (f"▶ Alibaba.comで検索：{c['en']}", AL + quote(c["en"])),
            (f"▶ Amazonで検索：{c['kw_jp']}", "https://www.amazon.co.jp/s?k=" + quote(c["kw_jp"])))):
        r = s3 + 3 + i
        ws.merge_cells(f"A{r}:O{r}")
        cell = put(ws, f"A{r}", label, B.F_LINK, align=B.LEFT_C)
        cell.hyperlink = url
    us = USER_US.get(c["id"])
    if us:
        u = US.get(us, {})
        r = s3 + 6
        ws.merge_cells(f"A{r}:O{r}")
        cell = put(ws, f"A{r}", f"▶ 米国の参照品 {us}：{u.get('title', '')[:80]}（${u.get('usd')}・月{u.get('bought')}・{u.get('weight', '')[:12]}）",
                   B.F_LINK, align=B.LEFT_C)
        cell.hyperlink = AMZ_US + us


# ---------------------------------------------------------------------------------------------- 01 overview
OV = ["No", "区分", "商品（自社仕様）", "詳細シート", "判定", "判定の根拠", "競合（Amazon）", "競合価格", "競合月販（下限）",
      "計画売価（税込）", "手数料区分", "1688原価 基準（元）", "1688原価 慎重（元）", "関税率", "付加価値費",
      "個口", "CBM", "国内送料（天瞳）", "税抜売上", "テンプレ利益率", "実質利益/個（広告5%）", "実質利益/個（広告10%）",
      "実質利益率（広告10%）", "慎重 利益/個", "慎重 利益率", "原価上限（元）利益率5%", "原価上限（元）利益率15%",
      "月10万円に必要な個数（広告10%）", "同（広告5%）", "必要個数÷競合月販", "混載20m³以上なら利益+",
      "旧試算 売価", "旧試算 利益/個", "今回−旧試算（広告5%）", "1688（仕様一致・月销最多）", "1688（ご提示リンク）", "ご提示リンクの照合",
      "Alibaba検索", "Amazon検索", "確定に必要な確認", "原価の根拠", "（参考）利益率5%に必要な売価", "（参考）同15%"]
OVW = [5, 9, 40, 14, 13, 30, 13, 9, 8, 10, 5, 9, 9, 6, 8, 5, 8, 9, 9, 8, 10, 10, 9, 10, 9, 9, 9, 9, 8, 8, 9, 9, 9, 9,
       26, 26, 30, 14, 14, 50, 50, 11, 11]


def build_overview(ws, rows, E):
    ws.title = "01_利益見込み一覧"
    put(ws, "A1", f"見積優先リストの利益見込み（天瞳の実料金・Amazon/1688 {DATE} 再調査）", B.F_TITLE, border=False)
    put(ws, "A2", "黄色＝入力（売価・1688原価・関税・付加価値費）。梱包は02シート、料金は前提条件シート。判定は広告10%・国際送料17,325円/m³の実質利益率（税抜売上比）："
                  "A＝15%以上かつ競合月販100個以上、B＝5%以上（需要未確認なら15%以上でもB）、C＝それ以外。", B.F_NOTE, border=False)
    put(ws, "A3", "『原価上限』＝その単価以下の見積なら利益率5%／15%を確保できる1688単価（推定梱包・広告10%）。見積の判断基準に使ってください。", B.F_NOTE, border=False)
    head_row(ws, 5, OV, OVW, height=48)
    for c, r in rows:
        e = E[c["id"]]
        sh = qs(c["sheet"])
        rv = amz(c["rival"])
        hx = hexgbk(c["kw_cn"])
        vals = {
            "A": (c["id"], B.F_BOLD, None), "B": (c["grp"], B.F_SMALL, None), "C": (c["name"], B.F_SMALL, None),
            "E": (f'=IF(W{r}>={P["hi"]},IF(I{r}>={P["dmin"]},"A 見積依頼","B 需要確認"),IF(W{r}>={P["lo"]},IF(I{r}>={P["dmin"]},"B 条件付き","C 需要未確認"),"C 見送り"))',
                  B.F_BOLD, None),
            "F": (f'="広告10%で"&TEXT(W{r},"0.0%")&"・¥"&TEXT(V{r},"#,##0")&"/個／競合月販"&TEXT(I{r},"#,##0")&"+／5%確保の原価上限"&TEXT(Z{r},"0")&"元"',
                  B.F_SMALL, None),
            "H": (rv.get("price") or rv.get("search_price"), B.F_SMALL, YEN), "I": (rv["bought_max"], B.F_SMALL, "#,##0"),
            "J": (c["price"], B.F_BOLD, YEN), "K": (c["fee"], B.F_SMALL, None), "L": (c["cny"], B.F_BOLD, CNY), "M": (c["cny_c"], B.F_SMALL, CNY),
            "N": (c["duty"], B.F_SMALL, PCT), "O": (c["va"], B.F_SMALL, YEN),
            "P": (f"={qs('02_梱包・送料')}!V{r - 1}", B.F_SMALL, "0"), "Q": (f"={qs('02_梱包・送料')}!X{r - 1}", B.F_SMALL, M3),
            "R": (f"={qs('02_梱包・送料')}!Y{r - 1}", B.F_SMALL, YEN), "S": (f"={sh}!G{S0 + 3}", B.F_SMALL, YEN),
            "T": (f"={sh}!R15", B.F_SMALL, PCT), "U": (f"={sh}!G{PL_ROWS['p']}", B.F_BOLD, YEN), "V": (f"={sh}!H{PL_ROWS['p']}", B.F_BOLD, YEN),
            "W": (f"={sh}!H{PL_ROWS['m']}", B.F_BOLD, PCT), "X": (f"={sh}!I{PL_ROWS['p']}", B.F_SMALL, YEN), "Y": (f"={sh}!I{PL_ROWS['m']}", B.F_SMALL, PCT),
            "Z": (f"={sh}!H{PL_ROWS['cap5']}", B.F_BOLD, '0"元"'), "AA": (f"={sh}!H{PL_ROWS['cap15']}", B.F_SMALL, '0"元"'),
            "AB": (f"={sh}!H{PL_ROWS['n']}", B.F_BOLD, "#,##0"), "AC": (f"={sh}!G{PL_ROWS['n']}", B.F_SMALL, "#,##0"),
            "AD": (f'=IFERROR(AB{r}/I{r},"-")', B.F_SMALL, "0.00"), "AE": (f"=({P['fr']}-{P['fr_b']})*Q{r}*(1+N{r})", B.F_SMALL, YEN),
            "AF": (c.get("old_price"), B.F_SMALL, YEN), "AG": (c.get("old_profit") or (c.get("old_note") or None), B.F_SMALL, YEN),
            "AH": (f'=IF(ISNUMBER(AG{r}),U{r}-AG{r},"")', B.F_SMALL, YEN),
            "AK": (c["user1688_check"], B.F_SMALL, None), "AN": (c["confirm"], B.F_SMALL, None), "AO": (c["cny_note"], B.F_SMALL, None),
            "AP": (need_price(c), B.F_SMALL, YEN), "AQ": (need_price(c, 0.15), B.F_SMALL, YEN),
        }
        for col, (v, font, fmt) in vals.items():
            fill = B.FILL_IN if col in ("J", "K", "L", "M", "N", "O") else None
            put(ws, f"{col}{r}", v, font, fmt=fmt, fill=fill, align=B.WRAP_TL if col in ("C", "F", "AK", "AN", "AO") else B.WRAP_C)
        cell = put(ws, f"D{r}", c["sheet"], B.F_LINK, align=B.WRAP_C)
        link_sheet(cell, f"{sh}!A1")
        for col, text, url in (("G", c["rival"], AMZ + c["rival"]),
                               ("AI", (lambda o: f"{o['title'][:20]}（{o['price']:.0f}元・月销{o['sold']}）" if o else c.get("alt1688") or "")(offer(c.get("alt1688"))),
                                DET1688.format(c["alt1688"]) if c.get("alt1688") else None),
                               ("AJ", (lambda o: f"{c['user1688']}（{o['price']:.0f}元）" if o else (c.get("user1688") or "（ご提示なし）"))(offer(c.get("user1688"))),
                                DET1688.format(c["user1688"]) if c.get("user1688") else None),
                               ("AL", "Alibaba", AL + quote(c["en"])), ("AM", "Amazon", "https://www.amazon.co.jp/s?k=" + quote(c["kw_jp"]))):
            cell = put(ws, f"{col}{r}", text, B.F_LINK if url else B.F_SMALL, align=B.WRAP_TL)
            if url:
                cell.hyperlink = url
        ws.row_dimensions[r].height = 64
    last = rows[-1][1]
    for txt, fill in (("A", B.FILL_GO), ("B", B.FILL_COND), ("C", B.FILL_NO)):
        ws.conditional_formatting.add(f"E6:E{last}", FormulaRule(formula=[f'LEFT(E6,1)="{txt}"'], fill=fill))
    ws.conditional_formatting.add(f"U6:Y{last}", CellIsRule(operator="lessThan", formula=["0"], font=Font(color="C00000", bold=True)))
    ws.freeze_panes = "D6"
    ws.auto_filter.ref = f"A5:AQ{last}"
    put(ws, f"A{last + 2}", "AP・AQ列は作成時点の計算値（売価以外の入力が変わると変わります）。" + D.USER_NOTE, B.F_NOTE, border=False)


# ---------------------------------------------------------------------------------------------- 03 RFQ
def build_rfq(ws, rows):
    ws.title = "03_見積依頼（目標単価）"
    put(ws, "A1", "1688の工場への見積依頼：指定仕様・目標単価・依頼文（中国語）", B.F_TITLE, border=False)
    put(ws, "A2", "目標単価＝01シートの『原価上限（利益率15%）』、上限単価＝『原価上限（利益率5%）』（自動計算）。依頼文はコピーして1688のチャット（旺旺）に貼り付け。"
                  "外箱の実測寸法・重量を必ず回答してもらい、02シートの青字を置き換えてください。", B.F_NOTE, border=False)
    head_row(ws, 4, ["No", "商品", "判定", "目標単価（元）", "上限単価（元）", "現在の基準原価（元）", "指定仕様（必須）", "見積依頼文（中国語・コピー用）", "ご提示の1688リンク", "照合"],
             [5, 30, 12, 10, 10, 10, 50, 80, 22, 30], height=36)
    O1 = qs("01_利益見込み一覧")
    for i, (c, r1) in enumerate(rows):
        r = 5 + i
        put(ws, f"A{r}", c["id"], B.F_BOLD, align=B.WRAP_C)
        put(ws, f"B{r}", c["name"], B.F_SMALL, align=B.WRAP_TL)
        put(ws, f"C{r}", f"={O1}!E{r1}", B.F_BOLD, align=B.WRAP_C)
        put(ws, f"D{r}", f"=MAX(0,{O1}!AA{r1})", B.F_BOLD, fmt='0"元"', align=B.WRAP_C)
        put(ws, f"E{r}", f"=MAX(0,{O1}!Z{r1})", B.F_BOLD, fmt='0"元"', align=B.WRAP_C)
        put(ws, f"F{r}", f"={O1}!L{r1}", B.F_SMALL, fmt='0"元"', align=B.WRAP_C)
        put(ws, f"G{r}", c["spec_cn"], B.F_SMALL, align=B.WRAP_TL)
        msg = (f'="您好！我们是日本亚马逊卖家，计划采购以下产品，首单{c["qty"]}件，之后每月补货。"&CHAR(10)&'
               f'"【规格】{c["spec_cn"]}"&CHAR(10)&'
               f'"【请报价】50件／100件／300件的单价（含/不含税请注明）、交期、样品价格和运费。"&CHAR(10)&'
               f'"【请提供】每个外箱的尺寸（长×宽×高cm）和毛重（kg）、可否拆分为多箱、每箱数量；产品认证与检测报告。"&CHAR(10)&'
               f'"【包装】五层瓦楞纸箱，需通过跌落测试；日文说明书由我方提供。"&CHAR(10)&'
               f'"【目标价】"&TEXT(D{r},"0")&"元/件左右（最高不超过"&TEXT(E{r},"0")&"元）。谢谢！"')
        put(ws, f"H{r}", msg, B.F_SMALL, align=B.WRAP_TL)
        if c.get("user1688"):
            cell = put(ws, f"I{r}", c["user1688"], B.F_LINK, align=B.WRAP_TL)
            cell.hyperlink = DET1688.format(c["user1688"])
        put(ws, f"J{r}", c["user1688_check"], B.F_SMALL, align=B.WRAP_TL)
        ws.row_dimensions[r].height = 150
    for txt, fill in (("A", B.FILL_GO), ("B", B.FILL_COND), ("C", B.FILL_NO)):
        ws.conditional_formatting.add(f"C5:C{4 + len(rows)}", FormulaRule(formula=[f'LEFT(C5,1)="{txt}"'], fill=fill))
    ws.freeze_panes = "C5"


# ---------------------------------------------------------------------------------------------- 04 link check
def build_linkcheck(ws):
    ws.title = "04_1688リンク照合"
    put(ws, "A1", "ご提示の1688リンク（統合リストの原価確認先）が仕様と合っているかの照合と、仕様が一致する代替出品", B.F_TITLE, border=False)
    put(ws, "A2", f"{DATE}に1688の検索ページで取得（商品詳細ページは自動アクセスでロボット確認が出るため、カードの価格＝最安SKUの価格・月销）。"
                  "『不一致』の行は右側の仕様一致品を原価確認先にしてください。", B.F_NOTE, border=False)
    head_row(ws, 4, ["No", "商品", "ご提示リンク", "その出品の商品名", "価格（元）", "月销", "照合", "仕様一致品（代替）", "価格（元）", "月销"],
             [5, 30, 16, 44, 9, 8, 40, 44, 9, 8], height=32)
    r = 5
    for c in D.C:
        uo, ao = offer(c.get("user1688")), offer(c.get("alt1688"))
        put(ws, f"A{r}", c["id"], B.F_BOLD, align=B.WRAP_C)
        put(ws, f"B{r}", c["name"][:40], B.F_SMALL, align=B.WRAP_TL)
        if c.get("user1688"):
            cell = put(ws, f"C{r}", c["user1688"], B.F_LINK, align=B.WRAP_C)
            cell.hyperlink = DET1688.format(c["user1688"])
        else:
            put(ws, f"C{r}", "（なし）", B.F_SMALL, align=B.WRAP_C)
        put(ws, f"D{r}", (uo or {}).get("title", ""), B.F_SMALL, align=B.WRAP_TL)
        put(ws, f"E{r}", (uo or {}).get("price"), B.F_SMALL, fmt=CNY)
        put(ws, f"F{r}", (uo or {}).get("sold"), B.F_SMALL, fmt="#,##0")
        bad = "不一致" in c["user1688_check"]
        put(ws, f"G{r}", c["user1688_check"], B.F_RED if bad else B.F_SMALL, align=B.WRAP_TL, fill=B.FILL_NO if bad else None)
        if ao:
            cell = put(ws, f"H{r}", ao["title"], B.F_LINK, align=B.WRAP_TL)
            cell.hyperlink = DET1688.format(ao["id"])
            put(ws, f"I{r}", ao["price"], B.F_SMALL, fmt=CNY)
            put(ws, f"J{r}", ao["sold"], B.F_SMALL, fmt="#,##0")
        ws.row_dimensions[r].height = 42
        r += 1
    ws.freeze_panes = "C5"


# ---------------------------------------------------------------------------------------------- 05 amazon
def build_amazon(ws):
    ws.title = "05_Amazon実勢"
    put(ws, "A1", f"Amazon.co.jp の実勢（{DATE} 取得）：ご提示のASIN・試算の競合・市場の上位", B.F_TITLE, border=False)
    put(ws, "A2", "月販＝『過去1か月でN点以上購入』の下限。商品ページと検索カードで表示が違う場合は両方を記載（検索カードの数字はバリエーション全体の場合がある）。", B.F_NOTE, border=False)
    head_row(ws, 4, ["No", "区分", "ASIN", "価格（ページ）", "価格（検索）", "月販（ページ）", "月販（検索）", "評価数", "★", "売れ筋ランキング", "重量", "商品名"],
             [5, 16, 13, 10, 10, 9, 9, 8, 5, 40, 12, 70], height=32)
    r = 5
    for c in D.C:
        rows = [("試算の競合", c["rival"])]
        if USER_AMZ.get(c["id"]) and USER_AMZ[c["id"]] != c["rival"]:
            rows.append(("ご提示のASIN", USER_AMZ[c["id"]]))
        rows += [("市場上位", x["asin"]) for x in market(c["market_kws"], n=4) if x["asin"] not in {c["rival"], USER_AMZ.get(c["id"])}]
        for tag, asin in rows:
            d = amz(asin)
            vals = [c["id"], tag, asin, DET.get(asin, {}).get("price"), d.get("search_price"), d["bought_page"] if asin in DET else None,
                    d["bought_search"], d.get("reviews"), d.get("rating"), re.sub(r"\s*\(.*?\)\s*", " ", d.get("bsr") or "")[:60],
                    (d.get("weight") or "")[:14], d.get("title", "")[:100]]
            for j, v in enumerate(vals, start=1):
                cell = put(ws, f"{CL(j)}{r}", v, B.F_SMALL, fmt=YEN if j in (4, 5) else ("#,##0" if j in (6, 7, 8) else None),
                           align=B.WRAP_TL if j >= 10 else B.WRAP_C)
                if j == 3:
                    cell.font = B.F_LINK
                    cell.hyperlink = AMZ + asin
            r += 1
        us = USER_US.get(c["id"])
        if us:
            u = US.get(us, {})
            vals = [c["id"], "米国の参照品", us, None, None, None, None, u.get("reviews"), u.get("rating"), u.get("bsr", "")[:60], u.get("weight", "")[:14],
                    f"${u.get('usd')}・月{u.get('bought')}｜{u.get('title', '')[:90]}"]
            for j, v in enumerate(vals, start=1):
                cell = put(ws, f"{CL(j)}{r}", v, B.F_SMALL, align=B.WRAP_TL if j >= 10 else B.WRAP_C)
                if j == 3:
                    cell.font = B.F_LINK
                    cell.hyperlink = AMZ_US + us
            r += 1
    ws.freeze_panes = "D5"


# ---------------------------------------------------------------------------------------------- 1688 raw
def build_raw(ws):
    ws.title = "1688根拠"
    put(ws, "A1", f"1688 仕様一致品の一覧（{DATE}・検索ページのカード。広告枠は除外）", B.F_TITLE, border=False)
    head_row(ws, 3, ["No", "検索キー", "価格（元）", "月销", "累計", "最小ロット", "店舗", "商品名（クリックで1688）"], [5, 12, 9, 8, 8, 8, 26, 80])
    r = 4
    for c in D.C:
        os_ = offers(c["key"])
        pr = [o["price"] for o in os_]
        put(ws, f"A{r}", c["id"], B.F_BOLD)
        put(ws, f"B{r}", c["key"], B.F_SMALL)
        put(ws, f"H{r}", f"{len(os_)}件：P25 {q(pr, .25) or 0:.0f}元／中央値 {q(pr, .5) or 0:.0f}元／P75 {q(pr, .75) or 0:.0f}元（{c['kw_cn']}）", B.F_BOLD)
        r += 1
        for o in os_[:15]:
            vals = [c["id"], c["key"], o["price"], o["sold"], o.get("total"), o.get("moq"), o.get("shop"), o["title"]]
            for j, v in enumerate(vals, start=1):
                cell = put(ws, f"{CL(j)}{r}", v, B.F_SMALL, fmt=CNY if j == 3 else ("#,##0" if j in (4, 5) else None))
                if j == 8:
                    cell.font = B.F_LINK
                    cell.hyperlink = DET1688.format(o["id"])
            r += 1
    ws.freeze_panes = "C4"


# ---------------------------------------------------------------------------------------------- 00 summary
def build_summary(ws, rows, E):
    ws.title = "00_結論"
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 34
    for col, w in zip("CDEFGHIJK", (12, 10, 11, 11, 9, 10, 11, 10, 60)):
        ws.column_dimensions[col].width = w
    put(ws, "A1", "見積優先リストの利益見込みと再調査の結論（2026-11-08）", B.F_TITLE, border=False)
    put(ws, "A2", "Amazon.co.jp（商品ページ43件・検索38語）と1688（26仕様×2〜5語）を当日取得し、天瞳の料金表（2024.1.6版）で再計算。リサーチ表（原本テンプレート）は各候補シートに1枚ずつ。",
        B.F_NOTE, border=False)
    for i, t in enumerate(D.SUMMARY):
        ws.merge_cells(f"A{4 + i}:K{4 + i}")
        put(ws, f"A{4 + i}", t, B.F_BASE, align=B.WRAP_TL, border=False)
        ws.row_dimensions[4 + i].height = 66
    r0 = 5 + len(D.SUMMARY)
    head_row(ws, r0, ["No", "商品", "判定", "計画売価", "利益/個（広告10%）", "利益/個（広告5%）", "利益率（広告10%）", "競合月販", "原価上限（5%）", "旧試算 利益/個", "理由"],
             None, height=36)
    O1 = qs("01_利益見込み一覧")
    order = sorted(rows, key=lambda cr: ({"A": 0, "B": 1, "C": 2}[verdict(cr[0], E[cr[0]["id"]], amz(cr[0]["rival"])["bought_max"])[0]],
                                         -E[cr[0]["id"]]["p10"]))
    for i, (c, r1) in enumerate(order):
        r = r0 + 1 + i
        vals = [(c["id"], None), (c["name"][:34], None), (f"={O1}!E{r1}", None), (f"={O1}!J{r1}", YEN), (f"={O1}!V{r1}", YEN),
                (f"={O1}!U{r1}", YEN), (f"={O1}!W{r1}", PCT), (f"={O1}!I{r1}", "#,##0"), (f"={O1}!Z{r1}", '0"元"'),
                (c.get("old_profit") or c.get("old_note") or "", YEN), (D.REASON.get(c["id"], ""), None)]
        for j, (v, fmt) in enumerate(vals, start=1):
            cell = put(ws, f"{CL(j)}{r}", v, B.F_BOLD if j in (3, 5) else B.F_SMALL, fmt=fmt, align=B.WRAP_TL if j in (2, 11) else B.WRAP_C)
            if j == 1:
                cell.font = B.F_LINK
                link_sheet(cell, f"{qs(c['sheet'])}!A1")
        ws.row_dimensions[r].height = 40
    last = r0 + len(order)
    for txt, fill in (("A", B.FILL_GO), ("B", B.FILL_COND), ("C", B.FILL_NO)):
        ws.conditional_formatting.add(f"C{r0 + 1}:C{last}", FormulaRule(formula=[f'LEFT(C{r0 + 1},1)="{txt}"'], fill=fill))
    ws.conditional_formatting.add(f"E{r0 + 1}:F{last}", CellIsRule(operator="lessThan", formula=["0"], font=Font(color="C00000", bold=True)))
    ws.freeze_panes = f"C{r0 + 1}"


def build_sources(ws):
    ws.title = "出典"
    put(ws, "A1", "出典・取得方法", B.F_TITLE, border=False)
    rows = [
        ("天瞳 送料・保管料一覧表（2024.1.6版）", "アップロードいただいた料金表（docx）。海上運賃（法人）0〜2m³ 33,000円／2〜20m³ 17,325円／20m³以上 13,125円／20f 13,750円／40f 10,450円、保管 77円/m³/日、佐川60〜260サイズ。", ""),
        ("天瞳リサーチ表（テンプレート）", "アップロードいただいた原本（各候補シートはこの『リサーチ表』の複製。式は変更せず、複数個口の商品のみCBMを全個口の合計に置換）。", ""),
        ("Amazon.co.jp 商品ページ", f"{DATE} 取得（お届け先：東京都千代田区）。価格・月販バッジ・評価数・売れ筋ランキング・重量・梱包サイズ（記載がある場合）。", "https://www.amazon.co.jp/"),
        ("Amazon.co.jp 検索結果", f"{DATE} 取得（38語・1ページ目）。検索カードの価格・月販バッジ・評価数。", "https://www.amazon.co.jp/"),
        ("1688 検索ページ", f"{DATE} 取得（https://www.1688.com/market/-{{GBK}}.html）。カードの価格（最安SKU）・月销・累計・店舗。商品詳細ページ（detail.1688.com）は自動アクセスにロボット確認（スライダー）が出るため未取得＝SKU別価格は見積で確認。", "https://www.1688.com/"),
        ("Alibaba.com", "自動アクセスにロボット確認が出るため検索リンクのみ。", "https://www.alibaba.com/"),
        ("米国Amazon", "2026-10-27 取得の新着ランキング・商品ページ（N1〜N4の参照品）。", "https://www.amazon.com/"),
        ("関税率", "税関 実行関税率表（2026年10月31日版）：6306.22 テント WTO 4%（RCEP中国 2.5%）、3924.90 プラスチック製品 3.9%（1.8%）、7616.99 アルミ製品 3%（1.4%）、94類家具・9506運動用具・8716.80・9010.60は無税。",
         "https://www.customs.go.jp/tariff/2026_10_31/index.htm"),
        ("Amazon販売手数料", "2026年4月改定：売上750円超の15%→15.4%、10%→10.4%（税抜）。家具は2万円までの部分15.4%・超える部分10.4%。", ""),
    ]
    head_row(ws, 3, ["項目", "内容", "URL"], [30, 110, 40])
    for i, (a, b, u) in enumerate(rows):
        r = 4 + i
        put(ws, f"A{r}", a, B.F_BOLD, align=B.WRAP_TL)
        put(ws, f"B{r}", b, B.F_SMALL, align=B.WRAP_TL)
        cell = put(ws, f"C{r}", u, B.F_LINK if u else B.F_SMALL, align=B.WRAP_TL)
        if u:
            cell.hyperlink = u
        ws.row_dimensions[r].height = 40


# ---------------------------------------------------------------------------------------------- 06 extra leads
def build_extra(ws):
    ws.title = "06_追加候補"
    put(ws, "A1", "追加候補：v6の1,426商品を今回の厳しい条件（国際送料17,325円/m³・広告10%）で再計算した上位から、未検証の市場を1688の仕様一致品とAmazonの実勢で確認", B.F_TITLE, border=False)
    put(ws, "A2", f"{DATE}取得。値は作成時点の計算（式ではない）。日本の売れ筋価格に対して1688の一致品の原価が高い、またはかさばって送料が重いものはC。", B.F_NOTE, border=False)
    head_row(ws, 4, ["商品", "日本の売れ筋（クリックでAmazon）", "価格", "月販", "想定売価", "1688原価（元）", "梱包（cm・kg）", "国内送料", "利益/個（広告10%）",
                     "利益率（広告10%）", "判定", "根拠", "1688 仕様一致品（月销最多）"],
             [30, 40, 9, 7, 9, 9, 18, 9, 10, 9, 12, 60, 40], height=36)
    for i, x in enumerate(D.EXTRA):
        r = 5 + i
        c = dict(x, cny_c=x["cny"] * 1.25)
        e = econ7(c)
        cards = [y for items in EXTRA.get(x["key"], {}).get("amazon", {}).values() for y in items if y["asin"] == x["leader"]]
        lv = max(cards, key=lambda y: y.get("bought") or 0) if cards else None
        cn = [o for o in EXTRA.get(x["key"], {}).get("cn", []) if not o.get("ad")]
        v = "A 見積依頼" if e["m10"] >= PV["hi"] and (lv or {}).get("bought", 0) >= 100 else ("B 要追加調査" if e["m10"] >= PV["lo"] else "C 見送り")
        if v.startswith("A") and len(cn) < 3:  # cost not backed by enough spec-matched offers
            v = "B 要追加調査（原価未確認）"
        vals = [x["name"], (lv or {}).get("title", x["leader"])[:60], (lv or {}).get("price"), (lv or {}).get("bought"), x["price"], x["cny"],
                "／".join(f"{a}×{b}×{h} {k}kg" for a, b, h, k in x["boxes"]), e["dom"], round(e["p10"]), e["m10"], v, x["note"],
                f"{cn[0]['title'][:30]}（{cn[0]['price']:.0f}元・月销{cn[0]['sold']}）" if cn else "（一致品なし）"]
        for j, val in enumerate(vals, start=1):
            fmt = YEN if j in (3, 5, 8, 9) else (PCT if j == 10 else (CNY if j == 6 else ("#,##0" if j == 4 else None)))
            cell = put(ws, f"{CL(j)}{r}", val, B.F_BOLD if j in (9, 11) else B.F_SMALL, fmt=fmt, align=B.WRAP_TL if j in (1, 2, 12, 13) else B.WRAP_C)
            if j == 2:
                cell.font = B.F_LINK
                cell.hyperlink = AMZ + x["leader"]
            if j == 13 and cn:
                cell.font = B.F_LINK
                cell.hyperlink = DET1688.format(cn[0]["id"])
        ws.row_dimensions[r].height = 48
    ws.conditional_formatting.add(f"K5:K{4 + len(D.EXTRA)}", FormulaRule(formula=['LEFT(K5,1)="C"'], fill=B.FILL_NO))
    ws.conditional_formatting.add(f"K5:K{4 + len(D.EXTRA)}", FormulaRule(formula=['LEFT(K5,1)="B"'], fill=B.FILL_COND))


# ---------------------------------------------------------------------------------------------- main
def main(template, out):
    wb = load_workbook(template)
    tpl = wb["リサーチ表"]
    names = ["00_結論", "01_利益見込み一覧", "02_梱包・送料", "03_見積依頼（目標単価）", "04_1688リンク照合", "05_Amazon実勢", "06_追加候補",
             "1688根拠", "前提条件", "出典"]
    S = {n: wb.create_sheet(n) for n in names}
    rows = [(c, 6 + i) for i, c in enumerate(D.C)]
    E = {c["id"]: econ7(c) for c in D.C}
    build_assumptions(S["前提条件"])
    build_parcels(S["02_梱包・送料"], [(c, r - 1) for c, r in rows])
    build_overview(S["01_利益見込み一覧"], rows, E)
    build_rfq(S["03_見積依頼（目標単価）"], rows)
    build_linkcheck(S["04_1688リンク照合"])
    build_amazon(S["05_Amazon実勢"])
    build_raw(S["1688根拠"])
    build_extra(S["06_追加候補"])
    build_summary(S["00_結論"], rows, E)
    build_sources(S["出典"])
    sheets = [build_product(wb, tpl, c, r, r - 1, E[c["id"]]) for c, r in rows]
    tpl.title = "テンプレート(原本)"
    wb._sheets = [S[n] for n in names[:7]] + sheets + [S["1688根拠"], S["前提条件"], S["出典"], tpl]
    wb.active = 0
    for ws in wb.worksheets:
        ws.sheet_view.tabSelected = ws is S["00_結論"]
    wb.save(out)
    for c in D.C:
        e = E[c["id"]]
        dem = amz(c["rival"])["bought_max"]
        print(f"{c['id']:4s} {verdict(c, e, dem):10s} tm {(e['tm'] or 0) * 100:5.1f}% p5 {e['p5']:7.0f} p10 {e['p10']:7.0f} m10 {e['m10'] * 100:5.1f}% "
              f"pc {e['pc'] if e['pc'] is None else round(e['pc']):>7} cap5 {e['cap5']:5.0f} cap15 {e['cap15']:5.0f} dom {e['dom']}/{e['dom_c']} dem {dem} {c['name'][:22]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
