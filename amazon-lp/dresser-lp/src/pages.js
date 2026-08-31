const { P, dresserSVG } = require('./parts.js');
const { slot, PHOTO_CSS } = require('./photo.js');

// =============================== 共通CSS ===============================
const CSS = `
${PHOTO_CSS}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:2000px;height:2000px;background:#fff}
.stage{width:2000px;height:2000px;position:relative;overflow:hidden;
  font-family:'Noto Sans JP',sans-serif;color:${P.ink};
  -webkit-font-smoothing:antialiased}
.dresser{display:block;width:100%;height:100%}

/* --- テキスト系 --- */
.eyebrow{font-size:40px;font-weight:700;letter-spacing:.18em;color:${P.gold}}
.h1{font-size:132px;font-weight:900;line-height:1.13;letter-spacing:-.015em}
.h2{font-size:96px;font-weight:900;line-height:1.18;letter-spacing:-.01em}
.lead{font-size:40px;font-weight:500;line-height:1.62;color:${P.inkSoft}}
.hl{color:${P.gold}}
.mark{background:linear-gradient(transparent 62%, ${P.goldPale} 62%)}

/* --- 帯・囲み --- */
.rule{height:5px;width:120px;background:${P.gold};border-radius:3px}
.chip{display:inline-flex;align-items:center;gap:16px;background:${P.ink};color:#fff;
  border-radius:999px;padding:18px 44px;font-size:38px;font-weight:700;letter-spacing:.04em}
.chip.g{background:${P.gold}}
.chip.o{background:#fff;color:${P.ink};border:4px solid ${P.line}}
.card{background:#fff;border:4px solid ${P.line};border-radius:36px}
.num{font-family:'Noto Serif JP',serif;font-weight:900;color:${P.goldLt};line-height:.82}

/* --- 下部スペックバー --- */
.specbar{position:absolute;left:0;right:0;bottom:0;height:132px;background:${P.ink};
  display:flex;align-items:center;justify-content:center;gap:70px;color:#fff}
.specbar b{font-size:44px;font-weight:900;letter-spacing:.02em}
.specbar span{font-size:34px;font-weight:500;opacity:.72}
.specbar i{width:3px;height:52px;background:rgba(255,255,255,.26);display:block}
.note{font-size:26px;color:${P.inkFaint};line-height:1.6}
`;

const page = (title, bodyCSS, body) => `<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><title>${title}</title><style>${CSS}${bodyCSS}</style></head>
<body><div class="stage">${body}</div></body></html>`;

// ============================================================
// 01  メイン画像 ─ 純白背景・商品単体・テキストなし（Amazon規約準拠）
// ============================================================
const p01 = () => page('01 メイン画像', `
.stage{background:#fff;display:flex;align-items:center;justify-content:center}
.wrap{width:1340px;height:1983px}
`, `<div class="wrap">${slot('main',
    dresserSVG({ id:'m1', mirror:'closed', stool:true, glow:'neutral', items:true }),
    { fit:'contain' })}</div>`);

// ============================================================
// 02  3大特徴ヒーロー
// ============================================================
const p02 = () => {
  const feat = (n, t, s) => `
   <div class="f">
     <div class="num">${n}</div>
     <div class="ft"><b>${t}</b><p>${s}</p></div>
   </div>`;
  return page('02 3大特徴', `
.stage{background:
  radial-gradient(1200px 900px at 76% 12%, #FFFFFF 0%, rgba(255,255,255,0) 62%),
  linear-gradient(160deg, ${P.cream} 0%, ${P.cream2} 100%)}
.head{position:absolute;left:108px;top:100px;width:1046px}
.head .h1{font-size:116px}
.head .lead{font-size:36px}
.head .eyebrow{margin-bottom:26px}
.head .h1{margin-bottom:34px}
.head .lead{width:1046px}
.pic{position:absolute;left:52px;bottom:132px;width:784px;height:1160px}
.feats{position:absolute;right:96px;top:520px;width:800px;
  display:flex;flex-direction:column;gap:34px}
.f{background:#fff;border-radius:34px;padding:44px 48px;display:flex;align-items:center;gap:38px;
   box-shadow:0 18px 44px rgba(120,100,74,.11);border:3px solid rgba(228,218,206,.9)}
.f .num{font-size:104px;min-width:150px;text-align:center}
.ft b{display:block;font-size:52px;font-weight:900;line-height:1.24;margin-bottom:12px}
.ft p{font-size:31px;font-weight:500;color:${P.inkSoft};line-height:1.52}
.blob{position:absolute;right:-180px;top:-200px;width:900px;height:900px;border-radius:50%;
  background:${P.goldPale};opacity:.5}
`, `
<div class="blob"></div>
<div class="head">
  <div class="eyebrow">WIDTH 80cm  DRESSER</div>
  <div class="h1">朝の支度が、<br>ここで<span class="hl">完結</span>する。</div>
  <div class="lead">鏡・照明・収納をひとつに。<span class="mark">幅80cmのコンパクト設計</span>だから、<br>ワンルームでも“自分だけの場所”がつくれます。</div>
</div>
<div class="pic">${slot('hero',
    dresserSVG({ id:'m2', mirror:'closed', glow:'warm', items:true }), { fit:'contain' })}</div>
<div class="feats">
  ${feat('01','3色調光LEDミラー','電球色・昼白色・昼光色を切替。<br>朝も夜も、顔色が正しく見える。')}
  ${feat('02','スライドミラー','鏡を横にスライドすれば<br>収納が全開。デスクにも早変わり。')}
  ${feat('03','4か所の収納','引き出し4杯・オープン棚・鏡裏収納。<br>デスク引き出しは鍵付き。')}
</div>
<div class="specbar">
  <b>幅80 × 奥行35 × 高さ130cm</b><i></i><span>スツール付き</span><i></i>
  <span>鍵付き引き出し</span><i></i><span>組立式</span>
</div>`);
};

