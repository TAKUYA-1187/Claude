"""最適化ルールの設定値。

すべてコマンドライン引数で上書きできる（main.py 参照）。
数値の根拠は README.md の「ルールの考え方」を参照。
"""

from dataclasses import dataclass


@dataclass
class Settings:
    # 目標ACOS（例: 0.20 = 20%）。損益分岐ACOS（＝広告費控除前の粗利率）より
    # 少し低い値を設定する。
    target_acos: float = 0.20

    # 除外キーワード判定: このクリック数以上で注文ゼロなら除外候補
    negative_click_threshold: int = 10

    # 刈り取り判定: オート/部分一致の検索語をこの注文数以上で完全一致へ移管
    harvest_order_threshold: int = 2

    # 入札調整の判定に必要な最低クリック数（少なすぎると統計的に無意味）
    bid_min_clicks: int = 5

    # 入札の上げ下げ幅の上限（一度に動かしすぎない）
    max_bid_increase: float = 0.30  # +30%まで
    max_bid_decrease: float = 0.30  # -30%まで

    # 入札を上げる条件: ACOSが目標のこの割合以下（余裕がある）
    bid_up_acos_ratio: float = 0.75

    # 入札を下げる条件: ACOSが目標のこの割合以上（超過している）
    bid_down_acos_ratio: float = 1.25
