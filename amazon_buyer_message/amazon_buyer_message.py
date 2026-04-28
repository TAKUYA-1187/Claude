#!/usr/bin/env python3
"""
Amazon Seller Central - 購入者への取扱説明書メッセージ自動送信
対象ASIN: B0G1B3LND1, B0G19VXNCJ, B0G1B2J9Q9, B0G1B4QN85
毎日15:00 JSTに実行
"""

import json
import os
import sys
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from sp_api.api import Orders, Messaging
    from sp_api.base import Marketplaces, SellingApiException
except ImportError:
    print("Error: python-amazon-sp-api が未インストールです。次を実行してください: pip install python-amazon-sp-api")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
SENT_ORDERS_FILE = SCRIPT_DIR / "sent_orders.json"
LOG_FILE = SCRIPT_DIR / "amazon_message.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

TARGET_ASINS = {
    "B0G1B3LND1",  # タブレットホルダー有り ナチュラルオーク
    "B0G19VXNCJ",  # タブレットホルダー無し ウォルナットブラウン
    "B0G1B2J9Q9",  # タブレットホルダー無し ナチュラルオーク
    "B0G1B4QN85",  # タブレットホルダー付き ウォルナットブラウン
}

MARKETPLACE_ID = "A1VC38T7YXB528"  # Amazon.co.jp

MESSAGE_TEXT = """大変お世話になっております。
この度は当店の商品をご購入いただき、誠にありがとうございます。
本製品には取扱説明書を同梱しておりますが、より分かりやすくご確認いただける補足資料につきまして、同梱ができておりませんでしたため、PDF版の取扱説明書をお送りいたします。
組み立て時に迷いやすい下記の内容を中心に、詳細を記載しております。
・伸縮ポールは1本で内部に収納されている構造
・ポールの向き(黒い樹脂側が脚部側)
・天板が下がらない場合の操作方法
また、組み立て時によくある事象として、
支柱内部のポール(内筒)が入り込んでいる状態では、脚部側のネジが届かず取り付けできない場合がございます。
本製品はガス圧式の構造のため、内筒は手で引き出すことができません。
その場合は、先に天板側の昇降レバーを取り付けていただくことで、内部の支柱が作動し、内筒が適正位置まで出てまいります。
その後、脚部の取り付けを行っていただくことで、問題なく組み立てが可能となります。
上記の手順につきましても、PDF内で詳しくご案内しておりますので、あわせてご確認いただけますと幸いです。
なお、本製品はガス圧式の特性により、初期状態では昇降時にやや抵抗を感じる場合がございますが、数回操作いただくことでスムーズに動作するようになります。
万が一、組み立てやご使用にあたりご不明点がございましたら、Amazonの購入履歴よりお気軽にご連絡ください。
何卒よろしくお願い申し上げます。
▼取扱説明書(PDF)
https://1drv.ms/b/c/c37e10a4e80c2802/IQBLXIJ1RYeaRp8HRHS4EKs-Ab1_D0p3A0M0jzIK0MJ0TSM?e=fjybm7"""


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {CONFIG_FILE}\n"
            "config.json.template をコピーして config.json を作成し、認証情報を入力してください。"
        )
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_sent_orders() -> set:
    if not SENT_ORDERS_FILE.exists():
        return set()
    with open(SENT_ORDERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("sent_orders", []))


