"""お得情報アカウントの投稿から「同じ商品」を見つけ、自分の広告リンクと独自の文章で原稿にする。

    python kao_deals.py posts.txt --ledger kao_ledger_snapshot.json --out out/

posts.txt には X の投稿URLを1行に1つ書く（# で始まる行は無視）。
処理の流れ（1投稿ずつ）:
  1. X 公式の oEmbed で投稿本文とリンクを読む（ログイン不要。投稿の一覧取得はできない）
  2. 短縮リンク・他者の広告リンクをたどり、商品そのものの URL に直す（他者の広告タグは捨てる）
  3. 停止対象（ベッドテーブル等）と台帳の既出を照合する
  4. 自分の広告リンクを作る（楽天は RAKUTEN_AFFILIATE_ID がある時だけ。Amazon は保留）
  5. 公式の商品ページで商品名・価格を読み取る（読み取れた値は「観測値」。公開可否は台帳担当が判定）
  6. 独自テンプレートで原稿を作り、元投稿の文章と似ていないかを検査する

出力: candidates.json（台帳担当に渡す候補）と drafts.md（読みやすい一覧）。
このスクリプトは投稿しない。公開は台帳担当（ChatGPT 側）が正規の接続で行う。
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
from difflib import SequenceMatcher
from pathlib import Path

import requests

JST = dt.timezone(dt.timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
TIMEOUT = 20

# 停止対象（台帳の blocked_publication_scope）。商品名・URLに含まれたら候補にしない
BLOCKED_WORDS = ("ベッドテーブル", "LIFE STAR", "lifestar")

# 他者の広告リンク・短縮リンクで、行き先がクエリに入っているもの
WRAPPER_PARAMS = {
    "hb.afl.rakuten.co.jp": ("pc", "m"),
    "af.moshimo.com": ("url",),
    "px.a8.net": ("a8ejpredirect",),
    "ck.jp.ap.valuecommerce.com": ("vc_url",),
}
# 商品URLから捨てるクエリ（他者の広告タグ・計測）
DROP_PARAMS = re.compile(r"^(tag|linkCode|linkId|ascsubtag|btn_type|btn_ref|ref_?|psc|th|smid|scid|sc2id|icm_.*|utm_.*|l-id|rafcid|s-id|iasid|af_.*|a8|vc_.*)$")

# X の文字数換算（日本語などは2、URLは一律23）
def x_weighted_length(text: str) -> int:
    urls = re.findall(r"https?://\S+", text)
    rest = re.sub(r"https?://\S+", "", text)
    w = sum(1 if (o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247) else 2 for o in map(ord, rest))
    return w + 23 * len(urls)


def now_jst() -> str:
    return dt.datetime.now(JST).isoformat(timespec="seconds")


def read_post(post_url: str) -> dict:
    """oEmbed で投稿の本文・リンク・投稿日を読む。"""
    r = requests.get("https://publish.x.com/oembed", params={"url": post_url, "omit_script": 1}, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()
    raw = d["html"]
    body = raw.split("</p>")[0]
    text = html.unescape(re.sub(r"<[^>]+>", "", body.replace("<br>", "\n")))
    links = [h for h in re.findall(r'href="(https://t\.co/[^"]+)"', body)]
    posted = re.findall(r">([A-Z][a-z]+ \d{1,2}, \d{4})</a></blockquote>", raw)
    return {"author": d.get("author_name"), "author_url": d.get("author_url"), "text": text.strip(), "links": links,
            "posted_on": posted[0] if posted else None}


def resolve(url: str, hops: int = 8) -> str:
    """リダイレクトと広告リンクの包みを外して、最終的な行き先 URL を返す。"""
    for _ in range(hops):
        host = urllib.parse.urlsplit(url).netloc.lower()
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        for key in WRAPPER_PARAMS.get(host, ()):
            if q.get(key):
                url = q[key][0]
                break
        else:
            try:
                # ブラウザ風の名乗りだと t.co は転送ではなく中継ページを返すため、短い名乗りでたどる
                r = requests.get(url, headers={"User-Agent": "kao-deals/1.0"}, timeout=TIMEOUT, allow_redirects=False)
            except requests.RequestException:
                return url
            if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
                url = urllib.parse.urljoin(url, r.headers["Location"])
                continue
            m = re.search(r'http-equiv="refresh"[^>]*url=([^"]+)"', r.text[:3000], re.I)
            if m:
                url = urllib.parse.urljoin(url, html.unescape(m.group(1)))
                continue
            return url
    return url


def unwrap(url: str) -> str:
    """他者の広告リンクの包みを、ネットワークを使わずに外す（何重でも）。"""
    for _ in range(5):
        parts = urllib.parse.urlsplit(url)
        q = urllib.parse.parse_qs(parts.query)
        keys = WRAPPER_PARAMS.get(parts.netloc.lower(), ())
        inner = next((q[k][0] for k in keys if q.get(k)), None)
        if not inner:
            return url
        url = inner
    return url


def canonical(url: str) -> dict:
    """店ごとに商品IDを取り出し、他者の広告タグを外した URL にする。"""
    url = unwrap(url)
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.lower()
    q = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not DROP_PARAMS.match(k)]
    clean = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(q), ""))
    if "amazon.co.jp" in host:
        m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", parts.path)
        if m:
            return {"shop": "amazon", "product_id": m.group(1), "url": f"https://www.amazon.co.jp/dp/{m.group(1)}"}
    if host == "item.rakuten.co.jp":
        m = re.match(r"/([^/]+)/([^/]+)", parts.path)
        if m:
            return {"shop": "rakuten", "product_id": f"{m.group(1)}/{m.group(2)}", "url": f"https://item.rakuten.co.jp/{m.group(1)}/{m.group(2)}/"}
    if host.endswith("rakuten.co.jp"):
        return {"shop": "rakuten_campaign", "product_id": parts.path.strip("/"), "url": clean}
    if host == "store.shopping.yahoo.co.jp":
        m = re.match(r"/([^/]+)/([^/.]+)\.html", parts.path)
        if m:
            return {"shop": "yahoo", "product_id": f"{m.group(1)}/{m.group(2)}", "url": f"https://store.shopping.yahoo.co.jp/{m.group(1)}/{m.group(2)}.html"}
    if host in ("x.com", "twitter.com", "pic.twitter.com", "pic.x.com"):
        return {"shop": "x", "product_id": None, "url": clean}
    return {"shop": "other", "product_id": None, "url": clean}


def own_affiliate(prod: dict) -> dict:
    """自分の広告リンクを作る。作れない時は理由を返す（他者の広告IDは使わない）。"""
    if prod["shop"] in ("rakuten", "rakuten_campaign"):
        aid = os.getenv("RAKUTEN_AFFILIATE_ID", "").strip()
        if not aid:
            return {"url": None, "status": "楽天アフィリエイトID未設定（RAKUTEN_AFFILIATE_ID）"}
        enc = urllib.parse.quote(prod["url"], safe="")
        link = f"https://hb.afl.rakuten.co.jp/hgc/{aid}/?pc={enc}&m={enc}"
        dest = canonical(resolve(link))
        ok = dest.get("product_id") == prod.get("product_id")
        return {"url": link, "status": "遷移先一致" if ok else f"遷移先不一致（{dest.get('url')}）", "redirect_verified": ok}
    if prod["shop"] == "amazon":
        return {"url": None, "status": "Amazon広告連携は保留（台帳ルール）"}
    return {"url": None, "status": "広告リンク対象外（公式URLを使う）"}


def observe_page(prod: dict) -> dict:
    """公式の商品ページから商品名と表示価格を読む。読めなければ null。"""
    if prod["shop"] not in ("amazon", "rakuten", "yahoo"):
        return {"title": None, "price": None}
    try:
        r = requests.get(prod["url"], headers=UA, timeout=TIMEOUT)
    except requests.RequestException as e:
        return {"title": None, "price": None, "error": type(e).__name__}
    if r.encoding in (None, "ISO-8859-1"):
        r.encoding = r.apparent_encoding
    s = r.text
    title = None
    for pat in (r'id="productTitle"[^>]*>\s*([^<]+)', r'<meta property="og:title" content="([^"]+)"', r"<title>([^<]+)</title>"):
        m = re.search(pat, s)
        if m:
            title = html.unescape(m.group(1)).strip()
            break
    price = None
    for pat in (r'"priceAmount":\s*([\d.]+)', r'class="a-price-whole">([\d,]+)', r'itemprop="price" content="([\d.]+)"', r'"price":\s*"?([\d,]+)'):
        m = re.search(pat, s)
        if m:
            price = int(float(m.group(1).replace(",", "")))
            break
    return {"title": title, "price": price, "http": r.status_code}


def ledger_texts(path: str | None) -> str:
    if not path:
        return ""
    return json.dumps(json.load(open(path, encoding="utf-8")), ensure_ascii=False)


def similarity(a: str, b: str) -> dict:
    """原稿と元投稿の似かたを測る。長い一致（12文字以上）があれば書き直しが必要。"""
    a2, b2 = re.sub(r"https?://\S+|\s", "", a), re.sub(r"https?://\S+|\s", "", b)
    m = SequenceMatcher(None, a2, b2).find_longest_match(0, len(a2), 0, len(b2))
    return {"ratio": round(SequenceMatcher(None, a2, b2).ratio(), 2), "longest_common": a2[m.a:m.a + m.size], "ok": m.size < 12}


def draft(title: str, price: int, link: str, pr: bool) -> str:
    """独自テンプレート（価格を先頭→商品→確認事項→リンク）。元投稿の文は使わない。"""
    name = re.sub(r"\s+", " ", title)
    name = name[:40] + ("…" if len(name) > 40 else "")
    lines = [("PR｜" if pr else "") + f"{price:,}円で販売中", name, "・価格・送料・ポイントは購入前に商品ページで確認を", link]
    return "\n".join(lines)


def process(post_url: str, ledger: str) -> list[dict]:
    observed = now_jst()
    post = read_post(post_url)
    out = []
    for short in post["links"]:
        prod = canonical(resolve(short))
        if prod["shop"] in ("x", "other") and not prod["product_id"]:
            continue
        cid = f"claude-{observed[:10].replace('-', '')}-{prod['shop']}-{re.sub(r'[^A-Za-z0-9]', '-', prod['product_id'] or 'campaign')[:40]}"
        rec = {
            "candidate_id": cid, "producer": "claude", "observed_at_jst": observed,
            "source_post_url": post_url, "source_author": post["author"], "source_posted_at": post["posted_on"],
            "discovery_url": short, "category": None, "official_url": prod["url"], "seller": prod["shop"],
            "JAN": None, "ASIN": prod["product_id"] if prod["shop"] == "amazon" else None, "model": None,
            "dedup_key": f"{prod['shop']}|{prod['product_id']}",
            "content_type": "commerce_ad", "price_including_tax": None, "shipping": None, "point_amount": None,
            "stock": None, "expires_at": None, "publication_gate": "verifying", "notes": [],
        }
        blob = f"{post['text']} {prod['url']}"
        if any(w.lower() in blob.lower() for w in BLOCKED_WORDS):
            rec.update(publication_gate="blocked", notes=["停止対象（ベッドテーブル関連）"])
            out.append(rec)
            continue
        if prod["product_id"] and prod["product_id"] in ledger:
            rec["notes"].append("台帳に同じ商品IDあり：既出・同条件かを台帳担当が判定")
            rec["publication_gate"] = "hold_possible_duplicate"
        aff = own_affiliate(prod)
        rec["own_affiliate_url"] = aff["url"]
        rec["affiliate_status"] = aff["status"]
        rec["affiliate_link_owner_verified"] = aff.get("redirect_verified")
        rec["pr_required"] = bool(aff["url"])
        page = observe_page(prod)
        rec["product_name"] = page.get("title")
        rec["page_price_observed"] = page.get("price")
        rec["missing_fields"] = [k for k in ("price_including_tax", "shipping", "point_amount", "stock", "expires_at") if rec.get(k) is None]
        if page.get("title") and page.get("price") and aff["url"]:
            text = draft(page["title"], page["price"], aff["url"], pr=True)
            sim = similarity(text, post["text"])
            rec.update(draft_text=text, x_weighted_length=x_weighted_length(text), originality=sim)
            if not sim["ok"]:
                rec["notes"].append("元投稿と長い一致あり：書き直しが必要")
        else:
            rec["draft_text"] = None
            rec["notes"].append("原稿なし：商品名・価格・自分の広告リンクのどれかが未確定")
        out.append(rec)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("posts", help="X の投稿URLを1行1件で書いたファイル")
    ap.add_argument("--ledger", help="台帳の抜粋 JSON（既出照合に使う）")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    ledger = ledger_texts(a.ledger)
    urls = [l.strip() for l in open(a.posts, encoding="utf-8") if l.strip() and not l.startswith("#")]
    results, errors = [], []
    for u in urls:
        try:
            results += process(u, ledger)
        except Exception as e:  # 1件の失敗で全体を止めない
            errors.append({"source_post_url": u, "tried_at_jst": now_jst(), "error": f"{type(e).__name__}: {e}"[:200]})
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "candidates.json").write_text(json.dumps({"candidates": results, "errors": errors}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["| 元投稿 | 商品 | 自分の広告リンク | 観測価格 | 状態 |", "|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['source_post_url']} | {r.get('product_name') or r['official_url']} | {r.get('affiliate_status', '-')} | {r.get('page_price_observed')} | {r['publication_gate']} |")
    for r in results:
        if r.get("draft_text"):
            md += ["", f"### {r['candidate_id']}（X換算 {r['x_weighted_length']}/280・元投稿との一致 {r['originality']['ratio']}）", "```", r["draft_text"], "```"]
    (outdir / "drafts.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(results)} candidates, {len(errors)} errors -> {outdir}")


if __name__ == "__main__":
    sys.exit(main())
