# -*- coding: utf-8 -*-
"""Build the v2 research workbook on top of the user's 天瞳 research template.

usage: python3 build_v2.py <template.xlsx> <out.xlsx>

Each finalist gets a copy of the template sheet (formulas untouched, the two
rival blocks and the review questions filled in) plus an added block that
recomputes our own planned product with the template formula and with a
real P&L. Everything reads from the 前提条件 sheet, so replacing the placeholder
domestic shipping table with 天瞳's rates updates the whole workbook.
"""
import sys
from copy import copy
from urllib.parse import quote

from openpyxl import load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink

import data_v2 as D

FONT = "游ゴシック"
F_BASE = Font(name=FONT, size=10)
F_SMALL = Font(name=FONT, size=9)
F_NOTE = Font(name=FONT, size=8, color="595959")
F_BOLD = Font(name=FONT, size=10, bold=True)
F_TITLE = Font(name=FONT, size=14, bold=True)
F_SUB = Font(name=FONT, size=11, bold=True, color="1F4E78")
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_EST = Font(name=FONT, size=10, italic=True, color="0000FF")
F_URL = Font(name=FONT, size=10, color="0563C1", underline="single")
F_LINK = Font(name=FONT, size=10, color="0563C1", underline="single")
F_RED = Font(name=FONT, size=10, bold=True, color="C00000")

FILL_HEAD = PatternFill("solid", fgColor="1F4E78")
FILL_SUB = PatternFill("solid", fgColor="DDEBF7")
FILL_IN = PatternFill("solid", fgColor="FFF2CC")
FILL_GO = PatternFill("solid", fgColor="C6EFCE")
FILL_COND = PatternFill("solid", fgColor="FFEB9C")
FILL_NO = PatternFill("solid", fgColor="E7E6E6")
FILL_KEY = PatternFill("solid", fgColor="FCE4D6")

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP_TL = Alignment(wrap_text=True, vertical="top", horizontal="left")
WRAP_C = Alignment(wrap_text=True, vertical="center", horizontal="center")
LEFT_C = Alignment(vertical="center", horizontal="left", wrap_text=True)

YEN = '"¥"#,##0;[Red]"-¥"#,##0;"¥0"'
PCT = '0.0%;[Red]-0.0%;0.0%'
CNY = '#,##0" 元"'
M3 = '0.000'
KG = '0.0"kg"'
CM = '0.0'

AS = "'前提条件'"
OV = "'01_商品化判断_総合'"
PK = "'梱包明細'"
RM = "'03_年商5億ロードマップ'"
P = {  # assumption cells
    "fx": f"{AS}!$B$4", "tfee": f"{AS}!$B$5", "tvat": f"{AS}!$B$6", "tduty": f"{AS}!$B$7",
    "frbig": f"{AS}!$B$8", "frsmall": f"{AS}!$B$9",
    "feeA": f"{AS}!$B$12", "feeB": f"{AS}!$B$13", "ad10": f"{AS}!$B$14", "ad5": f"{AS}!$B$15",
    "ret": f"{AS}!$B$16", "stor": f"{AS}!$B$17", "mon": f"{AS}!$B$18", "hand": f"{AS}!$B$19",
    "cn": f"{AS}!$B$20", "tax": f"{AS}!$B$21", "fr": f"{AS}!$B$22",
    "go_t": f"{AS}!$B$25", "go_r": f"{AS}!$B$26", "c_t": f"{AS}!$B$27", "c_r": f"{AS}!$B$28",
}
SZ_UP = f"{AS}!$D$34:$D$45"
SZ_NAME = f"{AS}!$B$34:$B$46"
SZ_RATE = f"{AS}!$E$34:$E$46"
WT_UP = f"{AS}!$I$34:$I$40"
WT_MIN = f"{AS}!$J$34:$J$41"

# Python mirror of the defaults (used for sorting and for checking LibreOffice)
DEF = dict(fx=23.5, tfee=0.165, tvat=0.10, tduty=0.10, fr=17325, feeA=0.154, feeB=0.104,
           ad10=0.10, ad5=0.05, ret=0.04, stor=3000, mon=1.5, hand=300, cn=0.08, tax=0.10,
           go_t=0.30, go_r=0.15, c_t=0.25, c_r=0.10)
SIZE_TABLE = [  # name, upper (three-side sum, cm), placeholder rate (yen)
    ("60サイズ", 60, 650), ("80サイズ", 80, 750), ("100サイズ", 100, 900),
    ("120サイズ", 120, 1050), ("140サイズ", 140, 1250), ("160サイズ", 160, 1450),
    ("170サイズ", 170, 1900), ("180サイズ", 180, 2200), ("200サイズ", 200, 2700),
    ("220サイズ", 220, 3300), ("240サイズ", 240, 3900), ("260サイズ", 260, 4600),
    ("家財便・チャーター（260cm超 or 50kg超）", None, 7000),
]
WEIGHT_TABLE = [(2, 1), (5, 2), (10, 3), (15, 4), (20, 5), (30, 6), (50, 7), (None, 13)]


def size_idx(s, kg):
    si = sum(1 for _, up, _ in SIZE_TABLE[:12] if up < s) + 1
    wi = WEIGHT_TABLE[sum(1 for up, _ in WEIGHT_TABLE[:7] if up < kg)][1]
    return max(si, wi)


def model(c):
    d = DEF
    cbm = sum(L * W * H for L, W, H, _ in c["parcels"]) / 1e6
    dom = sum(SIZE_TABLE[size_idx(L + W + H, kg) - 1][2] for L, W, H, kg in c["parcels"])
    n = len(c["parcels"])
    fee = d["feeA"] if c["fee"] == "A" else d["feeB"]
    J = c["cny"] * d["fx"]
    tq = c["price"] - J - dom - c["price"] * d["tfee"] - J * d["tvat"] - J * d["tduty"] - d["fr"] * cbm
    rev = c["price"] / (1 + d["tax"])
    landed = J * (1 + d["cn"]) + c["va"] + d["fr"] * cbm + (J * (1 + d["cn"]) + d["fr"] * cbm) * c["duty"]
    base = rev - c["price"] * fee - dom - rev * d["ret"] - cbm * d["stor"] * d["mon"] - d["hand"] * n - landed
    r10 = (base - rev * d["ad10"]) / rev
    r5 = (base - rev * d["ad5"]) / rev
    tm = tq / c["price"]
    judge = "GO" if tm >= d["go_t"] and r5 >= d["go_r"] else (
        "COND" if tm >= d["c_t"] and r5 >= d["c_r"] else "NO")
    return dict(cbm=cbm, dom=dom, tm=tm, r10=r10, r5=r5, p10=base - rev * d["ad10"],
                p5=base - rev * d["ad5"], landed=landed, judge=judge)


def link_sheet(cell, location):
    """Internal jump (location attribute, no external relationship)."""
    cell.hyperlink = Hyperlink(ref=cell.coordinate, location=location)


def link_1688(kw):
    return "https://s.1688.com/selloffer/offer_search.htm?charset=utf8&keywords=" + quote(kw)


