"""
歌声の合成 (ヴォカリーズ = 歌詞なしの歌声)。

何ができて何ができないかを最初に書いておく:

  できること   母音 (ア・オ・ウ・エ・イ) とハミングで旋律を「歌う」声。
               ビブラート・ポルタメント・息継ぎ・かすれまで作り込むと、
               「シンセの歌声」としてちゃんと聴ける。
  できないこと 歌詞。子音の連結 (歌詞が聞き取れる歌) は音素合成の領域で、
               ライセンスされた歌声ライブラリ (VOCALOID 等) か
               大規模なニューラルモデルが必要。ここでは嘘をつかない。

仕組みは source-filter モデルの加算合成版:
  1. 声帯 = 倍音列 (位相は f0 の積分。ポルタメント/ビブラートもここ)
  2. 声道 = フォルマント (共鳴) カーブを各倍音の振幅に直接かける
     → フィルタを使わないのでエイリアシングも位相事故も起きない
  3. 息  = 帯域ノイズを声の包絡に沿わせて薄く足す
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import dsp
from .dsp import SR, TWO_PI, midi2hz


# ──────────────────────────────────────────────────────────────
# フォルマント表 (F1..F4 [Hz], 相対ゲイン [dB], 帯域幅 [Hz])
# ──────────────────────────────────────────────────────────────

_VOWELS_F = {   # 高い声 (女声寄り)
    "a": ([850, 1220, 2810, 3500], [0, -7, -9, -14]),
    "o": ([450, 800, 2830, 3500], [0, -6, -12, -16]),
    "u": ([370, 950, 2670, 3400], [0, -8, -13, -17]),
    "e": ([610, 2330, 2990, 3600], [0, -9, -11, -15]),
    "i": ([310, 2790, 3310, 3900], [0, -10, -10, -15]),
    "m": ([250, 1000, 2200, 3200], [0, -18, -22, -26]),   # ハミング
}
_VOWELS_M = {   # 低い声 (男声寄り)
    "a": ([730, 1090, 2440, 3400], [0, -7, -10, -15]),
    "o": ([460, 880, 2530, 3300], [0, -6, -13, -17]),
    "u": ([300, 870, 2240, 3200], [0, -8, -14, -18]),
    "e": ([530, 1840, 2480, 3400], [0, -9, -12, -16]),
    "i": ([270, 2290, 3010, 3700], [0, -10, -11, -16]),
    "m": ([220, 900, 2100, 3100], [0, -18, -22, -26]),
}
_BW = [90, 110, 150, 180]


@dataclass
class Voice:
    """声のプリセット"""
    name: str
    vowels: dict
    formant_scale: float     # フォルマント全体の伸縮 (声の大きさ・性別感)
    tilt_db_oct: float       # スペクトル傾斜。負で暗い声
    vibrato_hz: float
    vibrato_cents: float
    vibrato_delay: float     # ビブラートが始まるまでの秒数
    breath: float            # 息の量 (0..1)
    jitter_cents: float      # ピッチの微揺れ


# 高い声。合成音声らしい透明感を隠さず、きれいに響かせる方向
HIKARI = Voice("hikari", _VOWELS_F, formant_scale=1.12, tilt_db_oct=-4.5,
               vibrato_hz=5.8, vibrato_cents=32.0, vibrato_delay=0.22,
               breath=0.35, jitter_cents=7.0)

# 低い声。息多め・ビブラート深めで情感を出す
AOI = Voice("aoi", _VOWELS_M, formant_scale=1.0, tilt_db_oct=-6.5,
            vibrato_hz=5.1, vibrato_cents=42.0, vibrato_delay=0.30,
            breath=0.5, jitter_cents=9.0)

VOICES = {"hikari": HIKARI, "aoi": AOI}


# ──────────────────────────────────────────────────────────────
# 1 音の合成
# ──────────────────────────────────────────────────────────────

def _formant_gain(freqs: np.ndarray, voice: Voice, vowel: str) -> np.ndarray:
    """周波数列に対する声道のゲイン (フォルマント共鳴の和 + 傾斜)"""
    Fs, Gs = voice.vowels[vowel]
    g = np.zeros_like(freqs)
    for F, G, B in zip(Fs, Gs, _BW):
        F = F * voice.formant_scale
        g += dsp.db2lin(G) / (1.0 + ((freqs - F) / (B * 1.4)) ** 2)
    # 声帯そのものの傾斜 (-12dB/oct 程度) + 声のキャラクタの傾斜
    tilt = (np.maximum(freqs, 60.0) / 500.0) ** ((-12.0 + voice.tilt_db_oct) / 6.0
                                                 * 0.5)
    return g * tilt


def sing_note(voice: Voice, midi: float, dur: float, vowel: str = "a",
              prev_midi: float | None = None, vel: float = 0.8,
              phrase_end: bool = False, seed: int = 0,
              sr: int = SR) -> np.ndarray:
    """
    1 音を歌う。
      prev_midi   直前の音。指定するとポルタメントで滑らかに入る
      phrase_end  フレーズ末尾ならリリースを長く取り、息を混ぜる
    """
    rng = np.random.default_rng(seed + int(midi * 100))
    n = int(dur * sr)
    if n < 32:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n, dtype=np.float64) / sr

    # ── f0 の軌跡 ─────────────────────────────────────────
    f_target = float(midi2hz(midi))
    f0 = np.full(n, f_target)
    # ポルタメント: 前の音から 70ms で滑り込む
    if prev_midi is not None and abs(prev_midi - midi) > 0.1:
        n_g = min(int(0.07 * sr), n)
        f_prev = float(midi2hz(prev_midi))
        f0[:n_g] = f_prev * (f_target / f_prev) ** (np.arange(n_g) / max(n_g, 1))
    # オーバーシュート: 狙いの 25 cent 上を掠めて戻る (歌の生っぽさの素)
    n_o = min(int(0.12 * sr), n)
    f0[:n_o] *= 2.0 ** (25.0 / 1200.0 * np.sin(np.pi * np.arange(n_o) / max(n_o, 1)))
    # ビブラート (遅れて深くなる)
    vib_on = np.clip((t - voice.vibrato_delay) / 0.5, 0.0, 1.0)
    f0 = f0 * 2.0 ** (voice.vibrato_cents / 1200.0 * vib_on
                      * np.sin(TWO_PI * voice.vibrato_hz * t
                               + rng.uniform(0, TWO_PI)))
    # ジッター (ゆっくりした無意識の揺れ)
    n_j = max(n // 2048, 4)
    j = rng.standard_normal(n_j)
    j = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, n_j), j)
    f0 = f0 * 2.0 ** (voice.jitter_cents / 1200.0 * j / 3.0)

    phase = TWO_PI * np.cumsum(f0) / sr

    # ── 倍音を積む ────────────────────────────────────────
    nyq = sr * 0.45
    n_harm = max(int(nyq / f_target), 3)
    n_harm = min(n_harm, 60)
    ks = np.arange(1, n_harm + 1, dtype=np.float64)
    gains = _formant_gain(ks * f_target, voice, vowel)
    # -60dB 以下の倍音は聞こえないので捨てる (速度が段違いになる)
    keep = gains > 1e-3
    y = np.zeros(n, dtype=np.float64)
    for k, g in zip(ks[keep], gains[keep]):
        y += g * np.sin(k * phase + rng.uniform(0, TWO_PI) * 0.01)

    # シンマー (振幅の微揺れ)
    n_s = max(n // 1024, 4)
    s = rng.standard_normal(n_s)
    s = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, n_s), s)
    y *= 1.0 + 0.02 * s

    # ── 包絡 ─────────────────────────────────────────────
    atk = min(int(0.055 * sr), n // 3)
    rel = min(int((0.22 if phrase_end else 0.09) * sr), n // 2)
    env = np.ones(n)
    env[:atk] = np.sin(0.5 * np.pi * np.arange(atk) / max(atk, 1)) ** 1.2
    env[n - rel:] = np.cos(0.5 * np.pi * np.arange(rel) / max(rel, 1)) ** 1.2
    y *= env

    # ── 息 ───────────────────────────────────────────────
    nz = rng.standard_normal(n).astype(np.float32)
    nz = dsp.bandpass(nz, 1400.0, 7500.0, taps=257)
    breath_env = env * (0.4 + 0.6 * np.clip(1.0 - t / max(dur, 1e-6), 0, 1))
    if phrase_end:
        # フレーズ末尾は息が抜ける
        breath_env[n - rel:] += np.linspace(0, 0.8, rel)
    y += nz * breath_env * voice.breath * 0.035 * np.abs(y).max()

    peak = np.abs(y).max() + 1e-9
    return (y / peak * (0.30 + 0.55 * vel)).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# 旋律の生成 (歌う用 — 楽器のメロディよりフレーズ構造を強く持つ)
# ──────────────────────────────────────────────────────────────

def make_vocal_line(spans, clock, scale_root: int, scale: str,
                    lo: int, hi: int, rng: np.random.Generator,
                    chorus_beats: set | None = None,
                    density: float = 0.8) -> list[dict]:
    """
    歌の旋律を返す。要素: start_beat, dur, midi, vowel, phrase_end。

    ルール (歌が歌らしく聞こえる最低条件):
      - 2 小節フレーズ + 息継ぎの繰り返し
      - フレーズは順次進行が基本。跳躍したら逆方向に畳む
      - フレーズ末尾はコードトーンに着地して伸ばす
      - サビ (chorus_beats) では音域を上げ、音価を倍にする
    """
    from .theory import scale_pitches, nearest_chord_tone
    from .arrange import chord_at

    allowed = scale_pitches(scale_root, scale, lo, hi)
    if not allowed:
        return []
    arr = np.asarray(allowed)
    chorus_beats = chorus_beats or set()

    def snap(p):
        return int(arr[np.argmin(np.abs(arr - p))])

    notes = []
    cur = allowed[len(allowed) // 2]
    beat = 0.0
    total = float(clock.total_beats)
    bpb = clock.beats_per_bar

    while beat < total - bpb:
        sp = chord_at(spans, beat)
        if not sp.section.melody or sp.section.density < 0.55 * density:
            beat = (int(beat / bpb) + 1) * bpb
            continue
        in_chorus = int(beat) in chorus_beats
        # 2 小節フレーズのリズムを選ぶ
        pats = ([[1.5, 0.5, 1.0, 1.0, 2.0, 2.0],
                 [1.0, 1.0, 2.0, 1.0, 1.0, 2.0],
                 [2.0, 1.0, 1.0, 4.0]] if in_chorus else
                [[0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 2.0, 2.0],
                 [1.0, 0.5, 0.5, 1.0, 1.0, 2.0, 2.0],
                 [0.5, 1.0, 0.5, 2.0, 1.0, 3.0],
                 [1.0, 1.0, 1.0, 1.0, 2.0, 2.0]])
        pat = pats[int(rng.integers(0, len(pats)))]
        # フレーズの開始音はコードトーン
        cur = snap(nearest_chord_tone(cur + (2 if in_chorus else 0),
                                      sp.chord, lo, hi))
        last_dir = 0
        for i, d in enumerate(pat):
            if beat >= total - 0.5:
                break
            is_last = (i == len(pat) - 1)
            sp2 = chord_at(spans, beat)
            if is_last or d >= 2.0:
                nxt = snap(nearest_chord_tone(cur, sp2.chord, lo, hi))
            else:
                step = int(rng.choice([-2, -1, -1, 1, 1, 2, 3, -3],
                                      p=[0.10, 0.24, 0.10, 0.24, 0.10,
                                         0.12, 0.05, 0.05]))
                if last_dir and abs(step) >= 3:
                    step = -np.sign(last_dir) * abs(step)   # 跳躍は畳む
                idx = int(np.clip(np.argmin(np.abs(arr - cur)) + step,
                                  0, len(arr) - 1))
                nxt = int(arr[idx])
                last_dir = step
            # 母音: フレーズ頭は開く (ア/オ)、途中は流す、末尾は閉じるか開くか
            if i == 0:
                vowel = str(rng.choice(["a", "o", "a"]))
            elif is_last:
                vowel = str(rng.choice(["a", "o", "u", "m"]))
            else:
                vowel = str(rng.choice(["a", "o", "u", "e"],
                                       p=[0.4, 0.3, 0.15, 0.15]))
            notes.append(dict(start_beat=beat, dur_beats=d * 0.94,
                              midi=nxt + (12 if in_chorus and hi - nxt > 14
                                          else 0),
                              vowel=vowel, phrase_end=is_last,
                              chorus=in_chorus))
            cur = nxt
            beat += d
        # 息継ぎ
        beat += float(rng.choice([0.5, 1.0, 1.0, 2.0]))

    return notes


def render_vocal(buf: np.ndarray, notes: list[dict], clock, voice: Voice,
                 gain: float = 0.5, seed: int = 0, pan: float = 0.0) -> None:
    """旋律をバッファへ歌い込む"""
    from .arrange import add_panned
    prev = None
    for nt in notes:
        dur = clock.dur(nt["dur_beats"])
        y = sing_note(voice, nt["midi"], dur, vowel=nt["vowel"],
                      prev_midi=prev, vel=0.85 if nt.get("chorus") else 0.72,
                      phrase_end=nt["phrase_end"], seed=seed)
        if len(y):
            add_panned(buf, y, clock.at(nt["start_beat"]), gain, pan)
        prev = nt["midi"]
