#!/usr/bin/env python3
"""
クリスマス曲・冬のメロディの Shorts (縦 1080x1920・45 秒) を作る。

まとめ版 (x01〜x04, x08, w01, w02) の音源から、曲ごとの頭の 45 秒を切り出し、同じ動画の
ループ映像のうちツリーのある右側を縦に切り出して使う。文字はサムネと同じ
セリフ体 (Cinzel / Cormorant Garamond)。Shorts は「長尺は 1 日 1 本」の数に入れない。

    python3 make_xmas_shorts.py              # 全部
    python3 make_xmas_shorts.py --only 1 5   # 番号で選ぶ

出力: out/shorts_xmas/NN_<名前>.mp4 と同名の .txt (タイトル・説明・設定)
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from bgm_studio import video as VID
from bgm_studio.illustrated import CREAM, _font, _glow_text, _spaced_width
from bgm_studio.tracks import BY_SLUG, MEDLEY_SONGS

OUT = Path(__file__).resolve().parent / "out"
W, H = 1080, 1920
DUR = 45.0
SONG_S = 720.0              # まとめ版は 1 曲 12 分

# (元のまとめ版, 曲名 (MEDLEY_SONGS の名前), 画面の 2 行, 副題, Shorts のタイトル)
SHORTS = [
    ("x03_christmas_bells", "c09_jingle_bells_full", ["JINGLE", "BELLS"], "PIANO & SLEIGH BELLS",
     "Jingle Bells 🔔 Piano & Sleigh Bells | Cozy Christmas Music"),
    ("x03_christmas_bells", "c02_deck_the_halls", ["DECK THE", "HALLS"], "PIANO & SLEIGH BELLS",
     "Deck the Halls 🔔 Piano & Sleigh Bells | Christmas Music"),
    ("x03_christmas_bells", "c10_ding_dong_merrily", ["DING DONG", "MERRILY"], "PIANO & SLEIGH BELLS",
     "Ding Dong Merrily on High 🔔 Piano & Bells | Christmas Carol"),
    ("x03_christmas_bells", "c01_we_wish_you", ["MERRY", "CHRISTMAS"], "WE WISH YOU · PIANO & BELLS",
     "We Wish You a Merry Christmas 🔔 Piano & Sleigh Bells"),
    ("x04_christmas_calm", "n08_silent_night_lullaby", ["SILENT", "NIGHT"], "CALM CHRISTMAS PIANO",
     "Silent Night 🌙 Calm Christmas Piano"),
    ("x04_christmas_calm", "c15_o_holy_night", ["O HOLY", "NIGHT"], "CALM CHRISTMAS PIANO",
     "O Holy Night 🌟 Calm Christmas Piano"),
    ("x04_christmas_calm", "c18_what_child", ["WHAT CHILD", "IS THIS"], "CALM CHRISTMAS PIANO",
     "What Child Is This 🌙 Calm Christmas Piano (Greensleeves)"),
    ("x04_christmas_calm", "c16_o_little_town", ["O LITTLE", "TOWN"], "OF BETHLEHEM · PIANO",
     "O Little Town of Bethlehem 🌙 Calm Christmas Piano"),
    ("x02_christmas_musicbox", "n08_silent_night_lullaby", ["SILENT", "NIGHT"], "MUSIC BOX",
     "Silent Night 🎁 Christmas Music Box"),
    ("x02_christmas_musicbox", "n10_jingle_bells_lullaby", ["JINGLE", "BELLS"], "MUSIC BOX",
     "Jingle Bells 🎁 Christmas Music Box"),
    ("x08_christmas_carols_2_musicbox", "c18_what_child", ["WHAT CHILD", "IS THIS"], "MUSIC BOX",
     "What Child Is This 🎁 Christmas Music Box"),
    ("x01_christmas_piano", "c03_o_christmas_tree", ["O CHRISTMAS", "TREE"], "SOFT CHRISTMAS PIANO",
     "O Christmas Tree 🎄 Soft Christmas Piano"),
    # 2026-10-31 冬のメロディ
    ("w01_winter_piano", "d01_vivaldi_winter", ["VIVALDI", "WINTER"], "LARGO · SOFT PIANO",
     "Vivaldi – Winter (Largo) ❄️ Soft Piano"),
    ("w01_winter_piano", "c18_what_child", ["GREENSLEEVES"], "WINTER PIANO",
     "Greensleeves ❄️ Soft Winter Piano"),
    ("w01_winter_piano", "d02_lindenbaum", ["THE LINDEN", "TREE"], "SCHUBERT · WINTER PIANO",
     "Schubert – Der Lindenbaum (The Linden Tree) ❄️ Soft Piano"),
    ("w01_winter_piano", "d03_auld_lang_syne", ["AULD LANG", "SYNE"], "NEW YEAR'S EVE PIANO",
     "Auld Lang Syne ✨ Soft Piano for New Year's Eve"),
    ("w02_winter_musicbox", "d01_vivaldi_winter", ["VIVALDI", "WINTER"], "MUSIC BOX",
     "Vivaldi – Winter (Largo) ❄️ Music Box"),
    ("w02_winter_musicbox", "d06_huron_carol", ["HURON", "CAROL"], "MUSIC BOX",
     "Huron Carol ('Twas in the Moon of Wintertime) ❄️ Music Box"),
]

DESCRIPTION = """{title}