// ============================================================
// 03  3色調光LED
// ============================================================
const p03 = () => {
  const mirror = (id, col, glowOp) => `
  <svg viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg" class="mv">
    <defs>
      <linearGradient id="mg${id}" x1=".1" y1="0" x2=".9" y2="1">
        <stop offset="0" stop-color="#F2F7FA"/><stop offset=".5" stop-color="#FBFDFE"/>
        <stop offset="1" stop-color="#DCE7EE"/>
      </linearGradient>
      <filter id="fg${id}" x="-70%" y="-70%" width="240%" height="240%">
        <feGaussianBlur stdDeviation="7"/>
      </filter>
    </defs>
    <rect x="14" y="10" width="72" height="96" rx="5" fill="${col}" opacity="${glowOp}" filter="url(#fg${id})"/>
    <rect x="16" y="12" width="68" height="92" rx="4" fill="${col}" opacity=".85"/>
    <rect x="21" y="17" width="58" height="82" rx="2" fill="url(#mg${id})"/>
    <rect x="16" y="12" width="68" height="92" rx="4" fill="none" stroke="#CFC6B8" stroke-width="0.7"/>
    <path d="M26 97 L46 19 L54 19 L34 97 Z" fill="#fff" opacity=".42"/>
    <path d="M58 97 L69 19 L73 19 L62 97 Z" fill="#fff" opacity=".24"/>
    <circle cx="50" cy="110" r="3.4" fill="#fff" stroke="${P.line}" stroke-width="1"/>
    <circle cx="50" cy="110" r="1.2" fill="${P.goldLt}"/>
  </svg>`;
  const card = (id, col, op, k, t, s, ph) => `
   <div class="c">
     <div class="mw">${slot(ph, mirror(id, col, op), { fit:'cover', radius:22 })}</div>
     <div class="k">${k}</div>
     <b>${t}</b>
     <p>${s}</p>
   </div>`;
  return page('03 3色調光LED', `
.stage{background:linear-gradient(175deg,#FFFFFF 0%, ${P.cream} 58%, ${P.cream2} 100%)}
.top{position:absolute;left:0;right:0;top:110px;text-align:center}
.top .eyebrow{margin-bottom:24px}
.top .h2{margin-bottom:30px}
.top .lead{font-size:38px}
.cards{position:absolute;left:96px;right:96px;top:600px;display:flex;gap:44px}
.c{flex:1;background:#fff;border-radius:40px;padding:56px 40px 48px;text-align:center;
   border:3px solid rgba(228,218,206,.9);box-shadow:0 18px 44px rgba(120,100,74,.10)}
.mw{width:100%;height:466px;margin-bottom:30px}
.mv{width:100%;height:100%}
.k{display:inline-block;background:${P.goldPale};color:${P.gold};font-size:29px;font-weight:900;
   letter-spacing:.1em;border-radius:999px;padding:12px 30px;margin-bottom:24px}
.c b{display:block;font-size:56px;font-weight:900;margin-bottom:20px;letter-spacing:-.01em}
.c p{font-size:31px;font-weight:500;color:${P.inkSoft};line-height:1.62}
.dim{position:absolute;left:96px;right:96px;bottom:210px;background:${P.ink};color:#fff;
  border-radius:34px;padding:46px 60px;display:flex;align-items:center;gap:46px}
.dim .bt{font-size:46px;font-weight:900;white-space:nowrap}
.dim .bar{flex:1;height:26px;border-radius:13px;
  background:linear-gradient(90deg,#4A423A 0%, #8C7350 34%, #D8B47E 68%, #FFF0D2 100%);position:relative}
.dim .bar::after{content:'';position:absolute;right:-2px;top:-9px;width:44px;height:44px;border-radius:50%;
  background:#fff;box-shadow:0 0 0 6px rgba(255,255,255,.28)}
.dim .bs{font-size:32px;font-weight:500;opacity:.78;white-space:nowrap}
`, `
<div class="top">
  <div class="eyebrow">3 COLOR  ×  DIMMABLE  LED</div>
  <div class="h2">顔色まで、ちゃんと見える。</div>
  <div class="lead">シーンに合わせて選べる<span class="hl">3色の光</span>。タッチひとつで切り替わります。</div>
</div>
<div class="cards">
  ${card('a','#FFC069','.55','電球色 3000K','くつろぐ夜に','やわらかな暖色。<br>就寝前のスキンケアに。','led_warm')}
  ${card('b','#FFE7BC','.75','昼白色 4500K','ふだんのメイクに','自然光に近い明るさ。<br>色ムラのない仕上がりに。','led_neutral')}
  ${card('c','#CFE4FF','.60','昼光色 6000K','細部チェックに','クリアな白色光。<br>アイメイクや眉の確認に。','led_cool')}
</div>
<div class="dim">
  <div class="bt">明るさ 無段階調光</div>
  <div class="bar"></div>
  <div class="bs">長押しでお好みの明るさに</div>
</div>
<div class="specbar">
  <b>3色調光 LED</b><i></i><span>タッチスイッチ</span><i></i>
  <span>グラデーション調光</span><i></i><span>ミラー 45×60cm</span>
</div>`);
};

