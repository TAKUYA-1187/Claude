"""
短いオリジナルのピアノ曲を、楽譜データ (和音・旋律) から録音のピアノで演奏する汎用の部品。2026-11-08。

orig01.py と同じ考え方 (旋律と半音でぶつかる伴奏の音を抜く・低音を濁らせない・控えめな残響) を、
曲ごとに拍子・速さ・伴奏の型・低音の下限を変えられるようにしたもの。orig01 自体は再現性のため触らない。
Shorts 用の 20 秒前後の曲 (pets.py) で使う。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import dsp
from . import arrange as A
from . import instruments as I
from .orig01 import note_num, chord


@dataclass
class Piece:
    slug: str
    bpm: float
    bar: float                                  # 1 小節の拍数 (4 分音符)
    sections: list[tuple[str, str]]             # (部分名, 和音を 1 小節ずつ。"," で等分)
    melody: dict[str, str]                      # 部分名 → "音名/拍 ..."
    acc_style: dict[str, str]                   # 部分名 → "eighths" / "waltz" / "quarters" / "open5"
    bass_lo: int = 41                           # 低音の下限 (F2)
    upper_lo: int = 48                          # 和音の音の下限 (C3)
    ritard_bars: int = 2
    tail_s: float = 3.0
    reverb_send: float = 0.20
    seed: int = 1
    mel_gain: float = 0.42
    acc_gain: float = 0.34
    mel_vel: dict[str, float] = field(default_factory=dict)


def score(p: Piece):
    mel, chs, t0 = [], [], 0.0
    for sec, spec in p.sections:
        bars = spec.split()
        t = t0
        for b in bars:
            parts = b.split(",")
            for c in parts:
                chs.append((t, p.bar / len(parts), c, sec))
                t += p.bar / len(parts)
        t = t0
        for tok in p.melody[sec].replace("|", " ").split():
            n, d = tok.split("/")
            d = float(d)
            if n != "R":
                mel.append((t, d, note_num(n), sec))
            t += d
        assert abs(t - (t0 + p.bar * len(bars))) < 1e-6, (p.slug, sec, t - t0, p.bar * len(bars))
        t0 += p.bar * len(bars)
    return mel, chs, t0


def time_map(p: Piece, total: float):
    beat = 60.0 / p.bpm
    n_bars = int(round(total / p.bar))
    factors = [1.0] * n_bars
    for i in range(p.ritard_bars):
        b = n_bars - p.ritard_bars + i
        factors[b] = 1.0 + 0.07 * (i + 1)
    starts = np.concatenate([[0.0], np.cumsum([p.bar * beat * f for f in factors])])

    def t(q: float) -> float:
        b = min(int(q // p.bar), n_bars - 1)
        return float(starts[b] + (q - b * p.bar) * beat * factors[b])
    return t


def accompaniment(p: Piece, chs, mel):
    out = []
    for s, d, name, sec in chs:
        bass_pc, pcs = chord(name)
        bass = p.bass_lo + (bass_pc - p.bass_lo) % 12
        upper = [c for c in pcs if c != bass_pc] or pcs
        voic = sorted(p.upper_lo + (c - p.upper_lo) % 12 for c in upper)
        mel_pcs = {m % 12 for ms, md, m, _ in mel if ms < s + d and s < ms + md}
        voic = [v for v in voic if all((v - mp) % 12 not in (1, 11) for mp in mel_pcs)] or voic[:1]
        u = [voic[i % len(voic)] for i in range(3)]
        style = p.acc_style[sec]
        if style == "eighths":
            seq, step = [bass, u[0], u[1], u[2], u[1], u[0], u[1], u[2]], 0.5
        elif style == "waltz":
            seq, step = [bass, u[0], u[1], u[2], u[1], u[0]], 0.5
        elif style == "open5":
            # 低音の 5 度も旋律と半音でぶつかるなら、1 オクターブ上の低音に替える
            # (pet03 の 1 回目：旋律 C#5 と 5 度の D4 が短 9 度でぶつかった)
            fifth = bass + 7
            if any((fifth - mp) % 12 in (1, 11) for mp in mel_pcs):
                fifth = bass + 12
            seq, step = [bass, fifth, u[0], u[1]], 1.0
        else:
            seq, step = [bass, u[0], u[1], u[2]], 1.0
        seq = seq[: int(round(d / step))]
        for i, m in enumerate(seq):
            out.append((s + i * step, d - i * step, m, 0.29 if i == 0 else 0.21 * (1.0 - 0.05 * (i % 2))))
    return out


def render(p: Piece, sr: int = dsp.SR):
    rng = np.random.default_rng(p.seed)
    mel, chs, total = score(p)
    acc = accompaniment(p, chs, mel)
    tm = time_map(p, total)
    end_s = tm(total) + p.tail_s
    n = int(end_s * sr)
    buf = np.zeros((n, 2), dtype=np.float32)
    bank = I.SampleBank(seed=p.seed, n_variants=3)

    def put(q, dur_q, m, vel, gain, pan, legato):
        t = max(0.0, tm(q) + float(rng.normal(0, 0.004)))
        x = bank.note("soft_piano", int(m), float(np.clip(vel + rng.normal(0, 0.012), 0.15, 0.7)))
        hold = int((tm(q + dur_q) - tm(q) + legato) * sr)
        if hold < len(x):
            nr = min(int(0.35 * sr), len(x) - hold)
            x = x[:hold + nr].copy()
            x[hold:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 2
        A.add_panned(buf, x, int(t * sr), gain, pan)

    for s, d, m, sec in mel:
        vel = p.mel_vel.get(sec, 0.40) + 0.03 * float(np.clip((m - 72) / 7, -1, 1))
        put(s, d, m, vel, p.mel_gain, 0.08, 0.12)
    for s, d, m, vel in acc:
        put(s, d, m, vel, p.acc_gain, -0.12 if m < 55 else -0.02, 0.05)

    ir = dsp.make_reverb_ir(2.2, rt60=1.8, damp=0.55, predelay=0.02, width=0.6, seed=p.seed)
    x = dsp.reverb(buf, ir, mix=p.reverb_send, tail=True)[:n]
    x = dsp.shelf(x, 3000.0, 2.0, kind="high")
    x = dsp.lowpass(x, 12000.0, order=2)
    x = dsp.highpass(x, 40.0, order=2)
    nf = int(min(2.5, p.tail_s) * sr)
    x[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None] ** 2
    x, info = dsp.normalize_lufs(x, target=-14.0, ceiling_db=-1.0)
    info.update(mel=mel, chords=chs, acc=acc, total_beats=total, end_s=end_s,
                section_times=[(c[3], round(tm(c[0]), 2)) for i, c in enumerate(chs) if i == 0 or chs[i - 1][3] != c[3]],
                lowest_note=min(m for _, _, m, _ in acc), onsets=sorted({round(tm(s), 3) for s, *_ in mel} |
                                                                     {round(tm(s), 3) for s, *_ in acc}))
    return x, info
