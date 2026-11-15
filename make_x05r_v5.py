#!/usr/bin/env python3
"""
x05r Jingle Bells の 60〜90 秒の試作 v5 (合格した v4 に柔らかいそり鈴を足した比較版) を作り、自己検収する。2026-11-15。
v4 (make_x05r_v4.py、out/release_2026-11-15c/) はオーナーが合格とした。鈴の入れ方は bgm_studio/x05r_v5.py の冒頭。

    python3 prepare_salamander.py --variant 48k24      # 初回だけ (約 1.2 GB)
    python3 prepare_vcsl_sleigh.py                     # 初回だけ (そり鈴、約 3 MB)
    PYTHONHASHSEED=0 python3 make_x05r_v5.py

出力 (out/release_2026-11-15d/、Genspark の指示書の 4 点セット)
  x05r_60s.flac        44.1kHz / 24bit / ステレオ
  x05r_60s.mp3         同じ内容、320 kbps
  x05r_provenance.md   出典・採譜表・差分表・音源とライセンス・サンプルレート・再現方法・ハッシュ
  x05r_qa.json         自己検収の実測値
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio import dsp, grand, video as V                  # noqa: E402
from bgm_studio import x05r_v2 as V2                            # noqa: E402
from bgm_studio import x05r_v5 as X                             # noqa: E402
from make_orig01 import write_wav24, clicks                     # noqa: E402
from qa_check import octave_bands, BELLS_BAND_WINDOW as PURE_PIANO_BAND_WINDOW   # noqa: E402  (鈴入りなので鈴の曲の目安)

OUT = ROOT / "out" / "release_2026-11-15d"
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

# 1857 年版の歌詞と音の対応 (休符を除いた音の順)。ヴァースは 1 番と 2 番、サビは 1 つ。
# "〃" はスラーで前の音節を伸ばす。"—" はその番に歌詞がない音
SYLLABLES = {
    ("verse", 0): (["—"], ["A"]),
    ("verse", 1): (["Dash-", "ing", "thro'", "the"], ["day", "or", "two", "a-"]),
    ("verse", 2): (["snow,", "In", "a"], ["go,", "I", "〃"]),
    ("verse", 3): (["one", "horse", "o-", "pen"], ["tho't", "I'd", "take", "a"]),
    ("verse", 4): (["sleigh,", "〃"], ["ride", "And"]),
    ("verse", 5): (["O'er", "the", "hills", "we"], ["soon", "miss", "Fan-", "nie"]),
    ("verse", 6): (["go,", "〃"], ["Bright", "Was"]),
    ("verse", 7): (["Laugh-", "ing", "all", "the"], ["seat-", "ed", "by", "my"]),
    ("verse", 8): (["way;", "— (未確認)"], ["side,", "The"]),
    ("verse", 9): (["Bells", "on", "bob", "tail"], ["horse", "was", "lean", "and"]),
    ("verse", 10): (["ring,", "〃"], ["lank", "Mis-"]),
    ("verse", 11): (["Mak-", "ing", "spir-", "its"], ["for-", "tune", "seem'd", "his"]),
    ("verse", 12): (["bright,", "〃"], ["lot", "He"]),
    ("verse", 13): (["Oh", "what", "sport", "to"], ["got", "in-", "to", "a"]),
    ("verse", 14): (["ride", "and", "sing", "A"], ["drift-", "ed", "bank", "And"]),
    ("verse", 15): (["sleigh-", "ing", "song", "to"], ["we—", "we", "got", "up"]),
    ("verse", 16): (["night."], ["sot."]),
    ("chorus", 1): (["Jin-", "gle", "bells,"], None), ("chorus", 2): (["Jin-", "gle", "bells,"], None),
    ("chorus", 3): (["Jin-", "gle", "all", "the"], None), ("chorus", 4): (["way;"], None),
    ("chorus", 5): (["Oh!", "what", "joy", "it"], None), ("chorus", 6): (["is", "to", "ride", "In", "a"], None),
    ("chorus", 7): (["one", "horse", "o-", "pen"], None), ("chorus", 8): (["sleigh."], None),
    ("chorus", 9): (["Jin-", "gle", "bells,"], None), ("chorus", 10): (["Jin-", "gle", "bells,"], None),
    ("chorus", 11): (["Jin-", "gle", "all", "the"], None), ("chorus", 12): (["way,"], None),
    ("chorus", 13): (["Oh!", "what", "joy", "it"], None), ("chorus", 14): (["is", "to", "ride", "In", "a"], None),
    ("chorus", 15): (["one", "horse", "o-", "pen"], None), ("chorus", 16): (["sleigh."], None),
}

# 今の一般的な形 (ト長調、2/4 の小節ごとの音の高さの並び。同じ音の連続は 1 つにまとめる)。
# Claude が書いた参照で、特定の出版物ではない。リズムは比べない
MODERN_G = {
    "verse": ["D B A G", "D", "D B A G", "E", "E C B A", "F#", "D C A", "B",
              "D B A G", "D", "D B A G", "E", "E C B A", "D", "E D C A", "G"],
    "chorus": ["B", "B", "B D G A", "B", "C", "C B", "B A B", "A D",
               "B", "B", "B D G A", "B", "C", "C B", "D C A", "G"],
}


def nm(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def pcs_collapsed(notes, shift):
    out = []
    for m, d in notes:
        if m is None:
            continue
        n = NAMES[(m + shift) % 12]
        if not out or out[-1] != n:
            out.append(n)
    return " ".join(out)


def ffprobe(path):
    ff = V.ffmpeg_exe()
    probe = str(Path(ff).with_name("ffprobe"))
    if not Path(probe).exists():
        probe = "ffprobe"
    try:
        o = subprocess.run([probe, "-v", "error", "-show_entries",
                            "stream=sample_rate,channels,bits_per_raw_sample,sample_fmt,bit_rate,codec_name",
                            "-show_entries", "format=duration", "-of", "json", str(path)],
                           capture_output=True, text=True, check=True).stdout
        return json.loads(o)
    except Exception as e:                                   # ffprobe が無い環境
        return {"error": str(e)}


def decode(path, sr=dsp.SR):
    ff = V.ffmpeg_exe()
    raw = subprocess.run([ff, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


def ebur128(path):
    ff = V.ffmpeg_exe()
    e = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    s = e[e.rfind("Summary:"):]
    out = {}
    for k, pat in (("I_lufs", r"I:\s+(-?[\d.]+) LUFS"), ("LRA_lu", r"LRA:\s+(-?[\d.]+) LU"),
                   ("true_peak_dbfs", r"Peak:\s+(-?[\d.]+) dBFS")):
        m = re.search(pat, s)
        out[k] = float(m.group(1)) if m else None
    return out


def f0(x, m, sr=dsp.SR, start=0.15):
    x = x.mean(1)[int(start * sr):int(start * sr) + 32768].astype(np.float64)
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x)), 8 * len(x)))
    f = np.fft.rfftfreq(8 * len(x), 1 / sr)
    t = 440 * 2 ** ((m - 69) / 12)
    sel = (f > t * 2 ** (-2 / 12)) & (f < t * 2 ** (1 / 12))
    i = int(np.argmax(sp * sel))
    a, b, c = np.log(sp[i - 1:i + 2] + 1e-20)
    p = 0.5 * (a - c) / (a - 2 * b + c)
    fr = (i + p) * (f[1] - f[0])
    return fr, 1200 * np.log2(fr / t)


def silences(x, until_s, thr_db=-55.0, min_s=0.45, hop_s=0.01):
    """-55 dBFS 以下が min_s 秒以上続く所 (until_s より前だけ。末尾の減衰は除く)。10 ms ごとの RMS (左右の大きい方)"""
    h = int(hop_s * dsp.SR)
    n = len(x) // h
    r = np.sqrt((x[: n * h].reshape(n, h, 2) ** 2).mean(axis=1)).max(axis=1)
    db = 20 * np.log10(r + 1e-12)
    out, start = [], None
    for i, v in enumerate(db):
        t = i * hop_s
        if v < thr_db and t < until_s:
            start = t if start is None else start
        else:
            if start is not None and t - start >= min_s:
                out.append([round(start, 2), round(t, 2)])
            start = None
    return out


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def reference_tone(tmp: Path):
    """A=440 の基準音：同じピアノ・同じ経路 (48k/24bit → 44.1k、1 回の再サンプリング) で A4 を鳴らし、FLAC に書いて読み直して測る"""
    p = grand.Grand("48k24")
    out = []
    for vel in (40, 62):
        y = p.strike(69, vel, 3.0)
        wav, fl = tmp / f"a4_{vel}.wav", tmp / f"a4_{vel}.flac"
        write_wav24(wav, y / max(1e-9, np.abs(y).max()) * 0.5)
        subprocess.run([V.ffmpeg_exe(), "-y", "-v", "error", "-i", str(wav), "-c:a", "flac", str(fl)], check=True)
        fr, c = f0(decode(fl), 69)
        out.append({"note": "A4", "velocity": vel, "expected_hz": 440.0, "measured_hz": round(fr, 3), "cents": round(c, 2),
                    })
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dsp.set_tuning(440.0)
    ff = V.ffmpeg_exe()
    x, info = X.render()
    flac, mp3 = OUT / "x05r_60s.flac", OUT / "x05r_60s.mp3"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        wav = td / "x05r_60s.wav"
        write_wav24(wav, x)
        subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "flac", "-sample_fmt", "s32", str(flac)], check=True)
        subprocess.run([ff, "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "320k", str(mp3)], check=True)
        ref = reference_tone(td)

    # ---- 検収 (書き出したファイルを読み直して測る) ----
    xf = decode(flac)
    xm = decode(mp3)
    pf, pm = ffprobe(flac), ffprobe(mp3)
    ef, em = ebur128(flac), ebur128(mp3)
    dur = len(xf) / dsp.SR
    final_damper = info["pedal_lifts_s"][-1]
    on = np.array(info["onsets"])
    cand = clicks(xf)
    raw_isolated = [round(c, 3) for c in cand if np.min(np.abs(on - c)) > 0.015]
    # 段差の大きさが -90 dBFS 未満のもの (24 bit の最小単位付近の量子化。曲の最後で無音になる所に出る) は数えない
    d2 = np.abs(np.diff(xf.mean(axis=1).astype(np.float64), n=2))
    lvl = {c: round(float(20 * np.log10(d2[max(0, int(c * dsp.SR) - 2): int(c * dsp.SR) + 3].max() + 1e-12)), 1)
           for c in raw_isolated}
    isolated = [c for c in raw_isolated if lvl[c] >= -90.0]
    # 実効サンプルレート：基準音の高さから逆算する (48k を 44.1k として読むと -147 cent = レートが 8.8% ずれる)
    eff = [round(float(dsp.SR * 2 ** (-r["cents"] / 1200)), 1) for r in ref]
    hop = dsp.SR
    mono = xf.mean(axis=1).astype(np.float64)
    db1 = 20 * np.log10(np.sqrt((mono[: len(mono) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-12)
    jumps = [(i, round(float(db1[i] - db1[i - 1]), 1)) for i in range(1, len(db1)) if db1[i] - db1[i - 1] > 6.0]
    bands = {k: round(float(v), 1) for k, v in octave_bands(xf.mean(axis=1)).items()}
    clash = []
    for s, d, m, sec in info["mel"]:
        for a0, ad, am, _ in info["acc"]:
            if a0 < s + d and s < a0 + ad and (m - am) % 12 in (1, 11):
                clash.append({"time_s": round(info["tm"](max(s, a0)), 2), "beat": round(max(s, a0), 2),
                              "melody": nm(m), "accomp": nm(am)})
    mp3_corr = float(np.corrcoef(xf[: min(len(xf), len(xm))].ravel(), xm[: min(len(xf), len(xm))].ravel())[0, 1])
    sil = silences(xf, final_damper)
    # 旋律の照合：ヴァースとサビは v2 と同じ (verify_x05r_v2.py で 32 小節を採譜の文字列と照合済み)、前奏は 1913 年版のサビ 1〜4 小節 +3 半音
    sys.argv = [sys.argv[0], "--out", str(Path(tempfile.gettempdir()) / "x05r_v3_verify")]
    import verify_x05r_v2 as VV
    n3, c3, _, _ = X.build()
    exp_ = VV.expected()
    # サビ 7 小節目はオーナーの指示で 4 つ目の音を今の一般的な形 (B) に変えたので、期待値もそのように置き換える
    exp_ = [(p_, b_, s_, [(V2.nn(nn_) + 3, d_) for nn_, d_ in X.OPEN_FIX_G]) if (p_ == "chorus" and b_ == X.OPEN_FIX_BAR) else (p_, b_, s_, e_)
            for p_, b_, s_, e_ in exp_]
    body_ok = all(VV.norm(e) == VV.norm(g) for (_, _, _, e), g in zip(exp_, VV.produced(n3, c3)))
    intro = [(q, m) for q, d, m, role, sec in n3 if role == "mel" and sec == "intro"]
    want = [(m + 3, d) for hb in V2.H1913[16:20] for m, d in hb if m is not None]
    # 制作データ (X.build) は変ロ長調。書き出しは +2 半音 (ハ長調)
    intro_ok = [m for _, m in intro] == [m for m, _ in want]
    qa = {
        "file": "x05r_60s.flac",
        "duration_s": round(dur, 3),
        "sample_rate": {
            "declared_flac_header_hz": int(pf["streams"][0]["sample_rate"]) if "streams" in pf else None,
            "declared_mp3_header_hz": int(pm["streams"][0]["sample_rate"]) if "streams" in pm else None,
            "flac_bits": pf["streams"][0].get("bits_per_raw_sample") if "streams" in pf else None,
            "flac_channels": pf["streams"][0].get("channels") if "streams" in pf else None,
            "effective_hz_from_reference_tone": eff,
            "effective_vs_declared_percent": [round(float(100 * (e / dsp.SR - 1)), 3) for e in eff],
            "criterion": "差 0.5% 未満",
            "pass": all(abs(e / dsp.SR - 1) < 0.005 for e in eff),
            "note": "基準音の高さのずれをすべてレートの誤差とみなした上限値。実際には録音のピアノ自体の調律 (A4 で約 +1 cent) を含む",
        },
        "integrated_lufs": {"ffmpeg_flac": ef["I_lufs"], "ffmpeg_mp3": em["I_lufs"],
                            "internal": round(dsp.lufs_integrated(xf), 2), "criterion": "-14±1 (目安。合格の根拠にしない)",
                            "within": ef["I_lufs"] is not None and abs(ef["I_lufs"] + 14) <= 1.0},
        "loudness_range_lu": ef["LRA_lu"],
        "true_peak": {"ffmpeg_flac_dbtp": ef["true_peak_dbfs"], "ffmpeg_mp3_dbtp": em["true_peak_dbfs"],
                      "internal_4x_dbtp": round(dsp.true_peak_db(xf), 2), "criterion": "-1.0 dBTP 以下",
                      "pass": ef["true_peak_dbfs"] is not None and ef["true_peak_dbfs"] <= -1.0
                      and em["true_peak_dbfs"] is not None and em["true_peak_dbfs"] <= -1.0},
        "clipping": {"samples_abs_ge_0_9999_flac": int((np.abs(xf) >= 0.9999).sum()),
                     "samples_abs_ge_0_9999_mp3": int((np.abs(xm) >= 0.9999).sum()), "criterion": "0"},
        "isolated_clicks": {"count": len(isolated), "times_s": isolated,
                            "method": "2 階差分が周りより 18 dB 以上大きい所のうち、打鍵の時刻から 15 ms より離れたもの。"
                                      "段差の大きさが -90 dBFS 未満のもの (24 bit の最小単位付近の量子化) は数えない",
                            "raw_detections_before_level_floor": [{"time_s": c, "step_dbfs": lvl[c]} for c in raw_isolated],
                            "criterion": "0"},
        "silence_inside_song": {"runs_s": sil, "count": len(sil),
                                "method": "10 ms ごとの RMS (左右の大きい方) が -55 dBFS 以下で 0.45 秒以上続く所。最後のペダルを上げた時刻より前だけを見る",
                                "end_of_song_damper_s": round(final_damper, 2), "criterion": "0 (末尾の減衰・余韻は可)"},
        "reference_pitch": {"declared": "A4 = 440 Hz、平均律", "measurements": ref, "criterion": "±10 cent 以内",
                            "pass": all(abs(r["cents"]) <= 10 for r in ref)},
        "melody_matches_sources": {"verse_and_chorus_32_bars": body_ok, "intro_4_bars_vs_1913_chorus_1_4": intro_ok,
                                   "method": "採譜の文字列 (1857 年版 +2 半音、1913 年版 +3 半音) だけから期待される旋律を作り、制作データ (変ロ長調で組んだもの) と小節ごとに比べた。サビ 7 小節目はオーナーの指示による 1 音の変更を期待値に入れた。書き出しはさらに +2 半音でハ長調",
                                   "editorial_change": "サビ 7 小節目 (2/4) の 4 つ目の音：1908/1913 年版 G (ト長調) → 今の一般的な形 B。ハ長調では E5 (版のままなら C5)"},
        "loop": "ループ納品ではない (最後は余韻で消える)。継ぎ目の確認用の切り出しは不要",
        "limiter": info["limiter"],
        "loudness_jumps_over_6db_per_1s": jumps,
        "bands_db_rel_250_500": bands,
        "band_window_BELLS": {str(k): v for k, v in PURE_PIANO_BAND_WINDOW.items()},
        "band_issues_BELLS_window": [f"{k}: {bands[k]}" for k, (lo, hi) in PURE_PIANO_BAND_WINDOW.items() if not lo <= bands[k] <= hi],
        "sleigh_bells": {k: v for k, v in info["layers"].items() if k != "onsets"},
        "melody_accomp_semitone_overlaps": clash,
        "melody_vs_accompaniment": info["melody_vs_rest_db"],
        "lowest_note": nm(info["lowest_note"]),
        "section_times_s": info["section_times"],
        "mp3_vs_flac_correlation": round(mp3_corr, 6),
        "piano": {"name": "Salamander Grand Piano V3 (Yamaha C5)", "variant": "48kHz/24bit 原本",
                  "velocity_layers_in_library": 16,
                  "layers_used": sorted({s[:-4].split("v")[-1] for s in info["samples_used"]}, key=int),
                  "release_samples": "弦共鳴リリース (harmS/harmL) とハンマーノイズ (rel) を使用",
                  "sustain_pedal": "和音が変わるたびに踏み替え (時刻は pedal_changes_s)"},
        "resampling": {"per_note": "1 回 (音の高さ合わせと 48k→44.1k を同時に)", "unique_resample_operations": info["resample_calls"],
                       "prepare_stage": "なし (配布された 48kHz/24bit の WAV をそのまま読む)", "export_stage": "なし (44.1kHz で書き出し)"},
        "pedal_changes_s": info["pedal_changes_s"],
        "machine_checked": "上の数値すべて",
        "not_listened_by_human": ["鈴の大きさ (柔らかく聞こえるか・ピアノを邪魔しないか)", "鈴の音色 (耳に刺さらないか)", "鈴を入れる場所 (ヴァース後半とサビ) と、前奏・最後の和音の振り",
                                  "副旋律 (旋律の下の音・伴奏) が小さくなったか", "明るく聞こえるか", "テンポ ♩=84 の速さ",
                                  "46 秒付近 (のばした音の後の句の入り) で急に大きく感じないか", "コンプレッサーの効き (最大の下げ幅は limiter.compressor)",
                                  "打鍵の自然さ", "低音の濁り", "ペダルの濁り・切れ", "終わりの余韻"],
        "self_judgement_of_tone": "しない (指示書のとおり)",
    }
    (OUT / "x05r_qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=1), encoding="utf-8")
    write_provenance(info, qa, flac, mp3)
    print(json.dumps({k: qa[k] for k in ("duration_s", "sample_rate", "integrated_lufs", "loudness_range_lu", "true_peak",
                                          "clipping", "isolated_clicks", "silence_inside_song", "reference_pitch", "limiter",
                                          "loudness_jumps_over_6db_per_1s", "bands_db_rel_250_500",
                                          "melody_accomp_semitone_overlaps", "melody_vs_accompaniment", "section_times_s")},
                     ensure_ascii=False, indent=1))
    return 0


def write_provenance(info, qa, flac, mp3):
    L = []
    w = L.append
    secs = dict(info["section_times"])
    w("# x05r Jingle Bells：60〜90 秒の試作 v5・鈴入り（出典と制作の記録）\n")
    w("作成：2026-11-15（Claude）。Genspark の指示書「Claudeへ貼る指示文（x05r Jingle Bells／2026-11-15）」への回答の 3 回目。")
    w("**v4 はオーナーが合格とした。v5 は、そのピアノに柔らかいそり鈴を足した比較版**（オーナー：「もっと求めるなら、鈴の音も柔らかく入れて下さい」）。"
      "ピアノの部分（打鍵・強さ・ペダル・和音・旋律）は v4 と同じ。\n")
    sb = info["layers"]
    w("## 00. 鈴の入れ方（v5 で足したもの）\n")
    w("| 部分 | 鈴 |\n|---|---|")
    w("| 前奏の頭 | 軽く 1 回振る（約 2 秒で消える） |")
    w("| ヴァース前半 | なし |")
    w("| ヴァース後半 | 4/4 の 2・4 拍目だけ |")
    w("| サビ | 毎拍。2・4 拍目を基準に、1・3 拍目は 4 dB 弱く。最後の 2 小節（2/4）で少しずつ弱く |")
    w("| 最後の和音 | 振り続ける音を小さく重ね、約 3 秒で消す |\n")
    w(f"- 回数：振る音 {sb['n_hits']} 回、振り続ける音 {sb['n_shakes']} 回")
    w(f"- 大きさ：鈴だけの音量を、ピアノだけの音量より {sb['bells_below_piano_db']:.0f} dB 小さくした（残響の前で、ピアノ {sb['piano_lufs_before_reverb']} LUFS、鈴 {sb['bells_lufs_before_reverb']} LUFS）")
    w(f"- 柔らかくするために：{sb['lowpass_hz']} Hz より上を丸めた。2 種類の録音の中から、音の重心が低い方（約 7 kHz）を使った。打つ瞬間を 4 ms でなめらかにした。左右は少し右寄り")
    w("- 参考にしたもの：この曲の鈴の入った演奏でよく使われる形（サビで拍に合わせて鳴らす・句の頭で振る）。**Claude は他の動画の音を聞けないので、特定の動画をまねたものではない**")
    w("- 音源：Versilian Community Sample Library（VCSL）のそり鈴の録音（`sleighbell2_hit_2.wav`・`sleighbell2_hit_loud.wav`・`sleighbell2_shake1.wav`）。**CC0 1.0**（商用可・無償・表示も不要）。"
      "44.1 kHz / 24 bit のまま使い、レート変換・音程の変更なし。取得元 https://github.com/sgossner/vcsl（commit c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e）、"
      "原文と sha256 は `data/licenses/vcsl_sleigh_bells/`\n")
    w("制作 ID：`x05r_jingle_bells_piano`（旧 x05 / Mpl70FC93HQ とは別物）。**音色の合否は Claude では判定していません。**\n")
    w("## 0. v3 の試聴判定と、v4 で変えたこと（v5 のピアノも同じ）\n")
    w("オーナーの判定（原文）：音色 不合格（副旋律の音が大きい、音色が暗い）／旋律の大きさ ちょうどよい／テンポ 速く／音量 今の版（-14.5）／"
      "サビの「o-pen」の 1 音 一般的な形に直す／明るい気持ちになるように\n")
    w("| 判定 | v3 | v4・v5 |\n|---|---|---|")
    w("| 副旋律が大きい | サビ全体で旋律の下に 3 度・6 度を重ねた。旋律と伴奏の差 +2.3 dB | サビ前半は重ねない。後半も 8 弱く。伴奏の音量を -2 dB。旋律と伴奏の差 "
      f"{qa['melody_vs_accompaniment']['melody_minus_accompaniment_db']:+.1f} dB |")
    w("| 音色が暗い | 変ロ長調。Gm7・Cm9・Dm7、終わりに E♭m6（同主短調の IV）。高域を -2 dB | **ハ長調**（全体を +2 半音）。長三和音中心（C・F・G7・C7 など）、終わりは F/C → C。高域を下げる補正をやめた。伴奏と低音を強めの段（明るい録音）で弾き、音量は下げた |")
    w("| テンポ | ♩=66 | **♩=84** |")
    w("| 音量 | -14.5 LUFS | 同じく -14 前後（下の 9 節） |")
    w("| 「o-pen」の 1 音 | 1908/1913 年版のまま（ト長調で G） | **今の一般的な形（ト長調で B）に変更**。出典の版とは違う 1 音。ハ長調では E5 |")
    w("| 旋律の大きさ | — | 変えていない（旋律の強さは v3 と同じ） |\n")
    w("## 1. 曲の情報\n")
    w("| 項目 | 内容 |\n|---|---|")
    w("| 曲名 | Jingle Bells（原題 The One Horse Open Sleigh、J. Pierpont 作）— 静かな読書向けのピアノ独奏 |")
    w(f"| 長さ | {qa['duration_s']:.2f} 秒 |")
    w("| 拍子 | 4/4（出典は 2/4。出典の 2 小節を 1 小節にした） |")
    w(f"| テンポ | ♩=84 を基準に、句の終わりで約 4% ゆっくり、最後の 3 小節で 10〜30% ゆっくり（原曲の Allegro より落ち着いた速さ） |")
    w("| 調 | ハ長調（C major）。出典の変イ長調から +4 半音、1908/1913 年版のト長調から +5 半音 |")
    w("| 小節数 | 4/4 で 20 小節（前奏 2・ヴァース 8・サビ 8・終わり 2）＋最後の和音の余韻 |")
    w("| 楽器 | ピアノと、柔らかいそり鈴（効果音・歌声なし） |")
    w("| 基準音 | A4 = 440 Hz、平均律 |\n")
    w("**構成**\n")
    w("| 時刻 | 部分 | 中身 |\n|---|---|---|")
    w(f"| 0:00〜{secs['verse']:.1f} 秒 | 前奏（主題） | サビの頭「Jingle bells, jingle bells, jingle all the way」を静かに。和音は Cadd9 → G/B → C → G6 |")
    w(f"| {secs['verse']:.1f}〜{secs['chorus']:.1f} 秒 | ヴァース | 前半は「低音＋2 音」の 4 分音符、後半は 8 分音符が加わる |")
    w(f"| {secs['chorus']:.1f}〜{secs['coda']:.1f} 秒 | サビ（伴奏の変化） | 左手が 8 分音符の分散和音に変わる。旋律の下に重ねる音は後半だけ、弱く |")
    w(f"| {secs['coda']:.1f} 秒〜終わり | 終止と余韻 | 最初の動機（G E D C）を 1 オクターブ上で → F/C → C の和音を下から分散。約 5 秒鳴らしてからペダルを上げ、音が消えるまで |\n")
    w("**和音**（2/4 の 1 小節ごと、ハ長調。すべて Claude が新しく付けた）\n")
    w("- 前奏：" + " | ".join(X.chord_name_shift(c) for c in X.INTRO_CH))
    w("- ヴァース：" + " | ".join(X.chord_name_shift(c) for c in X.VERSE_CH))
    w("- サビ：" + " | ".join(X.chord_name_shift(c) for c in X.CHORUS_CH))
    w("- 終わり：" + " | ".join(X.chord_name_shift(c) for c in X.CODA_CH) + "\n")
    w("## 2. 音源とライセンス\n")
    w("| 項目 | 内容 |\n|---|---|")
    w("| ピアノ音源 | Salamander Grand Piano V3（作者 Alexander Holm、Yamaha C5、AKG C414 2 本を弦の上約 12 cm に AB 配置） |")
    w("| 版 | 原本 48kHz / 24bit（FreePats `SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz`、sha256 ae30854d2cb686f81dbfae3c0475173838b0053454feb28df0ec425fdc64ad1e） |")
    w("| 仕様 | 強さ 16 段階、短 3 度ごとの録音、弦共鳴のリリース（3 段階）、ハンマーノイズのリリース（半音ごと）、ペダルの音（今回は不使用） |")
    w("| ライセンス | CC BY 3.0（商用可・無償・表示が必要。NC・SA なし）。同梱の README に「Licence: CC-by http://creativecommons.org/licenses/by/3.0/」 |")
    w("| 証拠の保存場所 | `data/licenses/salamander_grand_piano_v3/`（README・sfz・取得ページ・CC BY 3.0 の原文） |")
    w("| そり鈴 | VCSL（Versilian Studios）、CC0 1.0。表示は不要（入れる場合：Sleigh bells: Versilian Community Sample Library (CC0)） |")
    w("| 費用 | 0 円（追加購入・有料プラン・有料 API なし） |\n")
    w("**概要欄に入れるクレジット（必須）**\n")
    w("```\nPiano: Salamander Grand Piano V3 by Alexander Holm (CC BY 3.0)\nhttps://creativecommons.org/licenses/by/3.0/\n```\n")
    w("- 人が弾いた録音ではありません（打鍵の時刻・強さ・ペダルはプログラムで作った）。「real piano」「live」とは書かない。AI 使用の開示は「はい」\n")
    w("## 3. サンプルレートと再サンプリング\n")
    w("| 段階 | サンプルレート | 処理 |\n|---|---|---|")
    w("| 準備（音源） | 48,000 Hz / 24 bit | 配布された WAV をそのまま読む。読み込むたびに WAV のヘッダーが 48 kHz・24 bit かを確かめ、違えば止まる。レート変換なし |")
    w(f"| 描画（レンダー） | 44,100 Hz（`bgm_studio/dsp.SR`） | 1 音につき 1 回だけ再サンプリング：音の高さ合わせ（最大 ±1 半音）と 48k→44.1k を同じ `resample_poly` で同時に行う。ハ長調への移調もこの高さ合わせに含まれる（曲全体を速くして移調してはいない）。異なる（録音・高さ）の組み合わせは {qa['resampling']['unique_resample_operations']} 通り |")
    w("| 書き出し | 44,100 Hz / 24 bit（FLAC）、44,100 Hz（MP3 320 kbps） | レート変換なし |")
    sr_ = qa['sample_rate']
    w(f"| 実測 | FLAC ヘッダー {sr_['declared_flac_header_hz']} Hz、{sr_['flac_bits']} bit、{sr_['flac_channels']} ch | 基準音 A4 の高さから逆算した実効レート " + "・".join(f"{e:.1f}" for e in sr_['effective_hz_from_reference_tone']) + " Hz（宣言値との差 " + "・".join(f"{d:+.3f}" for d in sr_['effective_vs_declared_percent']) + " %。録音のピアノ自体の調律 約 +1 cent を含む上限値） |\n")
    w("- 曲全体を速くしたり遅くしたりして音程を合わせることはしていません")
    w("- 同じ曲を 44.1kHz/16bit 版の音源で鳴らした場合と、単音の高さが 0.01 cent まで一致することを確認しました（48k を 44.1k として読む誤り・二重補正がないことの確認）\n")
    w("## 4. 再現方法\n")
    w("```\ngit checkout claude/youtube-bgm-marketing-strategy-7yy7kq\npython3 prepare_salamander.py --variant 48k24      # 音源の取得と sha256 の確認（約 1.2 GB）\npython3 prepare_vcsl_sleigh.py                     # そり鈴の録音（sha256 を確認）\nPYTHONHASHSEED=0 python3 make_x05r_v5.py           # 4 点セットを out/release_2026-11-15d/ に書き出し、検収する\n```\n")
    w("- コード：`bgm_studio/x05r_v5.py`・`bgm_studio/sleigh.py`（そり鈴）、`bgm_studio/x05r_v4.py`（合格した v4 のピアノ：和音・強さ・テンポ・調・音量）、`bgm_studio/x05r_v3.py`（前奏の主題・リミッター）、`bgm_studio/x05r_v2.py`（採譜・旋律の出典・伴奏の形）、`bgm_studio/grand.py`（ピアノ）")
    w("- 乱数の種は固定（打鍵の揺れ・強さの揺れ）。同じコマンドで同じ音になることを、2 回書き出して確認\n")
    w("**ハッシュ（SHA-256）**\n")
    w(f"- x05r_60s.flac：`{sha256(flac)}`")
    w(f"- x05r_60s.mp3：`{sha256(mp3)}`\n")
    w("## 5. 原典と採譜\n")
    w("**原典**：Johns Hopkins University, Lester S. Levy Sheet Music Collection, Box 062 Item 044")
    w("- 所蔵ページ：https://levysheetmusic.mse.jhu.edu/collection/062/044")
    w("- 譜面 PDF（4 ページ）：https://levysheetmusic.mse.jhu.edu/sites/default/files/collection-pdfs/levy-062-044.pdf（2026-11-15 取得、`data/licenses/x05r_jingle_bells/1857_levy_jhu/levy-062-044.pdf`）")
    w("- 目録：Written and Composed by J. Peirpont（目録の綴り。印刷は J. PIERPONT）／Boston: Oliver Ditson & Co.／1857／plate 18200／piano and voice／strophic with chorus")
    w("- 参照：米国議会図書館 https://www.loc.gov/item/2023812429/ は 403 のまま（取得していない）。同じ版（plate 18200）の議会図書館の画像は Wikimedia Commons 経由で保存済み（`../1857_first_edition_loc/`）\n")
    w("**譜面の様子**（目視）")
    w("- PDF 1 ページ目：表紙。2 ページ目（印刷 p.3）：ピアノの前奏（Allegro、2/4、変イ長調）の後に歌のヴァース。1 番と 2 番の歌詞が上下に印刷されている")
    w("- 3〜4 ページ目（印刷 p.4〜5）：CHORUS。4 声の合唱とピアノ。ここでは最上声を採譜した。最後にピアノの後奏（8va）。3・4 番の歌詞は p.5 に文字だけで印刷")
    w("- 反復記号：見当たらない（有節形式。2〜4 番は同じヴァースをくり返して歌う）")
    w("- 弱起：歌の最初の小節は休符の後、最後の 8 分音符に 2 番の歌詞「A」だけが付く。1 番の歌詞は次の小節の頭から（ここでは小節 0 とした）\n")
    w("**採譜表**（歌声パートのみ。実際の高さ、変イ長調。音価は 4 分音符 = 1）\n")
    w("| PDF ページ | 段 | 小節 | 音（音価） | 1 番の歌詞 | 2 番の歌詞 | 確かさ・備考 |\n|---|---|---|---|---|---|---|")
    for page, sys_, bar, notes, conf, rem in V2.SOURCE_1857_AB:
        part = "verse" if (page == 2) else "chorus"
        syl = SYLLABLES.get((part, bar), (None, None))
        s1 = " ".join(syl[0]) if syl[0] else ""
        s2 = " ".join(syl[1]) if syl[1] else "（サビは歌詞 1 つ）" if part == "chorus" else ""
        mark = "未確認（候補 A♭4。3 つ目の音の位置がかすれている）" if conf == "中" else "確か"
        rem = rem.replace("3 つ目は A♭4 (第 2 間) と読んだ。400 dpi で確認", "400 dpi の画像で見た")
        w(f"| {page} | {sys_} | {('サビ ' if part == 'chorus' else 'ヴァース ') + str(bar)} | {notes} | {s1} | {s2} | {mark}。{rem} |")
    w("\n- 「〃」はスラーで前の音節を伸ばす音。「— (未確認)」は 1 番の歌詞が付いていない音で、1 番で歌うのか休むのかは印刷からは分からない")
    w("- サビ 5 小節目の 3 つ目の音は、400 dpi で見ても A♭4 か B♭4 か確定できなかった。制作にはこの小節を使っていない\n")
    w("## 6. 実際に使った旋律と、今の一般的な形との差分表\n")
    w("比べ方：ト長調にそろえ、各小節（2/4）の音の高さの並びを比べた（同じ音の連続は 1 つにまとめ、リズムは比べない）。"
      "「今の一般的な形」は Claude が書いた参照で、特定の出版物ではありません。\n")
    w("| 部分 | 小節 | 使った版 | 1857 年版 | 1908/1913 年版 | 今の一般的な形 | 差（使った旋律 vs 今の形） |\n|---|---|---|---|---|---|---|")
    for part, plan in (("verse", V2.VERSE_PLAN), ("chorus", V2.CHORUS_PLAN)):
        for (bar, src, why) in plan:
            n1857 = pcs_collapsed(V2.parse((V2.VERSE_1857 if part == "verse" else V2.CHORUS_1857)[bar]), -1)
            n1913 = pcs_collapsed(V2.H1913[(0 if part == "verse" else 16) + bar - 1], 0)
            mod = MODERN_G[part][bar - 1]
            used = n1857 if src == "1857" else n1913
            if part == "chorus" and bar == X.OPEN_FIX_BAR:
                used = pcs_collapsed([(V2.nn(n_), d_) for n_, d_ in X.OPEN_FIX_G], 0)
                src = "1913＋変更"
            diff = "同じ" if used == mod else f"違う（{used} / 今の形 {mod}）"
            w(f"| {'ヴァース' if part == 'verse' else 'サビ'} | {bar} | {src} | {n1857} | {n1913} | {mod} | {diff} |")
    w("\n**差の説明**")
    w("- ヴァース 8 小節目：1857 年版の最後の 8 分音符（D）は 2 番の歌詞「The」の音。版のとおり弾いた")
    w("- サビ 7 小節目「one-horse o-pen」の 4 つ目の音：1908/1913 年版は G、今の一般的な形は B。**オーナーの指示で今の一般的な形（B）に変えた**（ハ長調では E5。版のままなら C5）。この 1 音は保存した出典の版にはなく、Claude が変えた音")
    w("- 1857 年版と今の形が違う所（使わなかった所）：ヴァース 7 小節目（G から 7 度跳び上がる）、ヴァース 14 小節目（G E♭ D♮ E♭）、サビ全体（別の旋律）。この 3 か所は 1908/1913 年版を使った")
    w("- 1908/1913 年版：『The Most Popular Home Songs』（1913）p.54–55、George Rosey 編曲、Copyright 1908 by Hinds, Noble & Eldredge（Internet Archive `mostpopularhomes00nobl`、`data/licenses/x05r_jingle_bells/1913_most_popular_home_songs/`）")
    w("- 照合：採譜の文字列だけから期待される旋律を作り（サビ 7 小節目は上の 1 音の変更を入れて）、制作データと 32 小節すべて一致することを機械で確認。前奏の 4 小節は 1913 年版のサビ 1〜4 小節と同じ\n")
    w("## 7. 権利の分け方\n")
    w("| 層 | 何を使ったか | 状態 |\n|---|---|---|")
    w("| 作曲（旋律） | J. Pierpont、1857 年出版 | 米国でパブリックドメイン（1929 年より前の出版）。米国以外の各国は個別に確認していない |")
    w("| 版（印刷譜）① | 1857 年 Ditson 版（Levy 所蔵）から 42 音 | 米国でパブリックドメイン。所蔵館の画像の利用条件のページ（library.jhu.edu）は Cloudflare の確認画面で取得できず、回避していない。使ったのは画像ではなく、読み取った音の並び |")
    w("| 版（印刷譜）② | 1908/1913 年 Rosey 編曲版から 58 音＋前奏 | 米国でパブリックドメイン（1929 年より前の出版）。米国以外は未確認 |")
    w("| 旋律の 1 音の変更 | サビ 7 小節目の 4 つ目の音を、今の一般的な形に（オーナーの指示） | 版にない 1 音。パブリックドメインの曲の、広く歌われている形に合わせたもの。この形を載せた版は保存していない |")
    w("| 編曲（和声・伴奏・前奏・終わり） | Claude が新しく作った（v4 で付け直した） | 旧 x05 の音源・伴奏、Hardy／England 等の ABC・和音記号・編曲、Rosey の伴奏、既存の録音は使っていない |")
    w("| 録音（音源） | Salamander Grand Piano V3 | CC BY 3.0。クレジットが必要 |")
    w("| 録音（そり鈴） | VCSL の Sleigh Bells | CC0 1.0。表示は不要 |")
    w("| 演奏 | プログラムで作った打鍵・強さ・ペダル | 新しい制作物。AI 使用として開示する |\n")
    w("## 8. 未確認のこと\n")
    w("1. 1908/1913 年版のサビ（1857 年版と違う旋律）が、いつ・誰によって今の形になったか。米国以外の国での扱い")
    w("2. Levy コレクション（JHU）の画像の利用条件（条件のページが Cloudflare の確認画面で取得できなかった）")
    w("3. サビ 7 小節目の変えた 1 音（今の一般的な形）を載せたパブリックドメインの版は、まだ探していない")
    w("4. 1857 年版の 2 か所：サビ 5 小節目の 3 つ目の音（A♭4 か B♭4 か）、ヴァース 8 小節目の 8 分音符を 1 番で歌うか（どちらも制作には影響しない）")
    w("5. 鈴の大きさ・音色・入れる場所、と v4 から引き継いだ点：人の耳で聴いていない（`x05r_qa.json` の not_listened_by_human）\n")
    w("## 9. 機械で確認した項目と、まだ聴いていない項目\n")
    q = qa
    w("| 項目 | 結果 | 基準 |\n|---|---|---|")
    w(f"| サンプルレート | ヘッダー {q['sample_rate']['declared_flac_header_hz']} Hz（MP3 も {q['sample_rate']['declared_mp3_header_hz']} Hz）、実効 " + "・".join(f"{e:.1f}" for e in q['sample_rate']['effective_hz_from_reference_tone']) + " Hz（差 " + "・".join(f"{d:+.3f}" for d in q['sample_rate']['effective_vs_declared_percent']) + " %） | 差 0.5% 未満 |")
    w(f"| Integrated LUFS | FLAC {q['integrated_lufs']['ffmpeg_flac']}、MP3 {q['integrated_lufs']['ffmpeg_mp3']}（ffmpeg）／自前 {q['integrated_lufs']['internal']} | -14±1（目安） |")
    w(f"| True Peak | FLAC {q['true_peak']['ffmpeg_flac_dbtp']} dBTP、MP3 {q['true_peak']['ffmpeg_mp3_dbtp']} dBTP（ffmpeg）／自前 {q['true_peak']['internal_4x_dbtp']} | -1.0 dBTP 以下 |")
    w(f"| クリップ（\\|x\\|≥0.9999） | FLAC {q['clipping']['samples_abs_ge_0_9999_flac']}、MP3 {q['clipping']['samples_abs_ge_0_9999_mp3']} | 0 |")
    raw = q['isolated_clicks']['raw_detections_before_level_floor']
    w(f"| 孤立クリック | {q['isolated_clicks']['count']}" + (f"（検出器の生の結果は {len(raw)} 件：" + "、".join(f"{r['time_s']} 秒・段差 " + ("なし（デジタルの無音の中で検出器が反応したもの）" if r['step_dbfs'] < -200 else f"{r['step_dbfs']} dBFS") for r in raw) + "。曲の最後の無音の所。-90 dBFS 未満の段差は聞こえないので数えない）" if raw else "") + " | 0 |")
    w(f"| 曲中の無音（-55 dBFS が 0.45 秒以上） | {q['silence_inside_song']['count']} | 0（末尾の余韻は可） |")
    w(f"| 基準音 A4 | " + "、".join(f"{r['measured_hz']} Hz（{r['cents']:+.2f} cent、強さ {r['velocity']}）" for r in q['reference_pitch']['measurements']) + " | ±10 cent 以内 |")
    w(f"| ループ・継ぎ目 | ループ納品ではない | — |")
    w(f"| LRA | {q['loudness_range_lu']} LU | （参考） |")
    lim = q["limiter"]
    cp = lim["compressor"]
    w(f"| コンプレッサー（ゆっくり効く、{cp['ratio']}:1） | 最大 {cp['max_reduction_db']} dB 下げた。1 dB を超えて下げた時間 {cp['time_over_1db_s']} 秒 | （参考） |")
    w(f"| リミッター | 最大 {lim['max_gain_reduction_db']} dB、1 dB を超えて圧縮した時間 {lim['time_with_reduction_over_1db_s']} 秒、3 dB 超 {lim['time_with_reduction_over_3db_s']} 秒、天井で切ったサンプル {lim['samples_hard_clipped_at_ceiling']} | （参考） |")
    w(f"| 旋律と伴奏の半音のぶつかり | {len(q['melody_accomp_semitone_overlaps'])} | （参考） |")
    w(f"| 1 秒ごとの音量が 6 dB 以上上がる所 | {len(q['loudness_jumps_over_6db_per_1s'])}" + ("（" + "、".join(f"{t} 秒 +{v} dB" for t, v in q['loudness_jumps_over_6db_per_1s']) + "。のばした音が消えかけた所から次の句へ。聞いて確かめてほしい所）" if q['loudness_jumps_over_6db_per_1s'] else "") + " | （参考） |")
    w(f"| 帯域（250〜500 Hz を 0） | " + " / ".join(f"{k} Hz {v:+.1f}" for k, v in q['bands_db_rel_250_500'].items()) + " | （参考） |")
    w(f"| 旋律と伴奏の音量差 | 旋律が {q['melody_vs_accompaniment']['melody_minus_accompaniment_db']:+.2f} dB（残響の前で測定） | （参考） |\n")
    w("**まだ人の耳で聴いていない項目**：" + "、".join(q["not_listened_by_human"]) + "。音色の合否は Claude では判定していません。")
    (OUT / "x05r_provenance.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
