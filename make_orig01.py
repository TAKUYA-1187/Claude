#!/usr/bin/env python3
"""
新曲 orig01_winter_reading_piano の 3 分試聴版を作り、検査する。

    PYTHONHASHSEED=0 python3 make_orig01.py

出力 (out/release_2026-11-07/):
  orig01_master.wav (48kHz/24bit) / orig01_master.flac / orig01_preview_3min.mp3 (320kbps)
  orig01_score.mid (作曲データ) / orig01_qa.json (自動検査の数値)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bgm_studio import dsp, orig01 as O, video as V   # noqa: E402
import qa_check as Q                                    # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "release_2026-11-07"
SR = dsp.SR


def write_wav24(path: Path, x: np.ndarray) -> None:
    y = np.clip(x, -1.0, 1.0 - 2 ** -23)
    i = (y * (2 ** 23)).astype(np.int32)
    b = np.zeros((i.size, 3), dtype=np.uint8)
    flat = i.reshape(-1)
    b[:, 0] = flat & 0xFF
    b[:, 1] = (flat >> 8) & 0xFF
    b[:, 2] = (flat >> 16) & 0xFF
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b.tobytes())


def clicks(x: np.ndarray, thresh_db: float = 18.0) -> list[float]:
    """
    クリック (急な段差) の検出: 2 次差分の大きさが、その前後 50ms の 2 次差分の RMS より
    thresh_db 以上大きいサンプルを探す。ピアノの打鍵の立ち上がりでも出るので、
    打鍵の時刻 (±15ms) に重なるものは除き、残りを時刻で返す
    """
    m = x.mean(axis=1).astype(np.float64)
    d2 = np.abs(np.diff(m, n=2))
    win = int(0.05 * SR)
    k = np.ones(win) / win
    rms = np.sqrt(np.convolve(d2 ** 2, k, mode="same")) + 1e-9
    idx = np.nonzero(d2 > rms * 10 ** (thresh_db / 20))[0]
    return [round(i / SR, 3) for i in idx]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dsp.set_tuning(440.0)
    x, info = O.render()
    dur = x.shape[0] / SR

    wav = OUT / "orig01_master.wav"
    write_wav24(wav, x)
    ff = V.ffmpeg_exe()
    subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "flac", str(OUT / "orig01_master.flac")], check=True)
    subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "320k",
                    str(OUT / "orig01_preview_3min.mp3")], check=True)
    O.write_midi(OUT / "orig01_score.mid", info)

    # ── 自動検査 ────────────────────────────────────────
    r = {"duration_s": round(dur, 2), "sample_rate": SR, "format": "WAV PCM 24-bit stereo / FLAC / MP3 320k"}
    r["lufs_integrated"] = round(dsp.lufs_integrated(x), 2)
    r["true_peak_dbtp"] = round(dsp.true_peak_db(x), 2)
    r["clipped_samples"] = int((np.abs(x) >= 0.999).sum())
    # ffmpeg の ebur128 で統合ラウドネス・LRA・True Peak を別に測る (自前の計算の確認)
    e = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(wav), "-filter_complex",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = e[e.rfind("Summary:"):]
    for key, pat in (("ffmpeg_I_lufs", r"I:\s+(-?[\d.]+) LUFS"), ("ffmpeg_LRA_lu", r"LRA:\s+(-?[\d.]+) LU"),
                     ("ffmpeg_true_peak_dbfs", r"Peak:\s+(-?[\d.]+) dBFS")):
        m = re.search(pat, summ)
        r[key] = float(m.group(1)) if m else None
    # 区間ごとの音量 (0.5 秒の RMS) と無音
    mono = x.mean(axis=1).astype(np.float64)
    hop = SR // 2
    db = 20 * np.log10(np.sqrt((mono[: len(mono) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-12)
    runs, st = [], None
    for i, q in enumerate(db < -50):
        if q and st is None:
            st = i
        if not q and st is not None:
            runs.append((st * 0.5, (i - st) * 0.5))
            st = None
    if st is not None:
        runs.append((st * 0.5, (len(db) - st) * 0.5))
    r["silence_runs_over_1s"] = [rr for rr in runs if rr[1] >= 1.0]
    r["first_sound_s"] = round(float(np.argmax(np.abs(mono) > 10 ** (-50 / 20)) / SR), 3)
    # 急な音量差: 2 秒ごとの RMS が前の 2 秒より 6dB 以上大きくなる所
    h2 = SR * 2
    db2 = 20 * np.log10(np.sqrt((mono[: len(mono) // h2 * h2].reshape(-1, h2) ** 2).mean(1)) + 1e-12)
    r["loudness_jumps_over_6db"] = [(i * 2, round(float(db2[i] - db2[i - 1]), 1)) for i in range(1, len(db2))
                                    if db2[i] - db2[i - 1] > 6.0]
    r["rms_db_per_2s"] = [round(float(v), 1) for v in db2]
    # 帯域 (全体と、始め・中ほど・終わりの 30 秒)
    r["bands_db_rel"] = {k: round(float(v), 1) for k, v in Q.octave_bands(dsp.mono(x)).items()}
    for name, a in (("start_0_30", 0), ("middle", int(dur / 2 - 15)), ("end_last_30", int(dur - 30))):
        seg = x[a * SR:(a + 30) * SR]
        r[f"bands_{name}"] = {k: round(float(v), 1) for k, v in Q.octave_bands(dsp.mono(seg)).items()}
    win = Q.PURE_PIANO_BAND_WINDOW
    r["band_window_used"] = "PURE_PIANO_BAND_WINDOW (環境音なしのピアノ曲の窓)"
    r["band_issues"] = [f"{f}: {r['bands_db_rel'][f]}" for f, (lo, hi) in win.items()
                        if not lo <= r["bands_db_rel"][f] <= hi]
    # クリック: 打鍵の時刻を除いて残るもの
    tm = O.time_map(info["total_beats"])
    onsets = np.array(sorted({round(tm(s), 3) for s, *_ in info["mel"]} | {round(tm(s), 3) for s, *_ in info["acc"]}))
    cand = clicks(x)
    r["click_candidates_total"] = len(cand)
    r["clicks_not_at_onsets"] = [c for c in cand if np.min(np.abs(onsets - c)) > 0.015][:50]
    # 旋律と伴奏の半音のぶつかり (楽譜上で、同時に鳴る音を比べる)
    clash = []
    for s, d, m, sec in info["mel"]:
        for a0, ad, am, _ in info["acc"]:
            if a0 < s + d and s < a0 + ad and (m - am) % 12 in (1, 11) and abs(m - am) < 24:
                clash.append((round(s, 2), sec, m, am))
    r["melody_accomp_semitone_overlaps"] = clash
    r["sections_start_s"] = info["section_times"]
    (OUT / "orig01_qa.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in r.items():
        if k != "rms_db_per_2s":
            print(k, ":", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
