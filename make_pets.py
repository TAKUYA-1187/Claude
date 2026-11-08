#!/usr/bin/env python3
"""
pet02・pet03 の試作音源を作り、検査する。2026-11-08。

    PYTHONHASHSEED=0 python3 make_pets.py

出力 (out/release_2026-11-08/): <slug>.flac (44.1kHz/24bit) / <slug>.mp3 (320k) / <slug>_qa.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bgm_studio import dsp, video as V                       # noqa: E402
from bgm_studio.piano_piece import render                      # noqa: E402
from bgm_studio.pets import PIECES                             # noqa: E402
from make_orig01 import write_wav24, clicks                    # noqa: E402
import qa_check as Q                                           # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "release_2026-11-08"
SR = dsp.SR


def qa(x, info, path: Path) -> dict:
    ff = V.ffmpeg_exe()
    r = {"duration_s": round(x.shape[0] / SR, 2), "sample_rate_hz": SR, "bit_depth": 24, "channels": 2, "tuning": "A=440 Hz 平均律",
         "lufs_internal": round(dsp.lufs_integrated(x), 2), "true_peak_dbtp": round(dsp.true_peak_db(x), 2),
         "clipped_samples": int((np.abs(x) >= 0.999).sum())}
    e = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = e[e.rfind("Summary:"):]
    for k, pat in (("ffmpeg_I_lufs", r"I:\s+(-?[\d.]+) LUFS"), ("ffmpeg_LRA_lu", r"LRA:\s+(-?[\d.]+) LU"),
                   ("ffmpeg_true_peak_dbfs", r"Peak:\s+(-?[\d.]+) dBFS")):
        m = re.search(pat, summ)
        r[k] = float(m.group(1)) if m else None
    mono = x.mean(axis=1).astype(np.float64)
    r["first_sound_s"] = round(float(np.argmax(np.abs(mono) > 10 ** (-50 / 20)) / SR), 3)
    q = SR // 4
    db = 20 * np.log10(np.sqrt((mono[: len(mono) // q * q].reshape(-1, q) ** 2).mean(1)) + 1e-12)
    r["rms_db_per_0_25s"] = [round(float(v), 1) for v in db]
    r["quiet_below_-50dB_s"] = round(float((db < -50).sum() * 0.25), 2)
    h = SR
    db1 = 20 * np.log10(np.sqrt((mono[: len(mono) // h * h].reshape(-1, h) ** 2).mean(1)) + 1e-12)
    r["loudness_jumps_over_6db_per_1s"] = [(i, round(float(db1[i] - db1[i - 1]), 1)) for i in range(1, len(db1))
                                           if db1[i] - db1[i - 1] > 6.0]
    r["bands_db_rel_250_500"] = {k: round(float(v), 1) for k, v in Q.octave_bands(dsp.mono(x)).items()}
    win = Q.PURE_PIANO_BAND_WINDOW
    r["band_issues_PURE_PIANO_window"] = [f"{f}: {r['bands_db_rel_250_500'][f]}" for f, (lo, hi) in win.items()
                                          if not lo <= r["bands_db_rel_250_500"][f] <= hi]
    on = np.array(info["onsets"])
    cand = clicks(x)
    r["clicks_not_at_note_onsets"] = [c for c in cand if np.min(np.abs(on - c)) > 0.015]
    clash = []
    for s, d, m, sec in info["mel"]:
        for a0, ad, am, _ in info["acc"]:
            if a0 < s + d and s < a0 + ad and (m - am) % 12 in (1, 11):
                clash.append({"beat": round(s, 2), "section": sec, "melody_midi": m, "accomp_midi": am})
    r["melody_accomp_semitone_overlaps"] = clash
    r["lowest_note_midi"] = info["lowest_note"]
    r["lowest_note_hz"] = round(float(440 * 2 ** ((info["lowest_note"] - 69) / 12)), 1)
    r["section_times_s"] = info["section_times"]
    r["end_ring_s"] = "最後の和音を鳴らしたまま 2.5 秒で消す（響きを途中で切らない）"
    r["human_listening"] = "Claude は音を聞けない。すべて自動検査"
    return r


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dsp.set_tuning(440.0)
    ff = V.ffmpeg_exe()
    for slug, p in PIECES.items():
        x, info = render(p)
        wav = OUT / f"{slug}.wav"
        write_wav24(wav, x)
        subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "flac", str(OUT / f"{slug}.flac")], check=True)
        subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "320k",
                        str(OUT / f"{slug}.mp3")], check=True)
        r = qa(x, info, wav)
        wav.unlink()
        (OUT / f"{slug}_qa.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(slug, {k: v for k, v in r.items() if k != "rms_db_per_0_25s"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
