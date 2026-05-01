"""
Amazon購入者への取扱説明書PDF案内メッセージ自動送信スクリプト。
対象ASINの注文を取得し、未送信の購入者にメッセージを送る。
送信済み注文IDはsent_orders.jsonで管理し、重複送信を防ぐ。
"""
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from sp_api.api import Orders, Messaging
from sp_api.base import Marketplaces, SellingApiException

from config import TARGET_ASINS, MARKETPLACE_ID, ORDERS_CREATED_AFTER, MESSAGE_BODY

load_dotenv()

JST = timezone(timedelta(hours=9))
SENT_ORDERS_FILE = Path(__file__).parent / "sent_orders.json"

CREDENTIALS = {
    "lwa_app_id": os.environ["SP_API_CLIENT_ID"],
    "lwa_client_secret": os.environ["SP_API_CLIENT_SECRET"],
    "refresh_token": os.environ["SP_API_REFRESH_TOKEN"],
}


def load_sent_orders() -> dict:
    if SENT_ORDERS_FILE.exists():
        return json.loads(SENT_ORDERS_FILE.read_text(encoding="utf-8"))
    return {}


def save_sent_orders(sent: dict) -> None:
    SENT_ORDERS_FILE.write_text(
        json.dumps(sent, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def fetch_all_orders() -> list[dict]:
    """Amazonから全注文を取得（ページネーション対応）。"""
    orders_api = Orders(credentials=CREDENTIALS, marketplace=Marketplaces.JP)
    all_orders: list[dict] = []

    kwargs = {
        "MarketplaceIds": [MARKETPLACE_ID],
        "OrderStatuses": ["Shipped", "Delivered", "Unshipped", "PartiallyShipped"],
        "CreatedAfter": ORDERS_CREATED_AFTER,
        "MaxResultsPerPage": 100,
    }

    response = orders_api.get_orders(**kwargs)
    payload = response.payload
    all_orders.extend(payload.get("Orders", []))

    next_token = payload.get("NextToken")
    while next_token:
        time.sleep(1)  # API rate limit
        response = orders_api.get_orders(NextToken=next_token, MarketplaceIds=[MARKETPLACE_ID])
        payload = response.payload
        all_orders.extend(payload.get("Orders", []))
        next_token = payload.get("NextToken")

    return all_orders


def order_contains_target_asin(order_id: str) -> bool:
    """注文に対象ASINの商品が含まれているか確認する。"""
    orders_api = Orders(credentials=CREDENTIALS, marketplace=Marketplaces.JP)
    try:
        response = orders_api.get_order_items(order_id=order_id)
        items = response.payload.get("OrderItems", [])
        return any(item.get("ASIN") in TARGET_ASINS for item in items)
    except SellingApiException as e:
        print(f"  注文アイテム取得エラー ({order_id}): {e}")
        return False


def get_available_actions(order_id: str) -> list[str]:
    """注文に対して利用可能なメッセージアクションを取得する。"""
    messaging_api = Messaging(credentials=CREDENTIALS, marketplace=Marketplaces.JP)
    try:
        response = messaging_api.get_messaging_actions_for_order(
            amazon_order_id=order_id,
            marketplace_ids=[MARKETPLACE_ID],
        )
        links = response.payload.get("_links", {})
        actions = links.get("actions", [])
        return [a.get("name", "") if isinstance(a, dict) else str(a) for a in actions]
    except SellingApiException as e:
        print(f"  利用可能アクション取得エラー ({order_id}): {e}")
        return []


def send_message(order_id: str) -> bool:
    """購入者にメッセージを送信する。成功時はTrueを返す。"""
    messaging_api = Messaging(credentials=CREDENTIALS, marketplace=Marketplaces.JP)
    available = get_available_actions(order_id)

    # 取扱説明書送付に最適なアクションを優先順に試みる
    action_methods = [
        ("createDigitalAccessKey", messaging_api.create_digital_access_key),
        ("createUnexpectedProblem", messaging_api.create_unexpected_problem),
        ("createConfirmDeliveryDetails", messaging_api.create_confirm_delivery_details),
        ("createConfirmOrderDetails", messaging_api.create_confirm_order_details),
    ]

    for action_name, method in action_methods:
        if action_name not in available:
            continue
        try:
            method(
                amazon_order_id=order_id,
                marketplace_ids=[MARKETPLACE_ID],
                body={"text": MESSAGE_BODY},
            )
            print(f"  送信成功 [{action_name}]: {order_id}")
            return True
        except SellingApiException as e:
            print(f"  送信失敗 [{action_name}] ({order_id}): {e}")
            continue

    if not available:
        print(f"  利用可能なメッセージアクションなし: {order_id}")
    else:
        print(f"  対応アクションなし ({order_id}). 利用可能: {available}")
    return False


def main() -> None:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    print(f"=== 顧客フォローアップメッセージ送信 ({today}) ===")

    sent_orders = load_sent_orders()
    print(f"送信済み注文数: {len(sent_orders)}")

    print("注文一覧を取得中...")
    all_orders = fetch_all_orders()
    print(f"取得注文数: {len(all_orders)}")

    # 未送信の注文のみ絞り込み
    candidate_orders = [
        o for o in all_orders
        if o.get("AmazonOrderId") not in sent_orders
    ]
    print(f"未送信の注文数: {len(candidate_orders)}")

    # 対象ASINを含む注文を特定
    target_order_ids: list[str] = []
    for i, order in enumerate(candidate_orders, 1):
        order_id = order["AmazonOrderId"]
        print(f"[{i}/{len(candidate_orders)}] アイテム確認中: {order_id}")
        if order_contains_target_asin(order_id):
            target_order_ids.append(order_id)
        time.sleep(0.5)  # API rate limit

    print(f"メッセージ送信対象: {len(target_order_ids)} 件")

    success_count = 0
    fail_count = 0

    for order_id in target_order_ids:
        print(f"送信中: {order_id}")
        try:
            if send_message(order_id):
                sent_orders[order_id] = {"sent_date": today}
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"  予期しないエラー ({order_id}): {e}")
            fail_count += 1
        time.sleep(1)  # API rate limit

    save_sent_orders(sent_orders)
    print(f"\n=== 完了: 成功 {success_count} 件 / 失敗 {fail_count} 件 ===")

    if fail_count > 0 and success_count == 0 and len(target_order_ids) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
