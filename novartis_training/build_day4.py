# -*- coding: utf-8 -*-
"""
Renal MR スキルアッププロジェクト DAY4
「ちょっと分かるだけで世界が変わる」 — テーマ：戦略的思考

DAY4_base_1-7.pptx の冒頭7枚を保持し（Agendaの文言のみ更新）、8枚目以降を生成。

■ 構成（計60分）
   オープニング 5分 ／ テーマ①「視座を変える」25分 ／
   テーマ②「順序を変える」25分 ／ エリア戦略・まとめ 5分

■ 到達目標（プロジェクト公式・戦略的思考）
   担当施設と周辺エリアに対する成功像・現状・課題・解決法を言語化できる

■ 設計の柱（企画ミーティング＋DAY1〜3の内容を反映）
   - 戦略的思考 ＝ ①視座（どこを見るか）× ②順序（どう考えるか）
   - DAY1の「影響力はテリトリーとニーズで決まる」を、自分のテリトリーの話へ拡張
   - 大学攻略 ≠ 任された範囲の攻略。大学の枠を外して範囲の中に大学を置き直す
   - 大学の機能（DAY1の教育・研究・臨床＋人事・派遣・発信・講演会）から選んで使う
   - 情報は成功像と仮説から逆算（DAY3の「取り方」に「取りに行く理由」を足す）
   - 「要望に応える活動」から「範囲の課題から動かす活動」へ
   - 言語化の道具は自由。4Sは整理の一例として付録に置く
   - 後半のBeyondは「プラス1」。全員必達にしない
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
AGENDA_LINES = ["■オープニング　5分",
                "■テーマ①「視座を変える」　25分",
                "■テーマ②「順序を変える」　25分",
                "■エリア戦略・まとめ　5分"]
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
header(s, "AGENDA", "本日の進め方 — 60分、大きく4つのブロックです")
blocks = [("■ オープニング", "5分", "3回で何が変わったか／戦略的思考とは何か", GREEN),
          ("■ テーマ①「視座を変える」", "25分", "大学の中から見る → 自分の任された範囲から見る", NAVY),
          ("■ テーマ②「順序を変える」", "25分", "情報から考える → 成功像から逆算して考える", NAVY),
          ("■ エリア戦略・まとめ", "5分", "Beyond：影響を広げる／自分の範囲に責任を持つ", GREEN)]
y = 1.95
for t, tm, d, col in blocks:
    card(s, 0.6, y, 6.3, 1.02, [P([R(t, 16, True, WHITE)])], fill=col, radius=0.1, pad=0.2)
    card(s, 7.0, y, 1.15, 1.02, [P([R(tm, 14, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 8.28, y, 4.47, 1.02, [P([R(d, 11.5, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 1.16
card(s, 0.6, 6.42, 12.15, 0.55,
     [P([R("テーマ①②はどちらも「レクチャー10分 → ワーク10分 → 共有5分」。", 13, True, DEEP),
         R("　手を動かす時間を長く取っています。", 12.5, False, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 9 戦略的思考とは
s = add_slide()
header(s, "TODAY'S DESIGN", "第4回のテーマは「戦略的思考」です")
pillars = [("採用", "DAY 1", GREEN2), ("面会", "DAY 2", GREEN2),
           ("情報収集", "DAY 3", GREEN2), ("戦略的思考", "DAY 4", DEEP)]
for i, (t, d, col) in enumerate(pillars):
    x = 0.6 + i * 3.12
    card(s, x, 1.85, 2.95, 0.85,
         [P([R("◆ " + t, 15, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(d, 11.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
card(s, 0.6, 2.85, 12.15, 0.75,
     [P([R("DAY4の到達目標：", 14, True, DEEP),
         R("担当施設と周辺エリアに対する", 15, True, INK),
         R("成功像・現状・課題・解決法を言語化できる", 15, True, RED)], align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
txt(s, 0.6, 3.85, 12.15, 0.4,
    [P([R("戦略的思考といっても、難しい理論は使いません。今日変えるのは、この2つだけです。", 14, True, INK)],
       align=PP_ALIGN.CENTER)])
two = [("① 視座", "どこを見るか", "大学の中から見る　→　自分の任された範囲から見る",
        "テーマ①（25分）", NAVY, PALEB),
       ("② 順序", "どう考えるか", "情報から考える　→　成功像から逆算して考える",
        "テーマ②（25分）", GOLD, YPALE)]
for i, (t, sub, d, tag, col, fill) in enumerate(two):
    x = 0.6 + i * 6.15
    card(s, x, 4.3, 6.0, 0.6,
         [P([R(t + "　", 17, True, WHITE), R(sub, 12.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
    card(s, x, 4.96, 6.0, 0.95, [P([R(d, 14, True, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=fill, radius=0.1, pad=0.16)
    card(s, x + 1.75, 5.99, 2.5, 0.42, [P([R(tag, 11.5, True, col)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=col, radius=0.2)
card(s, 0.6, 6.5, 12.15, 0.42,
     [P([R("戦略的思考 ＝ 「どこを見るか」×「どう考えるか」。この2つが変わると、同じ活動でも意味が変わります。", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 10 3回で手に入れた力
s = add_slide()
header(s, "LOOK BACK", "3回で、あなたはこれだけの力を手に入れました")
days = [("DAY 1", "大学・基幹病院のイロハ", GREEN,
         ["大学の使命（教育・研究・臨床）と、医師派遣による地域への影響",
          "影響力はテリトリーとニーズで決まる（GP／HP／HS）",
          "教授の裁量権と「医局の集合体」という構造／薬審・採用の流れ"],
         "先生の“影響力の大きさ”が読める"),
        ("DAY 2", "「会えない」を「会える」に", NAVY,
         ["未訪問 → 初回接点 → 仮説面会 → 定期面会 の設計",
          "Best Time / Best Place：ルーチンワークの把握とカレンダー管理",
          "「会う理由」を設計し、次回の約束を残す／My teacherをつくる"],
         "会いたい先生に“会える”"),
        ("DAY 3", "やっぱりMRは情報が命", GOLD,
         ["ドライ情報 × ウェット情報で顧客理解の解像度を上げる",
          "分からないことは small b として面会に持ち込む",
          "面会後は「なぜ」を分解し、仮説を立てて次の面会へ"],
         "必要な情報が“取れる”")]
for i, (d, t, col, lines, gain) in enumerate(days):
    x = 0.6 + i * 4.09
    card(s, x, 1.85, 3.9, 0.72,
         [P([R(d + "　", 14.5, True, WHITE), R(t, 11.5, True, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
    card(s, x, 2.64, 3.9, 2.05,
         [P([R("・" + l, 11, False, INK)], line=1.25, space_after=8) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
    card(s, x, 4.78, 3.9, 0.5, [P([R("→ " + gain, 12, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, radius=0.12)
card(s, 0.6, 5.5, 12.15, 1.3,
     [P([R("では、その力を —— どこに、何のために使いますか？", 22, True, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("大学に行ける。会える。情報も取れる。DAY4は、そこで終わらせずに「使い道を自分で決める」回です。", 13, False, MINT)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 11 チェックイン（Teamsチャット）
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, 3.4, 0.42, "CHECK IN　｜　3分", fill=GREEN)
card(s, 0.6, 0.95, 12.15, 1.15,
     [P([R("Q. この3回の勉強会で、あなたの", 23, True, INK),
         R("「大学の見方」は変わりましたか？", 23, True, RED),
         R("　", 23, False, INK)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("大学担当としての", 23, True, INK), R("「自信」はつきましたか？", 23, True, RED)],
        align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.06, pad=0.16)
card(s, 3.15, 2.28, 7.0, 0.65,
     [P([R("Teamsチャットに、思ったことを自由に書き込んでください", 15, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.15)
txt(s, 0.6, 3.15, 12.15, 0.35,
    [P([R("形式も長さも自由です。ひと言だけでもOK。難しく考えずに、思い浮かんだことをどうぞ。", 13.5, True, INK)],
       align=PP_ALIGN.CENTER)])
hints = [("思い出すきっかけ①", "大学に行くとき、以前と違うことはありますか？", GREEN),
         ("思い出すきっかけ②", "会う人・聞くことは、変わりましたか？", NAVY),
         ("思い出すきっかけ③", "まだ「ここが分からない」と思うことは？", GOLD)]
for i, (t, q, col) in enumerate(hints):
    x = 0.6 + i * 4.09
    card(s, x, 3.65, 3.9, 0.45, [P([R(t, 11.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, x, 4.16, 3.9, 0.95, [P([R(q, 13, True, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
card(s, 0.6, 5.35, 12.15, 1.55,
     [P([R("「変わった」でも「あまり変わっていない」でも、どちらでも大歓迎です。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=7),
      P([R("感想・気づき・モヤモヤ、なんでも構いません。正解はありません。", 13, False, INK)],
        align=PP_ALIGN.CENTER, space_after=7),
      P([R("他の人の投稿も、ぜひ読んでみてください。同じことを感じている仲間が、全国にいると分かります。", 12.5, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, radius=0.1, pad=0.18)
footer(s)

# ================================================================ 12 テーマ①扉
s = add_slide()
section(s, "①", "視座を変える", "テーマ①　｜　25分（レクチャー10分・ワーク10分・共有5分）",
        "大学を攻略すれば、あなたの範囲の課題は解決しますか？",
        ["DAY1で考えた「先生のテリトリー」を、今日は「自分のテリトリー」に置き換える",
         "大学に固執しない。大学は、エリアマッピングの中の「1施設」として置き直す",
         "その1施設が持つ影響力を、どう活かすかを自分で決める"])

# ================================================================ 13 DAY1復習：テリトリー
s = add_slide()
header(s, "THEME ①", "DAY1の復習 — 影響力は「テリトリー」と「ニーズ」で決まる", "25分", kcolor=NAVY,
       lead="皆さんの担当は「基幹病院（HP）」と「大学病院（HS）」。この2つでも、見ている世界もニーズもまったく違います。")
tiers = [("HP（基幹病院）", ["1病院", "医師会・医療圏", "関連病院・出身医局"],
          "紹介率を上げたい・関連病院と協働したい・院内で負けたくない", GREEN),
         ("HS（大学病院）", ["県内", "県内＋他大学・専門領域", "日本全体・学会・世界"],
          "研修医が欲しい・論文を出したい・県内での存在感が欲しい", NAVY)]
for i, (t, terr, need, col) in enumerate(tiers):
    x = 0.6 + i * 4.55
    card(s, x, 2.1, 4.35, 0.5, [P([R(t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    yy = 2.68
    for j, tr in enumerate(terr):
        card(s, x + 0.22 * (2 - j), yy, 4.35 - 0.44 * (2 - j), 0.42,
             [P([R(tr, 11, True, col)], align=PP_ALIGN.CENTER)],
             fill=PALE2, line=col, radius=0.2)
        yy += 0.5
    card(s, x, 4.28, 4.35, 0.7, [P([R("ニーズ：" + need, 10.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
card(s, 9.85, 2.1, 2.9, 0.5, [P([R("GP（開業医）", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
card(s, 9.85, 2.68, 2.9, 2.3,
     [P([R("今回、皆さんの担当施設ではありません。", 11.5, True, INK)], space_after=8, line=1.25),
      P([R("ただし、患者さんの流れの起点として、範囲の絵の中には存在します。", 11, False, INK)], space_after=8, line=1.25),
      P([R("→ 「担当する施設」と「範囲の中にある施設」は別モノ。両方を見るのが戦略的思考です。", 11, True, GRAY)], line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.15)
card(s, 0.6, 5.15, 12.15, 1.5,
     [P([R("DAY1では「先生のテリトリーはどこまでか」を考えました。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("今日は、その問いを自分に向けます。", 17, True, MINT)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("あなたのテリトリーは、どこですか？　その中で、大学はどれくらいの大きさですか？", 21, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 14 かごを取り払う
s = add_slide()
header(s, "THEME ①", "「大学の中から」ではなく「範囲の中に大学を置く」", "25分", kcolor=NAVY)
card(s, 0.6, 1.85, 5.8, 0.62,
     [P([R("これまで：大学の中から、周りを見る", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GRAY, radius=0.1)
card(s, 0.6, 2.55, 5.8, 2.6,
     [P([R("・視点の中心は「大学」", 12.5, False, INK)], space_after=10),
      P([R("・成功像が、大学内の採用・処方・面会・講演会になりやすい", 12.5, False, INK)], space_after=10, line=1.25),
      P([R("・大学から依頼されたことに応える活動になりやすい", 12.5, False, INK)], space_after=10, line=1.25),
      P([R("・大学を攻略すれば解決する、という前提に立ちやすい", 12.5, False, INK)], line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
arrow(s, 6.62, 3.5, 0.65, 0.6, color=GOLD)
card(s, 7.5, 1.85, 5.25, 0.62,
     [P([R("これから：範囲の中に、大学を置く", 14.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.1)
card(s, 7.5, 2.55, 5.25, 2.6,
     [P([R("・視点の中心は「自分の任された範囲」", 12.5, True, INK)], space_after=10, line=1.25),
      P([R("・成功像は、範囲全体がどうなっているか", 12.5, True, INK)], space_after=10, line=1.25),
      P([R("・大学は、エリアマッピングの中の「1施設」", 12.5, True, RED)], space_after=10, line=1.25),
      P([R("・大学が中心とは限らない。基幹病院が中心の範囲もある", 12.5, True, INK)], line=1.25)],
     fill=PALE, line=GREEN, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 0.6, 5.4, 12.15, 1.4,
     [P([R("「大学を軸としたエリア攻略」ではなく、「エリア攻略のために大学を活かす」。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("表面的には同じ「教授面会」「講演会」でも、大学だけを見て実施した活動と、範囲全体を見て大学を活かした活動では、", 13, False, INK),
         R("意味も成果の質もまったく違います。", 13, True, RED)], align=PP_ALIGN.CENTER, line=1.25)],
     fill=YPALE, radius=0.1, pad=0.2)

# ================================================================ 15 答えは人によって違う
s = add_slide()
header(s, "THEME ①", "だから、答えは人によって違います", "25分", kcolor=NAVY,
       lead="大学が強い地域もあれば、基幹病院のほうが症例数・影響力を持つ地域もあります。")
pats = [("① 一つの大学が中心",
         [("A大", 1.15, 1.05, 0.45, PALE, DEEP), ("基幹", 0.62, 2.1, 1.3, WHITE, GRAY),
          ("基幹", 0.62, 0.35, 1.4, WHITE, GRAY)],
         "大学の方針が範囲全体に波及する。医局人事と情報発信が効く", GREEN),
        ("② 複数の大学が並ぶ",
         [("A大", 0.95, 0.5, 0.5, PALE, DEEP), ("B大", 0.95, 1.75, 1.1, PALE, GREEN2),
          ("基幹", 0.6, 1.35, 0.3, WHITE, GRAY)],
         "1大学では範囲は動かない。両大学に共通する課題を探す", NAVY),
        ("③ 基幹病院が中心",
         [("基幹", 1.2, 0.95, 0.5, PALEB, NAVY), ("A大", 0.7, 0.4, 1.5, PALE, DEEP),
          ("基幹", 0.65, 2.1, 1.45, PALEB, NAVY2)],
         "症例数・実務の影響力は基幹病院。大学は研究・教育で効かせる", GOLD),
        ("④ 大学の影響が広域に",
         [("A大", 1.1, 0.5, 0.45, PALE, DEEP), ("県外", 0.65, 2.0, 0.4, WHITE, GRAY),
          ("県外", 0.65, 2.1, 1.45, WHITE, GRAY)],
         "先生の影響が担当範囲を超える。営業所・全国への展開を考える", RED)]
for i, (t, circles, note, col) in enumerate(pats):
    x = 0.6 + i * 3.12
    card(s, x, 2.1, 2.95, 0.5, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    shape(s, x, 2.65, 2.95, 2.45, fill=PALE2, line=LGRAY, radius=0.04)
    for lbl, d, dx, dy, fc, lc in circles:
        circle(s, x + dx, 2.8 + dy, d, lbl, fill=fc, line=lc,
               size=10 if d > 0.9 else 8.5, color=lc)
    card(s, x, 5.2, 2.95, 1.1, [P([R(note, 11, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
card(s, 0.6, 6.45, 12.15, 0.45,
     [P([R("正解の型はありません。大事なのは、", 12.5, False, INK),
         R("「自分は任された範囲をこう見ている」と言えること", 12.5, True, RED),
         R("です。", 12.5, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 16 大学のどの機能を使うか
s = add_slide()
header(s, "THEME ①", "大学の「どの機能」を使いますか？", "25分", kcolor=NAVY,
       lead="DAY1で学んだとおり、大学病院はトップダウン組織ではなく「医局の集合体」。使える機能は複数あります。")
funcs = [("教育", "若手が学び、数年後に範囲の病院へ散っていく", GREEN),
         ("研究", "エビデンスをつくり、学会・論文で外へ届く", GREEN),
         ("臨床", "症例が集まる。専門治療の実施と評価の場", GREEN),
         ("医局人事", "関連病院の部長・医長を決める。方針が波及する", NAVY),
         ("医師派遣", "誰がどの施設に行くか。範囲の布陣が決まる", NAVY),
         ("情報発信", "治療方針が、時間差で範囲の標準になる", GOLD),
         ("講演会・研究会", "地域の医師が集まる場。共通認識をつくれる", GOLD)]
for i, (t, d, col) in enumerate(funcs):
    x = 0.6 + (i % 4) * 3.12
    y = 2.15 + (i // 4) * 1.42
    card(s, x, y, 2.95, 0.48, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, x, y + 0.53, 2.95, 0.8, [P([R(d, 10.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
card(s, 9.96, 3.57, 2.79, 1.33,
     [P([R("この7つのうち、", 12, True, WHITE)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("あなたの課題を解くのに\n必要なのはどれ？", 13, True, YELL)], align=PP_ALIGN.CENTER, line=1.25)],
     fill=DEEP, radius=0.1, pad=0.14)
card(s, 0.6, 5.2, 12.15, 0.75,
     [P([R("DAY1の「教授の裁量権」を思い出してください：", 13, True, DEEP),
         R("①臨床機会の配分　②医局人事・異動　③教授会・教授選　④研究・教育の方向性", 12.5, False, INK)],
       align=PP_ALIGN.CENTER, space_after=4),
      P([R("＝ 教授は「処方者」ではなく、機能を動かせる人。誰を通じて、どの機能を動かすかを設計します。", 12, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=PALEB, radius=0.1, pad=0.16)
card(s, 0.6, 6.05, 12.15, 0.85,
     [P([R("「大学を攻略する」ではなく、「この課題を解くために、大学のこの機能を使う」と言えるか。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("例：範囲の紹介が遅い → 使うのは", 12.5, False, INK), R("情報発信と講演会", 12.5, True, RED),
         R("　／　例：基幹病院の治療方針を変えたい → 使うのは", 12.5, False, INK),
         R("医局人事と医師派遣", 12.5, True, RED)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1, pad=0.16)

# ================================================================ 17 ワーク①
s = add_slide()
header(s, "WORK ①", "自分のテリトリーを、1枚の絵にする", "10分", kcolor=GREEN)
card(s, 0.6, 1.8, 8.05, 0.78,
     [P([R("手元の紙に、あなたの任された範囲を描いてください。描き方は自由。上手さは関係ありません。", 14, True, INK)],
       line=1.2)],
     fill=PALE, radius=0.08, pad=0.16)
steps = [("4分", "施設を丸で置く", "担当する大学・基幹病院を全部。丸の大きさ＝あなたが考える重要度"),
         ("3分", "つながりを線で結ぶ", "患者の流れ／医師の人事・派遣／情報・診療方針の流れ"),
         ("3分", "大学の丸に機能を書く", "教育・研究・臨床・医局人事・医師派遣・情報発信・講演会から選ぶ")]
y = 2.75
for tm, t, d in steps:
    circle(s, 0.6, y, 0.7, tm, fill=GREEN, size=12)
    card(s, 1.5, y, 7.15, 0.7,
         [P([R(t, 12.5, True, DEEP)], space_after=2), P([R(d, 10.5, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.85
card(s, 0.6, 5.35, 8.05, 1.45,
     [P([R("描き終えたら、自分に問いかけてください。", 13, True, INK)], space_after=6),
      P([R("あなたの絵で、大学は何番目に大きいですか？", 18, True, RED)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("一番大きくなくても、まったく問題ありません。それがあなたの範囲の実態です。", 11.5, False, GRAY)])],
     fill=YPALE, radius=0.08, pad=0.2)
card(s, 8.9, 1.8, 3.85, 5.0,
     [P([R("迷ったときは", 14.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=12),
      P([R("・施設が多すぎる → 重要そうな5〜6施設だけでOK", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・担当外の施設（クリニック等）は、患者の流れが分かる範囲で薄く描けば十分", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・重要度が決められない →「この施設が変われば、範囲全体が変わるか？」で判断", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・線が分からない → 分からない線は点線＋「？」で。それが次に取りに行く情報", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・大学が複数ある → 全部描く。関係が分からなければ、それも「？」", 11.5, False, WHITE)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06, pad=0.2)

# ================================================================ 18 共有①
s = add_slide()
header(s, "SHARE ①", "共有：描いた絵を見せ合って、自由に話しましょう", "5分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.72,
     [P([R("3〜4人1組。順番も型も決めません。描いた絵を画面に映して、思ったことを話してください。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
topics = [("話のきっかけ①", "あなたの範囲で、一番大きい施設はどこ？　それはなぜ？"),
          ("話のきっかけ②", "大学と基幹病院、いまはどちらが効いていますか？"),
          ("話のきっかけ③", "描いてみて、意外だったこと・困ったことは？")]
y = 2.85
for t, q in topics:
    card(s, 0.6, y, 2.6, 0.72, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GREEN, radius=0.12)
    card(s, 3.3, y, 9.45, 0.72, [P([R(q, 14, True, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 0.85
card(s, 0.6, 5.5, 12.15, 0.75,
     [P([R("どれから話しても、全部飛ばして別の話をしてもOK。他の人の話に乗っかるのも大歓迎です。", 13.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE2, line=GREEN, radius=0.12, pad=0.14)
card(s, 0.6, 6.35, 12.15, 0.55,
     [P([R("他の人の絵は、最高の教材です。「大学が中心じゃない範囲もあるのか」— 自分の絵の空白が見えてきます。", 12.5, True, INK)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 19 テーマ②扉
s = add_slide()
section(s, "②", "順序を変える", "テーマ②　｜　25分（レクチャー10分・ワーク10分・共有5分）",
        "その情報は、何のために取りましたか？",
        ["情報を集めてから考えるのではなく、成功像から逆算して取りに行く",
         "自分の範囲のWINと、大学・医局のWINが重なるところに打ち手を置く",
         "成功像・現状・課題・解決法を、自分の言葉で言語化する"])

# ================================================================ 20 順序が逆
s = add_slide()
header(s, "THEME ②", "情報は、集めるほど良いわけではありません", "25分", kcolor=NAVY,
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
conn(s, 12.63, 4.3, 12.63, 5.32, color=GREEN2, weight=1.6, dash="dash")
conn(s, 1.0, 5.32, 12.63, 5.32, color=GREEN2, weight=1.6, dash="dash")
arrow(s, 0.88, 4.35, 0.24, 1.0, color=GREEN2, direction="up")
txt(s, 4.4, 5.38, 4.5, 0.3, [P([R("← 回しながら精度を上げる", 10.5, True, GREEN)], align=PP_ALIGN.CENTER)])
card(s, 0.6, 5.82, 12.15, 1.0,
     [P([R("DAY3では「情報の取り方」を学びました。今日足すのは、「取りに行く理由」です。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("範囲をどうしたいかというビジョンと、大学・基幹病院にどんな役割が要るかという仮説があるから、確かめるために情報を取りに行く。", 12.5, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=PALE, radius=0.1, pad=0.18)

# ================================================================ 21 WIN-WINの重なり
s = add_slide()
header(s, "THEME ②", "戦略は、WIN-WIN の「重なり」にあります", "25分", kcolor=NAVY,
       lead="DAY3の ROTF3「顧客の意思決定のニーズを正確に捉え、Win-Winの関係となる提案を行う」を、エリア規模でやります。")
# 2円のベン図
set_alpha(shape(s, 1.55, 2.2, 3.6, 3.6, fill=NAVY2, line=NAVY, line_w=1.8, kind=MSO_SHAPE.OVAL), 78)
set_alpha(shape(s, 3.55, 2.2, 3.6, 3.6, fill=GREEN, line=GREEN, line_w=1.8, kind=MSO_SHAPE.OVAL), 78)
txt(s, 1.35, 2.55, 2.1, 0.7,
    [P([R("自分の範囲の\n成功像", 12.5, True, NAVY)], align=PP_ALIGN.CENTER, line=1.2)])
txt(s, 5.25, 2.55, 2.1, 0.7,
    [P([R("大学・医局が\nしたいこと", 12.5, True, GREEN)], align=PP_ALIGN.CENTER, line=1.2)])
txt(s, 3.7, 3.55, 1.3, 0.9,
    [P([R("戦略", 17, True, RED)], align=PP_ALIGN.CENTER, space_after=2),
     P([R("の核", 11, True, RED)], align=PP_ALIGN.CENTER)])
txt(s, 1.55, 5.95, 5.6, 0.35,
    [P([R("重なりが大きいほど、打ち手は動きやすい", 12, True, DEEP)], align=PP_ALIGN.CENTER)])
cases = [("A", "大学の要望に応えるだけ",
          "大学はWIN。でも自分の範囲は変わらない。担当者の介入価値が見えない", GRAY, WHITE),
         ("B", "自分の範囲の都合だけ",
          "範囲としては正しい。でも医局にメリットがなく、動いてもらえない", GRAY, WHITE),
         ("C", "WIN-WIN　← ここが戦略",
          "範囲の課題と、医局がしたいことが重なるところに打ち手を置く。だから相手も本気で動く", RED, RPALE)]
y = 2.2
for tag, t, d, col, fill in cases:
    circle(s, 7.6, y + 0.12, 0.55, tag, fill=col, size=14)
    card(s, 8.35, y, 4.4, 1.15,
         [P([R(t, 13, True, col)], space_after=4),
          P([R(d, 10.5, False, INK)], line=1.2)],
         fill=fill, line=col if col == RED else LGRAY, radius=0.1, pad=0.14)
    y += 1.3
card(s, 0.6, 6.4, 12.15, 0.55,
     [P([R("実例：複数の大学がある地域で、一つの大学の要望に応えるのではなく、範囲の課題と両大学がやりたいことの重なりを見つけて共通の方向へ乗せた講演会。", 11.5, False, INK)],
       align=PP_ALIGN.CENTER, line=1.2)],
     fill=YPALE, radius=0.12, pad=0.12)

# ================================================================ 21.5 医局のWIN × 影響力の使い方
s = add_slide()
header(s, "THEME ②", "医局は何をしたいのか／その影響力を、どう活かすか", "25分", kcolor=NAVY)
card(s, 0.6, 1.85, 6.0, 0.55,
     [P([R("腎臓内科の医局が「したいこと」の例", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
wants = ["専門性の高い症例を集めたい（紹介を増やしたい）",
         "若手・専攻医を増やしたい、育てたい",
         "研究データを出したい・論文を書きたい",
         "関連病院との連携を強めたい／派遣先を確保したい",
         "県内・地域での存在感を高めたい",
         "学会・研究会で発信したい"]
card(s, 0.6, 2.48, 6.0, 2.45,
     [P([R("・" + w, 12, False, INK)], line=1.2, space_after=8) for w in wants],
     fill=PALE, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
card(s, 0.6, 5.03, 6.0, 0.8,
     [P([R("DAY1で見た「HSのニーズ」そのものです。", 12, True, DEEP)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("「先生が困っていること」だけでなく「先生がやりたいこと」を聞く。", 11.5, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, radius=0.1, pad=0.13)
card(s, 6.75, 1.85, 6.0, 0.55,
     [P([R("影響力の活かし方 ＝ 誰に × 何を × どこまで", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
how = [("誰に", "影響力を持つのは誰か", "教授／医局長／若手／連携の要。キーパーソンは1人とは限らない", NAVY),
       ("何を", "どの機能を動かすか", "教育・研究・臨床・医局人事・医師派遣・情報発信・講演会から選ぶ", GOLD),
       ("どこまで", "影響をどこへ届けるか", "施設内／関連病院／担当範囲／営業所・広域。どこまで届かせたいかを先に決める", GREEN)]
y = 2.48
for t, sub, d, col in how:
    card(s, 6.75, y, 1.5, 0.75, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, 8.35, y, 4.4, 0.75,
         [P([R(sub, 11, True, col)], space_after=2), P([R(d, 10.5, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
    y += 0.85
card(s, 6.75, 5.03, 6.0, 0.8,
     [P([R("大学に固執しない。大学は「1施設」。", 12, True, RED)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("その1施設が持つ影響力を、範囲のどこに効かせるかを設計します。", 11.5, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=WHITE, line=RED, radius=0.1, pad=0.13)
card(s, 0.6, 5.98, 12.15, 0.9,
     [P([R("問いはシンプルです。", 14, True, DEEP),
         R("「先生がやりたいこと」を叶えながら、「私の範囲の課題」も同時に解ける打ち手は何か？", 15, True, RED)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("これが見つかれば、お願いする活動ではなく、一緒にやる活動になります。", 12.5, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 22 言語化する4つの問い
s = add_slide()
header(s, "THEME ②", "言語化する — 4つの問い ＋ 3", "25分", kcolor=NAVY,
       lead="プロジェクトの到達目標「成功像・現状・課題・解決法を言語化できる」を、問いの形にしました。")
quads = [(0.6, 2.05, "① 成功像", "任された範囲が、どうなっていたら最高ですか？", GREEN, PALE),
         (6.75, 2.05, "② 現状・課題", "いま、その理想とどこがどう違いますか？", NAVY, PALEB),
         (0.6, 3.45, "③ 原因", "なぜ、そのギャップが生まれていますか？", GOLD, YPALE),
         (6.75, 3.45, "④ 解決法", "そのギャップを埋めるために、何を起こしますか？", RED, RPALE)]
for x, y, t, d, col, fill in quads:
    card(s, x, y, 6.0, 0.45, [P([R(t, 13.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, y + 0.5, 6.0, 0.82, [P([R(d, 12, False, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=fill, radius=0.1, pad=0.14)
plus = [("＋ 大学・医局のWIN", "相手は、何をしたいのですか？"),
        ("＋ 使う機能・影響力", "誰に・何を・どこまで効かせますか？"),
        ("＋ 自分の介入点", "自分にしかできないことは何ですか？")]
for i, (t, d) in enumerate(plus):
    x = 0.6 + i * 4.09
    card(s, x, 4.82, 3.9, 0.45, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=DEEP, radius=0.1)
    card(s, x, 5.32, 3.9, 0.6, [P([R(d, 11.5, False, INK)], align=PP_ALIGN.CENTER, line=1.2)],
         fill=MINT, radius=0.1, pad=0.12)
card(s, 0.6, 6.05, 12.15, 0.85,
     [P([R("①〜④が「自分の範囲をどうしたいか」、＋3が「そのために誰の・どの影響力を、どう活かすか」。", 13, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=4),
      P([R("形式は自由です。", 12.5, True, RED),
         R("箇条書きでも絵への書き込みでも構いません（整理の一例として「4Sシート」を付録Bに用意）。整ったシートより、「なぜ重要か」を説明できることが大切です。", 12, False, INK)],
        align=PP_ALIGN.CENTER, line=1.2)],
     fill=PALE, radius=0.12, pad=0.14)

# ================================================================ 23 記入例
s = add_slide()
header(s, "THEME ②", "言語化の例：複数の大学がある地域（架空の例）", "25分", kcolor=NAVY)
ex = [(0.6, 1.8, "① 成功像", GREEN, PALE,
       "範囲の基幹病院でも専門治療が必要な患者さんが適切に見極められ、必要な患者さんが大学に集まっている。"),
      (6.75, 1.8, "② 現状・課題", NAVY, PALEB,
       "基幹病院ごとに判断がばらつく。A大学とB大学で治療方針の温度差があり、両大学の関連病院の先生が迷っている。"),
      (0.6, 3.25, "③ 原因", GOLD, YPALE,
       "なぜばらつく？→判断の目安が共有されていない →なぜ？→範囲共通の基準がない →なぜ？→両大学と基幹病院が同じ場で話す機会がない。"),
      (6.75, 3.25, "④ 解決法", RED, RPALE,
       "両大学と主要な基幹病院が同席する会を企画し、範囲共通の判断の目安を、両大学の連名で発信してもらう。")]
for x, y, t, col, fill, d in ex:
    card(s, x, y, 6.0, 0.45, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, y + 0.49, 6.0, 0.92, [P([R(d, 10.5, False, INK)], line=1.25)],
         fill=fill, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.13)
plus_ex = [("＋ 大学・医局のWIN", "A大学＝県内での存在感を高めたい／B大学＝関連病院との連携を強めたい　→ どちらも「関連病院に発信する場」を求めていた"),
           ("＋ 使う機能・影響力", "誰に＝両大学の教授と医局長／何を＝情報発信と講演会／どこまで＝範囲の基幹病院まで"),
           ("＋ 自分の介入点", "両大学の関係性を踏まえた会の設計と、両医局長への事前相談は、範囲全体を見ている自分にしかできない")]
y = 4.68
for t, d in plus_ex:
    card(s, 0.6, y, 3.0, 0.48, [P([R(t, 11.5, True, WHITE)])], fill=DEEP, radius=0.1, pad=0.12)
    card(s, 3.75, y, 9.0, 0.48, [P([R(d, 10.5, False, INK)])], fill=MINT, radius=0.1, pad=0.12)
    y += 0.56
card(s, 0.6, 6.42, 12.15, 0.5,
     [P([R("注目：この会は「大学から頼まれた会」でも「こちらの都合の会」でもありません。", 12, True, RED),
         R("範囲の課題と、両大学がしたいことの重なりに置いた会です。", 12, True, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.15)

# ================================================================ 24 ワーク②
s = add_slide()
header(s, "WORK ②", "自分の範囲を、4つの問いで言語化する", "10分", kcolor=GREEN)
card(s, 0.6, 1.8, 8.05, 0.78,
     [P([R("さきほど描いた絵を横に置いて、範囲の戦略を言葉にします。完璧でなくて構いません。", 14, True, INK)], line=1.2)],
     fill=PALE, radius=0.08, pad=0.16)
steps = [("3分", "① 成功像 ② 現状・課題", "絵を見ながら「範囲がどうなっていたら最高か」から書く"),
         ("3分", "③ 原因 ＋ 大学・医局のWIN", "なぜ？を3回。あわせて「相手は何をしたいか」も書き出す"),
         ("4分", "④ 解決法 ＋ 影響力・介入点", "2つのWINが重なる打ち手は何か。誰に・何を・どこまで効かせるか")]
y = 2.75
for tm, t, d in steps:
    circle(s, 0.6, y, 0.7, tm, fill=GREEN, size=12)
    card(s, 1.5, y, 7.15, 0.7,
         [P([R(t, 12.5, True, DEEP)], space_after=2), P([R(d, 10.5, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.85
card(s, 0.6, 5.35, 8.05, 1.45,
     [P([R("合言葉：整った戦略より、語れる戦略。", 17, True, RED)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("空欄があってもかまいません。偏っていてもかまいません。1つでも「これが重要だ」と言い切れるものがあれば、今日は成功です。", 11.5, False, INK)],
        line=1.25)],
     fill=YPALE, radius=0.08, pad=0.2)
card(s, 8.9, 1.8, 3.85, 5.0,
     [P([R("手が止まったら", 14.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=12),
      P([R("・成功像が出ない →「1年後、上司に自慢したい範囲の姿」を想像する", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・課題が出ない → 絵の中で詰まっている線を探す（紹介・人事・情報）", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・相手のWINが分からない → それが次に聞きに行くこと。「先生は今、何をやりたいですか？」", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("・役割が決まらない → 大学の7つの機能に戻り、必要なものを1つだけ選ぶ", 11.5, False, WHITE)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06, pad=0.2)

# ================================================================ 25 共有②
s = add_slide()
header(s, "SHARE ②", "共有：グループで、自由にディスカッション", "5分", kcolor=GREEN)
card(s, 0.6, 1.82, 12.15, 0.68,
     [P([R("3〜4人1組。発表会ではありません。テーマは用意しましたが、話したいことから自由にどうぞ。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
themes = [("A", "いま、自分の範囲で一番動かしたいことは何ですか？", GREEN),
          ("B", "その大学・医局は、何をやりたいと思っていますか？　（分からなければ、それも話題に）", NAVY),
          ("C", "大学と基幹病院、どちらに効かせるのが早いと思いますか？", GOLD),
          ("D", "これまでで「うまくいった」「難しかった」と感じた経験", RED)]
y = 2.75
for tag, q, col in themes:
    circle(s, 0.6, y, 0.6, tag, fill=col, size=14)
    card(s, 1.42, y, 11.33, 0.6, [P([R(q, 13.5, True, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 0.72
card(s, 0.6, 5.7, 6.0, 1.15,
     [P([R("進め方のルールは1つだけ", 13, True, GREEN)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("順番を決めず、思いついた人から話す。人の話に乗っかるのも大歓迎です。", 12, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=PALE2, line=GREEN, radius=0.1, pad=0.15)
card(s, 6.75, 5.7, 6.0, 1.15,
     [P([R("うまくまとまらなくて当然です", 13, True, GOLD)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("今日はじめて考えたことです。詰まった箇所が、そのまま持ち帰りの宿題になります。", 12, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=YPALE, radius=0.1, pad=0.15)

# ================================================================ 26 Beyond 影響の輪
s = add_slide()
header(s, "BEYOND", "影響の輪 — 得た情報とメッセージを、どこまで届けるか", "5分", kcolor=GOLD,
       lead="ここからは発展的な視点です。全員が今日到達する必要はありません。持ち帰ってみてください。")
rings = [("施設の中", 4.5, GREEN2), ("関連病院", 3.55, GREEN),
         ("担当範囲", 2.6, NAVY2), ("営業所・営業部", 1.65, NAVY)]
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
         [P([R(t, 13, True, GOLD)], space_after=4), P([R(d, 11, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 1.17
card(s, 6.9, 6.35, 5.85, 0.55,
     [P([R("一施設で終わらせない。それが大学担当の価値。", 12.5, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 27 目指す状態
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

# ================================================================ 28 まとめ
s = add_slide()
header(s, "WRAP UP", "本日のまとめ — 戦略的思考は、この2つから始まる")
msgs = [("視座", "大学に固執しない。大学は範囲の中の「1施設」",
         "「大学を軸としたエリア攻略」ではなく、「エリア攻略のために大学を活かす」。", NAVY),
        ("順序", "情報からではなく、成功像から",
         "成功像 → 大学・医局に求める役割の仮説 → 必要な情報 → 取りに行く → 修正。", GOLD),
        ("重なり", "打ち手は、WIN-WINの重なりに置く",
         "自分の範囲の成功像と、医局がしたいことが重なるところ。だから相手も本気で動く。", GREEN)]
y = 1.95
for no, t, d, col in msgs:
    card(s, 0.6, y, 1.6, 1.05, [P([R(no, 15, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, 2.35, y, 10.4, 1.05,
         [P([R(t, 16, True, col)], space_after=4), P([R(d, 12.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.2)
    y += 1.2
card(s, 0.6, 5.6, 12.15, 1.25,
     [P([R("今日の持ち帰りは、これだけで十分です。", 14, True, WHITE)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("一度、大学という枠を外して、自分の範囲を眺めてみる。", 21, True, YELL)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("そして、整った戦略より「なぜそれが重要か」を語れる戦略を。", 12.5, False, MINT)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 29 行動宣言
s = add_slide()
header(s, "ACTION", "行動宣言 — 明日からの一手を、1人1行", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 1.05,
     [P([R("今日つくった絵と言葉から", 17, True, INK),
         R("「明日やること」を1つだけ", 17, True, RED),
         R("選び、チャットに投稿してください", 17, True, INK)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("宣言した瞬間、研修は「聞いた話」から「自分の計画」に変わります", 12.5, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.08, pad=0.18)
ex = [("例①", "「自分の範囲の絵で『？』にした線を、来週の面会で1つ確認する」", GREEN),
      ("例②", "「A大学の医局長に、B大学との関係について聞いてみる」", NAVY),
      ("例③", "「描いた絵を上司に見せて、施設の優先順位が合っているか相談する」", GOLD)]
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

# ================================================================ 30 Thank you
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

# ================================================================ 31 付録A ワークシート（絵）
s = add_slide()
header(s, "APPENDIX A", "ワークシート① 自分のテリトリーを描く（印刷・配布用）", kcolor=GRAY)
shape(s, 0.6, 1.7, 8.9, 4.55, fill=PALE2, line=GREEN, radius=0.02)
txt(s, 0.8, 1.8, 6.5, 0.32,
    [P([R("私の任された範囲（　　　　　　　　　　　　　　　）", 12, True, GREEN)])])
txt(s, 0.85, 2.2, 8.4, 0.4,
    [P([R("この枠の中に、施設を丸で置いてください。丸の大きさ＝あなたが考える重要度です。", 10.5, False, GRAY)])])
card(s, 9.75, 1.7, 3.0, 2.2,
     [P([R("描く要素", 13, True, WHITE)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("□ 担当する大学・基幹病院（全部）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 担当外だが流れに関わる施設（薄く）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 重要な医師（誰が動かす？）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 患者の流れ", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 医師の人事・派遣", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 情報・診療方針の流れ", 11, False, WHITE)], line=1.2)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.16)
card(s, 9.75, 4.05, 3.0, 2.2,
     [P([R("使う「機能」を書き込む", 12.5, True, INK)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("教育／研究／臨床／医局人事／医師派遣／情報発信／講演会・研究会", 11, False, INK)], line=1.3, space_after=8),
      P([R("→ この課題を解くのに必要な機能を、丸の中に書く", 11, True, GOLD)], line=1.25)],
     fill=YPALE, line=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.16)
card(s, 0.6, 6.4, 12.15, 0.42,
     [P([R("問い：あなたの絵で、大学は何番目に大きいですか？　その理由を説明できますか？", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 32 付録B 4つの問い（4S）
s = add_slide()
header(s, "APPENDIX B", "ワークシート② 4つの問いで言語化する（＝4Sシート）", kcolor=GRAY)
txt(s, 0.6, 1.6, 12.15, 0.32,
    [P([R("範囲名（　　　　　　　　　　）　作成日（　　／　　）　作成者（　　　　　　）", 11.5, False, INK)])])
tq = [(0.6, 1.95, "① 成功像　—　範囲がどうなっていたら最高か", GREEN),
      (6.75, 1.95, "② 現状・課題　—　理想とどこがどう違うか", NAVY),
      (0.6, 3.5, "③ 原因　—　なぜそのギャップが生まれているか", GOLD),
      (6.75, 3.5, "④ 解決法　—　何を起こすか", RED)]
for x, y, t, col in tq:
    card(s, x, y, 6.0, 0.45, [P([R(t, 12, True, WHITE)])], fill=col, radius=0.1, pad=0.13)
    card(s, x, y + 0.5, 6.0, 1.0, [P([R("", 10)])], fill=WHITE, line=col, radius=0.1)
plus = ["＋ 大学・医局のWIN（相手は何をしたいか）", "＋ 使う機能・影響力（誰に・何を・どこまで）",
        "＋ 自分の介入点／次の行動"]
for i, t in enumerate(plus):
    x = 0.6 + i * 4.09
    card(s, x, 5.05, 3.9, 0.45, [P([R(t, 10.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=DEEP, radius=0.1, pad=0.1)
    card(s, x, 5.55, 3.9, 0.85, [P([R("", 10)])], fill=WHITE, line=DEEP, radius=0.1)
card(s, 0.6, 6.42, 12.15, 0.42,
     [P([R("セルフチェック：　□ 主語は「範囲」か　　□ 相手のWINを書けたか　　□ 影響力の効かせ方を決めたか　　□ 「なぜ重要か」を語れるか", 11.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 33 付録C DAY1-3総まとめ
s = add_slide()
header(s, "APPENDIX C", "DAY1〜3の学び 総まとめ（1枚で振り返る）", kcolor=GRAY)
recap = [("DAY 1", "大学・基幹病院のイロハ", GREEN,
          ["大学の3使命：教育・研究・臨床。医師派遣で地域医療を支える",
           "影響力はテリトリーとニーズで決まる（GP／HP／HS）",
           "教授の裁量権：臨床機会の配分・医局人事・教授選・研究教育の方向性",
           "大学は「医局の集合体」。病院教授／特任教授は財源・任期・実権で見分ける",
           "薬審・採用は施設ごとに流れが違う。宣伝許可・申請時期・採用形態を確認"]),
         ("DAY 2", "「会えない」を「会える」に", NAVY,
          ["未訪問 → 初回接点 → 仮説面会 → 定期面会 と段階で設計する",
           "アクセス方法：訪問ルール確認・秘書経由・メール・手紙・直接訪問",
           "Best Time / Best Place：外来・外勤・医局会・総回診・カンファを把握",
           "カレンダーで情報管理し、行動ログで1週間後に検証する",
           "「会う理由」を設計し次回の約束を残す。まず1人、My teacherをつくる"]),
         ("DAY 3", "やっぱりMRは情報が命", GOLD,
          ["ドライ情報：HP・機関紙・掲示物・Veeva Link・講演内容 など",
           "ウェット情報：面会・他Dr・社内他領域・MS・HCP・講演会での雑談 など",
           "分からないことは small b として面会に持ち込み、解像度を上げていく",
           "顧客理解＝現状把握。何を・なぜ使い、患者をどうしたいのかを知る",
           "面会後は「なぜ」を分解し、仮説を立てて次の面会へつなげる"])]
for i, (d, t, col, lines) in enumerate(recap):
    x = 0.6 + i * 4.09
    card(s, x, 1.75, 3.9, 0.68,
         [P([R(d + "　", 14, True, WHITE), R(t, 11, True, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
    card(s, x, 2.5, 3.9, 3.6,
         [P([R("・" + l, 10.5, False, INK)], line=1.25, space_after=9) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
card(s, 0.6, 6.25, 12.15, 0.65,
     [P([R("DAY4：この3つを「何のために使うか」を決めるのが、戦略的思考です。", 14, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12)

# ================================================================ 34 付録D 肩書き
s = add_slide()
header(s, "APPENDIX D", "大学の「肩書き」早見表 — DAY1の補足", kcolor=GRAY,
       lead="肩書きではなく「財源・任期・実権・医局への接続」で判断する、というDAY1の考え方の一覧版です。")
colA = [("教授（診療科長）", "方針・人事の最終決定者。ただし多忙で、現場の細部は下のポジションが握っていることが多い"),
        ("准教授・講師", "実務の要であり、次期教授候補。3年後のキーパーソンとして関係構築は先行投資になる"),
        ("医局長", "医局の雑務・人事、医局行事の窓口。教授からの信頼が高く、影響力が大きい"),
        ("助教・医員・専攻医", "実処方と臨床研究の担い手。数年後、関連病院の幹部として範囲の中に散っていく")]
colB = [("病院教授", "臨床・病院運営に強い教授級ポスト。採用・薬審・院内導線には強いが、医局人事権とは別のことがある"),
        ("特任教授", "寄附講座・共同研究など外部資金による任用。研究・講演には強いが、医局人事は限定的なことも"),
        ("客員・非常勤", "本務は他施設。院内の決定権は限定的だが、施設間ネットワークのハブになっていることがある"),
        ("名誉教授", "退官後の称号で現役の決定権はない。ただし人脈・影響力は健在。研究会や講演会の重鎮")]
card(s, 0.6, 2.05, 6.0, 0.48, [P([R("院内の本流ライン", 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GREEN, radius=0.12)
card(s, 6.75, 2.05, 6.0, 0.48, [P([R("読み違えやすい肩書き（要・個別確認）", 13, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
for ci, (rows_, col) in enumerate(((colA, GREEN), (colB, NAVY))):
    x = 0.6 + ci * 6.15
    y = 2.6
    for t, d in rows_:
        card(s, x, y, 6.0, 0.86,
             [P([R(t, 12.5, True, col)], space_after=3), P([R(d, 10.5, False, INK)], line=1.18)],
             fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
        y += 0.94
card(s, 0.6, 6.45, 12.15, 0.42,
     [P([R("MR確認チェック：① 財源　② 任期　③ 実権（薬審・採用・医局人事のどこに効くか）　④ 本務教授・医局長・薬剤部との距離　⑤ COIの扱い", 11, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 35 付録E コンプラ
s = add_slide()
header(s, "APPENDIX E", "大学活動 コンプライアンスの5原則", kcolor=GRAY,
       lead="アンケートの不安「寄附金・広告協賛・宣伝許可・施設ルール」に応えて。攻める活動ほど、守りが土台になります。")
pr = [("① 施設ルールが最優先", "訪問・面会・資材配布のルールは施設ごとに違う。着任時と変更時に必ず確認し、迷ったら守りに倒す"),
      ("② 寄附金・広告協賛は「その場で約束しない」", "依頼を受けたら即答せず、必ず社内の申請・審査手続きに乗せる。誠実な「持ち帰ります」は信頼を損なわない"),
      ("③ 宣伝許可・採用ルールは現行の文書で確認", "「前任者がやっていた」は根拠にならない。DAY1で学んだ薬審・採用の流れを、施設ごとに毎回確認する"),
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

# ================================================================ 36 付録F ファシリテーター
s = add_slide()
header(s, "APPENDIX F", "ファシリテーター用メモ（進行のコツ）", kcolor=GRAY)
tips = [("事前準備・時間管理",
         ["事前案内：A4白紙1枚とペンを持参、担当範囲の施設を思い出してくる",
          "録画を回し、気づきリストとセットで欠席者へ共有（アンケートで要望多数）",
          "オープニングは5分厳守。テーマ①②の各25分（講義10・ワーク10・共有5）を死守する"]),
        ("場づくり",
         ["チェックインは進行役が最初に投稿し、投稿のハードルを下げる",
          "「大学が一番大きくない絵」が出たら、その場で全体に紹介する",
          "ワーク中は沈黙OKと伝える。ブレイクアウトは各室を1周して1声かけ"]),
        ("つまずき対応",
         ["絵が描けない人には「重要そうな5施設だけ」と伝える",
          "「正解がない」ことに戸惑う人には、4パターンのスライドに戻る",
          "言葉が埋まらない人には「1つでも言い切れれば成功」と伝える"]),
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
