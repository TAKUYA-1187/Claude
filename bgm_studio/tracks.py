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

    # beds は「呼ぶと環境音を返す関数」のリスト。
    # 全部を先に作ると 24 分 × 3 レイヤーで 1.5GB 常駐してしまうので、
    # 1 本ずつ生成して足したそばから捨てる。
    if beds:
        for make_bed in beds:
            b = make_bed() if callable(make_bed) else make_bed
            music[:, :] += b[:n]
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
        lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.45, window=True) * 0.32,
        lambda: dsp.to_stereo(I.vinyl_crackle(n, np.random.default_rng(spec.seed + 2))) * 0.9,
        lambda: NT.room_tone(n, seed=spec.seed + 3) * 0.5,
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
    A.play_pad(buf, spans, clock, bank, gain=0.30, octave=0, brightness=0.55,
               attack=6.0, release=7.0, rng=rng, n_voices=5, low=40, high=76)
    A.play_drone(buf, T.note("A", 2) + spec.key_root, clock, bank,
                 gain=0.16, partials=9)
    A.play_sparse_bells(buf, spans, clock, bank, inst="bowl", gain=0.10,
                        every_bars=6.0, center=60, rng=rng)

    ir = dsp.make_reverb_ir(5.0, rt60=6.5, damp=0.75, predelay=0.05,
                            width=1.2, seed=spec.seed)
    n = clock.n_samples
    beds = [
        lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.35, window=True) * 0.26,
        lambda: NT.room_tone(n, seed=spec.seed + 2) * 0.8,
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=600.0, gain_db=-7.0)
        x = dsp.lowpass(x, 7200.0, order=2)     # 高域を大きく削る = 覚醒させない
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
        lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.7, window=True) * 0.55,
        lambda: NT.thunder(n, seed=spec.seed + 2, count=3) * 0.35,
        lambda: NT.room_tone(n, seed=spec.seed + 3) * 0.6,
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
        lambda: NT.cafe_ambience(n, seed=spec.seed + 1) * 0.30,
        lambda: NT.room_tone(n, seed=spec.seed + 2) * 0.5,
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
        lambda: NT.cafe_ambience(n, seed=spec.seed + 1) * 0.20,
        lambda: NT.room_tone(n, seed=spec.seed + 2) * 0.4,
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
                            width=1.3, seed=spec.seed)
    n = clock.n_samples
    beds = [NT.room_tone(n, seed=spec.seed + 1) * 0.7]

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
        lambda: NT.fireplace(n, seed=spec.seed + 1) * 0.42,
        lambda: NT.room_tone(n, seed=spec.seed + 2) * 0.6,
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

    ir = dsp.make_reverb_ir(5.0, rt60=5.5, damp=0.68, width=1.25, seed=spec.seed)
    n = clock.n_samples
    beds = [
        lambda: NT.ocean(n, seed=spec.seed + 1, period=8.5) * 0.62,
        lambda: NT.wind(n, seed=spec.seed + 2) * 0.12,
        lambda: NT.room_tone(n, seed=spec.seed + 3) * 0.5,
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
        lambda: NT.fireplace(n, seed=spec.seed + 1) * 0.40,
        lambda: NT.cafe_ambience(n, seed=spec.seed + 2) * 0.14,   # 酒場のざわめき
        lambda: NT.room_tone(n, seed=spec.seed + 3) * 0.6,
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
        lambda: NT.brown_noise_bed(n, seed=spec.seed + 1, tilt_hz=420.0) * 0.30,
        lambda: NT.room_tone(n, seed=spec.seed + 2) * 0.5,
    ]

    def master(x):
        x = dsp.tilt_eq(x, pivot=700.0, gain_db=-4.0)
        x = dsp.lowpass(x, 11000.0, order=2)
        x = dsp.highpass(x, 30.0, order=2)
        return dsp.saturate(x, drive=1.1, mix=0.22)

    return _finish(buf, clock, spec, ir, 0.34, beds, master)


# ──────────────────────────────────────────────────────────────
# トラック一覧
# ──────────────────────────────────────────────────────────────

TRACKS: list[TrackSpec] = [
    TrackSpec(
        slug="01_lofi_rainy_study",
        title_en="Rainy Lofi Study Beats",
        genre_ja="ローファイ・ヒップホップ（雨の窓辺）",
        use_case="study", bpm=78.0, key="Am", key_root=9, scale="minor",
        prog_key="lofi", visual="rainy_city", seed=1011,
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
]

BY_SLUG = {t.slug: t for t in TRACKS}


def render(spec: TrackSpec, seconds: float = LOOP_SECONDS) -> tuple[np.ndarray, dict]:
    """1 トラックをレンダリングして (stereo float32, 情報 dict) を返す"""
    if spec.build is None:
        raise ValueError(f"no builder for {spec.slug}")
    audio, info = spec.build(spec, seconds)
    info["slug"] = spec.slug
    info["seconds"] = seconds
    return audio, info
