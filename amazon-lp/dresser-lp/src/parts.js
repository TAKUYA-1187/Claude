// =============================================================
//  Amazon LP 画像ジェネレーター  ─ 共通パーツ / デザインシステム
//  商品: ドレッサー 幅80cm LEDスライドミラー 収納充実 スツール付
// =============================================================

const P = {
  ink:      '#2F2A25',
  inkSoft:  '#6B6156',
  inkFaint: '#9C9186',
  cream:    '#FBF7F2',
  cream2:   '#F3ECE3',
  line:     '#E4DACE',
  gold:     '#B8935E',
  goldLt:   '#D9BC8E',
  goldPale: '#F2E7D5',
  rose:     '#D9A9A3',
  rosePale: '#F7EBE9',
  white:    '#FFFFFF',
  bodyEdge: '#DCD6CF',
  bodyShade:'#F0EEEB',
  wood:     '#C9A176',
  woodDk:   '#A87F4F',
  glass1:   '#EAF1F5',
  glass2:   '#CFDDE6',
  led:      '#FFCF8A',
};

// ---- レイアウト定数（cm 単位、床 y=135 / 本体 x:10-90）----
const G = {
  floorY: 135, left: 10, right: 90, topY: 5,
  deskTop: 60, deskBot: 63,
  midX: 45,
};

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// -------------------------------------------------------------
//  ドレッサー正面図 SVG
//  opts: { mirror:'right'|'left'|'none', stool:bool, glow:'warm'|'neutral'|'cool'|null,
//          items:bool (収納物を描く), dim:bool (寸法補助線) }
// -------------------------------------------------------------
function dresserSVG(opts = {}) {
  const o = Object.assign(
    { mirror:'right', stool:true, glow:null, items:true, xray:false, id:'d' }, opts);
  const u = o.id; // defs の id 衝突回避

  const glowCol = { warm:'#FFC069', neutral:'#FFF3DE', cool:'#CFE4FF' }[o.glow] || null;

  // ミラー位置
  const mL = o.mirror === 'left' ? 12 : 50;
  const mR = mL + 38;

  const drawer = (x1, y1, x2, y2, lock=false, inside='') => `
    ${inside ? `<rect x="${x1}" y="${y1}" width="${x2-x1}" height="${y2-y1}" rx="1.2" fill="#FFFDFA"/>
       <rect x="${x1}" y="${y1}" width="${x2-x1}" height="${y2-y1}" rx="1.2" fill="#EFEBE5" opacity=".5"/>
       ${inside}` : ''}
    <rect x="${x1}" y="${y1}" width="${x2-x1}" height="${y2-y1}" rx="1.2"
          fill="url(#face${u})" opacity="${inside ? '0.40' : '1'}"
          stroke="${P.bodyEdge}" stroke-width="0.45"
          stroke-dasharray="${inside ? '2.4 1.8' : 'none'}"/>
    <rect x="${(x1+x2)/2 - 7}" y="${(y1+y2)/2 - 0.85}" width="14" height="1.7" rx="0.85"
          fill="${P.wood}"/>
    <rect x="${(x1+x2)/2 - 7}" y="${(y1+y2)/2 - 0.85}" width="14" height="0.6" rx="0.3"
          fill="${P.woodDk}" opacity=".35"/>
    ${lock ? `<circle cx="${x2-4.5}" cy="${(y1+y2)/2}" r="1.15" fill="none"
          stroke="${P.woodDk}" stroke-width="0.4"/>
       <circle cx="${x2-4.5}" cy="${(y1+y2)/2}" r="0.35" fill="${P.woodDk}"/>` : ''}`;


  // 引き出しの中身（xray 表示）
  const itm = (x, floor, w, h, col, r=0.6) =>
    `<rect x="${x}" y="${floor-h}" width="${w}" height="${h}" rx="${r}" fill="${col}"/>`;
  const IN1 = !o.xray ? '' : [
    itm(14,84,2.6,7.5,'#D9A9A3',1.3), itm(17.6,84,2.6,6,'#C98F88',1.3),
    itm(21.2,84,2.6,8,'#E0B6AF',1.3), itm(24.8,84,2.6,6.5,'#CFA098',1.3),
    itm(29.5,84,6.5,3,'#DCD3C6'), itm(37,84,4.5,3.4,'#E4D6C4'),
  ].join('');
  const IN2 = !o.xray ? '' : [
    itm(13.8,107,13,4.2,'#DED5C8'), itm(15.5,102.8,3.4,1.2,'#C9BCAA',0.4),
    itm(28,107,1.7,10,'#C9A176',0.8), itm(30.4,107,1.7,8.5,'#B98F63',0.8),
    itm(32.8,107,1.7,11,'#D4AE86',0.8), itm(36.5,107,3.6,8,'#DCE3E0'),
  ].join('');
  const IN3 = !o.xray ? '' : [
    itm(13.8,128.5,10,9,'#DCD3C6',1.6), itm(25.5,128.5,4,11,'#E2D6C2',1),
    itm(31,128.5,3.6,8.5,'#DDE5E2',1), itm(35.5,128.5,4.2,10,'#EBDCD4',1),
  ].join('');
  const IN4 = !o.xray ? '' : [
    itm(50,77,14,4,'#DED5C8'), itm(66,77,8,5,'#E4D6C4'), itm(76.5,77,6,5.5,'#DCE3E0'),
    itm(84,77,3,4.5,'#D9A9A3',1),
  ].join('');

  // 棚に置く小物（香水・スキンケア等）
  const bottle = (x, base, h, w, col) => `
    <rect x="${x}" y="${base-h}" width="${w}" height="${h}" rx="${Math.min(0.9,w/3)}" fill="${col}"/>
    <rect x="${x+w*0.32}" y="${base-h-1.6}" width="${w*0.36}" height="1.6" rx="0.3" fill="${col}" opacity=".8"/>`;
  const jar = (x, base, r, col) => `
    <rect x="${x}" y="${base-r*1.5}" width="${r*2}" height="${r*1.5}" rx="0.6" fill="${col}"/>
    <rect x="${x-0.2}" y="${base-r*1.5-0.9}" width="${r*2+0.4}" height="1" rx="0.4" fill="${col}" opacity=".75"/>`;

  const shelfItems = !o.items ? '' : `
    <g opacity=".95">
      ${bottle(14, 22, 8, 3, '#E6D2C0')}${bottle(18.5, 22, 5.5, 2.6, P.rosePale)}
      ${jar(22.5, 22, 2, '#EAD9CB')}${bottle(28, 22, 9.5, 2.4, '#DCE6E3')}
      ${bottle(32, 22, 6, 3.2, '#F0E2D2')}
      ${bottle(14, 39, 7, 2.8, '#DFE7E9')}${jar(18, 39, 2.3, '#EFDCD6')}
      ${bottle(23, 39, 10, 2.2, '#E8DCC8')}${bottle(26.5, 39, 5, 3, '#E3D3C6')}
      ${bottle(31.5, 39, 8, 2.6, P.rosePale)}
      ${bottle(14, 57.5, 9, 3, '#E9DED0')}${bottle(18.5, 57.5, 6.5, 2.5, '#DDE8E6')}
      ${jar(22.5, 57.5, 2.2, '#F1E2DA')}${bottle(28, 57.5, 11, 2.3, '#E4D8C6')}
      ${bottle(31.5, 57.5, 7, 3, '#EADCCB')}
      ${bottle(52, 22, 7, 2.8, '#E7DACB')}${jar(56, 22, 2.1, '#EFE0D8')}
      ${bottle(61, 22, 9, 2.4, '#DFE8E6')}${bottle(65, 22, 5.5, 3, '#F0E3D4')}
      ${bottle(70, 22, 8, 2.6, P.rosePale)}${bottle(74.5, 22, 6, 2.8, '#E5D6C6')}
      ${bottle(52, 39, 10, 2.3, '#E8DBC9')}${bottle(56, 39, 6, 3, '#E2E9E7')}
      ${jar(61, 39, 2.4, '#F0DFD8')}${bottle(66.5, 39, 8.5, 2.5, '#E6D8C8')}
      ${bottle(70.5, 39, 5.5, 3.1, '#EFE1D1')}${bottle(75, 39, 7.5, 2.4, '#DEE7E5')}
      ${bottle(52, 57.5, 8, 3, '#E9DCCC')}${jar(56.5, 57.5, 2.2, '#F1E3DB')}
      ${bottle(61, 57.5, 10.5, 2.4, '#E5DAC7')}${bottle(65, 57.5, 6, 2.9, '#E1E8E6')}
      ${bottle(70, 57.5, 8.5, 2.6, '#EDDFD0')}${bottle(74.5, 57.5, 5.5, 2.8, P.rosePale)}
    </g>`;

  return `
<svg class="dresser" viewBox="0 0 100 148" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="face${u}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="${P.bodyShade}"/>
    </linearGradient>
    <linearGradient id="side${u}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#F7F5F2"/><stop offset="1" stop-color="#FFFFFF"/>
    </linearGradient>
    <linearGradient id="glass${u}" x1="0.1" y1="0" x2="0.9" y2="1">
      <stop offset="0" stop-color="${P.glass1}"/><stop offset=".45" stop-color="#F4F8FA"/>
      <stop offset="1" stop-color="${P.glass2}"/>
    </linearGradient>
    <linearGradient id="cav${u}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#E7E3DE"/><stop offset="1" stop-color="#F6F4F1"/>
    </linearGradient>
    <radialGradient id="shadow${u}" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#8A7A66" stop-opacity=".30"/>
      <stop offset="1" stop-color="#8A7A66" stop-opacity="0"/>
    </radialGradient>
    ${glowCol ? `<filter id="glow${u}" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>` : ''}
  </defs>

  <!-- 接地影 -->
  <ellipse cx="50" cy="136" rx="46" ry="4.2" fill="url(#shadow${u})"/>

  <!-- ===== 上部ユニット（オープンラック） ===== -->
  <rect x="10" y="5" width="80" height="55" rx="1.4" fill="url(#cav${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <rect x="11.6" y="6.6" width="76.8" height="51.8" fill="#EDEAE5" opacity=".6"/>
  <!-- 棚板 -->
  <rect x="10" y="5" width="80" height="2.2" rx="1" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.4"/>
  <rect x="11.6" y="22.4" width="76.8" height="1.8" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="11.6" y="39.4" width="76.8" height="1.8" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <!-- 側板 -->
  <rect x="10" y="5" width="1.8" height="55" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="88.2" y="5" width="1.8" height="55" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <!-- 中仕切り -->
  <rect x="46.6" y="6.6" width="1.4" height="51.8" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  ${shelfItems}

  <!-- ===== スライドミラー ===== -->
  ${o.mirror === 'none' ? '' : `
  <!-- レール -->
  <rect x="11" y="5.4" width="78" height="1.4" rx="0.7" fill="${P.goldPale}" stroke="${P.goldLt}" stroke-width="0.25"/>
  <g ${glowCol ? `filter="url(#glow${u})"` : ''}>
    <rect x="${mL}" y="7" width="38" height="50" rx="1.6"
          fill="${glowCol || P.led}" opacity="${glowCol ? .55 : .32}"/>
    <rect x="${mL+1.5}" y="8.5" width="35" height="47" rx="1" fill="url(#glass${u})"/>
  </g>
  <rect x="${mL}" y="7" width="38" height="50" rx="1.6" fill="none"
        stroke="${P.bodyEdge}" stroke-width="0.55"/>
  <rect x="${mL+1.5}" y="8.5" width="35" height="47" rx="1" fill="none"
        stroke="${glowCol || P.goldLt}" stroke-width="0.8" opacity=".9"/>
  <!-- 鏡面ハイライト -->
  <path d="M ${mL+4} 55 L ${mL+16} 9.6 L ${mL+22} 9.6 L ${mL+10} 55 Z" fill="#FFFFFF" opacity=".38"/>
  <path d="M ${mL+24} 55 L ${mL+31} 9.6 L ${mL+33.5} 9.6 L ${mL+26.5} 55 Z" fill="#FFFFFF" opacity=".22"/>
  <!-- タッチスイッチ -->
  <circle cx="${mR-3.4}" cy="52.5" r="1.15" fill="#FFFFFF" opacity=".85" stroke="${P.goldLt}" stroke-width="0.3"/>`}

  <!-- ===== 天板 ===== -->
  <rect x="8" y="60" width="84" height="3" rx="1.1" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <rect x="8" y="62.2" width="84" height="0.8" fill="${P.bodyShade}"/>

  <!-- ===== 下部：左チェスト（引き出し3杯） ===== -->
  <rect x="10" y="63" width="34" height="72" rx="1.2" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  ${drawer(11.4, 65, 42.6, 86, false, IN1)}
  ${drawer(11.4, 88, 42.6, 109, false, IN2)}
  ${drawer(11.4, 111, 42.6, 130.5, false, IN3)}
  <rect x="12.5" y="131.5" width="29" height="3.5" fill="${P.bodyShade}" stroke="${P.bodyEdge}" stroke-width="0.35"/>

  <!-- ===== 下部：右 鍵付きワイド引き出し＋ニースペース ===== -->
  ${drawer(46, 65, 90, 79, true, IN4)}
  <rect x="88.2" y="79" width="1.8" height="56" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="46" y="79" width="42.2" height="56" fill="url(#cav${u})"/>
  <rect x="46" y="79" width="42.2" height="1.2" fill="#DCD6CF" opacity=".7"/>
  <line x1="46" y1="135" x2="90" y2="135" stroke="${P.bodyEdge}" stroke-width="0.5"/>

  ${o.stool ? `
  <!-- ===== スツール ===== -->
  <g>
    <ellipse cx="67" cy="134" rx="15" ry="2.6" fill="#8A7A66" opacity=".16"/>
    <rect x="52" y="104" width="30" height="6.4" rx="3.2" fill="${P.rosePale}" stroke="${P.bodyEdge}" stroke-width="0.45"/>
    <path d="M53 106.5 q14 3 28 0" stroke="#E4CFCA" stroke-width="0.5" fill="none"/>
    <rect x="53" y="110.4" width="28" height="3" rx="1" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.4"/>
    <rect x="55.5" y="113.4" width="2.4" height="20.4" rx="1.2" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.4"/>
    <rect x="76.1" y="113.4" width="2.4" height="20.4" rx="1.2" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.4"/>
    <rect x="57.9" y="122" width="18.2" height="1.8" rx="0.9" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  </g>` : ''}
</svg>`;
}

module.exports = { P, G, dresserSVG, esc };
