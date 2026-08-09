"""
音楽理論レイヤ。

BGM が「AI っぽい」「打ち込みっぽい」と言われる最大の原因は
和声がぶつかること・進行が不自然なことなので、ここは手癖ではなく
実際のジャズ/ポップスの定石どおりに組んである。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ── 音名 ────────────────────────────────────────────────────
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NAME_TO_PC = {n: i for i, n in enumerate(NOTE_NAMES)}
NAME_TO_PC.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})


def note(name: str, octave: int = 4) -> int:
    """'Eb', 3 → MIDI 番号"""
    return NAME_TO_PC[name] + (octave + 1) * 12


# ── スケール ────────────────────────────────────────────────
SCALES: dict[str, list[int]] = {
    "major":            [0, 2, 4, 5, 7, 9, 11],
    "minor":            [0, 2, 3, 5, 7, 8, 10],   # natural minor / aeolian
    "harmonic_minor":   [0, 2, 3, 5, 7, 8, 11],
    "dorian":           [0, 2, 3, 5, 7, 9, 10],
    "phrygian":         [0, 1, 3, 5, 7, 8, 10],
    "lydian":           [0, 2, 4, 6, 7, 9, 11],
    "mixolydian":       [0, 2, 4, 5, 7, 9, 10],
    "pent_minor":       [0, 3, 5, 7, 10],
    "pent_major":       [0, 2, 4, 7, 9],
    "kumoi":            [0, 2, 3, 7, 9],          # 和風。ヒーリング系で映える
    "hirajoshi":        [0, 2, 3, 7, 8],
    "in_sen":           [0, 1, 5, 7, 10],
}


# ── コード品質 (ルートからの半音インターバル) ────────────────
CHORDS: dict[str, list[int]] = {
    "maj":     [0, 4, 7],
    "min":     [0, 3, 7],
    "dim":     [0, 3, 6],
    "aug":     [0, 4, 8],
    "sus2":    [0, 2, 7],
    "sus4":    [0, 5, 7],
    "maj7":    [0, 4, 7, 11],
    "min7":    [0, 3, 7, 10],
    "dom7":    [0, 4, 7, 10],
    "m7b5":    [0, 3, 6, 10],
    "dim7":    [0, 3, 6, 9],
    "maj9":    [0, 4, 7, 11, 14],
    "min9":    [0, 3, 7, 10, 14],
    "dom9":    [0, 4, 7, 10, 14],
    "min11":   [0, 3, 7, 10, 14, 17],
    "maj13":   [0, 4, 7, 11, 14, 21],
    "dom13":   [0, 4, 7, 10, 14, 21],
    "min6":    [0, 3, 7, 9],
    "maj6":    [0, 4, 7, 9],
    "add9":    [0, 4, 7, 14],
    "madd9":   [0, 3, 7, 14],
    "dom7b9":  [0, 4, 7, 10, 13],
    "dom7s11": [0, 4, 7, 10, 18],
}


@dataclass
class Chord:
    """1 コード = ルート(MIDI ピッチクラス基準) + 品質 + 小節数"""
    root: int            # MIDI 番号 (オクターブ込み)
    quality: str
    bars: float = 1.0
    bass: int | None = None   # 分数コードのベース音を明示したいとき

    def pitches(self) -> list[int]:
        return [self.root + i for i in CHORDS[self.quality]]

    def bass_note(self) -> int:
        return self.bass if self.bass is not None else self.root

    @property
    def pcs(self) -> set[int]:
        return {p % 12 for p in self.pitches()}


def voice_close(chord: Chord, center: int = 60, n_voices: int = 4) -> list[int]:
    """
    クローズドボイシング。center 付近に音を寄せる。
    毎回同じ転回形にならないよう、center に一番近い転回を選ぶ。
    """
    ps = chord.pitches()[:max(n_voices, 3)]
    # 全部を center 付近のオクターブへ畳み込む
    out = []
    for p in ps:
        while p < center - 6:
            p += 12
        while p > center + 18:
            p -= 12
        out.append(p)
    return sorted(set(out))


def voice_jazz_rootless(chord: Chord, center: int = 62) -> list[int]:
    """
    ルートレス・ボイシング (3-7-9-5 系)。
    ベースがルートを弾く前提で、鍵盤は 3rd/7th を中心に押さえる。
    ジャズ喫茶系 BGM の「らしさ」はほぼこれで決まる。
    """
    iv = CHORDS[chord.quality]
    have = set(iv)

    def pick(*cands):
        for c in cands:
            if c in have:
                return c
            if c + 12 in have:
                return c + 12
        return None

    third = pick(4, 3)          # 長 3 度 or 短 3 度
    seventh = pick(10, 11, 9)   # 短 7 / 長 7 / 6th
    ninth = pick(14, 13, 2)
    fifth = pick(7, 6, 8)
    thirteenth = pick(21, 9)

    sel = [v for v in (third, seventh, ninth, fifth or thirteenth) if v is not None]
    if len(sel) < 3:
        sel = iv[:4]

    ps = [chord.root + v for v in sel]
    # center 付近に収める
    out = []
    for p in ps:
        while p < center - 7:
            p += 12
        while p > center + 14:
            p -= 12
        out.append(p)
    return sorted(set(out))


def voice_spread(chord: Chord, low: int = 45, high: int = 84,
                 n_voices: int = 5) -> list[int]:
    """
    パッド用の広いボイシング。低音は根音+5度、上は密集させない。
    低域で 3 度を重ねると濁るので避ける (アンビエントで特に重要)。
    """
    iv = CHORDS[chord.quality]
    root = chord.root
    out = [root - 12, root - 5]  # ルートと 5 度下 (= 4度上)
    upper = [root + i for i in iv if i != 0]
    oct_up = 0
    for i, p in enumerate(upper):
        q = p + 12 * (1 if i >= 2 else 0)
        out.append(q)
    out = [p for p in out if low <= p <= high]
    return sorted(set(out))[:n_voices]


def scale_pitches(root: int, scale: str, lo: int, hi: int) -> list[int]:
    """指定音域のスケール構成音をすべて返す (メロディ生成用)"""
    degs = SCALES[scale]
    pcs = {(root + d) % 12 for d in degs}
    return [p for p in range(lo, hi + 1) if p % 12 in pcs]


def nearest_chord_tone(target: int, chord: Chord, lo: int, hi: int) -> int:
    """target に一番近いコードトーンを返す (メロディを和声に着地させる)"""
    cands = [p for p in range(lo, hi + 1) if p % 12 in chord.pcs]
    if not cands:
        return target
    return min(cands, key=lambda p: abs(p - target))


# ──────────────────────────────────────────────────────────────
# 進行ライブラリ
#   ジャンルごとに「実際によく使われる」進行だけを載せている。
#   root は C を基準に書き、transpose() でキーを移す。
# ──────────────────────────────────────────────────────────────

C3, C4 = 48, 60


def _prog(*specs) -> list[Chord]:
    """('D', 'min9', 1) のようなタプル列 → Chord 列 (オクターブは C4 基準)"""
    out = []
    for name, qual, bars in specs:
        pc = NAME_TO_PC[name]
        out.append(Chord(root=C4 + pc, quality=qual, bars=bars))
    return out


PROGRESSIONS: dict[str, list[list[Chord]]] = {
    # ── lofi hip hop: ii-V-I を軸に、9th/11th で霞ませる
    "lofi": [
        _prog(("D", "min9", 1), ("G", "dom13", 1), ("C", "maj9", 1), ("A", "min11", 1)),
        _prog(("F", "maj9", 1), ("E", "min7", 1), ("D", "min9", 1), ("G", "dom9", 1)),
        _prog(("A", "min9", 1), ("F", "maj7", 1), ("C", "maj9", 1), ("G", "dom9", 1)),
        _prog(("C", "maj9", 2), ("A", "min9", 2)),
    ],
    # ── ジャズ喫茶: 循環コードと ii-V
    "jazz": [
        _prog(("C", "maj7", 1), ("A", "min7", 1), ("D", "min7", 1), ("G", "dom13", 1)),
        _prog(("F", "maj7", 1), ("B", "m7b5", 1), ("E", "dom7b9", 1), ("A", "min9", 1)),
        _prog(("D", "min7", 1), ("G", "dom7", 1), ("C", "maj9", 2)),
        _prog(("E", "min7", 1), ("A", "dom7", 1), ("D", "min7", 1), ("G", "dom7", 1)),
    ],
    # ── ボサノヴァ: maj7/min7 中心、半音下行のベース
    "bossa": [
        _prog(("A", "min7", 1), ("D", "dom9", 1), ("G", "maj7", 1), ("C", "maj7", 1)),
        _prog(("F", "maj7", 1), ("F", "min6", 1), ("C", "maj7", 1), ("A", "dom7b9", 1)),
        _prog(("D", "min9", 1), ("G", "dom13", 1), ("C", "maj9", 1), ("E", "dom7b9", 1)),
    ],
    # ── アンビエント/睡眠: 変化を最小限に。長い持続と全音下行
    "ambient": [
        _prog(("A", "min9", 4), ("F", "maj9", 4), ("C", "maj9", 4), ("G", "add9", 4)),
        _prog(("D", "min9", 4), ("Bb", "maj7", 4)),
        _prog(("C", "maj9", 4), ("A", "min11", 4), ("F", "maj9", 8)),
    ],
    # ── ヒーリング/瞑想: sus とペダルで浮遊させる
    "healing": [
        _prog(("D", "sus2", 4), ("A", "min9", 4), ("G", "maj9", 4), ("D", "sus2", 4)),
        _prog(("C", "add9", 4), ("G", "sus4", 4), ("A", "min9", 4), ("F", "maj9", 4)),
    ],
    # ── ピアノ+雨: 王道のポップ進行を長く伸ばす
    "piano_rain": [
        _prog(("C", "maj9", 2), ("G", "add9", 2), ("A", "min9", 2), ("F", "maj9", 2)),
        _prog(("F", "maj9", 2), ("C", "maj9", 2), ("D", "min9", 2), ("G", "dom9", 2)),
        _prog(("A", "min9", 2), ("E", "min7", 2), ("F", "maj9", 2), ("C", "maj9", 2)),
    ],
    # ── ファンタジー/中世: モーダル。3度を避けて 5度と 4度で
    "fantasy": [
        _prog(("D", "min", 2), ("C", "maj", 2), ("Bb", "maj", 2), ("A", "min", 2)),
        _prog(("D", "sus4", 2), ("F", "maj", 2), ("C", "maj", 2), ("G", "min", 2)),
        _prog(("A", "min", 2), ("G", "maj", 2), ("F", "maj", 2), ("E", "min", 2)),
    ],
    # ── 集中/ディープワーク: ほぼ動かない。1 コードのモーダル
    "focus": [
        _prog(("A", "min11", 8), ("F", "maj9", 8)),
        _prog(("D", "min11", 8), ("G", "add9", 8)),
    ],
    # ── 冬/暖炉: 温かいメジャー系
    "winter": [
        _prog(("F", "maj9", 2), ("A", "min7", 2), ("Bb", "maj7", 2), ("C", "dom9", 2)),
        _prog(("C", "maj9", 2), ("E", "min7", 2), ("F", "maj9", 2), ("G", "dom9", 2)),
    ],
    # ── アニソン風: 日本のアニメ主題歌で定番の進行。
    #    海外の「Emotional Anime Piano」需要はかなり大きい。
    #    情感の正体はコード進行そのものなので、ここを外すと成立しない。
    "anime": [
        # 王道進行 IV-V-iii-vi。J-POP/アニソンで最も多い形。
        # iii→vi で切なさが出て、そのまま次の IV へ戻れる。
        _prog(("F", "maj7", 1), ("G", "dom9", 1),
              ("E", "min7", 1), ("A", "min9", 1)),
        # カノン進行。ベースが順次下降するので旋律が自由に泳げる。
        _prog(("C", "maj9", 1), ("G", "add9", 1), ("A", "min9", 1),
              ("E", "min7", 1), ("F", "maj9", 1), ("C", "maj9", 1),
              ("F", "maj9", 1), ("G", "dom9", 1)),
        # 小室進行 vi-IV-V-I。サビの解放感はこれ。
        _prog(("A", "min9", 1), ("F", "maj9", 1),
              ("G", "dom9", 1), ("C", "maj9", 1)),
        # 一度暗くしてから戻す。転調感が出て「引き」が生まれる。
        _prog(("F", "maj9", 1), ("G", "dom9", 1),
              ("E", "min7", 1), ("A", "min9", 1),
              ("D", "min9", 1), ("G", "dom9", 1), ("C", "maj9", 2)),
    ],
    # ── 爽やか: 朝・晴れ。add9 と maj9 で開けた響きにする。
    #    暗い音 (min7 の連続) を避けるのが「爽やかさ」の条件。
    "fresh": [
        _prog(("D", "add9", 1), ("A", "add9", 1),
              ("B", "min9", 1), ("G", "maj9", 1)),
        _prog(("G", "maj9", 1), ("A", "dom9", 1),
              ("D", "add9", 1), ("B", "min7", 1)),
        _prog(("D", "maj9", 2), ("G", "maj9", 2)),
        _prog(("E", "min9", 1), ("A", "dom9", 1),
              ("D", "add9", 1), ("G", "maj9", 1)),
    ],
    # ── 海/夜: 広がりのある add9 系
    "ocean": [
        _prog(("G", "add9", 4), ("D", "add9", 4), ("E", "min9", 4), ("C", "maj9", 4)),
        _prog(("C", "maj9", 4), ("G", "add9", 4), ("A", "min9", 4), ("F", "maj9", 4)),
    ],
}


def transpose(prog: list[Chord], semitones: int) -> list[Chord]:
    return [Chord(c.root + semitones, c.quality, c.bars,
                  None if c.bass is None else c.bass + semitones) for c in prog]


@dataclass
class Section:
    """展開の 1 ブロック。同じ進行を何回か回して、密度だけ変える"""
    prog: list[Chord]
    repeats: int = 2
    density: float = 1.0        # 0=薄い 1=通常 1.5=濃い
    melody: bool = True
    tag: str = ""


def build_form(progressions: list[list[Chord]], total_bars: float,
               rng: np.random.Generator,
               density_curve=(0.55, 0.8, 1.0, 0.85, 0.65)) -> list[Section]:
    """
    総小節数を埋めるように、進行を並べて「起伏のある構成」を作る。

    ずっと同じ密度だと 2 時間は絶対にもたないので、
    薄い→濃い→薄いの波を density_curve で作り、それを繰り返す。
    """
    sections: list[Section] = []
    bars_done = 0.0
    i = 0
    while bars_done < total_bars:
        prog = progressions[i % len(progressions)]
        prog_bars = sum(c.bars for c in prog)
        d = density_curve[i % len(density_curve)]
        # 薄いセクションは長めに回して「休ませる」
        repeats = 2 if d >= 0.8 else 3
        sec_bars = prog_bars * repeats
        if bars_done + sec_bars > total_bars:
            repeats = max(int((total_bars - bars_done) // prog_bars), 1)
            sec_bars = prog_bars * repeats
        sections.append(Section(
            prog=prog,
            repeats=repeats,
            density=d,
            melody=(d >= 0.7),
            tag=f"S{i}",
        ))
        bars_done += sec_bars
        i += 1
    return sections
