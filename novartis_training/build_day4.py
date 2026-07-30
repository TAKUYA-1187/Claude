# -*- coding: utf-8 -*-
"""
Renal MR スキルアッププロジェクト DAY4
「ちょっと分かるだけで世界が変わる」 — テーマ：戦略的思考

DAY4_base_1-7.pptx の冒頭7枚を保持し（Agendaの文言のみ更新）、8枚目以降を生成。

■ 構成（計60分）
   ① 5分  振り返り
   ② 5分  Triple Win Beyond
   ③10分  ワーク①：Wants／Needsの仕分け
   ④ 5分  仕分けの意義と仮説立て
   ⑤10分  ワーク②：仮説立て（WantsをNeedsへ）
   ⑥ 5分  仮説立ての意義とエリアプラン・4S
   ⑦10分  インタビュー（エリア＋大学攻略事例）
   ⑧ 5分  まとめ（女子医大の活動）
   ⑨ 5分  総括

■ 到達目標（プロジェクト公式・戦略的思考）
   収集した情報から、エリアの課題・原因・解決方法を可視化できる
   本日の到達点：得た情報をFact・Wants・Needsに仕分け、そこから仮説を立てられる

■ 設計の柱
   - 中心は「仕分け → 仮説 → 4S／エリアプラン」の一本道
   - Needs＝理想と現状のGap（状態）、Wants＝Gapを埋める具体的な手段（ROTF3）
   - ワーク①の題材は腎臓内科の医局から得た情報9件。製品には紐づけない
   - Fact／Wants／Needsの3分類にすることで、DAY3で集めた情報がそのまま使える
   - 4Sとの対応：Needs→成功像／Fact→現状／仮説→課題・原因／Wants→解決策の入口
   - Triple Win（患者・顧客・自社）を Beyond（エリア）まで広げる
   - まとめは女子医大の活動。大学を個で見ず、エリアの1施設として影響の輪を設計した事例
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

BASE = "/home/user/Claude/novartis_training/DAY4_base_1-7.pptx"
OUT  = "/home/user/Claude/novartis_training/DAY4_ちょっと分かるだけで世界が変わる.pptx"
KEEP = 7

# ---------------------------------------------------------------- palette
DEEP   = RGBColor(0x0B, 0x4F, 0x37)
DEEP2  = RGBColor(0x07, 0x35, 0x25)
GREEN  = RGBColor(0x12, 0x8A, 0x54)
GREEN2 = RGBColor(0x3D, 0xA5, 0x74)
MINT   = RGBColor(0xBF, 0xE8, 0xD2)
PALE   = RGBColor(0xE9, 0xF5, 0xEE)
PALE2  = RGBColor(0xF4, 0xFA, 0xF6)
NAVY   = RGBColor(0x1F, 0x38, 0x64)
NAVY2  = RGBColor(0x3B, 0x5C, 0x99)
PALEB  = RGBColor(0xEA, 0xF0, 0xF9)
GOLD   = RGBColor(0xB8, 0x6A, 0x00)
YELL   = RGBColor(0xFF, 0xC0, 0x00)
YPALE  = RGBColor(0xFF, 0xF6, 0xDC)
RED    = RGBColor(0xC0, 0x00, 0x00)
RPALE  = RGBColor(0xFB, 0xEC, 0xEC)
INK    = RGBColor(0x26, 0x26, 0x26)
GRAY   = RGBColor(0x59, 0x59, 0x59)
LGRAY  = RGBColor(0xD9, 0xD9, 0xD9)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Meiryo UI"

# ---------------------------------------------------------------- base
prs = Presentation(BASE)
_sld = prs.slides._sldIdLst
for sl in list(_sld)[KEEP:]:
    rId = sl.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    prs.part.drop_rel(rId); _sld.remove(sl)

BLANK = None
for m in prs.slide_masters:
    for lay in m.slide_layouts:
        if len(lay.placeholders) == 0:
            BLANK = lay; break
    if BLANK is not None:
        break
if BLANK is None:
    BLANK = prs.slide_masters[0].slide_layouts[6]

# --- 冒頭2枚目のAgenda文言のみ更新（書式は維持） ---
AGENDA_LINES = ["■振り返り／Triple Win Beyond　10分",
                "■ワーク①「Wants／Needs」　15分",
                "■ワーク②「仮説立て」と4S　15分",
                "■インタビュー／まとめ・総括　20分"]
for sh in prs.slides[1].shapes:
    if sh.has_text_frame and "オープニング" in sh.text_frame.text:
        for pi, para in enumerate(sh.text_frame.paragraphs):
            if pi < len(AGENDA_LINES) and para.runs:
                para.runs[0].text = AGENDA_LINES[pi]
                for r in para.runs[1:]:
                    r.text = ""
        break

# ---------------------------------------------------------------- helpers
def _font(run, size, bold, color, italic=False, name=FONT):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.italic = italic
    f.color.rgb = color; f.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', name)

def add_slide():
    s = prs.slides.add_slide(BLANK)
    for sh in list(s.shapes):
        if sh.is_placeholder:
            sh._element.getparent().remove(sh._element)
    return s

def _fill(tf, paras, anchor):
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        if p.get("space_before") is not None: para.space_before = Pt(p["space_before"])
        if p.get("space_after") is not None: para.space_after = Pt(p["space_after"])
        if p.get("line") is not None: para.line_spacing = p["line"]
        for text, st in p["runs"]:
            r = para.add_run(); r.text = text
            _font(r, st.get("size", 14), st.get("bold", False),
                  st.get("color", INK), st.get("italic", False))

def txt(s, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    _fill(tf, paras, anchor)
    return tb

def P(runs, **kw):
    d = {"runs": runs}; d.update(kw); return d

def R(t, size=14, bold=False, color=INK, italic=False):
    return (t, {"size": size, "bold": bold, "color": color, "italic": italic})

def shape(s, x, y, w, h, fill=PALE, line=None, line_w=1.0,
          kind=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    sp = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None: sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        try: sp.adjustments[0] = radius
        except Exception: pass
    tf = sp.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    return sp

def card(s, x, y, w, h, paras, fill=PALE, line=None, line_w=1.0,
         anchor=MSO_ANCHOR.MIDDLE, radius=0.08, pad=None, kind=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = shape(s, x, y, w, h, fill=fill, line=line, line_w=line_w, kind=kind, radius=radius)
    _fill(sp.text_frame, paras, anchor)
    if pad is not None:
        sp.text_frame.margin_left = sp.text_frame.margin_right = Inches(pad)
        sp.text_frame.margin_top = sp.text_frame.margin_bottom = Inches(pad * 0.7)
    return sp

def chip_w(label, base=0.6, min_w=2.0):
    a = sum(1 for ch in label if ord(ch) < 0x2E80)
    return max(min_w, 0.13 * a + 0.24 * (len(label) - a) + base)

def chip(s, x, y, w, h, text, fill=GREEN, size=12.5, color=WHITE):
    sp = card(s, x, y, w, h, [P([R(text, size, True, color)], align=PP_ALIGN.CENTER)],
              fill=fill, radius=0.5)
    sp.text_frame.word_wrap = False
    return sp

def circle(s, x, y, d, text, fill=GREEN, size=13, color=WHITE, line=None, wrap=False):
    sp = shape(s, x, y, d, d, fill=fill, line=line, kind=MSO_SHAPE.OVAL)
    tf = sp.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = wrap
    _fill(tf, [P([R(text, size, True, color)], align=PP_ALIGN.CENTER, line=1.05)],
          MSO_ANCHOR.MIDDLE)
    return sp

def arrow(s, x, y, w, h, color=GREEN, direction="right"):
    kind = {"right": MSO_SHAPE.RIGHT_ARROW, "down": MSO_SHAPE.DOWN_ARROW,
            "up": MSO_SHAPE.UP_ARROW, "left": MSO_SHAPE.LEFT_ARROW}[direction]
    sp = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def set_alpha(sp, pct):
    """塗りに透明度を設定（重なりを濃く見せる）。pct=0〜100"""
    fill = sp.fill._xPr.find(qn('a:solidFill'))
    if fill is None:
        return sp
    clr = fill.find(qn('a:srgbClr'))
    if clr is None:
        return sp
    a = clr.makeelement(qn('a:alpha'), {'val': str(int((100 - pct) * 1000))})
    clr.append(a)
    return sp

def conn(s, x1, y1, x2, y2, color=GRAY, weight=1.5, dash=None):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                               Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(weight); c.shadow.inherit = False
    if dash:
        ln = c.line._get_or_add_ln()
        ln.append(ln.makeelement(qn('a:prstDash'), {'val': dash}))
    return c

PAGE = [KEEP]
FOOT = "Renal MR スキルアッププロジェクト DAY4｜戦略的思考"

def footer(s, dark=False):
    PAGE[0] += 1
    txt(s, 2.8, 7.14, 7.4, 0.3, [P([R(FOOT, 9, False, MINT if dark else GRAY)])])
    txt(s, 12.2, 7.14, 0.55, 0.3,
        [P([R(str(PAGE[0]), 10, True, MINT if dark else GREEN)], align=PP_ALIGN.RIGHT)])

def header(s, kicker, title, time=None, kcolor=GREEN, lead=None):
    label = kicker + (("　｜　" + time) if time else "")
    chip(s, 0.6, 0.34, chip_w(label), 0.42, label, fill=kcolor)
    txt(s, 0.6, 0.86, 12.2, 0.66, [P([R(title, 25, True, DEEP)])])
    if lead:
        txt(s, 0.6, 1.56, 12.2, 0.42, [P([R(lead, 13.5, True, INK)])])
    footer(s)

def section(s, no, title, subtitle, question, bullets):
    shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
    shape(s, 0, 0, 13.333, 0.55, fill=DEEP2, kind=MSO_SHAPE.RECTANGLE)
    txt(s, 0.9, 1.35, 2.4, 1.5, [P([R(no, 80, True, RGBColor(0x1D, 0x74, 0x51))])])
    txt(s, 3.2, 1.25, 9.4, 0.45, [P([R(subtitle, 14.5, True, MINT)])])
    txt(s, 3.2, 1.7, 9.4, 1.0, [P([R(title, 34, True, WHITE)])])
    card(s, 0.9, 3.15, 11.7, 0.95, [P([R(question, 19, True, DEEP)], align=PP_ALIGN.CENTER)],
         fill=YELL, radius=0.1, pad=0.16)
    for i, b in enumerate(bullets):
        circle(s, 0.95, 4.5 + i * 0.78, 0.44, str(i + 1), fill=YELL, size=13, color=DEEP)
        txt(s, 1.6, 4.58 + i * 0.78, 10.9, 0.55, [P([R(b, 15, False, WHITE)], line=1.15)])
    footer(s, dark=True)

# ================================================================ 8 Agenda
s = add_slide()
header(s, "AGENDA", "本日の進め方")
blocks = [("振り返り ／ Triple Win Beyond", "10分", "3回の振り返り｜Winをエリアまで広げる", GREEN),
          ("ワーク①「WantsとNeedsの仕分け」", "15分", "得た情報を3つに分ける｜仕分けの意義", NAVY),
          ("ワーク②「仮説立て」とエリアプラン", "15分", "WantsをNeedsへ｜4Sにつなげる", NAVY),
          ("インタビュー ／ まとめ・総括", "20分", "エリア＋大学攻略事例｜女子医大の活動", GREEN)]
y = 2.0
for t, tm, d, col in blocks:
    card(s, 0.6, y, 6.3, 1.0, [P([R("■ " + t, 16, True, WHITE)])], fill=col, radius=0.1, pad=0.22)
    card(s, 7.0, y, 1.2, 1.0, [P([R(tm, 15, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 8.35, y, 4.4, 1.0, [P([R(d, 12.5, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.18)
    y += 1.2

# ================================================================ 9 本日の到達点
s = add_slide()
header(s, "TODAY'S GOAL", "情報を「仕分ける」と、仮説が立つ")
txt(s, 0.6, 1.58, 12.15, 0.4,
    [P([R("― 得た情報をFact・Wants・Needsに分け、エリアの打ち手につなげる ―", 15, True, GRAY)],
       align=PP_ALIGN.CENTER)])
pillars = [("採用", "DAY 1", GREEN2), ("面会", "DAY 2", GREEN2),
           ("情報収集", "DAY 3", GREEN2), ("戦略的思考", "DAY 4", DEEP)]
for i, (t, d, col) in enumerate(pillars):
    x = 0.6 + i * 3.12
    card(s, x, 2.1, 2.95, 0.75,
         [P([R("◆ " + t, 15, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(d, 11, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
card(s, 0.6, 3.0, 12.15, 0.9,
     [P([R("到達目標：", 13.5, True, DEEP),
         R("収集した情報から、エリアの課題・原因・解決方法を可視化できる", 15, True, RED)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("本日の到達点：得た情報を仕分け、そこから仮説を立てられる", 13.5, True, DEEP)],
        align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
flow = [("Fact", "集めた事実", GRAY), ("仕分け", "3つに分ける", NAVY),
        ("仮説", "なぜかを立てる", GOLD), ("4S・エリアプラン", "打ち手にする", GREEN)]
for i, (t, d, col) in enumerate(flow):
    x = 0.6 + i * 3.12
    card(s, x, 4.2, 2.85, 0.62, [P([R(t, 15, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 4.9, 2.85, 0.55, [P([R(d, 12.5, False, INK)], align=PP_ALIGN.CENTER)],
         fill=PALE2, radius=0.1, pad=0.1)
    if i < 3:
        arrow(s, x + 2.89, 4.37, 0.16, 0.28, color=GREEN2)
card(s, 0.6, 5.75, 12.15, 1.05,
     [P([R("情報の量では差がつかない。", 15, False, WHITE)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("同じ情報から、どんな仮説を立てられるかで差がつく。", 21, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 10 ① 振り返り
s = add_slide()
header(s, "① 振り返り", "3回で手に入れた力", kcolor=GREEN)
looks = [("DAY 1", "見る力", ["大学・基幹病院の構造", "誰がどこまで決められるか"], GREEN),
         ("DAY 2", "会う力", ["Best Time / Best Place", "一人で突破しない"], NAVY2),
         ("DAY 3", "情報を取る力", ["Dry情報とWet情報", "顧客理解を深める"], NAVY)]
for i, (d, t, lines, col) in enumerate(looks):
    x = 0.6 + i * 4.09
    card(s, x, 1.9, 3.9, 0.75,
         [P([R(d, 11.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=3),
          P([R(t, 16, True, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
    card(s, x, 2.73, 3.9, 1.35,
         [P([R("・" + l, 13, False, INK)], line=1.25, space_after=9) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 0.6, 4.35, 12.15, 0.75,
     [P([R("DAY3の最後の問い　", 14, False, INK),
         R("「営業として、その情報をどう活かすか」", 17, True, RED)], align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.1)
card(s, 0.6, 5.35, 12.15, 1.4,
     [P([R("情報は、もう集まっている。", 15, False, WHITE)], align=PP_ALIGN.CENTER, space_after=7),
      P([R("今日は、その情報を仕分けて、仮説を立てて、エリアで動かす。", 21, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 11 ② Triple Win
s = add_slide()
header(s, "② TRIPLE WIN", "解決策とは、3者が同時にWinになっているもの", kcolor=NAVY)
wins = [("患者さん", ["適切な診断・治療に、", "適切なタイミングで届く"], GREEN),
        ("顧客（医局・施設）", ["果たしたい役割が果たせる", "施設・医師の価値が上がる"], NAVY),
        ("ノバルティス", ["必要な患者さんに届く", "エリアで信頼される"], GOLD)]
for i, (t, lines, col) in enumerate(wins):
    x = 0.6 + i * 4.09
    circle(s, x + 1.55, 1.9, 0.8, "WIN", fill=col, size=14)
    card(s, x, 2.85, 3.9, 0.62, [P([R(t, 15, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 3.55, 3.9, 1.2,
         [P([R("・" + l, 13, False, INK)], line=1.25, space_after=8) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 0.6, 5.0, 12.15, 0.7,
     [P([R("ノバルティスの目標・顧客の目標・患者さんの3者がWinになっているか（SAM）", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE2, line=LGRAY, radius=0.1)
card(s, 0.6, 5.95, 12.15, 0.85,
     [P([R("どれか1つが欠けた打ち手は、続かない。", 21, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 12 ② Beyond
s = add_slide()
header(s, "② BEYOND", "Winを、エリアまで広げる", kcolor=NAVY)
card(s, 0.6, 1.8, 5.85, 0.58, [P([R("大学を「個」で見ると", 15, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
n1 = ["その施設の中でWinが完結する", "1人の先生の要望に応える形になる", "隣の施設には何も起きない"]
card(s, 0.6, 2.48, 5.85, 1.75,
     [P([R("・" + l, 13.5, False, INK)], line=1.3, space_after=11) for l in n1],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)
arrow(s, 6.65, 2.9, 0.6, 0.55, color=GOLD)
card(s, 7.5, 1.8, 5.25, 0.58, [P([R("エリアの1施設として見ると", 15, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
n2 = ["関連病院・近隣大学にWinが広がる", "医師同士の関係が動く", "患者さんの流れが変わる"]
card(s, 7.5, 2.48, 5.25, 1.75,
     [P([R("・" + l, 13.5, True, INK)], line=1.3, space_after=11) for l in n2],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)
card(s, 0.6, 4.5, 12.15, 0.68,
     [P([R("Triple Win（患者・顧客・自社）　＋　Beyond（関連病院・近隣大学・地域の先生）", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
card(s, 0.6, 5.45, 12.15, 1.35,
     [P([R("大学は、エリアの中の1施設。", 15, False, WHITE)], align=PP_ALIGN.CENTER, space_after=7),
      P([R("影響の輪まで設計すると、同じ打ち手でもWinが大きくなる。", 21, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 13 ③ NeedsとWants
s = add_slide()
header(s, "③ NEEDS & WANTS", "Needsは「状態」、Wantsは「手段」", kcolor=NAVY)
card(s, 0.6, 1.75, 3.5, 0.62, [P([R("理想の状態", 15, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.1)
card(s, 0.6, 2.5, 3.5, 0.85,
     [P([R("Gap ＝ Needs", 22, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.1)
card(s, 0.6, 3.48, 3.5, 0.62, [P([R("現状", 15, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.1)
txt(s, 0.6, 4.2, 3.5, 0.36,
    [P([R("＝ 満たされていない状態", 13, True, DEEP)], align=PP_ALIGN.CENTER)])
arrow(s, 4.3, 2.72, 0.6, 0.5, color=GREEN2)
card(s, 5.1, 1.75, 7.65, 0.62, [P([R("Gapを埋める具体的なもの ＝ Wants", 15, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
card(s, 5.1, 2.5, 7.65, 1.6,
     [P([R("・顧客が口にするのは、ほとんどがWants（やり方の指定）", 13.5, True, INK)], line=1.3, space_after=9),
      P([R("・Wantsに応えるだけでは、その手段が正しいか分からない", 13.5, False, INK)], line=1.3, space_after=9),
      P([R("・Needsが分かれば、手段は他にも選べる", 13.5, False, INK)], line=1.3)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)
lat = [("顕在Needs", "顧客自身が気づいている", NAVY2),
       ("潜在Needs", "顧客自身が気づいていない", GOLD)]
for i, (t, d, col) in enumerate(lat):
    x = 5.1 + i * 3.9
    card(s, x, 4.2, 3.75, 0.62, [P([R(t, 14, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 4.9, 3.75, 0.55, [P([R(d, 12, False, INK)], align=PP_ALIGN.CENTER)],
         fill=PALE2, radius=0.1, pad=0.1)
card(s, 0.6, 5.75, 12.15, 1.05,
     [P([R("顕在化することは珍しい。", 15, False, WHITE)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("気づかれていないNeedsを、競合より早く見つけられるかで差がつく。", 20, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 14 ③ 3つの箱
s = add_slide()
header(s, "③ 仕分けの目安", "得た情報を、3つのどれかに置く", kcolor=NAVY)
boxes = [("Fact（事実）", "観察できること", ["数字・出来事・体制", "願望が入っていない", "例：腎生検が半減している"], GRAY),
         ("Wants（手段）", "やり方の指定", ["「〜が欲しい」", "「〜してほしい」", "例：勉強会をやってほしい"], GREEN),
         ("Needs（状態）", "満たされていないGap", ["「〜したい」", "「〜が足りない・困っている」", "例：若手を育てたい"], RED)]
for i, (t, sub, lines, col) in enumerate(boxes):
    x = 0.6 + i * 4.09
    card(s, x, 1.85, 3.9, 0.85,
         [P([R(t, 16, True, WHITE)], align=PP_ALIGN.CENTER, space_after=3),
          P([R(sub, 11.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
    card(s, x, 2.8, 3.9, 1.9,
         [P([R("・" + l, 13, False, INK)], line=1.3, space_after=11) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 4.95, 12.15, 0.72,
     [P([R("迷ったら　", 14, False, INK),
         R("「これは状態か、手段か」", 18, True, DEEP),
         R("　願望が入っていなければ Fact", 14, False, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
card(s, 0.6, 5.9, 12.15, 0.9,
     [P([R("Factは、仮説の材料。Wantsは、入口。Needsは、目指す状態。", 20, True, YELL)],
       align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 15 ③ ワーク①-1 例題を仕分ける
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, chip_w("WORK ①-1　｜　4分"), 0.42, "WORK ①-1　｜　4分", fill=NAVY)
txt(s, 0.6, 0.86, 12.2, 0.52, [P([R("例題を、Fact／Wants／Needsに仕分ける", 24, True, DEEP)])])
txt(s, 0.6, 1.44, 12.2, 0.32,
    [P([R("腎臓内科の医局・先生から得た情報です。①〜⑨を、下の3つのどこに置くか決めてください。", 13.5, False, INK)])])
items = ["① 関連病院の先生向けに、CKDの勉強会をやってほしい",
         "② 腎生検の件数が、3年前の半分になっている",
         "③ 若手に、腎病理を読める医師を育てたい",
         "④ 〇〇大学の△△先生を、次の研究会に呼んでほしい",
         "⑤ eGFRが20を切ってから紹介されることが多い",
         "⑥ うちの医局を、もっと全国に知ってもらいたい",
         "⑦ 先月の学会のスライドが欲しい",
         "⑧ 教授が来年、学会の会長を務める",
         "⑨ 透析導入を、できるだけ遅らせたい"]
for i, it in enumerate(items):
    x = 0.6 + (i % 3) * 4.09
    y = 1.85 + (i // 3) * 0.72
    card(s, x, y, 3.9, 0.62, [P([R(it, 12, True, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
rows = [("Fact（事実）", GRAY), ("Wants（手段）", GREEN), ("Needs（状態）", RED)]
y = 4.22
for t, col in rows:
    card(s, 0.6, y, 2.6, 0.78, [P([R(t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    shape(s, 3.35, y, 9.4, 0.78, fill=WHITE, line=LGRAY, line_w=1.0, radius=0.02)
    y += 0.86
txt(s, 3.35, 6.78, 9.4, 0.28,
    [P([R("※ 番号を入れて、なぜそこに置いたかを一言で言えるようにしてください", 10.5, False, GRAY)])])
footer(s)

# ================================================================ 16 ③ ワーク①-2 経験を共有
s = add_slide()
header(s, "WORK ①-2", "これまでの経験を共有する", "6分", kcolor=NAVY)
card(s, 0.6, 1.85, 12.15, 0.95,
     [P([R("これまでの活動で、先生のWantsから", 18, False, INK),
         R("Needsを汲み取れた経験", 18, True, RED),
         R("はありますか？", 18, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.08, pad=0.16)
card(s, 0.6, 3.05, 12.15, 0.48, [P([R("話を深めるヒント", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
hints = ["先生の、どんな言葉（Wants）から始まりましたか？",
         "その裏にあるNeedsは、何だと考えましたか？",
         "気づいたあと、活動や提案はどう変わりましたか？"]
y = 3.68
for i, h in enumerate(hints):
    circle(s, 0.6, y, 0.68, str(i + 1), fill=NAVY2, size=17)
    card(s, 1.52, y, 11.23, 0.68, [P([R(h, 16.5, True, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.2)
    y += 0.8
card(s, 0.6, 6.15, 12.15, 0.66,
     [P([R("3〜4人で。うまくいかなかった経験、まだ分からない経験でも構いません。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 17 ③ 記録用（ワーク①）
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=WHITE, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, chip_w("記録用　｜　ワーク①"), 0.42, "記録用　｜　ワーク①", fill=NAVY2)
txt(s, 0.6, 0.86, 12.2, 0.5, [P([R("Wantsから、Needsを汲み取った経験", 23, True, DEEP)])])
txt(s, 0.6, 1.42, 12.2, 0.3,
    [P([R("書記の方は、出てきた発言をこの表に記録してください。", 12.5, False, GRAY)])])
cols = [("出てきたWants（言われた言葉）", 4.1, GREEN),
        ("汲み取ったNeeds（状態）", 4.1, RED),
        ("活動・提案がどう変わったか", 3.95, NAVY)]
x = 0.6
for t, w, col in cols:
    card(s, x, 1.85, w, 0.55, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.08)
    x += w + 0.05
for r in range(4):
    y = 2.48 + r * 1.08
    x = 0.6
    for t, w, col in cols:
        shape(s, x, y, w, 1.0, fill=PALE2 if r % 2 else WHITE, line=LGRAY, line_w=1.0, radius=0.02)
        x += w + 0.05
footer(s)

# ================================================================ 18 ④ 仕分けの意義
s = add_slide()
header(s, "④ なぜ仕分けるのか", "仕分けが終われば、仮説はほとんど出来ている", kcolor=GOLD)
mean = [("Factだけでは動けない", "情報は「量」ではなく「意味」。並べただけでは打ち手にならない", GRAY),
        ("Wantsに応えるだけでは足りない", "その手段が最善か分からない。次の一手も出てこない", GREEN),
        ("Needsが分かれば手段を選べる", "同じNeedsに対して、より効く手段を提案できる", RED)]
y = 1.95
for t, d, col in mean:
    card(s, 0.6, y, 4.5, 0.85, [P([R(t, 15, True, WHITE)], line=1.2)], fill=col, radius=0.1, pad=0.2)
    card(s, 5.25, y, 7.5, 0.85, [P([R(d, 13.5, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.2)
    y += 1.0
card(s, 0.6, 5.05, 12.15, 0.6,
     [P([R("御用聞きと提案の違いは、Needsまで降りているかどうか。", 16, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
card(s, 0.6, 5.78, 12.15, 0.55,
     [P([R("参考：付録B〜Dに、考えられるFact／Wants／Needsを掲載（ワーク②の題材にも使えます）", 13, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.1)
card(s, 0.6, 6.45, 12.15, 0.38,
     [P([R("仕分けは、仮説を立てるための下ごしらえ。", 16, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.06)

# ================================================================ 19 ④ WantsをNeedsへ
s = add_slide()
header(s, "④ 仮説立て", "Wantsに「なぜ？」を重ねて、Needsへ降りる", kcolor=GOLD)
steps = [("Wants", "関連病院の先生向けに、勉強会をやってほしい", GREEN),
         ("なぜ？", "関連病院から、進行してから紹介されることが多い", NAVY2),
         ("なぜ困る？", "早く紹介されれば、まだ治療の選択肢が残る", NAVY),
         ("Needs", "地域で早く見つけ、適切なタイミングで紹介される状態にしたい", RED)]
y = 1.9
for i, (t, d, col) in enumerate(steps):
    card(s, 0.6, y, 2.5, 0.72, [P([R(t, 14.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, 3.25, y, 9.5, 0.72, [P([R(d, 14, True if i == 3 else False, INK)], line=1.2)],
         fill=PALE if i == 3 else WHITE, line=GREEN if i == 3 else LGRAY, radius=0.1, pad=0.18)
    if i < 3:
        arrow(s, 1.73, y + 0.75, 0.24, 0.28, color=GRAY, direction="down")
    y += 1.06
card(s, 0.6, 6.1, 12.15, 0.75,
     [P([R("仮説は1つとは限らない。", 15, False, WHITE),
         R("　複数立てて、次の面談の質問で確かめる。", 19, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.16)

# ================================================================ 20 ⑤ ワーク② 進め方
s = add_slide()
header(s, "WORK ②", "自分の担当施設で、仮説と解決策を考える", "10分", kcolor=NAVY)
wsteps = [("1", "Fact・Wants・Needsを置く", GRAY),
          ("2", "仮説を1文にする", NAVY),
          ("3", "4Sに当てはめる", GOLD),
          ("4", "解決策を出す", GREEN)]
for i, (no, t, col) in enumerate(wsteps):
    x = 0.6 + i * 3.12
    card(s, x, 1.78, 2.95, 0.62,
         [P([R(no + "　" + t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    if i < 3:
        arrow(s, x + 2.99, 1.95, 0.14, 0.28, color=GREEN2)
card(s, 0.6, 2.6, 6.0, 0.55, [P([R("仮説の例", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.1)
hyp = ["この医局は「地域の腎臓診療の入口」を担いたいのではないか",
       "教授が学会長を務める年だから、医局の実績を外に出したいのではないか",
       "若手が育っていないことが、腎生検の減少につながっているのではないか",
       "紹介が遅いのは、地域の先生に紹介基準が伝わっていないからではないか",
       "全国発信の場を求めていて、近隣大学とも組める余地があるのではないか"]
card(s, 0.6, 3.22, 6.0, 2.6,
     [P([R("・" + l, 12.5, False, INK)], line=1.3, space_after=11) for l in hyp],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 6.75, 2.6, 6.0, 0.55, [P([R("解決策の例", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
sol = ["関連病院＋近隣大学を巻き込んだ合同勉強会を、医局と共同で企画する",
       "紹介基準を、地域の先生と共有できる形（研究会・連携パス）に落とす",
       "若手向けの症例検討会をつくり、医局の教育実績として残す",
       "医局の症例を、エリア・全国の講演会で発信する機会を設計する",
       "医師から医師へ案内してもらう形にして、参加の角度を上げる"]
card(s, 6.75, 3.22, 6.0, 2.6,
     [P([R("・" + l, 12.5, False, INK)], line=1.3, space_after=11) for l in sol],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 6.0, 12.15, 0.82,
     [P([R("例はあくまで参考。自分のエリアの言葉に置き換えてください。", 13.5, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("解決策は「顧客・患者さん・自社」の3者がWinになっているかで検証する。", 16, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.14)

# ================================================================ 21 ⑤ 4S記入シート（記録用）
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=WHITE, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.3, chip_w("記録用　｜　ワーク②"), 0.4, "記録用　｜　ワーク②", fill=NAVY2)
txt(s, 0.6, 0.78, 8.6, 0.46, [P([R("4S：エリア・施設の課題解決シート", 22, True, DEEP)])])
txt(s, 9.3, 0.86, 3.45, 0.3,
    [P([R("施設（　　　　　　　　　）", 12, False, GRAY)], align=PP_ALIGN.RIGHT)])
# 成功像
card(s, 0.6, 1.35, 12.15, 0.42, [P([R("【成功像】　← Needs", 13, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.06)
shape(s, 0.6, 1.79, 12.15, 0.72, fill=WHITE, line=LGRAY, line_w=1.2, radius=0.02)
# 中央の矢印帯
arrow(s, 3.1, 2.57, 0.3, 0.4, color=NAVY, direction="down")
txt(s, 3.5, 2.63, 3.3, 0.3, [P([R("理想とのGAPを洗い出す", 11.5, True, NAVY)])])
arrow(s, 9.7, 2.57, 0.3, 0.4, color=NAVY, direction="up")
txt(s, 10.1, 2.63, 2.7, 0.3, [P([R("理想に近づくか検証", 11.5, True, RED)])])
# 現状・課題
card(s, 0.6, 3.05, 6.0, 0.42, [P([R("【現状・課題】　← Fact", 13, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.06)
shape(s, 0.6, 3.49, 6.0, 1.35, fill=WHITE, line=LGRAY, line_w=1.2, radius=0.02)
arrow(s, 3.1, 4.9, 0.3, 0.34, color=NAVY, direction="down")
txt(s, 3.5, 4.93, 3.1, 0.3, [P([R("その理由を深掘る", 11.5, True, NAVY)])])
# 原因
card(s, 0.6, 5.32, 6.0, 0.42, [P([R("【原因】　← 仮説", 13, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.06)
shape(s, 0.6, 5.76, 6.0, 1.05, fill=WHITE, line=LGRAY, line_w=1.2, radius=0.02)
# 解決策
card(s, 6.75, 3.05, 6.0, 0.42, [P([R("【解決策】　← 打ち手（Wantsを手がかりに）", 13, True, WHITE)],
                                  align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.06)
shape(s, 6.75, 3.49, 6.0, 3.32, fill=WHITE, line=LGRAY, line_w=1.2, radius=0.02)
arrow(s, 6.28, 5.9, 0.4, 0.3, color=GREEN, direction="right")
footer(s)

# ================================================================ 22 ⑥ 4S記入例
s = add_slide()
header(s, "⑥ 記入例", "仕分けと仮説が、そのまま4Sに入る", kcolor=GREEN)
card(s, 0.6, 1.72, 12.15, 0.4, [P([R("【成功像】　← Needs", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.06)
card(s, 0.6, 2.14, 12.15, 0.6,
     [P([R("地域で早く見つかり、適切なタイミングで紹介される状態になっている", 15, True, INK)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, line=LGRAY, radius=0.02, pad=0.14)
card(s, 0.6, 2.95, 6.0, 0.4, [P([R("【現状・課題】　← Fact", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.06)
card(s, 0.6, 3.37, 6.0, 1.25,
     [P([R("・腎生検が3年前の半減", 12.5, False, INK)], line=1.25, space_after=7),
      P([R("・進行してから紹介されることが多い", 12.5, False, INK)], line=1.25, space_after=7),
      P([R("・教授が来年、学会の会長を務める", 12.5, False, INK)], line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.02, pad=0.16)
card(s, 0.6, 4.72, 6.0, 0.4, [P([R("【原因】　← 仮説", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.06)
card(s, 0.6, 5.14, 6.0, 1.05,
     [P([R("地域の腎臓診療の入口を担いたいが、関連病院との接点が薄く、紹介基準が共有されていない", 12.5, True, INK)],
       line=1.3)],
     fill=PALEB, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.02, pad=0.16)
card(s, 6.75, 2.95, 6.0, 0.4, [P([R("【解決策】　← 打ち手", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.06)
card(s, 6.75, 3.37, 6.0, 2.82,
     [P([R("・関連病院＋近隣大学の合同勉強会を、医局と共同で企画", 12.5, True, INK)], line=1.3, space_after=10),
      P([R("・テーマは「紹介基準の共通認識づくり」", 12.5, False, INK)], line=1.3, space_after=10),
      P([R("・近隣大学のファカルティも登壇に入れる", 12.5, False, INK)], line=1.3, space_after=10),
      P([R("・案内は医師から医師へ", 12.5, False, INK)], line=1.3, space_after=10),
      P([R("・学会長の年に合わせ、医局の症例発信の場も設計", 12.5, False, INK)], line=1.3)],
     fill=PALE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.02, pad=0.16)
card(s, 0.6, 6.35, 12.15, 0.48,
     [P([R("Wants（勉強会をやってほしい）は解決策の入口。Needsまで降りたから、エリアの形になった。", 13.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)


# ================================================================ 24 ⑦ インタビュー
s = add_slide()
section(s, "⑦", "エリア＋大学攻略事例", "インタビュー　｜　10分",
        "どの情報から、その仮説にたどり着いたのか？",
        ["大学1施設で終わらせず、エリアにどう広げたか",
         "Wantsのまま動いた時と、Needsまで降りた時で、何が違ったか",
         "最初に確かめるのは、どの情報か"])

# ================================================================ 25 ⑦ 記録用
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=WHITE, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, chip_w("記録用　｜　インタビュー"), 0.42, "記録用　｜　インタビュー", fill=GOLD)
txt(s, 0.6, 0.86, 12.2, 0.5, [P([R("聞きながら、自分のエリアに置き換える", 23, True, DEEP)])])
imemo = ["決め手になったFact", "先生のWantsとNeeds",
         "エリアの誰を、どの順番で巻き込んだか", "自分のエリアで確かめたいこと"]
y = 1.55
for t in imemo:
    card(s, 0.6, y, 3.6, 1.22, [P([R(t, 13, True, WHITE)], line=1.25)], fill=NAVY, radius=0.06, pad=0.16)
    shape(s, 4.35, y, 8.4, 1.22, fill=WHITE, line=LGRAY, line_w=1.2, radius=0.02)
    y += 1.3
footer(s)

# ================================================================ 26 ⑧ 女子医大①
s = add_slide()
header(s, "⑧ まとめ", "女子医大の活動 — 一言のWantsから始まった", kcolor=GREEN)
card(s, 0.6, 1.75, 12.15, 0.75,
     [P([R("初回面談の一言　", 13.5, True, GRAY),
         R("「女子医大腎臓内科を全国に売り出したい」", 20, True, RED)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.08, pad=0.14)
card(s, 0.6, 2.7, 5.85, 0.58, [P([R("集まっていたFact", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
f = ["女子医大では新機序薬の使用経験が複数例", "条件の近い近隣2大学では未使用",
     "希少疾患のため「誰に使うべきか」の情報が全国的に不足", "院内の小児腎・移植でも適正使用の共有Needs",
     "近隣大学の先生は共同研究者・女子医大出身"]
card(s, 0.6, 3.38, 5.85, 2.05,
     [P([R("・" + l, 12.5, False, INK)], line=1.25, space_after=7) for l in f],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
arrow(s, 6.65, 3.9, 0.6, 0.55, color=GOLD)
card(s, 7.5, 2.7, 5.25, 0.58, [P([R("降りた先のNeeds", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.1)
card(s, 7.5, 3.38, 5.25, 0.95,
     [P([R("実臨床の経験を、全国と地域に届ける場がない", 14, True, INK)], line=1.3)],
     fill=PALE, line=GREEN, radius=0.1, pad=0.18)
card(s, 7.5, 4.45, 5.25, 0.5, [P([R("立てた仮説", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.1)
card(s, 7.5, 5.03, 5.25, 0.4,
     [P([R("女子医大をHUBにすれば、横展開が起こる", 13, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALEB, line=NAVY2, radius=0.1, pad=0.1)
card(s, 0.6, 5.7, 12.15, 1.1,
     [P([R("「売り出したい」はWants。その裏の", 15, False, WHITE),
         R("「発信する場がない」というNeeds", 17, True, YELL),
         R("まで降りたことが起点。", 15, False, WHITE)], align=PP_ALIGN.CENTER, line=1.3)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 27 ⑧ 女子医大②
s = add_slide()
header(s, "⑧ まとめ", "3つの大学をつないで、影響の輪を設計した", kcolor=GREEN)
card(s, 0.6, 1.75, 5.85, 0.58, [P([R("設計", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.1)
des = ["女子医大をHUBに、近隣2大学を企画段階から巻き込む",
       "「エリア横展開・院内横展開・成人×小児」を、ファカルティ間で共通認識に",
       "MRからではなく、医師から医師へ参加案内",
       "現地開催＋海外演者で、会のPriorityを上げる"]
card(s, 0.6, 2.43, 5.85, 2.35,
     [P([R("・" + l, 12.5, False, INK)], line=1.3, space_after=10) for l in des],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 6.9, 1.75, 5.85, 0.58, [P([R("成果", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
res = ["参加医師35名（想定以上）",
       "処方確約1例／患者発掘1例／IC向上2施設",
       "大学間・診療科間の医師同士の関係性を複数確認",
       "次の疾患の活動の土台になった"]
card(s, 6.9, 2.43, 5.85, 2.35,
     [P([R("・" + l, 12.5, True, INK)], line=1.3, space_after=10) for l in res],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 4.95, 12.15, 0.7,
     [P([R("1つの大学のWinで終わらせず、近隣大学・院内の他科・患者さんの流れまでWinを広げた", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
card(s, 0.6, 5.85, 12.15, 0.95,
     [P([R("大学を「個」で見ず、エリアの1施設として影響の輪を設計した。", 20, True, YELL)],
       align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 28 ⑧ まとめメッセージ
s = add_slide()
header(s, "⑧ まとめ", "本日の3つ")
msgs = [("1", "情報は、仕分けた瞬間に意味を持つ",
         "Fact・Wants・Needs。どれかに置くだけで、次に何を聞くかが決まる。", NAVY),
        ("2", "Needsまで降りれば、手段は選べる",
         "Wantsに応えるのが仕事ではない。仮説を立てて、4Sで解決策を選ぶ。", GOLD),
        ("3", "大学は、エリアの1施設",
         "Triple Winをエリアまで広げると、同じ打ち手でも残るものが変わる。", GREEN)]
y = 1.95
for no, t, d, col in msgs:
    circle(s, 0.6, y + 0.15, 0.8, no, fill=col, size=20)
    card(s, 1.6, y, 11.15, 1.1,
         [P([R(t, 17, True, col)], space_after=5), P([R(d, 13, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.22)
    y += 1.25
card(s, 0.6, 5.66, 12.15, 1.12,
     [P([R("各自のFactを仕分けて、仮説を立てて、エリア攻略に。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("大学PJで共有した活動を、明日からの担当エリアで活かしてください。", 20, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 29 ⑨ 総括
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, chip_w("⑨ 総括　｜　5分"), 0.42, "⑨ 総括　｜　5分", fill=GREEN)
txt(s, 0.6, 0.95, 12.2, 0.8, [P([R("総括", 32, True, DEEP)])])
card(s, 0.6, 2.0, 12.15, 0.85,
     [P([R("4回を通して、大学・基幹病院の担当として何が変わったか", 22, True, INK)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.06, pad=0.18)
steps4 = [("第1回", "見る力", GREEN2), ("第2回", "会う力", GREEN2),
          ("第3回", "情報を取る力", GREEN2), ("第4回", "仮説を立てる力", YELL)]
for i, (d, t, col) in enumerate(steps4):
    x = 0.6 + i * 3.12
    card(s, x, 3.15, 2.9, 0.95,
         [P([R(d, 12.5, True, DEEP if col == YELL else WHITE)], align=PP_ALIGN.CENTER, space_after=4),
          P([R(t, 14.5, True, DEEP if col == YELL else WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col, radius=0.1)
    if i < 3:
        arrow(s, x + 2.93, 3.5, 0.14, 0.24, color=GREEN2)
shape(s, 0.6, 4.4, 12.15, 2.0, fill=WHITE, line=LGRAY, line_w=1.2, radius=0.02)
txt(s, 0.85, 4.55, 11.6, 0.3, [P([R("※ 所長よりご総括", 11, False, GRAY)])])
footer(s)

# ================================================================ 30 クロージング
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
txt(s, 0.9, 1.2, 11.5, 0.5, [P([R("ありがとうございました", 19, True, MINT)])])
card(s, 0.9, 2.0, 11.5, 1.55,
     [P([R("第3回では「どんな情報を、どこから取るか」を考えました。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("第4回では、その情報を仕分け、仮説を立て、エリアの打ち手に変えました。", 15, False, WHITE)],
        align=PP_ALIGN.CENTER)],
     fill=RGBColor(0x11, 0x63, 0x45), radius=0.1, pad=0.2)
card(s, 0.9, 3.85, 11.5, 1.7,
     [P([R("大学担当者に求められるのは、大学の中だけを詳しく知ることではありません。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("得た情報から仮説を立て、", 17, True, DEEP),
         R("エリアの中でWinを広げられること。", 21, True, DEEP)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=YELL, radius=0.1, pad=0.2)
txt(s, 0.9, 5.85, 11.5, 0.4,
    [P([R("明日から、担当施設のFactを1つ仕分けてみてください。", 15, True, MINT)],
       align=PP_ALIGN.CENTER)])
footer(s, dark=True)

# ================================================================ 30 付録A ワーク①の仕分け例
s = add_slide()
header(s, "APPENDIX A", "参考：ワーク① 仕分けの一例", kcolor=GRAY)
txt(s, 0.6, 1.62, 12.15, 0.34,
    [P([R("唯一の正解ではありません。なぜそう置いたかを説明できることが目的です。", 12.5, False, GRAY)],
       align=PP_ALIGN.CENTER)])
ans = [("Fact（事実）", GRAY,
        ["② 腎生検の件数が、3年前の半分になっている",
         "⑤ eGFRが20を切ってから紹介されることが多い",
         "⑧ 教授が来年、学会の会長を務める"],
        "→ 仮説の材料。単独では打ち手にならない"),
       ("Wants（手段）", GREEN,
        ["① 関連病院向けにCKDの勉強会をやってほしい",
         "④ 〇〇大学の△△先生を研究会に呼んでほしい",
         "⑦ 先月の学会のスライドが欲しい"],
        "→ 「なぜ？」を重ねてNeedsへ降りる"),
       ("Needs（状態）", RED,
        ["③ 若手に、腎病理を読める医師を育てたい",
         "⑥ うちの医局を、もっと全国に知ってもらいたい",
         "⑨ 透析導入を、できるだけ遅らせたい"],
        "→ 成功像になる。手段はここから選ぶ")]
for i, (t, col, lines, note) in enumerate(ans):
    x = 0.6 + i * 4.09
    card(s, x, 2.05, 3.9, 0.55, [P([R(t, 14, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.68, 3.9, 2.15,
         [P([R(l, 12, False, INK)], line=1.3, space_after=13) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
    card(s, x, 4.93, 3.9, 0.72, [P([R(note, 12, True, DEEP)], line=1.25)],
         fill=PALE2, radius=0.1, pad=0.14)
card(s, 0.6, 5.85, 12.15, 0.95,
     [P([R("一つの発言にも、複数の解釈があり得ます。仕分けが割れること自体が、確認すべき情報の在りかです。", 15, True, YELL)],
       align=PP_ALIGN.CENTER, line=1.25)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 31 付録B 考えられるFact
s = add_slide()
header(s, "APPENDIX B", "参考：考えられるFact（事実）", kcolor=GRAY)
txt(s, 0.6, 1.56, 12.15, 0.3,
    [P([R("評価や推測を混ぜず、確認できた事実として書く。大学・基幹病院で取得し得るFactの例です。", 12, False, GRAY)],
       align=PP_ALIGN.CENTER)])
facts = [("施設・診療体制",
          ["腎生検件数が3年前より減少している", "腎病理を専門とする医師が院内にいない",
           "腎生検結果の確認まで平均3週間かかる", "専門外来が週1回のみである",
           "他院からの症例相談は医局長が一括対応"]),
         ("患者・診療実態",
          ["腎機能が高度に低下してから紹介される", "大学と関連病院で治療方針が異なる",
           "治療導入の判断が特定の医師に集中", "若手医師によって検査・治療の進め方に差",
           "紹介後のフィードバックが紹介元へ返らない"]),
         ("人事・組織",
          ["来年度に教授交代が予定されている", "医局長が関連病院人事の調整を担当",
           "複数の基幹病院部長が同じ医局の出身", "若手医師が減少している",
           "新たな寄附講座が設置された"]),
         ("教育・研究・学術",
          ["教授が次年度の学会長を務める", "医局が特定疾患の研究班へ参加している",
           "若手向け勉強会が定期開催されていない", "研究会の演者が毎回同じ医師に偏る",
           "複数大学による共同研究実績がある"]),
         ("関係性",
          ["基幹病院部長が大学教授へ定期的に症例相談", "若手の相談相手は教授ではなく講師",
           "近隣大学間に共同研究・同年卒のつながり", "過去の人事を背景に施設間の関係が良好でない",
           "研究会の実務を医局長ではなく若手が担う"]),
         ("地域・外部環境",
          ["地域の腎臓専門医数が減少している", "専門医療機関への患者流出が増えている",
           "地域連携パスが十分に活用されていない", "行政がCKD連携事業を開始している",
           "紹介基準が地域内で統一されていない"])]
for i, (t, lines) in enumerate(facts):
    x = 0.6 + (i % 3) * 4.09
    y = 1.95 + (i // 3) * 2.45
    card(s, x, y, 3.9, 0.45, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GRAY, radius=0.1)
    card(s, x, y + 0.5, 3.9, 1.88,
         [P([R("・" + l, 10.5, False, INK)], line=1.18, space_after=6) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.13)
txt(s, 2.8, 6.85, 9.95, 0.28,
    [P([R("Factは単独では打ち手にならない。いくつかを線でつなぎ、仮説の材料にする。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)])

# ================================================================ 32 付録C Wants→複数のNeeds仮説→確認質問
s = add_slide()
header(s, "APPENDIX C", "参考：Wants → 複数のNeeds仮説 → 確認したい質問", kcolor=GRAY)
txt(s, 0.6, 1.56, 12.15, 0.3,
    [P([R("一つのWantsに、Needs仮説は複数あり得ます。決めつけず、質問で確かめる。", 12, False, GRAY)],
       align=PP_ALIGN.CENTER)])
wn = [("勉強会をやってほしい", "若手の診療力向上／接点の維持／紹介を早める／方針の浸透",
       "特に誰に、何を持ち帰ってほしいですか？"),
      ("A大学のB先生を呼んでほしい", "外部の知見／A大学との関係強化／医局を変える刺激／若手への視点",
       "B先生の、どの経験を聞きたいのでしょうか？"),
      ("学会のスライド・文献が欲しい", "院内で共有したい／理解を深めたい／症例判断・教育に使いたい",
       "どの内容を、どの場面で活用したいですか？"),
      ("若手に腎病理を学ばせたい", "診断の質の安定／特定医師への依存減／将来の体制維持",
       "どのレベルまで判断できる状態を目指しますか？"),
      ("連携パスを整えたい", "役割分担の明確化／逆紹介の円滑化／患者の流れの安定",
       "今、連携のどこで最も困っていますか？"),
      ("もっと早く紹介してほしい", "適切な時期につなぐ／治療の選択肢を残す／地域の基準を揃える",
       "紹介の、どの段階が最も課題ですか？")]
wn2 = [("症例をまとめたい・論文にしたい", "業績が必要／専門医・学位／医局の評価を上げたい",
        "いつまでに、どの形で発表したいですか？"),
       ("医局の活動を全国へ発信したい", "存在価値を高める／入局者を増やす／共同研究へつなげる",
        "全国に最も伝えたい強みは何ですか？"),
       ("関連病院に若手を出したい", "経験を積ませたい／派遣先との関係維持／ポストの確保",
        "派遣で、若手に何を得てほしいですか？"),
       ("市民公開講座をやりたい", "地域での認知向上／早期受診につなげる／患者・家族の支援",
        "参加者に、何を持ち帰ってほしいですか？"),
       ("〇〇大学と共同で会をやりたい", "研究の幅を広げる／人材交流／エリアでの存在感",
        "その大学と、何を一緒に実現したいですか？"),
       ("小児科・移植科と話す場が欲しい", "移行期診療の円滑化／院内での症例共有",
        "どの患者さんの場面を想定していますか？")]
for c, data in enumerate([wn, wn2]):
    x = 0.6 + c * 6.25
    for r, (w, n, q) in enumerate(data):
        y = 1.95 + r * 0.815
        card(s, x, y, 6.05, 0.755,
             [P([R("Wants ", 10, True, GREEN), R("「" + w + "」", 10.5, True, INK)], space_after=2),
              P([R("Needs仮説 ", 9.5, True, RED), R(n, 9.5, False, INK)], line=1.1, space_after=2),
              P([R("質問 ", 9.5, True, NAVY2), R(q, 9.5, False, GRAY)], line=1.1)],
             fill=WHITE if r % 2 else PALE2, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE,
             radius=0.06, pad=0.12)
txt(s, 2.8, 6.85, 9.95, 0.28,
    [P([R("同じWantsでも、裏のNeedsは施設によって違う。仮説が変われば、解決策も変わる。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)])

# ================================================================ 33 付録D Needsの例と解決策の広がり
s = add_slide()
header(s, "APPENDIX D", "参考：考えられるNeedsと、解決策の広がり", kcolor=GRAY)
card(s, 0.6, 1.7, 6.0, 0.5, [P([R("大学・基幹病院に考えられるNeeds（状態）", 13.5, True, WHITE)],
                               align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.1)
needs = ["診療の質を均一化したい", "適切なタイミングで専門医へつなぎたい",
         "診断に必要な専門性を維持したい", "若手を育成し、将来の体制を維持したい",
         "関連病院との役割分担を明確にしたい", "大学の知見を地域へ広げたい",
         "実臨床経験を学術的に発信したい", "施設・医局の存在価値を高めたい",
         "複数施設で共通する課題を解決したい", "大学間・診療科間の連携を強化したい",
         "研究と実臨床をつなげたい", "患者紹介後の連携を改善したい"]
card(s, 0.6, 2.28, 6.0, 4.1,
     [P([R("・" + n, 11, False, INK)], line=1.2, space_after=7) for n in needs],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
txt(s, 0.6, 6.45, 6.0, 0.44,
    [P([R("「勉強会をしたい」のような手段ではなく、実現したい状態で書く。", 11, True, DEEP)], line=1.2)])
card(s, 6.9, 1.7, 5.85, 0.5, [P([R("考える型", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.1)
chain = [("Wants", GREEN), ("複数のNeeds仮説", RED), ("確かめる質問", NAVY2), ("複数の解決策", GOLD)]
y = 2.32
for i, (t, col) in enumerate(chain):
    card(s, 6.9, y, 5.85, 0.42, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    if i < 3:
        arrow(s, 9.68, y + 0.43, 0.24, 0.14, color=GRAY, direction="down")
    y += 0.6
card(s, 6.9, 4.75, 5.85, 0.5, [P([R("解決策は、影響の範囲で選べる", 13.5, True, WHITE)],
                                 align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
spread = ["① 一つの施設の中で解決する", "② 大学と関連病院をつないで解決する",
          "③ 複数の大学・基幹病院をつないで解決する", "④ エリア全体へ広げて解決する"]
card(s, 6.9, 5.33, 5.85, 1.5,
     [P([R(l, 11, i2 >= 2, INK)], line=1.2, space_after=6) for i2, l in enumerate(spread)],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.15)

# ================================================================ 34 付録E 4S参考例×3
s = add_slide()
header(s, "APPENDIX E", "参考：4Sへつなげる思考プロセスの例", kcolor=GRAY)
txt(s, 0.6, 1.5, 12.15, 0.3,
    [P([R("以下は参考例です。同じ情報から異なる仮説・解決策も考えられます。どのFactからどの仮説を立てたかを見てください。", 11.5, True, DEEP)],
       align=PP_ALIGN.CENTER)])
ex_titles = [("例1：関連病院向け勉強会", NAVY), ("例2：全国発信", GOLD), ("例3：腎病理教育", GREEN)]
for i, (t, col) in enumerate(ex_titles):
    card(s, 1.7 + i * 3.72, 1.88, 3.62, 0.36, [P([R(t, 11, True, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.08)
rows = [("起点", 0.66, GRAY,
         ["Fact：進行後の紹介が多く、施設で時期に差\nWants：関連病院向けに勉強会を",
          "Fact：症例・研究実績はあるが発表は一部に限定\nWants：医局の活動を全国へ",
          "Fact：病理評価が少数医師に集中\nWants：若手に腎病理を学ばせたい"]),
        ("仮説", 0.52, RED,
         ["紹介判断の考え方を共有し、適切な時期につなぎたい",
          "存在価値を高め、若手の成長機会と人脈を広げたい",
          "診断の質と、将来の診療・教育体制を維持したい"]),
        ("質問", 0.52, NAVY2,
         ["勉強会の後、関連病院の何が変わってほしいですか？",
          "全国に最も伝えたい医局の強みは何ですか？",
          "どのレベルまで判断できる状態を目指しますか？"]),
        ("Success", 0.52, RED,
         ["相談・紹介の考え方が、大学と関連病院で共有されている",
          "強みが認知され、若手も含め継続的に発信している",
          "複数の医師が病理所見を臨床と統合して検討できる"]),
        ("Situation", 0.52, GRAY,
         ["進行後の紹介が多く、施設ごとに紹介時期が異なる",
          "実績はあるが、発信する医師と機会が限られている",
          "評価が少数に集中し、若手の教育機会が少ない"]),
        ("Source", 0.52, NAVY,
         ["紹介の目安が共有されず、相談の時期を判断しにくい",
          "テーマ整理・若手育成・外部との接点が不足",
          "継続的に振り返る場と、臨床と病理をつなぐ機会が不足"]),
        ("Solution", 0.62, GREEN,
         ["一方向の講演ではなく、症例で相談時期を議論する場を設計",
          "若手・中堅も含め、近隣大学・基幹病院と共同で発信機会を設計",
          "病理医・臨床医・関連病院の若手による継続的な症例検討を設計"])]
y = 2.3
for t, h, col, cells in rows:
    card(s, 0.6, y, 1.02, h, [P([R(t, 9.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.06)
    for j, c in enumerate(cells):
        paras = [P([R(seg, 9, False, INK)], line=1.12) for seg in c.split("\n")]
        card(s, 1.7 + j * 3.72, y, 3.62, h, paras,
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE, radius=0.04, pad=0.09)
    y += h + 0.055

# ================================================================ 35 付録F ファシリテーター用メモ
s = add_slide()
header(s, "APPENDIX F", "ファシリテーター用メモ", kcolor=GRAY)
tips = [("当日の進行",
         ["0-10 振り返り＋Triple Win Beyond／10-25 ワーク①＋意義",
          "25-40 ワーク②＋4S／40-50 インタビュー／50-60 まとめ・総括",
          "レクチャーは合計20分。ワークと共有に30分を残す"]),
        ("ワーク①・ワーク②",
         ["ワーク①前半4分：例題9件を仕分け（15枚目の欄に番号）",
          "ワーク①後半6分：WantsからNeedsを汲み取った経験を共有",
          "ワーク②：20枚目の例を残したまま、21枚目の4Sに書き切る"]),
        ("付録の使い方",
         ["付録A〜Dは、ワーク①の後に投影してよい（考える材料）",
          "付録E（4S参考例）はワーク前に投影しない — なぞってしまうため",
          "使うのは、ワーク②後の解説／議論が止まった時／研修後の自己学習",
          "「例が正しいのではなく、どのFactからどの仮説を立てたかを見る」"]),
        ("記録・書記",
         ["17・21・24枚目が記録用スライド（そのまま入力可）",
          "ワーク①はWants／Needs／変化の3列で拾う",
          "終了後、記録用スライドをTeamsへ格納"])]
for i, (t, lines) in enumerate(tips):
    x = 0.6 + (i % 2) * 6.15
    y = 1.9 + (i // 2) * 2.5
    card(s, x, y, 6.0, 0.55, [P([R(t, 14, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GRAY, radius=0.12)
    card(s, x, y + 0.6, 6.0, 1.8,
         [P([R("・" + l, 11, False, INK)], space_after=7, line=1.2) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
txt(s, 4.35, 6.9, 8.4, 0.3,
    [P([R("ワーク①の題材・付録の事例はすべて架空です。", 11, False, GRAY)])])

# ---------------------------------------------------------------- save
prs.save(OUT)
print("saved:", OUT, "| slides:", len(prs.slides._sldIdLst))
