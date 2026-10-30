#!/usr/bin/env python3
"""
BGM 動画ビルダー (CLI)

使い方
------
    # 全 10 本を 2 時間 24 分の動画として書き出す
    python3 render_bgm.py

    # 音源だけ / 特定のトラックだけ
    python3 render_bgm.py --no-video
    python3 render_bgm.py --tracks 01_lofi_rainy_study 04_cozy_coffee_jazz

    # 短くして動作確認
    python3 render_bgm.py --seconds 60 --repeats 2

出力
----
    out/audio/<slug>.wav          ループ 1 周ぶんのマスター (24 分, 24bit)
    out/preview/<slug>.mp3        試聴用の抜粋 (90 秒)
    out/visual/<slug>.mp4         ループ映像 (20 秒)
    out/video/<slug>.mp4          アップロード用の本編 (2 時間 24 分)
    out/thumbnail/<slug>.png      サムネイル (1280x720)
    out/metadata/<slug>.json      タイトル・説明文・タグ
    out/report.json               検証結果 (長さ / LUFS / 継ぎ目)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from bgm_studio import copywriting as COPY
from bgm_studio import tracks as TR
from bgm_studio import video as VID
from bgm_studio import visuals as VIS
from bgm_studio.dsp import SR

OUT = Path("out")


def log(msg: str) -> None:
    print(msg, flush=True)


def bar(i: int, n: int, label: str) -> None:
    pct = 100 * i // max(n, 1)
    filled = pct // 5
    print(f"\r    [{'█' * filled}{'░' * (20 - filled)}] {pct:3d}%  {label}",
          end="", flush=True)


# ──────────────────────────────────────────────────────────────
# メタデータ (アップロード時にそのまま貼れる形)
# ──────────────────────────────────────────────────────────────

def build_metadata(spec: TR.TrackSpec, info: dict, total_seconds: float) -> dict:
    seo = spec.seo
    dur = VID.hhmmss(total_seconds)
    hours = total_seconds / 3600.0
    # 1 時間未満を "0:33:00" と書くと説明文の冒頭が不自然になる
    if total_seconds < 3600:
        dur = f"{int(round(total_seconds / 60))} minutes"
    elif abs(total_seconds % 3600) < 1.0:
        h_ = int(round(total_seconds / 3600))
        dur = f"{h_} hour" if h_ == 1 else f"{h_} hours"
    # 童謡・子守唄は乳幼児向け。YouTube (COPPA) 上「子ども向け」に設定する義務がある
    is_kids = spec.slug[:1] == "n" and spec.slug[1:3].isdigit()

    # 10本すべてを同じテンプレートで書くと、外形が「テンプレート量産」に
    # なってしまう。1本ずつ書き下ろした説明文があればそちらを使う。
    written = COPY.get(spec.slug, dur)
    if written:
        return {
            "slug": spec.slug,
            "title": seo.get("title", spec.title_en),
            "description": written,
            "tags": seo.get("keywords", []),
            "category": "Music",
            "language": "en",
            "visibility": "public",
            "made_for_kids": is_kids,
            "specs": _specs(spec, info, total_seconds, dur),
        }

    description = f"""{seo.get('title', spec.title_en)}

{dur} of original {spec.title_en.lower()} — composed, mixed and mastered for this video.
Press play, leave it running, and let the room fill up.

▶ WHAT THIS IS
{_use_case_line(spec.use_case)}
· Original composition — not a compilation, not stock music
· Seamless loop: no gaps, no fades, no jarring transitions
· Mastered to -14 LUFS so it sits at a comfortable level all night

▶ ABOUT THIS TRACK
· Genre: {spec.title_en}
· Tempo: {info.get('bpm', spec.bpm):.0f} BPM
· Key: {spec.key}
· Tuning: A = {spec.a4:.0f} Hz
· Length: {dur} ({hours:.1f} hours)

▶ HOW TO USE
· Studying, deep work, reading, writing
· Falling asleep / staying asleep
· Background for cafés, shops and small businesses
· Take a break, breathe, and come back to it

Headphones or a small speaker both work. Volume low is best.

If this helped you focus or drift off, a like really does help the channel —
and subscribe if you'd like more of these.

#{_hashtags(seo.get('keywords', []))}

