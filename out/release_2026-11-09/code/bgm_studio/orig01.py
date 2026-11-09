"""
orig01_winter_reading_piano — 新しく作曲したピアノ曲 (既存の曲を借りない)。

なぜ (2026-11-07): 保留中のクリスマス・冬の動画は、使った譜面データの利用条件が商用に合わず、
公開できない。権利の確認が「録音サンプル (Iowa, 制限なし) と自分のコード」だけで済む、
オリジナルの旋律・和声・構成の曲を作る。用途は「静かな読書・夜の作業」。

曲の作り (4/4、F 長調、♩=64、46 小節 ≒ 3 分):
  前奏 4 小節 (伴奏だけ) → A 8 → A' 8 → B 8 (ニ短調) → つなぎ 4 → A'' 8 → 終わり 6 (少しずつ遅く)
・A は「上がって開く」主題 (ラ-ド-ファ)。A' は同じ頭で始まり、主音に下りて閉じる
・B は平行調のニ短調で、旋律を高い音域に移して別の表情にする
・A'' は主題の戻り。伴奏に 9 度の音を足して少しだけ豊かに
・低音は F2 (87Hz) より下を使わず、和音の 3 度は C3 より上に置く (低音を濁らせない)
・旋律と伴奏が半音でぶつからないよう、伴奏の和音から旋律と半音違いの音を抜く (render で検査)
"""

from __future__ import annotations

import numpy as np

from . import dsp
from . import arrange as A
from . import instruments as I

BPM = 64.0
BAR = 4.0

# 和音: 1 小節ずつ。"," で区切ると半小節ずつ
SECTIONS = [
    ("intro", "F Dm7 Bbmaj7 C7sus4,C7"),
    ("A", "F Dm7 Bbmaj7 C7sus4,C7 F/A Bb Gm7 C"),
    ("A2", "F Am7 Dm7 Bbmaj7 Gm7 C7 F F"),
    ("B", "Dm Bb Gm A7 Dm Bb Gm7 C7"),
    ("bridge", "Bbmaj7 Am7 Gm7 C7sus4,C7"),
    ("A3", "F Dm7 Bbmaj7 C7sus4,C7 F/A Bb Gm7,C7 F"),
    ("coda", "Bbmaj7 F/A Gm7 C7 F F"),
]

# 旋律 (音名/拍)。R は休み。前奏は旋律なし
MELODY = {
    "intro": "R/16",
    "A": "A4/1.5 C5/.5 F5/2 | E5/1 D5/1 C5/1.5 A4/.5 | D5/2 C5/1 Bb4/1 | A4/1 G4/1 C5/2 | "
         "A4/1.5 C5/.5 F5/1 G5/1 | A5/2 G5/1 F5/1 | E5/1 F5/1 G5/1 D5/1 | C5/4",
    "A2": "A4/1.5 C5/.5 F5/2 | E5/1.5 G5/.5 E5/2 | F5/1 E5/1 D5/1 C5/1 | D5/3 A4/1 | "
          "Bb4/1 A4/1 G4/1 Bb4/1 | E5/2 D5/1 C5/1 | A4/2 G4/1 F4/1 | F4/3 R/1",
    "B": "D5/1 E5/1 F5/1.5 E5/.5 | D5/2 F5/2 | G5/1.5 F5/.5 E5/1 D5/1 | C#5/2 E5/2 | "
         "D5/1 E5/1 F5/1.5 A5/.5 | Bb5/2 A5/1 G5/1 | F5/1 E5/1 D5/1 F5/1 | E5/2 C5/2",
    "bridge": "R/1 D5/1 C5/1 Bb4/1 | C5/2 A4/2 | Bb4/1.5 A4/.5 G4/2 | F4/2 E4/2",
    "A3": "A4/1.5 C5/.5 F5/1.5 G5/.5 | A5/1 G5/1 F5/1.5 D5/.5 | D5/2 C5/1 Bb4/1 | A4/1 G4/1 C5/2 | "
          "A4/1.5 C5/.5 F5/1 G5/1 | A5/2 Bb5/1 A5/1 | G5/1.5 F5/.5 E5/1 G5/1 | F5/4",
    "coda": "D5/2 C5/2 | C5/2 A4/2 | Bb4/1.5 A4/.5 G4/2 | E4/2 G4/2 | F4/4 | R/4",
}

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_Q = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
      "7sus4": (0, 5, 7, 10),
      # 2026-11-09 追加 (x05r 用)。orig01 の和音には出てこないので、orig01 の音は変わらない
      "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9)}


