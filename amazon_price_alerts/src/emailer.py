"""値下がりアラートメール送信 (Gmail SMTP)。

Gmail は 2段階認証 + アプリパスワード（16桁）で SMTP 認証する。
発行: Google アカウント → セキュリティ → 2段階認証 → アプリパスワード
"""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import Config
from .deal_filter import Alert

log = logging.getLogger(__name__)


def _format_yen(value) -> str:
    return f"¥{value:,}" if value is not None else "-"


def build_subject(alerts: list[Alert]) -> str:
    top = alerts[0]
    return (
        f"【Amazon刈り取り】値下がり{len(alerts)}件 "
        f"最大-{top.drop_percent:.0f}% {top.title[:25]}"
    )


def build_html(alerts: list[Alert]) -> str:
    rows = []
    for a in alerts:
        rows.append(
            "<tr>"
            f'<td><a href="{a.amazon_url}">{a.title[:60]}</a><br>'
            f'<small>{a.asin} / <a href="{a.keepa_url}">Keepaグラフ</a></small></td>'
            f'<td style="text-align:right;font-weight:bold;color:#c0392b;">{_format_yen(a.current_price)}</td>'
            f'<td style="text-align:right;">{_format_yen(a.avg30_price)}</td>'
            f'<td style="text-align:right;color:#c0392b;">-{a.drop_percent:.1f}%<br>'
            f"<small>(-{_format_yen(a.drop_yen)})</small></td>"
            f'<td style="text-align:right;">{a.seller_count}名</td>'
            f'<td style="text-align:right;">{a.sales_rank if a.sales_rank is not None else "-"}</td>'
            "</tr>"
        )
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    return f"""
<html><body style="font-family:sans-serif;">
<h2>Amazon 値下がりアラート ({now})</h2>
<p>30日平均から大幅に値下がりした商品です。通常価格に戻る前に仕入れを検討してください。<br>
※ 新品出品者3名以上（独占販売は除外済み）。値下がり直後は在庫が消えるのが早いので即確認推奨。</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
<tr style="background:#f0f0f0;">
<th>商品</th><th>現在価格</th><th>30日平均</th><th>下落率</th><th>新品出品者</th><th>ランキング</th>
</tr>
{''.join(rows)}
</table>
<p><small>Keepaグラフで「戻り価格」（値下がり前の安定価格）を必ず確認してから仕入れてください。</small></p>
</body></html>
"""


def send_alert_email(alerts: list[Alert], cfg: Config) -> None:
    if not alerts:
        return
    if not cfg.can_send_email():
        raise ValueError(
            "SMTP_USER / SMTP_PASSWORD が未設定のためメール送信できません。\n"
            ".env または GitHub Secrets に Gmail アドレスとアプリパスワードを設定してください。"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = build_subject(alerts)
    msg["From"] = cfg.smtp_user
    msg["To"] = ", ".join(cfg.alert_to)
    msg.attach(MIMEText(build_html(alerts), "html", "utf-8"))

    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(cfg.smtp_user, cfg.smtp_password)
        server.sendmail(cfg.smtp_user, cfg.alert_to, msg.as_string())

    log.info("アラートメール送信完了: %d件 → %s", len(alerts), ", ".join(cfg.alert_to))
