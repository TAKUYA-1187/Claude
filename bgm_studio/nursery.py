"""
童謡・子守唄シリーズ (Nursery Rhymes & Lullabies)。

ChatGPT 側で進んでいた「童謡を 30 分前後のピアノ動画にして 1 本ずつ公開する」
企画を、このエンジンに取り込んだもの。方針は 3 つ:

  1. ノイズゼロ。環境音のベッドを一切敷かない。
     子供向けの睡眠用途では、微かなヒスでも「ノイズがある」と受け取られる。
     音は楽器と残響だけで作り、床ノイズも入れない。
  2. 実調律 A=432Hz。表記だけでなく実音が 432Hz 基準 (dsp.set_tuning)。
     効能は謳わず、「柔らかく聞こえる調律の選択」としてだけ説明する。
  3. 同じ曲でも 33 分ずっと同じ聞こえ方にしない。
     楽器・オクターブ・伴奏・テンポ・調を 13 通りに変えて巡回させる
     (ChatGPT 側は 3 分ループの繰り返しだった)。

使う旋律は全てパブリックドメインの伝承曲/古典。
他人の録音・編曲は一切使わず、旋律から和声も自動で付ける。

旋律の確実性について:
  自分が音符まで確かめられた曲だけを入れてある。ブラームスの子守歌は
  旋律を裏取りできなかったので入れていない (間違った旋律を出すより外す)。
"""

from __future__ import annotations

import numpy as np

from . import arrange as A
from . import dsp
from . import instruments as I
from .arrange import Clock

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_tune(s: str) -> list[tuple[int | None, float]]:
    """'C/1 G5/.5 R/1' → [(60,1.0),(79,0.5),(None,1.0)]。数字は無ければ4オクターブ"""
    out = []
    for tok in s.replace("|", " ").split():
        name, dur = tok.split("/")
        d = float(dur)
        if name == "R":
            out.append((None, d))
            continue
        pc = _PC[name[0]]
        rest = name[1:]
        if rest.startswith("#"):
            pc += 1
            rest = rest[1:]
        elif rest.startswith("b"):
            pc -= 1
            rest = rest[1:]
        octv = int(rest) if rest else 4
        out.append((12 * (octv + 1) + pc, d))
    return out


