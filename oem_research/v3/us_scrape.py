# -*- coding: utf-8 -*-
"""Amazon.com (US) New Releases lists and product pages, for spotting products launched
this year that are not yet sold in Japan."""
import html
import os
import re

import scrape as S

UA_LANG = "en-US,en;q=0.9"
CACHE = S.CACHE


def _get(url, name):
    return S._fetch(url, os.path.join(CACHE, "us", name), accept_lang=UA_LANG)


def new_releases(path, page=1):
    """path like 'home-garden' or 'home-garden/1063306'. Returns (items, child category paths)."""
    url = f"https://www.amazon.com/gp/new-releases/{path}/?pg={page}"
    s = _get(url, "nr_" + path.replace("/", "_") + f"_{page}.html")
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    cat = html.unescape(title.group(1)).split(" in ")[-1].strip() if title else path
    items = []
    for blk in s.split('id="p13n-asin-index-')[1:]:
        asin = re.search(r'data-asin="([A-Z0-9]{10})"', blk)
        rank = re.search(r'zg-bdg-text">#(\d+)', blk)
        name = re.search(r'line-clamp-\d[^"]*">([^<]+)<', blk)
        price = re.search(r'p13n-sc-price[^"]*">\$([\d,]+\.?\d*)', blk)
        rv = re.search(r'aria-label="([\d.]+) out of 5 stars, ([\d,]+) ratings?"', blk)
        if asin:
            items.append(dict(asin=asin.group(1), rank=int(rank.group(1)) if rank else None,
                              title=html.unescape(name.group(1)).strip() if name else "",
                              usd=float(price.group(1).replace(",", "")) if price else None,
                              rating=float(rv.group(1)) if rv else None,
                              reviews=int(rv.group(2).replace(",", "")) if rv else 0,
                              category=cat, url=f"https://www.amazon.com/dp/{asin.group(1)}"))
    kids = sorted(set(re.findall(r'href="/gp/new-releases/([a-z\-]+/\d+)/ref=zg_bsnr_nav', s)))
    return items, kids, cat


def product(asin):
    """Date first available, BSR, weight/dimensions, brand from the US product page."""
    s = _get(f"https://www.amazon.com/dp/{asin}", f"dp_{asin}.html")
    flat = re.sub(r"\s+", " ", html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", s, flags=re.S)))

    def grab(label, n=60):
        i = flat.find(label)
        return flat[i + len(label):i + len(label) + n].strip(" :‎‎") if i >= 0 else ""
    d = dict(asin=asin, ok="productTitle" in s)
    # the 2026 page layout dropped "Date First Available"; the ASIN series (B0G/B0H = late 2025-2026) is used instead
    d["date"] = grab("Date First Available", 25)
    d["dims"] = (grab("Item Dimensions D x W x H", 40) or grab("Product Dimensions", 40)).split(" About")[0]
    d["weight"] = grab("Item Weight", 16).split(" Item")[0]
    d["brand"] = (grab("Brand Name", 40) or grab("Brand", 30)).split(" Recommended")[0].split(" Color")[0]
    m = re.search(r"Best Sellers Rank\s*:?\s*(#[\d,]+ in [^(#]+)", flat)
    d["bsr"] = m.group(1).strip() if m else ""
    m = re.search(r"([\d,]+K?\+?) bought in past month", flat)
    d["bought"] = m.group(1) if m else ""
    m = re.search(r'id="productTitle"[^>]*>(.*?)</span>', s, re.S)
    d["title"] = html.unescape(m.group(1)).strip() if m else ""
    return d
