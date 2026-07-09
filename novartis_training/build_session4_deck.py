# -*- coding: utf-8 -*-
"""
大学担当者育成勉強会 第4回「ちょっと分かるだけで世界が変わる」
PowerPoint 資料生成スクリプト (python-pptx)
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
import copy

# ---------------------------------------------------------------- palette
DEEP   = RGBColor(0x0B, 0x4F, 0x37)   # 濃緑（タイトル帯）
GREEN  = RGBColor(0x12, 0x8A, 0x54)   # 基調グリーン
GREEN2 = RGBColor(0x3D, 0xA5, 0x74)   # 明るめグリーン
PALE   = RGBColor(0xE9, 0xF5, 0xEE)   # 薄緑背景
PALE2  = RGBColor(0xF4, 0xFA, 0xF6)   # さらに薄い緑
NAVY   = RGBColor(0x1F, 0x38, 0x64)   # 紺
PALEB  = RGBColor(0xEA, 0xF0, 0xF9)   # 薄青背景
YELL   = RGBColor(0xFF, 0xC0, 0x00)   # 強調イエロー
YPALE  = RGBColor(0xFF, 0xF6, 0xDC)   # 薄黄背景
RED    = RGBColor(0xC0, 0x00, 0x00)   # 注意レッド
RPALE  = RGBColor(0xFB, 0xEC, 0xEC)   # 薄赤背景
INK    = RGBColor(0x26, 0x26, 0x26)   # 本文
GRAY   = RGBColor(0x59, 0x59, 0x59)   # 補足
LGRAY  = RGBColor(0xD9, 0xD9, 0xD9)   # 罫線
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Meiryo UI"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

# ---------------------------------------------------------------- helpers
def _apply_font(run, size, bold, color, italic=False, name=FONT):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.italic = italic
    f.color.rgb = color; f.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', name)

def add_slide():
    return prs.slides.add_slide(BLANK)

def txt(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, wrap=True):
    """paras: list of dicts {runs:[(text,{size,bold,color,italic})], align, space_before, space_after, line}"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        if p.get("space_before") is not None: para.space_before = Pt(p["space_before"])
        if p.get("space_after")  is not None: para.space_after  = Pt(p["space_after"])
        if p.get("line") is not None:
            para.line_spacing = p["line"]
        for text, st in p["runs"]:
            r = para.add_run(); r.text = text
            _apply_font(r, st.get("size", 14), st.get("bold", False),
                        st.get("color", INK), st.get("italic", False))
    return tb

def P(runs, **kw):
    """paragraph shorthand"""
    d = {"runs": runs}; d.update(kw); return d

def R(text, size=14, bold=False, color=INK, italic=False):
    return (text, {"size": size, "bold": bold, "color": color, "italic": italic})

def box(slide, x, y, w, h, fill=PALE, line=None, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        radius=0.08, shadow=False):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try: sp.adjustments[0] = radius
        except Exception: pass
    tf = sp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    return sp

def box_txt(sp, paras, anchor=MSO_ANCHOR.MIDDLE):
    tf = sp.text_frame
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.CENTER)
        if p.get("space_before") is not None: para.space_before = Pt(p["space_before"])
        if p.get("space_after")  is not None: para.space_after  = Pt(p["space_after"])
        if p.get("line") is not None: para.line_spacing = p["line"]
        for text, st in p["runs"]:
            r = para.add_run(); r.text = text
            _apply_font(r, st.get("size", 14), st.get("bold", False),
                        st.get("color", INK), st.get("italic", False))
    return sp

def card(slide, x, y, w, h, paras, fill=PALE, line=None, anchor=MSO_ANCHOR.MIDDLE, radius=0.08):
    sp = box(slide, x, y, w, h, fill=fill, line=line, radius=radius)
    box_txt(sp, paras, anchor=anchor)
    return sp

