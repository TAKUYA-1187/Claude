"""OneDrive の匿名共有フォルダから CSV を取得する。

個人向け OneDrive の匿名共有リンクは、認証不要の OneDrive API
(`api.onedrive.com`) の `/shares/{token}/root` で解決できる。
Microsoft Graph (`graph.microsoft.com`) の同エンドポイントは Bearer トークン必須の
ため、認証情報を持たないこのツールでは基本的に使えないが、フォールバックとして残す。

Docs: https://learn.microsoft.com/onedrive/developer/rest-api/api/shares_get
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

# 匿名アクセス可の OneDrive API を優先し、Graph はフォールバック
API_BASES = [
    ("https://api.onedrive.com/v1.0", "root"),
    ("https://graph.microsoft.com/v1.0", "driveItem"),
]

DOWNLOAD_URL_KEYS = ("@content.downloadUrl", "@microsoft.graph.downloadUrl")


def _encode_share_url(url: str) -> str:
    b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return "u!" + b64


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
def _get_json(url: str) -> dict:
    r = requests.get(url, timeout=30)
    if not r.ok:
        log.warning("GET %s -> HTTP %d: %s", url.split("?")[0], r.status_code, r.text[:200])
    r.raise_for_status()
    return r.json()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
def _download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)


def _iter_children(item_api_url: str) -> Iterable[dict]:
    """children を next page 含めて列挙。"""
    url = item_api_url
    while url:
        data = _get_json(url)
        for c in data.get("value", []):
            yield c
        url = data.get("@odata.nextLink")


def _resolve_root(share_url: str) -> tuple[str, dict]:
    """共有リンクを解決し、(children列挙用URL, ルートitem) を返す。"""
    token = _encode_share_url(share_url)
    last_error: Exception | None = None
    for base, root_seg in API_BASES:
        root_url = f"{base}/shares/{token}/{root_seg}"
        try:
            root = _get_json(root_url)
            log.info("Resolved share via %s", base)
            return f"{root_url}/children", root
        except Exception as e:
            log.warning("Share resolve failed via %s: %s", base, e)
            last_error = e
    raise RuntimeError(
        f"OneDrive共有リンクを解決できませんでした。リンクが「リンクを知っている全員」で"
        f"共有されているか確認してください: {last_error}"
    )


def fetch_folder(share_url: str, dest_dir: Path, extensions: tuple[str, ...] = (".csv",)) -> list[Path]:
    """共有フォルダ直下のファイルを取得。サブフォルダは再帰的にたどる。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    children_url, root = _resolve_root(share_url)
    base = children_url.split("/shares/")[0]

    if "folder" not in root:
        # 単一ファイルが共有された場合
        return _download_file(root, dest_dir, extensions)

    downloaded: list[Path] = []
    for item in _iter_children(children_url):
        if "folder" in item:
            # サブフォルダは driveId + itemId で辿る
            drive_id = item["parentReference"]["driveId"]
            item_id = item["id"]
            sub_url = f"{base}/drives/{drive_id}/items/{item_id}/children"
            for sub in _iter_children(sub_url):
                downloaded += _download_file(sub, dest_dir, extensions)
        else:
            downloaded += _download_file(item, dest_dir, extensions)
    return downloaded


def _download_file(item: dict, dest_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    name = item.get("name", "")
    if not any(name.lower().endswith(ext) for ext in extensions):
        return []
    download_url = next(
        (item[k] for k in DOWNLOAD_URL_KEYS if item.get(k)), None
    )
    if not download_url:
        log.warning("No downloadUrl for %s (keys: %s)", name, list(item.keys())[:10])
        return []
    dest = dest_dir / name
    _download(download_url, dest)
    log.info("Downloaded %s (%d bytes)", name, dest.stat().st_size)
    return [dest]
