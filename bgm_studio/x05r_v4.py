"""
x05r v4：オーナーの試聴判定 (2026-11-15) を反映した試作。v3 (x05r_60s、♩=66、変ロ長調) は不合格だった。

オーナーの判定 (原文)
  音色：不合格（理由：副旋律の音が大きい、音色が暗い）／旋律の大きさ：ちょうどよい／テンポ：速く／
  音量：今の版（-14.5）／サビの「o-pen」の1音：一般的な形に直す／明るい気持ちになるように

v3 からの変更 (1 回に変える点は、この判定の項目だけ)
  1. 副旋律を小さく：サビ前半の「旋律の下の 3 度・6 度」(harm) をなくし、後半は 8 弱く。
     伴奏 (acc) も 3 弱く。旋律の大きさ (強さ) は v3 と同じ
  2. 明るく：
     - 調を変ロ長調 → ハ長調 (全体を +2 半音。旋律は出典の +5 半音 = 1913 年版のト長調から +5)
     - 和音を長三和音中心に (Gm7・Cm9・Dm7・終わりの E♭m6 = 同主短調の IV をやめる)。変ロ長調で書き、最後に +2 する
     - 高域を 2 dB 下げていた補正をやめる
     - 伴奏と低音を 4 強く弾く (Salamander は強い段ほど明るい録音)。副旋律は上の 1 のとおり弱めるので、差し引きで小さくなる
  3. テンポ：♩=66 → 84
  4. サビ 7 小節目 (2/4) の「o-pen」の 4 つ目の音：1908/1913 年版の G (ト長調) を、今の一般的な形の B に替える。
     出典の版とは違う 1 音 (Claude による変更、オーナーの指示)。記録に残す
"""

from __future__ import annotations

import numpy as np

from . import dsp
from . import x05r_v2 as V2
from . import x05r_v3 as V3
from .grand import Grand

SLUG = "x05r_60s"
BPM = 84.0
SEED = 10504
SHIFT = 2                                 # 変ロ長調で組み、最後に +2 半音でハ長調にする
KEY = "C major"

INTRO_CH = ["Bbadd9", "F/A", "Bb", "F6"]
VERSE_CH = ["Bbadd9", "Bb6", "Bb/D", "Eb", "Cm7", "F", "F7", "Bb",
            "Bbadd9", "Bb6", "Bb/D", "Eb", "Cm7", "F", "F7", "Bb"]
CHORUS_CH = ["Bb", "Gm7", "Bb", "F/A", "Eb", "Bb", "C7", "F",
             "Bb", "Gm7", "Bb", "Bb7", "Eb", "Bb", "F7", "Bb"]
CODA_CH = ["Bbadd9", "Eb/Bb", "Bb69", "Bb69"]

# サビ 7 小節目 (2/4)：1913 年版 B4 A4 A4 G4 (ト長調) → 今の一般的な形 B4 A4 A4 B4
OPEN_FIX_BAR = 7
OPEN_FIX_G = [("B4", .5), ("A4", .5), ("A4", .5), ("B4", .5)]


def chorus_plan():
    bars = V2.plan_melody(V2.CHORUS_PLAN, V2.CHORUS_1857, 16)
    out = []
    for bar, src, notes in bars:
        if bar == OPEN_FIX_BAR:
            notes = [(V2.nn(n) + V2.TRANSPOSE, d) for n, d in OPEN_FIX_G]
            src = "1913 (4 つ目の音だけ今の一般的な形に変更)"
        out.append((bar, src, notes))
    return out


def build():
    verse = V2.plan_melody(V2.VERSE_PLAN, V2.VERSE_1857, 0)
    chorus = chorus_plan()
    secs = ([("intro", INTRO_CH, V3.intro_melody())] +
            [("verse", VERSE_CH, [b[2] for b in verse])] +
            [("chorus", CHORUS_CH, [b[2] for b in chorus])] +
            [("coda", CODA_CH, V2.CODA_MEL)])
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
    acc = V2.accompaniment(chords, notes)
    # 副旋律を小さく：サビ前半の「旋律の下の音」をなくす (後半は強さで弱める)
    acc = [n for n in acc if not (n[3] == "harm" and n[4] == "chorus" and n[0] < chords[0][0] + 8 + 32 + 16 - 1e-9)]
    notes += acc
    notes.sort(key=lambda n: (n[0], n[2]))
    return notes, chords, t, {"intro": V3.intro_melody(), "verse": verse, "chorus": chorus}


