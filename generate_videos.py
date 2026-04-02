#!/usr/bin/env python3
"""
Relaxing YouTube Video Generator
5本のリラックス動画を生成:
  1. campfire.mp4     - 焚き火（揺らぎ炎エフェクト）
  2. candle.mp4       - キャンドル（暗室でのロウソク）
  3. aurora.mp4       - オーロラ（北極光）
  4. rain.mp4         - 雨（夜の雨）
  5. ocean_night.mp4  - 夜の海（月明かり）
"""

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import imageio
import os
import math
import sys

# ─────────────────────────────────────────────
# 共通設定
# ─────────────────────────────────────────────
W, H   = 1280, 720   # 720p HD (YouTube対応)
FPS    = 30
DUR    = 180          # 秒 (3分)
N      = FPS * DUR
OUTDIR = "videos"
os.makedirs(OUTDIR, exist_ok=True)


def progress(i, total, label):
    pct = 100 * i // total
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)
    print(f"\r  [{bar}] {pct:3d}%  {label}", end="", flush=True)


def save_video(path, gen, total, label):
    """フレームイテレータから MP4 を保存"""
    writer = imageio.get_writer(
        path,
        fps=FPS,
        macro_block_size=16,
        ffmpeg_log_level="quiet",
        output_params=["-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast"],
    )
    for i, frame in enumerate(gen):
        writer.append_data(np.asarray(frame, dtype=np.uint8))
        if i % FPS == 0:
            progress(i, total, label)
    writer.close()
    print(f"\n  完成 → {path}")


# ─────────────────────────────────────────────
# 共通ユーティリティ
# ─────────────────────────────────────────────

def alpha_composite(bg: np.ndarray, fg: np.ndarray) -> np.ndarray:
    """RGBA fg を RGB bg に合成して RGB を返す"""
    alpha = fg[:, :, 3:4] / 255.0
    return np.clip(
        bg.astype(np.float32) * (1 - alpha) + fg[:, :, :3].astype(np.float32) * alpha,
        0, 255
    ).astype(np.uint8)


def make_star_field(w, h, n=500, seed=0):
    """静的な星空 numpy 配列 (H,W,3) を生成"""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # 空グラデーション (上: 黒, 下: 紺)
    for y in range(h):
        v = int(y / h * 18)
        img[y, :] = [0, 0, v]
    # 星をばら撒く
    sx = rng.integers(0, w, n)
    sy = rng.integers(0, int(h * 0.75), n)
    sv = rng.integers(120, 240, n)
    for i in range(n):
        img[sy[i], sx[i]] = [sv[i], sv[i], sv[i]]
    return img


# ─────────────────────────────────────────────
# 炎シミュレーション (Doom Fire アルゴリズム)
# ─────────────────────────────────────────────

def _make_fire_palette():
    p = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        x = i / 255.0
        if x < 0.20:
            p[i] = [int(x / 0.20 * 160), 0, 0]
        elif x < 0.45:
            v = (x - 0.20) / 0.25
            p[i] = [int(160 + v * 95), int(v * 70), 0]
        elif x < 0.70:
            v = (x - 0.45) / 0.25
            p[i] = [255, int(70 + v * 155), 0]
        elif x < 0.90:
            v = (x - 0.70) / 0.20
            p[i] = [255, int(225 + v * 30), int(v * 80)]
        else:
            v = (x - 0.90) / 0.10
            p[i] = [255, 255, int(80 + v * 175)]
    return p

FIRE_PALETTE = _make_fire_palette()


