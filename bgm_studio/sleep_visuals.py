"""
大人向けの睡眠ピアノ (柱 A「Gentle Piano for Sleep」) の映像とサムネイル。

子守唄のキャラクター映像とは逆に、顔や文字の動きは入れない。
寝る前に一度だけ画面を見て「落ち着く」と感じ、あとは画面を見ないで聞く使われ方なので、
  - 暗すぎない深い藍色 (真っ黒は「止まっている」ように見える)
  - 動くのは、湖面に映る月の揺らぎ・ゆっくりした星のまたたきだけ
  - サムネは大きな白い文字 2 語 + 「雨音なし・雑音なし」の約束
にしている。雨や環境音を嫌う視聴者 (このチャンネルのオーナー自身がそう) に向けて、
「NO RAIN · NO NOISE」をはっきり書くのが差別化になる。
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .kids_visuals import _font, _outlined, moon_sprite, sparkle_sprite
from .visuals import H, TWO_PI, W, _upscale, static_grain, vgrad


# Sleep Piano シリーズの色違い。同じ構図で色だけ変え、シリーズとして並んだときに
# 「同じチャンネルの別の回」と一目で分かるようにする
PALETTES = {
    "blue": dict(sky=[(14, 22, 58), (30, 42, 92), (62, 74, 134), (104, 104, 160)],
                 ridge=[(36, 40, 82), (24, 28, 62)]),
    "violet": dict(sky=[(28, 16, 58), (58, 36, 104), (112, 74, 150), (176, 120, 170)],
                   ridge=[(62, 40, 96), (42, 26, 72)]),
    "teal": dict(sky=[(8, 26, 46), (18, 54, 78), (40, 96, 116), (92, 140, 150)],
                 ridge=[(20, 52, 66), (12, 36, 50)]),
}


def scene_moon_lake(seed: int = 90, palette: str = "blue"):
    """静かな湖に映る三日月。揺れるのは月の映り込みと星だけ"""
    rng = np.random.default_rng(seed)
    pal = PALETTES[palette]
    horizon = 0.66
    sky = vgrad(pal["sky"], stops=[0.0, 0.40, 0.56, horizon])
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    mx, my = 0.64, 0.28
    d = np.sqrt(((x - mx) * (W / H)) ** 2 + (y - my) ** 2)
    sky = sky + (np.exp(-(d / 0.30) ** 2) * 55)[:, :, None] * np.array([1.0, 0.95, 0.8])
    # 遠くの山並み (2 層)
    xs = np.linspace(0, 1, W)
    ridge1 = horizon - 0.055 - 0.035 * (np.sin(TWO_PI * (xs * 1.7 + 0.2)) * 0.6
                                         + np.sin(TWO_PI * (xs * 4.3 + 0.7)) * 0.4)
    ridge2 = horizon - 0.020 - 0.018 * np.sin(TWO_PI * (xs * 3.1 + 0.4))
    m1 = ((y >= ridge1[None, :]) & (y < horizon)).astype(np.float32)
    m2 = ((y >= ridge2[None, :]) & (y < horizon)).astype(np.float32)
    sky = sky * (1 - m1[:, :, None]) + m1[:, :, None] * np.array(pal["ridge"][0])
    sky = sky * (1 - m2[:, :, None]) + m2[:, :, None] * np.array(pal["ridge"][1])
    # 湖面 (空を上下反転して暗くしたもの)
    water_rows = H - int(horizon * H)
    top = int(horizon * H)
    refl = sky[top - water_rows:top][::-1] * 0.55
    base = sky.copy()
    base[top:] = refl
    base = base + static_grain(seed=seed, amount=1.4)
    base_im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)) \
        .filter(ImageFilter.GaussianBlur(1.2)).convert("RGBA")

    moon = moon_sprite(300, face=False, cap=False, body=(252, 240, 210, 255))
    n_st = 140
    st_x = rng.uniform(0.0, 1.0, n_st)
    st_y = rng.uniform(0.02, horizon - 0.12, n_st) ** 1.2
    st_s = rng.integers(6, 18, n_st)
    st_ph = rng.uniform(0, TWO_PI, n_st)
    st_cy = rng.integers(1, 3, n_st)
    sparkles = {int(s): sparkle_sprite(int(s)) for s in np.unique(st_s)}

    # 月の映り込み (低解像度で計算して拡大する)
    rh, rw = water_rows // 3, W // 3
    ry = np.linspace(0, 1, rh, dtype=np.float32)[:, None]
    rx = np.linspace(0, 1, rw, dtype=np.float32)[None, :]

    def frame(t01: float) -> np.ndarray:
        im = base_im.copy()
        for i in range(n_st):
            k = 0.5 + 0.5 * np.sin(TWO_PI * st_cy[i] * t01 + st_ph[i])
            sz = max(int(st_s[i] * (0.7 + 0.3 * k)), 4)
            sp = sparkles[int(st_s[i])].resize((sz, sz), Image.BILINEAR)
            a = np.asarray(sp.split()[3], dtype=np.float32) * (0.25 + 0.6 * k)
            sp.putalpha(Image.fromarray(a.astype(np.uint8)))
            im.alpha_composite(sp, (int(st_x[i] * W) - sz // 2, int(st_y[i] * H) - sz // 2))
        im.alpha_composite(moon, (int(mx * W - moon.width / 2), int(my * H - moon.height / 2)))

        # 縦に伸びた光の帯を、横方向のさざ波で切れ切れにする
        wob = 0.012 * np.sin(TWO_PI * (ry * 9.0 - 2 * t01)) \
            + 0.006 * np.sin(TWO_PI * (ry * 23.0 + 3 * t01))
        width = 0.018 + 0.05 * ry
        band = np.exp(-((rx - mx - wob) / width) ** 2)
        rip = 0.55 + 0.45 * np.sin(TWO_PI * (ry * 40.0 - 4 * t01)) ** 2
        fade = (1.0 - ry) ** 1.4
        g = (band * rip * fade * 150.0)[:, :, None] * np.array([1.0, 0.96, 0.85])
        g = _upscale(g.astype(np.float32), water_rows, W)
        arr = np.asarray(im.convert("RGB"), dtype=np.float32)
        arr[top:] = 255.0 - (255.0 - arr[top:]) * (255.0 - g) / 255.0
        return arr
    return frame


SLEEP_SCENES = {
    "moon_lake": scene_moon_lake,
    "moon_lake_violet": lambda seed=90: scene_moon_lake(seed, "violet"),
    "moon_lake_teal": lambda seed=90: scene_moon_lake(seed, "teal"),
}


def calm_thumbnail(title_lines: list[str], badge: str, promise: str,
                   scene: str = "moon_lake", seed: int = 90,
                   size=(1280, 720), badge_color=(246, 214, 140),
                   brighten: float = 1.12) -> Image.Image:
    """
    大人向け睡眠動画のサムネ: 左に大きな白い文字 2 行、その下に長さのバッジと「約束」の 1 行。
    子ども向けの黄色い文字とは色を変えて、同じチャンネルでも棚が分かれて見えるようにする
    """
    from .visuals import scene_maker
    frame = scene_maker(scene)(seed=seed)(0.2)
    im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    im = ImageEnhance.Brightness(im).enhance(brighten)
    im = ImageEnhance.Color(im).enhance(1.12).convert("RGBA")
    w, h = size
    d = ImageDraw.Draw(im)
    x0 = int(w * 0.05)
    y = int(h * 0.16)
    for line in title_lines:
        px = int(h * 0.19)
        f = _font(px, "SemiBold")
        while d.textbbox((0, 0), line, font=f)[2] > w * 0.50 and px > 40:   # 月 (横 64%) に重ねない
            px -= 4
            f = _font(px, "SemiBold")
        _outlined(d, (x0, y), line, f, (255, 255, 255), (16, 22, 60), int(px * 0.07))
        y += int(px * 1.06)
    bf = _font(int(h * 0.072), "SemiBold")
    bb = d.textbbox((0, 0), badge, font=bf)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    by = y + int(h * 0.04)
    d.rounded_rectangle([x0, by, x0 + bw + int(h * 0.08), by + bh + int(h * 0.06)],
                        radius=int(h * 0.05), fill=badge_color)
    d.text((x0 + int(h * 0.04), by + int(h * 0.025) - bb[1]), badge, font=bf,
           fill=(28, 32, 74))
    pf = _font(int(h * 0.058), "Medium")
    _outlined(d, (x0, by + bh + int(h * 0.11)), promise, pf, (226, 232, 255),
              (16, 22, 60), int(h * 0.006))
    return im.convert("RGB")
