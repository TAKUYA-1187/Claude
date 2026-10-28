"""
イラスト (静止画) を背景にした映像と、上品な文字組みのサムネイル。

2026-10-28 オーナーの判断:「背景とサムネは ChatGPT の作ったもの (水彩の月夜・眠る子猫・
セリフ体の金文字) が最適」。絵を描くのは画像生成ができる ChatGPT に任せ、こちらは
  - その静止画を 20 秒で完全ループする「生きた絵」にする (ゆっくりした呼吸のようなズーム、
    星のまたたき、漂う光の粒)
  - 同じ雰囲気の文字組みでサムネを作る (Cinzel のタイトル + 字間を空けた副題 + 枠線の時間バッジ
    + チャンネル名)
を受け持つ。文字の入っていない絵 (16:9, 1920x1080 以上) を art/ に置いて使う。

ChatGPT の絵がまだ無い動画には、こちらのシーンに水彩風の処理 (watercolor) をかけて代わりにする。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .visuals import H, TWO_PI, W

FONT_DIR = Path(__file__).resolve().parent / "fonts"
CREAM = (248, 236, 212)
INK = (22, 26, 52)


def _font(name: str, size: int, weight: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT_DIR / f"{name}.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def _cover(im: Image.Image, w: int, h: int) -> Image.Image:
    """縦横比を保ったまま (w, h) を覆う大きさにして中央で切る"""
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    x0, y0 = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


# ──────────────────────────────────────────────────────────────
# 水彩風の処理 (ChatGPT の絵が無いときの代わり)
# ──────────────────────────────────────────────────────────────

def watercolor(im: Image.Image, seed: int = 0) -> Image.Image:
    """平らな塗りを、にじみ・顔料のたまり・紙の目のある水彩風にする"""
    rng = np.random.default_rng(seed)
    base = im.convert("RGB").filter(ImageFilter.MedianFilter(5))
    a = np.asarray(base, dtype=np.float32)
    soft = np.asarray(base.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32)
    # 顔料が縁にたまる: 局所の変化が大きいところを少し濃くする
    edge = np.abs(a - soft).mean(axis=2, keepdims=True)
    edge = np.clip(edge / 18.0, 0, 1)
    a = a * (1.0 - 0.22 * edge)
    # にじみ
    a = 0.7 * a + 0.3 * np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
                                   .filter(ImageFilter.GaussianBlur(2.2)), dtype=np.float32)
    # 紙の目 (細かい粒 + ゆるいムラ)
    h, w = a.shape[:2]
    grain = rng.standard_normal((h, w)).astype(np.float32)
    grain = np.asarray(Image.fromarray(((grain * 22) + 128).clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 128.0 - 1.0
    low = rng.standard_normal((h // 64 + 2, w // 64 + 2)).astype(np.float32)
    low = np.asarray(Image.fromarray(((low * 30) + 128).clip(0, 255).astype(np.uint8))
                     .resize((w, h), Image.BICUBIC), dtype=np.float32) / 128.0 - 1.0
    paper = 1.0 + 0.035 * grain[:, :, None] + 0.04 * low[:, :, None]
    a = a * paper
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return ImageEnhance.Color(out).enhance(0.92)


# ──────────────────────────────────────────────────────────────
# 静止画を「生きた絵」にする
# ──────────────────────────────────────────────────────────────

def _sparkle(px: int) -> Image.Image:
    big = Image.new("L", (px * 4, px * 4), 0)
    d = ImageDraw.Draw(big)
    c, a, b = px * 2, px * 1.9, px * 0.35
    d.polygon([(c, c - a), (c + b, c - b), (c + a, c), (c + b, c + b),
               (c, c + a), (c - b, c + b), (c - a, c), (c - b, c - b)], fill=255)
    m = big.resize((px, px), Image.LANCZOS)
    g = m.filter(ImageFilter.GaussianBlur(px * 0.15))
    m = Image.fromarray(np.maximum(np.asarray(m), np.asarray(g)))
    spr = Image.new("RGBA", (px, px), (255, 246, 214, 0))
    spr.putalpha(m)
    return spr


def _mote(px: int) -> Image.Image:
    """ふわっと光る粒 (蛍・光のほこり)"""
    y, x = np.mgrid[0:px, 0:px].astype(np.float32)
    r = np.sqrt((x - px / 2) ** 2 + (y - px / 2) ** 2) / (px / 2)
    a = np.clip(1.0 - r, 0, 1) ** 2.2
    spr = Image.new("RGBA", (px, px), (255, 236, 170, 0))
    spr.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return spr


def scene_from_image(path: str | Path, seed: int = 0, sky_frac: float = 0.42,
                     n_stars: int = 36, n_motes: int = 22):
    """
    静止画 → フレーム関数 (t01 ∈ [0,1) で完全ループ)。
      - 1.00〜1.035 倍の呼吸のようなズームと、ごくわずかな横移動 (20 秒で 1 往復)
      - 画面上部 (空) に、絵の明るさに合わせた星のまたたき
      - 下半分に、ゆっくり漂って明滅する光の粒
    """
    rng = np.random.default_rng(seed)
    src = Image.open(path).convert("RGB")
    over = 1.06
    big = _cover(src, int(W * over), int(H * over))
    lum = np.asarray(big.convert("L"), dtype=np.float32)

    # 星は「空」の暗いところだけに置く (明るい雲や月の上には置かない)
    stars = []
    tries = 0
    while len(stars) < n_stars and tries < n_stars * 40:
        tries += 1
        x = rng.uniform(0.02, 0.98)
        y = rng.uniform(0.02, sky_frac)
        px_, py_ = int(x * big.width), int(y * big.height)
        if lum[py_, px_] < 95:
            stars.append((x, y, int(rng.integers(8, 20)), rng.uniform(0, TWO_PI),
                          int(rng.integers(1, 3))))
    star_spr = {s: _sparkle(s) for s in {st[2] for st in stars}}
    motes = [(rng.uniform(0.05, 0.95), rng.uniform(0.55, 0.92), int(rng.integers(10, 22)),
              rng.uniform(0, TWO_PI), rng.uniform(0.01, 0.03), int(rng.integers(1, 3)))
             for _ in range(n_motes)]
    mote_spr = {s: _mote(s) for s in {m[2] for m in motes}}

    def frame(t01: float) -> np.ndarray:
        z = 1.0 + 0.0175 * (1 - np.cos(TWO_PI * t01))          # 1.0 → 1.035 → 1.0
        cw, ch = int(W * over / z), int(H * over / z)
        cx = (big.width - cw) / 2 + 8 * np.sin(TWO_PI * t01)
        cy = (big.height - ch) / 2
        im = big.crop((int(cx), int(cy), int(cx) + cw, int(cy) + ch)).resize((W, H), Image.BICUBIC)
        im = im.convert("RGBA")
        sx, sy = W / cw, H / ch
        for (x, y, s, ph, cyc) in stars:
            k = 0.5 + 0.5 * np.sin(TWO_PI * cyc * t01 + ph)
            sz = max(int(s * (0.6 + 0.4 * k)), 4)
            spr = star_spr[s].resize((sz, sz), Image.BILINEAR)
            al = (np.asarray(spr.split()[3], dtype=np.float32) * (0.25 + 0.75 * k)).astype(np.uint8)
            spr.putalpha(Image.fromarray(al))
            px_ = int((x * big.width - cx) * sx) - sz // 2
            py_ = int((y * big.height - cy) * sy) - sz // 2
            if 0 <= px_ < W - sz and 0 <= py_ < H - sz:
                im.alpha_composite(spr, (px_, py_))
        for (x, y, s, ph, amp, cyc) in motes:
            mx = x + amp * np.sin(TWO_PI * t01 + ph)
            my = y + amp * 0.8 * np.sin(TWO_PI * 2 * t01 + ph * 1.3)
            k = 0.5 + 0.5 * np.sin(TWO_PI * cyc * t01 + ph * 2.0)
            spr = mote_spr[s]
            al = (np.asarray(spr.split()[3], dtype=np.float32) * (0.15 + 0.6 * k)).astype(np.uint8)
            spr = spr.copy()
            spr.putalpha(Image.fromarray(al))
            im.alpha_composite(spr, (int(mx * W) - s // 2, int(my * H) - s // 2))
        return np.asarray(im.convert("RGB"), dtype=np.float32)
    return frame


# ──────────────────────────────────────────────────────────────
# 上品な文字組みのサムネイル (ChatGPT のサムネに倣う)
# ──────────────────────────────────────────────────────────────

def _leaf(d: ImageDraw.ImageDraw, x: int, y: int, s: int, color):
    """チャンネル名の前に置く小さな双葉"""
    d.ellipse([x, y - s * 0.55, x + s * 0.55, y + s * 0.05], fill=color)
    d.ellipse([x + s * 0.45, y - s * 0.75, x + s * 1.05, y - s * 0.12], fill=color)
    d.line([(x + s * 0.5, y + s * 0.45), (x + s * 0.5, y - s * 0.3)], fill=color, width=max(s // 8, 2))


def _glow_text(base: Image.Image, xy, text, font, fill, glow=(0, 0, 0), radius=10,
               strength=170, spacing: int = 0):
    """柔らかい影 (後光) 付きの文字。spacing で字間を空ける"""
    layer = Image.new("L", base.size, 0)
    d = ImageDraw.Draw(layer)
    _draw_spaced(d, xy, text, font, 255, spacing)
    halo = layer.filter(ImageFilter.GaussianBlur(radius))
    halo = Image.fromarray((np.asarray(halo, dtype=np.float32) * strength / 255).astype(np.uint8))
    base.paste(Image.new("RGB", base.size, glow), (0, 0), halo)
    d2 = ImageDraw.Draw(base)
    _draw_spaced(d2, xy, text, font, fill, spacing)


def _draw_spaced(d, xy, text, font, fill, spacing):
    x, y = xy
    if spacing == 0:
        d.text((x, y), text, font=font, fill=fill)
        return
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + spacing


def _spaced_width(d, text, font, spacing):
    return sum(d.textlength(ch, font=font) for ch in text) + spacing * max(len(text) - 1, 0)


def elegant_thumbnail(background: Image.Image, title_lines: list[str], subtitle: str,
                      badge: str, brand: str = "QUIET HOURS MUSIC",
                      size=(1280, 720), text_center_x: float = 0.30) -> Image.Image:
    """
    左寄りに大きなセリフ体のタイトル 2 行、その下に線で挟んだ字間の広い副題、
    左下に枠線の時間バッジとチャンネル名。左側だけ少し暗くして文字を読ませる
    """
    w, h = size
    im = _cover(background.convert("RGB"), w, h)
    # 左側を暗くするグラデーション (右の主役の絵はそのまま)
    a = np.asarray(im, dtype=np.float32)
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
    shade = 1.0 - 0.38 * np.clip(1.0 - x / 0.62, 0, 1) ** 1.3
    im = Image.fromarray(np.clip(a * shade, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    cx = int(w * text_center_x)

    y = int(h * 0.20)
    for line in title_lines:
        px = int(h * 0.165)
        f = _font("Cinzel", px, "Bold")
        while d.textlength(line, font=f) > w * 0.52 and px > 30:
            px -= 3
            f = _font("Cinzel", px, "Bold")
        tw = d.textlength(line, font=f)
        _glow_text(im, (cx - tw / 2, y), line, f, CREAM, glow=(8, 10, 30), radius=12)
        y += int(px * 1.05)

    spx = int(h * 0.062)
    sf = _font("CormorantGaramond", spx, "SemiBold")
    sp = int(h * 0.012)
    sw = _spaced_width(d, subtitle, sf, sp)
    while sw > w * 0.42 and spx > 20:            # 両脇の線ごと画面内に収める
        spx -= 2
        sf = _font("CormorantGaramond", spx, "SemiBold")
        sw = _spaced_width(d, subtitle, sf, sp)
    sy = y + int(h * 0.025)
    _glow_text(im, (cx - sw / 2, sy), subtitle, sf, CREAM, glow=(8, 10, 30), radius=8,
               spacing=sp)
    ly = sy + int(h * 0.040)
    gap, ln = int(h * 0.03), int(h * 0.075)
    d.line([(cx - sw / 2 - gap - ln, ly), (cx - sw / 2 - gap, ly)], fill=CREAM, width=2)
    d.line([(cx + sw / 2 + gap, ly), (cx + sw / 2 + gap + ln, ly)], fill=CREAM, width=2)

    # 時間バッジ (枠線のみ・半透明の地)
    bf = _font("CormorantGaramond", int(h * 0.060), "Bold")
    bw = d.textlength(badge, font=bf)
    bx0, by0 = int(w * 0.045), int(h * 0.80)
    bx1, by1 = int(bx0 + bw + h * 0.09), int(by0 + h * 0.095)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([bx0, by0, bx1, by1], radius=int(h * 0.048),
                         fill=(18, 22, 46, 150), outline=CREAM + (255,), width=3)
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    tb = d.textbbox((0, 0), badge, font=bf)
    d.text(((bx0 + bx1) / 2 - (tb[2] - tb[0]) / 2 - tb[0], (by0 + by1) / 2 - (tb[3] - tb[1]) / 2 - tb[1]),
           badge, font=bf, fill=CREAM)

    # チャンネル名
    nf = _font("CormorantGaramond", int(h * 0.040), "SemiBold")
    _leaf(d, bx0 + 4, by1 + int(h * 0.055), int(h * 0.04), (176, 196, 140))
    _draw_spaced(d, (bx0 + int(h * 0.065), by1 + int(h * 0.022)), brand, nf, CREAM,
                 int(h * 0.006))
    return im
