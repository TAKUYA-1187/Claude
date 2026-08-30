// =============================================================
//  写真スロット: photos/ に画像を置くと自動でイラストと差し替わる
// =============================================================
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, '..', 'photos');
const EXT = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG'];

function findPhoto(name) {
  for (const e of EXT) {
    const p = path.join(DIR, name + e);
    if (fs.existsSync(p)) return 'file://' + p;
  }
  return null;
}
const has = name => !!findPhoto(name);

// fit: 'contain'（商品全体を見せる）/ 'cover'（枠いっぱいに埋める）
function slot(name, fallbackSVG, opts = {}) {
  const { fit = 'contain', radius = 0, bg = 'transparent' } = opts;
  const src = findPhoto(name);
  if (!src) return `<div class="phbox">${fallbackSVG}</div>`;
  return `<div class="phbox" style="background:${bg};border-radius:${radius}px;overflow:hidden">
    <img class="ph" src="${src}" style="object-fit:${fit}"></div>`;
}

const PHOTO_CSS = `
.phbox{width:100%;height:100%;display:flex;align-items:center;justify-content:center}
.ph{width:100%;height:100%;display:block}
`;

// 必要な写真スロットの一覧（撮影指示書と対応）
const SLOTS = [
  ['main',          '01 メイン', '白背景・商品単体（切り抜き）'],
  ['hero',          '02 ヒーロー', '商品全体・斜め45度'],
  ['led_warm',      '03 LED', 'ミラー点灯：電球色'],
  ['led_neutral',   '03 LED', 'ミラー点灯：昼白色'],
  ['led_cool',      '03 LED', 'ミラー点灯：昼光色'],
  ['mirror_closed', '04 2WAY', 'ミラーを中央に寄せた状態'],
  ['mirror_open',   '04 2WAY', 'ミラーを横にスライドした状態'],
  ['storage_1',     '05 収納', 'オープンラックに収納した状態'],
  ['storage_2',     '05 収納', '鍵付き引き出しを開けた状態'],
  ['storage_3',     '05 収納', '引き出し3杯を開けた状態'],
  ['storage_4',     '05 収納', 'スツールを足元に収めた状態'],
];

module.exports = { findPhoto, has, slot, PHOTO_CSS, SLOTS, DIR };
