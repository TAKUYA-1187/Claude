"""
そり鈴 (スレイベル) の録音。2026-11-15。

音源：Versilian Community Sample Library (VCSL) の Idiophones/Struck Idiophones/Sleigh Bells
  - ライセンス：CC0 1.0 (商用可・無償・表示も不要)。原文と sha256 は data/licenses/vcsl_sleigh_bells/
  - 取得：https://github.com/sgossner/vcsl (commit c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e) を
    prepare_vcsl_sleigh.py で samples/vcsl_sleigh_bells/ へ写す (samples/ は git に入れない)
  - 使うのは 2 組目 (sleighbell2_*、44.1kHz/24bit)。1 組目 (Sleighbells_Hit_rr*) より音の重心が低く (約 7kHz、1 組目は約 10kHz) 柔らかい

鈴は音程がないので、高さ合わせの再サンプリングはしない。録音のレートは 44.1kHz で、エンジンと同じ (読み込み時に確かめる)。
旧 instruments.sleigh_real (タンバリンのシェイクを 5 度下げた代用品) は使わない。
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from scipy import signal as _sig

from . import dsp

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "samples" / "vcsl_sleigh_bells"
SHA256 = {
    "sleighbell2_hit_2.wav": "7e872bb764f789697bf33850c3918cf6a5963d7a0de4ed14d77c843460086bb2",
    "sleighbell2_hit_loud.wav": "356166c87916ef63bba6539a0d4eda1881d1ddb1ba8045668058e62b91fbcf17",
    "sleighbell2_shake1.wav": "e34644affa5dd56af5e2a93c8330b39f96c74b0671d69878815a5f14f6704b89",
}
LOWPASS_HZ = 6500.0          # 耳に刺さらないように、これより上を丸める (2 次)


def _read(name: str) -> np.ndarray:
    with wave.open(str(DIR / name)) as w:
        assert w.getframerate() == dsp.SR, (name, w.getframerate())
        assert w.getnchannels() == 2 and w.getsampwidth() == 3, (name, w.getsampwidth())
        raw = w.readframes(w.getnframes())
    b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
    v = b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16)
    v = np.where(v >= 1 << 23, v - (1 << 24), v)
    return (v.astype(np.float32) / float(1 << 23)).reshape(-1, 2)


def _soften(x: np.ndarray) -> np.ndarray:
    sos = _sig.butter(2, LOWPASS_HZ, "lowpass", fs=dsp.SR, output="sos")
    return _sig.sosfilt(sos, x, axis=0).astype(np.float32)


class Sleigh:
    def __init__(self, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        hits = []
        for name in ("sleighbell2_hit_2.wav", "sleighbell2_hit_loud.wav"):
            x = _read(name)
            a = np.abs(x).max(axis=1)
            on = int(np.argmax(a > 0.25 * a.max()))      # 振った瞬間 (hit_loud は前に小さな揺れがある)
            x = x[max(0, on - int(0.008 * dsp.SR)):]
            x = x / np.sqrt((x[: int(0.3 * dsp.SR)] ** 2).mean())   # 最初の 0.3 秒の RMS をそろえる
            n = len(x)
            nf = min(n, int(0.25 * dsp.SR))
            x[n - nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]
            nfi = int(0.004 * dsp.SR)
            x[:nfi] *= np.linspace(0, 1, nfi, dtype=np.float32)[:, None]
            hits.append(_soften(x))
        self.hits = hits
        s = _read("sleighbell2_shake1.wav")
        self.shake_src = _soften(s / np.sqrt((s ** 2).mean()))
        self.count = {"hit": 0, "shake": 0}

    def hit(self, gain_db: float) -> np.ndarray:
        """1 回振る。2 つの録音を交互に使い、音量を ±1.5 dB 揺らす"""
        k = self.count["hit"] % 2
        self.count["hit"] += 1
        g = dsp.db2lin(gain_db + float(self.rng.normal(0, 0.75)))
        return (self.hits[k] * g).astype(np.float32)

    def shake(self, seconds: float, gain_db: float, fade_in: float = 0.15, fade_out: float = 1.2) -> np.ndarray:
        """振り続ける音を seconds 秒。入りと消えをなめらかに"""
        self.count["shake"] += 1
        n = min(int(seconds * dsp.SR), len(self.shake_src))
        start = int(self.rng.integers(int(0.2 * dsp.SR), max(int(0.2 * dsp.SR) + 1, len(self.shake_src) - n)))
        x = self.shake_src[start:start + n].copy()
        fi, fo = int(fade_in * dsp.SR), min(n, int(fade_out * dsp.SR))
        x[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]
        x[n - fo:] *= (np.linspace(1, 0, fo, dtype=np.float32) ** 2)[:, None]
        return (x * dsp.db2lin(gain_db)).astype(np.float32)
