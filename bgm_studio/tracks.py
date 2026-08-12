"""
10 本の BGM トラック定義。

ジャンル選定は docs/02_genre_strategy.md の分析に対応している。
「需要が大きい × 飽和しきっていない × RPM が高い」の 3 条件で選び、
睡眠 / 集中 / 作業 / くつろぎ の 4 用途をカバーするように配分した。

各トラックは
    ループ長 LOOP_SECONDS 秒 = 24 分の「完全に継ぎ目のない」音源
として書き出し、動画側で 6 回ループして 2 時間 24 分にする。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from . import arrange as A
from . import dsp
from . import instruments as I
from . import nature as NT
from . import theory as T
from .arrange import Clock
from .dsp import SR

# ループ 1 周ぶんの長さ。動画ではこれを LOOP_REPEATS 回つなぐ。
LOOP_SECONDS = 1440          # 24 分
LOOP_REPEATS = 6             # → 2 時間 24 分
TARGET_LUFS_DEFAULT = -14.0  # YouTube のラウドネス正規化目標に一致させる


def clock_for(seconds: float, target_bpm: float, bpb: int = 4) -> Clock:
    """
    目標 BPM に最も近くなる小節数を選ぶ。
    ループ長 (秒) を固定して BPM を微調整するので、
    サンプル数の端数が絶対に出ない。
    """
    bar_sec = 60.0 / target_bpm * bpb
    bars = max(int(round(seconds / bar_sec)), 4)
    return Clock(total_seconds=seconds, bars=bars, beats_per_bar=bpb)


@dataclass
class TrackSpec:
    slug: str
    title_en: str
    genre_ja: str
    use_case: str                  # sleep / study / work / relax
    bpm: float
    key: str                       # 'Am' など表示用
    key_root: int                  # ピッチクラス (C=0)
    scale: str
    prog_key: str                  # theory.PROGRESSIONS のキー
    visual: str                    # visuals.py のシーン名
    seed: int
    a4: float = 440.0
    target_lufs: float = TARGET_LUFS_DEFAULT
    build: Callable | None = None
    seo: dict = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# 共通ヘルパ
# ──────────────────────────────────────────────────────────────

def _new_buf(clock: Clock, tail: float = 0.0) -> np.ndarray:
    """本体 + リバーブ用の尻尾ぶんを確保したバッファ"""
    return np.zeros((clock.n_samples + int(tail * clock.sr), 2), dtype=np.float32)


def _timeline(spec: TrackSpec, clock: Clock,
              rng: np.random.Generator) -> list[A.Span]:
    progs = [T.transpose(p, spec.key_root) for p in T.PROGRESSIONS[spec.prog_key]]
    sections = T.build_form(progs, clock.bars, rng)
    return A.build_timeline(sections, clock)


def _finish(buf: np.ndarray, clock: Clock, spec: TrackSpec,
            ir: np.ndarray | None, send: float,
            beds: list | None = None,          # 呼ぶと環境音を返す関数のリスト
            master=None, warp=None) -> tuple[np.ndarray, dict]:
    """
    仕上げ工程。
      1. 楽器バスにリバーブをかける (尻尾を残す)
      2. fold_tail() で尻尾をループ先頭へ折り返して継ぎ目を消す
      3. 環境音ベッドを足す (こちらはもともと完全ループ)
      4. ピッチ揺らぎ (テープ感) — ループ長ちょうどで巡回させる
      5. ジャンル別のマスタリング
      6. LUFS 正規化 + リミッタ
    """
    n = clock.n_samples

    if ir is not None and send > 0.0:
        buf = dsp.reverb(buf, ir, mix=send, tail=True)

    music = dsp.fold_tail(buf, n)
    del buf          # 500MB 級なので明示的に手放す

    # ── 環境音を「音楽に対する相対レベル」で混ぜる ──────────
    #
    # ここは一度、固定ゲインで作って失敗している。
    # 雨が音楽より +6.9dB 大きくなり、「ノイズの下で楽器が鳴っている」
    # 状態になった。環境音の音量を勘で決めてはいけない。
    #
    # 正しくは、音楽の RMS を測ってから、その何 dB 下に置くかを指定する。
    # 目安:
    #   -10 〜 -14 dB … その環境音が主役の曲 (波、雨とピアノ)
    #   -16 〜 -20 dB … 情景として聞かせたい (焚き火、カフェ)
    #   -22 〜 -26 dB … 質感として敷くだけ (レコードノイズ)
    #   -30 dB 以下   … 無音を避けるためだけの床 (部屋鳴り)
    music_rms = float(np.sqrt(np.mean(music.astype(np.float64) ** 2))) + 1e-9
    bed_report = []
    if beds:
        for item in beds:
            make_bed, rel_db = item if isinstance(item, tuple) else (item, -20.0)
            b = make_bed() if callable(make_bed) else make_bed
            b = b[:n]
            b_rms = float(np.sqrt(np.mean(b.astype(np.float64) ** 2))) + 1e-12
            g = float(music_rms * dsp.db2lin(rel_db) / b_rms)
            music[:, :] += (b * np.float32(g))
            bed_report.append(round(rel_db, 1))
            del b

    # ワウフラッターは読み出し位置を巡回させる必要があるので、
    # パディングではなく「ちょうどループ長」の状態でかける。
    if warp is not None:
        music = warp(music)

    # 以降のマスタリングは巡回的に適用する。EQ もリミッタも内部で
    # 前後を参照するので、素直にかけると両端に段差が復活してしまう。
    if master is not None:
        music = dsp.circular_process(music, master, pad_seconds=2.0)

    out, info = dsp.normalize_lufs(music, target=spec.target_lufs,
                                   ceiling_db=-1.0, circular=True)
    info["bed_levels_db"] = bed_report
    info["seam_db"] = dsp.check_loop_seam(out)
    info["seam_dbfs"] = dsp.seam_step_dbfs(out)
    info["bpm"] = round(clock.bpm, 2)
    info["bars"] = clock.bars
    return out, info


# ──────────────────────────────────────────────────────────────
# 01. Lofi Study Beats  (雨の窓辺)
# ──────────────────────────────────────────────────────────────

def build_lofi_study(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=12.0)

    A.play_pad(buf, spans, clock, bank, gain=0.10, octave=0, brightness=0.7,
               attack=1.2, release=1.8, rng=rng, n_voices=4)
    A.play_comp(buf, spans, clock, bank, inst="rhodes", style="lofi",
                gain=0.30, voicing="rootless", center=62, swing=0.15, rng=rng)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="pump",
                gain=0.32, octave=-2, rng=rng)
    A.play_lofi_drums(buf, spans, clock, bank, gain=0.30, swing=0.16, rng=rng)
    A.play_melody(buf, spans, clock, bank, inst="rhodes", gain=0.16,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=67, hi=84, density=0.35, rng=rng, rest_prob=0.45)

    ir = dsp.make_reverb_ir(2.6, rt60=2.0, damp=0.65, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.45, window=True), -21.0),
        (lambda: dsp.to_stereo(I.vinyl_crackle(n, np.random.default_rng(spec.seed + 2))), -26.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -34.0),
    ]

    def warp(x):
        # テープのピッチ揺らぎ。lofi の「アナログっぽさ」の正体
        return dsp.wow_flutter(x, depth=0.0022, rate=0.6, loop_n=n)

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-4.5)     # 高域を落として眠くする
        x = dsp.lowpass(x, 13500.0, order=2)              # lofi のこもり
        x = dsp.saturate(x, drive=1.35, mix=0.55)         # テープの温かみ
        return dsp.shelf(x, 120.0, 1.5, kind="low")

    return _finish(buf, clock, spec, ir, 0.26, beds, master, warp=warp)


# ──────────────────────────────────────────────────────────────
# 02. Deep Sleep Ambient  (深い睡眠)
# ──────────────────────────────────────────────────────────────

def build_deep_sleep(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=32.0)

    # 主役は分厚いパッド。アタック 6 秒でゆっくり立ち上げる
    A.play_pad(buf, spans, clock, bank, gain=0.30, octave=0, brightness=0.78,
               attack=6.0, release=7.0, rng=rng, n_voices=5, low=40, high=82)
    A.play_drone(buf, T.note("A", 2) + spec.key_root, clock, bank,
                 gain=0.16, partials=9)
    A.play_sparse_bells(buf, spans, clock, bank, inst="bowl", gain=0.10,
                        every_bars=6.0, center=60, rng=rng)
    A.play_arp(buf, spans, clock, bank, inst="celesta", gain=0.07, rate=2.0,
               octaves=2, center=78, direction="up", rng=rng)

    ir = dsp.make_reverb_ir(5.0, rt60=6.5, damp=0.75, predelay=0.05,
                            width=0.55, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.35, window=True), -18.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-2.5)
        x = dsp.lowpass(x, 14500.0, order=2)
        x = dsp.highpass(x, 32.0, order=2)
        return dsp.saturate(x, drive=1.1, mix=0.3)

    return _finish(buf, clock, spec, ir, 0.50, beds, master)


# ──────────────────────────────────────────────────────────────
# 03. Piano & Rain  (雨とピアノ)
# ──────────────────────────────────────────────────────────────

def build_piano_rain(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=16.0)

    A.play_pad(buf, spans, clock, bank, gain=0.07, brightness=0.6,
               attack=3.0, release=3.5, rng=rng, n_voices=4)
    A.play_comp(buf, spans, clock, bank, inst="piano", style="ballad",
                gain=0.30, voicing="close", center=54, rng=rng, spread_ms=45.0)
    A.play_arp(buf, spans, clock, bank, inst="piano", gain=0.13, rate=1.0,
               octaves=1, center=69, direction="updown", rng=rng, pan=0.1)
    A.play_melody(buf, spans, clock, bank, inst="piano", gain=0.26,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=64, hi=88, density=0.4, rng=rng, rest_prob=0.42)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                gain=0.16, octave=-2, rng=rng)

    ir = dsp.make_reverb_ir(4.0, rt60=3.6, damp=0.55, predelay=0.03, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.7, window=True), -13.0),
        (lambda: NT.thunder(n, seed=spec.seed + 2, count=3), -20.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-3.0)
        x = dsp.lowpass(x, 15000.0, order=2)
        return dsp.saturate(x, drive=1.15, mix=0.28)

    return _finish(buf, clock, spec, ir, 0.36, beds, master)


# ──────────────────────────────────────────────────────────────
# 04. Cozy Coffee Shop Jazz  (カフェジャズ)
# ──────────────────────────────────────────────────────────────

def build_cafe_jazz(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=12.0)

    A.play_comp(buf, spans, clock, bank, inst="piano", style="jazz",
                gain=0.26, voicing="rootless", center=62, swing=0.30,
                rng=rng, spread_ms=28.0, pan=-0.12)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="walk",
                gain=0.30, octave=-2, rng=rng,
                scale_root=spec.key_root, scale=spec.scale)
    A.play_jazz_brushes(buf, spans, clock, bank, gain=0.22, rng=rng)
    A.play_melody(buf, spans, clock, bank, inst="piano", gain=0.22,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=64, hi=86, density=0.5, rng=rng, rest_prob=0.34, pan=0.15)

    ir = dsp.make_reverb_ir(2.2, rt60=1.5, damp=0.5, predelay=0.015, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.cafe_ambience(n, seed=spec.seed + 1), -20.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-2.0)
        x = dsp.peak_eq(x, 250.0, 1.2, q=1.0)     # 胴鳴りの温かさ
        return dsp.saturate(x, drive=1.2, mix=0.3)

    return _finish(buf, clock, spec, ir, 0.24, beds, master)


# ──────────────────────────────────────────────────────────────
# 05. Bossa Nova Cafe  (ボサノヴァ)
# ──────────────────────────────────────────────────────────────

def build_bossa(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=12.0)

    A.play_comp(buf, spans, clock, bank, inst="nylon", style="bossa",
                gain=0.30, voicing="close", center=59, rng=rng,
                spread_ms=22.0, pan=-0.15)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="bossa",
                gain=0.28, octave=-2, rng=rng)
    A.play_bossa_perc(buf, spans, clock, bank, gain=0.18, rng=rng)
    A.play_melody(buf, spans, clock, bank, inst="rhodes", gain=0.17,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=64, hi=84, density=0.42, rng=rng, rest_prob=0.4, pan=0.18)

    ir = dsp.make_reverb_ir(2.0, rt60=1.3, damp=0.45, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.cafe_ambience(n, seed=spec.seed + 1), -24.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -34.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=900.0, gain_db=-1.5)
        return dsp.saturate(x, drive=1.15, mix=0.25)

    return _finish(buf, clock, spec, ir, 0.20, beds, master)


# ──────────────────────────────────────────────────────────────
# 06. Healing Meditation 432Hz  (瞑想 / ヒーリング)
# ──────────────────────────────────────────────────────────────

def build_healing_432(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=38.0)

    A.play_pad(buf, spans, clock, bank, gain=0.24, brightness=0.5,
               attack=7.0, release=8.0, rng=rng, n_voices=5, low=43, high=79)
    A.play_drone(buf, T.note("D", 2) + spec.key_root, clock, bank,
                 gain=0.14, partials=8)
    A.play_sparse_bells(buf, spans, clock, bank, inst="bowl", gain=0.20,
                        every_bars=4.0, center=57, rng=rng)
    A.play_arp(buf, spans, clock, bank, inst="harp", gain=0.09, rate=2.0,
               octaves=2, center=72, direction="up", rng=rng, pan=0.0)

    ir = dsp.make_reverb_ir(6.0, rt60=8.0, damp=0.7, predelay=0.06,
                            width=0.55, seed=spec.seed)
    n = clock.n_samples
    beds = [(lambda: NT.room_tone(n, seed=spec.seed + 1), -32.0)]

    def master(x):
        x = dsp.tilt_eq(x, pivot=650.0, gain_db=-5.5)
        x = dsp.lowpass(x, 9500.0, order=2)
        x = dsp.highpass(x, 34.0, order=2)
        return dsp.saturate(x, drive=1.08, mix=0.25)

    return _finish(buf, clock, spec, ir, 0.46, beds, master)


# ──────────────────────────────────────────────────────────────
# 07. Fireplace Winter Jazz  (暖炉と冬のジャズ)
# ──────────────────────────────────────────────────────────────

def build_winter_fire(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=14.0)

    A.play_comp(buf, spans, clock, bank, inst="piano", style="jazz",
                gain=0.24, voicing="rootless", center=60, swing=0.28,
                rng=rng, spread_ms=30.0, pan=-0.10)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="walk",
                gain=0.26, octave=-2, rng=rng,
                scale_root=spec.key_root, scale=spec.scale)
    A.play_jazz_brushes(buf, spans, clock, bank, gain=0.16, rng=rng, ride_prob=0.35)
    A.play_melody(buf, spans, clock, bank, inst="celesta", gain=0.16,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=72, hi=93, density=0.34, rng=rng, rest_prob=0.5, pan=0.2)
    A.play_pad(buf, spans, clock, bank, gain=0.07, brightness=0.6,
               attack=2.5, release=3.0, rng=rng, n_voices=4)

    ir = dsp.make_reverb_ir(2.8, rt60=2.2, damp=0.6, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.fireplace(n, seed=spec.seed + 1), -16.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-3.5)
        x = dsp.shelf(x, 150.0, 2.0, kind="low")
        x = dsp.lowpass(x, 14000.0, order=2)
        return dsp.saturate(x, drive=1.25, mix=0.35)

    return _finish(buf, clock, spec, ir, 0.28, beds, master)


# ──────────────────────────────────────────────────────────────
# 08. Ocean Waves Ambient  (夜の海)
# ──────────────────────────────────────────────────────────────

def build_ocean_ambient(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=24.0)

    A.play_pad(buf, spans, clock, bank, gain=0.24, brightness=0.65,
               attack=5.0, release=6.0, rng=rng, n_voices=5, low=42, high=81)
    A.play_arp(buf, spans, clock, bank, inst="celesta", gain=0.07, rate=3.0,
               octaves=2, center=76, direction="updown", rng=rng)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                gain=0.14, octave=-2, rng=rng)

    ir = dsp.make_reverb_ir(5.0, rt60=5.5, damp=0.68, width=0.55, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.ocean(n, seed=spec.seed + 1, period=8.5), -11.0),
        (lambda: NT.wind(n, seed=spec.seed + 2), -26.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=650.0, gain_db=-5.0)
        x = dsp.lowpass(x, 10500.0, order=2)
        x = dsp.highpass(x, 34.0, order=2)
        return dsp.saturate(x, drive=1.1, mix=0.25)

    return _finish(buf, clock, spec, ir, 0.42, beds, master)


# ──────────────────────────────────────────────────────────────
# 09. Fantasy Tavern  (中世ファンタジー / 酒場)
# ──────────────────────────────────────────────────────────────

def build_fantasy_tavern(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=15.0)

    # 中世モードらしく 3 度を薄くして 5 度と 4 度を強調する
    A.play_pad(buf, spans, clock, bank, gain=0.10, brightness=0.55,
               attack=3.0, release=3.5, rng=rng, n_voices=4, low=40, high=72)
    A.play_arp(buf, spans, clock, bank, inst="harp", gain=0.20, rate=0.5,
               octaves=2, center=64, direction="updown", rng=rng, pan=-0.15)
    A.play_melody(buf, spans, clock, bank, inst="nylon", gain=0.20,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=60, hi=81, density=0.42, rng=rng, rest_prob=0.42, pan=0.2)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="root",
                gain=0.22, octave=-2, rng=rng)

    ir = dsp.make_reverb_ir(3.4, rt60=3.0, damp=0.5, predelay=0.025, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.fireplace(n, seed=spec.seed + 1), -17.0),
        (lambda: NT.cafe_ambience(n, seed=spec.seed + 2), -26.0),   # 酒場のざわめき
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=750.0, gain_db=-3.5)
        x = dsp.lowpass(x, 13000.0, order=2)
        return dsp.saturate(x, drive=1.2, mix=0.3)

    return _finish(buf, clock, spec, ir, 0.32, beds, master)


# ──────────────────────────────────────────────────────────────
# 10. Deep Focus Flow  (集中 / ディープワーク)
# ──────────────────────────────────────────────────────────────

def build_deep_focus(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=18.0)

    # 集中用はメロディを入れない。旋律があると脳が追ってしまう。
    A.play_pad(buf, spans, clock, bank, gain=0.20, brightness=0.6,
               attack=4.5, release=5.0, rng=rng, n_voices=4, low=45, high=79)
    A.play_drone(buf, T.note("A", 2) + spec.key_root, clock, bank,
                 gain=0.10, partials=7)
    A.play_arp(buf, spans, clock, bank, inst="marimba", gain=0.10, rate=1.0,
               octaves=2, center=72, direction="up", rng=rng)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                gain=0.16, octave=-2, rng=rng)

    ir = dsp.make_reverb_ir(3.6, rt60=3.2, damp=0.62, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.brown_noise_bed(n, seed=spec.seed + 1, tilt_hz=420.0), -22.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -34.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-4.0)
        x = dsp.lowpass(x, 11000.0, order=2)
        x = dsp.highpass(x, 30.0, order=2)
        return dsp.saturate(x, drive=1.1, mix=0.22)

    return _finish(buf, clock, spec, ir, 0.34, beds, master)


# ──────────────────────────────────────────────────────────────
# 12. Emotional Anime Piano  (アニソン風・情感のあるピアノ)
# ──────────────────────────────────────────────────────────────

def build_anime_piano(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    「アニソンのような、心に響く」インスト。

    他の曲と設計思想がはっきり違う。既存 10 本は「意識に上らないこと」が
    目的だったが、この曲は逆で、聴いた人に何かを思い出させるのが目的。
    だから BGM の定石をいくつか意図的に破っている:

      - メロディをはっきり立てる (density を上げ、休符を減らす)
      - コード進行を動かす (王道進行・カノン進行)
      - 環境音をほぼ入れない。情感の邪魔になる

    ただし作業用として何時間も流せる範囲は守る。ドラムは入れない。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=4)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=20.0)

    # ストリングス代わりの厚いパッド。主役ではないが情感の土台になる
    A.play_pad(buf, spans, clock, bank, gain=0.13, brightness=0.72,
               attack=2.2, release=4.0, rng=rng, n_voices=5, low=48, high=84)
    # ピアノの伴奏。close voicing でポップスらしく
    A.play_comp(buf, spans, clock, bank, inst="piano", style="ballad",
                gain=0.26, voicing="close", center=57, rng=rng, spread_ms=32.0)
    # 主旋律。ここがこの曲の全て。休符を減らして歌わせる
    A.play_melody(buf, spans, clock, bank, inst="piano", gain=0.34,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=67, hi=91, density=0.62, rng=rng, rest_prob=0.22)
    # 高音のきらめき。サビの解放感を補強する
    A.play_arp(buf, spans, clock, bank, inst="celesta", gain=0.08, rate=0.5,
               octaves=2, center=81, direction="updown", rng=rng, pan=0.15)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                gain=0.17, octave=-2, rng=rng)

    ir = dsp.make_reverb_ir(3.8, rt60=3.4, damp=0.5, predelay=0.025,
                            seed=spec.seed)
    n = clock.n_samples
    # 環境音は「部屋の気配」だけ。雨も波も入れない
    beds = [(lambda: NT.room_tone(n, seed=spec.seed + 1), -34.0)]

    def master(x):
        # 情感系はこもらせない。高域を残して抜けを作る
        x = dsp.tilt_eq(x, pivot=900.0, gain_db=-1.5)
        x = dsp.shelf(x, 140.0, 1.2, kind="low")
        x = dsp.lowpass(x, 16000.0, order=2)
        return dsp.saturate(x, drive=1.12, mix=0.22)

    return _finish(buf, clock, spec, ir, 0.30, beds, master)


# ──────────────────────────────────────────────────────────────
# 13. Fresh Morning Acoustic  (爽やかな朝のアコースティック)
# ──────────────────────────────────────────────────────────────

def build_fresh_morning(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    爽やか系。

    「爽やかさ」は明るいコードを置けば出るものではなく、
      - 低域を膨らませない (もたつくと途端に重くなる)
      - 高域に空気を残す
      - 音数を詰めない
    の 3 つで決まる。マスタリングもその方向に振っている。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=4)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=12.0)

    # ナイロン弦のギターが主役。爽やかさはこの音色に依るところが大きい
    A.play_comp(buf, spans, clock, bank, inst="nylon", style="bossa",
                gain=0.24, voicing="close", center=59, rng=rng, spread_ms=40.0)
    # マリンバの軽いメロディ。木の音は朝によく合う
    A.play_melody(buf, spans, clock, bank, inst="marimba", gain=0.22,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=69, hi=91, density=0.45, rng=rng, rest_prob=0.40)
    # 薄いパッドで空気感。厚くすると途端に眠くなるので控えめに
    A.play_pad(buf, spans, clock, bank, gain=0.07, brightness=0.85,
               attack=2.0, release=3.0, rng=rng, n_voices=4, low=55, high=86)
    A.play_arp(buf, spans, clock, bank, inst="celesta", gain=0.06, rate=1.0,
               octaves=2, center=84, direction="up", rng=rng, pan=-0.15)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="bossa",
                gain=0.18, octave=-1, rng=rng)
    # シェイカー中心の軽い打楽器。歩くようなテンポ感を作る
    A.play_bossa_perc(buf, spans, clock, bank, gain=0.12, rng=rng)

    ir = dsp.make_reverb_ir(1.9, rt60=1.4, damp=0.4, predelay=0.012,
                            seed=spec.seed)
    n = clock.n_samples
    # 朝の外の気配。ごく薄く風だけ
    beds = [
        (lambda: NT.wind(n, seed=spec.seed + 1), -28.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -34.0),
    ]

    def master(x):
        # 低域を持ち上げない。むしろ削って軽くする
        x = dsp.highpass(x, 55.0, order=2)
        x = dsp.tilt_eq(x, pivot=1100.0, gain_db=+1.5)   # 高域寄りに傾ける
        x = dsp.lowpass(x, 17000.0, order=2)
        return dsp.saturate(x, drive=1.1, mix=0.18)

    return _finish(buf, clock, spec, ir, 0.22, beds, master)


# ──────────────────────────────────────────────────────────────
# 14. Japanese Lofi  (和風ローファイ)
# ──────────────────────────────────────────────────────────────

def build_japanese_lofi(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    琴 × lofi ビート。

    リサーチで「まだ飽和していない成長ジャンル」と出た組み合わせ。
    琴の旋律は kumoi 音階に固定する。ここが平均律の 7 音階だと
    ただの lofi に琴の音色が乗っただけになってしまい、和にならない。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=16.0)

    A.play_pad(buf, spans, clock, bank, gain=0.10, brightness=0.55,
               attack=4.0, release=5.0, rng=rng, n_voices=4, low=45, high=76)
    A.play_arp(buf, spans, clock, bank, inst="koto", gain=0.15, rate=1.0,
               octaves=1, center=64, direction="updown", rng=rng, pan=-0.12)
    # 旋律の音階は A を根にした平調子。進行 (wafu) は A センターで
    # 書いてあるので、key_root ではなく A(=9) からの平調子に固定する。
    A.play_melody(buf, spans, clock, bank, inst="koto", gain=0.30,
                  scale_root=(spec.key_root + 9) % 12, scale=spec.scale,
                  lo=64, hi=88, density=0.45, rng=rng, rest_prob=0.40)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="pump",
                gain=0.20, octave=-2, rng=rng)
    A.play_lofi_drums(buf, spans, clock, bank, gain=0.24, swing=0.14,
                      rng=rng, use_rim=True)

    ir = dsp.make_reverb_ir(2.8, rt60=2.2, damp=0.6, predelay=0.02,
                            seed=spec.seed)
    n = clock.n_samples
    warp = lambda x: dsp.wow_flutter(x, depth=0.0018, rate=0.6,
                                     loop_n=n, seed=spec.seed)
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.35, window=True), -22.0),
        (lambda: dsp.to_stereo(I.vinyl_crackle(n, np.random.default_rng(spec.seed + 2))), -27.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -34.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-4.0)
        x = dsp.lowpass(x, 13000.0, order=2)
        x = dsp.saturate(x, drive=1.3, mix=0.45)
        return dsp.shelf(x, 120.0, 1.2, kind="low")

    return _finish(buf, clock, spec, ir, 0.26, beds, master, warp=warp)


# ──────────────────────────────────────────────────────────────
# 15. Rain & Thunder Night  (雷雨の夜 — 環境音が主役)
# ──────────────────────────────────────────────────────────────

def build_rain_thunder(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    雨と遠雷。音楽はほぼ入れない。

    リサーチの結論として、視聴回数の天井が最も高いのがこの
    「純環境音の睡眠動画」(10M+ 再生が常態)。
    音楽は 1 音を数十秒伸ばすパッドだけを、雨のはるか下に敷く。
    完全な無音楽より「何かがいる」気配があるほうが不気味さが消える。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=30.0)

    # 気配としてのパッドとドローンのみ。旋律なし
    A.play_pad(buf, spans, clock, bank, gain=0.22, brightness=0.45,
               attack=8.0, release=9.0, rng=rng, n_voices=4, low=40, high=64)
    A.play_drone(buf, T.note("A", 1) + spec.key_root, clock, bank,
                 gain=0.12, partials=6)

    ir = dsp.make_reverb_ir(5.0, rt60=6.0, damp=0.8, predelay=0.05,
                            seed=spec.seed)
    n = clock.n_samples
    # 雨が主役なので相対レベルは正の値 (音楽より上に置く)。
    # 検索の定番も「rain on window」なので、屋外の雨ではなく
    # 窓越し (高域を大きく削った雨) を使う。素の雨はスペクトルが
    # 平坦すぎて、-14 LUFS まで上げると夜の耳には刺さる。
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.85, window=True), +5.0),
        (lambda: NT.thunder(n, seed=spec.seed + 2, count=7), -4.0),
        (lambda: NT.wind(n, seed=spec.seed + 3), -14.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 4), -30.0),
    ]

    def master(x):
        # 雨の高域は耳に刺さりやすい。夜向けに大きく丸める
        x = dsp.tilt_eq(x, pivot=450.0, gain_db=-7.5)
        x = dsp.lowpass(x, 8000.0, order=2)
        x = dsp.highpass(x, 36.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.40, beds, master)


# ──────────────────────────────────────────────────────────────
# 16. Autumn Café Jazz  (秋のカフェジャズ — 9〜11月の季節枠)
# ──────────────────────────────────────────────────────────────

def build_autumn_jazz(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    秋のジャズ。04 のカフェジャズより一段暗く、遅く、温かく。
    「autumn jazz」「cozy fall」は 9 月に検索が跳ねる季節ジャンルで、
    8 月のいま撮り溜めておくのが最も効率がいい。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=14.0)

    A.play_comp(buf, spans, clock, bank, inst="piano", style="jazz",
                gain=0.24, voicing="rootless", center=60, swing=0.55, rng=rng)
    A.play_melody(buf, spans, clock, bank, inst="rhodes", gain=0.20,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=62, hi=84, density=0.42, rng=rng, rest_prob=0.45)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="walk",
                gain=0.22, octave=-1, rng=rng,
                scale_root=spec.key_root, scale=spec.scale)
    A.play_jazz_brushes(buf, spans, clock, bank, gain=0.16, rng=rng,
                        ride_prob=0.4)

    ir = dsp.make_reverb_ir(2.4, rt60=1.8, damp=0.55, predelay=0.018,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.wind(n, seed=spec.seed + 1), -20.0),
        (lambda: NT.cafe_ambience(n, seed=spec.seed + 2), -22.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -33.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-3.5)
        x = dsp.peak_eq(x, 240.0, 1.5, q=1.0)      # 木の温かさ
        x = dsp.lowpass(x, 13500.0, order=2)
        return dsp.saturate(x, drive=1.2, mix=0.3)

    return _finish(buf, clock, spec, ir, 0.26, beds, master)


# ──────────────────────────────────────────────────────────────
# 17. Christmas Jazz  (クリスマスジャズ — 11〜12月の季節枠)
# ──────────────────────────────────────────────────────────────

def build_christmas_jazz(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    クリスマスのジャズ。12 月は 1 年で最も BGM 需要が跳ねる月で、
    「christmas jazz」は毎年 10M+ 再生の動画が量産される。
    定番曲の旋律は使わない (Content ID で収益が差し押さえられる)。
    maj6 と dom7b9 の進行 + スレイベル + セレスタで
    「あの頃のクリスマス」の匂いだけを原曲なしで作る。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=14.0)

    A.play_comp(buf, spans, clock, bank, inst="piano", style="jazz",
                gain=0.24, voicing="rootless", center=62, swing=0.55, rng=rng)
    A.play_melody(buf, spans, clock, bank, inst="celesta", gain=0.18,
                  scale_root=spec.key_root, scale=spec.scale,
                  lo=72, hi=93, density=0.40, rng=rng, rest_prob=0.42)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="walk",
                gain=0.22, octave=-1, rng=rng,
                scale_root=spec.key_root, scale=spec.scale)
    A.play_jazz_brushes(buf, spans, clock, bank, gain=0.15, rng=rng,
                        ride_prob=0.35)
    A.play_sleigh(buf, spans, clock, bank, gain=0.10, rng=rng)

    ir = dsp.make_reverb_ir(2.6, rt60=2.0, damp=0.5, predelay=0.02,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.fireplace(n, seed=spec.seed + 1), -18.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -33.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-2.5)
        x = dsp.peak_eq(x, 250.0, 1.2, q=1.0)
        x = dsp.lowpass(x, 14500.0, order=2)
        return dsp.saturate(x, drive=1.15, mix=0.28)

    return _finish(buf, clock, spec, ir, 0.28, beds, master)


# ──────────────────────────────────────────────────────────────
# 18. Starship Sleeping Quarters  (宇宙船の寝室 — 睡眠用ハム音)
# ──────────────────────────────────────────────────────────────

def build_spaceship(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    宇宙船のエンジン音。実体は「非常に低いドローン + 整形したノイズ床」で、
    このジャンルの定番動画も中身はほぼ同じ。合成との相性が全ジャンルで最も良い。
    覚醒させる成分 (旋律・急な変化・高域) を全部抜くのが正解。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=24.0)

    # エンジンの唸り: 2 本の低いドローンをわずかにデチューンして
    # ゆっくりしたうなり (ビート) を作る
    A.play_drone(buf, T.note("A", 1) + spec.key_root, clock, bank,
                 gain=0.30, partials=7)
    A.play_drone(buf, T.note("E", 2) + spec.key_root, clock, bank,
                 gain=0.14, partials=5)
    # 空調のような薄いパッド
    A.play_pad(buf, spans, clock, bank, gain=0.14, brightness=0.4,
               attack=9.0, release=10.0, rng=rng, n_voices=3, low=40, high=59)

    ir = dsp.make_reverb_ir(4.0, rt60=4.5, damp=0.85, predelay=0.04,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.brown_noise_bed(n, seed=spec.seed + 1, tilt_hz=350.0), +2.0),
        (lambda: NT.wind(n, seed=spec.seed + 2), -16.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -26.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=400.0, gain_db=-6.0)
        x = dsp.lowpass(x, 6500.0, order=2)
        x = dsp.highpass(x, 34.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.30, beds, master)


# ──────────────────────────────────────────────────────────────
# 19. 528Hz Love Frequency  (528Hz — 実音もちゃんと 528Hz)
# ──────────────────────────────────────────────────────────────

def build_528(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    528Hz 系。A=444Hz に調律すると C5 がちょうど 528.0Hz になる。
    この層の視聴者はスペクトラムアプリで実際に確かめるので、
    表記だけでなく実音を合わせることが信頼に直結する。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=36.0)

    A.play_pad(buf, spans, clock, bank, gain=0.24, brightness=0.6,
               attack=7.0, release=8.0, rng=rng, n_voices=5, low=48, high=84)
    # C5 = 528Hz のドローンを中心に据える
    A.play_drone(buf, T.note("C", 5), clock, bank, gain=0.10, partials=4)
    A.play_drone(buf, T.note("C", 3), clock, bank, gain=0.14, partials=7)
    A.play_sparse_bells(buf, spans, clock, bank, inst="bowl", gain=0.16,
                        every_bars=5.0, center=60, rng=rng)

    ir = dsp.make_reverb_ir(6.0, rt60=7.5, damp=0.7, predelay=0.05,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [(lambda: NT.room_tone(n, seed=spec.seed + 1), -32.0)]

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-3.0)
        x = dsp.lowpass(x, 13000.0, order=2)
        x = dsp.highpass(x, 40.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.42, beds, master)


# ──────────────────────────────────────────────────────────────
# 20. 40Hz Focus  (ガンマ波リズムの集中用ドローン)
# ──────────────────────────────────────────────────────────────

def build_focus_40hz(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    40Hz の振幅パルスを敷いた集中用。
    バイノーラル (L/R別周波数) はスピーカーで無効になる上に
    モノ互換検査も通らないので、モノラルでも効く振幅変調にする。
    40Hz はループ長 1440 秒に対して整数周期 (57600 回) なので継ぎ目も出ない。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=20.0)

    A.play_pad(buf, spans, clock, bank, gain=0.22, brightness=0.55,
               attack=5.0, release=6.0, rng=rng, n_voices=4, low=45, high=76)
    A.play_drone(buf, T.note("A", 2) + spec.key_root, clock, bank,
                 gain=0.16, partials=8)
    A.play_arp(buf, spans, clock, bank, inst="marimba", gain=0.07, rate=1.0,
               octaves=1, center=69, direction="up", rng=rng)

    ir = dsp.make_reverb_ir(3.0, rt60=2.8, damp=0.6, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.brown_noise_bed(n, seed=spec.seed + 1, tilt_hz=420.0), -18.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -32.0),
    ]

    def master(x):
        # 40Hz の振幅パルス (深さ 25%)。深すぎると耳障りになる
        t = np.arange(x.shape[0], dtype=np.float64) / dsp.SR
        pulse = (1.0 - 0.25 * 0.5 * (1.0 + np.sin(2 * np.pi * 40.0 * t))
                 ).astype(np.float32)
        x = x * pulse[:, None]
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-4.0)
        x = dsp.lowpass(x, 11000.0, order=2)
        x = dsp.highpass(x, 30.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.30, beds, master)


# ──────────────────────────────────────────────────────────────
# 21. Halloween Ambience  (ハロウィン — 9〜10月の季節枠)
# ──────────────────────────────────────────────────────────────

def build_halloween(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    ハロウィンの夜。不穏だが「怖すぎない」線を守る。
    (作業/パーティ用 BGM なので、ホラー効果音で驚かせてはいけない)
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=18.0)

    A.play_pad(buf, spans, clock, bank, gain=0.16, brightness=0.45,
               attack=5.0, release=6.0, rng=rng, n_voices=4, low=41, high=67)
    # オルゴールが半音ずれたような celesta。ハロウィンの音はほぼこれ
    A.play_melody(buf, spans, clock, bank, inst="celesta", gain=0.20,
                  scale_root=(spec.key_root + 9) % 12, scale="harmonic_minor",
                  lo=69, hi=88, density=0.35, rng=rng, rest_prob=0.5)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                gain=0.16, octave=-2, rng=rng)
    A.play_sparse_bells(buf, spans, clock, bank, inst="bowl", gain=0.10,
                        every_bars=9.0, center=48, rng=rng)   # 遠い鐘

    ir = dsp.make_reverb_ir(4.5, rt60=5.0, damp=0.55, predelay=0.04,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.wind(n, seed=spec.seed + 1), -13.0),
        (lambda: NT.night_ambience(n, seed=spec.seed + 2), -22.0),
        (lambda: NT.thunder(n, seed=spec.seed + 3, count=2), -18.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 4), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=650.0, gain_db=-4.0)
        x = dsp.lowpass(x, 12000.0, order=2)
        return dsp.saturate(x, drive=1.1, mix=0.2)

    return _finish(buf, clock, spec, ir, 0.34, beds, master)


# ──────────────────────────────────────────────────────────────
# 22. Snowstorm & Fireplace  (吹雪と暖炉 — 12〜2月の季節枠)
# ──────────────────────────────────────────────────────────────

def build_snowstorm(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    外は吹雪、中は暖炉。「守られている感じ」がこのジャンルの快感の正体。
    風は 2 系統 (遠くの唸り + 窓に当たる近い風) 重ねると吹雪になる。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=26.0)

    A.play_pad(buf, spans, clock, bank, gain=0.18, brightness=0.5,
               attack=7.0, release=8.0, rng=rng, n_voices=4, low=43, high=69)
    # 進行は A センターで書いてあるので、ドローンも A + key_root に合わせる
    A.play_drone(buf, T.note("A", 2) + spec.key_root, clock, bank,
                 gain=0.12, partials=6)

    ir = dsp.make_reverb_ir(4.5, rt60=5.0, damp=0.75, predelay=0.04,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.wind(n, seed=spec.seed + 1), +2.0),
        (lambda: NT.wind(n, seed=spec.seed + 11), -6.0),
        (lambda: NT.fireplace(n, seed=spec.seed + 2), -8.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -30.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=500.0, gain_db=-5.5)
        x = dsp.lowpass(x, 8500.0, order=2)
        x = dsp.highpass(x, 34.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.34, beds, master)


# ──────────────────────────────────────────────────────────────
# 23. Forest Night Camp  (夜の森の野営 — TTRPG/睡眠クロスオーバー)
# ──────────────────────────────────────────────────────────────

def build_forest_camp(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    夜の森の焚き火。TTRPG (D&D) のセッション用と睡眠用の両方に刺さる。
    ハープは「たまにしか弾かれない」ことが大事。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=20.0)

    A.play_pad(buf, spans, clock, bank, gain=0.12, brightness=0.5,
               attack=6.0, release=7.0, rng=rng, n_voices=4, low=45, high=72)
    A.play_arp(buf, spans, clock, bank, inst="harp", gain=0.08, rate=2.0,
               octaves=2, center=69, direction="up", rng=rng)
    A.play_sparse_bells(buf, spans, clock, bank, inst="harp", gain=0.09,
                        every_bars=7.0, center=64, rng=rng)

    ir = dsp.make_reverb_ir(3.5, rt60=3.5, damp=0.6, predelay=0.03,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.night_ambience(n, seed=spec.seed + 1), -10.0),
        (lambda: NT.fireplace(n, seed=spec.seed + 2), -12.0),
        (lambda: NT.wind(n, seed=spec.seed + 3), -20.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 4), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=650.0, gain_db=-4.5)
        x = dsp.lowpass(x, 11000.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.32, beds, master)


# ──────────────────────────────────────────────────────────────
# 24. Deep Space Drone  (ダークアンビエント / 星雲)
# ──────────────────────────────────────────────────────────────

def build_dark_ambient(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    ダークアンビエント。巨大な空間の低いドローン。
    ただし「こもり」検査に落ちない程度の高域の空気
    (ボウルの倍音) を必ず残す。02 で学んだ教訓。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=40.0)

    A.play_pad(buf, spans, clock, bank, gain=0.24, brightness=0.62,
               attack=10.0, release=12.0, rng=rng, n_voices=5, low=38, high=78)
    A.play_drone(buf, T.note("A", 1) + spec.key_root, clock, bank,
                 gain=0.20, partials=6)
    A.play_sparse_bells(buf, spans, clock, bank, inst="bowl", gain=0.13,
                        every_bars=8.0, center=64, rng=rng)
    A.play_arp(buf, spans, clock, bank, inst="celesta", gain=0.05, rate=3.0,
               octaves=2, center=81, direction="up", rng=rng)

    ir = dsp.make_reverb_ir(8.0, rt60=10.0, damp=0.6, predelay=0.08,
                            width=0.55, seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.wind(n, seed=spec.seed + 1), -16.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 2), -30.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=800.0, gain_db=-3.5)
        x = dsp.lowpass(x, 12000.0, order=2)
        x = dsp.highpass(x, 30.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.46, beds, master)


# ──────────────────────────────────────────────────────────────
# 25. Cyberpunk Rain  (サイバーパンクの雨の夜)
# ──────────────────────────────────────────────────────────────

def build_cyberpunk(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    ネオンの雨。シンセのアルペジオ + 短調のヴァンプ + 雨。
    ゲーマー/作業用の需要。動かないコード進行が「未来の倦怠感」を作る。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=14.0)

    A.play_pad(buf, spans, clock, bank, gain=0.16, brightness=0.7,
               attack=3.0, release=4.5, rng=rng, n_voices=5, low=45, high=79)
    A.play_arp(buf, spans, clock, bank, inst="synth", gain=0.15, rate=0.5,
               octaves=2, center=64, direction="up", rng=rng, pan=0.1)
    A.play_melody(buf, spans, clock, bank, inst="synth", gain=0.16,
                  scale_root=(spec.key_root + 9) % 12, scale="minor",
                  lo=69, hi=88, density=0.35, rng=rng, rest_prob=0.5)
    A.play_bass(buf, spans, clock, bank, inst="subbass", style="pump",
                gain=0.22, octave=-2, rng=rng)

    ir = dsp.make_reverb_ir(3.2, rt60=2.8, damp=0.5, predelay=0.03,
                            seed=spec.seed)
    n = clock.n_samples
    warp = lambda x: dsp.wow_flutter(x, depth=0.0012, rate=0.5,
                                     loop_n=n, seed=spec.seed)
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.55, window=False), -15.0),
        (lambda: NT.thunder(n, seed=spec.seed + 2, count=2), -22.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-3.0)
        x = dsp.lowpass(x, 14000.0, order=2)
        return dsp.saturate(x, drive=1.25, mix=0.35)

    return _finish(buf, clock, spec, ir, 0.28, beds, master, warp=warp)


# ──────────────────────────────────────────────────────────────
# 26. Dark Academia Library  (古い図書室 — 勉強用)
# ──────────────────────────────────────────────────────────────

def build_academia(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    古い図書室。物憂げなピアノ + 柱時計 + 暖炉 + 窓の外の雨。
    BPM を 60 にすると柱時計 (毎拍のチック) が正確に 1 秒刻みになる。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=14.0)

    A.play_comp(buf, spans, clock, bank, inst="piano", style="ballad",
                gain=0.24, voicing="close", center=55, rng=rng, spread_ms=40.0)
    A.play_melody(buf, spans, clock, bank, inst="piano", gain=0.24,
                  scale_root=(spec.key_root + 9) % 12, scale="minor",
                  lo=62, hi=84, density=0.42, rng=rng, rest_prob=0.45)
    A.play_pad(buf, spans, clock, bank, gain=0.08, brightness=0.5,
               attack=4.0, release=5.0, rng=rng, n_voices=4, low=48, high=74)
    A.play_bass(buf, spans, clock, bank, inst="upright", style="root",
                gain=0.14, octave=-1, rng=rng)

    # 柱時計。毎拍 (=1 秒) の小さなチック。60 拍ごとにわずかに強く
    for b in range(int(clock.total_beats)):
        g = 0.050 if b % 60 else 0.075
        A.add_panned(buf, bank.hit("rim"), clock.at(float(b)), g, -0.3)

    ir = dsp.make_reverb_ir(2.6, rt60=2.2, damp=0.5, predelay=0.02,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.fireplace(n, seed=spec.seed + 1), -17.0),
        (lambda: NT.rain(n, seed=spec.seed + 2, intensity=0.45, window=True), -20.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -32.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-3.5)
        x = dsp.peak_eq(x, 250.0, 1.2, q=1.0)
        x = dsp.lowpass(x, 13000.0, order=2)
        return dsp.saturate(x, drive=1.15, mix=0.25)

    return _finish(buf, clock, spec, ir, 0.28, beds, master)


# ──────────────────────────────────────────────────────────────
# 27. Rain — Black Screen  (黒画面の雨 10時間)
# ──────────────────────────────────────────────────────────────

def build_rain_black(spec: TrackSpec, seconds: float) -> tuple[np.ndarray, dict]:
    """
    黒画面 + 雨だけ。睡眠系で確立された定番フォーマット
    (画面の光がゼロ = 部屋が真っ暗のまま)。
    15 とは別の雨 (穏やかで雷なし) をシードから合成する。
    """
    rng = np.random.default_rng(spec.seed)
    clock = clock_for(seconds, spec.bpm)
    bank = I.SampleBank(seed=spec.seed, n_variants=2)
    spans = _timeline(spec, clock, rng)
    buf = _new_buf(clock, tail=24.0)

    A.play_pad(buf, spans, clock, bank, gain=0.16, brightness=0.4,
               attack=9.0, release=10.0, rng=rng, n_voices=3, low=40, high=62)
    A.play_drone(buf, T.note("A", 1) + spec.key_root, clock, bank,
                 gain=0.10, partials=5)

    ir = dsp.make_reverb_ir(5.0, rt60=6.0, damp=0.8, predelay=0.05,
                            seed=spec.seed)
    n = clock.n_samples
    beds = [
        (lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.6, window=True), +6.0),
        (lambda: NT.wind(n, seed=spec.seed + 2), -18.0),
        (lambda: NT.room_tone(n, seed=spec.seed + 3), -30.0),
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=450.0, gain_db=-7.0)
        x = dsp.lowpass(x, 8000.0, order=2)
        x = dsp.highpass(x, 36.0, order=2)
        return x

    return _finish(buf, clock, spec, ir, 0.36, beds, master)


# ──────────────────────────────────────────────────────────────
# トラック一覧
# ──────────────────────────────────────────────────────────────

TRACKS: list[TrackSpec] = [
    TrackSpec(
        slug="01_lofi_rainy_study",
        title_en="Rainy Lofi Study Beats",
        genre_ja="ローファイ・ヒップホップ（雨の窓辺）",
        use_case="study", bpm=78.0, key="Am", key_root=9, scale="minor",
        prog_key="lofi", visual="night_drive", seed=1011,
        build=build_lofi_study,
        seo=dict(
            title="Rainy Lofi Beats to Study & Relax 🌧️ 2 Hours of Chill Hip Hop",
            keywords=["lofi", "lofi hip hop", "study music", "rain",
                      "chill beats", "relaxing music", "focus"],
        ),
    ),
    TrackSpec(
        slug="02_deep_sleep_ambient",
        title_en="Deep Sleep Ambient",
        genre_ja="ディープスリープ・アンビエント",
        use_case="sleep", bpm=52.0, key="Am", key_root=9, scale="minor",
        prog_key="ambient", visual="starry_night", seed=2022,
            build=build_deep_sleep,
        seo=dict(
            title="Deep Sleep Music 😴 Fall Asleep Fast — 2 Hours of Calm Ambient & Rain",
            keywords=["sleep music", "deep sleep", "insomnia", "ambient",
                      "relaxing music", "rain sounds", "calm"],
        ),
    ),
    TrackSpec(
        slug="03_piano_and_rain",
        title_en="Piano & Rain",
        genre_ja="ピアノ＋雨音",
        use_case="relax", bpm=62.0, key="C", key_root=0, scale="major",
        prog_key="piano_rain", visual="rain_street", seed=3033,
        build=build_piano_rain,
        seo=dict(
            title="Relaxing Piano & Rain Sounds 🎹🌧️ 2 Hours for Sleep, Study & Stress Relief",
            keywords=["piano music", "rain sounds", "relaxing piano",
                      "sleep music", "study music", "stress relief"],
        ),
    ),
    TrackSpec(
        slug="04_cozy_coffee_jazz",
        title_en="Cozy Coffee Shop Jazz",
        genre_ja="カフェ・ジャズ",
        use_case="work", bpm=96.0, key="C", key_root=0, scale="major",
        prog_key="jazz", visual="coffee_shop", seed=4044,
        build=build_cafe_jazz,
        seo=dict(
            title="Cozy Coffee Shop Jazz ☕ 2 Hours of Warm Jazz Piano for Work & Study",
            keywords=["jazz music", "coffee shop", "cafe music",
                      "relaxing jazz", "work music", "background music"],
        ),
    ),
    TrackSpec(
        slug="05_bossa_nova_cafe",
        title_en="Bossa Nova Cafe",
        genre_ja="ボサノヴァ・カフェ",
        use_case="work", bpm=124.0, key="G", key_root=7, scale="major",
        prog_key="bossa", visual="seaside_cafe", seed=5055,
        build=build_bossa,
        seo=dict(
            title="Bossa Nova Cafe 🌿 2 Hours of Smooth Brazilian Jazz for a Good Mood",
            keywords=["bossa nova", "cafe music", "brazilian jazz",
                      "background music", "morning music", "relaxing"],
        ),
    ),
    TrackSpec(
        slug="06_healing_meditation_432",
        title_en="Healing Meditation 432Hz",
        genre_ja="ヒーリング／瞑想（432Hz）",
        use_case="sleep", bpm=48.0, key="Dm", key_root=2, scale="dorian",
        prog_key="healing", visual="zen_water", seed=6066, a4=432.0,
            build=build_healing_432,
        seo=dict(
            title="432Hz Healing Meditation Music 🧘 2 Hours of Singing Bowls for Deep Relaxation",
            keywords=["432hz", "meditation music", "healing music",
                      "singing bowl", "yoga music", "chakra", "relaxation"],
        ),
    ),
    TrackSpec(
        slug="07_fireplace_winter_jazz",
        title_en="Fireplace Winter Jazz",
        genre_ja="暖炉＋冬のジャズ",
        use_case="relax", bpm=88.0, key="F", key_root=5, scale="major",
        prog_key="winter", visual="fireplace", seed=7077,
        build=build_winter_fire,
        seo=dict(
            title="Fireplace Jazz 🔥 2 Hours of Warm Winter Jazz & Crackling Fire",
            keywords=["fireplace", "winter jazz", "christmas jazz",
                      "cozy", "relaxing jazz", "crackling fire"],
        ),
    ),
    TrackSpec(
        slug="08_ocean_waves_ambient",
        title_en="Ocean Waves Ambient",
        genre_ja="海のアンビエント",
        use_case="sleep", bpm=50.0, key="G", key_root=7, scale="major",
        prog_key="ocean", visual="moonlit_ocean", seed=8088,
            build=build_ocean_ambient,
        seo=dict(
            title="Ocean Waves & Ambient Music 🌊 2 Hours of Calm Sea Sounds for Sleep",
            keywords=["ocean waves", "sea sounds", "sleep music",
                      "ambient", "beach", "relaxing music", "nature sounds"],
        ),
    ),
    TrackSpec(
        slug="09_fantasy_tavern",
        title_en="Fantasy Tavern Ambience",
        genre_ja="ファンタジー酒場（中世アンビエンス）",
        use_case="work", bpm=84.0, key="Dm", key_root=2, scale="dorian",
        prog_key="fantasy", visual="tavern", seed=9099,
        build=build_fantasy_tavern,
        seo=dict(
            title="Medieval Tavern Ambience 🍺 2 Hours of Fantasy Music & Crackling Fire",
            keywords=["tavern", "medieval music", "fantasy ambience",
                      "dnd music", "rpg", "celtic", "reading music"],
        ),
    ),
    TrackSpec(
        slug="10_deep_focus_flow",
        title_en="Deep Focus Flow",
        genre_ja="ディープフォーカス（集中）",
        use_case="study", bpm=60.0, key="Am", key_root=9, scale="dorian",
        prog_key="focus", visual="night_skyline", seed=1100,
        build=build_deep_focus,
        seo=dict(
            title="Deep Focus Music 🧠 2 Hours of Ambient Flow State Music for Studying & Work",
            keywords=["focus music", "concentration", "study music",
                      "deep work", "brown noise", "ambient", "productivity"],
        ),
    ),
    # 再生時間の稼ぎ頭。8時間版として書き出す (--repeats 20)。
    # 02 と同じジャンルだが seed も調も違うので完全に別の曲。
    # 同じ音源を長さ違いで2本出すのはポリシー違反になるため、必ず別曲にする。
    TrackSpec(
        slug="11_sleep_city_8h",
        title_en="All Night Sleep Ambient",
        genre_ja="8時間睡眠アンビエント（夜の街）",
        use_case="sleep", bpm=46.0, key="Dm", key_root=2, scale="minor",
        prog_key="ambient", visual="night_skyline", seed=1212,
        build=build_deep_sleep,
        seo=dict(
            title="8 Hour Sleep Music 🌃 Deep Ambient for a Full Night's Rest",
            keywords=["8 hour sleep music", "sleep music", "deep sleep",
                      "ambient", "insomnia", "relaxing music", "night"],
        ),
    ),
    TrackSpec(
        slug="12_anime_piano_emotional",
        title_en="Emotional Anime Piano",
        genre_ja="アニソン風・情感のあるピアノ",
        use_case="relax", bpm=76.0, key="C", key_root=0, scale="major",
        prog_key="anime", visual="anime_dusk", seed=1212 + 77,
        build=build_anime_piano,
        seo=dict(
            title="Emotional Anime Piano 🌸 Beautiful Japanese Melodies "
                  "for Study & Relaxing",
            keywords=["anime piano", "emotional piano", "japanese music",
                      "anime ost", "sad piano", "study music",
                      "relaxing piano", "anime bgm"],
        ),
    ),
    TrackSpec(
        slug="13_fresh_morning_acoustic",
        title_en="Fresh Morning Acoustic",
        genre_ja="爽やかな朝のアコースティック",
        use_case="work", bpm=104.0, key="D", key_root=2, scale="major",
        prog_key="fresh", visual="morning_meadow", seed=1313,
        build=build_fresh_morning,
        seo=dict(
            title="Fresh Morning Music ☀️ Uplifting Acoustic for a Good Day",
            keywords=["morning music", "fresh music", "acoustic",
                      "positive music", "good morning", "happy music",
                      "work music", "cafe acoustic"],
        ),
    ),
    TrackSpec(
        slug="14_japanese_lofi_koto",
        title_en="Japanese Lofi (Koto & Beats)",
        genre_ja="和風ローファイ（琴）",
        use_case="study", bpm=72.0, key="Am", key_root=0, scale="hirajoshi",
        prog_key="wafu", visual="lantern_street", seed=1414,
        build=build_japanese_lofi,
        seo=dict(
            title="Japanese Lofi 🏮 Koto & Chill Beats for Study & Work",
            keywords=["japanese lofi", "koto music", "lofi hip hop",
                      "japan chill", "study music", "zen lofi",
                      "asian lofi", "tokyo night"],
        ),
    ),
    TrackSpec(
        slug="15_rain_thunder_night",
        title_en="Rain & Distant Thunder at Night",
        genre_ja="雷雨の夜（環境音メイン）",
        use_case="sleep", bpm=48.0, key="Am", key_root=0, scale="minor",
        prog_key="ambient", visual="storm_window", seed=1515,
        build=build_rain_thunder,
        seo=dict(
            title="Heavy Rain & Distant Thunder at Night 🌧️ for Deep Sleep",
            keywords=["rain sounds", "thunder", "rain on window",
                      "sleep sounds", "thunderstorm", "rain for sleeping",
                      "insomnia relief", "night rain"],
        ),
    ),
    TrackSpec(
        slug="16_autumn_cafe_jazz",
        title_en="Autumn Café Jazz",
        genre_ja="秋のカフェジャズ（9〜11月の季節枠）",
        use_case="work", bpm=80.0, key="Bb", key_root=10, scale="major",
        prog_key="jazz", visual="autumn_leaves", seed=1616,
        build=build_autumn_jazz,
        seo=dict(
            title="Autumn Jazz 🍂 Cozy Fall Café Music for Work & Study",
            keywords=["autumn jazz", "fall music", "cozy jazz",
                      "september jazz", "coffee jazz", "rainy autumn",
                      "work music", "smooth jazz"],
        ),
    ),
    TrackSpec(
        slug="17_christmas_jazz",
        title_en="Christmas Jazz",
        genre_ja="クリスマスジャズ（11〜12月の季節枠）",
        use_case="relax", bpm=92.0, key="C", key_root=0, scale="major",
        prog_key="christmas", visual="christmas_window", seed=1717,
        build=build_christmas_jazz,
        seo=dict(
            title="Christmas Jazz 🎄 Cozy Holiday Music by the Fireplace",
            keywords=["christmas jazz", "christmas music", "holiday jazz",
                      "winter jazz", "cozy christmas", "fireplace",
                      "december", "holiday music instrumental"],
        ),
    ),
    TrackSpec(
        slug="18_starship_sleep",
        title_en="Starship Sleeping Quarters",
        genre_ja="宇宙船の寝室（睡眠用ハム音）",
        use_case="sleep", bpm=45.0, key="Am", key_root=0, scale="minor",
        prog_key="ambient", visual="spaceship_window", seed=1818,
        build=build_spaceship,
        seo=dict(
            title="Starship Sleeping Quarters 🚀 Deep Space White Noise for Sleep",
            keywords=["spaceship white noise", "starship ambience",
                      "space sounds", "sleep sounds", "sci-fi ambience",
                      "deep bass sleep", "white noise", "engine hum"],
        ),
    ),
    TrackSpec(
        slug="19_528hz_love_frequency",
        title_en="528Hz Healing Frequency",
        genre_ja="528Hz ヒーリング（A=444Hz実調律）",
        use_case="relax", bpm=50.0, key="C", key_root=0, scale="major",
        prog_key="ambient", visual="golden_light", seed=1919, a4=444.0,
        build=build_528,
        seo=dict(
            title="528Hz Healing Frequency ✨ Pure Tone Meditation & Deep Sleep",
            keywords=["528hz", "healing frequency", "love frequency",
                      "meditation music", "sleep music", "solfeggio",
                      "positive energy", "relaxation"],
        ),
    ),
    TrackSpec(
        slug="20_focus_40hz",
        title_en="40Hz Deep Focus",
        genre_ja="40Hz集中ドローン（ガンマ波リズム）",
        use_case="study", bpm=60.0, key="Am", key_root=0, scale="dorian",
        prog_key="focus", visual="focus_depths", seed=2020,
        build=build_focus_40hz,
        seo=dict(
            title="40Hz Focus Music 🧠 Gamma Rhythm Ambient for Deep Work",
            keywords=["40hz", "gamma waves", "focus music", "study music",
                      "concentration", "deep work", "adhd focus",
                      "brain music"],
        ),
    ),
    TrackSpec(
        slug="21_halloween_night",
        title_en="Halloween Night Ambience",
        genre_ja="ハロウィンの夜（9〜10月の季節枠）",
        use_case="relax", bpm=66.0, key="Am", key_root=0, scale="harmonic_minor",
        prog_key="halloween", visual="halloween_manor", seed=2121,
        build=build_halloween,
        seo=dict(
            title="Halloween Ambience 🎃 Spooky Night Music & Autumn Wind",
            keywords=["halloween ambience", "spooky music", "halloween music",
                      "october", "autumn night", "haunted", "halloween party",
                      "trick or treat"],
        ),
    ),
    TrackSpec(
        slug="22_snowstorm_fireplace",
        title_en="Snowstorm & Fireplace",
        genre_ja="吹雪と暖炉（12〜2月の季節枠）",
        use_case="sleep", bpm=48.0, key="Dm", key_root=5, scale="minor",
        prog_key="ambient", visual="snow_cabin", seed=2222,
        build=build_snowstorm,
        seo=dict(
            title="Blizzard & Crackling Fireplace ❄️ Cozy Snowstorm for Sleep",
            keywords=["blizzard sounds", "snowstorm", "fireplace",
                      "winter sounds", "sleep sounds", "howling wind",
                      "cozy cabin", "snow storm sleep"],
        ),
    ),
    TrackSpec(
        slug="23_forest_night_camp",
        title_en="Forest Night Campfire",
        genre_ja="夜の森の野営（TTRPG/睡眠）",
        use_case="sleep", bpm=50.0, key="D", key_root=0, scale="dorian",
        prog_key="healing", visual="forest_camp", seed=2323,
        build=build_forest_camp,
        seo=dict(
            title="Forest Night Campfire 🏕️ Crickets & Crackling Fire for Sleep",
            keywords=["campfire sounds", "forest night", "crickets",
                      "camping ambience", "dnd ambience", "nature sounds",
                      "night forest", "sleep sounds"],
        ),
    ),
    TrackSpec(
        slug="24_deep_space_drone",
        title_en="Deep Space Drone",
        genre_ja="ダークアンビエント（星雲）",
        use_case="sleep", bpm=40.0, key="Em", key_root=7, scale="minor",
        prog_key="ambient", visual="nebula", seed=2424,
        build=build_dark_ambient,
        seo=dict(
            title="Deep Space Ambient 🌌 Dark Drone Music for Sleep & Cosmic Calm",
            keywords=["dark ambient", "space ambient", "drone music",
                      "cosmic", "nebula", "deep sleep", "interstellar",
                      "space music"],
        ),
    ),
    TrackSpec(
        slug="25_cyberpunk_rain",
        title_en="Cyberpunk Rain",
        genre_ja="サイバーパンクの雨の夜",
        use_case="work", bpm=86.0, key="Am", key_root=0, scale="minor",
        prog_key="cyber", visual="neon_rain", seed=2525,
        build=build_cyberpunk,
        seo=dict(
            title="Cyberpunk Rain 🌃 Neon Night Synth Ambient for Work & Focus",
            keywords=["cyberpunk music", "synthwave ambient", "neon rain",
                      "night city", "futuristic", "blade runner vibes",
                      "work music", "coding music"],
        ),
    ),
    TrackSpec(
        slug="26_dark_academia_library",
        title_en="Dark Academia Library",
        genre_ja="古い図書室（ダークアカデミア）",
        use_case="study", bpm=60.0, key="Am", key_root=0, scale="minor",
        prog_key="academia", visual="old_library", seed=2626,
        build=build_academia,
        seo=dict(
            title="Dark Academia Library 🕯️ Melancholy Piano, Rain & a Ticking Clock",
            keywords=["dark academia", "library ambience", "study music",
                      "melancholy piano", "rainy library", "old books",
                      "classical study", "writing music"],
        ),
    ),
    TrackSpec(
        slug="27_rain_black_screen",
        title_en="Rain — Black Screen",
        genre_ja="黒画面の雨（10時間）",
        use_case="sleep", bpm=46.0, key="Am", key_root=0, scale="minor",
        prog_key="ambient", visual="black_screen", seed=2727,
        build=build_rain_black,
        seo=dict(
            title="Rain Sounds for Sleep 🌧️ BLACK SCREEN · 10 Hours of Gentle Night Rain",
            keywords=["rain black screen", "black screen sleep",
                      "rain sounds 10 hours", "dark screen rain",
                      "sleep sounds", "rain no music", "insomnia",
                      "rain all night"],
        ),
    ),
]

BY_SLUG = {t.slug: t for t in TRACKS}


def render(spec: TrackSpec, seconds: float = LOOP_SECONDS) -> tuple[np.ndarray, dict]:
    """1 トラックをレンダリングして (stereo float32, 情報 dict) を返す"""
    if spec.build is None:
        raise ValueError(f"no builder for {spec.slug}")
    # 基準ピッチを実際の合成に反映する (432Hz / 444Hz チューニング)
    dsp.set_tuning(spec.a4)
    try:
        audio, info = spec.build(spec, seconds)
    finally:
        dsp.set_tuning(440.0)
    info["slug"] = spec.slug
    info["seconds"] = seconds
    info["a4_hz"] = spec.a4
    return audio, info
