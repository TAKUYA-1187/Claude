#!/usr/bin/env python3
"""
子守唄シリーズの Shorts (子ども向け) を作る。

BGM の Shorts (make_shorts.py) は横長の映像を縮めて上下をぼかしで埋めていたが、
子守唄はキャラクター (Luna) が主役なので、Luna を中心に縦に切り出して画面いっぱいに見せる。
文字は子ども向けの高再生動画に倣って、太い丸文字 + 縁取りを上に置く。

    python3 make_kids_shorts.py                 # n01〜n10 を 1 本ずつ
    python3 make_kids_shorts.py --tracks n01_twinkle_lullaby

出力: out/shorts_kids/<slug>.mp4 (1080x1920, 40 秒) と <slug>.txt (貼り付け用)
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from bgm_studio import video as VID
from bgm_studio.kids_visuals import _font, _outlined
from bgm_studio.tracks import BY_SLUG

OUT = Path(__file__).resolve().parent / "out"
W, H = 1080, 1920
DUR = 40.0

# (画面上の 2 行, Shorts のタイトル)
SHORTS = {
    "n01_twinkle_lullaby": (["Twinkle Twinkle", "Little Star"], "Twinkle Twinkle Little Star 🌙 Lullaby for Babies"),
    "n02_mary_lamb_lullaby": (["Mary Had a", "Little Lamb"], "Mary Had a Little Lamb 🐑 Soft Lullaby for Babies"),
    "n03_row_your_boat_lullaby": (["Row Row Row", "Your Boat"], "Row Row Row Your Boat 🚣 Calm Lullaby for Babies"),
    "n04_frere_jacques_lullaby": (["Frère", "Jacques"], "Frère Jacques 🔔 Bedtime Lullaby for Babies"),
    "n05_london_bridge_lullaby": (["London", "Bridge"], "London Bridge 🌉 Music Box Lullaby for Babies"),
    "n06_old_macdonald_lullaby": (["Old", "MacDonald"], "Old MacDonald 🐮 Gentle Lullaby for Naptime"),
    "n07_au_clair_lullaby": (["Au Clair", "de la Lune"], "Au Clair de la Lune 🌕 French Lullaby for Babies"),
    "n08_silent_night_lullaby": (["Silent", "Night"], "Silent Night 🎄 Christmas Lullaby for Babies"),
    "n09_ode_to_joy_lullaby": (["Ode to", "Joy"], "Ode to Joy ✨ Music Box Lullaby for Babies"),
    "n10_jingle_bells_lullaby": (["Jingle", "Bells"], "Jingle Bells ❄️ Slow Lullaby for Babies"),
}

DESCRIPTION = """{title}

A short piece of our 1-hour lullaby, played on a soft piano and a music box.
No background noise — just gentle music and Luna, the sleepy moon.

The full 1-hour version is on our channel.

#lullaby #babysleep #nurseryrhymes
"""


def overlay(lines: list[str]) -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = int(H * 0.035)
    for ln in lines:
        px = 118
        f = _font(px, "Bold")
        while d.textbbox((0, 0), ln, font=f)[2] > W - 110 and px > 56:
            px -= 4
            f = _font(px, "Bold")
        bb = d.textbbox((0, 0), ln, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        _outlined(d, (x, y), ln, f, (255, 224, 74), (38, 34, 102), int(px * 0.10))
        y += int(px * 1.15)
    # バッジ (下部の UI に隠れない高さ)
    bf = _font(62, "SemiBold")
    badge = "Lullaby for Babies"
    bb = d.textbbox((0, 0), badge, font=bf)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    bx, by = (W - bw) // 2 - 36, int(H * 0.70)
    d.rounded_rectangle([bx, by, bx + bw + 72, by + bh + 48], radius=44,
                        fill=(255, 128, 170), outline=(255, 255, 255), width=8)
    d.text((bx + 36, by + 24 - bb[1]), badge, font=bf, fill=(255, 255, 255))
    return im


def build(slug: str) -> Path:
    visual = OUT / "visual" / f"{slug}.mp4"
    wav = OUT / "audio" / f"{slug}.wav"
    if not visual.exists() or not wav.exists():
        raise FileNotFoundError(f"{visual} / {wav} が必要です。先に render_bgm.py を実行してください")
    d = OUT / "shorts_kids"
    d.mkdir(parents=True, exist_ok=True)
    ov = d / f".ov_{slug}.png"
    overlay(SHORTS[slug][0]).save(ov)
    out = d / f"{slug}.mp4"
    # Luna は横 70% の位置にいる。幅 720 で切り出して 1.5 倍 (1080x1620) にし、
    # 上に 300px の帯を足して曲名を置く (画面いっぱいに切り出すと曲名がナイトキャップに
    # 重なった)。帯は単色だと境目が線になって見えたので、映像の上端を上下反転して
    # ぼかしたもので埋め、境目の色をつなげる
    cx = int(1920 * 0.70)
    x0 = min(max(cx - 360, 0), 1920 - 720)
    filt = (f"[0:v]crop=720:1080:{x0}:0,scale=1080:1620:flags=lanczos,setsar=1,split[a][b];"
            f"[b]crop=1080:300:0:0,vflip,gblur=sigma=24[top];"
            f"[top][a]vstack[bg];"
            f"[bg][2:v]overlay=0:0,format=yuv420p[v];"
            f"[1:a]afade=t=in:d=0.6,afade=t=out:st={DUR - 2.5}:d=2.5[a]")
    cmd = [VID.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
           "-stream_loop", "2", "-i", str(visual),
           "-ss", "0.5", "-t", str(DUR), "-i", str(wav),
           "-i", str(ov),
           "-filter_complex", filt, "-map", "[v]", "-map", "[a]", "-t", str(DUR),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    ov.unlink(missing_ok=True)
    title = SHORTS[slug][1]
    out.with_suffix(".txt").write_text(
        f"[タイトル]\n{title} #shorts\n\n[説明]\n{DESCRIPTION.format(title=title)}\n"
        "[設定]\n子ども向け: はい / AI の使用: はい / 関連動画: 選べる場合だけ、同じ曲の 1 時間版\n",
        encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracks", nargs="*", default=list(SHORTS))
    for slug in ap.parse_args().tracks:
        assert slug in BY_SLUG, slug
        p = build(slug)
        print(f"{p}  {p.stat().st_size / 1e6:.1f}MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
