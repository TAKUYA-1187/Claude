# -*- coding: utf-8 -*-
"""Builds the Japanese instruction manual (A4, 4 pages) as a single HTML file."""
import figures as F
import glyph as G
from canvas import svg

CSS = open("style.css", encoding="utf-8").read()
FONTS = open("fonts.css", encoding="utf-8").read() if __import__("os").path.exists("fonts.css") else ""
QR = open("qr.svg", encoding="utf-8").read()
RUN = "昇降式 折りたたみ サイドテーブル / ベッドテーブル"

PARTS = [
    ("A", "天板", "×1", F.part_A(), ""),
    ("B", "H型ベース", "×1", F.part_B(), ""),
    ("C", "伸縮ポール", "×1", F.part_C(), "黒い樹脂リングが付いた側が下（脚部側）です"),
    ("D", "天板ユニット", "×1", F.part_D(),
     "接続フレーム／スプリング折りたたみ部品／六角ネジ(M8×10)×4 は組立済みです"),
    ("E", "高さ調整レバー", "×1", F.part_E(), ""),
    ("F", "六角ボルト M8×50", "×4", F.part_bolt(64, 4), "ベース用（いちばん長い）"),
    ("G", "六角ボルト M8×40", "×4", F.part_bolt(48, 4), "天板ユニット用"),
    ("H", "六角ボルト M8×12", "×6", F.part_bolt(16, 6, 3), "天板用（いちばん短い）"),
    ("I", "ワッシャー", "×4", F.part_I(4), "Fボルトと一緒に使います"),
    ("J", "六角レンチ", "×1", F.part_J(), "必要な工具はこれ1本だけ"),
]

STEPS = [
    ("STEP 1", "高さ調整レバーを差し込む", F.step1(),
     "伸縮ポール（C）の上のほうにある四角いスロットへ、高さ調整レバー（E）を"
     "奥までまっすぐ差し込みます。ポールは床に寝かせても立てても構いません。",
     "使う部品：C・E",
     ("blue", "向きに注意", "レバーの<b>平らな（なめらかな）面が上</b>を向く向きで差し込みます。"
      "逆向きでは入りません。無理に押し込まないでください。")),
    ("STEP 2", "天板ユニットをポールに固定する", F.step2(),
     "天板ユニット（D）のワンタッチピンを引いて接続フレームを起こすと、"
     "取付穴が現れます。伸縮ポール（C）の上端に載せ、六角ボルト G（M8×40）4本で固定します。",
     "使う部品：C・D・G×4・J",
     ("blue", "締め方のコツ", "4本すべてを<b>先に仮締め</b>してから、対角線の順に本締めします。"
      "1本ずつ締め切ると穴がずれます。")),
    ("STEP 3", "天板を取り付ける", F.step3(),
     "天板（A）を裏返して床に置きます。接続フレームを倒して天板の穴に重ね、"
     "六角ボルト H（M8×12）6本で固定します。",
     "使う部品：A・H×6・J",
     ("red", "床と天板を守る", "床には毛布や段ボールを敷いてください。"
      "穴が合わない向きのまま<b>力を加えない</b>でください。")),
    ("STEP 4", "H型ベースを取り付ける", F.step4(),
     "上を向いている伸縮ポール（C）の端に、H型ベース（B）をかぶせます。"
     "ワッシャー I をはさみ、六角ボルト F（M8×50）4本で固定します。",
     "使う部品：B・F×4・I×4・J",
     ("blue", "ワッシャーを忘れずに", "ワッシャー（I）は<b>ボルトの頭の下</b>に必ず1枚ずつ入れます。"
      "ここも4本を仮締めしてから本締めしてください。")),
]

TROUBLE = [
    ("天板が下がらない／下げるのが固い",
     "ガス圧式の仕様です。新品時は内部ロックの影響で下降が固いことがあります。"
     "①レバーをしっかり握る ②支柱の真上あたりの天板に手を添える ③少しずつ体重をかけて真下へ押し下げる。"
     "3〜5回くり返すとスムーズになります。"),
    ("テーブルがガタつく",
     "ボルトの締め忘れ・締めすぎが原因です。全部のボルトを2/3ほど緩めて水平を確認し、"
     "対角線の順に締め直してください。"),
    ("まったく昇降しない",
     "天板と脚部の接合がずれている可能性があります。STEP 3・4のボルトを一度緩め、"
     "がたつきを取ってから締め直してください。"),
    ("天板が勢いよく上がる",
     "レバーを離すと止まる仕様です。上げるときは<b>必ず天板に手を添えて</b>ください。"),
    ("レバーが重い／効きが悪い",
     "強く握りすぎると破損のおそれがあります。適度な力で操作してください。"
     "改善しない場合は使用を中止し、下記までご連絡ください。"),
    ("折りたたみが固い／ピンが戻らない",
     "天板を軽く支えて力を逃がしながら、ピンをゆっくり操作してください。"
     "無理な力を加えないでください。"),
]

