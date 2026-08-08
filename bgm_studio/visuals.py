"""
映像ループ生成。

方針
----
* 2 時間の映像を素直に描画するのは無駄なので、20 秒の「完全ループ」を作り、
  ffmpeg 側で繰り返す。ファイルサイズもエンコード時間も桁で下がる。
* 完全ループにするため、アニメーションはすべて位相 t01 ∈ [0,1) の
  周期関数で駆動する。状態を持つシミュレーション (炎の物理計算など) は
  ループできないので使わない。
* 低ビットレートでも破綻しないよう、
    - グラデーションは滑らかに
    - 「動かない」微細ノイズを最初から乗せてバンディングを隠す
      (静止ノイズなら I フレームに一度入るだけで、P フレームは太らない)
  という 2 点を守る。
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
FPS = 15
LOOP_SECONDS = 20
TWO_PI = 2.0 * np.pi


# ──────────────────────────────────────────────────────────────
# 描画プリミティブ
# ──────────────────────────────────────────────────────────────

def _yx(h: int = H, w: int = W):
    """正規化座標グリッド (0..1)。y は上が 0"""
    y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
    return y, x


def vgrad(colors, stops=None, h: int = H, w: int = W) -> np.ndarray:
    """縦方向の多段グラデーション。colors は (r,g,b) の列"""
    colors = np.asarray(colors, dtype=np.float32)
    n = len(colors)
    stops = np.linspace(0, 1, n) if stops is None else np.asarray(stops, dtype=np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)
    out = np.empty((h, 3), dtype=np.float32)
    for c in range(3):
        out[:, c] = np.interp(t, stops, colors[:, c])
    return np.repeat(out[:, None, :], w, axis=1)


def radial_glow(cx: float, cy: float, radius: float, color, strength: float = 1.0,
                h: int = H, w: int = W, falloff: float = 2.0,
                res_div: int = 1) -> np.ndarray:
    """
    中心 (cx,cy)、半径 radius (画面幅基準) の柔らかい光。
    毎フレーム呼ぶ場合は res_div=3 にすると軽い (輪郭が無いので劣化しない)。
    """
    hh, ww = max(h // res_div, 8), max(w // res_div, 8)
    y, x = _yx(hh, ww)
    ar = w / h
    d = np.sqrt(((x - cx) * ar) ** 2 + (y - cy) ** 2) / max(radius, 1e-4)
    g = (np.exp(-(d ** falloff)) * strength)[:, :, None] \
        * np.asarray(color, dtype=np.float32)[None, None, :]
    return _upscale(g, h, w) if res_div > 1 else g


def screen(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """スクリーン合成。光を足すときは加算よりこちらのほうが飽和しにくい"""
    return 255.0 - (255.0 - a) * (255.0 - b) / 255.0


def vignette(img: np.ndarray, amount: float = 0.35, h: int = H, w: int = W) -> np.ndarray:
    """周辺減光。これがあるだけで一気に「映像作品」らしくなる"""
    y, x = _yx(h, w)
    ar = w / h
    d = np.sqrt(((x - 0.5) * ar) ** 2 + (y - 0.5) ** 2) / 0.78
    v = 1.0 - amount * np.clip(d, 0, 1.6) ** 2
    return img * v[:, :, None]


def static_grain(h: int = H, w: int = W, amount: float = 3.0,
                 seed: int = 0) -> np.ndarray:
    """
    静止した微細ノイズ。
    毎フレーム変わるノイズはビットレートを食うが、静止していれば
    最初の I フレームに入るだけで済み、バンディングだけ消せる。
    """
    rng = np.random.default_rng(seed)
    return (rng.standard_normal((h, w, 1)) * amount).astype(np.float32)


def _upscale(a: np.ndarray, h: int = H, w: int = W) -> np.ndarray:
    """低解像度で計算した場を元の大きさへ戻す (柔らかい光は劣化しない)"""
    if a.shape[0] == h and a.shape[1] == w:
        return a
    mode = "F" if a.ndim == 2 else "RGB"
    src = a if a.ndim == 2 else np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(src.astype(np.float32) if a.ndim == 2 else src, mode)
    return np.asarray(im.resize((w, h), Image.BILINEAR), dtype=np.float32)


def blur(img: np.ndarray, radius: float, fast: bool = True) -> np.ndarray:
    """
    ガウシアンぼかし。fast=True なら半分の解像度でぼかしてから戻す。
    ぼかした結果は元々ディテールが無いので、見た目は変わらず 4 倍速くなる。
    """
    a = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(a)
    if fast and radius >= 3.0:
        h, w = a.shape[:2]
        im = im.resize((w // 2, h // 2), Image.BILINEAR)
        im = im.filter(ImageFilter.GaussianBlur(radius / 2.0))
        im = im.resize((w, h), Image.BILINEAR)
    else:
        im = im.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(im, dtype=np.float32)


def periodic_noise(t01: float, scale: float = 3.0, cycles: int = 1,
                   seed: int = 0, h: int = H, w: int = W,
                   n_waves: int = 6, res_div: int = 3) -> np.ndarray:
    """
    正弦波の重ね合わせによる周期ノイズ場。
    時間項が t01 の整数倍周期なので、必ずループする。

    低周波の場なので 1/3 解像度で計算して拡大しても差が出ない。
    ここが毎フレームの最大の計算負荷なので効果が大きい。
    """
    hh, ww = max(h // res_div, 8), max(w // res_div, 8)
    rng = np.random.default_rng(seed)
    y, x = _yx(hh, ww)
    acc = np.zeros((hh, ww), dtype=np.float32)
    for _ in range(n_waves):
        fx = rng.uniform(-scale, scale)
        fy = rng.uniform(-scale, scale)
        c = int(rng.integers(1, cycles + 1))
        ph = rng.uniform(0, TWO_PI)
        acc += np.sin(TWO_PI * (fx * x + fy * y + c * t01) + ph)
    return _upscale(acc / n_waves, h, w)


# ── パーティクル (雨・埃・火の粉) ────────────────────────────

def _particle_layer(t01: float, n: int, seed: int, h: int, w: int,
                    length: float, thickness: float, color,
                    speed: float, drift: float, size_var: float = 1.0,
                    glow: bool = False) -> np.ndarray:
    """
    縦に流れる粒子/線を描く。位置は (y0 + speed*t01) % 1 で必ず巡回する。
    PIL の線描画は速いので、粒子数が数百なら十分実用的。
    """
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = rng.random(n)
    y0 = rng.random(n)
    # 速度は「ループ 1 周あたり画面を何回横切るか」の整数にする。
    # 非整数だと t01 が 1 に戻った瞬間に粒子がワープしてしまう。
    sp = np.maximum(np.round(speed * (0.55 + 0.9 * rng.random(n))), 1.0)
    ln = length * (0.5 + size_var * rng.random(n))
    al = (0.35 + 0.65 * rng.random(n))
    # 横移動も整数周回にする (0 なら真っ直ぐ落ちる)
    dxm = np.round(drift * 8.0 * (rng.random(n) - 0.5))
    slant = drift * (rng.random(n) - 0.5)   # 線の傾きは静的な見た目の要素

    yy = (y0 + sp * t01) % 1.0
    xx = (x0 + dxm * t01) % 1.0
    col = np.asarray(color, dtype=np.float32)
    for i in range(n):
        px, py = xx[i] * w, yy[i] * h
        c = tuple(int(v) for v in np.clip(col * al[i], 0, 255))
        if length <= 0.0:
            r = max(thickness * (0.5 + size_var * 0.5), 0.6)
            d.ellipse([px - r, py - r, px + r, py + r], fill=c)
        else:
            d.line([px, py, px + slant[i] * w * 1.6, py + ln[i] * h],
                   fill=c, width=max(int(thickness), 1))
    out = np.asarray(img, dtype=np.float32)
    if glow:
        out = out + blur(out, 6.0) * 0.8
    return out


# ──────────────────────────────────────────────────────────────
# シーン
#   各関数は (t01) -> float32 (H,W,3) を返すクロージャを作る。
#   静的な部分は事前計算しておき、毎フレームの計算量を最小化する。
# ──────────────────────────────────────────────────────────────

def scene_rainy_window(seed: int = 1):
    """雨の窓辺 (lofi の定番)。奥のボケた街灯 + ガラスを流れる雫"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(12, 16, 30), (22, 26, 46), (34, 30, 44), (26, 22, 32)])
    # 街灯のボケ玉
    lights = np.zeros_like(bg)
    for _ in range(26):
        cx, cy = rng.uniform(0.05, 0.95), rng.uniform(0.25, 0.85)
        r = rng.uniform(0.02, 0.075)
        warm = rng.random() < 0.7
        col = ((255, 186, 110) if warm else (140, 190, 255))
        lights += radial_glow(cx, cy, r, col, rng.uniform(0.35, 0.9))
    lights = blur(lights, 26.0)
    base = np.clip(screen(bg, lights), 0, 255)
    base = blur(base, 7.0)                    # ガラス越しのボケ
    base = vignette(base, 0.42) + static_grain(seed=seed)

    def frame(t01):
        img = base.copy()
        # 手前を流れる雨滴
        img = screen(img, _particle_layer(t01, 190, seed + 1, H, W,
                                          length=0.055, thickness=2,
                                          color=(150, 175, 210), speed=3.0,
                                          drift=0.02, glow=True) * 0.55)
        # 細かい霧雨
        img = screen(img, _particle_layer(t01, 260, seed + 2, H, W,
                                          length=0.02, thickness=1,
                                          color=(110, 130, 165), speed=6.0,
                                          drift=0.01) * 0.4)
        return img
    return frame


