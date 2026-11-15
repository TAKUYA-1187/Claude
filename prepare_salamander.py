#!/usr/bin/env python3
"""
Salamander Grand Piano V3 (44.1kHz/16bit 版) を取得して展開する。2026-11-15。

    python3 prepare_salamander.py

- 取得元：FreePats (https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html)
- ライセンス：CC BY 3.0 (作者 Alexander Holm)。原文と同梱の README は data/licenses/salamander_grand_piano_v3/
- 約 394 MiB をダウンロードし、展開後は約 1.2 GB (samples/ は git に入れない)
- 録音の WAV は 44.1kHz のまま使う。ここではレート変換も音量の加工もしない (grand.py が読み込み時にレートを確かめる)
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio.grand import ARCHIVE_SHA256, SAL_DIR   # noqa: E402

URL = ("https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/"
       "SalamanderGrandPianoV3+20161209_44khz16bit.tar.xz")
DST = SAL_DIR.parent / "SalamanderGrandPianoV3_44khz16bit.tar.xz"


def main() -> int:
    DST.parent.mkdir(parents=True, exist_ok=True)
    if not DST.exists():
        subprocess.run(["curl", "-sS", "-L", "-o", str(DST), URL], check=True)
    h = hashlib.sha256(DST.read_bytes()).hexdigest()
    if h != ARCHIVE_SHA256:
        print(f"sha256 が違います: {h} (期待 {ARCHIVE_SHA256})")
        return 1
    if not (SAL_DIR / "SalamanderGrandPianoV3.sfz").exists():
        subprocess.run(["tar", "-xJf", str(DST), "-C", str(DST.parent)], check=True)
    n = len(list((SAL_DIR / "44.1khz16bit").glob("*.wav")))
    print(f"OK: {SAL_DIR} ({n} 個の WAV)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