def put(ws, ref, value, font=F_BASE, fmt=None, fill=None, align=None, border=True):
    cell = ws[ref]
    cell.value = value
    cell.font = font
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    if align:
        cell.alignment = align
    if border:
        cell.border = BORDER
    return cell


def head_row(ws, row, headers, widths=None, height=30):
    for i, h in enumerate(headers, start=1):
        put(ws, f"{get_column_letter(i)}{row}", h, F_HEAD, fill=FILL_HEAD, align=WRAP_C)
        if widths:
            ws.column_dimensions[get_column_letter(i)].width = widths[i - 1]
    ws.row_dimensions[row].height = height


def merge_put(ws, rng, value, font=F_BASE, fill=None, align=WRAP_TL, border=True):
    ws.merge_cells(rng)
    first = rng.split(":")[0]
    put(ws, first, value, font, fill=fill, align=align, border=border)


# ---------------------------------------------------------------------------
def build_assumptions(ws):
    ws.title = "前提条件"
    ws.column_dimensions["A"].width = 44
    for col, w in zip("BCDEFGHIJK", (14, 12, 12, 12, 40, 3, 12, 12, 14, 30)):
        ws.column_dimensions[col].width = w
    put(ws, "A1", "前提条件（ここを変えると全シートが再計算されます）", F_TITLE, border=False)
    put(ws, "A2", "黄色セル＝入力値。青字（斜体）＝推定値で要実測・要確認。国内送料表は天瞳の送料表が未入手のため仮置き（佐川・ヤマトの公示額と大口割引を参考）。",
        F_NOTE, border=False)

    put(ws, "A3", "① 天瞳リサーチ表（テンプレート）の計算パラメータ", F_SUB, border=False)
    tmpl = [
        (4, "人民元レート（円/元）", DEF["fx"], "0.00", "テンプレートI7と同じ。2026/9/24 実勢は約23.65円"),
        (5, "Amazon手数料（テンプレート）", DEF["tfee"], PCT, "テンプレートL7と同じ16.5%。2026/4以降の実質は15.4%＋消費税＝16.94%（ホーム・ペット等）"),
        (6, "消費税（輸入・仕入原価×）", DEF["tvat"], PCT, "テンプレートM7と同じ"),
        (7, "関税（仕入原価×）", DEF["tduty"], PCT, "テンプレートN7と同じ（実際は家具・金属製品の多くが0%）"),
        (8, "国際送料 発注合計2m³超（円/m³）", DEF["fr"], YEN, "確認事項8"),
        (9, "国際送料 発注合計2m³以下（円/m³）", 33000, YEN, "確認事項8（初回小ロット時）"),
    ]
    for r, label, v, fmt, note in tmpl:
        put(ws, f"A{r}", label)
        put(ws, f"B{r}", v, fmt=fmt, fill=FILL_IN)
        put(ws, f"C{r}", note, F_NOTE, align=LEFT_C, border=False)

    put(ws, "A11", "② 実質試算（Claude）の追加パラメータ", F_SUB, border=False)
    real = [
        (12, "販売手数料A（ホーム・ペット・DIY・オフィス・産業・ベビー）", DEF["feeA"], PCT, "税抜。売価（税込）×率。仕入税額控除で消費税分は戻る"),
        (13, "販売手数料B（スポーツ・カー用品・おもちゃ・ドラッグ）", DEF["feeB"], PCT, "同上"),
        (14, "広告費（立ち上げ期・保守）売上比", DEF["ad10"], PCT, "1位獲得までの期間"),
        (15, "広告費（1位定着後）売上比", DEF["ad5"], PCT, "オーガニック中心になった後"),
        (16, "返品・破損 売上比", DEF["ret"], PCT, "大型品は配送破損を見込む"),
        (17, "保管料（円/m³/月）", DEF["stor"], YEN, "天瞳倉庫の実額に要差替え"),
        (18, "平均保管月数", DEF["mon"], "0.0", ""),
        (19, "出荷作業費（円/個口）", DEF["hand"], YEN, "天瞳倉庫の実額に要差替え"),
        (20, "中国側諸費用（検品・国内運送・代行）仕入原価比", DEF["cn"], PCT, ""),
        (21, "消費税率（売上）", DEF["tax"], PCT, "売上の消費税は納税。輸入消費税は控除で戻る"),
        (22, "国際送料（実質試算で使う単価）", f"={P['frbig']}", YEN, "量産時（2m³超）の単価"),
    ]
    for r, label, v, fmt, note in real:
        put(ws, f"A{r}", label)
        put(ws, f"B{r}", v, fmt=fmt, fill=FILL_IN)
        put(ws, f"C{r}", note, F_NOTE, align=LEFT_C, border=False)

    put(ws, "A24", "③ 判定基準", F_SUB, border=False)
    crit = [
        (25, "GO：テンプレ利益率 下限", DEF["go_t"]), (26, "GO：実質利益率（広告5%）下限", DEF["go_r"]),
        (27, "COND：テンプレ利益率 下限", DEF["c_t"]), (28, "COND：実質利益率（広告5%）下限", DEF["c_r"]),
    ]
    for r, label, v in crit:
        put(ws, f"A{r}", label)
        put(ws, f"B{r}", v, fmt=PCT, fill=FILL_IN)
    put(ws, "C25", "両方を満たせばGO。テンプレ利益率は広告・返品・保管・出荷作業・売上消費税を含まないため、実質より約20pt高く出る（テンプレ15%≒実質赤字）",
        F_NOTE, align=LEFT_C, border=False)
    ws.merge_cells("C25:F28")
    ws["C25"].alignment = WRAP_TL

    put(ws, "A31", "④ 国内送料表（仮置き：天瞳の送料表をE列に入力してください）", F_SUB, border=False)
    put(ws, "H31", "重量区分（重量によってサイズが繰り上がる）", F_SUB, border=False)
    for col, h in zip("ABCDEF", ("区分No", "サイズ区分", "三辺合計（超）", "三辺合計（以下）", "送料（円/個口）", "備考")):
        put(ws, f"{col}33", h, F_HEAD, fill=FILL_HEAD, align=WRAP_C)
    for col, h in zip("HIJK", ("重量（超）kg", "重量（以下）kg", "最低サイズ区分No", "備考")):
        put(ws, f"{col}33", h, F_HEAD, fill=FILL_HEAD, align=WRAP_C)
    lower = 0
    for i, (name, up, rate) in enumerate(SIZE_TABLE, start=1):
        r = 33 + i
        put(ws, f"A{r}", i)
        put(ws, f"B{r}", name)
        put(ws, f"C{r}", lower)
        put(ws, f"D{r}", up if up is not None else "―")
        put(ws, f"E{r}", rate, fmt=YEN, fill=FILL_IN, font=F_EST)
        put(ws, f"F{r}", "仮置き（要差替え）", F_NOTE)
        lower = up if up is not None else lower
    wl = 0
    for i, (up, idx) in enumerate(WEIGHT_TABLE, start=1):
        r = 33 + i
        put(ws, f"H{r}", wl)
        put(ws, f"I{r}", up if up is not None else "―")
        put(ws, f"J{r}", idx)
        put(ws, f"K{r}", "50kg超は家財便・チャーター扱い" if up is None else "", F_NOTE)
        wl = up if up is not None else wl

    put(ws, "A49", "⑤ 読み方・注意", F_SUB, border=False)
    notes = [
        "・テンプレート（天瞳）の利益率＝売価−原価−国内送料−手数料16.5%−輸入消費税−関税−国際送料。広告費・返品・保管料・出荷作業費・売上の消費税が入っていない。",
        "・実質利益率＝税抜売上−販売手数料−国内送料−返品−保管−出荷作業−（原価×1.08＋付加価値費＋国際送料）−広告費。輸入消費税・手数料の消費税は仕入税額控除で戻る前提。",
        "・判定はテンプレ30%以上かつ実質（広告5%）15%以上をGO。前回ご指定の「利益率15%以上」はテンプレ基準だと実質マイナスになり得るため、基準を引き上げた。",
        "・Amazon手数料：2026年4月1日改定で売上750円超は15%→15.4%、10%→10.4%（税抜表示）。テンプレの16.5%は実質16.94%（15.4%×1.1）よりやや低い。",
        "・国内送料：三辺合計と重量の大きい方の区分を採用。260cm超・50kg超は家財便（仮¥7,000）。天瞳の送料表を入れれば全シートが更新される。",
        "・ランキング（30/60/90日平均）・月販はKeepa／セラースプライト等で要取得（本調査環境からAmazon・1688に直接接続できなかったため）。",
    ]
    for i, t in enumerate(notes):
        r = 50 + i
        ws.merge_cells(f"A{r}:K{r}")
        put(ws, f"A{r}", t, F_SMALL, align=WRAP_TL, border=False)
        ws.row_dimensions[r].height = 28
    ws.freeze_panes = "A4"