def fire_step(fire: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
    """
    fire : (fh, fw) uint8   0=冷, 255=最高温
    seed_mask : (fw,) bool  底辺のどの列に着火するか
    """
    fh, fw = fire.shape
    spread = np.random.randint(0, 3, size=(fh - 1, fw))   # 0,1,2
    decay  = np.random.randint(0, 4, size=(fh - 1, fw))   # 0,1,2,3
    src_x  = (np.arange(fw) + spread - 1 + fw) % fw       # (fh-1, fw)
    row_bl = np.arange(1, fh)[:, None] * np.ones(fw, dtype=int)
    gathered = fire[row_bl, src_x]
    new_top  = np.clip(gathered.astype(np.int16) - decay, 0, 255).astype(np.uint8)
    out = fire.copy()
    out[:-1] = new_top
    n_seed = seed_mask.sum()
    if n_seed:
        out[-1, seed_mask]  = np.random.randint(215, 256, size=n_seed, dtype=np.uint8)
        out[-2, seed_mask]  = np.random.randint(190, 250, size=n_seed, dtype=np.uint8)
    out[-1, ~seed_mask] = np.maximum(
        0, out[-1, ~seed_mask].astype(np.int16) - 15
    ).astype(np.uint8)
    return out


def fire_to_rgb(fire: np.ndarray, fw_out: int, fh_out: int) -> np.ndarray:
    """fire → RGBカラー → PIL でリサイズ → numpy"""
    colored = FIRE_PALETTE[fire]          # (fh, fw, 3)
    img = Image.fromarray(colored)
    img = img.resize((fw_out, fh_out), Image.LANCZOS)
    return np.array(img)


# ─────────────────────────────────────────────
# VIDEO 1: 焚き火 (Campfire)
# ─────────────────────────────────────────────

def gen_campfire():
    FW, FH = 280, 160       # 炎シミュレーショングリッド
    SCALE  = 3              # 描画サイズ = FW*SCALE x FH*SCALE
    FW_S, FH_S = FW * SCALE, FH * SCALE

    # 種火マスク: 中央 40%
    cx = FW // 2
    hw = FW // 5
    base_mask = np.zeros(FW, dtype=bool)
    base_mask[cx - hw : cx + hw] = True

    sky   = make_star_field(W, H, n=400, seed=11)
    fire  = np.zeros((FH, FW), dtype=np.uint8)

    # 地面と丸太のオーバーレイ (RGBA)
    ground_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ground_img)
    gy = int(H * 0.80)
    gd.rectangle([0, gy, W, H], fill=(8, 18, 8, 255))
    rng2 = np.random.default_rng(7)
    for gx in range(0, W, 5):
        gh = int(rng2.uniform(4, 18))
        gd.polygon([(gx, gy), (gx+2, gy - gh), (gx+5, gy)], fill=(12, 28, 10, 200))
    # 丸太
    lcx = W // 2
    log_col = (40, 22, 10, 255)
    gd.polygon([(lcx-90, gy-6), (lcx+100, gy-16), (lcx+112, gy+4), (lcx-78, gy+8)],
               fill=log_col)
    gd.polygon([(lcx-105, gy-16), (lcx+85, gy-6), (lcx+75, gy+8), (lcx-115, gy+4)],
               fill=log_col)
    ground = np.array(ground_img)

    # ウォームアップ
    for _ in range(120):
        fire = fire_step(fire, base_mask)

    # 炎の配置座標
    fire_x0 = W // 2 - FW_S // 2
    fire_y1 = int(H * 0.80)
    fire_y0 = fire_y1 - FH_S

    for fi in range(N):
        t = fi / FPS
        # 揺らぎ: 炎幅をランダムに変化
        fw_var = int(hw * (0.75 + 0.25 * math.sin(t * 1.1) + 0.10 * math.sin(t * 3.3)))
        mask = np.zeros(FW, dtype=bool)
        mask[cx - fw_var : cx + fw_var] = True
        fire = fire_step(fire, mask)

        # フレームベース
        frame = sky.copy()

        # 炎 RGB をスクリーンに合成 (Screen blend)
        f_rgb = fire_to_rgb(fire, FW_S, FH_S)

        # クリッピング計算
        fy0 = max(fire_y0, 0)
        fy0_src = fy0 - fire_y0       # f_rgb 内オフセット
        fh_draw = min(FH_S - fy0_src, H - fy0)
        fx0 = max(fire_x0, 0)
        fx0_src = fx0 - fire_x0
        fw_draw = min(FW_S - fx0_src, W - fx0)

        if fh_draw > 0 and fw_draw > 0:
            reg  = frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw].astype(np.float32)
            fsrc = f_rgb[fy0_src:fy0_src+fh_draw, fx0_src:fx0_src+fw_draw].astype(np.float32)
            # Screen: 1-(1-a)(1-b)
            blended = 255 - (255 - reg) * (255 - fsrc) / 255
            frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw] = np.clip(blended, 0, 255).astype(np.uint8)

            # グロー (Glow)
            glow_pil = Image.fromarray(f_rgb[fy0_src:fy0_src+fh_draw, fx0_src:fx0_src+fw_draw])
            glow = np.array(glow_pil.filter(ImageFilter.GaussianBlur(radius=30))).astype(np.float32)
            frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw] = np.clip(
                frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw].astype(np.float32) + glow * 0.25,
                0, 255
            ).astype(np.uint8)

        # 地面・丸太を上書き
        frame = alpha_composite(frame, ground)

        # 全体輝度フリッカー
        br = 0.96 + 0.04 * math.sin(t * 5.7 + 0.4 * math.sin(t * 2.1))
        frame = np.clip(frame.astype(np.float32) * br, 0, 255).astype(np.uint8)

        yield frame


