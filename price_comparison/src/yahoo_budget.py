"""Yahoo!ショッピングAPIの利用量を一元管理する。

- 収集（jan_collector）と価格検索（yahoo_client / kaitori_catalog）が同じ予算を共有する
- 429（利用上限）を受けたら即停止し、冷却期間中は別の実行でも呼ばない（再試行しない・回避しない）
- 1日の利用数を data/state/yahoo_usage.json に保存し、同じ日の別実行とも共有する
  （GitHub Actionsの実行間は、このファイルをコミットして引き継ぐ）

上限値は環境変数で設定する。既定値は控えめな仮置きで、Yahoo!の公式上限は未確認。
  YAHOO_DAILY_BUDGET   … 1日あたりの上限（既定 5000）
  YAHOO_RUN_BUDGET     … 1回の実行あたりの上限（既定 28。2026-11-28の実測で約30件目に429）
  YAHOO_MIN_INTERVAL   … リクエスト間隔の秒数（既定 1.5。公式の目安は「1クエリー/秒」）
  YAHOO_COOLDOWN_MIN   … 429を受けてから再開しない時間（既定 60分）。公式は「一定時間利用できなくなる」とのみ記載
"""
from __future__ import annotations

import atexit
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

log = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))
ENDPOINT = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
STATE = Path(os.getenv("YAHOO_STATE_FILE",
                       Path(__file__).resolve().parent.parent / "data" / "state" / "yahoo_usage.json"))


class RateLimited(Exception):
    """HTTP 429。その日の利用を止める。"""


class BudgetExhausted(Exception):
    """設定した予算を使い切った。"""


class YahooBudget:
    _instance: "YahooBudget | None" = None

    @classmethod
    def shared(cls) -> "YahooBudget":
        if cls._instance is None:
            cls._instance = cls()
            atexit.register(cls._instance.save)
        return cls._instance

    def __init__(self, state_path: Path = STATE):
        self.state_path = Path(state_path)
        self.daily = int(os.getenv("YAHOO_DAILY_BUDGET", "5000"))
        self.per_run = int(os.getenv("YAHOO_RUN_BUDGET", "28"))
        self.interval = float(os.getenv("YAHOO_MIN_INTERVAL", "1.5"))
        self.cooldown_min = float(os.getenv("YAHOO_COOLDOWN_MIN", "60"))
        self.run_used = 0
        self.counts = {"requests": 0, "ok": 0, "http_error": 0, "network_error": 0, "rate_limited": 0}
        self._last = 0.0
        self._load()

    # ---- 永続化 ----
    def _today(self) -> str:
        return datetime.now(JST).strftime("%Y-%m-%d")

    def _load(self):
        s = {}
        if self.state_path.exists():
            try:
                s = json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                s = {}
        if s.get("date") != self._today():
            s = {"date": self._today(), "used": 0, "rate_limited_at": s.get("rate_limited_at")}
        self.state = s

    def save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 判定 ----
    @property
    def stopped_reason(self) -> str | None:
        rl = self.state.get("rate_limited_at")
        if rl:
            since = datetime.strptime(rl, "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
            if datetime.now(JST) - since < timedelta(minutes=self.cooldown_min):
                return f"429（利用制限）を {rl} に受信。{self.cooldown_min:.0f}分の冷却期間中のため停止"
        if self.state["used"] >= self.daily:
            return f"1日の予算 {self.daily} 回を使い切った"
        if self.run_used >= self.per_run:
            return f"今回の実行の予算 {self.per_run} 回を使い切った"
        return None

    def remaining(self) -> int:
        if self.stopped_reason:
            return 0
        return min(self.daily - self.state["used"], self.per_run - self.run_used)

    # ---- 呼び出し ----
    def get(self, params: dict, timeout: int = 15) -> dict:
        reason = self.stopped_reason
        if reason:
            raise (RateLimited if "429" in reason else BudgetExhausted)(reason)
        wait = self.interval - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        attempts = 0
        while True:
            attempts += 1
            self._last = time.time()
            self.state["used"] += 1
            self.run_used += 1
            self.counts["requests"] += 1
            try:
                r = requests.get(ENDPOINT, params=params, timeout=timeout)
            except requests.RequestException as e:
                self.counts["network_error"] += 1
                if attempts < 2:          # 通信エラーのみ1回だけ再試行
                    time.sleep(3)
                    continue
                self.save()
                raise
            if r.status_code == 429:
                self.counts["rate_limited"] += 1
                self.state["rate_limited_at"] = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                self.save()
                log.error("Yahoo API が 429（利用上限）を返したため、冷却期間まで呼び出しを停止します")
                raise RateLimited(self.stopped_reason)
            if r.status_code >= 500 and attempts < 2:   # サーバー側の一時エラーのみ1回再試行
                self.counts["http_error"] += 1
                time.sleep(5)
                continue
            if not r.ok:
                self.counts["http_error"] += 1
                self.save()
                r.raise_for_status()
            self.counts["ok"] += 1
            if self.counts["requests"] % 50 == 0:
                self.save()
            return r.json()
