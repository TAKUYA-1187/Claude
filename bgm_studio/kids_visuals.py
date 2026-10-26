"""
子守唄シリーズ用の映像とサムネイル。

視聴者の指摘: 「暗くて抽象的な映像・小さな文字のサムネでは見られない」。
子ども向けの高再生動画 (例: Super Simple の「きらきらぼし」5,000 万回) に共通するのは
  1. 顔のあるキャラクターが画面の主役にいる
  2. 明るく、彩度の高いパステル調 (真っ暗にしない)
  3. サムネは キャラ + 太い丸文字 2〜3 語 + 縁取り で、スマホの小さな表示でも読める
の 3 点。ここではそれに倣いつつ、キャラクターは他社の星のキャラを真似ず、
オリジナルの「ナイトキャップをかぶって眠るお月さま (Luna)」をシリーズ共通の顔にする。

全ての動きは t01 ∈ [0,1) の周期関数なので、20 秒で完全にループする。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .visuals import H, TWO_PI, W, static_grain, vgrad

FONT_DIR = Path(__file__).resolve().parent / "fonts"


def _font(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    """丸ゴシック体 Fredoka (SIL OFL 1.1)。無ければ DejaVu Bold で代用"""
    try:
        f = ImageFont.truetype(str(FONT_DIR / "Fredoka.ttf"), size)
        f.set_variation_by_name(weight)
        return f
    except (OSError, ValueError):
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


# ──────────────────────────────────────────────────────────────
# スプライト (一度だけ高解像度で描いて、毎フレームは貼るだけ)
# ──────────────────────────────────────────────────────────────

def _supersample(draw_fn, size: tuple[int, int], ss: int = 3) -> Image.Image:
    """ss 倍で描いて縮小する。PIL の多角形はアンチエイリアスが無いため"""
    big = Image.new("RGBA", (size[0] * ss, size[1] * ss), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), ss)
    return big.resize(size, Image.LANCZOS)


def moon_sprite(px: int = 640) -> Image.Image:
    """ナイトキャップをかぶって眠る三日月 (Luna)。px 四方"""
    def draw(d: ImageDraw.ImageDraw, s: int):
        S = px * s
        cx, cy, r = S * 0.50, S * 0.56, S * 0.36
        body = (255, 226, 132, 255)
        # 三日月 = 大きな円 − ずらした円 (右側が欠ける)
        moon = Image.new("L", (S, S), 0)
        md = ImageDraw.Draw(moon)
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        md.ellipse([cx - r * 0.35, cy - r * 1.02, cx + r * 1.55, cy + r * 0.98], fill=0)
        layer = Image.new("RGBA", (S, S), body)
        d._image.paste(layer, (0, 0), moon)
        # 内側のやわらかい陰 (立体感)
        shade = Image.new("L", (S, S), 0)
        sd = ImageDraw.Draw(shade)
        sd.ellipse([cx - r * 0.95, cy - r * 0.95, cx + r * 0.6, cy + r * 0.95], fill=60)
        shade = shade.filter(ImageFilter.GaussianBlur(S * 0.03))
        shade = Image.fromarray(np.minimum(np.asarray(shade), np.asarray(moon)))
        d._image.paste(Image.new("RGBA", (S, S), (236, 170, 90, 255)), (0, 0),
                       Image.fromarray((np.asarray(shade) * 0.6).astype(np.uint8)))
        # 顔 (閉じた目・ほっぺ・口)。三日月の太い部分 (左側) に置く
        fx, fy = cx - r * 0.50, cy + r * 0.05
        lw = max(int(S * 0.012), 2)
        ink = (110, 70, 60, 255)
        d.arc([fx - r * 0.20, fy - r * 0.16, fx + r * 0.02, fy + r * 0.02],
              start=20, end=160, fill=ink, width=lw)          # 閉じた目 (∪)
        d.ellipse([fx - r * 0.30, fy + r * 0.06, fx - r * 0.08, fy + r * 0.20],
                  fill=(255, 150, 150, 200))                 # ほっぺ
        d.arc([fx - r * 0.05, fy + r * 0.14, fx + r * 0.13, fy + r * 0.30],
              start=10, end=170, fill=ink, width=lw)          # 口
        # ナイトキャップ。上の角 (外円と内円の交点 ≈ (+0.35r, -0.94r)) にかぶせ、
        # 先をたらして先端にぼんぼりを付ける。スプライトの外にはみ出さない寸法
        def bez(p0, p1, p2, n=24):
            t = np.linspace(0, 1, n)[:, None]
            return ((1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1)
                    + t ** 2 * np.array(p2)).tolist()
        P0 = (cx - r * 0.30, cy - r * 0.95)                  # つばの左端 (外円上)
        P1 = (cx + r * 0.46, cy - r * 0.86)                  # つばの右端 (角の先の少し外)
        T = (cx + r * 0.80, cy - r * 1.10)                   # たれた先端
        A = (cx - r * 0.05, cy - r * 1.62)                   # 上のふくらみ
        outline = bez(P0, A, T) + bez(T, (cx + r * 0.55, cy - r * 1.05), P1)[1:]
        capmask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(capmask).polygon([tuple(p) for p in outline], fill=255)
        capimg = Image.new("RGBA", (S, S), (122, 160, 236, 255))
        dots = ImageDraw.Draw(capimg)
        dr = r * 0.055
        for (ux, uy) in [(-0.10, -1.25), (0.15, -1.38), (0.30, -1.15), (0.50, -1.18),
                         (-0.02, -1.05), (0.62, -1.06)]:
            px_, py_ = cx + r * ux, cy + r * uy
            dots.ellipse([px_ - dr, py_ - dr, px_ + dr, py_ + dr], fill=(240, 246, 255, 255))
        d._image.paste(capimg, (0, 0), capmask)
        bw = r * 0.17                                        # つば (白い折り返し)
        d.line([P0, P1], fill=(250, 250, 255, 255), width=int(bw))
        for px_, py_ in (P0, P1):
            d.ellipse([px_ - bw / 2, py_ - bw / 2, px_ + bw / 2, py_ + bw / 2],
                      fill=(250, 250, 255, 255))
        pr = r * 0.13                                        # ぼんぼり
        d.ellipse([T[0] - pr, T[1] - pr, T[0] + pr, T[1] + pr], fill=(255, 255, 255, 255))
    return _supersample(draw, (px, px))


def cloud_sprite(w: int, h: int, seed: int, color=(246, 238, 255)) -> Image.Image:
    """円を重ねたふわふわの雲。円がスプライトの外に出ると縁が直線で切れるので、内側に収める"""
    rng = np.random.default_rng(seed)

    def draw(d: ImageDraw.ImageDraw, s: int):
        Wb, Hb = w * s, h * s
        base_y = Hb * 0.70
        floor = Hb * 0.86
        n = 5
        for i in range(n):
            rr = Hb * (0.30 if i in (0, n - 1) else rng.uniform(0.34, 0.44))
            x = Wb * 0.08 + rr + (Wb * 0.84 - 2 * rr) * i / (n - 1)
            top = max(base_y - rr * 1.2, Hb * 0.04)
            d.ellipse([x - rr, top, x + rr, min(base_y + rr * 0.5, floor)],
                      fill=(*color, 255))
        d.rounded_rectangle([Wb * 0.10, base_y - Hb * 0.12, Wb * 0.90, floor],
                            radius=int(Hb * 0.14), fill=(*color, 255))
    im = _supersample(draw, (w, h))
    return im.filter(ImageFilter.GaussianBlur(1.2))


def sparkle_sprite(px: int) -> Image.Image:
    """4 方向に光る小さな星 (きらきら)"""
    def draw(d: ImageDraw.ImageDraw, s: int):
        S = px * s
        c = S / 2
        a, b = S * 0.48, S * 0.11
        d.polygon([(c, c - a), (c + b, c - b), (c + a, c), (c + b, c + b),
                   (c, c + a), (c - b, c + b), (c - a, c), (c - b, c - b)],
                  fill=(255, 246, 196, 255))
    im = _supersample(draw, (px, px))
    glow = im.filter(ImageFilter.GaussianBlur(px * 0.12))
    return Image.alpha_composite(glow, im)


# ──────────────────────────────────────────────────────────────
# シーン
# ──────────────────────────────────────────────────────────────

def scene_lullaby_moon(seed: int = 80):
    """パステルの夜空。眠るお月さまがゆらゆら揺れ、雲が流れ、星がきらめく"""
    rng = np.random.default_rng(seed)
    # 真っ暗にしない。上は藍、下はラベンダー〜桃色
    bg = vgrad([(38, 44, 112), (70, 66, 150), (126, 102, 182), (196, 150, 196)],
               stops=[0.0, 0.45, 0.78, 1.0])
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    # 月の後光
    d = np.sqrt(((x - 0.70) * (W / H)) ** 2 + (y - 0.36) ** 2)
    bg = bg + (np.exp(-(d / 0.42) ** 2) * 70)[:, :, None] * np.array([1.0, 0.92, 0.6])
    # なだらかな丘 (2 層)
    xs = np.linspace(0, 1, W)
    hill1 = 0.86 + 0.035 * np.sin(TWO_PI * (xs * 1.3 + 0.1))
    hill2 = 0.92 + 0.025 * np.sin(TWO_PI * (xs * 2.1 + 0.6))
    m1 = (y >= hill1[None, :]).astype(np.float32)
    m2 = (y >= hill2[None, :]).astype(np.float32)
    bg = bg * (1 - m1[:, :, None]) + m1[:, :, None] * np.array([92, 78, 150])
    bg = bg * (1 - m2[:, :, None]) + m2[:, :, None] * np.array([70, 58, 126])
    base = np.clip(bg + static_grain(seed=seed, amount=1.6), 0, 255).astype(np.uint8)
    base_im = Image.fromarray(base).filter(ImageFilter.GaussianBlur(1.0)).convert("RGBA")

    moon = moon_sprite(600)
    clouds = [(cloud_sprite(int(rng.uniform(300, 460)), int(rng.uniform(150, 210)),
                            seed=seed + i,
                            color=(250, 244, 255) if i % 2 == 0 else (236, 226, 252)),
               rng.uniform(0, 1), rng.uniform(0.60, 0.82), int(rng.integers(1, 2)),
               rng.uniform(0.75, 1.0))
              for i in range(4)]
    n_sp = 46
    sp_x = rng.uniform(0.02, 0.98, n_sp)
    sp_y = rng.uniform(0.04, 0.62, n_sp)
    sp_s = rng.integers(14, 40, n_sp)
    sp_ph = rng.uniform(0, TWO_PI, n_sp)
    sp_cy = rng.integers(1, 4, n_sp)
    sparkles = {int(s): sparkle_sprite(int(s)) for s in np.unique(sp_s)}
    zfonts = [_font(40 + 14 * j, "SemiBold") for j in range(3)]

    def frame(t01: float) -> np.ndarray:
        im = base_im.copy()
        # 星のきらめき (大きさと明るさが周期的に変わる)
        for i in range(n_sp):
            k = 0.55 + 0.45 * np.sin(TWO_PI * sp_cy[i] * t01 + sp_ph[i])
            sz = max(int(sp_s[i] * (0.6 + 0.4 * k)), 6)
            sp = sparkles[int(sp_s[i])].resize((sz, sz), Image.BILINEAR)
            a = np.asarray(sp.split()[3], dtype=np.float32) * (0.35 + 0.65 * k)
            sp.putalpha(Image.fromarray(a.astype(np.uint8)))
            im.alpha_composite(sp, (int(sp_x[i] * W) - sz // 2, int(sp_y[i] * H) - sz // 2))
        # 雲。画面を横切らせると 20 秒ループでは速すぎて落ち着かないので、
        # その場でゆっくり左右に揺らすだけにする (不透明。半透明だと丘の線が透けた)
        for k, (spr, x0, yy, cyc, _alpha) in enumerate(clouds):
            xx = int(x0 * (W - spr.width) + 40 * np.sin(TWO_PI * (t01 + k * 0.23)))
            im.alpha_composite(spr, (xx, int(yy * H)))
        # お月さま (ゆりかごのように ±5° 揺れて、少し上下する)
        ang = 5.0 * np.sin(TWO_PI * 2 * t01)
        bob = 10.0 * np.sin(TWO_PI * 2 * t01 + 0.6)
        mr = moon.rotate(ang, resample=Image.BICUBIC, expand=False)
        im.alpha_composite(mr, (int(W * 0.70 - mr.width / 2), int(H * 0.36 - mr.height / 2 + bob)))
        # Zzz (順番にふわっと浮かんで消える)
        dz = ImageDraw.Draw(im)
        for j in range(3):
            p = (t01 * 2 + j / 3.0) % 1.0
            a = int(255 * np.sin(np.pi * p) ** 1.5)
            zx = W * 0.62 - 40 * j + 30 * np.sin(TWO_PI * p)
            zy = H * 0.20 - 160 * p
            dz.text((zx, zy), "z", font=zfonts[j],
                    fill=(255, 255, 255, a))
        return np.asarray(im.convert("RGB"), dtype=np.float32)
    return frame


KIDS_SCENES = {"lullaby_moon": scene_lullaby_moon}


# ──────────────────────────────────────────────────────────────
# サムネイル
# ──────────────────────────────────────────────────────────────

def _outlined(d: ImageDraw.ImageDraw, xy, text, font, fill, stroke, width):
    d.text(xy, text, font=font, fill=fill, stroke_width=width, stroke_fill=stroke)


def kids_thumbnail(title_lines: list[str], badge: str, sub: str = "",
                   scene: str = "lullaby_moon", seed: int = 80,
                   size=(1280, 720)) -> Image.Image:
    """
    子ども向けの高再生サムネに倣ったレイアウト:
      左: 太い丸文字 2 行 (黄色 + 濃紺の太い縁取り)
      左下: 用途のバッジ (桃色の角丸)
      右: キャラクター (映像の 1 コマ)
    """
    frame = KIDS_SCENES[scene](seed=seed)(0.18)
    im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    # 彩度を少し上げる (小さい表示でも目に留まる)
    from PIL import ImageEnhance
    im = ImageEnhance.Color(im).enhance(1.18).convert("RGBA")
    w, h = size
    d = ImageDraw.Draw(im)

    x0 = int(w * 0.05)
    y = int(h * 0.14)
    for i, line in enumerate(title_lines):
        size_px = int(h * (0.20 if len(line) <= 9 else 0.155))
        f = _font(size_px, "Bold")
        while d.textbbox((0, 0), line, font=f)[2] > w * 0.60 and size_px > 40:
            size_px -= 4
            f = _font(size_px, "Bold")
        _outlined(d, (x0, y), line, f, (255, 224, 74), (38, 34, 102), int(size_px * 0.10))
        y += int(size_px * 1.08)

    # バッジ
    bf = _font(int(h * 0.075), "SemiBold")
    bb = d.textbbox((0, 0), badge, font=bf)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    by = y + int(h * 0.04)
    d.rounded_rectangle([x0, by, x0 + bw + int(h * 0.08), by + bh + int(h * 0.06)],
                        radius=int(h * 0.05), fill=(255, 128, 170), outline=(255, 255, 255),
                        width=int(h * 0.008))
    d.text((x0 + int(h * 0.04), by + int(h * 0.025) - bb[1]), badge, font=bf,
           fill=(255, 255, 255))
    if sub:
        sf = _font(int(h * 0.058), "SemiBold")
        _outlined(d, (x0, by + bh + int(h * 0.11)), sub, sf, (255, 255, 255),
                  (38, 34, 102), int(h * 0.008))
    return im.convert("RGB")
