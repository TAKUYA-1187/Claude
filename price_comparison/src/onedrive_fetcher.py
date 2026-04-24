"""OneDrive の匿名共有フォルダから CSV を取得する。

Microsoft Graph の `/shares/{token}/driveItem` エンドポイントは、
アクセス権のある共有リンク (表示/編集) に対して匿名でもアクセスできる。
各ファイルの直リンク (`@microsoft.graph.downloadUrl`) をたどってダウンロード。

Docs: https://learn.microsoft.com/graph/api/shares-get
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _encode_share_url(url: str) -> str:
    b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return "u!" + b64


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16))
def _get_json(url: str) -> dict:
    r = requests.get(url, timeout=30)
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


def fetch_folder(share_url: str, dest_dir: Path, extensions: tuple[str, ...] = (".csv",)) -> list[Path]:
    """共有フォルダ直下のファイルを取得。サブフォルダは再帰的にたどる。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    token = _encode_share_url(share_url)
    root_url = f"{GRAPH_BASE}/shares/{token}/driveItem"
    root = _get_json(root_url)

    if "folder" not in root:
        # 単一ファイルが共有された場合
        return _download_file(root, dest_dir, extensions)

    # フォルダの場合 → children を列挙
    children_url = f"{GRAPH_BASE}/shares/{token}/driveItem/children"
    downloaded: list[Path] = []
    for item in _iter_children(children_url):
        if "folder" in item:
            # サブフォルダは driveId + itemId で辿る
            drive_id = item["parentReference"]["driveId"]
            item_id = item["id"]
            sub_url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/children"
            for sub in _iter_children(sub_url):
                downloaded += _download_file(sub, dest_dir, extensions)
        else:
            downloaded += _download_file(item, dest_dir, extensions)
    return downloaded


def _download_file(item: dict, dest_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    name = item.get("name", "")
    if not any(name.lower().endswith(ext) for ext in extensions):
        return []
    download_url = item.get("@microsoft.graph.downloadUrl")
    if not download_url:
        log.warning("No downloadUrl for %s", name)
        return []
    dest = dest_dir / name
    _download(download_url, dest)
    log.info("Downloaded %s (%d bytes)", name, dest.stat().st_size)
    return [dest]
