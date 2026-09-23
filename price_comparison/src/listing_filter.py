"""JAN検索で紛れ込む「別の商品」を見分ける。

EC の JAN 検索は、本体の JAN を付けたダウンロードコード・修理サービス・中古品などが
最安値に来ることがある（2026-09 の実行で PS5 本体にコード販売 1,098円が当たった）。
こうした出品は買取店の条件（新品・完品）と一致しないため、価格比較から除く。
"""
from __future__ import annotations

CAUTION_WORDS = (
    "中古", "ジャンク", "訳あり", "わけあり", "アウトレット", "箱なし", "箱無し", "外箱なし",
    "ばら売り", "バラ売り", "未検品", "再生品", "整備済", "リファービッシュ",
    "ダウンロード", "コード", "修理", "レンタル", "互換", "交換用",
)


def looks_mismatched(name: str | None) -> bool:
    return bool(name) and any(w in name for w in CAUTION_WORDS)