FAQ = [
    ("伸縮ポールが1本しか入っていません。形も写真と違います。",
     "伸縮ポールは1本です。細いポールは新品時ポールの内部に収納されており、"
     "手で引き出すことはできません。組立後、レバー操作ではじめて出てきます。"),
    ("伸縮ポールはどちらが下ですか？",
     "<b>黒い樹脂リングが付いている側が下（ベース側）</b>、金属だけの側が上（天板側）です。"),
    ("部品が足りません／傷がありました。",
     "部品の記号（A〜J）と数量をお知らせください。確認のうえ、再送・交換いたします。"),
]


def head(title, lead=""):
    l = f'<span class="lead">{lead}</span>' if lead else ""
    return f'<div class="sec"><h2>{title}</h2>{l}</div>'


def page(n, body):
    return (f'<section class="page" data-pg="{n} / 4" data-run="{RUN}">{body}</section>')


# ------------------------------------------------------------------ page 1
def page1():
    cells = ""
    for ltr, nm, qty, fig, note in PARTS:
        note_html = f'<div class="note">{note}</div>' if note else ""
        cells += (f'<div class="pcell"><div class="hd"><span class="ltr">{ltr}</span>'
                  f'<span class="qty">{qty}</span></div>'
                  f'<div class="nm"><span class="chk"></span>{nm}</div>'
                  f'{fig}{note_html}</div>')

    guide = f'<div class="bg-item">{F.bolt_compare()}</div>'

    flow = ""
    for i, (t, s) in enumerate([("レバー", "を差し込む"), ("天板ユニット", "を固定"),
                                ("天板", "を固定"), ("ベース", "を固定"),
                                ("起こして", "完成")], 1):
        flow += (f'<div class="f"><i>STEP {i}</i><b>{t}</b><em>{s}</em></div>')

    return page(1, f"""
<div class="cover-top">
  <div>
    <div class="brandline">FOR HOME &amp; BEDSIDE</div>
    <h1 class="ptitle">昇降式 折りたたみ<br>サイドテーブル / ベッドテーブル
      <small>無段階ガス圧昇降 ＋ ワンタッチ折りたたみ</small></h1>
    <div class="doclabel">取扱説明書 兼 組立説明書</div>
  </div>
  <div class="qrbox">{QR}<b>組立動画</b><span>スマホで読み取ると<br>動画を確認できます</span></div>
</div>

<div class="herowrap">
  <div class="h1fig">{F.hero(150)}</div>
  <div class="h2fig">{F.hero_folded(150)}</div>
</div>
<div class="hcap">通常の状態（高さは無段階で調整できます）　　　　折りたたんだ状態（すき間に収納）</div>

<div class="facts">
  <div class="fact"><b>組立時間のめやす</b><span>約10〜15分</span><em>はじめての方でも1人で組めます</em></div>
  <div class="fact"><b>用意するもの</b><span>付属の六角レンチ（J）だけ</span><em>床に敷く毛布・段ボールがあると安心</em></div>
  <div class="fact"><b>組立のポイント</b><span>裏返したまま組む</span><em>最後のSTEP 5で起こします</em></div>
</div>

<div class="flow">{flow}</div>

<div style="margin-top:4mm">{head("同梱部品の確認", "＊組み立てる前に、部品がすべて揃っているかご確認ください")}</div>
<div class="parts">{cells}</div>

<div class="boltguide">
  <div class="bg-t">ボルトの見分け方<em>長さで区別します。取り違えは破損の原因になります。</em></div>
  {guide}
  <div style="font-size:8.2pt;line-height:1.6;color:var(--ink2)">
    ボルトは<b>長い順に F → G → H</b>。<br>Fだけワッシャー（I）と組で使います。</div>
</div>

<div class="chknote">□にチェックを入れながらご確認ください。
  部品の不足・破損があった場合は、<b>組み立てずに</b>4ページの窓口までご連絡ください。
  すぐに手配いたします。</div>
</div>""")


