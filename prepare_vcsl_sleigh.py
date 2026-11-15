#!/usr/bin/env python3
"""
そり鈴の録音 (VCSL、CC0) を samples/vcsl_sleigh_bells/ に用意する。2026-11-15。

    python3 prepare_vcsl_sleigh.py

- 取得元：https://github.com/sgossner/vcsl (commit c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e)
  の Idiophones/Struck Idiophones/Sleigh Bells/ だけを、浅い・部分的な git clone で取る
- ライセンス：CC0 1.0 (原文は data/licenses/vcsl_sleigh_bells/LICENSE_CC0_from_vcsl.txt)
- sha256 を bgm_studio/sleigh.py の SHA256 と照合する。レート変換・加工はしない
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio.sleigh import DIR, SHA256   # noqa: E402

URL = "https://github.com/sgossner/vcsl"
SUB = "Idiophones/Struck Idiophones/Sleigh Bells"


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    if not all((DIR / n).exists() for n in SHA256):
        with tempfile.TemporaryDirectory() as td:
            env = {"GIT_LFS_SKIP_SMUDGE": "1"}
            import os
            env = {**os.environ, **env}
            subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", URL, td + "/vcsl"], check=True, env=env)
            subprocess.run(["git", "-C", td + "/vcsl", "sparse-checkout", "set", "--no-cone", f"/{SUB}/*"], check=True, env=env)
            for p in (Path(td) / "vcsl" / SUB).glob("*.wav"):
                shutil.copy2(p, DIR / p.name)
    bad = [n for n, h in SHA256.items() if hashlib.sha256((DIR / n).read_bytes()).hexdigest() != h]
    if bad:
        print("sha256 が違います:", bad)
        return 1
    print(f"OK: {DIR} ({len(SHA256)} 個を照合)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
