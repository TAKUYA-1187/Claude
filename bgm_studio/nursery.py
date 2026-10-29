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

    # ── 海外で定番の子守唄・愛唱歌 (2026-10-29 追加) ─────────────────────
    # 記憶で書かず、パブリックドメインの楽譜を ABC 記譜で確認してから C に移した。
    #   Brahms / Rock-a-bye / All Through the Night: "The Everyday Song Book" (1927)
    #     (abcnotation.com 経由 trillian.mit.edu の John Chambers による入力)
    #   Amazing Grace: "New Britain" (1831) (colinhume.com の ABC)
    # 弱起 (アウフタクト) の曲は、頭に休符を足して小節線をそろえる (伴奏の和声がずれないように)
    "n12_brahms_lullaby": dict(
        # 原調 E♭ → C。弱起 1 拍
        title="Brahms' Lullaby", bar=3, bpm=66, visual="starry_night",
        # 3 拍子のゆっくりした伴奏は音が少なく、オルゴール版は旋律が前に出すぎた (500Hz +16)
        mb_lg=0.75,
        chords="C C C G7 G7 G7 G7 G7 C F C Dm C F C G7 C",
        tune="R/2 E/.5 E/.5 G/1.5 E/.5 E/1 G/1 R/1 E/.5 G/.5 "
             "C5/1 B/1.5 A/.5 A/1 G/1 D/.5 E/.5 F/1 D/1 D/.5 E/.5 F/1 R/1 D/.5 F/.5 "
             "B/.5 A/.5 G/1 B/1 C5/1 R/1 C/.5 C/.5 C5/2 A/.5 F/.5 G/2 E/.5 C/.5 "
             "F/1 G/1 A/1 G/2 C/.5 C/.5 C5/2 A/.5 F/.5 G/2 E/.5 C/.5 F/1 E/1 D/1 C/2 R/1"),
    "n13_rockabye_baby": dict(
        # 原調 B♭ → C。6/8 (付点 4 分 = 1.5 拍で数え、1 小節 = 3 拍)
        title="Rock-a-bye Baby", bar=3, bpm=84, visual="starry_night",
        # 旋律が F5 まで上がるので、オルゴール版は G 長調に下げる (最高音 F6 → C6)
        mb_trans=-5,
        # 8 分音符が多く旋律の音数が多いので、オルゴール版は旋律を控えめにし、
        # 伴奏のピアノを少し厚くする (2kHz -5 → -8, 500Hz +18 → 基準内)
        mb_lg=0.6, mb_ag=1.3,
        chords="C G G7 C C G F G7,C",
        tune="E/.75 G/.25 E5/.5 D5/1 C5/.5 E/.75 G/.25 C5/.5 B/1.5 "
             "F/.75 G/.25 F5/.5 E5/1 D5/.5 D5/.5 C5/.5 A/.5 G/1.5 "
             "E/.75 G/.25 E5/.5 D5/1 C5/.5 E/.75 G/.25 C5/.5 B/1 A/.5 "
             "G/.5 C5/.5 F5/.5 E5/.5 C5/1 D5/.5 A/.5 B/.5 C5/1 R/.5"),
    "n14_amazing_grace_lullaby": dict(
        # 原調 G → C (4 度上)。弱起 1 拍
        title="Amazing Grace", bar=3, bpm=72, visual="starry_night",
        chords="C C C7 F C C Am G G C C7 F C Am G7 C C",
        tune="R/2 G/1 C5/2 E5/.5 C5/.5 E5/2 D5/1 C5/2 A/1 G/2 G/1 "
             "C5/2 E5/.5 C5/.5 E5/2 D5/1 G5/5 E5/1 "
             "G5/2 E5/.5 C5/.5 E5/2 D5/1 C5/2 A/1 G/2 G/1 "
             "C5/2 E5/.5 C5/.5 E5/2 D5/1 C5/5 R/1"),
    "n15_all_through_the_night": dict(
        # 原調 G → C (4 度上)。7 小節目の "E3 F> F" は小節が 5 拍になる入力の誤りと
        # 判断し、3 小節目と同じ "E2 F> F" にそろえた
        title="All Through the Night", bar=4, bpm=66, visual="starry_night",
        chords="C G F,G C C G F,G C F F,C F,G C,G C G F,G C",
        tune="C5/1.5 B/.5 A/1 C5/1 D5/1.5 C5/.5 B/1 G/1 A/2 B/1.5 B/.5 C5/3 R/1 "
             "C5/1.5 B/.5 A/1 C5/1 D5/1.5 C5/.5 B/1 G/1 A/2 B/1.5 B/.5 C5/3 R/1 "
             "F5/1 E5/1 F5/1 G5/1 A5/1 G5/1 F5/1 E5/1 F5/1 E5/1 D5/1 C5/1 E5/1.5 D5/.5 C5/1 B/1 "
             "C5/1.5 B/.5 A/1 C5/1 D5/1.5 C5/.5 B/1 G/1 A/2 B/1.5 B/.5 C5/3 R/1"),
}

