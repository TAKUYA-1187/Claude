"""ブログ（blog/ の Astro）のビルド結果から、WordPress 用の一式を作る。

    cd blog && SITE_URL=https://example.com npm run build && cd ..
    python wordpress/build_wp.py

出力（wordpress/dist/）
- posts.json               : publish_wp.py が REST API で投稿する内容（記事＋固定ページ）
- sedori-note-import.xml   : WordPress の「ツール → インポート → WordPress」で読み込めるファイル
- sedori-note-kit.zip      : 「プラグイン → 新規追加 → アップロード」で入れるプラグイン

本文は Astro が描画した HTML をそのまま使う（アフィリエイトリンク・PR表記・note 案内・計算ツールも同じ）。
外部ライブラリは使わない（GitHub Actions でも追加インストール不要）。
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
POSTS_SRC = BLOG / "src" / "content" / "posts"
DIST_SITE = BLOG / "dist"
OUT = Path(__file__).resolve().parent / "dist"
PLUGIN = Path(__file__).resolve().parent / "sedori-note-kit"
JST = timezone(timedelta(hours=9))

PR_NOTICE = '<p class="pr-notice">本記事はプロモーション（アフィリエイト広告）を含みます。</p>'
# 固定ページとして WordPress に作るページ（Astro のパス → WordPress のスラッグ・タイトル）
PAGES = {
    "about": "運営者情報",
    "privacy": "プライバシーポリシー・免責事項",
    "contact": "お問い合わせ",
}


def parse_frontmatter(path: Path) -> dict:
    """記事の frontmatter を読む。使っている書き方（文字列・配列・真偽値・日付）だけに対応する。"""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: frontmatter がありません")
    data: dict = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, raw = line.partition(":")
        if not sep:
            raise ValueError(f"{path.name}: 読めない行があります: {line}")
        data[key.strip()] = parse_value(raw.strip(), path.name)
    return data


def parse_value(raw: str, name: str):
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [parse_value(v.strip(), name) for v in split_list(inner)] if inner else []
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        s = raw[1:-1]
        return s.replace("''", "'") if raw[0] == "'" else s
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def split_list(inner: str) -> list[str]:
    items, buf, quote_ch = [], "", None
    for ch in inner:
        if quote_ch:
            buf += ch
            if ch == quote_ch:
                quote_ch = None
        elif ch in "'\"":
            quote_ch = ch
            buf += ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
    items.append(buf)
    return items


def parse_date(value: str) -> datetime:
    """Astro（z.coerce.date）と同じ解釈：日付だけなら UTC の0時。"""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_between(page: str, start: str, end: str, name: str) -> str:
    i = page.find(start)
    j = page.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or j < 0:
        raise ValueError(f"{name}: 本文の位置（{start}）が見つかりません。blog のテンプレートを確認してください")
    return page[i + len(start) : j]


def clean(fragment: str) -> str:
    # Astro のスコープ付きCSS用の属性は WordPress では不要
    return re.sub(r"\sdata-astro-cid-[\w-]+", "", fragment).strip()


def wrap(body: str) -> str:
    """「カスタムHTML」ブロックとして渡す。クラシック本文のままだと WordPress の自動整形（wpautop）が
    タグの間に <p>・<br> を足し、計算ツールや表のレイアウトが崩れる。"""
    return f'<!-- wp:html -->\n<div class="sedori-post">{body}</div>\n<!-- /wp:html -->'


def load_posts() -> list[dict]:
    posts = []
    for md in sorted(POSTS_SRC.glob("*.md")):
        fm = parse_frontmatter(md)
        slug = md.stem
        built = DIST_SITE / "posts" / slug / "index.html"
        draft = bool(fm.get("draft", False))
        if not built.exists():
            if draft:
                continue  # 下書きは Astro が出力しない
            raise FileNotFoundError(f"{built} がありません。先に blog で npm run build を実行してください")
        page = built.read_text(encoding="utf-8")
        body = extract_between(page, '<div class="post-body">', '<aside class="author-box">', slug)
        body = clean(body.rstrip()[: -len("</div>")] if body.rstrip().endswith("</div>") else body)
        if 'class="pr-notice"' in page.split('<div class="post-body">')[0]:
            body = PR_NOTICE + body
        content = wrap(body)
        date = parse_date(str(fm["pubDate"]))
        posts.append(
            {
                "type": "post",
                "slug": slug,
                "title": fm["title"],
                "excerpt": fm.get("description", ""),
                "content": content,
                "date_gmt": date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "status": "draft" if draft else "publish",
                "category": fm.get("tags", ["未分類"])[0] if fm.get("tags") else "未分類",
                "tags": fm.get("tags", []),
            }
        )
    return posts


def load_pages() -> list[dict]:
    pages = []
    for slug, title in PAGES.items():
        page = (DIST_SITE / slug / "index.html").read_text(encoding="utf-8")
        main = extract_between(page, '<main class="wrap">', "</main>", slug)
        main = re.sub(r"<h1[^>]*>.*?</h1>", "", main, count=1, flags=re.S)  # タイトルはテーマが出す
        main = re.sub(r'^<article class="prose"[^>]*>|</article>$', "", clean(main))
        pages.append(
            {
                "type": "page",
                "slug": slug,
                "title": title,
                "excerpt": "",
                "content": wrap(main.strip()),
                "status": "publish",
            }
        )
    return pages


def with_hash(items: list[dict]) -> list[dict]:
    for item in items:
        src = json.dumps({k: v for k, v in item.items() if k != "hash"}, ensure_ascii=False, sort_keys=True)
        item["hash"] = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
    return items


def term_slug(name: str) -> str:
    """WordPress の sanitize_title と同じ形（日本語は小文字のパーセントエンコード）。"""
    ascii_ = re.sub(r"[^a-z0-9\-]+", "-", name.lower()).strip("-")
    if ascii_ and ascii_ == name.lower():
        return ascii_
    return quote(name.replace(" ", "-"), safe="-").lower()


def cdata(text: str) -> str:
    return "<![CDATA[" + text.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def build_wxr(items: list[dict], site: dict) -> str:
    base = site["url"].rstrip("/")
    categories = sorted({i["category"] for i in items if i["type"] == "post"})
    tags = sorted({t for i in items if i["type"] == "post" for t in i["tags"]})
    out = [
        '<?xml version="1.0" encoding="UTF-8" ?>',
        '<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"'
        ' xmlns:content="http://purl.org/rss/1.0/modules/content/"'
        ' xmlns:wfw="http://wellformedweb.org/CommentAPI/"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:wp="http://wordpress.org/export/1.2/">',
        "<channel>",
        f"<title>{html.escape(site['name'])}</title>",
        f"<link>{html.escape(base)}</link>",
        f"<description>{html.escape(site['tagline'])}</description>",
        "<language>ja</language>",
        "<wp:wxr_version>1.2</wp:wxr_version>",
        f"<wp:base_site_url>{html.escape(base)}</wp:base_site_url>",
        f"<wp:base_blog_url>{html.escape(base)}</wp:base_blog_url>",
        "<wp:author><wp:author_id>1</wp:author_id>"
        f"<wp:author_login>{cdata('sedori-note')}</wp:author_login>"
        f"<wp:author_email>{cdata('')}</wp:author_email>"
        f"<wp:author_display_name>{cdata(site['author'])}</wp:author_display_name>"
        "</wp:author>",
    ]
    for n, name in enumerate(categories, start=1):
        out.append(
            f"<wp:category><wp:term_id>{n}</wp:term_id>"
            f"<wp:category_nicename>{cdata(term_slug(name))}</wp:category_nicename>"
            f"<wp:category_parent>{cdata('')}</wp:category_parent>"
            f"<wp:cat_name>{cdata(name)}</wp:cat_name></wp:category>"
        )
    for n, name in enumerate(tags, start=100):
        out.append(
            f"<wp:tag><wp:term_id>{n}</wp:term_id>"
            f"<wp:tag_slug>{cdata(term_slug(name))}</wp:tag_slug>"
            f"<wp:tag_name>{cdata(name)}</wp:tag_name></wp:tag>"
        )
    for post_id, item in enumerate(items, start=1):
        is_post = item["type"] == "post"
        if is_post:
            gmt = datetime.fromisoformat(item["date_gmt"]).replace(tzinfo=timezone.utc)
        else:
            gmt = datetime(2026, 9, 23, tzinfo=timezone.utc)
        local = gmt.astimezone(JST)
        link = f"{base}/posts/{item['slug']}/" if is_post else f"{base}/{item['slug']}/"
        out += [
            "<item>",
            f"<title>{cdata(item['title'])}</title>",
            f"<link>{html.escape(link)}</link>",
            f"<pubDate>{format_datetime(gmt)}</pubDate>",
            f"<dc:creator>{cdata('sedori-note')}</dc:creator>",
            f'<guid isPermaLink="false">{html.escape(base)}/?{"p" if is_post else "page_id"}={post_id}</guid>',
            "<description></description>",
            f"<content:encoded>{cdata(item['content'])}</content:encoded>",
            f"<excerpt:encoded>{cdata(item['excerpt'])}</excerpt:encoded>",
            f"<wp:post_id>{post_id}</wp:post_id>",
            f"<wp:post_date>{cdata(local.strftime('%Y-%m-%d %H:%M:%S'))}</wp:post_date>",
            f"<wp:post_date_gmt>{cdata(gmt.strftime('%Y-%m-%d %H:%M:%S'))}</wp:post_date_gmt>",
            f"<wp:comment_status>{cdata('closed')}</wp:comment_status>",
            f"<wp:ping_status>{cdata('closed')}</wp:ping_status>",
            f"<wp:post_name>{cdata(item['slug'])}</wp:post_name>",
            f"<wp:status>{cdata(item['status'])}</wp:status>",
            "<wp:post_parent>0</wp:post_parent>",
            "<wp:menu_order>0</wp:menu_order>",
            f"<wp:post_type>{cdata(item['type'])}</wp:post_type>",
            f"<wp:post_password>{cdata('')}</wp:post_password>",
            "<wp:is_sticky>0</wp:is_sticky>",
        ]
        if is_post:
            out.append(
                f'<category domain="category" nicename="{term_slug(item["category"])}">{cdata(item["category"])}</category>'
            )
            for tag in item["tags"]:
                out.append(f'<category domain="post_tag" nicename="{term_slug(tag)}">{cdata(tag)}</category>')
        out.append(
            f"<wp:postmeta><wp:meta_key>{cdata('sedori_source_hash')}</wp:meta_key>"
            f"<wp:meta_value>{cdata(item['hash'])}</wp:meta_value></wp:postmeta>"
        )
        out.append("</item>")
    out += ["</channel>", "</rss>", ""]
    return "\n".join(out)


def read_site_config() -> dict:
    text = (BLOG / "src" / "site.config.ts").read_text(encoding="utf-8")

    def field(name: str) -> str:
        m = re.search(rf"^\s*{name}:\s*'([^']*)'", text, re.M)
        return m.group(1) if m else ""

    # URL は Astro のビルド結果（canonical）から読む。SITE_URL で上書きした値が反映されている
    about = (DIST_SITE / "about" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<link rel="canonical" href="([^"]+)/about/"', about)
    return {
        "name": field("name"),
        "tagline": field("tagline"),
        "author": field("author"),
        "url": m.group(1) if m else "https://example.com",
    }


def build_plugin_zip() -> Path:
    # 計算ツールの JS はブログと同じファイルを使う（二重管理しない）
    shutil.copyfile(BLOG / "public" / "calc.js", PLUGIN / "assets" / "calc.js")
    target = OUT / "sedori-note-kit.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PLUGIN.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(str(Path("sedori-note-kit") / path.relative_to(PLUGIN)), (2026, 1, 1, 0, 0, 0))
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, path.read_bytes())
    return target


def main() -> int:
    if not (DIST_SITE / "index.html").exists():
        print("blog/dist がありません。先に blog で npm run build を実行してください", file=sys.stderr)
        return 1
    OUT.mkdir(exist_ok=True)
    site = read_site_config()
    items = with_hash(load_posts() + load_pages())
    (OUT / "posts.json").write_text(
        json.dumps({"site": site, "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "sedori-note-import.xml").write_text(build_wxr(items, site), encoding="utf-8")
    plugin = build_plugin_zip()
    posts = sum(1 for i in items if i["type"] == "post")
    print(f"記事 {posts} 本・固定ページ {len(items) - posts} 本（サイトURL: {site['url']}）")
    print(f"→ {OUT / 'posts.json'}\n→ {OUT / 'sedori-note-import.xml'}\n→ {plugin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
