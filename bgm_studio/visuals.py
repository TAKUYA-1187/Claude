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
FPS = 24     # 15 だと速い粒子 (雨・雪) が 1 フレームで 20px 以上跳び、カクついて見える
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
    bg = vgrad([(88, 152, 158), (128, 172, 170), (176, 182, 168), (156, 146, 122)])
    base = np.clip(screen(bg, radial_glow(0.78, 0.20, 0.30, (255, 244, 210), 0.35)), 0, 255)
    base = vignette(base, 0.42) + static_grain(seed=seed, amount=2.0)

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


def _city_layers(rng, w, h, horizon, tower_x=0.56):
    """
    夜のビル群と電波塔を描いた RGB 配列を返す。
    写真は著作権上使えないので、矩形と光だけで街を組み立てる。
    """
    city = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(city)

    # 奥から手前へ3層。奥ほど暗く、低く、窓が少ない
    for layer, (dark, hmax, wmin, wmax, dens) in enumerate([
            (0.30, 0.26, 46, 110, 0.16),
            (0.55, 0.34, 70, 150, 0.24),
            (1.00, 0.22, 96, 210, 0.30)]):
        x = -80
        while x < w + 80:
            bw = int(rng.integers(wmin, wmax))
            # 1割ほどは飛び抜けて高いビルにして、平坦なスカイラインを避ける
            tall = rng.random() < 0.10
            bh = int(rng.uniform(0.30, 1.0) * hmax * h * (1.9 if tall else 1.0))
            top = horizon - bh + layer * 22
            col = tuple(int(v * dark) for v in (20, 24, 38))
            d.rectangle([x, top, x + bw, h], fill=col)
            # 屋上の航空障害灯
            if rng.random() < 0.35:
                d.ellipse([x + bw // 2 - 3, top - 3, x + bw // 2 + 3, top + 3],
                          fill=(255, 90, 70))
            # 窓
            step_y, step_x = 20, 16
            for wy in range(top + 10, h, step_y):
                for wx in range(x + 8, x + bw - 7, step_x):
                    if rng.random() < dens:
                        warm = rng.random() < 0.78
                        c = (255, 205, 128) if warm else (168, 205, 255)
                        f = 0.45 + 0.55 * dark
                        d.rectangle([wx, wy, wx + 6, wy + 8],
                                    fill=tuple(int(v * f) for v in c))
            x += bw + int(rng.integers(3, 16))

    # 電波塔
    tx = int(w * tower_x)
    base_y, top_y = horizon + 6, int(h * 0.12)
    seg = 70
    for i in range(seg):
        t0, t1 = i / seg, (i + 1) / seg
        y0 = base_y + (top_y - base_y) * t0
        y1 = base_y + (top_y - base_y) * t1
        half0 = int(104 * (1.0 - t0) ** 1.9) + 4
        half1 = int(104 * (1.0 - t1) ** 1.9) + 4
        # 鉄骨のトラス感を出すため、明暗を交互に
        c = (46, 34, 34) if i % 2 == 0 else (34, 26, 28)
        d.polygon([(tx - half0, y0), (tx + half0, y0),
                   (tx + half1, y1), (tx - half1, y1)], fill=c)
    # 展望台
    for t, hw, hh in ((0.42, 60, 16), (0.74, 34, 11)):
        y = base_y + (top_y - base_y) * t
        d.rectangle([tx - hw, y - hh, tx + hw, y + hh], fill=(58, 40, 36))
    # ライトアップと頂部の灯り
    for t, r, c in ((0.20, 7, (255, 168, 92)), (0.42, 10, (255, 186, 110)),
                    (0.62, 7, (255, 168, 92)), (0.80, 6, (255, 150, 80)),
                    (0.95, 5, (255, 90, 70))):
        y = base_y + (top_y - base_y) * t
        d.ellipse([tx - r, y - r, tx + r, y + r], fill=c)
    d.line([(tx, top_y), (tx, top_y - 78)], fill=(44, 34, 38), width=4)
    return np.asarray(city, dtype=np.float32)


def scene_night_skyline(seed: int = 11):
    """
    夜の街のスカイライン。手前に川、対岸にビル群、中央に電波塔。

    「綺麗な夜景」を成立させているのは主に3つ:
      - 空を単色にせず、地平線近くを街の光で暖色に染める
      - ビルの光を大きくぼかして空へ滲ませる (ブルーム)
      - 水面に街を映し、横方向の波でゆっくり歪ませる
    """
    rng = np.random.default_rng(seed)
    horizon = int(H * 0.62)

    # 空 — 上は藍、地平線近くは街明かりで暖色に
    sky = vgrad([(4, 7, 22), (9, 13, 34), (20, 22, 48),
                 (52, 40, 58), (86, 60, 54)],
                stops=[0.0, 0.28, 0.46, 0.56, 0.62])
    # 星
    n_star = 420
    sx = rng.integers(0, W, n_star)
    sy = (rng.random(n_star) ** 2.0 * horizon * 0.72).astype(int)
    sv = rng.uniform(50, 190, n_star).astype(np.float32)
    sky[sy, sx] += sv[:, None]

    city_a = _city_layers(rng, W, H, horizon)
    mask = (city_a.sum(axis=2) > 1)[:, :, None]
    base = np.where(mask, city_a, sky)

    # 街の光を空へ滲ませる (ブルーム)。
    # 小さな窓を大きくぼかすと値が一気に落ちるので、
    # 半径の違う3段を強めに増幅して重ねる。これが「夜景らしさ」の正体。
    lights = np.where(city_a > 100, city_a, 0.0)
    base = screen(base, np.clip(blur(lights, 60.0) * 4.0, 0, 255) * 0.30)
    base = screen(base, np.clip(blur(lights, 22.0) * 2.6, 0, 255) * 0.30)
    base = screen(base, np.clip(blur(lights, 7.0) * 1.8, 0, 255) * 0.42)
    # 街全体が空を染める光のドーム
    base = screen(base, radial_glow(0.5, 0.63, 0.62, (150, 96, 70), 0.38,
                                    falloff=1.5))
    base = screen(base, radial_glow(0.56, 0.50, 0.26, (170, 110, 78), 0.35,
                                    falloff=1.6))

    # 川 — 街を上下反転して映し、暗く沈める
    water_top = int(H * 0.78)
    refl = base[:water_top][::-1]
    wh = H - water_top
    refl = refl[:wh] if refl.shape[0] >= wh else np.vstack(
        [refl, np.zeros((wh - refl.shape[0], W, 3), np.float32)])
    # 反射は縦に引き伸ばしてから軽くぼかすと、水面に光の筋が伸びる
    refl_img = Image.fromarray(np.clip(refl, 0, 255).astype(np.uint8))
    refl_img = refl_img.resize((W, wh), Image.BILINEAR)
    refl = np.asarray(refl_img, dtype=np.float32)
    streak = np.asarray(
        Image.fromarray(np.clip(refl, 0, 255).astype(np.uint8))
        .filter(ImageFilter.GaussianBlur(2)).resize((W // 6, wh), Image.BILINEAR)
        .resize((W, wh), Image.BILINEAR), dtype=np.float32)
    base[water_top:] = np.clip(blur(refl, 5.0) * 0.55 + streak * 0.35, 0, 255)
    # 岸辺を暗く締める
    base[water_top - 6:water_top + 4] *= 0.30

    base = vignette(base, 0.48) + static_grain(seed=seed, amount=2.0)
    y, x = _yx()
    water_mask = np.clip((y - (water_top / H)) / 0.05, 0, 1)

    def frame(t01):
        img = base.copy()
        # 水面のゆらぎ (縦方向に波打たせて反射を崩す)
        wv = periodic_noise(t01, scale=2.0, cycles=1, seed=seed + 4, n_waves=4)
        img += (water_mask * (0.5 + 0.5 * wv) * 16.0)[:, :, None] \
            * np.array([0.55, 0.65, 1.0], dtype=np.float32)
        # 塔の頂の赤灯が明滅
        pulse = 0.5 + 0.5 * np.sin(TWO_PI * t01)
        img = screen(img, radial_glow(0.56, 0.135, 0.035, (255, 90, 70),
                                      0.30 + 0.40 * pulse, res_div=3))
        img = screen(img, radial_glow(0.56, 0.34, 0.10, (255, 170, 95),
                                      0.10 + 0.06 * pulse, res_div=3))
        # 空の薄雲がゆっくり流れる
        hz = periodic_noise(t01, scale=0.9, cycles=1, seed=seed + 7, n_waves=3)
        haze = np.clip((0.60 - y) / 0.55, 0, 1) * (0.5 + 0.5 * hz) * 0.13
        img = screen(img, haze[:, :, None]
                     * np.array([120, 110, 160], dtype=np.float32))
        return img
    return frame


def scene_rainy_city(seed: int = 23):
    """
    雨の夜の街。スカイラインの上に雨を降らせ、ガラス越しにぼかす。
    lofi の定番構図を、単なるボケ玉ではなく「街」として描く。
    """
    rng = np.random.default_rng(seed)
    horizon = int(H * 0.68)
    sky = vgrad([(6, 8, 20), (12, 14, 32), (26, 24, 44), (64, 46, 52)],
                stops=[0.0, 0.34, 0.54, 0.68])
    city_a = _city_layers(rng, W, H, horizon, tower_x=0.34)
    mask = (city_a.sum(axis=2) > 1)[:, :, None]
    base = np.where(mask, city_a, sky)
    lights = np.where(city_a > 100, city_a, 0.0)
    base = screen(base, blur(lights, 54.0) * 0.85)
    base = blur(base, 9.0)                       # ガラス越し
    base = vignette(base, 0.46) + static_grain(seed=seed)

    def frame(t01):
        img = base.copy()
        img = screen(img, _particle_layer(t01, 200, seed + 1, H, W,
                                          length=0.06, thickness=2,
                                          color=(150, 175, 215), speed=3.0,
                                          drift=0.02, glow=True) * 0.55)
        img = screen(img, _particle_layer(t01, 280, seed + 2, H, W,
                                          length=0.022, thickness=1,
                                          color=(110, 132, 170), speed=6.0,
                                          drift=0.01) * 0.42)
        return img
    return frame


def scene_night_drive(seed: int = 31):
    """
    夜景の中をドライブしている映像。

    「走っている」と感じさせるのは、細かい要素を足すことではなく、
    長時間露光の光跡のように「光が尾を引いて流れる」ことだった。
    最初は雨も街灯も細かく描いたが、引っかき傷のように見えたので削った。

      - 街の光が消失点から外へ、太く柔らかい尾を引いて流れる
      - 濡れた路面が前方の光を縦に反射する
      - 先行車のテールランプが揺れながら遠ざかる
      - 雨は控えめに。多いと視界の邪魔になり、就寝用に使えない

    完全ループにするため、光跡は 1 周でちょうど画面外へ抜ける位相で動かす。
    """
    rng = np.random.default_rng(seed)
    horizon = int(H * 0.50)
    vpx, vpy = int(W * 0.50), horizon

    # 空 — 上は藍、地平線近くは街明かりで暖色に
    sky = vgrad([(4, 6, 18), (9, 12, 30), (24, 24, 46), (78, 52, 52)],
                stops=[0.0, 0.24, 0.42, 0.50])

    # 遠景のビル。主役ではないので暗く、密度も落とす
    far = _city_layers(np.random.default_rng(seed + 1), W, H, horizon,
                       tower_x=0.66)
    mask = (far.sum(axis=2) > 1)[:, :, None]
    base = np.where(mask, far * 0.42, sky)
    lights = np.where(far > 100, far, 0.0)
    base = screen(base, np.clip(blur(lights, 58.0) * 3.0, 0, 255) * 0.36)
    base = screen(base, np.clip(blur(lights, 18.0) * 2.0, 0, 255) * 0.26)

    # 路面
    road = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(road)
    d.polygon([(-int(W * 0.35), H), (int(W * 1.35), H),
               (vpx + 46, vpy), (vpx - 46, vpy)], fill=(22, 20, 26))
    # 車線 (実線2本 + 中央の破線)
    for lx in (-0.34, 0.34):
        d.polygon([(int(W * (0.5 + lx * 2.1)), H),
                   (int(W * (0.5 + lx * 2.1)) + 26, H),
                   (vpx + int(46 * lx * 2), vpy)], fill=(78, 74, 82))
    for k in range(7):
        t0 = (k / 7.0) ** 2.1
        t1 = ((k + 0.45) / 7.0) ** 2.1
        y0, y1 = vpy + (H - vpy) * t0, vpy + (H - vpy) * t1
        w0, w1 = 3 + 26 * t0, 3 + 26 * t1
        d.polygon([(vpx - w0, y0), (vpx + w0, y0),
                   (vpx + w1, y1), (vpx - w1, y1)], fill=(96, 92, 100))
    road_a = np.asarray(road, dtype=np.float32)
    rmask = (road_a.sum(axis=2) > 1)[:, :, None]
    base = np.where(rmask, road_a, base)
    # 地平線の光の帯
    base = screen(base, radial_glow(0.5, horizon / H, 0.55, (150, 96, 74),
                                    0.42, falloff=1.4))

    base = vignette(base, 0.50) + static_grain(seed=seed, amount=2.0)
    y, x = _yx()
    road_zone = np.clip((y - horizon / H) / 0.14, 0, 1)

    # 光跡。少なく、太く、明るく
    n_streak = 16
    ang = rng.uniform(0, TWO_PI, n_streak)
    ph0 = rng.random(n_streak)
    warm = rng.random(n_streak) < 0.70
    size = rng.uniform(0.7, 1.5, n_streak)

    def frame(t01):
        img = base.copy()

        streaks = Image.new("RGB", (W, H), (0, 0, 0))
        sd = ImageDraw.Draw(streaks)
        for i in range(n_streak):
            ph = (ph0[i] + t01) % 1.0
            # 手前ほど加速し、尾も長くなる
            r0 = 0.05 + ph ** 2.3 * 1.25
            r1 = 0.05 + min(ph + 0.10 + 0.16 * ph, 1.25) ** 2.3 * 1.25
            fade = min(ph * 5.0, 1.0) * (1.0 - ph * 0.55)
            c0 = (255, 198, 120) if warm[i] else (146, 194, 255)
            c = tuple(int(v * fade) for v in c0)
            ca, sa_ = np.cos(ang[i]), np.sin(ang[i])
            sd.line([vpx + ca * r0 * W * 0.9, vpy + sa_ * r0 * H * 0.9,
                     vpx + ca * r1 * W * 0.9, vpy + sa_ * r1 * H * 0.9],
                    fill=c, width=max(int(3 + 12 * ph * size[i]), 2))
        sa = np.asarray(streaks, dtype=np.float32)
        img = screen(img, sa * 0.55 + blur(sa, 20.0) * 1.6)

        # 先行車のテールランプ
        ty = horizon / H + 0.115 + 0.030 * np.sin(TWO_PI * t01)
        for dx in (-0.026, 0.026):
            img = screen(img, radial_glow(0.50 + dx, ty, 0.014,
                                          (255, 66, 48), 0.95, res_div=3))
        img = screen(img, radial_glow(0.50, ty, 0.085, (170, 44, 34),
                                      0.26, res_div=3))
        # 濡れた路面に落ちる縦の反射
        img = screen(img, radial_glow(0.50, ty + 0.20, 0.05, (150, 40, 32),
                                      0.20, falloff=1.2, res_div=3))

        # 対向車が左から手前へ抜ける
        hp = (t01 + 0.5) % 1.0
        hx = 0.36 - 0.34 * hp ** 1.9
        hy = horizon / H + 0.05 + 0.34 * hp ** 2.5
        img = screen(img, radial_glow(hx, hy, 0.013 + 0.085 * hp ** 2.1,
                                      (220, 234, 255), 0.22 + 0.80 * hp,
                                      res_div=3))

        # 路面の濡れた光沢
        shine = periodic_noise(t01, scale=2.4, cycles=2, seed=seed + 5, n_waves=4)
        img += (road_zone * (0.5 + 0.5 * shine) * 15.0)[:, :, None] \
            * np.array([1.0, 0.80, 0.60], dtype=np.float32)

        # 雨は控えめに。画面下半分だけ
        rain = _particle_layer(t01, 45, seed + 9, H, W,
                               length=0.030, thickness=2,
                               color=(140, 162, 196), speed=5.0, drift=0.10)
        img = screen(img, rain * np.clip((y - 0.30) / 0.35, 0, 1)[:, :, None] * 0.34)
        return img
    return frame


def _cloud_field(seed: int, kx_max: int = 3, ky_scale: float = 2.2,
                 n_waves: int = 8, h: int = H, w: int = W,
                 res_div: int = 3) -> np.ndarray:
    """
    横方向に厳密に周期的なノイズ場。

    雲は np.roll で横に流すので、場そのものが左右で連続していないと
    継ぎ目が縦の筋になって出る。periodic_noise() は横の周波数に
    非整数を使っているため、これに使うと必ず筋が見える
    (実際にサムネイルで四角い継ぎ目として出た)。
    横の波数を整数に限れば x=0 と x=1 が一致して筋が消える。
    """
    hh, ww = max(h // res_div, 8), max(w // res_div, 8)
    rng = np.random.default_rng(seed)
    y, x = _yx(hh, ww)
    acc = np.zeros((hh, ww), dtype=np.float32)
    for _ in range(n_waves):
        kx = float(rng.integers(1, kx_max + 1))     # 整数 → 横に周期的
        ky = rng.uniform(-ky_scale, ky_scale)
        ph = rng.uniform(0, TWO_PI)
        acc += np.sin(TWO_PI * (kx * x + ky * y) + ph)
    return _upscale(acc / n_waves, h, w)


def scene_anime_dusk(seed: int = 41):
    """
    夕暮れの空。アニメの「あの感じ」を写真を使わず幾何形状だけで作る。

    情感の出どころは空の色そのものなので、そこに手をかける。
    藍→紫→桃→橙→淡黄を縦に重ね、地平線近くに強い光を置いて逆光にする。
    手前を暗いシルエットで抜くと一気に奥行きが出る。

    動きは「雲が流れる・花びらが舞う」だけ。
    雲は静的な場を整数ピクセルずつ横にずらすので完全にループする。
    """
    rng = np.random.default_rng(seed)
    horizon = int(H * 0.70)
    y, x = _yx()

    sky = vgrad([(34, 42, 88), (72, 66, 122), (140, 92, 130),
                 (206, 126, 118), (242, 158, 108), (252, 206, 150)],
                stops=[0.0, 0.20, 0.38, 0.52, 0.63, 0.72])
    base = np.clip(screen(sky, radial_glow(0.50, 0.70, 0.46, (255, 186, 118),
                                           0.85, falloff=1.6)), 0, 255)

    # 雲。低周波の場を薄く伸ばして、空の上側だけに置く
    field = _cloud_field(seed + 1, kx_max=3, ky_scale=2.1, n_waves=7)
    cloud = np.clip(field * 1.7 - 0.10, 0, 1) * np.clip((0.66 - y) / 0.52, 0, 1) ** 1.2
    clouds = blur(cloud[:, :, None] * np.array([255, 200, 176], dtype=np.float32), 9.0)

    # 遠景の丘と、手前の丘。2 枚重ねると空気遠近が出る
    silhouette = Image.new("RGB", (W, H), (0, 0, 0))
    ds = ImageDraw.Draw(silhouette)
    far = [(0, horizon + 40)]
    for i in range(13):
        far.append((int(W * i / 12), horizon + 18 - int(46 * np.sin(i * 0.9 + 1.2))))
    far += [(W, horizon + 40), (W, H), (0, H)]
    ds.polygon(far, fill=(58, 44, 68))
    near = [(0, horizon + 150)]
    for i in range(11):
        near.append((int(W * i / 10), horizon + 130 - int(58 * np.sin(i * 0.7))))
    near += [(W, horizon + 150), (W, H), (0, H)]
    ds.polygon(near, fill=(26, 20, 34))
    # 電柱と電線。アニメの夕景でいちばん効く小道具。
    # 腕木を 2 段にして電線を張る。1 段だと十字架に見えてしまう。
    poles = [int(W * 0.17), int(W * 0.62), int(W * 1.02)]
    tops = []
    for px in poles:
        top = horizon - 250
        ds.rectangle([px - 6, top, px + 6, H], fill=(20, 15, 26))
        for dy, half in ((30, 52), (66, 40)):
            ds.rectangle([px - half, top + dy, px + half, top + dy + 7],
                         fill=(20, 15, 26))
        tops.append((px, top))
    # 電線をたるませて張る (放物線)
    for k, off in enumerate((-44, -30, 32, 46)):
        for (x0, t0), (x1, t1) in zip(tops, tops[1:]):
            sag = 34 + 8 * k
            pts = []
            for i in range(25):
                u = i / 24
                xx = x0 + (x1 - x0) * u
                yy = (t0 + 33) + (t1 - t0) * u + sag * 4 * u * (1 - u)
                pts.append((xx, yy + off * 0.35))
            ds.line(pts, fill=(24, 18, 30), width=3)
    sil = np.asarray(silhouette, dtype=np.float32)
    smask = (sil.sum(axis=2) > 1)[:, :, None]

    base = vignette(base, 0.34) + static_grain(seed=seed, amount=2.0)

    def frame(t01):
        img = base.copy()
        # 雲は整数ピクセルで巡回させる
        img = screen(img, np.roll(clouds, int(round(t01 * W)), axis=1) * 0.55)
        img = np.where(smask, sil, img)
        # 舞う花びらと逆光の玉ボケ。
        # 数を入れすぎると雪に見えて、情感ではなく賑やかさになる。
        # 「言われないと気付かないが、無いと寂しい」量に留める。
        img = screen(img, _particle_layer(
            t01, 26, seed + 2, H, W, length=0.0, thickness=4.0,
            color=(236, 176, 190), speed=1.0, drift=0.5, size_var=1.3) * 0.55)
        img = screen(img, _particle_layer(
            t01, 11, seed + 3, H, W, length=0.0, thickness=10.0,
            color=(255, 222, 168), speed=1.0, drift=0.3, size_var=1.6,
            glow=True) * 0.30)
        return img
    return frame


def scene_morning_meadow(seed: int = 42):
    """
    朝の草原。爽やか系はとにかく「軽さ」が命なので、
    色を濁らせないことと、動きを増やしすぎないことだけを守る。
    """
    rng = np.random.default_rng(seed)
    hz = 0.60                       # 地平線 (0..1)
    y, x = _yx()

    # 空。地平線に近づくほど白く霞ませると奥行きが出る
    sky = vgrad([(52, 112, 170), (94, 152, 196), (146, 186, 210),
                 (196, 212, 206)],
                stops=[0.0, 0.28, 0.48, hz])
    base = np.clip(screen(sky, radial_glow(0.24, 0.17, 0.36, (255, 248, 214),
                                           0.50, falloff=1.8)), 0, 255)

    # 雲。朝なので白く、控えめに
    field = _cloud_field(seed + 1, kx_max=4, ky_scale=2.6, n_waves=8)
    cloud = (np.clip(field * 1.9 - 0.32, 0, 1)
             * np.clip((hz - 0.05 - y) / 0.44, 0, 1) ** 1.1)
    clouds = blur(cloud[:, :, None] * np.array([255, 255, 252], dtype=np.float32), 12.0)

    # 草原。べた塗りにすると人工芝に見えるので、縦グラデーションで
    # 「奥は霞んで明るく、手前は濃い」を作る
    # 階調は地面の範囲 [hz, 1] の中に置く。全画面基準で作ると
    # 地面には暗い側しか出てこず、結局べた塗りに見えてしまう。
    ground = vgrad([(190, 206, 166), (150, 178, 112), (112, 148, 76),
                    (80, 118, 54), (56, 92, 40)],
                   stops=[hz, hz + 0.03, hz + 0.12, hz + 0.26, 1.0])
    gmask = np.clip((y - hz) / 0.010, 0, 1)[:, :, None]

    # 地平線の木立。小さく散らすだけで一気に「広さ」が出る
    # 白黒で描いてから alpha として使う。ぼかした画像をそのまま
    # 閾値で切り抜くと、半端に暗い縁が黒い輪郭になって漫画みたいになる。
    tree_a = Image.new("L", (W, H), 0)
    dt = ImageDraw.Draw(tree_a)
    for _ in range(30):
        tx = rng.random() * W
        th = rng.uniform(20, 52)
        tw = th * rng.uniform(0.55, 0.95)
        ty = hz * H + rng.uniform(-3, 6)
        for j in range(int(rng.integers(1, 4))):     # 少し塊にする
            ox = (j - 0.5) * tw * 0.8
            hh = th * rng.uniform(0.7, 1.0)
            dt.ellipse([tx + ox - tw * 0.7, ty - hh,
                        tx + ox + tw * 0.7, ty + hh * 0.2], fill=255)
    ta = (np.asarray(blur(np.asarray(tree_a, dtype=np.float32)[:, :, None]
                          .repeat(3, axis=2), 2.5), dtype=np.float32)[:, :, :1] / 255.0)
    # 遠くのものほど空の色に寄せる (空気遠近)。手前の草と同じ緑だと距離が出ない。
    tree_col = np.array([124, 152, 128], dtype=np.float32)

    # 手前の草。細く多く、画面下だけ。3 層に分けて視差で揺らす
    blades = []
    for k in range(3):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        shade = (44 + 14 * k, 74 + 16 * k, 36 + 12 * k)
        for _ in range(260):
            bx = rng.random() * W
            bh = rng.uniform(46, 128) * (0.7 + 0.45 * k)
            by = H + rng.uniform(-26, 10)
            d.line([bx, by, bx + rng.uniform(-16, 16), by - bh],
                   fill=shade, width=int(rng.uniform(2, 4)))
        blades.append(np.asarray(im, dtype=np.float32))

    base = vignette(base, 0.28) + static_grain(seed=seed, amount=2.0)

    def frame(t01):
        img = base.copy()
        img = screen(img, np.roll(clouds, int(round(t01 * W * 0.5)), axis=1) * 0.7)
        img = img * (1.0 - gmask) + ground * gmask
        img = img * (1.0 - ta) + tree_col * ta
        # 風で草が揺れる。sin なので必ずループする
        for k, bl in enumerate(blades):
            sh = int((5 + 4 * k) * np.sin(TWO_PI * (t01 + k * 0.3)))
            m = np.roll(bl, sh, axis=1)
            img = np.where((m.sum(axis=2) > 1)[:, :, None], m, img)
        # 陽の当たる側にだけ、control された光の粒
        img = screen(img, _particle_layer(
            t01, 20, seed + 4, H, W, length=0.0, thickness=7.0,
            color=(255, 250, 206), speed=1.0, drift=0.5, size_var=1.4,
            glow=True) * 0.38)
        return img
    return frame


def scene_lantern_street(seed: int = 51):
    """
    提灯の並ぶ夜の路地。和風ローファイ用。
    構図は night_drive と同じ「奥へ引き込む一点透視」だが、
    光源を提灯の暖色に置き換えるだけで日本の路地になる。
    """
    rng = np.random.default_rng(seed)
    horizon = int(H * 0.52)
    vpx = int(W * 0.5)

    sky = vgrad([(10, 10, 24), (18, 16, 36), (30, 22, 44), (16, 14, 30)],
                stops=[0.0, 0.35, 0.52, 1.0])
    base = np.clip(screen(sky, radial_glow(0.5, 0.50, 0.5, (60, 36, 40),
                                           0.5, falloff=1.6)), 0, 255)

    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    # 路面 (石畳風の台形)
    d.polygon([(int(W * 0.30), horizon), (int(W * 0.70), horizon),
               (W + 200, H), (-200, H)], fill=(26, 22, 26))
    # 両側の建物シルエット
    for side in (-1, 1):
        for k in range(6):
            u = k / 6.0
            x0 = vpx + side * int((60 + 900 * u))
            wdt = int(30 + 200 * u)
            hgt = int(60 + 460 * u)
            xa, xb = sorted((x0, x0 + side * wdt))
            d.rectangle([xa, horizon - hgt, xb, horizon + int(180 * u) + 40],
                        fill=(14, 12, 20))
    stat = np.asarray(im, dtype=np.float32)
    smask = (stat.sum(axis=2) > 1)[:, :, None]

    # 提灯の位置 (両側に奥へ並べる)
    lanterns = []
    for side in (-1, 1):
        for k in range(7):
            u = (k + 0.5) / 7.0
            lx = (vpx + side * (46 + 780 * u ** 1.25)) / W
            ly = (horizon - 40 - 240 * u * 0.35 + 90 * u) / H
            lanterns.append((lx, ly, 0.010 + 0.030 * u, k * 1.7 + (side + 1)))
    base = vignette(base, 0.42) + static_grain(seed=seed, amount=2.2)

    def frame(t01):
        img = base.copy()
        img = np.where(smask, stat, img)
        for lx, ly, r, ph in lanterns:
            # 提灯の揺れ (ごくわずかに左右へ)
            sway = 0.004 * np.sin(TWO_PI * (t01 + ph * 0.13))
            flicker = 0.82 + 0.18 * np.sin(TWO_PI * (2 * t01 + ph))
            img = screen(img, radial_glow(lx + sway, ly, r * 3.2,
                                          (255, 120, 40), 0.55 * flicker,
                                          falloff=1.7, res_div=3))
            img = screen(img, radial_glow(lx + sway, ly, r,
                                          (255, 190, 110), 0.95 * flicker,
                                          falloff=1.2, res_div=3))
        # 蛍のような微光の粒
        img = screen(img, _particle_layer(
            t01, 14, seed + 2, H, W, length=0.0, thickness=5.0,
            color=(180, 150, 80), speed=1.0, drift=0.6, size_var=1.3,
            glow=True) * 0.35)
        return img
    return frame


def scene_storm_window(seed: int = 52):
    """
    雷雨の夜の窓。rainy_window の強雨版 + 稲光。

    稲光はループを壊しやすい要素なので、光る時刻を t01 上に
    固定で埋め込む (乱数はシードで固定)。フレーム関数は t01 だけの
    純関数のままなので、末尾→先頭は必ず連続する。
    """
    rng = np.random.default_rng(seed)
    bg = vgrad([(7, 8, 17), (12, 14, 26), (18, 19, 33), (9, 10, 18)])
    # 遠くの街灯のボケ玉 (嵐の夜なので数を減らし、寒色寄りに)
    lights = np.zeros_like(bg)
    for _ in range(16):
        cx, cy = rng.uniform(0.05, 0.95), rng.uniform(0.35, 0.85)
        r = rng.uniform(0.018, 0.06)
        warm = rng.random() < 0.45
        col = ((255, 180, 105) if warm else (120, 165, 235))
        lights += radial_glow(cx, cy, r, col, rng.uniform(0.25, 0.7))
    base = np.clip(screen(bg, blur(lights, 28.0)), 0, 255)
    base = blur(base, 8.0)                    # ガラス越しのボケ
    base = vignette(base, 0.5) + static_grain(seed=seed, amount=2.4)

    # 窓枠
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for x in (int(W * 0.055), int(W * 0.492), int(W * 0.93)):
        d.rectangle([x, 0, x + int(W * 0.014), H], fill=(15, 12, 11))
    d.rectangle([0, int(H * 0.475), W, int(H * 0.507)], fill=(15, 12, 11))
    frame_a = np.asarray(im, dtype=np.float32)
    fmask = (frame_a.sum(axis=2) > 1)[:, :, None]

    # 稲光のスケジュール: (発生時刻 t01, 強さ, 画面上の横位置)。
    # 時刻を固定で埋め込むので、ループしても稲光の位置関係は保たれる
    flashes = [(float(rng.uniform(0, 1)), float(rng.uniform(0.5, 1.0)),
                float(rng.uniform(0.2, 0.8))) for _ in range(5)]

    def frame(t01):
        img = base.copy()
        # 稲光: 一瞬立ち上がって数百 ms で減衰。空全体をわずかに明るくし、
        # 発生位置の周りを強く光らせる
        for ft, fs, fx in flashes:
            dt = (t01 - ft) % 1.0
            k = np.exp(-dt * 90.0) * fs
            if k > 0.01:
                img = img * (1.0 + 0.5 * k)
                img = screen(img, radial_glow(fx, 0.15, 0.7,
                                              (175, 185, 235), 1.2 * k,
                                              falloff=1.5, res_div=3))
        # ガラスを流れる雨。ほぼ垂直 (drift を大きくすると引っかき傷になる)
        img = screen(img, _particle_layer(
            t01, 230, seed + 1, H, W, length=0.06, thickness=2.0,
            color=(140, 160, 200), speed=4.0, drift=0.02, glow=True) * 0.6)
        img = screen(img, _particle_layer(
            t01, 300, seed + 2, H, W, length=0.025, thickness=1.0,
            color=(105, 125, 160), speed=7.0, drift=0.01) * 0.45)
        img = np.where(fmask, frame_a, img)
        return np.clip(img, 0, 255)
    return frame


def scene_autumn_leaves(seed: int = 53):
    """
    秋。夕方の琥珀色の光と、舞い落ちる葉。
    """
    rng = np.random.default_rng(seed)
    y, x = _yx()
    sky = vgrad([(96, 60, 40), (152, 92, 52), (198, 130, 66),
                 (170, 104, 56), (92, 56, 36)],
                stops=[0.0, 0.30, 0.55, 0.72, 1.0])
    base = np.clip(screen(sky, radial_glow(0.32, 0.38, 0.40, (255, 200, 120),
                                           0.65, falloff=1.7)), 0, 255)

    # 紅葉の茂み (画面の上両隅から覆いかぶさる)。
    # 枝を線で描くと棒にしか見えないので、葉の塊を楕円の集まりで作り、
    # ぼかした白黒を alpha として使う (morning_meadow と同じ手法)
    # 樹冠は「隅からの距離場 + ノイズで揺らした縁」で作る。
    # 楕円をばら撒く方式は、密度が足りないと泥はねに見えてしまう
    ar = W / H
    edge = _cloud_field(seed + 7, kx_max=5, ky_scale=3.0, n_waves=8)
    fa = np.zeros((H, W), dtype=np.float32)
    for cx, cy, r0 in ((-0.10, -0.35, 0.72), (1.10, -0.30, 0.66)):
        dd = np.sqrt(((x - cx) * ar) ** 2 + (y - cy) ** 2)
        fa = np.maximum(fa, np.clip((r0 + 0.09 * edge - dd) / 0.05, 0, 1))
    fa = fa[:, :, None]
    # 逆光の紅葉なので暗い赤茶
    fol_col = np.array([70, 34, 20], dtype=np.float32)

    # 地面に積もった葉
    ground = vgrad([(120, 70, 34), (86, 48, 26), (56, 32, 20)],
                   stops=[0.80, 0.90, 1.0])
    gmask = np.clip((y - 0.80) / 0.012, 0, 1)[:, :, None]
    base = vignette(base, 0.36) + static_grain(seed=seed, amount=2.2)

    def frame(t01):
        img = base.copy()
        img = img * (1.0 - gmask) + ground * gmask
        img = img * (1.0 - fa) + fol_col * fa
        # 舞い落ちる葉 (2 層: 大きくゆっくり / 小さく速く)。
        # 短い斜めの線にすると「葉がひらひら落ちる」感じに寄る
        img = screen(img, _particle_layer(
            t01, 34, seed + 3, H, W, length=0.006, thickness=8.0,
            color=(225, 118, 36), speed=1.0, drift=0.05, size_var=1.5) * 0.9)
        img = screen(img, _particle_layer(
            t01, 24, seed + 4, H, W, length=0.005, thickness=5.5,
            color=(185, 84, 28), speed=2.0, drift=0.04, size_var=1.2) * 0.65)
        return img
    return frame


def scene_christmas_window(seed: int = 54):
    """
    クリスマスの夜の窓辺。雪、ツリーの灯り、暖色の部屋。
    """
    rng = np.random.default_rng(seed)
    # 夜の屋外 (窓の外) — 深い青
    bg = vgrad([(10, 14, 34), (16, 22, 46), (24, 32, 60), (14, 18, 40)])
    base = np.clip(screen(bg, radial_glow(0.30, 0.30, 0.34, (120, 140, 190),
                                          0.4, falloff=1.9)), 0, 255)

    # ツリーのシルエット (右手前) と灯り
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = int(W * 0.78), int(H * 0.92)
    for k in range(4):
        wdt = 420 - 90 * k
        top = cy - 240 - 150 * k
        d.polygon([(cx - wdt // 2, top + 210), (cx + wdt // 2, top + 210),
                   (cx, top)], fill=(10, 26, 16))
    tree = np.asarray(im, dtype=np.float32)
    tmask = (tree.sum(axis=2) > 1)[:, :, None]

    # ツリーの電飾 (シルエット内にランダムに配置)
    lights = []
    for _ in range(46):
        u = rng.random()
        lvl = int(u * 3.999)
        wdt = (420 - 90 * lvl) * 0.42
        ly = cy - 130 - 150 * lvl - rng.random() * 130
        lx = cx + (rng.random() * 2 - 1) * wdt * (1.0 - 0.3 * rng.random())
        col = [(255, 90, 60), (255, 200, 90), (120, 200 , 255), (180, 255, 140)][
            int(rng.integers(0, 4))]
        lights.append((lx / W, ly / H, col, float(rng.uniform(0, 6.28))))

    base = vignette(base, 0.42) + static_grain(seed=seed, amount=2.2)

    def frame(t01):
        img = base.copy()
        img = np.where(tmask, tree, img)
        # 電飾: それぞれ位相の違う 2 周期のまたたき
        for lx, ly, col, ph in lights:
            tw = 0.55 + 0.45 * np.sin(TWO_PI * (2 * t01) + ph)
            img = screen(img, radial_glow(lx, ly, 0.012, col, 0.9 * tw,
                                          falloff=1.2, res_div=3))
        # 部屋の暖色の光が左から差す
        img = screen(img, radial_glow(0.06, 0.72, 0.5, (200, 120, 50),
                                      0.5, falloff=1.8, res_div=3))
        # 雪 (2 層)
        img = screen(img, _particle_layer(
            t01, 90, seed + 2, H, W, length=0.0, thickness=4.4,
            color=(235, 240, 250), speed=1.0, drift=0.7, size_var=1.3) * 0.8)
        img = screen(img, _particle_layer(
            t01, 50, seed + 3, H, W, length=0.0, thickness=7.0,
            color=(255, 255, 255), speed=2.0, drift=0.5, size_var=1.5) * 0.55)
        return img
    return frame


def scene_spaceship_window(seed: int = 61):
    """宇宙船の窓。流れる星 + 船体のフレーム + 計器の淡い光"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(2, 3, 8), (4, 6, 14), (8, 10, 20), (3, 4, 10)])
    base = np.clip(screen(bg, radial_glow(0.5, 0.5, 0.55, (30, 40, 70),
                                          0.5, falloff=2.0)), 0, 255)
    # 船体フレーム (窓の縁)
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, int(H * 0.09)], fill=(12, 13, 16))
    d.rectangle([0, int(H * 0.91), W, H], fill=(12, 13, 16))
    d.rectangle([0, 0, int(W * 0.05), H], fill=(10, 11, 14))
    d.rectangle([int(W * 0.95), 0, W, H], fill=(10, 11, 14))
    # 計器のランプ
    for k in range(7):
        x0 = int(W * (0.12 + 0.11 * k))
        col = [(60, 180, 120), (200, 150, 60), (80, 130, 200)][k % 3]
        d.rectangle([x0, int(H * 0.945), x0 + 26, int(H * 0.955)], fill=col)
    hull = np.asarray(im, dtype=np.float32)
    hmask = (hull.sum(axis=2) > 1)[:, :, None]

    # 星: 3 層の視差。横に整数回流れる
    star_layers = []
    for k, (n_s, sp, size) in enumerate(((90, 1, 1.4), (50, 2, 2.0), (22, 3, 2.8))):
        xs, ys = rng.random(n_s), rng.random(n_s) * 0.8 + 0.1
        br = 0.4 + 0.6 * rng.random(n_s)
        star_layers.append((xs, ys, br, sp, size))

    base = vignette(base, 0.4) + static_grain(seed=seed, amount=1.8)

    def frame(t01):
        img = base.copy()
        im2 = Image.new("RGB", (W, H), (0, 0, 0))
        d2 = ImageDraw.Draw(im2)
        for xs, ys, br, sp, size in star_layers:
            xx = (xs - sp * t01) % 1.0
            for i in range(len(xs)):
                c = int(140 + 100 * br[i])
                d2.ellipse([xx[i] * W - size, ys[i] * H - size,
                            xx[i] * W + size, ys[i] * H + size],
                           fill=(c, c, min(255, c + 20)))
        img = screen(img, np.asarray(im2, dtype=np.float32))
        img = np.where(hmask, hull, img)
        return img
    return frame


def scene_golden_light(seed: int = 62):
    """528Hz 用。呼吸する金色の光。動きは呼吸のリズム (約6秒周期) だけ"""
    bg = vgrad([(20, 12, 6), (36, 22, 10), (54, 34, 14), (26, 16, 8)])
    base = vignette(bg, 0.4) + static_grain(seed=seed, amount=2.0)
    breaths = 3   # 20秒の映像ループ中に 3 回 → 1 周期 6.7 秒

    def frame(t01):
        img = base.copy()
        b = 0.5 + 0.5 * np.sin(TWO_PI * breaths * t01 - np.pi / 2)
        s = 0.55 + 0.30 * b
        img = screen(img, radial_glow(0.5, 0.52, 0.30 + 0.05 * b,
                                      (255, 190, 90), s, falloff=1.6, res_div=3))
        img = screen(img, radial_glow(0.5, 0.52, 0.62,
                                      (200, 130, 50), 0.35 * s, falloff=1.9, res_div=3))
        img = screen(img, _particle_layer(
            t01, 24, seed + 1, H, W, length=0.0, thickness=5.0,
            color=(255, 214, 130), speed=1.0, drift=0.4, size_var=1.4,
            glow=True) * 0.4)
        return img
    return frame


def scene_focus_depths(seed: int = 63):
    """40Hz 集中用。深い青の空間をごく遅い光の帯が漂う"""
    bg = vgrad([(6, 10, 22), (10, 18, 34), (14, 26, 44), (8, 12, 26)])
    base = np.clip(screen(bg, radial_glow(0.5, 0.42, 0.5, (40, 80, 130),
                                          0.5, falloff=1.9)), 0, 255)
    base = vignette(base, 0.42) + static_grain(seed=seed, amount=2.0)

    def frame(t01):
        img = base.copy()
        f1 = periodic_noise(t01, scale=1.6, cycles=1, seed=seed + 1, n_waves=5)
        band = np.clip(f1 * 1.3, 0, 1)[:, :, None] * np.array(
            [30, 70, 110], dtype=np.float32)
        img = screen(img, band * 0.7)
        img = screen(img, _particle_layer(
            t01, 30, seed + 2, H, W, length=0.0, thickness=4.0,
            color=(120, 190, 235), speed=1.0, drift=0.3, size_var=1.3,
            glow=True) * 0.35)
        return img
    return frame


def scene_halloween_manor(seed: int = 64):
    """ハロウィン。丘の上の館 + 雲間の月 + カボチャ提灯"""
    rng = np.random.default_rng(seed)
    y, x = _yx()
    bg = vgrad([(14, 10, 26), (26, 18, 42), (44, 30, 56), (20, 14, 30)],
               stops=[0.0, 0.35, 0.62, 1.0])
    base = np.clip(screen(bg, radial_glow(0.72, 0.20, 0.10,
                                          (230, 226, 200), 1.0, falloff=1.2)), 0, 255)
    base = np.clip(screen(base, radial_glow(0.72, 0.20, 0.30,
                                            (140, 130, 110), 0.4, falloff=1.8)), 0, 255)
    # 丘と館のシルエット
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    hill = [(0, int(H * 0.78))]
    for i in range(13):
        hill.append((int(W * i / 12),
                     int(H * 0.74 + 40 * np.sin(i * 0.8 + 2.0))))
    hill += [(W, int(H * 0.80)), (W, H), (0, H)]
    d.polygon(hill, fill=(10, 7, 16))
    mx, mh = int(W * 0.30), int(H * 0.72)
    d.rectangle([mx - 130, mh - 180, mx + 130, mh + 60], fill=(8, 6, 13))
    d.polygon([(mx - 150, mh - 180), (mx + 150, mh - 180), (mx, mh - 260)],
              fill=(8, 6, 13))
    for tx in (mx - 100, mx + 100):
        d.rectangle([tx - 26, mh - 240, tx + 26, mh - 60], fill=(8, 6, 13))
        d.polygon([(tx - 34, mh - 240), (tx + 34, mh - 240), (tx, mh - 300)],
                  fill=(8, 6, 13))
    manor = np.asarray(im, dtype=np.float32)
    mmask = (manor.sum(axis=2) > 1)[:, :, None]
    # 窓の灯り (2つだけ。多いと怖さが消える)
    wins = [(mx - 40, mh - 120), (mx + 55, mh - 90)]
    # カボチャ (手前の丘に 3 つ)
    pumps = [(0.62, 0.84, 0.020), (0.70, 0.88, 0.026), (0.55, 0.90, 0.016)]

    base = vignette(base, 0.46) + static_grain(seed=seed, amount=2.4)

    def frame(t01):
        img = base.copy()
        # 月の前を雲が流れる
        cf = _cloud_field(seed + 3, kx_max=2, ky_scale=1.4, n_waves=6)
        cl = np.clip(np.roll(cf, int(round(t01 * W)), axis=1) * 1.6 - 0.2, 0, 1)
        cl *= np.clip((0.45 - y) / 0.40, 0, 1)
        img = img * (1.0 - 0.55 * cl[:, :, None])
        img = np.where(mmask, manor, img)
        for wx, wy in wins:
            flick = 0.7 + 0.3 * np.sin(TWO_PI * (3 * t01 + wx * 0.01))
            img = screen(img, radial_glow(wx / W, wy / H, 0.014,
                                          (255, 170, 60), 0.9 * flick,
                                          falloff=1.2, res_div=3))
        for px, py, pr in pumps:
            flick = 0.75 + 0.25 * np.sin(TWO_PI * (5 * t01 + px * 40))
            img = screen(img, radial_glow(px, py, pr * 2.6, (255, 110, 20),
                                          0.6 * flick, falloff=1.6, res_div=3))
            img = screen(img, radial_glow(px, py, pr, (255, 190, 80),
                                          1.0 * flick, falloff=1.1, res_div=3))
        # 舞う落ち葉
        img = screen(img, _particle_layer(
            t01, 26, seed + 4, H, W, length=0.008, thickness=4.0,
            color=(150, 80, 30), speed=2.0, drift=0.06, size_var=1.3) * 0.6)
        return img
    return frame


def scene_snow_cabin(seed: int = 65):
    """吹雪の窓。storm_window の雪版 + 部屋の暖色"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(10, 12, 22), (16, 20, 32), (24, 28, 40), (12, 14, 24)])
    lights = np.zeros_like(bg)
    for _ in range(8):
        cx, cy = rng.uniform(0.1, 0.9), rng.uniform(0.4, 0.8)
        lights += radial_glow(cx, cy, rng.uniform(0.02, 0.05),
                              (255, 190, 120), rng.uniform(0.2, 0.5))
    base = np.clip(screen(bg, blur(lights, 30.0)), 0, 255)
    base = blur(base, 9.0)
    base = np.clip(screen(base, radial_glow(0.08, 0.75, 0.45, (210, 130, 60),
                                            0.55, falloff=1.9)), 0, 255)
    base = vignette(base, 0.48) + static_grain(seed=seed, amount=2.4)

    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for xx in (int(W * 0.055), int(W * 0.492), int(W * 0.93)):
        d.rectangle([xx, 0, xx + int(W * 0.014), H], fill=(26, 18, 13))
    d.rectangle([0, int(H * 0.475), W, int(H * 0.507)], fill=(26, 18, 13))
    fr = np.asarray(im, dtype=np.float32)
    fmask = (fr.sum(axis=2) > 1)[:, :, None]

    def frame(t01):
        img = base.copy()
        # 吹雪: 斜めに流れる雪 3 層 (速いほど斜めに)
        img = screen(img, _particle_layer(
            t01, 160, seed + 1, H, W, length=0.015, thickness=2.6,
            color=(220, 228, 240), speed=3.0, drift=0.05, size_var=1.2) * 0.75)
        img = screen(img, _particle_layer(
            t01, 90, seed + 2, H, W, length=0.008, thickness=4.0,
            color=(240, 245, 252), speed=2.0, drift=0.07, size_var=1.5) * 0.8)
        img = screen(img, _particle_layer(
            t01, 40, seed + 3, H, W, length=0.0, thickness=6.0,
            color=(255, 255, 255), speed=1.0, drift=0.09, size_var=1.6) * 0.6)
        img = np.where(fmask, fr, img)
        return img
    return frame


def scene_forest_camp(seed: int = 66):
    """夜の森の焚き火。木々のシルエット + 火の明滅 + 蛍"""
    rng = np.random.default_rng(seed)
    y, x = _yx()
    bg = vgrad([(6, 10, 18), (10, 16, 26), (16, 24, 30), (8, 12, 16)])
    base = np.clip(screen(bg, radial_glow(0.60, 0.16, 0.12, (200, 210, 230),
                                          0.55, falloff=1.4)), 0, 255)
    # 木々 (両側から)
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for tx in [0.06, 0.16, 0.86, 0.94, 0.26, 0.76]:
        tw = rng.uniform(26, 50)
        d.rectangle([int(tx * W - tw / 2), 0, int(tx * W + tw / 2), H],
                    fill=(4, 6, 8))
        for k in range(5):
            by = int(H * (0.1 + 0.15 * k))
            bl = rng.uniform(60, 130)
            sgn = -1 if tx > 0.5 else 1
            d.line([int(tx * W), by, int(tx * W + sgn * bl), by + 40],
                   fill=(4, 6, 8), width=14)
    trees = np.asarray(im, dtype=np.float32)
    tmask = (trees.sum(axis=2) > 1)[:, :, None]
    # 地面
    gmask = np.clip((y - 0.82) / 0.01, 0, 1)[:, :, None]
    ground = np.array([8, 10, 9], dtype=np.float32)

    base = vignette(base, 0.5) + static_grain(seed=seed, amount=2.2)

    def frame(t01):
        img = base.copy()
        img = img * (1.0 - gmask) + ground * gmask
        img = np.where(tmask, trees, img)
        # 焚き火の明滅 (画面下中央)
        f = periodic_noise(t01, scale=6.0, cycles=4, seed=seed + 1, n_waves=5)
        pul = 0.75 + 0.25 * float(f[f.shape[0] // 2, f.shape[1] // 2] * 0.5 + 0.5)
        img = screen(img, radial_glow(0.46, 0.93, 0.30, (255, 120, 30),
                                      0.85 * pul, falloff=1.7, res_div=3))
        img = screen(img, radial_glow(0.46, 0.96, 0.10, (255, 200, 90),
                                      1.1 * pul, falloff=1.2, res_div=3))
        # 火の粉
        img = screen(img, _particle_layer(
            t01, 22, seed + 2, H, W, length=0.006, thickness=2.6,
            color=(255, 150, 50), speed=2.0, drift=0.10, size_var=1.2) * 0.5)
        # 蛍
        img = screen(img, _particle_layer(
            t01, 12, seed + 3, H, W, length=0.0, thickness=4.0,
            color=(160, 220, 90), speed=1.0, drift=0.7, size_var=1.3,
            glow=True) * 0.4)
        return img
    return frame


def scene_nebula(seed: int = 67):
    """星雲。色の違う雲を 2 層重ね、ゆっくり流す"""
    rng = np.random.default_rng(seed)
    bg = vgrad([(4, 3, 10), (8, 6, 18), (12, 8, 24), (5, 4, 12)])
    # 星 (静止)
    stars = Image.new("RGB", (W, H), (0, 0, 0))
    ds = ImageDraw.Draw(stars)
    for _ in range(240):
        sx, sy = rng.random() * W, rng.random() * H
        r = rng.uniform(0.6, 2.0)
        c = int(rng.uniform(90, 230))
        ds.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(c, c, min(255, c + 25)))
    st = np.asarray(stars, dtype=np.float32)
    f1 = _cloud_field(seed + 1, kx_max=2, ky_scale=1.6, n_waves=7)
    f2 = _cloud_field(seed + 2, kx_max=3, ky_scale=2.0, n_waves=7)
    base = vignette(bg, 0.4) + static_grain(seed=seed, amount=2.0)

    def frame(t01):
        img = base.copy()
        img = screen(img, st)
        c1 = np.clip(np.roll(f1, int(round(t01 * W)), axis=1) * 0.9, 0, 1)
        c2 = np.clip(np.roll(f2, -int(round(t01 * W)), axis=1) * 0.9, 0, 1)
        img = screen(img, blur(c1[:, :, None] * np.array([70, 30, 90],
                                                         dtype=np.float32), 30.0))
        img = screen(img, blur(c2[:, :, None] * np.array([20, 50, 90],
                                                         dtype=np.float32), 30.0))
        img = screen(img, radial_glow(0.62, 0.40, 0.16, (180, 120, 200),
                                      0.5 + 0.06 * np.sin(TWO_PI * t01),
                                      falloff=1.6, res_div=3))
        return img
    return frame


def scene_neon_rain(seed: int = 68):
    """サイバーパンク。night_skyline の構図をネオン配色にして雨を足す"""
    rng = np.random.default_rng(seed)
    horizon = int(H * 0.55)
    sky = vgrad([(6, 4, 16), (14, 8, 30), (30, 12, 44), (10, 6, 20)],
                stops=[0.0, 0.35, 0.60, 1.0])
    base = np.clip(screen(sky, radial_glow(0.5, 0.58, 0.6, (120, 30, 90),
                                           0.5, falloff=1.7)), 0, 255)
    layers = _city_layers(rng, W, H, horizon, tower_x=0.62)
    base = np.where((layers.sum(axis=2) > 1)[:, :, None], layers, base)
    # ネオンの光源
    neons = [(0.18, 0.50, (255, 40, 120)), (0.34, 0.44, (40, 220, 255)),
             (0.62, 0.30, (255, 60, 180)), (0.80, 0.52, (60, 120, 255)),
             (0.48, 0.56, (200, 80, 255))]
    base = vignette(base, 0.44) + static_grain(seed=seed, amount=2.4)

    def frame(t01):
        img = base.copy()
        for nx, ny, col in neons:
            fl = 0.7 + 0.3 * np.sin(TWO_PI * (2 * t01 + nx * 17))
            img = screen(img, radial_glow(nx, ny, 0.06, col, 0.7 * fl,
                                          falloff=1.5, res_div=3))
        # 濡れた路面の反射
        img = screen(img, radial_glow(0.5, 0.86, 0.5, (90, 30, 90),
                                      0.35, falloff=2.0, res_div=3))
        # 雨 (ほぼ垂直)
        img = screen(img, _particle_layer(
            t01, 210, seed + 1, H, W, length=0.05, thickness=1.8,
            color=(150, 170, 220), speed=4.0, drift=0.02) * 0.55)
        return img
    return frame


def scene_old_library(seed: int = 69):
    """古い図書室。本棚のシルエット + 蝋燭 + 埃の粒"""
    rng = np.random.default_rng(seed)
    y, x = _yx()
    bg = vgrad([(22, 14, 8), (34, 22, 12), (46, 30, 16), (24, 16, 10)])
    base = np.clip(screen(bg, radial_glow(0.30, 0.55, 0.35, (255, 170, 70),
                                          0.7, falloff=1.7)), 0, 255)
    # 本棚 (左右) — 棚板と本の背表紙
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for side_x0, side_x1 in ((0, int(W * 0.20)), (int(W * 0.80), W)):
        d.rectangle([side_x0, 0, side_x1, H], fill=(16, 10, 6))
        for shelf in range(5):
            sy = int(H * (0.08 + 0.19 * shelf))
            d.rectangle([side_x0, sy + 96, side_x1, sy + 104], fill=(28, 18, 10))
            bx = side_x0 + 8
            while bx < side_x1 - 14:
                bw = int(rng.uniform(10, 22))
                bh = int(rng.uniform(66, 92))
                shade = int(rng.uniform(20, 44))
                d.rectangle([bx, sy + 96 - bh, bx + bw, sy + 96],
                            fill=(shade, int(shade * 0.7), int(shade * 0.45)))
                bx += bw + 3
    shelves = np.asarray(im, dtype=np.float32)
    smask = (shelves.sum(axis=2) > 1)[:, :, None]
    base = vignette(base, 0.5) + static_grain(seed=seed, amount=2.4)

    def frame(t01):
        img = base.copy()
        img = np.where(smask, shelves, img)
        # 蝋燭の炎のゆらぎ
        fl = (0.75 + 0.18 * np.sin(TWO_PI * 5 * t01)
              + 0.07 * np.sin(TWO_PI * 11 * t01 + 1.3))
        img = screen(img, radial_glow(0.30, 0.62, 0.05, (255, 200, 100),
                                      1.1 * fl, falloff=1.1, res_div=3))
        img = screen(img, radial_glow(0.30, 0.60, 0.22, (255, 150, 50),
                                      0.5 * fl, falloff=1.8, res_div=3))
        # 光の中を漂う埃
        img = screen(img, _particle_layer(
            t01, 26, seed + 1, H, W, length=0.0, thickness=2.6,
            color=(255, 220, 150), speed=1.0, drift=0.8, size_var=1.4) * 0.35)
        return img
    return frame


def scene_black_screen(seed: int = 70):
    """
    完全な黒。睡眠系の確立フォーマット「black screen」。
    画面の光をゼロにする (部屋が暗いまま) ことが価値なので、
    洒落た演出を足してはいけない。
    """
    blank = np.zeros((H, W, 3), dtype=np.float32)

    def frame(t01):
        return blank
    return frame


SCENES = {
    "spaceship_window": scene_spaceship_window,
    "golden_light": scene_golden_light,
    "focus_depths": scene_focus_depths,
    "halloween_manor": scene_halloween_manor,
    "snow_cabin": scene_snow_cabin,
    "forest_camp": scene_forest_camp,
    "nebula": scene_nebula,
    "neon_rain": scene_neon_rain,
    "old_library": scene_old_library,
    "black_screen": scene_black_screen,
    "lantern_street": scene_lantern_street,
    "storm_window": scene_storm_window,
    "autumn_leaves": scene_autumn_leaves,
    "christmas_window": scene_christmas_window,
    "anime_dusk": scene_anime_dusk,
    "morning_meadow": scene_morning_meadow,
    "night_drive": scene_night_drive,
    "night_skyline": scene_night_skyline,
    "rainy_city": scene_rainy_city,
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
    w, h = size

    # 文字の可読性を上げる暗幕。
    # 単色の矩形だと境界に直線が出て安っぽく見えるので、
    # 上端から徐々に濃くなるグラデーションにする。
    y0 = int(h * 0.42)
    ramp = np.zeros((h, w, 4), dtype=np.uint8)
    t = np.clip((np.arange(h) - y0) / (h - y0), 0.0, 1.0) ** 1.4
    ramp[:, :, 3] = (t[:, None] * 165).astype(np.uint8)
    im = Image.alpha_composite(im.convert("RGBA"), Image.fromarray(ramp)).convert("RGB")

    d = ImageDraw.Draw(im, "RGBA")

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
