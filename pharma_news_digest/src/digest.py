"""各ソースからの記事を集約・重複排除・分類し、ダイジェストを組み立てる。"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from . import keywords as kw
from .config import Config
from .models import Article
from .sources import europepmc, google_news, pubmed

logger = logging.getLogger(__name__)

# セクション定義（表示順・見出し）
SECTIONS = [
    ("fabhalta", "🎯 ファビハルタ／IgA腎症（自社・注目領域）"),
    ("competitor", "🧬 腎臓・競合パイプライン"),
    ("industry", "🏛 国内 医療・製薬業界ニュース（薬価・規制・情報誌）"),
    ("global", "🌏 世界のアップデート（グローバル承認・規制・企業動向）"),
    ("literature", "📄 最新論文（PubMed／Europe PMC）"),
]
SECTION_TITLES = dict(SECTIONS)


def _within(article: Article, since: datetime) -> bool:
    """発行日時が since 以降、または日時不明なら通す。"""
    dt = article.published_utc
    if dt is None:
        return True
    return dt >= since


def collect(cfg: Config) -> List[Article]:
    """全ソースから記事を取得する。"""
    articles: List[Article] = []
    per = cfg.max_items_per_section

    # --- ニュース（Google ニュース RSS） ---
    articles += google_news.fetch_many(
        kw.FABHALTA_TERMS + kw.IGAN_TERMS, "fabhalta", lang="ja", limit=8
    )
    articles += google_news.fetch_many(
        kw.COMPETITOR_TERMS, "competitor", lang="ja", limit=5
    )
    articles += google_news.fetch_many(
        kw.COMPANY_TERMS + kw.INDUSTRY_JP_TERMS + kw.TRADE_PRESS_TERMS,
        "industry",
        lang="ja",
        limit=5,
    )
    articles += google_news.fetch_many(
        kw.GLOBAL_TERMS, "global", lang="en", limit=5
    )

    # --- 論文（PubMed + Europe PMC） ---
    articles += pubmed.fetch_many(
        kw.LITERATURE_QUERIES, cfg.paper_lookback_days, api_key=cfg.ncbi_api_key, limit=6
    )
    articles += europepmc.fetch_many(
        kw.LITERATURE_QUERIES, cfg.paper_lookback_days, limit=6
    )

    logger.info("取得記事数（重複排除前）: %d", len(articles))
    return articles


def build(cfg: Config, seen: Dict[str, str]) -> Dict[str, List[Article]]:
    """セクションごとに、新規かつ期間内の記事を整理して返す。"""
    now = datetime.now(timezone.utc)
    news_since = now - timedelta(hours=cfg.news_lookback_hours)
    paper_since = now - timedelta(days=cfg.paper_lookback_days)

    raw = collect(cfg)

    grouped: Dict[str, List[Article]] = {key: [] for key, _ in SECTIONS}
    dedupe: set[str] = set()

    for art in raw:
        if art.uid in seen or art.uid in dedupe:
            continue
        since = paper_since if art.section == "literature" else news_since
        if not _within(art, since):
            continue
        if art.section not in grouped:
            continue
        dedupe.add(art.uid)
        grouped[art.section].append(art)

    # 各セクションを新しい順に並べ、上限で切る
    for key in grouped:
        grouped[key].sort(
            key=lambda a: a.published_utc or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        grouped[key] = grouped[key][: cfg.max_items_per_section]

    total = sum(len(v) for v in grouped.values())
    logger.info("新規記事数（配信対象）: %d", total)
    return grouped