def ship_formula(sum_ref, kg_ref):
    return (f"=INDEX({SZ_RATE},MAX(COUNTIF({SZ_UP},\"<\"&{sum_ref})+1,"
            f"INDEX({WT_MIN},COUNTIF({WT_UP},\"<\"&{kg_ref})+1)))")


def build_parcels(ws, rows):
    ws.title = "梱包明細"
    put(ws, "A1", "梱包明細（1行＝1個口。国内送料は前提条件の送料表から自動計算）", F_TITLE, border=False)
    put(ws, "A2", "梱包寸法は1688類似品・製品寸法からの推定（青字）。サンプル入手後に実測値へ置き換えてください。", F_NOTE, border=False)
    head_row(ws, 3, ["候補No", "商品名", "個口", "縦(cm)", "横(cm)", "高(cm)", "重量(kg)", "三辺合計",
                     "区分No", "サイズ区分", "国内送料", "CBM"],
             widths=[9, 46, 6, 9, 9, 9, 9, 10, 8, 26, 11, 9])
    r = 4
    first = {}
    for c in rows:
        for k, (L, W, H, kg) in enumerate(c["parcels"], start=1):
            first.setdefault(c["id"], r)
            put(ws, f"A{r}", c["id"])
            put(ws, f"B{r}", c["name"], F_SMALL)
            put(ws, f"C{r}", k)
            for col, v in zip("DEFG", (L, W, H, kg)):
                put(ws, f"{col}{r}", v, F_EST, fmt=CM)
            put(ws, f"H{r}", f"=D{r}+E{r}+F{r}", fmt=CM)
            put(ws, f"I{r}", f"=MAX(COUNTIF({SZ_UP},\"<\"&H{r})+1,INDEX({WT_MIN},COUNTIF({WT_UP},\"<\"&G{r})+1))")
            put(ws, f"J{r}", f"=INDEX({SZ_NAME},I{r})", F_SMALL)
            put(ws, f"K{r}", f"=INDEX({SZ_RATE},I{r})", fmt=YEN)
            put(ws, f"L{r}", f"=D{r}*E{r}*F{r}/1000000", fmt=M3)
            r += 1
    ws.freeze_panes = "C4"
    ws.auto_filter.ref = f"A3:L{r - 1}"
    return first


ORDER = {"採用（HERO）": 0, "採用（HERO候補）": 1, "採用": 2, "採用（サポート）": 3}


FIN_IDX = {c["id"]: i for i, c in enumerate(D.FINALISTS)}


def sort_key(c, m):
    f = c["final"] or ""
    if c["id"] in FIN_IDX and (f in ORDER or f.startswith("条件付き")):
        return (ORDER.get(f, 4), 0, FIN_IDX[c["id"]])
    if f in ORDER:
        g = ORDER[f]
    elif f.startswith("条件付き"):
        g = 4
    elif f.startswith("保留"):
        g = 5
    elif f.startswith("不採用"):
        g = 7
    else:
        g = {"GO": 4.5, "COND": 5.5}.get(m["judge"], 7)
    return (g, 1, -m["r5"])


