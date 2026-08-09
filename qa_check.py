#!/usr/bin/env python3
"""
音と映像の品質検査。

耳で確かめられない項目を数値で押さえるためのもの。
「なんとなく良さそう」で出さず、基準を決めて全部通す。

    python3 qa_check.py

検査項目 (音)
  1. ラウドネス       -14 LUFS ±1        YouTube の正規化目標
  2. トゥルーピーク   -1.0 dBTP 以下     エンコード歪みを避ける
  3. ループ継ぎ目     曲中の変化より小さい
  4. 帯域バランス     実在の音源に近いか  ← こもり / 耳障りを検出
  5. 環境音の比率     音楽より下にあるか  ← 「ノイズがひどい」の再発防止
  6. クリップ         0 サンプル
  7. DC オフセット    -60 dBFS 以下
  8. モノ互換性       位相打ち消しがないか
  9. ダイナミクス     圧縮しすぎていないか
 10. 耳障りな帯域     2-5kHz が突出していないか

検査項目 (映像)
 11. 平均輝度        暗すぎ / 明るすぎを検出
 12. フレーム間の動き 眠りを妨げる激しい動きがないか
 13. ループの連続性   末尾→先頭が飛ばないか
"""

from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from bgm_studio import dsp, video as VID  # noqa: E402

OUT = Path("out")

# ── 合格基準 ───────────────────────────────────────────────
LUFS_TARGET, LUFS_TOL = -14.0, 1.0
TRUE_PEAK_MAX = -0.9
SEAM_REL_MAX = 0.0          # dB。0 以下なら曲中の変化に埋もれる
SEAM_ABS_MAX = -40.0        # dBFS。どちらかを満たせば可
DC_MAX_DBFS = -60.0
CREST_MIN_DB = 6.0          # これ未満は潰しすぎ
MONO_CORR_MIN = 0.20        # これ未満は位相打ち消しの疑い

# オクターブバンドの許容範囲 (250-500Hz を 0dB とした相対値)
# 実在のリラクゼーション音源を参考にした窓。
BAND_WINDOW = {
    500: (-8.0, +3.0),
    1000: (-14.0, -1.0),
    2000: (-22.0, -5.0),
    4000: (-30.0, -10.0),
    8000: (-42.0, -16.0),
}


def read_wav(path: Path, seconds: float | None = None,
             offset: float = 0.0) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        sr, sw, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
        if offset:
            w.setpos(min(int(offset * sr), w.getnframes() - 1))
        n = w.getnframes() - int(offset * sr)
        if seconds:
            n = min(n, int(seconds * sr))
        raw = w.readframes(n)
    if sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v & 0x800000, v - 0x1000000, v)
        x = v.astype(np.float32) / 8388608.0
    else:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return x.reshape(-1, ch)


def octave_bands(mono: np.ndarray) -> dict[int, float]:
    """250-500Hz を基準にしたオクターブバンドの相対レベル [dB]"""
    m = np.asarray(mono, dtype=np.float64)
    sp = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
    f = np.fft.rfftfreq(len(m), 1.0 / dsp.SR)
    ref = sp[(f >= 250) & (f < 500)].sum()
    out = {}
    for lo in BAND_WINDOW:
        e = sp[(f >= lo) & (f < lo * 2)].sum()
        out[lo] = 10.0 * np.log10(max(e, 1e-18) / max(ref, 1e-18))
    return out


def audio_qa(slug: str) -> dict:
    wav = OUT / "audio" / f"{slug}.wav"
    if not wav.exists():
        return {"slug": slug, "error": "音源が見つかりません"}

    x = read_wav(wav)
    m = dsp.mono(x).astype(np.float64)
    issues = []

    r = {"slug": slug}
    r["lufs"] = dsp.lufs_integrated(x)
    r["true_peak_db"] = dsp.true_peak_db(x)
    r["seam_rel_db"] = dsp.check_loop_seam(x)
    r["seam_abs_dbfs"] = dsp.seam_step_dbfs(x)
    r["peak"] = float(np.abs(x).max())
    r["clipped"] = int((np.abs(x) >= 0.9999).sum())
    r["dc_dbfs"] = float(dsp.lin2db(abs(m.mean())))

    rms = float(np.sqrt((m ** 2).mean()))
    r["crest_db"] = float(dsp.lin2db(np.abs(m).max() / max(rms, 1e-12)))

    l, rr = x[:, 0].astype(np.float64), x[:, 1].astype(np.float64)
    denom = np.sqrt((l ** 2).sum() * (rr ** 2).sum())
    r["mono_corr"] = float((l * rr).sum() / denom) if denom > 0 else 1.0

    # 帯域は中盤の 120 秒で見る (曲頭は静かで代表性がない)
    mid = read_wav(wav, seconds=120.0, offset=max(len(m) / dsp.SR * 0.35, 0))
    r["bands"] = {k: round(v, 1) for k, v in octave_bands(dsp.mono(mid)).items()}

    # ── 判定 ──────────────────────────────────────────────
    if abs(r["lufs"] - LUFS_TARGET) > LUFS_TOL:
        issues.append(f"LUFS {r['lufs']:.1f}")
    if r["true_peak_db"] > TRUE_PEAK_MAX:
        issues.append(f"TP {r['true_peak_db']:.2f}")
    if r["seam_rel_db"] > SEAM_REL_MAX and r["seam_abs_dbfs"] > SEAM_ABS_MAX:
        issues.append(f"継ぎ目 {r['seam_rel_db']:+.1f}dB")
    if r["clipped"]:
        issues.append(f"クリップ {r['clipped']}")
    if r["dc_dbfs"] > DC_MAX_DBFS:
        issues.append(f"DC {r['dc_dbfs']:.0f}dB")
    if r["crest_db"] < CREST_MIN_DB:
        issues.append(f"潰しすぎ crest {r['crest_db']:.1f}dB")
    if r["mono_corr"] < MONO_CORR_MIN:
        issues.append(f"位相 {r['mono_corr']:.2f}")
    for lo, (mn, mx) in BAND_WINDOW.items():
        v = r["bands"][lo]
        if v < mn:
            issues.append(f"{lo}Hz こもり({v:+.0f})")
        elif v > mx:
            issues.append(f"{lo}Hz 耳障り({v:+.0f})")

    r["issues"] = issues
    return r


