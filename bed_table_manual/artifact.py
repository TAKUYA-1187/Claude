# -*- coding: utf-8 -*-
"""Screen proof of the printed manual: the four A4 pages on a review desk."""
import build as B

PROOF_CSS = """
/* --- review desk -------------------------------------------------------- */
:root{
  --desk:#878E97; --desk-edge:#6E757E; --desk-ink:#FFFFFF; --desk-ink2:#DDE2E7;
  --desk-chip:rgba(255,255,255,.14); --desk-rule:rgba(255,255,255,.24);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --desk:#23272C; --desk-edge:#16191D; --desk-ink:#F2F4F6; --desk-ink2:#A8B0B8;
    --desk-chip:rgba(255,255,255,.09); --desk-rule:rgba(255,255,255,.16);
  }
}
:root[data-theme="dark"]{
  --desk:#23272C; --desk-edge:#16191D; --desk-ink:#F2F4F6; --desk-ink2:#A8B0B8;
  --desk-chip:rgba(255,255,255,.09); --desk-rule:rgba(255,255,255,.16);
}
body{background:var(--desk)}
.proofbar,.folio{color:var(--desk-ink)}
.proof{--z:1; padding:0 0 14mm; min-height:100vh}
.proofbar{
  display:flex; flex-wrap:wrap; align-items:baseline; gap:10px 18px;
  padding:20px clamp(14px,4vw,40px) 18px; border-bottom:1px solid var(--desk-rule);
  background:var(--desk-edge); margin-bottom:clamp(16px,3vw,32px);
}
.proofbar h1{
  font-size:clamp(15px,2.2vw,19px); font-weight:900; margin:0; letter-spacing:.01em;
  color:var(--desk-ink); line-height:1.4;
}
.proofbar p{margin:0; font-size:12.5px; color:var(--desk-ink2); line-height:1.6}
.proofbar .spec{display:flex; gap:7px; flex-wrap:wrap; margin-left:auto}
.proofbar .spec span{
  font-size:11px; font-weight:700; letter-spacing:.04em; padding:3px 9px;
  border-radius:2px; background:var(--desk-chip); color:var(--desk-ink);
  font-variant-numeric:tabular-nums;
}
.slot{
  width:100%; height:calc(297mm * var(--z)); display:flex; justify-content:center;
  margin-bottom:calc(11mm * var(--z));
}
.slot .page{transform:scale(var(--z)); transform-origin:top center; margin:0}
.folio{
  text-align:center; font-size:11px; letter-spacing:.16em; font-weight:700;
  color:var(--desk-ink2); margin:0 0 7px;
}
@media print{
  .proofbar,.folio{display:none}
  .proof{--z:1 !important; padding:0}
  .slot{height:auto; margin:0}
  .slot .page{transform:none}
  body{background:#fff}
}
"""

PROOF_JS = """
<script>
(function(){
  var proof = document.querySelector('.proof');
  var PAGE_PX = 210 / 25.4 * 96;              // A4 width at CSS 96dpi
  function fit(){
    var avail = proof.clientWidth - 28;
    proof.style.setProperty('--z', Math.min(1, avail / PAGE_PX).toFixed(4));
  }
  fit();
  window.addEventListener('resize', fit);
  if (window.ResizeObserver) new ResizeObserver(fit).observe(proof);
})();
</script>
"""


def main():
    pages = [B.page1(), B.page2(), B.page3(), B.page4()]
    labels = ["表紙・同梱部品", "組み立て方", "仕上げと使い方", "安全・困ったときは"]
    slots = "".join(
        f'<p class="folio">{i} / 4　{lab}</p><div class="slot">{pg}</div>'
        for i, (pg, lab) in enumerate(zip(pages, labels), 1))
    html = f"""<title>昇降式ベッドテーブル 取扱説明書</title>
<style>{B.FONTS}</style>
<style>{B.CSS}{PROOF_CSS}</style>
<div class="proof">
  <header class="proofbar">
    <div>
      <h1>昇降式 折りたたみ サイドテーブル / ベッドテーブル　取扱説明書 兼 組立説明書</h1>
      <p>同梱・入稿用の校正紙です。ブラウザの印刷（等倍・余白なし）でそのまま出力できます。</p>
    </div>
    <div class="spec"><span>A4 4ページ</span><span>片面カラー</span><span>Noto Sans JP</span></div>
  </header>
  {slots}
</div>
{PROOF_JS}"""
    open("manual-artifact.html", "w", encoding="utf-8").write(html)
    print("wrote manual-artifact.html", len(html), "bytes")


if __name__ == "__main__":
    main()
