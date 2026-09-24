# -*- coding: utf-8 -*-
"""Build the large-item OEM research workbook (openpyxl, formula-driven)."""
import sys
from urllib.parse import quote

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from research_data import MAIN, OTHERS, REVIEWS, SOURCES

OUT = sys.argv[1] if len(sys.argv) > 1 else "research.xlsx"

FONT = "游ゴシック"
F_BASE = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_TITLE = Font(name=FONT, size=14, bold=True)
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_INPUT = Font(name=FONT, size=10, color="0000FF")
F_LINK_SHEET = Font(name=FONT, size=10, color="008000")
F_URL = Font(name=FONT, size=10, color="0563C1", underline="single")
F_NOTE = Font(name=FONT, size=9, color="595959")
F_RED = Font(name=FONT, size=10, bold=True, color="C00000")

FILL_HEAD = PatternFill("solid", fgColor="1F4E78")
FILL_GROUP = PatternFill("solid", fgColor="D9E1F2")
FILL_INPUT = PatternFill("solid", fgColor="FFF2CC")
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
FILL_PASS = PatternFill("solid", fgColor="E2EFDA")
FILL_SECTION = PatternFill("solid", fgColor="F2F2F2")

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

YEN = '"¥"#,##0;[Red]"-¥"#,##0;"-"'
PCT = '0.0%;[Red]-0.0%;"-"'
CNY = '#,##0" 元"'
INT = '#,##0'
M3 = '0.000'
KG = '0.0'

ASSUME = "'前提条件'"
A = {  # assumption cells
    "fx": f"{ASSUME}!$B$4", "cn": f"{ASSUME}!$B$5", "fr": f"{ASSUME}!$B$6",
    "shipk": f"{ASSUME}!$B$7", "ad": f"{ASSUME}!$B$8", "ret": f"{ASSUME}!$B$9",
    "stor": f"{ASSUME}!$B$10", "mon": f"{ASSUME}!$B$11", "hand": f"{ASSUME}!$B$12",
    "tax": f"{ASSUME}!$B$13", "tgt": f"{ASSUME}!$B$14", "tgtm": f"{ASSUME}!$B$15",
    "cond": f"{ASSUME}!$B$16",
}
FEE_CAT = f"{ASSUME}!$A$20:$A$28"
FEE_RATE = f"{ASSUME}!$B$20:$B$28"
SZ_NAME = f"{ASSUME}!$B$34:$B$46"
SZ_LOW = f"{ASSUME}!$C$34:$C$46"
SZ_RATE = f"{ASSUME}!$E$34:$E$46"
WT_LOW = f"{ASSUME}!$H$34:$H$41"
WT_IDX = f"{ASSUME}!$J$34:$J$41"

RS = "リサーチ表(15%以上)"
RSQ = f"'{RS}'"


def link_1688(kw):
    return "https://s.1688.com/selloffer/offer_search.htm?charset=utf8&keywords=" + quote(kw)


def link_amazon(kw):
    return "https://www.amazon.co.jp/s?k=" + quote(kw)


def put(ws, ref, value, font=F_BASE, fmt=None, fill=None, align=None, border=True):
    c = ws[ref]
    c.value = value
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = BORDER
    return c


def put_url(ws, ref, url, text=None):
    c = put(ws, ref, text or url, font=F_URL, align=WRAP)
    if url and url.startswith("http"):
        c.hyperlink = url
    return c


