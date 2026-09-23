"""価格比較 & 利益商品抽出のオーケストレーター。

使い方:
  python -m src.main                          # 買取ルート + Amazon販売ルートの両方
  python -m src.main --mode buyback           # 買取ルートのみ (従来動作)
  python -m src.main --mode amazon            # Amazon販売ルートのみ
  python -m src.main --collect                # EC からの JAN 収集も実行して母集団に加える
  python -m src.main --limit 10               # 先頭10件だけ処理 (テスト用)

母集団 (JANコードの集合):
  - 買取スキャナーの全データCSV (data/input/*.csv)
  - --collect 指定時は Yahoo!ショッピング / 楽天ブックス / Amazon から
    売れ筋商品の JAN を収集してマージ (data/collected/collected_latest.csv)
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import config
from .csv_loader import last_stats as csv_loader_stats
from .csv_loader import load_all
from .jan_collector import collect_all, save_collected
from .numbers_convert import convert_all as convert_numbers
from .onedrive_fetcher import fetch_folder
from .profit_calculator import (
    AmazonProfitRow,
    PriceRow,
    ProfitRow,
    compute,
    compute_amazon,
    is_amazon_profitable,
    is_profitable,
)
from .rakuten_client import RakutenClient, credentials_problem
from .yahoo_client import YahooClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("main")


@dataclass
class Candidate:
    """利益判定の対象となる1商品 (JAN単位)。"""

    jan: str
    name: str = ""
    category: str = ""
    buy_price: Optional[float] = None  # 買取店の買取価格 (CSV由来)
    buy_shop: str = ""
    seed_prices: dict = field(default_factory=dict)  # 収集時に見えた価格 {source: price}


def build_clients():
    rakuten = None
    yahoo = None
    amazon = None
    rakuten_problem = credentials_problem(config.rakuten_app_id, config.rakuten_access_key)
    if rakuten_problem:
        log.error("楽天APIをスキップ: %s", rakuten_problem)
        _annotate("warning", "楽天APIの設定が必要です", rakuten_problem)
    elif config.rakuten_app_id:
        rakuten = RakutenClient(
            config.rakuten_app_id,
            config.rakuten_access_key,
            config.rakuten_referer,
            config.rakuten_affiliate_id or None,
        )
    else:
        log.warning("RAKUTEN_APP_ID not set; skipping Rakuten")
    if config.yahoo_app_id:
        yahoo = YahooClient(config.yahoo_app_id)
    else:
        log.warning("YAHOO_APP_ID not set; skipping Yahoo")
    if config.amazon_access_key and config.amazon_secret_key and config.amazon_partner_tag:
        try:
            from .amazon_client import AmazonClient

            amazon = AmazonClient(
                config.amazon_access_key,
                config.amazon_secret_key,
                config.amazon_partner_tag,
                config.amazon_host,
                config.amazon_region,
            )
        except Exception as e:
            log.warning("Amazon client init failed: %s", e)
    else:
        log.warning("Amazon credentials not set; skipping Amazon")

    if not (rakuten or yahoo or amazon):
        log.error("No EC site API configured. Set at least one in .env")
        sys.exit(2)
    return amazon, rakuten, yahoo


def build_candidates(collect: bool, amazon_client) -> list[Candidate]:
    candidates: dict[str, Candidate] = {}

    # 1) 買取スキャナー CSV (買取価格つき)
    products = load_all(config.input_dir, config.enabled_shops)
    for p in products:
        candidates[p.jan] = Candidate(
            jan=p.jan,
            name=p.name,
            category=p.category or "",
            buy_price=p.buy_price,
            buy_shop=p.buy_shop,
        )

    # 2) EC から収集した JAN (買取価格なし → Amazon販売ルートのみ判定対象)
    if collect:
        log.info(
            "Collecting JANs from EC sites (keywords=%d, yahoo_genres=%d, pages=%d)...",
            len(config.collect_keywords),
            len(config.collect_yahoo_genres),
            config.collect_pages,
        )
        collected = collect_all(
            keywords=config.collect_keywords,
            yahoo_genres=config.collect_yahoo_genres,
            pages=config.collect_pages,
            yahoo_app_id=config.yahoo_app_id,
            rakuten_app_id=config.rakuten_app_id,
            rakuten_access_key=config.rakuten_access_key,
            rakuten_referer=config.rakuten_referer,
            amazon_client=amazon_client,
        )
        save_collected(collected, config.collected_dir)
        for jan, item in collected.items():
            c = candidates.get(jan)
            if c is None:
                c = Candidate(jan=jan, name=item.name, category=item.category)
                candidates[jan] = c
            elif not c.name:
                c.name = item.name
            if item.price:
                c.seed_prices[item.source] = item.price

    return list(candidates.values())


def write_outputs(rows: list, prefix: str, ts: str, row_type: type):
    """結果を書き出す。0件でも *_latest は空にして上書きし、前回の結果が残り続けないようにする。"""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [f.name for f in dataclasses.fields(row_type)]
    if not rows:
        log.info("No profitable products for '%s' this run (latest files cleared)", prefix)
    targets = [config.output_dir / f"{prefix}_latest.csv"]
    if rows:
        targets.insert(0, config.output_dir / f"{prefix}_{ts}.csv")
    for target in targets:
        with target.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                w.writerow(r.as_dict())
    json_targets = [config.output_dir / f"{prefix}_latest.json"]
    if rows:
        json_targets.insert(0, config.output_dir / f"{prefix}_{ts}.json")
    for target in json_targets:
        target.write_text(
            json.dumps([r.as_dict() for r in rows], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    log.info("Wrote %s_{%s,latest}.{csv,json} (%d rows)", prefix, ts, len(rows))


def _annotate(level: str, title: str, message: str) -> None:
    """GitHub Actions の実行画面に警告を表示する（ローカル実行では何もしない）。"""
    if os.getenv("GITHUB_ACTIONS") == "true":
        print(f"::{level} title={title}::{message}", flush=True)


def run(
    limit: int | None = None,
    skip_fetch: bool = False,
    mode: str = "both",
    collect: bool = False,
):
    onedrive_status = "未設定 (ONEDRIVE_SHARE_URL なし)"
    if skip_fetch:
        onedrive_status = "スキップ (--skip-fetch)"
    elif config.onedrive_share_url:
        log.info("Fetching CSV from OneDrive share...")
        try:
            fetched = fetch_folder(config.onedrive_share_url, config.input_dir)
            onedrive_status = f"ok ({len(fetched)} files)"
            log.info("Fetched %d file(s) from OneDrive", len(fetched))
            if not fetched:
                _annotate(
                    "warning",
                    "OneDrive 共有フォルダに CSV / Numbers ファイルがありません",
                    "買取スキャナーの全データCSVを共有フォルダに保存してください。",
                )
        except Exception as e:
            onedrive_status = f"失敗: {e}"
            log.error("OneDrive fetch failed: %s", e)
            _annotate("warning", "OneDrive から買取スキャナーCSVを取得できません", str(e))
            # CSV がなくても EC 収集分と買取商店カタログ照合は続行する
    converted = convert_numbers(config.input_dir)
    if converted:
        log.info("Converted %d table(s) from Numbers files to CSV", len(converted))
    log.info("Mode: %s / Enabled shops: %s", mode, config.enabled_shops)

    amazon, rakuten, yahoo = build_clients()
    candidates = build_candidates(collect=collect, amazon_client=amazon)

    if not candidates:
        log.error(
            "対象商品が見つかりません。買取スキャナーCSVを %s に配置するか、"
            "--collect で EC からの JAN 収集を有効にしてください。",
            config.input_dir,
        )
        sys.exit(1)
    # API の1日上限で途中停止しても価値の高い商品を先に見られるよう、買取価格の高い順に照会する
    candidates.sort(key=lambda c: c.buy_price or 0, reverse=True)
    if limit:
        candidates = candidates[:limit]
    log.info("Candidates: %d JAN codes", len(candidates))
    # 買取価格が「最低利益＋送料」に届かない商品は、仕入れ値0円でも基準を満たさないので照会しない
    unreachable_below = config.min_profit + config.shipping_cost
    skipped_unreachable = 0

    buyback_rows: list = []
    amazon_rows: list = []
    price_hits = {"amazon": 0, "rakuten": 0, "yahoo": 0}
    for i, c in enumerate(candidates, 1):
        if c.buy_price and c.buy_price < unreachable_below and amazon is None and not c.seed_prices:
            skipped_unreachable += 1
            continue
        # 収集時に価格が取れているソースは再照会せず流用する (APIクォータ節約)。
        # 収集は売れ筋順のため最安値より高い場合があるが、仕入れ値としては保守的な近似になる
        amz = c.seed_prices.get("amazon") or (amazon.min_price_by_jan(c.jan) if amazon else None)
        rak = c.seed_prices.get("rakuten_books") or (
            rakuten.min_price_by_jan(c.jan) if rakuten else None
        )
        yho = c.seed_prices.get("yahoo") or (yahoo.min_price_by_jan(c.jan) if yahoo else None)
        price_hits["amazon"] += 1 if amz else 0
        price_hits["rakuten"] += 1 if rak else 0
        price_hits["yahoo"] += 1 if yho else 0

        # ルートA: EC仕入れ → 買取店売却 (買取価格がある商品のみ)
        if mode in ("buyback", "both") and c.buy_price:
            pr = PriceRow(c.jan, c.name, c.buy_price, c.buy_shop, amz, rak, yho)
            row = compute(pr, config)
            if row is not None:
                buyback_rows.append(row)

        # ルートB: 楽天/Yahoo仕入れ → Amazon販売 (FBA手数料控除)
        if mode in ("amazon", "both"):
            row = compute_amazon(
                jan=c.jan,
                name=c.name,
                category=c.category,
                amazon_price=amz,
                rakuten_price=rak,
                yahoo_price=yho,
                cfg=config,
                buyback_price=c.buy_price,
                buyback_shop=c.buy_shop,
            )
            if row is not None:
                amazon_rows.append(row)

        if i % 50 == 0:
            log.info("Processed %d / %d", i, len(candidates))

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    summary: dict = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "candidates": len(candidates),
        "buyback_candidates": sum(1 for c in candidates if c.buy_price),
        "skipped_unreachable": skipped_unreachable,
        "price_hits": price_hits,
        "sources": {
            "amazon_api": "ok" if amazon else "未設定 (PA-APIキーなし → Amazon価格・Amazon販売ルート判定不可)",
            "rakuten_api": (
                credentials_problem(config.rakuten_app_id, config.rakuten_access_key)
                or ("停止 (連続失敗でスキップ)" if rakuten and rakuten.dead else "ok" if rakuten else "未設定")
            ),
            "yahoo_api": ("停止 (連続失敗でスキップ)" if yahoo and yahoo.dead else "ok" if yahoo else "未設定"),
        },
        "routes": {},
    }
    summary["sources"]["onedrive"] = onedrive_status
    if csv_loader_stats:
        summary["sources"]["kaitori_data"] = dict(csv_loader_stats)
    if not summary["buyback_candidates"]:
        summary["sources"]["kaitori_csv"] = (
            "買取価格つきの商品なし (共有フォルダにファイルがない・データが古い等。onedrive / kaitori_data を参照)"
        )

    if mode in ("buyback", "both"):
        profitable = sorted(
            (r for r in buyback_rows if is_profitable(r, config)),
            key=lambda r: r.profit,
            reverse=True,
        )
        log.info("[買取ルート] priced: %d, profitable: %d", len(buyback_rows), len(profitable))
        write_outputs(profitable, "profitable", ts, ProfitRow)
        summary["routes"]["buyback"] = {"priced": len(buyback_rows), "profitable": len(profitable)}

    if mode in ("amazon", "both"):
        profitable = sorted(
            (r for r in amazon_rows if is_amazon_profitable(r, config)),
            key=lambda r: r.profit,
            reverse=True,
        )
        log.info(
            "[Amazon販売ルート] priced: %d, profitable: %d", len(amazon_rows), len(profitable)
        )
        write_outputs(profitable, "amazon_profitable", ts, AmazonProfitRow)
        summary["routes"]["amazon"] = {"priced": len(amazon_rows), "profitable": len(profitable)}

    config.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = config.output_dir / "run_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("Run summary: %s", json.dumps(summary, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument(
        "--mode",
        choices=["buyback", "amazon", "both"],
        default="both",
        help="buyback=EC仕入れ→買取店 / amazon=楽天・Yahoo仕入れ→Amazon販売 / both=両方",
    )
    ap.add_argument(
        "--collect",
        action="store_true",
        help="EC サイトから売れ筋商品の JAN を収集して母集団に加える",
    )
    ap.add_argument(
        "--skip-fetch",
        action="store_true",
        help="OneDrive からの取得をスキップし、ローカルCSVのみ使用",
    )
    args = ap.parse_args()
    run(limit=args.limit, skip_fetch=args.skip_fetch, mode=args.mode, collect=args.collect)


if __name__ == "__main__":
    main()
