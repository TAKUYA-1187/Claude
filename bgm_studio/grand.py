"""
録音のグランドピアノ (Salamander Grand Piano V3) を、強さ・ペダル・離鍵まで含めて鳴らす部品。2026-11-15。

音源：Salamander Grand Piano V3 (Alexander Holm、Yamaha C5、CC BY 3.0)
  - 取得元：https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html
    SalamanderGrandPianoV3+20161209_44khz16bit.tar.xz
    (作者が 48kHz/24bit 録音から作った 44.1kHz/16bit 版。こちらでレート変換はしない)
  - 16 段階の強さ、短 3 度ごとの録音 (A0〜C8)。離鍵時の弦の響きの録音つき
  - 表示が必要：「Salamander Grand Piano V3 by Alexander Holm, CC BY 3.0」
  - ライセンスの原文：data/licenses/salamander_grand_piano_v3/

旧エンジン (instruments.SampleBank の soft_piano) との違い
  - 旧：Iowa MIS の mf 1 段階だけ。強さは音量を変えるだけで、音色は同じ
  - 新：強さごとに別の録音を使う (弱く弾くと音色も柔らかくなる)
  - サステインペダルを模す：ペダルが踏まれている間は離鍵しても鳴り続け、上げたときにダンパーで止まる
  - 離鍵の瞬間に、録音された弦の響き (harmS/harmL) を小さく足す
  - F#6 (MIDI 90) より上はダンパーが無い (実際のピアノと同じ)

音程：サンプルは 44.1kHz で、エンジンも 44.1kHz (dsp.SR)。保存・読み込みでのレート変換はしない。
鳴らすときに、その音へ合わせる再サンプリングを 1 回だけ行う (最大 ±1 半音 + 調律の補正)。
調律は録音のまま (SalamanderGrandPianoV3.sfz。tune の補正なし)。2026-11-15 に実測した A4 は +0.5〜+1.2 cent、
C4 は約 -1.5 cent、A5 は約 +7 cent、A2 は約 -5.5 cent (実際のピアノと同じく、高音はやや高く低音はやや低い)。
同梱の Retuned 版 (tune 値つき) は中音域が 3〜4 cent 低くなったので使わない。
基準 A は dsp.midi2hz の設定 (A4) を使う。録音の基準は A=440 とみなす。
"""

from __future__ import annotations

import re
import wave
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy import signal as _sig

from . import dsp

ROOT = Path(__file__).resolve().parent.parent
SAL_DIR = ROOT / "samples" / "salamander_raw" / "SalamanderGrandPianoV3_44.1khz16bit"
SFZ = SAL_DIR / "SalamanderGrandPianoV3.sfz"
ARCHIVE_SHA256 = "58750eb1366761e187f71ddb9b932355ea894d28ec4331e74ab8acb44c819936"

MAX_SECONDS = 11.0          # 1 音の長さの上限 (録音は 12〜15 秒。最後の 1 秒はフェード)
NO_DAMPER_FROM = 89         # この MIDI 番号以上はダンパーなし (sfz の "Notes without dampers")


def _attrs(line: str) -> dict:
    return dict(re.findall(r"(\w+)=([^\s]+)", line))


def parse_sfz(path: Path = SFZ):
    """主な音の領域と、離鍵の響きの領域を読む。pitch_keycenter が無い行は sfz の既定 60"""
    notes, harm = [], []
    group = {}
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("<group>"):
            group = _attrs(line)
            continue
        if not line.startswith("<region>"):
            continue
        a = {**group, **_attrs(line)}
        a["sample"] = a["sample"].replace("\\", "/").split("/")[-1]
        r = dict(sample=a["sample"], lokey=int(a.get("lokey", 0)), hikey=int(a.get("hikey", 127)),
                 lovel=int(a.get("lovel", 1)), hivel=int(a.get("hivel", 127)),
                 key=int(a.get("pitch_keycenter", 60)), tune=float(a.get("tune", 0.0)))
        if a.get("trigger") == "release":
            if a["sample"].startswith("harm"):
                r.update(volume=float(a.get("volume", 0.0)), rt_decay=float(a.get("rt_decay", 0.0)))
                harm.append(r)
        elif re.match(r"[A-G]#?\d+v\d+\.wav", a["sample"]):
            notes.append(r)
    return notes, harm


def _read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        assert w.getframerate() == dsp.SR, (path, w.getframerate())   # 48k を 44.1k として鳴らした失敗の再発防止
        assert w.getsampwidth() == 2 and w.getnchannels() == 2
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2)
    return (x.astype(np.float32) / 32768.0)