# ─────────────────────────────────────────────
# VIDEO 2: キャンドル (Candle)
# ─────────────────────────────────────────────

def gen_candle():
    FW, FH = 30, 80
    SCALE  = 5
    FW_S, FH_S = FW * SCALE, FH * SCALE

    cx = FW // 2
    hw = FW // 5
    mask = np.zeros(FW, dtype=bool)
    mask[cx - hw : cx + hw + 1] = True

    fire = np.zeros((FH, FW), dtype=np.uint8)
    for _ in range(100):
        fire = fire_step(fire, mask)

    # キャンドルの描画位置
    candle_x_center = W // 2
    fire_x0 = candle_x_center - FW_S // 2
    candle_top_y = int(H * 0.55)
    fire_y1 = candle_top_y
    fire_y0 = fire_y1 - FH_S

    # キャンドル本体オーバーレイ
    candle_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(candle_img)
    cw = 20
    ch_start = candle_top_y
    ch_end   = candle_top_y + 120
    cd.rectangle([candle_x_center - cw, ch_start, candle_x_center + cw, ch_end],
                 fill=(220, 210, 180, 255))
    # 受け皿
    cd.ellipse([candle_x_center - 35, ch_end - 10, candle_x_center + 35, ch_end + 10],
               fill=(160, 130, 90, 255))
    candle_overlay = np.array(candle_img)

    for fi in range(N):
        t = fi / FPS

        # 風揺れ: 炎を左右に微妙にずらす
        sway = int(1.5 * math.sin(t * 0.7 + 0.3 * math.sin(t * 1.9)))
        cur_mask = np.roll(mask, sway)
        fire = fire_step(fire, cur_mask)

        # 暗い部屋の背景
        frame = np.zeros((H, W, 3), dtype=np.uint8)

        # 炎の光が壁に当たるアンビエントグロー
        glow_center_x, glow_center_y = W // 2, H // 2
        Y, X = np.mgrid[0:H, 0:W]
        dist2 = ((X - glow_center_x) ** 2 + (Y - glow_center_y) ** 2).astype(np.float32)
        flicker = 0.85 + 0.15 * math.sin(t * 4.3)
        ambient = np.exp(-dist2 / (2 * (250 ** 2))) * 60 * flicker
        frame[:, :, 0] = np.clip(ambient, 0, 255).astype(np.uint8)
        frame[:, :, 1] = np.clip(ambient * 0.35, 0, 255).astype(np.uint8)
        frame[:, :, 2] = 0

        # 炎を配置
        f_rgb = fire_to_rgb(fire, FW_S, FH_S)
        fy0 = max(fire_y0, 0)
        fy0_src = fy0 - fire_y0
        fh_draw = min(FH_S - fy0_src, H - fy0)
        fx0 = max(fire_x0, 0)
        fx0_src = fx0 - fire_x0
        fw_draw = min(FW_S - fx0_src, W - fx0)

        if fh_draw > 0 and fw_draw > 0:
            reg  = frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw].astype(np.float32)
            fsrc = f_rgb[fy0_src:fy0_src+fh_draw, fx0_src:fx0_src+fw_draw].astype(np.float32)
            blended = 255 - (255 - reg) * (255 - fsrc) / 255
            frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw] = np.clip(blended, 0, 255).astype(np.uint8)
            glow = np.array(
                Image.fromarray(f_rgb[fy0_src:fy0_src+fh_draw, fx0_src:fx0_src+fw_draw])
                     .filter(ImageFilter.GaussianBlur(radius=15))
            ).astype(np.float32)
            frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw] = np.clip(
                frame[fy0:fy0+fh_draw, fx0:fx0+fw_draw].astype(np.float32) + glow * 0.4,
                0, 255
            ).astype(np.uint8)

        # キャンドル本体を上書き
        frame = alpha_composite(frame, candle_overlay)
        yield frame


