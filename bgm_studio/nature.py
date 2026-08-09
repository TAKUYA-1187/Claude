"""
自然音・環境音レイヤ。

BGM 動画で滞在時間を伸ばす最大の武器がこれ。音楽単体より、
雨・焚き火・波・カフェの喧騒を薄く敷いたほうが「つけっぱなし」にされやすい。

設計
----
制約は「長さ n で完全にループすること」。2 時間ぶんを ffmpeg で
ループ結合しても継ぎ目が出てはいけない。そこで:

  1. ノイズ床は「巡回タイル」を作って敷き詰める。
     フィルタも巡回版を使うのでタイル境界は数学的に連続。

     ただしタイルは 1 枚では絶対に足りない。ここは実際に間違えて、
     視聴者に動画を消された。「フィルタ済みノイズなら反復は
     聞こえない」というのは誤りで、測ると相関はちょうど 1.0000 —
     同じ 14 秒が動画全体で 630 回鳴っていた。
     長さの違う 3 枚を、反復回数が互いに素になるように重ねる
     (_tile_set)。詳しい理由はその docstring に書いた。
  2. 目立つ単発音 (雨粒・薪のはぜる音・食器) は全長にわたって
     ばら撒く。ここに反復パターンが出ると一発でバレるため。
  3. ゆっくりした変調はすべて loop_lfo() で整数周期にする。

この分担のおかげで、24 分ぶんの環境音でも数秒で生成できる。
"""

from __future__ import annotations

import numpy as np

from . import dsp
from .dsp import SR


# ──────────────────────────────────────────────────────────────
# 内部ヘルパ
# ──────────────────────────────────────────────────────────────

def _tile_len(n: int, target_sec: float, sr: int = SR) -> int:
    """
    n を割り切る中で target_sec に最も近いタイル長を返す。
    割り切れないと最後のタイルが途中で切れてループの継ぎ目になる。
    """
    target = max(int(target_sec * sr), 1)
    k0 = max(int(round(n / target)), 1)
    for delta in range(0, k0 + 64):
        for k in (k0 - delta, k0 + delta):
            if k >= 1 and n % k == 0:
                return n // k
    return n