def build_overview(ws, rows, models):
    ws.title = "01_商品化判断_総合"
    put(ws, "A1", "商品化判断 総合表（全68候補・同一条件で再計算）", F_TITLE, border=False)
    put(ws, "A2", "青字＝推定値。数値判定：テンプレ利益率≥30%かつ実質利益率（広告5%）≥15%→GO／≥25%かつ≥10%→COND／それ以外NO。"
                  "最終判定は1位獲得の可能性・データ確度・価格実勢を加味。月販目標は3年目の計画値（03シート）。", F_NOTE, border=False)
    headers = ["No", "商品名（企画仕様）", "出典", "販売手数料率", "想定売価（定常・税込）", "1688原価（元）",
               "付加価値費（円）", "実関税率", "個口", "CBM", "国内送料", "円の商品原価",
               "テンプレ粗利", "テンプレ利益率", "売上（税抜）", "1個仕入総額（原価+諸費用+付加価値+国際送料）",
               "広告費前利益", "実質利益率（広告10%）", "実質利益率（広告5%）", "1個利益（広告10%）", "1個利益（広告5%）",
               "数値判定", "最終判定", "1位可能性", "現1位・主要競合（価格）", "差別化の核／判断理由",
               "月販目標（3年目）", "月利目標（3年目）", "詳細シート"]
    widths = [7, 40, 5, 8, 10, 8, 8, 6, 5, 7, 9, 9, 10, 9, 10, 12, 10, 9, 9, 10, 10, 7, 14, 6, 44, 52, 8, 11, 16]
    head_row(ws, 4, headers, widths, height=48)
    rowmap = {}
    order = sorted(rows, key=lambda c: sort_key(c, models[c["id"]]))
    for i, c in enumerate(order):
        r = 5 + i
        rowmap[c["id"]] = r
        put(ws, f"A{r}", c["id"])
        put(ws, f"B{r}", c["name"], F_SMALL, align=LEFT_C)
        put(ws, f"C{r}", c["src"])
        put(ws, f"D{r}", f"={P['feeA'] if c['fee'] == 'A' else P['feeB']}", fmt=PCT)
        put(ws, f"E{r}", c["price"], fmt=YEN, fill=FILL_IN)
        put(ws, f"F{r}", c["cny"], F_EST, fmt=CNY, fill=FILL_IN)
        put(ws, f"G{r}", c["va"], fmt=YEN, fill=FILL_IN)
        put(ws, f"H{r}", c["duty"], fmt=PCT, fill=FILL_IN)
        put(ws, f"I{r}", f"=COUNTIF({PK}!$A:$A,$A{r})")
        put(ws, f"J{r}", f"=SUMIF({PK}!$A:$A,$A{r},{PK}!$L:$L)", fmt=M3)
        put(ws, f"K{r}", f"=SUMIF({PK}!$A:$A,$A{r},{PK}!$K:$K)", fmt=YEN)
        put(ws, f"L{r}", f"=F{r}*{P['fx']}", fmt=YEN)
        put(ws, f"M{r}", f"=E{r}-L{r}-K{r}-E{r}*{P['tfee']}-L{r}*{P['tvat']}-L{r}*{P['tduty']}-{P['frbig']}*J{r}", fmt=YEN)
        put(ws, f"N{r}", f"=M{r}/E{r}", fmt=PCT)
        put(ws, f"O{r}", f"=E{r}/(1+{P['tax']})", fmt=YEN)
        put(ws, f"P{r}", f"=L{r}*(1+{P['cn']})+G{r}+{P['fr']}*J{r}+(L{r}*(1+{P['cn']})+{P['fr']}*J{r})*H{r}", fmt=YEN)
        put(ws, f"Q{r}", f"=O{r}-E{r}*D{r}-K{r}-O{r}*{P['ret']}-J{r}*{P['stor']}*{P['mon']}-{P['hand']}*I{r}-P{r}", fmt=YEN)
        put(ws, f"R{r}", f"=(Q{r}-O{r}*{P['ad10']})/O{r}", fmt=PCT)
        put(ws, f"S{r}", f"=(Q{r}-O{r}*{P['ad5']})/O{r}", F_BOLD, fmt=PCT)
        put(ws, f"T{r}", f"=Q{r}-O{r}*{P['ad10']}", fmt=YEN)
        put(ws, f"U{r}", f"=Q{r}-O{r}*{P['ad5']}", fmt=YEN)
        put(ws, f"V{r}", f"=IF(AND(N{r}>={P['go_t']},S{r}>={P['go_r']}),\"GO\",IF(AND(N{r}>={P['c_t']},S{r}>={P['c_r']}),\"COND\",\"NO\"))",
            F_BOLD, align=WRAP_C)
        if c["final"]:
            put(ws, f"W{r}", c["final"], F_SMALL, align=WRAP_C)
        else:
            put(ws, f"W{r}", f"=IF(V{r}=\"GO\",\"採用候補（要精査）\",IF(V{r}=\"COND\",\"見送り（薄利）\",\"不採用\"))", F_SMALL, align=WRAP_C)
        put(ws, f"X{r}", c["rank1"], align=WRAP_C)
        put(ws, f"Y{r}", c["comp"], F_SMALL, align=WRAP_TL)
        put(ws, f"Z{r}", c["diff"], F_SMALL, align=WRAP_TL)
        if c.get("y"):
            put(ws, f"AA{r}", c["y"][2], fmt="#,##0", fill=FILL_IN)
            put(ws, f"AB{r}", f"=AA{r}*U{r}", F_BOLD, fmt=YEN)
        else:
            put(ws, f"AA{r}", None)
            put(ws, f"AB{r}", None)
        if c.get("sheet"):
            cell = put(ws, f"AC{r}", c["sheet"], F_LINK)
            link_sheet(cell, f"'{c['sheet']}'!A1")
        else:
            put(ws, f"AC{r}", None)
        ws.row_dimensions[r].height = 42
    last = 4 + len(order)
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:AC{last}"
    rng = f"V5:V{last}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=['V5="GO"'], fill=FILL_GO))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['V5="COND"'], fill=FILL_COND))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['V5="NO"'], fill=FILL_NO))
    rng = f"W5:W{last}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=['OR(ISNUMBER(SEARCH("不採用",W5)),ISNUMBER(SEARCH("見送り",W5)))'], fill=FILL_NO))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['OR(ISNUMBER(SEARCH("条件",W5)),ISNUMBER(SEARCH("保留",W5)))'], fill=FILL_COND))
    ws.conditional_formatting.add(rng, FormulaRule(formula=['ISNUMBER(SEARCH("採用",W5))'], fill=FILL_GO))
    return rowmap, last


# ---------------------------------------------------------------------------
BLOCKS = [  # template rows for rival 1 / rival 2
    dict(name="F2", site="F3", maker="F4", price="F5", pkg=("I4", "J4", "K4"), pkg_kg="M4",
         prod=("I5", "J5", "K5"), prod_kg="M5", note="Q4", asin="E7", vrow=7, sum_ref="P5",
         wcheck="O5"),
    dict(name="F10", site="F11", maker="F12", price="F13", pkg=("I12", "J12", "K12"), pkg_kg="M12",
         prod=("I13", "J13", "K13"), prod_kg="M13", note="Q12", asin="E15", vrow=15, sum_ref="P13",
         wcheck="O13"),
]


def copy_conditional_formatting(src, dst):
    for cf in src.conditional_formatting:
        for rule in cf.rules:
            dst.conditional_formatting.add(str(cf.sqref), copy(rule))


def fill_rival(ws, b, rv, spec, cand):
    put(ws, b["name"], rv["name"], F_BASE, align=LEFT_C, border=False)
    cell = put(ws, b["site"], rv["url"], F_URL, align=LEFT_C, border=False)
    cell.hyperlink = rv["url"]
    put(ws, b["maker"], rv["maker"], F_BASE, align=WRAP_C, border=False)
    put(ws, b["price"], rv["price_note"], F_EST if rv["price_est"] else F_BASE, align=WRAP_C, border=False)
    for ref, v in zip(b["pkg"], rv["pkg"]):
        put(ws, ref, v, F_EST if rv["est"] else F_BASE, fmt=CM, align=WRAP_C, border=False)
    put(ws, b["pkg_kg"], rv["pkg_kg"], F_EST if rv["est"] else F_BASE, fmt=KG, align=WRAP_C, border=False)
    for ref, v in zip(b["prod"], rv["prod"]):
        put(ws, ref, v, F_SMALL, fmt=CM if not isinstance(v, str) else None, align=WRAP_C, border=False)
    put(ws, b["prod_kg"], rv["prod_kg"], F_SMALL, align=WRAP_C, border=False)
    put(ws, b["wcheck"], f"=IF({b['pkg_kg']}<=50,\"OK\",\"50kg超\")", F_SMALL, align=WRAP_C, border=False)
    note = (f"【根拠】{rv['note']}\n青字＝推定値（梱包は製品寸法＋梱包材で推定・要実測、原価は1688類似品の卸価格帯から推定・要見積）。"
            "1688・Amazonの検索リンクは下の【Claude追記】ブロック（93〜94行目）")
    put(ws, b["note"], note, F_NOTE, align=WRAP_TL, border=False)
    put(ws, b["asin"], rv["asin"], F_SMALL, align=WRAP_C, border=False)
    r = b["vrow"]
    put(ws, f"G{r}", rv["price"], F_EST if rv["price_est"] else F_BASE,
        fmt='"¥"#,##0_);[Red]\\("¥"#,##0\\)', border=False)
    put(ws, f"H{r}", rv["cny"], F_EST, fmt=CNY, border=False)
    put(ws, f"I{r}", f"={P['fx']}", Font(name="Arial", size=12), align=WRAP_C, border=False)
    put(ws, f"K{r}", ship_formula(b["sum_ref"], b["pkg_kg"]), Font(name="Arial", size=12),
        fmt='"¥"#,##0', border=False)
    put(ws, f"O{r}", f"={P['frbig']}", Font(name="Arial", size=12), fmt="#,##0", border=False)
    put(ws, f"T{r}", spec["target"], Font(name="Arial", size=12), align=Alignment(horizontal="right"), border=False)
    put(ws, f"V{r}", "要Keepa", F_SMALL, align=WRAP_C, border=False)
    put(ws, f"W{r}", cand["order"], Font(name="Arial", size=12), align=Alignment(horizontal="right"), border=False)


