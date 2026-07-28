# -*- coding: utf-8 -*-
"""
Renal MR スキルアッププロジェクト DAY4
「ちょっと分かるだけで世界が変わる」 — テーマ：戦略的思考

DAY4_base_1-7.pptx の冒頭7枚を保持し（Agendaの文言のみ更新）、8枚目以降を生成。

■ 構成（計60分）
   オープニング 5分 ／ テーマ①「影響力を考える」25分 ／
   テーマ②「影響の輪を考える」25分 ／ エリア戦略・まとめ 5分

■ 到達目標（プロジェクト公式・戦略的思考）
   担当施設と周辺エリアに対する成功像・現状・課題・解決法を言語化できる

■ 設計の柱（企画ミーティング＋DAY1〜3の内容を反映）
   - 戦略的思考 ＝ ①影響力（誰が、何を動かせるか）× ②影響の輪（どこまで届くか）
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
AGENDA_LINES = ["■オープニング　5分",
                "■テーマ①「影響力を考える」　25分",
                "■テーマ②「影響の輪を考える」　25分",
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
blocks = [("■ オープニング", "5分", "3回で何が変わったか／今日考える2つのこと", GREEN),
          ("■ テーマ①「影響力を考える」", "25分", "誰が、何を動かせるのか。DAY1の「影響力を紐解く」を自分の施設で", NAVY),
          ("■ テーマ②「影響の輪を考える」", "25分", "その力はどこまで届くのか。エリアプランニングをディスカッション", NAVY),
          ("■ エリア戦略・まとめ", "5分", "目指す状態／明日からの一手", GREEN)]
y = 1.95
for t, tm, d, col in blocks:
    card(s, 0.6, y, 6.3, 1.02, [P([R(t, 16, True, WHITE)])], fill=col, radius=0.1, pad=0.2)
    card(s, 7.0, y, 1.15, 1.02, [P([R(tm, 14, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 8.28, y, 4.47, 1.02, [P([R(d, 11.5, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 1.16
card(s, 0.6, 6.42, 12.15, 0.55,
     [P([R("テーマ①は「レクチャー10分 → ワーク10分 → 共有5分」、テーマ②は「レクチャー10分 → ディスカッション15分」。", 12.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 9 今日考える2つのこと
s = add_slide()
header(s, "TODAY'S DESIGN", "第4回のテーマは「戦略的思考」です")
pillars = [("採用", "DAY 1", GREEN2), ("面会", "DAY 2", GREEN2),
           ("情報収集", "DAY 3", GREEN2), ("戦略的思考", "DAY 4", DEEP)]
for i, (t, d, col) in enumerate(pillars):
    x = 0.6 + i * 3.12
    card(s, x, 1.85, 2.95, 0.8,
         [P([R("◆ " + t, 15, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(d, 11.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
card(s, 0.6, 2.8, 12.15, 0.72,
     [P([R("DAY4の到達目標：", 14, True, DEEP),
         R("担当施設と周辺エリアに対する", 15, True, INK),
         R("成功像・現状・課題・解決法を言語化できる", 15, True, RED)], align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
txt(s, 0.6, 3.75, 12.15, 0.4,
    [P([R("難しい理論は使いません。今日考えるのは、この2つだけです。", 14, True, INK)], align=PP_ALIGN.CENTER)])
two = [("① 影響力", "誰が、何を動かせるのか", "肩書きではなく「動かせるもの」で人と施設を見る",
        "テーマ①「影響力を考える」", NAVY, PALEB),
       ("② 影響の輪", "その力は、どこまで届くのか", "施設内 → 関連病院 → 担当エリア → その先へ",
        "テーマ②「影響の輪を考える」", GOLD, YPALE)]
for i, (t, sub, d, tag, col, fill) in enumerate(two):
    x = 0.6 + i * 6.15
    card(s, x, 4.28, 6.0, 0.6,
         [P([R(t + "　", 17, True, WHITE), R(sub, 12.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
    card(s, x, 4.94, 6.0, 0.95, [P([R(d, 14, True, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=fill, radius=0.1, pad=0.16)
    card(s, x + 0.6, 5.97, 4.8, 0.42, [P([R(tag, 11.5, True, col)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=col, radius=0.2)
card(s, 0.6, 6.48, 12.15, 0.45,
     [P([R("戦略的思考 ＝ ", 12.5, True, DEEP), R("影響力を見極め、その輪をどこまで広げるかを決めること", 12.5, True, RED),
         R("。この2つを考えると、同じ活動でも意味が変わります。", 12, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 10 3回で手に入れた力
s = add_slide()
header(s, "LOOK BACK", "3回で、あなたはこれだけの力を手に入れました")
days = [("DAY 1", "大学・基幹病院のイロハ", GREEN,
         ["大学の使命（教育・研究・臨床）と、医師派遣による地域への影響",
          "影響力はテリトリーとニーズで決まる（HP／HS）",
          "教授の裁量権と「医局の集合体」という構造／薬審・採用の流れ"],
         "誰が“偉い”かではなく“何を動かせるか”"),
        ("DAY 2", "「会えない」を「会える」に", NAVY,
         ["未訪問 → 初回接点 → 仮説面会 → 定期面会 の設計",
          "Best Time / Best Place：ルーチンワークの把握とカレンダー管理",
          "「会う理由」を設計し、次回の約束を残す／My teacherをつくる"],
         "動かせる人に“会える”"),
        ("DAY 3", "やっぱりMRは情報が命", GOLD,
         ["ドライ情報 × ウェット情報で顧客理解の解像度を上げる",
          "分からないことは small b として面会に持ち込む",
          "面会後は「なぜ」を分解し、仮説を立てて次の面会へ"],
         "その人のニーズが“分かる”")]
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
     [P([R("この3つが揃うと、「影響力」が見えるようになります。", 20, True, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("誰が何を動かせるか（DAY1）／その人に会える（DAY2）／その人が何をしたいか分かる（DAY3）。今日は、それを戦略にします。", 13, False, MINT)],
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
section(s, "①", "影響力を考える", "テーマ①　｜　誰が、何を動かせるのか　｜　25分（レクチャー10分・ワーク10分・共有5分）",
        "あなたの担当施設で、「何かを動かせる人」は誰ですか？",
        ["DAY1の「“影響力”を紐解いてみよう」を、今日は自分の担当施設で実際にやってみる",
         "影響力は「肩書き」ではなく「何を動かせるか」で見る",
         "DAY2で会えた人・DAY3で分かったことを、ここで結びつける"])

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
      P([R("ただし、患者さんの流れの起点として、エリアの中には存在します。", 11, False, INK)], space_after=8, line=1.25),
      P([R("→ 「担当する施設」と「エリアの中にある施設」は別モノ。両方を見るのが戦略的思考です。", 11, True, GRAY)], line=1.25)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.15)
card(s, 0.6, 5.15, 12.15, 1.5,
     [P([R("テリトリーが違えば、ニーズも違う。ニーズが違えば、動かせるものも違う。", 15, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("だから、影響力は肩書きでは測れません。", 17, True, MINT)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("「この先生は、何を動かせるのか？」で見ていきます。", 21, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 14 何を動かせるか
s = add_slide()
header(s, "THEME ①", "影響力は「肩書き」ではなく「何を動かせるか」", "25分", kcolor=NAVY,
       lead="DAY1で学んだとおり、大学病院はトップダウン組織ではなく「医局の集合体」。動かせるものは複数あります。")
funcs = [("教育", "若手が学び、数年後にエリアの病院へ散っていく", GREEN),
         ("研究", "エビデンスをつくり、学会・論文で外へ届く", GREEN),
         ("臨床", "症例が集まる。専門治療の実施と評価の場", GREEN),
         ("医局人事", "関連病院の部長・医長を決める。方針が波及する", NAVY),
         ("医師派遣", "誰がどの施設に行くか。エリアの布陣が決まる", NAVY),
         ("情報発信", "治療方針が、時間差でエリアの標準になる", GOLD),
         ("講演会・研究会", "地域の医師が集まる場。共通認識をつくれる", GOLD)]
for i, (t, d, col) in enumerate(funcs):
    x = 0.6 + (i % 4) * 3.12
    y = 2.15 + (i // 4) * 1.42
    card(s, x, y, 2.95, 0.48, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, x, y + 0.53, 2.95, 0.8, [P([R(d, 10.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
card(s, 9.96, 3.57, 2.79, 1.33,
     [P([R("この7つのうち、", 12, True, WHITE)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("あなたの担当施設は\nどれを動かせますか？", 13, True, YELL)], align=PP_ALIGN.CENTER, line=1.25)],
     fill=DEEP, radius=0.1, pad=0.14)
card(s, 0.6, 5.2, 12.15, 0.75,
     [P([R("DAY1の「教授の裁量権」を思い出してください：", 13, True, DEEP),
         R("①臨床機会の配分　②医局人事・異動　③教授会・教授選　④研究・教育の方向性", 12.5, False, INK)],
       align=PP_ALIGN.CENTER, space_after=4),
      P([R("＝ 教授は「処方者」ではなく、これらを動かせる人。逆に、動かせないものもあります。", 12, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=PALEB, radius=0.1, pad=0.16)
card(s, 0.6, 6.05, 12.15, 0.85,
     [P([R("肩書きの落とし穴：病院教授・特任教授は「教授」でも動かせるものが違う。", 14.5, True, RED)],
       align=PP_ALIGN.CENTER, space_after=5),
      P([R("DAY1で学んだとおり、", 12.5, False, INK), R("財源・任期・実権・医局への接続", 12.5, True, INK),
         R("で見極めます（詳細は付録D）。", 12.5, False, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 15 影響力は1人に集中しない
s = add_slide()
header(s, "THEME ①", "影響力は、1人に集中していません", "25分", kcolor=NAVY,
       lead="「教授＝キーパーソン」と決めつけた瞬間、動かせるはずの他の人が見えなくなります。")
roles = [("◎", "方針を決める人", "治療方針が、この人の一言で決まる", GREEN),
         ("○", "最初に試す人", "新しい治療を最初に使ってみる。実務の中心", GREEN2),
         ("★", "情報ハブ", "若手が困ったら聞きに行く。医局長であることが多い", GOLD),
         ("◇", "連携の要", "紹介患者の受け入れ・行き先を差配する", NAVY),
         ("□", "対外の顔", "研究会・講演会で、外に向けて発信する", NAVY2)]
y = 2.15
for mk, t, d, col in roles:
    circle(s, 0.6, y, 0.58, mk, fill=col, size=16)
    card(s, 1.38, y, 3.1, 0.58, [P([R(t, 13, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.12)
    card(s, 4.62, y, 4.5, 0.58, [P([R(d, 11.5, False, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
    y += 0.68
card(s, 9.3, 2.15, 3.45, 3.06,
     [P([R("DAY2・DAY3が効いてくる", 13, True, WHITE)], align=PP_ALIGN.CENTER, space_after=10),
      P([R("この5人を見分けるには、会って話すしかありません。", 11.5, False, WHITE)], space_after=10, line=1.25),
      P([R("DAY2：Best Time / Best Placeで会えるようになった", 11.5, True, MINT)], space_after=8, line=1.25),
      P([R("DAY3：ドライ×ウェット情報で、その人のニーズが見えてきた", 11.5, True, MINT)], space_after=10, line=1.25),
      P([R("→ 3回分の学びが、ここで1つになります。", 12, True, YELL)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.17)
card(s, 0.6, 5.6, 12.15, 1.25,
     [P([R("5人が同一人物とは限りません。基幹病院なら「部長＝◎かつ◇」など、兼ねることもあります。", 13.5, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("大事なのは、", 13, False, INK), R("「この施設で、何かを動かせるのは誰か」を固有名詞で言えること", 13.5, True, RED),
         R("。言えない場所が、次に会いに行く相手です。", 13, False, INK)], align=PP_ALIGN.CENTER, line=1.25)],
     fill=PALE, radius=0.1, pad=0.2)

# ================================================================ 16 ワーク①
s = add_slide()
header(s, "WORK ①", "担当施設の「影響力」を、絵にしてみる", "10分", kcolor=GREEN)
card(s, 0.6, 1.78, 8.05, 0.72,
     [P([R("手元の紙に、丸を描くだけです。上手さは関係ありません。5〜6施設でも十分です。", 14, True, INK)], line=1.2)],
     fill=PALE, radius=0.08, pad=0.16)
steps = [("STEP 1", "5分", "担当する大学・基幹病院を、丸で描く",
          "丸の大きさ＝あなたが感じる「影響力の大きさ」。理由はいりません、感覚でOK"),
         ("STEP 2", "5分", "丸の中に「動かせる人」を書く",
          "誰が・何を動かせるか。名前が出なければ役職でOK（◎○★◇□の記号だけでも可）")]
y = 2.68
for st, tm, t, d in steps:
    card(s, 0.6, y, 1.4, 0.95, [P([R(st, 12, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
                                P([R(tm, 11, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=GREEN, radius=0.12)
    card(s, 2.15, y, 6.5, 0.95,
         [P([R(t, 13, True, DEEP)], space_after=3), P([R(d, 10.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 1.08
card(s, 0.6, 4.9, 8.05, 1.9,
     [P([R("描けたら、自分に1つだけ問いかけてください。", 13, True, INK)], space_after=8),
      P([R("あなたの絵で、大学は何番目に大きいですか？", 19, True, RED)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("一番大きくなくても、まったく問題ありません。それがあなたのエリアの実態です。この後、その理由をみんなで話します。", 11.5, False, GRAY)],
        line=1.25)],
     fill=YPALE, radius=0.08, pad=0.2)
card(s, 8.9, 1.78, 3.85, 5.02,
     [P([R("迷ったら、これだけ", 14.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=14),
      P([R("・全部書かなくていい　重要そうな5〜6施設だけでOK", 12, False, WHITE)], space_after=12, line=1.25),
      P([R("・人が思い出せない　役職だけ、記号だけでも十分です", 12, False, WHITE)], space_after=12, line=1.25),
      P([R("・大きさに迷ったら　「ここが動けばエリアが変わるか？」で決める", 12, False, WHITE)], space_after=12, line=1.25),
      P([R("・分からないところは「？」　それが次に聞きに行くことです", 12, True, MINT)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06, pad=0.2)

# ================================================================ 17 共有①
s = add_slide()
header(s, "SHARE ①", "共有：描いた絵を見せ合って、自由に話しましょう", "5分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.72,
     [P([R("3〜4人1組。順番も型も決めません。描いた絵を画面に映して、思ったことを話してください。", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
topics = [("話のきっかけ①", "あなたの絵で、一番大きい丸はどこ？　それはなぜ？"),
          ("話のきっかけ②", "その施設で「動かせる人」は、誰でしたか？"),
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
     [P([R("他の人の絵は、最高の教材です。「大学が一番じゃないエリアもあるのか」— 自分の絵の空白が見えてきます。", 12.5, True, INK)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 18 テーマ②扉
s = add_slide()
section(s, "②", "影響の輪を考える", "テーマ②　｜　その力は、どこまで届くのか　｜　25分（レクチャー10分・ディスカッション15分）",
        "その影響力は、どこまで届きますか？",
        ["影響の輪：施設の中 → 関連病院 → 担当エリア → 営業所・その先へ",
         "大学に固執しない。大学は、エリアの中の1施設。輪の大きさは人によって違う",
         "輪を動かすには、相手のWINが要る。そしてエリアプランニングへ"])

# ================================================================ 19 影響の輪とは
s = add_slide()
header(s, "THEME ②", "影響の輪 — その先生の力は、どこまで届くのか", "25分", kcolor=NAVY,
       lead="同じ「影響力がある先生」でも、届く範囲はまったく違います。ここを見誤ると、打ち手を間違えます。")
rings = [("① 施設の中", 4.6, GREEN2), ("② 関連病院", 3.62, GREEN),
         ("③ 担当エリア", 2.64, NAVY2), ("④ 営業所・その先", 1.66, NAVY)]
cx, cy = 3.5, 4.35
for label, d, col in rings:
    shape(s, cx - d / 2, cy - d / 2, d, d, fill=None, line=col, line_w=1.6, kind=MSO_SHAPE.OVAL)
for label, d, col in rings:
    txt(s, cx - 1.1, cy - d / 2 + 0.06, 2.2, 0.26,
        [P([R(label, 10, True, col)], align=PP_ALIGN.CENTER)])
circle(s, cx - 0.38, cy - 0.38, 0.76, "先生", fill=YELL, size=11, color=DEEP)
card(s, 0.72, 6.32, 5.6, 0.58,
     [P([R("輪の大きさは、肩書きでは決まりません。実績・人脈・発信の量で決まります。", 10.5, True, GRAY)],
       align=PP_ALIGN.CENTER, line=1.2)],
     fill=WHITE, line=LGRAY, radius=0.15)
lv = [("① 施設の中まで", "院内の治療方針・採用は動く。でもエリアには届かない", GREEN2),
      ("② 関連病院まで", "医局人事・派遣を通じて、系列の病院に届く", GREEN),
      ("③ 担当エリアまで", "研究会・講演会・地域連携で、系列を越えて届く", NAVY2),
      ("④ 営業所・その先まで", "学会・全国の研究会で、担当範囲を超えて届く", NAVY)]
y = 2.05
for t, d, col in lv:
    card(s, 6.9, y, 5.85, 1.05,
         [P([R(t, 13, True, col)], space_after=4), P([R(d, 11, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 1.17
card(s, 6.9, 6.32, 5.85, 0.58,
     [P([R("問い：あなたのエリアで、一番大きな輪を持つのは誰？", 12.5, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.15)

# ================================================================ 20 大学に固執しない
s = add_slide()
header(s, "THEME ②", "だから、大学に固執しない — 大学はエリアの中の「1施設」", "25分", kcolor=NAVY,
       lead="輪が大きいのは大学とは限りません。基幹病院の部長のほうが、エリアに届くこともあります。")
pats = [("① 大学の輪が最大",
         [("A大", 1.15, 1.05, 0.42, PALE, DEEP), ("基幹", 0.62, 2.1, 1.28, WHITE, GRAY),
          ("基幹", 0.62, 0.35, 1.38, WHITE, GRAY)],
         "大学の方針がエリア全体に波及。医局人事と情報発信が効く", GREEN),
        ("② 複数の大学が並ぶ",
         [("A大", 0.95, 0.5, 0.48, PALE, DEEP), ("B大", 0.95, 1.75, 1.08, PALE, GREEN2),
          ("基幹", 0.6, 1.35, 0.28, WHITE, GRAY)],
         "1大学では動かない。両大学に共通する課題を探す", NAVY),
        ("③ 基幹病院の輪が最大",
         [("基幹", 1.2, 0.95, 0.48, PALEB, NAVY), ("A大", 0.7, 0.4, 1.48, PALE, DEEP),
          ("基幹", 0.65, 2.1, 1.43, PALEB, NAVY2)],
         "症例数・実務の影響力は基幹病院。大学は研究・教育で効かせる", GOLD),
        ("④ 輪がエリアを超える",
         [("A大", 1.1, 0.5, 0.42, PALE, DEEP), ("県外", 0.65, 2.0, 0.38, WHITE, GRAY),
          ("県外", 0.65, 2.1, 1.43, WHITE, GRAY)],
         "先生の影響が担当範囲を超える。営業所・全国への展開を考える", RED)]
for i, (t, circles, note, col) in enumerate(pats):
    x = 0.6 + i * 3.12
    card(s, x, 2.1, 2.95, 0.5, [P([R(t, 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    shape(s, x, 2.65, 2.95, 2.45, fill=PALE2, line=LGRAY, radius=0.04)
    for lbl, d, dx, dy, fc, lc in circles:
        circle(s, x + dx, 2.8 + dy, d, lbl, fill=fc, line=lc,
               size=10 if d > 0.9 else 8.5, color=lc)
    card(s, x, 5.2, 2.95, 1.1, [P([R(note, 11, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
card(s, 0.6, 6.42, 12.15, 0.48,
     [P([R("「大学を軸としたエリア攻略」ではなく、", 12.5, False, INK),
         R("「エリアを動かすために、どの輪を使うか」", 12.5, True, RED),
         R("。正解の型はありません。", 12.5, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 21 輪を動かすにはWIN-WIN
s = add_slide()
header(s, "THEME ②", "輪を動かすには、相手のWINが要ります", "25分", kcolor=NAVY,
       lead="DAY3の ROTF3「顧客の意思決定のニーズを正確に捉え、Win-Winの関係となる提案を行う」を、エリア規模で。")
set_alpha(shape(s, 0.95, 2.25, 3.4, 3.4, fill=NAVY2, line=NAVY, line_w=1.8, kind=MSO_SHAPE.OVAL), 78)
set_alpha(shape(s, 2.85, 2.25, 3.4, 3.4, fill=GREEN, line=GREEN, line_w=1.8, kind=MSO_SHAPE.OVAL), 78)
txt(s, 0.75, 2.6, 2.0, 0.7,
    [P([R("エリアで\n実現したいこと", 12, True, NAVY)], align=PP_ALIGN.CENTER, line=1.2)])
txt(s, 4.45, 2.6, 2.0, 0.7,
    [P([R("大学・医局が\nしたいこと", 12, True, GREEN)], align=PP_ALIGN.CENTER, line=1.2)])
txt(s, 2.95, 3.6, 1.3, 0.9,
    [P([R("打ち手", 16, True, RED)], align=PP_ALIGN.CENTER, space_after=2),
     P([R("はここ", 10.5, True, RED)], align=PP_ALIGN.CENTER)])
txt(s, 0.95, 5.78, 5.3, 0.32,
    [P([R("重なりが大きいほど、相手は本気で動いてくれる", 11.5, True, DEEP)], align=PP_ALIGN.CENTER)])
card(s, 6.6, 2.1, 6.15, 0.5,
     [P([R("腎臓内科の医局が「したいこと」の例", 13.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
wants = ["専門性の高い症例を集めたい（紹介を増やしたい）",
         "若手・専攻医を増やしたい、育てたい",
         "研究データを出したい・論文を書きたい",
         "関連病院との連携を強めたい／派遣先を確保したい",
         "県内・地域での存在感を高めたい",
         "学会・研究会で発信したい"]
card(s, 6.6, 2.68, 6.15, 2.4,
     [P([R("・" + w, 11.5, False, INK)], line=1.2, space_after=7) for w in wants],
     fill=PALE, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
card(s, 6.6, 5.2, 6.15, 0.9,
     [P([R("DAY1で見た「HSのニーズ」そのものです。", 12.5, True, DEEP)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("「先生が困っていること」だけでなく「先生がやりたいこと」を聞く。", 11.5, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, radius=0.1, pad=0.14)
card(s, 0.6, 6.25, 12.15, 0.65,
     [P([R("問いはシンプルです。", 13, True, DEEP),
         R("「先生がやりたいこと」を叶えながら、「エリアで実現したいこと」も進む打ち手は何か？", 14, True, RED)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12, pad=0.12)

# ================================================================ 22 エリアプランニングの流れ
s = add_slide()
header(s, "THEME ②", "エリアプランニング — 5つのステップで考える", "25分", kcolor=NAVY,
       lead="難しい手順はありません。成功像から始めて、輪を選び、相手のWINと重ねるだけです。")
flow = [("① 成功像", "エリアがどうなっていたら最高か", GREEN),
        ("② 輪を選ぶ", "誰の・どの輪を使うと届くか", NAVY2),
        ("③ WINを重ねる", "その先生は何をしたいか", GREEN),
        ("④ 情報を取る", "確かめるために何を聞くか（DAY3）", GOLD),
        ("⑤ やって、直す", "違っていたら成功像も打ち手も直す", RED)]
for i, (t, d, col) in enumerate(flow):
    x = 0.6 + i * 2.47
    card(s, x, 2.15, 2.28, 0.55, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.78, 2.28, 1.0, [P([R(d, 10.5, False, INK)], line=1.25)],
         fill=PALE2, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.13)
    if i < 4:
        arrow(s, x + 2.31, 2.32, 0.14, 0.24, color=GREEN2)
txt(s, 0.6, 3.86, 12.15, 0.3,
    [P([R("集めた情報から考えるのではなく、成功像から逆算する。DAY3で学んだ「取り方」に、「取りに行く理由」が加わります。", 11.5, True, GRAY)],
       align=PP_ALIGN.CENTER)])
card(s, 0.6, 4.24, 12.15, 0.42,
     [P([R("例：複数の大学があるエリア（架空の例）", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1)
ex = [("① 成功像", "エリアの基幹病院でも、専門治療が必要な患者さんが適切に見極められている", GREEN, PALE),
      ("② 輪を選ぶ", "A大学教授＝県内の研究会で発信できる（③の輪）／B大学＝関連病院に強い（②の輪）", NAVY2, PALEB),
      ("③ WINを重ねる", "A大学＝県内での存在感を高めたい／B大学＝関連病院との連携を強めたい", GREEN, PALE),
      ("④ 情報を取る", "両大学の関係性は？　研究会の世話人は？　基幹病院の部長の出身医局は？", GOLD, YPALE),
      ("⑤ 打ち手", "両大学と主要基幹病院が同席する会を企画。判断の目安を両大学の連名で発信してもらう", RED, RPALE)]
y = 4.74
for t, d, col, fill in ex:
    card(s, 0.6, y, 2.2, 0.4, [P([R(t, 11, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, 2.9, y, 9.85, 0.4, [P([R(d, 10.5, False, INK)])], fill=fill, radius=0.1, pad=0.1)
    y += 0.45

# ================================================================ 23 ワーク②＋ディスカッション
s = add_slide()
header(s, "WORK ②", "エリアプランニングを、みんなで考えてみる", "15分", kcolor=GREEN)
card(s, 0.6, 1.78, 12.15, 0.62,
     [P([R("まず1人でメモ（5分）→ そのままグループでディスカッション（10分）。発表会ではありません。", 14.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
qs3 = [("Q1", "あなたのエリアで、一番大きな「影響の輪」を持っているのは誰・どの施設？",
        "大学とは限りません。基幹病院の部長でも構いません", GREEN),
       ("Q2", "その輪を、どこまで広げたいですか？",
        "施設の中で十分？　関連病院まで？　エリア全体まで？", NAVY),
       ("Q3", "そのために、その先生・医局に何を提供できそうですか？",
        "思いつかなければ「ここが分からない」で十分です", RED)]
y = 2.55
for tag, q, hint, col in qs3:
    circle(s, 0.6, y + 0.05, 0.6, tag, fill=col, size=14)
    card(s, 1.4, y, 11.35, 0.7,
         [P([R(q, 13.5, True, DEEP)], space_after=3), P([R(hint, 10.5, False, GRAY)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.82
card(s, 0.6, 5.05, 6.0, 1.0,
     [P([R("ディスカッションのコツ", 13, True, GREEN)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("順番を決めず、思いついた人から。人の話に乗っかるのも大歓迎です。", 12, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=PALE2, line=GREEN, radius=0.1, pad=0.14)
card(s, 6.75, 5.05, 6.0, 1.0,
     [P([R("こんな話も大歓迎", 13, True, GOLD)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("「これはうまくいった」「これは難しかった」という実体験。他の人の一番の学びになります。", 12, False, INK)],
        align=PP_ALIGN.CENTER, line=1.25)],
     fill=YPALE, radius=0.1, pad=0.14)
card(s, 0.6, 6.2, 12.15, 0.7,
     [P([R("答えが出なくても、まったく問題ありません。", 15, True, RED),
         R("「ここが分からない」と気づけたら、それが今日一番の収穫です。", 13, False, INK)],
       align=PP_ALIGN.CENTER)],
     fill=WHITE, line=RED, radius=0.1, pad=0.14)

# ================================================================ 24 目指す状態
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.4, 2.2, 0.42, "BEYOND", fill=YELL, color=DEEP)
txt(s, 0.6, 1.05, 12.2, 0.5, [P([R("大学担当者として、目指す状態", 17, True, MINT)])])
card(s, 0.6, 1.7, 12.15, 1.35,
     [P([R("「このエリアは、自分に任せてください。", 26, True, DEEP)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("そのために、大学の影響力をこう使います」", 26, True, DEEP)], align=PP_ALIGN.CENTER)],
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
      P([R("指示された活動をこなす人ではなく、任されたエリアに責任を持ち、活動を設計・提案できる人へ。", 13.5, True, YELL)],
        align=PP_ALIGN.CENTER)],
     fill=DEEP2, radius=0.1, pad=0.16)
card(s, 0.6, 6.25, 12.15, 0.72,
     [P([R("現実には、会社の方針や予算で、最適でない施策を行うこともあります。それでも、自分のエリアを理解していれば", 12, False, MINT),
         R("「予算があるなら、こちらの施策のほうが成果につながります」と提案できる。", 12, True, WHITE)],
       align=PP_ALIGN.CENTER, line=1.25)],
     fill=RGBColor(0x11, 0x63, 0x45), radius=0.1, pad=0.14)
footer(s, dark=True)

# ================================================================ 25 まとめ
s = add_slide()
header(s, "WRAP UP", "本日のまとめ — 戦略的思考は、この3つを考えることから")
msgs = [(("誰が", "動かせるか"), "影響力は「肩書き」ではなく「何を動かせるか」",
         "◎方針を決める人／○最初に試す人／★情報ハブ／◇連携の要／□対外の顔。1人とは限らない。", NAVY),
        (("どこまで", "届くか"), "影響の輪で見る。大学に固執しない",
         "施設の中／関連病院／担当エリア／その先。輪が一番大きいのは大学とは限らない。", GOLD),
        (("どう", "動かすか"), "相手のWINと重ねる",
         "エリアで実現したいことと、医局がしたいことが重なるところに打ち手を置く。", GREEN)]
y = 1.95
for no, t, d, col in msgs:
    card(s, 0.6, y, 1.6, 1.05,
         [P([R(no[0], 12.5, True, WHITE)], align=PP_ALIGN.CENTER, line=1.15, space_after=1),
          P([R(no[1], 12.5, True, WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col, radius=0.12)
    card(s, 2.35, y, 10.4, 1.05,
         [P([R(t, 16, True, col)], space_after=4), P([R(d, 12.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.2)
    y += 1.2
card(s, 0.6, 5.6, 12.15, 1.25,
     [P([R("今日の持ち帰りは、これだけで十分です。", 14, True, WHITE)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("一度、大学という枠を外して、自分のエリアを眺めてみる。", 21, True, YELL)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("そして、整った戦略より「なぜそれが重要か」を語れる戦略を。", 12.5, False, MINT)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 26 行動宣言
s = add_slide()
header(s, "ACTION", "行動宣言 — 明日からの一手を、1人1行", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 1.05,
     [P([R("今日つくった絵と話したことから", 17, True, INK),
         R("「明日やること」を1つだけ", 17, True, RED),
         R("選び、チャットに投稿してください", 17, True, INK)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("宣言した瞬間、研修は「聞いた話」から「自分の計画」に変わります", 12.5, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.08, pad=0.18)
ex = [("例①", "「絵で『？』にしたところを、来週の面会で1つ確認する」", GREEN),
      ("例②", "「A大学の医局長に、いま力を入れたいことを聞いてみる」", NAVY),
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

# ================================================================ 27 Thank you
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
    [P([R("「このエリアは、自分に任せてください。そのために、大学の影響力をこう使います」", 16, True, MINT)])])
footer(s, dark=True)

# ================================================================ 28 付録A ワークシート①
s = add_slide()
header(s, "APPENDIX A", "ワークシート① 担当施設の「影響力」を描く（印刷・配布用）", kcolor=GRAY)
shape(s, 0.6, 1.7, 8.9, 4.55, fill=PALE2, line=GREEN, radius=0.02)
txt(s, 0.8, 1.8, 6.5, 0.32,
    [P([R("私の担当エリア（　　　　　　　　　　　　　　　）", 12, True, GREEN)])])
txt(s, 0.85, 2.2, 8.4, 0.6,
    [P([R("この枠の中に、担当施設を丸で置いてください。丸の大きさ＝あなたが感じる影響力の大きさです。", 10.5, False, GRAY)], space_after=3),
     P([R("動かせるもの：教育／研究／臨床／医局人事／医師派遣／情報発信／講演会・研究会", 10, True, GOLD)])])
card(s, 9.75, 1.7, 3.0, 2.2,
     [P([R("丸の中に書くこと", 13, True, WHITE)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("□ 施設名", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 動かせる人（名前 or 役職）", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ その人が動かせるもの", 11, False, WHITE)], space_after=7, line=1.2),
      P([R("□ 分からないところは「？」", 11, True, MINT)], line=1.2)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.16)
card(s, 9.75, 4.05, 3.0, 2.2,
     [P([R("役割の記号", 12.5, True, INK)], align=PP_ALIGN.CENTER, space_after=10),
      P([R("◎　方針を決める人", 11.5, False, INK)], space_after=7),
      P([R("○　最初に試す人", 11.5, False, INK)], space_after=7),
      P([R("★　情報ハブ", 11.5, False, INK)], space_after=7),
      P([R("◇　連携の要", 11.5, False, INK)], space_after=7),
      P([R("□　対外の顔", 11.5, False, INK)])],
     fill=YPALE, line=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.16)
card(s, 0.6, 6.4, 12.15, 0.42,
     [P([R("問い：あなたの絵で、大学は何番目に大きいですか？　その理由を説明できますか？", 12, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 29 付録B ワークシート②
s = add_slide()
header(s, "APPENDIX B", "ワークシート② エリアプランニングを考える（印刷・配布用）", kcolor=GRAY)
txt(s, 0.6, 1.6, 12.15, 0.32,
    [P([R("エリア名（　　　　　　　　　　）　作成日（　　／　　）　作成者（　　　　　　）", 11.5, False, INK)])])
tq = [(0.6, 1.95, "① 成功像　—　エリアがどうなっていたら最高か", GREEN),
      (6.75, 1.95, "② 輪を選ぶ　—　誰の・どの輪を使うと届くか", NAVY2),
      (0.6, 3.5, "③ WINを重ねる　—　その先生・医局は何をしたいか", GREEN),
      (6.75, 3.5, "④ 情報を取る　—　確かめるために何を聞くか", GOLD)]
for x, y, t, col in tq:
    card(s, x, y, 6.0, 0.45, [P([R(t, 11.5, True, WHITE)])], fill=col, radius=0.1, pad=0.13)
    card(s, x, y + 0.5, 6.0, 1.0, [P([R("", 10)])], fill=WHITE, line=col, radius=0.1)
card(s, 0.6, 5.05, 6.0, 0.45, [P([R("⑤ 打ち手　—　何を起こすか", 11.5, True, WHITE)])],
     fill=RED, radius=0.1, pad=0.13)
card(s, 0.6, 5.55, 6.0, 0.85, [P([R("", 10)])], fill=WHITE, line=RED, radius=0.1)
card(s, 6.75, 5.05, 6.0, 0.45, [P([R("＋ 明日、まず何をするか（1つだけ）", 11.5, True, WHITE)])],
     fill=DEEP, radius=0.1, pad=0.13)
card(s, 6.75, 5.55, 6.0, 0.85, [P([R("", 10)])], fill=WHITE, line=DEEP, radius=0.1)
card(s, 0.6, 6.42, 12.15, 0.42,
     [P([R("セルフチェック：　□ 主語は「エリア」か　　□ 誰のどの輪を使うか決めたか　　□ 相手のWINを書けたか　　□ 「なぜ重要か」を語れるか", 11.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 30 付録C DAY1-3総まとめ
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
     [P([R("DAY4：この3つが揃って初めて「影響力」が見え、「影響の輪」を設計できます。", 14, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12)

# ================================================================ 31 付録D 肩書き
s = add_slide()
header(s, "APPENDIX D", "大学の「肩書き」早見表 — DAY1の補足", kcolor=GRAY,
       lead="肩書きではなく「財源・任期・実権・医局への接続」で判断する、というDAY1の考え方の一覧版です。")
colA = [("教授（診療科長）", "方針・人事の最終決定者。ただし多忙で、現場の細部は下のポジションが握っていることが多い"),
        ("准教授・講師", "実務の要であり、次期教授候補。3年後のキーパーソンとして関係構築は先行投資になる"),
        ("医局長", "医局の雑務・人事、医局行事の窓口。教授からの信頼が高く、影響力が大きい"),
        ("助教・医員・専攻医", "実処方と臨床研究の担い手。数年後、関連病院の幹部としてエリアの中に散っていく")]
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

# ================================================================ 32 付録E コンプラ
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

# ================================================================ 33 付録F ファシリテーター
s = add_slide()
header(s, "APPENDIX F", "ファシリテーター用メモ（進行のコツ）", kcolor=GRAY)
tips = [("事前準備・時間管理",
         ["事前案内：A4白紙1枚とペンを持参、担当施設の顔ぶれを思い出してくる",
          "録画を回し、気づきリストとセットで欠席者へ共有（アンケートで要望多数）",
          "オープニング5分厳守。テーマ①は講義10・ワーク10・共有5、テーマ②は講義10・ディスカッション15"]),
        ("場づくり",
         ["チェックインは進行役が最初に投稿し、投稿のハードルを下げる",
          "「大学が一番大きくない絵」が出たら、その場で全体に紹介する",
          "テーマ②は発表会にしない。ブレイクアウトを1周して1声かけ、話が止まった部屋にQを振る"]),
        ("つまずき対応",
         ["絵が描けない人には「重要そうな5施設だけ」と伝える",
          "「正解がない」ことに戸惑う人には、4パターンのスライドに戻る",
          "Q3が出ない人には「相手が何をしたいか、まだ知らないだけ」と伝える"]),
        ("最終回としての締め方",
         ["Beyondは全員必達にしない。「考え方の紹介」として軽く置く",
          "難しくしすぎて手が止まるより、「大学の枠を外す」体験の持ち帰りを優先",
          "シリーズ全体の感想を1言ずつ集めてから終える"])]
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