def scene_starry_night(seed: int = 2):
    """星空。ゆっくり瞬く星 + 淡いオーロラ"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(3, 5, 16), (7, 11, 30), (14, 20, 44), (20, 26, 40)])
    stars = np.zeros((H, W, 3), dtype=np.float32)
    n_star = 700
    sx = rng.integers(0, W, n_star)
    sy = (rng.random(n_star) ** 1.6 * H * 0.92).astype(int)
    sv = rng.uniform(70, 255, n_star).astype(np.float32)
    phase = rng.uniform(0, TWO_PI, n_star)
    cyc = rng.integers(1, 4, n_star)
    tint = rng.random(n_star)
    base = vignette(bg, 0.5) + static_grain(seed=seed, amount=2.0)

    def frame(t01):
        img = base.copy()
        tw = 0.55 + 0.45 * np.sin(TWO_PI * cyc * t01 + phase)
        v = sv * tw
        img[sy, sx, 0] += v * (0.8 + 0.2 * tint)
        img[sy, sx, 1] += v * 0.9
        img[sy, sx, 2] += v
        img = screen(img, blur(np.where(img > 120, img, 0.0), 4.0) * 0.5)
        # オーロラ (緑〜青の帯)
        au = periodic_noise(t01, scale=1.4, cycles=1, seed=seed + 3, n_waves=4)
        y, _ = _yx()
        band = np.exp(-((y - 0.30 - 0.06 * au) / 0.17) ** 2)
        glow = band * (0.5 + 0.5 * au)
        img = screen(img, glow[:, :, None] * np.array([40, 150, 120], dtype=np.float32))
        return img
    return frame


def scene_rain_street(seed: int = 3):
    """夜の雨の街。街灯の光芒と路面の反射"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(8, 10, 20), (16, 20, 36), (24, 24, 38), (12, 12, 20)])
    lamps = np.zeros_like(bg)
    for cx in (0.16, 0.44, 0.72, 0.93):
        lamps += radial_glow(cx, 0.34, 0.10, (255, 178, 96), 0.95)
        lamps += radial_glow(cx, 0.80, 0.16, (200, 130, 70), 0.35, falloff=1.4)
    lamps = blur(lamps, 20.0)
    base = np.clip(screen(bg, lamps), 0, 255)
    # 路面 (下 30%) をやや暗く、反射を長く
    y, _ = _yx()
    ground = np.clip((y - 0.68) / 0.32, 0, 1)
    base = base * (1.0 - 0.35 * ground[:, :, None])
    base = blur(base, 3.0)
    base = vignette(base, 0.45) + static_grain(seed=seed)

    def frame(t01):
        img = base.copy()
        img = screen(img, _particle_layer(t01, 300, seed + 1, H, W,
                                          length=0.085, thickness=2,
                                          color=(160, 180, 215), speed=5.0,
                                          drift=0.05, glow=True) * 0.5)
        # 水たまりの揺らぎ
        rip = periodic_noise(t01, scale=6.0, cycles=2, seed=seed + 2, n_waves=5)
        img += (ground * (0.5 + 0.5 * rip))[:, :, None] * np.array([16, 12, 8],
                                                                   dtype=np.float32)
        return img
    return frame


