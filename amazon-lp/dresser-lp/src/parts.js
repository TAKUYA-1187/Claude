// =============================================================
//  Amazon LP 画像ジェネレーター  ─ 共通パーツ / デザインシステム
//  商品: ドレッサー 幅80×奥行35×高さ130cm
//  ※ 実測仕様に基づく（製品仕様図より）
//    天板高70 / チェスト高50・幅30 / オープン棚 24×13×60
//    ミラー裏収納 40×8.5×60 / ミラー 45×60 / スツール 32×21.5×36
// =============================================================

const P = {
  ink:'#2F2A25', inkSoft:'#6B6156', inkFaint:'#9C9186',
  cream:'#FBF7F2', cream2:'#F3ECE3', line:'#E4DACE',
  gold:'#B8935E', goldLt:'#D9BC8E', goldPale:'#F2E7D5',
  rose:'#D9A9A3', rosePale:'#F7EBE9',
  white:'#FFFFFF', bodyEdge:'#DCD6CF', bodyShade:'#F0EEEB',
  wood:'#C9A176', woodDk:'#A87F4F',
  glass1:'#EAF1F5', glass2:'#CFDDE6', led:'#FFCF8A',
  rail:'#3A3632',
};

// cm → SVG 座標（全幅80cm を x=10..90、床を y=135 に置く）
const X = cm => 10 + cm;          // 0..80cm
const Y = cm => 135 - cm;         // 高さcm（床=0）

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// -------------------------------------------------------------
//  ドレッサー正面図
//  opts: mirror 'closed'|'open'|'none' / stool / glow / items / xray
// -------------------------------------------------------------
function dresserSVG(opts = {}) {
  const o = Object.assign(
    { mirror:'closed', stool:true, glow:null, items:true, xray:false, id:'d' }, opts);
  const u = o.id;
  const glowCol = { warm:'#FFC069', neutral:'#FFF3DE', cool:'#CFE4FF' }[o.glow] || null;

  // ミラー 45×60cm。閉=裏収納を覆う / 開=右へスライドして収納が露出
  const mCm = o.mirror === 'open' ? 42 : 30;
  const mL = X(mCm), mR = X(mCm + 45), mT = Y(130), mB = Y(70);

  const drawer = (x1,y1,x2,y2,{lock=false,inside=''}={}) => `
    ${inside ? `<rect x="${x1}" y="${y1}" width="${x2-x1}" height="${y2-y1}" rx="1" fill="#FFFDFA"/>
      <rect x="${x1}" y="${y1}" width="${x2-x1}" height="${y2-y1}" rx="1" fill="#EFEBE5" opacity=".5"/>${inside}` : ''}
    <rect x="${x1}" y="${y1}" width="${x2-x1}" height="${y2-y1}" rx="1"
          fill="url(#face${u})" opacity="${inside?'0.40':'1'}" stroke="${P.bodyEdge}"
          stroke-width="0.4" stroke-dasharray="${inside?'2.2 1.7':'none'}"/>
    <rect x="${(x1+x2)/2-6}" y="${(y1+y2)/2-0.8}" width="12" height="1.6" rx="0.8" fill="${P.wood}"/>
    <rect x="${(x1+x2)/2-6}" y="${(y1+y2)/2-0.8}" width="12" height="0.55" rx="0.28" fill="${P.woodDk}" opacity=".35"/>
    ${lock?`<circle cx="${x2-4}" cy="${(y1+y2)/2}" r="1.1" fill="none" stroke="${P.woodDk}" stroke-width="0.35"/>
      <circle cx="${x2-4}" cy="${(y1+y2)/2}" r="0.32" fill="${P.woodDk}"/>
      <path d="M${x2-4} ${(y1+y2)/2+1.1} v2.4" stroke="${P.woodDk}" stroke-width="0.4"/>`:''}`;

  const btl=(x,base,h,w,c)=>`<rect x="${x}" y="${base-h}" width="${w}" height="${h}" rx="${Math.min(.8,w/3)}" fill="${c}"/>
    <rect x="${x+w*.32}" y="${base-h-1.3}" width="${w*.36}" height="1.3" rx=".25" fill="${c}" opacity=".8"/>`;
  const jar=(x,base,r,c)=>`<rect x="${x}" y="${base-r*1.4}" width="${r*2}" height="${r*1.4}" rx=".5" fill="${c}"/>
    <rect x="${x-.2}" y="${base-r*1.4-.8}" width="${r*2+.4}" height=".9" rx=".35" fill="${c}" opacity=".75"/>`;

  // 左オープン棚（4段, x 3..27cm, 高さ50..110cm）
  const towerItems = !o.items ? '' : `<g opacity=".95">
    ${btl(X(5),Y(96),7,2.4,'#E6D2C0')}${btl(X(8.5),Y(96),5,2.2,P.rosePale)}${jar(X(11.5),Y(96),1.7,'#EAD9CB')}
    ${btl(X(16),Y(96),8,2,'#DCE6E3')}${btl(X(19),Y(96),5.5,2.6,'#F0E2D2')}
    ${btl(X(5),Y(81),6,2.3,'#DFE7E9')}${jar(X(8.5),Y(81),1.9,'#EFDCD6')}${btl(X(12.5),Y(81),8.5,1.9,'#E8DCC8')}
    ${btl(X(15.5),Y(81),4.5,2.5,'#E3D3C6')}${btl(X(19.5),Y(81),6.5,2.2,P.rosePale)}
    ${btl(X(5),Y(66),7.5,2.5,'#E9DED0')}${btl(X(8.8),Y(66),5.5,2.1,'#DDE8E6')}${jar(X(12),Y(66),1.8,'#F1E2DA')}
    ${btl(X(16),Y(66),9,1.9,'#E4D8C6')}${btl(X(19),Y(66),6,2.5,'#EADCCB')}
    ${btl(X(5),Y(51),6.5,2.4,'#E9DCCC')}${jar(X(9),Y(51),1.8,'#F1E3DB')}${btl(X(13),Y(51),8,2,'#E5DAC7')}
    ${btl(X(16.5),Y(51),5,2.4,'#E1E8E6')}${btl(X(20),Y(51),7,2.1,'#EDDFD0')}</g>`;

  // ミラー裏収納（3段, x 23..63cm, 高さ70..130cm）
  const backItems = !o.items ? '' : `<g opacity=".95">
    ${btl(X(34.0),Y(112),7.5,2.4,'#E7DACB')}${jar(X(37.5),Y(112),1.8,'#EFE0D8')}${btl(X(42.0),Y(112),9,2.1,'#DFE8E6')}
    ${btl(X(45.0),Y(112),5.5,2.6,'#F0E3D4')}${btl(X(49.0),Y(112),8,2.2,P.rosePale)}${btl(X(52.5),Y(112),6,2.4,'#E5D6C6')}
    ${btl(X(56.0),Y(112),7,2.2,'#E9DCCF')}${btl(X(60.0),Y(112),5,2.5,'#DEE7E5')}${jar(X(64.0),Y(112),1.9,'#F0E1D9')}
    ${btl(X(34.0),Y(92),9,2,'#E8DBC9')}${btl(X(37.0),Y(92),5.5,2.6,'#E2E9E7')}${jar(X(41.0),Y(92),2,'#F0DFD8')}
    ${btl(X(45.0),Y(92),7.5,2.2,'#E6D8C8')}${btl(X(48.5),Y(92),5,2.7,'#EFE1D1')}${btl(X(52.5),Y(92),6.5,2.1,'#DEE7E5')}
    ${btl(X(56.0),Y(92),8,2.3,'#E7D9C7')}${jar(X(60.0),Y(92),1.8,'#F2E4DC')}${btl(X(64.0),Y(92),6,2.4,'#E4D7C9')}
    ${btl(X(34.0),Y(72),7,2.5,'#E9DCCC')}${jar(X(37.5),Y(72),1.9,'#F1E3DB')}${btl(X(41.5),Y(72),9,2.1,'#E5DAC7')}
    ${btl(X(45.0),Y(72),5.5,2.5,'#E1E8E6')}${btl(X(49.0),Y(72),7.5,2.3,'#EDDFD0')}${btl(X(53.0),Y(72),5,2.4,P.rosePale)}
    ${btl(X(57.0),Y(72),8,2.2,'#E6D9CA')}${btl(X(61.0),Y(72),5.5,2.5,'#E0E8E5')}</g>`;

  const IN = c => !o.xray ? '' : c;
  const itm=(x,fl,w,h,c,r=.5)=>`<rect x="${x}" y="${fl-h}" width="${w}" height="${h}" rx="${r}" fill="${c}"/>`;

  return `
<svg class="dresser" viewBox="0 0 100 148" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="face${u}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="${P.bodyShade}"/></linearGradient>
    <linearGradient id="side${u}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#F7F5F2"/><stop offset="1" stop-color="#FFFFFF"/></linearGradient>
    <linearGradient id="glass${u}" x1=".1" y1="0" x2=".9" y2="1">
      <stop offset="0" stop-color="${P.glass1}"/><stop offset=".45" stop-color="#F4F8FA"/>
      <stop offset="1" stop-color="${P.glass2}"/></linearGradient>
    <linearGradient id="cav${u}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#E7E3DE"/><stop offset="1" stop-color="#F6F4F1"/></linearGradient>
    <radialGradient id="shadow${u}" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#8A7A66" stop-opacity=".28"/>
      <stop offset="1" stop-color="#8A7A66" stop-opacity="0"/></radialGradient>
    ${glowCol?`<filter id="glow${u}" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`:''}
  </defs>

  <ellipse cx="50" cy="136" rx="46" ry="4" fill="url(#shadow${u})"/>

  <!-- ===== ミラー裏収納ユニット（40×60cm / 高さ70-130） ===== -->
  <rect x="${X(32)}" y="${Y(130)}" width="40" height="60" rx="1.2"
        fill="url(#cav${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <rect x="${X(32)}" y="${Y(130)}" width="40" height="1.8" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="${X(32)}" y="${Y(130)}" width="1.6" height="60" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  <rect x="${X(70.4)}" y="${Y(130)}" width="1.6" height="60" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  <rect x="${X(33.6)}" y="${Y(110)}" width="36.8" height="1.5" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  <rect x="${X(33.6)}" y="${Y(90)}" width="36.8" height="1.5" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  ${backItems}
  <!-- スライドレール（実物の黒い金具） -->
  <rect x="${X(32)}" y="${Y(129.5)}" width="40" height="2.4" rx="0.5" fill="${P.rail}"/>
  <rect x="${X(32)}" y="${Y(101)}" width="40" height="2.4" rx="0.5" fill="${P.rail}"/>

  <!-- ===== 左オープン棚（24×60cm / 高さ50-110） ===== -->
  <rect x="${X(3)}" y="${Y(110)}" width="24" height="60" rx="1.2"
        fill="url(#cav${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <rect x="${X(3)}" y="${Y(110)}" width="24" height="1.8" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="${X(3)}" y="${Y(110)}" width="1.6" height="60" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  <rect x="${X(25.4)}" y="${Y(110)}" width="1.6" height="60" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.3"/>
  ${[95,80,65].map(h=>`<rect x="${X(4.6)}" y="${Y(h)}" width="20.8" height="1.4" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.28"/>`).join('')}
  ${towerItems}

  <!-- ===== スライドミラー 45×60cm ===== -->
  ${o.mirror==='none'?'':`
  <g ${glowCol?`filter="url(#glow${u})"`:''}>
    <rect x="${mL}" y="${mT}" width="45" height="60" rx="2.4" fill="${glowCol||P.led}" opacity="${glowCol?.5:.28}"/>
    <rect x="${mL}" y="${mT}" width="45" height="60" rx="2.4" fill="url(#face${u})"/>
    <rect x="${mL+3}" y="${mT+3}" width="39" height="54" rx="1.4" fill="${glowCol||'#FFE0B2'}" opacity="${glowCol?.85:.55}"/>
    <rect x="${mL+4.6}" y="${mT+4.6}" width="35.8" height="50.8" rx="1" fill="url(#glass${u})"/>
  </g>
  <rect x="${mL}" y="${mT}" width="45" height="60" rx="2.4" fill="none" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <path d="M${mL+7} ${mB-5} L${mL+20} ${mT+5.4} L${mL+26} ${mT+5.4} L${mL+13} ${mB-5} Z" fill="#FFF" opacity=".34"/>
  <path d="M${mL+29} ${mB-5} L${mL+36} ${mT+5.4} L${mL+38.5} ${mT+5.4} L${mL+31.5} ${mB-5} Z" fill="#FFF" opacity=".2"/>
  <circle cx="${mR-6}" cy="${mB-7}" r="1.5" fill="none" stroke="${P.goldLt}" stroke-width="0.35" opacity=".9"/>
  <circle cx="${mR-6}" cy="${mB-7}" r="0.5" fill="${P.goldLt}"/>`}

  <!-- ===== デスク天板（高さ70cm / 幅50cm） ===== -->
  <rect x="${X(29)}" y="${Y(70)}" width="52" height="3" rx="1" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <rect x="${X(29)}" y="${Y(67.4)}" width="52" height="0.8" fill="${P.bodyShade}"/>

  <!-- ===== 鍵付きワイド引き出し（42×23×8cm） ===== -->
  ${drawer(X(31), Y(67), X(79), Y(55), { lock:true, inside: IN(
    itm(X(35),Y(56.5),12,3,'#DED5C8')+itm(X(49),Y(56.5),7,4,'#E4D6C4')+
    itm(X(58),Y(56.5),5,4.5,'#DCE3E0')+itm(X(65),Y(56.5),2.6,4,'#D9A9A3',.9)) })}

  <!-- ===== デスク脚・側板 ===== -->
  <rect x="${X(30)}" y="${Y(55)}" width="3" height="55" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="${X(77)}" y="${Y(55)}" width="3" height="55" fill="url(#side${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  <rect x="${X(33)}" y="${Y(55)}" width="44" height="55" fill="url(#cav${u})" opacity=".8"/>
  <rect x="${X(33)}" y="${Y(55)}" width="44" height="1" fill="${P.bodyEdge}" opacity=".55"/>

  <!-- ===== 3段チェスト（幅30 × 高さ50cm） ===== -->
  <rect x="${X(0)}" y="${Y(50)}" width="30" height="50" rx="1.2" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.5"/>
  <rect x="${X(0)}" y="${Y(50)}" width="30" height="2" rx="0.8" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  ${drawer(X(1.2), Y(47.5), X(28.8), Y(33), { inside: IN(
    itm(X(4),Y(34),2.2,6,'#D9A9A3',1.1)+itm(X(7),Y(34),2.2,5,'#C98F88',1.1)+
    itm(X(10),Y(34),2.2,6.5,'#E0B6AF',1.1)+itm(X(14),Y(34),5.5,2.6,'#DCD3C6')+itm(X(21),Y(34),4,3,'#E4D6C4')) })}
  ${drawer(X(1.2), Y(32), X(28.8), Y(17.5), { inside: IN(
    itm(X(4),Y(18.5),11,3.6,'#DED5C8')+itm(X(17),Y(18.5),1.5,8,'#C9A176',.7)+
    itm(X(19.5),Y(18.5),1.5,7,'#B98F63',.7)+itm(X(22),Y(18.5),3.2,6.5,'#DCE3E0')) })}
  ${drawer(X(1.2), Y(16.5), X(28.8), Y(3), { inside: IN(
    itm(X(4),Y(4),8,7,'#DCD3C6',1.3)+itm(X(14),Y(4),3.4,9,'#E2D6C2',.9)+
    itm(X(18.5),Y(4),3,7,'#DDE5E2',.9)+itm(X(23),Y(4),3.6,8,'#EBDCD4',.9)) })}
  <rect x="${X(1.5)}" y="${Y(2.6)}" width="27" height="2.6" fill="${P.bodyShade}" stroke="${P.bodyEdge}" stroke-width="0.3"/>

  ${o.stool?`
  <!-- ===== スツール 32×21.5×36cm ===== -->
  <g>
    <ellipse cx="${X(56)}" cy="134" rx="16" ry="2.4" fill="#8A7A66" opacity=".14"/>
    <path d="M${X(40)} ${Y(36)} q16 -3 32 0 v4.4 q-16 2.6 -32 0 z" fill="#FBF8F4" stroke="${P.bodyEdge}" stroke-width="0.4"/>
    <path d="M${X(41)} ${Y(34.6)} q15 2.4 30 0" stroke="#EDE6DC" stroke-width="0.45" fill="none"/>
    <rect x="${X(40)}" y="${Y(31.6)}" width="32" height="2.4" rx="0.8" fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
    <path d="M${X(42)} ${Y(29.2)} v${29.2} h3.4 v-${26.6} h21.2 v${26.6} h3.4 v-${29.2} z"
          fill="url(#face${u})" stroke="${P.bodyEdge}" stroke-width="0.35"/>
  </g>`:''}
</svg>`;
}

module.exports = { P, X, Y, dresserSVG, esc };