def note_num(name: str) -> int:
    pc = _PC[name[0]]
    rest = name[1:]
    if rest[:1] in ("#", "b"):
        pc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + pc


def chord(name: str) -> tuple[int, list[int]]:
    """'Bbmaj7' 'F/A' → (低音の pc, 構成音 pc)"""
    bass = None
    if "/" in name:
        name, b = name.split("/")
        bass = _PC[b[0]] + (1 if b[1:2] == "#" else -1 if b[1:2] == "b" else 0)
    root = _PC[name[0]]
    rest = name[1:]
    if rest[:1] in ("#", "b"):
        root += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    pcs = [(root + i) % 12 for i in _Q[rest]]
    return (bass if bass is not None else root) % 12, pcs


def score():
    """→ 旋律 [(開始拍, 長さ, 音, 部分)], 和音 [(開始拍, 長さ, 名前, 部分)], 全拍数"""
    mel, chs, t0 = [], [], 0.0
    for sec, spec in SECTIONS:
        bars = spec.split()
        t = t0
        for b in bars:
            parts = b.split(",")
            for p in parts:
                chs.append((t, BAR / len(parts), p, sec))
                t += BAR / len(parts)
        t = t0
        for tok in MELODY[sec].replace("|", " ").split():
            n, d = tok.split("/")
            d = float(d)
            if n != "R":
                mel.append((t, d, note_num(n), sec))
            t += d
        assert abs(t - (t0 + BAR * len(bars))) < 1e-6, (sec, t - t0, BAR * len(bars))
        t0 += BAR * len(bars)
    return mel, chs, t0