# ---------------------------------------------------------------- 前提条件
def build_assumptions(wb):
    ws = wb.create_sheet("前提条件")
    ws["A1"] = "前提条件（青字の値を書き換えると全シートが再計算されます）"
    ws["A1"].font = F_TITLE
    ws["A2"] = ("※ 国際送料・国内送料・保管料・出荷作業料は、天瞳の送料資料（今回のチャットでは本環境から参照できず）の数値に差し替えてください。"
                "現在の値は公開相場からの仮置きです。")
    ws["A2"].font = F_RED
    heads = ["項目", "値", "単位", "根拠・出典", "備考"]
    for i, h in enumerate(heads):
        put(ws, f"{get_column_letter(i + 1)}3", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
    params = [
        ("為替（円/元）", 24.0, "円/元", "2026-09-24 実勢 約23.65円（三菱UFJリサーチ&コンサルティング等）", "送金・両替コスト分の安全マージンを上乗せ", '0.00'),
        ("中国側諸費用率", 0.08, "仕入額比", "工場→中国倉庫の国内運賃・検品・代行手数料の想定", "天瞳の手数料体系に合わせて修正", PCT),
        ("国際送料単価（船便混載・日本倉庫着・通関込）", 12000, "円/m³", "公開相場：1CBM 7,800円（クレスト国際貿易）〜1,900元/m³≈40,850円（海源物流）", "関税・輸入消費税は別計算。天瞳資料の立米単価に差し替え", YEN),
        ("国内送料 補正係数", 1.0, "倍", "送料表（下）全体を一括で増減", "例：天瞳料金が送料表より2割安い→0.8", '0.00'),
        ("広告費率", 0.10, "税抜売上比", "前回ChatGPT案と同じ10%（立上げ期を含む平均）", "安定期は5〜7%に下がる想定", PCT),
        ("返品・破損引当率", 0.04, "税抜売上比", "前回案と同じ4%", "大型品は返送料が高いため据え置き", PCT),
        ("保管料単価", 3000, "円/m³/月", "国内3PLの一般的な水準（仮置き）", "天瞳倉庫の保管料に差し替え", YEN),
        ("平均在庫月数", 1.5, "か月", "船便リードタイムを踏まえた平均在庫", "", '0.0'),
        ("出荷作業料", 300, "円/個", "大型品のピッキング・梱包の仮置き", "天瞳の発送システム料金に差し替え", YEN),
        ("消費税率", 0.10, "", "売上・手数料の税抜換算に使用（輸入消費税は仕入税額控除で回収する前提）", "", PCT),
        ("目標利益率（判定ライン）", 0.15, "税抜売上比", "ユーザー指定：15%以上", "広告・返品・保管・出荷作業を控除した後の利益率", PCT),
        ("目標月利", 1000000, "円/月", "ユーザー指定：月利100万円以上", "", YEN),
        ("条件付き判定ライン", 0.10, "税抜売上比", "10〜15%は送料・原価しだいで15%に届く『条件付き』", "", PCT),
    ]
    for i, (name, val, unit, src, note, fmt) in enumerate(params):
        r = 4 + i
        put(ws, f"A{r}", name, F_BOLD)
        put(ws, f"B{r}", val, F_INPUT, fmt=fmt, fill=FILL_KEY if r in (6, 7, 10, 12) else FILL_INPUT)
        put(ws, f"C{r}", unit)
        put(ws, f"D{r}", src, align=WRAP)
        put(ws, f"E{r}", note, align=WRAP)

    ws["A18"] = "Amazon販売手数料率（2026年4月1日改定後・税抜表示。別途消費税）"
    ws["A18"].font = F_BOLD
    for i, h in enumerate(["カテゴリ", "手数料率", "備考"]):
        put(ws, f"{get_column_letter(i + 1)}19", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
    fees = [
        ("ホーム&キッチン", 0.154, "15%＋0.4pt（売上750円超）"),
        ("ペット用品", 0.154, "15%＋0.4pt"),
        ("DIY・工具・ガーデン", 0.154, "15%＋0.4pt"),
        ("文房具・オフィス用品", 0.154, "15%＋0.4pt"),
        ("産業・研究開発用品", 0.154, "15%＋0.4pt"),
        ("スポーツ&アウトドア", 0.104, "10%＋0.4pt"),
        ("車&バイク", 0.104, "10%＋0.4pt"),
        ("ビューティー（参考）", 0.104, "要確認"),
        ("家具（参考）", 0.154, "要確認"),
    ]
    for i, (cat, rate, note) in enumerate(fees):
        r = 20 + i
        put(ws, f"A{r}", cat)
        put(ws, f"B{r}", rate, F_INPUT, fmt=PCT, fill=FILL_INPUT)
        put(ws, f"C{r}", note)
    ws["D20"] = "出典：https://stockcrew.co.jp/insights/amazon-fee-2026 ／ 販売手数料は税抜表示：https://brandbuppan.jp/amazon-selling-fee-tax/"
    ws["D20"].font = F_NOTE

    ws["A31"] = "国内送料表（自社発送＝天瞳倉庫からの出荷を想定・税抜）"
    ws["A31"].font = F_BOLD
    ws["A32"] = ("仮置き値：公示運賃（佐川 飛脚ラージ 関東→関東 170サイズ2,600円〜260サイズ6,420円、ヤマト宅急便は200サイズ・30kgまで）から"
                 "契約割引を見込んだ想定。天瞳の送料資料の金額に置き換えてください。区分は3辺合計と重量の大きい方で決まります。")
    ws["A32"].font = F_NOTE
    for col, h in zip("ABCDEF", ["区分No", "サイズ区分", "3辺合計の下限(cm)", "3辺合計の上限(cm)", "送料(円・税抜)", "想定キャリア・備考"]):
        put(ws, f"{col}33", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
    sizes = [
        ("60サイズ", 0, 60, 650, "宅配便"), ("80サイズ", 60.01, 80, 750, "宅配便"), ("100サイズ", 80.01, 100, 900, "宅配便"),
        ("120サイズ", 100.01, 120, 1050, "宅配便"), ("140サイズ", 120.01, 140, 1250, "宅配便"), ("160サイズ", 140.01, 160, 1450, "宅配便（佐川は30kgまで）"),
        ("170サイズ", 160.01, 170, 1900, "佐川 飛脚ラージ（50kgまで）"), ("180サイズ", 170.01, 180, 2200, "飛脚ラージ／ヤマト180"),
        ("200サイズ", 180.01, 200, 2700, "飛脚ラージ／ヤマト200"), ("220サイズ", 200.01, 220, 3300, "飛脚ラージ"),
        ("240サイズ", 220.01, 240, 3900, "飛脚ラージ"), ("260サイズ", 240.01, 260, 4600, "飛脚ラージ（上限）"),
        ("家財便・チャーター", 260.01, 9999, 7000, "260超・50kg超。天瞳のチャーター便料金に差し替え"),
    ]
    for i, (name, low, high, rate, note) in enumerate(sizes):
        r = 34 + i
        put(ws, f"A{r}", i + 1, align=CENTER)
        put(ws, f"B{r}", name)
        put(ws, f"C{r}", low, fmt='0.00')
        put(ws, f"D{r}", high, fmt=INT)
        put(ws, f"E{r}", rate, F_INPUT, fmt=YEN, fill=FILL_KEY)
        put(ws, f"F{r}", note)
    for col, h in zip("HIJK", ["重量の下限(kg)", "重量の上限(kg)", "最低区分No", "備考"]):
        put(ws, f"{col}33", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
    weights = [(0, 2, 1, ""), (2.01, 5, 2, ""), (5.01, 10, 3, ""), (10.01, 15, 4, ""), (15.01, 20, 5, ""),
               (20.01, 30, 6, "160サイズ（佐川30kgまで）"), (30.01, 50, 7, "飛脚ラージ170以上"), (50.01, 9999, 13, "家財便・チャーター")]
    for i, (low, high, idx, note) in enumerate(weights):
        r = 34 + i
        put(ws, f"H{r}", low, fmt='0.00')
        put(ws, f"I{r}", high, fmt=INT)
        put(ws, f"J{r}", idx, align=CENTER)
        put(ws, f"K{r}", note)
    widths = {"A": 34, "B": 14, "C": 16, "D": 58, "E": 44, "F": 34, "H": 14, "I": 14, "J": 12, "K": 26}
    for k, v in widths.items():
        ws.column_dimensions[k].width = v
    ws.freeze_panes = "A4"
    return ws


# ---------------------------------------------------------------- shared calc formulas
def calc_formulas(r, c):
    """Return formula strings for one row. `c` maps logical names to column letters."""
    f = {}
    f["fee"] = f"=IFERROR(INDEX({FEE_RATE},MATCH({c['cat']}{r},{FEE_CAT},0)),{ASSUME}!$B$20)"
    f["sum"] = f"={c['L']}{r}+{c['W']}{r}+{c['H']}{r}"
    f["m3"] = f"={c['L']}{r}*{c['W']}{r}*{c['H']}{r}/1000000"
    f["idx"] = (f"=MAX(MATCH({c['sum']}{r},{SZ_LOW},1),"
                f"INDEX({WT_IDX},MATCH({c['kg']}{r},{WT_LOW},1)))")
    f["size"] = f"=INDEX({SZ_NAME},{c['idx']}{r})"
    f["dom"] = f"=INDEX({SZ_RATE},{c['idx']}{r})*{A['shipk']}"
    return f


# ---------------------------------------------------------------- research sheet
RCOLS = [
    # key, header, width, kind (input/text/formula/url), fmt
    ("rank", "優先順位", 7, "input", INT),
    ("name", "商品名（OEM企画）", 26, "text", None),
    ("concept", "コンセプト（狙い）", 34, "text", None),
    ("cat", "Amazonカテゴリ", 14, "input", None),
    ("fee", "販売手数料率", 9, "formula", PCT),
    ("comp", "主要競合（商品・スペック）", 38, "text", None),
    ("comp_url", "競合URL", 24, "url", None),
    ("comp_price", "競合価格・根拠", 28, "text", None),
    ("amz", "Amazon検索リンク", 16, "url", None),
    ("price", "想定販売価格（税込・円）", 12, "input", YEN),
    ("kw_cn", "1688検索キーワード（中国語）", 22, "text", None),
    ("l1688", "1688検索リンク", 16, "url", None),
    ("cny", "想定仕入単価（元）※推定", 11, "input", CNY),
    ("va", "付加価値の追加コスト（円）", 11, "input", YEN),
    ("L", "梱包 縦(cm)", 8, "input", INT),
    ("W", "梱包 横(cm)", 8, "input", INT),
    ("H", "梱包 高さ(cm)", 8, "input", INT),
    ("kg", "梱包重量(kg)", 8, "input", KG),
    ("sum", "3辺合計(cm)", 8, "formula", INT),
    ("m3", "容積(m³)", 8, "formula", M3),
    ("idx", "配送区分No", 7, "formula", INT),
    ("size", "国内配送サイズ", 12, "formula", None),
    ("dom", "国内送料（円）", 10, "formula", YEN),
    ("fba", "FBA区分（参考）", 9, "formula", None),
    ("duty", "関税率", 7, "input", PCT),
    ("goods", "仕入原価（円）", 10, "formula", YEN),
    ("intl", "国際送料（円）", 10, "formula", YEN),
    ("dutyamt", "関税（円）", 9, "formula", YEN),
    ("landed", "着地原価（円）", 11, "formula", YEN),
    ("rev", "税抜売上（円）", 11, "formula", YEN),
    ("feeamt", "販売手数料（円）", 10, "formula", YEN),
    ("adamt", "広告費（円）", 10, "formula", YEN),
    ("retamt", "返品・破損引当（円）", 10, "formula", YEN),
    ("storamt", "保管料（円）", 9, "formula", YEN),
    ("handamt", "出荷作業料（円）", 9, "formula", YEN),
    ("profit", "利益（円/個）", 11, "formula", YEN),
    ("margin", "利益率（税抜売上比）", 10, "formula", PCT),
    ("premargin", "広告前利益率", 10, "formula", PCT),
    ("roi", "ROI（利益÷着地原価）", 10, "formula", PCT),
    ("vol", "想定月販（個）※推定", 9, "input", INT),
    ("msales", "月商（税込・円）", 12, "formula", YEN),
    ("mprofit", "月利（円）", 12, "formula", YEN),
    ("need", "月利100万に必要な月販（個）", 11, "formula", INT),
    ("maxdom", "15%達成の国内送料上限（円）", 12, "formula", YEN),
    ("maxcny", "15%達成の仕入単価上限（元）", 12, "formula", CNY),
    ("judge", "判定", 11, "formula", None),
    ("va_text", "付加価値（差別化）案", 48, "text", None),
    ("pros", "高評価ポイント（競合レビュー）", 44, "text", None),
    ("cons", "改善要望（優先度付き）", 52, "text", None),
    ("top_fix", "最優先の改善", 30, "text", None),
    ("conf", "データ確度", 26, "text", None),
    ("next_check", "次の確認事項", 40, "text", None),
]
RGROUPS = [
    ("rank", "amz", "基本情報・競合（Amazon等）"),
    ("price", "price", "売価"),
    ("kw_cn", "duty", "仕入（1688）・梱包・物流"),
    ("goods", "landed", "着地原価（1個）"),
    ("rev", "roi", "損益（1個あたり・税抜）"),
    ("vol", "need", "月間シミュレーション"),
    ("maxdom", "judge", "感応度・判定"),
    ("va_text", "next_check", "差別化・レビュー分析"),
]


def col_map(cols):
    return {key: get_column_letter(i + 1) for i, (key, *_rest) in enumerate(cols)}


def row_formulas(r, c):
    f = calc_formulas(r, c)
    f["fba"] = (f'=IF(AND({c["sum"]}{r}<=200,{c["kg"]}{r}<=40),"大型以内",'
                f'IF(AND({c["sum"]}{r}<=260,{c["kg"]}{r}<=50),"特大型","FBA不可"))')
    f["goods"] = f"={c['cny']}{r}*{A['fx']}*(1+{A['cn']})"
    f["intl"] = f"={c['m3']}{r}*{A['fr']}"
    f["dutyamt"] = f"=({c['goods']}{r}+{c['intl']}{r})*{c['duty']}{r}"
    f["landed"] = f"={c['goods']}{r}+{c['va']}{r}+{c['intl']}{r}+{c['dutyamt']}{r}"
    f["rev"] = f"={c['price']}{r}/(1+{A['tax']})"
    f["feeamt"] = f"={c['price']}{r}*{c['fee']}{r}"
    f["adamt"] = f"={c['rev']}{r}*{A['ad']}"
    f["retamt"] = f"={c['rev']}{r}*{A['ret']}"
    f["storamt"] = f"={c['m3']}{r}*{A['stor']}*{A['mon']}"
    f["handamt"] = f"={A['hand']}"
    f["profit"] = (f"={c['rev']}{r}-{c['feeamt']}{r}-{c['dom']}{r}-{c['adamt']}{r}-{c['retamt']}{r}"
                   f"-{c['storamt']}{r}-{c['handamt']}{r}-{c['landed']}{r}")
    f["margin"] = f"=IF({c['rev']}{r}>0,{c['profit']}{r}/{c['rev']}{r},0)"
    f["premargin"] = f"=IF({c['rev']}{r}>0,({c['profit']}{r}+{c['adamt']}{r})/{c['rev']}{r},0)"
    f["roi"] = f"=IF({c['landed']}{r}>0,{c['profit']}{r}/{c['landed']}{r},0)"
    f["msales"] = f"={c['price']}{r}*{c['vol']}{r}"
    f["mprofit"] = f"={c['profit']}{r}*{c['vol']}{r}"
    f["need"] = f'=IF({c["profit"]}{r}>0,ROUNDUP({A["tgtm"]}/{c["profit"]}{r},0),"赤字")'
    f["maxdom"] = f"={c['dom']}{r}+({c['profit']}{r}-{A['tgt']}*{c['rev']}{r})"
    f["maxcny"] = (f"={c['cny']}{r}+({c['profit']}{r}-{A['tgt']}*{c['rev']}{r})"
                   f"/({A['fx']}*(1+{A['cn']})*(1+{c['duty']}{r}))")
    f["judge"] = (f'=IF({c["margin"]}{r}>={A["tgt"]},"◎ 15%以上",'
                  f'IF({c["margin"]}{r}>={A["cond"]},"△ 条件付き","× 除外"))')
    return f


def write_headers(ws, cols, groups, head_row, group_row):
    c = col_map(cols)
    for key_from, key_to, label in groups:
        a, b = c[key_from], c[key_to]
        ws.merge_cells(f"{a}{group_row}:{b}{group_row}")
        put(ws, f"{a}{group_row}", label, F_BOLD, fill=FILL_GROUP, align=CENTER)
    for i, (key, head, width, kind, fmt) in enumerate(cols):
        col = get_column_letter(i + 1)
        put(ws, f"{col}{head_row}", head, F_HEAD, fill=FILL_HEAD, align=CENTER)
        ws.column_dimensions[col].width = width
    ws.row_dimensions[head_row].height = 42


def build_research(wb):
    ws = wb.create_sheet(RS)
    ws["A1"] = "大型OEM リサーチ表（神田式）― 利益率15%以上に厳選　作成日：2026-09-24"
    ws["A1"].font = F_TITLE
    ws["A2"] = ("青字・黄色セル＝入力（推定値を含む）／黒字＝計算式／緑字＝他シート参照。利益率＝利益÷税抜売上。利益は広告費・返品引当・保管料・出荷作業料まで控除後（固定費は別）。"
                "データ確度 A=商品ページで確認／B=検索結果経由で確認／C=推定（要実測）。1688単価・梱包寸法・月販はC（推定）です。")
    ws["A2"].font = F_NOTE
    cols = RCOLS
    c = col_map(cols)
    write_headers(ws, cols, RGROUPS, head_row=4, group_row=3)
    for i, p in enumerate(sorted(MAIN, key=lambda x: x["rank"])):
        r = 5 + i
        f = row_formulas(r, c)
        vals = dict(p)
        vals["amz"] = link_amazon(p["kw_jp"])
        vals["l1688"] = link_1688(p["kw_cn"])
        for key, head, width, kind, fmt in cols:
            ref = f"{c[key]}{r}"
            if kind == "formula":
                put(ws, ref, f[key], fmt=fmt, align=WRAP if key in ("size", "judge", "fba") else None)
            elif kind == "url":
                label = {"amz": "Amazonで検索", "l1688": "1688で検索"}.get(key)
                put_url(ws, ref, vals[key], label)
            elif kind == "input":
                put(ws, ref, vals[key], F_INPUT, fmt=fmt, fill=FILL_INPUT, align=WRAP if key == "cat" else None)
            else:
                put(ws, ref, vals[key], align=WRAP, font=F_BOLD if key == "name" else F_BASE)
        ws.row_dimensions[r].height = 150
    last = 4 + len(MAIN)
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(cols))}{last}"
    note_r = last + 2
    ws[f"A{note_r}"] = "注記"
    ws[f"A{note_r}"].font = F_BOLD
    notes = [
        "・Amazon.co.jp と 1688.com の商品ページは、本作業環境のネットワーク制限で直接開けませんでした。競合の価格・仕様・レビューは検索エンジン経由で確認できた範囲（出典URLは『出典』『レビュー分析』シート）です。",
        "・1688の仕入単価は市場相場からの推定です。『1688検索リンク』から実際の出品を開き、単価・MOQ・梱包寸法・重量で上書きしてください（黄色セル）。",
        "・送料は天瞳の送料資料が未共有のため仮置きです。『前提条件』シートの送料表・立米単価を差し替えると、利益・判定・必要月販がすべて再計算されます。",
        "・『15%達成の国内送料上限』『15%達成の仕入単価上限』は、その金額以下なら利益率15%を満たすという損益分岐の目安です。",
    ]
    for j, t in enumerate(notes):
        ws[f"A{note_r + 1 + j}"] = t
        ws[f"A{note_r + 1 + j}"].font = F_NOTE
    return ws, c


# ---------------------------------------------------------------- screening sheet (all 40)
SCOLS = [
    ("srank", "順位（利益率順）", 7, "static", INT),
    ("no", "元リストNo", 7, "static", INT),
    ("group", "区分", 8, "static", None),
    ("name", "商品名", 24, "text", None),
    ("cat", "Amazonカテゴリ", 14, "input", None),
    ("fee", "販売手数料率", 9, "formula", PCT),
    ("price", "想定販売価格（税込・円）", 12, "input", YEN),
    ("basis", "価格の根拠（競合価格）", 36, "text", None),
    ("prev", "前回案の目標売価（参考）", 11, "static", YEN),
    ("cny", "想定仕入単価（元）※推定", 11, "input", CNY),
    ("va", "付加価値コスト（円）", 10, "input", YEN),
    ("L", "縦(cm)", 7, "input", INT),
    ("W", "横(cm)", 7, "input", INT),
    ("H", "高さ(cm)", 7, "input", INT),
    ("kg", "重量(kg)", 7, "input", KG),
    ("sum", "3辺合計", 7, "formula", INT),
    ("m3", "容積(m³)", 8, "formula", M3),
    ("idx", "区分No", 6, "formula", INT),
    ("size", "国内配送サイズ", 11, "formula", None),
    ("dom", "国内送料（円）", 10, "formula", YEN),
    ("duty", "関税率", 7, "input", PCT),
    ("landed", "着地原価（円）", 11, "formula", YEN),
    ("rev", "税抜売上（円）", 11, "formula", YEN),
    ("profit", "利益（円/個）", 11, "formula", YEN),
    ("margin", "利益率（税抜売上比）", 10, "formula", PCT),
    ("premargin", "広告前利益率", 10, "formula", PCT),
    ("vol", "想定月販（個）※推定", 9, "input", INT),
    ("mprofit", "月利（円）", 12, "formula", YEN),
    ("need", "月利100万に必要な月販", 11, "formula", INT),
    ("maxdom", "15%達成の国内送料上限（円）", 12, "formula", YEN),
    ("maxcny", "15%達成の仕入単価上限（元）", 12, "formula", CNY),
    ("judge", "判定", 11, "formula", None),
    ("comment", "判定理由・コメント", 60, "text", None),
    ("url", "競合・参考URL", 24, "url", None),
    ("l1688", "1688検索リンク", 14, "url", None),
    ("amz", "Amazon検索リンク", 14, "url", None),
]
SGROUPS = [
    ("srank", "prev", "候補・売価"),
    ("cny", "duty", "仕入・梱包・物流"),
    ("landed", "premargin", "損益（1個・税抜）"),
    ("vol", "need", "月間"),
    ("maxdom", "judge", "感応度・判定"),
    ("comment", "amz", "コメント・リンク"),
]


def screening_formulas(r, c):
    f = calc_formulas(r, c)
    goods = f"{c['cny']}{r}*{A['fx']}*(1+{A['cn']})"
    intl = f"{c['m3']}{r}*{A['fr']}"
    f["landed"] = f"={goods}+{c['va']}{r}+{intl}+({goods}+{intl})*{c['duty']}{r}"
    f["rev"] = f"={c['price']}{r}/(1+{A['tax']})"
    f["profit"] = (f"={c['rev']}{r}*(1-{A['ad']}-{A['ret']})-{c['price']}{r}*{c['fee']}{r}-{c['dom']}{r}"
                   f"-{c['m3']}{r}*{A['stor']}*{A['mon']}-{A['hand']}-{c['landed']}{r}")
    f["margin"] = f"=IF({c['rev']}{r}>0,{c['profit']}{r}/{c['rev']}{r},0)"
    f["premargin"] = f"=IF({c['rev']}{r}>0,({c['profit']}{r}+{c['rev']}{r}*{A['ad']})/{c['rev']}{r},0)"
    f["mprofit"] = f"={c['profit']}{r}*{c['vol']}{r}"
    f["need"] = f'=IF({c["profit"]}{r}>0,ROUNDUP({A["tgtm"]}/{c["profit"]}{r},0),"赤字")'
    f["maxdom"] = f"={c['dom']}{r}+({c['profit']}{r}-{A['tgt']}*{c['rev']}{r})"
    f["maxcny"] = (f"={c['cny']}{r}+({c['profit']}{r}-{A['tgt']}*{c['rev']}{r})"
                   f"/({A['fx']}*(1+{A['cn']})*(1+{c['duty']}{r}))")
    f["judge"] = (f'=IF({c["margin"]}{r}>={A["tgt"]},"◎ 15%以上",'
                  f'IF({c["margin"]}{r}>={A["cond"]},"△ 条件付き","× 除外"))')
    return f


def py_margin(price, fee, cny, va, L, W, H, kg, duty):
    """Python mirror of the sheet formulas (default assumptions) for ordering rows."""
    fx, cn, fr, ad, ret, stor, mon, hand = 24.0, 0.08, 12000, 0.10, 0.04, 3000, 1.5, 300
    sizes = [(0, 650), (60.01, 750), (80.01, 900), (100.01, 1050), (120.01, 1250), (140.01, 1450), (160.01, 1900),
             (170.01, 2200), (180.01, 2700), (200.01, 3300), (220.01, 3900), (240.01, 4600), (260.01, 7000)]
    weights = [(0, 1), (2.01, 2), (5.01, 3), (10.01, 4), (15.01, 5), (20.01, 6), (30.01, 7), (50.01, 13)]
    s = L + W + H
    si = max(i + 1 for i, (low, _) in enumerate(sizes) if s >= low)
    wi = [idx for low, idx in weights if kg >= low][-1]
    dom = sizes[max(si, wi) - 1][1]
    m3 = L * W * H / 1e6
    goods = cny * fx * (1 + cn)
    intl = m3 * fr
    landed = goods + va + intl + (goods + intl) * duty
    rev = price / 1.1
    profit = rev * (1 - ad - ret) - price * fee - dom - m3 * stor * mon - hand - landed
    return profit / rev, profit


# target prices from the previous (ChatGPT) plan, top 10 only — shown for comparison
PREV_PRICE = {1: 14980, 2: 15980, 3: 19800, 4: 19800, 5: 17980, 6: 21980, 7: 13980, 8: 16980, 9: 14980, 10: 17980}

FEES = {"ホーム&キッチン": .154, "ペット用品": .154, "DIY・工具・ガーデン": .154, "文房具・オフィス用品": .154,
        "産業・研究開発用品": .154, "スポーツ&アウトドア": .104, "車&バイク": .104}


def build_screening(wb, rc):
    ws = wb.create_sheet("全40候補スクリーニング")
    ws["A1"] = "全40候補スクリーニング（前回リストの40商品を同一条件で試算）"
    ws["A1"].font = F_TITLE
    ws["A2"] = ("緑字＝『リサーチ表(15%以上)』の入力を参照（厳選8商品はリサーチ表側で編集）。判定：◎＝利益率15%以上／△＝10〜15%（送料・原価しだいで到達）／×＝10%未満。"
                "並び順は既定の前提条件での利益率順です。")
    ws["A2"].font = F_NOTE
    cols = SCOLS
    c = col_map(cols)
    write_headers(ws, cols, SGROUPS, head_row=4, group_row=3)

    rows = []
    main_by_no = {p["no"]: p for p in MAIN}
    main_row = {p["no"]: 5 + i for i, p in enumerate(sorted(MAIN, key=lambda x: x["rank"]))}
    for p in MAIN:
        m, prof = py_margin(p["price"], FEES[p["cat"]], p["cny"], p["va"], p["L"], p["W"], p["H"], p["kg"], p["duty"])
        rows.append(("main", p["no"], m, p))
    for o in OTHERS:
        (no, group, name, cat, price, basis, kw_cn, kw_jp, cny, va, L, W, H, kg, duty, vol, url, comment) = o
        m, prof = py_margin(price, FEES[cat], cny, va, L, W, H, kg, duty)
        rows.append(("other", no, m, o))
    rows.sort(key=lambda x: -x[2])

    for i, (kind, no, m, d) in enumerate(rows):
        r = 5 + i
        f = screening_formulas(r, c)
        put(ws, f"{c['srank']}{r}", i + 1, align=CENTER)
        put(ws, f"{c['no']}{r}", no, align=CENTER)
        put(ws, f"{c['prev']}{r}", PREV_PRICE.get(no), fmt=YEN)
        if kind == "main":
            p = d
            src = main_row[no]
            put(ws, f"{c['group']}{r}", "上位10" if no <= 10 else "追加30", align=CENTER)
            link = lambda key: f"={RSQ}!{rc[key]}{src}"
            put(ws, f"{c['name']}{r}", link("name"), F_LINK_SHEET, align=WRAP)
            put(ws, f"{c['cat']}{r}", link("cat"), F_LINK_SHEET, align=WRAP)
            put(ws, f"{c['price']}{r}", link("price"), F_LINK_SHEET, fmt=YEN)
            put(ws, f"{c['basis']}{r}", link("comp_price"), F_LINK_SHEET, align=WRAP)
            for key, fmt in (("cny", CNY), ("va", YEN), ("L", INT), ("W", INT), ("H", INT), ("kg", KG), ("duty", PCT), ("vol", INT)):
                put(ws, f"{c[key]}{r}", link(key), F_LINK_SHEET, fmt=fmt)
            put(ws, f"{c['comment']}{r}", f"リサーチ表に掲載（優先順位{p['rank']}）。{p['concept']}", align=WRAP)
            put_url(ws, f"{c['url']}{r}", p["comp_url"])
            put_url(ws, f"{c['l1688']}{r}", link_1688(p["kw_cn"]), "1688で検索")
            put_url(ws, f"{c['amz']}{r}", link_amazon(p["kw_jp"]), "Amazonで検索")
        else:
            (no, group, name, cat, price, basis, kw_cn, kw_jp, cny, va, L, W, H, kg, duty, vol, url, comment) = d
            put(ws, f"{c['group']}{r}", group, align=CENTER)
            put(ws, f"{c['name']}{r}", name, F_BOLD, align=WRAP)
            put(ws, f"{c['cat']}{r}", cat, F_INPUT, fill=FILL_INPUT, align=WRAP)
            put(ws, f"{c['price']}{r}", price, F_INPUT, fmt=YEN, fill=FILL_INPUT)
            put(ws, f"{c['basis']}{r}", basis, align=WRAP)
            for key, val, fmt in (("cny", cny, CNY), ("va", va, YEN), ("L", L, INT), ("W", W, INT), ("H", H, INT),
                                  ("kg", kg, KG), ("duty", duty, PCT), ("vol", vol, INT)):
                put(ws, f"{c[key]}{r}", val, F_INPUT, fmt=fmt, fill=FILL_INPUT)
            put(ws, f"{c['comment']}{r}", comment, align=WRAP)
            put_url(ws, f"{c['url']}{r}", url)
            put_url(ws, f"{c['l1688']}{r}", link_1688(kw_cn), "1688で検索")
            put_url(ws, f"{c['amz']}{r}", link_amazon(kw_jp), "Amazonで検索")
        for key in ("fee", "sum", "m3", "idx", "size", "dom", "landed", "rev", "profit", "margin", "premargin",
                    "mprofit", "need", "maxdom", "maxcny", "judge"):
            fmt = dict((k, fm) for k, _h, _w, _kind, fm in cols)[key]
            put(ws, f"{c[key]}{r}", f[key], fmt=fmt, align=WRAP if key in ("size", "judge") else None)
        ws.row_dimensions[r].height = 60
    last = 4 + len(rows)
    ws.freeze_panes = "E5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(cols))}{last}"
    return ws, c, rows


# ---------------------------------------------------------------- reviews
def build_reviews(wb):
    ws = wb.create_sheet("レビュー分析")
    ws["A1"] = "関連商品の口コミ分析（高評価・改善要望・優先度）"
    ws["A1"].font = F_TITLE
    ws["A2"] = ("Amazon・1688の商品ページは本環境から直接閲覧できないため、検索結果の要約・比較記事・販売ページの表記から抽出しました（本文未閲覧を含む）。"
                "優先度：高＝製品仕様で必ず解決／中＝できれば仕様で解決／低＝商品ページ・説明書で対応。『要確認』はAmazonレビューの精読が必要な一般傾向です。")
    ws["A2"].font = F_NOTE
    heads = [("商品", 26), ("区分", 9), ("口コミの要旨", 56), ("優先度", 7), ("当社の対応（付加価値への反映）", 40), ("出典URL（検索結果）", 40), ("確認方法", 18)]
    for i, (h, w) in enumerate(heads):
        col = get_column_letter(i + 1)
        put(ws, f"{col}4", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
        ws.column_dimensions[col].width = w
    for i, (prod, kind, content, pri, resp, src) in enumerate(REVIEWS):
        r = 5 + i
        put(ws, f"A{r}", prod, F_BOLD, align=WRAP)
        put(ws, f"B{r}", kind, align=CENTER, fill=FILL_PASS if kind == "高評価" else None)
        put(ws, f"C{r}", content, align=WRAP)
        pri_font = F_RED if pri == "高" else F_BASE
        put(ws, f"D{r}", pri, pri_font, align=CENTER)
        put(ws, f"E{r}", resp, align=WRAP)
        if src.startswith("http"):
            put_url(ws, f"F{r}", src)
            put(ws, f"G{r}", "Web検索の要約（本文未閲覧）", align=WRAP)
        else:
            put(ws, f"F{r}", src, align=WRAP)
            put(ws, f"G{r}", "Amazonレビュー精読が必要", align=WRAP)
        ws.row_dimensions[r].height = 42
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:G{4 + len(REVIEWS)}"
    return ws


# ---------------------------------------------------------------- plan
PLAN = {  # no -> (SKU count, Amazon units per SKU per month)
    32: (3, 150), 24: (2, 150), 2: (1, 100), 26: (2, 80), 1: (1, 100), 9: (2, 120), 29: (1, 50), 38: (1, 80),
}


def build_plan(wb, rc):
    ws = wb.create_sheet("月利100万・年商5億計画")
    ws["A1"] = "月利100万円・年商5億円に向けた試算"
    ws["A1"].font = F_TITLE
    ws["A2"] = "緑字＝リサーチ表の計算結果を参照／青字＝計画値（編集可）。利益は広告・返品・保管・出荷作業控除後、固定費（人件費・サンプル費等）控除前。"
    ws["A2"].font = F_NOTE

    ws["A4"] = "① 月利100万円に必要な月販（利益率15%以上の8商品）"
    ws["A4"].font = F_BOLD
    heads = ["優先順位", "商品名", "販売価格（税込）", "利益（円/個）", "利益率", "月利100万に必要な月販", "想定月販（単品・Amazon）", "到達率", "見立て"]
    widths = [8, 34, 13, 12, 9, 13, 13, 9, 30]
    for i, (h, w) in enumerate(zip(heads, widths)):
        col = get_column_letter(i + 1)
        put(ws, f"{col}5", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
        ws.column_dimensions[col].width = w
    ws.row_dimensions[5].height = 36
    mains = sorted(MAIN, key=lambda x: x["rank"])
    for i, p in enumerate(mains):
        r = 6 + i
        src = 5 + i
        put(ws, f"A{r}", f"={RSQ}!{rc['rank']}{src}", F_LINK_SHEET, align=CENTER)
        put(ws, f"B{r}", f"={RSQ}!{rc['name']}{src}", F_LINK_SHEET, align=WRAP)
        put(ws, f"C{r}", f"={RSQ}!{rc['price']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"D{r}", f"={RSQ}!{rc['profit']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"E{r}", f"={RSQ}!{rc['margin']}{src}", F_LINK_SHEET, fmt=PCT)
        put(ws, f"F{r}", f"={RSQ}!{rc['need']}{src}", F_LINK_SHEET, fmt=INT)
        put(ws, f"G{r}", f"={RSQ}!{rc['vol']}{src}", F_LINK_SHEET, fmt=INT)
        put(ws, f"H{r}", f'=IF(ISNUMBER(F{r}),G{r}/F{r},0)', fmt=PCT)
        put(ws, f"I{r}", f'=IF(H{r}>=1,"単品で到達",IF(H{r}>=0.4,"サイズ・色展開＋楽天/Yahoo!併売で到達圏","単品では困難（補完商品）"))', align=WRAP)
        ws.row_dimensions[r].height = 30

    top = 6 + len(mains) + 2
    ws[f"A{top}"] = "② 年商5億円ロードマップ（試算）"
    ws[f"A{top}"].font = F_BOLD
    put(ws, f"A{top + 1}", "楽天・Yahoo!併売係数", F_BOLD)
    put(ws, f"C{top + 1}", 1.3, F_INPUT, fmt='0.00', fill=FILL_KEY)
    put(ws, f"D{top + 1}", "Amazon月販に対する全モール合計の倍率（仮定）", align=WRAP, border=False)
    put(ws, f"A{top + 2}", "目標年商（円）", F_BOLD)
    put(ws, f"C{top + 2}", 500000000, F_INPUT, fmt=YEN, fill=FILL_INPUT)
    put(ws, f"A{top + 3}", "目標年収（円）", F_BOLD)
    put(ws, f"C{top + 3}", 50000000, F_INPUT, fmt=YEN, fill=FILL_INPUT)
    k_ref = f"$C${top + 1}"

    h2 = top + 5
    heads2 = ["優先順位", "商品名", "販売価格（税込）", "利益（円/個）", "展開SKU数", "1SKUの月販（Amazon）", "月販合計（併売込み）", "月商（税込）", "月利", "年商", "年間利益"]
    for i, h in enumerate(heads2):
        col = get_column_letter(i + 1)
        put(ws, f"{col}{h2}", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
    for col, w in zip("GHIJK", (13, 15, 30, 15, 15)):
        ws.column_dimensions[col].width = w
    ws.row_dimensions[h2].height = 36
    for i, p in enumerate(mains):
        r = h2 + 1 + i
        src = 5 + i
        sku, units = PLAN[p["no"]]
        put(ws, f"A{r}", f"={RSQ}!{rc['rank']}{src}", F_LINK_SHEET, align=CENTER)
        put(ws, f"B{r}", f"={RSQ}!{rc['name']}{src}", F_LINK_SHEET, align=WRAP)
        put(ws, f"C{r}", f"={RSQ}!{rc['price']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"D{r}", f"={RSQ}!{rc['profit']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"E{r}", sku, F_INPUT, fmt=INT, fill=FILL_INPUT)
        put(ws, f"F{r}", units, F_INPUT, fmt=INT, fill=FILL_INPUT)
        put(ws, f"G{r}", f"=E{r}*F{r}*{k_ref}", fmt=INT)
        put(ws, f"H{r}", f"=G{r}*C{r}", fmt=YEN)
        put(ws, f"I{r}", f"=G{r}*D{r}", fmt=YEN)
        put(ws, f"J{r}", f"=H{r}*12", fmt=YEN)
        put(ws, f"K{r}", f"=I{r}*12", fmt=YEN)
        ws.row_dimensions[r].height = 30
    first, lastr = h2 + 1, h2 + len(mains)
    tr = lastr + 1
    put(ws, f"B{tr}", "合計", F_BOLD)
    for col, fmt in (("G", INT), ("H", YEN), ("I", YEN), ("J", YEN), ("K", YEN)):
        put(ws, f"{col}{tr}", f"=SUM({col}{first}:{col}{lastr})", F_BOLD, fmt=fmt, fill=FILL_SECTION)
    put(ws, f"B{tr + 1}", "目標年商との差（不足分）", F_BOLD)
    put(ws, f"J{tr + 1}", f"=C{top + 2}-J{tr}", F_BOLD, fmt=YEN)
    put(ws, f"B{tr + 2}", "不足分を月商に換算", F_BOLD)
    put(ws, f"H{tr + 2}", f"=MAX(0,J{tr + 1})/12", F_BOLD, fmt=YEN)
    put(ws, f"B{tr + 3}", "年間利益 − 目標年収（固定費控除前）", F_BOLD)
    put(ws, f"K{tr + 3}", f"=K{tr}-C{top + 3}", F_BOLD, fmt=YEN)
    notes = [
        "・8商品＋サイズ/色展開＋併売だけでは年商5億に届かない見込み。不足分は『全40候補』の△条件付き商品（猫トイレ収納・ステンレスワゴン・屋外ごみ保管ボックス等）を天瞳の送料で再試算し、15%を満たしたものから追加する。",
        "・月利100万円に最も近いのは大型宅配ボックスと大型猫用キャットタワー（1個あたり利益が大きく、カテゴリの需要も大きい）。単品で100万円を狙うより、2〜3サイズ展開と楽天・Yahoo!併売で到達させる設計が現実的。",
        "・想定月販はKeepa／セラースプライトでの実測前の仮置き（データ確度C）。発注前に上位3品の月販を確認し、黄色セルを更新すること。",
    ]
    for j, t in enumerate(notes):
        ws[f"A{tr + 5 + j}"] = t
        ws[f"A{tr + 5 + j}"].font = F_NOTE
    return ws


# ---------------------------------------------------------------- sources
def build_sources(wb):
    ws = wb.create_sheet("出典")
    ws["A1"] = "出典一覧（2026-09-24 に検索で確認。検索結果の要約を含む）"
    ws["A1"].font = F_TITLE
    for i, (h, w) in enumerate([("区分", 14), ("内容", 70), ("URL", 80)]):
        col = get_column_letter(i + 1)
        put(ws, f"{col}3", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
        ws.column_dimensions[col].width = w
    for i, (k, text, url) in enumerate(SOURCES):
        r = 4 + i
        put(ws, f"A{r}", k)
        put(ws, f"B{r}", text, align=WRAP)
        put_url(ws, f"C{r}", url)
    return ws


# ---------------------------------------------------------------- summary
def build_summary(wb, rc):
    ws = wb.active
    ws.title = "サマリー"
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 34
    for col, w in zip("CDEFGHI", (13, 12, 10, 13, 12, 12, 16)):
        ws.column_dimensions[col].width = w
    ws["B1"] = "大型OEMリサーチ（神田式）サマリー　2026-09-24"
    ws["B1"].font = F_TITLE
    lines = [
        ("結論", None),
        ("1. 前回の40候補を同じ条件（手数料15.4%/10.4%・広告10%・返品4%・保管・出荷作業・送料・関税込み）で試算すると、利益率15%以上は8商品。", None),
        ("2. 月利100万円に最も近いのは『大型宅配ボックス』と『大型猫用キャットタワー』。単品では必要月販が約350〜360個のため、サイズ・色展開と楽天・Yahoo!併売で到達させる設計。", None),
        ("3. 前回上位10のうち、タイヤラック（実勢¥5,720〜6,980）・45Lごみ箱ラック・梱包作業台は実勢価格か大型送料で不成立。猫トイレ収納・リネンカート・ポッティングベンチ・ステンレスワゴンは利益率10〜15%の『条件付き』（天瞳の送料・実見積しだい）。", None),
        ("4. 大型品の損益は国内送料と立米単価で大きく変わる。天瞳の送料資料の数値を『前提条件』に入れると全表が再計算され、『15%達成の国内送料上限』で合否がすぐ分かる。", None),
        ("データについて", None),
        ("・Amazon.co.jp／1688.com の商品ページは、この作業環境のネットワーク制限で直接開けなかった。競合の価格・仕様・口コミは検索結果で確認できた範囲（出典付き）、1688単価・梱包寸法・月販は推定（黄色セル＝要上書き）。", None),
        ("・添付のリサーチ表テンプレート・商品リスト・送料資料は本環境から参照できなかったため、列構成は一般的な中国輸入OEMリサーチ表に合わせた。", None),
    ]
    r = 3
    for text, _ in lines:
        ws.merge_cells(f"B{r}:I{r}")
        ws[f"B{r}"] = text
        ws[f"B{r}"].font = F_BOLD if text in ("結論", "データについて") else F_BASE
        ws[f"B{r}"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 15 * max(1, -(-len(text) // 58))
        r += 1
    r += 1
    ws[f"B{r}"] = "利益率15%以上の厳選8商品（リサーチ表から自動参照）"
    ws[f"B{r}"].font = F_BOLD
    r += 1
    heads = ["商品名", "販売価格", "利益/個", "利益率", "月利（想定月販）", "想定月販", "月利100万に必要な月販", "判定"]
    for i, h in enumerate(heads):
        put(ws, f"{get_column_letter(i + 2)}{r}", h, F_HEAD, fill=FILL_HEAD, align=CENTER)
    ws.row_dimensions[r].height = 30
    mains = sorted(MAIN, key=lambda x: x["rank"])
    for i, _p in enumerate(mains):
        rr = r + 1 + i
        src = 5 + i
        put(ws, f"B{rr}", f"={RSQ}!{rc['name']}{src}", F_LINK_SHEET, align=WRAP)
        put(ws, f"C{rr}", f"={RSQ}!{rc['price']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"D{rr}", f"={RSQ}!{rc['profit']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"E{rr}", f"={RSQ}!{rc['margin']}{src}", F_LINK_SHEET, fmt=PCT)
        put(ws, f"F{rr}", f"={RSQ}!{rc['mprofit']}{src}", F_LINK_SHEET, fmt=YEN)
        put(ws, f"G{rr}", f"={RSQ}!{rc['vol']}{src}", F_LINK_SHEET, fmt=INT)
        put(ws, f"H{rr}", f"={RSQ}!{rc['need']}{src}", F_LINK_SHEET, fmt=INT)
        put(ws, f"I{rr}", f"={RSQ}!{rc['judge']}{src}", F_LINK_SHEET)
        ws.row_dimensions[rr].height = 30
    r = r + 1 + len(mains) + 1
    ws[f"B{r}"] = "次にやること"
    ws[f"B{r}"].font = F_BOLD
    todo = [
        "① 天瞳の送料資料（立米単価・サイズ別の国内送料・保管料・出荷作業料）を『前提条件』の黄色セルに入力 → 判定を確定",
        "② 上位2商品（宅配ボックス・キャットタワー）の1688見積を各3社（単価・MOQ・梱包寸法・重量・耐荷重試験）→ 黄色セルを上書き",
        "③ Keepa／セラースプライトで競合上位3品の月販・価格推移を確認 → 想定月販を更新",
        "④ Amazonの星1〜3レビューを精読し、『レビュー分析』の要確認行を埋める → 付加価値の仕様書へ",
        "⑤ △条件付き（猫トイレ収納・ステンレスワゴン・屋外ごみ保管ボックス等）を天瞳の送料で再判定",
    ]
    for j, t in enumerate(todo):
        rr = r + 1 + j
        ws.merge_cells(f"B{rr}:I{rr}")
        ws[f"B{rr}"] = t
        ws[f"B{rr}"].font = F_BASE
        ws[f"B{rr}"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[rr].height = 15 * max(1, -(-len(t) // 58))
    r = r + 1 + len(todo) + 1
    ws[f"B{r}"] = "凡例：青字・黄色＝入力（推定含む）／黒字＝計算式／緑字＝他シート参照／黄色（濃）＝天瞳資料で必ず差し替える前提"
    ws[f"B{r}"].font = F_NOTE
    return ws


def main():
    wb = Workbook()
    build_assumptions(wb)
    rs_ws, rc = build_research(wb)
    build_reviews(wb)
    build_plan(wb, rc)
    build_screening(wb, rc)
    build_sources(wb)
    build_summary(wb, rc)
    # order sheets
    order = ["サマリー", RS, "レビュー分析", "月利100万・年商5億計画", "全40候補スクリーニング", "前提条件", "出典"]
    wb._sheets = [wb[n] for n in order]
    wb.active = 0
    for ws in wb.worksheets:
        ws.sheet_view.zoomScale = 90
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        if ws.title not in (RS, "全40候補スクリーニング"):
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0
            ws.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