def _tile_set(n: int, target_sec: float, count: int = 3,
              sr: int = SR) -> list[int]:
    """
    「反復回数がどの 2 つを取っても互いに素」なタイル長を count 枚返す。

    ここは一度作り方を間違えていて、視聴者に動画を消された原因になった。
    タイルを 1 枚だけ敷くと、そのタイルが数百回そのまま繰り返される。
    実測すると、タイル長ぶんずらした波形との相関がちょうど 1.0000 —
    つまり完全に同一の 14 秒が 24 分ループ内で 105 回、
    動画全体では 630 回鳴っていた。人間は繰り返されるノイズを
    驚くほど正確に聞き分けるので (noise memory)、これが
    「機械的な雑音」として耳につく。

    対策は 2 つを同時にかける:
      1. 反復回数を互いに素にする
         → 合成波形が元に戻るのは lcm = n のときだけ。
           つまりループ 1 周ぶん、同じ並びが二度と現れない。
      2. 枚数を増やし、1 枚あたりの寄与を下げる
         → タイル周期での相関は 1/count まで落ちる。
           3 枚なら 0.33。残り 2/3 は毎回違う音なので埋もれる。

    さらに呼び出し側でタイル自体を長く (50 秒前後) 取り、
    そもそもの反復回数を 105 回から 25 回程度まで減らしている。
    """
    target = max(int(target_sec * sr), 1)
    k0 = max(int(round(n / target)), 1)

    cands: list[int] = []
    for delta in range(0, 4096):
        for k in (k0 - delta, k0 + delta):
            if k >= 1 and n % k == 0 and k not in cands:
                cands.append(k)
        if len(cands) >= 64:
            break
    if not cands:
        return [n]

    picked: list[int] = []
    for k in cands:
        if all(np.gcd(k, p) == 1 for p in picked):
            picked.append(k)
            if len(picked) == count:
                break
    return [n // k for k in picked]


def _bed(n: int, seed: int, kind: str, band: tuple[float, float] | None = None,
         lp: float | None = None, hp: float | None = None,
         tile_sec: float = 50.0, order: float = 2.0, sr: int = SR) -> np.ndarray:
    """
    巡回ノイズタイルを作り、巡回フィルタをかけて n まで敷き詰める。
    反復が耳につかないよう、長さの違う複数枚を重ねる (_tile_set 参照)。
    """
    # 20Hz 未満は誰にも聞こえないのに、音量だけはしっかり食う。
    # ここも一度やらかしていて、実測すると
    #   焚き火 99.8% / 部屋鳴り 100% / ブラウンノイズ 99.9%
    # が 20Hz 未満だった。つまり「環境音を音楽の -16dB に置く」つもりが、
    # 聞こえない超低域を -16dB に置いていただけで、
    # 肝心の焚き火の音は -43dB 相当まで埋もれていた。
    # おまけにこの超低域がリミッタを叩くので、可聴帯域が余計に潰れる。
    # タイルの基本周期 (1/50秒 = 0.02Hz) が 1/f 整形で暴れるのが原因。
    HP_FLOOR = 30.0
    hp_eff = max(hp or 0.0, HP_FLOOR)

    def lay(L: int, s: int) -> np.ndarray:
        tile = dsp.looped_noise(L, np.random.default_rng(s), kind)
        if band is not None:
            tile = dsp.circular_filter(tile, "bandpass", band[0], band[1], order=order)
        if lp is not None:
            tile = dsp.circular_filter(tile, "lowpass", lp, order=order)
        tile = dsp.periodic_highpass(tile, hp_eff, sr)
        tile = (tile / (np.std(tile) + 1e-9)).astype(np.float32)
        return dsp.tile_to(tile, n)

    lens = _tile_set(n, tile_sec, count=3, sr=sr)
    out = lay(lens[0], seed)
    for i, L in enumerate(lens[1:], start=1):
        out += lay(L, seed + 7919 * i)
    return (out / (np.std(out) + 1e-9)).astype(np.float32)


def _scatter(dst: np.ndarray, sample: np.ndarray, positions, gains) -> None:
    """
    単発イベントを巡回加算する。末尾を越えたぶんは先頭へ回り込ませるので、
    ループしても「継ぎ目の直前だけイベントが途切れる」ことがない。
    """
    n = dst.shape[0]
    L = sample.shape[0]
    for p, g in zip(positions, gains):
        p = int(p) % n
        end = p + L
        if end <= n:
            dst[p:end] += sample * g
        else:
            first = n - p
            dst[p:] += sample[:first] * g
            wrap = min(L - first, n)
            dst[:wrap] += sample[first:first + wrap] * g


def _width(x: np.ndarray, w: float = 0.6) -> np.ndarray:
    """ループを壊さない簡易ステレオ幅 (M/S を単純にスケールするだけ)"""
    m = (x[:, 0] + x[:, 1]) * 0.5
    s = (x[:, 0] - x[:, 1]) * 0.5 * w
    return np.stack([m + s, m - s], axis=1).astype(np.float32)


# ──────────────────────────────────────────────────────────────
# 雨
# ──────────────────────────────────────────────────────────────

def rain(n: int, seed: int = 0, intensity: float = 0.6,
         window: bool = True, sr: int = SR) -> np.ndarray:
    """
    雨音。
    土台のピンクノイズ + 個々の雨粒のトランジェント。
    window=True なら「窓越しの雨」らしく高域を大きく削る (就寝前向け)。
    """
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2), dtype=np.float32)

    for c in range(2):
        if window:
            base = _bed(n, seed * 7 + c + 1, "pink",
                        lp=1600.0 + 900.0 * intensity, hp=80.0, tile_sec=55.0)
        else:
            base = _bed(n, seed * 7 + c + 1, "pink", band=(200.0, 9000.0), tile_sec=55.0)
        # 降りの強弱をゆっくり揺らす (整数周期なのでループが保たれる)
        swell = 0.78 + 0.22 * dsp.loop_lfo(n, 3 + c, phase=c * 0.9)
        out[:, c] = base * swell

    # 雨粒 (近くに落ちる粒だけ個別イベントとして足す)
    L = int(0.020 * sr)
    t = np.arange(L, dtype=np.float32) / sr
    for c in range(2):
        drop = (np.sin(2 * np.pi * rng.uniform(1400, 3200) * t)
                * np.exp(-t / 0.0022)).astype(np.float32)
        n_drops = int(90 * intensity * n / sr)
        pos = rng.integers(0, n, n_drops)
        gains = (rng.random(n_drops) ** 2.6).astype(np.float32) * 0.22
        _scatter(out[:, c], drop, pos, gains)

    out *= 0.5 * (0.55 + 0.75 * intensity)
    return _width(out, 0.6)


