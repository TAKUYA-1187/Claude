const { P, dresserSVG } = require('./parts.js');
const { page } = require('./pages.js');
const { slot, has } = require('./photo.js');

// ============================================================
// 05  大容量収納（引き出し線つきコールアウト）
// ============================================================
const p05illust = () => {
  // ドレッサー配置：viewBox 100x148 を 7.6px/単位 で描画
  const L = 620, T = 500, S = 7.6;
  const mx = c => L + c * S, my = c => T + c * S;

  const anchors = [
    { a:[24, 30],  from:[576, 748]  },   // オープンラック（左上）
    { a:[80, 72],  from:[1424, 1068] },  // 鍵付き引き出し（右）
    { a:[26, 100], from:[576, 1278] },   // 引き出し3杯（左下）
    { a:[70, 120], from:[1424, 1438] },  // スツール収納（右下）
  ];
  const lines = anchors.map(({a, from}) => {
    const [ax, ay] = [mx(a[0]), my(a[1])];
    const midX = (from[0] + ax) / 2;
    return `<path d="M ${from[0]} ${from[1]} L ${midX} ${from[1]} L ${midX} ${ay} L ${ax} ${ay}"
              fill="none" stroke="${P.gold}" stroke-width="3.5" stroke-linecap="round"
              stroke-linejoin="round" opacity=".85"/>
            <circle cx="${ax}" cy="${ay}" r="13" fill="#fff" stroke="${P.gold}" stroke-width="5"/>
            <circle cx="${from[0]}" cy="${from[1]}" r="7" fill="${P.gold}"/>`;
  }).join('');

  const card = (n, t, s, style) => `
    <div class="co" style="${style}">
      <div class="con">${n}</div>
      <div><b>${t}</b><p>${s}</p></div>
    </div>`;

  return page('05 大容量収納', `
.stage{background:linear-gradient(168deg,#FFFFFF 0%, ${P.cream} 55%, ${P.cream2} 100%)}
.top{position:absolute;left:0;right:0;top:96px;text-align:center}
.top .eyebrow{margin-bottom:22px}
.top .h2{margin-bottom:24px}
.top .lead{font-size:37px}
.pic{position:absolute;left:${L}px;top:${T}px;width:760px;height:1124.8px}
.ov{position:absolute;left:0;top:0;width:2000px;height:2000px;pointer-events:none}
.co{position:absolute;width:520px;background:#fff;border-radius:30px;padding:34px 36px;
    display:flex;gap:26px;align-items:flex-start;
    border:3px solid rgba(228,218,206,.9);box-shadow:0 16px 38px rgba(120,100,74,.12)}
.con{flex:none;width:66px;height:66px;border-radius:50%;background:${P.gold};color:#fff;
     font-size:34px;font-weight:900;display:flex;align-items:center;justify-content:center}
.co b{display:block;font-size:38px;font-weight:900;line-height:1.3;margin-bottom:12px}
.co p{font-size:28px;font-weight:500;color:${P.inkSoft};line-height:1.56}
.nt{position:absolute;left:0;right:0;bottom:196px;text-align:center}
`, `
<div class="top">
  <div class="eyebrow">PLENTY  OF  STORAGE</div>
  <div class="h2">コスメも、ドライヤーも。<br>“出しっぱなし”がなくなる。</div>
  <div class="lead">計<span class="hl">4杯の引き出し</span>と<span class="hl">3段のオープンラック</span>。使う順に、しまえます。</div>
</div>
<div class="pic">${dresserSVG({ id:'m5', mirror:'right', glow:null, stool:true, items:true, xray:true })}</div>
<svg class="ov" viewBox="0 0 2000 2000" xmlns="http://www.w3.org/2000/svg">${lines}</svg>
${card('1','オープンラック3段','高さのある香水・化粧水も<br>立てたまま収納できます。','left:56px;top:640px')}
${card('3','引き出し3杯','コスメ・アクセサリー・<br>ヘアケアを種類ごとに。','left:56px;top:1170px')}
${card('2','鍵付き引き出し','幅いっぱいのワイド設計。<br>ロックできて安心です。','left:1424px;top:960px')}
${card('4','スツールも収納','使わないときは足元へ。<br>床が広く使えます。','left:1424px;top:1330px')}
<div class="nt"><p class="note">※引き出し内・ラック上の小物は収納イメージです。商品には含まれません。</p></div>
<div class="specbar">
  <b>引き出し 計4杯</b><i></i><span>オープンラック 3段</span><i></i>
  <span>鍵付き</span><i></i><span>天板耐荷重 約15kg</span>
</div>`);
};

