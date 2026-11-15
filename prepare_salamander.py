#!/usr/bin/env python3
"""
Salamander Grand Piano V3 を取得し、sha256 を確かめて展開する。2026-11-15。

    python3 prepare_salamander.py                     # 44.1kHz/16bit 版 (x05r v2 まで)
    python3 prepare_salamander.py --variant 48k24     # 原本 48kHz/24bit 版 (x05r v3 = x05r_60s。約 1.2 GB、展開後 1.9 GB)

- 取得元：FreePats (https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html)
- ライセンス：CC BY 3.0 (作者 Alexander Holm)。原文と同梱の README は data/licenses/salamander_grand_piano_v3/
- samples/ は git に入れない
- ここではレート変換も音量の加工もしない。grand.py が読み込み時に WAV のレートとビット数を確かめる
  (48k24 版は、鳴らすときに音の高さ合わせと 48k→44.1k を 1 回の再サンプリングで行う)
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio.grand import VARIANTS   # noqa: E402

URLS = {"44k16": "https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_44khz16bit.tar.xz",
        "48k24": "https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz"}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="44k16", choices=sorted(VARIANTS))
    a = ap.parse_args()
    v = VARIANTS[a.variant]
    d = v["dir"]
    dst = d.parent / v["archive"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        subprocess.run(["curl", "-sS", "-L", "-o", str(dst), URLS[a.variant]], check=True)
    h = hashlib.sha256(dst.read_bytes()).hexdigest()
    if h != v["sha256"]:
        print(f"sha256 が違います: {h} (期待 {v['sha256']})")
        return 1
    if not (d / "SalamanderGrandPianoV3.sfz").exists():
        subprocess.run(["tar", "-xJf", str(dst), "-C", str(dst.parent)], check=True)
    n = len(list((d / v["wavdir"]).glob("*.wav")))
    print(f"OK: {d} ({n} 個の WAV、{v['sr']} Hz / {v['bits']} bit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
