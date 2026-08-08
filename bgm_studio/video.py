"""
書き出し・動画合成。

2 時間超の映像を素直にエンコードすると時間もディスクも溶けるので、
    - 音声: 24 分のループ WAV を ffmpeg 側で 6 回繰り返しながら一気に AAC 化
    - 映像: 20 秒のループ MP4 を作り、-stream_loop + -c copy で複製
という構成にしている。映像は再エンコードしないので一瞬で終わる。

ループ MP4 は「先頭が必ず IDR フレーム」「シーンチェンジ検出オフ」で
作ってあるため、コピーで連結しても破綻しない。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

from . import visuals as V
from .dsp import SR


def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def ffprobe_exe() -> str | None:
    return shutil.which("ffprobe")


def _run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-25:])
        raise RuntimeError(f"command failed: {' '.join(cmd[:6])} ...\n{tail}")


# ──────────────────────────────────────────────────────────────
# 音声
# ──────────────────────────────────────────────────────────────

def write_wav(path: str | Path, audio: np.ndarray, sr: int = SR,
              bits: int = 24) -> Path:
    """
    float32 stereo → WAV。
    24bit で書くのは、この後 AAC に変換するまでに量子化ノイズを
    足したくないから (静かな睡眠音源では 16bit だと僅かに乗る)。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)

    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(bits // 8)
        w.setframerate(sr)
        if bits == 16:
            w.writeframes((x * 32767.0).astype("<i2").tobytes())
        else:
            q = np.clip(np.round(x * 8388607.0), -8388608, 8388607).astype("<i4")
            # int32 の下位 3 バイトだけを取り出して 24bit little-endian にする
            b = q.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
            w.writeframes(b)
    return path


def loop_audio_to_aac(wav_path: str | Path, out_path: str | Path,
                      repeats: int, bitrate: str = "256k",
                      sample_rate: int = 48000) -> Path:
    """
    ループ WAV を repeats 回つないで AAC にする。
    連続した 1 本のストリームとしてエンコードするので、
    継ぎ目にエンコーダ由来の隙間が入らない。
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run([ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
          "-stream_loop", str(repeats - 1), "-i", str(wav_path),
          "-c:a", "aac", "-b:a", bitrate, "-ar", str(sample_rate), "-ac", "2",
          str(out_path)])
    return out_path


# ──────────────────────────────────────────────────────────────
# 映像
# ──────────────────────────────────────────────────────────────

def encode_visual_loop(scene: str, out_path: str | Path, seed: int = 0,
                       seconds: int = V.LOOP_SECONDS, fps: int = V.FPS,
                       crf: int = 24, maxrate: str = "400k",
                       progress=None) -> Path:
    """
    シーンのループ映像を MP4 にする。生 RGB を ffmpeg に流し込む。

    -sc_threshold 0 と keyint 固定で「決まった位置にしか IDR を置かない」
    状態にしておくのが要点。これでコピー連結しても崩れない。
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(seconds * fps)
    keyint = max(fps * 10, 1)

    cmd = [
        ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{V.W}x{V.H}", "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "slow",
        "-crf", str(crf), "-maxrate", maxrate, "-bufsize", "4M",
        "-pix_fmt", "yuv420p",
        "-g", str(keyint), "-keyint_min", str(keyint), "-sc_threshold", "0",
        "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for i, frame in enumerate(V.render_frames(scene, seed=seed,
                                                  seconds=seconds, fps=fps)):
            proc.stdin.write(frame.tobytes())
            if progress and i % fps == 0:
                progress(i, n_frames)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"x264 encode failed:\n{err[-2000:]}")
    return out_path


def mux_looped(visual_mp4: str | Path, audio_m4a: str | Path,
               out_path: str | Path, total_seconds: float,
               visual_seconds: int = V.LOOP_SECONDS) -> Path:
    """
    ループ映像を必要な回数だけ複製し、長尺の音声と多重化する。
    映像も音声も再エンコードしない (-c copy) ので数秒で終わる。
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 音声より確実に長くしてから -shortest で切る
    reps = int(np.ceil(total_seconds / visual_seconds)) + 1
    _run([ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
          "-stream_loop", str(reps - 1), "-i", str(visual_mp4),
          "-i", str(audio_m4a),
          "-map", "0:v:0", "-map", "1:a:0",
          "-c", "copy", "-shortest",
          "-movflags", "+faststart",
          str(out_path)])
    return out_path


# ──────────────────────────────────────────────────────────────
# 検証
# ──────────────────────────────────────────────────────────────

def probe(path: str | Path) -> dict:
    """ffprobe で長さ・コーデック・ビットレートを取り出す (検証用)"""
    exe = ffprobe_exe()
    if exe is None:
        # imageio-ffmpeg には ffprobe が同梱されないので ffmpeg の出力を解析する
        return _probe_via_ffmpeg(path)
    p = subprocess.run([exe, "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return {"error": p.stderr}
    info = json.loads(p.stdout)
    out = {
        "duration_s": float(info["format"].get("duration", 0.0)),
        "size_mb": int(info["format"].get("size", 0)) / 1e6,
        "bitrate_kbps": int(info["format"].get("bit_rate", 0)) / 1000,
        "streams": [],
    }
    for s in info.get("streams", []):
        out["streams"].append({
            "type": s.get("codec_type"),
            "codec": s.get("codec_name"),
            "rate": s.get("sample_rate") or f"{s.get('width')}x{s.get('height')}",
            "fps": s.get("r_frame_rate"),
            "duration": float(s.get("duration", 0.0) or 0.0),
        })
    return out


def _probe_via_ffmpeg(path: str | Path) -> dict:
    """
    ffprobe が無い環境向けのフォールバック。
    `ffmpeg -i` が stderr に出す情報から長さとストリームを拾う。
    """
    import re
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)],
                       capture_output=True, text=True)
    txt = p.stderr
    out: dict = {"size_mb": Path(path).stat().st_size / 1e6, "streams": []}

    m = re.search(r"Duration:\s*(\d+):(\d\d):(\d\d(?:\.\d+)?)", txt)
    if m:
        h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        out["duration_s"] = h * 3600 + mi * 60 + s
    m = re.search(r"bitrate:\s*(\d+)\s*kb/s", txt)
    if m:
        out["bitrate_kbps"] = int(m.group(1))

    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("Stream #"):
            continue
        if "Video:" in line:
            codec = re.search(r"Video:\s*(\w+)", line)
            size = re.search(r"(\d{3,5}x\d{3,5})", line)
            fps = re.search(r"([\d.]+)\s*fps", line)
            br = re.search(r"(\d+)\s*kb/s", line)
            out["streams"].append({
                "type": "video",
                "codec": codec.group(1) if codec else "?",
                "rate": size.group(1) if size else "?",
                "fps": fps.group(1) if fps else "?",
                "kbps": int(br.group(1)) if br else None,
            })
        elif "Audio:" in line:
            codec = re.search(r"Audio:\s*(\w+)", line)
            hz = re.search(r"(\d+)\s*Hz", line)
            br = re.search(r"(\d+)\s*kb/s", line)
            out["streams"].append({
                "type": "audio",
                "codec": codec.group(1) if codec else "?",
                "rate": hz.group(1) if hz else "?",
                "kbps": int(br.group(1)) if br else None,
            })
    return out


def hhmmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 3600:d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
