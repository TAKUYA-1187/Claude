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
   - ワークの冒頭で対象疾患を1つ選ばせる（慢性糸球体腎炎の診療を題材に）
   - ワークは「完成条件（作る一文）」まで明示する
   - 共有は発表の型と時間を決め、全員が確実に発言できるようにする
   - ワーク②は到達目標（成功像・現状/課題・解決法）と一致させる
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
header(s, "AGENDA", "本日の進め方")
blocks = [("オープニング", "5分", "3回の振り返り／今日の2つの視点", GREEN),
          ("テーマ①「影響力を考える」", "25分", "誰が、何を動かせるのか", NAVY),
          ("テーマ②「影響の輪を考える」", "25分", "その力は、どこまで届くのか", NAVY),
          ("エリア戦略・まとめ", "5分", "まとめ／今週の一手", GREEN)]
y = 1.9
for t, tm, d, col in blocks:
    card(s, 0.6, y, 6.3, 1.0, [P([R("■ " + t, 17, True, WHITE)])], fill=col, radius=0.1, pad=0.22)
    card(s, 7.0, y, 1.2, 1.0, [P([R(tm, 15, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.15)
    card(s, 8.35, y, 4.4, 1.0, [P([R(d, 13.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.18)
    y += 1.13
card(s, 0.6, 6.45, 12.15, 0.48,
     [P([R("テーマ① 講義10 → ワーク10 → 共有5　　｜　　テーマ② 講義10 → ワーク5 → ディスカッション10", 13, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 9 今日の2つの視点
s = add_slide()
header(s, "TODAY'S DESIGN", "第4回のテーマは「戦略的思考」")
pillars = [("採用", "DAY 1", GREEN2), ("面会", "DAY 2", GREEN2),
           ("情報収集", "DAY 3", GREEN2), ("戦略的思考", "DAY 4", DEEP)]
for i, (t, d, col) in enumerate(pillars):
    x = 0.6 + i * 3.12
    card(s, x, 1.8, 2.95, 0.8,
         [P([R("◆ " + t, 15.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(d, 11.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=col, radius=0.1)
card(s, 0.6, 2.75, 12.15, 0.72,
     [P([R("到達目標：", 14, True, DEEP),
         R("担当施設と周辺エリアに対する", 15, True, INK),
         R("成功像・現状・課題・解決法を言語化できる", 15, True, RED)], align=PP_ALIGN.CENTER)],
     fill=YPALE, line=YELL, radius=0.1)
two = [("① 影響力", "誰が、何を動かせるのか", "肩書きではなく「動かせるもの」で見る",
        "テーマ①", NAVY, PALEB),
       ("② 影響の輪", "その力は、どこまで届くのか", "施設 → 関連病院 → エリア → その先",
        "テーマ②", GOLD, YPALE)]
for i, (t, sub, d, tag, col, fill) in enumerate(two):
    x = 0.6 + i * 6.15
    card(s, x, 3.75, 6.0, 0.75,
         [P([R(t, 20, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(sub, 13, False, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 4.58, 6.0, 0.95, [P([R(d, 15, True, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=fill, radius=0.1, pad=0.16)
    card(s, x + 2.35, 5.62, 1.3, 0.42, [P([R(tag, 12, True, col)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=col, radius=0.2)
card(s, 0.6, 6.25, 12.15, 0.72,
     [P([R("戦略的思考 ＝ 影響力を見極め、その輪をどこまで広げるかを決めること", 17, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12)

# ================================================================ 10 3回で手に入れた力
s = add_slide()
header(s, "LOOK BACK", "3回で手に入れた力")
days = [("DAY 1", "大学・基幹病院のイロハ", GREEN,
         ["大学の3使命と医師派遣", "影響力はテリトリー×ニーズ（HP／HS）",
          "教授の裁量権／医局の集合体", "薬審・採用の流れ"],
         "誰が“何を動かせるか”"),
        ("DAY 2", "「会えない」を「会える」に", NAVY,
         ["未訪問 → 初回接点 → 仮説面会 → 定期面会", "Best Time / Best Place",
          "カレンダー管理と行動ログ", "会う理由を設計し、次の約束を残す"],
         "動かせる人に“会える”"),
        ("DAY 3", "やっぱりMRは情報が命", GOLD,
         ["ドライ情報 × ウェット情報", "small b として面会に持ち込む",
          "顧客理解＝現状把握", "面会後は「なぜ」を分解して次へ"],
         "その人のニーズが“分かる”")]
for i, (d, t, col, lines, gain) in enumerate(days):
    x = 0.6 + i * 4.09
    card(s, x, 1.85, 3.9, 0.75,
         [P([R(d, 15, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(t, 11.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.68, 3.9, 1.95,
         [P([R("・" + l, 12, False, INK)], line=1.25, space_after=10) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
    card(s, x, 4.72, 3.9, 0.55, [P([R(gain, 13, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, radius=0.12)
card(s, 0.6, 5.5, 12.15, 1.3,
     [P([R("この3つが揃うと、「影響力」が見える。", 24, True, WHITE)],
       align=PP_ALIGN.CENTER, space_after=6),
      P([R("今日は、それを戦略にします。", 15, False, MINT)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 11 チェックイン（1問）
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, 3.4, 0.42, "CHECK IN　｜　3分", fill=GREEN)
card(s, 0.6, 1.0, 12.15, 1.05,
     [P([R("この3回で、実際に変わったことは何ですか？", 30, True, INK)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.06, pad=0.18)
card(s, 1.9, 2.3, 9.55, 0.95,
     [P([R("Teamsチャットに、", 17, True, DEEP),
         R("「以前と比べて変わったこと」を1つ、1行で", 17, True, RED)],
       align=PP_ALIGN.CENTER, space_after=3),
      P([R("大学・基幹病院の見方、行動、準備の仕方 — どれでも構いません", 12.5, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.15, pad=0.16)
txt(s, 0.6, 3.55, 12.15, 0.32, [P([R("例", 13, True, GRAY)], align=PP_ALIGN.CENTER)])
exs = ["会う相手が、教授だけではなくなった",
       "面会前に、仮説を準備するようになった",
       "医局長や若手医師の役割を、見るようになった"]
y = 3.95
for e in exs:
    card(s, 2.6, y, 8.15, 0.62, [P([R(e, 15, False, INK)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=LGRAY, radius=0.1)
    y += 0.72
card(s, 2.6, 6.15, 8.15, 0.7,
     [P([R("まだ変わっていない方は、「今も不安なこと」を1つどうぞ", 15, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, line=GREEN, radius=0.12)
footer(s)

# ================================================================ 12 テーマ①扉
s = add_slide()
section(s, "①", "影響力を考える", "テーマ①　｜　誰が、何を動かせるのか　｜　25分",
        "その疾患で、「何かを動かせる人」は誰ですか？",
        ["DAY1の「“影響力”を紐解く」を、自分の担当施設で実際にやってみる",
         "影響力は「肩書き」ではなく「何を動かせるか」で見る",
         "DAY2で会えた人・DAY3で分かったニーズを、ここで結びつける"])

# ================================================================ 13 DAY1復習
s = add_slide()
header(s, "THEME ①", "影響力は「テリトリー」と「ニーズ」で決まる", "DAY1の復習", kcolor=NAVY)
tiers = [("HP（基幹病院）", ["1病院", "医師会・医療圏", "関連病院・出身医局"],
          "紹介率を上げたい／関連病院と協働したい／院内で負けたくない", GREEN),
         ("HS（大学病院）", ["県内", "県内＋他大学・専門領域", "日本全体・学会・世界"],
          "研修医が欲しい／論文を出したい／県内での存在感が欲しい", NAVY)]
for i, (t, terr, need, col) in enumerate(tiers):
    x = 0.6 + i * 6.15
    card(s, x, 2.05, 6.0, 0.6, [P([R(t, 17, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    yy = 2.78
    for j, tr in enumerate(terr):
        card(s, x + 0.45 * (2 - j), yy, 6.0 - 0.9 * (2 - j), 0.5,
             [P([R(tr, 13, True, col)], align=PP_ALIGN.CENTER)],
             fill=PALE2, line=col, radius=0.2)
        yy += 0.6
    card(s, x, 4.7, 6.0, 0.62, [P([R("ニーズ：" + need, 12.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
card(s, 0.6, 5.55, 12.15, 1.3,
     [P([R("テリトリーが違えば、ニーズも違う。ニーズが違えば、動かせるものも違う。", 16, False, WHITE)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("「この先生は、何を動かせるのか？」", 24, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.2)

# ================================================================ 14 何を動かせるか
s = add_slide()
header(s, "THEME ①", "影響力は「肩書き」ではなく「何を動かせるか」", "25分", kcolor=NAVY)
funcs = [("教育", "若手が数年後にエリアへ散る", GREEN),
         ("研究", "学会・論文で外へ届く", GREEN),
         ("臨床", "症例が集まる・評価の場", GREEN),
         ("医局人事", "関連病院の部長・医長を決める", NAVY),
         ("医師派遣", "エリアの布陣が決まる", NAVY),
         ("情報発信", "治療方針がエリアの標準に", GOLD),
         ("講演会・研究会", "地域の共通認識をつくる", GOLD)]
for i, (t, d, col) in enumerate(funcs):
    x = 0.6 + (i % 4) * 3.12
    y = 2.0 + (i // 4) * 1.5
    card(s, x, y, 2.95, 0.55, [P([R(t, 14, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, x, y + 0.6, 2.95, 0.75, [P([R(d, 11.5, False, INK)], align=PP_ALIGN.CENTER, line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.13)
card(s, 9.96, 3.5, 2.79, 1.35,
     [P([R("その疾患で", 12.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=5),
      P([R("どれを動かせる？", 15, True, YELL)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.14)
card(s, 0.6, 5.15, 6.0, 1.65,
     [P([R("教授の裁量権（DAY1）", 14, True, DEEP)], space_after=8),
      P([R("① 臨床機会の配分　② 医局人事・異動", 12.5, False, INK)], space_after=6, line=1.25),
      P([R("③ 教授会・教授選　④ 研究・教育の方向性", 12.5, False, INK)], space_after=8, line=1.25),
      P([R("＝ 教授は「処方者」ではなく、これらを動かせる人", 12, True, NAVY)], line=1.25)],
     fill=PALEB, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)
card(s, 6.75, 5.15, 6.0, 1.65,
     [P([R("肩書きの落とし穴（DAY1）", 14, True, RED)], space_after=8),
      P([R("病院教授・特任教授は「教授」でも動かせるものが違う", 12.5, True, INK)], space_after=8, line=1.25),
      P([R("財源・任期・実権・医局への接続で見極める（付録E）", 12, False, INK)], line=1.25)],
     fill=YPALE, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.2)

# ================================================================ 15 1人に集中しない
s = add_slide()
header(s, "THEME ①", "影響力は、1人に集中していない", "25分", kcolor=NAVY)
roles = [("◎", "方針を決める", "治療方針が、この人の一言で決まる", GREEN),
         ("○", "最初に試す", "新しい治療を最初に使う。実務の中心", GREEN2),
         ("★", "情報ハブ", "若手が困ったら聞きに行く。医局長に多い", GOLD),
         ("◇", "連携の要", "紹介患者の受け入れ・行き先を差配", NAVY),
         ("□", "対外の顔", "研究会・講演会で外に発信する", NAVY2)]
y = 2.0
for mk, t, d, col in roles:
    circle(s, 0.6, y, 0.62, mk, fill=col, size=17)
    card(s, 1.42, y, 2.6, 0.62, [P([R(t, 14, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.12)
    card(s, 4.18, y, 4.9, 0.62, [P([R(d, 12.5, False, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.14)
    y += 0.74
card(s, 9.3, 2.0, 3.45, 3.32,
     [P([R("DAY2・DAY3が効く", 14.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=14),
      P([R("この5人を見分けるには、会って話すしかない", 12.5, False, WHITE)], space_after=14, line=1.3),
      P([R("DAY2　会えるようになった", 12.5, True, MINT)], space_after=8, line=1.25),
      P([R("DAY3　ニーズが見えてきた", 12.5, True, MINT)], space_after=14, line=1.25),
      P([R("3回分の学びが、ここで1つに。", 13, True, YELL)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.2)
card(s, 0.6, 5.62, 12.15, 1.2,
     [P([R("「この施設で、何かを動かせるのは誰か」を固有名詞で言えるか。", 18, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=8),
      P([R("言えない場所が、次に会いに行く相手です。", 14, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1, pad=0.2)
# ================================================================ 16 ワーク①
s = add_slide()
header(s, "WORK ①", "影響力マップを描く", "10分", kcolor=GREEN)
card(s, 0.6, 1.75, 8.05, 0.85,
     [P([R("まず、今日考える疾患を1つ決めてください", 15, True, RED)], space_after=4),
      P([R("慢性糸球体腎炎の診療（IgA腎症など）から、あなたが一番動かしたい疾患を1つ", 12.5, False, INK)], line=1.2)],
     fill=YPALE, line=RED, radius=0.08, pad=0.16)
steps = [("STEP 1", "3分", "大学・基幹病院を、重要な順に3〜5施設描く",
          "丸の大きさ＝その施設が動いたとき、他施設の診療がどれだけ変わるか"),
         ("STEP 2", "4分", "各施設に、影響を持つ人を1〜2名書く",
          "誰か（氏名 or 役職）／何を動かせるか（方針・導入・教育・連携・発信）"),
         ("STEP 3", "3分", "分からない施設・人物・関係に「？」を書く",
          "その「？」が、次に聞きに行くことです")]
y = 2.75
for st, tm, t, d in steps:
    card(s, 0.6, y, 1.4, 0.95, [P([R(st, 12.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
                                P([R(tm, 11.5, False, WHITE)], align=PP_ALIGN.CENTER)],
         fill=GREEN, radius=0.12)
    card(s, 2.15, y, 6.5, 0.95,
         [P([R(t, 13.5, True, DEEP)], space_after=3), P([R(d, 11, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.16)
    y += 1.07
card(s, 0.6, 6.03, 8.05, 0.85,
     [P([R("問い：", 13, True, RED),
         R("その疾患で最も影響力が大きい施設はどこ？　大学・基幹病院はそれぞれどの位置？", 13, True, INK)],
       line=1.2)],
     fill=PALE, radius=0.08, pad=0.16)
card(s, 8.9, 1.75, 3.85, 2.65,
     [P([R("完成条件", 15, True, DEEP)], align=PP_ALIGN.CENTER, space_after=10),
      P([R("次の一文が作れたら完成です", 11.5, False, INK)], space_after=8),
      P([R("「この疾患で最も影響力が大きいのは〇〇施設の△△先生。□□を動かせるから」", 12.5, True, INK)], line=1.35)],
     fill=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.18)
card(s, 8.9, 4.55, 3.85, 2.33,
     [P([R("迷ったら", 14, True, WHITE)], align=PP_ALIGN.CENTER, space_after=12),
      P([R("・人が出てこなければ役職だけで可", 12, False, WHITE)], space_after=10, line=1.25),
      P([R("・影響が担当エリアを超えるなら、そう書いてよい", 12, False, WHITE)], space_after=10, line=1.25),
      P([R("・分からないところは「？」", 12, True, MINT)], line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06, pad=0.18)

# ================================================================ 17 共有①
s = add_slide()
header(s, "SHARE ①", "3人1組で、1人60秒ずつ", "5分", kcolor=GREEN)
card(s, 0.6, 1.85, 12.15, 0.65,
     [P([R("時計回りに、全員が話してください。1人60秒。", 17, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
card(s, 0.6, 2.7, 12.15, 0.5, [P([R("発表の型", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=NAVY, radius=0.12)
lines = [("私が選んだ疾患は", "〇〇", "です。"),
         ("最も影響力が大きい施設は", "△△", "です。"),
         ("動かせる人は", "□□先生", "で、◇◇を動かせると考えています。"),
         ("まだ分からないことは", "☆☆", "です。")]
y = 3.32
for a, b, c in lines:
    card(s, 0.6, y, 12.15, 0.62,
         [P([R(a, 15, False, INK), R(b, 15, True, RED), R(c, 15, False, INK)], align=PP_ALIGN.CENTER)],
         fill=WHITE, line=LGRAY, radius=0.1)
    y += 0.72
card(s, 0.6, 6.3, 12.15, 0.6,
     [P([R("聞き手の質問は1つだけ　—　", 14, False, INK),
         R("「その判断の根拠は何ですか？」", 17, True, GREEN)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 18 テーマ②扉
s = add_slide()
section(s, "②", "影響の輪を考える", "テーマ②　｜　その力は、どこまで届くのか　｜　25分",
        "その影響力は、どこまで届きますか？",
        ["影響の輪：施設の中 → 関連病院 → 担当エリア → 営業所・その先",
         "大学に固執しない。輪が一番大きいのは大学とは限らない",
         "輪を動かすには、相手のWINが要る"])

# ================================================================ 19 影響の輪
s = add_slide()
header(s, "THEME ②", "影響の輪 — その力は、どこまで届くのか", "25分", kcolor=NAVY)
rings = [("① 施設の中", 4.3, GREEN2), ("② 関連病院", 3.4, GREEN),
         ("③ 担当エリア", 2.5, NAVY2), ("④ その先", 1.6, NAVY)]
cx, cy = 3.5, 4.1
for label, d, col in rings:
    shape(s, cx - d / 2, cy - d / 2, d, d, fill=None, line=col, line_w=1.8, kind=MSO_SHAPE.OVAL)
for label, d, col in rings:
    txt(s, cx - 1.1, cy - d / 2 + 0.07, 2.2, 0.28,
        [P([R(label, 11, True, col)], align=PP_ALIGN.CENTER)])
circle(s, cx - 0.4, cy - 0.4, 0.8, "先生", fill=YELL, size=12, color=DEEP)
lv = [("① 施設の中まで", "院内の方針・採用は動く。エリアには届かない", GREEN2),
      ("② 関連病院まで", "医局人事・派遣を通じて、系列に届く", GREEN),
      ("③ 担当エリアまで", "研究会・講演会・地域連携で、系列を越える", NAVY2),
      ("④ その先まで", "学会・全国の研究会で、担当範囲を超える", NAVY)]
y = 1.95
for t, d, col in lv:
    card(s, 6.9, y, 5.85, 1.0,
         [P([R(t, 14.5, True, col)], space_after=4), P([R(d, 11.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.17)
    y += 1.12
card(s, 0.6, 6.42, 12.15, 0.5,
     [P([R("輪の大きさは、肩書きでは決まらない。　", 14, False, INK),
         R("その疾患で、一番大きな輪を持つのは誰？", 15, True, RED)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12)

# ================================================================ 20 大学に固執しない
s = add_slide()
header(s, "THEME ②", "大学に固執しない — 大学はエリアの中の「1施設」", "25分", kcolor=NAVY)
pats = [("① 大学の輪が最大",
         [("A大", 1.2, 1.05, 0.5, PALE, DEEP), ("基幹", 0.62, 2.15, 1.4, WHITE, GRAY),
          ("基幹", 0.62, 0.32, 1.5, WHITE, GRAY)],
         "方針がエリア全体に波及。人事と発信が効く", GREEN),
        ("② 複数の大学が並ぶ",
         [("A大", 1.0, 0.45, 0.55, PALE, DEEP), ("B大", 1.0, 1.75, 1.2, PALE, GREEN2),
          ("基幹", 0.6, 1.35, 0.3, WHITE, GRAY)],
         "1大学では動かない。共通する課題を探す", NAVY),
        ("③ 基幹病院の輪が最大",
         [("基幹", 1.25, 0.9, 0.55, PALEB, NAVY), ("A大", 0.72, 0.38, 1.6, PALE, DEEP),
          ("基幹", 0.66, 2.05, 1.55, PALEB, NAVY2)],
         "実務は基幹病院。大学は研究・教育で効かせる", GOLD),
        ("④ 輪がエリアを超える",
         [("A大", 1.15, 0.48, 0.5, PALE, DEEP), ("県外", 0.66, 2.05, 0.42, WHITE, GRAY),
          ("県外", 0.66, 2.15, 1.55, WHITE, GRAY)],
         "営業所・全国への展開を考える", RED)]
for i, (t, circles, note, col) in enumerate(pats):
    x = 0.6 + i * 3.12
    card(s, x, 1.95, 2.95, 0.52, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    shape(s, x, 2.52, 2.95, 2.7, fill=PALE2, line=LGRAY, radius=0.04)
    for lbl, d, dx, dy, fc, lc in circles:
        circle(s, x + dx, 2.68 + dy, d, lbl, fill=fc, line=lc,
               size=10.5 if d > 0.9 else 9, color=lc)
    card(s, x, 5.32, 2.95, 1.0, [P([R(note, 12, False, INK)], line=1.25)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
card(s, 0.6, 6.45, 12.15, 0.5,
     [P([R("「大学を軸としたエリア攻略」ではなく、", 14, False, INK),
         R("「エリアを動かすために、どの輪を使うか」", 15, True, RED)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 21 WIN-WIN
s = add_slide()
header(s, "THEME ②", "輪を動かすには、相手のWINが要る", "25分", kcolor=NAVY)
set_alpha(shape(s, 0.95, 2.1, 3.5, 3.5, fill=NAVY2, line=NAVY, line_w=1.8, kind=MSO_SHAPE.OVAL), 78)
set_alpha(shape(s, 2.9, 2.1, 3.5, 3.5, fill=GREEN, line=GREEN, line_w=1.8, kind=MSO_SHAPE.OVAL), 78)
txt(s, 0.72, 2.5, 2.1, 0.72,
    [P([R("エリアで\n実現したいこと", 12.5, True, NAVY)], align=PP_ALIGN.CENTER, line=1.2)])
txt(s, 4.55, 2.5, 2.1, 0.72,
    [P([R("大学・医局が\nしたいこと", 12.5, True, GREEN)], align=PP_ALIGN.CENTER, line=1.2)])
txt(s, 3.05, 3.5, 1.3, 0.9,
    [P([R("打ち手", 17, True, RED)], align=PP_ALIGN.CENTER, space_after=2),
     P([R("はここ", 11, True, RED)], align=PP_ALIGN.CENTER)])
txt(s, 0.95, 5.72, 5.4, 0.32,
    [P([R("重なりが大きいほど、相手は本気で動く", 12.5, True, DEEP)], align=PP_ALIGN.CENTER)])
card(s, 6.75, 2.1, 6.0, 0.55,
     [P([R("腎臓内科の医局が「したいこと」の例", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=GREEN, radius=0.12)
wants = ["専門性の高い症例を集めたい", "若手・専攻医を増やしたい、育てたい",
         "研究データを出したい・論文を書きたい", "関連病院との連携／派遣先を確保したい",
         "県内・地域での存在感を高めたい", "学会・研究会で発信したい"]
card(s, 6.75, 2.72, 6.0, 2.35,
     [P([R("・" + w, 12.5, False, INK)], line=1.2, space_after=8) for w in wants],
     fill=PALE, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.18)
card(s, 6.75, 5.2, 6.0, 0.75,
     [P([R("DAY1で見た「HSのニーズ」そのもの", 13, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, radius=0.1, pad=0.14)
card(s, 0.6, 6.15, 12.15, 0.8,
     [P([R("「先生がやりたいこと」を叶えながら、「エリアで実現したいこと」も進む打ち手は何か？", 16, True, RED)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.12, pad=0.14)

# ================================================================ 22 エリアプランニング
s = add_slide()
header(s, "THEME ②", "エリアプランニング — 4つのステップ", "25分", kcolor=NAVY)
flow = [("① 成功像", "1年後、エリアがどうなっていたら理想か", GREEN),
        ("② 使う影響力", "誰の・どの輪を、どこまで届かせるか", NAVY2),
        ("③ 相手のWIN", "その先生・医局は何を実現したいか", GOLD),
        ("④ 次の一手", "今週、誰に・何を・いつまでに", RED)]
for i, (t, d, col) in enumerate(flow):
    x = 0.6 + i * 3.12
    card(s, x, 1.95, 2.95, 0.6, [P([R(t, 14, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.62, 2.95, 0.9, [P([R(d, 12, False, INK)], align=PP_ALIGN.CENTER, line=1.25)],
         fill=PALE2, radius=0.1, pad=0.14)
    if i < 3:
        arrow(s, x + 2.98, 2.12, 0.12, 0.26, color=GREEN2)
txt(s, 0.6, 3.65, 12.15, 0.3,
    [P([R("情報から考えるのではなく、成功像から逆算する。DAY3の「取り方」に「取りに行く理由」が加わります。", 12, True, GRAY)],
       align=PP_ALIGN.CENTER)])
card(s, 0.6, 4.08, 12.15, 0.45,
     [P([R("例：IgA腎症（架空のエリア）", 13, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1)
ex = [("① 成功像", "主要な大学・基幹病院で、患者選択・治療導入・フォローの考え方が整理されている", GREEN, PALE),
      ("② 使う影響力", "A大学教授＝県内の研究会で発信（③の輪）／B大学＝関連病院に強い（②の輪）", NAVY2, PALEB),
      ("③ 相手のWIN", "A大学＝県内での存在感を高めたい／B大学＝関連病院との連携を強めたい", GOLD, YPALE),
      ("④ 次の一手", "今週、A大学の医局長に、県内の研究会での発信について相談する", RED, RPALE)]
y = 4.62
for t, d, col, fill in ex:
    card(s, 0.6, y, 2.3, 0.48, [P([R(t, 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, 3.0, y, 9.75, 0.48, [P([R(d, 12, False, INK)])], fill=fill, radius=0.1, pad=0.12)
    y += 0.56
# ================================================================ 23 ワーク②
s = add_slide()
header(s, "WORK ②", "エリアの次の一手を決める", "5分", kcolor=GREEN)
card(s, 0.6, 1.72, 12.15, 0.55,
     [P([R("選んだ疾患について、4つの問いに1人でメモしてください", 16, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1)
qs4 = [("Q1", "成功像", "1年後、担当エリアがどうなっていたら理想ですか？（一文で）", GREEN),
       ("Q2", "使う影響力", "誰の・どの輪を使いますか？　どこまで届かせたいですか？", NAVY2),
       ("Q3", "相手のWIN", "その先生・医局は、何を実現したいですか？（分からなければ「次回何を確認するか」）", GOLD),
       ("Q4", "次の一手", "今週、自分が最初に行うことは？（誰に・何を・いつまでに）", RED)]
y = 2.42
for tag, t, q, col in qs4:
    circle(s, 0.6, y + 0.03, 0.6, tag, fill=col, size=14)
    card(s, 1.4, y, 2.2, 0.66, [P([R(t, 13.5, True, col)], align=PP_ALIGN.CENTER)],
         fill=PALE2, line=col, radius=0.12)
    card(s, 3.75, y, 9.0, 0.66, [P([R(q, 13, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.15)
    y += 0.78
card(s, 0.6, 5.62, 12.15, 0.45, [P([R("完成条件：この4行が書けたら完成です", 13.5, True, WHITE)],
     align=PP_ALIGN.CENTER)], fill=DEEP, radius=0.1)
card(s, 0.6, 6.15, 12.15, 0.85,
     [P([R("私のエリアでは ", 14, False, INK), R("〇〇", 14, True, RED),
         R(" を実現したい。そのために ", 14, False, INK), R("△△先生の□□という影響力", 14, True, RED),
         R(" を使いたい。", 14, False, INK)], align=PP_ALIGN.CENTER, space_after=4),
      P([R("先生・医局のWINは ", 14, False, INK), R("◇◇", 14, True, RED),
         R(" だと考える。まず私は、今週 ", 14, False, INK), R("☆☆", 14, True, RED),
         R(" を確認・実行する。", 14, False, INK)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)

# ================================================================ 24 ディスカッション
s = add_slide()
header(s, "DISCUSSION", "3人1組で、戦略を確かめ合う", "10分", kcolor=GREEN)
prog = [("1人3分 × 3人", "発表2分 ＋ 質問1分", GREEN),
        ("最後の1分", "グループの一番の気づきを1つ決める", NAVY)]
y = 1.9
for t, d, col in prog:
    card(s, 0.6, y, 4.0, 0.85, [P([R(t, 16, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.12)
    card(s, 4.75, y, 8.0, 0.85, [P([R(d, 15, False, INK)])],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.18)
    y += 1.0
card(s, 0.6, 4.0, 12.15, 0.5, [P([R("発表は、ワーク②の4行をそのまま読むだけでOK", 14, True, WHITE)],
     align=PP_ALIGN.CENTER)], fill=DEEP, radius=0.1)
card(s, 0.6, 4.68, 12.15, 1.15,
     [P([R("聞き手の質問は1つだけ", 13.5, True, GRAY)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("「その打ち手で、成功像に本当に近づきますか？」", 22, True, RED)], align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.1, pad=0.16)
card(s, 0.6, 6.0, 12.15, 0.9,
     [P([R("施設や先生の紹介で終わらせず、", 14, False, INK),
         R("「その打ち手は成功像につながっているか」を確かめる時間", 15, True, DEEP),
         R("にしてください。", 14, False, INK)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.1, pad=0.16)

# ================================================================ 25 まとめ＋Beyond
s = add_slide()
header(s, "WRAP UP", "本日のまとめ")
msgs = [(("誰が", "動かせるか"), "影響力は「肩書き」ではなく「何を動かせるか」",
         "◎方針／○最初に試す／★情報ハブ／◇連携の要／□対外の顔。1人とは限らない。", NAVY),
        (("どこまで", "届くか"), "影響の輪で見る。大学に固執しない",
         "施設の中／関連病院／担当エリア／その先。一番大きいのは大学とは限らない。", GOLD),
        (("どう", "動かすか"), "相手のWINと重なる打ち手を選ぶ",
         "エリアで実現したいことと、医局がしたいことが重なるところに置く。", GREEN)]
y = 1.9
for no, t, d, col in msgs:
    card(s, 0.6, y, 1.7, 1.1,
         [P([R(no[0], 13, True, WHITE)], align=PP_ALIGN.CENTER, line=1.15, space_after=2),
          P([R(no[1], 13, True, WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col, radius=0.12)
    card(s, 2.45, y, 10.3, 1.1,
         [P([R(t, 17, True, col)], space_after=5), P([R(d, 13, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.22)
    y += 1.25
card(s, 0.6, 5.7, 12.15, 1.15,
     [P([R("一施設で終わらせず、その影響を担当エリアへ広げる。", 23, True, YELL)],
       align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1, pad=0.18)

# ================================================================ 26 行動宣言
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=PALE2, kind=MSO_SHAPE.RECTANGLE)
chip(s, 0.6, 0.34, 2.4, 0.42, "ACTION", fill=GREEN)
txt(s, 0.6, 0.95, 12.2, 0.8, [P([R("行動宣言", 32, True, DEEP)])])
card(s, 0.6, 1.95, 12.15, 1.1,
     [P([R("Teamsチャットに、「今週、誰に・何をするか」を1行で", 24, True, INK)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=GREEN, line_w=1.6, radius=0.06, pad=0.18)
card(s, 2.6, 3.35, 8.15, 0.65, [P([R("記入形式", 14, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.12)
card(s, 2.6, 4.08, 8.15, 0.95,
     [P([R("今週中に、", 19, False, INK), R("〇〇先生", 19, True, RED),
         R(" へ ", 19, False, INK), R("△△", 19, True, RED), R(" を確認する。", 19, False, INK)],
       align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.1)
card(s, 2.6, 5.35, 8.15, 0.85,
     [P([R("ワーク②のQ4に書いたことを、そのまま投稿すればOKです", 15, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12)
card(s, 2.6, 6.35, 8.15, 0.6,
     [P([R("「電話1本サイズ」に割ること。小さいほど、実行されます。", 14, True, GRAY)], align=PP_ALIGN.CENTER)],
     fill=WHITE, line=LGRAY, radius=0.12)
footer(s)

# ================================================================ 27 最終メッセージ
s = add_slide()
shape(s, 0, 0, 13.333, 7.5, fill=DEEP, kind=MSO_SHAPE.RECTANGLE)
txt(s, 0.9, 1.05, 11.5, 0.5, [P([R("ありがとうございました", 19, True, MINT)])])
steps4 = [("第1回", "見る力", GREEN2), ("第2回", "会う力", GREEN2),
          ("第3回", "情報を取る力", GREEN2), ("第4回", "何のために使うかを決める", YELL)]
for i, (d, t, col) in enumerate(steps4):
    x = 0.9 + i * 2.95
    card(s, x, 1.75, 2.75, 1.0,
         [P([R(d, 12.5, True, DEEP if col == YELL else WHITE)], align=PP_ALIGN.CENTER, space_after=4),
          P([R(t, 14, True, DEEP if col == YELL else WHITE)], align=PP_ALIGN.CENTER, line=1.15)],
         fill=col if col == YELL else RGBColor(0x11, 0x63, 0x45), radius=0.1, pad=0.14)
    if i < 3:
        arrow(s, x + 2.78, 2.13, 0.14, 0.24, color=MINT)
card(s, 0.9, 3.2, 11.5, 1.5,
     [P([R("「このエリアは、自分に任せてください。", 25, True, DEEP)], align=PP_ALIGN.CENTER, space_after=6),
      P([R("そのために、大学・基幹病院の力をこう組み合わせます」", 25, True, DEEP)], align=PP_ALIGN.CENTER)],
     fill=YELL, radius=0.1)
txt(s, 0.9, 5.0, 11.5, 0.5,
    [P([R("そう言える担当者を目指しましょう。", 20, True, WHITE)], align=PP_ALIGN.CENTER)])
items = [("今日中", "行動宣言をチャットへ"),
         ("今週", "録画・資料・気づきリストを共有"),
         ("これから", "困ったら、全国の仲間に相談を")]
for i, (t, d) in enumerate(items):
    x = 0.9 + i * 3.87
    card(s, x, 5.7, 3.6, 1.0,
         [P([R(t, 13, True, YELL)], align=PP_ALIGN.CENTER, space_after=4),
          P([R(d, 12, False, WHITE)], align=PP_ALIGN.CENTER, line=1.2)],
         fill=DEEP2, radius=0.1, pad=0.14)
footer(s, dark=True)

# ================================================================ 28 付録A ワークシート①
s = add_slide()
header(s, "APPENDIX A", "ワークシート① 影響力マップ", kcolor=GRAY)
txt(s, 0.6, 1.62, 12.15, 0.32,
    [P([R("選んだ疾患（　　　　　　　　　　　　）　　作成日（　　／　　）　　作成者（　　　　　　）", 12, False, INK)])])
shape(s, 0.6, 2.0, 8.9, 4.3, fill=PALE2, line=GREEN, radius=0.02)
txt(s, 0.85, 2.12, 8.4, 0.3,
    [P([R("丸の大きさ＝その施設が動いたとき、他施設の診療がどれだけ変わるか", 11, False, GRAY)])])
card(s, 9.75, 2.0, 3.0, 2.05,
     [P([R("各施設に書くこと", 13.5, True, WHITE)], align=PP_ALIGN.CENTER, space_after=10),
      P([R("□ 施設名", 12, False, WHITE)], space_after=8),
      P([R("□ 誰か（氏名 or 役職）", 12, False, WHITE)], space_after=8),
      P([R("□ 何を動かせるか", 12, False, WHITE)], space_after=8),
      P([R("□ 分からないところは「？」", 12, True, MINT)], line=1.2)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.18)
card(s, 9.75, 4.2, 3.0, 2.1,
     [P([R("役割の記号", 13, True, INK)], align=PP_ALIGN.CENTER, space_after=8),
      P([R("◎　方針を決める", 12, False, INK)], space_after=7),
      P([R("○　最初に試す", 12, False, INK)], space_after=7),
      P([R("★　情報ハブ", 12, False, INK)], space_after=7),
      P([R("◇　連携の要", 12, False, INK)], space_after=7),
      P([R("□　対外の顔", 12, False, INK)])],
     fill=YPALE, line=YELL, anchor=MSO_ANCHOR.TOP, radius=0.08, pad=0.18)
card(s, 0.6, 6.42, 12.15, 0.52,
     [P([R("完成条件：", 12, True, RED),
         R("「この疾患で最も影響力が大きいのは〇〇施設の△△先生。□□を動かせるから」と書けること", 12.5, True, DEEP)],
       align=PP_ALIGN.CENTER, space_after=2),
      P([R("動かせるもの：教育／研究／臨床／医局人事／医師派遣／情報発信／講演会・研究会　　※その他の医療機関は、背景となる患者動線として必要に応じて記載", 10, False, GRAY)],
        align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12, pad=0.1)

# ================================================================ 29 付録B ワークシート②
s = add_slide()
header(s, "APPENDIX B", "ワークシート② エリアの次の一手", kcolor=GRAY)
txt(s, 0.6, 1.62, 12.15, 0.32,
    [P([R("選んだ疾患（　　　　　　　　　　　　）　　作成日（　　／　　）　　作成者（　　　　　　）", 12, False, INK)])])
tq = [(0.6, 1.98, "Q1 成功像　—　1年後、エリアがどうなっていたら理想か", GREEN),
      (6.75, 1.98, "Q2 使う影響力　—　誰の・どの輪を、どこまで", NAVY2),
      (0.6, 3.5, "Q3 相手のWIN　—　その先生・医局は何を実現したいか", GOLD),
      (6.75, 3.5, "Q4 次の一手　—　今週、誰に・何を・いつまでに", RED)]
for x, y, t, col in tq:
    card(s, x, y, 6.0, 0.48, [P([R(t, 12, True, WHITE)])], fill=col, radius=0.1, pad=0.14)
    card(s, x, y + 0.53, 6.0, 0.95, [P([R("", 10)])], fill=WHITE, line=col, radius=0.1)
card(s, 0.6, 5.05, 12.15, 0.45,
     [P([R("完成文（この4行が書けたら完成）", 12.5, True, WHITE)], align=PP_ALIGN.CENTER)],
     fill=DEEP, radius=0.1)
card(s, 0.6, 5.58, 12.15, 0.85,
     [P([R("私のエリアでは〇〇を実現したい。そのために△△先生の□□という影響力を使いたい。", 13, False, INK)],
       align=PP_ALIGN.CENTER, space_after=4),
      P([R("先生・医局のWINは◇◇だと考える。まず私は、今週☆☆を確認・実行する。", 13, False, INK)],
        align=PP_ALIGN.CENTER)],
     fill=WHITE, line=DEEP, radius=0.1, pad=0.14)
card(s, 0.6, 6.55, 12.15, 0.4,
     [P([R("セルフチェック：　□ 主語は「エリア」か　　□ 使う輪を決めたか　　□ 相手のWINを書けたか　　□ 今週の行動まで落ちたか", 11.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.15)

# ================================================================ 30 付録C 疾患別の例
s = add_slide()
header(s, "APPENDIX C", "疾患別に考えると、こうなる（架空の例）", kcolor=GRAY)
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
    card(s, x, 2.6, 6.0, 0.42, [P([R("成功像", 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=GREEN, radius=0.1)
    card(s, x, 3.07, 6.0, 1.0, [P([R(success, 12, False, INK)], line=1.3)],
         fill=PALE, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
    card(s, x, 4.17, 6.0, 0.42, [P([R("影響の輪", 12, True, WHITE)], align=PP_ALIGN.CENTER)], fill=NAVY2, radius=0.1)
    card(s, x, 4.64, 6.0, 0.9, [P([R(ring, 12, False, INK)], line=1.3)],
         fill=PALEB, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.16)
    card(s, x, 5.64, 6.0, 0.72, [P([R(note, 11.5, True, col)], line=1.25)],
         fill=WHITE, line=col, radius=0.1, pad=0.15)
card(s, 0.6, 6.48, 12.15, 0.45,
     [P([R("同じエリアでも、疾患が違えば重要施設もキーパーソンも変わります。だからワークは疾患を1つ決めてから。", 12.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=YPALE, radius=0.15)

# ================================================================ 31 付録D DAY1-3総まとめ
s = add_slide()
header(s, "APPENDIX D", "DAY1〜3の学び 総まとめ", kcolor=GRAY)
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
          ["ドライ情報：HP・機関紙・掲示物・Veeva Link・講演内容",
           "ウェット情報：面会・他Dr・社内他領域・MS・HCP・雑談",
           "分からないことは small b として面会に持ち込む",
           "顧客理解＝現状把握。何を・なぜ使い、患者をどうしたいのか",
           "面会後は「なぜ」を分解し、仮説を立てて次へ"])]
for i, (d, t, col, lines) in enumerate(recap):
    x = 0.6 + i * 4.09
    card(s, x, 1.75, 3.9, 0.7,
         [P([R(d, 14, True, WHITE)], align=PP_ALIGN.CENTER, space_after=2),
          P([R(t, 11, True, WHITE)], align=PP_ALIGN.CENTER)], fill=col, radius=0.1)
    card(s, x, 2.52, 3.9, 3.55,
         [P([R("・" + l, 11, False, INK)], line=1.25, space_after=10) for l in lines],
         fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP, radius=0.1, pad=0.17)
card(s, 0.6, 6.25, 12.15, 0.62,
     [P([R("この3つが揃って初めて「影響力」が見え、「影響の輪」を設計できる。", 14.5, True, DEEP)],
       align=PP_ALIGN.CENTER)],
     fill=PALE, radius=0.12)

# ================================================================ 32 付録E 肩書き
s = add_slide()
header(s, "APPENDIX E", "大学の「肩書き」早見表", kcolor=GRAY)
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

# ================================================================ 33 付録F コンプラ
s = add_slide()
header(s, "APPENDIX F", "大学活動 コンプライアンスの5原則", kcolor=GRAY)
pr = [("① 施設ルールが最優先", "訪問・面会・資材配布のルールは施設ごとに違う。迷ったら守りに倒す"),
      ("② その場で約束しない", "寄附金・広告協賛の依頼は即答せず、必ず社内の申請・審査手続きへ"),
      ("③ 現行の文書で確認", "「前任者がやっていた」は根拠にならない。薬審・採用は施設ごとに毎回確認"),
      ("④ 自己判断しない", "基準はプロモーションコードと社内SOP。迷ったら相談してから動く"),
      ("⑤ 記録を残す", "依頼・回答・手続きの経緯を記録に。先生と自分の両方を守る")]
y = 2.05
for t, d in pr:
    card(s, 0.6, y, 3.6, 0.88, [P([R(t, 13, True, WHITE)])], fill=DEEP, radius=0.1, pad=0.18)
    card(s, 4.35, y, 8.4, 0.88, [P([R(d, 12.5, False, INK)], line=1.2)],
         fill=WHITE, line=LGRAY, radius=0.1, pad=0.18)
    y += 0.98
txt(s, 4.35, 6.75, 8.4, 0.3,
    [P([R("※ 個別の案件は、必ず最新の社内規程と担当部門の指示に従ってください。", 11, False, GRAY)])])

# ================================================================ 34 付録G ファシリテーター
s = add_slide()
header(s, "APPENDIX G", "ファシリテーター用メモ", kcolor=GRAY)
tips = [("当日の投影",
         ["冒頭は タイトル → 4回のロードマップ → 本日のAgenda の3枚だけ使う",
          "プロジェクト概要・メンバー紹介は開始前の待機画面／配布資料へ回す",
          "オープニング5分を守れないと、ワークの時間が削られる"]),
        ("ワークの前提",
         ["ワーク①の冒頭で、必ず対象疾患を1つ決めさせる",
          "疾患が違えば重要施設もキーパーソンも変わる（付録C）",
          "「完成条件の一文」が書けたら完成、と最初に伝える"]),
        ("共有・ディスカッション",
         ["共有①は時計回りで1人60秒。型どおりで構わないと伝える",
          "ディスカッションは1人3分（発表2分＋質問1分）×3人＋気づき1分",
          "質問は1つだけ。施設紹介で終わらせず、成功像との接続を確かめる"]),
        ("締め方",
         ["まとめは3つのメッセージだけ。掘り下げない",
          "行動宣言はワーク②のQ4をそのまま投稿してもらう",
          "最終メッセージまで必ず2〜3分残す"])]
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
