"""
手続き的サンプルバンク。

外部音源を一切使わず、加算合成 / 減算合成で楽器音を作る。

高速化の要:
  1 音ごとに合成すると 2 時間ぶんでは到底終わらないので、
  「音程 × 音色バリエーション」を一度だけレンダリングしてキャッシュし、
  シーケンサはキャッシュ済み配列を加算するだけにする (= 実質サンプラー)。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import dsp
from .dsp import SR, TWO_PI, midi2hz

# ──────────────────────────────────────────────────────────────
# 加算合成コア
# ──────────────────────────────────────────────────────────────


def additive(f0: float, dur: float, ratios, amps, taus,
             sr: int = SR, attack: float = 0.004,
             rng: np.random.Generator | None = None,
             detune_cents: float = 0.0, beat_hz: float = 0.0) -> np.ndarray:
    """
    部分音を足し合わせて 1 音を作る汎用エンジン。

    ratios : 基本周波数に対する各部分音の周波数比 (整数倍とは限らない)
    amps   : 各部分音の振幅
    taus   : 各部分音の減衰時定数 [秒] (1/e になるまで)
    beat_hz: 0 でなければ、各部分音を微妙にデチューンした 2 本にして
             うなり (beating) を作る。生っぽさが一気に増す。
    """
    rng = rng or np.random.default_rng(0)
    n = max(int(dur * sr), 16)
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, dtype=np.float32)
    nyq = sr * 0.47

    for r, a, tau in zip(ratios, amps, taus):
        fk = f0 * r * (2.0 ** (detune_cents / 1200.0))
        if fk >= nyq or a < 1e-4:
            continue
        env = np.exp(-t / max(tau, 1e-3))
        ph = rng.uniform(0.0, TWO_PI)
        if beat_hz > 0.0:
            d = beat_hz * (0.5 + rng.random())
            out += (a * 0.5 * env * (np.sin(TWO_PI * (fk - d) * t + ph)
                                     + np.sin(TWO_PI * (fk + d) * t + ph * 0.7))
                    ).astype(np.float32)
        else:
            out += (a * env * np.sin(TWO_PI * fk * t + ph)).astype(np.float32)

    # アタック整形 (クリックを消す)
    na = max(int(attack * sr), 2)
    if na < n:
        out[:na] *= np.linspace(0.0, 1.0, na, dtype=np.float32) ** 1.5
    # 末尾を必ず 0 に落とす (加算時のプチノイズ防止)
    nr = min(int(0.02 * sr), n // 4)
    if nr > 1:
        out[-nr:] *= np.linspace(1.0, 0.0, nr, dtype=np.float32)
    return out


def _n_partials(f0: float, top_hz: float, cap: int, floor: int = 6) -> int:
    """
    top_hz まで倍音を伸ばすのに必要な本数を返す。

    本数を固定にすると低音ほど倍音が足りなくなる。
    実測では E2 (82Hz) のウッドベースが 12 本しか無く、
    988Hz より上が空になっていた (本物は 3-4kHz まで鳴る)。
    """
    return int(np.clip(round(top_hz / max(f0, 1.0)), floor, cap))


def _harm_taus(tau0: float, ratios, slope: float = 0.30) -> list[float]:
    """
    高い部分音ほど速く減衰する (実際の弦/板の物理挙動)。

    slope を大きくしすぎると高次倍音が一瞬で消え、
    音が「毛布越し」になる。実測では slope=0.75 のとき
    2-4kHz が 250-500Hz より 17dB も低くなっていた
    (本物のピアノは -8〜-12dB)。0.30 前後が実測に近い。
    """
    return [tau0 / (1.0 + slope * (r - 1.0)) for r in ratios]


# ──────────────────────────────────────────────────────────────
# 鍵盤 / 撥弦
# ──────────────────────────────────────────────────────────────

def rhodes(m: int, vel: float = 0.8, sr: int = SR,
           rng: np.random.Generator | None = None) -> np.ndarray:
    """
    エレピ (Rhodes 系)。lofi / ジャズ喫茶の主役。
    特徴は「タイン」と呼ばれる金属棒の当たる音 = 高次倍音の速い減衰。
    """
    rng = rng or np.random.default_rng(m)
    f0 = midi2hz(m)
    dur = float(np.clip(6.0 - (m - 48) * 0.045, 1.6, 6.5))

    ratios = [1, 2, 3, 4, 5, 6, 8, 10, 13, 16]
    # ベロシティが高いほど倍音が明るくなる
    b = 1.32 - 0.42 * vel
    amps = [1.0, 0.42, 0.10, 0.20, 0.045, 0.085, 0.05, 0.030, 0.016, 0.009]
    amps = [a / (r ** (b - 1.0)) for a, r in zip(amps, ratios)]
    taus = _harm_taus(dur * 0.42, ratios, slope=0.30)

    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.003, rng=rng)

    # タイン (アタックのキラッとした金属音)
    n_t = int(0.10 * sr)
    t = np.arange(n_t, dtype=np.float32) / sr
    tine = (np.sin(TWO_PI * f0 * 7.02 * t) + 0.6 * np.sin(TWO_PI * f0 * 11.3 * t))
    tine *= np.exp(-t / 0.020) * 0.10 * vel
    y[:n_t] += tine.astype(np.float32)

    return (y * (0.35 + 0.65 * vel)).astype(np.float32)


def piano(m: int, vel: float = 0.8, sr: int = SR,
          rng: np.random.Generator | None = None) -> np.ndarray:
    """
    アコースティックピアノ。
    弦の「インハーモニシティ」(倍音が整数倍より少しずつ高くなる現象) を
    入れると、途端に本物らしくなる。
    """
    rng = rng or np.random.default_rng(m + 1000)
    f0 = midi2hz(m)
    dur = float(np.clip(9.0 - (m - 40) * 0.075, 1.8, 9.0))

    # インハーモニシティ係数: 低音弦ほど大きい
    B = 0.0004 * (2.0 ** ((60 - m) / 24.0))
    n_part = _n_partials(f0, 9000.0, cap=44, floor=10)
    ks = np.arange(1, n_part + 1)
    ratios = (ks * np.sqrt(1.0 + B * ks * ks)).tolist()

    b = 1.22 - 0.35 * vel
    amps = [(1.0 / (k ** b)) * (1.0 + 0.22 * rng.standard_normal()) for k in ks]
    amps = [max(a, 0.0) for a in amps]
    # 実際のピアノは 1 倍音より 2〜3 倍音のほうが強いことも多い
    if len(amps) > 2:
        amps[1] *= 1.25
        amps[2] *= 1.1
    taus = [dur * 0.35 / (1.0 + 0.16 * (k - 1)) for k in ks]

    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.002, rng=rng)

    # ハンマーノイズ
    n_h = int(0.04 * sr)
    hm = dsp.bandpass(rng.standard_normal(n_h).astype(np.float32), 900, 5500, taps=257)
    hm *= np.exp(-np.arange(n_h, dtype=np.float32) / (0.004 * sr)) * 0.035 * vel
    y[:n_h] += hm

    return (y * (0.30 + 0.70 * vel)).astype(np.float32)


def nylon_guitar(m: int, vel: float = 0.8, sr: int = SR,
                 rng: np.random.Generator | None = None) -> np.ndarray:
    """ナイロン弦ギター。ボサノヴァ用。奇数倍音がやや強い"""
    rng = rng or np.random.default_rng(m + 2000)
    f0 = midi2hz(m)
    dur = float(np.clip(4.5 - (m - 45) * 0.03, 1.2, 4.5))
    ks = np.arange(1, _n_partials(f0, 8000.0, cap=26, floor=10) + 1)
    ratios = (ks * np.sqrt(1.0 + 0.00012 * ks * ks)).tolist()
    b = 1.28 - 0.34 * vel
    amps = [(1.0 / (k ** b)) * (1.18 if k % 2 == 1 else 0.82) for k in ks]
    taus = _harm_taus(dur * 0.40, ratios, slope=0.40)
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.004, rng=rng)

    # 指が弦に触れる音
    n_p = int(0.03 * sr)
    pk = dsp.bandpass(rng.standard_normal(n_p).astype(np.float32), 1500, 7000, taps=257)
    pk *= np.exp(-np.arange(n_p, dtype=np.float32) / (0.003 * sr)) * 0.04 * vel
    y[:n_p] += pk
    return (y * (0.35 + 0.65 * vel)).astype(np.float32)


def harp(m: int, vel: float = 0.8, sr: int = SR,
         rng: np.random.Generator | None = None) -> np.ndarray:
    """ハープ/リュート。ファンタジー系とヒーリング系で使う"""
    rng = rng or np.random.default_rng(m + 3000)
    f0 = midi2hz(m)
    dur = float(np.clip(7.0 - (m - 50) * 0.05, 1.8, 7.0))
    ks = np.arange(1, _n_partials(f0, 10000.0, cap=30, floor=12) + 1)
    ratios = (ks * np.sqrt(1.0 + 0.00008 * ks * ks)).tolist()
    amps = [1.0 / (k ** (1.08 - 0.26 * vel)) for k in ks]
    taus = _harm_taus(dur * 0.45, ratios, slope=0.30)
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.003, rng=rng)
    return (y * (0.35 + 0.65 * vel)).astype(np.float32)


def koto(m: int, vel: float = 0.8, sr: int = SR,
         rng: np.random.Generator | None = None) -> np.ndarray:
    """
    琴。和風ローファイの主役。

    ナイロン弦との違いは 3 つ:
      - アタックの「爪音」がはっきり聞こえる (義甲で弾くため)
      - 高次倍音が最初の 0.1 秒で急速に消え、基音だけが残る
      - ピッチが弾いた瞬間わずかに高く、すぐ戻る (弦の張りが緩むため)
    """
    rng = rng or np.random.default_rng(m + 6500)
    f0 = midi2hz(m)
    dur = float(np.clip(5.0 - (m - 50) * 0.04, 1.4, 5.0))
    ks = np.arange(1, _n_partials(f0, 9000.0, cap=24, floor=10) + 1)
    ratios = (ks * np.sqrt(1.0 + 0.00020 * ks * ks)).tolist()
    b = 1.05 - 0.22 * vel
    amps = [(1.0 / (k ** b)) * (1.25 if k % 2 == 1 else 0.75) for k in ks]
    # 高次倍音ほど急速に減衰させる → 「ビン」と鳴ってすぐ丸くなる
    taus = [max(dur * 0.42 / (r ** 0.62), 0.05) for r in ratios]
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.002, rng=rng)

    # ピッチの初期偏差 (+18 セントから 60ms で戻る) を可変遅延で近似
    n = len(y)
    t = np.arange(n, dtype=np.float64) / sr
    dev = 0.0104 * np.exp(-t / 0.06)          # 18 cent ≈ 1.04%
    pos = np.clip(np.cumsum(1.0 + dev) - 1.0, 0, n - 1)
    y = np.interp(pos, np.arange(n), y.astype(np.float64)).astype(np.float32)

    # 爪音
    n_p = int(0.025 * sr)
    pk = dsp.bandpass(rng.standard_normal(n_p).astype(np.float32), 2000, 8000, taps=257)
    pk *= np.exp(-np.arange(n_p, dtype=np.float32) / (0.0025 * sr)) * 0.09 * vel
    y[:n_p] += pk
    return (y * (0.35 + 0.65 * vel)).astype(np.float32)


def celesta(m: int, vel: float = 0.8, sr: int = SR,
            rng: np.random.Generator | None = None) -> np.ndarray:
    """チェレスタ/グロッケン。冬・クリスマス系のきらめき"""
    rng = rng or np.random.default_rng(m + 4000)
    f0 = midi2hz(m)
    dur = float(np.clip(4.5 - (m - 60) * 0.03, 1.2, 4.5))
    ratios = [1, 2.0, 3.01, 4.2, 5.4, 6.8, 9.2, 12.1, 15.4]
    amps = [1.0, 0.55, 0.28, 0.16, 0.10, 0.06, 0.035, 0.020, 0.011]
    taus = [dur * 0.45, dur * 0.34, dur * 0.26, 0.75, 0.52, 0.36, 0.24, 0.16, 0.11]
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.002, rng=rng)
    return (y * (0.3 + 0.7 * vel)).astype(np.float32)


def singing_bowl(m: int, vel: float = 0.8, sr: int = SR,
                 rng: np.random.Generator | None = None) -> np.ndarray:
    """
    シンギングボウル / 大鐘。
    非整数比の部分音 + ゆっくりしたうなりが「癒し」の正体。
    瞑想・ヒーリング系の看板音。
    """
    rng = rng or np.random.default_rng(m + 5000)
    f0 = midi2hz(m)
    dur = 22.0
    ratios = [1.0, 2.76, 5.40, 8.93, 13.34, 18.64]
    amps = [1.0, 0.42, 0.24, 0.12, 0.06, 0.03]
    taus = [11.0, 7.0, 4.5, 2.6, 1.6, 1.0]
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.05,
                 rng=rng, beat_hz=0.32)
    return (y * (0.35 + 0.65 * vel)).astype(np.float32)


def marimba(m: int, vel: float = 0.8, sr: int = SR,
            rng: np.random.Generator | None = None) -> np.ndarray:
    """マリンバ/カリンバ。倍音が 1:4:10 なのが特徴"""
    rng = rng or np.random.default_rng(m + 6000)
    f0 = midi2hz(m)
    dur = 2.2
    ratios = [1.0, 3.99, 9.2, 15.0]
    amps = [1.0, 0.30, 0.10, 0.04]
    taus = [0.55, 0.16, 0.08, 0.05]
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.002, rng=rng)
    return (y * (0.3 + 0.7 * vel)).astype(np.float32)


def upright_bass(m: int, vel: float = 0.8, sr: int = SR,
                 rng: np.random.Generator | None = None) -> np.ndarray:
    """ウッドベース (ピチカート)。ジャズ/ボサ用"""
    rng = rng or np.random.default_rng(m + 7000)
    f0 = midi2hz(m)
    dur = 2.6
    ks = np.arange(1, _n_partials(f0, 3500.0, cap=34, floor=14) + 1)
    ratios = ks.tolist()
    amps = [1.0 / (k ** 1.20) for k in ks]
    taus = [0.85 / (1.0 + 0.28 * (k - 1)) for k in ks]
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.006, rng=rng)
    # 胴鳴りを足す
    y = dsp.peak_eq(y, 110.0, 3.0, q=1.2)
    return (y * (0.4 + 0.6 * vel)).astype(np.float32)


def sub_bass(m: int, vel: float = 0.8, sr: int = SR,
             rng: np.random.Generator | None = None) -> np.ndarray:
    """lofi / アンビエント用の丸いサイン系ベース"""
    rng = rng or np.random.default_rng(m + 8000)
    f0 = midi2hz(m)
    dur = 3.2
    ratios = [1.0, 2.0, 3.0]
    amps = [1.0, 0.13, 0.045]
    taus = [1.35, 0.5, 0.25]
    y = additive(f0, dur, ratios, amps, taus, sr=sr, attack=0.012, rng=rng)
    return (y * (0.4 + 0.6 * vel)).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# パッド / ドローン (持続音)
# ──────────────────────────────────────────────────────────────

def pad_voice(m: int, dur: float, sr: int = SR, brightness: float = 1.0,
              rng: np.random.Generator | None = None,
              n_detune: int = 3) -> np.ndarray:
    """
    パッドの 1 声部。デチューンした複数のノコギリ波をローパスに通す。
    アンビエント/睡眠系の土台。attack/release は呼び出し側で付ける。
    """
    rng = rng or np.random.default_rng(m + 9000)
    f0 = midi2hz(m)
    n = max(int(dur * sr), 16)
    t = np.arange(n, dtype=np.float32) / sr
    nyq = sr * 0.45
    out = np.zeros(n, dtype=np.float32)
    exp = 1.35 / max(brightness, 0.3)

    for v in range(n_detune):
        cents = (v - (n_detune - 1) / 2.0) * 7.0 + rng.uniform(-2.0, 2.0)
        f = f0 * (2.0 ** (cents / 1200.0))
        # 帯域制限ノコギリ波 (加算合成なのでエイリアシングが出ない)
        k = 1
        while f * k < nyq and k <= 40:
            a = 1.0 / (k ** exp)
            # -54dB より小さい倍音は聞こえないので打ち切る。
            # 暗いパッドでは 40 本のうち 15 本ほどで足りるため効果が大きい。
            if a < 0.002:
                break
            out += (a * np.sin(TWO_PI * f * k * t + rng.uniform(0, TWO_PI))
                    ).astype(np.float32)
            k += 1
    out /= n_detune * 2.0
    return out


def drone(m: int, dur: float, sr: int = SR, rng: np.random.Generator | None = None,
          partials: int = 12) -> np.ndarray:
    """
    睡眠・瞑想向けのドローン。
    倍音ごとに独立した超低速 LFO で振幅を揺らすと、
    「同じところに留まっているのに微かに動き続ける」音になる。

    重要: ドローンは減衰せず全長鳴り続けるので、各部分音の周波数を
    「ループ長でちょうど整数回振動する値」へスナップする。
    これをしないと、末尾→先頭で位相が飛んでプチッというノイズが出る。
    ずれ幅は 1/dur Hz (24分なら 0.0007Hz) なので聴感上は完全に同一。
    """
    rng = rng or np.random.default_rng(m + 11000)
    f0 = midi2hz(m)
    n = max(int(dur * sr), 16)
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, dtype=np.float32)
    nyq = sr * 0.45
    for k in range(1, partials + 1):
        f = f0 * k
        if f >= nyq:
            break
        # ループ長で整数周期になるようにスナップ
        cycles = max(round(f * n / sr), 1)
        f = cycles * sr / n
        a = 1.0 / (k ** 1.5)
        # 超低速 LFO も整数周期にする
        cyc = max(int(rng.integers(1, 5)), 1)
        mod = 0.65 + 0.35 * dsp.loop_lfo(n, cyc, phase=rng.uniform(0, TWO_PI))
        out += (a * mod * np.sin(TWO_PI * f * t + rng.uniform(0, TWO_PI))).astype(np.float32)
    return (out / max(partials * 0.25, 1.0)).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# 打楽器
# ──────────────────────────────────────────────────────────────

def kick(sr: int = SR, rng: np.random.Generator | None = None,
         f_start: float = 115.0, f_end: float = 46.0,
         decay: float = 0.42, click: float = 0.5) -> np.ndarray:
    """ピッチエンベロープ付きのキック"""
    rng = rng or np.random.default_rng(12000)
    n = int(0.65 * sr)
    t = np.arange(n, dtype=np.float32) / sr
    f = f_end + (f_start - f_end) * np.exp(-t / 0.028)
    ph = TWO_PI * np.cumsum(f) / sr
    y = np.sin(ph).astype(np.float32) * np.exp(-t / decay)
    n_c = int(0.006 * sr)
    y[:n_c] += (rng.standard_normal(n_c).astype(np.float32)
                * np.exp(-np.arange(n_c) / (0.0012 * sr)) * 0.35 * click)
    return dsp.fade(y * 0.9, fade_out=0.02)


def snare_soft(sr: int = SR, rng: np.random.Generator | None = None,
               tone: float = 190.0, decay: float = 0.16) -> np.ndarray:
    """lofi 向けの柔らかいスネア (高域を削って奥に置く)"""
    rng = rng or np.random.default_rng(13000)
    n = int(0.4 * sr)
    t = np.arange(n, dtype=np.float32) / sr
    nz = rng.standard_normal(n).astype(np.float32)
    nz = dsp.bandpass(nz, 320, 5200, taps=257)
    body = (np.sin(TWO_PI * tone * t) + 0.6 * np.sin(TWO_PI * tone * 1.58 * t))
    y = (nz * np.exp(-t / decay) * 0.8
         + body.astype(np.float32) * np.exp(-t / (decay * 0.55)) * 0.35)
    return dsp.fade(y * 0.55, fade_out=0.02)


def rimshot(sr: int = SR, rng: np.random.Generator | None = None) -> np.ndarray:
    """リムショット/クロススティック。lofi の 2・4 拍でよく使う"""
    rng = rng or np.random.default_rng(13500)
    n = int(0.18 * sr)
    t = np.arange(n, dtype=np.float32) / sr
    nz = dsp.bandpass(rng.standard_normal(n).astype(np.float32), 900, 4200, taps=257)
    tone = np.sin(TWO_PI * 420.0 * t).astype(np.float32)
    y = (nz * 0.55 + tone * 0.45) * np.exp(-t / 0.035)
    return dsp.fade(y * 0.5, fade_out=0.01)


def hihat(sr: int = SR, rng: np.random.Generator | None = None,
          decay: float = 0.05, open_hat: bool = False) -> np.ndarray:
    rng = rng or np.random.default_rng(14000)
    d = 0.42 if open_hat else decay
    n = int((0.7 if open_hat else 0.22) * sr)
    t = np.arange(n, dtype=np.float32) / sr
    nz = dsp.highpass(rng.standard_normal(n).astype(np.float32), 6500, order=3, taps=257)
    y = nz * np.exp(-t / d)
    return dsp.fade(y * 0.3, fade_out=0.01)


def brush(sr: int = SR, rng: np.random.Generator | None = None,
          length: float = 0.35, swell: bool = True) -> np.ndarray:
    """ジャズのブラシ。撫でるようなノイズのスウェル"""
    rng = rng or np.random.default_rng(15000)
    n = int(length * sr)
    t = np.arange(n, dtype=np.float32) / sr
    nz = dsp.bandpass(rng.standard_normal(n).astype(np.float32), 1800, 9000, taps=257)
    if swell:
        env = np.sin(np.pi * np.clip(t / length, 0, 1)) ** 1.5
    else:
        env = np.exp(-t / (length * 0.3))
    return dsp.fade((nz * env * 0.22).astype(np.float32), fade_in=0.005, fade_out=0.02)


def ride(sr: int = SR, rng: np.random.Generator | None = None) -> np.ndarray:
    """ライドシンバル。非整数比の金属倍音 + ノイズ"""
    rng = rng or np.random.default_rng(16000)
    n = int(1.4 * sr)
    t = np.arange(n, dtype=np.float32) / sr
    y = np.zeros(n, dtype=np.float32)
    for r, a, d in [(1.0, 0.5, 0.9), (1.73, 0.35, 0.6), (2.61, 0.28, 0.45),
                    (3.42, 0.2, 0.32), (4.9, 0.14, 0.22), (6.7, 0.1, 0.16)]:
        y += (a * np.exp(-t / d) * np.sin(TWO_PI * 520.0 * r * t
                                          + rng.uniform(0, TWO_PI))).astype(np.float32)
    nz = dsp.highpass(rng.standard_normal(n).astype(np.float32), 4000, taps=257)
    y += nz * np.exp(-t / 0.12) * 0.3
    return dsp.fade(y * 0.18, fade_out=0.05)


def shaker(sr: int = SR, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(17000)
    n = int(0.16 * sr)
    t = np.arange(n, dtype=np.float32) / sr
    nz = dsp.bandpass(rng.standard_normal(n).astype(np.float32), 4000, 12000, taps=257)
    env = np.sin(np.pi * np.clip(t / 0.09, 0, 1)) ** 2
    return dsp.fade((nz * env * 0.22).astype(np.float32), fade_out=0.02)


def sleigh_bells(sr: int = SR, rng: np.random.Generator | None = None) -> np.ndarray:
    """
    スレイベル (クリスマスの鈴)。
    小さな鈴が何十個も同時に鳴る音なので、単音ではなく
    5-9kHz に共鳴の集まったノイズとして作るのが正しい。
    """
    rng = rng or np.random.default_rng(18000)
    n = int(0.30 * sr)
    t = np.arange(n, dtype=np.float32) / sr
    nz = dsp.bandpass(rng.standard_normal(n).astype(np.float32), 4500, 10000, taps=257)
    # 鈴の共鳴 (ばらばらの高い正弦波を薄く重ねる)
    for _ in range(6):
        f = rng.uniform(5200, 8800)
        nz += (np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
               * np.exp(-t / 0.05) * 0.12).astype(np.float32)
    env = np.exp(-t / 0.075)
    return dsp.fade((nz * env * 0.20).astype(np.float32), fade_out=0.03)


def vinyl_crackle(n: int, rng: np.random.Generator, density: float = 42.0,
                  sr: int = SR) -> np.ndarray:
    """
    レコードのパチパチ + サーというヒスノイズ。
    lofi の空気感はほぼこれで決まる。ループ内で完結するよう作る。
    """
    hiss = dsp.looped_noise(n, rng, "pink") * 0.010
    crackle = np.zeros(n, dtype=np.float32)
    n_pops = int(density * n / sr)
    if n_pops > 0:
        pos = rng.integers(0, n, n_pops)
        amp = (rng.random(n_pops) ** 3.0) * 0.09
        # ポップ 1 個 = ごく短い減衰インパルス
        L = 90
        tt = np.arange(L, dtype=np.float32)
        shape = np.exp(-tt / 8.0) * np.sin(tt * 0.6)
        for p, a in zip(pos, amp):
            e = min(p + L, n)
            crackle[p:e] += (shape[:e - p] * a * rng.choice([-1.0, 1.0])).astype(np.float32)
    out = hiss + crackle
    return dsp.bandpass(out, 200.0, 11000.0, taps=257).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# サンプルバンク (キャッシュ)
# ──────────────────────────────────────────────────────────────

PITCHED = {
    "rhodes": rhodes,
    "piano": piano,
    "nylon": nylon_guitar,
    "harp": harp,
    "koto": koto,
    "celesta": celesta,
    "bowl": singing_bowl,
    "marimba": marimba,
    "upright": upright_bass,
    "subbass": sub_bass,
}

PERC = {
    "kick": kick,
    "snare": snare_soft,
    "rim": rimshot,
    "hat": hihat,
    "brush": brush,
    "ride": ride,
    "shaker": shaker,
    "sleigh": sleigh_bells,
}


@dataclass
class SampleBank:
    """
    (楽器, ピッチ, ベロシティ層, バリエーション) をキーにサンプルを貯める。
    同じ音でもバリエーションを複数持たせて回すと、機械的な反復感が薄れる。
    """
    seed: int = 0
    n_variants: int = 3
    vel_layers: tuple[float, ...] = (0.45, 0.72, 0.95)

    def __post_init__(self):
        self._cache: dict[tuple, np.ndarray] = {}
        self._rng = np.random.default_rng(self.seed)

    def note(self, inst: str, midi: int, vel: float = 0.8,
             variant: int | None = None) -> np.ndarray:
        # ベロシティを層に量子化してキャッシュヒット率を上げる
        li = int(np.argmin([abs(vel - v) for v in self.vel_layers]))
        if variant is None:
            variant = int(self._rng.integers(0, self.n_variants))
        key = (inst, int(midi), li, variant)
        s = self._cache.get(key)
        if s is None:
            rng = np.random.default_rng(
                (hash(key) & 0xFFFFFFFF) ^ (self.seed * 2654435761 & 0xFFFFFFFF))
            s = PITCHED[inst](int(midi), self.vel_layers[li], rng=rng)
            self._cache[key] = s
        # 層内の細かい強弱は加算時のゲインで表現する
        g = vel / self.vel_layers[li]
        return s if abs(g - 1.0) < 1e-3 else (s * g).astype(np.float32)

    def hit(self, name: str, variant: int | None = None, **kw) -> np.ndarray:
        if variant is None:
            variant = int(self._rng.integers(0, self.n_variants))
        key = ("P" + name, variant, tuple(sorted(kw.items())))
        s = self._cache.get(key)
        if s is None:
            rng = np.random.default_rng(
                (hash(key) & 0xFFFFFFFF) ^ (self.seed * 40503 & 0xFFFFFFFF))
            s = PERC[name](rng=rng, **kw)
            self._cache[key] = s
        return s

    def sustained(self, kind: str, midi: int, dur: float,
                  variant: int | None = None, **kw) -> np.ndarray:
        """
        パッド / ドローン。

        パッドは全トラック中で最も重い処理 (1 声部あたり数十本の倍音 × 数秒)。
        しかし実際には「同じ音程・同じ長さ」の組み合わせが何百回も出てくるので、
        キャッシュすると劇的に速くなる (24分のトラックで 1800 回 → 30 回程度)。

        位相まで完全に同じだと機械的に聞こえるため、バリエーションを
        複数持たせて順に使い回す。
        """
        if kind == "drone":
            # ドローンは 1 トラックに 1 回しか呼ばれないのでキャッシュ不要
            rng = np.random.default_rng((midi * 7919 + int(dur * 100)) ^ self.seed)
            return drone(midi, dur, rng=rng, **kw)

        if variant is None:
            variant = int(self._rng.integers(0, self.n_variants))
        key = ("PAD", int(midi), round(float(dur), 2), variant,
               tuple(sorted(kw.items())))
        s = self._cache.get(key)
        if s is None:
            rng = np.random.default_rng(
                (hash(key) & 0xFFFFFFFF) ^ (self.seed * 22695477 & 0xFFFFFFFF))
            s = pad_voice(midi, dur, rng=rng, **kw)
            self._cache[key] = s
        return s

    @property
    def size(self) -> int:
        return len(self._cache)
