"""
Amazon SP-API クライアント
===========================
Login with Amazon (LWA) + AWS SigV4 署名による認証を実装。
API未設定時はデモデータを返すフォールバック機能付き。
"""

import json
import time
import hashlib
import hmac
import datetime
import urllib.parse
import requests
import logging
from typing import Optional, Dict, Any, List
from config import config, APP_CONFIG

logger = logging.getLogger(__name__)


class LWAAuthClient:
    """Login with Amazon アクセストークン取得クライアント"""

    TOKEN_URL = "https://api.amazon.com/auth/o2/token"

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

    def get_access_token(self) -> Optional[str]:
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        if not all([config.lwa_app_id, config.lwa_client_secret, config.lwa_refresh_token]):
            logger.warning("LWA認証情報が未設定です。デモモードで動作します。")
            return None

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": config.lwa_refresh_token,
            "client_id": config.lwa_app_id,
            "client_secret": config.lwa_client_secret,
        }
        try:
            resp = requests.post(self.TOKEN_URL, data=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expiry = time.time() + data.get("expires_in", 3600)
            return self._access_token
        except Exception as e:
            logger.error(f"LWAトークン取得失敗: {e}")
            return None


class AWSSigV4Signer:
    """AWS SigV4 リクエスト署名"""

    def __init__(self, access_key: str, secret_key: str, region: str, service: str = "execute-api"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = service

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def get_signing_key(self, date_stamp: str) -> bytes:
        k_date = self._sign(("AWS4" + self.secret_key).encode("utf-8"), date_stamp)
        k_region = self._sign(k_date, self.region)
        k_service = self._sign(k_region, self.service)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def sign_request(self, method: str, url: str, headers: Dict, body: str = "") -> Dict:
        parsed = urllib.parse.urlparse(url)
        t = datetime.datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        canonical_uri = parsed.path or "/"
        canonical_querystring = parsed.query
        canonical_headers = f"host:{parsed.netloc}\nx-amz-date:{amz_date}\n"
        signed_headers = "host;x-amz-date"
        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        canonical_request = "\n".join([
            method, canonical_uri, canonical_querystring,
            canonical_headers, signed_headers, payload_hash
        ])

        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256", amz_date, credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        ])

        signing_key = self.get_signing_key(date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        auth_header = (
            f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        headers.update({"x-amz-date": amz_date, "Authorization": auth_header})
        return headers


class SPAPIClient:
    """Amazon SP-API メインクライアント"""

    def __init__(self):
        self.lwa = LWAAuthClient()
        self.signer = AWSSigV4Signer(
            config.aws_access_key, config.aws_secret_key, config.aws_region
        ) if config.aws_access_key else None
        self.base_url = config.endpoint
        self.session = requests.Session()
        self.demo_mode = APP_CONFIG["demo_mode"]

    def _is_configured(self) -> bool:
        return bool(config.lwa_app_id and config.lwa_refresh_token and config.aws_access_key)

    def _request(self, method: str, path: str, params: Dict = None, body: Dict = None) -> Dict:
        if not self._is_configured():
            return {"demo": True}

        token = self.lwa.get_access_token()
        if not token:
            return {"demo": True}

        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)

        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json",
        }
        body_str = json.dumps(body) if body else ""
        if self.signer:
            headers = self.signer.sign_request(method.upper(), url, headers, body_str)

        try:
            resp = self.session.request(
                method, url, headers=headers,
                data=body_str if body_str else None,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            logger.error(f"SP-API HTTPエラー {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"SP-APIリクエスト失敗: {e}")
            raise

    # ---- Orders API ----
    def get_orders(self, created_after: str, created_before: str = None,
                   order_statuses: List[str] = None) -> Dict:
        """注文一覧取得"""
        params = {
            "MarketplaceIds": config.marketplace_id,
            "CreatedAfter": created_after,
        }
        if created_before:
            params["CreatedBefore"] = created_before
        if order_statuses:
            params["OrderStatuses"] = ",".join(order_statuses)

        result = self._request("GET", "/orders/v0/orders", params=params)
        if result.get("demo"):
            return self._demo_orders()
        return result

    def get_order_items(self, order_id: str) -> Dict:
        """注文アイテム取得"""
        result = self._request("GET", f"/orders/v0/orders/{order_id}/orderItems")
        if result.get("demo"):
            return self._demo_order_items(order_id)
        return result

    # ---- Reports API ----
    def request_report(self, report_type: str, start_date: str, end_date: str) -> Dict:
        """レポートリクエスト"""
        body = {
            "reportType": report_type,
            "marketplaceIds": [config.marketplace_id],
            "dataStartTime": start_date,
            "dataEndTime": end_date,
        }
        result = self._request("POST", "/reports/2021-06-30/reports", body=body)
        if result.get("demo"):
            return {"reportId": "DEMO_REPORT_001"}
        return result

    # ---- Inventory API ----
    def get_inventory_summaries(self) -> Dict:
        """在庫サマリー取得"""
        params = {
            "details": "true",
            "granularityType": "Marketplace",
            "granularityId": config.marketplace_id,
            "marketplaceIds": config.marketplace_id,
        }
        result = self._request("GET", "/fba/inventory/v1/summaries", params=params)
        if result.get("demo"):
            return self._demo_inventory()
        return result

    # ---- Catalog API ----
    def search_catalog_items(self, keywords: str) -> Dict:
        """商品カタログ検索"""
        params = {
            "keywords": keywords,
            "marketplaceIds": config.marketplace_id,
        }
        result = self._request("GET", "/catalog/2022-04-01/items", params=params)
        if result.get("demo"):
            return {"items": []}
        return result

    # ---- Finance API ----
    def get_financial_events(self, posted_after: str, posted_before: str = None) -> Dict:
        """財務イベント取得"""
        params = {"PostedAfter": posted_after}
        if posted_before:
            params["PostedBefore"] = posted_before

        result = self._request("GET", "/finances/v0/financialEvents", params=params)
        if result.get("demo"):
            return self._demo_financial_events()
        return result

    # ================================================================
    # デモデータ (API未設定時のサンプルデータ)
    # ================================================================
    def _demo_orders(self) -> Dict:
        import random
        from datetime import datetime, timedelta
        orders = []
        base_date = datetime(2025, 1, 1)
        products = [
            ("ワイヤレスイヤホン Pro", "B08XYZ001", 8800),
            ("スマートウォッチ SE", "B08XYZ002", 15800),
            ("USBハブ 7ポート", "B08XYZ003", 3200),
            ("メカニカルキーボード", "B08XYZ004", 12800),
            ("ノイズキャンセリングヘッドホン", "B08XYZ005", 22000),
            ("ポータブルSSD 1TB", "B08XYZ006", 9800),
            ("LEDデスクライト", "B08XYZ007", 4500),
            ("Webカメラ 4K", "B08XYZ008", 7800),
        ]
        order_id_base = 503
        for i in range(180):
            date = base_date + timedelta(days=i % 365)
            num_items = random.randint(1, 3)
            order_items = []
            total = 0
            for _ in range(num_items):
                prod = random.choice(products)
                qty = random.randint(1, 2)
                price = prod[2] * qty
                total += price
                order_items.append({
                    "ASIN": prod[1],
                    "Title": prod[0],
                    "QuantityOrdered": qty,
                    "ItemPrice": {"Amount": str(price), "CurrencyCode": "JPY"},
                })
            orders.append({
                "AmazonOrderId": f"{order_id_base}-{1000000 + i:07d}-{2000000 + i:07d}",
                "PurchaseDate": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "OrderStatus": random.choice(["Shipped", "Delivered", "Shipped", "Delivered", "Pending"]),
                "OrderTotal": {"Amount": str(total), "CurrencyCode": "JPY"},
                "NumberOfItemsShipped": num_items,
                "FulfillmentChannel": random.choice(["AFN", "AFN", "MFN"]),
                "Items": order_items,
            })
        return {"payload": {"Orders": orders}}

    def _demo_order_items(self, order_id: str) -> Dict:
        return {"payload": {"OrderItems": []}}

    def _demo_inventory(self) -> Dict:
        items = [
            {"asin": "B08XYZ001", "fnSku": "X001ABCDEF", "sellerSku": "WE-PRO-001",
             "productName": "ワイヤレスイヤホン Pro",
             "inventoryDetails": {"fulfillableQuantity": 45, "inboundWorkingQuantity": 0,
                                  "inboundShippedQuantity": 20, "reservedQuantity": {"totalReservedQuantity": 3}}},
            {"asin": "B08XYZ002", "fnSku": "X002ABCDEF", "sellerSku": "SW-SE-002",
             "productName": "スマートウォッチ SE",
             "inventoryDetails": {"fulfillableQuantity": 12, "inboundWorkingQuantity": 30,
                                  "inboundShippedQuantity": 0, "reservedQuantity": {"totalReservedQuantity": 2}}},
            {"asin": "B08XYZ003", "fnSku": "X003ABCDEF", "sellerSku": "HUB-7P-003",
             "productName": "USBハブ 7ポート",
             "inventoryDetails": {"fulfillableQuantity": 98, "inboundWorkingQuantity": 0,
                                  "inboundShippedQuantity": 0, "reservedQuantity": {"totalReservedQuantity": 5}}},
            {"asin": "B08XYZ004", "fnSku": "X004ABCDEF", "sellerSku": "KB-MECH-004",
             "productName": "メカニカルキーボード",
             "inventoryDetails": {"fulfillableQuantity": 7, "inboundWorkingQuantity": 50,
                                  "inboundShippedQuantity": 0, "reservedQuantity": {"totalReservedQuantity": 1}}},
            {"asin": "B08XYZ005", "fnSku": "X005ABCDEF", "sellerSku": "HP-NC-005",
             "productName": "ノイズキャンセリングヘッドホン",
             "inventoryDetails": {"fulfillableQuantity": 23, "inboundWorkingQuantity": 0,
                                  "inboundShippedQuantity": 10, "reservedQuantity": {"totalReservedQuantity": 4}}},
            {"asin": "B08XYZ006", "fnSku": "X006ABCDEF", "sellerSku": "SSD-1T-006",
             "productName": "ポータブルSSD 1TB",
             "inventoryDetails": {"fulfillableQuantity": 3, "inboundWorkingQuantity": 100,
                                  "inboundShippedQuantity": 0, "reservedQuantity": {"totalReservedQuantity": 0}}},
            {"asin": "B08XYZ007", "fnSku": "X007ABCDEF", "sellerSku": "LT-LED-007",
             "productName": "LEDデスクライト",
             "inventoryDetails": {"fulfillableQuantity": 66, "inboundWorkingQuantity": 0,
                                  "inboundShippedQuantity": 0, "reservedQuantity": {"totalReservedQuantity": 8}}},
            {"asin": "B08XYZ008", "fnSku": "X008ABCDEF", "sellerSku": "CAM-4K-008",
             "productName": "Webカメラ 4K",
             "inventoryDetails": {"fulfillableQuantity": 31, "inboundWorkingQuantity": 0,
                                  "inboundShippedQuantity": 0, "reservedQuantity": {"totalReservedQuantity": 6}}},
        ]
        return {"payload": {"inventorySummaries": items}}

    def _demo_financial_events(self) -> Dict:
        return {"payload": {"FinancialEvents": {"ShipmentEventList": []}}}


# シングルトンクライアント
client = SPAPIClient()