def save_sent_orders(sent_orders: set) -> None:
    data = {
        "sent_orders": sorted(list(sent_orders)),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    with open(SENT_ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_credentials(config: dict) -> dict:
    return {
        "refresh_token": config["lwa_refresh_token"],
        "lwa_app_id": config["lwa_client_id"],
        "lwa_client_secret": config["lwa_client_secret"],
        "aws_secret_key": config["aws_secret_key"],
        "aws_access_key": config["aws_access_key"],
        "role_arn": config["role_arn"],
    }


def get_recent_orders(credentials: dict, days_back: int = 2) -> list:
    """直近 days_back 日間の注文一覧を取得する。"""
    orders_api = Orders(credentials=credentials, marketplace=Marketplaces.JP)
    created_after = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    all_orders: list = []
    next_token: str | None = None

    while True:
        try:
            if next_token:
                response = orders_api.get_orders(
                    NextToken=next_token,
                    MarketplaceIds=[MARKETPLACE_ID],
                )
            else:
                response = orders_api.get_orders(
                    CreatedAfter=created_after,
                    MarketplaceIds=[MARKETPLACE_ID],
                    OrderStatuses=["Unshipped", "PartiallyShipped", "Shipped", "Delivered"],
                )
            payload = response.payload
            all_orders.extend(payload.get("Orders", []))
            next_token = payload.get("NextToken")
            if not next_token:
                break
            time.sleep(1)  # API レート制限対策
        except SellingApiException as e:
            logger.error(f"注文取得エラー: {e}")
            break

    return all_orders


def order_contains_target_asin(credentials: dict, order_id: str) -> bool:
    """注文に対象 ASIN が含まれるか確認する。"""
    orders_api = Orders(credentials=credentials, marketplace=Marketplaces.JP)
    try:
        response = orders_api.get_order_items(order_id)
        for item in response.payload.get("OrderItems", []):
            if item.get("ASIN") in TARGET_ASINS:
                return True
        return False
    except SellingApiException as e:
        logger.error(f"注文アイテム取得エラー ({order_id}): {e}")
        return False


def send_message(credentials: dict, order_id: str) -> bool:
    """取扱説明書メッセージを購入者に送信する。"""
    messaging_api = Messaging(credentials=credentials, marketplace=Marketplaces.JP)

    # 利用可能なメッセージタイプを確認
    try:
        actions_resp = messaging_api.get_messaging_actions_for_order(order_id)
        links = actions_resp.payload.get("_links", {})
        available = [a.get("name", "") for a in links.get("actions", [])]
        logger.info(f"利用可能メッセージタイプ ({order_id}): {available}")
    except SellingApiException as e:
        logger.warning(f"メッセージタイプ確認失敗 ({order_id}): {e}")
        available = []

    body = {
        "text": {
            "locale": "ja_JP",
            "text": MESSAGE_TEXT,
        }
    }

    # 優先順位: warranty → unexpectedProblem → confirmDeliveryDetails
    send_methods = [
        ("createWarranty", messaging_api.create_warranty),
        ("createUnexpectedProblem", messaging_api.create_unexpected_problem),
        ("createConfirmDeliveryDetails", messaging_api.create_confirm_delivery_details),
    ]

    for type_name, method in send_methods:
        if available and type_name not in available:
            continue
        try:
            method(order_id, body=body)
            logger.info(f"メッセージ送信成功 ({type_name}): {order_id}")
            return True
        except SellingApiException as e:
            logger.warning(f"{type_name} 送信失敗 ({order_id}): {e}")

    logger.error(f"すべてのメッセージタイプで送信失敗: {order_id}")
    return False


def main() -> None:
    logger.info("=" * 60)
    logger.info("Amazon購入者 取扱説明書メッセージ送信 開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        config = load_config()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    sent_orders = load_sent_orders()
    logger.info(f"送信済み注文数: {len(sent_orders)}")

    credentials = build_credentials(config)
    days_back = config.get("days_back", 2)

    logger.info(f"直近 {days_back} 日間の注文を取得中...")
    orders = get_recent_orders(credentials, days_back=days_back)
    logger.info(f"取得注文数: {len(orders)}")

    sent_count = 0
    skipped_count = 0
    error_count = 0

    for order in orders:
        order_id = order.get("AmazonOrderId")
        if not order_id:
            continue

        if order_id in sent_orders:
            skipped_count += 1
            continue

        if not order_contains_target_asin(credentials, order_id):
            continue

        order_status = order.get("OrderStatus", "不明")
        logger.info(f"対象注文検出: {order_id} (ステータス: {order_status})")

        if send_message(credentials, order_id):
            sent_orders.add(order_id)
            save_sent_orders(sent_orders)
            sent_count += 1
        else:
            error_count += 1

        time.sleep(1)  # API レート制限対策

    logger.info(
        f"処理完了 - 送信: {sent_count}件 / スキップ(送信済み): {skipped_count}件 / エラー: {error_count}件"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
