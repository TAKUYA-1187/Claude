"""Amazon SP-API クライアント - 注文取得とバイヤーメッセージ送信"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List

from sp_api.api import Messaging, Orders
from sp_api.base import Marketplaces, SellerApiException
from sp_api.base.credential_provider import FromCodeCredentialProvider

logger = logging.getLogger(__name__)

# 日本語メッセージテンプレート
MESSAGE_TEMPLATE = """\
この度は、ベッドテーブルをご購入いただき、誠にありがとうございます。

お届けした商品に、旧版の取扱説明書が同梱されていた可能性がございます。
最新版の取扱説明書を以下のリンクよりご確認いただけますでしょうか。

▼ 最新版 取扱説明書（PDF）
{manual_url}

ご不便をおかけし、誠に申し訳ございません。
ご不明な点がございましたら、お気軽にご連絡ください。

どうぞよろしくお願いいたします。"""

# SP-API rate limit に配慮した待機時間（秒）
RATE_LIMIT_SLEEP = 1.0


def _make_credentials(config) -> dict:
    return {
        "lwa_app_id": config.lwa_client_id,
        "lwa_client_secret": config.lwa_client_secret,
        "refresh_token": config.lwa_refresh_token,
        "aws_access_key": "",
        "aws_secret_key": "",
    }


def get_orders(config, days_back: int) -> List[dict]:
    """指定ASINの注文一覧を取得する"""
    credentials = _make_credentials(config)
    orders_api = Orders(credentials=credentials, marketplace=Marketplaces.JP)

    created_after = (
        datetime.now(timezone.utc) - timedelta(days=days_back)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_orders = []
    next_token = None

    logger.info(f"注文一覧取得中 (ASIN: {config.product_asin}, 過去{days_back}日間)...")

    while True:
        try:
            if next_token:
                response = orders_api.get_orders(NextToken=next_token)
            else:
                response = orders_api.get_orders(
                    CreatedAfter=created_after,
                    MarketplaceIds=[config.marketplace_id],
                    OrderStatuses=["Shipped", "Unshipped", "PartiallyShipped"],
                )

            payload = response.payload
            orders = payload.get("Orders", [])

            # 対象ASINの注文のみフィルタリング
            for order in orders:
                order_id = order.get("AmazonOrderId", "")
                if _order_contains_asin(orders_api, order_id, config.product_asin):
                    all_orders.append(order)
                time.sleep(RATE_LIMIT_SLEEP)

            next_token = payload.get("NextToken")
            if not next_token:
                break

            time.sleep(RATE_LIMIT_SLEEP)

        except SellerApiException as e:
            logger.error(f"注文一覧取得エラー: {e}")
            break

    logger.info(f"対象注文数: {len(all_orders)} 件")
    return all_orders


def _order_contains_asin(orders_api, order_id: str, asin: str) -> bool:
    """注文に指定ASINが含まれるか確認する"""
    try:
        response = orders_api.get_order_items(order_id)
        items = response.payload.get("OrderItems", [])
        return any(item.get("ASIN") == asin for item in items)
    except SellerApiException as e:
        logger.warning(f"注文アイテム取得エラー ({order_id}): {e}")
        return False


def send_manual_message(config, order_id: str, dry_run: bool = False) -> bool:
    """バイヤーに取扱説明書の案内メッセージを送信する"""
    message_body = MESSAGE_TEMPLATE.format(manual_url=config.manual_url)

    if dry_run:
        logger.info(f"[DRY RUN] 注文 {order_id} にメッセージ送信（スキップ）")
        return True

    credentials = _make_credentials(config)
    messaging_api = Messaging(credentials=credentials, marketplace=Marketplaces.JP)

    try:
        # 利用可能なメッセージアクションを確認
        actions_response = messaging_api.get_messaging_actions_for_order(order_id)
        available_actions = [
            link["name"]
            for link in actions_response.payload.get("_links", {}).get("actions", [])
        ]
        logger.debug(f"注文 {order_id} の利用可能アクション: {available_actions}")

        # 優先順でメッセージタイプを選択
        if "createLegalDisclosure" in available_actions:
            messaging_api.create_legal_disclosure(
                order_id,
                body={"text": message_body},
            )
        elif "createUnexpectedProblem" in available_actions:
            messaging_api.create_unexpected_problem(
                order_id,
                body={"text": message_body},
            )
        elif "createAdditionalSellerSupport" in available_actions:
            # 汎用サポートメッセージ
            messaging_api.create_additional_seller_support(
                order_id,
                body={"text": message_body},
            )
        else:
            logger.warning(
                f"注文 {order_id}: 利用可能なメッセージアクションがありません "
                f"(アクション: {available_actions})"
            )
            return False

        logger.info(f"注文 {order_id}: メッセージ送信成功")
        return True

    except SellerApiException as e:
        logger.error(f"注文 {order_id}: メッセージ送信エラー - {e}")
        return False