def time_map(total_beats: float):
    """拍 → 秒。各 8 小節の区切りの最後の小節を 4% のばし、終わりの 4 小節で少しずつ遅くする"""
    beat = 60.0 / BPM
    phrase_ends = set()
    b0 = 0
    for sec, spec in SECTIONS:
        nb = len(spec.split())
        phrase_ends.add(b0 + nb - 1)
        b0 += nb
    n_bars = int(total_beats / BAR)
    factors = []
    for b in range(n_bars):
        f = 1.04 if b in phrase_ends else 1.0
        if b >= n_bars - 4:
            f *= 1.0 + 0.06 * (b - (n_bars - 5))       # 1.06, 1.12, 1.18, 1.24
        factors.append(f)
    starts = np.concatenate([[0.0], np.cumsum([BAR * beat * f for f in factors])])

    def t(q: float) -> float:
        b = min(int(q // BAR), n_bars - 1)
        return float(starts[b] + (q - b * BAR) * beat * factors[b])
    return t


def accompaniment(chs, mel):
    """伴奏の音 [(開始拍, 長さ (ペダル), 音, 強さ)]"""
    out = []
    mel_at = lambda q: [m for s, d, m, _ in mel if s <= q < s + d]
    for s, d, name, sec in chs:
        bass_pc, pcs = chord(name)
        bass = 41 + (bass_pc - 41) % 12            # F2 (41) 〜 E3
        upper = [p for p in pcs if p != bass_pc] or pcs
        if sec == "A3":
            upper = upper + [(pcs[0] + 2) % 12]     # 9 度を足す
        # 和音の音は C3 (48) より上に、低い順に
        voic = sorted(48 + (p - 48) % 12 for p in upper)
        voic = [v + 12 if v < 53 and (v % 12) in (pcs[1] % 12,) else v for v in voic]
        # 旋律と半音でぶつかる音を抜く (区間内で鳴る旋律の音すべてと比べる)
        mel_pcs = {m % 12 for q in np.arange(s, s + d, 0.5) for m in mel_at(q)}
        voic = [v for v in voic if all((v - mp) % 12 not in (1, 11) for mp in mel_pcs)] or voic[:1]
        vel_b, vel_c = (0.30, 0.22) if sec != "B" else (0.33, 0.25)
        if sec in ("intro", "coda"):
            vel_b, vel_c = 0.27, 0.20
        if sec == "B":
            # B は 4 分音符でゆっくり分散 (A の 8 分音符と違う動きにする)。1 回目は 1・3 拍目の和音だけにしたら、
            # 和音の間で音が減衰して 2 秒ごとの音量が 7.8dB 上下した
            u = [voic[i % len(voic)] for i in range(3)]
            seq = [bass, u[0], u[1], u[2]][: int(d)]
            for i, m in enumerate(seq):
                out.append((s + i, d - i, m, vel_b if i == 0 else vel_c))
            continue
        else:
            # 8 分音符の分散和音: 低音 → 和音の音を上へ → 戻る
            u = [voic[i % len(voic)] for i in range(3)]
            seq = [bass, u[0], u[1], u[2], u[1], u[0], u[1], u[2]][: int(d * 2)]
            for i, m in enumerate(seq):
                out.append((s + i * 0.5, d - i * 0.5, m, vel_b if i == 0 else vel_c * (1.0 - 0.05 * (i % 2))))
    return out


def render(seed: int = 7101, sr: int = dsp.SR):
    """→ (ステレオ float32 のマスター, 情報 dict)"""
    rng = np.random.default_rng(seed)
    mel, chs, total = score()
    acc = accompaniment(chs, mel)
    tm = time_map(total)
    end_s = tm(total) + 2.5
    n = int(end_s * sr)
    buf = np.zeros((n, 2), dtype=np.float32)
    bank = I.SampleBank(seed=seed, n_variants=3)

    def put(q, dur_q, m, vel, gain, pan, legato):
        t = tm(q) + float(rng.normal(0, 0.005))
        x = bank.note("soft_piano", int(m), float(np.clip(vel + rng.normal(0, 0.015), 0.15, 0.7)))
        hold = int((tm(q + dur_q) - tm(q) + legato) * sr)
        if hold < len(x):
            nr = min(int(0.35 * sr), len(x) - hold)
            x = x[:hold + nr].copy()
            x[hold:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 2
        A.add_panned(buf, x, int(t * sr), gain, pan)

    for s, d, m, sec in mel:
        vel = {"A": 0.40, "A2": 0.39, "B": 0.44, "bridge": 0.36, "A3": 0.43, "coda": 0.36}[sec]
        # フレーズの頂点 (高い音) を少し強く、低い音を少し弱く
        vel += 0.03 * np.clip((m - 72) / 7, -1, 1)
        put(s, d, m, vel, 0.42, 0.08, 0.12)
    for s, d, m, vel in acc:
        put(s, d, m, vel, 0.34, -0.12 if m < 55 else -0.02, 0.05)

    ir = dsp.make_reverb_ir(2.4, rt60=2.0, damp=0.55, predelay=0.02, width=0.6, seed=seed)
    wet = dsp.reverb(buf, ir, mix=0.22, tail=True)[:n]
    x = dsp.shelf(wet, 3000.0, 2.0, kind="high")
    x = dsp.lowpass(x, 12000.0, order=2)
    x = dsp.highpass(x, 40.0, order=2)
    # 最後の小節 (伴奏だけ) の響きを残し、最後の 2.5 秒で消す
    nf = int(2.5 * sr)
    x[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None] ** 2
    x, info = dsp.normalize_lufs(x, target=-14.0, ceiling_db=-1.0)
    info.update(mel=mel, chords=chs, acc=acc, total_beats=total,
                section_times=[(sec, round(tm(s), 2)) for s, _, _, sec in
                               [c for i, c in enumerate(chs) if i == 0 or chs[i - 1][3] != c[3]]],
                end_s=end_s)
    return x, info


def write_midi(path, info) -> None:
    """作曲データを MIDI にする (♩=64 の一定テンポ。演奏の揺らぎは入れない)"""
    import mido
    mf = mido.MidiFile(ticks_per_beat=480)
    for name, notes in (("melody", [(s, d, m, 0.42) for s, d, m, _ in info["mel"]]),
                        ("accompaniment", info["acc"])):
        tr = mido.MidiTrack()
        mf.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
        if name == "melody":
            tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
            tr.append(mido.MetaMessage("key_signature", key="F", time=0))
            tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
        ev = []
        for s, d, m, v in notes:
            ev.append((int(round(s * 480)), 1, int(m), int(v * 127 / 0.7)))
            ev.append((int(round((s + d) * 480)), 0, int(m), 0))
        ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for t, on, m, v in ev:
            tr.append(mido.Message("note_on" if on else "note_off", note=m, velocity=v, time=t - last))
            last = t
    mf.save(str(path))
