const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const A = require('./src/pages.js');
const B = require('./src/pages2.js');

const PAGES = [
  ['01_main_white',        A.p01, 'メイン画像（白背景・商品単体）'],
  ['02_hero_features',     A.p02, 'サブ1 3大特徴ヒーロー'],
  ['03_led_3color',        A.p03, 'サブ2 3色調光LED'],
  ['04_slide_mirror_2way', A.p04, 'サブ3 スライドミラー2WAY'],
  ['05_storage',           B.p05, 'サブ4 大容量収納'],
  ['06_dimensions',        B.p06, 'サブ5 寸法図'],
  ['07_spec_table',        B.p07, 'サブ6 仕様・安心ポイント'],
];

(async () => {
  const outDir = path.join(__dirname, 'dist');
  const htmlDir = path.join(outDir, 'html');
  fs.mkdirSync(htmlDir, { recursive: true });

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--no-sandbox'] });
  const pg = await browser.newPage({ viewport: { width: 2000, height: 2000 }, deviceScaleFactor: 1 });

  for (const [name, fn, label] of PAGES) {
    const html = fn();
    const hp = path.join(htmlDir, `${name}.html`);
    fs.writeFileSync(hp, html, 'utf8');
    await pg.goto('file://' + hp, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.waitForTimeout(350);
    const out = path.join(outDir, `${name}.png`);
    await pg.screenshot({ path: out, clip: { x: 0, y: 0, width: 2000, height: 2000 } });
    const kb = (fs.statSync(out).size / 1024).toFixed(0);
    console.log(`✓ ${name}.png  ${kb} KB   ${label}`);
  }
  await browser.close();
})().catch(e => { console.error('BUILD FAILED:', e); process.exit(1); });
