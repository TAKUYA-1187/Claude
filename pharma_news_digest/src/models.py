"""ダイジェストで扱う記事・論文の共通データモデル。"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _normalize_url(url: str) -> str:
    """トラッキングパラメータを除いた比較用 URL を返す。"""
    url = url.strip()
    # Google ニュースのリダイレクトや utm_* を除去して重複判定を安定させる
    url = re.sub(r"[?&](utm_[^=]+|oc|hl|gl|ceid)=[^&]*", "", url)
    return url.rstrip("/?&").lower()


@dataclass
class Article:
    """ニュース記事または論文 1 件を表す。"""

    title: str
    url: str
    source: str  # 例: "Google ニュース", "PubMed"
    section: str  # digest.SECTIONS のキー
    published: Optional[datetime] = None
    summary: str = ""
    publisher: str = ""  # 配信元メディア名 / ジャーナル名
    extra: dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        """重複排除に使う安定 ID。DOI > 正規化 URL > タイトルの順で決める。"""
        doi = self.extra.get("doi")
        if doi:
            base = f"doi:{doi.lower()}"
        elif self.url:
            base = f"url:{_normalize_url(self.url)}"
        else:
            base = "title:" + re.sub(r"\s+", " ", self.title.strip().lower())
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

    @property
    def published_utc(self) -> Optional[datetime]:
        if self.published is None:
            return None
        if self.published.tzinfo is None:
            return self.published.replace(tzinfo=timezone.utc)
        return self.published.astimezone(timezone.utc)