def thunder(n: int, seed: int = 0, count: int = 2, sr: int = SR) -> np.ndarray:
    """遠雷。数分に 1 回だけ低くゴロゴロ鳴らす程度が上品"""
    rng = np.random.default_rng(seed + 51)
    out = np.zeros((n, 2), dtype=np.float32)
    for _ in range(count):
        L = int(rng.uniform(3.5, 7.0) * sr)
        nz = dsp.brown_noise(L, rng)
        env = np.exp(-np.arange(L, dtype=np.float32) / (0.9 * sr))
        env *= 0.4 + 0.6 * np.abs(dsp.lfo(L, rng.uniform(0.6, 1.4), sr=sr))
        body = dsp.lowpass(nz * env, 220.0, order=3)
        body = dsp.fade(body, fade_in=0.05, fade_out=0.5)
        p = int(rng.integers(0, n))
        for c in range(2):
            _scatter(out[:, c], (body * rng.uniform(0.7, 1.0)).astype(np.float32),
                     [p], [0.5])
    return out


# ──────────────────────────────────────────────────────────────
# 焚き火 / 暖炉
# ──────────────────────────────────────────────────────────────

def fireplace(n: int, seed: int = 0, sr: int = SR) -> np.ndarray:
    """暖炉。低いゴーッという燃焼音 + パチパチはぜる音"""
    rng = np.random.default_rng(seed + 101)
    out = np.zeros((n, 2), dtype=np.float32)

    for c in range(2):
        base = _bed(n, seed * 13 + c + 1, "brown", band=(45.0, 900.0), tile_sec=50.0)
        flick = 0.7 + 0.3 * (dsp.loop_lfo(n, 5 + c, phase=c) * 0.6
                             + dsp.loop_lfo(n, 11, phase=c * 2.1) * 0.4)
        out[:, c] = base * flick * 0.9

    # はぜる音 (crackle)
    for c in range(2):
        L = int(0.06 * sr)
        t = np.arange(L, dtype=np.float32) / sr
        pop = (dsp.bandpass(rng.standard_normal(L).astype(np.float32), 700, 6500,
                            taps=257) * np.exp(-t / 0.006)).astype(np.float32)
        n_pop = int(7.0 * n / sr)
        pos = rng.integers(0, n, n_pop)
        gains = (rng.random(n_pop) ** 2.2).astype(np.float32) * 0.55
        _scatter(out[:, c], pop, pos, gains)

    return _width(out * 0.55, 0.6)


# ──────────────────────────────────────────────────────────────
# 波 / 海
# ──────────────────────────────────────────────────────────────

def ocean(n: int, seed: int = 0, period: float = 9.0, sr: int = SR) -> np.ndarray:
    """
    波。周期的に寄せて返す振幅エンベロープが命。
    ループ長 n に対して整数回だけ寄せるように周期を丸める。
    """
    cycles = max(round(n / sr / period), 1)
    out = np.zeros((n, 2), dtype=np.float32)

    for c in range(2):
        # 砕ける瞬間だけ高域が出るので、2 帯域を別エンベロープで動かす
        low = _bed(n, seed * 17 + c + 1, "pink", lp=700.0, tile_sec=55.0)
        high = _bed(n, seed * 17 + c + 41, "pink", band=(900.0, 7000.0), tile_sec=55.0)

        ph = dsp.loop_lfo(n, cycles + c, phase=c * 0.6)
        swell = (0.5 + 0.5 * ph) ** 1.8                       # ゆっくり寄せる
        crash = np.clip(swell - 0.45, 0.0, None) ** 2.2 * 2.2  # 砕ける瞬間

        out[:, c] = low * swell * 0.9 + high * crash * 0.55

    return _width(out * 0.5, 0.55)


