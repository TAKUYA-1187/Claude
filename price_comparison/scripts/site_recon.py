"""買取商店 (kaitorishouten-co.jp) のサイト構造を調査する使い捨てスクリプト。

GitHub Actions ランナー上で実行し、結果を data/recon/ に書き出す。
- robots.txt を取得して機械アクセスの可否を確認
- トップページのリンク構造を抽出
- JAN コード検索の URL パターンを数種類試す
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

BASE = "https://www.kaitorishouten-co.jp"
OUT = Path(__file__).resolve().parent.parent / "data" / "recon"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) price-research/1.0"}
TEST_JAN = "4902370554359"  # 収集済みの Switch2 ソフト
TEST_KW = "スプラトゥーン"

findings: dict = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "pages": {}}


def fetch(name: str, url: str, save_html: bool = False, max_bytes: int = 120_000):
    time.sleep(1.2)
    try:
        r = requests.get(url, headers=UA, timeout=30)
        info = {
            "url": url,
            "status": r.status_code,
            "final_url": r.url,
            "content_type": r.headers.get("content-type", ""),
            "length": len(r.text),
        }
        if r.ok:
            html = r.text
            # タイトルと、検索結果らしさの手がかり
            m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
            info["title"] = m.group(1).strip()[:200] if m else ""
            info["has_jan"] = TEST_JAN in html
            info["hits_yen"] = len(re.findall(r"[0-9,]+円", html))
            if save_html:
                (OUT / f"{name}.html").write_text(html[:max_bytes], encoding="utf-8")
        findings["pages"][name] = info
        print(name, info.get("status"), info.get("title", "")[:80])
        return r
    except Exception as e:
        findings["pages"][name] = {"url": url, "error": str(e)}
        print(name, "ERROR", e)
        return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    fetch("robots", f"{BASE}/robots.txt", save_html=True)
    r = fetch("home", f"{BASE}/", save_html=True)

    if r is not None and r.ok:
        links = sorted(set(re.findall(r'href="([^"]+)"', r.text)))
        internal = [l for l in links if "kaitorishouten" in l or l.startswith("/")]
        findings["home_links"] = internal[:200]

    # よくある検索パターンを試す
    candidates = {
        "search_wp": f"{BASE}/?s={TEST_JAN}",
        "search_wp_kw": f"{BASE}/?s={TEST_KW}",
        "search_path": f"{BASE}/search?q={TEST_JAN}",
        "item_search": f"{BASE}/item/?s={TEST_JAN}",
        "products": f"{BASE}/products/",
        "price_list": f"{BASE}/price/",
        "kaitori_list": f"{BASE}/kaitori/",
        "sitemap": f"{BASE}/sitemap.xml",
    }
    for name, url in candidates.items():
        fetch(name, url, save_html=name in ("search_wp", "search_wp_kw", "sitemap"))

    (OUT / "findings.json").write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("wrote", OUT / "findings.json")


if __name__ == "__main__":
    main()
