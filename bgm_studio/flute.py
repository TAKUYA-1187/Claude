"""
フルートの瞑想曲 (録音のアルトフルート + タンプーラ風の持続音)。

なぜ (2026-11-01): 最近 6 か月の再生数上位 30 本に、笛と持続音だけの瞑想曲 (インドの
バーンスリー風) が複数あった。バーンスリーの自由に使える録音は無いので、息の多い
やわらかい音の「アルトフルート」(Iowa MIS) で吹く。インドの楽器そのものとは名乗らない。

音楽の作り:
・持続音: タンプーラ (インドの、同じ音をくり返しはじく弦楽器) 風に、Pa - Sa' - Sa' - Sa を
  ゆっくりはじき続ける (倍音を足して作る)。下でチェロが Sa を薄くのばす
・旋律: Sa Re Ga Pa Dha (長調の 5 音音階) の上を、即興のように。1 フレーズ 3〜7 音、
  最後の音を長くのばして Sa・Ga・Pa のどれかで終わる。フレーズの間はしっかり休む
・前半はとても少なく (アーラープ = 導入のように)、少しずつ動きを増やし、また静かに戻る
"""

from __future__ import annotations

import numpy as np

from . import dsp
from . import arrange as A
from . import instruments as I
from .arrange import Clock
from .classical import bowed_note

SA = 62                                         # D4
# Sa Re Ga Pa Dha (2 オクターブ分)。アルトフルートの録音は G3 から
STEPS = [0, 2, 4, 7, 9]
SCALE = [SA - 12 + s for s in STEPS if SA - 12 + s >= 57] + [SA + s for s in STEPS] + [SA + 12 + s for s in STEPS[:3]]
RESTS = {SA, SA + 4, SA + 7, SA + 12}           # フレーズの終わりに置く音


def tanpura_pluck(midi: int, dur: float, rng: np.random.Generator, sr: int = dsp.SR) -> np.ndarray:
    """
    タンプーラ風の 1 回のはじき。倍音がたくさんあり、高い倍音が少し遅れてふくらむ
    (本物は「ジュワリ」という駒で弦が触れて、ジーンと明るくなる) のを、倍音ごとの
    ふくらみの速さを変えて真似る
    """
    f0 = float(dsp.midi2hz(midi))
    n = int(dur * sr)
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, dtype=np.float32)
    for k in range(1, 24):
        fk = f0 * k
        if fk > 7000:
            break
        a = 1.0 / k ** 0.9
        rise = 0.05 + 0.04 * k                  # 高い倍音ほど遅れてふくらむ
        tau = 5.0 / (1.0 + 0.10 * (k - 1))
        env = (1.0 - np.exp(-t / rise)) * np.exp(-t / tau)
        out += (a * env * np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi))).astype(np.float32)
    nr = min(int(0.6 * sr), n // 3)
    out[-nr:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 2
    return out / np.float32(np.abs(out).max() + 1e-9)


def _phrase(rng: np.random.Generator, prev: int, density: float) -> list[tuple[int, float]]:
    """1 フレーズ = [(音, 長さ秒)]。近い音へ動き、最後は休む音で長くのばす"""
    k = int(rng.integers(3, 5 + int(3 * density)))
    out = []
    cur = prev
    for i in range(k):
        cand = [m for m in SCALE if 0 < abs(m - cur) <= 5] or SCALE
        if i == k - 1:
            ends = [m for m in cand if m in RESTS]
            cand = ends or cand
        cur = int(rng.choice(cand))
        if i == k - 1:
            d = float(rng.uniform(3.5, 6.0))
        else:
            d = float(rng.choice([0.8, 1.2, 1.6, 2.4, 3.2], p=[0.15 + 0.15 * density, 0.25, 0.25, 0.2, 0.15 - 0.15 * density]))
        out.append((cur, d))
    return out


def build_flute(spec, seconds: float):
    from . import tracks as TR
    sr = dsp.SR
    rng = np.random.default_rng(spec.seed)
    clock = Clock(total_seconds=seconds, bars=max(int(seconds / 4), 4), beats_per_bar=4)
    n = clock.n_samples
    buf = np.zeros((n + int(12 * sr), 2), dtype=np.float32)
    drone = np.zeros_like(buf)

    # タンプーラ: Pa(A3) Sa'(D4) Sa'(D4) Sa(D3) を 1.25 秒おきに。1 周 5 秒
    cycle = [SA - 5, SA, SA, SA - 12]
    step = 1.25
    t = 0.5
    i = 0
    plucks = {}
    while t < seconds - 2.0:
        m = cycle[i % 4]
        if m not in plucks:
            plucks[m] = [tanpura_pluck(m, 6.0, rng, sr) for _ in range(3)]
        x = plucks[m][int(rng.integers(0, 3))]
        g = 0.20 if i % 4 != 3 else 0.24
        A.add_panned(drone, x, int((t + rng.normal(0, 0.01)) * sr), g * float(rng.uniform(0.9, 1.05)),
                     -0.25 if i % 4 in (1, 2) else -0.1)
        t += step
        i += 1
    # チェロの Sa (D3) を薄く。40 秒ごとにつなぎ直す
    t = 0.0
    while t < seconds:
        d = min(44.0, seconds - t + 4.0)
        A.add_panned(drone, bowed_note("cello", SA - 12, d, 0.30, sr), int(t * sr), 0.07, 0.2)
        t += 40.0

    # 旋律
    t = 8.0
    prev = SA
    end = seconds - 10.0
    while t < end:
        pos = t / seconds
        # 0〜15%: とても少なく / 中ほどで動きが増え / 最後の 15% はまた静かに
        density = float(np.clip(np.sin(np.pi * pos) * 1.2 - 0.1, 0.0, 1.0))
        ph = _phrase(rng, prev, density)
        for j, (m, d) in enumerate(ph):
            if t + d > end:
                break
            vel = float(np.clip(rng.normal(0.42 + 0.06 * density, 0.03), 0.32, 0.55))
            # 前の音と少し重ねて、息をつながった感じに (レガート)
            x = bowed_note("altoflute", m, d + 0.10, vel, sr)
            A.add_panned(buf, x, int(t * sr), 0.9, 0.05)
            t += d
            prev = m
        t += float(rng.uniform(2.5, 5.0) - 1.5 * density)
    # 旋律と持続音の比: 旋律を持続音より 9dB 上に
    rm = float(np.sqrt(np.mean(buf.astype(np.float64) ** 2))) + 1e-9
    rd = float(np.sqrt(np.mean(drone.astype(np.float64) ** 2))) + 1e-9
    buf += drone * np.float32(rm / rd * 10 ** (-9 / 20))
    ir = dsp.make_reverb_ir(4.5, rt60=3.8, damp=0.5, predelay=0.035, width=0.75, seed=spec.seed)

    def master(x):
        x = dsp.shelf(x, 3000.0, 1.5, kind="high")
        x = dsp.lowpass(x, 12000.0, order=2)
        return dsp.highpass(x, 45.0, order=2)

    out, info = TR._finish(buf, clock, spec, ir, 0.40, [], master)
    return out, info
