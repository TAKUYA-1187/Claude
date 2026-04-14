"""Gmail IMAP クライアント - 購入確認メールを取得する"""
import imaplib
import email
import logging
import quopri
import base64
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# 処理済み UID を記録するファイル
PROCESSED_UIDS_FILE = Path("processed_uids.txt")

# 対象ショップの送信元ドメイン
TARGET_DOMAINS = [
    "mail.yahoo.co.jp",
    "store.shopping.yahoo.co.jp",
    "yahoo.co.jp",
    "rakuten.co.jp",
    "email.apple.com",
    "apple.com",
]


class EmailMessage:
    """取得したメールの情報を保持するクラス"""

    def __init__(self, uid: int, from_addr: str, subject: str, html_body: str):
        self.uid = uid
        self.from_addr = from_addr
        self.subject = subject
        self.html_body = html_body


def _load_processed_uids() -> set:
    """処理済み UID をファイルから読み込む"""
    if not PROCESSED_UIDS_FILE.exists():
        return set()
    with open(PROCESSED_UIDS_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip().isdigit()}


def _save_processed_uid(uid: int) -> None:
    """処理済み UID をファイルに追記する"""
    with open(PROCESSED_UIDS_FILE, "a") as f:
        f.write(f"{uid}\n")


def _decode_header_value(value: str) -> str:
    """メールヘッダー値をデコードする"""
    parts = email.header.decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _extract_html_body(msg: email.message.Message) -> str:
    """メッセージから HTML ボディを抽出する"""
    html_part = None
    text_part = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html" and html_part is None:
                html_part = part
            elif content_type == "text/plain" and text_part is None:
                text_part = part
    else:
        if msg.get_content_type() == "text/html":
            html_part = msg
        elif msg.get_content_type() == "text/plain":
            text_part = msg

    target_part = html_part or text_part
    if target_part is None:
        return ""

    payload = target_part.get_payload(decode=True)
    if payload is None:
        return ""

    charset = target_part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _is_target_domain(from_addr: str) -> bool:
    """送信元アドレスが対象ドメインかどうかを確認する"""
    from_lower = from_addr.lower()
    return any(domain in from_lower for domain in TARGET_DOMAINS)


def fetch_purchase_emails(
    host: str,
    port: int,
    user: str,
    password: str,
    days_back: int,
    skip_processed: bool = True,
) -> List[EmailMessage]:
    """
    Gmail に IMAP 接続し、対象ショップからの購入確認メールを取得する。

    Args:
        host: IMAP ホスト (例: imap.gmail.com)
        port: IMAP ポート (例: 993)
        user: Gmail アドレス
        password: Gmail アプリパスワード
        days_back: 取得対象の日数
        skip_processed: True の場合、処理済み UID をスキップする

    Returns:
        EmailMessage のリスト
    """
    processed_uids = _load_processed_uids() if skip_processed else set()

    since_date = (date.today() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    logger.info(f"Gmail に接続中: {user} ({since_date} 以降)")

    messages: List[EmailMessage] = []

    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select("INBOX")

        # 日付フィルターで検索
        status, data = mail.search(None, f'SINCE "{since_date}"')
        if status != "OK" or not data[0]:
            logger.info("対象メールが見つかりませんでした。")
            mail.logout()
            return messages

        uid_list = data[0].split()
        logger.info(f"{len(uid_list)} 件のメールを検索しました。")

        for uid_bytes in uid_list:
            uid = int(uid_bytes)
            if uid in processed_uids:
                logger.debug(f"UID {uid}: 処理済みのためスキップ")
                continue

            status, msg_data = mail.fetch(uid_bytes, "(RFC822)")
            if status != "OK" or not msg_data[0]:
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_addr = msg.get("From", "")
            if not _is_target_domain(from_addr):
                continue

            subject = _decode_header_value(msg.get("Subject", ""))
            html_body = _extract_html_body(msg)

            if not html_body:
                logger.debug(f"UID {uid}: HTML ボディが空のためスキップ")
                continue

            messages.append(EmailMessage(
                uid=uid,
                from_addr=from_addr,
                subject=subject,
                html_body=html_body,
            ))
            logger.info(f"UID {uid}: 取得 [{from_addr}] {subject[:50]}")

        mail.logout()

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP エラー: {e}")
        raise

    logger.info(f"対象メール {len(messages)} 件を取得しました。")
    return messages


def mark_as_processed(uid: int) -> None:
    """指定した UID を処理済みとしてマークする"""
    _save_processed_uid(uid)
