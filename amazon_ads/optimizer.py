"""レポートの行を最適化アクション（推奨リスト）に変換するルールエンジン。

出力は4種類:
  negatives  : 除外キーワード候補（クリックが嵩んでいるのに注文ゼロ）
  harvests   : 刈り取り候補（オート/部分一致で売れている検索語 → 完全一致へ移管）
  bid_up     : 入札引き上げ候補（目標ACOSに対して余裕がある）
  bid_down   : 入札引き下げ候補（目標ACOSを超過している）

推奨入札は「クリック単価あたりの売上 × 目標ACOS」を基本に、
一度の変更幅を ±max_bid_* に制限して算出する。
"""

from dataclasses import dataclass

from config import Settings
from report_loader import Row

AUTO_MATCH_TYPES = {"-", "close-match", "loose-match", "substitutes", "complements", ""}
BROAD_MATCH_TYPES = {"broad", "phrase", "部分一致", "フレーズ一致"}
EXACT_MATCH_TYPES = {"exact", "完全一致"}


@dataclass
class Action:
    kind: str
    campaign: str
    ad_group: str
    target: str          # 検索語 or ターゲティング
    reason: str
    clicks: int
    spend: float
    sales: float
    orders: int
    acos: float | None = None
    current_cpc: float = 0.0
    suggested_bid: float = 0.0


def _suggest_bid(row: Row, settings: Settings) -> float:
    """理論入札 = クリックあたり売上 × 目標ACOS。変更幅は現CPC比で制限。"""
    ideal = row.value_per_click * settings.target_acos
    upper = row.cpc * (1 + settings.max_bid_increase)
    lower = row.cpc * (1 - settings.max_bid_decrease)
    return round(min(max(ideal, lower), upper))


def _is_exact(row: Row) -> bool:
    return row.match_type.strip().lower() in EXACT_MATCH_TYPES


def analyze(rows: list[Row], settings: Settings) -> dict[str, list[Action]]:
    actions: dict[str, list[Action]] = {
        "negatives": [],
        "harvests": [],
        "bid_up": [],
        "bid_down": [],
    }

    for row in rows:
        target = row.search_term or row.targeting
        if not target:
            continue
        base = dict(
            campaign=row.campaign,
            ad_group=row.ad_group,
            target=target,
            clicks=row.clicks,
            spend=row.spend,
            sales=row.sales,
            orders=row.orders,
            acos=row.acos,
            current_cpc=round(row.cpc, 1),
        )

        # 1) 除外候補: クリックが閾値以上で注文ゼロ
        if row.orders == 0 and row.clicks >= settings.negative_click_threshold:
            actions["negatives"].append(Action(
                kind="negative_exact",
                reason=f"{row.clicks}クリック・¥{row.spend:,.0f}消化で注文0。"
                       "ネガティブ完全一致に追加",
                **base,
            ))
            continue

        if row.orders == 0:
            continue

        # 2) 刈り取り候補: 完全一致以外で売れている検索語
        if (row.search_term
                and not _is_exact(row)
                and row.orders >= settings.harvest_order_threshold
                and (row.acos is None or row.acos <= settings.target_acos)):
            actions["harvests"].append(Action(
                kind="harvest_to_exact",
                reason=f"注文{row.orders}件・ACOS {row.acos:.1%}。"
                       f"完全一致キャンペーンへ移管し、推奨入札¥{_suggest_bid(row, settings)}"
                       "で配信。元キャンペーンではネガティブ完全一致に追加",
                suggested_bid=_suggest_bid(row, settings),
                **base,
            ))

        # 3) 入札調整: クリック数が十分ある行のみ判定
        if row.clicks < settings.bid_min_clicks or row.acos is None:
            continue

        if row.acos <= settings.target_acos * settings.bid_up_acos_ratio:
            actions["bid_up"].append(Action(
                kind="bid_up",
                reason=f"ACOS {row.acos:.1%} < 目標{settings.target_acos:.0%}に余裕。"
                       f"入札を¥{_suggest_bid(row, settings)}へ引き上げ（露出拡大）",
                suggested_bid=_suggest_bid(row, settings),
                **base,
            ))
        elif row.acos >= settings.target_acos * settings.bid_down_acos_ratio:
            actions["bid_down"].append(Action(
                kind="bid_down",
                reason=f"ACOS {row.acos:.1%} > 目標{settings.target_acos:.0%}を超過。"
                       f"入札を¥{_suggest_bid(row, settings)}へ引き下げ",
                suggested_bid=_suggest_bid(row, settings),
                **base,
            ))

    # 影響額（消化金額）の大きい順に並べる
    for key in actions:
        actions[key].sort(key=lambda a: a.spend, reverse=True)
    return actions