def tempo_map(chords, total):
    rng = np.random.default_rng(SEED + 1)
    f = []
    for s, d, name, sec, i in chords:
        k = 1.0 + float(rng.normal(0, 0.010))
        if sec in ("intro", "verse", "chorus") and i % 4 == 3:
            k *= 1.04
        if sec == "verse" and i == 15:
            k *= 1.05
        if sec == "chorus" and i >= 14:
            k *= 1.0 + 0.07 * (i - 13)
        if sec == "coda":
            k *= (1.10, 1.16, 1.30, 1.30)[i]
        f.append(k)
    beat = 60.0 / BPM
    starts = np.concatenate([[0.0], np.cumsum([2.0 * beat * k for k in f])])

    def tm(q: float) -> float:
        b = min(int(q // 2.0), len(f) - 1)
        return float(starts[b] + (q - 2.0 * b) * beat * f[b])
    return tm


def velocities(notes, chords):
    vel = V2.velocities(notes, chords)
    # 長くのばした旋律の音 (1.5 拍以上) の直後の句の入りは 5 弱く (のばした音が消えかけた所から急に大きくならないように)
    mel = sorted((q, d, k) for k, (q, d, m, role, sec) in enumerate(notes) if role == "mel")
    for (q0, d0, k0), (q1, d1, k1) in zip(mel, mel[1:]):
        if d0 >= 1.5 and notes[k1][4] in ("verse", "chorus"):
            for k, n in enumerate(notes):            # 句の入りの拍で同時に鳴る音 (旋律・低音・副旋律) をすべて 5 弱く
                if abs(n[0] - q1) < 1e-9:
                    vel[k] -= 5
    # 旋律をのばしている間に鳴る伴奏の音は 6 強く (旋律が消えかけて急に静かになる所を、伴奏が少し支える)
    for k, (q, d, m, role, sec) in enumerate(notes):
        if role == "acc" and sec in ("verse", "chorus") and any(q0 < q - 1e-9 and q < q0 + d0 - 1e-9 for q0, d0, _ in mel if d0 >= 1.5):
            vel[k] += 6
    for k, (q, d, m, role, sec) in enumerate(notes):
        if role == "harm":
            vel[k] -= 8                      # 副旋律を弱く
        elif role == "acc":
            vel[k] += 4 - 3                  # 明るい段の録音を使いつつ、音量は少し下げる (下の ACC_GAIN)
        elif role in ("bass", "roll"):
            vel[k] += 4
        if sec == "coda" and q < chords[-2][0] - 1e-9 and role in ("mel", "roll"):
            vel[k] -= 4
        vel[k] = int(np.clip(vel[k], 18, 96))
    return vel


ACC_GAIN = float(dsp.db2lin(-2.0))       # 伴奏・低音・副旋律の音量 (強さは上げて明るい音色、音量は下げる)


def chord_name_shift(name: str) -> str:
    names = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

    def sh(n):
        r = n[0] + (n[1] if n[1:2] in ("#", "b") else "")
        return names[(V2.nn(r + "0") + SHIFT) % 12] + n[len(r):]
    return "/".join(sh(p) for p in name.split("/"))


def gentle_compressor(x: np.ndarray, ratio: float = 2.0, pct: float = 75.0,
                      attack_ms: float = 40.0, release_ms: float = 400.0):
    """
    ゆっくり効くコンプレッサー (句の入りで 1 秒の音量が 6 dB 以上上がるのを和らげる)。
    50 ms ごとの RMS (左右の大きい方) が、曲中の上位 25% の境目 (pct) を超えた分だけ ratio:1 で下げる。
    打鍵の立ち上がりは潰さない (attack 40 ms)。戻りは 400 ms。最大の下げ幅を返す
    """
    B = int(0.05 * dsp.SR)
    nb = len(x) // B
    lv = 20 * np.log10(np.sqrt((x[: nb * B].reshape(nb, B, 2) ** 2).mean(axis=1)).max(axis=1) + 1e-9)
    active = lv[lv > lv.max() - 40]
    thr = float(np.percentile(active, pct))
    want = -(1 - 1 / ratio) * np.maximum(0.0, lv - thr)
    a = np.exp(-50.0 / attack_ms)
    r = np.exp(-50.0 / release_ms)
    g = np.empty_like(want)
    cur = 0.0
    for i, w in enumerate(want):
        cur = cur * a + w * (1 - a) if w < cur else cur * r + w * (1 - r)
        g[i] = cur
    gs = np.interp(np.arange(len(x)), np.arange(nb) * B + B / 2.0, g)
    y = (x * dsp.db2lin(gs)[:, None]).astype(np.float32)
    return y, {"ratio": ratio, "threshold_dbfs_rms_50ms": round(thr, 1), "max_reduction_db": round(float(-g.min()), 2),
               "time_over_1db_s": round(float((g < -1).sum() * 0.05), 2)}


def render(sr: int = dsp.SR, add_layers=None):
    """add_layers(buf, tm, chords) を渡すと、残響の前に別の楽器を足せる (v5 のそり鈴)。None なら v4 と同じ音"""
    assert sr == dsp.SR
    V2._Q.update(V3._Q_EXTRA)
    rng = np.random.default_rng(SEED)
    notes_bb, chords_bb, total, plans = build()
    notes = [(q, d, m + SHIFT, role, sec) for q, d, m, role, sec in notes_bb]
    chords = [(s, d, chord_name_shift(n), sec, i) for s, d, n, sec, i in chords_bb]
    tm = tempo_map(chords, total)
    vel = velocities(notes_bb, chords_bb)
    piano = Grand("48k24", hammer=True)
    changes = [tm(b) for b in V2.pedal_changes(chords)]
    final_hold = 5.0
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
            t += 0.010 * (m % 3)
        events.append(dict(t=max(0.0, t), q=q, beat_dur=d, m=m, vel=v, role=role, sec=sec,
                           key_up=key_up, sound_end=max(sound_end(key_up), key_up)))

    tail = 2.5
    n = int((max(e["sound_end"] for e in events) + tail) * sr)
    buf = np.zeros((n, 2), dtype=np.float32)
    mel_buf = np.zeros((n, 2), dtype=np.float32)
    for e in events:
        y = piano.strike(e["m"], e["vel"], e["sound_end"] - e["t"], held_s=e["key_up"] - e["t"])
        y = y * (V2.MELODY_VOICING if e["role"] == "mel" else ACC_GAIN)
        i0 = int(e["t"] * sr)
        k = min(len(y), n - i0)
        buf[i0:i0 + k] += y[:k]
        if e["role"] == "mel":
            mel_buf[i0:i0 + k] += y[:k]

    layers = add_layers(buf, tm, chords) if add_layers is not None else None
    ir = dsp.make_reverb_ir(2.2, rt60=1.4, damp=0.55, predelay=0.016, width=0.75, seed=SEED)
    x = dsp.reverb(buf, ir, mix=0.15, tail=False)[:n]
    x = dsp.highpass(x, 35.0, order=2)                     # v3 の高域 -2 dB はやめた
    nf = int(0.3 * sr)
    x[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]

    x, comp = gentle_compressor(x)
    lufs_raw, tp_raw = dsp.lufs_integrated(x), dsp.true_peak_db(x)
    gain_db = V3.TARGET_LUFS - lufs_raw
    ceiling = V3.CEILING_DBTP
    for _ in range(6):
        y, lim = V3.lookahead_limiter(x * np.float32(dsp.db2lin(gain_db)), ceiling)
        if dsp.true_peak_db(y) <= -1.0:
            break
        ceiling -= 0.2
    x = y
    lim.update(compressor=comp)
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
        harm_count={"first_half": 0, "second_half": sum(1 for e in events if e["role"] == "harm")},
        layers=layers,
    )
    return x, info