# 旋律データ。bar = 1 小節の拍数 (4分音符基準。6/8 は 3)
NURSERY: dict[str, dict] = {
    "n01_twinkle_lullaby": dict(
        title="Twinkle Twinkle Little Star", bar=4, bpm=66, visual="starry_night",
        tune="C/1 C/1 G/1 G/1 A/1 A/1 G/2 F/1 F/1 E/1 E/1 D/1 D/1 C/2 "
             "G/1 G/1 F/1 F/1 E/1 E/1 D/2 G/1 G/1 F/1 F/1 E/1 E/1 D/2 "
             "C/1 C/1 G/1 G/1 A/1 A/1 G/2 F/1 F/1 E/1 E/1 D/1 D/1 C/2"),
    "n02_mary_lamb_lullaby": dict(
        title="Mary Had a Little Lamb", bar=4, bpm=72, visual="morning_meadow",
        tune="E/1 D/1 C/1 D/1 E/1 E/1 E/2 D/1 D/1 D/2 E/1 G/1 G/2 "
             "E/1 D/1 C/1 D/1 E/1 E/1 E/1 E/1 D/1 D/1 E/1 D/1 C/4"),
    "n03_row_your_boat_lullaby": dict(
        title="Row, Row, Row Your Boat", bar=3, bpm=84, visual="zen_water",
        tune="C/1.5 C/1.5 C/1 D/.5 E/1.5 E/1 D/.5 E/1 F/.5 G/3 "
             "C5/.5 C5/.5 C5/.5 G/.5 G/.5 G/.5 E/.5 E/.5 E/.5 C/.5 C/.5 C/.5 "
             "G/1 F/.5 E/1 D/.5 C/3"),
    "n04_frere_jacques_lullaby": dict(
        title="Frère Jacques", bar=4, bpm=76, visual="minimal_gradient",
        tune="C/1 D/1 E/1 C/1 C/1 D/1 E/1 C/1 E/1 F/1 G/2 E/1 F/1 G/2 "
             "G/.5 A/.5 G/.5 F/.5 E/1 C/1 G/.5 A/.5 G/.5 F/.5 E/1 C/1 "
             "C/1 G3/1 C/2 C/1 G3/1 C/2"),
    "n05_london_bridge_lullaby": dict(
        title="London Bridge Is Falling Down", bar=4, bpm=80, visual="night_skyline",
        tune="G/1.5 A/.5 G/1 F/1 E/1 F/1 G/2 D/1 E/1 F/2 E/1 F/1 G/2 "
             "G/1.5 A/.5 G/1 F/1 E/1 F/1 G/2 D/2 G/2 E/2 C/2"),
    "n06_old_macdonald_lullaby": dict(
        title="Old MacDonald Had a Farm", bar=4, bpm=88, visual="seaside_cafe",
        tune="C/1 C/1 C/1 G/1 A/1 A/1 G/2 E/1 E/1 D/1 D/1 C/4 "
             "C/1 C/1 C/1 G/1 A/1 A/1 G/2 E/1 E/1 D/1 D/1 C/4"),
    "n07_au_clair_lullaby": dict(
        title="Au clair de la lune", bar=4, bpm=70, visual="moonlit_ocean",
        tune="C/1 C/1 C/1 D/1 E/2 D/2 C/1 E/1 D/1 D/1 C/4 "
             "D/1 D/1 D/1 D/1 A/2 A/2 D/1 C/1 B3/1 A3/1 G3/4 "
             "C/1 C/1 C/1 D/1 E/2 D/2 C/1 E/1 D/1 D/1 C/4"),
    "n08_silent_night_lullaby": dict(
        title="Silent Night", bar=3, bpm=60, visual="christmas_window",
        tune="G/1.5 A/.5 G/1 E/3 G/1.5 A/.5 G/1 E/3 D5/2 D5/1 B/3 C5/2 C5/1 G/3 "
             "A/2 A/1 C5/1.5 B/.5 A/1 G/1.5 A/.5 G/1 E/3 "
             "A/2 A/1 C5/1.5 B/.5 A/1 G/1.5 A/.5 G/1 E/3 "
             "D5/2 D5/1 F5/1.5 D5/.5 B/1 C5/3 E5/3 C5/1.5 G/.5 E/1 G/1.5 F/.5 D/1 C/3"),
    "n09_ode_to_joy_lullaby": dict(
        title="Ode to Joy", bar=4, bpm=84, visual="golden_light",
        tune="E/1 E/1 F/1 G/1 G/1 F/1 E/1 D/1 C/1 C/1 D/1 E/1 E/1.5 D/.5 D/2 "
             "E/1 E/1 F/1 G/1 G/1 F/1 E/1 D/1 C/1 C/1 D/1 E/1 D/1.5 C/.5 C/2 "
             "D/1 D/1 E/1 C/1 D/1 E/.5 F/.5 E/1 C/1 D/1 E/.5 F/.5 E/1 D/1 C/1 D/1 G3/2 "
             "E/1 E/1 F/1 G/1 G/1 F/1 E/1 D/1 C/1 C/1 D/1 E/1 D/1.5 C/.5 C/2"),
    "n10_jingle_bells_lullaby": dict(
        title="Jingle Bells", bar=4, bpm=92, visual="snow_cabin",
        tune="E/1 E/1 E/2 E/1 E/1 E/2 E/1 G/1 C/1.5 D/.5 E/4 "
             "F/1 F/1 F/1.5 F/.5 F/1 E/1 E/1 E/.5 E/.5 E/1 D/1 D/1 E/1 D/2 G/2 "
             "E/1 E/1 E/2 E/1 E/1 E/2 E/1 G/1 C/1.5 D/.5 E/4 "
             "F/1 F/1 F/1.5 F/.5 F/1 E/1 E/1 E/.5 E/.5 G/1 G/1 F/1 D/1 C/4"),
}