# 使う和音 (ルート pc, 構成音 pc)。ハ長調の主要三和音 + 副三和音
_CHORDS = {
    "C": (0, (0, 4, 7)), "Dm": (2, (2, 5, 9)), "Em": (4, (4, 7, 11)),
    "F": (5, (5, 9, 0)), "G": (7, (7, 11, 2)), "Am": (9, (9, 0, 4)),
    # 手書きの和声 (song["chords"]) で使う属七。5 度を省いて根音・3 度・7 度にする
    "G7": (7, (7, 11, 5)), "C7": (0, (0, 4, 10)),
}


def chords_from_spec(spec: str, bar_beats: int) -> list[tuple[float, float, str]]:
    """
    "C C G7,C ..." (1 小節 1 語。"," で区切るとその小節を等分) を和声区間の列にする。
    有名な曲は和音の流れまで耳に残っているので、自動の和声付けより標準の和声を優先する
    """
    out, t = [], 0.0
    for tok in spec.split():
        parts = tok.split(",")
        seg = bar_beats / len(parts)
        for name in parts:
            assert name in _CHORDS, name
            out.append((t, seg, name))
            t += seg
    return out


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
# アレンジ (やさしい 4 通りを、2 コーラスずつ順に回す)
# ──────────────────────────────────────────────────────────────
#
# 以前は 13 通りを 1 コーラスごとに切り替え、転調 (±2) やテンポ変更 (0.84〜1.02)、
# ハープ・アルベルティ・低音 C2 のブロック和音まで入れていた。視聴者から
# 「途中からメロディが変わる」「雑音っぽくなる」と指摘された。子守唄で
# 求められているのは変化ではなく安心感なので、次の方針に改めた。
#   - 調とテンポは変えない (全編 C・同じ速さ)
#   - 楽器はやわらかいピアノとオルゴールだけ (硬いハープ・celesta をやめる)
#   - 伴奏は中音域のパッドか、ゆっくりした分散和音だけ (C2 の低音を鳴らさない)
#   - 切り替えは 2 コーラスごと (約 1 分半) に減らす

#
# 2026-10-28 追記: オーナーの評価「メロディーが機械音で聞きにくい」。ピアノを録音に
# 置き換えたうえで、電子的に聞こえる合成パッドの伴奏とオルゴールの主旋律をやめ、
# ピアノだけの演奏にした (オルゴールは 1 オクターブ上でごく小さく重ねるときだけ)。

