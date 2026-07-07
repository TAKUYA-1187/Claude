"""Google ニュース RSS からの記事取得。

公式 RSS 検索エンドポイントを使う（API キー不要）。RSS は素朴な XML のため、
外部依存を避けて標準ライブラリ（requests + ElementTree）で解析する。
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import requests

from ..models import Article

logger = logging.getLogger(__name__)

_JA = "hl=ja&gl=JP&ceid=JP:ja"
_EN = "hl=en-US&gl=US&ceid=US:en"
_TIMEOUT = 20
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PharmaNewsDigest/1.0)"}


def _feed_url(query: str, lang: str) -> str:
    locale = _JA if lang == "ja" else _EN
    # 直近のニュースに絞るため when:2d を付与
    q = quote_plus(f"{query} when:2d")
    return f"https://news.google.com/rss/search?q={q}&{locale}"


def _parse_published(text: str) -> datetime | None:
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _clean_summary(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:280]


def fetch(query: str, section: str, lang: str = "ja", limit: int = 10) -> List[Article]:
    """1 クエリ分の記事を取得する。失敗しても例外を投げず空リストを返す。"""
    url = _feed_url(query, lang)
    articles: List[Article] = []
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("Google ニュース取得失敗 (%s): %s", query, exc)
        return articles

    for item in list(root.iterfind(".//item"))[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        source_el = item.find("source")
        publisher = (source_el.text or "").strip() if source_el is not None else ""
        articles.append(
            Article(
                title=title,
                url=link,
                source="Google ニュース",
                section=section,
                published=_parse_published(item.findtext("pubDate") or ""),
                summary=_clean_summary(item.findtext("description") or ""),
                publisher=publisher,
            )
        )
    return articles


def fetch_many(queries: List[str], section: str, lang: str = "ja", limit: int = 10) -> List[Article]:
    out: List[Article] = []
    for q in queries:
        out.extend(fetch(q, section, lang=lang, limit=limit))
    return out
