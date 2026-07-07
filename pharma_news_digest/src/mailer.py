"""Gmail SMTP 経由でのメール送信。"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import List

from .config import Config

logger = logging.getLogger(__name__)


def send(cfg: Config, subject: str, html_body: str, text_body: str) -> None:
    """設定済みの宛先へダイジェストメールを送る。"""
    if not cfg.email_configured:
        raise RuntimeError(
            "SENDER_EMAIL / SENDER_APP_PASSWORD が未設定です。メール送信をスキップします。"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.sender_email
    msg["To"] = ", ".join(cfg.recipients)
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, context=context) as server:
        server.login(cfg.sender_email, cfg.sender_password)
        server.sendmail(cfg.sender_email, cfg.recipients, msg.as_string())

    logger.info("メール送信完了: %s", ", ".join(cfg.recipients))
