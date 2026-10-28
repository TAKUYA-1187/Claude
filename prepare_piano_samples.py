#!/usr/bin/env python3
"""
本物のピアノの録音 (University of Iowa Electronic Music Studios の Musical Instrument
Samples) を取り込み、雑音を取り除いて samples/piano_clean/ に保存する。

なぜ: 2026-10-28 のオーナーの評価「メロディーが機械音で聞きにくい」。
これまでのピアノは倍音を足し算して作った合成音で、どう調整しても「電子音」に聞こえる。
実際のピアノ (スタインウェイ) を 1 音ずつ録った音に置き換える。

素材の条件: 公式サイトに "freely available ... may be downloaded and used for any projects,
without restrictions" と明記されている (https://theremin.music.uiowa.edu/MIS.html)。

処理:
  - mf (中くらいの強さ) だけを使う。pp は録音レベルが低く、雑音との差が 10〜20dB しかない
  - 発音の頭にそろえて切る
  - 末尾 1 秒から雑音のスペクトルを測り、スペクトル減算で取り除く (サーという雑音を消す)
  - 音が雑音の近くまで減衰したところでフェードアウトして切る
  - 全音に同じ倍率をかけて正規化する (音域ごとの自然な音量差は残す)

    python3 prepare_piano_samples.py          # ダウンロードから全部
    python3 prepare_piano_samples.py --skip-download
"""

from __future__ import annotations

import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import signal

from bgm_studio import video as VID

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "samples" / "iowa_piano"
CLEAN = ROOT / "samples" / "piano_clean"
SR = 48000
LO, HI = 36, 96            # C2〜C7
NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
URL = "https://theremin.music.uiowa.edu/sound%20files/MIS/Piano_Other/piano/Piano.mf.{}.aiff"


def note_name(m: int) -> str:
    return NAMES[m % 12] + str(m // 12 - 1)


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    def get(m: int) -> None:
        dst = RAW / f"Piano.mf.{note_name(m)}.aiff"
        if not dst.exists():
            subprocess.run(["curl", "-sS", "--retry", "3", "-o", str(dst), URL.format(note_name(m))],
                           check=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(get, range(LO, HI + 1)))


def load(path: Path) -> np.ndarray:
    p = subprocess.run([VID.ffmpeg_exe(), "-loglevel", "error", "-i", str(path),
                        "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, 2).copy()


def env_db(m: np.ndarray, win: float = 0.01) -> np.ndarray:
    n = max(int(win * SR), 1)
    e = np.sqrt(np.convolve(m.astype(np.float64) ** 2, np.ones(n) / n, "same"))
    return 20 * np.log10(e + 1e-12)


def clean(x: np.ndarray) -> np.ndarray:
    m = x.mean(axis=1)
    db = env_db(m)
    pk = db.max()
    # 打鍵の前に小さな物音が入っている録音がある (C3 など)。-40dB を基準にすると
    # それを音の頭と誤認したので、最大音量の直前で -20dB を超えた点を頭にする
    ipk = int(np.argmax(db))
    pre = np.where(db[:ipk] < pk - 20)[0]
    onset = int(pre[-1]) + 1 if len(pre) else 0
    start = max(onset - int(0.004 * SR), 0)

    # 雑音のスペクトルは録音の最後 1 秒 (音がほぼ消えたところ) から測る
    nper, nover = 2048, 1536
    tail = x[-SR:]
    _, _, Nt = signal.stft(tail.T, fs=SR, nperseg=nper, noverlap=nover)
    noise = np.abs(Nt).mean(axis=-1, keepdims=True)                   # (2, F, 1)

    y = x[start:]
    _, _, X = signal.stft(y.T, fs=SR, nperseg=nper, noverlap=nover)
    mag = np.abs(X)
    # パワーのスペクトル減算 (ウィーナー型)。振幅で雑音の 2 倍を引く方式では、
    # 雑音よりわずかに大きいだけの高い倍音まで消えて、4kHz より上がほぼ無くなった
    # (C4: -44dB → -66dB)。雑音より 2 倍以上大きい成分はほぼそのまま残る
    g = np.sqrt(np.clip(1.0 - 1.5 * (noise / (mag + 1e-12)) ** 2, 0.0, 1.0))
    g = signal.lfilter([0.35], [1.0, -0.65], g, axis=-1)
    g = np.maximum(g, 0.0)
    _, yc = signal.istft(X * g, fs=SR, nperseg=nper, noverlap=nover)
    yc = yc.T[: len(y)].astype(np.float32)

    # 低いうなり (空調など) を切る
    sos = signal.butter(2, 30.0, "highpass", fs=SR, output="sos")
    yc = signal.sosfilt(sos, yc, axis=0).astype(np.float32)

    # 減衰して雑音の近くまで来たところで切る (余韻はリバーブで補う)
    dbc = env_db(yc.mean(axis=1), 0.05)
    pkc = dbc.max()
    s0 = int(np.argmax(dbc)) + int(0.3 * SR)          # 最大音量の後から探す
    after = np.where(dbc[s0:] < pkc - 58)[0]
    end = s0 + int(after[0]) if len(after) else len(yc)
    end = min(end + int(0.4 * SR), len(yc))
    yc = yc[:end]
    nf = min(int(1.2 * SR), len(yc) // 3)
    yc[-nf:] *= np.linspace(1.0, 0.0, nf, dtype=np.float32)[:, None] ** 2
    return yc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()
    if not args.skip_download:
        download()
    CLEAN.mkdir(parents=True, exist_ok=True)
    out = {}
    for m in range(LO, HI + 1):
        out[m] = clean(load(RAW / f"Piano.mf.{note_name(m)}.aiff"))
    peak = max(float(np.abs(v).max()) for v in out.values())
    for m, v in out.items():
        np.save(CLEAN / f"m{m}.npy", (v * (0.9 / peak)).astype(np.float32))
    lens = [len(v) / SR for v in out.values()]
    print(f"{len(out)} 音を {CLEAN} に保存 (長さ {min(lens):.1f}〜{max(lens):.1f} 秒)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