def add_plan_block(ws, spec, cand, ov_row, pk_row):
    s = 77
    blue = PatternFill("solid", fgColor="BDD7EE")
    merge_put(ws, f"A{s}:O{s}", "【Claude追記】自社企画品（差別化仕様）の収益試算 ― 左：企画仕様、右上：テンプレート式、右下：実質（広告・返品・保管・出荷作業・売上消費税を反映）",
              F_BOLD, fill=blue, align=LEFT_C)
    ws.row_dimensions[s].height = 22
    left = [
        (s + 1, "企画品名", f"={OV}!B{ov_row}", None),
        (s + 2, "想定販売価格（定常）", f"={OV}!E{ov_row}", YEN),
        (s + 3, "導入価格（レビュー獲得期）", cand["launch"], YEN),
        (s + 4, "1688仕入原価（元）", f"={OV}!F{ov_row}", CNY),
        (s + 5, "レート", f"={P['fx']}", "0.00"),
        (s + 6, "円の商品原価", f"=E{s + 4}*E{s + 5}", YEN),
        (s + 7, "付加価値費（説明書・固定キット等）", f"={OV}!G{ov_row}", YEN),
        (s + 8, "梱包 縦／横／高（cm）", None, None),
        (s + 9, "梱包重量（kg）", f"={PK}!G{pk_row}", KG),
        (s + 10, "CBM（体積）", f"=E{s + 8}*F{s + 8}*G{s + 8}/1000000", M3),
        (s + 11, "三辺合計（cm）", f"=E{s + 8}+F{s + 8}+G{s + 8}", CM),
        (s + 12, "国内送料（前提条件の送料表）", ship_formula(f"E{s + 11}", f"E{s + 9}"), YEN),
        (s + 13, "月販目標（2年目）", cand["y"][1], "#,##0"),
        (s + 14, "初回発注数", cand["order"], "#,##0"),
        (s + 15, "初回仕入資金（原価・諸費用・付加価値・国際送料）", None, YEN),
    ]
    for r, label, v, fmt in left:
        ws.merge_cells(f"A{r}:D{r}")
        put(ws, f"A{r}", label, F_SMALL, fill=FILL_SUB, align=LEFT_C)
        if r == s + 1:
            ws.merge_cells(f"E{r}:O{r}")
            put(ws, f"E{r}", v, F_BOLD, align=LEFT_C)
        elif r == s + 8:
            put(ws, f"E{r}", f"={PK}!D{pk_row}", fmt=CM)
            put(ws, f"F{r}", f"={PK}!E{pk_row}", fmt=CM)
            put(ws, f"G{r}", f"={PK}!F{pk_row}", fmt=CM)
        elif r == s + 15:
            put(ws, f"E{r}", f"=E{s + 14}*(E{s + 6}*(1+{P['cn']})+E{s + 7}+{P['fr']}*E{s + 10})", F_BOLD, fmt=YEN)
        else:
            put(ws, f"E{r}", v, fmt=fmt, fill=FILL_IN if r in (s + 3, s + 13, s + 14) else None)
    # right panel
    merge_put(ws, f"I{s + 2}:O{s + 2}", "テンプレート式（天瞳リサーチ表と同じ計算）", F_BOLD, fill=FILL_SUB, align=LEFT_C)
    tm = [
        (s + 3, "販売価額", f"=E{s + 2}", YEN),
        (s + 4, "円の商品原価", f"=E{s + 6}", YEN),
        (s + 5, "国内送料", f"=E{s + 12}", YEN),
        (s + 6, "Amazon手数料（16.5%）", f"=M{s + 3}*{P['tfee']}", YEN),
        (s + 7, "消費税（原価×10%）", f"=M{s + 4}*{P['tvat']}", YEN),
        (s + 8, "関税（原価×10%）", f"=M{s + 4}*{P['tduty']}", YEN),
        (s + 9, "国際運送（17,325円×CBM）", f"={P['frbig']}*E{s + 10}", YEN),
        (s + 10, "粗利（テンプレ）", f"=M{s + 3}-M{s + 4}-M{s + 5}-M{s + 6}-M{s + 7}-M{s + 8}-M{s + 9}", YEN),
        (s + 11, "利益率（テンプレ）", f"=M{s + 10}/M{s + 3}", PCT),
    ]
    rl = [
        (s + 13, "売上（税抜）", f"=E{s + 2}/(1+{P['tax']})", YEN),
        (s + 14, "販売手数料（カテゴリ率×売価）", f"=E{s + 2}*{OV}!D{ov_row}", YEN),
        (s + 15, "国内送料", f"=E{s + 12}", YEN),
        (s + 16, "返品・破損（売上×4%）", f"=M{s + 13}*{P['ret']}", YEN),
        (s + 17, "保管料（CBM×3,000円×1.5か月）", f"=E{s + 10}*{P['stor']}*{P['mon']}", YEN),
        (s + 18, "出荷作業費", f"={P['hand']}", YEN),
        (s + 19, "仕入原価（中国側諸費用8%込）", f"=E{s + 6}*(1+{P['cn']})", YEN),
        (s + 20, "付加価値費", f"=E{s + 7}", YEN),
        (s + 21, "国際送料", f"={P['fr']}*E{s + 10}", YEN),
        (s + 22, "広告費前利益", f"=M{s + 13}-SUM(M{s + 14}:M{s + 21})", YEN),
        (s + 23, "実質利益（広告10%：立ち上げ期）", f"=M{s + 22}-M{s + 13}*{P['ad10']}", YEN),
        (s + 24, "実質利益（広告5%：1位定着後）", f"=M{s + 22}-M{s + 13}*{P['ad5']}", YEN),
        (s + 25, "判定（テンプレ≥30%かつ実質≥15%→GO）", None, None),
        (s + 26, "月利（2年目の月販×実質利益・広告5%）", f"=E{s + 13}*M{s + 24}", YEN),
    ]
    for r, label, v, fmt in tm + rl:
        ws.merge_cells(f"I{r}:L{r}")
        put(ws, f"I{r}", label, F_SMALL, fill=FILL_SUB, align=LEFT_C)
        if r == s + 25:
            put(ws, f"M{r}", f"=IF(AND(M{s + 11}>={P['go_t']},N{s + 24}>={P['go_r']}),\"GO\",IF(AND(M{s + 11}>={P['c_t']},N{s + 24}>={P['c_r']}),\"COND\",\"NO\"))",
                F_RED, align=WRAP_C)
        else:
            put(ws, f"M{r}", v, F_BOLD if r in (s + 10, s + 11, s + 24, s + 26) else F_BASE, fmt=fmt)
    merge_put(ws, f"I{s + 12}:O{s + 12}", "実質（Claude試算：広告・返品・保管・出荷作業・売上消費税を反映）", F_BOLD, fill=FILL_SUB, align=LEFT_C)
    for r in (s + 23, s + 24):
        put(ws, f"N{r}", f"=M{r}/M{s + 13}", F_BOLD, fmt=PCT)
        put(ws, f"O{r}", "利益率", F_NOTE, border=False)
    links = (
        (s + 16, "1688で同等品を検索（クリック）", f"▶ 1688：{spec['kw_cn']}", link_1688(spec["kw_cn"])),
        (s + 17, "Amazonで競合を検索（クリック）", f"▶ Amazon：{spec['kw_jp']}",
         "https://www.amazon.co.jp/s?k=" + quote(spec["kw_jp"])),
    )
    for r, label, text, url in links:
        ws.merge_cells(f"A{r}:D{r}")
        put(ws, f"A{r}", label, F_SMALL, fill=FILL_SUB, align=LEFT_C)
        ws.merge_cells(f"E{r}:H{r}")
        cell = put(ws, f"E{r}", text, F_LINK, align=LEFT_C)
        cell.hyperlink = url


