"""買取商店の新品買取価格を取得し、Yahoo!ショッピングの新品最安値と突合する（2026-11-28 復旧版）

取得方法:
  買取商店は2026年にReact製サイトへ移行し、旧来のHTML（/products/A/list_category/B）は廃止された。
  現行サイトが公開ページの表示に使う読み取り専用API GET /api/v1/products を使う。
  robots.txt で /api/v1/products は明示的に Allow されている（他の /api/ は Disallow のため使わない）。

Yahoo!の問い合わせ:
  - 新品買取価格がある商品のJANだけを問い合わせる（condition=new, in_stock=true, janCode一致のみ採用）
  - 結果は data/state/yahoo_price_cache.json にキャッシュし、YAHOO_CACHE_HOURS 以内のものは再取得しない（差分取得）
  - 利用枠は src/yahoo_budget.py で一元管理。429 で即停止。枠内で「最後に調べた日時が古い順」に巡回する

出力:
  data/output/kaitorishouten_catalog_latest.csv    … 買取商店の新品買取価格（取得日時つき）
  data/output/kaitorishouten_all_latest.csv        … 新鮮なYahoo価格と突合できたもの
  data/output/kaitorishouten_profitable_latest.csv … 実質利益プラスのもの
  data/output/kaitori_run_status.json             … 実行状態（正常終了／部分成功／取得失敗／古いデータ使用）と件数

取得0件・異常時は既存の出力を上書きせず、状態ファイルに「取得失敗」を記録する。
"""
from __future__ import annotations

import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.yahoo_budget import BudgetExhausted, RateLimited, YahooBudget  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("catalog")
JST = timezone(timedelta(hours=9))

BASE = "https://www.kaitorishouten-co.jp"
API = f"{BASE}/api/v1/products"
OUT_DIR = ROOT / "data" / "output"
STATE_DIR = ROOT / "data" / "state"
CACHE_FILE = STATE_DIR / "yahoo_price_cache.json"
STATUS_FILE = OUT_DIR / "kaitori_run_status.json"

UA = {"User-Agent": "Mozilla/5.0 (compatible; LIFESTAR-price-research/2.0)", "Accept": "application/json"}
THROTTLE_SEC = float(os.getenv("CRAWL_THROTTLE", "1.5"))
PER_PAGE = 100
MAX_PAGES = int(os.getenv("KAITORI_MAX_PAGES", "200"))
MIN_EXPECTED_ITEMS = int(os.getenv("KAITORI_MIN_ITEMS", "1000"))   # これ未満は異常（部分取得）とみなす
SHIPPING_COST = int(os.getenv("SHIPPING_COST", "600"))
MIN_PROFIT = int(os.getenv("MIN_PROFIT", "1"))
POINT_RATE = float(os.getenv("POINT_RATE", "0.05"))
CACHE_HOURS = float(os.getenv("YAHOO_CACHE_HOURS", "20"))
FRESH_HOURS = float(os.getenv("FRESH_HOURS", "36"))                 # 突合に使うYahoo価格の鮮度上限
YAHOO_APP_ID = os.getenv("YAHOO_APP_ID", "")

CAUTION_WORDS = ["中古", "ばら売り", "バラ売り", "ジャンク", "訳あり", "アウトレット",
                 "箱なし", "箱無し", "ダウンロード", "コード", "未検品", "再生品", "整備済",
                 "修理品", "外装箱傷", "傷あり", "展示品", "開封済"]


def now() -> datetime:
    return datetime.now(JST)


