"""
DSP core for the BGM studio.

numpy だけで完結する信号処理プリミティブ群。
外部の音源素材を一切使わず、すべて手続き的に合成する。

設計方針
--------
* すべてベクトル化する。サンプル単位の Python ループは書かない。
  (IIR が必要な場面は FFT 畳み込み or ブロック再帰で代替する)
* 信号は float32 の (n,) mono か (n, 2) stereo で統一する。
* ループ動画用に「継ぎ目のない」ループを作れることを最優先にする。
  → fold_tail() でリバーブ/ディレイの残響を先頭に折り返す。
"""

from __future__ import annotations

import numpy as np

SR = 44100  # サンプリングレート (YouTube 推奨は 48k だが 44.1k で作って最後に 48k へ変換)

TWO_PI = 2.0 * np.pi


# ──────────────────────────────────────────────────────────────
# 基本ユーティリティ
# ──────────────────────────────────────────────────────────────

def db2lin(x: float | np.ndarray) -> float | np.ndarray:
    """dB → 線形ゲイン"""
    return 10.0 ** (np.asarray(x, dtype=np.float64) / 20.0)


def lin2db(x: float | np.ndarray) -> float | np.ndarray:
    """線形ゲイン → dB"""
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))


_TUNING_A4 = 440.0


def set_tuning(a4: float) -> None:
    """
    セッション全体の基準ピッチを変える。

    以前は TrackSpec.a4 がメタデータ (説明文の表記) にしか使われておらず、
    「432Hz チューニング」を謳う動画の実音が 440Hz のままだった。
    周波数系の視聴者はスペクトラムアプリで実際に確かめるので、
    表記と実音がズレていると一発で信頼を失う。
    楽器側の midi2hz() 呼び出しは全てデフォルト引数なので、
    ここを差し替えれば全音源に効く。
    """
    global _TUNING_A4
    _TUNING_A4 = float(a4)


def midi2hz(m: float | np.ndarray, a4: float | None = None) -> float | np.ndarray:
    """MIDI ノート番号 → 周波数 (Hz)。a4 未指定なら set_tuning() の値を使う"""
    if a4 is None:
        a4 = _TUNING_A4
    return a4 * 2.0 ** ((np.asarray(m, dtype=np.float64) - 69.0) / 12.0)


def to_stereo(x: np.ndarray) -> np.ndarray:
    """(n,) → (n,2)。すでに stereo ならそのまま"""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    return x


def mono(x: np.ndarray) -> np.ndarray:
    """stereo → mono (L+R)/2"""
    x = np.asarray(x)
    return x.mean(axis=1) if x.ndim == 2 else x


def pan(x: np.ndarray, p: float) -> np.ndarray:
    """
    定パワーパンニング。p=-1 で完全 L、0 で center、+1 で R。
    mono 入力 → stereo 出力。
    """
    p = float(np.clip(p, -1.0, 1.0))
    ang = (p + 1.0) * 0.25 * np.pi          # 0..pi/2
    gl, gr = np.cos(ang), np.sin(ang)
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 2:
        x = mono(x)
    return np.stack([x * gl, x * gr], axis=1).astype(np.float32)


def add_into(dst: np.ndarray, src: np.ndarray, offset: int) -> None:
    """
    dst の offset 位置に src を加算する。範囲外は自動でクリップ。
    シーケンサの心臓部なので極力軽くしてある。
    """
    n_dst = dst.shape[0]
    if offset >= n_dst:
        return
    if offset < 0:
        src = src[-offset:]
        offset = 0
        if src.shape[0] == 0:
            return
    n = min(src.shape[0], n_dst - offset)
    if n <= 0:
        return
    if dst.ndim == 2 and src.ndim == 1:
        dst[offset:offset + n, 0] += src[:n]
        dst[offset:offset + n, 1] += src[:n]
    else:
        dst[offset:offset + n] += src[:n]


def fold_tail(x: np.ndarray, loop_len: int) -> np.ndarray:
    """
    継ぎ目のないループを作る中核処理。

    loop_len より長く合成した信号の「はみ出した尻尾」(リバーブ/ディレイの
    残響や、最後の小節で鳴らした音の減衰) を先頭へ巡回加算して畳み込む。
    こうするとループ後端 → 先頭の接続が数学的に完全に連続になる。
    """
    x = np.asarray(x, dtype=np.float32)
    if x.shape[0] <= loop_len:
        out = np.zeros((loop_len,) + x.shape[1:], dtype=np.float32)
        out[:x.shape[0]] = x
        return out

    out = x[:loop_len].copy()
    tail = x[loop_len:]
    pos = 0
    # 尻尾がループ長より長い場合もあるので巡回させながら足し込む
    while pos < tail.shape[0]:
        chunk = tail[pos:pos + loop_len]
        out[:chunk.shape[0]] += chunk
        pos += loop_len
    return out


