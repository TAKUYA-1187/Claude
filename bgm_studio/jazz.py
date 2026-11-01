"""
サックスのジャズ・バラード (録音のアルトサックス・ピアノ・コントラバス + ブラシ)。

なぜ (2026-11-01): 最近 6 か月の再生数上位 30 本に「夜のジャズ / サックスのラウンジ」が
複数あった。旋律は著作権の切れた古い歌 (Mutopia の PD 楽譜と、子守唄で使った手書きの旋律)。
ジャズの和音 (maj7・m7・7) は、楽譜の和声を読み取ってから付け直す。

1 曲の形: 前奏 (ピアノとベースで曲の最後の 4 区間) → サックスの旋律 → ピアノの旋律 →
サックスの旋律 → 最後の和音をのばして終わり。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from . import dsp
from . import arrange as A
from . import instruments as I
from .arrange import Clock
from .classical import bowed_note

DATA = Path(__file__).resolve().parent.parent / "data" / "jazz"
SAMPLES = Path(__file__).resolve().parent.parent / "samples"

# file: Mutopia の MIDI / mel: 旋律のトラック / bpm: 4 分音符の速さ / tonic: 主音 (0=C) と短調か
SONGS = {
    "home_sweet_home": dict(file="homeshome.mid", mel=1, bpm=66, tonic=(5, False),
                            title="Home, Sweet Home (H. R. Bishop, 1823)"),
    "last_rose": dict(file="03-TheLastRoseOfSummer.mid", mel=1, bpm=78, tonic=(5, False),
                      title="The Last Rose of Summer (Irish air)"),
    "blue_bells": dict(file="02-BlueBells.mid", mel=1, bpm=70, tonic=(3, False),
                       title="The Blue Bells of Scotland (Scottish air)"),
    # リュート譜は主和音に長三度 (ピカルディ終止) を使うが、ジャズでは短調の色を残したいので Am に
    "greensleeves": dict(file="Greensleaves.mid", mel=1, bpm=90, tonic=(9, True), fix={9: "min"},
                         title="Greensleeves (English air)"),
    "slumber": dict(file="slumber.mid", mel=1, bpm=84, tonic=(3, False),
                    title="Slumber, My Darling (S. C. Foster, 1862)"),
    # 子守唄の動画で使った手書きの旋律と和音 (nursery.py)
    "amazing_grace": dict(nursery="n14_amazing_grace_lullaby", bpm=76, tonic=(0, False),
                          title="Amazing Grace (traditional)"),
    "all_through_the_night": dict(nursery="n15_all_through_the_night", bpm=68, tonic=(0, False),
                                  title="All Through the Night (Welsh air)"),
}

QUAL = {"maj": (0, 4, 7), "min": (0, 3, 7), "dom": (0, 4, 7, 10), "dim": (0, 3, 6)}


# ── 楽譜を読む ─────────────────────────────────────────────────
def score(path: Path):
    """MIDI → ([(track, 開始, 終わり, 音)] 4 分音符単位, 1 小節の 4 分音符数)"""
    import mido
    mf = mido.MidiFile(str(path))
    tpb = mf.ticks_per_beat
    bar_q = 4.0
    notes = []
    for ti, tr in enumerate(mf.tracks):
        t = 0
        on: dict[int, int] = {}
        for msg in tr:
            t += msg.time
            if msg.type == "time_signature":
                bar_q = msg.numerator * 4.0 / msg.denominator
            elif msg.type == "note_on" and msg.velocity > 0:
                on[msg.note] = t
            elif msg.type in ("note_off", "note_on") and msg.note in on:
                s = on.pop(msg.note)
                if t > s:
                    notes.append((ti, s / tpb, t / tpb, msg.note))
    return sorted(notes, key=lambda r: r[1]), bar_q


def skyline(notes, track: int) -> list[tuple[float, float, int]]:
    """旋律のトラックから、同時に鳴る音の一番上をとる (合唱譜は 1 段に 2 声入っている)"""
    by_on: dict[float, list] = {}
    for ti, s, e, m in notes:
        if ti == track:
            by_on.setdefault(round(s, 4), []).append((e, m))
    ons = sorted(by_on)
    out = []
    for i, s in enumerate(ons):
        e, m = max(by_on[s], key=lambda r: r[1])
        if i + 1 < len(ons):
            e = min(e, ons[i + 1])
        out.append((s, e, m))
    return out


def downbeat_phase(notes, bar_q: float) -> float:
    """弱起の長さ。小節の頭に来る音の長さの合計が最大になる位置を、8 分音符きざみで探す"""
    best, arg = -1.0, 0.0
    for k in range(int(bar_q * 2)):
        ph = k * 0.5
        sc = sum(e - s for _, s, e, _ in notes if abs(((s - ph) / bar_q) - round((s - ph) / bar_q)) < 1e-3)
        if sc > best + 1e-6:
            best, arg = sc, ph
    return arg


def recognize_chords(notes, bar_q: float, phase: float, end: float) -> list[tuple[float, float, int, str]]:
    """
    区間 (4/4 は半小節、それ以外は 1 小節) ごとに、鳴っている音の長さを pc ごとに足し、
    いちばん合う和音 (根音, 種類) を選ぶ。区間の頭の最低音が根音なら加点
    """
    seg = bar_q / 2 if bar_q == 4.0 else bar_q
    starts = []
    t = phase - seg * np.ceil(phase / seg - 1e-9)
    while t < end - 1e-6:
        starts.append(t)
        t += seg
    out = []
    for s0 in starts:
        s1 = s0 + seg
        w = np.zeros(12)
        low = None
        for _, s, e, m in notes:
            ov = min(e, s1) - max(s, max(s0, 0.0))
            if ov > 1e-6:
                w[m % 12] += ov
                if s <= max(s0, 0.0) + 0.26 and (low is None or m < low):
                    low = m
        if w.sum() == 0:
            out.append((max(s0, 0.0), s1 - max(s0, 0.0), out[-1][2] if out else 0, out[-1][3] if out else "maj"))
            continue
        best, arg = -1e9, (0, "maj")
        for r in range(12):
            for q, iv in QUAL.items():
                pcs = {(r + i) % 12 for i in iv}
                sc = sum(w[p] for p in pcs) - 0.7 * sum(w[p] for p in range(12) if p not in pcs)
                if low is not None and low % 12 == r:
                    sc += 0.6 * w.sum() / 3
                sc -= {"maj": 0.0, "min": 0.05, "dom": 0.25, "dim": 0.4}[q] * w.sum()
                if sc > best:
                    best, arg = sc, (r, q)
        out.append((max(s0, 0.0), s1 - max(s0, 0.0), arg[0], arg[1]))
    # 同じ和音が続く区間はまとめる
    merged = []
    for c in out:
        if merged and merged[-1][2:] == c[2:]:
            s, d, r, q = merged[-1]
            merged[-1] = (s, d + c[1], r, q)
        else:
            merged.append(c)
    return merged


def jazzify(root: int, qual: str, tonic: int, minor: bool) -> tuple[int, tuple[int, ...]]:
    """三和音 → ジャズの 4 和音 (根音を除いた上の音の度数)。V は属七に、I・IV は maj7 など"""
    deg = (root - tonic) % 12
    if qual == "dim":
        return root, (3, 6, 9)
    if qual == "dom" or (qual == "maj" and deg == 7):
        return root, (4, 10, 14)                 # 3・7・9
    if qual == "min":
        return root, (3, 10, 14) if deg != (0 if minor else 99) else (3, 9, 14)   # m7(9) / 主和音は m6
    if minor and deg in (3, 8):
        return root, (4, 11, 14)                 # 短調の III・VI は maj7(9)
    return root, (4, 11, 14) if deg in (0, 5) else (4, 9, 14)   # maj7(9) / それ以外は 6(9)


def voicing(root: int, upper: tuple[int, ...], prev: list[int] | None) -> list[int]:
    """根音を抜いた 3 音を、52〜67 (E3〜G4) で前の和音に一番近い並べ方にする"""
    pcs = [(root + i) % 12 for i in upper]
    cands = []
    for base in range(48, 68):
        if base % 12 not in pcs:
            continue
        v = [base]
        for p in pcs:
            if p == base % 12:
                continue
            n = v[-1] + ((p - v[-1]) % 12 or 12)
            v.append(n)
        v = sorted(v)
        for lo in range(len(pcs)):
            vv = sorted(v[lo:] + [x + 12 for x in v[:lo]])
            if 52 <= vv[0] and vv[-1] <= 69:
                cands.append(vv)
    if not cands:
        return sorted(52 + (p - 52) % 12 for p in pcs)
    if prev is None:
        return min(cands, key=lambda v: abs(np.mean(v) - 60))
    return min(cands, key=lambda v: sum(abs(a - b) for a, b in zip(v, prev)))


# ── 1 曲分の素材 ─────────────────────────────────────────────
def song_material(key: str):
    """→ (旋律 [(開始, 終わり, 音)], 和音 [(開始, 長さ, 根音, 上の度数)], 1 小節, 終わり)"""
    so = SONGS[key]
    tonic, minor = so["tonic"]
    if "nursery" in so:
        from .nursery import NURSERY as NS, parse_tune, chords_from_spec, _chord_def
        ns = NS[so["nursery"]]
        bar_q = float(ns["bar"])
        mel, t = [], 0.0
        for m, d in parse_tune(ns["tune"]):
            if m is not None:
                mel.append((t, t + d, m))
            t += d
        end = t
        chords = []
        for s, d, name in chords_from_spec(ns["chords"], int(bar_q)):
            r, pcs = _chord_def(name)
            q = "dom" if name.endswith("7") else "min" if (pcs[1] - r) % 12 == 3 else "maj"
            chords.append((s, d, r, q))
        # 弱起: 旋律の最初の休符の分だけ和音を後ろへずらさない (nursery の和音は小節頭から)
    else:
        notes, bar_q = score(DATA / so["file"])
        mel = skyline(notes, so["mel"])
        end = max(e for _, _, e, _ in notes)
        phase = downbeat_phase(notes, bar_q)
        chords = recognize_chords(notes, bar_q, phase, end)
    fix = so.get("fix", {})
    jc = [(s, d) + jazzify(r, fix.get(r, q), tonic, minor) for s, d, r, q in chords]
    return mel, jc, bar_q, end


def sax_shift(mel) -> int:
    """アルトサックスのおいしい音域 (中央が F4〜A4) に旋律を移す半音数"""
    ms = [m for _, _, m in mel]
    med = float(np.median(ms))
    best = min(range(-24, 25), key=lambda k: (abs(med + k - 67) + 10 * max(0, max(ms) + k - 79)
                                              + 10 * max(0, 54 - (min(ms) + k))))
    return best


# ── 演奏 ───────────────────────────────────────────────────
def render_song(key: str, seed: int, sr: int = dsp.SR) -> np.ndarray:
    rng = np.random.default_rng(seed)
    so = SONGS[key]
    mel, chords, bar_q, end = song_material(key)
    beat = 60.0 / so["bpm"]
    k = sax_shift(mel)
    # 和音も同じだけ移す (根音の高さは pc だけ使う)
    chords = [(s, d, (r + k) % 12, up) for s, d, r, up in chords]
    mel = [(s, e, m + k) for s, e, m in mel]
    swing = bar_q in (2.0, 4.0)
    bank = I.SampleBank(seed=seed, n_variants=3)

    def q2s(q: float, swung: bool = True) -> float:
        if swung and swing:
            frac = q - np.floor(q)
            if abs(frac - 0.5) < 1e-3:
                q += 0.08                       # 裏の 8 分を少し遅らせる (軽いスウィング)
        return q * beat

    intro_chords = chords[-4:] if len(chords) >= 4 else chords
    intro_len = sum(d for _, d, _, _ in intro_chords)
    intro_len = float(np.ceil(intro_len / bar_q) * bar_q)
    form = [("intro", None), ("sax", 0), ("piano", 0), ("sax", 1)]
    total_q = intro_len + 3 * end + 2 * bar_q
    n = int((total_q * beat + 6.0) * sr)
    sax = np.zeros((n, 2), dtype=np.float32)
    pno = np.zeros((n, 2), dtype=np.float32)
    bass = np.zeros((n, 2), dtype=np.float32)
    drm = np.zeros((n, 2), dtype=np.float32)

    def comp(off: float, chs, last: bool = False):
        prev = None
        for i, (s, d, r, up) in enumerate(chs):
            v = voicing(r, up, prev)
            prev = v
            # ピアノ: 区間の頭 (と長い区間は 2 拍目の裏) に軽く
            hits = [0.0] if d < 2.0 else [0.0, 1.5] if bar_q != 3.0 else [0.0, 2.0]
            final = last and i == len(chs) - 1
            if final:
                hits = [0.0]
            for h in hits:
                if h >= d:
                    continue
                t = (off + s + h) * beat + rng.normal(0, 0.006)
                hold = (d - h if final else min(d - h, 2.0)) * beat + 0.3
                for j, m in enumerate(v):
                    x = bank.note("soft_piano", int(m), float(rng.uniform(0.30, 0.38)))
                    hn = int(hold * sr)
                    if hn < len(x):
                        nr = min(int(0.4 * sr), len(x) - hn)
                        x = x[:hn + nr].copy()
                        x[hn:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 2
                    A.add_panned(pno, x, int((t + 0.012 * j) * sr), 0.30, -0.15)
            # ベース: 区間の頭に根音。長い区間は 3 拍目 (3 拍子は 2 拍目なし) に 5 度か根音
            root_m = 36 + (r - 36) % 12
            if root_m > 43:
                root_m -= 12
            bhits = [(0.0, root_m)]
            if d >= 4.0 or (d >= 2.0 and bar_q == 4.0 and d > 2.0):
                bhits.append((2.0, root_m + 7 if rng.random() < 0.6 else root_m))
            elif bar_q == 3.0 and d >= 3.0:
                bhits.append((2.0, root_m + 7 if rng.random() < 0.5 else root_m + 12))
            if final:
                bhits = [(0.0, root_m)]
            for h, m in bhits:
                if h >= d:
                    continue
                t = (off + s + h) * beat
                x = _bass_note(m, float(rng.uniform(0.75, 0.9)), (d - h if final else min(d - h, 2.0)) * beat, sr)
                A.add_panned(bass, x, int(t * sr), 1.0, 0.05)

    def brushes(off: float, length_q: float):
        q = 0.0
        while q < length_q - 1e-6:
            pos_in_bar = q % bar_q
            t = (off + q) * beat
            if bar_q == 3.0:
                acc = pos_in_bar != 0.0
            else:
                acc = int(pos_in_bar) % 2 == 1
            x = bank.hit("brush", length=beat * 0.9, swell=True)
            A.add_panned(drm, x, int(t * sr), 0.55 if acc else 0.35, 0.25)
            q += 1.0

    def play_melody(off: float, inst: str, last: bool):
        for i, (s, e, m) in enumerate(mel):
            t = q2s(off + s) + 0.025 + rng.normal(0, 0.008)       # わずかに後ろ (レイドバック)
            d = (e - s) * beat
            if last and i == len(mel) - 1:
                d += 2 * bar_q * beat * 0.8
            if inst == "sax":
                vel = float(np.clip(rng.normal(0.40, 0.03), 0.30, 0.50))
                x = bowed_note("altosax", int(m), max(d * 0.95, 0.15), vel, sr)
                A.add_panned(sax, x, int(t * sr), 1.0, 0.08)
            else:
                x = bank.note("soft_piano", int(m + 12 if m < 60 else m), float(rng.uniform(0.42, 0.50)))
                A.add_panned(pno, x, int(t * sr), 0.42, 0.10)

    off = 0.0
    comp(off, [(s - intro_chords[0][0], d, r, up) for s, d, r, up in intro_chords])
    brushes(off, intro_len)
    off += intro_len
    for name, rep in form[1:]:
        last = name == "sax" and rep == 1
        play_melody(off, name, last)
        s_, d_, r_, up_ = chords[-1]
        comp(off, chords[:-1] + [(s_, d_ + 2 * bar_q, r_, up_)] if last else chords, last=last)
        brushes(off, end + (2 * bar_q if last else 0))
        off += end
    # 最後の和音は 2 小節のばしてあるので、そこから 1 秒で切って 1.5 秒で消す
    # (1 回目は +3 秒・2 秒で消していて、曲間が 4.5 秒の無音になった)
    end_s = (off + 2 * bar_q) * beat + 1.0
    m = int(end_s * sr)
    # 楽器の音量比 (RMS): サックス基準で ピアノ -4dB、ベース -7dB、ブラシ -20dB
    def rms(x):
        return float(np.sqrt(np.mean(x[:m].astype(np.float64) ** 2))) + 1e-9
    drm[:] = dsp.lowpass(drm, 5500.0, order=2)
    ref = rms(sax)
    out = sax[:m].copy()
    for part, db in ((pno, MIX["piano"]), (bass, MIX["bass"]), (drm, MIX["brush"])):
        out += part[:m] * np.float32(ref / rms(part) * 10 ** (db / 20))
    nf = int(1.5 * sr)
    out[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None] ** 2
    return out


# サックスに対する各楽器の音量 (RMS, dB)
# ブラシは 1 回目 -20dB で 4k・8kHz を一番大きくしていた (8k が基準帯の -24dB)。下げて高域も丸める
MIX = {"piano": -4.0, "bass": -7.0, "brush": -27.0}
_BASS: dict[int, np.ndarray] = {}


def _bass_note(midi: int, vel: float, dur: float, sr: int) -> np.ndarray:
    """コントラバスのピチカート (録音)。音の長さで切って、0.15 秒で消す"""
    from fractions import Fraction
    from scipy import signal as sg
    if not _BASS:
        d = SAMPLES / "bass_pizz_clean"
        _BASS.update({int(p.stem[1:]): np.load(p).astype(np.float32) for p in d.glob("m*.npy")})
    keys = np.array(sorted(_BASS))
    base = int(keys[np.argmin(np.abs(keys - midi))])
    x = _BASS[base]
    r = 2.0 ** ((midi - base) / 12.0)
    if abs(r - 1.0) > 1e-4:
        fr = Fraction(1.0 / r).limit_denominator(2000)
        x = sg.resample_poly(x, fr.numerator, fr.denominator).astype(np.float32)
    nn = min(len(x), int((dur + 0.15) * sr))
    x = x[:nn].copy()
    nr = min(int(0.15 * sr), nn // 3)
    x[-nr:] *= np.linspace(1, 0, nr, dtype=np.float32)
    return x * np.float32(vel)


SETS = {
    "j01_jazz_sax_ballads": ["home_sweet_home", "amazing_grace", "last_rose", "blue_bells",
                             "all_through_the_night", "greensleeves", "slumber"],
}


def build_jazz(spec, seconds: float):
    from . import tracks as TR
    order = SETS[spec.slug]
    sr = dsp.SR
    parts = [render_song(k, seed=spec.seed + i, sr=sr) for i, k in enumerate(order)]
    content = sum(len(x) for x in parts)
    n = int(round(seconds * sr))
    gap = (n - content) // len(parts)
    if gap < int(0.5 * sr):
        raise ValueError(f"{spec.slug}: ループ長 {seconds}s が短すぎます (曲だけで {content / sr:.0f}s)")
    buf = np.zeros((n + int(8 * sr), 2), dtype=np.float32)
    pos = 0
    starts = []
    for x in parts:
        starts.append(pos / sr)
        buf[pos:pos + len(x)] += x
        pos += len(x) + gap
    clock = Clock(total_seconds=seconds, bars=max(int(seconds / 4), 4), beats_per_bar=4)
    ir = dsp.make_reverb_ir(2.6, rt60=1.9, damp=0.55, predelay=0.02, width=0.6, seed=spec.seed)

    def master(x):
        x = dsp.shelf(x, 3000.0, 1.0, kind="high")
        x = dsp.lowpass(x, 11000.0, order=2)
        return dsp.highpass(x, 38.0, order=2)

    out, info = TR._finish(buf, clock, spec, ir, 0.24, [], master)
    info["piece_starts"] = [round(s, 1) for s in starts]
    return out, info


def set_seconds(slug: str, seed: int, gap: float = 0.5) -> float:
    total = sum(len(render_song(k, seed=seed + i)) / dsp.SR + gap for i, k in enumerate(SETS[slug]))
    return float(int(np.ceil(total)))