ARRANGEMENTS = [
    dict(lead="soft_piano", acc="broken", lg=0.44, ag=0.11),
    dict(lead="soft_piano", acc="block", lg=0.44, ag=0.10),
    # ピアノの 1 オクターブ上でオルゴールがそっと重なる
    dict(lead="soft_piano", acc="broken", lg=0.42, ag=0.11,
         double=12, double_inst="music_box"),
    dict(lead="soft_piano", acc="block", lg=0.42, ag=0.10),
]
# オルゴール版 (2026-10-28 追加。オーナーの依頼「ピアノ版とオルゴール版の 2 パターン」)。
# 旋律はオルゴール (鉄琴の録音) で 1 オクターブ上の、オルゴールらしい高い音域に置き、
# 伴奏はやわらかいピアノでごく小さく支える。調・テンポはピアノ版と同じ
MUSIC_BOX_ARRANGEMENTS = [
    dict(lead="music_box", octave=12, acc="broken", lg=0.34, ag=0.12),
    dict(lead="music_box", octave=12, acc="block", lg=0.34, ag=0.11),
]
MUSIC_BOX_SUFFIX = "_musicbox"

CHORUSES_PER_ARRANGEMENT = 2
BREATH_S = 2.4                           # コーラス間の息継ぎ


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

    is_mb = spec.slug.endswith(MUSIC_BOX_SUFFIX)
    song = NURSERY[spec.slug.removesuffix(MUSIC_BOX_SUFFIX)]
    arrangements = MUSIC_BOX_ARRANGEMENTS if is_mb else ARRANGEMENTS
    tune = parse_tune(song["tune"])
    bar_beats = song["bar"]
    chords = (chords_from_spec(song["chords"], bar_beats) if song.get("chords")
              else harmonize(tune, bar_beats))
    total_beats = sum(d for _, d in tune)
    # オルゴール版だけの曲ごとの調整。旋律を 1 オクターブ上げると、元の旋律が高い曲
    # (Rock-a-bye Baby は F5 まで) は F6 に届いて耳に刺さる。そういう曲は曲全体を
    # 移調して音域を下げる (mb_trans)。旋律と伴奏の音量も曲ごとに変えられる (mb_lg, mb_ag)
    mb_trans = int(song.get("mb_trans", 0)) if is_mb else 0
    lg_scale = float(song.get("mb_lg", 1.0)) if is_mb else 1.0
    ag_scale = float(song.get("mb_ag", 1.0)) if is_mb else 1.0
    rng = np.random.default_rng(spec.seed)
    sr = dsp.SR

    bars = max(int(seconds / (4 * 60.0 / song["bpm"])), 4)
    clock = Clock(total_seconds=seconds, bars=bars, beats_per_bar=4)
    n = clock.n_samples
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    buf = np.zeros((n + int(12 * sr), 2), dtype=np.float32)

    # ── コーラス数と速さを、ループ長にぴったり収まるように決める ──
    # 以前は「次のコーラスが入らなければ打ち切り」にしていたため、
    # 11 分ループの末尾に約 28 秒の無音が残り、33 分の動画で 3 回
    # 無音になっていた。コーラス数を決めてから速さを数 % だけ合わせる。
    head, tail = 0.8, 3.0
    avail = seconds - head - tail
    beat0 = 60.0 / song["bpm"]
    pass0 = total_beats * beat0
    n_pass = max(int(round((avail + BREATH_S) / (pass0 + BREATH_S))), 1)
    beat_s = (avail - (n_pass - 1) * BREATH_S) / (n_pass * total_beats)
    pass_s = total_beats * beat_s

    t = head
    for k in range(n_pass):
        arr = arrangements[(k // CHORUSES_PER_ARRANGEMENT) % len(arrangements)]

        # ── 旋律 ───────────────────────────────────────
        b = 0.0
        for midi, d in tune:
            if midi is not None:
                tt = t + b * beat_s + float(rng.normal(0, 0.006))
                vel = float(np.clip(rng.normal(0.50, 0.04), 0.38, 0.62))
                pos = int(round(tt * sr))
                lm = midi + arr.get("octave", 0) + mb_trans
                A.add_panned(buf, bank.note(arr["lead"], lm, vel), pos,
                             arr["lg"] * lg_scale, -0.05)
                if arr.get("double"):
                    A.add_panned(buf, bank.note(arr["double_inst"],
                                                lm + arr["double"], vel * 0.6),
                                 pos, arr["lg"] * 0.40, 0.12)
            b += d

        # ── 伴奏 (和声区間ごと) ───────────────────────────
        for (seg_start, seg_len, cname) in chords:
            seg_t = t + seg_start * beat_s
            bass, mids = _chord_notes(cname, mb_trans % 12)
            ag = arr["ag"] * ag_scale
            p0 = int(round(seg_t * sr))
            if arr["acc"] == "broken":
                # 1 拍に 1 音のゆっくりした分散和音。低音は C3 より下に行かない
                notes = [bass + 12, mids[0], mids[1], mids[2]]
                for si in range(int(seg_len)):
                    A.add_panned(buf, bank.note("soft_piano", notes[si % 4], 0.32),
                                 int(round((seg_t + si * beat_s) * sr)), ag, 0.08)
            elif arr["acc"] == "block":
                # やわらかい和音を区間の頭で 1 回 (長い区間は半分の位置でもう 1 回)。
                # 下から少しずらして弾くと、機械的な「ジャーン」にならない
                hits = [0.0] + ([seg_len / 2] if seg_len >= 4 else [])
                for h in hits:
                    for ci, m in enumerate([bass + 12] + mids):
                        A.add_panned(buf, bank.note("soft_piano", m, 0.30 - 0.02 * ci),
                                     int(round((seg_t + h * beat_s + 0.018 * ci) * sr)),
                                     ag, (-0.15, -0.05, 0.05, 0.15)[ci % 4])
            else:
                dur = seg_len * beat_s * 1.35
                for ci, m in enumerate([bass + 12] + mids[:2]):
                    _pad_note(bank, m, dur, ag, buf, p0, (-0.2, 0.0, 0.2)[ci])
        t += pass_s + BREATH_S
    k = n_pass

    ir = dsp.make_reverb_ir(2.4, rt60=2.2, damp=0.55, predelay=0.02,
                            width=0.55, seed=spec.seed)

    def master(x):
        # 童謡ピアノは暖かく、飽和も入れず素直に。
        # 以前は QA の「こもり」判定に合わせて 900Hz 以上を +3.5dB 持ち上げて
        # いたが、それが硬さ (雑音っぽさ) の一因だった。子守唄は暖かい方が正しい
        # ので持ち上げはやめ、12kHz より上をなだらかに落とす。
        # 曲ごとの補正 (合成ピアノ時代の bright / lowmid_cut / mid_cut)。録音ピアノでは
        # 不要になったので今は使っていないが、将来の曲のために仕組みは残す
        if song.get("bright"):
            x = dsp.shelf(x, 1000.0, float(song["bright"]), kind="high")
        if song.get("lowmid_cut"):
            x = dsp.peak_eq(x, 350.0, -float(song["lowmid_cut"]), q=1.2)
        if song.get("mid_cut"):
            x = dsp.peak_eq(x, 700.0, -float(song["mid_cut"]), q=1.0)
        # 録音ピアノ (2026-10-28〜) は 3kHz より上が少ない。空気感だけ少し足す
        if not is_mb:                     # オルゴール版は元から明るいので足さない
            x = dsp.shelf(x, 3000.0, 4.0, kind="high")
        else:
            # 鉄琴は基音の約 2.8 倍・5.4 倍に強い倍音がある (旋律 C5〜A5 なら 1.5〜4.7kHz)。
            # そこを棚で下げて、耳に刺さらないオルゴールにする
            x = dsp.shelf(x, 2200.0, -5.0, kind="high")
        x = dsp.lowpass(x, 12000.0, order=2)
        return dsp.highpass(x, 50.0, order=2)

    # beds=[]: 環境音ノイズは敷かない。ここがノイズゼロの核心
    out, info = TR._finish(buf, clock, spec, ir, 0.30, [], master)
    info["passes"] = k
    info["arrangements"] = len(arrangements)
    info["chords"] = " ".join(c for _, _, c in chords)
    return out, info