# ─────────────────────────────────────────────
# VIDEO 3: オーロラ (Aurora Borealis)
# ─────────────────────────────────────────────

def gen_aurora():
    rng = np.random.default_rng(42)
    NB = 10   # 帯数

    phases  = rng.uniform(0, 2 * math.pi, NB)
    freqs   = rng.uniform(0.0015, 0.005, NB)
    speeds  = rng.uniform(0.12, 0.45, NB)
    amps    = rng.uniform(H * 0.04, H * 0.11, NB)
    centers = rng.uniform(H * 0.12, H * 0.55, NB)
    widths  = rng.uniform(H * 0.025, H * 0.075, NB)
    r_m     = rng.uniform(0.00, 0.20, NB)
    g_m     = rng.uniform(0.55, 1.00, NB)
    b_m     = rng.uniform(0.20, 0.70, NB)
    pp      = rng.uniform(0, 2 * math.pi, NB)
    ps      = rng.uniform(0.08, 0.30, NB)

    # 星
    n_st = 350
    sx = rng.integers(0, W, n_st)
    sy = rng.integers(0, int(H * 0.65), n_st)
    sv = rng.integers(100, 200, n_st)

    x_arr = np.arange(W, dtype=np.float32)
    Y_grid = np.tile(np.arange(H, dtype=np.float32)[:, None], (1, W))  # (H,W)

    # 静的な暗い空グラデーション
    base_sky = np.zeros((H, W, 3), dtype=np.float32)
    for y in range(H):
        frac = y / H
        base_sky[y, :, 2] = 4 + frac * 15

    for fi in range(N):
        t = fi / FPS
        sky = base_sky.copy()

        for b in range(NB):
            bc = centers[b] + amps[b] * np.sin(x_arr * freqs[b] + t * speeds[b] + phases[b])
            dist = Y_grid - bc[np.newaxis, :]    # (H,W) ← 修正: bc shape(W,)→broadcast
            # 上記: dist[y,x] = y - bc[x]  ✓
            intensity = np.exp(-0.5 * (dist / widths[b]) ** 2)
            pulse = 0.65 + 0.35 * math.sin(t * ps[b] + pp[b])
            scale = pulse * 180

            sky[:, :, 0] += intensity * r_m[b] * scale
            sky[:, :, 1] += intensity * g_m[b] * scale
            sky[:, :, 2] += intensity * b_m[b] * scale

        frame = np.clip(sky, 0, 255).astype(np.uint8)

        # 星のきらめき
        for i in range(n_st):
            tw = int(sv[i] * (0.65 + 0.35 * math.sin(t * 1.7 + i * 0.4)))
            frame[sy[i], sx[i]] = [tw, tw, min(255, tw + 20)]

        # 地平線下: 暗い山シルエット
        hor_y = int(H * 0.80)
        frame[hor_y:, :] = np.clip(frame[hor_y:, :].astype(np.float32) * 0.15, 0, 255).astype(np.uint8)

        yield frame


# ─────────────────────────────────────────────
# VIDEO 4: 夜の雨 (Rain at Night)
# ─────────────────────────────────────────────

