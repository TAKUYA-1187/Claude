"""通知済みASINの記録 - 同じ値下がりを繰り返し通知しないための状態管理。

TTL 内でも「前回通知よりさらに5%以上安くなった」場合は再通知する
（刈り取りでは更なる下落は買い増しシグナルのため）。
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

RENOTIFY_DROP_RATIO = 0.95  # 前回通知価格の95%未満なら再通知


class AlertState:
    def __init__(self, path: Path, ttl_hours: int):
        self.path = path
        self.ttl_seconds = ttl_hours * 3600
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                log.warning("状態ファイルの読み込みに失敗、初期化します: %s", e)
                self._data = {}
        self._prune()

    def _prune(self) -> None:
        now = time.time()
        self._data = {
            asin: rec
            for asin, rec in self._data.items()
            if now - rec.get("ts", 0) < self.ttl_seconds
        }

    def should_alert(self, asin: str, current_price: int) -> bool:
        rec = self._data.get(asin)
        if rec is None:
            return True
        return current_price < rec.get("price", 0) * RENOTIFY_DROP_RATIO

    def mark_alerted(self, asin: str, current_price: int) -> None:
        self._data[asin] = {"price": current_price, "ts": time.time()}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
