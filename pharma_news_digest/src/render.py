"""ダイジェストを HTML／プレーンテキストのメール本文に整形する。"""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from .digest import SECTIONS
from .models import Article

_JST = timezone(timedelta(hours=9))


def _today_jst() -> str:
    return datetime.now(_JST).strftime("%Y年%m月%d日 (%a)")


def _fmt_date(art: Article) -> str:
    dt = art.published_utc
    if dt is None:
        return ""
    return dt.astimezone(_JST).strftime("%m/%d %H:%M")


def subject() -> str:
    return f"【腎臓領域ニュース】{datetime.now(_JST).strftime('%Y/%m/%d')} 朝刊ダイジェスト（ファビハルタ／IgA腎症）"


# --- HTML ---------------------------------------------------------------

def _item_html(art: Article) -> str:
    date = _fmt_date(art)
    meta_bits = [b for b in (art.publisher, art.source, date) if b]
    meta = " ・ ".join(html.escape(b) for b in meta_bits)
    summary = html.escape(art.summary) if art.summary else ""
    summary_html = f'<div style="color:#555;font-size:13px;margin-top:3px;">{summary}</div>' if summary else ""
    return f"""
      <li style="margin-bottom:14px;list-style:none;padding-left:14px;border-left:3px solid #e2e8f0;">
        <a href="{html.escape(art.url)}" style="color:#1a5276;font-weight:600;text-decoration:none;font-size:15px;line-height:1.4;">{html.escape(art.title)}</a>
        <div style="color:#888;font-size:12px;margin-top:2px;">{meta}</div>
        {summary_html}
      </li>"""


def render_html(grouped: Dict[str, List[Article]]) -> str:
    total = sum(len(v) for v in grouped.values())
    parts: List[str] = []
    for key, title in SECTIONS:
        items = grouped.get(key, [])
        if not items:
            body = '<p style="color:#999;font-size:13px;margin:4px 0 0;">本日の新規はありません。</p>'
        else:
            body = "<ul style=\"margin:8px 0 0;padding:0;\">" + "".join(_item_html(a) for a in items) + "</ul>"
        parts.append(
            f"""
      <div style="margin-bottom:28px;">
        <h2 style="font-size:16px;color:#0b3d5c;border-bottom:2px solid #0b3d5c;padding-bottom:6px;margin:0 0 10px;">{html.escape(title)}</h2>
        {body}
      </div>"""
        )

    note = """
      <div style="margin-top:24px;padding:12px 14px;background:#f7fafc;border-radius:6px;font-size:12px;color:#666;line-height:1.6;">
        <strong>ソースについて：</strong> ニュースは Google ニュース、論文は PubMed / Europe PMC の公開データから自動収集しています。
        RISFAX（じほう）等の情報誌は有料購読が必要で本文は取得できないため、公開インデックスされた見出しのみを「国内 医療・製薬業界ニュース」に含めています。
        詳細は各媒体の購読でご確認ください。
      </div>"""

    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#eef2f5;padding:16px;font-family:'Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif;">
  <div style="max-width:680px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">
    <div style="background:linear-gradient(135deg,#0b3d5c,#1a6ea8);color:#fff;padding:22px 24px;">
      <div style="font-size:20px;font-weight:700;">腎臓領域 ニュースダイジェスト</div>
      <div style="font-size:13px;opacity:.9;margin-top:4px;">{_today_jst()}　朝刊　｜　ファビハルタ・IgA腎症 担当（北陸）向け</div>
      <div style="font-size:12px;opacity:.8;margin-top:6px;">本日の新着 {total} 件</div>
    </div>
    <div style="padding:22px 24px;">
      {''.join(parts)}
      {note}
    </div>
    <div style="padding:14px 24px;background:#0b3d5c;color:#cfe0ec;font-size:11px;">
      自動配信 / Pharma News Digest ・ 毎朝 7:00 (JST)
    </div>
  </div>
</body></html>"""


# --- プレーンテキスト（HTML 非対応クライアント用） ----------------------

def render_text(grouped: Dict[str, List[Article]]) -> str:
    lines = [f"腎臓領域 ニュースダイジェスト  {_today_jst()} 朝刊", "=" * 48, ""]
    for key, title in SECTIONS:
        lines.append(f"■ {title}")
        items = grouped.get(key, [])
        if not items:
            lines.append("  （本日の新規はありません）")
        for a in items:
            date = _fmt_date(a)
            meta = " / ".join(b for b in (a.publisher, a.source, date) if b)
            lines.append(f"  ・{a.title}")
            if meta:
                lines.append(f"    {meta}")
            lines.append(f"    {a.url}")
        lines.append("")
    lines.append(
        "※ RISFAX 等の情報誌は有料購読が必要なため、公開見出しのみを掲載しています。"
    )
    return "\n".join(lines)
