"""腎臓領域 医療・製薬ニュース日次ダイジェスト メインスクリプト。

Google ニュース／PubMed／Europe PMC から担当領域（ファビハルタ／IgA腎症）
関連の記事・論文を収集し、HTML メールとして毎朝配信する。

使い方:
    python -m src.main               # 収集して配信（既読は再掲しない）
    python -m src.main --dry-run     # 送信せず HTML を out.html に書き出す
    python -m src.main --no-state    # 既読管理を使わず全件対象にする
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import digest, render, state
from .config import load_config
from .mailer import send

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="腎臓領域ニュース日次ダイジェスト")
    parser.add_argument("--dry-run", action="store_true", help="送信せず HTML を書き出す")
    parser.add_argument("--no-state", action="store_true", help="既読管理を無効化")
    parser.add_argument("--out", default="out.html", help="--dry-run 時の出力先")
    args = parser.parse_args(argv)

    cfg = load_config()
    seen = {} if args.no_state else state.load()

    grouped = digest.build(cfg, seen)
    total = sum(len(v) for v in grouped.values())

    html_body = render.render_html(grouped)
    text_body = render.render_text(grouped)
    subject = render.subject()

    if args.dry_run:
        Path(args.out).write_text(html_body, encoding="utf-8")
        logger.info("dry-run: %s に書き出しました（新規 %d 件）", args.out, total)
        print(text_body)
        return 0

    if total == 0:
        logger.info("新規記事がないため送信しません。")
        # 新規が無くても状況が分かるよう、送信自体は行う設計も可能だが既定はスキップ
        return 0

    try:
        send(cfg, subject, html_body, text_body)
    except RuntimeError as exc:
        logger.error("%s", exc)
        # メール未設定でも HTML を残してワークフローの artifact で確認できるようにする
        Path(args.out).write_text(html_body, encoding="utf-8")
        return 2

    # 配信できたものを既読として記録
    if not args.no_state:
        uids = [a.uid for items in grouped.values() for a in items]
        state.mark(seen, uids)
        state.save(seen)

    return 0


if __name__ == "__main__":
    sys.exit(main())
