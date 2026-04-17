"""Gmail API クライアント - 購入確認メールを取得する（OAuth2認証）"""
import base64
import logging
import os
from datetime import date, timedelta
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = Path("token.json")
PROCESSED_UIDS_FILE = Path("processed_uids.txt")

# 対象ショップの送信元ドメイン（Gmail 検索クエリ用）
SEARCH_FROM = [
    "from:mail.yahoo.co.jp",
    "from:store.shopping.yahoo.co.jp",
    "from:rakuten.co.jp",
    "from:email.apple.com",
]


class EmailMessage:
    """取得したメールの情報を保持するクラス"""

    def __init__(self, uid: str, from_addr: str, subject: str, html_body: str):
        self.uid = uid
        self.from_addr = from_addr
        self.subject = subject
        self.html_body = html_body


def _get_gmail_service(credentials_file: str):
    """Gmail API サービスを取得する（初回はブラウザで認証）"""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_file).exists():
                raise FileNotFoundError(
                    f"credentials.json が見つかりません: {credentials_file}\n"
                    "Google Cloud Console から OAuth2 認証情報をダウンロードして\n"
                    "プロジェクトフォルダに置いてください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            # ブラウザが自動で開き、ユーザーが「許可」をクリックするだけ
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info("Gmail 認証トークンを保存しました。次回からは自動でログインします。")

    return build("gmail", "v1", credentials=creds)


def _load_processed_uids() -> set:
    if not PROCESSED_UIDS_FILE.exists():
        return set()
    with open(PROCESSED_UIDS_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def _save_processed_uid(uid: str) -> None:
    with open(PROCESSED_UIDS_FILE, "a") as f:
        f.write(f"{uid}\n")


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_html_body(payload: dict) -> str:
    """Gmail API のペイロードから HTML 本文を抽出する"""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/html" and body_data:
        return base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")

    if mime_type == "text/plain" and body_data and not _extract_html_from_parts(payload.get("parts", [])):
        return base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")

    return _extract_html_from_parts(payload.get("parts", []))


def _extract_html_from_parts(parts: list) -> str:
    """マルチパートメールから HTML を再帰的に抽出する"""
    html_body = ""
    text_body = ""
    for part in parts:
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data", "")
        if mime_type == "text/html" and body_data:
            html_body = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        elif mime_type == "text/plain" and body_data and not html_body:
            text_body = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        elif "parts" in part:
            sub = _extract_html_from_parts(part["parts"])
            if sub:
                html_body = sub
    return html_body or text_body


def fetch_purchase_emails(
    credentials_file: str,
    days_back: int,
    skip_processed: bool = True,
) -> List[EmailMessage]:
    """
    Gmail API で対象ショップからの購入確認メールを取得する。

    初回実行時はブラウザが自動で開きます。
    「このアプリを許可」をクリックするだけで認証完了です。

    Args:
        credentials_file: credentials.json のパス
        days_back: 取得対象の日数
        skip_processed: 処理済みメールをスキップするか

    Returns:
        EmailMessage のリスト
    """
    processed_uids = _load_processed_uids() if skip_processed else set()
    service = _get_gmail_service(credentials_file)

    since_date = (date.today() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    from_query = " OR ".join(SEARCH_FROM)
    query = f"({from_query}) after:{since_date}"

    logger.info(f"Gmail を検索中 (過去{days_back}日間) ...")

    messages: List[EmailMessage] = []
    page_token = None

    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            kwargs["pageToken"] = page_token

        result = service.users().messages().list(**kwargs).execute()
        msg_refs = result.get("messages", [])

        for ref in msg_refs:
            msg_id = ref["id"]
            if msg_id in processed_uids:
                logger.debug(f"{msg_id}: 処理済みのためスキップ")
                continue

            msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()

            payload = msg.get("payload", {})
            headers = payload.get("headers", [])
            from_addr = _get_header(headers, "From")
            subject = _get_header(headers, "Subject")
            html_body = _extract_html_body(payload)

            if not html_body:
                logger.debug(f"{msg_id}: 本文が空のためスキップ")
                continue

            messages.append(EmailMessage(
                uid=msg_id,
                from_addr=from_addr,
                subject=subject,
                html_body=html_body,
            ))
            logger.info(f"{msg_id}: 取得 [{from_addr[:40]}] {subject[:50]}")

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    logger.info(f"対象メール {len(messages)} 件を取得しました。")
    return messages


def mark_as_processed(uid: str) -> None:
    """指定した ID を処理済みとしてマークする"""
    _save_processed_uid(uid)
