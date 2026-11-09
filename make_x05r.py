#!/usr/bin/env python3
"""
x05r_jingle_bells_piano の試作（約 67 秒）を作り、検査する。2026-11-09。

    PYTHONHASHSEED=0 python3 make_x05r.py

出力 (out/release_2026-11-09/): x05r_jingle_bells_piano.flac (44.1kHz/24bit) / .mp3 (320k) / _qa.json / _score.mid
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bgm_studio import dsp, video as V                        # noqa: E402
from bgm_studio.piano_piece import render, score               # noqa: E402
from bgm_studio.xmas_r import PIECES                           # noqa: E402
from make_orig01 import write_wav24                            # noqa: E402
from make_pets import qa                                        # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "release_2026-11-09"


def write_midi(path: Path, p, info) -> None:
    import mido
    mf = mido.MidiFile(ticks_per_beat=480)
    for name, notes in (("melody", [(s, d, m, 0.42) for s, d, m, _ in info["mel"]]), ("accompaniment", info["acc"])):
        tr = mido.MidiTrack()
        mf.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
        if name == "melody":
            tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(p.bpm), time=0))
            tr.append(mido.MetaMessage("key_signature", key="Bb", time=0))
        ev = []
        for s, d, m, v in notes:
            ev.append((int(round(s * 480)), 1, int(m), int(v * 127 / 0.7)))
            ev.append((int(round((s + d) * 480)), 0, int(m), 0))
        ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for t, on, m, v in ev:
            tr.append(mido.Message("note_on" if on else "note_off", note=m, velocity=v, time=t - last))
            last = t
    mf.save(str(path))


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
        r["tempo_bpm"], r["time_signature"], r["key"] = p.bpm, "4/4", "B♭ major（出典の G major から +3 半音）"
        r["sections_bars"] = {sec: len(spec.split()) for sec, spec in p.sections}
        write_midi(OUT / f"{slug}_score.mid", p, info)
        (OUT / f"{slug}_qa.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(slug, {k: v for k, v in r.items() if k != "rms_db_per_0_25s"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
