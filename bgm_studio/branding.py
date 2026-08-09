"""
チャンネルアート生成。

アイコン (800×800) とバナー (2048×1152) を、動画本編と同じ
シーン生成エンジンから作る。動画とチャンネルページの世界観が
揃っていることが「ちゃんとしたチャンネル」に見える最大の要因なので、
素材を共有するのが正しい。

バナーは表示領域がデバイスごとに違う。
  全体      2048 × 1152
  安全領域  1235 ×  338  (中央。全デバイスで必ず見える)
文字は必ず安全領域の内側に置く。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import visuals as V

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BANNER_W, BANNER_H = 2048, 1152
SAFE_W, SAFE_H = 1235, 338
ICON_SIZE = 800


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size=size)
    except OSError:
        return ImageFont.load_default()


def _scene_image(scene: str, seed: int, w: int, h: int, t01: float = 0.3) -> Image.Image:
    """シーンを1フレーム描画して指定サイズへ切り出す"""
    frame = V.SCENES[scene](seed=seed)(t01)
    im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
    # アスペクト比を保ったまま中央でクロップ
    src_ar, dst_ar = im.width / im.height, w / h
    if src_ar > dst_ar:
        new_w = int(im.height * dst_ar)
        im = im.crop(((im.width - new_w) // 2, 0, (im.width + new_w) // 2, im.height))
    else:
        new_h = int(im.width / dst_ar)
        im = im.crop((0, (im.height - new_h) // 2, im.width, (im.height + new_h) // 2))
    return im.resize((w, h), Image.LANCZOS)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font_path: str,
              max_w: int, start: int, min_size: int = 12) -> ImageFont.FreeTypeFont:
    """max_w に収まる最大のフォントサイズを見つける"""
    size = start
    while size > min_size:
        f = _font(font_path, size)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        size -= 2
    return _font(font_path, min_size)


# ──────────────────────────────────────────────────────────────

def channel_icon(name: str, scene: str = "coffee_shop", seed: int = 42,
                 accent: tuple[int, int, int] = (255, 198, 122),
                 lines: list[str] | None = None, blur_px: float = 14.0,
                 line_scale: list[float] | None = None) -> Image.Image:
    """
    チャンネルアイコン 800×800。

    小さく表示されたときに読めることが全て。既定では頭文字だけを大きく置く。
    lines を渡すと任意の行構成にできるが、
    行数が増えるほど 32px 表示での可読性は落ちる。
    """
    im = _scene_image(scene, seed, ICON_SIZE, ICON_SIZE, t01=0.3)
    im = im.filter(ImageFilter.GaussianBlur(blur_px))

    a = np.asarray(im, dtype=np.float32)
    # 中心を明るく、周辺を暗くして文字を浮かせる
    y, x = np.mgrid[0:ICON_SIZE, 0:ICON_SIZE].astype(np.float32) / ICON_SIZE
    d = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.7
    a *= np.clip(1.25 - 0.85 * d ** 2, 0.15, 1.3)[:, :, None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    d2 = ImageDraw.Draw(im)

    if lines is None:
        words = [w for w in name.replace("-", " ").split() if w]
        lines = ["".join(w[0] for w in words[:2]).upper() or name[:2].upper()]
    if line_scale is None:
        line_scale = [1.0] * len(lines)

    # 各行のフォントを決めてから、全体を縦中央に置く
    fonts, heights = [], []
    n = len(lines)
    base_h = int(ICON_SIZE * (0.60 if n == 1 else 0.72 / n))
    for text, sc in zip(lines, line_scale):
        f = _fit_text(d2, text, FONT_BOLD, int(ICON_SIZE * 0.84),
                      int(base_h * sc))
        fonts.append(f)
        bb = d2.textbbox((0, 0), text, font=f)
        heights.append(bb[3] - bb[1])

    gap = int(ICON_SIZE * 0.035)
    total = sum(heights) + gap * (n - 1)
    cy = (ICON_SIZE - total) // 2

    for text, f, h in zip(lines, fonts, heights):
        bb = d2.textbbox((0, 0), text, font=f)
        tx = (ICON_SIZE - (bb[2] - bb[0])) // 2 - bb[0]
        ty = cy - bb[1]
        for ox, oy in ((-6, 0), (6, 0), (0, -6), (0, 6), (-4, -4), (4, 4)):
            d2.text((tx + ox, ty + oy), text, font=f, fill=(0, 0, 0, 215))
        d2.text((tx, ty), text, font=f, fill=accent)
        cy += h + gap

    # 円形に切り抜く (YouTube 側で丸くされるので、角の情報を捨てておく)
    mask = Image.new("L", (ICON_SIZE, ICON_SIZE), 0)
    ImageDraw.Draw(mask).ellipse([6, 6, ICON_SIZE - 6, ICON_SIZE - 6], fill=255)
    out = Image.new("RGB", (ICON_SIZE, ICON_SIZE), (16, 18, 20))
    out.paste(im, (0, 0), mask)
    return out


def channel_banner(name: str, tagline: str = "", scene: str = "rainy_window",
                   seed: int = 7,
                   accent: tuple[int, int, int] = (255, 214, 150)) -> Image.Image:
    """
    チャンネルバナー 2048×1152。
    文字は中央 1235×338 の安全領域の内側にだけ置く。
    """
    im = _scene_image(scene, seed, BANNER_W, BANNER_H, t01=0.25)
    im = im.filter(ImageFilter.GaussianBlur(6))

    a = np.asarray(im, dtype=np.float32) * 0.62
    # 中央を横長に暗くして文字を読ませる
    y, x = np.mgrid[0:BANNER_H, 0:BANNER_W].astype(np.float32)
    cx, cy = BANNER_W / 2, BANNER_H / 2
    band = np.exp(-(((x - cx) / (BANNER_W * 0.42)) ** 2
                    + ((y - cy) / (BANNER_H * 0.20)) ** 2))
    a *= (1.0 - 0.45 * band)[:, :, None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    d = ImageDraw.Draw(im)
    sx0 = (BANNER_W - SAFE_W) // 2
    sy0 = (BANNER_H - SAFE_H) // 2

    # チャンネル名
    f_name = _fit_text(d, name, FONT_BOLD, int(SAFE_W * 0.88), 150)
    bb = d.textbbox((0, 0), name, font=f_name)
    nx = sx0 + (SAFE_W - (bb[2] - bb[0])) // 2 - bb[0]
    ny = sy0 + int(SAFE_H * 0.20)
    for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        d.text((nx + ox, ny + oy), name, font=f_name, fill=(0, 0, 0, 200))
    d.text((nx, ny), name, font=f_name, fill=(255, 255, 255))

    # タグライン
    if tagline:
        f_tag = _fit_text(d, tagline, FONT_REG, int(SAFE_W * 0.82), 54)
        bb2 = d.textbbox((0, 0), tagline, font=f_tag)
        tx = sx0 + (SAFE_W - (bb2[2] - bb2[0])) // 2 - bb2[0]
        ty = ny + (bb[3] - bb[1]) + int(SAFE_H * 0.16)
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            d.text((tx + ox, ty + oy), tagline, font=f_tag, fill=(0, 0, 0, 190))
        d.text((tx, ty), tagline, font=f_tag, fill=accent)

        # 細い区切り線
        line_y = ny + (bb[3] - bb[1]) + int(SAFE_H * 0.10)
        d.line([(sx0 + SAFE_W // 2 - 90, line_y), (sx0 + SAFE_W // 2 + 90, line_y)],
               fill=accent + (150,), width=2)

    return im


def build_all(name: str, tagline: str, out_dir: str | Path = "out/branding",
              icon_scene: str = "coffee_shop", banner_scene: str = "rainy_window",
              seed: int = 42) -> dict[str, Path]:
    """アイコンとバナーを書き出す"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    p = out_dir / "icon_800.png"
    channel_icon(name, scene=icon_scene, seed=seed).save(p)
    paths["icon"] = p

    p = out_dir / "banner_2048x1152.png"
    channel_banner(name, tagline, scene=banner_scene, seed=seed + 5).save(p)
    paths["banner"] = p

    return paths
