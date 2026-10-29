"""
チャットで渡せる大きさ (1 ファイル 400MiB 未満) の投稿用 zip を作る。

2時間24分の本編は約 790MB あり、そのままでは送れない。
音声 (256kbps AAC) は商品そのものなので一切いじらず、
20 秒の映像ループだけを予算内のビットレートで描き直して多重化し直す。

    python3 pack_for_chat.py 21_halloween_night 03_piano_and_rain

出力: out/upload/<slug>.zip  (mp4 + サムネイル png)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

from bgm_studio import video as VID
from bgm_studio.tracks import TRACKS

OUT = Path(__file__).resolve().parent / "out"
LIMIT_BYTES = 400 * 1024 * 1024
TARGET_BYTES = int(LIMIT_BYTES * 0.94)      # mp4 のコンテナ分と zip の余白


def _ffmpeg(*args: str) -> None:
    p = subprocess.run([VID.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                        *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:])


def _upload_text(slug: str) -> str | None:
    meta = OUT / "metadata" / f"{slug}.json"
    if not meta.exists():
        return None
    import json
    m = json.loads(meta.read_text(encoding="utf-8"))
    kids = "はい、子ども向けです" if m.get("made_for_kids") else "いいえ、子ども向けではありません"
    return (f"【タイトル】\n{m['title']}\n\n【説明】\n{m['description']}\n\n"
            f"【タグ】\n{', '.join(m.get('tags', []))}\n\n"
            f"【設定】\n視聴者: {kids}\nAI の使用（改変されたコンテンツ）: はい\n"
            f"動画の言語: 英語 / カテゴリ: 音楽\n")


def pack(slug: str) -> Path:
    spec = next(s for s in TRACKS if s.slug == slug)
    src = OUT / "video" / f"{slug}.mp4"
    png = OUT / "thumbnail" / f"{slug}.png"
    dur = VID.probe(src)["duration_s"]

    # 音声は本編からそのまま抜き出す (再エンコードしない)
    tmp = OUT / "tmp"
    tmp.mkdir(exist_ok=True)
    m4a = tmp / f"{slug}.chat.m4a"
    _ffmpeg("-i", str(src), "-map", "0:a:0", "-c", "copy", str(m4a))

    budget_bits = TARGET_BYTES * 8 - m4a.stat().st_size * 8
    v_kbps = int(budget_bits / dur / 1000)
    if v_kbps < 100:
        # 3 時間版などは 256kbps の音声だけで上限に近い。そのときだけ、元のループ WAV
        # から 192kbps で作り直す (AAC→AAC の再エンコードにしないため)。
        # YouTube 側の再生音質 (Opus 最大 160kbps 前後) よりは十分に高い
        wav = OUT / "audio" / f"{slug}.wav"
        loop_s = VID.probe(wav)["duration_s"]
        reps = int(round(dur / loop_s))
        VID.loop_audio_to_aac(wav, m4a, repeats=reps, bitrate="192k")
        budget_bits = TARGET_BYTES * 8 - m4a.stat().st_size * 8
        v_kbps = int(budget_bits / dur / 1000)
    if v_kbps < 80:
        raise SystemExit(f"{slug}: 音声だけで上限に近く、映像に {v_kbps}kbps しか残りません。"
                         "8時間・10時間版はこの方法では送れません。")
    v_kbps = min(v_kbps, 400)

    vis = tmp / f"{slug}.chat_visual.mp4"
    from bgm_studio.tracks import visual_for
    VID.encode_visual_loop(visual_for(spec), vis, seed=spec.seed,
                           crf=24, maxrate=f"{v_kbps}k",
                           # 既定の 4M だと 20 秒ループ全体より大きく、上限が効かない。
                           # 1 秒ぶんにして実際に頭打ちさせる
                           bufsize=f"{v_kbps}k",
                           # 400MiB に収めると 1080p では 100kbps 前後しか残らず、縦筋が出た。
                           # 同じビットレートなら 720p の方がはるかにきれい
                           out_size=(1280, 720) if v_kbps < 180 else None)
    mp4 = tmp / f"{slug}.mp4"
    VID.mux_looped(vis, m4a, mp4, total_seconds=dur)
    got = VID.probe(mp4)["duration_s"]
    if abs(got - dur) > 1.0:
        raise SystemExit(f"{slug}: 長さが変わりました ({dur:.1f}s → {got:.1f}s)")

    zpath = OUT / "upload" / f"{slug}.zip"
    zpath.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(mp4, mp4.name)
        z.write(png, png.name)
        txt = _upload_text(slug)
        if txt:
            # スマホで投稿するとき、タイトル・説明・タグを zip の中からそのままコピーできるように
            z.writestr(f"{slug}.txt", txt.encode("utf-8"))
    for p in (m4a, vis, mp4):
        p.unlink()

    size = zpath.stat().st_size
    print(f"{slug}: 映像 {v_kbps}kbps / zip {size / 2**20:.0f}MiB"
          f"{'' if size < LIMIT_BYTES else '  ⚠ 上限超え'}")
    if size >= LIMIT_BYTES:
        raise SystemExit(1)
    return zpath


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="+")
    for s in ap.parse_args().slugs:
        pack(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
