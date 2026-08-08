#!/usr/bin/env python3
"""
書き出した動画の検証。

「2時間以上あること」「音量が規定どおりであること」
「ループの継ぎ目が知覚できないレベルであること」を機械的に確認する。

    python3 verify_output.py
"""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from bgm_studio import dsp, video as VID  # noqa: E402

OUT = Path("out")
MIN_SECONDS = 2 * 3600          # 要件: 2時間以上


def read_wav24(path: Path, max_seconds: float | None = None) -> np.ndarray:
    """24bit WAV を float32 stereo として読む"""
    with wave.open(str(path), "rb") as w:
        n = w.getnframes()
        sw = w.getsampwidth()
        ch = w.getnchannels()
        if max_seconds:
            n = min(n, int(max_seconds * w.getframerate()))
        raw = w.readframes(n)
    if sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        # 24bit little-endian → int32 に符号拡張
        v = (b[:, 0].astype(np.int32)
             | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v & 0x800000, v - 0x1000000, v)
        x = v.astype(np.float32) / 8388608.0
    elif sw == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    else:
        raise ValueError(f"unsupported sample width: {sw}")
    return x.reshape(-1, ch)


def main() -> int:
    report_path = OUT / "report.json"
    videos = sorted((OUT / "video").glob("*.mp4"))
    audios = sorted((OUT / "audio").glob("*.wav"))

    if not videos and not audios:
        print("out/ に出力がありません。先に render_bgm.py を実行してください。")
        return 2

    print(f"{'トラック':30s} {'長さ':>9s} {'サイズ':>8s} {'LUFS':>7s} "
          f"{'TP':>6s} {'継ぎ目':>8s} {'絶対':>9s}  判定")
    print("─" * 100)

    rows = []
    ok_all = True
    for wav in audios:
        slug = wav.stem
        mp4 = OUT / "video" / f"{slug}.mp4"

        row = {"slug": slug}
        problems = []

        # ── 音源そのものを読み直して測る ──────────────────
        audio = read_wav24(wav)
        row["lufs"] = dsp.lufs_integrated(audio)
        row["true_peak_db"] = dsp.true_peak_db(audio)
        row["loop_seam_db"] = dsp.check_loop_seam(audio)
        row["seam_dbfs"] = dsp.seam_step_dbfs(audio)
        row["loop_seconds"] = audio.shape[0] / dsp.SR
        del audio

        if abs(row["lufs"] + 14.0) > 1.0:
            problems.append(f"LUFS {row['lufs']:.1f}")
        if row["true_peak_db"] > -0.9:
            problems.append(f"TP {row['true_peak_db']:.2f}")
        # 継ぎ目: 相対 0dB 以下、または絶対 -40dBFS 以下なら知覚されない
        if row["loop_seam_db"] > 0.0 and row["seam_dbfs"] > -40.0:
            problems.append(f"継ぎ目 {row['loop_seam_db']:+.1f}dB")

        # ── 動画 ──────────────────────────────────────────
        if mp4.exists():
            pr = VID.probe(mp4)
            row["duration_s"] = pr.get("duration_s", 0.0)
            row["size_mb"] = pr.get("size_mb", 0.0)
            row["streams"] = pr.get("streams", [])
            if row["duration_s"] < MIN_SECONDS:
                problems.append(f"尺不足 {VID.hhmmss(row['duration_s'])}")
            kinds = {s.get("type") for s in row["streams"]}
            if not {"video", "audio"} <= kinds:
                problems.append("ストリーム欠落")
        else:
            row["duration_s"] = 0.0
            row["size_mb"] = 0.0
            problems.append("動画なし")

        row["problems"] = problems
        ok = not problems
        ok_all &= ok
        rows.append(row)

        print(f"{slug:30s} {VID.hhmmss(row['duration_s']):>9s} "
              f"{row['size_mb']:7.0f}M {row['lufs']:7.2f} {row['true_peak_db']:6.2f} "
              f"{row['loop_seam_db']:+7.1f}dB {row['seam_dbfs']:8.1f}dB  "
              f"{'OK' if ok else '⚠ ' + ' / '.join(problems)}")

    print("─" * 100)
    total_h = sum(r["duration_s"] for r in rows) / 3600.0
    print(f"{len(rows)} 本 / 合計 {total_h:.1f} 時間 / "
          f"{sum(r['size_mb'] for r in rows) / 1000:.1f} GB")
    print(f"判定: {'全て合格' if ok_all else '要確認あり'}")

    (OUT / "verify.json").write_text(
        json.dumps({"min_seconds": MIN_SECONDS, "tracks": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"詳細を {OUT / 'verify.json'} に書き出しました。")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