def ts(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def caution_note(ec_name: str) -> str:
    hits = [w for w in CAUTION_WORDS if w in ec_name]
    return "要確認: " + "/".join(hits) if hits else ""


# ---- 買取商店 ---------------------------------------------------------------
def fetch_kaitori(session=None) -> tuple[dict[str, dict], dict]:
    """全商品をページ送りで取得。新品買取価格（price_new）があるJANだけを返す。"""
    s = session or requests.Session()
    s.headers.update(UA)
    catalog: dict[str, dict] = {}
    st = {"pages_ok": 0, "pages_failed": 0, "items_seen": 0, "items_with_new_price": 0,
          "items_without_jan": 0, "api_total": None, "started_at": ts(now())}
    page = 1
    while page <= MAX_PAGES:
        try:
            r = s.get(API, params={"per_page": PER_PAGE, "page": page, "nolog": 1}, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st["pages_failed"] += 1
            log.warning("買取商店 page %d 取得失敗: %s", page, e)
            if st["pages_failed"] >= 3:
                break
            time.sleep(THROTTLE_SEC * 3)
            continue
        fetched_at = ts(now())
        items = data.get("items") or []
        st["api_total"] = data.get("total")
        st["pages_ok"] += 1
        for it in items:
            st["items_seen"] += 1
            jan = str(it.get("jan") or "").strip()
            pn = (it.get("price_new") or {}).get("amount")
            if not jan:
                st["items_without_jan"] += 1
                continue
            if not pn or it.get("price_undecided"):
                continue
            st["items_with_new_price"] += 1
            prev = catalog.get(jan)
            if prev is None or pn > prev["price"]:
                catalog[jan] = {"name": it.get("name") or "", "price": int(pn), "fetched_at": fetched_at,
                                "site_update_date": it.get("update_date") or "",
                                "category": it.get("category") or "", "product_id": it.get("id")}
        total = data.get("total") or 0
        if not items or page * PER_PAGE >= total:
            break
        page += 1
        time.sleep(THROTTLE_SEC)
    st["finished_at"] = ts(now())
    st["unique_jan_new_price"] = len(catalog)
    return catalog, st


# ---- Yahoo!（キャッシュ・差分取得・巡回） -------------------------------------
def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(cache: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def age_hours(stamp: str | None) -> float:
    if not stamp:
        return 1e9
    return (now() - datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)).total_seconds() / 3600


def refresh_yahoo(jans: list[str], cache: dict, budget: YahooBudget) -> dict:
    """キャッシュが古いJANだけを、最後に調べた日時が古い順に問い合わせる。"""
    st = {"targets": len(jans), "cached_fresh": 0, "queried": 0, "found": 0, "not_found": 0,
          "failed": 0, "stopped_reason": None}
    due = [j for j in jans if age_hours(cache.get(j, {}).get("checked_at")) >= CACHE_HOURS]
    st["cached_fresh"] = len(jans) - len(due)
    due.sort(key=lambda j: cache.get(j, {}).get("checked_at") or "")   # 未調査（空）が最優先
    if not YAHOO_APP_ID:
        st["stopped_reason"] = "YAHOO_APP_ID 未設定"
        return st
    for jan in due:
        params = {"appid": YAHOO_APP_ID, "jan_code": jan, "sort": "+price", "results": 10,
                  "in_stock": "true", "condition": "new"}
        try:
            data = budget.get(params)
        except (RateLimited, BudgetExhausted) as e:
            st["stopped_reason"] = str(e)
            break
        except Exception as e:
            st["failed"] += 1
            log.warning("Yahoo %s 失敗: %s", jan, e)
            continue
        st["queried"] += 1
        hits = [h for h in (data.get("hits") or []) if str(h.get("janCode") or "") == jan and h.get("price")]
        entry = {"checked_at": ts(now())}
        if hits:
            best = min(hits, key=lambda h: h["price"])
            ship = best.get("shipping") or {}
            entry.update({"price": int(best["price"]), "name": best.get("name") or "", "url": best.get("url") or "",
                          "shipping_name": ship.get("name") if isinstance(ship, dict) else "",
                          "store": (best.get("seller") or {}).get("name", "") if isinstance(best.get("seller"), dict) else ""})
            st["found"] += 1
        else:
            st["not_found"] += 1
        cache[jan] = entry
        if st["queried"] % 100 == 0:
            save_cache(cache)
    save_cache(cache)
    return st


# ---- 状態判定 ---------------------------------------------------------------
def decide_status(k: dict, y: dict, matched_fresh: int, targets: int) -> tuple[str, list[str]]:
    reasons = []
    if k["unique_jan_new_price"] == 0:
        return "取得失敗", ["買取商店の新品買取価格を1件も取得できなかった"]
    partial = False
    if k["pages_failed"] or k["items_seen"] < MIN_EXPECTED_ITEMS or \
            (k["api_total"] and k["items_seen"] < k["api_total"]):
        partial = True
        reasons.append(f"買取商店の取得が不完全（{k['items_seen']}/{k['api_total']}件、失敗ページ{k['pages_failed']}）")
    if y["stopped_reason"]:
        partial = True
        reasons.append(f"Yahoo!の問い合わせを途中で停止: {y['stopped_reason']}")
    if y["failed"]:
        partial = True
        reasons.append(f"Yahoo!の問い合わせ失敗 {y['failed']}件")
    if matched_fresh == 0 and targets:
        return "取得失敗", reasons + ["鮮度内のYahoo!価格が1件もなく突合できなかった"]
    if matched_fresh < targets:
        partial = True
        reasons.append(f"未調査・鮮度切れで突合できなかった商品 {targets - matched_fresh}件（次回以降に巡回）")
    return ("部分成功" if partial else "正常終了"), reasons


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    started = now()
    catalog, kst = fetch_kaitori()
    log.info("買取商店: 取得 %s件 / API総数 %s / 新品買取価格あり %d JAN",
             kst["items_seen"], kst["api_total"], kst["unique_jan_new_price"])

    status = {"run_at": ts(started), "data_generated_at": None, "status": None, "reasons": [],
              "sources": {"kaitori": API, "yahoo": "Yahoo!ショッピング商品検索API v3 (condition=new, in_stock=true)"},
              "kaitori": kst}

    if kst["unique_jan_new_price"] == 0:
        prev = json.loads(STATUS_FILE.read_text(encoding="utf-8")) if STATUS_FILE.exists() else {}
        status.update(status="取得失敗", reasons=["買取商店の新品買取価格を1件も取得できなかった（前回の出力を保持）"],
                      data_generated_at=prev.get("data_generated_at"), yahoo={})
        STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        log.error("取得失敗: 出力ファイルは更新していません")
        return 0

    budget = YahooBudget.shared()
    cache = load_cache()
    jans = sorted(catalog, key=lambda j: -catalog[j]["price"])   # 高額商品から優先
    yst = refresh_yahoo(jans, cache, budget)
    yst["api_counts"] = budget.counts
    yst["daily_used"] = budget.state["used"]
    budget.save()

    both, uninvestigated = [], 0
    for jan in jans:
        it, y = catalog[jan], cache.get(jan)
        if not y or "price" not in y or age_hours(y.get("checked_at")) > FRESH_HOURS:
            if not y or age_hours(y.get("checked_at")) > FRESH_HOURS:
                uninvestigated += 1
            continue
        yp = y["price"]
        profit = it["price"] - yp - SHIPPING_COST
        eff_cost = int(round(yp * (1 - POINT_RATE)))
        eff = it["price"] - eff_cost - SHIPPING_COST
        both.append({
            "jan": jan, "ec_name": y.get("name", ""), "kaitori_name": it["name"], "kaitori_price": it["price"],
            "yahoo_price": yp, "shipping": SHIPPING_COST, "profit": profit,
            "profit_rate": round(profit / yp, 4) if yp else 0, "point_rate": POINT_RATE,
            "effective_cost": eff_cost, "effective_profit": eff,
            "effective_profit_rate": round(eff / eff_cost, 4) if eff_cost else 0,
            "note": caution_note(y.get("name", "")),
            "kaitori_url": BASE,   # 個別商品ページのURL形式は未確認のためトップを記載（商品名で検索）
            "category": it["category"], "yahoo_url": y.get("url", ""), "yahoo_store": y.get("store", ""),
            "yahoo_shipping": y.get("shipping_name", ""),
            "kaitori_fetched_at": it["fetched_at"], "yahoo_fetched_at": y["checked_at"],
        })
    both.sort(key=lambda r: r["effective_profit"], reverse=True)
    fresh_checked = sum(1 for j in jans if age_hours(cache.get(j, {}).get("checked_at")) <= FRESH_HOURS)

    fields = ["jan", "ec_name", "kaitori_name", "kaitori_price", "yahoo_price", "shipping", "profit", "profit_rate",
              "point_rate", "effective_cost", "effective_profit", "effective_profit_rate", "note", "kaitori_url",
              "category", "yahoo_url", "yahoo_store", "yahoo_shipping", "kaitori_fetched_at", "yahoo_fetched_at"]
    write_csv(OUT_DIR / "kaitorishouten_catalog_latest.csv",
              ["jan", "name", "kaitori_price", "category", "fetched_at", "site_update_date", "yahoo_checked_at"],
              [{"jan": j, "name": catalog[j]["name"], "kaitori_price": catalog[j]["price"],
                "category": catalog[j]["category"], "fetched_at": catalog[j]["fetched_at"],
                "site_update_date": catalog[j]["site_update_date"],
                "yahoo_checked_at": cache.get(j, {}).get("checked_at", "未調査")} for j in jans])
    write_csv(OUT_DIR / "kaitorishouten_all_latest.csv", fields, both)
    write_csv(OUT_DIR / "kaitorishouten_profitable_latest.csv", fields,
              [r for r in both if r["effective_profit"] >= MIN_PROFIT])

    st, reasons = decide_status(kst, yst, fresh_checked, len(jans))
    yst.update({"fresh_checked": fresh_checked, "uninvestigated_or_stale": uninvestigated,
                "matched": len(both), "profitable": sum(1 for r in both if r["effective_profit"] >= MIN_PROFIT)})
    status.update(status=st, reasons=reasons, data_generated_at=ts(now()), yahoo=yst)
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("状態: %s %s", st, " / ".join(reasons))
    log.info("突合 %d件（利益プラス %d件）、Yahoo問い合わせ %d回（本日累計 %d回）",
             len(both), yst["profitable"], yst["queried"], yst["daily_used"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