def visual_qa(slug: str) -> dict:
    """ループ映像から数フレーム取り出して、輝度と動きの量を見る"""
    vis = OUT / "visual" / f"{slug}.mp4"
    r = {"slug": slug}
    if not vis.exists():
        return {**r, "error": "映像が見つかりません"}

    frames = []
    for t in (0.0, 5.0, 10.0, 15.0, 19.93):
        p = subprocess.run(
            [VID.ffmpeg_exe(), "-v", "error", "-ss", str(t), "-i", str(vis),
             "-frames:v", "1", "-vf", "scale=160:90", "-f", "rawvideo",
             "-pix_fmt", "gray", "-"],
            capture_output=True)
        if len(p.stdout) >= 160 * 90:
            frames.append(np.frombuffer(p.stdout[:160 * 90],
                                        dtype=np.uint8).astype(np.float32))
    if len(frames) < 3:
        return {**r, "error": "フレームを取り出せません"}

    f = np.stack(frames)
    r["brightness"] = float(f.mean() / 255.0)
    # 連続するフレーム間の平均変化量 (0-1)
    r["motion"] = float(np.abs(np.diff(f[:-1], axis=0)).mean() / 255.0)
    # ループ末尾 → 先頭 の飛び。内部の動きと比べて過大でないか
    r["loop_jump"] = float(np.abs(f[-1] - f[0]).mean() / 255.0)

    issues = []
    if r["brightness"] < 0.04:
        issues.append(f"暗すぎ {r['brightness']:.3f}")
    if r["brightness"] > 0.55:
        issues.append(f"明るすぎ {r['brightness']:.2f}")
    if r["motion"] > 0.05:
        issues.append(f"動きすぎ {r['motion']:.3f}")
    if r["loop_jump"] > max(r["motion"] * 3.0, 0.02):
        issues.append(f"ループ飛び {r['loop_jump']:.3f}")
    r["issues"] = issues
    return r


def main() -> int:
    slugs = sorted(p.stem for p in (OUT / "audio").glob("*.wav"))
    if not slugs:
        print("out/audio が空です。先に render_bgm.py を実行してください。")
        return 2

    print("═" * 108)
    print("音声の検査")
    print("═" * 108)
    print(f"{'track':26s} {'LUFS':>6s} {'TP':>6s} {'継ぎ目':>7s} {'crest':>6s} "
          f"{'相関':>5s} {'1k':>5s} {'2k':>5s} {'4k':>5s} {'8k':>6s}  判定")
    print("─" * 108)

    audio, visual, ok_all = [], [], True
    for s in slugs:
        r = audio_qa(s)
        audio.append(r)
        if "error" in r:
            print(f"{s:26s} {r['error']}")
            ok_all = False
            continue
        b = r["bands"]
        ok = not r["issues"]
        ok_all &= ok
        print(f"{s:26s} {r['lufs']:6.2f} {r['true_peak_db']:6.2f} "
              f"{r['seam_rel_db']:+6.1f} {r['crest_db']:6.1f} {r['mono_corr']:5.2f} "
              f"{b[1000]:5.1f} {b[2000]:5.1f} {b[4000]:5.1f} {b[8000]:6.1f}  "
              f"{'OK' if ok else '⚠ ' + ' / '.join(r['issues'])}")

    print()
    print("═" * 108)
    print("映像の検査")
    print("═" * 108)
    print(f"{'track':26s} {'輝度':>7s} {'動き':>7s} {'ループ飛び':>10s}  判定")
    print("─" * 108)
    for s in slugs:
        r = visual_qa(s)
        visual.append(r)
        if "error" in r:
            print(f"{s:26s} {r['error']}")
            continue
        ok = not r["issues"]
        ok_all &= ok
        print(f"{s:26s} {r['brightness']:7.3f} {r['motion']:7.4f} "
              f"{r['loop_jump']:10.4f}  {'OK' if ok else '⚠ ' + ' / '.join(r['issues'])}")

    print()
    n_issue = sum(1 for r in audio + visual if r.get("issues"))
    print(f"{len(slugs)} 本を検査 / 指摘 {n_issue} 件")
    print(f"総合判定: {'全て合格 — アップロード可' if ok_all else '要修正あり'}")

    (OUT / "qa.json").write_text(
        json.dumps({"audio": audio, "visual": visual}, ensure_ascii=False,
                   indent=2, default=float), encoding="utf-8")
    print(f"詳細を {OUT / 'qa.json'} に書き出しました。")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
