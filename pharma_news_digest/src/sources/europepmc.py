"""Europe PMC REST API からの最新論文取得（PubMed の補完）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import requests

from ..models import Article

logger = logging.getLogger(__name__)

_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_TIMEOUT = 20


def _parse_date(raw: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def fetch(query: str, lookback_days: int, limit: int = 8) -> List[Article]:
    """1 クエリ分の新着論文を取得する。失敗時は空リスト。"""
    articles: List[Article] = []
    q = f'({query}) AND (FIRST_PDATE:[NOW-{lookback_days}DAYS TO NOW])'
    try:
        r = requests.get(
            _URL,
            params={
                "query": q,
                "format": "json",
                "pageSize": limit,
                "sort": "P_PDATE_D desc",
                "resultType": "core",
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        results = r.json().get("resultList", {}).get("result", [])
    except Exception as exc:
        logger.warning("Europe PMC 取得失敗 (%s): %s", query, exc)
        return articles

    for item in results:
        title = (item.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        doi = item.get("doi", "")
        pmid = item.get("pmid", "")
        if doi:
            url = f"https://doi.org/{doi}"
        elif pmid:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        else:
            url = f"https://europepmc.org/article/{item.get('source', 'MED')}/{item.get('id', '')}"
        articles.append(
            Article(
                title=title,
                url=url,
                source="Europe PMC",
                section="literature",
                published=_parse_date(item.get("firstPublicationDate", "")),
                summary=(item.get("authorString") or "")[:200],
                publisher=item.get("journalTitle", ""),
                extra={"doi": doi, "query": query},
            )
        )
    return articles


def fetch_many(queries: List[str], lookback_days: int, limit: int = 8) -> List[Article]:
    out: List[Article] = []
    for q in queries:
        out.extend(fetch(q, lookback_days, limit=limit))
    return out