class Grand:
    def __init__(self):
        if not SFZ.exists():
            raise FileNotFoundError(f"{SFZ} がありません。prepare_salamander.py を実行してください")
        self.notes, self.harm = parse_sfz()
        self._raw: dict[str, np.ndarray] = {}
        self._cache: dict[tuple, np.ndarray] = {}
        self.used: dict[str, int] = {}

    def _sample(self, name: str) -> np.ndarray:
        if name not in self._raw:
            x = _read_wav(SAL_DIR / "44.1khz16bit" / name)
            a = np.abs(x).max(axis=1)
            on = int(np.argmax(a > 1e-3 * a.max()))
            x = x[max(0, on - 24):]                        # 発音前の無音をそろえる (1〜3 ms)
            self._raw[name] = x[: int(MAX_SECONDS * dsp.SR)]
        return self._raw[name]

    @staticmethod
    def _pick(regions, m: int, vel: int):
        for r in regions:
            if r["lokey"] <= m <= r["hikey"] and r["lovel"] <= vel <= r["hivel"]:
                return r
        raise KeyError((m, vel))

    def _shifted(self, r: dict, m: int) -> np.ndarray:
        """領域の録音を、MIDI 番号 m の高さへ 1 回だけ再サンプリングする"""
        key = (r["sample"], m)
        if key not in self._cache:
            x = self._sample(r["sample"])
            target = float(dsp.midi2hz(m))
            # 録音の音 (key) を A=440 の平均律とみなす (tune は sfz にあれば使う。今の sfz には無い)
            src = 440.0 * 2 ** ((r["key"] - 69) / 12) / 2 ** (r["tune"] / 1200)
            ratio = target / src                           # >1 なら高くする = 短くする
            if abs(ratio - 1.0) > 1e-5:
                fr = Fraction(1.0 / ratio).limit_denominator(2000)
                x = _sig.resample_poly(x, fr.numerator, fr.denominator, axis=0).astype(np.float32)
            self._cache[key] = x
        return self._cache[key]

    def strike(self, m: int, vel: int, sound_s: float, held_s: float | None = None) -> np.ndarray:
        """
        1 音。vel は 1〜127。sound_s 秒でダンパーが下りる (鍵盤またはペダルが上がった時点)。
        held_s：打鍵から離鍵までの秒 (離鍵の響きの音量に使う。None なら sound_s)
        """
        vel = int(np.clip(vel, 1, 127))
        r = self._pick(self.notes, m, vel)
        self.used[r["sample"]] = self.used.get(r["sample"], 0) + 1
        x = self._shifted(r, m)
        # 同じ録音の中でも、強さに応じて少しだけ音量を変える (段の境目で音量が跳ばないように)
        center = (r["lovel"] + min(r["hivel"], 127)) / 2.0
        g = dsp.db2lin(0.16 * (vel - center))
        n_sound = int(max(0.02, sound_s) * dsp.SR)
        if m >= NO_DAMPER_FROM or n_sound >= len(x):
            y = x.copy()
        else:
            tau = 0.06 + (NO_DAMPER_FROM - m) * 0.0025     # 低い音ほどダンパーで止まるのが遅い (60〜220 ms)
            n_rel = min(int(tau * 6.9 * dsp.SR), len(x) - n_sound)
            y = x[: n_sound + n_rel].copy()
            env = np.exp(-np.arange(n_rel, dtype=np.float32) / (tau * dsp.SR))
            y[n_sound:] *= env[:, None]
            nf = min(n_rel, int(0.03 * dsp.SR))                # 減衰の最後 (-60 dB) で波形を切ると段差になるので 30 ms で 0 へ
            if nf > 0:
                y[len(y) - nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]
            y = self._add_release(y, m, vel, n_sound, held_s if held_s is not None else sound_s)
        nf = min(len(y), int(0.8 * dsp.SR))
        if len(y) >= int(MAX_SECONDS * dsp.SR) - 10:       # 録音の長さで切れる音は、最後を 0.8 秒で消す
            y[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None] ** 2
        return (y * g).astype(np.float32)

    def _add_release(self, y: np.ndarray, m: int, vel: int, at: int, held_s: float) -> np.ndarray:
        """離鍵の瞬間の弦の響き (sfz：volume -4dB、押していた 1 秒ごとに rt_decay dB 小さく)。さらに 8 dB 控えめにする"""
        hv = [h for h in self.harm if h["lokey"] <= m <= h["hikey"]]
        hv = [h for h in hv if h["lovel"] <= vel <= h["hivel"]] or hv
        if not hv:
            return y
        h = hv[0]
        z = self._shifted(h, m)
        z = z[: int(1.5 * dsp.SR)].copy()
        nf = min(len(z), int(0.4 * dsp.SR))
        z[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]
        g_db = h["volume"] - 8.0 - h["rt_decay"] * held_s + 20 * np.log10(max(vel, 1) / 127.0) * 0.9
        if g_db < -60:
            return y
        out = np.zeros((max(len(y), at + len(z)), 2), dtype=np.float32)
        out[: len(y)] = y
        out[at: at + len(z)] += z * dsp.db2lin(g_db)
        return out