def arrow(slide, x, y, w, h, color=GREEN, direction="right"):
    shp = {"right": MSO_SHAPE.RIGHT_ARROW, "down": MSO_SHAPE.DOWN_ARROW,
           "up": MSO_SHAPE.UP_ARROW}[direction]
    sp = slide.shapes.add_shape(shp, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def connector(slide, x1, y1, x2, y2, color=GRAY, weight=1.5, dash=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                   Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(weight)
    c.shadow.inherit = False
    if dash:
        ln = c.line._get_or_add_ln()
        d = ln.makeelement(qn('a:prstDash'), {'val': dash}); ln.append(d)
    return c

PAGE = [0]
def header(slide, kicker, title, ktime=None, kcolor=GREEN):
    """標準ヘッダー：キッカー（章ラベル）＋タイトル＋下線＋フッター"""
    k = kicker + ("｜" + ktime if ktime else "")
    card(slide, 0.55, 0.32, 2.9, 0.42,
         [P([R(k, 12.5, True, WHITE)])], fill=kcolor, radius=0.5)
    txt(slide, 0.55, 0.82, 12.3, 0.75,
        [P([R(title, 26, True, DEEP)])])
    bar = box(slide, 0.55, 1.52, 12.25, 0.035, fill=GREEN, shape=MSO_SHAPE.RECTANGLE)
    footer(slide)

def footer(slide):
    PAGE[0] += 1
    txt(slide, 0.55, 7.12, 9.0, 0.3,
        [P([R("大学担当者育成勉強会 第4回｜ちょっと分かるだけで世界が変わる", 9, False, GRAY)])])
    txt(slide, 12.3, 7.12, 0.5, 0.3,
        [P([R(str(PAGE[0]), 10, True, GREEN)], align=PP_ALIGN.RIGHT)])

# ================================================================ 1. 表紙
s = add_slide()
box(s, 0, 0, 13.333, 7.5, fill=DEEP, shape=MSO_SHAPE.RECTANGLE)
box(s, 0, 5.9, 13.333, 1.6, fill=RGBColor(0x08, 0x3B, 0x29), shape=MSO_SHAPE.RECTANGLE)
box(s, 0.9, 2.62, 0.14, 1.7, fill=YELL, shape=MSO_SHAPE.RECTANGLE)
txt(s, 1.0, 0.9, 11.4, 0.6,
    [P([R("大学担当者育成勉強会（全4回）", 18, True, RGBColor(0xBF, 0xE8, 0xD2))])])
card(s, 1.0, 1.55, 2.1, 0.62, [P([R("第 4 回", 22, True, DEEP)])], fill=YELL, radius=0.3)
txt(s, 3.3, 1.65, 3.0, 0.5, [P([R("— シリーズ最終回 —", 15, True, RGBColor(0xBF, 0xE8, 0xD2))])])
txt(s, 1.25, 2.5, 11.3, 2.0,
    [P([R("ちょっと分かるだけで", 44, True, WHITE)], space_after=4),
     P([R("世界が変わる", 44, True, WHITE)])])
txt(s, 1.25, 4.6, 11.3, 0.6,
    [P([R("〜 集めた情報を「武器」に変え、エリア戦略を描く 〜", 20, True, RGBColor(0xBF, 0xE8, 0xD2))])])
txt(s, 1.0, 6.15, 11.4, 1.1,
    [P([R("2026年8月6日（木）｜60〜90分（内容により＋30分延長）", 15, True, WHITE)], space_after=4),
     P([R("全員が主体的に参加：10分レクチャー × ワーク × 共有", 13, False, RGBColor(0xBF, 0xE8, 0xD2))], space_after=2),
     P([R("進行：腎臓領域担当（大学・基幹病院担当）", 12, False, RGBColor(0x9E, 0xCF, 0xB8))])])

# ================================================================ 2. チェックイン
s = add_slide()
header(s, "CHECK-IN", "チェックイン：まず、全員で口を開く", "5分")
card(s, 0.8, 1.95, 11.7, 1.75,
     [P([R("Q. この3回の勉強会で、あなたの", 24, True, DEEP),
         R("実際の動き", 24, True, RED),
         R("が変わったことを", 24, True, DEEP)], space_after=4),
      P([R("ひとつだけ", 24, True, RED),
         R("教えてください（1人30秒）", 24, True, DEEP)])],
     fill=PALE, line=GREEN, radius=0.06)
for i, (t, d) in enumerate([
    ("順番", "指名リレー方式。話した人が次の人を指名する"),
    ("30秒厳守", "短いほど良い。「小さな変化」こそ価値がある"),
    ("メモ", "他の人の変化で「真似したい」ものを1つメモする"),
]):
    card(s, 0.8 + i * 4.0, 4.05, 3.7, 1.5,
         [P([R(t, 16, True, GREEN)], space_after=6),
          P([R(d, 13, False, INK)], line=1.15)],
         fill=WHITE, line=LGRAY)
txt(s, 0.8, 5.85, 11.7, 0.9,
    [P([R("ねらい：", 13, True, NAVY),
        R("最初の5分で全員が発言すると、この後のワークの発言ハードルが一気に下がります。", 13, False, INK)], space_after=3),
     P([R("「変わったことが思いつかない」もOK。「変わらなかった理由」が今日の学びの出発点になります。", 12, False, GRAY)])])

# ================================================================ 2.5 アンケートの声
GOLD = RGBColor(0xB8, 0x6A, 0x00)
s = add_slide()
header(s, "VOICE", "この90分は、62名のアンケートから設計しました", kcolor=GOLD)
card(s, 0.8, 1.78, 5.75, 0.5, [P([R("皆さんの不安 TOP5", 14, True, WHITE)])], fill=RED, radius=0.12)
card(s, 6.75, 1.78, 5.75, 0.5, [P([R("皆さんの期待 TOP5", 14, True, WHITE)])], fill=GREEN, radius=0.12)
fuan = [
    ("① 継続面会・アポネタの獲得（最多）", "→ ワーク①＋「アポネタ製造機」で直接回答"),
    ("② 医局の構造・人間関係・肩書きの意味", "→ 構造マップの型＋付録D「肩書き早見表」"),
    ("③ 教わったことがない・自己流でやってきた", "→ 「型」で目線合わせ：構造マップ × 4Sシート"),
    ("④ 腎領域の知識・専門的な対話への不安", "→ 「教えてください」の武器化＋気づきリストで知を蓄積"),
    ("⑤ 寄附金・宣伝許可などのルール", "→ 付録E「コンプライアンスの5原則」"),
]
kitai = [
    ("① 他メンバーの事例・考え方（圧倒的最多）", "→ 共有を3回設計＋「全国気づきリスト」を今日から開始"),
    ("② 明日から使える実践スキル", "→ 7つの習慣・アポネタ・ネクストアクション"),
    ("③ 大学担当としての型・基本", "→ 構造マップと4S、2つの「型」を持ち帰る"),
    ("④ エリア戦略・優先順位付け", "→ 今日の本丸：レクチャー③＋「3つのモノサシ」"),
    ("⑤ 全国の横のつながり", "→ 気づきリスト＝このメンバーで続くネットワークの起点"),
]
for col_i, (rows_, col) in enumerate(((fuan, RED), (kitai, GREEN))):
    x = 0.8 + col_i * 5.95
    y = 2.38
    for t, d in rows_:
        c = card(s, x, y, 5.75, 0.64,
                 [P([R(t, 11.5, True, INK)], space_after=2, align=PP_ALIGN.LEFT),
                  P([R(d, 10, True, col)], align=PP_ALIGN.LEFT)],
                 fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
        c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.13)
        y += 0.72
card(s, 0.8, 6.14, 11.7, 0.62,
     [P([R("回答いただいた62名の皆さん、ありがとうございました。", 13, True, DEEP)], space_after=3),
      P([R("このアンケートが今日の設計図です。扱いきれないテーマは付録と「気づきリスト」で持ち帰れるようにしています。", 12, False, INK)])],
     fill=YPALE, radius=0.1)

# ================================================================ 3. シリーズの歩み
s = add_slide()
header(s, "ROADMAP", "ここまでの歩み — 今日は「集めた情報」を回収する回")
items = [
    ("第1回", "大学・基幹病院のイロハ", "大学担当者に求められる視点を理解し、医師・施設の影響力構造とニーズを説明できる", False),
    ("第2回", "「会えない」を「会える」に変える", "医師の行動パターンを基にBest Time / Best Placeを特定し、面談機会を設計できる", False),
    ("第3回", "やっぱりMRは情報が命", "施設・医師の仮説に基づき、必要な情報を意図的に取りに行く行動を設計・実行できる", False),
    ("第4回", "ちょっと分かるだけで世界が変わる", "収集した情報から4Sシートを用いて、エリアの課題・原因・解決方法を可視化できる", True),
]
for i, (no, t, d, today) in enumerate(items):
    x = 0.65 + i * 3.12
    ch = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(2.0), Inches(3.25), Inches(0.85))
    ch.fill.solid(); ch.fill.fore_color.rgb = DEEP if today else GREEN2
    ch.line.fill.background(); ch.shadow.inherit = False
    tf = ch.text_frame; tf.word_wrap = True
    box_txt(ch, [P([R(no + "　★本日" if today else no, 15, True, WHITE)])])
    cardc = card(s, x, 3.05, 2.9, 2.9,
         [P([R(t, 14, True, DEEP if today else GREEN)], space_after=7, line=1.1),
          P([R("到達目標", 10.5, True, GRAY)], space_after=3),
          P([R(d, 11.5, False, INK)], line=1.25)],
         fill=(YPALE if today else WHITE), line=(YELL if today else LGRAY), anchor=MSO_ANCHOR.TOP)
    cardc.text_frame.margin_top = Inches(0.15)
    cardc.text_frame.margin_left = cardc.text_frame.margin_right = Inches(0.14)
card(s, 0.65, 6.15, 12.15, 0.75,
     [P([R("第3回で「集め方」を学んだ情報は、", 15, False, INK),
         R("整理して・意味づけて・行動に変えて", 15, True, RED),
         R("初めて成果になる。今日はその変換装置を手に入れる回。", 15, False, INK)])],
     fill=PALE, radius=0.15)

# ================================================================ 3.5 道具箱（第1〜3回の学びを今日使う）
s = add_slide()
header(s, "TOOLBOX", "第1〜3回で手に入れた「道具」を、今日すべて使う")
tools = [
    ("第1回", "影響力構造のメガネ", "偉さと役割の違い・採用ルール・大学の影響圏という「見る目」",
     "ワーク①：構造マップの土台になる", GREEN),
    ("第2回", "Best Time × Best Place", "医師の導線・スケジュール仮説から面談機会を設計する技術",
     "特定したキーパーソンに「実際に会いに行く」計画で使う", NAVY),
    ("第3回", "情報源マップ＋Wetな情報", "病院HP・Veeva Link・スマイルPJ等のDry情報と、現場でつかむWet情報",
     "ワーク②：4Sシートの「根拠」になる", RGBColor(0xB8, 0x6A, 0x00)),
]
y = 1.95
for no, t, d, use, col in tools:
    card(s, 0.8, y, 1.75, 1.32,
         [P([R(no, 13.5, True, WHITE)], space_after=3), P([R("の道具", 11, False, WHITE)])], fill=col, radius=0.12)
    c = card(s, 2.7, y, 5.9, 1.32,
             [P([R(t, 15, True, DEEP)], space_after=4, align=PP_ALIGN.LEFT),
              P([R(d, 12, False, INK)], line=1.22, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = Inches(0.18)
    arrow(s, 8.7, y + 0.45, 0.45, 0.42, color=col)
    c = card(s, 9.25, y, 3.25, 1.32,
             [P([R("今日の使い所", 10.5, True, GRAY)], space_after=3, align=PP_ALIGN.LEFT),
              P([R(use, 11.5, True, col)], line=1.2, align=PP_ALIGN.LEFT)],
             fill=PALE2, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = Inches(0.15)
    y += 1.52
card(s, 0.8, 6.55, 11.7, 0.55,
     [P([R("今日の90分は、3回分の学びの総決算。", 15, True, DEEP),
         R("　道具はもう揃っている。あとは組み合わせて「戦略」にするだけ。", 13.5, False, INK)])],
     fill=PALE, radius=0.12)

# ================================================================ 4. 本日のゴール
s = add_slide()
header(s, "GOAL", "本日のゴール — 帰るときに、この状態になっている")
card(s, 0.8, 1.9, 11.7, 1.05,
     [P([R("収集した情報から４Sシートを用いて、エリアの", 19, True, WHITE),
         R("課題・原因・解決方法を可視化", 19, True, YELL),
         R("できる", 19, True, WHITE)])],
     fill=DEEP, radius=0.1)
goals = [
    ("①　整理する", "施設情報を「構造（人・役割・関係性）」で整理し、キーパーソンを特定できる", "ワーク①"),
    ("②　変換する", "「知っている」を「動ける」に変える。事実→解釈→打ち手を4Sシートで1枚に描ける", "ワーク②"),
    ("③　繋げる", "大学で分かったことを起点に、エリアアプローチ戦略を自分の言葉で説明できる", "レクチャー③"),
]
for i, (t, d, w) in enumerate(goals):
    y = 3.25 + i * 1.12
    card(s, 0.8, y, 2.6, 0.92, [P([R(t, 17, True, WHITE)])], fill=GREEN, radius=0.12)
    c = card(s, 3.55, y, 7.55, 0.92, [P([R(d, 13.5, False, INK)], align=PP_ALIGN.LEFT, line=1.2)],
             fill=WHITE, line=LGRAY)
    c.text_frame.margin_left = Inches(0.18)
    card(s, 11.25, y, 1.25, 0.92, [P([R(w, 11.5, True, NAVY)])], fill=PALEB, radius=0.15)
txt(s, 0.8, 6.72, 11.7, 0.4,
    [P([R("シリーズのゴール：担当者としての「自覚」＝ 自分が誰よりもこの施設・このエリアを分かっている、という状態。", 12.5, True, GRAY)])])

# ================================================================ 5. アジェンダ
s = add_slide()
header(s, "AGENDA", "本日の進め方（90分設計・60分短縮対応）")
rows = [
    ("00–05", "チェックイン", "3回の振り返りを1人30秒", "全員", GREEN),
    ("05–15", "レクチャー①", "情報を「構造」で整理する／キーパーソンの見つけ方", "講義10分", NAVY),
    ("15–30", "ワーク①", "担当施設の構造マップを描く", "個人ワーク", GREEN),
    ("30–40", "共有①", "ペアで質問をプレゼント → 全体共有", "ペア＋全体", GREEN),
    ("40–50", "レクチャー②", "「知っている」を「動ける」に変える／4Sシートの書き方", "講義10分", NAVY),
    ("50–70", "ワーク②", "自施設の4Sシートを作成（成功像→課題→原因→解決策）", "個人ワーク", GREEN),
    ("70–80", "共有②", "3人グループで発表＋フィードバック", "グループ", GREEN),
    ("80–90", "レクチャー③＋まとめ", "エリア戦略へ繋げる／ギフト集（持ち帰り可）／明日からの行動", "講義＋全員", NAVY),
]
y = 1.82
for tm, ttl, desc, form, col in rows:
    card(s, 0.8, y, 1.15, 0.52, [P([R(tm, 12.5, True, WHITE)])], fill=col, radius=0.2)
    c = card(s, 2.05, y, 3.05, 0.52, [P([R(ttl, 13.5, True, DEEP)], align=PP_ALIGN.LEFT)], fill=PALE2, radius=0.1)
    c.text_frame.margin_left = Inches(0.12)
    c = card(s, 5.2, y, 5.7, 0.52, [P([R(desc, 12, False, INK)], align=PP_ALIGN.LEFT)], fill=WHITE, line=LGRAY, radius=0.1)
    c.text_frame.margin_left = Inches(0.12)
    card(s, 11.0, y, 1.5, 0.52, [P([R(form, 11, True, NAVY)])], fill=PALEB, radius=0.15)
    y += 0.585
card(s, 0.8, y + 0.05, 11.7, 0.5,
     [P([R("⏱ 60分で終える場合：", 12.5, True, RED),
         R("ワーク①を10分・ワーク②を15分に短縮／共有はペアのみ／レクチャー③は資料配布＋3分要約", 12.5, False, INK)])],
     fill=RPALE, radius=0.12)

# ================================================================ 6. レクチャー①-1 なぜ整理か
s = add_slide()
header(s, "LECTURE ①", "情報は、集めただけでは1円にもならない", "10分", NAVY)
txt(s, 0.8, 1.8, 11.7, 0.55,
    [P([R("第3回の到達点：", 15, True, NAVY),
        R("「何を・どこで」つかむか（デスクトップリサーチ＋Wetな情報）は身についた。", 15, False, INK)])])
steps = [
    ("点", "集める", "面会メモ、HP、Veeva Link、\n医局の貼り紙、廊下の会話…\nバラバラの事実の山", PALE, GREEN),
    ("線", "整理する", "人と人・部署と部署を\n「関係」で結ぶ\n＝今日のワーク①", YPALE, RGBColor(0xB8, 0x8A, 0x00)),
    ("面", "意味づける", "施設全体・エリア全体の\n構造が見え、打ち手が\n浮かぶ ＝今日のワーク②", RPALE, RED),
]
for i, (big, t, d, fill, col) in enumerate(steps):
    x = 0.8 + i * 4.15
    c = card(s, x, 2.55, 3.5, 2.9,
         [P([R(big, 40, True, col)], space_after=2),
          P([R(t, 18, True, DEEP)], space_after=8),
          P([R(d.replace("\n", ""), 12.5, False, INK)], line=1.3, align=PP_ALIGN.LEFT)],
         fill=fill, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.2)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.2)
    if i < 2:
        arrow(s, x + 3.55, 3.7, 0.55, 0.5, color=GREEN)
card(s, 0.8, 5.75, 11.7, 1.1,
     [P([R("多くのMRは「点」で止まる。", 16, True, INK)], space_after=4, align=PP_ALIGN.LEFT),
      P([R("同じ情報量でも、「線」と「面」にした人だけが次の一手を打てる。今日やるのは、この2段の変換。", 14, False, INK)], align=PP_ALIGN.LEFT)],
     fill=PALE, radius=0.08)

# ================================================================ 7. レクチャー①-2 構造で整理
s = add_slide()
header(s, "LECTURE ①", "「構造」で整理する — 人・役割・関係性の3点セット", "10分", NAVY)
cols = [
    ("人", "誰がいるか", ["教授・准教授・講師・助教・医員・専攻医", "外来／病棟／透析室などの担当医", "薬剤部・看護部・地域連携室・医事課"], GREEN),
    ("役割", "誰が何を決めるか", ["診療方針を決める人（≠処方を書く人）", "採用・院内手続きを動かす人", "若手を教える人／勉強会を仕切る人"], NAVY),
    ("関係性", "誰と誰が繋がるか", ["医局人事：関連病院の部長は誰の系列か", "紹介・逆紹介：患者はどこから来てどこへ", "師弟・同門・研究グループの繋がり"], RGBColor(0xB8, 0x6A, 0x00)),
]
for i, (t, sub, lines, col) in enumerate(cols):
    x = 0.8 + i * 4.05
    card(s, x, 1.85, 3.85, 0.95,
         [P([R(t, 22, True, WHITE)], space_after=1),
          P([R(sub, 12, False, WHITE)])], fill=col, radius=0.1)
    c = card(s, x, 2.92, 3.85, 2.55,
             [P([R("・" + l, 12.5, False, INK)], line=1.25, space_after=7, align=PP_ALIGN.LEFT) for l in lines],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.16)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.16)
card(s, 0.8, 5.7, 11.7, 1.15,
     [P([R("ポイント：役職表は病院HPに載っている。載っていない「役割」と「関係性」こそMRの付加価値。", 15, True, DEEP)], space_after=5, align=PP_ALIGN.LEFT),
      P([R("第1回で学んだ「この先生、どれだけ偉い？」は肩書の話。今日は「この先生、何を動かせる？」に進化させる。", 13, False, INK)], align=PP_ALIGN.LEFT)],
     fill=PALE, radius=0.08)

# ================================================================ 8. レクチャー①-3 キーパーソン
s = add_slide()
header(s, "LECTURE ①", "キーパーソンは「役職」ではなく「影響力」で見る", "10分", NAVY)
txt(s, 0.8, 1.78, 11.7, 0.5,
    [P([R("次の5つの問いに固有名詞で答えられれば、その診療科は「分かっている」と言える。", 15, True, INK)])])
qs = [
    ("Q1", "治療方針は、誰の一言で決まる？", "◎ 方針決定者", GREEN),
    ("Q2", "新しい治療を最初に試すのは、誰？", "○ アーリーアダプター", GREEN),
    ("Q3", "若手が困ったとき、誰に聞きに行く？", "★ 情報ハブ", RGBColor(0xB8, 0x8A, 0x00)),
    ("Q4", "紹介患者の受け入れ・行き先を差配するのは、誰？", "◇ 連携の要", NAVY),
    ("Q5", "研究会・講演会など「外の顔」は、誰？", "□ 対外の顔", NAVY),
]
y = 2.42
for no, q, tag, col in qs:
    card(s, 0.8, y, 0.75, 0.62, [P([R(no, 14, True, WHITE)])], fill=col, radius=0.25)
    c = card(s, 1.68, y, 7.9, 0.62, [P([R(q, 14.5, True, INK)], align=PP_ALIGN.LEFT)], fill=WHITE, line=LGRAY)
    c.text_frame.margin_left = Inches(0.16)
    card(s, 9.75, y, 2.75, 0.62, [P([R(tag, 12, True, col)])], fill=PALE2, radius=0.15)
    y += 0.74
card(s, 0.8, y + 0.08, 11.7, 0.88,
     [P([R("5つの答えは同一人物とは限らない。", 15, True, RED),
         R("「教授＝キーパーソン」と決めつけた瞬間、他の4人が見えなくなる。", 15, False, INK)], space_after=3, align=PP_ALIGN.LEFT),
      P([R("学会の重鎮（KOL）と、その施設で物事を動かす人（キーパーソン）は別モノ。両方をマップに書き分ける。", 12.5, False, GRAY)], align=PP_ALIGN.LEFT)],
     fill=YPALE, radius=0.08)

# ================================================================ 9. 構造マップの例
s = add_slide()
header(s, "LECTURE ①", "構造マップの描き方 — 例：A大学病院 腎臓内科", "10分", NAVY)
# 中央系列
def node(x, y, w, h, title, sub, fill=WHITE, line=GREEN, tcol=DEEP, mark=""):
    c = card(s, x, y, w, h,
             [P([R((mark + " " if mark else "") + title, 12.5, True, tcol)], space_after=1),
              P([R(sub, 10, False, GRAY)], line=1.05)],
             fill=fill, line=line, radius=0.15)
    return c
# 大学内
box(s, 0.7, 1.85, 7.5, 4.6, fill=PALE2, line=GREEN, line_w=1.0, radius=0.04)
txt(s, 0.9, 1.95, 4.0, 0.35, [P([R("院内（腎臓内科）", 12, True, GREEN)])])
node(2.9, 2.35, 2.3, 0.85, "教授", "◎方針決定・医局人事", fill=PALE, line=DEEP)
node(1.0, 3.5, 2.2, 0.85, "医局長", "★情報ハブ・人事実務\n講演／面会の窓口", fill=YPALE, line=RGBColor(0xB8, 0x8A, 0x00))
node(3.45, 3.5, 2.2, 0.85, "病棟医長", "○入院治療の実務リーダー")
node(5.9, 3.5, 2.2, 0.85, "外来医長", "◇紹介患者の受付・差配", line=NAVY)
node(1.0, 4.75, 2.2, 0.85, "助教（臨床研究）", "○新規治療の導入役\n若手の相談相手")
node(3.45, 4.75, 2.2, 0.85, "専攻医・医員", "実処方の担い手\n数年で関連病院へ異動")
node(5.9, 4.75, 2.2, 0.85, "透析室・コメディカル", "薬剤部・看護・連携室\n※情報の宝庫", line=GRAY, tcol=INK)
connector(s, 4.05, 3.2, 2.1, 3.5)
connector(s, 4.05, 3.2, 4.55, 3.5)
connector(s, 4.05, 3.2, 7.0, 3.5)
connector(s, 2.1, 4.35, 2.1, 4.75)
connector(s, 4.55, 4.35, 4.55, 4.75)
connector(s, 7.0, 4.35, 7.0, 4.75)
# 院外
box(s, 8.5, 1.85, 4.15, 4.6, fill=PALEB, line=NAVY, line_w=1.0, radius=0.04)
txt(s, 8.7, 1.95, 3.6, 0.35, [P([R("院外（エリア）", 12, True, NAVY)])])
node(8.75, 2.4, 3.6, 0.8, "基幹病院B 腎臓内科部長", "元・同医局。教授の直系", line=NAVY)
node(8.75, 3.4, 3.6, 0.8, "連携病院C・クリニック群", "紹介元。逆紹介の受け皿", line=NAVY)
node(8.75, 4.4, 3.6, 0.8, "県の研究会・地方会", "教授が代表世話人", line=NAVY)
node(8.75, 5.4, 3.6, 0.8, "医師会・行政（健診）", "早期発見の入口", line=NAVY)
connector(s, 8.2, 2.75, 8.75, 2.8, color=NAVY, dash="dash")
connector(s, 8.2, 3.9, 8.75, 3.8, color=NAVY, dash="dash")
connector(s, 5.2, 2.75, 8.75, 2.6, color=NAVY, dash="dash")
# 凡例
card(s, 0.7, 6.6, 7.5, 0.5,
     [P([R("◎方針決定　○実行・導入　★情報ハブ　◇連携の要　", 11.5, True, INK),
         R("点線＝院外との関係（人事・紹介・研究会）", 11.5, False, GRAY)])],
     fill=WHITE, line=LGRAY, radius=0.2)
card(s, 8.5, 6.6, 4.15, 0.5,
     [P([R("※本スライドの例はすべて架空です", 10.5, False, GRAY)])], fill=WHITE, line=LGRAY, radius=0.2)

# ================================================================ 10. ワーク①
s = add_slide()
header(s, "WORK ①", "自分の担当施設の「構造マップ」を描く", "15分", GREEN)
card(s, 0.8, 1.85, 7.5, 1.0,
     [P([R("担当大学（または基幹病院）の診療科を1つ選び、", 15, False, INK),
         R("記憶だけで", 15, True, RED),
         R("構造マップを描いてください", 15, False, INK)], align=PP_ALIGN.LEFT, line=1.25)],
     fill=PALE, radius=0.08)
steps = [
    ("STEP 1（7分）", "人を書く：役職・名前を思い出せる限り配置する（テンプレは巻末）"),
    ("STEP 2（4分）", "マークを付ける：◎方針決定 ○実行 ★情報ハブ ◇連携の要"),
    ("STEP 3（4分）", "「？」を付ける：書けない・自信がない場所に赤で？を付ける"),
]
y = 3.05
for t, d in steps:
    card(s, 0.8, y, 2.5, 0.72, [P([R(t, 13, True, WHITE)])], fill=GREEN, radius=0.15)
    c = card(s, 3.45, y, 4.85, 0.72, [P([R(d, 12.5, False, INK)], align=PP_ALIGN.LEFT, line=1.15)], fill=WHITE, line=LGRAY)
    c.text_frame.margin_left = Inches(0.14)
    y += 0.85
card(s, 0.8, 5.7, 7.5, 1.15,
     [P([R("このワークの主役は「？」。", 16, True, RED)], space_after=4, align=PP_ALIGN.LEFT),
      P([R("スラスラ書ける部分はもう財産。書けない場所＝次の面会で聞くべきことリスト。？が多い人ほど収穫の多いワークです。", 13, False, INK)], align=PP_ALIGN.LEFT, line=1.25)],
     fill=YPALE, radius=0.08)
c = card(s, 8.6, 1.85, 3.95, 5.0,
     [P([R("ルール", 15, True, WHITE)], space_after=10),
      P([R("・スマホ・Veeva Linkは見ない（記憶が実力）", 12.5, False, WHITE)], space_after=8, align=PP_ALIGN.LEFT, line=1.25),
      P([R("・名前が出なければ「メガネの若い先生」でOK", 12.5, False, WHITE)], space_after=8, align=PP_ALIGN.LEFT, line=1.25),
      P([R("・医師以外（薬剤部・連携室・秘書）も必ず入れる", 12.5, False, WHITE)], space_after=8, align=PP_ALIGN.LEFT, line=1.25),
      P([R("・きれいに書かない。手が止まったら次のSTEPへ", 12.5, False, WHITE)], align=PP_ALIGN.LEFT, line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06)
c.text_frame.margin_top = Inches(0.25)
c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.22)

# ================================================================ 11. 共有①
s = add_slide()
header(s, "SHARE ①", "共有：ペアで「質問」をプレゼントし合う", "10分", GREEN)
card(s, 0.8, 1.9, 11.7, 0.85,
     [P([R("隣の人とペアになり、お互いのマップを見せ合う（1人3分×2）→ 最後に全体で2名共有（4分）", 15, True, DEEP)])],
     fill=PALE, radius=0.1)
cols = [
    ("話す人（3分）", ["マップを見せながら診療科の構造を説明", "「？」の場所＝自分が知らないことを白状する", "一番のキーパーソンだと思う人と、その理由"], GREEN),
    ("聞く人", ["「その人は誰と繋がっていますか？」と関係性を掘る", "自分の施設との共通点・違いを探す", "最後に「次の面会でこれを聞いたら？」という質問を1つプレゼント"], NAVY),
]
for i, (t, lines, col) in enumerate(cols):
    x = 0.8 + i * 6.0
    card(s, x, 3.0, 5.7, 0.6, [P([R(t, 15, True, WHITE)])], fill=col, radius=0.12)
    c = card(s, x, 3.72, 5.7, 2.2,
             [P([R("・" + l, 12.5, False, INK)], space_after=8, line=1.25, align=PP_ALIGN.LEFT) for l in lines],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.15); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.18)
card(s, 0.8, 6.15, 11.7, 0.75,
     [P([R("他人のマップは最高の鏡。", 14.5, True, DEEP),
         R("「自分の施設ではこの箱が空欄だ」という気づきが、そのまま行動計画になる。", 14.5, False, INK)])],
     fill=YPALE, radius=0.12)

# ================================================================ 11.5 アポネタ製造機（ブリッジ）
s = add_slide()
header(s, "BRIDGE", "最大の不安「継続面会・アポネタ」— ネタは、施設の中にある", kcolor=NAVY)
txt(s, 0.8, 1.78, 11.7, 0.5,
    [P([R("アンケート最多の不安への答え：", 14.5, True, INK),
        R("いま作った構造マップが、そのまま「アポネタ製造機」になります。", 14.5, True, RED)])])
netas = [
    ("①「？」は最高のアポネタ",
     "「先生、○○について教えてください」— 教えを乞う面会は断られにくい。マップの？の数だけ面会理由がある。完全アポ制の施設なら、秘書さん・連携室経由で聞くのも立派な一手。", GREEN, PALE),
    ("② 仮説をぶつける",
     "「私はこう理解していますが、合っていますか？」— 仮説の確認は医師の知的関心をくすぐる、一段上のアポネタ。4Sシートの成功像や原因が、そのままディスカッションテーマになる。", NAVY, PALEB),
    ("③ 情報を先に贈る",
     "学会・地域・連携の情報を先にギフトする。「あのMRは持ってくる」と認知されれば、次の面会は先生の方から理由をくれるようになる。", GOLD, YPALE),
]
for i, (t, d, col, fill) in enumerate(netas):
    x = 0.8 + i * 4.05
    card(s, x, 2.5, 3.85, 0.62, [P([R(t, 14, True, WHITE)])], fill=col, radius=0.1)
    c = card(s, x, 3.24, 3.85, 2.55,
             [P([R(d, 12, False, INK)], line=1.3, align=PP_ALIGN.LEFT)], fill=fill, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.15); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.17)
card(s, 0.8, 6.1, 11.7, 0.85,
     [P([R("「アポネタがない」は、「施設をまだ分かっていない」の別名。", 15, True, RED)], space_after=4),
      P([R("分かるほど、ネタは無限に湧く — だから今日の学びは、明日のアポに直結する。", 13.5, False, INK)])],
     fill=WHITE, line=RED, radius=0.08)

# ================================================================ 12. レクチャー②-1 事実→解釈→打ち手
s = add_slide()
header(s, "LECTURE ②", "「知っている」と「動ける」の間 — 事実→解釈→打ち手", "10分", NAVY)
hdrs = [("事実", "Fact：何を知った？", GREEN), ("解釈", "So What?：だから何が起きる？", RGBColor(0xB8, 0x8A, 0x00)), ("打ち手", "Now What?：だから私は何をする？", RED)]
for i, (t, sub, col) in enumerate(hdrs):
    x = 0.8 + i * 4.15
    card(s, x, 1.85, 3.5, 0.85,
         [P([R(t, 18, True, WHITE)], space_after=1), P([R(sub, 11, False, WHITE)])], fill=col, radius=0.1)
    if i < 2:
        arrow(s, x + 3.55, 2.05, 0.55, 0.45, color=GRAY)
ex_fact = card(s, 0.8, 2.9, 3.5, 3.3,
    [P([R("「教授が来年3月で退官予定らしい」", 14, True, INK)], space_after=10, line=1.3, align=PP_ALIGN.LEFT),
     P([R("医局長との雑談で得た、たった一言のWetな情報", 11.5, False, GRAY)], align=PP_ALIGN.LEFT, line=1.25)],
    fill=PALE2, line=GREEN, anchor=MSO_ANCHOR.TOP)
ex_int = card(s, 4.95, 2.9, 3.5, 3.3,
    [P([R("・後任人事で診療方針が変わり得る", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("・医局員の玉突き異動が起きる", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("・関連病院の部長ポストも動く", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("・研究会の世話人体制が変わる", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("→ 1つの事実から未来が4つ見える", 12.5, True, RGBColor(0xB8, 0x8A, 0x00))], align=PP_ALIGN.LEFT, line=1.2)],
    fill=YPALE, line=RGBColor(0xB8, 0x8A, 0x00), anchor=MSO_ANCHOR.TOP)
ex_act = card(s, 9.1, 2.9, 3.5, 3.3,
    [P([R("・後任候補（准教授・医局長）との関係を今から築く", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("・異動しそうな中堅の「行き先」を追う準備", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("・チーム・上司に共有し、エリア計画に反映", 12, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT),
     P([R("→ 半年後、「なぜ君はもう知ってるの？」と言われる側になる", 12.5, True, RED)], align=PP_ALIGN.LEFT, line=1.2)],
    fill=RPALE, line=RED, anchor=MSO_ANCHOR.TOP)
for c in (ex_fact, ex_int, ex_act):
    c.text_frame.margin_top = Inches(0.18); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.18)
card(s, 0.8, 6.35, 11.7, 0.6,
     [P([R("この「So What? / Now What?」を、施設・エリア単位で体系的にやる道具が ", 14, False, INK),
         R("４Sシート", 15, True, DEEP), R("。", 14, False, INK)])],
     fill=PALE, radius=0.12)

# ================================================================ 13. 4Sシートとは
s = add_slide()
header(s, "LECTURE ②", "４Sシート — 課題・原因・解決方法を1枚で可視化する", "10分", NAVY)
quads = [
    (0.8, 1.9, "① 成功像", "あるべき姿・ゴール", "担当施設・エリアが「こうなっていたら最高」という状態を具体的に書く。ここから書き始めるのが鉄則。", GREEN, PALE),
    (6.75, 1.9, "② 現状・課題", "理想とのGAP", "成功像と現実の差分を書く。「〜できていない」「〜が滞っている」。数字や事実で書けると強い。", NAVY, PALEB),
    (0.8, 4.35, "③ 原因", "なぜそのGAPがあるのか", "課題の裏にある真因。「なぜ？」を3回繰り返して、表面的な理由の奥まで掘る。", RGBColor(0xB8, 0x8A, 0x00), YPALE),
    (6.75, 4.35, "④ 解決策", "自分は何を打つか", "原因を解消する打ち手。講演会・面会・資材・連携…会社の武器と自分の行動を組み合わせる。", RED, RPALE),
]
for x, y, t, sub, d, col, fill in quads:
    card(s, x, y, 5.75, 0.72,
         [P([R(t, 16, True, WHITE), R("　" + sub, 11.5, False, WHITE)])], fill=col, radius=0.1)
    c = card(s, x, y + 0.78, 5.75, 1.42,
             [P([R(d, 12.5, False, INK)], line=1.3, align=PP_ALIGN.LEFT)], fill=fill, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.12); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.16)
arrow(s, 6.3, 2.6, 0.4, 0.4, color=GRAY)                     # ①→②
a = arrow(s, 6.42, 3.82, 0.42, 0.48, color=GRAY, direction="down")  # ②→③（斜め下・左向き）
a.rotation = 45
arrow(s, 6.3, 5.05, 0.4, 0.4, color=GRAY)                    # ③→④
# ④→① 確認の戻り矢印（右端を上へ）
a = arrow(s, 12.62, 2.55, 0.32, 3.3, color=GREEN2, direction="up")
card(s, 0.8, 6.5, 11.7, 0.62,
     [P([R("書く順番：①成功像 → ②現状・課題 → ③原因 → ④解決策。", 12.5, True, DEEP),
         R("　現状から書くと「愚痴のリスト」、理想から書くと「戦略」になる。", 12, False, INK)], space_after=3),
      P([R("仕上げの確認：④→①へ戻り「この打ち手で、成功像に本当に近づくか？」をチェック — これで4Sが1周閉じる。", 12, True, GREEN)])],
     fill=WHITE, line=GREEN, radius=0.12)

# ================================================================ 14. 4S記入例
s = add_slide()
header(s, "LECTURE ②", "記入例：腎臓内科 × エリア連携（架空の例）", "10分", NAVY)
exq = [
    (0.8, 1.9, "① 成功像", GREEN, PALE,
     "エリアの連携病院・クリニックから、専門治療が必要な患者さんが適切なタイミングで大学に紹介され、安定した患者さんは地域に逆紹介される「双方向の流れ」ができている。"),
    (6.75, 1.9, "② 現状・課題", NAVY, PALEB,
     "紹介はあるが、かなり進行してからの紹介が中心。逆紹介も滞りがちで大学外来がパンク気味。連携の「入口」も「出口」も詰まっている。"),
    (0.8, 4.2, "③ 原因（なぜ×3）", RGBColor(0xB8, 0x8A, 0x00), YPALE,
     "なぜ遅い？→紹介の目安が浸透していない → なぜ？→大学と地域の医師が診療科レベルで顔見知りでない → なぜ？→合同で話す「場」がここ数年ない。"),
    (6.75, 4.2, "④ 解決策", RED, RPALE,
     "教授（対外の顔）×連携病院の先生方による地域連携の場（研究会・講演会）を企画し、紹介・逆紹介の目安を共有。医局長（情報ハブ）を実務窓口に、連携室と共催で設計する。"),
]
for x, y, t, col, fill, d in exq:
    card(s, x, y, 5.75, 0.6, [P([R(t, 15, True, WHITE)])], fill=col, radius=0.1)
    c = card(s, x, y + 0.66, 5.75, 1.5,
             [P([R(d, 12, False, INK)], line=1.28, align=PP_ALIGN.LEFT)], fill=fill, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.1); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
card(s, 0.8, 6.5, 11.7, 0.62,
     [P([R("注目：", 13, True, RED),
         R("「講演会」が先にあるのではない。成功像→課題→原因と掘った結果、手段として会が出てくる。この順番が説得力の正体。", 13, True, INK)], space_after=3),
      P([R("最後に④→①の確認：「この会で紹介の目安が共有されれば、双方向の流れに近づくか？」→ Yesなら実行。", 12, False, GRAY)])],
     fill=YPALE, radius=0.12)

# ================================================================ 15. 良い4S・惜しい4S
s = add_slide()
header(s, "LECTURE ②", "「良い4S」と「惜しい4S」— 3つのチェックポイント", "10分", NAVY)
checks = [
    ("CHECK 1", "課題は「ギャップ」で書けているか",
     "△ 先生に会えていない", "○ 成功像は月2回の情報交換。現状は月0回、面会は挨拶のみ",
     "「〜できていない」単体は感想。成功像とセットで初めて課題になる。"),
    ("CHECK 2", "原因は「なぜ」を3回掘ったか",
     "△ 先生が忙しいから", "○ 忙しい中でも会う医師はいる → 優先されない → 会う価値を提示できていない",
     "1回目の「なぜ」は大抵、環境のせい。3回掘ると自分の打ち手が見える。"),
    ("CHECK 3", "解決策は「自分が動ける」ことか",
     "△ 本社が資材を作るべき", "○ 私が医局長に○○の相談をし、△△を企画する",
     "主語が自分でない解決策は実行されない。明日の自分の行動で書く。"),
]
y = 1.85
for no, t, bad, good, note in checks:
    card(s, 0.8, y, 1.5, 1.5, [P([R(no, 12.5, True, WHITE)])], fill=NAVY, radius=0.12)
    c = card(s, 2.42, y, 5.0, 1.5,
             [P([R(t, 13.5, True, DEEP)], space_after=5, align=PP_ALIGN.LEFT),
              P([R(note, 11.5, False, GRAY)], line=1.2, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.12); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.14)
    c = card(s, 7.55, y, 4.95, 1.5,
             [P([R(bad, 11.5, True, RED)], space_after=5, line=1.15, align=PP_ALIGN.LEFT),
              P([R(good, 11.5, True, GREEN)], line=1.15, align=PP_ALIGN.LEFT)],
             fill=PALE2, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.14)
    y += 1.68
txt(s, 0.8, 6.82, 11.7, 0.3,
    [P([R("△＝惜しい例　○＝直した例。ワーク②の後、この3つで自分のシートをセルフチェックします。", 12, False, GRAY)])])

# ================================================================ 16. ワーク②
s = add_slide()
header(s, "WORK ②", "自分の担当施設・エリアで「4Sシート」を書く", "20分", GREEN)
card(s, 0.8, 1.85, 7.5, 1.0,
     [P([R("ワーク①のマップと手持ちの情報を総動員して、担当施設（またはエリア）の4Sシートを1枚書き切る", 15, True, INK)], align=PP_ALIGN.LEFT, line=1.3)],
     fill=PALE, radius=0.08)
steps = [
    ("5分", "① 成功像", "1年後、この施設・エリアが「こうなっていたら最高」を具体的に"),
    ("5分", "② 現状・課題", "成功像とのGAPを事実ベースで。数字が入るとなお良い"),
    ("5分", "③ 原因", "「なぜ？」を3回。人・関係性・場の不足まで掘る"),
    ("5分", "④ 解決策", "主語は自分。誰に・何を・いつやるかまで書く"),
]
y = 3.05
for tm, t, d in steps:
    card(s, 0.8, y, 0.95, 0.7, [P([R(tm, 13, True, WHITE)])], fill=GREEN, radius=0.2)
    card(s, 1.87, y, 1.95, 0.7, [P([R(t, 13, True, DEEP)])], fill=PALE2, radius=0.12)
    c = card(s, 3.94, y, 4.36, 0.7, [P([R(d, 11.5, False, INK)], align=PP_ALIGN.LEFT, line=1.15)], fill=WHITE, line=LGRAY)
    c.text_frame.margin_left = Inches(0.12)
    y += 0.82
card(s, 0.8, 6.4, 7.5, 0.62,
     [P([R("合言葉：完璧より仮説。60点で書き切る。", 14.5, True, RED),
         R("　空欄はワーク①の「？」と同じ、次の宿題。", 12.5, False, INK)])],
     fill=YPALE, radius=0.12)
c = card(s, 8.6, 1.85, 3.95, 5.15,
     [P([R("困ったときのヒント", 15, True, WHITE)], space_after=10),
      P([R("・成功像が出ない → 「上司に自慢したい状態」を想像する", 12, False, WHITE)], space_after=8, align=PP_ALIGN.LEFT, line=1.25),
      P([R("・課題が出ない → マップの「？」や、詰まっている流れ（紹介・面会・採用）を探す", 12, False, WHITE)], space_after=8, align=PP_ALIGN.LEFT, line=1.25),
      P([R("・原因が浅い → 「それでも動く人がいるのはなぜ？」と自問する", 12, False, WHITE)], space_after=8, align=PP_ALIGN.LEFT, line=1.25),
      P([R("・解決策が出ない → キーパーソン（◎○★◇）を1人選び、その人と何をするかを考える", 12, False, WHITE)], align=PP_ALIGN.LEFT, line=1.25)],
     fill=DEEP, anchor=MSO_ANCHOR.TOP, radius=0.06)
c.text_frame.margin_top = Inches(0.22); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.2)

# ================================================================ 17. 共有②
s = add_slide()
header(s, "SHARE ②", "共有：3人グループで「戦略」として語る", "10分", GREEN)
card(s, 0.8, 1.9, 11.7, 0.8,
     [P([R("3人1組。1人3分（発表2分＋フィードバック1分）× 3ラウンド", 16, True, DEEP)])],
     fill=PALE, radius=0.1)
card(s, 0.8, 2.95, 5.7, 0.6, [P([R("発表者（2分）", 15, True, WHITE)])], fill=GREEN, radius=0.12)
c = card(s, 0.8, 3.67, 5.7, 2.3,
     [P([R("4Sシートを見せず、口頭で語るのがおすすめ：", 12.5, True, INK)], space_after=7, align=PP_ALIGN.LEFT),
      P([R("「私の施設は本当は◯◯◯になれるはずです（成功像）。でも今は△△△です（課題）。原因は□□□。だから私は◇◇◇をやります（解決策）」", 12.5, False, INK)], line=1.35, align=PP_ALIGN.LEFT, space_after=7),
      P([R("→ この型で話せたら、もう支店会議で戦略を語れる。", 12.5, True, GREEN)], align=PP_ALIGN.LEFT)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
c.text_frame.margin_top = Inches(0.15); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.18)
card(s, 6.8, 2.95, 5.7, 0.6, [P([R("聞き手（1分でフィードバック）", 15, True, WHITE)])], fill=NAVY, radius=0.12)
c = card(s, 6.8, 3.67, 5.7, 2.3,
     [P([R("質問はこの2つだけ：", 12.5, True, INK)], space_after=8, align=PP_ALIGN.LEFT),
      P([R("❶ 「その原因、本当に真因ですか？」（もう1回なぜ？を促す）", 12.5, False, INK)], space_after=8, line=1.3, align=PP_ALIGN.LEFT),
      P([R("❷ 「その解決策、あなたにしかできない要素はどこ？」", 12.5, False, INK)], space_after=8, line=1.3, align=PP_ALIGN.LEFT),
      P([R("ダメ出しではなく、シートを1段深くするための質問。", 12, False, GRAY)], align=PP_ALIGN.LEFT)],
     fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
c.text_frame.margin_top = Inches(0.15); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.18)
card(s, 0.8, 6.25, 11.7, 0.7,
     [P([R("時間が余ったグループは：", 13, True, NAVY),
         R("3枚のシートに共通する「エリアの課題」がないか探してみる → レクチャー③に繋がります。", 13, False, INK)])],
     fill=PALEB, radius=0.12)

# ================================================================ 18. レクチャー③ 大学はハブ
s = add_slide()
header(s, "LECTURE ③", "大学は「エリアのハブ」— 4Sをエリア戦略へ広げる", "5分", NAVY)
txt(s, 0.8, 1.8, 11.7, 0.5,
    [P([R("大学が分かると、なぜエリア全体が見えるのか。大学には3つの「流れ」の源流があるから。", 15, True, INK)])])
flows = [
    ("医師の流れ", "医局人事", "関連病院の部長・医長は元医局員。大学の人事が動けば、エリアの処方方針も動く。", GREEN, PALE),
    ("患者の流れ", "紹介・逆紹介", "重症例は大学へ、安定例は地域へ。この動線が分かれば「どの施設に何を届けるか」が決まる。", NAVY, PALEB),
    ("情報の流れ", "研究会・講演会・治療方針", "大学発の治療方針は、時間差でエリアに広がる。源流を知る人は先回りできる。", RGBColor(0xB8, 0x6A, 0x00), YPALE),
]
for i, (t, sub, d, col, fill) in enumerate(flows):
    x = 0.8 + i * 4.05
    card(s, x, 2.45, 3.85, 0.9,
         [P([R(t, 17, True, WHITE)], space_after=1), P([R(sub, 11.5, False, WHITE)])], fill=col, radius=0.1)
    c = card(s, x, 3.47, 3.85, 1.75,
             [P([R(d, 12.5, False, INK)], line=1.3, align=PP_ALIGN.LEFT)], fill=fill, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.13); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.16)
card(s, 0.8, 5.5, 11.7, 1.35,
     [P([R("エリアストーリーの型（この1文で語れれば合格）", 14, True, WHITE)], space_after=6),
      P([R("「大学で ", 15, False, WHITE), R("〇〇", 15, True, YELL),
         R(" が分かった。だからエリアでは ", 15, False, WHITE), R("△△", 15, True, YELL),
         R(" が起きるはず。だから私は ", 15, False, WHITE), R("□□（施設）", 15, True, YELL),
         R(" から ", 15, False, WHITE), R("◇◇（行動）", 15, True, YELL),
         R(" を始める」", 15, False, WHITE)], line=1.35)],
     fill=DEEP, radius=0.08)

# ================================================================ 18.5 優先順位の3つのモノサシ
s = add_slide()
header(s, "LECTURE ③", "全部は回れない — エリアの優先順位「3つのモノサシ」", "5分", NAVY)
txt(s, 0.8, 1.75, 11.7, 0.45,
    [P([R("期待の声「県全体の攻略」「優先順位付け」への答え：施設を3つのモノサシで採点し、攻める順番を決める。", 14, True, INK)])])
measures = [
    ("モノサシ①", "医局の繋がりの太さ", "元医局員がいるか。人事で人が動く先か。大学の方針が波及しやすい施設ほど高得点", GREEN),
    ("モノサシ②", "患者の流れの量", "紹介・逆紹介がどれだけ行き来しているか。流れが太い施設は、変化の影響も大きい", NAVY),
    ("モノサシ③", "動かせる度", "会えるか。キーパーソンと関係があるか。どんな好条件も、動かせなければ絵に描いた餅", GOLD),
]
for i, (no, t, d, col) in enumerate(measures):
    x = 0.8 + i * 4.05
    card(s, x, 2.3, 3.85, 0.6,
         [P([R(no + "　", 11.5, True, WHITE), R(t, 13.5, True, WHITE)])], fill=col, radius=0.1)
    c = card(s, x, 3.0, 3.85, 1.15,
             [P([R(d, 11, False, INK)], line=1.22, align=PP_ALIGN.LEFT)], fill=PALE2, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
# 採点例テーブル
tbl = [
    ("施設（例）", "繋がり", "患者の流れ", "動かせる度", "打ち方", True),
    ("基幹病院B（部長が元医局員）", "◎", "◎", "○", "最優先：足で通う", False),
    ("連携クリニック群C", "○", "◎", "△", "連携室・会で面として攻める", False),
    ("遠方のD病院", "△", "△", "△", "情報収集のみ（今は捨てる）", False),
]
ws = [3.6, 1.35, 1.55, 1.55, 3.65]
y = 4.35
for r, row in enumerate(tbl):
    x = 0.8
    hdr = row[5]
    for ci in range(5):
        val = row[ci]
        c = card(s, x, y, ws[ci], 0.5,
                 [P([R(val, 11 if not hdr else 11.5, True if (hdr or ci in (1,2,3)) else False,
                      WHITE if hdr else (GREEN if ci in (1,2,3) else INK))],
                    align=PP_ALIGN.LEFT if ci in (0,4) and not hdr else PP_ALIGN.CENTER)],
                 fill=NAVY if hdr else WHITE, line=LGRAY, radius=0.06)
        if ci in (0, 4) and not hdr:
            c.text_frame.margin_left = Inches(0.1)
        x += ws[ci] + 0.02
    y += 0.55
card(s, 0.8, 6.65, 11.7, 0.5,
     [P([R("「頑張って会いに行く施設」と「情報だけ取る施設」を分けるのが戦略。", 13, True, DEEP),
         R("　県攻略は、捨てる勇気から始まる。", 13, True, RED)])],
     fill=PALE, radius=0.12)

# ================================================================ 19. ミニワーク（延長時）
s = add_slide()
header(s, "MINI WORK", "エリアストーリーを30秒で語る（延長時／宿題）", "10分", GREEN)
card(s, 0.8, 1.9, 11.7, 1.5,
     [P([R("自分の4Sシートから1つ選び、先ほどの型でエリアストーリーを作る（3分）", 15.5, True, DEEP)], space_after=6),
      P([R("→ 隣の人に30秒で語る（30秒×2人）→ 全体で1〜2名", 14, False, INK)])],
     fill=PALE, radius=0.08)
c = card(s, 0.8, 3.7, 11.7, 1.9,
     [P([R("記入欄（メモ）", 13, True, GRAY)], space_after=10, align=PP_ALIGN.LEFT),
      P([R("大学で（　　　　　　　　　　　　　）が分かった。だからエリアでは（　　　　　　　　　　　　　）が起きるはず。", 14, False, INK)], space_after=10, line=1.5, align=PP_ALIGN.LEFT),
      P([R("だから私は（　　　　　　　　）という施設から、（　　　　　　　　　　　　　）を始める。", 14, False, INK)], line=1.5, align=PP_ALIGN.LEFT)],
     fill=WHITE, line=GREEN, anchor=MSO_ANCHOR.TOP)
c.text_frame.margin_top = Inches(0.18); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.25)
card(s, 0.8, 5.85, 11.7, 0.95,
     [P([R("60分運営で時間がない場合は宿題に：", 13.5, True, RED),
         R("次回のチーム会議・上司との同行前に、この1文を作って口頭で伝えてみる。", 13.5, False, INK)], space_after=3),
      P([R("「シートを書ける人」より「ストーリーを語れる人」が、エリアを任される人。", 12.5, True, GRAY)])],
     fill=YPALE, radius=0.1)

# ================================================================ 19.5 全国気づきリスト
s = add_slide()
header(s, "NETWORK", "今日の気づきを「全国62名の財産」にする — 気づきリスト")
steps_k = [
    ("STEP 1｜今日", "終了前に1人1行、「一番の気づき」をチャットに投稿（30秒）。小さな気づきほど歓迎"),
    ("STEP 2｜今週", "事務局が「全国気づきリスト」として集約し、録画とあわせて全員（欠席者含む）へ共有"),
    ("STEP 3｜明日から", "現場でうまくいった工夫・事例を随時追加。使ってみた人は「やってみた結果」も書き戻す"),
]
y = 2.0
for t, d in steps_k:
    card(s, 0.8, y, 2.55, 0.95, [P([R(t, 13.5, True, WHITE)])], fill=GREEN, radius=0.12)
    c = card(s, 3.5, y, 7.0, 0.95, [P([R(d, 12, False, INK)], line=1.25, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = Inches(0.17)
    if y < 3.9:
        arrow(s, 1.9, y + 1.0, 0.35, 0.28, color=GREEN2, direction="down")
    y += 1.33
c = card(s, 10.75, 2.0, 1.77, 3.61,
     [P([R("なぜ\nやるか", 13, True, WHITE)], line=1.2)],
     fill=DEEP, radius=0.1)
card(s, 0.8, 6.0, 11.7, 1.0,
     [P([R("アンケートで圧倒的1位の期待は「他メンバーの事例・考え方」。", 13.5, True, DEEP)], space_after=4),
      P([R("62名の現場知が1枚のリストに集まれば、どんな研修より強い教材になる。勉強会は今日が最終回、", 12.5, False, INK),
         R("ネットワークは今日が初回。", 12.5, True, RED)])],
     fill=YPALE, radius=0.08)

# ================================================================ GIFT① 7つの習慣
s = add_slide()
header(s, "GIFT ①", "私からのギフト：明日から真似できる「大学担当 7つの習慣」", kcolor=GOLD)
habits = [
    ("① 面会後5分メモ", "Wetな情報は3時間で蒸発する。廊下を出たらその場でメモ。誰が・何を・どんな表情で、まで"),
    ("② 週1回のHP巡回", "外来表・医局員一覧・行事案内の更新は、異動や方針転換の予兆。変化に最初に気づく人になる"),
    ("③ 秘書さん・連携室に名前を覚えてもらう", "面会の成否の3割は「取り次ぎ」で決まる。医師の手前にいる人こそ丁寧に"),
    ("④ 質問を1つ持って行く", "用件がない日ほど「教えてください」が効く。教育的な質問は先生との関係を深める"),
    ("⑤ 4月と10月は種まき月間", "人事異動の直後は、新任の先生も情報を欲しがっている。関係構築のゴールデンタイム"),
    ("⑥ 若手・専攻医こそ丁寧に", "3年後、エリアの関連病院で「あの時のMRさん」として再会する。未来への先行投資"),
    ("⑦ 情報は先に差し出す", "学会・地域・連携の情報を先にギブする。情報は、出す人のところに集まってくる"),
]
for i, (t, d) in enumerate(habits):
    x = 0.8 + (i % 2) * 6.0
    y = 1.82 + (i // 2) * 1.16
    c = card(s, x, y, 5.7, 1.04,
             [P([R(t, 13, True, GOLD)], space_after=3, align=PP_ALIGN.LEFT),
              P([R(d, 11, False, INK)], line=1.18, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
c = card(s, 6.8, 1.82 + 3 * 1.16, 5.7, 1.04,
         [P([R("どれも特別な才能は要らない。", 12.5, True, DEEP)], space_after=3),
          P([R("1つでも習慣になれば、今日の90分の元は取れます。", 11.5, False, INK)])],
         fill=PALE, anchor=MSO_ANCHOR.MIDDLE)
txt(s, 0.8, 6.72, 11.7, 0.35,
    [P([R("※ 時間が押した場合は持ち帰り用。次の1週間で「まず1つ」選んで試してみてください。", 11.5, False, GRAY)])])

# ================================================================ GIFT② なるほど視点6選
s = add_slide()
header(s, "GIFT ②", "視点が変わる「なるほど」6選 — 活動に取り入れてほしい見方", kcolor=GOLD)
views = [
    ("「会えない日」は「観察日」", "面会ゼロでも収穫はある。外来表・掲示板・待合の混み具合・医局前の空気が施設を語っている。"),
    ("医師の後ろに「流れ」を見る", "目の前の1人は、人事・患者・情報という3つの流れの結節点。1人の言葉からエリアが読める。"),
    ("大学1施設＝エリア10施設", "大学での30分は、関連病院10軒分の価値になり得る。だから大学担当は「割に合う」仕事。"),
    ("「知らない」と言えるのは強さ", "分からないことを「？」として言語化できた人から成長する。曖昧なままが一番怖い。"),
    ("会場では「誰と誰が話すか」を見る", "講演会・研究会は構造マップの答え合わせの場。演題より人の繋がりに注目する。"),
    ("記録は「未来の自分」への申し送り", "構造マップと4Sは、担当が変わっても戦える資産。引き継ぎ資料としても最強。"),
]
for i, (t, d) in enumerate(views):
    x = 0.8 + (i % 3) * 4.02
    y = 1.9 + (i // 3) * 2.35
    c = card(s, x, y, 3.82, 2.2,
             [P([R("なるほど", 10, True, WHITE)], space_after=0)],
             fill=GOLD, radius=0.08, anchor=MSO_ANCHOR.TOP)
    # 上帯つきカード：帯の下に白ボディを重ねる
    body = card(s, x, y + 0.34, 3.82, 1.86,
             [P([R(t, 13, True, DEEP)], space_after=6, line=1.15, align=PP_ALIGN.LEFT),
              P([R(d, 11, False, INK)], line=1.25, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
    body.text_frame.margin_top = Inches(0.12)
    body.text_frame.margin_left = body.text_frame.margin_right = Inches(0.15)
card(s, 0.8, 6.55, 11.7, 0.5,
     [P([R("共通点：どれも「追加の時間」はほぼゼロ。", 13, True, DEEP),
         R("　変えるのは行動量ではなく、ものの見方。", 13, False, INK)])],
     fill=PALE, radius=0.15)

# ================================================================ GIFT③ 4Sを完璧に仕上げる8つのコツ
s = add_slide()
header(s, "GIFT ③", "４Sシートを完璧に仕上げる「8つのコツ」", kcolor=GOLD)
card(s, 0.8, 1.82, 5.75, 0.52, [P([R("書くときの4つ", 14.5, True, WHITE)])], fill=GREEN, radius=0.12)
card(s, 6.75, 1.82, 5.75, 0.52, [P([R("磨くときの4つ", 14.5, True, WHITE)])], fill=NAVY, radius=0.12)
tips_w = [
    ("1．成功像は「日付＋固有名詞＋状態」", "「1年後、B病院から早期の紹介が月5件ある」— 曖昧な理想は測れず、測れないものは達成できない"),
    ("2．主役は患者さんと医療の姿", "自社都合の成功像は医師に見せられない。医療の姿で書けば、そのまま先生と共有できる4Sになる"),
    ("3．課題は数字とセット", "「少ない」ではなく「月1件」。数字で書けない課題は、現状把握がまだ足りないサイン"),
    ("4．原因は「人・関係性・場・情報」の4方向", "この4分類で探すと漏れがない。大抵の真因は「場がない」「関係が診療科レベルでない」に潜む"),
]
tips_m = [
    ("5．3回目の「なぜ」は自分に向ける", "環境のせいで終わらせず「自分に何が足りない？」まで掘る。そこから先だけが自分で変えられる"),
    ("6．解決策は「電話1本サイズ」に割る", "最初の一歩が小さいほど実行される。「連携室に共催の前例を1本聞く」から始まる戦略もある"),
    ("7．2分で語れるかテスト", "シートを見ずに語れない箇所＝考え切れていない箇所。語る練習が最高の推敲になる"),
    ("8．四半期に1回、書き直す", "4Sは提出物ではなく「生きた作戦板」。情報が更新されたら書き換えるから武器であり続ける"),
]
for col_i, tips in enumerate((tips_w, tips_m)):
    x = 0.8 + col_i * 5.95
    lcol = GREEN if col_i == 0 else NAVY
    y = 2.44
    for t, d in tips:
        c = card(s, x, y, 5.75, 0.98,
                 [P([R(t, 12.5, True, lcol)], space_after=3, align=PP_ALIGN.LEFT),
                  P([R(d, 10.5, False, INK)], line=1.18, align=PP_ALIGN.LEFT)],
                 fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
        c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
        y += 1.06
txt(s, 0.8, 6.72, 11.7, 0.3,
    [P([R("今日のワーク②では1〜4を、宿題（2週間以内の上司共有）では5〜8を意識してみてください。", 11.5, True, GRAY)])])

# ================================================================ GIFT④ 失敗と処方箋
s = add_slide()
header(s, "GIFT ④", "大学担当がやりがちな3つの失敗と処方箋", kcolor=GOLD)
txt(s, 0.8, 1.75, 11.7, 0.45,
    [P([R("どれも「頑張っている人」ほど陥る罠。先に知っておけば、数年分ショートカットできます。", 14, True, INK)])])
fails = [
    ("失敗①　教授にだけ通う", "「教授に会えている＝担当できている」という錯覚。教授は多忙で、現場の情報はむしろ薄い",
     "医局長・若手・コメディカルまで「面」で通う。構造マップの◎○★◇を巡回ルートにする"),
    ("失敗②　集めて満足する", "手帳は情報でいっぱい、でも行動はゼロ。「情報通のMR」で止まってしまう",
     "情報を得た日は「So What?（だから何）」を1行書き足す。書けない情報は、まだ活かせていない情報"),
    ("失敗③　講演会が目的化する", "「開催すること」がゴールになり、成功像が消える。終わった後に何も変わらない会になる",
     "4Sの④→①確認を使う：「この会で成功像に近づくか？」にYesと言えない企画は、やり直す"),
]
y = 2.3
for t, d, fix in fails:
    c = card(s, 0.8, y, 5.2, 1.32,
             [P([R(t, 13.5, True, RED)], space_after=4, align=PP_ALIGN.LEFT),
              P([R(d, 11, False, INK)], line=1.2, align=PP_ALIGN.LEFT)],
             fill=RPALE, line=RED, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
    arrow(s, 6.12, y + 0.44, 0.5, 0.44, color=GRAY)
    c = card(s, 6.75, y, 5.75, 1.32,
             [P([R("処方箋", 11, True, GREEN)], space_after=3, align=PP_ALIGN.LEFT),
              P([R(fix, 11.5, True, INK)], line=1.22, align=PP_ALIGN.LEFT)],
             fill=PALE, line=GREEN, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
    y += 1.48
card(s, 0.8, 6.75, 11.7, 0.42,
     [P([R("失敗は恥ではなく教材。今日の4Sシートには、この3つの「防止装置」がすでに組み込まれています。", 12, True, DEEP)])],
     fill=YPALE, radius=0.15)

# ================================================================ GIFT⑤ 4S習熟度セルフチェック
s = add_slide()
header(s, "GIFT ⑤", "４S習熟度セルフチェック — 自分は今どのレベル？", kcolor=GOLD)
levels = [
    ("LEVEL 1", "埋められる", "4つの箱を自分の言葉で書き切れる", "← 今日、全員ここに到達", PALE, GREEN),
    ("LEVEL 2", "根拠がある", "全項目が数字・固有名詞で裏づけられている", "目安：2週間以内（上司共有まで）", PALEB, NAVY),
    ("LEVEL 3", "2分で語れる", "シートを見ずに、質問にも答えながら戦略として話せる", "目安：1ヶ月（実行開始まで）", YPALE, GOLD),
    ("LEVEL 4", "エリアへ展開", "大学の4Sを、エリア全施設の打ち手に翻訳できる", "ここまで来たら、大学担当として一人前", RPALE, RED),
]
base_bottom = 6.5
for i, (lv, t, d, note, fill, col) in enumerate(levels):
    h = 1.35 + i * 0.75
    x = 0.85 + i * 2.98
    y = base_bottom - h
    c = card(s, x, y, 2.78, h,
             [P([R(lv, 12, True, col)], space_after=2),
              P([R(t, 15.5, True, col)], space_after=5),
              P([R(d, 11, False, INK)], line=1.2, align=PP_ALIGN.LEFT, space_after=4),
              P([R(note, 10, True, GRAY)], align=PP_ALIGN.LEFT)],
             fill=fill, line=col, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.12)
    c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.13)
card(s, 0.85, 6.58, 11.66, 0.5,
     [P([R("卒業基準：", 13.5, True, DEEP),
         R("上司の「あなたのエリア戦略は？」に、4Sの型（成功像→課題→原因→解決策）で即答できること。", 13.5, True, INK)])],
     fill=PALE, radius=0.12)

# ================================================================ 20. まとめ
s = add_slide()
box(s, 0, 0, 13.333, 7.5, fill=DEEP, shape=MSO_SHAPE.RECTANGLE)
txt(s, 0.9, 0.55, 11.5, 0.5, [P([R("まとめ", 16, True, RGBColor(0xBF, 0xE8, 0xD2))])])
txt(s, 0.9, 1.15, 11.5, 1.0,
    [P([R("ちょっと分かるだけで、世界が変わる", 34, True, WHITE)])])
msgs = [
    ("整理", "情報は「構造（人・役割・関係性）」で整理した瞬間、武器になる。書けない場所＝次に聞くこと。"),
    ("変換", "事実→解釈→打ち手。4Sシートに書けば、課題と戦略を1枚で・2分で語れる。"),
    ("拡張", "大学は医師・患者・情報の流れの源流。大学が分かれば、エリアの打ち手が先回りできる。"),
]
y = 2.35
for t, d in msgs:
    card(s, 0.9, y, 1.6, 0.95, [P([R(t, 18, True, DEEP)])], fill=YELL, radius=0.15)
    c = card(s, 2.7, y, 9.7, 0.95,
             [P([R(d, 14.5, False, WHITE)], align=PP_ALIGN.LEFT, line=1.25)],
             fill=RGBColor(0x11, 0x63, 0x45))
    c.text_frame.margin_left = Inches(0.22)
    y += 1.12
card(s, 0.9, 5.85, 11.5, 1.15,
     [P([R("シリーズを通じたゴール：担当者としての「自覚」", 15, True, YELL)], space_after=5),
      P([R("イロハを知り（第1回）、会えるようになり（第2回）、情報をつかみ（第3回）、今日、それを戦略に変えた。", 13.5, False, WHITE)], space_after=3),
      P([R("「この施設とこのエリアのことは、社内の誰よりも私が分かっている」— そう言える担当者になろう。", 13.5, True, WHITE)])],
     fill=RGBColor(0x08, 0x3B, 0x29), radius=0.08, anchor=MSO_ANCHOR.MIDDLE)
footer_dummy = None  # 表紙同様フッター無し（ページ番号は次スライドで継続）
PAGE[0] += 1

# ================================================================ 21. ネクストアクション
s = add_slide()
header(s, "NEXT ACTION", "明日からの3つの行動 — 研修を「成果」に変える")
acts = [
    ("今週中", "「？」を1つ埋める", "構造マップの「？」から1つ選び、次の面会・電話で確認する。医師以外（連携室・薬剤部）に聞くのも立派な一手。", GREEN),
    ("2週間以内", "4Sを上司・チームに見せる", "自分の4Sシートを上司または同僚1人に見せ、「原因は真因か？」のフィードバックを1つもらう。", NAVY),
    ("1ヶ月以内", "解決策を1つ実行する", "4Sシートの解決策から1つを実行に移す。結果はどうあれ「4Sを回した」経験が財産になる。", RED),
]
y = 1.9
for tm, t, d, col in acts:
    card(s, 0.8, y, 1.9, 1.25, [P([R(tm, 15, True, WHITE)])], fill=col, radius=0.12)
    c = card(s, 2.85, y, 9.65, 1.25,
             [P([R(t, 15.5, True, DEEP)], space_after=4, align=PP_ALIGN.LEFT),
              P([R(d, 12.5, False, INK)], line=1.25, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = Inches(0.2)
    y += 1.45
card(s, 0.8, 6.3, 11.7, 0.75,
     [P([R("情報のメンテナンスを習慣に：", 13.5, True, DEEP),
         R("病院HP・Veeva Link・スマイルPJ等での更新チェックを定例化。構造マップと4Sは「生き物」、四半期に1回は書き直す。", 13, False, INK)])],
     fill=PALE, radius=0.1)

# ================================================================ 22. 付録A 構造マップテンプレ
s = add_slide()
header(s, "APPENDIX A", "構造マップ テンプレート（印刷・配布用）", kcolor=GRAY)
box(s, 0.7, 1.8, 7.6, 4.7, fill=PALE2, line=GREEN, line_w=1.0, radius=0.03)
txt(s, 0.9, 1.9, 4.0, 0.35, [P([R("院内：診療科（　　　　　　科）", 12, True, GREEN)])])
def blank_node(x, y, w, h, label, line=GREEN):
    c = card(s, x, y, w, h,
             [P([R(label, 11, True, GRAY)], space_after=2),
              P([R("氏名：　　　　　　", 10.5, False, INK)], align=PP_ALIGN.LEFT),
              P([R("マーク：◎○★◇？", 10, False, LGRAY)], align=PP_ALIGN.LEFT)],
             fill=WHITE, line=line, radius=0.12, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.06); c.text_frame.margin_left = Inches(0.1)
    return c
blank_node(3.0, 2.3, 2.4, 1.0, "教授／診療科長", line=DEEP)
blank_node(0.95, 3.55, 2.25, 1.0, "医局長")
blank_node(3.45, 3.55, 2.25, 1.0, "病棟医長")
blank_node(5.95, 3.55, 2.25, 1.0, "外来医長")
blank_node(0.95, 4.85, 2.25, 1.0, "若手・専攻医")
blank_node(3.45, 4.85, 2.25, 1.0, "臨床研究の担い手")
blank_node(5.95, 4.85, 2.25, 1.0, "コメディカル・事務")
connector(s, 4.2, 3.3, 2.07, 3.55); connector(s, 4.2, 3.3, 4.57, 3.55); connector(s, 4.2, 3.3, 7.07, 3.55)
box(s, 8.55, 1.8, 4.1, 4.7, fill=PALEB, line=NAVY, line_w=1.0, radius=0.03)
txt(s, 8.75, 1.9, 3.6, 0.35, [P([R("院外：エリアとの繋がり", 12, True, NAVY)])])
for i, lbl in enumerate(["関連・基幹病院（元医局員は？）", "紹介元・逆紹介先", "研究会・地方会（世話人は？）", "医師会・行政・健診"]):
    blank_node(8.75, 2.35 + i * 1.05, 3.7, 0.95, lbl, line=NAVY)
card(s, 0.7, 6.58, 11.95, 0.46,
     [P([R("凡例：◎方針決定　○実行・導入　★情報ハブ　◇連携の要　", 11.5, True, INK),
         R("？＝分からない場所（＝次の面会で聞くことリスト）", 11.5, True, RED)])],
     fill=WHITE, line=LGRAY, radius=0.2)

# ================================================================ 23. 付録B 4Sテンプレ
s = add_slide()
header(s, "APPENDIX B", "４Sシート テンプレート（印刷・配布用）", kcolor=GRAY)
txt(s, 0.8, 1.7, 11.7, 0.4,
    [P([R("施設・エリア名（　　　　　　　　　　）　作成日（　　／　　）　作成者（　　　　　　）", 12.5, False, INK)])])
tq = [
    (0.8, 2.2, "① 成功像　— 1年後、こうなっていたら最高", GREEN, PALE,
     "誰が・何を・どうなっている状態か、具体的に。"),
    (6.75, 2.2, "② 現状・課題　— 成功像とのGAP", NAVY, PALEB,
     "事実・数字で。「〜できていない」は成功像とセットで。"),
    (0.8, 4.5, "③ 原因　— なぜ？×3回", RGBColor(0xB8, 0x8A, 0x00), YPALE,
     "なぜ①→なぜ②→なぜ③（真因）"),
    (6.75, 4.5, "④ 解決策　— 主語は自分。誰に・何を・いつ", RED, RPALE,
     "会社の武器（講演会・資材・連携）×自分の行動"),
]
for x, y, t, col, fill, hint in tq:
    card(s, x, y, 5.75, 0.55, [P([R(t, 13, True, WHITE)], align=PP_ALIGN.LEFT)], fill=col, radius=0.1).text_frame.margin_left = Inches(0.15)
    c = card(s, x, y + 0.6, 5.75, 1.6,
             [P([R(hint, 10.5, False, GRAY)], align=PP_ALIGN.LEFT)],
             fill=WHITE, line=col, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.08); c.text_frame.margin_left = Inches(0.15)
card(s, 0.8, 6.72, 11.7, 0.42,
     [P([R("セルフチェック：□ 課題はギャップで書けている　□ 原因はなぜ×3　□ 解決策の主語は自分", 12, True, DEEP)])],
     fill=PALE, radius=0.2)

# ================================================================ 24. 付録C ファシリテーターガイド
s = add_slide()
header(s, "APPENDIX C", "ファシリテーター用メモ（進行のコツ）", kcolor=GRAY)
tips = [
    ("事前準備・時間管理", ["事前案内（Outlook）：A4白紙2枚とペン持参、担当施設の顔ぶれを思い出してくる", "録画を回し、気づきリストとセットで欠席者へ共有（アンケートで要望多数）", "ワークは「あと2分」を予告してから切る。延長判断は共有②の前に宣言"]),
    ("場づくり", ["チェックインは自分（進行役）が30秒の見本を最初にやる", "ワーク中は沈黙OKと伝える。机間巡視で1人1声かけ", "共有で出た良い視点は、その場で口頭で「今のは◎」と拾う"]),
    ("つまずき対応", ["マップが書けない人には「まず外来と病棟の2箱から」", "4Sが止まった人には巻末のヒント欄を指差しで案内", "議論が製品の話に寄ったら「今日は構造と戦略の日」と戻す"]),
    ("次回への接続", ["最終回なので、シリーズ全体の感想を1言ずつ集めて終える", "作成した4Sシートは各自のエリア計画・上司面談で活用を宣言", "希望者には構造マップ・4Sのデータ版テンプレを共有"]),
]
for i, (t, lines) in enumerate(tips):
    x = 0.8 + (i % 2) * 6.0
    y = 1.85 + (i // 2) * 2.55
    card(s, x, y, 5.7, 0.55, [P([R(t, 14, True, WHITE)])], fill=GRAY, radius=0.12)
    c = card(s, x, y + 0.62, 5.7, 1.75,
             [P([R("・" + l, 11.5, False, INK)], space_after=6, line=1.2, align=PP_ALIGN.LEFT) for l in lines],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.TOP)
    c.text_frame.margin_top = Inches(0.1); c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.15)
txt(s, 0.8, 6.95, 11.7, 0.35,
    [P([R("本資料の事例・人名はすべて架空です。実施設の情報を扱う際は社内の情報取り扱いルールに従ってください。", 11, False, GRAY)])])

# ================================================================ 付録D 肩書き早見表
s = add_slide()
header(s, "APPENDIX D", "大学の「肩書き」早見表 — 立場の読み方と注意点", kcolor=GRAY)
colA = [
    ("教授（診療科長）", "方針・人事の最終決定者。ただし多忙で、現場の細部は下のポジションが握っていることが多い"),
    ("准教授・講師", "実務の要であり、次期教授候補。3年後のキーパーソンとして関係構築は先行投資になる"),
    ("助教・医員・専攻医", "実処方と臨床研究の担い手。「教えてください」の相手として最適で、将来は関連病院の幹部に"),
    ("医局長（役職名は大学ごと）", "人事実務・外部窓口の情報ハブ。講演依頼・面会調整はまずこの人、という大学が多い"),
]
colB = [
    ("特任教授・特任講師 など", "特定プロジェクトや資金で任用。医局ラインの人事権・決定権とは別枠のことが多い→役割を個別確認"),
    ("客員・非常勤", "本務は他施設。院内の決定権は限定的だが、施設間ネットワークのハブになっていることがある"),
    ("名誉教授", "退官後の称号で現役の決定権はない。ただし人脈・影響力は健在。研究会や講演会の重鎮"),
    ("寄附講座（教員）", "寄附により設置された講座。本流医局との距離感は大学ごとに全く違う→最初に立ち位置を確認"),
]
card(s, 0.8, 1.78, 5.75, 0.5, [P([R("院内の本流ライン", 13.5, True, WHITE)])], fill=GREEN, radius=0.12)
card(s, 6.75, 1.78, 5.75, 0.5, [P([R("読み違えやすい肩書き（要・個別確認）", 13.5, True, WHITE)])], fill=NAVY, radius=0.12)
for col_i, (rows_, col) in enumerate(((colA, GREEN), (colB, NAVY))):
    x = 0.8 + col_i * 5.95
    y = 2.38
    for t, d in rows_:
        c = card(s, x, y, 5.75, 0.98,
                 [P([R(t, 12.5, True, col)], space_after=3, align=PP_ALIGN.LEFT),
                  P([R(d, 10.5, False, INK)], line=1.18, align=PP_ALIGN.LEFT)],
                 fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
        c.text_frame.margin_left = c.text_frame.margin_right = Inches(0.14)
        y += 1.08
card(s, 0.8, 6.72, 11.7, 0.42,
     [P([R("肩書きは「地図の記号」。同じ肩書きでも大学ごとに意味が違う — 実際の力関係は構造マップで個別に確かめる。", 12.5, True, DEEP)])],
     fill=PALE, radius=0.15)

# ================================================================ 付録E コンプライアンスの5原則
s = add_slide()
header(s, "APPENDIX E", "大学活動 コンプライアンスの5原則", kcolor=GRAY)
txt(s, 0.8, 1.75, 11.7, 0.42,
    [P([R("アンケートの不安「寄附金・広告協賛・宣伝許可・施設ルール」に応えて。攻める活動ほど、守りが土台になる。", 13.5, True, INK)])])
principles = [
    ("① 施設ルールが最優先", "訪問・面会・資材配布のルールは施設ごとに違う。着任時と変更時に必ず確認し、迷ったら守りに倒す"),
    ("② 寄附金・広告協賛は「その場で約束しない」", "依頼を受けたら即答せず、必ず社内の申請・審査手続きに乗せる。誠実な「持ち帰ります」は信頼を損なわない"),
    ("③ 宣伝許可・採用ルールは現行の文書で確認", "「前任者がやっていた」は根拠にならない。院内手続きの現行ルールを自分の目で確認する"),
    ("④ 迷ったら自己判断しない", "判断基準はプロモーションコードと社内SOP。少しでも迷ったら上司・コンプライアンス部門に相談してから動く"),
    ("⑤ 記録を残す", "依頼・回答・手続きの経緯を記録に残す。誠実さの証明であり、先生と自分の両方を守る武器になる"),
]
y = 2.3
for t, d in principles:
    card(s, 0.8, y, 3.9, 0.78, [P([R(t, 12.5, True, WHITE)], align=PP_ALIGN.LEFT)], fill=DEEP, radius=0.1).text_frame.margin_left = Inches(0.15)
    c = card(s, 4.85, y, 7.65, 0.78, [P([R(d, 11.5, False, INK)], line=1.2, align=PP_ALIGN.LEFT)],
             fill=WHITE, line=LGRAY, anchor=MSO_ANCHOR.MIDDLE)
    c.text_frame.margin_left = Inches(0.15)
    y += 0.88
txt(s, 0.8, 6.75, 11.7, 0.35,
    [P([R("※ 本スライドは一般的な注意喚起です。個別の案件は、必ず最新の社内規程と担当部門の指示に従ってください。", 11.5, True, GRAY)])])

# ---------------------------------------------------------------- save
out = "/home/user/Claude/novartis_training/第4回_ちょっと分かるだけで世界が変わる.pptx"
prs.save(out)
print("saved:", out, "| slides:", len(prs.slides.__iter__.__self__._sldIdLst))
