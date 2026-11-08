"""
ハンドパン風の瞑想音楽 (録音のヴィブラフォン)。

なぜ (2026-11-01): 最近 6 か月に再生数の多かったメロディ動画の 1 位が、ハンドパン (やわらかい
金属の打楽器) の 1 時間動画で、同じ作者の動画が上位 30 本に 4 本あった。
ハンドパンの録音で自由に使えるものは無いので、同じ「やわらかく響く金属の音」の楽器である
ヴィブラフォンの録音 (Iowa MIS) を、打音を丸めて使う。

音楽の作り: ハンドパンでよく使う Kurd 音階 (A3 を低い「ディン」に、A 短調の音を上に並べる)。
1 小節目の頭でディンを鳴らし、和音 (Am - F - G - Am) の音を 8 分音符の型で、まばらに、
くり返しながら少しずつ変えて鳴らす。下で弓のヴィブラフォンが和音の根音を薄くのばす。
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np

from . import dsp
from . import arrange as A
from .arrange import Clock

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
DING = 57                                           # A3
SCALE = [64, 65, 67, 69, 71, 72, 74, 76]            # E4 F4 G4 A4 B4 C5 D5 E5
CHORDS = [(69, (69, 72, 76, 64)), (65, (65, 69, 72, 76)), (67, (67, 71, 74, 65)), (69, (69, 72, 76, 64))]
# 8 分音符 8 つ分の型 (1 = 鳴らす)。ゆったりした曲なので密度は低め
RHYTHMS = [
    (1, 0, 0, 1, 0, 0, 1, 0),
    (1, 0, 1, 0, 0, 1, 0, 0),
    (0, 0, 1, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 1, 0, 1, 0),
    (0, 1, 0, 0, 1, 0, 0, 0),
]
_BANK: dict[str, dict[int, np.ndarray]] = {}


def _bank(kind: str) -> dict[int, np.ndarray]:
    if kind not in _BANK:
        d = SAMPLES / f"vibes_{kind}_clean"
        _BANK[kind] = {int(p.stem[1:]): np.load(p).astype(np.float32) for p in d.glob("m*.npy")}
    return _BANK[kind]


def _pitched(kind: str, midi: int, sr: int) -> np.ndarray:
    from scipy import signal as sg
    bank = _bank(kind)
    keys = np.array(sorted(bank))
    base = int(keys[np.argmin(np.abs(keys - midi))])
    x = bank[base]
    r = float(dsp.midi2hz(midi)) / (440.0 * 2.0 ** ((base - 69) / 12.0))
    if abs(r - 1.0) > 1e-4:
        fr = Fraction(1.0 / r).limit_denominator(2000)
        x = sg.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)
    return x


_HIT_CACHE: dict[tuple[int, int], np.ndarray] = {}


def hit(midi: int, vel: float, sr: int = dsp.SR) -> np.ndarray:
    """
    叩いた音。ヴィブラフォンは硬いマレットの ff 録音なので、
    ・最初の 6ms をなだらかにして「手でたたいた」ような丸い立ち上がりに
    ・2 次の低域通過で、金属の硬い倍音を抑える (強く叩くほど明るく)
    """
    from scipy import signal as sg
    key = (midi, int(vel * 20))
    if key not in _HIT_CACHE:
        x = _pitched("sustain", midi, sr)[: int(9.0 * sr)].copy()
        na = int(0.006 * sr)
        x[:na] *= np.linspace(0, 1, na, dtype=np.float32)
        x = dsp.fade(x, fade_out=2.0)
        # 試聴 1 回目は 1500Hz からで、こもった (1kHz が基準帯の -25dB)。ハンドパンらしい
        # 2〜4kHz のきらめきを残すところまで上げる
        sos = sg.butter(2, 2800.0 + 3600.0 * vel ** 2, "lowpass", fs=sr, output="sos")
        y = sg.sosfilt(sos, x)
        # ハンドパンは 1 つの音の中で「1 オクターブ上」と「その 5 度上」も鳴るように調律されている。
        # ヴィブラフォンはほぼ基音だけなので、その 2 つを薄く重ねてハンドパンの響きに寄せる
        for up, g in ((12, 0.32), (19, 0.12)):
            if midi + up <= 89:
                z = _pitched("sustain", midi + up, sr)[: len(y)]
                z = sg.sosfilt(sos, z) * g
                y[: len(z)] += z
        _HIT_CACHE[key] = (y * 3.0).astype(np.float32)
    return _HIT_CACHE[key] * np.float32(vel)


def drone(midi: int, dur: float, sr: int = dsp.SR) -> np.ndarray:
    """弓のヴィブラフォンを、録音の中ほどをクロスフェードでつないで dur 秒にのばす"""
    x = _pitched("bow", midi, sr)
    a, b = int(len(x) * 0.25), int(len(x) * 0.80)
    seg = x[a:b]
    xf = min(int(0.8 * sr), len(seg) // 3)
    need = int(dur * sr)
    out = x[:b].copy()
    while len(out) < need:
        f = np.linspace(0, 1, xf, dtype=np.float32)
        out[-xf:] = out[-xf:] * (1 - f) + seg[:xf] * f
        out = np.concatenate([out, seg[xf:]])
    out = out[:need].copy()
    n = min(int(2.5 * sr), need // 3)
    out[:n] *= np.linspace(0, 1, n, dtype=np.float32) ** 2
    out[-n:] *= np.linspace(1, 0, n, dtype=np.float32) ** 2
    return out


def build_handpan(spec, seconds: float):
    from . import tracks as TR
    sr = dsp.SR
    rng = np.random.default_rng(spec.seed)
    bpm = spec.bpm
    beat = 60.0 / bpm
    bar = 4 * beat
    n_bars = int((seconds - 6.0) / bar)
    clock = Clock(total_seconds=seconds, bars=max(int(seconds / bar), 4), beats_per_bar=4)
    n = clock.n_samples
    buf = np.zeros((n + int(12 * sr), 2), dtype=np.float32)
    pad = np.zeros_like(buf)

    t0 = 2.0
    prev = 69
    rhythm = RHYTHMS[0]
    for b in range(n_bars):
        root, tones = CHORDS[(b // 2) % len(CHORDS)]
        section = (b // 16) % 4                     # 16 小節ごとに密度を変える (静 → 中 → 少し動く → 静)
        if b % 4 == 0:
            rhythm = RHYTHMS[int(rng.integers(0, len(RHYTHMS)))]
        bt = t0 + b * bar
        # 低いディン (1 小節目の頭)。静かな部分では 2 小節に 1 回
        if section != 0 or b % 2 == 0:
            A.add_panned(buf, hit(DING, float(rng.uniform(0.42, 0.50))), int(bt * sr), 0.55, 0.0)
        for i, on in enumerate(rhythm):
            if not on or (section == 0 and rng.random() < 0.35) or (section == 3 and i > 4):
                continue
            # 旋律: 和音の音を中心に、前の音から近い音へ (大きな跳躍を避ける)
            cand = [m for m in SCALE if abs(m - prev) <= 5] or SCALE
            w = np.array([3.0 if (m % 12) in {t % 12 for t in tones} else 1.0 for m in cand])
            w /= w.sum()
            m = int(rng.choice(cand, p=w))
            prev = m
            vel = float(np.clip(rng.normal(0.46 if i % 2 == 0 else 0.38, 0.04), 0.28, 0.56))
            tt = bt + i * beat / 2 + float(rng.normal(0, 0.008))
            A.add_panned(buf, hit(m, vel), int(tt * sr), 0.50, float(np.clip((m - 70) / 20, -0.4, 0.4)))
        # 弓のドローン: 2 小節ごとに和音の根音 (下の音域) をのばす
        if b % 2 == 0:
            d = drone(root - 12 if root - 12 >= 53 else root, 2 * bar + 2.0, sr)
            A.add_panned(pad, d, int(bt * sr), 0.12, -0.15)
    buf += pad
    ir = dsp.make_reverb_ir(4.0, rt60=3.4, damp=0.45, predelay=0.03, width=0.7, seed=spec.seed)

    def master(x):
        x = dsp.shelf(x, 2500.0, 2.0, kind="high")
        x = dsp.lowpass(x, 11000.0, order=2)
        return dsp.highpass(x, 45.0, order=2)

    out, info = TR._finish(buf, clock, spec, ir, 0.38, [], master)
    info["bars"] = n_bars
    return out, info
