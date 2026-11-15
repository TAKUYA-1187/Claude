"""
x05r v5：オーナーが合格とした v4 に、柔らかいそり鈴を足した比較版。2026-11-15。

オーナーの言葉：「これでいいです。合格。もっと求めるなら、鈴の音も柔らかく入れて下さい。
鈴の音が入っている、他のこの曲の動画も参考にして下さい。」

- ピアノの部分は v4 と同じ (同じ打鍵・強さ・ペダル。x05r_v4.render に鈴を足すだけ)
- 鈴：VCSL のそり鈴の録音 (CC0)。sleigh.py を参照
- 入れ方は、この曲の鈴の入った演奏でよく使われる形 (サビで拍に合わせて鳴らす・句の頭で振る) を控えめにした。
  Claude は他の動画の音を聞けないので、特定の動画をまねたものではない
    前奏の頭        ：軽く 1 回振る (約 2 秒で消える)
    ヴァース前半    ：なし
    ヴァース後半    ：4/4 の 2・4 拍目だけ
    サビ            ：毎拍。2・4 拍目を基準に、1・3 拍目は 4 dB 弱く。最後の 2 小節 (2/4) で少しずつ弱く
    最後の和音      ：振り続ける音を小さく重ね、約 3 秒で消す
- 大きさ：鈴だけの音量 (LUFS) を、ピアノだけの音量より 18 dB 小さくする (BELL_BELOW_PIANO_DB)
- 6.5 kHz より上を丸める (sleigh.LOWPASS_HZ)。左右は少し右寄り
"""

from __future__ import annotations

import numpy as np

from . import dsp
from . import x05r_v4 as V4
from .sleigh import Sleigh

SLUG = "x05r_60s"
SEED = 10505
BELL_BELOW_PIANO_DB = 18.0


def bell_events(chords):
    """(拍, 種類, 相対 dB) の列。拍は 4 分音符単位 (前奏 0〜8・ヴァース 8〜40・サビ 40〜72・終わり 72〜)"""
    ev = [(0.0, "shake_intro", -6.0)]
    for q in range(24, 40):                                   # ヴァース後半：2・4 拍目
        if q % 4 in (1, 3):
            ev.append((float(q), "hit", -3.0))
    for q in range(40, 72):                                   # サビ：毎拍
        g = 0.0 if q % 2 == 1 else -4.0
        if q >= 68:
            g -= 1.5 * (q - 67)
        ev.append((float(q), "hit", g))
    final = [c for c in chords if c[3] == "coda"][2][0]       # 最後の和音 (B♭69 → ハ長調で C69)
    ev.append((final, "shake_end", -4.0))
    return ev


def make_add_layers(seed: int = SEED):
    rec = {}

    def add(buf, tm, chords):
        sl = Sleigh(seed)
        rng = np.random.default_rng(seed + 1)
        bells = np.zeros_like(buf)
        events = []
        for q, kind, g in bell_events(chords):
            t = max(0.0, tm(q) + float(np.clip(rng.normal(0, 0.003), -0.008, 0.008)))
            if kind == "hit":
                y = sl.hit(g)
            elif kind == "shake_intro":
                y = sl.shake(2.0, g, fade_in=0.3, fade_out=1.5)
            else:
                y = sl.shake(4.0, g, fade_in=0.4, fade_out=3.0)
            i0 = int(t * dsp.SR)
            k = min(len(y), len(bells) - i0)
            bells[i0:i0 + k] += y[:k]
            events.append({"time_s": round(t, 3), "beat": q, "kind": kind, "relative_db": g})
        bells[:, 0] *= 0.85                                    # 少し右寄り
        lp, lb = dsp.lufs_integrated(buf), dsp.lufs_integrated(bells)
        gain = dsp.db2lin((lp - BELL_BELOW_PIANO_DB) - lb)
        bells *= np.float32(gain)
        buf += bells
        rec.update(sample="VCSL sleighbell2_hit_2 / hit_loud / shake1 (CC0)", lowpass_hz=6500,
                   bells_below_piano_db=BELL_BELOW_PIANO_DB,
                   piano_lufs_before_reverb=round(lp, 2), bells_lufs_before_reverb=round(dsp.lufs_integrated(bells), 2),
                   n_hits=sum(e["kind"] == "hit" for e in events), n_shakes=sum(e["kind"] != "hit" for e in events),
                   events=events, onsets=[e["time_s"] for e in events])
        return rec
    return add


def render(sr: int = dsp.SR):
    x, info = V4.render(sr, add_layers=make_add_layers())
    info["onsets"] = sorted(set(info["onsets"]) | set(info["layers"]["onsets"]))
    return x, info


# 旋律・和音・構成は v4 と同じ (書き出しと検収のスクリプトが参照する)
from .x05r_v4 import (OPEN_FIX_BAR, OPEN_FIX_G, INTRO_CH, VERSE_CH, CHORUS_CH, CODA_CH,  # noqa: E402,F401
                      chord_name_shift, build)