A short piece from our {length} {theme} video: {full}.
Real recorded piano and bells, tuned to A = 432 Hz, with no background noise.

The full version is on our channel.

{tags}
"""


def overlay(lines: list[str], sub: str) -> Image.Image:
    """上の帯に曲名 2 行と副題、下寄りにチャンネル名"""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    y = 120
    for ln in lines:
        px = 150
        f = _font("Cinzel", px, "Bold")
        while d.textlength(ln, font=f) > W - 140 and px > 60:
            px -= 4
            f = _font("Cinzel", px, "Bold")
        tw = d.textlength(ln, font=f)
        _glow_text(im, ((W - tw) / 2, y), ln, f, CREAM, glow=(8, 10, 30), radius=14)
        y += int(px * 1.08)
    sf = _font("CormorantGaramond", 54, "SemiBold")
    sw = _spaced_width(d, sub, sf, 8)
    _glow_text(im, ((W - sw) / 2, y + 30), sub, sf, CREAM, glow=(8, 10, 30), radius=10,
               spacing=8)
    nf = _font("CormorantGaramond", 46, "SemiBold")
    name = "QUIET HOURS MUSIC"
    nw = _spaced_width(d, name, nf, 8)
    _glow_text(im, ((W - nw) / 2, int(H * 0.70)), name, nf, CREAM, glow=(8, 10, 30),
               radius=10, spacing=8)
    # 文字の部分だけを不透明にする (黒地はくり抜く)
    a = np.asarray(im, dtype=np.float32).max(axis=2)
    mask = Image.fromarray(np.clip(a * 3.0, 0, 255).astype(np.uint8))
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def build(i: int) -> Path:
    src, song, lines, sub, title = SHORTS[i]
    wav = OUT / "audio" / f"{src}.wav"
    visual = OUT / "visual" / f"{src}.mp4"
    if not wav.exists() or not visual.exists():
        raise FileNotFoundError(f"{src}: 先に render_bgm.py で書き出してください")
    offset = MEDLEY_SONGS[src].index(song) * SONG_S + 0.5
    d = OUT / "shorts_xmas"
    d.mkdir(parents=True, exist_ok=True)
    kind = {"x01_christmas_piano": "piano", "x02_christmas_musicbox": "musicbox",
            "x03_christmas_bells": "bells", "x04_christmas_calm": "calm_piano",
            "x08_christmas_carols_2_musicbox": "musicbox",
            "w01_winter_piano": "winter_piano", "w02_winter_musicbox": "winter_musicbox"}[src]
    words = " ".join(lines).lower().replace("-", " ").split()
    name = f"{i + 1:02d}_{'_'.join(words)}_{kind}"
    ov = d / f".ov_{name}.png"
    overlay(lines, sub).save(ov)
    out = d / f"{name}.mp4"
    # ツリーは横 78% の位置。幅 720 で切り出して 1.5 倍 (1080x1620) にし、上に 300px の
    # 帯 (映像の上端を反転してぼかしたもの) を足して曲名を置く (子守唄の Shorts と同じ作り)
    x0 = min(max(int(1920 * 0.78) - 360, 0), 1920 - 720)
    filt = (f"[0:v]crop=720:1080:{x0}:0,scale=1080:1620:flags=lanczos,setsar=1,split[a][b];"
            f"[b]crop=1080:300:0:0,vflip,gblur=sigma=24[top];"
            f"[top][a]vstack[bg];"
            f"[bg][2:v]overlay=0:0,format=yuv420p[v];"
            f"[1:a]afade=t=in:d=0.6,afade=t=out:st={DUR - 3.0}:d=3.0[a]")
    cmd = [VID.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
           "-stream_loop", "2", "-i", str(visual),
           "-ss", f"{offset:.2f}", "-t", str(DUR), "-i", str(wav),
           "-i", str(ov),
           "-filter_complex", filt, "-map", "[v]", "-map", "[a]", "-t", str(DUR),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    ov.unlink(missing_ok=True)
    spec = BY_SLUG[src]
    winter = src.startswith("w")
    theme = "winter" if winter else "Christmas"
    tags = ("#wintermusic #winter #pianomusic #shorts" if winter
            else "#christmasmusic #christmas #christmascarols #shorts")
    length = "2-hour"
    out.with_suffix(".txt").write_text(
        f"[タイトル]\n{title} #shorts\n\n[説明]\n"
        f"{DESCRIPTION.format(title=title, length=length, full=spec.seo['title'], theme=theme, tags=tags)}\n"
        "[設定]\n子ども向け: いいえ / AI の使用: はい / 関連動画: "
        f"「{spec.seo['title']}」\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int)
    a = ap.parse_args()
    for i in ([n - 1 for n in a.only] if a.only else range(len(SHORTS))):
        p = build(i)
        print(f"{p.name}  {p.stat().st_size / 1e6:.1f}MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
