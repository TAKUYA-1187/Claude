"""OneDrive の匿名共有フォルダから CSV を取得する。

個人向け OneDrive の「リンクを知っている全員」共有は、2024年以降
`api.onedrive.com` / `graph.microsoft.com` の `/shares/` を匿名で呼ぶと HTTP 401 になる
（2026-07 の実行ログで両方 401 を確認）。

現在の OneDrive Web 画面は、匿名閲覧時に Badger トークン
(`api-badgerp.svc.ms`) を取得し、`my.microsoftpersonalcontent.com` の
`/shares/` API を呼んでいる。これを第一候補とし、旧エンドポイントはフォールバックに残す。
Badger は非公開APIのため、Microsoft 側の変更で使えなくなる可能性がある。

ログには共有URL・共有ID・トークンを出さない（HTTPステータスとエラーコードのみ）。
"""
from __future__ import annotations

import base64
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import requests

log = logging.getLogger(__name__)

BADGER_TOKEN_URL = "https://api-badgerp.svc.ms/v1.0/token"
# OneDrive Web が匿名共有の閲覧に使っているアプリID
BADGER_APP_ID = "5cbed6ac-a083-4e14-b191-b4ba07653de2"

DOWNLOAD_URL_KEYS = ("@content.downloadUrl", "@microsoft.graph.downloadUrl")
TIMEOUT = 30


class OneDriveFetchError(RuntimeError):
    pass


@dataclass
class _Strategy:
    name: str
    base: str
    root_seg: str
    headers: Callable[[], dict]


def _encode_share_url(url: str) -> str:
    b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return "u!" + b64


def _describe_error(r: requests.Response) -> str:
    try:
        err = r.json().get("error", {})
        code = err.get("code", "")
    except ValueError:
        code = ""
    return f"HTTP {r.status_code}" + (f" ({code})" if code else "")


def _get_json(url: str, headers: dict) -> dict:
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    if not r.ok:
        raise OneDriveFetchError(_describe_error(r))
    return r.json()


def _badger_headers_factory() -> Callable[[], dict]:
    cache: dict[str, str] = {}

    def headers() -> dict:
        if "token" not in cache:
            r = requests.post(BADGER_TOKEN_URL, json={"appId": BADGER_APP_ID}, timeout=TIMEOUT)
            if not r.ok:
                raise OneDriveFetchError(f"token {_describe_error(r)}")
            cache["token"] = r.json()["token"]
        return {"Authorization": f"Badger {cache['token']}", "Prefer": "autoredeem"}

    return headers


def _strategies() -> list[_Strategy]:
    return [
        _Strategy("badger", "https://my.microsoftpersonalcontent.com/_api/v2.0", "driveItem", _badger_headers_factory()),
        _Strategy("onedrive-api", "https://api.onedrive.com/v1.0", "root", lambda: {}),
        _Strategy("graph", "https://graph.microsoft.com/v1.0", "driveItem", lambda: {}),
    ]


def _share_url_variants(share_url: str) -> list[str]:
    """短縮リンク (1drv.ms) はリダイレクト先URLも候補にする。"""
    variants = [share_url.strip()]
    try:
        r = requests.get(variants[0], allow_redirects=False, timeout=TIMEOUT)
        location = r.headers.get("Location")
        if location and location not in variants:
            variants.append(location)
    except requests.RequestException as e:
        log.info("Share link redirect lookup skipped: %s", type(e).__name__)
    return variants


def _iter_children(url: str, headers: Callable[[], dict]) -> Iterable[dict]:
    while url:
        data = _get_json(url, headers())
        yield from data.get("value", [])
        url = data.get("@odata.nextLink")


def _download_file(item: dict, dest_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    name = item.get("name", "")
    if not name.lower().endswith(extensions):
        return []
    download_url = next((item[k] for k in DOWNLOAD_URL_KEYS if item.get(k)), None)
    if not download_url:
        log.warning("No download URL for %s", name)
        return []
    dest = dest_dir / Path(name).name
    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
    log.info("Downloaded a .%s file (%d bytes)", _kind(item), dest.stat().st_size)
    return [dest]


MAX_DEPTH = 3


def _kind(item: dict) -> str:
    if "folder" in item:
        return "folder"
    suffix = Path(item.get("name", "")).suffix.lower().lstrip(".")
    return suffix or "no-ext"


def _fetch_with(strategy: _Strategy, share_id: str, dest_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    root_url = f"{strategy.base}/shares/{share_id}/{strategy.root_seg}"
    root = _get_json(root_url, strategy.headers())
    if "folder" not in root:
        log.info("OneDrive share is a single file (.%s)", _kind(root))
        return _download_file(root, dest_dir, extensions)

    downloaded: list[Path] = []
    seen: Counter[str] = Counter()

    def walk(children_url: str, depth: int) -> None:
        nonlocal downloaded
        for item in _iter_children(children_url, strategy.headers):
            seen[_kind(item)] += 1
            if "folder" in item:
                if depth < MAX_DEPTH:
                    drive_id = item["parentReference"]["driveId"]
                    walk(f"{strategy.base}/drives/{drive_id}/items/{item['id']}/children", depth + 1)
            else:
                downloaded += _download_file(item, dest_dir, extensions)

    walk(f"{root_url}/children", 1)
    # 公開リポジトリのログに残るため、ファイル名は出さず種類ごとの件数だけ記録する
    log.info("OneDrive shared folder contents (by type, up to %d levels): %s", MAX_DEPTH, dict(seen) or "empty")
    return downloaded


def fetch_folder(
    share_url: str, dest_dir: Path, extensions: tuple[str, ...] = (".csv", ".numbers")
) -> list[Path]:
    """共有フォルダ（または単一ファイル）の CSV を dest_dir に保存する。サブフォルダは3階層までたどる。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    variants = _share_url_variants(share_url)
    for strategy in _strategies():
        for i, url in enumerate(variants):
            label = f"{strategy.name}/{'link' if i == 0 else 'redirect'}"
            try:
                files = _fetch_with(strategy, _encode_share_url(url), dest_dir, extensions)
            except OneDriveFetchError as e:
                reason = f"{label}: {e}"
            except (requests.RequestException, KeyError, ValueError) as e:
                # 例外メッセージにはURL（共有IDやダウンロード用トークン）が含まれうるので型名だけ残す
                reason = f"{label}: {type(e).__name__}"
            else:
                log.info("OneDrive share resolved via %s", label)
                return files
            log.warning("OneDrive %s", reason)
            errors.append(reason)
    raise OneDriveFetchError(
        "OneDrive共有フォルダからCSVを取得できませんでした（"
        + " / ".join(errors)
        + "）。共有が「リンクを知っている全員」になっているか、リンクを作り直していないかを確認してください。"
    )