def build_product_sheet(wb, tpl, spec, cand, ov_row, pk_row):
    ws = wb.copy_worksheet(tpl)
    ws.title = spec["sheet"]
    copy_conditional_formatting(tpl, ws)
    ws["A1"].value = f"リサーチ｜{spec['code']} {spec['title']}"
    ws["A1"].font = Font(name=FONT, size=20, bold=True)
    for b, rv in zip(BLOCKS, spec["rivals"]):
        fill_rival(ws, b, rv, spec, cand)
    ws["E9"].value = ("※売れ筋ランキング30/60/90日平均はKeepa等の有料ツールで取得してください（本調査環境からAmazonへ直接接続できず未記入＝緑のまま）。"
                      "青字は推定値。G列の販売価額はライバルの実勢価格、H列の原価は同等仕様を1688で作った場合の推定。")
    ws["E9"].font = F_NOTE
    ws["E9"].alignment = LEFT_C
    for ref, key in (("B31", "merits"), ("B36", "demerits"), ("B41", "ours"), ("B47", "latent")):
        c = ws[ref]
        c.value = spec[key]
        c.font = Font(name=FONT, size=10)
        c.alignment = WRAP_TL
    for r in list(range(31, 35)) + list(range(36, 40)):
        ws.row_dimensions[r].height = 30
    ws["B30"].value = (ws["B30"].value or "") + "　【優先度】A＝★1〜2レビューに頻出・購入判断に直結／B＝改善で満足度が上がる／C＝あると嬉しい"
    ws["Y1"].value = spec["memo"]
    ws["Y1"].font = Font(name=FONT, size=10)
    ws["Y1"].alignment = WRAP_TL
    for col in ("Y", "Z", "AA", "AB"):
        ws.column_dimensions[col].width = 16
    add_plan_block(ws, spec, cand, ov_row, pk_row)
    return ws


# ---------------------------------------------------------------------------
def build_strategy(ws):
    ws.title = "02_1位獲得戦略"
    put(ws, "A1", "ランキング1位を取るための戦略（採用8品）", F_TITLE, border=False)
    put(ws, "A2", "1位ライン目安の月販は計画上の目安。Keepa／セラースプライトで上位10品の月販を確認してから発注数を確定してください。", F_NOTE, border=False)
    headers = ["詳細シート", "役割", "狙うノード・キーワード", "現在の上位・競合（価格）", "1位を取れる根拠（勝ち筋）",
               "差別化仕様（必須）", "価格戦略（導入→定常）", "1位ライン目安（月販）", "立ち上げ施策（レビュー・広告・画像）",
               "主なリスクと対策", "次に確認すること"]
    head_row(ws, 4, headers, [16, 10, 34, 36, 40, 38, 20, 12, 34, 30, 32], height=36)
    for i, row in enumerate(D.STRATEGY):
        r = 5 + i
        for j, v in enumerate(row, start=1):
            cell = put(ws, f"{get_column_letter(j)}{r}", v, F_SMALL, align=WRAP_TL)
            if j == 1:
                cell.font = F_LINK
                link_sheet(cell, f"'{v}'!A1")
        ws.row_dimensions[r].height = 120
    ws.freeze_panes = "B5"