---
All music and visuals in this video were created from scratch for this channel.
"""

    return {
        "slug": spec.slug,
        "title": seo.get("title", spec.title_en),
        "description": description,
        "tags": seo.get("keywords", []),
        "category": "Music",
        "language": "en",
        "visibility": "public",
        "made_for_kids": is_kids,
        "specs": _specs(spec, info, total_seconds, dur),
    }


def _specs(spec: TR.TrackSpec, info: dict, total_seconds: float, dur: str) -> dict:
    return {
        "genre_ja": spec.genre_ja,
        "use_case": spec.use_case,
        "bpm": round(info.get("bpm", spec.bpm), 2),
        "key": spec.key,
        "a4_hz": spec.a4,
        "loop_seconds": info.get("seconds"),
        "total_seconds": total_seconds,
        "total_hhmmss": dur,
        "lufs": round(info.get("lufs_after", 0.0), 2),
        "true_peak_db": round(info.get("true_peak_db", 0.0), 2),
        "loop_seam_db": round(info.get("seam_db", 0.0), 2),
        "visual": spec.visual,
    }


def _use_case_line(use_case: str) -> str:
    return {
        "sleep": "· Made for sleep — low, warm, and slow, with nothing that will wake you",
        "study": "· Made for studying — steady, unobtrusive, no sudden changes",
        "work": "· Made for work — warm and human, keeps the room from feeling empty",
        "relax": "· Made for winding down — soft dynamics, plenty of space",
    }.get(use_case, "· Background music for whatever you are doing")


def _hashtags(keywords: list[str]) -> str:
    tags = [k.replace(" ", "").replace("-", "") for k in keywords[:3]]
    return " #".join(tags) if tags else "relaxingmusic"


# ──────────────────────────────────────────────────────────────
# 1 トラックの処理
# ──────────────────────────────────────────────────────────────

def process(spec: TR.TrackSpec, args) -> dict:
    t_start = time.time()
    log(f"\n▸ {spec.slug}  ({spec.genre_ja})")

    # 映像だけ作り直す場合は、時間のかかる音源合成を丸ごと飛ばす。
    # 音は変えずに絵だけ差し替えたいときのための経路。
    if args.visual_only:
        return process_visual_only(spec, args, t_start)

    # ── 音源 ───────────────────────────────────────────────
    log("  音源を合成中...")
    t = time.time()
    audio, info = TR.render(spec, seconds=args.seconds)
    log(f"    BPM {info['bpm']:.2f} / {info['bars']} 小節 / "
        f"{info['lufs_after']:.2f} LUFS / TP {info['true_peak_db']:.2f} dB / "
        f"継ぎ目 {info['seam_db']:+.1f} dB   ({time.time() - t:.0f}s)")

    wav = VID.write_wav(OUT / "audio" / f"{spec.slug}.wav", audio, SR, bits=24)

    # 試聴用の抜粋 (ループ中盤から)
    prev_dir = OUT / "preview"
    prev_dir.mkdir(parents=True, exist_ok=True)
    start = int(args.seconds * 0.35)
    subprocess.run([VID.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", str(start), "-t", "90", "-i", str(wav),
                    "-c:a", "libmp3lame", "-b:a", "128k",
                    str(prev_dir / f"{spec.slug}.mp3")], check=False)

    total_seconds = args.seconds * args.repeats
    result = {
        "slug": spec.slug,
        "title": spec.seo.get("title", spec.title_en),
        "bpm": info["bpm"], "bars": info["bars"],
        "lufs": info["lufs_after"], "true_peak_db": info["true_peak_db"],
        "loop_seam_db": info["seam_db"],
        "loop_seconds": args.seconds,
        "total_seconds": total_seconds,
        "total_hhmmss": VID.hhmmss(total_seconds),
    }
    del audio

    # ── サムネイル ─────────────────────────────────────────
    thumb_dir = OUT / "thumbnail"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    _make_thumbnail(spec, total_seconds).save(thumb_dir / f"{spec.slug}.png")

    # ── メタデータ ─────────────────────────────────────────
    meta = build_metadata(spec, info, total_seconds)
    meta_dir = OUT / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / f"{spec.slug}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.no_video:
        result["elapsed_s"] = round(time.time() - t_start, 1)
        return result

    # ── 映像 ───────────────────────────────────────────────
    log("  映像ループを描画中...")
    t = time.time()
    vis = VID.encode_visual_loop(
        TR.visual_for(spec), OUT / "visual" / f"{spec.slug}.mp4", seed=spec.seed,
        progress=lambda i, n: bar(i, n, spec.slug))
    print()
    log(f"    {VIS.LOOP_SECONDS}s @ {VIS.FPS}fps  "
        f"{vis.stat().st_size / 1e6:.1f} MB   ({time.time() - t:.0f}s)")

    # ── 音声を必要な長さまで伸ばして AAC 化 ────────────────
    log(f"  音声を {args.repeats} 回つないで AAC 化中...")
    t = time.time()
    m4a = VID.loop_audio_to_aac(wav, OUT / "tmp" / f"{spec.slug}.m4a",
                                repeats=args.repeats, bitrate=args.audio_bitrate)
    log(f"    {m4a.stat().st_size / 1e6:.0f} MB   ({time.time() - t:.0f}s)")

    # ── 多重化 ─────────────────────────────────────────────
    log("  本編を書き出し中...")
    t = time.time()
    out_mp4 = VID.mux_looped(vis, m4a, OUT / "video" / f"{spec.slug}.mp4",
                             total_seconds=total_seconds)
    pr = VID.probe(out_mp4)
    log(f"    {out_mp4}  {VID.hhmmss(pr.get('duration_s', 0))}  "
        f"{pr.get('size_mb', 0):.0f} MB   ({time.time() - t:.0f}s)")

    result["video"] = str(out_mp4)
    result["probe"] = pr
    if not args.keep_temp:
        m4a.unlink(missing_ok=True)

    result["elapsed_s"] = round(time.time() - t_start, 1)
    return result


def process_visual_only(spec: TR.TrackSpec, args, t_start: float) -> dict:
    """既存の WAV を使い、映像・サムネ・本編だけ作り直す"""
    wav = OUT / "audio" / f"{spec.slug}.wav"
    if not wav.exists():
        raise FileNotFoundError(f"{wav} がありません。先に通常のレンダリングが必要です。")

    total_seconds = args.seconds * args.repeats
    log("  映像ループを描画中...")
    t = time.time()
    vis = VID.encode_visual_loop(
        TR.visual_for(spec), OUT / "visual" / f"{spec.slug}.mp4", seed=spec.seed,
        progress=lambda i, n: bar(i, n, spec.slug))
    print()
    log(f"    {spec.visual}  {vis.stat().st_size / 1e6:.1f} MB  ({time.time() - t:.0f}s)")

    thumb_dir = OUT / "thumbnail"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    _make_thumbnail(spec, total_seconds).save(thumb_dir / f"{spec.slug}.png")

    log(f"  音声を {args.repeats} 回つないで AAC 化中...")
    m4a = VID.loop_audio_to_aac(wav, OUT / "tmp" / f"{spec.slug}.m4a",
                                repeats=args.repeats, bitrate=args.audio_bitrate)
    log("  本編を書き出し中...")
    out_mp4 = VID.mux_looped(vis, m4a, OUT / "video" / f"{spec.slug}.mp4",
                             total_seconds=total_seconds)
    pr = VID.probe(out_mp4)
    log(f"    {out_mp4}  {VID.hhmmss(pr.get('duration_s', 0))}  "
        f"{pr.get('size_mb', 0):.0f} MB")
    if not args.keep_temp:
        m4a.unlink(missing_ok=True)
    return {"slug": spec.slug, "video": str(out_mp4), "probe": pr,
            "total_seconds": total_seconds,
            "total_hhmmss": VID.hhmmss(total_seconds),
            "lufs": -14.0, "loop_seam_db": 0.0,
            "elapsed_s": round(time.time() - t_start, 1)}


# 子守唄のサムネ: キャラクター + 太い丸文字 2 行 + 用途のバッジ
# (子ども向けの高再生動画に倣う。kids_visuals.kids_thumbnail 参照)
KIDS_THUMB = {
    "n11_lullaby_medley": ["10 BABY", "LULLABIES"],
    "n01_twinkle_lullaby": ["TWINKLE", "TWINKLE"],
    "n02_mary_lamb_lullaby": ["MARY HAD A", "LITTLE LAMB"],
    "n03_row_your_boat_lullaby": ["ROW ROW", "YOUR BOAT"],
    "n04_frere_jacques_lullaby": ["FRÈRE", "JACQUES"],
    "n05_london_bridge_lullaby": ["LONDON", "BRIDGE"],
    "n06_old_macdonald_lullaby": ["OLD", "MACDONALD"],
    "n07_au_clair_lullaby": ["AU CLAIR", "DE LA LUNE"],
    "n08_silent_night_lullaby": ["SILENT", "NIGHT"],
    "n09_ode_to_joy_lullaby": ["ODE TO", "JOY"],
    "n10_jingle_bells_lullaby": ["JINGLE", "BELLS"],
}


# 大きな白い文字 2 行 + 長さのバッジ + 1 行の約束。2026-10-28 から BGM もこの型に統一
# (旧来の「暗い映像に細い文字」はスマホの一覧で読めず、クリック率 0% が続いた)
SLEEP_BADGE = (246, 214, 140)
JAZZ_BADGE = (240, 168, 96)
SEASON_BADGE = (232, 120, 120)
BOLD_THUMB = {
    "g01_gentle_piano_sleep": (["SLEEP", "PIANO"], "No rain · No noise · Just piano", SLEEP_BADGE),
    "g02_deep_sleep_piano": (["DEEP SLEEP", "PIANO"], "No rain · No noise · Just piano", SLEEP_BADGE),
    "g03_emotional_sleep_piano": (["BEAUTIFUL", "SLEEP PIANO"], "No rain · No noise · Just piano", SLEEP_BADGE),
    "03_piano_and_rain": (["PIANO", "& RAIN"], "Soft piano · Gentle rain", SLEEP_BADGE),
    "04_cozy_coffee_jazz": (["COFFEE", "JAZZ"], "Warm piano for work & study", JAZZ_BADGE),
    "05_bossa_nova_cafe": (["BOSSA NOVA", "CAFE"], "Smooth guitar · Good mood", JAZZ_BADGE),
    "07_fireplace_winter_jazz": (["FIREPLACE", "JAZZ"], "Warm jazz · Crackling fire", SEASON_BADGE),
    "17_christmas_jazz": (["CHRISTMAS", "JAZZ"], "Cozy holiday piano", SEASON_BADGE),
    "21_halloween_night": (["HALLOWEEN", "NIGHT"], "Spooky, not scary · Music box", SEASON_BADGE),
}


# 2026-10-28 からの標準サムネ (ChatGPT のサムネに倣った、セリフ体の上品な文字組み)。
# art/<slug>.png (ChatGPT の文字なしイラスト) があればその絵に、無ければこちらの
# シーンを水彩風にした絵に載せる。(タイトル 2 行, 副題)
ELEGANT = {
    "g01_gentle_piano_sleep": (["SLEEP", "PIANO"], "NO RAIN · NO NOISE"),
    "g02_deep_sleep_piano": (["DEEP SLEEP", "PIANO"], "NO RAIN · NO NOISE"),
    "g03_emotional_sleep_piano": (["BEAUTIFUL", "SLEEP PIANO"], "NO RAIN · NO NOISE"),
    "03_piano_and_rain": (["PIANO", "& RAIN"], "FOR SLEEP & STUDY"),
    "04_cozy_coffee_jazz": (["COFFEE", "SHOP JAZZ"], "WARM PIANO"),
    "05_bossa_nova_cafe": (["BOSSA NOVA", "CAFÉ"], "SMOOTH GUITAR"),
    "07_fireplace_winter_jazz": (["FIREPLACE", "JAZZ"], "WARM WINTER NIGHT"),
    "17_christmas_jazz": (["CHRISTMAS", "JAZZ"], "COZY HOLIDAY PIANO"),
    "21_halloween_night": (["HALLOWEEN", "NIGHT"], "SPOOKY, NOT SCARY"),
    "n01_twinkle_lullaby": (["TWINKLE", "TWINKLE"], "LULLABY FOR BABIES"),
    "n02_mary_lamb_lullaby": (["MARY HAD A", "LITTLE LAMB"], "LULLABY FOR BABIES"),
    "n03_row_your_boat_lullaby": (["ROW ROW", "YOUR BOAT"], "LULLABY FOR BABIES"),
    "n04_frere_jacques_lullaby": (["FRÈRE", "JACQUES"], "LULLABY FOR BABIES"),
    "n05_london_bridge_lullaby": (["LONDON", "BRIDGE"], "MUSIC BOX LULLABY"),
    "n06_old_macdonald_lullaby": (["OLD", "MACDONALD"], "LULLABY FOR NAPTIME"),
    "n07_au_clair_lullaby": (["AU CLAIR", "DE LA LUNE"], "FRENCH LULLABY"),
    "n08_silent_night_lullaby": (["SILENT", "NIGHT"], "CHRISTMAS LULLABY"),
    "n09_ode_to_joy_lullaby": (["ODE TO", "JOY"], "MUSIC BOX LULLABY"),
    "n10_jingle_bells_lullaby": (["JINGLE", "BELLS"], "SLOW LULLABY"),
    "n11_lullaby_medley": (["10 BABY", "LULLABIES"], "SOFT PIANO & MUSIC BOX"),
    "x01_christmas_piano": (["CHRISTMAS", "PIANO"], "10 CLASSIC CAROLS"),
    "x02_christmas_musicbox": (["CHRISTMAS", "MUSIC BOX"], "10 CLASSIC CAROLS"),
    "x03_christmas_bells": (["CHRISTMAS", "BELLS"], "PIANO & SLEIGH BELLS"),
    "x04_christmas_calm": (["CALM", "CHRISTMAS"], "PEACEFUL PIANO CAROLS"),
    "x05_jingle_bells_sleigh": (["JINGLE", "BELLS"], "PIANO & SLEIGH BELLS"),
    "x06_silent_night_piano": (["SILENT", "NIGHT"], "CALM CHRISTMAS PIANO"),
    "x07_o_holy_night_piano": (["O HOLY", "NIGHT"], "CALM CHRISTMAS PIANO"),
    "x08_christmas_carols_2_musicbox": (["CHRISTMAS", "MUSIC BOX"], "VOL. 2 · 10 MORE CAROLS"),
    "x09_we_wish_you_bells": (["MERRY", "CHRISTMAS"], "PIANO & SLEIGH BELLS"),
    "n12_brahms_lullaby": (["BRAHMS'", "LULLABY"], "SOFT PIANO FOR BABIES"),
    "n12_brahms_lullaby_musicbox": (["BRAHMS'", "LULLABY"], "MUSIC BOX LULLABY"),
    "n13_rockabye_baby": (["ROCK-A-BYE", "BABY"], "SOFT PIANO FOR BABIES"),
    "n13_rockabye_baby_musicbox": (["ROCK-A-BYE", "BABY"], "MUSIC BOX LULLABY"),
    "n14_amazing_grace_lullaby": (["AMAZING", "GRACE"], "SOFT PIANO LULLABY"),
    "n14_amazing_grace_lullaby_musicbox": (["AMAZING", "GRACE"], "MUSIC BOX LULLABY"),
    "n15_all_through_the_night": (["ALL THROUGH", "THE NIGHT"], "SOFT PIANO LULLABY"),
    "n15_all_through_the_night_musicbox": (["ALL THROUGH", "THE NIGHT"], "MUSIC BOX LULLABY"),
}


def _length_badge(total_seconds: float) -> str:
    h = total_seconds / 3600.0
    if h >= 0.99:
        n = int(total_seconds // 3600)
        return "1 HOUR" if n == 1 else f"{n} HOURS"
    return f"{int(round(total_seconds / 60))} MIN"


def _make_thumbnail(spec: TR.TrackSpec, total_seconds: float):
    art = TR.art_for(spec)
    if art is not None:
        import json
        from PIL import Image
        cfg = art.with_suffix(".json")
        if cfg.exists() and json.loads(cfg.read_text(encoding="utf-8")).get("has_text"):
            # ChatGPT が文字まで入れて仕上げたサムネは、そのまま使う
            im = Image.open(art).convert("RGB").resize((1280, 720), Image.LANCZOS)
            if spec.slug.endswith("_musicbox"):
                # オルゴール版は同じ絵なので、右上にバッジを重ねてピアノ版と見分けられるようにする
                from bgm_studio import illustrated as IL
                im = IL.corner_badge(im, "MUSIC BOX")
            return im
    if spec.slug in ELEGANT:
        from PIL import Image
        import numpy as np
        from bgm_studio import illustrated as IL
        lines, sub = ELEGANT[spec.slug]
        art = TR.art_for(spec)
        if art:
            bg = Image.open(art)
        else:
            fr = VIS.scene_maker(spec.visual)(seed=spec.seed)(0.2)
            bg = IL.watercolor(Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)),
                               seed=spec.seed)
        im = IL.elegant_thumbnail(bg, lines, sub, _length_badge(total_seconds))
        # タイトルに MUSIC BOX と書いてあるときは、バッジを重ねると同じ言葉が 2 回になる
        if spec.slug.endswith("_musicbox") and "MUSIC BOX" not in " ".join(lines):
            im = IL.corner_badge(im, "MUSIC BOX")
        return im
    return _make_thumbnail_v1(spec, total_seconds)


def _make_thumbnail_v1(spec: TR.TrackSpec, total_seconds: float):
    if spec.slug in KIDS_THUMB:
        from bgm_studio import kids_visuals as KV
        h = total_seconds / 3600.0
        hrs = int(round(h))
        length = (("1 HOUR" if hrs == 1 else f"{hrs} HOURS") if h >= 0.99 else
                  f"{int(round(total_seconds / 60))} MIN")
        badge = f"{length} LULLABY" if spec.slug != "n11_lullaby_medley" else f"{length} · 10 SONGS"
        return KV.kids_thumbnail(KIDS_THUMB[spec.slug], badge,
                                 "for Babies & Sleep", scene=spec.visual, seed=spec.seed)
    if spec.slug in BOLD_THUMB:
        from bgm_studio import sleep_visuals as SV
        lines, promise, color = BOLD_THUMB[spec.slug]
        hrs = int(total_seconds // 3600)
        # 暖炉・ハロウィン・雨の映像は暗いので、サムネだけ明るく持ち上げる
        bright = 1.12 if spec.visual.startswith("moon_lake") else 1.4
        return SV.calm_thumbnail(lines, f"{hrs} HOURS", promise, scene=spec.visual,
                                 seed=spec.seed, badge_color=color, brighten=bright)
    return VIS.thumbnail(spec.visual, _thumb_lines(spec, total_seconds), seed=spec.seed)


def _thumb_lines(spec: TR.TrackSpec, total_seconds: float) -> list[str]:
    """サムネの文字。3〜4 語まで、用途が一目で分かること"""
    hours = int(total_seconds // 3600)
    head = {
        "01_lofi_rainy_study": ["LOFI RAIN", f"{hours} HOURS · STUDY"],
        "02_deep_sleep_ambient": ["DEEP SLEEP", f"{hours} HOURS"],
        "03_piano_and_rain": ["PIANO & RAIN", f"{hours} HOURS"],
        "04_cozy_coffee_jazz": ["COFFEE JAZZ", f"{hours} HOURS · WORK"],
        "05_bossa_nova_cafe": ["BOSSA NOVA", f"{hours} HOURS · CAFE"],
        "06_healing_meditation_432": ["432Hz HEALING", f"{hours} HOURS"],
        "07_fireplace_winter_jazz": ["FIREPLACE JAZZ", f"{hours} HOURS"],
        "08_ocean_waves_ambient": ["OCEAN WAVES", f"{hours} HOURS · SLEEP"],
        "09_fantasy_tavern": ["TAVERN AMBIENCE", f"{hours} HOURS"],
        "10_deep_focus_flow": ["DEEP FOCUS", f"{hours} HOURS · FLOW"],
        "11_sleep_city_8h": ["SLEEP MUSIC", f"{hours} HOURS · ALL NIGHT"],
        "12_anime_piano_emotional": ["ANIME PIANO", f"{hours} HOURS · EMOTIONAL"],
        "13_fresh_morning_acoustic": ["MORNING MUSIC", f"{hours} HOURS · FRESH"],
        "14_japanese_lofi_koto": ["JAPANESE LOFI", f"{hours} HOURS · KOTO"],
        "15_rain_thunder_night": ["RAIN & THUNDER", f"{hours} HOURS · SLEEP"],
        "16_autumn_cafe_jazz": ["AUTUMN JAZZ", f"{hours} HOURS · COZY"],
        "17_christmas_jazz": ["CHRISTMAS JAZZ", f"{hours} HOURS · HOLIDAY"],
        "18_starship_sleep": ["STARSHIP SLEEP", f"{hours} HOURS · SPACE HUM"],
        "19_528hz_love_frequency": ["528 Hz", f"{hours} HOURS · HEALING"],
        "20_focus_40hz": ["40Hz FOCUS", f"{hours} HOURS · DEEP WORK"],
        "21_halloween_night": ["HALLOWEEN", f"{hours} HOURS · SPOOKY"],
        "22_snowstorm_fireplace": ["SNOWSTORM", f"{hours} HOURS · FIREPLACE"],
        "23_forest_night_camp": ["NIGHT CAMPFIRE", f"{hours} HOURS · FOREST"],
        "24_deep_space_drone": ["DEEP SPACE", f"{hours} HOURS · DARK AMBIENT"],
        "25_cyberpunk_rain": ["CYBERPUNK RAIN", f"{hours} HOURS · NEON"],
        "26_dark_academia_library": ["DARK ACADEMIA", f"{hours} HOURS · STUDY"],
        "27_rain_black_screen": ["RAIN · BLACK SCREEN", f"{hours} HOURS"],
    }
    nursery = {
        "n01_twinkle_lullaby": ["TWINKLE TWINKLE", "LULLABY PIANO"],
        "n02_mary_lamb_lullaby": ["MARY HAD A", "LITTLE LAMB"],
        "n03_row_your_boat_lullaby": ["ROW ROW ROW", "YOUR BOAT"],
        "n04_frere_jacques_lullaby": ["FRÈRE JACQUES", "LULLABY"],
        "n05_london_bridge_lullaby": ["LONDON BRIDGE", "LULLABY"],
        "n06_old_macdonald_lullaby": ["OLD MACDONALD", "SOFT PIANO"],
        "n07_au_clair_lullaby": ["AU CLAIR", "DE LA LUNE"],
        "n08_silent_night_lullaby": ["SILENT NIGHT", "PIANO LULLABY"],
        "n09_ode_to_joy_lullaby": ["ODE TO JOY", "MUSIC BOX"],
        "n10_jingle_bells_lullaby": ["JINGLE BELLS", "SLOW LULLABY"],
    }
    if spec.slug in nursery:
        mins = int(round(total_seconds / 60.0))
        return [nursery[spec.slug][0], f"{mins} MIN · {nursery[spec.slug][1]}"]
    return head.get(spec.slug, [spec.title_en.upper(), f"{hours} HOURS"])


# ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="YouTube 向け BGM 動画を生成する")
    ap.add_argument("--tracks", nargs="*", default=None,
                    help="対象スラッグ (省略時は全 10 本)")
    ap.add_argument("--seconds", type=float, default=TR.LOOP_SECONDS,
                    help=f"ループ 1 周の長さ [秒] (既定 {TR.LOOP_SECONDS})")
    ap.add_argument("--repeats", type=int, default=TR.LOOP_REPEATS,
                    help=f"ループ回数 (既定 {TR.LOOP_REPEATS})")
    ap.add_argument("--no-video", action="store_true", help="音源とメタだけ作る")
    ap.add_argument("--visual-only", action="store_true",
                    help="既存の音源を使い、映像とサムネだけ作り直して再多重化する")
    ap.add_argument("--audio-bitrate", default="256k")
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()

    specs = TR.TRACKS
    if args.tracks:
        missing = [s for s in args.tracks if s not in TR.BY_SLUG]
        if missing:
            print(f"未知のスラッグ: {missing}", file=sys.stderr)
            return 2
        specs = [TR.BY_SLUG[s] for s in args.tracks]

    total = args.seconds * args.repeats
    log(f"=== BGM Studio ===")
    log(f"トラック数 : {len(specs)}")
    log(f"ループ長   : {args.seconds:.0f}s × {args.repeats} = "
        f"{VID.hhmmss(total)}")
    log(f"映像       : {VIS.W}x{VIS.H} @ {VIS.FPS}fps "
        f"({VIS.LOOP_SECONDS}s ループ)")

    results = []
    t0 = time.time()
    for spec in specs:
        try:
            results.append(process(spec, args))
        except Exception as e:  # 1 本失敗しても残りは続ける
            import traceback
            traceback.print_exc()
            results.append({"slug": spec.slug, "error": f"{type(e).__name__}: {e}"})

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(
        json.dumps({"total_seconds": total, "tracks": results},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"\n=== 完了 ({(time.time() - t0) / 60:.1f} 分) ===")
    ok = [r for r in results if "error" not in r]
    for r in ok:
        log(f"  {r['slug']:28s} {r['total_hhmmss']}  "
            f"{r['lufs']:.1f} LUFS  継ぎ目 {r['loop_seam_db']:+.1f} dB")
    for r in results:
        if "error" in r:
            log(f"  {r['slug']:28s} 失敗: {r['error']}")
    return 0 if len(ok) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