# ------------------------------------------------------------------ page 2
def page2():
    cards = ""
    for i, (sn, title, fig, body, use, (kind, ctitle, ctext)) in enumerate(STEPS, 1):
        cls = "callout red" if kind == "red" else "callout"
        cards += (f'<div class="step"><div class="sh"><span class="num">{i}</span>'
                  f'<span><span class="sn">{sn}</span><br><span class="st">{title}</span></span></div>'
                  f'<div class="sbody">{fig}<p>{body}</p>'
                  f'<span class="use">{use}</span>'
                  f'<div class="{cls}"><b>{ctitle}</b>：{ctext}</div></div></div>')
    return page(2, f"""
{head("組み立て方", "＊STEP 1 → 4 の順に進めてください")}
<div class="prep">
  <div class="ph"><span class="warnmark">!</span>組み立てる前に</div>
  <div class="pg">
    <div class="pi"><i>1</i><span>部品がすべて揃っているか確認する<em>（1ページの□にチェック）</em></span></div>
    <div class="pi"><i>2</i><span>床に毛布や段ボールを敷く<em>（天板と床のキズ防止）</em></span></div>
    <div class="pi"><i>3</i><span>ボルトは全部を仮締め →最後に本締め<em>（1本ずつ締め切らない）</em></span></div>
    <div class="pi"><i>4</i><span>電動ドライバーは使わない<em>（ネジ穴の破損・空回りの原因）</em></span></div>
  </div>
</div>
<div class="banner"><b>ここが大事</b><span>STEP 2〜4 は本体を
  <u>逆さま（天板が下・ベースが上）</u>にしたまま作業します。最後の STEP 5 で起こせば完成です。</span></div>
<div style="height:3.4mm"></div>
<div class="steps">{cards}</div>""")


# ------------------------------------------------------------------ page 3
def page3():
    checks = [
        "ボルト14本（F×4・G×4・H×6）がすべて最後まで締まっている",
        "水平な床でガタつきがない",
        "レバーを握ると天板がなめらかに動く",
    ]
    ck = "".join(f'<div class="ci"><b>✓</b><span>{c}</span></div>' for c in checks)
    return page(3, f"""
{head("仕上げと使い方")}
<div class="duo">
  <div class="opcard">
    <div class="oh"><span class="num" style="background:var(--brand);color:#fff;width:5.6mm;
      height:5.6mm;border-radius:50%;display:grid;place-items:center;font-size:8pt;
      font-weight:900">5</span>STEP 5　本体を起こして完成</div>
    <div class="ob">
      <div class="fig">{F.step5()}</div>
      <p>天板を支えながら、ゆっくり起こして立てます。最後にすべてのボルトをもう一度
      しっかり本締めし、下の3点を確認してください。</p>
    </div>
  </div>
  <div class="opcard">
    <div class="oh"><span class="dot">✓</span>完成後のチェック</div>
    <div class="ob">
      <div class="check" style="flex-direction:column;gap:2mm;margin-top:0">{ck}</div>
      <div class="callout" style="margin-top:auto"><b>ガタつくときは</b>：一度ボルトを2/3ほど緩め、
      水平を確認してから対角線の順に締め直してください。</div>
    </div>
  </div>
</div>

<div style="height:4mm"></div>
{head("高さを変える", "＊レバーを握っている間だけ動きます。離すとその高さで止まります")}
<div class="duo">
  <div class="opcard">
    <div class="oh"><span class="dot">▼</span>下げるとき</div>
    <div class="ob"><div class="fig">{F.op_down()}</div>
      <p>レバーを握ったまま、<b>支柱の真上あたりの天板</b>に手を添え、
      体重をかけるようにまっすぐ押し下げます。好みの高さでレバーを離します。</p></div>
  </div>
  <div class="opcard">
    <div class="oh"><span class="dot">▲</span>上げるとき</div>
    <div class="ob"><div class="fig">{F.op_up()}</div>
      <p>レバーを握ると天板がひとりでに上がります。勢いよく上がることがあるので、
      <b>必ず天板に手を添えて</b>支えてください。好みの高さでレバーを離します。</p></div>
  </div>
</div>
<div class="callout red"><b>新品のうちは下げるのが固いことがあります</b>：ガス圧式の仕様です。
上の手順を3〜5回くり返すとなめらかになります。故障ではありません。</div>

<div style="height:4mm"></div>
{head("折りたたむ", "＊使わないときは天板を立てて、すき間に収納できます")}
<div class="trio">
  <div class="opcard sm"><div class="oh"><span class="dot">1</span>ピンを引く</div>
    <div class="ob"><div class="fig">{F.fold_pin()}</div>
      <p>片手で天板を支えながら、天板の下にあるワンタッチピンを手前に引きます。</p></div></div>
  <div class="opcard sm"><div class="oh"><span class="dot">2</span>天板を起こす</div>
    <div class="ob"><div class="fig">{F.fold_lift()}</div>
      <p>ピンを引いたまま、天板を垂直になるまでゆっくり起こします。</p></div></div>
  <div class="opcard sm"><div class="oh"><span class="dot">3</span>固定を確認</div>
    <div class="ob"><div class="fig">{F.fold_done()}</div>
      <p>ピンから手を離し、天板が動かないことを確認します。戻すときは同じ手順で水平に。</p></div></div>
</div>
<div class="callout red"><b>指はさみ注意</b>：折りたたみ・展開のときは、天板の下や
ちょうつがい部分に手や指を入れないでください。お子様のそばで操作しないでください。</div>""")


