#!/usr/bin/env python3
"""
Shorts 生成 (CLI)

なぜ Shorts を作るのか
----------------------
BGMチャンネルの収益化を止めるのは「再生時間」ではなく「登録者1,000人」。
2時間24分の動画なら、たった1,667人が完走するだけで4,000時間に届く。
一方でBGMは「つけっぱなしにして去る」使われ方なので登録されにくい。

Shorts の再生時間は4,000時間にカウントされないが、
**登録者を集める手段としては現状これしかない**。
だからここは自動化する価値が最も高い。

使い方
------
    # 全トラックから各2本ずつ (合計20本) 作る
    python3 make_shorts.py

    # 特定のトラックだけ / 本数を変える
    python3 make_shorts.py --tracks 04_cozy_coffee_jazz --per-track 3

出力
----
    out/shorts/<slug>_s1.mp4      1080x1920 / 40秒
    out/shorts/<slug>_s1.txt      貼り付け用のタイトルと説明文
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bgm_studio import copywriting as COPY
from bgm_studio import tracks as TR
from bgm_studio import video as VID

OUT = Path("out")
W, H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
# Mac にはこのパスが無いので候補を並べておく
FONT_CANDIDATES = [
    FONT_BOLD,
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_overlay(hook: str, footer: str) -> Image.Image:
    """
    文字と、上下のグラデーションを載せた透過PNGを作る。

    Shorts は最初の2秒で判断されるので、文字は上寄せにして
    サムネ的に一瞬で読める位置に置く。下部はUIに隠れるため避ける。
    """
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 上部を暗くして文字を読ませる
    for y in range(0, int(H * 0.42)):
        a = int(150 * (1.0 - y / (H * 0.42)) ** 1.3)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))

    lines = hook.split("\n")
    f = _font(96)
    # 長い行があれば縮める
    while max(d.textbbox((0, 0), ln, font=f)[2] for ln in lines) > W - 120 \
            and f.size > 44:
        f = _font(f.size - 4)

    y = int(H * 0.12)
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        for ox, oy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
            d.text((x + ox, y + oy), ln, font=f, fill=(0, 0, 0, 220))
        d.text((x, y), ln, font=f, fill=(255, 255, 255, 255))
        y += int(f.size * 1.25)

    # フッタ (長尺への誘導)。UIに隠れない高さに置く
    ff = _font(46)
    bb = d.textbbox((0, 0), footer, font=ff)
    fx = (W - (bb[2] - bb[0])) // 2 - bb[0]
    fy = int(H * 0.80)
    for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        d.text((fx + ox, fy + oy), footer, font=ff, fill=(0, 0, 0, 210))
    d.text((fx, fy), footer, font=ff, fill=(255, 214, 150, 255))
    return im


def build_short(slug: str, hook: str, start_s: float, dur_s: float,
                index: int, total_hhmmss: str) -> Path:
    """
    1本の Shorts を書き出す。

    16:9 のループ映像をそのまま縦に切ると構図が崩れるので、
    横幅いっぱいに収めたうえで、上下を「同じ映像を拡大してぼかしたもの」で
    埋める。縦動画でよく使われる処理で、破綻しない。
    """
    visual = OUT / "visual" / f"{slug}.mp4"
    audio = OUT / "audio" / f"{slug}.wav"
    if not visual.exists() or not audio.exists():
        raise FileNotFoundError(
            f"{visual} と {audio} が必要です。先に render_bgm.py を実行してください。")

    short_dir = OUT / "shorts"
    short_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = short_dir / f"{slug}_s{index}.mp4"

    ov_path = short_dir / f".overlay_{slug}_{index}.png"
    make_overlay(hook, f"full {total_hhmmss} version on the channel").save(ov_path)

    loops = int(dur_s // 20) + 2       # 20秒ループを必要なだけ繰り返す
    filt = (
        f"[0:v]scale={W}:-2,setsar=1[fg];"
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},gblur=sigma=42,eq=brightness=-0.18:saturation=0.7[bg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
        f"[base][2:v]overlay=0:0,format=yuv420p[v]"
    )
    cmd = [
        VID.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-stream_loop", str(loops), "-i", str(visual),
        "-ss", str(start_s), "-t", str(dur_s), "-i", str(audio),
        "-i", str(ov_path),
        "-filter_complex", filt,
        "-map", "[v]", "-map", "1:a",
        "-t", str(dur_s),
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    ov_path.unlink(missing_ok=True)
    return out_mp4


def main() -> int:
    ap = argparse.ArgumentParser(description="長尺から Shorts を切り出す")
    ap.add_argument("--tracks", nargs="*", default=None)
    ap.add_argument("--per-track", type=int, default=2,
                    help="1トラックあたりの本数 (既定2, 最大3)")
    ap.add_argument("--duration", type=float, default=40.0,
                    help="1本の長さ [秒] (Shorts は60秒未満)")
    args = ap.parse_args()

    specs = TR.TRACKS
    if args.tracks:
        missing = [s for s in args.tracks if s not in TR.BY_SLUG]
        if missing:
            print(f"未知のスラッグ: {missing}", file=sys.stderr)
            return 2
        specs = [TR.BY_SLUG[s] for s in args.tracks]

    print(f"=== Shorts 生成 ===")
    print(f"{len(specs)} トラック × {args.per_track} 本 = "
          f"{len(specs) * args.per_track} 本 / 各 {args.duration:.0f}秒\n")

    t0 = time.time()
    made = 0
    for spec in specs:
        hooks = COPY.SHORT_HOOKS.get(spec.slug, ["relaxing music"])
        n = min(args.per_track, len(hooks))
        wav = OUT / "audio" / f"{spec.slug}.wav"
        if not wav.exists():
            print(f"  スキップ {spec.slug}（音源なし）")
            continue

        # ループ全体に散らして切り出す（同じ箇所を使わない）
        loop_s = TR.LOOP_SECONDS
        for i in range(n):
            start = loop_s * (0.18 + 0.30 * i)
            try:
                p = build_short(spec.slug, hooks[i], start, args.duration,
                                i + 1, "2:24:00")
            except Exception as e:
                print(f"  失敗 {spec.slug}_s{i+1}: {type(e).__name__}: {e}")
                continue

            title = hooks[i].replace("\n", " ") + " 🎧"
            desc = COPY.SHORT_DESCRIPTION.format(
                hook=hooks[i].replace("\n", " "),
                duration="2 hour",
                tag1=(spec.seo.get("keywords", ["music"])[0]).replace(" ", ""),
                tag2=(spec.seo.get("keywords", ["music", "relax"])[-1]).replace(" ", ""),
            )
            p.with_suffix(".txt").write_text(
                f"[タイトル]\n{title}\n\n[説明]\n{desc}", encoding="utf-8")
            print(f"  {p.name}  {p.stat().st_size / 1e6:.1f}MB  「{hooks[i].splitlines()[0]}…」")
            made += 1

    print(f"\n{made} 本を out/shorts/ に書き出しました（{time.time() - t0:.0f}秒）")
    print("1日1本のペースで投稿してください。長尺は週2〜4本のままです。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