# 使う和音 (ルート pc, 構成音 pc)。ハ長調の主要三和音 + 副三和音
_CHORDS = {
    "C": (0, (0, 4, 7)), "Dm": (2, (2, 5, 9)), "Em": (4, (4, 7, 11)),
    "F": (5, (5, 9, 0)), "G": (7, (7, 11, 2)), "Am": (9, (9, 0, 4)),
}


_CAND = ["C", "F", "G", "Am", "Dm"]
# よく使われる進行は移行コストを小さく (和声の流れが自然になる)
_GOOD = {("C", "F"), ("C", "G"), ("F", "C"), ("G", "C"), ("F", "G"),
         ("Am", "F"), ("Am", "Dm"), ("Dm", "G"), ("C", "Am"), ("G", "Am"),
         ("F", "Dm"), ("Dm", "C"), ("Am", "G"), ("G", "F")}


def harmonize(tune: list, bar_beats: int) -> list[tuple[float, float, str]]:
    """
    旋律から和音を選び、[(開始拍, 長さ拍, 和音名)] を返す。

    4 拍子は半小節 (2 拍) ごと、3 拍子/6-8 は 1 小節ごとに 1 和音。
    区間ごとに「和音構成音に当たる音価の合計」を点にし (強拍は 2.5 倍、
    強拍が非和声音なら減点)、Viterbi 法で全体を通して最良の列を選ぶ。
      - よく使われる進行 (C→F, G→C, Am→F ...) は移行コストを小さく
      - 同じ和音の継続はコスト 0 (忙しく動かさない)
      - 先頭は C、最後は必ず C、最後の手前は G か F で終止形にする
    """
    seg_len = 2.0 if bar_beats == 4 else float(bar_beats)
    total = sum(d for _, d in tune)
    n_seg = int(round(total / seg_len))

    # 区間ごとに (pc, 重なった音価, 区間内の開始位置) を集める
    segs: list[list[tuple[int, float, float]]] = [[] for _ in range(n_seg)]
    t = 0.0
    for midi, d in tune:
        if midi is not None:
            t0, t1 = t, t + d
            for si in range(n_seg):
                s0, s1 = si * seg_len, (si + 1) * seg_len
                ov = min(t1, s1) - max(t0, s0)
                if ov > 1e-6:
                    segs[si].append((midi % 12, ov, max(t0, s0) - s0))
        t += d

    def emit(si: int, name: str) -> float:
        pcs = _CHORDS[name][1]
        sc = 0.0
        for pc, ov, pos in segs[si]:
            strong = pos < 1e-6
            if pc in pcs:
                sc += ov * (2.5 if strong else 1.0)
            elif strong and ov >= 1.0:
                sc -= 2.0
        if si == 0 and name == "C":
            sc += 2.0
        if si == n_seg - 2:
            sc += {"G": 1.2, "F": 0.6}.get(name, 0.0)
        if si == n_seg - 1:
            sc += 100.0 if name == "C" else -100.0
        return sc

    def trans(a: str, b: str) -> float:
        if a == b:
            return 0.0
        return 0.35 if (a, b) in _GOOD else 0.95

    INF = -1e9
    dp = [{c: INF for c in _CAND} for _ in range(n_seg)]
    bp = [{c: None for c in _CAND} for _ in range(n_seg)]
    for c in _CAND:
        dp[0][c] = emit(0, c)
    for si in range(1, n_seg):
        for c in _CAND:
            best, arg = INF, None
            for pc_ in _CAND:
                v = dp[si - 1][pc_] - trans(pc_, c)
                if v > best:
                    best, arg = v, pc_
            dp[si][c] = best + emit(si, c)
            bp[si][c] = arg
    cur = max(_CAND, key=lambda c: dp[n_seg - 1][c])
    names = [cur]
    for si in range(n_seg - 1, 0, -1):
        cur = bp[si][cur]
        names.append(cur)
    names.reverse()
    return [(i * seg_len, seg_len, nm) for i, nm in enumerate(names)]