def build_roadmap(ws, rowmap):
    ws.title = "03_年商5億ロードマップ"
    put(ws, "A1", "年商5億円・年収5,000万円への到達計画（Amazon＋楽天・Yahoo!）", F_TITLE, border=False)
    put(ws, "A2", "月販は計画値（黄色＝入力）。1年目は広告10%、2年目以降は広告5%（1位定着後）で利益を計算。固定費（人件費・事務所・ツール）と法人税は含まない。",
        F_NOTE, border=False)
    headers = ["商品", "役割", "詳細シート", "定常売価", "1個利益（広告10%）", "1個利益（広告5%）", "1個仕入総額",
               "1年目 月販", "2年目 月販", "3年目 月販", "1年目 年商", "2年目 年商", "3年目 年商",
               "1年目 年利", "2年目 年利", "3年目 年利"]
    head_row(ws, 4, headers, [40, 14, 16, 10, 10, 10, 10, 8, 8, 8, 14, 14, 14, 13, 13, 13], height=36)
    r = 5
    for c in D.FINALISTS:
        o = rowmap[c["id"]]
        put(ws, f"A{r}", f"={OV}!B{o}", F_SMALL, align=LEFT_C)
        put(ws, f"B{r}", c["role"], F_SMALL, align=WRAP_C)
        if c["sheet"]:
            cell = put(ws, f"C{r}", c["sheet"], F_LINK)
            link_sheet(cell, f"'{c['sheet']}'!A1")
        else:
            cell = put(ws, f"C{r}", f"01シート {c['id']}", F_LINK)
            link_sheet(cell, f"{OV}!A{o}")
        put(ws, f"D{r}", f"={OV}!E{o}", fmt=YEN)
        put(ws, f"E{r}", f"={OV}!T{o}", fmt=YEN)
        put(ws, f"F{r}", f"={OV}!U{o}", fmt=YEN)
        put(ws, f"G{r}", f"={OV}!P{o}", fmt=YEN)
        for col, v in zip("HIJ", c["y"]):
            put(ws, f"{col}{r}", v, fmt="#,##0", fill=FILL_IN)
        put(ws, f"K{r}", f"=D{r}*H{r}*12", fmt=YEN)
        put(ws, f"L{r}", f"=D{r}*I{r}*12", fmt=YEN)
        put(ws, f"M{r}", f"=D{r}*J{r}*12", fmt=YEN)
        put(ws, f"N{r}", f"=E{r}*H{r}*12", fmt=YEN)
        put(ws, f"O{r}", f"=F{r}*I{r}*12", fmt=YEN)
        put(ws, f"P{r}", f"=F{r}*J{r}*12", fmt=YEN)
        ws.row_dimensions[r].height = 30
        r += 1
    last = r - 1
    t = r
    put(ws, f"A{t}", "Amazon 合計", F_BOLD, fill=FILL_SUB)
    for col in "HIJKLMNOP":
        put(ws, f"{col}{t}", f"=SUM({col}5:{col}{last})", F_BOLD, fmt=YEN if col in "KLMNOP" else "#,##0", fill=FILL_SUB)
    for col in "BCDEFG":
        put(ws, f"{col}{t}", None, fill=FILL_SUB)
    u = t + 2
    put(ws, f"A{u}", "楽天・Yahoo!の上乗せ率（Amazon比）", F_BOLD)
    for col, v in zip("KLM", (0, 0.15, 0.20)):
        put(ws, f"{col}{u}", v, fmt=PCT, fill=FILL_IN)
    put(ws, f"A{u + 1}", "総年商（全モール）", F_BOLD, fill=FILL_KEY)
    put(ws, f"A{u + 2}", "総年利（営業利益・固定費前。他モールも同率と仮定）", F_BOLD, fill=FILL_KEY)
    for col, pc in zip("KLM", "NOP"):
        put(ws, f"{col}{u + 1}", f"={col}{t}*(1+{col}{u})", F_BOLD, fmt=YEN, fill=FILL_KEY)
        put(ws, f"{pc}{u + 2}", f"={pc}{t}*(1+{col}{u})", F_BOLD, fmt=YEN, fill=FILL_KEY)
    put(ws, f"A{u + 4}", "目標年商", F_BOLD)
    put(ws, f"K{u + 4}", 500000000, fmt=YEN, fill=FILL_IN)
    put(ws, f"A{u + 5}", "3年目の達成率（総年商÷目標）", F_BOLD)
    put(ws, f"K{u + 5}", f"=M{u + 1}/K{u + 4}", F_RED, fmt=PCT)
    put(ws, f"A{u + 6}", "3年目に必要な在庫・輸送中在庫の資金（月販×3か月×1個仕入総額）", F_BOLD)
    put(ws, f"K{u + 6}", f"=SUMPRODUCT(G5:G{last},J5:J{last})*3", F_BOLD, fmt=YEN)
    put(ws, f"A{u + 7}", "3年目の月商（Amazon）", F_BOLD)
    put(ws, f"K{u + 7}", f"=M{t}/12", fmt=YEN)
    notes = [
        "・年商5億円は1商品では届かない。ヒーロー4品（宅配ボックス・猫ケージ・大型猫タワー・猫トイレ収納）をそれぞれのサブカテゴリで1位（月販200〜400個）にし、主力3品（ゴルフ・A3・自転車）＋条件付き1品（ゴミストッカー）＋サポート3品と楽天・Yahoo!展開で3年目に到達させる計画。",
        "・各商品の月販目標は「1位ライン目安（02シート）」の範囲内に設定。Keepaで上位の実売を確認し、届かない商品は月販を下げてバリエーション（サイズ・色・2区画タイプ等）で補う。",
        "・年収5,000万円（役員報酬）の原資は総年利から固定費と法人税等を引いた残り。総年利が1億円に届かない場合は、ヒーローのバリエーション追加で売上を積み増す。",
        "・1年目は広告10%・レビュー獲得のための導入価格期間があるため利益が薄い（1個利益（広告10%）で試算）。",
    ]
    for i, tx in enumerate(notes):
        rr = u + 9 + i
        ws.merge_cells(f"A{rr}:P{rr}")
        put(ws, f"A{rr}", tx, F_SMALL, align=WRAP_TL, border=False)
        ws.row_dimensions[rr].height = 30
    ws.freeze_panes = "B5"
    return dict(total=t, uplift=u, first=5, last=last)


