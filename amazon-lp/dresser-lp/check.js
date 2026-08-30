// =============================================================
//  Amazon 画像規約チェッカー
//  dist/*.png と photos/* を解析し、入稿前に問題を洗い出す
// =============================================================
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { SLOTS, findPhoto } = require('./src/photo.js');

const MIN_LONG_SIDE = 1600;   // ズーム機能の要件
const REC_LONG_SIDE = 2000;   // 推奨
const MAX_BYTES = 10 * 1024 * 1024;
const MAIN_FILL_MIN = 85;     // メイン画像は商品が枠の85%以上

// ブラウザ内で1枚を解析する
async function analyze(pg, fileUrl) {
  return pg.evaluate(async (src) => {
    const img = new Image();
    img.src = src;
    await img.decode();
    const w = img.naturalWidth, h = img.naturalHeight;
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0);
    const d = ctx.getImageData(0, 0, w, h).data;

    const at = (x, y) => { const i = (y * w + x) * 4; return [d[i], d[i+1], d[i+2]]; };
    const isPureWhite = p => p[0] === 255 && p[1] === 255 && p[2] === 255;
    const isNearWhite = p => p[0] >= 250 && p[1] >= 250 && p[2] >= 250;

    // 外周1px（枠）の白色純度
    let border = 0, pure = 0, near = 0;
    for (let x = 0; x < w; x++) for (const y of [0, h - 1]) {
      const p = at(x, y); border++; if (isPureWhite(p)) pure++; if (isNearWhite(p)) near++;
    }
    for (let y = 1; y < h - 1; y++) for (const x of [0, w - 1]) {
      const p = at(x, y); border++; if (isPureWhite(p)) pure++; if (isNearWhite(p)) near++;
    }

    // 被写体のバウンディングボックス（白でない画素の範囲）
    let x0 = w, y0 = h, x1 = -1, y1 = -1;
    const step = Math.max(1, Math.floor(Math.min(w, h) / 900)); // 大きい画像は間引き
    for (let y = 0; y < h; y += step) for (let x = 0; x < w; x += step) {
      const i = (y * w + x) * 4;
      if (d[i] < 245 || d[i+1] < 245 || d[i+2] < 245) {
        if (x < x0) x0 = x; if (x > x1) x1 = x;
        if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
    }
    const bw = x1 < 0 ? 0 : x1 - x0 + 1, bh = y1 < 0 ? 0 : y1 - y0 + 1;
    return {
      w, h,
      borderPureRatio: pure / border,
      borderNearRatio: near / border,
      fillW: bw / w, fillH: bh / h,
    };
  }, fileUrl);
}

const ok = s => `\x1b[32m✓\x1b[0m ${s}`;
const warn = s => `\x1b[33m▲\x1b[0m ${s}`;
const bad = s => `\x1b[31m✗\x1b[0m ${s}`;

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const pg = await browser.newPage();
  // file:// の画像を canvas から読むため、同じ file:// オリジンのページを開く
  const blank = path.resolve('dist', '.check.html');
  fs.writeFileSync(blank, '<!doctype html><meta charset="utf-8"><body></body>');
  await pg.goto('file://' + blank);

  let errors = 0, warns = 0;

  // ---------- 1. 出力画像 ----------
  console.log('\n━━━ 出力画像（dist/） ━━━\n');
  const outs = fs.readdirSync('dist').filter(f => /^0[1-7]_.*\.png$/.test(f)).sort();
  for (const f of outs) {
    const p = path.resolve('dist', f);
    const size = fs.statSync(p).size;
    const r = await analyze(pg, 'file://' + p);
    const long = Math.max(r.w, r.h);
    const lines = [];

    if (long < MIN_LONG_SIDE) { lines.push(bad(`長辺 ${long}px — ズーム要件 ${MIN_LONG_SIDE}px 未満`)); errors++; }
    else if (long < REC_LONG_SIDE) { lines.push(warn(`長辺 ${long}px — 推奨 ${REC_LONG_SIDE}px 未満`)); warns++; }
    if (size > MAX_BYTES) { lines.push(bad(`${(size/1048576).toFixed(1)}MB — 上限10MB超`)); errors++; }

    // メイン画像だけ厳格に判定
    if (f.startsWith('01_')) {
      const fill = Math.max(r.fillW, r.fillH) * 100;
      if (r.borderPureRatio >= 0.999) lines.push(ok('背景 純白 RGB(255,255,255)'));
      else if (r.borderNearRatio >= 0.99) { lines.push(warn(`背景がわずかに白でない（純白率 ${(r.borderPureRatio*100).toFixed(1)}%）`)); warns++; }
      else { lines.push(bad(`背景が白ではありません（純白率 ${(r.borderPureRatio*100).toFixed(1)}%）`)); errors++; }

      if (fill >= MAIN_FILL_MIN) lines.push(ok(`商品の占有率 ${fill.toFixed(0)}%（要件 ${MAIN_FILL_MIN}%以上）`));
      else { lines.push(bad(`商品の占有率 ${fill.toFixed(0)}% — ${MAIN_FILL_MIN}%以上に拡大してください`)); errors++; }
      lines.push(warn('メイン画像は実物の写真である必要があります（イラスト・AI生成画像は不可）'));
      warns++;
    }
    if (!lines.length) lines.push(ok('問題なし'));
    console.log(`  ${f}  ${r.w}×${r.h}  ${(size/1024).toFixed(0)}KB`);
    lines.forEach(l => console.log(`    ${l}`));
    console.log('');
  }

  // ---------- 2. 素材写真 ----------
  console.log('━━━ 素材写真（photos/） ━━━\n');
  let found = 0;
  for (const [name, img, desc] of SLOTS) {
    const src = findPhoto(name);
    if (!src) continue;
    found++;
    const p = src.replace('file://', '');
    const r = await analyze(pg, src);
    const long = Math.max(r.w, r.h);
    const lines = [];
    if (long < MIN_LONG_SIDE) { lines.push(bad(`長辺 ${long}px — ${MIN_LONG_SIDE}px 以上にしてください`)); errors++; }
    else if (long < REC_LONG_SIDE) { lines.push(warn(`長辺 ${long}px — ${REC_LONG_SIDE}px 以上を推奨`)); warns++; }
    if (name === 'main') {
      if (r.borderPureRatio < 0.99) {
        lines.push(bad(`背景が純白ではありません（純白率 ${(r.borderPureRatio*100).toFixed(1)}%）— 切り抜きが必要`));
        errors++;
      } else lines.push(ok('背景 純白'));
    }
    if (!lines.length) lines.push(ok('問題なし'));
    console.log(`  ${path.basename(p)}  ${r.w}×${r.h}  (${img} ${desc})`);
    lines.forEach(l => console.log(`    ${l}`));
    console.log('');
  }
  if (!found) console.log('  写真が1枚も配置されていません（全ページイラストで代替中）\n');

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`  エラー ${errors} 件 / 警告 ${warns} 件\n`);
  await browser.close();
  try { fs.unlinkSync(path.resolve('dist', '.check.html')); } catch {}
  process.exit(errors > 0 ? 1 : 0);
})().catch(e => { console.error('CHECK FAILED:', e); process.exit(2); });
