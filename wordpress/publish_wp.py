"""wordpress/dist/posts.json の記事・固定ページを、WordPress の REST API で投稿・更新する。

    WP_URL=https://example.com WP_USER=ユーザー名 WP_APP_PASSWORD='xxxx xxxx ...' python wordpress/publish_wp.py

- WP_APP_PASSWORD は WordPress の「ユーザー → プロフィール → アプリケーションパスワード」で発行したもの
  （ログイン用のパスワードではない）
- 同じスラッグの記事があれば更新、なければ作成する。内容が変わっていない記事は触らない
  （プラグイン sedori-note-kit が保存する sedori_source_hash で判定）
- WordPress 側で削除・手直しした記事を、こちらから消すことはしない
- 公開日時が未来の記事は、WordPress の予約投稿になる
- 環境変数がなければ、何を投稿するかを表示するだけで終わる（エラーにしない）
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent / "dist" / "posts.json"
TIMEOUT = 30


class WordPress:
    def __init__(self, url: str, user: str, app_password: str):
        self.api = url.rstrip("/") + "/wp-json/wp/v2"
        token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "sedori-note-publisher/1.0",
        }

    def request(self, method: str, path: str, params: dict | None = None, body: dict | None = None):
        url = f"{self.api}/{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                return json.loads(res.read().decode("utf-8") or "null")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"{method} {path} → HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"{method} {path} → 接続できません: {e.reason}") from None

    def term_id(self, taxonomy: str, name: str, cache: dict) -> int:
        key = (taxonomy, name)
        if key not in cache:
            found = self.request("GET", taxonomy, {"search": name, "per_page": 100, "context": "edit"})
            match = next((t for t in found if t["name"] == name), None)
            cache[key] = match["id"] if match else self.request("POST", taxonomy, body={"name": name})["id"]
        return cache[key]

    def find(self, endpoint: str, slug: str):
        found = self.request(
            "GET", endpoint, {"slug": slug, "status": "publish,future,draft,pending,private", "context": "edit"}
        )
        return found[0] if found else None


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    items = payload["items"]
    url, user, password = (os.environ.get(k, "").strip() for k in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"))
    if not (url and user and password):
        print("WP_URL / WP_USER / WP_APP_PASSWORD が未設定のため、投稿はしません。対象：")
        for item in items:
            print(f"  {item['type']:4} {item['status']:7} /{item['slug']}/  {item['title']}")
        return 0

    wp = WordPress(url, user, password)
    me = wp.request("GET", "users/me", {"context": "edit"})
    print(f"WordPress に接続しました：{url}（ユーザー {me.get('name')}）")

    terms: dict = {}
    counts = {"作成": 0, "更新": 0, "変更なし": 0}
    for item in items:
        endpoint = "posts" if item["type"] == "post" else "pages"
        existing = wp.find(endpoint, item["slug"])
        if existing and (existing.get("meta") or {}).get("sedori_source_hash") == item["hash"]:
            counts["変更なし"] += 1
            continue

        body = {
            "slug": item["slug"],
            "title": item["title"],
            "content": item["content"],
            "excerpt": item["excerpt"],
            "meta": {"sedori_source_hash": item["hash"]},
        }
        if item["type"] == "post":
            body["categories"] = [wp.term_id("categories", item["category"], terms)]
            body["tags"] = [wp.term_id("tags", t, terms) for t in item["tags"]]
        if existing:
            # 公開済みの記事の公開日・状態は WordPress 側を優先する（手動で非公開にした記事を勝手に戻さない）。
            # 下書き・予約投稿のあいだは、記事側の公開日時に合わせる
            if existing["status"] in ("draft", "future") and item["status"] == "publish":
                body["status"] = "publish"
                if item["type"] == "post":
                    body["date_gmt"] = item["date_gmt"]
            wp.request("POST", f"{endpoint}/{existing['id']}", body=body)
            action = "更新"
        else:
            body["status"] = item["status"]
            if item["type"] == "post":
                body["date_gmt"] = item["date_gmt"]
            created = wp.request("POST", endpoint, body=body)
            if (created.get("meta") or {}).get("sedori_source_hash") != item["hash"]:
                print(
                    "  注意：sedori_source_hash が保存されていません。プラグイン「Sedori Note Kit」を有効にしてください"
                    "（有効にしないと、毎回すべての記事を更新します）"
                )
            action = "作成"
        counts[action] += 1
        print(f"  {action}：/{item['slug']}/  {item['title']}")

    print("結果：" + "／".join(f"{k} {v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"エラー：{e}", file=sys.stderr)
        sys.exit(1)