// ---- 05 写真版（storage_1〜4 がそろったら自動でこちらを使用）----
const p05photo = () => {
  const cell = (n, ph, t, sub) => `
    <div class="g">
      <div class="gp">${slot(ph, '', { fit:'cover' })}<div class="gn">${n}</div></div>
      <div class="gc"><b>${t}</b><p>${sub}</p></div>
    </div>`;
  return page('05 大容量収納', `
.stage{background:linear-gradient(168deg,#FFFFFF 0%, ${P.cream} 55%, ${P.cream2} 100%)}
.top{position:absolute;left:0;right:0;top:96px;text-align:center}
.top .eyebrow{margin-bottom:22px}
.top .h2{margin-bottom:24px}
.top .lead{font-size:37px}
.grid{position:absolute;left:96px;right:96px;top:572px;
  display:grid;grid-template-columns:1fr 1fr;gap:30px}
.g{background:#fff;border-radius:32px;overflow:hidden;
   border:3px solid rgba(228,218,206,.9);box-shadow:0 16px 38px rgba(120,100,74,.10)}
.gp{position:relative;height:372px;background:${P.cream2}}
.gp .phbox{width:100%;height:100%}
.gn{position:absolute;left:22px;top:22px;width:62px;height:62px;border-radius:50%;
    background:${P.gold};color:#fff;font-size:32px;font-weight:900;
    display:flex;align-items:center;justify-content:center}
.gc{padding:24px 34px 28px}
.gc b{display:block;font-size:42px;font-weight:900;margin-bottom:10px}
.gc p{font-size:28px;font-weight:500;color:${P.inkSoft};line-height:1.5}
.nt{position:absolute;left:0;right:0;bottom:196px;text-align:center}
`, `
<div class="top">
  <div class="eyebrow">PLENTY  OF  STORAGE</div>
  <div class="h2">コスメも、ドライヤーも。<br>“出しっぱなし”がなくなる。</div>
  <div class="lead">計<span class="hl">4杯の引き出し</span>と<span class="hl">3段のオープンラック</span>。使う順に、しまえます。</div>
</div>
<div class="grid">
  ${cell('1','storage_1','オープンラック3段','高さのある香水・化粧水も立てたまま。')}
  ${cell('2','storage_2','鍵付き引き出し','幅いっぱいのワイド設計。ロックできて安心。')}
  ${cell('3','storage_3','引き出し3杯','コスメ・アクセサリー・ヘアケアを種類ごとに。')}
  ${cell('4','storage_4','スツールも収納','使わないときは足元へ。床が広く使えます。')}
</div>
<div class="nt"><p class="note">※小物は収納イメージです。商品には含まれません。</p></div>
<div class="specbar">
  <b>引き出し 計4杯</b><i></i><span>オープンラック 3段</span><i></i>
  <span>鍵付き</span><i></i><span>天板耐荷重 約15kg</span>
</div>`);
};

// 写真がそろっていれば写真版、なければイラスト版
const STORAGE_PHOTOS = ['storage_1','storage_2','storage_3','storage_4'];
const p05 = () => (STORAGE_PHOTOS.every(has) ? p05photo() : p05illust());

