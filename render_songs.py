#!/usr/bin/env python3
"""
歌もの (ヴォカリーズ) を 10 曲、動画として書き出す。

BGM と違う点:
  - 長さは 3〜4 分。ループしない。ちゃんと終わる (フェードアウト)
  - 歌 (合成の歌声) が主役で、伴奏は歌の下に置く
  - 検査も歌向け (継ぎ目検査なし、クリック/LUFS/TP/位相は同じ基準)

    python3 render_songs.py                # 全曲
    python3 render_songs.py --songs s01_first_light
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from bgm_studio import arrange as A          # noqa: E402
from bgm_studio import dsp                   # noqa: E402
from bgm_studio import instruments as I      # noqa: E402
from bgm_studio import nature as NT          # noqa: E402
from bgm_studio import theory as T           # noqa: E402
from bgm_studio import video as VID          # noqa: E402
from bgm_studio import visuals as VIS        # noqa: E402
from bgm_studio import vocal as VO           # noqa: E402
from bgm_studio.arrange import Clock         # noqa: E402

OUT = Path(__file__).parent / "out" / "songs"


# ──────────────────────────────────────────────────────────────
# 曲の定義
# ──────────────────────────────────────────────────────────────

@dataclass
class SongSpec:
    slug: str
    title_en: str
    voice: str                  # 'hikari' / 'aoi' / 'duet'
    style: str                  # 伴奏: pop / ballad / lofi / jazz / synth / folk / koto
    bpm: float
    key_root: int
    scale: str
    prog_key: str
    visual: str
    seed: int
    desc: str                   # 説明文 (1曲ずつ書く)
    # 構成: (タグ, 進行番号, 繰り返し, 密度, 歌うか, サビか)
    form: list = field(default_factory=lambda: [
        ("intro", 0, 1, 0.55, False, False),
        ("A1", 0, 2, 0.85, True, False),
        ("B1", 1, 1, 0.9, True, False),
        ("cho1", 2, 2, 1.0, True, True),
        ("inter", 0, 1, 0.6, False, False),
        ("A2", 0, 2, 0.85, True, False),
        ("cho2", 2, 2, 1.0, True, True),
        ("out", 1, 1, 0.5, False, False),
    ])


SONGS: list[SongSpec] = [
    SongSpec("s01_first_light", "First Light", "hikari", "pop",
             96.0, 0, "major", "anime", "morning_meadow", 3101,
             "A bright wordless pop song for the first hour of the day. "
             "The chorus climbs an octave the way anime openings do."),
    SongSpec("s02_rain_letter", "Rain Letter", "hikari", "ballad",
             68.0, 0, "major", "piano_rain", "rainy_window", 3202,
             "A quiet piano ballad sung to the sound of rain. "
             "The voice stays soft, like reading a letter aloud."),
    SongSpec("s03_midnight_homework", "Midnight Homework", "hikari", "lofi",
             76.0, 0, "minor", "lofi", "night_drive", 3303,
             "Lo-fi with a hummed vocal line instead of a lead instrument. "
             "For finishing what you promised yourself you'd finish."),
    SongSpec("s04_neon_heart", "Neon Heart", "hikari", "synth",
             92.0, 0, "minor", "cyber", "neon_rain", 3404,
             "A synth-pop vocalise for the city at 2am. Two chords, "
             "one voice, rain on neon."),
    SongSpec("s05_golden_hour", "Golden Hour", "hikari", "folk",
             104.0, 2, "major", "fresh", "anime_dusk", 3505,
             "Nylon guitar and a bright voice for the hour before sunset. "
             "Light as a walk home."),
    SongSpec("s06_papercrane", "Papercrane", "aoi", "ballad",
             63.0, 0, "major", "anime", "starry_night", 3606,
             "A low, breathy voice over the canon progression. "
             "Folded slowly, like its namesake."),
    SongSpec("s07_closing_time", "Closing Time", "aoi", "jazz",
             66.0, 0, "minor", "academia", "old_library", 3707,
             "Jazz for an emptying library: brushes, upright bass, and a "
             "voice that hums more than it sings."),
    SongSpec("s08_last_train_north", "Last Train North", "aoi", "jazz",
             72.0, 5, "major", "winter", "snow_cabin", 3808,
             "A winter jazz waltz-of-sorts for the last train of the night. "
             "Deep voice, warm brushes, snow outside."),
    SongSpec("s09_paper_lantern", "Paper Lantern", "aoi", "koto",
             72.0, 0, "hirajoshi", "wafu", "lantern_street", 3909,
             "Koto and a low hummed voice in a Japanese five-note scale. "
             "An alley of lanterns, walked slowly."),
    SongSpec("s10_parallel_stars", "Parallel Stars", "duet", "pop",
             88.0, 0, "major", "anime", "night_skyline", 4010,
             "Two synthesized voices — one high, one low — trading verses "
             "and meeting an octave apart in the chorus."),
]

BY_SLUG = {s.slug: s for s in SONGS}


# ──────────────────────────────────────────────────────────────
# 伴奏
# ──────────────────────────────────────────────────────────────

def _backing(style: str, spec: SongSpec, buf, spans, clock, bank, rng, n):
    """スタイルごとの伴奏。歌が主役なのでゲインは BGM より控えめ"""
    beds = []
    if style == "pop":
        A.play_comp(buf, spans, clock, bank, inst="piano", style="lofi",
                    gain=0.17, voicing="close", center=57, rng=rng)
        A.play_pad(buf, spans, clock, bank, gain=0.10, brightness=0.7,
                   attack=2.5, release=3.5, rng=rng, n_voices=4, low=48, high=79)
        A.play_bass(buf, spans, clock, bank, inst="subbass", style="pump",
                    gain=0.18, octave=-2, rng=rng)
        A.play_lofi_drums(buf, spans, clock, bank, gain=0.20, swing=0.06,
                          rng=rng, use_rim=False)
    elif style == "ballad":
        A.play_comp(buf, spans, clock, bank, inst="piano", style="ballad",
                    gain=0.22, voicing="close", center=55, rng=rng,
                    spread_ms=38.0)
        A.play_pad(buf, spans, clock, bank, gain=0.10, brightness=0.6,
                   attack=3.5, release=4.5, rng=rng, n_voices=4, low=48, high=78)
        A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                    gain=0.15, octave=-2, rng=rng)
        beds = [(lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.4,
                                 window=True), -24.0)]
    elif style == "lofi":
        A.play_comp(buf, spans, clock, bank, inst="rhodes", style="lofi",
                    gain=0.18, voicing="rootless", center=60, rng=rng)
        A.play_bass(buf, spans, clock, bank, inst="subbass", style="pump",
                    gain=0.18, octave=-2, rng=rng)
        A.play_lofi_drums(buf, spans, clock, bank, gain=0.22, swing=0.15,
                          rng=rng)
        beds = [(lambda: dsp.to_stereo(
            I.vinyl_crackle(n, np.random.default_rng(spec.seed + 2))), -26.0)]
    elif style == "jazz":
        A.play_comp(buf, spans, clock, bank, inst="piano", style="jazz",
                    gain=0.18, voicing="rootless", center=60, swing=0.55,
                    rng=rng)
        A.play_bass(buf, spans, clock, bank, inst="upright", style="walk",
                    gain=0.18, octave=-1, rng=rng,
                    scale_root=spec.key_root, scale="major")
        A.play_jazz_brushes(buf, spans, clock, bank, gain=0.13, rng=rng,
                            ride_prob=0.35)
    elif style == "synth":
        A.play_arp(buf, spans, clock, bank, inst="synth", gain=0.12, rate=0.5,
                   octaves=2, center=57, direction="up", rng=rng, pan=-0.1)
        A.play_pad(buf, spans, clock, bank, gain=0.13, brightness=0.7,
                   attack=2.5, release=4.0, rng=rng, n_voices=5, low=45, high=79)
        A.play_bass(buf, spans, clock, bank, inst="subbass", style="pump",
                    gain=0.20, octave=-2, rng=rng)
        beds = [(lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.45,
                                 window=False), -22.0)]
    elif style == "folk":
        A.play_comp(buf, spans, clock, bank, inst="nylon", style="bossa",
                    gain=0.20, voicing="close", center=59, rng=rng,
                    spread_ms=36.0)
        A.play_bass(buf, spans, clock, bank, inst="upright", style="bossa",
                    gain=0.15, octave=-1, rng=rng)
        A.play_bossa_perc(buf, spans, clock, bank, gain=0.09, rng=rng)
    elif style == "koto":
        A.play_arp(buf, spans, clock, bank, inst="koto", gain=0.13, rate=1.0,
                   octaves=1, center=64, direction="updown", rng=rng)
        A.play_pad(buf, spans, clock, bank, gain=0.09, brightness=0.5,
                   attack=4.0, release=5.0, rng=rng, n_voices=4, low=45, high=74)
        A.play_bass(buf, spans, clock, bank, inst="subbass", style="root",
                    gain=0.16, octave=-2, rng=rng)
        beds = [(lambda: NT.rain(n, seed=spec.seed + 1, intensity=0.3,
                                 window=True), -26.0)]
    return beds


# ──────────────────────────────────────────────────────────────
# 1 曲のレンダリング
# ──────────────────────────────────────────────────────────────

def build_song(spec: SongSpec) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(spec.seed)
    progs = [T.transpose(p, spec.key_root)
             for p in T.PROGRESSIONS[spec.prog_key]]

    # 構成 → セクション列と小節数
    sections = []
    chorus_beats: set[int] = set()
    sing_tags = {}
    bar_cursor = 0
    for tag, pi, reps, dens, sing, chorus in spec.form:
        prog = progs[pi % len(progs)]
        prog_bars = int(sum(c.bars for c in prog))
        sections.append(T.Section(prog=prog, repeats=reps, density=dens,
                                  melody=sing, tag=tag))
        bars = prog_bars * reps
        if chorus:
            for b in range(bar_cursor * 4, (bar_cursor + bars) * 4):
                chorus_beats.add(b)
        sing_tags[tag] = (sing, chorus)
        bar_cursor += bars

    total_bars = bar_cursor
    seconds = total_bars * 4 * 60.0 / spec.bpm
    clock = Clock(total_seconds=seconds, bars=total_bars, beats_per_bar=4)
    spans = A.build_timeline(sections, clock)
    n = clock.n_samples
    bank = I.SampleBank(seed=spec.seed, n_variants=3)
    buf = np.zeros((n + int(8.0 * dsp.SR), 2), dtype=np.float32)

    beds = _backing(spec.style, spec, buf, spans, clock, bank, rng, n)

    # ── 歌 ───────────────────────────────────────────────
    melody_scale = spec.scale
    m_root = spec.key_root
    if spec.prog_key == "wafu":       # 和風は A センター平調子
        m_root = (spec.key_root + 9) % 12
    if spec.scale == "hirajoshi":
        pass
    elif spec.prog_key in ("anime", "fresh", "piano_rain", "winter"):
        melody_scale = "major"
    notes = VO.make_vocal_line(spans, clock, m_root, melody_scale,
                               lo=60, hi=81, rng=rng,
                               chorus_beats=chorus_beats)
    if spec.voice == "duet":
        half = [nt for nt in notes if not nt["chorus"]]
        cho = [nt for nt in notes if nt["chorus"]]
        VO.render_vocal(buf, half, clock, VO.HIKARI, gain=0.46,
                        seed=spec.seed, pan=-0.08)
        VO.render_vocal(buf, cho, clock, VO.HIKARI, gain=0.46,
                        seed=spec.seed, pan=-0.10)
        low = [dict(nt, midi=nt["midi"] - 12) for nt in cho]
        VO.render_vocal(buf, low, clock, VO.AOI, gain=0.34,
                        seed=spec.seed + 7, pan=0.14)
    else:
        voice = VO.VOICES[spec.voice]
        base_gain = 0.48
        if spec.voice == "aoi":
            notes = [dict(nt, midi=nt["midi"] - 12) for nt in notes]
        VO.render_vocal(buf, notes, clock, voice, gain=base_gain,
                        seed=spec.seed)

    # ── 空間と仕上げ ──────────────────────────────────────
    ir = dsp.make_reverb_ir(2.6, rt60=2.1, damp=0.55, predelay=0.02,
                            seed=spec.seed)
    x = dsp.reverb(buf, ir, mix=0.22, tail=True)[:n + int(4 * dsp.SR)]
    del buf

    music_rms = float(np.sqrt(np.mean(dsp.mono(x[:n]).astype(np.float64) ** 2))) + 1e-9
    for make_bed, rel_db in beds:
        b = make_bed()[:n]
        b_rms = float(np.sqrt(np.mean(b.astype(np.float64) ** 2))) + 1e-12
        x[:n] += b * np.float32(music_rms * dsp.db2lin(rel_db) / b_rms)
        del b

    x = dsp.tilt_eq(x, pivot=900.0, gain_db=-2.0)
    x = dsp.lowpass(x, 15500.0, order=2)
    x = dsp.highpass(x, 40.0, order=2)
    x = dsp.saturate(x, drive=1.1, mix=0.18)

    # 終わり方: 最後の 5 秒でフェードアウト (歌もののフェード終止)
    n_end = len(x)
    fade_out = min(int(5.0 * dsp.SR), n_end // 4)
    x[n_end - fade_out:] *= np.linspace(1, 0, fade_out,
                                        dtype=np.float32)[:, None]
    fade_in = int(0.6 * dsp.SR)
    x[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]

    y, info = dsp.normalize_lufs(x, target=-14.0, ceiling_db=-1.0,
                                 circular=False)
    info.update(bpm=spec.bpm, bars=total_bars,
                seconds=round(n_end / dsp.SR, 1), n_notes=len(notes))
    return y, info


# ──────────────────────────────────────────────────────────────
# 検査 (歌もの用)
# ──────────────────────────────────────────────────────────────

def song_qa(y: np.ndarray) -> tuple[dict, list[str]]:
    m = dsp.mono(y).astype(np.float64)
    issues = []
    r = {}
    r["lufs"] = dsp.lufs_integrated(y)
    r["tp"] = dsp.true_peak_db(y)
    d = np.abs(np.diff(m))
    med = float(np.median(d) + 1e-12)
    r["clicks"] = int((d > max(med * 80.0, 0.05)).sum())
    l, rr = y[:, 0].astype(np.float64), y[:, 1].astype(np.float64)
    den = np.sqrt((l ** 2).sum() * (rr ** 2).sum())
    r["corr"] = float((l * rr).sum() / den) if den > 0 else 1.0
    rms = float(np.sqrt((m ** 2).mean()))
    r["crest"] = float(dsp.lin2db(np.abs(m).max() / max(rms, 1e-12)))
    if abs(r["lufs"] + 14.0) > 1.0:
        issues.append(f"LUFS {r['lufs']:.1f}")
    if r["tp"] > -0.9:
        issues.append(f"TP {r['tp']:.2f}")
    if r["clicks"]:
        issues.append(f"クリック {r['clicks']}")
    if r["corr"] < 0.20:
        issues.append(f"位相 {r['corr']:.2f}")
    if r["crest"] < 6.0:
        issues.append(f"潰しすぎ {r['crest']:.1f}")
    return r, issues


# ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--songs", nargs="*", default=None)
    args = ap.parse_args()

    specs = SONGS if not args.songs else [BY_SLUG[s] for s in args.songs]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tmp").mkdir(exist_ok=True)

    ok_all = True
    report = []
    for spec in specs:
        t0 = time.time()
        print(f"▸ {spec.slug}  ({spec.title_en} / voice={spec.voice})")
        y, info = build_song(spec)
        qa, issues = song_qa(y)
        dur = len(y) / dsp.SR
        wav = OUT / f"{spec.slug}.wav"
        VID.write_wav(wav, y)

        # 映像: 既存シーンの 20 秒ループを曲の長さぶん繰り返す
        vis = OUT / "tmp" / f"{spec.slug}_loop.mp4"
        VID.encode_visual_loop(spec.visual, vis, seed=spec.seed)
        m4a = OUT / "tmp" / f"{spec.slug}.m4a"
        VID.loop_audio_to_aac(wav, m4a, repeats=1, bitrate="192k")
        VID.mux_looped(vis, m4a, OUT / f"{spec.slug}.mp4", dur)

        # サムネイルとメタデータ
        VIS.thumbnail(spec.visual, [spec.title_en.upper(), "ORIGINAL SONG"],
                      seed=spec.seed).save(OUT / f"{spec.slug}.png")
        meta = dict(
            slug=spec.slug,
            title=f"{spec.title_en} — Original Song (Synthesized Vocals)",
            description=(
                f"{spec.desc}\n\n"
                f"A note on the voice: this is a fully synthesized vocalise — "
                f"a wordless voice built from sine harmonics and formant "
                f"resonances, singing vowels rather than lyrics. No vocal "
                f"sample libraries were used; the voice, like every "
                f"instrument here, is generated from scratch.\n\n"
                f"{int(spec.bpm)} BPM · original composition · "
                f"synthesized voice & instruments.\n\n"
                f"— Written, sung (synthetically) and mixed for this channel."),
            duration_s=round(dur, 1), qa=qa, issues=issues)
        (OUT / f"{spec.slug}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=float),
            encoding="utf-8")

        ok = not issues
        ok_all &= ok
        report.append((spec.slug, dur, qa, issues))
        print(f"    {dur/60:.1f}分 / LUFS {qa['lufs']:.2f} / TP {qa['tp']:.2f} "
              f"/ クリック {qa['clicks']} / 相関 {qa['corr']:.2f} "
              f"→ {'OK' if ok else '⚠ ' + ' / '.join(issues)}   "
              f"({time.time()-t0:.0f}s)")

    print()
    print(f"{len(report)} 曲 / 指摘 {sum(1 for *_, i in report if i)} 件")
    print("総合判定:", "全て合格" if ok_all else "要修正あり")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