def gen_rain():
    rng = np.random.default_rng(55)
    N_DROP = 300

    dx = rng.uniform(0, W, N_DROP).astype(np.float32)
    dy = rng.uniform(-H, H, N_DROP).astype(np.float32)
    spd = rng.uniform(400, 700, N_DROP).astype(np.float32)
    dlen = rng.integers(15, 35, N_DROP)
    angle = 0.18   # 傾き (右へ)

    # 波紋リスト: [x, y, r, max_r, born_t]
    ripples = []
    next_rip_t = 0.5
    rip_y = int(H * 0.82)   # 地面 y

    # 静的背景: 暗い夜
    static_bg = np.zeros((H, W, 3), dtype=np.uint8)
    # 遠くの街明かり (オレンジ霧)
    Y_bg, X_bg = np.mgrid[0:H, 0:W].astype(np.float32)
    glow_bg = np.exp(-((Y_bg - H * 0.78) ** 2) / (2 * (80 ** 2))) * 35
    static_bg[:, :, 0] = np.clip(glow_bg * 1.0, 0, 255).astype(np.uint8)
    static_bg[:, :, 1] = np.clip(glow_bg * 0.45, 0, 255).astype(np.uint8)
    # 地面
    static_bg[rip_y:, :, 0] = 12
    static_bg[rip_y:, :, 1] = 12
    static_bg[rip_y:, :, 2] = 18

    dt = 1.0 / FPS
    for fi in range(N):
        t = fi / FPS
        frame = static_bg.copy()

        # 雨粒を動かす
        dy += spd * dt
        dx += spd * angle * dt
        off = dy > H + 40
        dy[off] = rng.uniform(-60, -10, off.sum()).astype(np.float32)
        dx[off] = rng.uniform(0, W, off.sum()).astype(np.float32)

        # 雨粒を描画 (numpy ライン近似)
        frame_pil = Image.fromarray(frame)
        draw_r = ImageDraw.Draw(frame_pil)
        for i in range(N_DROP):
            x0 = int(dx[i])
            y0 = int(dy[i])
            x1 = int(x0 - dlen[i] * angle)
            y1 = y0 - int(dlen[i])
            brightness = rng.integers(80, 160)
            draw_r.line([(x0, y0), (x1, y1)], fill=(brightness, brightness, int(brightness * 1.1)), width=1)
        frame = np.array(frame_pil)

        # 波紋を追加
        if t >= next_rip_t:
            rx = int(rng.uniform(50, W - 50))
            ripples.append([rx, rip_y, 0.0, rng.uniform(30, 70), t])
            next_rip_t = t + rng.uniform(0.2, 0.6)

        # 波紋を描画
        still_alive = []
        frame_pil2 = Image.fromarray(frame)
        draw_rip = ImageDraw.Draw(frame_pil2)
        for rp in ripples:
            rx, ry, r, mr, bt = rp
            age = t - bt
            r = age * mr / 0.8
            alpha_rip = max(0, 1 - age / 0.8)
            if r < mr and alpha_rip > 0:
                gray = int(100 * alpha_rip)
                draw_rip.ellipse(
                    [rx - r, ry - r * 0.25, rx + r, ry + r * 0.25],
                    outline=(gray, gray, int(gray * 1.2)), width=1
                )
                rp[2] = r
                still_alive.append(rp)
        frame = np.array(frame_pil2)
        ripples[:] = still_alive

        # 霧の深さ感 (遠近ブラー)
        if fi % 3 == 0:   # 3フレームに1回だけ適用
            fog = np.array(
                Image.fromarray(frame).filter(ImageFilter.GaussianBlur(radius=1))
            )
            frame = np.clip(frame.astype(np.float32) * 0.7 + fog.astype(np.float32) * 0.3,
                            0, 255).astype(np.uint8)

        yield frame


# ─────────────────────────────────────────────
# VIDEO 5: 夜の海 (Ocean at Night)
# ─────────────────────────────────────────────

