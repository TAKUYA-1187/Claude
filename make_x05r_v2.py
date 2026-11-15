#!/usr/bin/env python3
"""
x05r_jingle_bells_piano_v2 の試聴版 (約 75 秒) を作り、検査する。2026-11-15。GPT 指示書 §26。

    PYTHONHASHSEED=0 python3 make_x05r_v2.py

前提：samples/salamander_raw/ に Salamander Grand Piano V3 (44.1kHz/16bit) があること (prepare_salamander.py)

出力 (out/release_2026-11-15/):
  x05r_jingle_bells_piano_v2.flac (44.1kHz/24bit) / .mp3 (320k) / _qa.json / _score.mid
  x05r_v2_transcription_1857.csv  1857 年版の採譜 (ページ・段・小節・音・確かさ)
  x05r_v2_melody_sources.csv      使った旋律の小節ごとの出典と、今の一般的な形との違い
  x05r_v2_performance.csv         1 音ずつの打鍵時刻 (秒)・強さ・ペダルで止まる時刻
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio import dsp, video as V                        # noqa: E402
from bgm_studio import x05r_v2 as X                            # noqa: E402
from bgm_studio import grand                                    # noqa: E402
from make_orig01 import write_wav24                            # noqa: E402
from make_pets import qa                                        # noqa: E402

OUT = ROOT / "out" / "release_2026-11-15"
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

# 今の一般的な形 (ト長調、2/4 の小節ごと)。比較のためだけに使う (制作には使っていない)。
# 出典の版ではなく、広く歌われている形を Claude が書いたもの
MODERN_G_VERSE = {6: "F#4/1.5 R/.5", 7: "D5/.5 D5/.5 C5/.5 A4/.5", 14: "D5/.5 D5/.5 D5/.5 D5/.5"}
MODERN_G_CHORUS = {7: "B4/.5 A4/.5 A4/.5 B4/.5"}


def nm(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def write_midi(path: Path, info) -> None:
    import mido
    mf = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mf.tracks.append(tr)
    tr.append(mido.MetaMessage("track_name", name="x05r v2 piano (written score, constant tempo)", time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(X.BPM), time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.MetaMessage("key_signature", key="Bb", time=0))
    ev = []
    for e in info["events"]:
        ch = 0 if e["role"] == "mel" else 1
        ev.append((int(round(e["q"] * 480)), 1, ch, int(e["m"]), int(e["vel"])))
        ev.append((int(round((e["q"] + e["beat_dur"]) * 480)), 0, ch, int(e["m"]), 0))
    tm_inv = []
    for b in X.pedal_changes(info["chords"]):
        tm_inv += [(int(round(b * 480)) + 10, 2, 0, 64, 0), (int(round(b * 480)) + 40, 3, 0, 64, 127)]
    ev += tm_inv
    ev.sort(key=lambda e: (e[0], e[1]))
    last = 0
    for t, kind, ch, m, v in ev:
        if kind in (2, 3):
            tr.append(mido.Message("control_change", channel=ch, control=64, value=v, time=t - last))
        else:
            tr.append(mido.Message("note_on" if kind else "note_off", channel=ch, note=m, velocity=v, time=t - last))
        last = t
    mf.save(str(path))


def melody_rows(info):
    rows = []
    for part, plan, modern in (("verse", X.VERSE_PLAN, MODERN_G_VERSE), ("chorus", X.CHORUS_PLAN, MODERN_G_CHORUS)):
        bars = info["plans"][part]
        for (bar, src, why), (_, _, notes) in zip(plan, bars):
            used = " ".join(f"{nm(m) if m is not None else 'R'}/{d:g}" for m, d in notes)
            s1857 = (X.VERSE_1857 if part == "verse" else X.CHORUS_1857)[bar]
            s1913 = " ".join(f"{nm(m) if m is not None else 'R'}/{d:g}" for m, d in X.H1913[(0 if part == "verse" else 16) + bar - 1])
            mod = modern.get(bar, "")
            mod_bb = " ".join(f"{nm(m + 3) if m is not None else 'R'}/{d:g}" for m, d in X.parse(mod)) if mod else ""
            rows.append(dict(part=part, bar_2_4=bar, source_used=src, used_in_Bb=used,
                             source_1857_in_Ab=s1857, source_1913_in_G=s1913,
                             modern_common_form_in_Bb_if_different=mod_bb, note=why))
    return rows


def pedal_overlaps(info):
    """ペダルで鳴り続ける伴奏の音と、旋律の音が半音でぶつかる時間 (秒)。書いた長さでなく、実際に鳴る長さで見る"""
    mel = [e for e in info["events"] if e["role"] == "mel"]
    acc = [e for e in info["events"] if e["role"] != "mel"]
    out = []
    for a in mel:
        a_end = a["sound_end"]
        for b in acc:
            if (a["m"] - b["m"]) % 12 in (1, 11):
                ov = min(a_end, b["sound_end"]) - max(a["t"], b["t"])
                if ov > 0.05:
                    out.append(dict(time_s=round(max(a["t"], b["t"]), 2), beat=round(max(a["q"], b["q"]), 2),
                                    melody=nm(a["m"]), accomp=nm(b["m"]), overlap_s=round(ov, 2),
                                    interval_semitones=abs(a["m"] - b["m"])))
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dsp.set_tuning(440.0)
    ff = V.ffmpeg_exe()
    x, info = X.render()
    slug = X.SLUG
    wav = OUT / f"{slug}.wav"
    write_wav24(wav, x)
    subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "flac", str(OUT / f"{slug}.flac")], check=True)
    subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "320k",
                    str(OUT / f"{slug}.mp3")], check=True)
    r = qa(x, info, wav)
    wav.unlink()
    r["tuning"] = "A=440 Hz を基準に平均律で鳴らす。録音そのものの調律の差 (A4 で約 +1 cent、A5 で約 +7 cent) は残る"
    r["render_sample_rate_hz"] = dsp.SR
    r["sample_source_rate_hz"] = "44100 (Salamander の 44.1kHz/16bit 版。読み込み時にレートを確かめ、変換しない)"
    r["export"] = "FLAC 44.1kHz/24bit ステレオ、MP3 320kbps"
    r["tempo_bpm"], r["time_signature"], r["key"] = X.BPM, "4/4 (出典は 2/4。2/4 の 2 小節を 4/4 の 1 小節にした)", "B♭ major"
    r["tempo_note"] = "♩=72 を基準に、句の終わりで 5%、最後の 3 小節で 12〜35% ゆっくりにする (tempo_map)"
    r["loudness_note"] = (f"リミッターなし。True Peak が -1 dB を超えない範囲のゲイン ({info['gain_db']:+.2f} dB) だけかけた。"
                          "-14 LUFS まで上げるとピークを潰すことになるので、ピアノの強弱を優先した")
    r["melody_vs_accompaniment"] = info["melody_vs_rest_db"]
    r["pedal_sustained_semitone_overlaps"] = pedal_overlaps(info)
    r["pedal_changes_s"] = info["pedal_changes_s"]
    r["final_pedal_release_s"] = info["pedal_lifts_s"][-1]
    r["end_music_s"] = round(info["end_music_s"], 2)
    r["velocity_layers_used"] = sorted({s[:-4].split("v")[-1] for s in info["samples_used"]}, key=int)
    r["notes"] = {"melody": sum(e["role"] == "mel" for e in info["events"]),
                  "accompaniment": sum(e["role"] != "mel" for e in info["events"])}
    r["velocity_percentiles_5_50_95"] = {
        "melody": [int(v) for v in np.percentile([e["vel"] for e in info["events"] if e["role"] == "mel"], [5, 50, 95])],
        "accompaniment": [int(v) for v in np.percentile([e["vel"] for e in info["events"] if e["role"] != "mel"], [5, 50, 95])]}
    r["end_ring_s"] = "最後の和音を約 6 秒鳴らしてからペダルを上げ、ダンパーと残響で消える (最後の 0.3 秒だけフェード)"
    write_midi(OUT / f"{slug}_score.mid", info)
    (OUT / f"{slug}_qa.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")

    with open(OUT / "x05r_v2_transcription_1857.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pdf_page", "system", "bar_2_4", "notes_sounding_pitch_Ab_major", "confidence", "remark"])
        for row in X.SOURCE_1857_AB:
            w.writerow(row)
    rows = melody_rows(info)
    with open(OUT / "x05r_v2_melody_sources.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "x05r_v2_performance.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["onset_s", "beat", "written_beats", "note", "midi", "velocity", "role", "section",
                    "key_up_s", "damper_s"])
        for e in sorted(info["events"], key=lambda e: e["t"]):
            w.writerow([round(e["t"], 3), round(e["q"], 3), e["beat_dur"], nm(e["m"]), e["m"], e["vel"], e["role"],
                        e["sec"], round(e["key_up"], 3), round(e["sound_end"], 3)])
    # Shorts の区間の候補 (音声の切り出しは、試聴版の承認の後)。始まりは旋律の最初の打鍵の 0.06 秒前
    tm = info["tm"]
    cues = [
        ("cue1_verse_end_to_chorus", 32, 56, 0.6,
         "ヴァース最後の句 (What fun it is to ride…) からサビ前半。サビ前半の終わり (sleigh、F7sus4) で止め、"
         "次の Jingle bells の打鍵の前で切る。Shorts でくり返すと属和音から主和音の頭へ戻る"),
        ("cue2_chorus_second_half_to_end", 56, None, 2.0,
         "サビ後半の Jingle bells から始め、終わりの動機・E♭m6・最後の B♭ の和音まで。最後の和音の響きの中で 2 秒フェード"),
    ]
    with open(OUT / "x05r_v2_shorts_cues.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cue", "start_s", "end_s", "length_s", "start_beat", "end_beat", "fade_in_s", "fade_out_s", "why"])
        for name, b0, b1, fo, why in cues:
            s0 = round(tm(b0) - 0.06, 2)
            s1 = round(tm(b1) - 0.06, 2) if b1 is not None else round(info["pedal_lifts_s"][-1] - 1.0, 2)
            w.writerow([name, s0, s1, round(s1 - s0, 2), b0, b1 if b1 is not None else "最後の和音", 0.01, fo, why])
    print(json.dumps({k: v for k, v in r.items() if k not in ("rms_db_per_0_25s", "pedal_changes_s")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
