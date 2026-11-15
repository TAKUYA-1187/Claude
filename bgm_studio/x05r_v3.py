"""
x05r_jingle_bells_piano v3：Genspark の指示書「Claudeへ貼る指示文（x05r Jingle Bells／2026-11-15）」への回答。2026-11-15。

v2 (同日) からの変更点 (指示書の条件に合わせたもの)
  1. ピアノ：Salamander Grand Piano V3 の原本 (48kHz/24bit) を使う。v2 は作者が作った 44.1kHz/16bit 版だった。
     エンジンは 44.1kHz なので、1 音ごとに「音の高さ合わせ + 48k→44.1k」を 1 回の再サンプリングで行う (grand.py)
  2. 離鍵の音：弦の響き (harm) に加えて、ハンマーノイズ (rel) も鳴らす
  3. 冒頭で主題が分かるように、前奏をサビの主題 (Jingle bells, jingle bells, jingle all the way) にした。
     v2 の前奏は和音だけだった
  4. テンポを ♩=72 → 66 にして、静けさに寄せた
  5. 音量：-14 LUFS 付近を目安に、先読みのピークリミッター (最大の圧縮量を記録) をかける。v2 はリミッターなしで -17.5 LUFS だった

旋律の出典・採譜・和声・伴奏・演奏の考え方は v2 (x05r_v2.py) と同じものを使う。
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d

from . import dsp
from . import x05r_v2 as V2
from .grand import Grand

SLUG = "x05r_60s"
BPM = 66.0
SEED = 10503
TARGET_LUFS = -14.0
CEILING_DBTP = -1.2

# 前奏：サビの最初の 4 小節 (2/4。1913 年版、VERSE/CHORUS と同じく +3 半音で変ロ長調) を静かに。
# 和音は旋律の D と半音でぶつからないもの (E♭ を含む和音は使わない)
INTRO_CH = ["Bbmaj7", "Dm7", "Gm7", "F6"]
_Q_EXTRA = {"6": (0, 4, 7, 9)}


def intro_melody():
    return [[(None if m is None else m + V2.TRANSPOSE, d) for m, d in V2.H1913[16 + i]] for i in range(4)]


def build():
    verse = V2.plan_melody(V2.VERSE_PLAN, V2.VERSE_1857, 0)
    chorus = V2.plan_melody(V2.CHORUS_PLAN, V2.CHORUS_1857, 16)
    secs = ([("intro", INTRO_CH, intro_melody())] +
            [("verse", V2.VERSE_CH, [b[2] for b in verse])] +
            [("chorus", V2.CHORUS_CH, [b[2] for b in chorus])] +
            [("coda", V2.CODA_CH, V2.CODA_MEL)])
    notes, chords, t = [], [], 0.0
    for sec, chs, mels in secs:
        for i, (c, mel) in enumerate(zip(chs, mels)):
            chords.append((t, 2.0, c, sec, i))
            q = t
            for m, d in mel:
                if m is not None:
                    notes.append((q, d, m, "mel", sec))
                q += d
            t += 2.0
    notes += V2.accompaniment(chords, notes)
    notes.sort(key=lambda n: (n[0], n[2]))
    return notes, chords, t, {"intro": intro_melody(), "verse": verse, "chorus": chorus}


def tempo_map(chords, total):
    """v2 と同じ考え方 (句の終わりで 5%、最後で 12〜35% ゆっくり)。基準は ♩=66"""
    rng = np.random.default_rng(SEED + 1)
    f = []
    for s, d, name, sec, i in chords:
        k = 1.0 + float(rng.normal(0, 0.012))
        if sec in ("intro", "verse", "chorus") and i % 4 == 3:
            k *= 1.05
        if sec == "intro" and i == 3:
            k *= 1.04                                      # 前奏の終わりで一息
        if sec == "verse" and i == 15:
            k *= 1.06
        if sec == "chorus" and i >= 14:
            k *= 1.0 + 0.08 * (i - 13)
        if sec == "coda":
            k *= (1.12, 1.18, 1.35, 1.35)[i]
        f.append(k)
    beat = 60.0 / BPM
    starts = np.concatenate([[0.0], np.cumsum([2.0 * beat * k for k in f])])

    def tm(q: float) -> float:
        b = min(int(q // 2.0), len(f) - 1)
        return float(starts[b] + (q - 2.0 * b) * beat * f[b])
    return tm


def lookahead_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 3.0, release_ms: float = 180.0):
    """
    先読みのピークリミッター。サンプルごとに「天井を超えないために必要なゲイン」を求め、
    前後 look_ms の最小値 → 同じ幅の平均でなめらかにする (ピークの位置では必ず必要なゲイン以下になる)。
    戻りは release_ms の一次遅れ。最後に念のため天井で切るが、切った (クリップした) サンプル数を返す
    """
    c = float(dsp.db2lin(ceiling_db))
    pk = np.abs(x).max(axis=1)
    req = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    a = max(1, int(look_ms * 1e-3 * dsp.SR))
    g = minimum_filter1d(req, size=2 * a + 1, mode="nearest")
    g = uniform_filter1d(g, size=a + 1, mode="nearest")
    # 戻り (リリース)：64 サンプルごとに一次遅れで戻し、なめらかな方 (小さい方) を使う
    B = 64
    nb = (len(g) + B - 1) // B
    gp = np.concatenate([g, np.ones(nb * B - len(g))])
    blk = gp.reshape(nb, B).min(axis=1)
    coef = float(np.exp(-B / (release_ms * 1e-3 * dsp.SR)))
    rel = np.empty_like(blk)
    cur = 1.0
    for i, v in enumerate(blk):
        cur = v if v < cur else cur + (v - cur) * (1.0 - coef)
        rel[i] = cur
    rel_s = np.interp(np.arange(len(g)), np.arange(nb) * B + B / 2.0, rel)
    gain = np.minimum(g, rel_s).astype(np.float32)
    y = x * gain[:, None]
    over = int((np.abs(y) > c).sum())
    y = np.clip(y, -c, c).astype(np.float32)
    gr = -20 * np.log10(np.maximum(gain, 1e-9))
    stats = {"max_gain_reduction_db": round(float(gr.max()), 2),
             "time_with_reduction_over_1db_s": round(float((gr > 1.0).sum() / dsp.SR), 2),
             "time_with_reduction_over_3db_s": round(float((gr > 3.0).sum() / dsp.SR), 2),
             "samples_hard_clipped_at_ceiling": over}
    return y, stats


def render(sr: int = dsp.SR):
    assert sr == dsp.SR
    V2._Q.update(_Q_EXTRA)
    rng = np.random.default_rng(SEED)
    notes, chords, total, plans = build()
    tm = tempo_map(chords, total)
    vel = V2.velocities(notes, chords)
    # v2 の強さから変えた所：終わりの動機と E♭m6 を少し弱く (♩=66 で間が長くなり、句の入りで 1 秒の音量が 6 dB 上がったため)
    for k, (q, d, m, role, sec) in enumerate(notes):
        if sec == "coda" and q < chords[-2][0] - 1e-9 and role in ("mel", "roll"):
            vel[k] = max(18, vel[k] - (8 if q >= chords[-3][0] - 1e-9 else 4))   # E♭m6 の小節はさらに弱く
    piano = Grand("48k24", hammer=True)
    changes = [tm(b) for b in V2.pedal_changes(chords)]
    final_hold = 6.0
    end_music = tm(total)
    lifts = np.array(sorted([c + 0.035 for c in changes[1:]] + [tm(chords[-2][0]) + final_hold]))

    def sound_end(key_up: float) -> float:
        nxt = lifts[lifts >= key_up]
        return float(nxt[0]) if len(nxt) else key_up

    mel = [n for n in notes if n[3] == "mel"]
    events = []
    for (q, d, m, role, sec), v in zip(notes, vel):
        t = tm(q) + float(np.clip(rng.normal(0, 0.006), -0.016, 0.016))
        if role == "mel":
            t -= 0.010
            nxt = [n[0] for n in mel if n[0] > q + 1e-9]
            key_up = tm(q + d) + (0.03 if nxt and nxt[0] - (q + d) < 1e-9 else -0.02)
        else:
            key_up = tm(q + d) - 0.01
        if role == "acc" and d < 2.0 and sec != "coda":
            t += 0.012 * (m % 3)
        events.append(dict(t=max(0.0, t), q=q, beat_dur=d, m=m, vel=v, role=role, sec=sec,
                           key_up=key_up, sound_end=max(sound_end(key_up), key_up)))

    tail = 2.5
    n = int((max(e["sound_end"] for e in events) + tail) * sr)
    buf = np.zeros((n, 2), dtype=np.float32)
    mel_buf = np.zeros((n, 2), dtype=np.float32)
    for e in events:
        y = piano.strike(e["m"], e["vel"], e["sound_end"] - e["t"], held_s=e["key_up"] - e["t"])
        if e["role"] == "mel":
            y = y * V2.MELODY_VOICING
        i0 = int(e["t"] * sr)
        k = min(len(y), n - i0)
        buf[i0:i0 + k] += y[:k]
        if e["role"] == "mel":
            mel_buf[i0:i0 + k] += y[:k]

    ir = dsp.make_reverb_ir(2.4, rt60=1.5, damp=0.6, predelay=0.018, width=0.7, seed=SEED)
    x = dsp.reverb(buf, ir, mix=0.16, tail=False)[:n]
    x = dsp.shelf(x, 4500.0, -2.0, kind="high")
    x = dsp.highpass(x, 30.0, order=2)
    nf = int(0.3 * sr)
    x[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]

    lufs_raw, tp_raw = dsp.lufs_integrated(x), dsp.true_peak_db(x)
    gain_db = TARGET_LUFS - lufs_raw
    ceiling = CEILING_DBTP
    for _ in range(6):                                    # True Peak が -1.0 dBTP 以下になるまで天井を下げる
        y, lim = lookahead_limiter(x * np.float32(dsp.db2lin(gain_db)), ceiling)
        tp = dsp.true_peak_db(y)
        if tp <= -1.0:
            break
        ceiling -= 0.2
    x = y
    lim.update(ceiling_db=round(ceiling, 2), makeup_gain_db=round(gain_db, 2),
               lufs_before=round(lufs_raw, 2), true_peak_before_db=round(tp_raw, 2))

    acc = [(e["q"], e["beat_dur"], e["m"], e["vel"]) for e in events if e["role"] != "mel"]
    info = dict(
        mel=[(q, d, m, sec) for q, d, m, role, sec in notes if role == "mel"],
        acc=acc, events=events, chords=chords, plans=plans, total_beats=total, end_music_s=end_music,
        limiter=lim, lowest_note=min(m for _, _, m, _ in acc),
        section_times=[(c[3], round(tm(c[0]), 2)) for k, c in enumerate(chords) if k == 0 or chords[k - 1][3] != c[3]],
        onsets=sorted({round(e["t"], 3) for e in events}),
        pedal_changes_s=[round(c, 3) for c in changes], pedal_lifts_s=[round(float(c), 3) for c in lifts],
        samples_used=dict(sorted(piano.used.items())), resample_calls=piano.resample_calls,
        piano_variant=piano.variant, tm=tm,
        melody_vs_rest_db=V2._stem_ratio(mel_buf, buf - mel_buf),
    )
    return x, info