# ------------------------------------------------------------------ page 4
def page4():
    rows = "".join(f'<tr><td class="sym">{a}</td><td>{b}</td></tr>' for a, b in TROUBLE)
    qa = "".join(f'<dt><span class="q">Q</span><span>{q}</span></dt>'
                 f'<dd><span class="a">A</span>　{a}</dd>' for q, a in FAQ)
    return page(4, f"""
{head("安全にお使いいただくために")}
<div class="safety">
  <div class="sbox w"><div class="sth">⚠ 警告<span style="font-size:7.6pt;font-weight:500">
    けが・事故につながります</span></div>
    <ul>
      <li>天板の上に乗ったり、座ったり、寄りかからないでください。</li>
      <li>昇降部・ちょうつがい部に手や指を入れないでください。</li>
      <li>お子様だけで昇降・折りたたみ操作をさせないでください。</li>
      <li>分解・改造はしないでください。ガススプリングは内部に高圧ガスが入っています。</li>
    </ul>
  </div>
  <div class="sbox c"><div class="sth">⚠ 注意<span style="font-size:7.6pt;font-weight:500">
    破損・変形の原因になります</span></div>
    <ul>
      <li>水平で安定した場所でお使いください。</li>
      <li>天板の端にだけ重い物を置かないでください。バランスをくずします。</li>
      <li>熱い鍋・やかんなどを直接置かないでください。</li>
      <li>水などをこぼしたときは、すぐに拭き取ってください。</li>
    </ul>
  </div>
</div>
<div class="callout"><b>お手入れ</b>：乾いたやわらかい布で拭いてください。汚れがひどいときは、
うすめた中性洗剤を含ませて固くしぼった布で拭き、そのあと乾拭きします。
シンナー・ベンジン・研磨剤入り洗剤は使わないでください。</div>

<div style="height:4mm"></div>
{head("困ったときは")}
<table class="tb"><tr><th style="width:42mm">症状</th><th>確認すること・対処</th></tr>{rows}</table>

<div style="height:4mm"></div>
{head("よくあるご質問")}
<div class="qa"><dl>{qa}</dl></div>

<div class="support">
  <div class="sph">お問い合わせ・サポート</div>
  <div class="spb">
    <div class="col"><b>まずはAmazonの購入履歴から</b>
      製品に関するご不明点、部品の不足・破損、不具合がございましたら、
      Amazonの購入履歴よりお問い合わせください。</div>
    <div class="col"><b>Amazonからのご連絡が難しい場合</b>
      <div class="big">lifester.1178@gmail.com</div>
      <div class="big">076-491-0865</div></div>
    <div class="col"><b>対応について</b>
      内容を確認のうえ、部品の再送や交換等の対応をさせていただきます。
      通常、1〜2営業日以内にご返信いたします。</div>
  </div>
</div>
<div class="foot">＊本書の内容および製品の仕様は、改良のため予告なく変更する場合があります。
　＊本書は大切に保管してください。</div>""")


def main():
    html = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>昇降式折りたたみベッドテーブル 取扱説明書</title>
<style>{FONTS}</style>
<style>{CSS}</style></head><body>
{page1()}
{page2()}
{page3()}
{page4()}
</body></html>"""
    open("bed-table-manual.html", "w", encoding="utf-8").write(html)
    print("wrote bed-table-manual.html", len(html), "bytes")


if __name__ == "__main__":
    main()
