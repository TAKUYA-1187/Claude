# -*- coding: utf-8 -*-
"""Fetch and parse Amazon.co.jp search/product pages and 1688 market pages.

Pages are cached under CACHE (default: ./cache) so that re-runs do not hit the
sites again. Requests are spaced out (DELAY seconds) to stay polite.
"""
import html
import os
import random
import re
import subprocess
import time
from urllib.parse import quote

CACHE = os.environ.get("OEM_CACHE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"))
DELAY = float(os.environ.get("OEM_DELAY", "2.5"))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
_last = [0.0]
JAR = os.path.join(CACHE, "amazon_cookies.txt")


def session_init(zipcode="100-0001"):
    """Give the Amazon session a Japanese delivery address (otherwise items that
    cannot ship abroad are hidden) and JPY prices."""
    os.makedirs(CACHE, exist_ok=True)
    base = ["curl", "-s", "--compressed", "--max-time", "30", "-A", UA, "-c", JAR, "-b", JAR,
            "-H", "Accept-Language: ja-JP,ja;q=0.9"]
    s = subprocess.run(base + ["https://www.amazon.co.jp/s?k=%E6%A3%9A"], capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r"ajaxHeaders&quot;:\{&quot;anti-csrftoken-a2z&quot;:&quot;([^&]+)", s)
    t1 = m.group(1) if m else ""
    a = subprocess.run(base + ["-H", f"anti-csrftoken-a2z: {t1}",
                               "https://www.amazon.co.jp/portal-migration/hz/glow/get-rendered-address-selections"
                               "?deviceType=desktop&pageType=Search&storeContext=NoStoreName&actionSource=desktop-modal"],
                       capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r'CSRF_TOKEN : "([^"]+)"', a)
    t2 = m.group(1) if m else ""
    body = ('{"locationType":"LOCATION_INPUT","zipCode":"%s","deviceType":"web","storeContext":"generic",'
            '"pageType":"Search","actionSource":"glow"}' % zipcode)
    r = subprocess.run(base + ["-H", "Content-Type: application/json", "-H", f"anti-csrftoken-a2z: {t2}",
                               "-H", "X-Requested-With: XMLHttpRequest", "-X", "POST", "--data", body,
                               "https://www.amazon.co.jp/portal-migration/hz/glow/address-change?actionSource=glow"],
                       capture_output=True).stdout.decode("utf-8", "ignore")
    lines = [ln for ln in open(JAR, encoding="utf-8").read().splitlines() if "i18n-prefs" not in ln]
    lines.append(".amazon.co.jp\tTRUE\t/\tFALSE\t2082787201\ti18n-prefs\tJPY")
    open(JAR, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return '"countryCode":"JP"' in r


def _fetch(url, path, accept_lang="ja-JP,ja;q=0.9", tries=3):
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return open(path, encoding="utf-8", errors="ignore").read()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = ""
    for i in range(tries):
        wait = DELAY + random.uniform(0, 1.5) - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        cookies = ["-b", JAR, "-c", JAR] if "amazon" in url and os.path.exists(JAR) else []
        r = subprocess.run(["curl", "-s", "-L", "--compressed", "--max-time", "30", "-A", UA,
                            "-H", f"Accept-Language: {accept_lang}"] + cookies + [url],
                           capture_output=True)
        body = r.stdout.decode("utf-8", errors="ignore")
        blocked = ("captcha" in body.lower() and "amazon" in url and "s-search-result" not in body
                   and "productTitle" not in body) or "punish" in body[:3000]
        if len(body) > 5000 and not blocked:
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            return body
        time.sleep(10 * (i + 1))
    return body


def text(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def _num(s):
    s = s.replace(",", "")
    m = re.search(r"[\d.]+", s)
    return float(m.group(0)) if m else None


def _badge(s):
    m = re.search(r"過去1か月で([\d,.]+)(万)?点以上購入", s)
    if not m:
        return 0
    v = float(m.group(1).replace(",", ""))
    return int(v * 10000) if m.group(2) else int(v)


# ---------------------------------------------------------------------------
def amazon_search(kw, page=1):
    url = "https://www.amazon.co.jp/s?k=" + quote(kw) + (f"&page={page}" if page > 1 else "")
    path = os.path.join(CACHE, "amz_s", f"{quote(kw, safe='')}_{page}.html")
    s = _fetch(url, path)
    items = []
    parts = re.split(r'(?=<div[^>]+data-asin="[A-Z0-9]{10}"[^>]+data-component-type="s-search-result")', s)
    for p in parts[1:]:
        asin = re.search(r'data-asin="([A-Z0-9]{10})"', p).group(1)
        p = p[:60000]
        title = ""
        m = re.search(r"<h2[^>]*>(.*?)</h2>", p, re.S)
        if m:
            title = text(m.group(1))
        price = None
        m = re.search(r'class="a-price"[^>]*>.*?<span class="a-offscreen">([^<]+)</span>', p, re.S)
        if m:
            price = _num(m.group(1))
        rating = None
        m = re.search(r"5つ星のうち([\d.]+)", p)
        if m:
            rating = float(m.group(1))
        reviews = 0
        m = re.search(r'aria-label="([\d,]+)件の評価', p) or re.search(r'aria-label="([\d,]+) 件の評価', p)
        if not m:
            m = re.search(r'<span class="a-size-base s-underline-text">([\d,]+)</span>', p) or \
                re.search(r'\(([\d,.]+)(千|万)?\)</span>', p)
        if m:
            reviews = int(float(m.group(1).replace(",", "")))
        sponsored = ("スポンサー" in p[:20000]) or ("sp_atf" in p) or ("Sponsored" in p[:20000])
        items.append(dict(asin=asin, title=title, price=price, rating=rating, reviews=reviews,
                          bought=_badge(p), sponsored=sponsored))
    # de-duplicate (sponsored + organic copies)
    seen, out = set(), []
    for it in items:
        if it["asin"] in seen:
            continue
        seen.add(it["asin"])
        out.append(it)
    return out


def amazon_detail(asin):
    url = f"https://www.amazon.co.jp/dp/{asin}"
    path = os.path.join(CACHE, "amz_d", f"{asin}.html")
    s = _fetch(url, path)
    d = dict(asin=asin, ok="productTitle" in s)
    m = re.search(r'id="productTitle"[^>]*>(.*?)</span>', s, re.S)
    d["title"] = text(m.group(1)) if m else ""
    price = None
    for anchor in ("corePriceDisplay_desktop_feature_div", "corePrice_feature_div", "apex_desktop"):
        i = s.find(anchor)
        if i >= 0:
            m = re.search(r'a-offscreen">\s*￥\s*([\d,]+)', s[i:i + 8000])
            if m:
                price = _num(m.group(1))
                break
    d["price"] = price
    m = re.search(r'id="acrCustomerReviewText"[^>]*>([^<]+)', s)
    d["reviews"] = int(_num(m.group(1))) if m else 0
    m = re.search(r"5つ星のうち([\d.]+)", s)
    d["rating"] = float(m.group(1)) if m else None
    d["bought"] = _badge(s)
    flat = text(s[:2_000_000])

    def grab(label, n=80):
        i = flat.find(label)
        return flat[i + len(label):i + len(label) + n].strip() if i >= 0 else ""
    d["dims"] = grab("商品の寸法") or grab("梱包サイズ")
    d["pkg"] = grab("梱包サイズ", 40)
    d["weight"] = grab("商品の重量", 30) or grab("重量", 30)
    d["brand"] = grab("ブランド", 30)
    d["maker"] = grab("メーカー名", 30) or grab("メーカー", 30)
    d["since"] = grab("Amazon.co.jp での取り扱い開始日", 20) or grab("取り扱い開始日", 20)
    m = re.search(r"Amazon 売れ筋ランキング(.{0,400}?)(?:ASIN|カスタマーレビュー|お客様のご意見|製品情報|$)", flat)
    d["bsr"] = m.group(1).strip(" :-") if m else ""
    m = re.search(r"販売元\s*(\S{2,40})", flat)
    d["seller"] = m.group(1) if m else ""
    # star histogram and the reviews shown on the product page
    hist = {}
    for k, n in (("oneStar", 1), ("twoStar", 2), ("threeStar", 3), ("fourStar", 4), ("fiveStar", 5)):
        m = re.search(k + r'(?:\\&quot;|&quot;|")\s*:\s*(\d+)', s)
        if m:
            hist[n] = int(m.group(1))
    d["hist"] = hist
    revs = []
    for blk in re.split(r'data-hook="review" class=', s)[1:]:
        blk = blk[:30000]
        m = re.search(r"a-star-(\d)|5つ星のうち([\d.]+)|星5つ中([\d.]+)つ", blk)
        k = blk.find('data-hook="reviewText"')
        title = re.search(r'<h5[^>]*>(.*?)</h5>', blk, re.S)
        if m and k >= 0:
            body = blk[k:k + 8000]
            body = re.split(r"続きを読む|表示を減らす|data-hook=\"reviewExpandButtonContainer\"", body)[0]
            t = text(re.sub(r"^[^>]*>", "", body))
            t = re.sub(r"Brief content visible, double tap to read full content\.|Full content visible, double tap to read brief content\.", "", t).strip()
            t = re.sub(r"\s*<\w.*$", "", t).strip()
            tt = text(title.group(1)) if title else ""
            if t:
                revs.append((float(next(g for g in m.groups() if g)), (tt + "｜" if tt else "") + t[:500]))
    d["reviews_txt"] = revs[:12]
    return d


# ---------------------------------------------------------------------------
def m1688_market(kw_cn):
    h = "".join("%02X" % b for b in kw_cn.encode("gbk"))
    url = f"https://www.1688.com/market/-{h}.html"
    path = os.path.join(CACHE, "1688", f"{h}.html")
    s = _fetch(url, path, accept_lang="zh-CN,zh;q=0.9")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    t = text(t)
    offers = []
    for m in re.finditer(r"([^¥]{10,80})¥\s*([\d.]+)\s*月销\s*([\d.]+)(万)?\s*\S*", t):
        sold = float(m.group(3)) * (10000 if m.group(4) else 1)
        offers.append(dict(title=m.group(1)[-60:].strip(), price=float(m.group(2)), sold=int(sold)))
    return offers