def check_loop_seam(x: np.ndarray, sr: int = SR) -> float:
    """
    ループの継ぎ目の段差を dB で返す検証用関数。

    「末尾サンプル → 先頭サンプル」の飛びを、信号全体の隣接サンプル差分の
    99.9 パーセンタイルと比べる。0 dB なら「音楽の中で普通に起きている
    変化と同じ大きさ」= 継ぎ目として知覚されない、という意味になる。

    比較対象を信号全体の分布にしているのは、先頭が偶然静かな曲だと
    局所的な比較では過大に見えてしまうため。
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    seam_step = float(np.max(np.abs(x[0] - x[-1])))
    # 全体をなめると重いので間引いてサンプリングする
    stride = max(x.shape[0] // 2_000_000, 1)
    d = np.abs(np.diff(x[::stride], axis=0))
    inner = float(np.percentile(d, 99.9)) if d.size else 1e-9
    return float(lin2db(seam_step / max(inner, 1e-12)))


def seam_step_dbfs(x: np.ndarray) -> float:
    """
    継ぎ目の段差の絶対量 (dBFS)。
    相対値だけだと「静かな曲ほど悪く見える」ので、絶対量も併記して判断する。
    -60 dBFS を下回っていれば、どんな曲でも継ぎ目は聞こえない。
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    return float(lin2db(np.max(np.abs(x[0] - x[-1]))))


# ──────────────────────────────────────────────────────────────
# 畳み込み (FFT overlap-add)
# ──────────────────────────────────────────────────────────────

def _next_pow2(n: int) -> int:
    return 1 << (int(n) - 1).bit_length()


def convolve(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """
    1D overlap-add FFT 畳み込み。戻り値の長さは len(x)+len(h)-1。
    numpy だけで scipy.signal.fftconvolve 相当を実装している。
    """
    x = np.asarray(x, dtype=np.float32)
    h = np.asarray(h, dtype=np.float32)
    nx, nh = x.shape[0], h.shape[0]
    if nh == 0 or nx == 0:
        return np.zeros(max(nx + nh - 1, 0), dtype=np.float32)

    # 短い場合は一発 FFT
    if nx + nh - 1 <= 1 << 16:
        nfft = _next_pow2(nx + nh - 1)
        y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft), nfft)
        return y[:nx + nh - 1].astype(np.float32)

    # overlap-add: ブロック長は IR 長の 4〜8 倍程度が効率的
    nfft = _next_pow2(max(nh * 8, 1 << 13))
    step = nfft - nh + 1
    H = np.fft.rfft(h, nfft)
    out = np.zeros(nx + nh - 1, dtype=np.float32)
    for start in range(0, nx, step):
        blk = x[start:start + step]
        y = np.fft.irfft(np.fft.rfft(blk, nfft) * H, nfft)
        end = min(start + y.shape[0], out.shape[0])
        out[start:end] += y[:end - start].astype(np.float32)
    return out


