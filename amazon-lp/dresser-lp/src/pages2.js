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
    { a:[20, 45],  from:[576, 928]  },   // 左オープン棚
    { a:[40, 20],  from:[1424, 708] },   // 鏡裏収納
    { a:[60, 74],  from:[1424, 1168] },  // 鍵付きデスク引き出し
    { a:[25, 110], from:[576, 1388] },   // 3段チェスト
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
  <div class="lead"><span class="hl">引き出し4杯</span>に加えて、<span class="hl">オープン棚</span>と<span class="hl">鏡裏収納</span>。</div>
</div>
<div class="pic">${dresserSVG({ id:'m5', mirror:'open', glow:null, stool:true, items:true, xray:true })}</div>
<svg class="ov" viewBox="0 0 2000 2000" xmlns="http://www.w3.org/2000/svg">${lines}</svg>
${card('1','オープン棚','24×13×60cm。<br>すぐ手の届く位置に。','left:56px;top:820px')}
${card('4','3段チェスト','24×23×8cm ×3杯。<br>種類ごとに分類できます。','left:56px;top:1280px')}
${card('2','鏡裏収納','40×8.5×60cm。<br>鏡の後ろの隠し収納。','left:1424px;top:600px')}
${card('3','鍵付き引き出し','42×23×8cm。<br>ロックできて安心です。','left:1424px;top:1060px')}
<div class="nt"><p class="note">※引き出し内・ラック上の小物は収納イメージです。商品には含まれません。</p></div>
<div class="specbar">
  <b>引き出し 計4杯</b><i></i><span>オープン棚 24×13×60cm</span><i></i>
  <span>鏡裏収納 40×8.5×60cm</span>
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
  <div class="lead"><span class="hl">引き出し4杯</span>に加えて、<span class="hl">オープン棚</span>と<span class="hl">鏡裏収納</span>。</div>
</div>
<div class="grid">
  ${cell('1','storage_1','オープン棚','24×13×60cm。手を伸ばせばすぐ取れる位置に。')}
  ${cell('2','storage_2','鏡裏収納','40×8.5×60cm。鏡をスライドさせると現れます。')}
  ${cell('3','storage_3','鍵付き引き出し','42×23×8cm。大切なものはロックして保管。')}
  ${cell('4','storage_4','3段チェスト','24×23×8cm × 3杯。種類ごとに分類できます。')}
</div>
<div class="nt"><p class="note">※小物は収納イメージです。商品には含まれません。</p></div>
<div class="specbar">
  <b>引き出し 計4杯</b><i></i><span>オープン棚 24×13×60cm</span><i></i>
  <span>鏡裏収納 40×8.5×60cm</span>
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
    ${ext(mx(10), my(65), 300, my(65))}
    ${vDim(my(65), my(135), 1120, '天板高 70cm')}
    ${ext(mx(90), my(65), 1140, my(65))} ${ext(mx(90), my(135), 1140, my(135))}
    ${vDim(my(5), my(65), 1230, 'ミラー 60cm')}
    ${ext(mx(76), my(5), 1250, my(5))} ${ext(mx(76), my(65), 1250, my(65))}
    ${hDim(mx(31), mx(76), 330, 'ミラー 45cm')}
    <!-- 側面図 -->
    <rect x="${SX}" y="${my(5)}" width="${SW}" height="${my(135) - my(5)}" rx="6"
          fill="url(#sideface)" stroke="${P.bodyEdge}" stroke-width="3"/>
    <path d="M${SX} ${my(25)} H${SX + SW} M${SX} ${my(45)} H${SX + SW}"
          stroke="${P.bodyEdge}" stroke-width="2" opacity=".75"/>
    <rect x="${SX - 10}" y="${my(65)}" width="${SW + 20}" height="${my(68) - my(65)}" rx="4"
          fill="#FFFFFF" stroke="${P.bodyEdge}" stroke-width="3"/>
    <path d="M${SX} ${my(85)} H${SX + SW} M${SX} ${my(103)} H${SX + SW} M${SX} ${my(118)} H${SX + SW}"
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
<div class="pic">${dresserSVG({ id:'m6', mirror:'closed', glow:null, stool:false, items:false })}</div>
<svg class="ov" viewBox="0 0 2000 2000" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="sideface" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#FBF7F2"/><stop offset="1" stop-color="#FFFFFF"/>
  </linearGradient></defs>
  ${dims}
</svg>
<div class="chips">
  ${chip('デスク引き出し<br>42×23×8cm 鍵付き')}
  ${chip('チェスト引き出し<br>24×23×8cm × 3杯')}
  ${chip('オープン棚<br>24×13×60cm')}
  ${chip('鏡裏収納<br>40×8.5×60cm')}
  ${chip('スツール<br>32×21.5×36cm')}
</div>
<div class="nt"><p class="note">※サイズは手作業採寸のため、多少の誤差が生じる場合があります。</p></div>
<div class="specbar">
  <b>幅80 × 奥行35 × 高さ130cm</b><i></i><span>天板高 70cm</span><i></i><span>スツール付き</span>
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
  ${row('外寸', '幅80 × 奥行35 × 高さ130cm（天板高 70cm）')}
  ${row('カラー', 'ホワイト')}
  ${row('素材', '木製（MDF）／ スライドレール：スチール')}
  ${row('収納', 'デスク引き出し 42×23×8cm（鍵付き）／ 3段チェスト 24×23×8cm×3<br>オープン棚 24×13×60cm ／ 鏡裏収納 40×8.5×60cm')}
  ${row('照明', 'LED 3色（電球色・昼白色・昼光色）タップ切替<br>長押しでグラデーション調光 0〜100%')}
  ${row('ミラー', '45 × 60cm ／ 横スライド式（鏡裏収納が現れます）')}
  ${row('スツール', '幅32 × 奥行21.5 × 高さ36cm（付属）')}
  ${row('組立', 'お客様組立（組立説明書・工具付属）')}
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
<div class="nt"><p class="note">※本製品は木製のため、サイズに多少の誤差が生じる場合がございます。</p></div>
<div class="specbar">
  <b>スツール付き</b><i></i><span>鍵付きデスク引き出し</span><i></i><span>3色LED・調光機能</span>
</div>`);
};

module.exports = { p05, p06, p07 };
