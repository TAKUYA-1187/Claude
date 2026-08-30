const fs=require('fs'), path=require('path');
const { chromium } = require('playwright');
const IMGS=[
 ['01_main_white.png','メイン画像','白背景・商品単体（テキストなし）'],
 ['02_hero_features.png','サブ1','3大特徴ヒーロー'],
 ['03_led_3color.png','サブ2','3色調光LED'],
 ['04_slide_mirror_2way.png','サブ3','スライドミラー2WAY'],
 ['05_storage.png','サブ4','大容量収納'],
 ['06_dimensions.png','サブ5','寸法図'],
 ['07_spec_table.png','サブ6','仕様・安心ポイント'],
];
const cells=IMGS.map(([f,tag,label],i)=>`
 <figure><div class="n">${String(i+1).padStart(2,'0')}</div>
  <img src="file://${path.join(__dirname,'dist',f)}">
  <figcaption><b>${tag}</b><span>${label}</span></figcaption></figure>`).join('');
const html=`<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:2560px;background:#F7F4EF;font-family:'Noto Sans JP',sans-serif;color:#2F2A25;padding:56px 56px 64px}
h1{font-size:52px;font-weight:900;margin-bottom:8px}
p.sub{font-size:28px;color:#6B6156;margin-bottom:40px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:34px}
figure{background:#fff;border-radius:24px;overflow:hidden;border:3px solid #E4DACE;position:relative}
figure img{display:block;width:100%;aspect-ratio:1/1;object-fit:contain;background:#fff}
.n{position:absolute;left:16px;top:16px;z-index:2;background:#2F2A25;color:#fff;font-size:24px;font-weight:900;
   width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center}
figcaption{padding:20px 22px 22px;border-top:3px solid #F0EAE1}
figcaption b{display:block;font-size:28px;font-weight:900}
figcaption span{font-size:23px;color:#6B6156}
</style></head><body>
<h1>ドレッサー 幅80cm ─ Amazon 商品ページ画像 7枚</h1>
<p class="sub">2000 × 2000px / 各画像は差し替え・編集可能な HTML ソース付き</p>
<div class="grid">${cells}</div></body></html>`;
(async()=>{
 const p=path.join(__dirname,'dist','00_contact_sheet.html'); fs.writeFileSync(p,html,'utf8');
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--no-sandbox']});
 const pg=await b.newPage({viewport:{width:2560,height:1400}});
 await pg.goto('file://'+p,{waitUntil:'load'}); await pg.evaluate(()=>document.fonts.ready);
 await pg.waitForTimeout(500);
 await pg.screenshot({path:path.join(__dirname,'dist','00_contact_sheet.png'),fullPage:true});
 await b.close(); console.log('✓ 00_contact_sheet.png');
})();