// ============================================================
// 04  スライドミラー 2WAY
// ============================================================
const p04 = () => {
  const panel = (tag, title, sub, svg, accent, ph) => `
  <div class="pn">
    <div class="tag" style="background:${accent}">${tag}</div>
    <div class="pv">${slot(ph, svg, { fit:'contain' })}</div>
    <b>${title}</b>
    <p>${sub}</p>
  </div>`;
  return page('04 スライドミラー', `
.stage{background:linear-gradient(160deg,${P.cream} 0%, #FFFFFF 46%, ${P.cream2} 100%)}
.top{position:absolute;left:0;right:0;top:96px;text-align:center}
.top .eyebrow{margin-bottom:22px}
.top .h2{margin-bottom:26px}
.top .lead{font-size:38px}
.pair{position:absolute;left:80px;right:80px;top:624px;display:flex;align-items:stretch;gap:34px}
.pn{flex:1;background:#fff;border-radius:40px;padding:40px 36px 44px;text-align:center;position:relative;
    border:3px solid rgba(228,218,206,.9);box-shadow:0 18px 44px rgba(120,100,74,.10)}
.tag{position:absolute;left:50%;top:-30px;transform:translateX(-50%);color:#fff;font-size:30px;
  font-weight:900;letter-spacing:.08em;border-radius:999px;padding:14px 40px;white-space:nowrap}
.pv{height:648px;margin:30px 0 24px}
.pn b{display:block;font-size:50px;font-weight:900;margin-bottom:16px}
.pn p{font-size:30px;font-weight:500;color:${P.inkSoft};line-height:1.58}
.arrow{width:150px;display:flex;align-items:center;justify-content:center;flex:none}
.arrow svg{width:130px;height:130px}
.foot{position:absolute;left:80px;right:80px;bottom:212px;display:flex;gap:26px}
.fx{flex:1;background:${P.goldPale};border-radius:26px;padding:32px 34px;text-align:center}
.fx b{display:block;font-size:36px;font-weight:900;color:${P.ink};margin-bottom:8px}
.fx span{font-size:27px;font-weight:500;color:${P.inkSoft}}
`, `
<div class="top">
  <div class="eyebrow">SLIDE MIRROR  /  2WAY</div>
  <div class="h2">鏡を、スライド。<br>ドレッサーが、デスクになる。</div>
  <div class="lead">鏡は左右に動かせるから、<span class="mark">使いたい方だけ開く</span>。<br>限られたスペースも、ムダなく使えます。</div>
</div>
<div class="pair">
  ${panel('ドレッサーとして','鏡を中央へ','正面に鏡がくる位置に。<br>座ったままメイクが完結します。',
    dresserSVG({ id:'m4a', mirror:'closed', glow:'warm', stool:true, items:true }), P.gold, 'mirror_closed')}
  <div class="arrow">
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="46" fill="#fff" stroke="${P.line}" stroke-width="3"/>
      <path d="M30 42 H70 M30 58 H70" stroke="${P.gold}" stroke-width="6" stroke-linecap="round"/>
      <path d="M38 32 L26 42 L38 52" fill="none" stroke="${P.gold}" stroke-width="6"
            stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M62 48 L74 58 L62 68" fill="none" stroke="${P.gold}" stroke-width="6"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>
  ${panel('収納を開くとき','鏡を右へスライド','鏡裏の収納が全開に。<br>コスメの出し入れがスムーズ。',
    dresserSVG({ id:'m4b', mirror:'open', glow:null, stool:true, items:true }), P.ink, 'mirror_open')}
</div>
<div class="foot">
  <div class="fx"><b>指1本で軽く動く</b><span>スムーズなスライドレール</span></div>
  <div class="fx"><b>天板 幅50cm</b><span>ノートPCもゆったり</span></div>
  <div class="fx"><b>鏡を隠せる</b><span>来客時もすっきり</span></div>
</div>
<div class="specbar">
  <b>1台2役</b><i></i><span>ドレッサー ↔ ワークデスク</span><i></i><span>天板高 70cm</span>
</div>`);
};

module.exports = { CSS, page, p01, p02, p03, p04 };
