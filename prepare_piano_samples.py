#!/usr/bin/env python3
"""
本物のピアノの録音 (University of Iowa Electronic Music Studios の Musical Instrument
Samples) を取り込み、雑音を取り除いて samples/piano_clean/ に保存する。

なぜ: 2026-10-28 のオーナーの評価「メロディーが機械音で聞きにくい」。
これまでのピアノは倍音を足し算して作った合成音で、どう調整しても「電子音」に聞こえる。
実際のピアノ (スタインウェイ) を 1 音ずつ録った音に置き換える。

素材の条件: 公式サイトに "freely available ... may be downloaded and used for any projects,
without restrictions" と明記されている (https://theremin.music.uiowa.edu/MIS.html)。

処理:
  - mf (中くらいの強さ) だけを使う。pp は録音レベルが低く、雑音との差が 10〜20dB しかない
  - 発音の頭にそろえて切る
  - 末尾 1 秒から雑音のスペクトルを測り、スペクトル減算で取り除く (サーという雑音を消す)
  - 音が雑音の近くまで減衰したところでフェードアウトして切る
  - 全音に同じ倍率をかけて正規化する (音域ごとの自然な音量差は残す)

    python3 prepare_piano_samples.py          # ダウンロードから全部
    python3 prepare_piano_samples.py --skip-download
"""

from __future__ import annotations

import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import signal

from bgm_studio import video as VID

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "samples" / "iowa_piano"
CLEAN = ROOT / "samples" / "piano_clean"
SR = 48000
LO, HI = 36, 96            # C2〜C7
NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
URL = "https://theremin.music.uiowa.edu/sound%20files/MIS/Piano_Other/piano/Piano.mf.{}.aiff"