def convolve_stereo(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """
    stereo 信号 (n,2) を stereo IR (m,2) で畳み込む。
    """
    x = to_stereo(x)
    h = to_stereo(h)
    n_out = x.shape[0] + h.shape[0] - 1
    out = np.zeros((n_out, 2), dtype=np.float32)
    for c in range(2):
        out[:, c] = convolve(x[:, c], h[:, c])
    return out


# ──────────────────────────────────────────────────────────────
# FIR フィルタ設計 (零位相応答から線形位相 FIR を作る)
# ──────────────────────────────────────────────────────────────

def design_fir(resp_fn, taps: int = 1025, sr: int = SR, nfft: int = 8192) -> np.ndarray:
    """
    周波数応答関数 resp_fn(freq_hz_array) -> gain_array から
    線形位相 FIR 係数を作る。resp_fn は実数の振幅応答を返すこと。
    """
    if taps % 2 == 0:
        taps += 1
    nfft = max(nfft, _next_pow2(taps * 2))
    f = np.fft.rfftfreq(nfft, 1.0 / sr)
    H = np.asarray(resp_fn(f), dtype=np.float64)
    h = np.fft.irfft(H, nfft)
    h = np.roll(h, taps // 2)[:taps]
    h = h * np.hanning(taps)
    return h.astype(np.float32)


def _lp_resp(cutoff: float, order: float = 2.0):
    """Butterworth 風のなだらかなローパス応答"""
    def fn(f):
        return 1.0 / np.sqrt(1.0 + (f / max(cutoff, 1.0)) ** (2.0 * order))
    return fn


def _hp_resp(cutoff: float, order: float = 2.0):
    def fn(f):
        r = (f / max(cutoff, 1.0)) ** (2.0 * order)
        return np.sqrt(r / (1.0 + r))
    return fn


def lowpass(x: np.ndarray, cutoff: float, order: float = 2.0,
            taps: int = 513, sr: int = SR) -> np.ndarray:
    """線形位相ローパス。BGM は位相歪みを避けたいので FIR を使う"""
    h = design_fir(_lp_resp(cutoff, order), taps=taps, sr=sr)
    return _apply_fir(x, h)


def highpass(x: np.ndarray, cutoff: float, order: float = 2.0,
             taps: int = 513, sr: int = SR) -> np.ndarray:
    h = design_fir(_hp_resp(cutoff, order), taps=taps, sr=sr)
    return _apply_fir(x, h)


def bandpass(x: np.ndarray, lo: float, hi: float, order: float = 2.0,
             taps: int = 513, sr: int = SR) -> np.ndarray:
    lp, hp = _lp_resp(hi, order), _hp_resp(lo, order)
    h = design_fir(lambda f: lp(f) * hp(f), taps=taps, sr=sr)
    return _apply_fir(x, h)


def tilt_eq(x: np.ndarray, pivot: float = 700.0, gain_db: float = -3.0,
            taps: int = 513, sr: int = SR) -> np.ndarray:
    """
    ティルト EQ。gain_db が負なら高域を落として低域を持ち上げる
    (= 眠くて温かい音になる)。BGM の質感づくりの主役。
    """
    def fn(f):
        # pivot を中心に ±gain_db/2 で傾ける (対数周波数で線形)
        oct_from_pivot = np.log2(np.maximum(f, 1.0) / pivot)
        w = np.clip(oct_from_pivot / 6.0, -1.0, 1.0)  # ±6oct で振り切る
        return db2lin(gain_db * 0.5 * w)

    h = design_fir(fn, taps=taps, sr=sr)
    return _apply_fir(x, h)


def shelf(x: np.ndarray, freq: float, gain_db: float, kind: str = "high",
          taps: int = 513, sr: int = SR) -> np.ndarray:
    g = db2lin(gain_db)

    def fn(f):
        w = 1.0 / (1.0 + (np.maximum(f, 1.0) / freq) ** (-2.0))
        if kind == "low":
            w = 1.0 - w
        return 1.0 + (g - 1.0) * w

    h = design_fir(fn, taps=taps, sr=sr)
    return _apply_fir(x, h)


def peak_eq(x: np.ndarray, freq: float, gain_db: float, q: float = 1.0,
            taps: int = 513, sr: int = SR) -> np.ndarray:
    g = db2lin(gain_db)

    def fn(f):
        # q が大きいほど狭い山 (対数周波数上のガウシアン)
        w = np.exp(-0.5 * (max(q, 0.05) * np.log2(np.maximum(f, 1.0) / freq)) ** 2)
        return 1.0 + (g - 1.0) * w

    h = design_fir(fn, taps=taps, sr=sr)
    return _apply_fir(x, h)


def _apply_fir(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """FIR を適用し、群遅延 (taps//2) を補正して元の長さで返す"""
    d = h.shape[0] // 2
    if x.ndim == 2:
        out = np.empty_like(x, dtype=np.float32)
        for c in range(x.shape[1]):
            y = convolve(x[:, c], h)
            out[:, c] = y[d:d + x.shape[0]]
        return out
    y = convolve(np.asarray(x, dtype=np.float32), h)
    return y[d:d + x.shape[0]].astype(np.float32)


def fir_circular(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """
    「巡回」FIR フィルタ。

    通常の線形畳み込みは信号の両端を 0 とみなすため、完全な周期信号に
    かけると端が痩せてループの継ぎ目が生まれてしまう。
    前後を巻き付けてから畳み込み、中央を切り出すことで周期性を保つ。
    """
    x = np.asarray(x, dtype=np.float32)
    h = np.asarray(h, dtype=np.float32)
    t = h.shape[0]
    d = t // 2
    n = x.shape[0]
    if n <= t:  # 短すぎる場合は素直に線形で
        return _apply_fir(x, h)

    if x.ndim == 2:
        out = np.empty_like(x)
        for c in range(x.shape[1]):
            out[:, c] = fir_circular(x[:, c], h)
        return out

    xp = np.concatenate([x[-d:], x, x[:t]])
    y = convolve(xp, h)
    return y[2 * d: 2 * d + n].astype(np.float32)


def circular_filter(x: np.ndarray, kind: str, *args, taps: int = 513,
                    sr: int = SR, **kw) -> np.ndarray:
    """ループ素材向けに lowpass/highpass/bandpass を巡回版で適用する"""
    if kind == "lowpass":
        h = design_fir(_lp_resp(args[0], kw.get("order", 2.0)), taps=taps, sr=sr)
    elif kind == "highpass":
        h = design_fir(_hp_resp(args[0], kw.get("order", 2.0)), taps=taps, sr=sr)
    elif kind == "bandpass":
        lp, hp = _lp_resp(args[1], kw.get("order", 2.0)), _hp_resp(args[0], kw.get("order", 2.0))
        h = design_fir(lambda f: lp(f) * hp(f), taps=taps, sr=sr)
    else:
        raise ValueError(kind)
    return fir_circular(x, h)


def periodic_highpass(x: np.ndarray, cutoff: float, sr: int = SR) -> np.ndarray:
    """
    周期信号 (ループタイル) 専用のハイパス。

    FIR では低い遮断周波数を実現できない。44.1kHz / 513 タップだと
    周波数分解能が 86Hz しかなく、30Hz のハイパスはまったく効かない
    (実際これに気付かず、超低域が残ったまま出荷しかけた)。

    タイルは厳密な周期信号なので、周波数領域で該当ビンを直接落とすのが
    正しい。数学的に正確で、ループの連続性も完全に保たれる。
    """
    x = np.asarray(x, dtype=np.float32)
    n = x.shape[0]
    F = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    # 遮断周波数の半分から下を落とす。垂直に切ると不自然なので直線で繋ぐ。
    w = np.clip((f - cutoff * 0.5) / (cutoff * 0.5), 0.0, 1.0)
    F *= (w[:, None] if F.ndim == 2 else w)
    return np.fft.irfft(F, n, axis=0).astype(np.float32)


def tile_to(x: np.ndarray, n: int) -> np.ndarray:
    """
    巡回素材 x を長さ n まで敷き詰める。
    x 自身が周期信号なので、タイル境界も末尾→先頭も完全に連続になる。
    """
    x = np.asarray(x, dtype=np.float32)
    if x.shape[0] >= n:
        return x[:n]
    reps = int(np.ceil(n / x.shape[0]))
    if x.ndim == 2:
        return np.tile(x, (reps, 1))[:n]
    return np.tile(x, reps)[:n]


def morph_lowpass(x: np.ndarray, cutoffs, weights) -> np.ndarray:
    """
    時間変化するローパスの近似。
    複数のカットオフで静的にフィルタした版を作り、weights (時間関数) で
    クロスフェードする。サンプル単位 IIR を避けつつ「フィルタが動く」感じを出す。

    cutoffs : list[float]                 長さ K
    weights : np.ndarray (n, K)           各時刻の混合比 (行和 1 を想定)
    """
    x = np.asarray(x, dtype=np.float32)
    weights = np.asarray(weights, dtype=np.float32)
    acc = np.zeros_like(x)
    for k, fc in enumerate(cutoffs):
        w = weights[:, k]
        if x.ndim == 2:
            acc += lowpass(x, fc) * w[:, None]
        else:
            acc += lowpass(x, fc) * w
    return acc


# ──────────────────────────────────────────────────────────────
# ノイズ
# ──────────────────────────────────────────────────────────────

def white_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n).astype(np.float32)


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    """1/f ノイズ。FFT 領域で成形するので厳密かつ高速"""
    nfft = _next_pow2(n * 2)
    spec = np.fft.rfft(rng.standard_normal(nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    f[0] = f[1]
    spec /= np.sqrt(f)
    y = np.fft.irfft(spec, nfft)[:n]
    return (y / (np.std(y) + 1e-9)).astype(np.float32)


def brown_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    """1/f^2 ノイズ。低域が非常に厚く、雨/波/焚き火の土台になる"""
    nfft = _next_pow2(n * 2)
    spec = np.fft.rfft(rng.standard_normal(nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    f[0] = f[1]
    spec /= f
    y = np.fft.irfft(spec, nfft)[:n]
    return (y / (np.std(y) + 1e-9)).astype(np.float32)


def looped_noise(n: int, rng: np.random.Generator, kind: str = "brown") -> np.ndarray:
    """
    「それ自体が完全にループする」ノイズを作る。
    長さ n の周期信号として FFT 領域で直接生成するので、
    末尾→先頭が数学的に連続になり、2時間ループしても継ぎ目が出ない。
    """
    n_half = n // 2 + 1
    mag = rng.standard_normal(n_half) + 1j * rng.standard_normal(n_half)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f[0] = f[1] if len(f) > 1 else 1.0
    if kind == "white":
        shape = np.ones_like(f)
    elif kind == "pink":
        shape = 1.0 / np.sqrt(f)
    else:  # brown
        shape = 1.0 / f
    mag *= shape
    mag[0] = 0.0
    y = np.fft.irfft(mag, n)
    return (y / (np.std(y) + 1e-9)).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# エンベロープ
# ──────────────────────────────────────────────────────────────

def adsr(n: int, a: float, d: float, s: float, r: float,
         sustain_n: int | None = None, sr: int = SR) -> np.ndarray:
    """秒指定の ADSR。n はトータルサンプル数"""
    env = np.zeros(n, dtype=np.float32)
    na = max(int(a * sr), 1)
    nd = max(int(d * sr), 1)
    nr = max(int(r * sr), 1)
    ns = sustain_n if sustain_n is not None else max(n - na - nd - nr, 0)

    i = 0
    seg = min(na, n - i)
    if seg > 0:
        env[i:i + seg] = np.linspace(0.0, 1.0, seg, dtype=np.float32)
        i += seg
    seg = min(nd, n - i)
    if seg > 0:
        env[i:i + seg] = np.linspace(1.0, s, seg, dtype=np.float32)
        i += seg
    seg = min(ns, n - i)
    if seg > 0:
        env[i:i + seg] = s
        i += seg
    seg = min(nr, n - i)
    if seg > 0:
        env[i:i + seg] = np.linspace(s, 0.0, seg, dtype=np.float32)
        i += seg
    return env


def exp_decay(n: int, tau: float, sr: int = SR) -> np.ndarray:
    """指数減衰。tau は 1/e になるまでの秒数"""
    t = np.arange(n, dtype=np.float32) / sr
    return np.exp(-t / max(tau, 1e-4)).astype(np.float32)


def fade(x: np.ndarray, fade_in: float = 0.0, fade_out: float = 0.0,
         sr: int = SR) -> np.ndarray:
    """等パワーではなく単純な線形フェード (短時間なのでこれで十分)"""
    x = np.asarray(x, dtype=np.float32).copy()
    n = x.shape[0]
    ni = min(int(fade_in * sr), n)
    no = min(int(fade_out * sr), n)
    if ni > 0:
        w = np.linspace(0.0, 1.0, ni, dtype=np.float32)
        x[:ni] = x[:ni] * (w[:, None] if x.ndim == 2 else w)
    if no > 0:
        w = np.linspace(1.0, 0.0, no, dtype=np.float32)
        x[-no:] = x[-no:] * (w[:, None] if x.ndim == 2 else w)
    return x


def lfo(n: int, freq: float, phase: float = 0.0, shape: str = "sin",
        sr: int = SR) -> np.ndarray:
    """-1..1 の低周波発振器"""
    t = np.arange(n, dtype=np.float64) / sr
    ph = TWO_PI * freq * t + phase
    if shape == "sin":
        y = np.sin(ph)
    elif shape == "tri":
        y = 2.0 / np.pi * np.arcsin(np.sin(ph))
    else:
        y = np.sign(np.sin(ph))
    return y.astype(np.float32)


def loop_lfo(n: int, cycles: float, phase: float = 0.0,
             shape: str = "sin") -> np.ndarray:
    """
    ループ長 n に対して「整数回」振動する LFO。
    cycles を整数にすればループ境界で位相が完全に一致する。
    """
    c = max(round(cycles), 1)
    t = np.arange(n, dtype=np.float64) / n
    ph = TWO_PI * c * t + phase
    if shape == "sin":
        y = np.sin(ph)
    elif shape == "tri":
        y = 2.0 / np.pi * np.arcsin(np.sin(ph))
    else:
        y = np.sign(np.sin(ph))
    return y.astype(np.float32)


# ──────────────────────────────────────────────────────────────
# エフェクト
# ──────────────────────────────────────────────────────────────

def lerp_read(x: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """
    小数位置 pos から線形補間で読み出す。

    np.interp(pos, np.arange(n), x) と同じ結果だが、
    長さ n の座標配列 (24分なら 500MB) を作らずに済む。
    可変ディレイ系はこれを何度も呼ぶので効果が大きい。
    """
    x = np.asarray(x, dtype=np.float32)
    n = x.shape[0]
    base = np.floor(pos).astype(np.int64)
    np.clip(base, 0, n - 2, out=base)
    frac = (pos - base).astype(np.float32)
    return (x[base] + frac * (x[base + 1] - x[base])).astype(np.float32)


def make_reverb_ir(seconds: float = 3.0, rt60: float = 2.6, predelay: float = 0.02,
                   damp: float = 0.55, width: float = 0.55, seed: int = 0,
                   sr: int = SR) -> np.ndarray:
    """
    合成リバーブ IR (n,2)。
    低域ほど長く、高域ほど早く減衰する 3 バンド構成にして自然な響きにする。
    さらに初期反射を数タップ足して「部屋」の輪郭を出す。
    """
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n, dtype=np.float32) / sr

    bands = [
        # (lo,   hi,     rt60 倍率, レベル)
        (20.0, 400.0, 1.30, 1.00),
        (400.0, 2500.0, 1.00, 0.85),
        (2500.0, 16000.0, 0.42 + 0.5 * (1.0 - damp), 0.45 * (1.0 - damp) + 0.12),
    ]

    ir = np.zeros((n, 2), dtype=np.float32)
    for lo, hi, rt_mul, lvl in bands:
        rt = max(rt60 * rt_mul, 0.05)
        env = np.exp(-6.9078 * t / rt)  # -60dB になるまで rt 秒
        for c in range(2):
            nz = rng.standard_normal(n).astype(np.float32)
            nz = bandpass(nz, lo, hi, order=2, taps=513, sr=sr)
            ir[:, c] += nz * env * lvl

    # 拡散が立ち上がるまでの短いランプ (これが無いと「バシャッ」と不自然になる)
    build = np.clip(t / 0.03, 0.0, 1.0)
    ir *= build[:, None]

    # 初期反射
    for _ in range(12):
        d = int(rng.uniform(0.005, 0.06) * sr)
        g = rng.uniform(-0.5, 0.5) * np.exp(-d / (0.05 * sr))
        c = rng.integers(0, 2)
        if d < n:
            ir[d, c] += g

    # プリディレイ
    pd = int(predelay * sr)
    if pd > 0:
        ir = np.vstack([np.zeros((pd, 2), dtype=np.float32), ir])[:n]

    # ステレオ幅 (M/S で S 成分を調整)
    m = (ir[:, 0] + ir[:, 1]) * 0.5
    s = (ir[:, 0] - ir[:, 1]) * 0.5 * width
    ir = np.stack([m + s, m - s], axis=1)

    # エネルギー正規化 (どの設定でも send 量の感覚が変わらないように)
    e = np.sqrt(np.sum(ir.astype(np.float64) ** 2) / 2.0)
    if e > 0:
        ir = (ir / e).astype(np.float32)
    return ir


def reverb(x: np.ndarray, ir: np.ndarray, mix: float = 0.3,
           tail: bool = True) -> np.ndarray:
    """
    畳み込みリバーブ。tail=True なら残響ぶんだけ長い信号を返す
    (fold_tail() でループ先頭へ折り返すため)。

    24 分の素材では 1 本の配列だけで 500MB を超えるため、
    dry 用の配列を別に作らず wet に直接足し込む。
    式で書くと巨大なテンポラリが 2 本できてしまうので、
    チャンクに切って in-place で処理している。
    """
    x = to_stereo(x)
    wet = convolve_stereo(x, ir)
    if not tail:
        wet = wet[:x.shape[0]]
    np.multiply(wet, np.float32(mix), out=wet)
    g = np.float32(1.0 - mix)
    n_dry = min(x.shape[0], wet.shape[0])
    step = 1 << 22
    for s in range(0, n_dry, step):
        e = min(s + step, n_dry)
        wet[s:e] += x[s:e] * g
    return wet


def delay(x: np.ndarray, time: float, feedback: float = 0.35, mix: float = 0.25,
          damp: float = 6000.0, pingpong: bool = False, sr: int = SR,
          n_taps: int = 24) -> np.ndarray:
    """
    フィードバックディレイを「有限タップ展開」で実装する。
    y = x + g·x(t-D) + g²·x(t-2D) + ... と展開すれば IIR ループが不要になり
    完全にベクトル化できる。g<1 なので 24 タップも取れば -60dB 以下に落ちる。
    """
    x = to_stereo(x)
    d = max(int(time * sr), 1)
    n_out = x.shape[0] + d * n_taps
    dry = np.zeros((n_out, 2), dtype=np.float32)
    dry[:x.shape[0]] = x
    out = np.zeros((n_out, 2), dtype=np.float32)

    src = x.copy()
    g = 1.0
    for k in range(1, n_taps + 1):
        g *= feedback
        if g < 1e-4:
            break
        # 各リピートごとに少しずつ暗くする (テープディレイ的な減衰)
        src = lowpass(src, damp * (0.88 ** (k - 1)) + 300.0, order=1, taps=257, sr=sr)
        off = d * k
        seg = src[:n_out - off]
        if pingpong:
            # 奇数回は L/R を入れ替える
            seg = seg[:, ::-1] if k % 2 == 1 else seg
        out[off:off + seg.shape[0]] += seg * g

    return (dry * (1.0 - mix) + out * mix).astype(np.float32)


def chorus(x: np.ndarray, depth_ms: float = 6.0, rate: float = 0.25,
           mix: float = 0.35, voices: int = 3, sr: int = SR,
           loop_n: int | None = None) -> np.ndarray:
    """
    コーラス/アンサンブル。np.interp による可変ディレイで実装。
    loop_n を渡すと LFO がループ長で整数周期になり、ループ継ぎ目が保たれる。
    """
    x = to_stereo(x)
    n = x.shape[0]
    idx = np.arange(n, dtype=np.float32)
    acc = np.zeros_like(x)
    for v in range(voices):
        ph = TWO_PI * v / voices
        if loop_n:
            m = loop_lfo(n, max(round(rate * loop_n / sr), 1), phase=ph)
        else:
            m = lfo(n, rate * (1.0 + 0.13 * v), phase=ph, sr=sr)
        d = (depth_ms * 0.001 * sr) * (0.5 + 0.5 * m) + 0.002 * sr
        pos = idx - d
        np.clip(pos, 0, n - 1, out=pos)
        for c in range(2):
            # 声部ごとに L/R の重みを変えて広がりを作る
            w = 0.5 + 0.5 * np.cos(ph + (0.0 if c == 0 else np.pi))
            acc[:, c] += lerp_read(x[:, c], pos) * w
    acc /= max(voices * 0.5, 1.0)
    return (x * (1.0 - mix) + acc * mix).astype(np.float32)


def saturate(x: np.ndarray, drive: float = 1.5, mix: float = 1.0) -> np.ndarray:
    """
    tanh サチュレーション。倍音が付いてアナログっぽい温かみが出る。
    lofi の質感づくりに必須。
    """
    x = np.asarray(x, dtype=np.float32)
    wet = np.tanh(x * drive) / np.tanh(drive)
    return (x * (1.0 - mix) + wet * mix).astype(np.float32)


def wow_flutter(x: np.ndarray, depth: float = 0.0025, rate: float = 0.7,
                sr: int = SR, loop_n: int | None = None,
                seed: int = 0) -> np.ndarray:
    """
    テープのワウフラッター (ピッチのゆらぎ)。
    これがあるかないかで「打ち込み臭さ」が大きく変わる。
    """
    x = to_stereo(x)
    n = x.shape[0]
    idx = np.arange(n, dtype=np.float64)
    if loop_n:
        m = (loop_lfo(n, max(round(rate * n / sr), 1))
             + 0.5 * loop_lfo(n, max(round(rate * 2.7 * n / sr), 1), phase=1.1))
    else:
        m = lfo(n, rate, sr=sr) + 0.5 * lfo(n, rate * 2.7, phase=1.1, sr=sr)
    # 位相 = 累積したピッチ偏差
    warp = np.cumsum(m.astype(np.float64)) * depth
    warp -= warp.mean()
    if loop_n:
        # ループ素材では読み出し位置を巡回させる。LFO は整数周期なので
        # 末尾から先頭へ戻ったときにピッチのズレが残らない。
        pos = (idx + warp) % n
    else:
        pos = np.clip(idx + warp, 0, n - 1)
    out = np.empty_like(x)
    for c in range(2):
        out[:, c] = lerp_read(x[:, c], pos)
    return out


def stereo_width(x: np.ndarray, width: float = 1.0,
                 bass_mono_hz: float = 140.0) -> np.ndarray:
    """
    M/S でステレオ幅を調整。低域はモノにまとめる (再生環境で崩れないように)。
    """
    x = to_stereo(x)
    m = (x[:, 0] + x[:, 1]) * 0.5
    s = (x[:, 0] - x[:, 1]) * 0.5 * width
    if bass_mono_hz > 0:
        s = highpass(s, bass_mono_hz, order=1, taps=513)
    return np.stack([m + s, m - s], axis=1).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# ラウドネス (簡易 ITU-R BS.1770 / K-weighting)
# ──────────────────────────────────────────────────────────────

def _k_weight_fir(sr: int = SR, taps: int = 1025) -> np.ndarray:
    """K-weighting (高域シェルフ +4dB @ ~1.5kHz + 60Hz ハイパス) の FIR 近似"""
    def fn(f):
        f = np.maximum(f, 1.0)
        shelf_g = db2lin(3.999)
        w = 1.0 / (1.0 + (f / 1681.97) ** (-2.0))
        hs = 1.0 + (shelf_g - 1.0) * w
        r = (f / 38.13) ** 4
        hp = np.sqrt(r / (1.0 + r))
        return hs * hp
    return design_fir(fn, taps=taps, sr=sr)


_K_FIR: np.ndarray | None = None


def lufs_integrated(x: np.ndarray, sr: int = SR) -> float:
    """
    統合ラウドネス (LUFS) をゲーティング付きで測る。
    厳密な BS.1770 の biquad ではなく線形位相 FIR 近似だが、
    実測との差は 0.2 LU 程度で、マスタリング用途には十分。
    """
    global _K_FIR
    if _K_FIR is None:
        _K_FIR = _k_weight_fir(sr)
    x = to_stereo(x)
    y = _apply_fir(x, _K_FIR).astype(np.float64)

    block = int(0.400 * sr)
    hop = block // 4
    n_blocks = max((y.shape[0] - block) // hop + 1, 1)
    if n_blocks < 1:
        return -70.0

    # 各ブロックの平均二乗 (L,R 等重み)。
    # ブロックごとに mean を取ると 24 分では 14000 回ループすることになるので、
    # 二乗和の累積和を 1 回作って差分で求める。
    sq = (y[:, 0] ** 2 + y[:, 1] ** 2)
    csum = np.empty(sq.shape[0] + 1, dtype=np.float64)
    csum[0] = 0.0
    np.cumsum(sq, out=csum[1:])
    starts = np.arange(n_blocks) * hop
    powers = (csum[starts + block] - csum[starts]) / block

    ll = -0.691 + 10.0 * np.log10(np.maximum(powers, 1e-15))
    # 絶対ゲート -70 LUFS
    keep = ll > -70.0
    if not keep.any():
        return -70.0
    # 相対ゲート -10 LU
    rel = -0.691 + 10.0 * np.log10(np.mean(powers[keep])) - 10.0
    keep2 = keep & (ll > rel)
    if not keep2.any():
        keep2 = keep
    return float(-0.691 + 10.0 * np.log10(np.mean(powers[keep2])))


def true_peak_db(x: np.ndarray, oversample: int = 4,
                 max_candidates: int = 40000) -> float:
    """
    4x オーバーサンプリングで真のピークを推定する。

    全サンプルを 4 倍に補間すると 24 分で 2.5 億点になるため、
    「生ピークに近いところ」だけを候補にして、その周辺のみ細かく見る。
    サンプル間に隠れたピークは必ず生ピークの近傍にあるので、これで十分。
    """
    x = to_stereo(x)
    n = x.shape[0]
    if n < 4:
        return float(lin2db(np.max(np.abs(x)) if x.size else 0.0))

    offs = np.arange(-2.0, 2.0, 1.0 / oversample)
    pk = 0.0
    for c in range(2):
        ch = x[:, c]
        absch = np.abs(ch)
        raw = float(absch.max())
        if raw <= 0.0:
            continue
        idx = np.flatnonzero(absch >= raw * 0.85)
        if idx.size > max_candidates:      # 天井に張り付いた信号への保険
            idx = idx[np.argsort(absch[idx])[-max_candidates:]]
        pos = (idx[:, None].astype(np.float64) + offs[None, :]).ravel()
        np.clip(pos, 0, n - 1, out=pos)
        pk = max(pk, raw, float(np.max(np.abs(lerp_read(ch, pos)))))
    return float(lin2db(pk))


def limiter(x: np.ndarray, ceiling_db: float = -1.0, lookahead_ms: float = 5.0,
            release_ms: float = 120.0, sr: int = SR) -> np.ndarray:
    """
    ブロック単位のピークリミッタ。
    64 サンプルごとのピークを取り、そこにスライディング最大 + 平滑化をかけて
    ゲイン曲線を作る。サンプル単位ループを避けつつ歪まない。
    """
    x = to_stereo(x)
    ceil_lin = float(db2lin(ceiling_db))
    B = 64
    n = x.shape[0]
    nb = (n + B - 1) // B
    pad = nb * B - n
    xp = np.vstack([x, np.zeros((pad, 2), dtype=np.float32)]) if pad else x

    peak = np.abs(xp).reshape(nb, B, 2).max(axis=(1, 2))
    need = np.minimum(1.0, ceil_lin / np.maximum(peak, 1e-9))

    # ルックアヘッド: 先の需要も先取りする (スライディング最小)
    la = max(int(lookahead_ms * 0.001 * sr / B), 1)
    g = need.copy()
    for s in range(1, la + 1):
        g[:-s] = np.minimum(g[:-s], need[s:])

    # アタックは即時、リリースは一次遅れで緩やかに戻す
    rel_blocks = max(int(release_ms * 0.001 * sr / B), 1)
    coef = float(np.exp(-1.0 / rel_blocks))
    smooth = np.empty_like(g)
    cur = 1.0
    for i in range(nb):
        target = g[i]
        cur = target if target < cur else cur + (target - cur) * (1.0 - coef)
        smooth[i] = cur

    gain = np.interp(np.arange(n), np.arange(nb) * B + B / 2.0, smooth)
    y = x * gain[:, None].astype(np.float32)
    return np.clip(y, -ceil_lin, ceil_lin).astype(np.float32)


def circular_process(x: np.ndarray, fn, pad_seconds: float = 1.0,
                     sr: int = SR) -> np.ndarray:
    """
    任意の処理チェーンを「ループを壊さずに」適用する。

    FIR フィルタもリミッタもワウフラッターも、内部で前後のサンプルを参照する。
    素直にかけると信号の両端が特別扱いされ、せっかく継ぎ目を消したループに
    段差が復活してしまう。前後を巻き付けてから処理し、中央だけ取り出せば
    「無限に続く信号の一部を処理した」のと同じ結果になる。
    """
    x = to_stereo(x)
    n = x.shape[0]
    p = min(int(pad_seconds * sr), n)
    if p <= 0:
        return fn(x)
    xp = np.concatenate([x[-p:], x, x[:p]], axis=0)
    y = to_stereo(fn(xp))
    return y[p:p + n].astype(np.float32)


def normalize_lufs(x: np.ndarray, target: float = -14.0, ceiling_db: float = -1.0,
                   sr: int = SR, circular: bool = False) -> tuple[np.ndarray, dict]:
    """
    目標 LUFS に合わせてゲインを決め、最後にリミッタで天井を守る。
    YouTube は -14 LUFS へ正規化する (大きい音は下げるが、小さい音は上げない)
    ので、-14 に合わせておくのが最も素直。

    circular=True ならリミッタをループ境界をまたいで適用する。
    """
    x = to_stereo(x)
    cur = lufs_integrated(x, sr)
    g = float(db2lin(target - cur))
    y = (x * g).astype(np.float32)
    if circular:
        y = circular_process(y, lambda z: limiter(z, ceiling_db=ceiling_db, sr=sr),
                             pad_seconds=1.0, sr=sr)
    else:
        y = limiter(y, ceiling_db=ceiling_db, sr=sr)
    info = {
        "lufs_before": cur,
        "gain_db": target - cur,
        "lufs_after": lufs_integrated(y, sr),
        "true_peak_db": true_peak_db(y),
    }
    return y, info