// ============================================================
// 06  寸法図
// ============================================================
const p06 = () => {
  const L = 380, T = 360, S = 7.6;
  const mx = c => L + c * S, my = c => T + c * S;
  const GD = P.gold, TX = P.ink;

  // 寸法線ヘルパー（stage px 座標）
  const hDim = (x1, x2, y, label, off = 0) => `
    <path d="M${x1} ${y - 12} V${y + 12} M${x2} ${y - 12} V${y + 12}" stroke="${GD}" stroke-width="3"/>
    <path d="M${x1} ${y} H${x2}" stroke="${GD}" stroke-width="3"/>
    <path d="M${x1 + 20} ${y - 9} L${x1} ${y} L${x1 + 20} ${y + 9}" fill="${GD}"/>
    <path d="M${x2 - 20} ${y - 9} L${x2} ${y} L${x2 - 20} ${y + 9}" fill="${GD}"/>
    <rect x="${(x1 + x2) / 2 - 118 + off}" y="${y - 34}" width="236" height="68" rx="12" fill="#fff"/>
    <text x="${(x1 + x2) / 2 + off}" y="${y + 15}" text-anchor="middle"
          font-family="Noto Sans JP" font-size="42" font-weight="900" fill="${TX}">${label}</text>`;
  const vDim = (y1, y2, x, label) => `
    <path d="M${x - 12} ${y1} H${x + 12} M${x - 12} ${y2} H${x + 12}" stroke="${GD}" stroke-width="3"/>
    <path d="M${x} ${y1} V${y2}" stroke="${GD}" stroke-width="3"/>
    <path d="M${x - 9} ${y1 + 20} L${x} ${y1} L${x + 9} ${y1 + 20}" fill="${GD}"/>
    <path d="M${x - 9} ${y2 - 20} L${x} ${y2} L${x + 9} ${y2 - 20}" fill="${GD}"/>
    <g transform="translate(${x} ${(y1 + y2) / 2}) rotate(-90)">
      <rect x="-118" y="-34" width="236" height="68" rx="12" fill="#fff"/>
      <text x="0" y="15" text-anchor="middle"
            font-family="Noto Sans JP" font-size="42" font-weight="900" fill="${TX}">${label}</text>
    </g>`;
  const ext = (x1, y1, x2, y2) => `<path d="M${x1} ${y1} L${x2} ${y2}" stroke="${P.line}"
     stroke-width="2.5" stroke-dasharray="9 9"/>`;

  const SX = 1330, SW = 35 * S; // 側面図 x開始 / 奥行35cm

  const dims = `
    ${ext(mx(10), my(135), mx(10), 1478)} ${ext(mx(90), my(135), mx(90), 1478)}
    ${hDim(mx(10), mx(90), 1450, '幅 80cm')}
    ${ext(mx(10), my(5), 300, my(5))} ${ext(mx(10), my(135), 300, my(135))}
    ${vDim(my(5), my(135), 330, '高さ 130cm')}
    ${ext(mx(10), my(60), 300, my(60))}
    ${vDim(my(60), my(135), 1140, '天板高 75cm')}
    ${ext(mx(90), my(60), 1160, my(60))} ${ext(mx(90), my(135), 1160, my(135))}
    ${vDim(my(7), my(57), 1230, 'ミラー 50cm')}
    ${ext(mx(88), my(7), 1250, my(7))} ${ext(mx(88), my(57), 1250, my(57))}
    <!-- 側面図 -->
    <rect x="${SX}" y="${my(5)}" width="${SW}" height="${my(135) - my(5)}" rx="6"
          fill="url(#sideface)" stroke="${P.bodyEdge}" stroke-width="3"/>
    <path d="M${SX} ${my(23.3)} H${SX + SW} M${SX} ${my(40.3)} H${SX + SW}"
          stroke="${P.bodyEdge}" stroke-width="2" opacity=".75"/>
    <rect x="${SX - 10}" y="${my(60)}" width="${SW + 20}" height="${my(63) - my(60)}" rx="4"
          fill="#FFFFFF" stroke="${P.bodyEdge}" stroke-width="3"/>
    <path d="M${SX} ${my(86)} H${SX + SW} M${SX} ${my(109)} H${SX + SW} M${SX} ${my(131)} H${SX + SW}"
          stroke="${P.bodyEdge}" stroke-width="2" opacity=".75"/>
    <path d="M${SX - 14} ${my(60)} H${SX + SW + 14}" stroke="${P.line}" stroke-width="2.5" stroke-dasharray="9 9"/>
    <text x="${SX + SW / 2}" y="${my(5) - 34}" text-anchor="middle" font-family="Noto Sans JP"
          font-size="38" font-weight="700" fill="${P.inkSoft}">側面</text>
    ${ext(SX, my(135), SX, 1478)} ${ext(SX + SW, my(135), SX + SW, 1478)}
    ${hDim(SX, SX + SW, 1450, '奥行 35cm')}`;

  const chip = t => `<div class="dc">${t}</div>`;

  return page('06 寸法図', `
.stage{background:#fff}
.grid{position:absolute;inset:0;
  background-image:linear-gradient(${P.cream2} 1px, transparent 1px),
                   linear-gradient(90deg, ${P.cream2} 1px, transparent 1px);
  background-size:50px 50px;opacity:.55}
.top{position:absolute;left:0;right:0;top:76px;text-align:center}
.top .eyebrow{margin-bottom:18px}
.top .h2{font-size:82px}
.pic{position:absolute;left:${L}px;top:${T}px;width:760px;height:1124.8px}
.ov{position:absolute;left:0;top:0;width:2000px;height:2000px;pointer-events:none}
.chips{position:absolute;left:96px;right:96px;bottom:296px;display:flex;gap:22px}
.dc{flex:1;background:${P.cream};border:3px solid ${P.line};border-radius:22px;
    padding:26px 16px;text-align:center;font-size:28px;font-weight:700;color:${P.ink};line-height:1.44}
.nt{position:absolute;left:0;right:0;bottom:216px;text-align:center}
`, `
<div class="grid"></div>
<div class="top">
  <div class="eyebrow">SIZE  &amp;  DIMENSIONS</div>
  <div class="h2">置ける場所が、きっとある。</div>
</div>
<div class="pic">${dresserSVG({ id:'m6', mirror:'right', glow:null, stool:false, items:false })}</div>
<svg class="ov" viewBox="0 0 2000 2000" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="sideface" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#FBF7F2"/><stop offset="1" stop-color="#FFFFFF"/>
  </linearGradient></defs>
  ${dims}
</svg>
<div class="chips">
  ${chip('引き出し内寸<br>約28×30×深13cm')}
  ${chip('ラック1段の有効高<br>約16cm')}
  ${chip('ミラー<br>約38×50cm')}
  ${chip('スツール<br>約38×43cm')}
  ${chip('重量 / 梱包<br>約25kg・1箱')}
</div>
<div class="nt"><p class="note">※サイズは手作業採寸のため、多少の誤差が生じる場合があります。</p></div>
<div class="specbar">
  <b>幅80 × 奥行35 × 高さ130cm</b><i></i><span>天板高 75cm</span><i></i><span>スツール付き</span>
</div>`);
};

