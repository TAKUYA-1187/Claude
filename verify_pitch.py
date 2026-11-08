#!/usr/bin/env python3
"""
48kHz/44.1kHz の音程不具合の検証 (2026-11-08)。実行するとすべて作り直す。

    PYTHONHASHSEED=0 python3 verify_pitch.py --old-banks <修正前のサンプル (*_clean) のフォルダ> --out <出力先>

エンジンの状態を 3 つ切り替えて、同じ楽譜・同じ音・同じ区間で比べる:
  before     : 修正前の録音バンク (48kHz で保存したファイル) を、修正前と同じく 44.1kHz として読む。音量均し (_even_out) なし
  pitch_only : 修正後のバンク (44.1kHz)。音量均しなし         ← 音程の修正だけの効果
  after      : 修正後のバンク + 音量均し (現在のエンジン)       ← 音量均しの効果は pitch_only との差

出力: pitch_2x2.csv / pitch_mix.csv / sample_banks.csv / pitch_path.md / reference_tones/*.flac /
      orig01_compare/*.flac (修正前後の同じ区間 25 秒 × 3 か所、同じ知覚音量 -18 LUFS にそろえる)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio import dsp, instruments as I, classical as C, handpan as H, jazz as J, video as V  # noqa: E402

SR = dsp.SR
NEW = ROOT / "samples"
_REAL_EVEN_OUT = I._even_out


def set_engine(state: str, old_root: Path) -> None:
    """エンジンが読むサンプルの場所と音量均しを切り替え、メモリ上のキャッシュをすべて捨てる"""
    root = old_root if state == "before" else NEW
    I._PIANO_DIR, I._PIANO = root / "piano_clean", None
    I._BELLS_DIR, I._BELLS = root / "bells_clean", None
    I._SAMPLES, I._CROTALES = root, None
    I._PERC_CACHE.clear()
    C.SAMPLES = root
    C._BOWED.clear()
    H.SAMPLES = root
    H._BANK.clear()
    H._HIT_CACHE.clear()
    J.SAMPLES = root
    J._BASS.clear()
    I._even_out = _REAL_EVEN_OUT if state == "after" else (lambda bank, **kw: None)


def peak_hz(x: np.ndarray, target: float, t0: float = 0.15, n: int = 1 << 15) -> float:
    """target の -2 半音〜+1 半音の範囲で、いちばん強い周波数 (放物線補間) を返す。
    修正前は -1.47 半音なので範囲に入る。-3 半音まで広げると、和音の C5 で隣の A4 (ちょうど -3 半音) を拾った"""
    x = x.mean(axis=1) if x.ndim == 2 else x
    seg = x[int(t0 * SR):int(t0 * SR) + n].astype(np.float64)
    seg = np.pad(seg, (0, max(0, n - len(seg)))) * np.hanning(n)
    nfft = n * 8
    sp = np.abs(np.fft.rfft(seg, nfft))
    f = np.fft.rfftfreq(nfft, 1 / SR)
    band = np.nonzero((f > target * 2 ** (-2 / 12)) & (f < target * 2 ** (1 / 12)))[0]
    k = band[np.argmax(sp[band])]
    a, b, c = np.log(sp[k - 1] + 1e-12), np.log(sp[k] + 1e-12), np.log(sp[k + 1] + 1e-12)
    return float(f[k] + 0.5 * (a - c) / (a - 2 * b + c) * (f[1] - f[0]))


def cents(f: float, ref: float) -> float:
    return round(float(1200 * np.log2(f / ref)), 2)


PATHS = [  # (名前, MIDI, 鳴らす関数)。実際の制作で使う読み込み経路そのもの
    ("piano: instruments.real_piano", 69, lambda m: I.PITCHED["soft_piano"](m, 0.5, rng=np.random.default_rng(0))),
    ("music box: instruments.real_music_box", 81, lambda m: I.PITCHED["music_box"](m, 0.5, rng=np.random.default_rng(0))),
    ("crotale: instruments.real_crotale", 84, lambda m: I.PITCHED["crotale"](m, 0.5, rng=np.random.default_rng(0))),
    ("cello: classical.bowed_note", 57, lambda m: C.bowed_note("cello", m, 1.5, 0.5)),
    ("violin: classical.bowed_note", 69, lambda m: C.bowed_note("violin", m, 1.5, 0.5)),
    ("alto sax: classical.bowed_note", 69, lambda m: C.bowed_note("altosax", m, 1.5, 0.5)),
    ("alto flute: classical.bowed_note", 69, lambda m: C.bowed_note("altoflute", m, 1.5, 0.5)),
    ("vibraphone: handpan._pitched", 69, lambda m: H._pitched("sustain", m, SR)[: SR * 2]),
    ("double bass pizz: jazz._bass_note", 45, lambda m: J._bass_note(m, 0.8, 1.5, SR)),
]
NOT_PITCH_SCALED = {
    "triangle / tambourine roll (instruments.triangle_real / sleigh_real)":
        "音程を持たない打楽器。音程の計算はせず、録音をそのまま (sleigh_real は意図的に 5 度下げて) 使う。"
        "48k/44.1k の不具合では、修正前は再生が約 8.8% 遅く・低くなっていた",
    "合成の楽器 (instruments.additive を使う soft_piano 以外の合成音、flute.tanpura_pluck)":
        "録音を使わず 44.1kHz で直接合成するので、この不具合の影響を受けない",
}


def flac(path: Path, x: np.ndarray, bits: int = 16) -> None:
    raw = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run([V.ffmpeg_exe(), "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "flac", str(path)], input=raw, check=True)


def match_lufs(x: np.ndarray, target: float) -> np.ndarray:
    x = dsp.to_stereo(x)
    return (x * np.float32(10 ** ((target - dsp.lufs_integrated(x)) / 20))).astype(np.float32)


def bank_rows(old_root: Path) -> list[list]:
    ff = V.ffmpeg_exe()
    rows = [["バンク", "元の録音フォルダ", "元の録音のサンプルレート", "保存したレート（修正前）", "保存したレート（修正後）",
             "準備時のレート変換（修正前→修正後）", "演奏時の変換", "ファイル数", "修正後の sha256（全ファイルを名前順に連結）",
             "修正前の sha256", "修正後の作成日時", "キャッシュ"]]
    raw_of = {"piano_clean": "iowa_piano", "bells_clean": "iowa_bells", "crotale_clean": "iowa_perc", "perc_clean": "iowa_perc",
              "cello_clean": "iowa_cello", "violin_clean": "iowa_violin", "vibes_sustain_clean": "iowa_vibes_sustain",
              "vibes_bow_clean": "iowa_vibes_bow", "altosax_clean": "iowa_altosax", "altoflute_clean": "iowa_altoflute",
              "bass_pizz_clean": "iowa_bass_pizz"}

    def digest(d: Path) -> str:
        h = hashlib.sha256()
        for p in sorted(d.glob("*.npy")):
            h.update(p.name.encode())
            h.update(p.read_bytes())
        return h.hexdigest()
    for bank, raw in raw_of.items():
        d = NEW / bank
        rates = set()
        for p in sorted((NEW / raw).glob("*"))[:200]:
            m = re.search(r"(\d+) Hz", subprocess.run([ff, "-hide_banner", "-i", str(p)], capture_output=True,
                                                      text=True).stderr)
            if m:
                rates.add(int(m.group(1)))
        files = sorted(d.glob("*.npy"))
        import datetime
        mt = datetime.datetime.fromtimestamp(max(p.stat().st_mtime for p in files)).isoformat(timespec="seconds")
        rows.append([bank, f"samples/{raw}", "/".join(map(str, sorted(rates))), "48000", str(SR),
                     "44.1k→48k の 1 回 → 変換なし（元が 44.1k なので 0 回）",
                     "音の高さに合わせた再サンプリング 1 回（scipy resample_poly）", len(files), digest(d),
                     digest(old_root / bank) if (old_root / bank).exists() else "（修正前のファイルなし）", mt,
                     "ディスク上のキャッシュなし。メモリ上のキャッシュ（_PIANO 等）は実行ごとに作り直す"])
    return rows


def pitch_path_md() -> str:
    def find(path: str, pat: str) -> list[str]:
        out = []
        for i, line in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
            if re.search(pat, line):
                out.append(f"- `{path}:{i}` `{line.strip()}`")
        return out
    parts = ["# 音の高さが決まる場所（verify_pitch.py が実行時に検索して作った一覧）\n",
             "## 1. 基準ピッチ（A=440 / A=432）：1 か所だけ",
             *find("bgm_studio/dsp.py", r"^def set_tuning|^def midi2hz|_TUNING_A4 = |return a4 \* 2"),
             "\n`set_tuning(a4)` で決めた A を、`midi2hz(m)` が MIDI 番号から周波数にするときに 1 回だけ使う。\n",
             "## 2. 録音サンプルの保存レート：1 か所だけ",
             *find("prepare_piano_samples.py", r"from bgm_studio.dsp import SR|\"-ar\", str\(SR\)"),
             "\n元の録音（44.1kHz）を、エンジンと同じ 44.1kHz で保存する。修正前はここが 48000 で、44.1k→48k に変換していた。\n",
             "## 3. 演奏時に音の高さを合わせる再サンプリング：楽器ごとに 1 回",
             *find("bgm_studio/instruments.py", r"r = float\(midi2hz\(m\)\)|resample_poly"),
             *find("bgm_studio/classical.py", r"r = float\(dsp.midi2hz\(midi\)\)|resample_poly"),
             *find("bgm_studio/handpan.py", r"r = float\(dsp.midi2hz\(midi\)\)|resample_poly"),
             *find("bgm_studio/jazz.py", r"r = 2.0 \*\* |resample_poly"),
             "\n比は「目標周波数 midi2hz(m) ÷ 録音の音の周波数（A=440 の平均律と仮定）」。サンプルレートの補正はどこにも入っていない（入れる必要がない）。",
             "例外：`jazz._bass_note` は `2 ** ((midi - base) / 12)` で、A の設定を使わない（ジャズは A=440 だけで使う）。\n",
             "## 4. 移調（曲の調を変える）：楽譜データの MIDI 番号に足すだけ",
             *find("bgm_studio/nursery.py", r"trans = |mb_trans"),
             "\n移調は MIDI 番号を整数で足すだけで、周波数やサンプルレートには触れない。\n",
             "## 5. サンプルレートを参照する所",
             *find("bgm_studio/dsp.py", r"^SR = "),
             *find("bgm_studio/video.py", r"sample_rate: int = 48000"),
             "\n`video.py` の 48000 は、完成した音声を AAC にするときの出力レート（最後に 1 回）。音の高さは変わらない。",
             "\n## 結論",
             "音の高さに関わる処理は「基準ピッチ 1 回」と「楽器ごとの再サンプリング 1 回」だけ。",
             "修正は 2. の保存レートだけで、補正の処理を足していないので、二重補正にはならない。"]
    return "\n".join(parts) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-banks", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--skip-orig01", action="store_true")
    a = ap.parse_args()
    out = a.out
    (out / "reference_tones").mkdir(parents=True, exist_ok=True)
    (out / "orig01_compare").mkdir(parents=True, exist_ok=True)

    # ── 2×2 (修正前/後 × A=440/432)。同じ関数・同じ MIDI 番号・同じ区間 (発音 0.15 秒後から 0.74 秒) ──
    rows = [["読み込み経路", "MIDI", "A 設定", "目標 Hz", "修正前 Hz", "修正前 cent", "修正後 Hz", "修正後 cent", "修正前後の差 cent"]]
    js = []
    for name, m, fn in PATHS:
        for a4 in (440.0, 432.0):
            dsp.set_tuning(a4)
            ref = float(dsp.midi2hz(m))
            res = {}
            for st in ("before", "after"):
                set_engine(st, a.old_banks)
                res[st] = peak_hz(fn(m), ref)
            rows.append([name, m, a4, round(ref, 2), round(res["before"], 2), cents(res["before"], ref),
                         round(res["after"], 2), cents(res["after"], ref), cents(res["after"], res["before"])])
            js.append(dict(zip(rows[0], rows[-1])))
    with open(out / "pitch_2x2.csv", "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)

    # ── 和音と混合 (ピアノの F 長三和音、ピアノ A4 + チェロ A3) ──
    mix_rows = [["音", "成分", "A 設定", "目標 Hz", "修正前 Hz", "修正前 cent", "修正後 Hz", "修正後 cent"]]
    for a4 in (440.0, 432.0):
        dsp.set_tuning(a4)
        for st in ("before", "after"):
            set_engine(st, a.old_banks)
            chord = sum(dsp.to_stereo(I.PITCHED["soft_piano"](m, 0.5, rng=np.random.default_rng(0))[: SR * 3])
                        for m in (65, 69, 72))
            mixv = dsp.to_stereo(I.PITCHED["soft_piano"](69, 0.5, rng=np.random.default_rng(0))[: SR * 3])
            ce = dsp.to_stereo(C.bowed_note("cello", 57, 2.5, 0.5))[: SR * 3]
            mixv[: len(ce)] += ce
            for nm, x, comps in (("ピアノ F 長三和音", chord, (65, 69, 72)), ("ピアノ A4 + チェロ A3", mixv, (57, 69))):
                for m in comps:
                    ref = float(dsp.midi2hz(m))
                    hz = peak_hz(x, ref)
                    key = (nm, m, a4)
                    if st == "before":
                        mix_rows.append([nm, m, a4, round(ref, 2), round(hz, 2), cents(hz, ref), None, None])
                    else:
                        r = next(r for r in mix_rows[1:] if (r[0], r[1], r[2]) == key)
                        r[6], r[7] = round(hz, 2), cents(hz, ref)
            # 基準音 (2.5 秒、同じ知覚音量 -20 LUFS)
            tone = dsp.to_stereo(I.PITCHED["soft_piano"](69, 0.5, rng=np.random.default_rng(0))[: int(SR * 2.5)])
            nf = int(0.2 * SR)
            tone[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]
            flac(out / "reference_tones" / f"piano_A4_{st}_A{a4:g}.flac", match_lufs(tone, -20.0))
            flac(out / "reference_tones" / f"piano_Fchord_{st}_A{a4:g}.flac", match_lufs(chord, -20.0))
            flac(out / "reference_tones" / f"piano_A4_cello_A3_{st}_A{a4:g}.flac", match_lufs(mixv, -20.0))
    with open(out / "pitch_mix.csv", "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(mix_rows)

    with open(out / "sample_banks.csv", "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(bank_rows(a.old_banks))
    (out / "pitch_path.md").write_text(pitch_path_md(), encoding="utf-8")

    # ── orig01 の同じ区間を 3 状態で (25 秒 × 3 か所、-18 LUFS にそろえる) ──
    lufs = {}
    if not a.skip_orig01:
        from bgm_studio import orig01 as O
        dsp.set_tuning(440.0)
        for st in ("before", "pitch_only", "after"):
            set_engine(st, a.old_banks)
            x, info = O.render()
            for t0, label in ((15.0, "A_theme"), (75.0, "B_minor"), (150.0, "coda")):
                seg = x[int(t0 * SR):int((t0 + 25) * SR)].copy()
                nf = int(0.3 * SR)
                seg[:nf] *= np.linspace(0, 1, nf, dtype=np.float32)[:, None]
                seg[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]
                lufs[f"{label}_{st}"] = round(dsp.lufs_integrated(seg), 2)
                flac(out / "orig01_compare" / f"orig01_{label}_{t0:g}s_{st}.flac", match_lufs(seg, -18.0))
    set_engine("after", a.old_banks)
    (out / "pitch_summary.json").write_text(json.dumps({
        "engine_sample_rate_hz": SR, "theoretical_shift_cents": round(1200 * np.log2(44100 / 48000), 3),
        "method": "FFT（2^15 サンプル・ハン窓・8 倍のゼロ詰め）で、目標の -2〜+1 半音の範囲の最大ピークを放物線補間。発音 0.15 秒後から",
        "known_exception": "jazz._bass_note は A の設定を使わず、いつも A=440 で鳴る（A=432 の行で +44 cent になるのはこのため）。j01 は A=440 なので、作った動画には影響しない",
        "states": {"before": "修正前のバンク（48kHz 保存）を 44.1kHz として読む・音量均しなし",
                   "pitch_only": "修正後のバンク・音量均しなし", "after": "修正後のバンク・音量均しあり（現在）"},
        "pitch_2x2": js, "not_pitch_scaled": NOT_PITCH_SCALED,
        "orig01_compare_lufs_before_matching": lufs,
        "orig01_compare_note": "3 状態とも同じ楽譜・同じ乱数。各 25 秒を -18 LUFS（同じ知覚音量）にそろえた。リミッタなし",
        "not_verified": ["人の耳での比較（Claude は聞けない）", "修正前のバンクは Claude の作業場所にだけある（リポジトリには入れていない）"],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print((out / "pitch_2x2.csv").read_text(encoding="utf-8-sig"))
    print((out / "pitch_mix.csv").read_text(encoding="utf-8-sig"))
    print(lufs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