# ──────────────────────────────────────────────────────────────
# アレンジ (33 分の間に巡回させる 13 通り)
# ──────────────────────────────────────────────────────────────

ARRANGEMENTS = [
    dict(lead="celesta", shift=0, acc="pad", tempo=1.00, trans=0, lg=0.40, ag=0.10),
    dict(lead="piano", shift=0, acc="alberti", tempo=1.00, trans=0, lg=0.40, ag=0.20),
    dict(lead="piano", shift=0, acc="pad", tempo=0.96, trans=0, lg=0.38, ag=0.12, double=12),
    dict(lead="harp", shift=0, acc="block", tempo=1.00, trans=0, lg=0.38, ag=0.18),
    dict(lead="celesta", shift=0, acc="alberti", tempo=0.95, trans=0, lg=0.38, ag=0.22),
    dict(lead="piano", shift=0, acc="harp", tempo=0.88, trans=0, lg=0.40, ag=0.15),
    dict(lead="celesta", shift=0, acc="pad", tempo=1.00, trans=2, lg=0.38, ag=0.10),
    dict(lead="harp", shift=0, acc="pad", tempo=0.94, trans=0, lg=0.40, ag=0.12),
    dict(lead="piano", shift=0, acc="block", tempo=1.00, trans=0, lg=0.40, ag=0.16, echo=12),
    dict(lead="piano", shift=0, acc="alberti", tempo=0.94, trans=-2, lg=0.40, ag=0.20),
    dict(lead="celesta", shift=0, acc="harp", tempo=1.02, trans=0, lg=0.36, ag=0.15),
    # 伴奏なしにすると高音域だけが残り、500Hz 帯が突き出る (QA で実測)。
    # 極薄のパッドを下に敷いて、低〜中域を空にしない
    dict(lead="celesta", shift=0, acc="pad", tempo=0.84, trans=0, lg=0.40, ag=0.09),
    dict(lead="piano", shift=0, acc="pad", tempo=1.00, trans=0, lg=0.40, ag=0.12, echo=-12),
]


def _chord_notes(name: str, trans: int) -> tuple[int, list[int]]:
    """和音の (ベース音 midi, 中音域の構成音 midi 3 つ)"""
    root, pcs = _CHORDS[name]
    bass = 36 + root + trans
    mids = []
    for pc in pcs:
        m = 55 + ((pc + trans - 55) % 12)       # 55..66 に収める
        mids.append(m)
    return bass, sorted(mids)