def build_summary(ws, rowmap, last_ov, rm):
    ws.title = "00_結論"
    ws.column_dimensions["A"].width = 44
    for col, w in zip("BCDEFGHIJK", (14, 12, 12, 12, 12, 12, 12, 12, 10, 18)):
        ws.column_dimensions[col].width = w
    put(ws, "A1", "大型OEM 商品化判断 v2（天瞳リサーチ表形式）｜年商5億・年収5,000万円に向けて", F_TITLE, border=False)
    put(ws, "A2", "作成日 2026-09-25／調査方法：WebSearchによるAmazon・楽天・Yahoo!・価格比較サイト・1688関連ページの調査（Amazon・1688へは直接接続不可）",
        F_NOTE, border=False)
    put(ws, "A4", "結論（要点）", F_SUB, border=False)
    points = [
        "1. 前回の「利益率15%以上」は危険でした。天瞳リサーチ表の利益率には広告費・返品・保管・出荷作業・売上消費税が入らず、実質より約20pt高く出ます（テンプレ15%≒実質赤字）。本表は「テンプレ30%以上かつ実質（広告5%）15%以上」をGOとしました。",
        "2. 68候補を同一条件で再計算し、詳細シート8品（うち条件付き1品）＋サポート3品の計11品に絞りました（集計は下表・数式で自動更新）。",
        "3. 1位を狙うHEROは4品：宅配ボックス（拡大市場・盗難/錠/錆の不満）、猫ケージ3段トイレ一体（脱走/砂漏れ/騒音の不満）、大型猫キャットタワー（揺れの不満）、猫トイレ収納（木部膨張/におい）。いずれもレビューの低評価が具体的で、仕様でつぶせます。",
        "4. 高利益ニッチはゴルフバッグ2本ラック（実質約28%）・A3プリンター台・自転車2台スタンド。ゴミストッカーは200サイズ梱包が条件。",
        "5. 物置・二段ベッド・ハーフラック・トランポリン等の重量・長尺品は、国内送料が公示額並みだと赤字。天瞳の大型配送単価が大幅に安ければ再評価します（前提条件の送料表に入力するだけで再計算）。",
        "6. 年商5億は単品では届きません。HERO4品を各サブカテゴリ1位（月販200〜400個）にし、主力・サポート＋楽天/Yahoo!展開で3年目に年商約5.2億円・営業利益（固定費前）約0.9億円とする計画です（03シート・初期前提）。",
        "7. 未確定事項：月販・ランキング（要Keepa）、1688の正式見積、梱包の実測値、天瞳の国内送料表。青字はすべて推定値です。",
    ]
    for i, t in enumerate(points):
        r = 5 + i
        ws.merge_cells(f"A{r}:K{r}")
        put(ws, f"A{r}", t, F_BASE, align=WRAP_TL, border=False)
        ws.row_dimensions[r].height = 44
    r0 = 13
    put(ws, f"A{r0}", "判定の集計（01シートから自動集計）", F_SUB, border=False)
    rng = f"{OV}!$V$5:$V${last_ov}"
    stats = [("候補数", f"=COUNTA({OV}!$A$5:$A${last_ov})"), ("GO（数値判定）", f"=COUNTIF({rng},\"GO\")"),
             ("COND（数値判定）", f"=COUNTIF({rng},\"COND\")"), ("NO（数値判定）", f"=COUNTIF({rng},\"NO\")")]
    for i, (label, f) in enumerate(stats):
        put(ws, f"A{r0 + 1 + i}", label)
        put(ws, f"B{r0 + 1 + i}", f, F_BOLD, fmt="#,##0")
    r1 = r0 + 6
    put(ws, f"A{r1}", "採用ラインナップ（数値は01シートから自動参照）", F_SUB, border=False)
    headers = ["商品", "役割", "最終判定", "定常売価", "テンプレ利益率", "実質利益率（広告5%）", "1個利益（広告5%）",
               "月販目標（3年目）", "月利目標（3年目）", "1位可能性", "詳細シート"]
    for j, h in enumerate(headers, start=1):
        put(ws, f"{get_column_letter(j)}{r1 + 1}", h, F_HEAD, fill=FILL_HEAD, align=WRAP_C)
    ws.row_dimensions[r1 + 1].height = 32
    for i, c in enumerate(D.FINALISTS):
        r = r1 + 2 + i
        o = rowmap[c["id"]]
        put(ws, f"A{r}", f"={OV}!B{o}", F_SMALL, align=LEFT_C)
        put(ws, f"B{r}", c["role"], F_SMALL, align=WRAP_C)
        put(ws, f"C{r}", f"={OV}!W{o}", F_SMALL, align=WRAP_C)
        put(ws, f"D{r}", f"={OV}!E{o}", fmt=YEN)
        put(ws, f"E{r}", f"={OV}!N{o}", fmt=PCT)
        put(ws, f"F{r}", f"={OV}!S{o}", F_BOLD, fmt=PCT)
        put(ws, f"G{r}", f"={OV}!U{o}", fmt=YEN)
        put(ws, f"H{r}", f"={OV}!AA{o}", fmt="#,##0")
        put(ws, f"I{r}", f"={OV}!AB{o}", F_BOLD, fmt=YEN)
        put(ws, f"J{r}", c["rank1"], align=WRAP_C)
        target = c["sheet"] or None
        cell = put(ws, f"K{r}", target or f"01シート {c['id']}", F_LINK)
        link_sheet(cell, f"'{target}'!A1" if target else f"{OV}!A{o}")
        ws.row_dimensions[r].height = 30
    r2 = r1 + 2 + len(D.FINALISTS) + 1
    put(ws, f"A{r2}", "年商5億の到達見込み（03シートから自動参照）", F_SUB, border=False)
    for j, h in enumerate(["", "1年目", "2年目", "3年目"], start=1):
        put(ws, f"{get_column_letter(j)}{r2 + 1}", h, F_HEAD, fill=FILL_HEAD, align=WRAP_C)
    u = rm["uplift"]
    put(ws, f"A{r2 + 2}", "総年商（Amazon＋楽天・Yahoo!）", F_BOLD)
    put(ws, f"A{r2 + 3}", "総年利（営業利益・固定費前）", F_BOLD)
    for col, src_s, src_p in (("B", "K", "N"), ("C", "L", "O"), ("D", "M", "P")):
        put(ws, f"{col}{r2 + 2}", f"={RM}!{src_s}{u + 1}", F_BOLD, fmt=YEN)
        put(ws, f"{col}{r2 + 3}", f"={RM}!{src_p}{u + 2}", F_BOLD, fmt=YEN)
    put(ws, f"A{r2 + 4}", "3年目の目標達成率（年商5億円比）", F_BOLD)
    put(ws, f"D{r2 + 4}", f"={RM}!K{u + 5}", F_RED, fmt=PCT)
    r3 = r2 + 6
    put(ws, f"A{r3}", "次にやること（優先順）", F_SUB, border=False)
    todo = [
        "① 天瞳の国内送料表を「前提条件」E34:E46に入力（全シート自動再計算。重量品の判定が変わる可能性あり）",
        "② Keepa／セラースプライトでHERO4品の上位10品の月販・価格推移を確認し、各シートの緑セル（ランキング）を埋める",
        "③ 1688で各3社に見積（各シートQ4・Q12のリンク）。原価（元）と梱包実寸を01シート・梱包明細に反映",
        "④ サンプル発注：宅配ボックス・猫ケージ・大型猫タワーの3品から（差別化仕様を指示書にして発注）",
        "⑤ 商標出願・JANコード・PL保険。宅配ボックスは防水・塩水噴霧、キャットタワーは耐荷重の試験データを取得",
    ]
    for i, t in enumerate(todo):
        r = r3 + 1 + i
        ws.merge_cells(f"A{r}:K{r}")
        put(ws, f"A{r}", t, F_BASE, align=WRAP_TL, border=False)
        ws.row_dimensions[r].height = 22


def build_sources(ws):
    ws.title = "出典"
    put(ws, "A1", "出典（2026-09-24〜25 WebSearchで確認）", F_TITLE, border=False)
    head_row(ws, 3, ["No", "区分", "内容", "URL"], [5, 14, 80, 70])
    for i, (cat, text, url) in enumerate(D.SOURCES, start=1):
        r = 3 + i
        put(ws, f"A{r}", i)
        put(ws, f"B{r}", cat, F_SMALL)
        put(ws, f"C{r}", text, F_SMALL, align=WRAP_TL)
        cell = put(ws, f"D{r}", url, F_URL, align=WRAP_TL)
        cell.hyperlink = url
    ws.freeze_panes = "A4"


def main(template, out):
    wb = load_workbook(template)
    tpl = wb["リサーチ表"]
    rows = D.candidates()
    models = {c["id"]: model(c) for c in rows}
    cands = {c["id"]: c for c in rows}

    ws_sum = wb.create_sheet("00_結論")
    ws_ov = wb.create_sheet("01_商品化判断_総合")
    ws_st = wb.create_sheet("02_1位獲得戦略")
    ws_rm = wb.create_sheet("03_年商5億ロードマップ")
    ws_as = wb.create_sheet("前提条件")
    ws_pk = wb.create_sheet("梱包明細")
    ws_src = wb.create_sheet("出典")

    build_assumptions(ws_as)
    rowmap, last_ov = build_overview(ws_ov, rows, models)
    order = sorted(rows, key=lambda c: rowmap[c["id"]])
    pk_first = build_parcels(ws_pk, order)
    build_strategy(ws_st)
    rm = build_roadmap(ws_rm, rowmap)
    build_summary(ws_sum, rowmap, last_ov, rm)
    build_sources(ws_src)

    product_sheets = []
    for spec in D.SHEETS:
        cand = cands[spec["cand"]]
        product_sheets.append(build_product_sheet(wb, tpl, spec, cand, rowmap[cand["id"]], pk_first[cand["id"]]))

    tpl.title = "テンプレート(原本)"
    wanted = [ws_sum, ws_ov, ws_st, ws_rm] + product_sheets + [ws_as, ws_pk, ws_src, tpl]
    wb._sheets = wanted
    wb.active = 0
    for ws in wb.worksheets:
        ws.sheet_view.tabSelected = ws is ws_sum
    wb.save(out)

    print("models (python mirror):")
    for c in order:
        m = models[c["id"]]
        print(f"  {c['id']} {m['judge']:4s} tmpl {m['tm']*100:5.1f}% real10 {m['r10']*100:5.1f}% "
              f"real5 {m['r5']*100:5.1f}% p5 {m['p5']:7.0f} {c['name'][:24]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
