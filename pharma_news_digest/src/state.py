"""配信済み記事 ID の永続化。

毎日実行のため、前日までに配信した記事・論文を再掲しないよう
既読 ID を JSON で保持する。GitHub Actions 側でコミットして保存する。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "state" / "seen_ids.json"
_RETENTION_DAYS = 45


def load(path: Path = _DEFAULT_PATH) -> Dict[str, str]:
    """{uid: ISO日時} の辞書を返す。"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("既読状態の読み込み失敗: %s", exc)
        return {}


def save(seen: Dict[str, str], path: Path = _DEFAULT_PATH) -> None:
    # 古い ID を間引いてファイルの肥大化を防ぐ
    cutoff = datetime.now(timezone.utc).timestamp() - _RETENTION_DAYS * 86400
    pruned = {}
    for uid, ts in seen.items():
        try:
            if datetime.fromisoformat(ts).timestamp() >= cutoff:
                pruned[uid] = ts
        except ValueError:
            pruned[uid] = ts
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pruned, ensure_ascii=False, indent=0), encoding="utf-8")


def mark(seen: Dict[str, str], uids: Iterable[str]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for uid in uids:
        seen[uid] = now