def gen_ocean():
    rng = np.random.default_rng(99)
    HORIZON = int(H * 0.42)

    # 星
    n_st = 450
    sx = rng.integers(0, W, n_st)
    sy = rng.integers(0, HORIZON, n_st)
    sv = rng.integers(120, 220, n_st)

    # 月の位置
    moon_x, moon_y = int(W * 0.75), int(H * 0.14)
    moon_r = 38

    x_arr = np.arange(W, dtype=np.float32)
    y_arr = np.arange(H, dtype=np.float32)

    # 静的空グラデーション (上=暗紺, 地平=薄紺)
    sky_r = np.interp(np.arange(HORIZON), [0, HORIZON], [2, 15]).astype(np.float32)
    sky_g = np.interp(np.arange(HORIZON), [0, HORIZON], [2, 18]).astype(np.float32)
    sky_b = np.interp(np.arange(HORIZON), [0, HORIZON], [20, 45]).astype(np.float32)

    for fi in range(N):
        t = fi / FPS
        frame = np.zeros((H, W, 3), dtype=np.float32)

        # 空
        frame[:HORIZON, :, 0] = sky_r[:, None]
        frame[:HORIZON, :, 1] = sky_g[:, None]
        frame[:HORIZON, :, 2] = sky_b[:, None]

        # 星のきらめき
        for i in range(n_st):
            tw = sv[i] * (0.6 + 0.4 * math.sin(t * 1.3 + i * 0.55))
            frame[sy[i], sx[i]] = [tw * 0.9, tw * 0.9, tw]

        # 月
        Y_m, X_m = np.ogrid[:H, :W]
        moon_mask = ((X_m - moon_x) ** 2 + (Y_m - moon_y) ** 2) <= moon_r ** 2
        frame[moon_mask] = [240, 240, 210]
        # 月のグロー
        moon_glow = np.exp(-(((Y_m - moon_y) ** 2 + (X_m - moon_x) ** 2).astype(np.float32)) / (2 * (70 ** 2))) * 40
        frame[:, :, 0] += moon_glow
        frame[:, :, 1] += moon_glow
        frame[:, :, 2] += moon_glow * 0.9

        # 海
        for y in range(HORIZON, H):
            depth = (y - HORIZON) / (H - HORIZON)
            w1 = 0.25 * np.sin(x_arr * 0.018 + t * 0.7)
            w2 = 0.15 * np.sin(x_arr * 0.032 - t * 1.1 + 0.8)
            w3 = 0.08 * np.sin(x_arr * 0.077 + t * 2.0 + 1.5)
            wave = w1 + w2 + w3   # -0.48 ~ +0.48

            base_r = 3  + depth * 5
            base_g = 8  + depth * 18
            base_b = 28 + depth * 40

            # 月の反射
            moon_ref_x = moon_x + (y - HORIZON) * 0.05 * math.sin(t * 0.4)
            moon_ref_dist = np.abs(x_arr - moon_ref_x)
            moon_ref = np.exp(-(moon_ref_dist ** 2) / (2 * (30 + depth * 60) ** 2)) * 80

            highlight = (wave + 0.48) / 0.96 * 25
            frame[y, :, 0] = np.clip(base_r + highlight * 0.5 + moon_ref * 0.6, 0, 255)
            frame[y, :, 1] = np.clip(base_g + highlight * 0.8 + moon_ref * 0.7, 0, 255)
            frame[y, :, 2] = np.clip(base_b + highlight + moon_ref, 0, 255)

        # 地平線付近をわずかにブレンド
        blend_h = 6
        for dy2 in range(blend_h):
            alpha2 = dy2 / blend_h
            yy = HORIZON + dy2
            if yy < H:
                frame[yy] = frame[yy] * alpha2 + frame[HORIZON - 1] * (1 - alpha2)

        yield np.clip(frame, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────

VIDEOS = [
    ("campfire.mp4",    gen_campfire, "焚き火"),
    ("candle.mp4",      gen_candle,   "キャンドル"),
    ("aurora.mp4",      gen_aurora,   "オーロラ"),
    ("rain.mp4",        gen_rain,     "夜の雨"),
    ("ocean_night.mp4", gen_ocean,    "夜の海"),
]

if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else [v[0] for v in VIDEOS]

    print(f"解像度: {W}x{H}, FPS: {FPS}, 尺: {DUR}秒 ({DUR//60}分{DUR%60}秒)")
    print(f"出力先: {os.path.abspath(OUTDIR)}/\n")

    for fname, gen_fn, label in VIDEOS:
        if fname not in targets:
            continue
        path = os.path.join(OUTDIR, fname)
        print(f"【{label}】{fname}")
        save_video(path, gen_fn(), N, label)

    print("\n全動画の生成が完了しました！")
    print("YouTubeにアップロードできます。")