# ──────────────────────────────────────────────────────────────
# 風 / 森 / 夜
# ──────────────────────────────────────────────────────────────

def wind(n: int, seed: int = 0, sr: int = SR) -> np.ndarray:
    """風。カットオフの動きを 3 段のクロスフェードで近似する"""
    out = np.zeros((n, 2), dtype=np.float32)
    for c in range(2):
        b1 = _bed(n, seed * 19 + c + 1, "pink", lp=350.0, tile_sec=50.0)
        b2 = _bed(n, seed * 19 + c + 1, "pink", lp=900.0, tile_sec=50.0)
        b3 = _bed(n, seed * 19 + c + 1, "pink", lp=2200.0, tile_sec=50.0)
        m = 0.5 + 0.5 * (dsp.loop_lfo(n, 2 + c, phase=c * 1.3) * 0.6
                         + dsp.loop_lfo(n, 7, phase=c * 0.4) * 0.4)
        out[:, c] = b1 * (1 - m) ** 2 + b2 * (2 * m * (1 - m)) + b3 * m ** 2
    return _width(out * 0.4, 0.55)


def night_ambience(n: int, seed: int = 0, sr: int = SR) -> np.ndarray:
    """夏の夜。虫の声 (規則的なチャープ) + 微かな風"""
    rng = np.random.default_rng(seed + 401)
    out = np.zeros((n, 2), dtype=np.float32)

    L = int(0.035 * sr)
    t = np.arange(L, dtype=np.float32) / sr
    for c in range(2):
        f = rng.uniform(4200, 5200)
        chirp = (np.sin(2 * np.pi * f * t) * np.sin(2 * np.pi * 180 * t)
                 * np.exp(-((t - 0.017) / 0.010) ** 2)).astype(np.float32)
        step = int(sr * rng.uniform(0.42, 0.52))
        base = np.arange(0, n, step)
        pos = base + rng.integers(-600, 600, base.shape[0])
        gains = (0.5 + 0.5 * rng.random(base.shape[0])).astype(np.float32) * 0.07
        _scatter(out[:, c], chirp, pos, gains)

    out += wind(n, seed + 7) * 0.35
    return (out * 0.8).astype(np.float32)


def forest_birds(n: int, seed: int = 0, sr: int = SR) -> np.ndarray:
    """朝の森。小鳥のさえずりをまばらに"""
    rng = np.random.default_rng(seed + 501)
    out = np.zeros((n, 2), dtype=np.float32)
    for c in range(2):
        n_calls = int(6.0 * n / sr)
        for _ in range(n_calls):
            L = max(int(rng.uniform(0.08, 0.22) * sr), 64)
            t = np.arange(L, dtype=np.float32) / sr
            f0 = rng.uniform(2200, 4200)
            sweep = f0 * (1.0 + rng.uniform(-0.35, 0.45) * (t / t[-1]))
            ph = 2 * np.pi * np.cumsum(sweep) / sr
            # sin(pi) が浮動小数で負に振れると NaN になるのでクリップする
            env = np.clip(np.sin(np.pi * t / t[-1]), 0.0, None) ** 1.4
            call = (np.sin(ph) * env).astype(np.float32)
            _scatter(out[:, c], call, [rng.integers(0, n)], [rng.uniform(0.02, 0.06)])
    out += wind(n, seed + 11) * 0.25
    return out.astype(np.float32)


# ──────────────────────────────────────────────────────────────
# カフェ / 室内
# ──────────────────────────────────────────────────────────────

