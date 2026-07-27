# -*- coding: utf-8 -*-
"""
Renal MR スキルアッププロジェクト DAY4
「ちょっと分かるだけで世界が変わる」

DAY4_base_1-7.pptx（既存の冒頭7枚：表紙・Agenda・お気持ち・概要・ゴール・
メンバー・今後の流れ）はそのまま保持し、8枚目以降を生成する。

設計方針（企画ミーティングの内容を反映）
 - DAY4は知識を「増やす」回ではなく「使う」回
 - 大学攻略 ≠ 担当範囲の攻略。大学という「かご」を外し、任された範囲の中に大学を置き直す
 - 大学の機能（診療/研究/教育/医局人事/医師派遣/情報発信/講演会）から目的に合うものを選ぶ
 - 情報は目的・仮説から逆算して取りに行く
 - 「要望に応える活動」から「範囲の課題から大学を動かす活動」へ
 - 4Sは目的ではなく手段。整った4Sより「なぜ重要か」を語れること
 - 前半＝基本（全員のベースアップ）／後半＝Beyond（視座を上げるプラス1）
 - 構成：オープニング5分／レクチャー&ワーク①25分／同②25分／エリア戦略・まとめ5分
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

BASE = "/home/user/Claude/novartis_training/DAY4_base_1-7.pptx"
OUT  = "/home/user/Claude/novartis_training/DAY4_ちょっと分かるだけで世界が変わる.pptx"
KEEP = 7   # 冒頭7枚は変更しない

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

# ---------------------------------------------------------------- base deck
prs = Presentation(BASE)
_sld = prs.slides._sldIdLst
for sl in list(_sld)[KEEP:]:
    rId = sl.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    prs.part.drop_rel(rId)
    _sld.remove(sl)

BLANK = None
for m in prs.slide_masters:
    for lay in m.slide_layouts:
        if len(lay.placeholders) == 0:
            BLANK = lay
            break
    if BLANK is not None:
        break
if BLANK is None:
    BLANK = prs.slide_masters[0].slide_layouts[6]

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

def conn(s, x1, y1, x2, y2, color=GRAY, weight=1.5, dash=None):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                               Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(weight); c.shadow.inherit = False
    if dash:
        ln = c.line._get_or_add_ln()
        ln.append(ln.makeelement(qn('a:prstDash'), {'val': dash}))
    return c

PAGE = [KEEP]
FOOT = "Renal MR スキルアッププロジェクト DAY4｜ちょっと分かるだけで世界が変わる"

def footer(s, dark=False):
    PAGE[0] += 1
    txt(s, 2.8, 7.14, 7.4, 0.3, [P([R(FOOT, 9, False, MINT if dark else GRAY)])])
    txt(s, 12.2, 7.12, 0.55, 0.3,
        [P([R(str(PAGE[0]), 10, True, MINT if dark else GREEN)], align=PP_ALIGN.RIGHT)])

def header(s, kicker, title, time=None, kcolor=GREEN, lead=None):
    label = kicker + (("　｜　" + time) if time else "")
    chip(s, 0.6, 0.34, chip_w(label), 0.42, label, fill=kcolor)
    txt(s, 0.6, 0.86, 12.2, 0.66, [P([R(title, 25, True, DEEP)])])
    if lead:
        txt(s, 0.6, 1.56, 12.2, 0.42, [P([R(lead, 13.5, True, INK)])])
    footer(s)

def section(s, no, title, subtitle, bullets):
    shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
    shape(s, 0, 0, 13.333, 0.55, fill=DEEP2, kind=MSO_SHAPE.RECTANGLE)
    txt(s, 0.95, 2.2, 2.4, 1.7, [P([R(no, 92, True, RGBColor(0x1D, 0x74, 0x51))])])
    txt(s, 3.35, 2.0, 9.3, 0.5, [P([R(subtitle, 15, True, MINT)])])
    txt(s, 3.35, 2.5, 9.3, 1.1, [P([R(title, 35, True, WHITE)])])
    for i, b in enumerate(bullets):
        circle(s, 3.4, 4.3 + i * 0.78, 0.44, str(i + 1), fill=YELL, size=13, color=DEEP)
        txt(s, 4.05, 4.38 + i * 0.78, 8.6, 0.55, [P([R(b, 15, False, WHITE)], line=1.15)])
    footer(s, dark=True)

# ================================================================ 8 Agenda
s = add_slide()
header(s, "AGENDA", "本日の進め方 — 大きく4つのブロックです")
blocks = [
    ("■ オープニング", "5分", "第1〜3回で、あなたは何が変わりましたか？／今日の位置づけ", GREEN),
    ("■ レクチャー&ワーク①「構造マップ」", "25分", "大学の枠を一度外し、任された範囲全体を1枚の図に描く", NAVY),
    ("■ レクチャー&ワーク②「4Sシート」", "25分", "その情報を何のために使うのか。成功像から逆算して言語化する", NAVY),
    ("■ エリア戦略・まとめ", "5分", "Beyond：影響を広げる／自分の範囲に責任を持つ", GREEN),
]
y = 1.95
for t, tm, d, col in blocks:
    card(s, 0.6, y, 6.6, 1.02, [P([R(t, 16, True, WHITE)])], fill=col, radius=0.1, pad=0.2)
    card(s, 7.3, y, 1.15, 1.02, [P([R(tm, 14, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 8.58, y, 4.17, 1.02, [P([R(d, 11.5, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 1.16
card(s, 0.6, 6.42, 12.15, 0.55,
     [P([R("今日は「レクチャー→すぐワーク」を2セット。", 13.5, True, DEEP),
         R("　手を動かす時間を長く取っています。巻末に持ち帰り用の付録があります。", 13, False, INK)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 9 今日は「使う回」
s = add_slide()
header(s, "TODAY'S DESIGN", "第4回は、知識を「増やす」回ではなく「使う」回です")
card(s, 0.6, 1.85, 5.5, 0.6,
     [P([R("第1〜3回で、手に入れたもの", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
got = ["大学・基幹病院の構造と役割が分かる", "医師に会える／会う工夫ができる",
       "必要な情報を集められる", "医師・施設の関係性と影響力が読める"]
y = 2.55
for g in got:
    card(s, 0.6, y, 5.5, 0.62, [P([R("✔　" + g, 12.5, False, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.7
arrow(s, 6.35, 3.55, 0.6, 0.55, color=GOLD)
card(s, 7.2, 1.85, 5.55, 0.6,
     [P([R("第4回で、考えること", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.1)
card(s, 7.2, 2.55, 5.55, 2.72,
     [P([R("その情報を、", 20, True, INK)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("何のために、どう使うのか", 22, True, RED)], align=PP_ALIGN.CENTER, space_after=12),
      P([R("大学を訪問できる。教授や医局長の役割が分かる。情報も集まる。\nそこで終わらせず、その情報を活動と戦略に変える。", 12.5, False, INK)],
        align=PP_ALIGN.CENTER, line=1.3)],
     fill=RPALE, line=RED, radius=0.08, pad=0.2)
card(s, 0.6, 5.6, 12.15, 1.2,
     [P([R("今日は「大学に行けるようになった」ことを前提に、その一段先へ進みます。", 16, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("新しい知識を足すのではなく、すでに持っている情報の", 13.5, False, INK),
         R("使い道を、自分で決められるようになる", 13.5, True, RED),
         R("のがゴールです。", 13.5, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1, pad=0.2)

# ================================================================ 10 チェックイン
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, 2.4, 0.42, "CHECK IN", fill=GREEN)
txt(s, 0.6, 0.9, 12.2, 0.8, [P([R("この3回で、あなたは何が変わりましたか？", 30, True, DEEP)])])
txt(s, 0.6, 1.78, 12.2, 0.4,
    [P([R("「何を学んだか」ではなく、「自分がどう変わったか」を思い出してください。", 13.5, True, INK)])])
qs = [("大学の「見方」は変わった？", "以前と今で、大学という場所の見え方は？"),
      ("訪問への不安は減った？", "医局に入るとき、以前より足取りは軽い？"),
      ("担当者としての自信は？", "「自分は大学担当だ」と言えるようになった？"),
      ("実際の行動は変わった？", "会う相手・聞くこと・準備の仕方は変わった？")]
for i, (q, d) in enumerate(qs):
    x = 0.6 + (i % 2) * 6.15
    y = 2.3 + (i // 2) * 1.3
    circle(s, x, y + 0.2, 0.72, "0" + str(i + 1), fill=GREEN, size=15)
    card(s, x + 0.9, y, 5.25, 1.12,
         [P([R(q, 15, True, DEEP)], space_after=5),
          P([R(d, 11.5, False, GRAY)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
card(s, 3.5, 5.15, 6.35, 0.68,
     [P([R("一番変わったことを1つ、チャットに書いてください", 15, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.15)
card(s, 0.6, 6.05, 12.15, 0.85,
     [P([R("変化が思い浮かばなくても大丈夫です。", 13, True, INK),
         R("「まだここが不安」も立派な出発点 — それが今日のワークの材料になります。", 13, False, INK)],
       align=PP_ALIGN.CENTER, space_after=4),
      P([R("今日は「大学に行けるようになった」その先を扱います。", 12, False, GRAY)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, radius=0.1, pad=0.16)
footer(s)

# ================================================================ 11 今日いちばん大事な問い
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.4, 3.1, 0.42, "THE QUESTION", fill=YELL, color=DEEP)
txt(s, 0.6, 1.15, 12.2, 1.7,
    [P([R("大学を攻略すれば、", 34, True, WHITE)], space_after=6),
     P([R("あなたの範囲の課題は、すべて解決しますか？", 34, True, YELL)])])
card(s, 0.6, 3.3, 12.15, 0.75,
     [P([R("大学を攻略することと、任された範囲全体を攻略することは、同じではありません。", 17, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=MINT, radius=0.1)
facts = [("地域で違う", "大学が強い地域もあれば、基幹病院のほうが症例数・影響力を持つ地域もある"),
         ("疾患で違う", "その疾患の患者さんがどこにいるかで、効く施設は変わる"),
         ("都市部では", "複数の大学があり、1つの大学だけで範囲全体が動くわけではない")]
for i, (t, d) in enumerate(facts):
    x = 0.6 + i * 4.09
    card(s, x, 4.3, 3.9, 1.35,
         [P([R(t, 15, True, YELL)], align=PP_ALIGN.CENTER, space_after=6),
          P([R(d, 12, False, WHITE)], line=1.3)],
         fill=DEEP2, radius=0.1, pad=0.18)
card(s, 0.6, 5.9, 12.15, 0.95,
     [P([R("今日のゴールは「大学の攻略法」を覚えることではありません。", 14, False, WHITE)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("自分の任された範囲を見渡し、その中で大学をどう使うかを、自分で決められるようになることです。", 15, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP2, radius=0.1, pad=0.18)
footer(s, dark=True)

# ================================================================ 12 SECTION 01
s = add_slide()
section(s, "01", "大学の枠を外して、範囲全体を描く", "レクチャー&ワーク①｜構造マップ　25分",
        ["大学という「かご」を、一度取り払う",
         "任された範囲全体の中に、大学を置き直す",
         "施設の大きさと役割は、自分の目で決める"])

# ================================================================ 13 かごを取り払う
s = add_slide()
header(s, "LECTURE ①", "視点を入れ替える — 「かご」を取り払う", "25分", kcolor=NAVY,
       lead="大学の中から周囲を見るのではなく、任された範囲の中に大学を置き直してみましょう。")
card(s, 0.6, 2.1, 5.8, 0.62,
     [P([R("これまで：大学の中から、周りを見る", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
card(s, 0.6, 2.8, 5.8, 2.5,
     [P([R("・視点の中心は「大学」", 12.5, False, INK)], space_after=9),
      P([R("・成功像は、大学内の採用・処方・面会・講演会になりやすい", 12.5, False, INK)], space_after=9, line=1.25),
      P([R("・大学から依頼されたことに応える活動になりやすい", 12.5, False, INK)], space_after=9, line=1.25),
      P([R("・大学を攻略すれば解決する、という前提に立ちやすい", 12.5, False, INK)], line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
arrow(s, 6.62, 3.6, 0.65, 0.6, color=GOLD)
card(s, 7.5, 2.1, 5.25, 0.62,
     [P([R("これから：範囲の中に、大学を置く", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
card(s, 7.5, 2.8, 5.25, 2.5,
     [P([R("・視点の中心は「自分の任された範囲」", 12.5, True, INK)], space_after=9, line=1.25),
      P([R("・成功像は、範囲全体がどうなっているか", 12.5, True, INK)], space_after=9, line=1.25),
      P([R("・大学は、その成功像を実現するために使える資源の一つ", 12.5, True, INK)], space_after=9, line=1.25),
      P([R("・大学が中心とは限らない。基幹病院が中心の範囲もある", 12.5, True, INK)], line=1.25)],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 5.55, 12.15, 1.3,
     [P([R("表面的には、同じ「教授面会」「講演会」でも —", 15, True, DEEP)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("大学だけを見て実施した活動と、範囲全体を見て大学を活用した活動では、", 13.5, False, INK),
         R("意味も成果の質もまったく違います。", 13.5, True, RED)], align=PP_ALIGN.CENTER, line=1.25)],
     fill=YPALE, radius=0.1, pad=0.2)

# ================================================================ 14 大学の7つの機能
s = add_slide()
header(s, "LECTURE ①", "大学の「どの機能」を使いますか？", "25分", kcolor=NAVY,
       lead="大学の影響力を全部使う必要はありません。目的に合う機能を、選んで使います。")
funcs = [("診療", "症例が集まる。専門治療の実施と評価の場", GREEN),
         ("研究", "エビデンスをつくる。学会・論文で外へ届く", GREEN),
         ("教育", "若手が学び、数年後にエリアへ散っていく", GREEN),
         ("医局人事", "関連病院の部長・医長を決める。方針が波及する", NAVY),
         ("医師派遣", "誰がどの施設に行くか。エリアの布陣が決まる", NAVY),
         ("情報発信", "治療方針が、時間差でエリアの標準になる", GOLD),
         ("講演会・研究会", "地域の医師が集まる場。共通認識をつくれる", GOLD)]
for i, (t, d, col) in enumerate(funcs):
    x = 0.6 + (i % 4) * 3.12
    y = 2.15 + (i // 4) * 1.5
    card(s, x, y, 2.95, 0.5, [P([R(t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, x, y + 0.55, 2.95, 0.85, [P([R(d, 11, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
card(s, 10.0, 3.65, 2.75, 1.4,
     [P([R("この7つのうち、", 12.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("あなたの課題を解くのに\n必要なのはどれ？", 13.5, True, YELL)], align=PP_ALIGN.CENTER, line=1.25)],
     fill=DEEP, radius=0.1, pad=0.14)
card(s, 0.6, 5.4, 12.15, 1.4,
     [P([R("「大学を攻略する」ではなく、「この課題を解くために、大学のこの機能を使う」と言えるか。", 15.5, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=7),
      P([R("例：範囲の紹介が遅い → 使うのは", 13, False, INK), R("「情報発信」と「講演会」", 13, True, RED),
         R("。　例：基幹病院の治療方針を変えたい → 使うのは", 13, False, INK),
         R("「医局人事」と「医師派遣」", 13, True, RED), R("。", 13, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=PALE, radius=0.1, pad=0.2)

# ================================================================ 15 構造マップの描き方
s = add_slide()
header(s, "LECTURE ①", "構造マップの描き方 — 任された範囲を、1枚の図にする", "25分", kcolor=NAVY)
shape(s, 0.6, 1.8, 8.35, 5.05, fill=PALE2, line=GREEN, radius=0.02)
txt(s, 0.8, 1.9, 5.0, 0.32, [P([R("私の任された範囲（例：◯◯県／◯◯エリア）", 11.5, True, GREEN)])])
circle(s, 1.55, 2.55, 1.75, "A大学\n腎臓内科", fill=PALE, line=DEEP, size=12, color=DEEP, wrap=True)
circle(s, 4.35, 2.75, 1.35, "B基幹病院", fill=PALEB, line=NAVY, size=11.5, color=NAVY, wrap=True)
circle(s, 6.55, 2.35, 1.05, "C大学", fill=PALE, line=GREEN2, size=11, color=DEEP, wrap=True)
circle(s, 1.95, 4.95, 1.1, "D市中病院", fill=WHITE, line=GRAY, size=10.5, color=INK, wrap=True)
circle(s, 4.05, 5.15, 0.85, "E病院", fill=WHITE, line=GRAY, size=10.5, color=INK, wrap=True)
for i in range(3):
    circle(s, 6.15 + i * 0.6, 4.95 + (i % 2) * 0.35, 0.55, "CL", fill=WHITE, line=LGRAY, size=9, color=GRAY)
txt(s, 6.05, 5.75, 2.4, 0.3, [P([R("クリニック群", 10, False, GRAY)], align=PP_ALIGN.CENTER)])
conn(s, 2.5, 4.3, 2.5, 4.95, color=GREEN, weight=2.2)
conn(s, 3.25, 3.4, 4.35, 3.4, color=GREEN, weight=2.2)
conn(s, 5.05, 4.1, 4.45, 5.15, color=GREEN, weight=1.8)
conn(s, 5.7, 3.4, 6.6, 3.4, color=NAVY, weight=1.6, dash="dash")
conn(s, 3.0, 2.6, 6.55, 2.6, color=NAVY, weight=1.6, dash="dash")
conn(s, 5.3, 4.2, 6.5, 4.95, color=GOLD, weight=1.6, dash="sysDot")
conn(s, 2.9, 4.5, 6.15, 5.2, color=GOLD, weight=1.6, dash="sysDot")
card(s, 0.75, 6.28, 8.05, 0.44,
     [P([R("　患者の流れ　", 10, True, GREEN), R("／", 10, False, GRAY),
         R("　医師の人事・派遣（破線）　", 10, True, NAVY), R("／", 10, False, GRAY),
         R("　情報・診療方針の流れ（点線）", 10, True, GOLD)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=LGRAY, radius=0.2)
card(s, 9.2, 1.8, 3.55, 2.35,
     [P([R("描くもの", 13.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("・大学／基幹病院／その他の施設", 11.5, False, WHITE)], space_after=6, line=1.2),
      P([R("・重要な医師（誰が動かすか）", 11.5, False, WHITE)], space_after=6, line=1.2),
      P([R("・患者の流れ（紹介・逆紹介）", 11.5, False, WHITE)], space_after=6, line=1.2),
      P([R("・医師の人事・派遣", 11.5, False, WHITE)], space_after=6, line=1.2),
      P([R("・情報／診療方針の流れ", 11.5, False, WHITE)], space_after=6, line=1.2),
      P([R("・各施設の影響が及ぶ範囲", 11.5, False, WHITE)], line=1.2)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.18)
card(s, 9.2, 4.3, 3.55, 2.55,
     [P([R("描き方のルール", 13.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("・丸の大きさ＝あなたが考える重要度", 11.5, True, INK)], space_after=8, line=1.2),
      P([R("・大学を一番大きく描く必要はない", 11.5, True, RED)], space_after=8, line=1.2),
      P([R("・きれいな図でなくてよい。手描きの丸と矢印で十分", 11.5, False, INK)], space_after=8, line=1.2),
      P([R("・正解の型はない。人によって違う図になる", 11.5, False, INK)], line=1.2)],
     fill=YPALE, line=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.18)
card(s, 9.2, 4.3, 3.55, 0.42, [P([R("描き方のルール", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GOLD, radius=0.5)

# ================================================================ 16 4パターン
s = add_slide()
header(s, "LECTURE ①", "全員が同じ図になる必要はありません", "25分", kcolor=NAVY,
       lead="地域や施設構成によって、大学と基幹病院の関係はまったく違います。")
pats = [("① 一つの大学が中心", [("A大", 1.15, 1.05, 0.5, PALE, DEEP), ("基幹", 0.62, 2.1, 1.35, WHITE, GRAY),
                            ("基幹", 0.62, 0.35, 1.45, WHITE, GRAY)]),
        ("② 複数の大学が並ぶ", [("A大", 0.95, 0.5, 0.55, PALE, DEEP), ("B大", 0.95, 1.75, 1.15, PALE, GREEN2),
                            ("基幹", 0.6, 1.35, 0.35, WHITE, GRAY)]),
        ("③ 基幹病院が中心", [("基幹", 1.2, 0.95, 0.55, PALEB, NAVY), ("A大", 0.7, 0.4, 1.55, PALE, DEEP),
                          ("CL群", 0.6, 2.15, 1.5, WHITE, GRAY)]),
        ("④ 大学の影響が広域に", [("A大", 1.1, 0.5, 0.5, PALE, DEEP), ("県外", 0.65, 2.0, 0.45, WHITE, GRAY),
                            ("県外", 0.65, 2.1, 1.5, WHITE, GRAY)])]
notes = ["大学の方針が範囲全体に波及する。医局人事と情報発信が効く",
         "1大学では範囲は動かない。両大学に共通する課題を探す",
         "症例数・実務の影響力は基幹病院。大学は研究・教育で効かせる",
         "先生の影響が担当範囲を超える。営業所・全国への展開を考える"]
for i, ((t, circles), note) in enumerate(zip(pats, notes)):
    x = 0.6 + i * 3.12
    card(s, x, 2.1, 2.95, 0.5, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
         fill=[GREEN, NAVY, GOLD, RED][i], radius=0.12)
    shape(s, x, 2.65, 2.95, 2.5, fill=PALE2, line=LGRAY, radius=0.04)
    for lbl, d, dx, dy, fc, lc in circles:
        circle(s, x + dx, 2.85 + dy, d, lbl, fill=fc, line=lc,
               size=10 if d > 0.9 else 8.5, color=lc)
    card(s, x, 5.25, 2.95, 1.1, [P([R(note, 11, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
card(s, 0.6, 6.5, 12.15, 0.42,
     [P([R("大事なのは正しい図を描くことではなく、", 12.5, False, INK),
         R("「自分は任された範囲をこう見ている」を可視化すること", 12.5, True, RED),
         R("です。", 12.5, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 17 ワーク①
s = add_slide()
header(s, "WORK ①", "自分の任された範囲を、1枚の図に描く", "10分", kcolor=GREEN)
card(s, 0.6, 1.8, 8.05, 0.72,
     [P([R("手元の紙に、あなたの担当範囲を描いてください。上手さは関係ありません。", 14, True, INK)])],
     fill=PALE, radius=0.08, pad=0.16)
steps = [("4分", "施設を丸で置く", "大学・基幹病院・その他。丸の大きさ＝あなたが考える重要度"),
         ("3分", "矢印を引く", "患者の流れ／医師の人事・派遣／情報・診療方針の流れ"),
         ("3分", "大学の丸に機能を書く", "診療・研究・教育・医局人事・医師派遣・情報発信・講演会から選ぶ")]
y = 2.7
for tm, t, d in steps:
    circle(s, 0.6, y, 0.7, tm, fill=GREEN, size=12)
    card(s, 1.5, y, 7.15, 0.7,
         [P([R(t + "　", 13, True, DEEP), R(d, 11, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.85
card(s, 0.6, 5.3, 8.05, 1.5,
     [P([R("描き終えたら、自分に問いかけてください。", 13.5, True, INK)], space_after=6),
      P([R("あなたの図で、大学は何番目に大きいですか？", 18, True, RED)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("一番大きくなくても、まったく問題ありません。それがあなたの範囲の実態です。", 12, False, GRAY)])],
     fill=YPALE, radius=0.08, pad=0.2)
card(s, 8.9, 1.8, 3.85, 5.0,
     [P([R("迷ったときは", 14.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=12),
      P([R("・施設が多すぎる → 重要そうな5〜6施設だけでOK", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・重要度が決められない → 「この施設が変わったら、範囲全体が変わるか？」で判断", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・矢印が分からない → 分からない線は点線＋「？」で描く。それが次に取りに行く情報", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・大学が複数ある → 全部描く。関係が分からなければ、それも「？」", 11.5, False, WHITE)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06, pad=0.2)

# ================================================================ 18 共有①
s = add_slide()
header(s, "SHARE ①", "共有：あなたの範囲を、他の人に説明する", "5分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.75,
     [P([R("3〜4人1組。1人1分で、自分の図を見せながら説明します。", 15, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
card(s, 0.6, 2.9, 6.0, 0.55, [P([R("話す人（1分）", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
card(s, 0.6, 3.52, 6.0, 2.2,
     [P([R("この型で話してみてください：", 12.5, True, INK)], space_after=8),
      P([R("「私の範囲は◯◯が中心です。大学は△△の機能で効いています。いま一番動かしたいのは□□です」", 12.5, False, INK)],
        line=1.35, space_after=8),
      P([R("→ 大学が一番大きくない人は、その理由も添えてください。", 12, True, GREEN)], line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 6.75, 2.9, 6.0, 0.55, [P([R("聞く人", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
card(s, 6.75, 3.52, 6.0, 2.2,
     [P([R("質問はこの1つだけ：", 12.5, True, INK)], space_after=8),
      P([R("「なぜ、その施設が一番大きいのですか？」", 14, True, NAVY)], space_after=8, line=1.25),
      P([R("答えに詰まったら、それは重要度の根拠がまだ言語化されていないということ。批判ではなく、深めるための質問です。", 11.5, False, GRAY)],
        line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 5.95, 12.15, 0.9,
     [P([R("他の人の図は、最高の教材です。", 14.5, True, DEEP)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("「大学が中心じゃない範囲もあるのか」「その施設の見方があったか」— 自分の図の空白が見えてきます。", 12.5, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 19 SECTION 02
s = add_slide()
section(s, "02", "その情報は、何のために使うのか", "レクチャー&ワーク②｜4Sシート　25分",
        ["情報は、目的と仮説から逆算して取りに行く",
         "「要望に応える活動」から「課題から動かす活動」へ",
         "4Sは目的ではなく、自分の考えを整理する手段"])

# ================================================================ 20 情報は目的から逆算
s = add_slide()
header(s, "LECTURE ②", "情報は、集めるほど良いわけではありません", "25分", kcolor=NAVY,
       lead="教授の専門、医局員の横のつながり、派遣先、人事、研究内容 — 知ること自体は目的ではありません。")
card(s, 0.6, 2.15, 12.15, 0.62,
     [P([R("よくある順番：", 13, True, WHITE), R("情報を集める", 13, True, WHITE),
         R("　→　", 13, False, WHITE), R("何に使えるか考える", 13, True, WHITE),
         R("　→　集めたけれど活かせない", 13, False, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
flow = [("① 成功像を考える", "任された範囲を、どうしたいのか", GREEN),
        ("② 役割を仮説化する", "大学・基幹病院に、どんな役割が必要か", NAVY),
        ("③ 必要な情報を決める", "その仮説を確かめるには、何を知る必要があるか", NAVY),
        ("④ 情報を取りに行く", "DAY3で学んだドライ／ウェットの方法で", GOLD),
        ("⑤ 仮説と活動を直す", "違っていたら、成功像や打ち手を修正する", RED)]
for i, (t, d, col) in enumerate(flow):
    x = 0.6 + i * 2.47
    card(s, x, 3.15, 2.28, 0.6, [P([R(t, 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 3.83, 2.28, 1.2, [P([R(d, 10.5, False, INK)], line=1.25)],
         fill=PALE2, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.13)
    if i < 4:
        arrow(s, x + 2.31, 3.32, 0.14, 0.26, color=GREEN2)
conn(s, 12.63, 4.3, 12.63, 5.35, color=GREEN2, weight=1.6, dash="dash")
conn(s, 0.9, 5.35, 12.63, 5.35, color=GREEN2, weight=1.6, dash="dash")
arrow(s, 0.78, 4.35, 0.24, 1.0, color=GREEN2, direction="up")
txt(s, 4.4, 5.42, 4.5, 0.3, [P([R("← 回しながら精度を上げる", 10.5, True, GREEN)], align=PP_ALIGN.CENTER)])
card(s, 0.6, 5.85, 12.15, 1.0,
     [P([R("「何のためにその情報が必要なのか」が先にある。", 15.5, True, DEEP)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("範囲をどうしたいかというビジョンと、大学・基幹病院にどんな役割が要るかという仮説があるから、確かめるために情報を取りに行く。", 12.5, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=PALE, radius=0.1, pad=0.18)

# ================================================================ 21 応える活動と動かす活動
s = add_slide()
header(s, "LECTURE ②", "同じ「講演会」でも、価値がまったく違います", "25分", kcolor=NAVY)
card(s, 0.6, 1.85, 6.0, 0.58,
     [P([R("A：要望に応える活動", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GRAY, radius=0.1)
stepsA = ["大学から講演会を依頼された", "依頼どおりに企画・実施した", "大学の要望に応えられた"]
y = 2.55
for i, t in enumerate(stepsA):
    card(s, 0.6, y, 6.0, 0.6, [P([R(t, 12.5, False, INK)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=LGRAY, radius=0.1)
    if i < 2:
        arrow(s, 3.42, y + 0.63, 0.36, 0.24, color=LGRAY, direction="down")
    y += 0.87
card(s, 0.6, 5.2, 6.0, 0.75,
     [P([R("担当者の介入価値が見えにくい", 13, True, GRAY)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GRAY, radius=0.1)
card(s, 6.75, 1.85, 6.0, 0.58,
     [P([R("B：範囲の課題から動かす活動", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GREEN, radius=0.1)
stepsB = ["任された範囲に、この課題がある", "大学・基幹病院にも共通する課題だと分かった",
          "解決には、あの先生からこのメッセージが要る", "そのために講演会を企画する"]
y = 2.55
for i, t in enumerate(stepsB):
    card(s, 6.75, y, 6.0, 0.6, [P([R(t, 12, True, INK)], align=PP_ALIGN.CENTER)],
         fill=PALE, line=GREEN, radius=0.1, pad=0.1)
    if i < 3:
        arrow(s, 9.57, y + 0.63, 0.36, 0.2, color=GREEN2, direction="down")
    y += 0.83
card(s, 6.75, 5.2, 6.0, 0.75,
     [P([R("担当者が課題を捉え、大学を動かした活動", 13, True, GREEN)], align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.1)
card(s, 0.6, 6.05, 12.15, 0.85,
     [P([R("実例：複数の大学がある地域で、一つの大学の要望に応えるのではなく、範囲全体の課題を起点に、各大学の考え方と関係性を踏まえて共通の方向へ乗せた講演会。", 12.5, False, INK)],
       space_after=4, line=1.2),
      P([R("表面上はどちらも「講演会」。違いは、その手前で何を考えたかだけです。", 13, True, RED)])],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 22 4Sは手段
s = add_slide()
header(s, "LECTURE ②", "４Sは目的ではありません。整理するための手段です", "25分", kcolor=NAVY)
card(s, 0.6, 1.9, 6.0, 0.55, [P([R("４Sは、こういうものではない", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=RED, radius=0.12)
nots = ["大学を攻略するための提出物", "きれいに項目を埋めるシート", "大学1施設の成功像をつくるもの"]
y = 2.55
for t in nots:
    card(s, 0.6, y, 6.0, 0.62, [P([R("✕　" + t, 12.5, False, INK)])],
         fill=RPALE, radius=0.1, pad=0.14)
    y += 0.72
card(s, 6.75, 1.9, 6.0, 0.55, [P([R("４Sは、こういうもの", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
oks = ["自分が考えた成功像・課題・原因を整理する道具",
       "大学・基幹病院の役割と、自分の介入点を決めるための道具",
       "次の行動を1つに絞り込むための道具"]
y = 2.55
for t in oks:
    card(s, 6.75, y, 6.0, 0.62, [P([R("○　" + t, 12.5, True, INK)], line=1.2)],
         fill=PALE, radius=0.1, pad=0.14)
    y += 0.72
card(s, 0.6, 4.85, 12.15, 0.85,
     [P([R("戦略は、一点に強く偏っていてもかまいません。", 15, True, DEEP)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("ある先生に特定のメッセージを発信してもらうことが範囲にとって最重要なら、それが戦略の中心になります。", 12.5, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=PALEB, radius=0.1, pad=0.16)
card(s, 0.6, 5.9, 12.15, 0.95,
     [P([R("整った４Sをつくることより、", 17, True, WHITE),
         R("「なぜ、それが重要なのか」を説明できること", 17, True, YELL)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("シートはあくまで、考えを外に出すための一例です。図でも箇条書きでも構いません。", 12, False, MINT)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.16)

# ================================================================ 23 4S+α
s = add_slide()
header(s, "LECTURE ②", "４S ＋ α — 範囲の戦略を、7つの箱で言語化する", "25分", kcolor=NAVY,
       lead="プロジェクトのゴール「担当施設と周辺エリアに対する成功像・現状・課題・解決法を言語化できる」を形にします。")
quads = [(0.6, 2.1, "① 成功像", "任された範囲が、こうなっていたら最高", GREEN, PALE),
         (6.75, 2.1, "② 現状・課題", "成功像とのGAP。どこが、どう詰まっているか", NAVY, PALEB),
         (0.6, 3.75, "③ 原因", "なぜそのGAPがあるのか（なぜ？を3回）", GOLD, YPALE),
         (6.75, 3.75, "④ 解決策", "GAPを埋めるために、何を起こすか", RED, RPALE)]
for x, y, t, d, col, fill in quads:
    card(s, x, y, 6.0, 0.5, [P([R(t + "　", 13.5, True, WHITE), R(d, 10.5, False, WHITE)])],
         fill=col, radius=0.1, pad=0.14)
    card(s, x, y + 0.55, 6.0, 1.02, [P([R("", 10)])], fill=fill, radius=0.1, pad=0.14)
alpha = [("＋ 大学・基幹病院の役割", "どの施設の、どの機能を使うのか", DEEP),
         ("＋ 自分の介入点", "自分にしかできないことは何か", DEEP),
         ("＋ 次の行動", "明日、まず何をするか（1つだけ）", DEEP)]
for i, (t, d, col) in enumerate(alpha):
    x = 0.6 + i * 4.09
    card(s, x, 5.42, 3.9, 0.5, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 5.97, 3.9, 0.62, [P([R(d, 11, False, INK)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=MINT, radius=0.1, pad=0.12)
card(s, 0.6, 6.68, 12.15, 0.4,
     [P([R("①〜④が「範囲をどうしたいか」、＋αが「そのために大学・基幹病院をどう使い、自分が何をするか」です。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 24 記入例
s = add_slide()
header(s, "LECTURE ②", "記入例：複数の大学がある地域（架空の例）", "25分", kcolor=NAVY)
ex = [(0.6, 1.85, "① 成功像", GREEN, PALE,
       "範囲全体で、専門治療が必要な患者さんが、どの地域にいても適切なタイミングで専門医にたどり着いている。"),
      (6.75, 1.85, "② 現状・課題", NAVY, PALEB,
       "紹介が遅い。地域差が大きい。A大学とB大学で治療方針の温度差があり、地域の医師がどちらに合わせるべきか迷っている。"),
      (0.6, 3.6, "③ 原因（なぜ×3）", GOLD, YPALE,
       "なぜ遅い？→紹介の目安が共有されていない →なぜ？→範囲共通の基準がない →なぜ？→両大学が同じ場で話す機会がない。"),
      (6.75, 3.6, "④ 解決策", RED, RPALE,
       "両大学の先生が同席する会を企画し、範囲共通の紹介の目安を、両大学の連名で発信してもらう。")]
for x, y, t, col, fill, d in ex:
    card(s, x, y, 6.0, 0.48, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, y + 0.52, 6.0, 1.0, [P([R(d, 11, False, INK)], line=1.25)],
         fill=fill, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.14)
alpha_ex = [("＋ 大学・基幹病院の役割", "A大学＝情報発信（メッセージの発信源）／B大学＝地域連携の実務／基幹病院C＝受け皿"),
            ("＋ 自分の介入点", "両大学の関係性を踏まえた会の設計と、両医局長への事前相談は、範囲を見ている自分にしかできない"),
            ("＋ 次の行動", "来週、A大学の医局長に「範囲の紹介の遅れ」について相談し、B大学との共催の可能性を確認する")]
y = 4.92
for t, d in alpha_ex:
    card(s, 0.6, y, 3.15, 0.44, [P([R(t, 11.5, True, WHITE)])], fill=DEEP, radius=0.1, pad=0.12)
    card(s, 3.9, y, 8.85, 0.44, [P([R(d, 11, False, INK)])], fill=MINT, radius=0.1, pad=0.12)
    y += 0.5
card(s, 0.6, 6.5, 12.15, 0.42,
     [P([R("注目：この会は「大学から頼まれた会」ではありません。範囲の課題から逆算して、担当者が設計した会です。", 12, True, RED)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.15)

# ================================================================ 25 ワーク②
s = add_slide()
header(s, "WORK ②", "構造マップを、４S＋αに翻訳する", "10分", kcolor=GREEN)
card(s, 0.6, 1.8, 8.05, 0.75,
     [P([R("さきほど描いた図を横に置いて、範囲の戦略を言葉にします。完璧でなくて構いません。", 14, True, INK)], line=1.2)],
     fill=PALE, radius=0.08, pad=0.16)
steps = [("3分", "①成功像 ②現状・課題", "図を見ながら「範囲がどうなっていたら最高か」から書く"),
         ("3分", "③原因", "「なぜ？」を3回。人・関係性・場・情報の4方向で探す"),
         ("4分", "＋α（役割・介入点・次の行動）", "どの施設のどの機能を使うか。自分にしかできないことは何か")]
y = 2.75
for tm, t, d in steps:
    circle(s, 0.6, y, 0.7, tm, fill=GREEN, size=12)
    card(s, 1.5, y, 7.15, 0.7,
         [P([R(t, 12.5, True, DEEP)], space_after=2), P([R(d, 10.5, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.85
card(s, 0.6, 5.35, 8.05, 1.45,
     [P([R("合言葉：整った４Sより、語れる４S。", 17, True, RED)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("空欄があってもかまいません。偏っていてもかまいません。1つでも「これが重要だ」と言い切れる箱があれば、今日は成功です。", 12, False, INK)],
        line=1.25)],
     fill=YPALE, radius=0.08, pad=0.2)
card(s, 8.9, 1.8, 3.85, 5.0,
     [P([R("手が止まったら", 14.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=12),
      P([R("・成功像が出ない → 「1年後、上司に自慢したい範囲の姿」を想像する", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・課題が出ない → 図の中で詰まっている矢印を探す（紹介・人事・情報）", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・原因が浅い → 「それでもうまくいっている地域があるのはなぜ？」と自問する", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・役割が決まらない → 大学の7つの機能に戻り、必要なものを1つだけ選ぶ", 11.5, False, WHITE)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06, pad=0.2)

# ================================================================ 26 共有②
s = add_slide()
header(s, "SHARE ②", "共有：「なぜ、それが重要なのか」を語る", "5分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.72,
     [P([R("3〜4人1組。1人1分半。シートを読み上げるのではなく、自分の言葉で語ってください。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
card(s, 0.6, 2.85, 12.15, 1.35,
     [P([R("語り方の型", 13, True, WHITE)], align=PP_ALIGN.CENTER, space_after=7),
      P([R("「私の範囲は ", 15, False, WHITE), R("◯◯", 15, True, YELL),
         R(" が課題です。原因は ", 15, False, WHITE), R("△△", 15, True, YELL),
         R("。だから ", 15, False, WHITE), R("□□先生", 15, True, YELL),
         R(" に ", 15, False, WHITE), R("◇◇", 15, True, YELL),
         R(" してもらいます。そのために私は ", 15, False, WHITE), R("☆☆", 15, True, YELL),
         R(" をします」", 15, False, WHITE)], align=PP_ALIGN.CENTER, line=1.3)],
     fill=DEEP, radius=0.1, pad=0.18)
card(s, 0.6, 4.4, 6.0, 0.55, [P([R("聞き手が聞く質問（1つだけ）", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
card(s, 0.6, 5.02, 6.0, 1.6,
     [P([R("「なぜ、それが重要なのですか？」", 15, True, NAVY)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("答えられれば、その戦略はもう自分のものです。詰まったら、そこが次に考えるところ。", 11.5, False, INK)],
        line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 6.75, 4.4, 6.0, 0.55, [P([R("この共有のねらい", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
card(s, 6.75, 5.02, 6.0, 1.6,
     [P([R("・他の人の範囲の見方を知る（アンケート期待1位）", 11.5, False, INK)], space_after=7, line=1.2),
      P([R("・自分の戦略を、声に出して確かめる", 11.5, False, INK)], space_after=7, line=1.2),
      P([R("・「大学の使い方」の引き出しを、全員で増やす", 11.5, False, INK)], line=1.2)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 6.7, 12.15, 0.4,
     [P([R("上手に語れなくて当然です。今日はじめて考えたことなので、詰まった箇所が持ち帰りの宿題になります。", 12, True, GRAY)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 27 SECTION 03
s = add_slide()
section(s, "03", "そして、その先へ　Beyond", "エリア戦略・まとめ　5分",
        ["影響の輪：目の前の先生は、どこまで届くのか",
         "「この範囲は自分に任せてください」と言える状態へ",
         "会社の方針の中でも、自分の戦略を持つ"])

# ================================================================ 28 Beyond 影響の輪
s = add_slide()
header(s, "BEYOND", "影響の輪 — 得た情報とメッセージを、どこまで届けるか", kcolor=GOLD,
       lead="ここからは発展的な視点です。全員が今日到達する必要はありません。持ち帰ってみてください。")
rings = [("施設の中", 4.5, GREEN2), ("関連病院", 3.55, GREEN), ("担当範囲", 2.6, NAVY2), ("営業所・営業部", 1.65, NAVY)]
cx, cy = 3.5, 4.35
for label, d, col in rings:
    shape(s, cx - d / 2, cy - d / 2, d, d, fill=None, line=col, line_w=1.6, kind=MSO_SHAPE.OVAL)
for label, d, col in rings:
    txt(s, cx - 1.0, cy - d / 2 + 0.06, 2.0, 0.26,
        [P([R(label, 10, True, col)], align=PP_ALIGN.CENTER)])
circle(s, cx - 0.38, cy - 0.38, 0.76, "先生", fill=YELL, size=11, color=DEEP)
card(s, 0.75, 6.35, 5.55, 0.55,
     [P([R("※ 大学の先生が、担当範囲を超えて広域・全国に影響を持つこともある", 10.5, True, GRAY)],
       align=PP_ALIGN.CENTER, line=1.15)],
     fill=WHITE, line=LGRAY, radius=0.15)
spread = [("他の大学・基幹病院へ広げる", "同じ課題を持つ施設は、範囲の中に必ずある"),
          ("他の担当MRの活動に活かす", "自分が得た情報は、チームの武器になる"),
          ("講演会・研究会で発信する", "1対1の面会では届かない範囲に、一度に届く"),
          ("疾患啓発へつなげる", "担当範囲を超えて、患者さんの流れそのものを変える")]
y = 2.05
for t, d in spread:
    card(s, 6.9, y, 5.85, 1.05,
         [P([R(t, 13, True, GOLD)], space_after=4),
          P([R(d, 11, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 1.17
card(s, 6.9, 6.35, 5.85, 0.55,
     [P([R("一施設で終わらせない。それが大学担当の価値。", 12.5, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 29 Beyond 目指す状態
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.4, 2.2, 0.42, "BEYOND", fill=YELL, color=DEEP)
txt(s, 0.6, 1.05, 12.2, 0.5, [P([R("大学担当者として、目指す状態", 17, True, MINT)])])
card(s, 0.6, 1.7, 12.15, 1.35,
     [P([R("「この範囲は、自分に任せてください。", 26, True, DEEP)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("そのために、大学をこう使います」", 26, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.1)
txt(s, 0.6, 3.25, 12.2, 0.4,
    [P([R("と、自分の言葉で説明できる状態。そのために、次の5つを自分なりに考えます。", 14, False, WHITE)],
       align=PP_ALIGN.CENTER)])
items = ["どの施設を優先するか", "大学と基幹病院を、どう組み合わせるか", "誰の影響力を使うか",
         "どの情報を、取りに行くか", "どんな施策を打つか"]
for i, t in enumerate(items):
    x = 0.6 + i * 2.47
    card(s, x, 3.85, 2.28, 1.15,
         [P([R("0" + str(i + 1), 15, True, YELL)], align=PP_ALIGN.CENTER, space_after=6),
          P([R(t, 11.5, True, WHITE)], align=PP_ALIGN.CENTER, line=1.2)],
         fill=DEEP2, radius=0.1, pad=0.14)
card(s, 0.6, 5.25, 12.15, 0.85,
     [P([R("一施設の担当者という視点ではなく、営業所・営業部に近い視座で考えてみる。", 15, True, WHITE)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("指示された活動をこなす人ではなく、任された範囲に責任を持ち、活動を設計・提案できる人へ。", 13.5, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP2, radius=0.1, pad=0.16)
card(s, 0.6, 6.25, 12.15, 0.72,
     [P([R("現実には、会社の方針や予算で、最適でない施策を行うこともあります。それでも、自分の範囲を理解していれば", 12, False, MINT),
         R("「予算があるなら、こちらの施策のほうが成果につながります」と提案できる。", 12, True, WHITE)],
       align=PP_ALIGN.CENTER, line=1.25)],
     fill=RGBColor(0x11, 0x63, 0x45), radius=0.1, pad=0.14)
footer(s, dark=True)

# ================================================================ 30 まとめ
s = add_slide()
header(s, "WRAP UP", "本日のまとめ")
msgs = [("01", "大学の攻略が目的ではない",
         "任された範囲を攻略するために、大学を使う。大学が一番大きいとは限らない。", GREEN),
        ("02", "情報は、目的と仮説から逆算する",
         "成功像 → 大学・基幹病院に求める役割の仮説 → 必要な情報 → 取りに行く → 修正。", NAVY),
        ("03", "４Sは手段。語れることが目的",
         "整ったシートより、「なぜそれが重要か」を自分の言葉で説明できること。", GOLD)]
y = 1.95
for no, t, d, col in msgs:
    circle(s, 0.6, y + 0.12, 0.8, no, fill=col, size=16)
    card(s, 1.6, y, 11.15, 1.05,
         [P([R(t, 16, True, col)], space_after=4),
          P([R(d, 12.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.2)
    y += 1.2
card(s, 0.6, 5.6, 12.15, 1.25,
     [P([R("今日の持ち帰りは、これだけで十分です。", 15, True, WHITE)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("一度、大学という枠を外して、自分の範囲を眺めてみる。", 22, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 31 行動宣言
s = add_slide()
header(s, "ACTION", "行動宣言 — 明日からの一手を、1人1行", "5分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 1.05,
     [P([R("今日つくった図とシートから", 17, True, INK),
         R("「明日やること」を1つだけ", 17, True, RED),
         R("選び、チャットに投稿してください", 17, True, INK)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("宣言した瞬間、研修は「聞いた話」から「自分の計画」に変わります", 12.5, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.08, pad=0.18)
ex = [("例①", "「自分の範囲の図で『？』にした線を、来週の面会で1つ確認する」", GREEN),
      ("例②", "「A大学の医局長に、B大学との関係について聞いてみる」", NAVY),
      ("例③", "「描いた図を上司に見せて、施設の優先順位が合っているか相談する」", GOLD)]
y = 3.2
for t, d, col in ex:
    card(s, 0.6, y, 1.5, 0.72, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, 2.2, y, 10.55, 0.72, [P([R(d, 13, False, INK)])], fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 0.85
card(s, 0.6, 5.85, 12.15, 1.0,
     [P([R("コツは「電話1本サイズ」に割ること。", 14.5, True, RED),
         R("　最初の一歩が小さいほど、実行されます。", 13.5, False, INK)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("投稿された宣言と気づきは、事務局が集約し、録画・資料とあわせて全員（欠席者含む）へ共有します。", 12.5, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 32 Thank you
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
txt(s, 1.0, 1.75, 11.3, 1.2, [P([R("ありがとうございました", 42, True, WHITE)])])
txt(s, 1.05, 3.1, 11.3, 0.6,
    [P([R("4回シリーズ、おつかれさまでした。ここからが本番です。", 18, True, MINT)])])
items = [("今日中", "行動宣言と気づきをチャットへ"),
         ("今週", "気づきリスト・録画・テンプレートを事務局から共有"),
         ("これから", "困ったら、全国の仲間に相談を")]
for i, (t, d) in enumerate(items):
    x = 1.0 + i * 3.85
    card(s, x, 4.15, 3.55, 1.15,
         [P([R(t, 14, True, YELL)], align=PP_ALIGN.CENTER, space_after=5),
          P([R(d, 12, False, WHITE)], align=PP_ALIGN.CENTER, line=1.2)],
         fill=DEEP2, radius=0.1, pad=0.15)
txt(s, 1.0, 5.95, 11.3, 0.5,
    [P([R("「この範囲は、自分に任せてください。そのために、大学をこう使います」", 16, True, MINT)])])
footer(s, dark=True)

# ================================================================ 33 付録A 構造マップ
s = add_slide()
header(s, "APPENDIX A", "構造マップ テンプレート（印刷・配布用）", kcolor=GRAY)
shape(s, 0.6, 1.7, 8.9, 4.55, fill=PALE2, line=GREEN, radius=0.02)
txt(s, 0.8, 1.8, 6.0, 0.32,
    [P([R("私の任された範囲（　　　　　　　　　　　　　　　）", 12, True, GREEN)])])
txt(s, 0.85, 2.2, 8.4, 0.4,
    [P([R("この枠の中に、施設を丸で置いてください。丸の大きさ＝あなたが考える重要度です。", 10.5, False, GRAY)])])
card(s, 9.75, 1.7, 3.0, 2.2,
     [P([R("描く要素", 13, True, WHITE)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("□ 大学／基幹病院／その他", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 重要な医師（誰が動かす？）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 患者の流れ（実線）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 人事・派遣（破線）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 情報・方針（点線）", 11, False, WHITE)], line=1.2)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.16)
card(s, 9.75, 4.05, 3.0, 2.2,
     [P([R("使う「機能」を書き込む", 12.5, True, INK)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("診療／研究／教育／医局人事／医師派遣／情報発信／講演会・研究会", 11, False, INK)], line=1.3, space_after=8),
      P([R("→ この課題を解くのに必要な機能を、丸の中に書く", 11, True, GOLD)], line=1.25)],
     fill=YPALE, line=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.16)
card(s, 0.6, 6.45, 12.15, 0.45,
     [P([R("問い：あなたの図で、大学は何番目に大きいですか？　その理由を説明できますか？", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 34 付録B 4S+α
s = add_slide()
header(s, "APPENDIX B", "４S ＋ α シート テンプレート（印刷・配布用）", kcolor=GRAY)
txt(s, 0.6, 1.6, 12.15, 0.32,
    [P([R("範囲名（　　　　　　　　　　）　作成日（　　／　　）　作成者（　　　　　　）", 11.5, False, INK)])])
tq = [(0.6, 1.95, "① 成功像　—　範囲がこうなっていたら最高", GREEN),
      (6.75, 1.95, "② 現状・課題　—　成功像とのGAP", NAVY),
      (0.6, 3.5, "③ 原因　—　なぜ？×3", GOLD),
      (6.75, 3.5, "④ 解決策　—　何を起こすか", RED)]
for x, y, t, col in tq:
    card(s, x, y, 6.0, 0.45, [P([R(t, 12, True, WHITE)])], fill=col, radius=0.1, pad=0.13)
    card(s, x, y + 0.5, 6.0, 1.0, [P([R("", 10)])], fill=WHITE, line=col, radius=0.1)
alpha = [("＋ 大学・基幹病院の役割", DEEP), ("＋ 自分の介入点", DEEP), ("＋ 次の行動（1つだけ）", DEEP)]
for i, (t, col) in enumerate(alpha):
    x = 0.6 + i * 4.09
    card(s, x, 5.05, 3.9, 0.45, [P([R(t, 11.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 5.55, 3.9, 0.85, [P([R("", 10)])], fill=WHITE, line=DEEP, radius=0.1)
card(s, 0.6, 6.55, 12.15, 0.42,
     [P([R("セルフチェック：　□ 主語は「範囲」になっているか　　□ 使う機能を選べているか　　□ 「なぜ重要か」を語れるか", 11.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 35 付録C 施設内マップ
s = add_slide()
header(s, "APPENDIX C", "施設の中を見るとき — キーパーソン5つの問い（DAY1の復習）", kcolor=GRAY,
       lead="範囲全体の図を描いたあと、重要施設の「中」を見るときに使ってください。")
qs = [("Q1", "治療方針は、誰の一言で決まる？", "◎ 方針決定者", GREEN),
      ("Q2", "新しい治療を最初に試すのは、誰？", "○ アーリーアダプター", GREEN),
      ("Q3", "若手が困ったとき、誰に聞きに行く？", "★ 情報ハブ", GOLD),
      ("Q4", "紹介患者の受け入れ・行き先を差配するのは、誰？", "◇ 連携の要", NAVY),
      ("Q5", "研究会・講演会など「外の顔」は、誰？", "□ 対外の顔", NAVY)]
y = 2.15
for no, q, tag, col in qs:
    circle(s, 0.6, y, 0.6, no, fill=col, size=13)
    card(s, 1.4, y, 8.2, 0.6, [P([R(q, 14, True, INK)])], fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    card(s, 9.75, y, 3.0, 0.6, [P([R(tag, 12, True, col)], align=PP_ALIGN.CENTER)], fill=PALE2, radius=0.15)
    y += 0.7
card(s, 0.6, 5.72, 12.15, 1.1,
     [P([R("5つの答えは同一人物とは限りません。", 14.5, True, RED),
         R("「教授＝キーパーソン」と決めつけた瞬間、他の4人が見えなくなります。", 13.5, False, INK)],
       space_after=5, line=1.2),
      P([R("学会の重鎮（KOL）と、その施設で物事を動かす人は別モノ。範囲の図の中で、誰の影響力を使うかを決めてから中に入りましょう。", 12, False, GRAY)])],
     fill=YPALE, radius=0.1, pad=0.2)

# ================================================================ 36 付録D 肩書き
s = add_slide()
header(s, "APPENDIX D", "大学の「肩書き」早見表 — 立場の読み方と注意点", kcolor=GRAY)
colA = [("教授（診療科長）", "方針・人事の最終決定者。ただし多忙で、現場の細部は下のポジションが握っていることが多い"),
        ("准教授・講師", "実務の要であり、次期教授候補。3年後のキーパーソンとして関係構築は先行投資になる"),
        ("助教・医員・専攻医", "実処方と臨床研究の担い手。数年後、関連病院の幹部として範囲の中に散っていく"),
        ("医局長（呼称は大学ごと）", "人事実務・外部窓口の情報ハブ。講演依頼・面会調整はまずこの人、という大学が多い")]
colB = [("特任教授・特任講師 など", "特定プロジェクトや資金で任用。医局ラインの人事権・決定権とは別枠のことが多い → 役割を個別確認"),
        ("客員・非常勤", "本務は他施設。院内の決定権は限定的だが、施設間ネットワークのハブになっていることがある"),
        ("名誉教授", "退官後の称号で現役の決定権はない。ただし人脈・影響力は健在。研究会や講演会の重鎮"),
        ("寄附講座（教員）", "寄附により設置された講座。本流医局との距離感は大学ごとに全く違う → 最初に立ち位置を確認")]
card(s, 0.6, 1.72, 6.0, 0.5, [P([R("院内の本流ライン", 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GREEN, radius=0.12)
card(s, 6.75, 1.72, 6.0, 0.5, [P([R("読み違えやすい肩書き（要・個別確認）", 13, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
for ci, (rows_, col) in enumerate(((colA, GREEN), (colB, NAVY))):
    x = 0.6 + ci * 6.15
    y = 2.32
    for t, d in rows_:
        card(s, x, y, 6.0, 1.0,
             [P([R(t, 12.5, True, col)], space_after=3), P([R(d, 10.5, False, INK)], line=1.18)],
             fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
        y += 1.08
card(s, 0.6, 6.62, 12.15, 0.4,
     [P([R("肩書きは「地図の記号」。同じ肩書きでも大学ごとに意味が違います — 実際の力関係は、必ず個別に確かめましょう。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 37 付録E コンプラ
s = add_slide()
header(s, "APPENDIX E", "大学活動 コンプライアンスの5原則", kcolor=GRAY,
       lead="アンケートの不安「寄附金・広告協賛・宣伝許可・施設ルール」に応えて。攻める活動ほど、守りが土台になります。")
pr = [("① 施設ルールが最優先", "訪問・面会・資材配布のルールは施設ごとに違う。着任時と変更時に必ず確認し、迷ったら守りに倒す"),
      ("② 寄附金・広告協賛は「その場で約束しない」", "依頼を受けたら即答せず、必ず社内の申請・審査手続きに乗せる。誠実な「持ち帰ります」は信頼を損なわない"),
      ("③ 宣伝許可・採用ルールは現行の文書で確認", "「前任者がやっていた」は根拠にならない。DAY1で学んだ院内運用の確認を、毎回やり直す"),
      ("④ 迷ったら自己判断しない", "判断基準はプロモーションコードと社内SOP。少しでも迷ったら上司・コンプライアンス部門に相談してから動く"),
      ("⑤ 記録を残す", "依頼・回答・手続きの経緯を記録に残す。誠実さの証明であり、先生と自分の両方を守る武器になる")]
y = 2.15
for t, d in pr:
    card(s, 0.6, y, 4.15, 0.8, [P([R(t, 12, True, WHITE)])], fill=DEEP, radius=0.1, pad=0.15)
    card(s, 4.9, y, 7.85, 0.8, [P([R(d, 11.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 0.9
txt(s, 2.8, 6.72, 10.0, 0.32,
    [P([R("※ 本スライドは一般的な注意喚起です。個別の案件は、必ず最新の社内規程と担当部門の指示に従ってください。", 11.5, True, GRAY)])])

# ================================================================ 38 付録F ファシリテーター
s = add_slide()
header(s, "APPENDIX F", "ファシリテーター用メモ（進行のコツ）", kcolor=GRAY)
tips = [("事前準備・時間管理",
         ["事前案内：A4白紙1枚とペンを持参、担当範囲の施設を思い出してくる",
          "録画を回し、気づきリストとセットで欠席者へ共有（アンケートで要望多数）",
          "ワークは「あと2分」を予告してから切る。2ブロックの時間配分を最優先で守る"]),
        ("場づくり",
         ["チェックインは進行役が最初に投稿し、投稿のハードルを下げる",
          "「大学が一番大きくない図」が出たら、その場で全体に紹介する",
          "ワーク中は沈黙OKと伝える。ブレイクアウトは各室を1周して1声かけ"]),
        ("つまずき対応",
         ["図が描けない人には「重要そうな5施設だけ」と伝える",
          "「正解がない」ことに戸惑う人には、4パターンのスライドに戻る",
          "4Sが埋まらない人には「1箱でも言い切れれば成功」と伝える"]),
        ("Beyondの扱い",
         ["Beyondは全員必達にしない。「考え方の紹介」として軽く置く",
          "難しくしすぎて手が止まるより、「大学の枠を外す」体験の持ち帰りを優先",
          "最終回なので、シリーズ全体の感想を1言ずつ集めてから終える"])]
for i, (t, lines) in enumerate(tips):
    x = 0.6 + (i % 2) * 6.15
    y = 1.75 + (i // 2) * 2.45
    card(s, x, y, 6.0, 0.52, [P([R(t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GRAY, radius=0.12)
    card(s, x, y + 0.58, 6.0, 1.68,
         [P([R("・" + l, 11, False, INK)], space_after=7, line=1.2) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.15)
txt(s, 2.8, 6.72, 10.0, 0.32,
    [P([R("本資料の事例・人名はすべて架空です。実施設の情報を扱う際は、社内の情報取り扱いルールに従ってください。", 11, False, GRAY)])])

# ---------------------------------------------------------------- save
prs.save(OUT)
print("saved:", OUT, "| slides:", len(prs.slides._sldIdLst))