def scene_coffee_shop(seed: int = 4):
    """カフェの店内。琥珀色のボケ + カップの湯気"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(30, 20, 14), (54, 34, 20), (72, 46, 26), (40, 26, 16)])
    bok = np.zeros_like(bg)
    for _ in range(22):
        bok += radial_glow(rng.uniform(0.02, 0.98), rng.uniform(0.05, 0.7),
                           rng.uniform(0.025, 0.09), (255, 196, 120),
                           rng.uniform(0.3, 0.85))
    bok = blur(bok, 24.0)
    base = np.clip(screen(bg, bok), 0, 255)

    # カップのシルエット
    cup = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(cup)
    cx, cy = int(W * 0.30), int(H * 0.82)
    d.ellipse([cx - 190, cy - 60, cx + 190, cy + 40], fill=(26, 16, 10))
    d.rectangle([cx - 175, cy - 20, cx + 175, cy + 120], fill=(26, 16, 10))
    d.ellipse([cx + 150, cy + 0, cx + 265, cy + 90], outline=(26, 16, 10), width=26)
    d.ellipse([cx - 240, cy + 120, cx + 240, cy + 190], fill=(20, 12, 8))
    cup_a = np.asarray(cup, dtype=np.float32)
    mask = (cup_a.sum(axis=2) > 1)[:, :, None]
    base = np.where(mask, cup_a, base)
    base = vignette(base, 0.5) + static_grain(seed=seed)

    y, x = _yx()
    steam_zone = np.exp(-((x - 0.30) / 0.075) ** 2) * np.clip((0.80 - y) / 0.32, 0, 1) \
        * np.clip((y - 0.44) / 0.12, 0, 1)

    def frame(t01):
        img = base.copy()
        s = periodic_noise(t01, scale=9.0, cycles=1, seed=seed + 5, n_waves=5)
        steam = steam_zone * np.clip(0.45 + 0.55 * s, 0, 1)
        img = screen(img, blur(steam[:, :, None] * np.array([210, 190, 170],
                                                            dtype=np.float32), 9.0) * 0.8)
        return img
    return frame


def scene_seaside_cafe(seed: int = 5):
    """海辺のカフェ。明るいターコイズ + 葉のシルエットが揺れる"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(120, 200, 205), (168, 222, 218), (226, 231, 214), (198, 186, 156)])
    base = np.clip(screen(bg, radial_glow(0.78, 0.20, 0.30, (255, 244, 210), 0.6)), 0, 255)
    base = vignette(base, 0.30) + static_grain(seed=seed, amount=2.0)

    # 葉のシルエットを何枚か用意して揺らす
    leaves = []
    for k in range(3):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        ox = [-120, W // 2, W + 120][k]
        oy = [-60, -160, -40][k]
        for j in range(9):
            ang = -0.5 + j * 0.16 + k * 0.2
            L = 460 + 60 * ((j * 7 + k * 3) % 5)
            ex, ey = ox + L * np.cos(ang), oy + L * np.sin(ang) + 380
            d.line([ox, oy + 300, ex, ey], fill=(24, 52, 40), width=52)
        leaves.append(np.asarray(im, dtype=np.float32))

    def frame(t01):
        img = base.copy()
        for k, lv in enumerate(leaves):
            sh = int(16 * np.sin(TWO_PI * (t01 + k * 0.3)))
            m = np.roll(lv, sh, axis=1)
            img = np.where((m.sum(axis=2) > 1)[:, :, None], m * 0.9, img)
        return img
    return frame


def scene_zen_water(seed: int = 6):
    """禅。暗い水面に広がる同心円の波紋。動きは最小限に"""
    bg = vgrad([(10, 18, 20), (16, 30, 32), (24, 42, 42), (12, 20, 22)])
    base = np.clip(screen(bg, radial_glow(0.5, 0.22, 0.16, (200, 230, 220), 0.45)), 0, 255)
    base = vignette(base, 0.5) + static_grain(seed=seed, amount=2.0)
    y, x = _yx()
    ar = W / H
    centers = [(0.5, 0.62, 0.0), (0.28, 0.78, 0.37), (0.74, 0.72, 0.68)]
    dists = [np.sqrt(((x - cx) * ar) ** 2 + (y - cy) ** 2) for cx, cy, _ in centers]

    def frame(t01):
        img = base.copy()
        for (cx, cy, off), d in zip(centers, dists):
            ph = (t01 + off) % 1.0
            r = ph * 0.85
            ring = np.exp(-((d - r) / 0.022) ** 2) * (1.0 - ph) ** 1.5
            ring += 0.4 * np.exp(-((d - r * 0.55) / 0.03) ** 2) * (1.0 - ph)
            img = screen(img, ring[:, :, None] * np.array([90, 150, 145],
                                                          dtype=np.float32))
        return img
    return frame


def scene_fireplace(seed: int = 7):
    """暖炉。周期ノイズで作る炎 + 舞い上がる火の粉"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(14, 8, 6), (30, 14, 8), (52, 22, 10), (26, 12, 6)])
    hearth = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(hearth)
    d.rectangle([0, int(H * 0.80), W, H], fill=(20, 12, 8))
    for k in range(4):     # 薪
        yy = int(H * 0.80) - 18 * k
        d.polygon([(W * 0.30 + 30 * k, yy), (W * 0.70 - 20 * k, yy - 26),
                   (W * 0.70 - 20 * k, yy + 16), (W * 0.30 + 30 * k, yy + 30)],
                  fill=(44, 26, 14))
    hearth_a = np.asarray(hearth, dtype=np.float32)
    hmask = (hearth_a.sum(axis=2) > 1)[:, :, None]

    y, x = _yx()
    flame_zone = (np.exp(-((x - 0.5) / 0.13) ** 2)
                  * np.clip((0.80 - y) / 0.30, 0, 1) ** 1.4
                  * np.clip((y - 0.44) / 0.10, 0, 1))
    base = vignette(bg, 0.45) + static_grain(seed=seed)

    def frame(t01):
        img = base.copy()
        f = periodic_noise(t01, scale=7.0, cycles=3, seed=seed + 1, n_waves=6)
        f2 = periodic_noise(t01, scale=13.0, cycles=5, seed=seed + 2, n_waves=5)
        flame = np.clip(flame_zone * (0.55 + 0.55 * f + 0.25 * f2), 0, 1.4)
        hot = flame ** 2.2
        fire = (flame[:, :, None] * np.array([255, 96, 18], dtype=np.float32)
                + hot[:, :, None] * np.array([120, 130, 60], dtype=np.float32))
        img = screen(img, blur(fire, 5.0))
        # 部屋全体が炎で明滅する
        pulse = 1.0 + 0.10 * np.sin(TWO_PI * 3 * t01) + 0.05 * np.sin(TWO_PI * 7 * t01)
        img = screen(img, radial_glow(0.5, 0.72, 0.55, (120, 52, 16),
                                      0.55 * pulse, falloff=1.5, res_div=3))
        img = np.where(hmask, hearth_a + img * 0.20, img)
        # 火の粉
        img = screen(img, _particle_layer(1.0 - t01, 90, seed + 3, H, W,
                                          length=0.0, thickness=3,
                                          color=(255, 150, 60), speed=1.2,
                                          drift=0.10, glow=True) * 0.45)
        return img
    return frame


def scene_moonlit_ocean(seed: int = 8):
    """月夜の海。月光の道と、横に広がる波のきらめき"""
    bg = vgrad([(6, 10, 26), (12, 20, 44), (16, 28, 52), (8, 14, 30)])
    base = np.clip(screen(bg, radial_glow(0.5, 0.24, 0.055, (240, 245, 255), 1.0)), 0, 255)
    base = np.clip(screen(base, radial_glow(0.5, 0.24, 0.22, (120, 150, 210), 0.35)), 0, 255)
    rng = np.random.default_rng(seed)
    n_star = 320
    sx = rng.integers(0, W, n_star)
    sy = (rng.random(n_star) ** 2 * H * 0.44).astype(int)
    sv = rng.uniform(60, 200, n_star).astype(np.float32)
    base = vignette(base, 0.5) + static_grain(seed=seed, amount=2.0)

    y, x = _yx()
    sea = np.clip((y - 0.46) / 0.06, 0, 1)
    path = np.exp(-((x - 0.5) / (0.055 + 0.30 * np.clip((y - 0.46) / 0.5, 0, 1))) ** 2)

    def frame(t01):
        img = base.copy()
        img[sy, sx] += sv[:, None]
        w1 = periodic_noise(t01, scale=2.5, cycles=1, seed=seed + 1, n_waves=4)
        w2 = periodic_noise(t01, scale=11.0, cycles=2, seed=seed + 2, n_waves=5)
        shim = sea * (0.35 + 0.65 * np.clip(w1 * 0.6 + w2 * 0.7, -1, 1) ** 2)
        img = screen(img, (shim * path)[:, :, None]
                     * np.array([220, 230, 255], dtype=np.float32))
        img = screen(img, (shim * 0.16)[:, :, None]
                     * np.array([70, 100, 150], dtype=np.float32))
        return img
    return frame


def scene_tavern(seed: int = 9):
    """中世の酒場。暖炉の灯り、木の梁、舞う埃"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(22, 14, 8), (44, 26, 12), (62, 36, 16), (30, 18, 10)])
    base = np.clip(screen(bg, radial_glow(0.30, 0.62, 0.26, (255, 150, 55), 0.85)), 0, 255)
    base = np.clip(screen(base, radial_glow(0.82, 0.30, 0.10, (255, 190, 90), 0.45)), 0, 255)

    beams = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(beams)
    d.rectangle([0, 0, W, int(H * 0.085)], fill=(28, 17, 9))
    for k in range(5):
        bx = int(W * (0.08 + 0.21 * k))
        d.rectangle([bx, 0, bx + 46, int(H * 0.30)], fill=(34, 21, 11))
    d.rectangle([0, int(H * 0.86), W, H], fill=(26, 16, 9))
    beams_a = np.asarray(beams, dtype=np.float32)
    bmask = (beams_a.sum(axis=2) > 1)[:, :, None]
    base = np.where(bmask, beams_a, base)
    base = vignette(base, 0.5) + static_grain(seed=seed)

    def frame(t01):
        img = base.copy()
        pulse = 1.0 + 0.09 * np.sin(TWO_PI * 2 * t01) + 0.05 * np.sin(TWO_PI * 5 * t01)
        img = screen(img, radial_glow(0.30, 0.66, 0.20, (200, 90, 25),
                                      0.5 * pulse, res_div=3))
        # 埃 (ゆっくり漂う)
        img = screen(img, _particle_layer(1.0 - t01, 120, seed + 1, H, W,
                                          length=0.0, thickness=2,
                                          color=(255, 214, 150), speed=0.35,
                                          drift=0.06) * 0.30)
        return img
    return frame


def scene_minimal_gradient(seed: int = 10):
    """集中用の抽象背景。刺激を与えないよう、彩度も動きも最小限にする"""
    base = vgrad([(16, 18, 26), (26, 30, 42), (34, 38, 52), (20, 22, 32)])
    base = vignette(base, 0.4) + static_grain(seed=seed, amount=2.5)
    blobs = [(0.28, 0.35, 0.30, (46, 70, 96), 1), (0.72, 0.62, 0.34, (70, 54, 88), 1),
             (0.50, 0.85, 0.28, (40, 76, 80), 2)]

    def frame(t01):
        img = base.copy()
        for cx, cy, r, col, cyc in blobs:
            ox = 0.035 * np.sin(TWO_PI * cyc * t01)
            oy = 0.025 * np.cos(TWO_PI * cyc * t01)
            img = screen(img, radial_glow(cx + ox, cy + oy, r, col, 0.55,
                                          falloff=1.6, res_div=3))
        return img
    return frame


SCENES = {
    "rainy_window": scene_rainy_window,
    "starry_night": scene_starry_night,
    "rain_street": scene_rain_street,
    "coffee_shop": scene_coffee_shop,
    "seaside_cafe": scene_seaside_cafe,
    "zen_water": scene_zen_water,
    "fireplace": scene_fireplace,
    "moonlit_ocean": scene_moonlit_ocean,
    "tavern": scene_tavern,
    "minimal_gradient": scene_minimal_gradient,
}


def render_frames(scene_name: str, seed: int = 0, seconds: int = LOOP_SECONDS,
                  fps: int = FPS):
    """シーンのフレームを順に yield する (uint8 RGB)"""
    make = SCENES[scene_name]
    frame_fn = make(seed=seed)
    n = int(seconds * fps)
    for i in range(n):
        img = frame_fn(i / n)          # t01 は必ず [0,1) → 完全ループ
        yield np.clip(img, 0, 255).astype(np.uint8)


def thumbnail(scene_name: str, title_lines: list[str], seed: int = 0,
              size=(1280, 720)) -> Image.Image:
    """
    サムネイル。シーンの 1 フレームに大きな文字を載せる。
    BGM のサムネは「一目で用途と雰囲気が分かる」ことが全てなので、
    文字は 3〜4 語まで、フォントは太く大きく。
    """
    make = SCENES[scene_name]
    img = np.clip(make(seed=seed)(0.25), 0, 255).astype(np.uint8)
    im = Image.fromarray(img).resize(size, Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    w, h = size

    # 文字の可読性を上げる暗幕
    d.rectangle([0, int(h * 0.52), w, h], fill=(0, 0, 0, 110))

    from PIL import ImageFont
    y = int(h * 0.58)
    for i, line in enumerate(title_lines):
        try:
            f = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                size=int(h * (0.115 if i == 0 else 0.072)))
        except OSError:
            f = ImageFont.load_default()
        bb = d.textbbox((0, 0), line, font=f)
        tw = bb[2] - bb[0]
        x = (w - tw) // 2
        # 縁取り
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            d.text((x + ox, y + oy), line, font=f, fill=(0, 0, 0, 220))
        d.text((x, y), line, font=f,
               fill=(255, 255, 255, 255) if i == 0 else (255, 226, 170, 245))
        y += int(h * (0.13 if i == 0 else 0.09))
    return im
