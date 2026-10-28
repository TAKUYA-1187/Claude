"""
シーケンサ / 編曲エンジン。

「2 時間ずっと同じでは飽きるが、変化しすぎると眠りを妨げる」という
BGM 特有の要件に合わせて、
  - 音符の配置は毎回わずかに違う (乱数シードで再現可能)
  - 展開の波は section の density で穏やかに与える
  - タイミングとベロシティは必ず人間らしく散らす
という方針で組んである。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import dsp
from .dsp import SR
from .theory import Chord, Section, nearest_chord_tone, scale_pitches
from .theory import voice_close, voice_jazz_rootless, voice_spread


# ──────────────────────────────────────────────────────────────
# 時間軸
# ──────────────────────────────────────────────────────────────

@dataclass
class Clock:
    """
    ループ長を「秒」で先に決め、そこから BPM を逆算する。

    こうする理由: ループ長がサンプル数でぴったり整数秒になっていないと、
    ffmpeg でループ結合したときに端数がずれて継ぎ目のノイズになる。
    BPM が 80.00 か 79.37 かは誰にも聞き分けられないので、
    「秒を優先し、BPM を合わせる」のが正しい。
    """
    total_seconds: float
    bars: int
    beats_per_bar: int = 4
    sr: int = SR

    @property
    def bar_seconds(self) -> float:
        return self.total_seconds / self.bars

    @property
    def beat_seconds(self) -> float:
        return self.bar_seconds / self.beats_per_bar

    @property
    def bpm(self) -> float:
        return 60.0 / self.beat_seconds

    @property
    def n_samples(self) -> int:
        return int(round(self.total_seconds * self.sr))

    @property
    def total_beats(self) -> int:
        return self.bars * self.beats_per_bar

    def at(self, beat: float) -> int:
        """拍位置 (小数可) → サンプル位置"""
        return int(round(beat * self.beat_seconds * self.sr))

    def dur(self, beats: float) -> float:
        """拍数 → 秒"""
        return beats * self.beat_seconds


@dataclass
class Span:
    """タイムライン上の 1 コード区間"""
    start_beat: float
    end_beat: float
    chord: Chord
    section: Section

    @property
    def beats(self) -> float:
        return self.end_beat - self.start_beat


def build_timeline(sections: list[Section], clock: Clock) -> list[Span]:
    """Section 列 → コード区間の並び。総拍数がクロックを超えたら打ち切る"""
    spans: list[Span] = []
    beat = 0.0
    limit = float(clock.total_beats)
    for sec in sections:
        for _ in range(sec.repeats):
            for ch in sec.prog:
                b = ch.bars * clock.beats_per_bar
                if beat >= limit:
                    return spans
                spans.append(Span(beat, min(beat + b, limit), ch, sec))
                beat += b
    return spans


def chord_at(spans: list[Span], beat: float) -> Span:
    for s in spans:
        if s.start_beat <= beat < s.end_beat:
            return s
    return spans[-1]


# ──────────────────────────────────────────────────────────────
# 加算ヘルパ
# ──────────────────────────────────────────────────────────────

def add_panned(buf: np.ndarray, sample: np.ndarray, pos: int,
               gain: float = 1.0, pan: float = 0.0) -> None:
    """mono サンプルを定パワーパンで stereo バッファへ加算する"""
    if gain <= 0.0:
        return
    ang = (float(np.clip(pan, -1, 1)) + 1.0) * 0.25 * np.pi
    gl, gr = float(np.cos(ang)) * gain, float(np.sin(ang)) * gain
    n_buf = buf.shape[0]
    if pos >= n_buf:
        return
    if pos < 0:
        sample = sample[-pos:]
        pos = 0
    n = min(sample.shape[0], n_buf - pos)
    if n <= 0:
        return
    buf[pos:pos + n, 0] += sample[:n] * gl
    buf[pos:pos + n, 1] += sample[:n] * gr


def humanize(rng: np.random.Generator, ms: float = 12.0, sr: int = SR) -> int:
    """タイミングの微妙なズレ。これが無いと一瞬で打ち込みだとバレる"""
    return int(rng.normal(0.0, ms * 0.001 * sr))


# ──────────────────────────────────────────────────────────────
# プレイヤー: パッド / ドローン
# ──────────────────────────────────────────────────────────────

def play_pad(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
             gain: float = 0.16, octave: int = 0, brightness: float = 1.0,
             attack: float = 1.6, release: float = 2.2,
             rng: np.random.Generator | None = None,
             n_voices: int = 5, low: int = 45, high: int = 84) -> None:
    """
    コードごとに長いパッドを敷く。
    隣り合うコードのパッドを重ねてクロスフェードさせるのが肝で、
    そうしないとコードチェンジのたびに音が途切れて眠りを妨げる。
    """
    rng = rng or np.random.default_rng(0)
    for sp in spans:
        pitches = voice_spread(sp.chord, low=low, high=high, n_voices=n_voices)
        # 次のコードへ食い込ませる長さ
        dur = clock.dur(sp.beats) + release
        pos = clock.at(sp.start_beat)
        n = int(dur * clock.sr)
        env = np.ones(n, dtype=np.float32)
        na = min(int(attack * clock.sr), n // 2)
        nr = min(int(release * clock.sr), n // 2)
        env[:na] = np.linspace(0, 1, na, dtype=np.float32) ** 1.6
        env[-nr:] = np.linspace(1, 0, nr, dtype=np.float32) ** 1.6
        g = gain * sp.section.density
        for i, p in enumerate(pitches):
            v = bank.sustained("pad", p + 12 * octave, dur,
                               brightness=brightness, n_detune=3)
            pn = (i / max(len(pitches) - 1, 1) - 0.5) * 1.3
            add_panned(buf, (v[:n] * env).astype(np.float32), pos,
                       g / max(len(pitches) ** 0.5, 1.0), pn)


def play_drone(buf: np.ndarray, root_midi: int, clock: Clock, bank,
               gain: float = 0.12, partials: int = 12) -> None:
    """
    全長にわたる 1 本のドローン。睡眠/瞑想系の土台。
    ループ長ぴったりで作り、内部の LFO も整数周期なので継ぎ目が出ない。
    """
    n = clock.n_samples
    v = bank.sustained("drone", root_midi, n / clock.sr, partials=partials)
    add_panned(buf, v[:n], 0, gain * 0.5, -0.25)
    add_panned(buf, v[:n], 0, gain * 0.5, +0.25)


# ──────────────────────────────────────────────────────────────
# プレイヤー: コード伴奏 (コンピング)
# ──────────────────────────────────────────────────────────────

#   拍位置のパターン。1 小節 (4拍) を単位に、拍のオフセットで表す。
COMP_PATTERNS = {
    "lofi":   [[0.0, 1.5, 2.5], [0.0, 2.0], [0.0, 1.5, 2.5, 3.5], [0.5, 2.0, 3.0]],
    "jazz":   [[0.0, 1.5], [0.5, 2.5], [0.0, 2.0, 3.5], [1.0, 2.5]],
    "bossa":  [[0.0, 1.5, 2.5], [0.0, 1.5, 3.0], [0.5, 1.5, 2.5, 3.5]],
    "sparse": [[0.0], [0.0, 2.0]],
    "ballad": [[0.0], [0.0, 2.5]],
}


def play_comp(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
              inst: str = "rhodes", style: str = "lofi", gain: float = 0.22,
              voicing: str = "rootless", center: int = 62,
              swing: float = 0.0, rng: np.random.Generator | None = None,
              spread_ms: float = 18.0, pan: float = 0.0) -> None:
    """
    コード伴奏。
    voicing='rootless' でジャズらしく、'close' でポップスらしくなる。
    spread_ms は「和音を完全に同時に鳴らさない」ためのばらし幅で、
    これがあると鍵盤を押さえた感じが出る。
    """
    rng = rng or np.random.default_rng(1)
    pats = COMP_PATTERNS[style]

    for sp in spans:
        if sp.section.density < 0.5:
            continue
        pitches = (voice_jazz_rootless(sp.chord, center) if voicing == "rootless"
                   else voice_close(sp.chord, center, n_voices=4))
        bars = int(np.ceil(sp.beats / clock.beats_per_bar))
        for b in range(bars):
            pat = pats[int(rng.integers(0, len(pats)))]
            for off in pat:
                beat = sp.start_beat + b * clock.beats_per_bar + off
                if beat >= sp.end_beat:
                    continue
                # スイング: 裏拍を後ろにずらす
                sw = swing * clock.beat_seconds * 0.5 if (off % 1.0) >= 0.5 else 0.0
                base = clock.at(beat) + int(sw * clock.sr) + humanize(rng, 10.0)
                vel = float(np.clip(rng.normal(0.62, 0.11), 0.25, 0.95))
                vel *= 0.75 + 0.35 * sp.section.density
                for i, p in enumerate(pitches):
                    s = bank.note(inst, p, vel)
                    jitter = int(rng.uniform(0, spread_ms * 0.001 * clock.sr))
                    pn = pan + (i / max(len(pitches) - 1, 1) - 0.5) * 0.5
                    add_panned(buf, s, base + jitter,
                               gain / max(len(pitches) ** 0.45, 1.0), pn)


def play_arp(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
             inst: str = "harp", gain: float = 0.14, rate: float = 0.5,
             octaves: int = 2, center: int = 64, direction: str = "updown",
             rng: np.random.Generator | None = None, pan: float = 0.0) -> None:
    """アルペジオ。rate は 1 音あたりの拍数 (0.5 = 8分音符)"""
    rng = rng or np.random.default_rng(2)
    for sp in spans:
        if sp.section.density < 0.6:
            continue
        base_p = voice_close(sp.chord, center, n_voices=4)
        seq = []
        for o in range(octaves):
            seq.extend([p + 12 * o for p in base_p])
        if direction == "updown":
            seq = seq + seq[-2:0:-1]
        elif direction == "down":
            seq = seq[::-1]
        if not seq:
            continue
        k = 0
        beat = sp.start_beat
        while beat < sp.end_beat:
            p = seq[k % len(seq)]
            vel = float(np.clip(rng.normal(0.5, 0.10), 0.2, 0.85))
            s = bank.note(inst, p, vel)
            add_panned(buf, s, clock.at(beat) + humanize(rng, 9.0),
                       gain * sp.section.density,
                       pan + 0.35 * np.sin(k * 0.7))
            beat += rate
            k += 1


# ──────────────────────────────────────────────────────────────
# プレイヤー: ベース
# ──────────────────────────────────────────────────────────────

def play_bass(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
              inst: str = "subbass", style: str = "root", gain: float = 0.26,
              octave: int = -2, rng: np.random.Generator | None = None,
              scale_root: int = 0, scale: str = "major") -> None:
    """
    style:
      root    … 各コードの頭でルートを 1 発 (lofi/アンビエント)
      pump    … ルート + 5度を交互に (lofi)
      walk    … ウォーキングベース (ジャズ)
      bossa   … ルート→5度の 2 分音符 (ボサノヴァ)
    """
    rng = rng or np.random.default_rng(3)
    lo, hi = 33, 55

    def clamp(p):
        while p < lo:
            p += 12
        while p > hi:
            p -= 12
        return p

    for sp in spans:
        root = clamp(sp.chord.bass_note() + 12 * octave)
        fifth = clamp(root + 7)
        bars = max(int(round(sp.beats / clock.beats_per_bar)), 1)

        if style == "root":
            for b in range(bars):
                beat = sp.start_beat + b * clock.beats_per_bar
                if beat >= sp.end_beat:
                    break
                add_panned(buf, bank.note(inst, root, 0.8),
                           clock.at(beat) + humanize(rng, 12.0), gain, 0.0)

        elif style == "pump":
            for b in range(bars):
                for off, p in ((0.0, root), (2.5, fifth)):
                    beat = sp.start_beat + b * clock.beats_per_bar + off
                    if beat >= sp.end_beat:
                        continue
                    add_panned(buf, bank.note(inst, p, 0.75 if off else 0.85),
                               clock.at(beat) + humanize(rng, 12.0), gain, 0.0)

        elif style == "bossa":
            for b in range(bars):
                for off, p in ((0.0, root), (1.5, fifth), (2.0, fifth), (3.5, root)):
                    beat = sp.start_beat + b * clock.beats_per_bar + off
                    if beat >= sp.end_beat:
                        continue
                    add_panned(buf, bank.note(inst, p, 0.62 + 0.2 * (off == 0)),
                               clock.at(beat) + humanize(rng, 10.0), gain * 0.85, 0.0)

        elif style == "walk":
            # 4 分音符で、コードトーン → 経過音 → 次のコードへ半音で着地
            allowed = scale_pitches(scale_root, scale, lo, hi)
            cur = root
            n_beats = int(sp.beats)
            for i in range(n_beats):
                beat = sp.start_beat + i
                if i == 0:
                    p = root
                elif i == n_beats - 1:
                    # 次のコードのルートへ半音上/下からアプローチ
                    nxt = clamp(chord_at(spans, min(beat + 1, clock.total_beats - 1))
                                .chord.bass_note() + 12 * octave)
                    p = nxt + int(rng.choice([-1, 1]))
                else:
                    cands = [q for q in allowed if abs(q - cur) <= 5 and q != cur]
                    p = int(rng.choice(cands)) if cands else cur
                    if i == n_beats // 2:
                        p = nearest_chord_tone(p, sp.chord, lo, hi)
                cur = p
                add_panned(buf, bank.note(inst, clamp(p), 0.72),
                           clock.at(beat) + humanize(rng, 11.0), gain, 0.0)


# ──────────────────────────────────────────────────────────────
# プレイヤー: メロディ / 装飾
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 作曲型の旋律 (v2)
# ──────────────────────────────────────────────────────────────
#
# 2026-10-28: オーナーの評価「メロディは良いが高評価とは言えない。聞きやすく高品質に」。
# v1 (motif) は進行ごとに作ったフレーズを繰り返していたが、フレーズの中身は
# 1 音ずつの酔歩で、歌の形 (動機・問いと答え・終止) を持っていなかった。
# v2 は作曲の定石どおりに組み立てる:
#   - 1 小節の動機 a を作り、次の小節で高さを変えて模倣する (a')
#   - 8 小節を「問い (4 小節目で 2 度か 5 度に半終止)」+「答え (8 小節目で主音に終止)」にする
#   - 6 小節目あたりを頂点にした山形の旋律線
#   - 強拍は必ずコードトーン、弱拍は順次進行。跳躍は動機の頭だけ
#   - 終止の音は長く伸ばして、次のフレーズの前に息継ぎを入れる

_MOTIFS_SPARSE = [[2.0, 2.0], [3.0, 1.0], [2.0, 1.0, 1.0], [1.0, 1.0, 2.0]]
_MOTIFS = [[1.0, 1.0, 2.0], [2.0, 1.0, 1.0], [1.5, 0.5, 2.0], [1.0, 1.0, 1.0, 1.0],
           [1.0, 0.5, 0.5, 2.0], [2.0, 2.0], [3.0, 1.0]]
# 8 小節の役割と、旋律線の高さ (中心からの音階の段数)
_PERIOD_ROLES = ["a", "a2", "b", "H", "a", "a2", "b2", "F"]
_PERIOD_CONTOUR = [0, 1, 2, 1, 1, 3, 2, 0]


def _compose_phrase(prog, bpb: int, allowed: list[int], tonic_pc: int,
                    rng: np.random.Generator, sparse: bool) -> list[tuple[float, int, float]]:
    """進行 1 周ぶんの旋律を作る。戻り値は (進行頭からの拍, 音高, ベロシティ) の列"""
    arr = np.asarray(allowed)
    n_bars = max(int(round(sum(c.bars for c in prog))), 1)
    edges, b = [], 0.0
    for c in prog:
        edges.append((b * bpb, (b + c.bars) * bpb, c))
        b += c.bars

    def chord_at(beat):
        for s0, s1, c in edges:
            if s0 <= beat < s1:
                return c
        return prog[-1]

    def idx(p):
        return int(np.argmin(np.abs(arr - p)))

    def chord_tone_near(target, chord):
        cands = [p for p in allowed if p % 12 in chord.pcs]
        return min(cands, key=lambda p: abs(p - target)) if cands else target

    def degree_near(target, pcs, chord):
        """pcs (音階の度数) のうち、コードに含まれるものを優先して target 近くを選ぶ"""
        want = [p for p in allowed if p % 12 in pcs and p % 12 in chord.pcs]
        if not want:
            want = [p for p in allowed if p % 12 in pcs] or allowed
        return min(want, key=lambda p: abs(p - target))

    pool = _MOTIFS_SPARSE if sparse else _MOTIFS
    ra = pool[int(rng.integers(len(pool)))]
    rb = pool[int(rng.integers(len(pool)))]
    if rb == ra and len(pool) > 1:
        rb = pool[(pool.index(ra) + 1) % len(pool)]
    center = len(allowed) // 2

    # 役割を小節に割り当てる (8 小節単位。最後の小節は必ず終止)
    roles, contour = [], []
    for i in range(n_bars):
        roles.append(_PERIOD_ROLES[i % 8])
        contour.append(_PERIOD_CONTOUR[i % 8])
    roles[-1] = "F"
    if n_bars >= 8 and n_bars % 8 == 0 and n_bars > 8:
        for i in range(7, n_bars - 1, 8):
            roles[i] = "H"          # 途中の周期の終わりは半終止にして先へつなぐ

    shapes: dict[str, list[int]] = {}
    notes: list[tuple[float, int, float]] = []
    second_pcs = {(tonic_pc + 2) % 12, (tonic_pc + 7) % 12}
    for bar, role in enumerate(roles):
        t0 = bar * bpb
        target = allowed[int(np.clip(center + contour[bar], 0, len(allowed) - 1))]
        climax = 0.05 if contour[bar] >= 2 else 0.0
        if role in ("H", "F"):
            ch = chord_at(t0)
            # 終止音は直前の音の近くに置く (オクターブ跳んで終わると唐突に聞こえた)
            prev = notes[-1][1] if notes else target
            land = degree_near(prev if role == "H" else prev - 1,
                               second_pcs if role == "H" else {tonic_pc}, ch)
            if role == "H" and not sparse:
                # 半終止の前に 1 音だけ経過音を置く
                pre = allowed[int(np.clip(idx(land) + 1, 0, len(allowed) - 1))]
                notes.append((t0, pre, 0.50))
                notes.append((t0 + bpb / 2, land, 0.48))
            else:
                notes.append((t0, land, 0.46 if role == "F" else 0.5))
            continue
        rhythm = ra if role in ("a", "a2") else rb
        base = role.rstrip("2")
        beat, pitches = 0.0, []
        start = chord_tone_near(target, chord_at(t0))
        if base in shapes:
            # 模倣: 同じ動機の音程の形 (音階の段数) を、この小節の和音に合わせて置き直す
            steps = shapes[base]
            if role.endswith("2"):
                steps = steps[:-1] + [steps[-1] + int(rng.choice([-1, 1]))]
            cur = idx(start)
            for k, dur in enumerate(rhythm):
                if k > 0:
                    cur = int(np.clip(cur + steps[min(k - 1, len(steps) - 1)], 0, len(allowed) - 1))
                p = allowed[cur]
                strong = abs((beat % 2.0)) < 1e-6
                if strong and p % 12 not in chord_at(t0 + beat).pcs:
                    p = chord_tone_near(p, chord_at(t0 + beat))
                    cur = idx(p)
                pitches.append(p)
                beat += dur
        else:
            # 新しい動機: b は頭で少し跳んでから順次に下りる、a は順次で目標へ向かう
            cur = idx(start) + (2 if base == "b" else 0)
            cur = int(np.clip(cur, 0, len(allowed) - 1))
            steps = []
            for k, dur in enumerate(rhythm):
                if k > 0:
                    st = int(rng.choice([-1, 1, -2, 1] if base == "b" else [1, -1, 1, 2]))
                    if base == "b":
                        st = -abs(st) if rng.random() < 0.7 else abs(st)
                    steps.append(st)
                    cur = int(np.clip(cur + st, 0, len(allowed) - 1))
                p = allowed[cur]
                strong = abs((beat % 2.0)) < 1e-6
                if strong and p % 12 not in chord_at(t0 + beat).pcs:
                    p = chord_tone_near(p, chord_at(t0 + beat))
                    cur = idx(p)
                pitches.append(p)
                beat += dur
            shapes[base] = steps or [0]
        beat = 0.0
        for p, dur in zip(pitches, rhythm):
            strong = abs(beat % 2.0) < 1e-6
            vel = 0.52 + (0.06 if strong else 0.0) + climax + float(rng.normal(0, 0.025))
            notes.append((t0 + beat, p, float(np.clip(vel, 0.3, 0.8))))
            beat += dur
    return notes


def play_melody(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
                inst: str = "piano", gain: float = 0.20,
                scale_root: int = 0, scale: str = "major",
                lo: int = 62, hi: int = 86, density: float = 0.45,
                rng: np.random.Generator | None = None,
                pan: float = 0.12, rest_prob: float = 0.35,
                motif: bool = True, composed: bool = True) -> None:
    """
    生成メロディ。

    ルール:
      - 音程は基本 2 度・3 度で動く (跳躍しすぎると耳が起きる)
      - 小節頭とフレーズ終わりはコードトーンに着地させる
      - 休符をしっかり入れる。BGM は「鳴っていない時間」が命

    motif=True (既定) では、進行の中の「何番目のコードか」ごとにフレーズを
    1 度だけ作り、同じ進行が戻ってくるたびに同じフレーズを弾く。
    以前は毎回その場で音を選んでいたため旋律が二度と戻らず、さらに薄い
    区間ではメロディを丸ごと止めていた。視聴者には「途中からメロディが
    変わる」「(残った環境音が) 雑音っぽくなる」と聞こえた。
    薄い区間でも同じフレーズを音数を減らして弾き、旋律を途切れさせない。
    """
    rng = rng or np.random.default_rng(4)
    allowed = scale_pitches(scale_root, scale, lo, hi)
    if not allowed:
        return
    arr = np.asarray(allowed)

    def idx_of(p: int) -> int:
        """
        スケール外の音 (コードトーンに着地させた結果など) が来ても
        壊れないよう、常に「一番近いスケール音の位置」を返す。
        """
        return int(np.argmin(np.abs(arr - p)))

    cur = allowed[len(allowed) // 2]

    if composed:
        # v2: 進行 1 周ごとに作曲した旋律を、同じ進行が戻るたびにそのまま弾く
        bpb = clock.beats_per_bar
        phrases2: dict[int, list] = {}
        pass_start = 0.0
        for sp in spans:
            prog = sp.section.prog
            slot = next((i for i, c in enumerate(prog) if c is sp.chord), 0)
            if slot == 0:
                pass_start = sp.start_beat
            ph = phrases2.get(id(prog))
            if ph is None:
                ph = _compose_phrase(prog, bpb, allowed, scale_root % 12, rng,
                                     sparse=density < 0.45)
                phrases2[id(prog)] = ph
            dens = sp.section.density
            keep = 0.45 + 0.55 * min(dens / 0.85, 1.0)
            lo_b, hi_b = sp.start_beat - pass_start, sp.end_beat - pass_start
            for off, pitch, vel in ph:
                if not (lo_b <= off < hi_b):
                    continue
                if abs(off % bpb) > 1e-6 and rng.random() > keep:
                    continue
                v = float(np.clip(vel * density * 1.6, 0.2, 0.95))
                add_panned(buf, bank.note(inst, pitch, v),
                           clock.at(pass_start + off) + humanize(rng, 12.0),
                           gain * (0.55 + 0.45 * min(dens, 1.0)), pan)
        return

    if motif:
        phrases: dict[tuple, list[tuple[float, int, float]]] = {}
        for sp in spans:
            prog = sp.section.prog
            slot = next((i for i, c in enumerate(prog) if c is sp.chord), 0)
            key = (id(prog), slot)
            ph = phrases.get(key)
            if ph is None:
                ph = []
                beat = 0.0
                while beat < sp.beats:
                    step = float(rng.choice([0.5, 1.0, 1.0, 1.5, 2.0, 2.0, 3.0],
                                            p=[0.10, 0.22, 0.20, 0.14, 0.16, 0.10, 0.08]))
                    if rng.random() < rest_prob * 0.6:
                        beat += step
                        continue
                    move = int(rng.choice([-3, -2, -1, 1, 2, 3],
                                          p=[0.08, 0.20, 0.22, 0.22, 0.20, 0.08]))
                    nxt = allowed[int(np.clip(idx_of(cur) + move, 0, len(allowed) - 1))]
                    on_bar = abs(beat % clock.beats_per_bar) < 1e-6
                    if on_bar or step >= 2.0:
                        nxt = nearest_chord_tone(nxt, sp.chord, lo, hi)
                    cur = nxt
                    vel = float(np.clip(rng.normal(0.55, 0.10), 0.25, 0.85))
                    ph.append((beat, cur, vel))
                    beat += step
                phrases[key] = ph
            dens = sp.section.density
            # 薄い区間ほど音を間引く。ただし小節頭の音は残して旋律の形を保つ
            keep = 0.45 + 0.55 * min(dens / 0.85, 1.0)
            for (off, pitch, vel) in ph:
                if sp.start_beat + off >= sp.end_beat:
                    break
                if abs(off % clock.beats_per_bar) > 1e-6 and rng.random() > keep:
                    continue
                v = float(np.clip(vel * density * 1.6, 0.2, 0.95))
                s = bank.note(inst, pitch, v)
                add_panned(buf, s, clock.at(sp.start_beat + off) + humanize(rng, 16.0),
                           gain * (0.55 + 0.45 * min(dens, 1.0)), pan)
        return

    for sp in spans:
        if not sp.section.melody or sp.section.density < 0.7:
            continue
        beat = sp.start_beat
        while beat < sp.end_beat:
            # 音価: 8分〜2分をランダムに (長めを多めに)
            step = float(rng.choice([0.5, 1.0, 1.0, 1.5, 2.0, 2.0, 3.0],
                                    p=[0.10, 0.22, 0.20, 0.14, 0.16, 0.10, 0.08]))
            if rng.random() < rest_prob * (1.4 - sp.section.density):
                beat += step
                continue
            # 順次進行を優先しつつたまに跳躍
            move = int(rng.choice([-4, -3, -2, -1, 1, 2, 3, 4],
                                  p=[0.06, 0.10, 0.18, 0.16, 0.16, 0.18, 0.10, 0.06]))
            idx = int(np.clip(idx_of(cur) + move, 0, len(allowed) - 1))
            nxt = allowed[idx]
            on_bar = abs((beat - sp.start_beat) % clock.beats_per_bar) < 1e-6
            if on_bar or step >= 2.0:
                nxt = nearest_chord_tone(nxt, sp.chord, lo, hi)
            cur = nxt
            vel = float(np.clip(rng.normal(0.55, 0.12), 0.22, 0.9)) * density * 1.6
            s = bank.note(inst, cur, float(np.clip(vel, 0.2, 0.95)))
            add_panned(buf, s, clock.at(beat) + humanize(rng, 16.0),
                       gain * sp.section.density, pan)
            beat += step


def play_sparse_bells(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
                      inst: str = "bowl", gain: float = 0.18,
                      every_bars: float = 8.0, center: int = 55,
                      rng: np.random.Generator | None = None) -> None:
    """
    数小節に 1 回だけ鳴らす鐘/ボウル。
    瞑想系の「間」を作る。鳴らしすぎると一気に安っぽくなる。
    """
    rng = rng or np.random.default_rng(5)
    beat = 0.0
    limit = float(clock.total_beats)
    while beat < limit:
        sp = chord_at(spans, beat)
        p = nearest_chord_tone(center, sp.chord, center - 7, center + 7)
        add_panned(buf, bank.note(inst, p, float(rng.uniform(0.5, 0.85))),
                   clock.at(beat) + humanize(rng, 40.0), gain,
                   float(rng.uniform(-0.4, 0.4)))
        beat += every_bars * clock.beats_per_bar * float(rng.uniform(0.8, 1.25))


# ──────────────────────────────────────────────────────────────
# プレイヤー: ドラム
# ──────────────────────────────────────────────────────────────

def play_lofi_drums(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
                    gain: float = 0.30, swing: float = 0.16,
                    rng: np.random.Generator | None = None,
                    use_rim: bool = True) -> None:
    """
    lofi hip hop のビート。

    肝は「わざと少しヨレていること」。キックは気持ち前、スネアは
    気持ち後ろに置くと、あの気だるいグルーヴになる。
    """
    rng = rng or np.random.default_rng(6)
    bpb = clock.beats_per_bar
    n_bars = clock.bars

    for b in range(n_bars):
        base_beat = b * bpb
        sp = chord_at(spans, base_beat)
        d = sp.section.density
        if d < 0.5:
            continue
        g = gain * (0.6 + 0.5 * d)

        # キック: 1 拍目 + 気まぐれに 3 拍裏
        kicks = [0.0]
        if rng.random() < 0.75:
            kicks.append(2.5 if rng.random() < 0.6 else 2.0)
        if rng.random() < 0.25:
            kicks.append(3.75)
        for off in kicks:
            add_panned(buf, bank.hit("kick"),
                       clock.at(base_beat + off) + humanize(rng, 8.0) - 300,
                       g * float(rng.uniform(0.85, 1.0)), 0.0)

        # スネア/リム: 2・4 拍。少し後ろに置く
        for off in (1.0, 3.0):
            name = "rim" if (use_rim and rng.random() < 0.35) else "snare"
            add_panned(buf, bank.hit(name),
                       clock.at(base_beat + off) + humanize(rng, 9.0) + 700,
                       g * float(rng.uniform(0.8, 1.0)) * (0.8 if name == "rim" else 1.0),
                       float(rng.uniform(-0.08, 0.08)))

        # ハイハット: 8分。裏拍をスイングさせる
        for i in range(bpb * 2):
            off = i * 0.5
            if rng.random() < 0.12:
                continue
            sw = swing * clock.beat_seconds * 0.5 if i % 2 else 0.0
            vel = 0.9 if i % 2 == 0 else 0.55
            add_panned(buf, bank.hit("hat", open_hat=(rng.random() < 0.06)),
                       clock.at(base_beat + off) + int(sw * clock.sr) + humanize(rng, 7.0),
                       g * vel * float(rng.uniform(0.7, 1.0)) * 0.8,
                       float(rng.uniform(-0.25, 0.25)))


def play_jazz_brushes(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
                      gain: float = 0.22, rng: np.random.Generator | None = None,
                      ride_prob: float = 0.6) -> None:
    """ジャズのブラシ + ライド。スウィングの 3 連符感を出す"""
    rng = rng or np.random.default_rng(7)
    bpb = clock.beats_per_bar
    for b in range(clock.bars):
        base_beat = b * bpb
        sp = chord_at(spans, base_beat)
        d = sp.section.density
        if d < 0.5:
            continue
        g = gain * (0.6 + 0.5 * d)
        # ブラシのスウィープ (各拍)
        for i in range(bpb):
            add_panned(buf, bank.hit("brush"),
                       clock.at(base_beat + i) + humanize(rng, 14.0),
                       g * float(rng.uniform(0.7, 1.0)), -0.15)
        # ライド: 4分 + 3連の裏 (ding-ding-a-ding)
        if rng.random() < ride_prob:
            for i in range(bpb):
                add_panned(buf, bank.hit("ride"),
                           clock.at(base_beat + i) + humanize(rng, 10.0),
                           g * 0.55 * float(rng.uniform(0.8, 1.0)), 0.25)
                if i % 2 == 1:
                    add_panned(buf, bank.hit("ride"),
                               clock.at(base_beat + i + 2.0 / 3.0) + humanize(rng, 10.0),
                               g * 0.32, 0.25)


def play_sleigh(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
                gain: float = 0.14, rng: np.random.Generator | None = None) -> None:
    """
    スレイベル。8分で振り続け、表拍にアクセント。
    クリスマス感はほぼこれ 1 本で出る。音量を上げすぎると安っぽくなる。
    """
    rng = rng or np.random.default_rng(9)
    bpb = clock.beats_per_bar
    for b in range(clock.bars):
        base_beat = b * bpb
        sp = chord_at(spans, base_beat)
        if sp.section.density < 0.5:
            continue
        g = gain * (0.6 + 0.5 * sp.section.density)
        for i in range(bpb * 2):
            off = i * 0.5
            vel = 1.0 if i % 2 == 0 else 0.62
            add_panned(buf, bank.hit("sleigh"),
                       clock.at(base_beat + off) + humanize(rng, 9.0),
                       g * vel * float(rng.uniform(0.8, 1.0)),
                       float(rng.uniform(-0.1, 0.1)))


def play_bossa_perc(buf: np.ndarray, spans: list[Span], clock: Clock, bank,
                    gain: float = 0.20, rng: np.random.Generator | None = None) -> None:
    """ボサノヴァのリズム。シェイカー + リム (クラーベ風)"""
    rng = rng or np.random.default_rng(8)
    bpb = clock.beats_per_bar
    clave = [0.0, 1.5, 3.0]          # 前小節
    clave2 = [0.5, 2.0, 3.0]         # 後小節
    for b in range(clock.bars):
        base_beat = b * bpb
        sp = chord_at(spans, base_beat)
        if sp.section.density < 0.5:
            continue
        g = gain * (0.6 + 0.5 * sp.section.density)
        for i in range(bpb * 2):
            add_panned(buf, bank.hit("shaker"),
                       clock.at(base_beat + i * 0.5) + humanize(rng, 8.0),
                       g * (0.9 if i % 2 == 0 else 0.55) * float(rng.uniform(0.8, 1.0)),
                       float(rng.uniform(-0.3, 0.3)))
        for off in (clave if b % 2 == 0 else clave2):
            add_panned(buf, bank.hit("rim"),
                       clock.at(base_beat + off) + humanize(rng, 10.0),
                       g * 0.7, -0.2)


DRUMMERS = {
    "lofi": play_lofi_drums,
    "jazz": play_jazz_brushes,
    "bossa": play_bossa_perc,
}
