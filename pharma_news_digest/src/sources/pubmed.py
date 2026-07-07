"""PubMed E-utilities からの最新論文取得。

esearch で直近 N 日の PMID を取得し、esummary で書誌情報を得る。
NCBI_API_KEY があればレート制限が緩和される（任意）。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import requests

from ..models import Article

logger = logging.getLogger(__name__)

_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_TIMEOUT = 20


def _params(api_key: str, **kw) -> dict:
    p = {"db": "pubmed", "retmode": "json", **kw}
    if api_key:
        p["api_key"] = api_key
    return p


def _parse_pubdate(raw: str) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%Y %b %d", "%Y %b", "%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def fetch(query: str, lookback_days: int, api_key: str = "", limit: int = 8) -> List[Article]:
    """1 クエリ分の新着論文を取得する。失敗時は空リスト。"""
    articles: List[Article] = []
    try:
        term = f"{query} AND (\"last {lookback_days} days\"[dp])"
        r = requests.get(
            f"{_BASE}/esearch.fcgi",
            params=_params(api_key, term=term, retmax=limit, sort="date"),
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return articles

        r2 = requests.get(
            f"{_BASE}/esummary.fcgi",
            params=_params(api_key, id=",".join(ids)),
            timeout=_TIMEOUT,
        )
        r2.raise_for_status()
        result = r2.json().get("result", {})
    except Exception as exc:
        logger.warning("PubMed 取得失敗 (%s): %s", query, exc)
        return articles

    for pmid in result.get("uids", []):
        item = result.get(pmid, {})
        title = (item.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        authors = item.get("authors") or []
        author_str = ", ".join(a.get("name", "") for a in authors[:3])
        if len(authors) > 3:
            author_str += " ら"
        doi = ""
        for aid in item.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
        articles.append(
            Article(
                title=title,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                source="PubMed",
                section="literature",
                published=_parse_pubdate(item.get("pubdate", "")),
                summary=author_str,
                publisher=item.get("fulljournalname") or item.get("source", ""),
                extra={"doi": doi, "query": query},
            )
        )
    return articles


def fetch_many(queries: List[str], lookback_days: int, api_key: str = "", limit: int = 8) -> List[Article]:
    out: List[Article] = []
    for q in queries:
        out.extend(fetch(q, lookback_days, api_key=api_key, limit=limit))
    return out