def cafe_ambience(n: int, seed: int = 0, sr: int = SR) -> np.ndarray:
    """
    カフェの喧騒。
    人の話し声は「言葉として聞き取れてしまうと集中を邪魔する」ので、
    フォルマント帯域を強調したノイズで“ざわめきの気配”だけを作る。
    """
    rng = np.random.default_rng(seed + 601)
    out = np.zeros((n, 2), dtype=np.float32)

    # ここも 1 枚のタイルを敷くと「同じざわめき」が何百回も繰り返される。
    # 長さの違う複数枚を重ねてループ 1 周ぶん反復しないようにする。
    lens = _tile_set(n, 60.0, count=3, sr=sr)

    def babble_tile(L: int, s: int) -> np.ndarray:
        tile = dsp.looped_noise(L, np.random.default_rng(s), "pink")
        tile = dsp.circular_filter(tile, "bandpass", 260.0, 2600.0, order=2)
        # 声の帯域を持ち上げてざわめきらしくする
        for f, g, q in ((520.0, 4.0, 1.2), (1300.0, 3.0, 1.4)):
            h = dsp.design_fir(
                lambda ff, f=f, g=g, q=q: 1.0 + (dsp.db2lin(g) - 1.0)
                * np.exp(-0.5 * (q * np.log2(np.maximum(ff, 1.0) / f)) ** 2),
                taps=513, sr=sr)
            tile = dsp.fir_circular(tile, h)
        tile = (tile / (np.std(tile) + 1e-9)).astype(np.float32)
        return dsp.tile_to(tile, n)

    for c in range(2):
        babble = babble_tile(lens[0], seed * 23 + c + 1)
        for i, L in enumerate(lens[1:], start=1):
            babble += babble_tile(L, seed * 23 + c + 7919 * i)
        babble = (babble / (np.std(babble) + 1e-9)).astype(np.float32)
        # 会話の波 (盛り上がったり静かになったり)
        env = 0.62 + 0.38 * (dsp.loop_lfo(n, 4 + c, phase=c) * 0.5
                             + dsp.loop_lfo(n, 9, phase=c * 1.7) * 0.3
                             + dsp.loop_lfo(n, 23, phase=c * 0.3) * 0.2)
        out[:, c] = babble * env * 0.5

    # 食器の音 (カップとソーサー)
    for c in range(2):
        Lc = int(0.35 * sr)
        t = np.arange(Lc, dtype=np.float32) / sr
        clink = np.zeros(Lc, dtype=np.float32)
        for r, a, d in [(1.0, 1.0, 0.18), (2.41, 0.6, 0.10), (4.1, 0.35, 0.06)]:
            clink += (a * np.exp(-t / d)
                      * np.sin(2 * np.pi * 2600 * r * t)).astype(np.float32)
        n_cl = int(1.6 * n / sr)
        pos = rng.integers(0, n, n_cl)
        gains = (rng.random(n_cl) ** 2.0).astype(np.float32) * 0.05
        _scatter(out[:, c], clink, pos, gains)

    return _width(out * 0.5, 0.6)


def room_tone(n: int, seed: int = 0, sr: int = SR) -> np.ndarray:
    """
    部屋鳴り。ほぼ聞こえないレベルのノイズ床。
    完全な無音があると「音源が止まった」と誤解されるので必ず薄く敷く。
    """
    out = np.zeros((n, 2), dtype=np.float32)
    for c in range(2):
        out[:, c] = _bed(n, seed * 29 + c + 1, "brown", lp=320.0, tile_sec=45.0) * 0.35
    return _width(out * 0.12, 0.6).astype(np.float32)


def brown_noise_bed(n: int, seed: int = 0, tilt_hz: float = 500.0,
                    sr: int = SR) -> np.ndarray:
    """集中/睡眠用のブラウンノイズ床。単体でも需要が大きい"""
    out = np.zeros((n, 2), dtype=np.float32)
    for c in range(2):
        out[:, c] = _bed(n, seed * 31 + c + 1, "brown", lp=tilt_hz,
                         tile_sec=50.0, order=1.0)
    return _width(out * 0.5, 0.65)


LAYERS = {
    "rain": rain,
    "thunder": thunder,
    "fireplace": fireplace,
    "ocean": ocean,
    "wind": wind,
    "night": night_ambience,
    "birds": forest_birds,
    "cafe": cafe_ambience,
    "room": room_tone,
    "brown": brown_noise_bed,
}
