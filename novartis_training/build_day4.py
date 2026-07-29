# -*- coding: utf-8 -*-
"""
Renal MR スキルアッププロジェクト DAY4
「ちょっと分かるだけで世界が変わる」 — テーマ：戦略的思考

DAY4_base_1-7.pptx の冒頭7枚を保持し（Agendaの文言のみ更新）、8枚目以降を生成。

■ 構成（計60分）
   オープニング（含DAY3→DAY4）9分 ／ テーマ①「影響力を見極めた経験」16分 ／
   テーマ②「エリアの中の影響力」31分（藤さんの事例10分を含む） ／ まとめ 4分

■ 到達目標（プロジェクト公式・戦略的思考）
   担当施設と周辺エリアに対する成功像・現状・課題・解決法を言語化できる

■ 設計の柱（企画ミーティング＋DAY1〜3の内容を反映）
   - 戦略的思考 ＝ ①影響力（誰が、何を動かせるか）× ②影響の輪（どこまで届くか）
   - 疾患・製品の戦略は作らせない。IgA腎症は付録の参考例のみ
   - テーマ①②とも「過去の経験の共有」を軸にしたフリーディスカッション
   - 詳細な講義コンテンツは付録に格納し、本編は問いと対話に集中させる
   - テーマ①はDAY1の「"影響力"を紐解いてみよう」を、自分の担当施設で実際にやる回。
     DAY2で会えた人・DAY3で得た情報を、ここで結びつける
   - テーマ②は影響の輪をエリアへ広げ、エリアプランニングを簡単にディスカッションする回
   - 大学に固執しない。大学はエリアの中の1施設。輪の大きさは人によって違う
   - 輪を動かすには相手のWINが要る（WIN-WIN）
   - ワークは「丸を描く」「3つの問い」だけ。答えが出なくても分かれば収穫
   - 共有は型にはめず、フリーディスカッション
   - Beyondは「プラス1」。全員必達にしない
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
AGENDA_LINES = ["■オープニング　9分",
                "■テーマ①「影響力を見極めた経験」　16分",
                "■テーマ②「エリアの中の影響力」　31分",
                "■まとめ・行動宣言　4分"]
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
blocks = [("オープニング", "9分", "3回の振り返り／DAY3からDAY4へ", GREEN),
          ("テーマ①「影響力を見極めた経験」", "16分", "これまでの経験を持ち寄る", NAVY),
          ("テーマ②「エリアの中の影響力」", "31分", "藤さんの事例10分 → 自分のエリアへ", NAVY),
          ("まとめ・行動宣言", "4分", "3つの学び／次に確かめたいこと", GREEN)]
y = 1.9
for t, tm, d, col in blocks:
    card(s, 0.6, y, 6.3, 1.0, [P([R("■ " + t, 16.5, True, WHITE)])], fill=col, radius=0.1, pad=0.22)
    card(s, 7.0, y, 1.2, 1.0, [P([R(tm, 15, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 8.35, y, 4.4, 1.0, [P([R(d, 13, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.18)
    y += 1.13
card(s, 0.6, 6.45, 12.15, 0.48,
     [P([R("レクチャーは合計6分ほど。皆さんが考え、話す時間を40分とっています。", 13.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 9 今日のテーマ
s = add_slide()
header(s, "TODAY'S DESIGN", "顧客理解を、エリアを見る力に変える")
txt(s, 0.6, 1.58, 12.15, 0.4,
    [P([R("― 大学・基幹病院の影響力を見極め、エリア全体を捉える ―", 15, True, GRAY)],
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
      P([R("本日の到達点：自分のエリアにおける影響力のつながりを、自分の言葉で説明できる", 13, True, DEEP)],
        align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
flow3 = [("① 経験を持ち寄る", "影響力を、どう見極めてきたか", "テーマ①", NAVY),
         ("② 事例から学ぶ", "藤さんのエリアでは、どう広がっていたか", "テーマ②", GOLD),
         ("③ 自分に当てはめる", "私のエリアでは、どうつながっているか", "テーマ②", GREEN)]
for i, (t, d, tag, col) in enumerate(flow3):
    x = 0.6 + i * 4.09
    card(s, x, 4.15, 3.9, 0.62, [P([R(t, 15, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 4.85, 3.9, 0.8, [P([R(d, 12.5, False, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=PALE2, radius=0.1, pad=0.14)
    if i < 2:
        arrow(s, x + 3.94, 4.32, 0.14, 0.28, color=GREEN2)
card(s, 0.6, 5.85, 12.15, 1.05,
     [P([R("完成したエリアプランをつくる回ではありません。", 14, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("「自分のエリアでは、どの施設・医師が、どんな関係を通じて周囲に影響しているか」を語れれば成功です。", 15, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 10 チェックイン
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, 3.4, 0.42, "CHECK IN　｜　3分", fill=GREEN)
card(s, 0.6, 1.15, 12.15, 1.8,
     [P([R("この3回で、あなたの", 28, True, INK),
         R("「大学の見方」", 28, True, RED),
         R("は変わりましたか？", 28, True, INK)], align=PP_ALIGN.CENTER, space_after=10),
      P([R("大学担当としての", 28, True, INK),
         R("「自信」", 28, True, RED),
         R("はつきましたか？", 28, True, INK)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.06, pad=0.2)
card(s, 3.2, 3.55, 6.95, 0.85,
     [P([R("Teamsチャットへ、自由に書き込んでください", 18, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.15, pad=0.14)
hooks = [("大学に行くとき、以前と違うことは？", GREEN),
         ("会う人・聞くことは、変わった？", NAVY),
         ("まだ「分からない」と思うことは？", GOLD)]
for i, (t, col) in enumerate(hooks):
    card(s, 0.6 + i * 4.1, 5.3, 3.95, 1.05,
         [P([R(t, 15, True, INK)], align=PP_ALIGN.CENTER, line=1.2)],
         fill=WHITE, line=col, line_w=1.3, radius=0.1, pad=0.16)
footer(s)

# ================================================================ 11 DAY3→DAY4
s = add_slide()
header(s, "BRIDGE", "情報を集めるだけでは、エリアは見えてこない", "4分", kcolor=GOLD)
card(s, 0.6, 2.0, 5.8, 0.62, [P([R("DAY3までにできるようになったこと", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
d3 = ["どんな情報が必要か", "どこから情報を取るか", "仮説を持って確認する", "顧客理解を深める"]
card(s, 0.6, 2.72, 5.8, 2.15,
     [P([R("・" + l, 13, False, INK)], line=1.25, space_after=11) for l in d3],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)
arrow(s, 6.62, 3.4, 0.65, 0.6, color=GOLD)
card(s, 7.5, 2.0, 5.25, 0.62, [P([R("DAY4で考えること", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
d4 = ["その情報から、誰の影響力が見えるか", "その影響は、どこまで広がっているか",
      "大学・基幹病院が、エリアでどんな役割を持つか"]
card(s, 7.5, 2.72, 5.25, 2.15,
     [P([R("・" + l, 13, True, INK)], line=1.25, space_after=14) for l in d4],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)
card(s, 0.6, 5.15, 12.15, 1.35,
     [P([R("情報の価値は、持っている量ではなく、", 17, False, WHITE)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("見方や活動が変わるかで決まる。", 23, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)
# ================================================================ 12 テーマ①扉
s = add_slide()
section(s, "①", "影響力を見極めた経験", "テーマ①　｜　16分（ディスカッション12分・全体共有4分）",
        "「この先生・この施設が鍵だった」と気づいた経験は？",
        ["正解を教える時間ではありません。皆さんの経験を持ち寄る時間です",
         "3〜4人で、思い出した経験を自由に話してください",
         "最後にグループで「影響力を見極めるうえで重要だったこと」を1つ決めます"])

# ================================================================ 13 テーマ①ディスカッション
s = add_slide()
header(s, "DISCUSSION ①", "影響力を見極めた経験を共有してください", "12分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.95,
     [P([R("これまでの活動で、", 18, False, INK),
         R("「この先生・この施設が鍵だった」", 18, True, RED),
         R("と気づいた経験は？", 18, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.08, pad=0.16)
card(s, 0.6, 3.0, 12.15, 0.48, [P([R("話を深めるヒント", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
hints = ["何をきっかけに、その先生・施設が重要だと気づきましたか？",
         "その後、活動の進め方や関わる相手はどう変わりましたか？",
         "結果として、何が前進しましたか？"]
y = 3.55
for i, h in enumerate(hints):
    circle(s, 0.6, y, 0.58, str(i + 1), fill=NAVY2, size=15)
    card(s, 1.42, y, 11.33, 0.58, [P([R(h, 15, True, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 0.66
steps = [("最初の1分", "話したい経験を、ひとつ思い出す", GREEN),
         ("9分", "3〜4人で自由に話す（順番も型もありません）", GREEN),
         ("最後の2分", "グループで「影響力を見極めるうえで重要だったこと」を1つ決める", NAVY)]
y = 5.5
for t, d, col in steps:
    card(s, 0.6, y, 2.2, 0.34, [P([R(t, 11.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, 3.0, y, 9.75, 0.34, [P([R(d, 12, False, INK)])], fill=PALE2, radius=0.1, pad=0.1)
    y += 0.38

# ================================================================ 14 テーマ①全体共有
s = add_slide()
header(s, "SHARE ①", "全体共有 — 影響力は、どこを見れば分かるのか", "4分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.6,
     [P([R("2〜3グループから、30〜45秒ずつ　—　「私たちのグループでは、〇〇が重要だという意見になりました」", 14.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
views = [("① 周囲がどう反応しているか", ["誰に相談しているか", "誰の意見を参考にしているか",
                                "誰の発言で議論が進むか"], NAVY),
         ("② 実際にどんな役割を担っているか", ["診療方針を示す／新しい取り組みを実行する",
                                   "若手を育成する／施設間をつなぐ", "院外へ情報を発信する"], GREEN),
         ("③ その影響がどこまで届くか", ["施設の中", "関連病院／担当エリア",
                               "担当エリアの外"], GOLD)]
for i, (t, lines, col) in enumerate(views):
    x = 0.6 + i * 4.09
    card(s, x, 2.7, 3.9, 0.62, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col, radius=0.1)
    card(s, x, 3.4, 3.9, 1.85,
         [P([R("・" + l, 12, False, INK)], line=1.25, space_after=10) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 0.6, 5.45, 12.15, 1.35,
     [P([R("皆さんの経験は、この3つの見方に整理できます。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("肩書きではなく、周囲の反応・実際の役割・届く範囲で見る。", 21, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 15 テーマ②扉
s = add_slide()
section(s, "②", "エリアの中の影響力", "テーマ②　｜　31分（事例10分・個人ワーク6分・共有13分）",
        "その影響力は、エリアの中でどう広がっているか？",
        ["一人の医師、一つの大学の影響力は、その施設の中だけで完結するとは限らない",
         "まず藤さんの事例から、影響力の広がり方を具体的に見る",
         "そのあと、自分のエリアに当てはめて考え、メンバーと共有する"])

# ================================================================ 16 テーマ②オープニング
s = add_slide()
header(s, "THEME ②", "影響力は、何を通じて広がるのか", "2分", kcolor=NAVY)
paths = [("医局人事・医師派遣", GREEN), ("患者紹介・症例相談", GREEN),
         ("教育・若手育成", NAVY2), ("同門・卒大・人脈", NAVY2),
         ("研究会・講演会", GOLD), ("研究・学会発信", GOLD),
         ("日常的な医師同士の相談", RED)]
for i, (t, col) in enumerate(paths):
    x = 0.6 + (i % 4) * 3.12
    y = 2.05 + (i // 4) * 0.95
    card(s, x, y, 2.95, 0.7, [P([R(t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col, radius=0.12)
card(s, 9.96, 3.0, 2.79, 0.7,
     [P([R("…など", 13.5, True, GRAY)], align=PP_ALIGN.CENTER)],
     fill=PALE2, line=LGRAY, radius=0.12)
card(s, 0.6, 4.15, 12.15, 1.25,
     [P([R("大学が常に中心とは限らない。", 22, True, YELL)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("大学と基幹病院が、それぞれ異なる役割を持っている場合もある。", 15, False, WHITE)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)
card(s, 0.6, 5.7, 12.15, 1.1,
     [P([R("では、実際にどう広がっているのか。", 15, False, INK)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("藤さんの事例から、一緒に見ていきましょう。", 19, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.18)
# ================================================================ 17 事例の見どころ
s = add_slide()
header(s, "CASE", "藤さんの事例紹介 — 見どころ", "10分", kcolor=GOLD)
card(s, 0.6, 1.85, 12.15, 0.6,
     [P([R("成功事例の紹介ではなく、", 15, False, INK),
         R("「どの情報から、エリア内の影響力のつながりを読み取ったか」", 15, True, RED),
         R("を見てください。", 15, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
parts = [("① 担当エリアの背景", "1分", "どんな大学・基幹病院があるか／当初どう見ていたか", GREEN),
         ("② 転機となった情報・気づき", "2分", "どの先生・施設が鍵だと気づいたか／何がきっかけか", NAVY2),
         ("③ 影響力のつながり", "3分", "大学と基幹病院がどうつながっていたか（図）", NAVY),
         ("④ 活動の変化", "2分", "見方が変わる前と後で、活動はどう変わったか", GOLD),
         ("⑤ 伝えたい学び", "2分", "肩書きだけでは分からなかったこと／応用できる視点", RED)]
y = 2.6
for t, tm, d, col in parts:
    card(s, 0.6, y, 3.5, 0.5, [P([R(t, 12.5, True, WHITE)])], fill=col, radius=0.1, pad=0.14)
    card(s, 4.25, y, 0.9, 0.5, [P([R(tm, 12, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 5.3, y, 7.45, 0.5, [P([R(d, 12, False, INK)])], fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.58
card(s, 0.6, 5.62, 12.15, 1.25,
     [P([R("最後に、藤さんへの問い", 13, True, MINT)], align=PP_ALIGN.CENTER, space_after=7),
      P([R("「自分のエリアを見るとき、最初にどこを確認するとよいと思いますか？」", 20, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 18-21 事例テンプレート
case_tpl = [("① 担当エリアの背景", "1分", GREEN,
             ["どんな大学・基幹病院がありますか？", "当初、エリアをどのように見ていましたか？"]),
            ("② 転機となった情報・気づき", "2分", NAVY2,
             ["どの先生・施設が鍵だと気づきましたか？", "何をきっかけに気づきましたか？",
              "Dry情報／Wet情報のどちらでしたか？　誰から得た情報でしたか？"]),
            ("③ 影響力のつながり", "3分", NAVY,
             ["大学と基幹病院は、どうつながっていましたか？",
              "医師同士の関係／人事・派遣／患者紹介／研究会・同門／情報発信"]),
            ("④ 活動の変化と、伝えたい学び", "4分", GOLD,
             ["見方が変わる前と後で、活動はどう変わりましたか？",
              "大学だけでなく、基幹病院をどう組み合わせましたか？",
              "肩書きだけでは分からなかったこと／他のエリアでも応用できる視点"])]
for idx, (t, tm, col, qs) in enumerate(case_tpl):
    s = add_slide()
    header(s, "CASE", "藤さんの事例　" + t, tm, kcolor=GOLD)
    card(s, 0.6, 1.78, 12.15, 0.42 + 0.26 * len(qs),
         [P([R("・" + q, 12, True, INK)], line=1.2, space_after=5) for q in qs],
         fill=PALE2, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE, radius=0.1, pad=0.14)
    top = 1.78 + 0.42 + 0.26 * len(qs) + 0.15
    shape(s, 0.6, top, 12.15, 6.85 - top, fill=WHITE, line=col, line_w=1.4, radius=0.02)
    if idx == 2:
        txt(s, 0.85, top + 0.12, 11.6, 0.3,
            [P([R("凡例：　人事・派遣　／　患者紹介・症例相談　／　同門・卒大　／　研究会・教育　／　情報発信", 10.5, False, GRAY)])])
    txt(s, 0.85, 6.4, 11.6, 0.3,
        [P([R("※ 藤さんのスライド・図をこのエリアに配置してください", 10, False, LGRAY)])])

# ================================================================ 22 個人ワーク
s = add_slide()
header(s, "WORK", "自分のエリアの「影響力のつながり」を考える", "6分", kcolor=GREEN)
card(s, 0.6, 1.75, 12.15, 0.72,
     [P([R("自分の担当エリアで、", 16, False, INK),
         R("大学・基幹病院の影響力が、どこからどこへ、どのように広がっているか", 16, True, RED),
         R("を考えてください。", 16, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
card(s, 0.6, 2.62, 6.0, 0.5, [P([R("考えるヒント", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
hints = ["影響力の起点となっている先生・施設はどこですか？",
         "どのようなつながりを通じて、影響が広がっていますか？",
         "大学と基幹病院は、それぞれどんな役割を持っていますか？",
         "まだ分からない関係やつながりは、どこですか？"]
card(s, 0.6, 3.22, 6.0, 2.1,
     [P([R("・" + h, 12, False, INK)], line=1.25, space_after=10) for h in hints],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 6.75, 2.62, 6.0, 0.5, [P([R("描いてよいもの", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
items = ["大学・基幹病院／重要な医師", "医局人事・医師派遣", "患者紹介・症例相談",
         "同門・卒大／教育・研究会", "情報発信", "分からない関係は「？」"]
card(s, 6.75, 3.22, 6.0, 2.1,
     [P([R("・" + i2, 12, False, INK)], line=1.25, space_after=7) for i2 in items],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 0.6, 5.55, 12.15, 1.3,
     [P([R("正確な組織図をつくるワークではありません。", 17, True, RED)], align=PP_ALIGN.CENTER, space_after=7),
      P([R("文字でも図でも構いません。今分かっている範囲で、自分がエリアをどう見ているかを自由に表してください。", 13.5, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=YPALE, radius=0.1, pad=0.18)

# ================================================================ 23 テーマ②ディスカッション
s = add_slide()
header(s, "DISCUSSION ②", "自分のエリアの見え方を共有する", "10分", kcolor=GREEN)
card(s, 0.6, 1.82, 12.15, 0.55,
     [P([R("3人1組。1人約3分で自分のエリアを説明します。発表の型はありません。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
pts = [("① 影響力の中心はどこか", "大学か／基幹病院か／特定の医師か／複数の施設か", NAVY),
       ("② 何を通じて広がっているか", "人事・派遣／患者紹介／教育／同門・人脈／研究会／情報発信", GREEN),
       ("③ 大学と基幹病院の役割の違い", "大学が方針を示し基幹病院が実践する／基幹病院の経験を大学が発信する など", GOLD),
       ("④ まだ分からないことは何か", "誰が誰に相談しているか／医局人事の実態／研究会の中心人物／施設間の関係性", RED)]
y = 2.6
for t, d, col in pts:
    card(s, 0.6, y, 3.6, 0.72, [P([R(t, 12.5, True, WHITE)], line=1.15)], fill=col, radius=0.1, pad=0.15)
    card(s, 4.35, y, 8.4, 0.72, [P([R(d, 12, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 0.84
card(s, 0.6, 6.0, 12.15, 0.85,
     [P([R("残り時間で、", 14, False, INK),
         R("「他の人のエリアと比べて、最も違っていた点・参考になった点」", 15, True, DEEP),
         R("を話してください。", 14, False, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 24 テーマ②全体共有
s = add_slide()
header(s, "SHARE ②", "全体共有 — エリアの見方は、どう変わったか", "3分", kcolor=GREEN)
card(s, 0.6, 1.9, 12.15, 1.0,
     [P([R("他の人のエリアを聞いて、", 20, False, INK),
         R("自分のエリアの見方が変わった点", 20, True, RED),
         R("は何ですか？", 20, False, INK)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.08, pad=0.16)
txt(s, 0.6, 3.1, 12.15, 0.32,
    [P([R("こんな気づきが出てきます", 13, True, GRAY)], align=PP_ALIGN.CENTER)])
finds = ["大学が中心ではないエリアがある",
         "同じ大学でも、疾患やテーマによって影響範囲が違う",
         "基幹病院の臨床的な影響が大きいこともある",
         "一人の医師が、複数の施設をつないでいる",
         "自分が把握できていない関係が見えた"]
y = 3.46
for f in finds:
    card(s, 2.2, y, 8.95, 0.5, [P([R(f, 14, False, INK)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=LGRAY, radius=0.1)
    y += 0.58
card(s, 0.6, 6.36, 12.15, 0.5,
     [P([R("優れたエリア戦略を発表する場ではありません。「視座が変わったこと」を共有してください。", 13, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)
# ================================================================ 25 まとめ
s = add_slide()
header(s, "WRAP UP", "本日の3つの学び")
msgs = [(("1"), "影響力は、肩書きだけでは分からない",
         "周囲が誰を頼り、誰の意見で動いているかを見る。", NAVY),
        (("2"), "影響力は、施設の外へ広がっている",
         "人事、派遣、紹介、教育、研究会、人脈を通じてエリアへ広がる。", GOLD),
        (("3"), "エリアの見方に、唯一の正解はない",
         "大学が中心の場合も、基幹病院が中心の場合もある。自分の言葉で説明できることが重要。", GREEN)]
y = 1.95
for no, t, d, col in msgs:
    circle(s, 0.6, y + 0.15, 0.8, no, fill=col, size=20)
    card(s, 1.6, y, 11.15, 1.1,
         [P([R(t, 17, True, col)], space_after=5), P([R(d, 13, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.22)
    y += 1.25
card(s, 0.6, 5.66, 12.15, 1.12,
     [P([R("大学の中だけを詳しく知ることが、大学担当者の仕事ではない。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("エリアの中で、どうつながり、どこに影響しているかを説明できること。", 20, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 26 行動宣言
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, 2.4, 0.42, "ACTION", fill=GREEN)
txt(s, 0.6, 0.95, 12.2, 0.8, [P([R("行動宣言", 32, True, DEEP)])])
card(s, 0.6, 1.95, 12.15, 1.0,
     [P([R("Teamsチャットに、", 21, True, INK),
         R("「自分のエリアで、次に確かめたいこと」", 21, True, RED),
         R("を1つ、1行で", 21, True, INK)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.06, pad=0.18)
txt(s, 0.6, 3.2, 12.15, 0.32, [P([R("例", 13, True, GRAY)], align=PP_ALIGN.CENTER)])
exs = ["大学と主要基幹病院の間で、誰が日常的に相談されているか確認する",
       "医局長に、関連病院への派遣と役割分担を聞く",
       "基幹病院部長が、どの先生の意見を参考にしているか確認する",
       "研究会の企画を、実際に動かしている先生を確認する"]
y = 3.62
for e in exs:
    card(s, 2.2, y, 8.95, 0.56, [P([R(e, 14, False, INK)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=LGRAY, radius=0.1)
    y += 0.66
card(s, 2.2, 6.28, 8.95, 0.62,
     [P([R("描いたエリアの図は、営業所でも共有を（DAY3）", 14, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.12)
footer(s)

# ================================================================ 27 クロージング
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
txt(s, 0.9, 1.0, 11.5, 0.5, [P([R("ありがとうございました", 19, True, MINT)])])
steps4 = [("第1回", "見る力", GREEN2), ("第2回", "会う力", GREEN2),
          ("第3回", "情報を取る力", GREEN2), ("第4回", "エリアを見る力", YELL)]
for i, (d, t, col) in enumerate(steps4):
    x = 0.9 + i * 2.95
    card(s, x, 1.65, 2.75, 0.95,
         [P([R(d, 12.5, True, DEEP if col == YELL else WHITE)], align=PP_ALIGN.CENTER, space_after=4),
          P([R(t, 14, True, DEEP if col == YELL else WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col if col == YELL else RGBColor(0x11, 0x63, 0x45), radius=0.1, pad=0.14)
    if i < 3:
        arrow(s, x + 2.78, 2.0, 0.14, 0.24, color=MINT)
card(s, 0.9, 2.95, 11.5, 1.45,
     [P([R("第3回では、顧客を理解するために「どんな情報を取るか」を考えました。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("第4回では、その情報をつなげ、大学・基幹病院の影響力をエリアの中で捉えました。", 15, False, WHITE)],
        align=PP_ALIGN.CENTER)],
     fill=RGBColor(0x11, 0x63, 0x45), radius=0.1, pad=0.18)
card(s, 0.9, 4.65, 11.5, 1.5,
     [P([R("大学担当者に求められるのは、大学の中だけを詳しく知ることではありません。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("大学・基幹病院がエリアの中でどうつながり、", 19, True, DEEP)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("どこに影響しているかを説明できることです。", 19, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.1, pad=0.18)
footer(s, dark=True)

# ================================================================ 28 付録A ワークシート
s = add_slide()
header(s, "APPENDIX A", "ワークシート：自分のエリアの「影響力のつながり」", kcolor=GRAY)
txt(s, 0.6, 1.62, 12.15, 0.32,
    [P([R("担当エリア（　　　　　　　　　　　　）　　作成日（　　／　　）　　作成者（　　　　　　）", 12, False, INK)])])
shape(s, 0.6, 2.0, 8.9, 4.35, fill=PALE2, line=GREEN, radius=0.02)
txt(s, 0.85, 2.12, 8.4, 0.3,
    [P([R("文字でも図でも構いません。分からない関係は「？」で。", 11, False, GRAY)])])
card(s, 9.75, 2.0, 3.0, 2.1,
     [P([R("描いてよいもの", 13.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=9),
      P([R("□ 大学・基幹病院／重要な医師", 11.5, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 医局人事・医師派遣", 11.5, False, WHITE)], space_after=7),
      P([R("□ 患者紹介・症例相談", 11.5, False, WHITE)], space_after=7),
      P([R("□ 同門・卒大／教育・研究会", 11.5, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 情報発信", 11.5, False, WHITE)])],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.17)
card(s, 9.75, 4.25, 3.0, 2.1,
     [P([R("考えるヒント", 13, True, INK)], align=PP_ALIGN.CENTER, space_after=9),
      P([R("・影響力の起点はどこか", 11.5, False, INK)], space_after=8),
      P([R("・何を通じて広がっているか", 11.5, False, INK)], space_after=8),
      P([R("・大学と基幹病院の役割の違い", 11.5, False, INK)], space_after=8, line=1.2),
      P([R("・まだ分からない関係はどこか", 11.5, True, GOLD)], line=1.2)],
     fill=YPALE, line=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.17)
card(s, 0.6, 6.45, 12.15, 0.45,
     [P([R("正確な組織図ではなく、「自分がエリアをどう見ているか」を表すシートです。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 29 付録B 影響力の見極め方
s = add_slide()
header(s, "APPENDIX B", "参考：影響力の見極め方（DAY1の復習）", kcolor=GRAY)
card(s, 0.6, 1.85, 6.0, 0.5, [P([R("テリトリーとニーズ", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
tiers = [("HP（基幹病院）", "1病院 → 医師会・医療圏 → 関連病院・出身医局",
          "紹介率を上げたい／関連病院と協働したい"),
         ("HS（大学病院）", "県内 → 県内＋他大学・専門領域 → 日本全体・学会",
          "研修医が欲しい／論文を出したい／県内での存在感")]
y = 2.45
for t, terr, need in tiers:
    card(s, 0.6, y, 6.0, 1.05,
         [P([R(t, 13, True, DEEP)], space_after=4),
          P([R(terr, 11, False, INK)], space_after=3, line=1.2),
          P([R("ニーズ：" + need, 10.5, False, GRAY)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 1.17
card(s, 0.6, 4.8, 6.0, 0.5, [P([R("大学が動かせるもの（7つ）", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
card(s, 0.6, 5.4, 6.0, 1.0,
     [P([R("教育／研究／臨床／医局人事／医師派遣／情報発信／講演会・研究会", 13, True, INK)], line=1.35)],
     fill=PALEB, radius=0.1, pad=0.17)
card(s, 6.75, 1.85, 6.0, 0.5, [P([R("影響力を持つ5つの役割", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GOLD, radius=0.12)
roles = [("◎", "方針を決める", "治療方針が、この人の一言で決まる"),
         ("○", "最初に試す", "新しい治療を最初に使う。実務の中心"),
         ("★", "情報ハブ", "若手が困ったら聞きに行く。医局長に多い"),
         ("◇", "連携の要", "紹介患者の受け入れ・行き先を差配"),
         ("□", "対外の顔", "研究会・講演会で外に発信する")]
y = 2.45
for mk, t, d in roles:
    circle(s, 6.75, y, 0.52, mk, fill=GOLD, size=14)
    card(s, 7.45, y, 5.3, 0.52,
         [P([R(t + "　", 12.5, True, GOLD), R(d, 11, False, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
    y += 0.62
card(s, 6.75, 5.55, 6.0, 0.85,
     [P([R("教授の裁量権（DAY1）", 12.5, True, DEEP)], space_after=4),
      P([R("① 臨床機会の配分　② 医局人事・異動　③ 教授会・教授選　④ 研究・教育の方向性", 11, False, INK)], line=1.2)],
     fill=PALE, radius=0.1, pad=0.15)
card(s, 0.6, 6.55, 12.15, 0.42,
     [P([R("本編では扱いません。ディスカッションで「見極めの視点」を整理するときの参考に。", 12, True, GRAY)],
       align=PP_ALIGN.CENTER)],
     fill=PALE2, radius=0.15)

# ================================================================ 30 付録C エリアのパターンと影響の輪
s = add_slide()
header(s, "APPENDIX C", "参考：エリアのパターンと、影響が届く範囲", kcolor=GRAY)
pats = [("① 大学の輪が最大",
         [("A大", 1.15, 1.0, 0.45, PALE, DEEP), ("基幹", 0.6, 2.05, 1.3, WHITE, GRAY),
          ("基幹", 0.6, 0.3, 1.4, WHITE, GRAY)],
         "方針がエリア全体に波及", GREEN),
        ("② 複数の大学が並ぶ",
         [("A大", 0.95, 0.45, 0.5, PALE, DEEP), ("B大", 0.95, 1.7, 1.1, PALE, GREEN2),
          ("基幹", 0.58, 1.3, 0.28, WHITE, GRAY)],
         "1大学では動かない", NAVY),
        ("③ 基幹病院の輪が最大",
         [("基幹", 1.2, 0.85, 0.5, PALEB, NAVY), ("A大", 0.7, 0.35, 1.5, PALE, DEEP),
          ("基幹", 0.62, 1.95, 1.45, PALEB, NAVY2)],
         "実務の影響力は基幹病院", GOLD),
        ("④ 輪がエリアを超える",
         [("A大", 1.1, 0.45, 0.45, PALE, DEEP), ("県外", 0.62, 1.95, 0.4, WHITE, GRAY),
          ("県外", 0.62, 2.05, 1.45, WHITE, GRAY)],
         "営業所・全国への展開", RED)]
for i, (t, circles, note, col) in enumerate(pats):
    x = 0.6 + i * 3.12
    card(s, x, 1.9, 2.95, 0.48, [P([R(t, 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    shape(s, x, 2.43, 2.95, 2.35, fill=PALE2, line=LGRAY, radius=0.04)
    for lbl, d, dx, dy, fc, lc in circles:
        circle(s, x + dx, 2.58 + dy, d, lbl, fill=fc, line=lc,
               size=10 if d > 0.9 else 8.5, color=lc)
    card(s, x, 4.88, 2.95, 0.48, [P([R(note, 11.5, False, INK)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.1)
card(s, 0.6, 5.55, 12.15, 0.5, [P([R("影響が届く範囲（4層）", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
lv = [("① 施設の中", "院内の方針・採用は動く", GREEN2),
      ("② 関連病院", "医局人事・派遣を通じて系列に届く", GREEN),
      ("③ 担当エリア", "研究会・講演会・地域連携で系列を越える", NAVY2),
      ("④ その先", "学会・全国の研究会で担当範囲を超える", NAVY)]
for i, (t, d, col) in enumerate(lv):
    x = 0.6 + i * 3.12
    card(s, x, 6.15, 2.95, 0.72,
         [P([R(t, 12, True, col)], align=PP_ALIGN.CENTER, space_after=3),
          P([R(d, 10, False, INK)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.12)

# ================================================================ 31 付録D 情報の入手先
s = add_slide()
header(s, "APPENDIX D", "参考：その情報は、誰から取れるか（DAY3）", kcolor=GRAY)
srcs = [("医師本人", "直接聞くのが、最も有効",
         ["今後の目標・成し遂げたいこと", "興味のある領域・研究テーマ",
          "参考にしている先生・KOL", "人脈、連携している施設"], GREEN),
        ("周辺関係者", "会えない時間を埋めてくれる",
         ["医局秘書：予定・医局の動き", "看護師・師長：現場の課題と関係性",
          "若手医師：医局の雰囲気と本音", "前任者・他領域MR・MS・社内メディカル"], NAVY),
        ("学会・研究会", "人的ネットワークが見える",
         ["共著論文：誰と誰が組んでいるか", "演者の顔ぶれ・座長との関係",
          "卒大・同門・同年次のつながり", "※DAY3事例：同年同卒を調べて会を設計"], GOLD)]
for i, (t, sub, lines, col) in enumerate(srcs):
    x = 0.6 + i * 4.09
    card(s, x, 1.95, 3.9, 0.75,
         [P([R(t, 16, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(sub, 11, False, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.78, 3.9, 2.15,
         [P([R("・" + l, 11.5, False, INK)], line=1.25, space_after=9) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
card(s, 0.6, 5.1, 6.0, 0.85,
     [P([R("聞き方のコツ（DAY3）", 12.5, True, DEEP)], space_after=4),
      P([R("仮説を持って行き、「クローズドで聞ける状態」にしてから会う", 12, False, INK)], line=1.2)],
     fill=PALEB, radius=0.1, pad=0.16)
card(s, 6.75, 5.1, 6.0, 0.85,
     [P([R("噂レベルの情報は", 12.5, True, DEEP)], space_after=4),
      P([R("複数の関係者から確認して、精度を上げる", 12, False, INK)], line=1.2)],
     fill=PALEB, radius=0.1, pad=0.16)
card(s, 0.6, 6.1, 12.15, 0.75,
     [P([R("信頼が深まっているサイン　—　", 13, False, INK),
         R("プライベートな話をしてくれる／将来の話をしてくれる", 15, True, RED),
         R("　→ 味方になってくれる可能性が高い", 13, False, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12, pad=0.14)
# ================================================================ 32 付録E DAY1-3総まとめ
s = add_slide()
header(s, "APPENDIX E", "参考：DAY1〜3の学び 総まとめ", kcolor=GRAY)
recap = [("DAY 1", "大学・基幹病院のイロハ", GREEN,
          ["大学の3使命：教育・研究・臨床。医師派遣で地域を支える",
           "影響力はテリトリーとニーズで決まる",
           "教授の裁量権：臨床機会・医局人事・教授選・研究教育",
           "大学は「医局の集合体」。病院教授／特任教授は財源・任期・実権で見分ける",
           "薬審・採用は施設ごとに流れが違う"]),
         ("DAY 2", "「会えない」を「会える」に", NAVY,
          ["未訪問 → 初回接点 → 仮説面会 → 定期面会 で設計",
           "アクセス：訪問ルール確認・秘書経由・メール・手紙・直接訪問",
           "Best Time / Best Place：外来・外勤・医局会・総回診・カンファ",
           "カレンダーで情報管理し、行動ログで検証",
           "会う理由を設計し次の約束を残す。My teacherをつくる"]),
         ("DAY 3", "やっぱりMRは情報が命", GOLD,
          ["顧客理解を深める必要性",
           "どこで、どの情報を取るか（ドライ×ウェット）",
           "仮説を持ち、クローズドで聞ける状態にする",
           "顧客理解＝現状把握。何を・なぜ使い、患者をどうしたいのか",
           "そして —— その情報を、どう活かすか"])]
for i, (d, t, col, lines) in enumerate(recap):
    x = 0.6 + i * 4.09
    card(s, x, 1.75, 3.9, 0.7,
         [P([R(d, 14, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(t, 11, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.52, 3.9, 3.55,
         [P([R("・" + l, 11, False, INK)], line=1.25, space_after=10) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 0.6, 6.25, 12.15, 0.62,
     [P([R("DAY4は、この3つを「エリアを見る力」に変える回でした。", 14.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12)

# ================================================================ 33 付録F 肩書き早見表
s = add_slide()
header(s, "APPENDIX F", "参考：大学の「肩書き」早見表", kcolor=GRAY)
colA = [("教授（診療科長）", "方針・人事の最終決定者。多忙で現場の細部は下が握ることも"),
        ("准教授・講師", "実務の要であり次期教授候補。関係構築は先行投資"),
        ("医局長", "医局の雑務・人事、行事の窓口。教授の信頼が厚く影響力大"),
        ("助教・医員・専攻医", "実処方と臨床研究の担い手。数年後は関連病院の幹部へ")]
colB = [("病院教授", "臨床・病院運営に強い。採用・薬審には効くが医局人事権は別のことも"),
        ("特任教授", "寄附講座・外部資金による任用。研究・講演に強いが医局人事は限定的"),
        ("客員・非常勤", "本務は他施設。院内の決定権は限定的だがネットワークのハブに"),
        ("名誉教授", "現役の決定権はない。人脈・影響力は健在。研究会の重鎮")]
card(s, 0.6, 1.9, 6.0, 0.5, [P([R("院内の本流ライン", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
card(s, 6.75, 1.9, 6.0, 0.5, [P([R("読み違えやすい肩書き（要・個別確認）", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
for ci, (rows_, col) in enumerate(((colA, GREEN), (colB, NAVY))):
    x = 0.6 + ci * 6.15
    y = 2.48
    for t, d in rows_:
        card(s, x, y, 6.0, 0.92,
             [P([R(t, 13, True, col)], space_after=4), P([R(d, 11, False, INK)], line=1.2)],
             fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
        y += 1.0
card(s, 0.6, 6.5, 12.15, 0.45,
     [P([R("見極めの5点：① 財源　② 任期　③ 実権　④ 本務教授・医局長・薬剤部との距離　⑤ COIの扱い", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 34 付録G コンプラ
s = add_slide()
header(s, "APPENDIX G", "参考：大学活動 コンプライアンスの5原則", kcolor=GRAY)
pr = [("① 施設ルールが最優先", "訪問・面会・資材配布のルールは施設ごとに違う。迷ったら守りに倒す"),
      ("② その場で約束しない", "寄附金・広告協賛の依頼は即答せず、必ず社内の申請・審査手続きへ"),
      ("③ 現行の文書で確認", "「前任者がやっていた」は根拠にならない。薬審・採用は施設ごとに毎回確認"),
      ("④ 自己判断しない", "基準はプロモーションコードと社内SOP。迷ったら相談してから動く"),
      ("⑤ 記録を残す", "依頼・回答・手続きの経緯を記録に。先生と自分の両方を守る")]
y = 2.0
for t, d in pr:
    card(s, 0.6, y, 3.6, 0.84, [P([R(t, 13, True, WHITE)])], fill=DEEP, radius=0.1, pad=0.18)
    card(s, 4.35, y, 8.4, 0.84, [P([R(d, 12.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.18)
    y += 0.93
txt(s, 4.35, 6.66, 8.4, 0.3,
    [P([R("※ 個別の案件は、必ず最新の社内規程と担当部門の指示に従ってください。", 11, False, GRAY)])])

# ================================================================ 35 付録H 疾患別の参考例
s = add_slide()
header(s, "APPENDIX H", "参考：疾患が変わると、影響力の見え方も変わる（架空の例）", kcolor=GRAY)
cases = [("C3腎症", GREEN,
          "大学・主要基幹病院の間で、疑う患者像、病理・補体評価、専門医への相談経路について共通認識がある",
          "病理や補体領域に詳しい大学医師から、関連基幹病院へ診断上の視点を発信する",
          "大学の「研究」「情報発信」の輪が効きやすい。まず疑ってもらう段階から"),
         ("IgA腎症", NAVY,
          "主要な大学・基幹病院で、患者選択、治療導入、フォローに関する考え方が整理されている",
          "診療経験を持つ基幹病院医師と大学医師が、施設間の治療課題を共有する",
          "基幹病院の「臨床」の輪も大きい。大学と基幹病院を組み合わせる")]
for i, (t, col, success, ring, note) in enumerate(cases):
    x = 0.6 + i * 6.15
    card(s, x, 1.9, 6.0, 0.6, [P([R(t, 17, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, x, 2.6, 6.0, 0.42, [P([R("目指したい状態", 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GREEN, radius=0.1)
    card(s, x, 3.07, 6.0, 1.0, [P([R(success, 12, False, INK)], line=1.3)],
         fill=PALE, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
    card(s, x, 4.17, 6.0, 0.42, [P([R("影響力の広がり方", 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=NAVY2, radius=0.1)
    card(s, x, 4.64, 6.0, 0.9, [P([R(ring, 12, False, INK)], line=1.3)],
         fill=PALEB, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
    card(s, x, 5.64, 6.0, 0.72, [P([R(note, 11.5, True, col)], line=1.25)],
         fill=WHITE, line=col, radius=0.1, pad=0.15)
card(s, 0.6, 6.48, 12.15, 0.45,
     [P([R("本編では扱いません。同じエリアでも、疾患が違えば重要施設もキーパーソンも変わります。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.15)

# ================================================================ 36 付録I ファシリテーター
s = add_slide()
header(s, "APPENDIX I", "ファシリテーター用メモ", kcolor=GRAY)
tips = [("当日の投影・時間",
         ["冒頭は タイトル → 4回のロードマップ → 本日のAgenda の3枚だけ使う",
          "0-9 オープニング／9-25 テーマ①／25-56 テーマ②／56-60 まとめ",
          "レクチャーは合計6分。話しすぎないことが最大のポイント"]),
        ("テーマ①のコツ",
         ["正解を教えない。参加者の経験を引き出す時間と割り切る",
          "3つの補助質問は画面に残したまま進める",
          "最後の2分で「重要だったこと」を1つ決めさせ、全体共有につなげる"]),
        ("藤さんの事例（10分）",
         ["成功事例ではなく「どの情報からつながりを読み取ったか」に焦点を",
          "③の図は、口頭説明よりも図を見せる時間を長く",
          "最後に「自分のエリアを見るとき、最初にどこを確認するか」を必ず聞く"]),
        ("テーマ②・締め方",
         ["個人ワークは「正確な組織図ではない」と最初に伝える",
          "全体共有は優れた戦略ではなく「視座が変わった点」を拾う",
          "行動宣言まで必ず4分残す。DAY3のチーム展開（営業所で共有）も一言添える"])]
for i, (t, lines) in enumerate(tips):
    x = 0.6 + (i % 2) * 6.15
    y = 1.9 + (i // 2) * 2.5
    card(s, x, y, 6.0, 0.55, [P([R(t, 14, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GRAY, radius=0.12)
    card(s, x, y + 0.6, 6.0, 1.7,
         [P([R("・" + l, 11.5, False, INK)], space_after=9, line=1.2) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
txt(s, 4.35, 6.9, 8.4, 0.3,
    [P([R("本資料の事例・人名はすべて架空です。", 11, False, GRAY)])])

# ---------------------------------------------------------------- save
prs.save(OUT)
print("saved:", OUT, "| slides:", len(prs.slides._sldIdLst))