// ============================================================
// 07  仕様＋安心ポイント
// ============================================================
const p07 = () => {
  const row = (k, v) => `<div class="r"><div class="k">${k}</div><div class="v">${v}</div></div>`;
  const badge = (svg, t, s) => `
    <div class="bd"><div class="bi">${svg}</div><b>${t}</b><p>${s}</p></div>`;

  const ic = d => `<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"
      fill="none" stroke="${P.gold}" stroke-width="2.6" stroke-linecap="round"
      stroke-linejoin="round">${d}</svg>`;

  return page('07 仕様', `
.stage{background:linear-gradient(172deg,${P.cream} 0%, #FFFFFF 60%, ${P.cream2} 100%)}
.top{position:absolute;left:0;right:0;top:88px;text-align:center}
.top .eyebrow{margin-bottom:20px}
.top .h2{font-size:84px}
.tbl{position:absolute;left:96px;top:380px;width:1808px;background:#fff;border-radius:36px;
  overflow:hidden;border:3px solid ${P.line};box-shadow:0 16px 40px rgba(120,100,74,.09)}
.r{display:flex;border-bottom:2px solid ${P.cream2}}
.r:last-child{border-bottom:0}
.r .k{flex:none;width:520px;background:${P.cream};padding:30px 40px;font-size:34px;font-weight:900;
  color:${P.ink};display:flex;align-items:center}
.r .v{flex:1;padding:30px 40px;font-size:34px;font-weight:500;color:${P.inkSoft};
  display:flex;align-items:center;line-height:1.5}
.bds{position:absolute;left:96px;right:96px;bottom:302px;display:flex;gap:26px}
.bd{flex:1;background:#fff;border:3px solid ${P.line};border-radius:32px;padding:38px 26px 34px;
  text-align:center}
.bi{width:96px;height:96px;margin:0 auto 22px;background:${P.goldPale};border-radius:50%;
  display:flex;align-items:center;justify-content:center}
.bi svg{width:52px;height:52px}
.bd b{display:block;font-size:36px;font-weight:900;margin-bottom:10px;line-height:1.3}
.bd p{font-size:26px;font-weight:500;color:${P.inkSoft};line-height:1.5}
.nt{position:absolute;left:0;right:0;bottom:222px;text-align:center}
`, `
<div class="top">
  <div class="eyebrow">SPECIFICATIONS</div>
  <div class="h2">買う前に、ぜんぶ確認。</div>
</div>
<div class="tbl">
  ${row('サイズ', '幅80 × 奥行35 × 高さ130cm（天板高 75cm）')}
  ${row('カラー', 'ホワイト / ナチュラル / ブラック（全3色）')}
  ${row('素材', '天板・本体：MDF（環境配慮素材）／ 脚・レール：スチール')}
  ${row('収納', '引き出し 計4杯（うち1杯は鍵付き）／ オープンラック 3段')}
  ${row('照明', 'LED 3色調光（電球色・昼白色・昼光色）／ 無段階調光・タッチ操作')}
  ${row('耐荷重', '天板 約15kg ／ 棚1段 約3kg ／ スツール 約100kg')}
  ${row('付属品', 'スツール ／ 転倒防止金具 ／ 組立用工具・取扱説明書')}
  ${row('組立', 'お客様組立（目安 約40分・2名推奨）／ 梱包 1箱・約25kg')}
</div>
<div class="bds">
  ${badge(ic('<path d="M8 40V20l16-12 16 12v20"/><path d="M18 40V28h12v12"/>'),
    'スツール付き','届いたその日から<br>すぐに使えます')}
  ${badge(ic('<path d="M24 6l14 6v11c0 9-6 16-14 19-8-3-14-10-14-19V12z"/><path d="M18 24l4.5 4.5L31 20"/>'),
    '転倒防止金具付','壁に固定して<br>安全に設置できます')}
  ${badge(ic('<rect x="7" y="14" width="34" height="24" rx="3"/><path d="M7 22h34M18 14V8h12v6"/>'),
    '1箱でお届け','受け取りやすい<br>コンパクト梱包')}
  ${badge(ic('<path d="M24 8v8M24 32v8M8 24h8M32 24h8"/><circle cx="24" cy="24" r="8"/>'),
    '1年保証','初期不良は<br>無償で交換対応')}
</div>
<div class="nt"><p class="note">※画像はイメージです。仕様は改良のため予告なく変更となる場合があります。</p></div>
<div class="specbar">
  <b>安心の国内カスタマーサポート</b><i></i><span>組立説明書つき</span><i></i><span>お気軽にお問い合わせください</span>
</div>`);
};

module.exports = { p05, p06, p07 };