def note_name(m: int) -> str:
    return NAMES[m % 12] + str(m // 12 - 1)


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    def get(m: int) -> None:
        dst = RAW / f"Piano.mf.{note_name(m)}.aiff"
        if not dst.exists():
            subprocess.run(["curl", "-sS", "--retry", "3", "-o", str(dst), URL.format(note_name(m))],
                           check=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(get, range(LO, HI + 1)))


def load(path: Path) -> np.ndarray:
    p = subprocess.run([VID.ffmpeg_exe(), "-loglevel", "error", "-i", str(path),
                        "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, 2).copy()


def env_db(m: np.ndarray, win: float = 0.01) -> np.ndarray:
    n = max(int(win * SR), 1)
    e = np.sqrt(np.convolve(m.astype(np.float64) ** 2, np.ones(n) / n, "same"))
    return 20 * np.log10(e + 1e-12)


def clean(x: np.ndarray) -> np.ndarray:
    m = x.mean(axis=1)
    db = env_db(m)
    pk = db.max()
    # 打鍵の前に小さな物音が入っている録音がある (C3 など)。-40dB を基準にすると
    # それを音の頭と誤認したので、最大音量の直前で -20dB を超えた点を頭にする
    ipk = int(np.argmax(db))
    pre = np.where(db[:ipk] < pk - 20)[0]
    onset = int(pre[-1]) + 1 if len(pre) else 0
    start = max(onset - int(0.004 * SR), 0)

    # 雑音のスペクトルは録音の最後 1 秒 (音がほぼ消えたところ) から測る
    nper, nover = 2048, 1536
    tail = x[-SR:]
    _, _, Nt = signal.stft(tail.T, fs=SR, nperseg=nper, noverlap=nover)
    noise = np.abs(Nt).mean(axis=-1, keepdims=True)                   # (2, F, 1)

    y = x[start:]
    _, _, X = signal.stft(y.T, fs=SR, nperseg=nper, noverlap=nover)
    mag = np.abs(X)
    # パワーのスペクトル減算 (ウィーナー型)。振幅で雑音の 2 倍を引く方式では、
    # 雑音よりわずかに大きいだけの高い倍音まで消えて、4kHz より上がほぼ無くなった
    # (C4: -44dB → -66dB)。雑音より 2 倍以上大きい成分はほぼそのまま残る
    g = np.sqrt(np.clip(1.0 - 1.5 * (noise / (mag + 1e-12)) ** 2, 0.0, 1.0))
    g = signal.lfilter([0.35], [1.0, -0.65], g, axis=-1)
    g = np.maximum(g, 0.0)
    _, yc = signal.istft(X * g, fs=SR, nperseg=nper, noverlap=nover)
    yc = yc.T[: len(y)].astype(np.float32)

    # 低いうなり (空調など) を切る
    sos = signal.butter(2, 30.0, "highpass", fs=SR, output="sos")
    yc = signal.sosfilt(sos, yc, axis=0).astype(np.float32)

    # 減衰して雑音の近くまで来たところで切る (余韻はリバーブで補う)
    dbc = env_db(yc.mean(axis=1), 0.05)
    pkc = dbc.max()
    s0 = int(np.argmax(dbc)) + int(0.3 * SR)          # 最大音量の後から探す
    after = np.where(dbc[s0:] < pkc - 58)[0]
    end = s0 + int(after[0]) if len(after) else len(yc)
    end = min(end + int(0.4 * SR), len(yc))
    yc = yc[:end]
    nf = min(int(1.2 * SR), len(yc) // 3)
    yc[-nf:] *= np.linspace(1.0, 0.0, nf, dtype=np.float32)[:, None] ** 2
    return yc


# ── オルゴール用: グロッケンシュピール (プラスチックのマレット) ──────────
# 無料で自由に使えるオルゴールの録音は見つからなかった。オルゴールと同じく「鋼の棒が
# 鳴る」楽器の録音で代える (同じ Iowa MIS, 2014 年収録, C5〜E8)。
BELLS_RAW = ROOT / "samples" / "iowa_bells"
BELLS_CLEAN = ROOT / "samples" / "bells_clean"
BELLS_URL = ("https://theremin.music.uiowa.edu/sound%20files/MIS%20Pitches%20-%202014/"
             "Percussion/Bells/bells.plastic.ff.{}.stereo.aif")
BELLS_LO, BELLS_HI = 72, 100      # C5〜E8


def prepare_bells(skip_download: bool) -> None:
    BELLS_RAW.mkdir(parents=True, exist_ok=True)
    BELLS_CLEAN.mkdir(parents=True, exist_ok=True)

    def get(m: int) -> None:
        dst = BELLS_RAW / f"bells.{note_name(m)}.aif"
        if not dst.exists():
            subprocess.run(["curl", "-sS", "--retry", "3", "-o", str(dst),
                            BELLS_URL.format(note_name(m))], check=True)
    if not skip_download:
        with ThreadPoolExecutor(8) as ex:
            list(ex.map(get, range(BELLS_LO, BELLS_HI + 1)))
    out = {m: clean(load(BELLS_RAW / f"bells.{note_name(m)}.aif"))
           for m in range(BELLS_LO, BELLS_HI + 1)
           if (BELLS_RAW / f"bells.{note_name(m)}.aif").exists()}
    peak = max(float(np.abs(v).max()) for v in out.values())
    for m, v in out.items():
        np.save(BELLS_CLEAN / f"m{m}.npy", (v * (0.9 / peak)).astype(np.float32))
    lens = [len(v) / SR for v in out.values()]
    print(f"{len(out)} 音を {BELLS_CLEAN} に保存 (長さ {min(lens):.1f}〜{max(lens):.1f} 秒)")


# ── クリスマスの鈴 (2026-10-30) ─────────────────────────────────────
# 「鈴の音などの楽しい動画も」という依頼に応える。同じ Iowa MIS (2014 年収録) の
# ・クロタル (小さな調律された鈴, C6〜C8)       → 長い音にきらめきを添える
# ・トライアングル                               → フレーズの頭に 1 回だけ
# ・タンバリンのシェイク・ロール (ジングルの音)  → そり鈴 (スレイベル) の代わり
# pp の録音は雑音との差が 20dB ほどしかなく、上げるとサーという音が出るので、
# 雑音の少ない ff (差 60〜75dB) を使い、鳴らすときに音量と高域を下げる。
PERC_RAW = ROOT / "samples" / "iowa_perc"
PERC_CLEAN = ROOT / "samples" / "perc_clean"
CROTALE_CLEAN = ROOT / "samples" / "crotale_clean"
PERC_URL = "https://theremin.music.uiowa.edu/sound%20files/MIS%20Pitches%20-%202014/Percussion/"
CROTALE_NOTES = ["C6", "D6", "E6", "F6", "G6", "A6", "B6", "C7", "D7", "E7", "F7", "G7",
                 "A7", "B7", "C8"]
PERC_FILES = {
    "triangle6": "Hand%20Percussion/Triangles/6triangle.ff.stereo.aif",
    "triangle8": "Hand%20Percussion/Triangles/8triangle.ff.stereo.aif",
    "roll1": "Tambourines/tambourine1.shakeroll.ff.stereo.aif",
    "roll2": "Tambourines/tambourine2.shakeroll.ff.stereo.aif",
    "roll3": "Tambourines/tambourine3.shakeroll.ff.stereo.aif",
}


def _midi_of(name: str) -> int:
    return NAMES.index(name[:-1]) + 12 * (int(name[-1]) + 1)


def prepare_perc(skip_download: bool) -> None:
    PERC_RAW.mkdir(parents=True, exist_ok=True)
    PERC_CLEAN.mkdir(parents=True, exist_ok=True)
    CROTALE_CLEAN.mkdir(parents=True, exist_ok=True)
    jobs = {f"Crotale.ff.{n}.stereo.aif": PERC_URL + f"Crotales/Crotale.ff.{n}.stereo.aif"
            for n in CROTALE_NOTES}
    jobs.update({f"{k}.aif": PERC_URL + v for k, v in PERC_FILES.items()})
    if not skip_download:
        def get(item):
            dst = PERC_RAW / item[0]
            if not dst.exists():
                subprocess.run(["curl", "-sS", "--retry", "3", "-o", str(dst), item[1]],
                               check=True)
        with ThreadPoolExecutor(8) as ex:
            list(ex.map(get, jobs.items()))

    crot = {_midi_of(n): clean(load(PERC_RAW / f"Crotale.ff.{n}.stereo.aif")).mean(axis=1)
            for n in CROTALE_NOTES}
    peak = max(float(np.abs(v).max()) for v in crot.values())
    for m, v in crot.items():
        np.save(CROTALE_CLEAN / f"m{m}.npy", (v * (0.9 / peak)).astype(np.float32))

    hp = signal.butter(2, 2000.0, "highpass", fs=SR, output="sos")
    for k in PERC_FILES:
        x = load(PERC_RAW / f"{k}.aif")
        if k.startswith("roll"):
            # シェイク・ロールは鳴り続けている録音なので、頭そろえ・末尾の切り詰めはしない。
            # 皮 (ヘッド) の低い鳴りを 2kHz の高域通過で落として、ジングルの音だけにする
            y = signal.sosfilt(hp, x.mean(axis=1)).astype(np.float32)
        else:
            y = clean(x).mean(axis=1)
        np.save(PERC_CLEAN / f"{k}.npy", (y * (0.9 / float(np.abs(y).max()))).astype(np.float32))
    print(f"クロタル {len(crot)} 音 → {CROTALE_CLEAN} / 鈴・トライアングル {len(PERC_FILES)} 本 → {PERC_CLEAN}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--bells", action="store_true", help="オルゴール用の鉄琴だけを処理する")
    ap.add_argument("--perc", action="store_true", help="クリスマスの鈴 (クロタル・トライアングル・そり鈴)")
    args = ap.parse_args()
    if args.bells:
        prepare_bells(args.skip_download)
        return 0
    if args.perc:
        prepare_perc(args.skip_download)
        return 0
    if not args.skip_download:
        download()
    CLEAN.mkdir(parents=True, exist_ok=True)
    out = {}
    for m in range(LO, HI + 1):
        out[m] = clean(load(RAW / f"Piano.mf.{note_name(m)}.aiff"))
    peak = max(float(np.abs(v).max()) for v in out.values())
    for m, v in out.items():
        np.save(CLEAN / f"m{m}.npy", (v * (0.9 / peak)).astype(np.float32))
    lens = [len(v) / SR for v in out.values()]
    print(f"{len(out)} 音を {CLEAN} に保存 (長さ {min(lens):.1f}〜{max(lens):.1f} 秒)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