def _pad_note(bank, midi: int, dur: float, gain: float, buf, pos: int,
              pan: float) -> None:
    """持続音。フェードを自前でかける (pad_voice は包絡を持たない)"""
    v = bank.sustained("pad", int(midi), round(dur, 1), brightness=0.5, n_detune=3)
    n = len(v)
    env = np.ones(n, dtype=np.float32)
    na = min(int(0.9 * dsp.SR), n // 2)
    nr = min(int(1.2 * dsp.SR), n // 2)
    env[:na] = np.linspace(0, 1, na, dtype=np.float32) ** 1.5
    env[-nr:] = np.linspace(1, 0, nr, dtype=np.float32) ** 1.5
    A.add_panned(buf, (v * env).astype(np.float32), pos, gain, pan)


def build_nursery(spec, seconds: float):
    """童謡 1 曲を、アレンジを変えながら `seconds` の間くり返す"""
    from . import tracks as TR

    song = NURSERY[spec.slug]
    tune = parse_tune(song["tune"])
    bar_beats = song["bar"]
    chords = harmonize(tune, bar_beats)
    total_beats = sum(d for _, d in tune)
    rng = np.random.default_rng(spec.seed)
    sr = dsp.SR

    bars = max(int(seconds / (4 * 60.0 / song["bpm"])), 4)
    clock = Clock(total_seconds=seconds, bars=bars, beats_per_bar=4)
    n = clock.n_samples
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    buf = np.zeros((n + int(12 * sr), 2), dtype=np.float32)

    t = 0.8                                  # 最初の音の前に少し間を置く
    k = 0
    limit = seconds - 7.0                    # 最後は残響が自然に尽きる余白
    while True:
        arr = ARRANGEMENTS[k % len(ARRANGEMENTS)]
        beat_s = 60.0 / song["bpm"] / arr["tempo"]
        pass_s = total_beats * beat_s
        if t + pass_s > limit:
            break
        trans = arr["trans"]
        shift = arr["shift"] + trans

        # ── 旋律 ───────────────────────────────────────
        b = 0.0
        for midi, d in tune:
            if midi is not None:
                tt = t + b * beat_s + float(rng.normal(0, 0.006))
                vel = float(np.clip(rng.normal(0.55, 0.05), 0.38, 0.70))
                m = midi + shift
                pos = int(round(tt * sr))
                A.add_panned(buf, bank.note(arr["lead"], m, vel), pos,
                             arr["lg"], -0.05)
                if arr.get("double"):
                    A.add_panned(buf, bank.note(arr["lead"], m + arr["double"],
                                                vel * 0.6),
                                 pos, arr["lg"] * 0.55, 0.10)
                if arr.get("echo"):
                    A.add_panned(buf, bank.note("celesta", m + arr["echo"],
                                                vel * 0.7),
                                 pos + int(0.5 * beat_s * sr), arr["lg"] * 0.45, 0.22)
            b += d

        # ── 伴奏 (和声区間ごと) ───────────────────────────
        for (seg_start, seg_len, cname) in chords:
            seg_t = t + seg_start * beat_s
            bass, mids = _chord_notes(cname, trans)
            acc = arr["acc"]
            ag = arr["ag"]
            if acc == "none":
                continue
            p0 = int(round(seg_t * sr))
            if acc == "alberti":
                seq = [bass, mids[1], mids[2], mids[1]]
                for si in range(int(seg_len * 2)):
                    vel = 0.34 if si % 2 == 0 else 0.26
                    A.add_panned(buf, bank.note("piano", seq[si % 4], vel),
                                 int(round((seg_t + si * 0.5 * beat_s) * sr)),
                                 ag, 0.05)
            elif acc == "block":
                A.add_panned(buf, bank.note("piano", bass, 0.40), p0, ag * 1.1, 0.0)
                for ci, m in enumerate(mids):
                    A.add_panned(buf, bank.note("piano", m, 0.30),
                                 p0 + int((0.012 + 0.014 * ci) * sr), ag * 0.8, 0.05)
            elif acc == "harp":
                notes = [bass + 12, mids[0], mids[1], mids[2], mids[1], mids[0]]
                for si in range(min(int(seg_len * 2), len(notes))):
                    A.add_panned(buf, bank.note("harp", notes[si], 0.34),
                                 int(round((seg_t + si * 0.5 * beat_s) * sr)),
                                 ag, 0.10)
            elif acc == "pad":
                dur = seg_len * beat_s * 1.35
                for ci, m in enumerate([bass + 12] + mids[:2]):
                    _pad_note(bank, m, dur, ag, buf, p0, (-0.2, 0.0, 0.2)[ci])
        t += pass_s + float(rng.uniform(1.8, 3.2))    # フレーズ間の息継ぎ
        k += 1

    ir = dsp.make_reverb_ir(2.4, rt60=2.2, damp=0.55, predelay=0.02,
                            width=0.55, seed=spec.seed)

    def master(x):
        # 童謡ピアノは暖かく、でも籠らせない。飽和も入れず素直に
        x = dsp.tilt_eq(x, pivot=900.0, gain_db=-1.5)
        x = dsp.lowpass(x, 15000.0, order=2)
        return dsp.highpass(x, 40.0, order=2)

    # beds=[]: 環境音ノイズは敷かない。ここがノイズゼロの核心
    out, info = TR._finish(buf, clock, spec, ir, 0.30, [], master)
    info["passes"] = k
    info["arrangements"] = len(ARRANGEMENTS)
    info["chords"] = " ".join(c for _, _, c in chords)
    return out, info
