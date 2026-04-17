"""送信済み注文ID の追跡 - JSON ファイルで管理"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_sent_orders(path: Path) -> set:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("sent_order_ids", []))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"送信済みリストの読み込みに失敗しました ({path}): {e}")
        return set()


def save_sent_order(path: Path, order_id: str) -> None:
    sent = load_sent_orders(path)
    sent.add(order_id)
    path.write_text(
        json.dumps({"sent_order_ids": sorted(sent)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_already_sent(path: Path, order_id: str) -> bool:
    return order_id in load_sent_orders(path)
