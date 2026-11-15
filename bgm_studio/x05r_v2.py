"""
x05r_jingle_bells_piano v2：Jingle Bells の静かな読書向けピアノ (試聴用 60〜90 秒)。2026-11-15。

GPT 指示書 §26 (BGM は Claude、画像と映像は GPT) への回答。v1 (2026-11-09、Iowa の mf 1 段階のピアノ) からの変更：
  1. 旋律：§23 の 1857 年所蔵譜 (Levy Collection 062.044) を、ページ・段・小節ごとに採譜した (SOURCE_1857_AB)。
     ヴァースは 1857 年版を基本にし、2 か所だけ 1908/1913 年版 (今の一般的な形と同じ) を使う。
     サビは 1857 年版が別の旋律なので、1908/1913 年版 (SOURCE_1913_G、v1 と同じ読み取り) を使う。
     どの小節をどの版から採ったかは VERSE_PLAN / CHORUS_PLAN と verify_x05r_v2.py の表に出る
  2. 音源：Salamander Grand Piano V3 (Yamaha C5、16 段階の強さ、CC BY 3.0)。grand.py を参照
  3. 演奏：強さを旋律の山と拍で変え、打鍵の時刻を数 ms ずつ揺らし、旋律を伴奏より約 10 ms 先に出す。
     句の終わりで少しゆるめ、最後の 3 小節でゆっくりにする。サステインペダルは和音が変わるたびに踏み替える
  4. 編曲：和音・伴奏はすべて新しく作った (旧 c09・Hardy 版・Rosey の伴奏は使わない)。
     ヴァース前半は「低音＋2 音」の 4 分音符、後半で 8 分音符が加わり、サビは 8 分音符の分散和音と旋律の下の 3 度・6 度
"""

from __future__ import annotations

import numpy as np

from . import dsp
from .grand import Grand
from .xmas_r import SOURCE_1913_G

SLUG = "x05r_jingle_bells_piano_v2"
BPM = 72.0
SEED = 10502
MELODY_VOICING = float(dsp.db2lin(2.0))   # 旋律だけ +2 dB。伴奏はペダルで重なって鳴り続けるので、旋律が埋もれないように
TRANSPOSE = 3                     # ト長調 (1913 年版) → 変ロ長調。1857 年版 (変イ長調) からは +2

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def nn(name: str) -> int:
    pc = _PC[name[0]]
    rest = name[1:]
    while rest[:1] in ("#", "b"):
        pc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + pc


def parse(s: str):
    out = []
    for tok in s.replace("|", " ").split():
        n, d = tok.split("/")
        out.append((None if n == "R" else nn(n), float(d)))
    return out


# ---------------------------------------------------------------------------------------------
# 1857 年版の採譜 (Levy Sheet Music Collection, Box 062 Item 044、J. Pierpont「The One Horse Open Sleigh」
# Boston: Oliver Ditson & Co.、1857、plate 18200)。歌の旋律だけ。変イ長調・2/4 拍子。1 要素 = 1 小節 (2 拍)。
# 音名は実際の高さ (調号の B♭ E♭ A♭ D♭ を反映)。(PDF のページ, 段, 小節, 音, 確かさ, 備考)
# PDF の 2 ページ目 = 印刷のページ 3 (ヴァース)、3〜4 ページ目 = 印刷のページ 4〜5 (サビ、4 声の合唱の最上声)
SOURCE_1857_AB = [
    # ヴァース (印刷 p.3)
    (2, 2, 0, "R/1 R/.5 Eb4/.5", "高", "弱起。上の歌詞「2. A」は 2 番だけの音 (1 番の歌詞は次の小節から)"),
    (2, 2, 1, "Eb4/.5 C5/.5 Bb4/.5 Ab4/.5", "高", "1. Dash-ing thro' the"),
    (2, 2, 2, "Eb4/1 R/.5 Eb4/.25 Eb4/.25", "高", "snow, In a (16 分音符 2 つ)"),
    (2, 2, 3, "Eb4/.5 C5/.5 Bb4/.5 Ab4/.5", "高", "one horse o-pen"),
    (2, 2, 4, "F4/1.5 F4/.5", "高", "sleigh, (付点 4 分と 8 分をスラーで結ぶ)"),
    (2, 2, 5, "F4/.5 Db5/.5 C5/.5 Bb4/.5", "高", "O'er the hills we"),
    (2, 3, 6, "G4/1.5 G4/.5", "高", "go, (スラー)"),
    (2, 3, 7, "G4/.5 F5/.5 Eb5/.5 Db5/.5", "高", "Laugh-ing all the。低い G4 から F5 へ 7 度跳ぶ (今の形とは違う)"),
    (2, 3, 8, "C5/1.5 Eb4/.5", "高", "way; の後の 8 分音符は 2 番の歌詞「The」の音"),
    (2, 3, 9, "Eb4/.5 C5/.5 Bb4/.5 Ab4/.5", "高", "Bells on bob tail"),
    (2, 3, 10, "Eb4/1.5 Eb4/.5", "高", "ring, (スラー)"),
    (2, 3, 11, "Eb4/.5 C5/.5 Bb4/.5 Ab4/.5", "高", "Mak-ing spir-its"),
    (2, 4, 12, "F4/1.5 F4/.5", "高", "bright, (スラー)"),
    (2, 4, 13, "F4/.5 Db5/.5 C5/.5 Bb4/.5", "高", "Oh what sport to"),
    (2, 4, 14, "G4/.5 Eb5/.5 D5/.5 Eb5/.5", "高", "ride and sing A。3 つ目の D に ♮ (D♮5)。今の形 (同じ音を 4 回) とは違う"),
    (2, 4, 15, "F5/.5 Eb5/.5 Db5/.5 Bb4/.5", "高", "sleigh-ing song to"),
    (2, 4, 16, "Ab4/2", "高", "night. (2 分音符・複縦線)"),
    # サビ (印刷 p.4〜5、CHORUS。最上声)
    (3, 1, 1, "C5/.5 C5/.5 C5/1", "高", "Jin-gle bells,"),
    (3, 1, 2, "Eb5/.5 Eb5/.5 Eb5/1", "高", "Jin-gle bells,"),
    (3, 1, 3, "C5/.5 C5/.5 F5/.75 F5/.25", "高", "Jin-gle all the (付点 8 分と 16 分)"),
    (3, 1, 4, "E5/2", "高", "way; (E に ♮。E♮5)"),
    (3, 1, 5, "F5/.5 Db5/.5 Ab4/.5 F5/.5", "中", "Oh! what joy it。3 つ目は A♭4 (第 2 間) と読んだ。400 dpi で確認"),
    (3, 2, 6, "Eb5/.5 C5/.5 Ab4/.5 Ab4/.25 Bb4/.25", "高", "is to ride In a"),
    (3, 2, 7, "C5/.5 Bb4/.5 Ab4/.5 Bb4/.5", "高", "one horse o-pen"),
    (3, 2, 8, "C5/2", "高", "sleigh."),
    (3, 2, 9, "C5/.5 C5/.5 C5/1", "高", "Jin-gle bells,"),
    (3, 2, 10, "Eb5/.5 Eb5/.5 Eb5/1", "高", "Jin-gle bells,"),
    (4, 1, 11, "C5/.5 C5/.5 F5/.5 F5/.5", "高", "Jin-gle all the"),
    (4, 1, 12, "E5/2", "高", "way, (E♮5)"),
    (4, 1, 13, "F4/.5 Db5/.5 C5/.5 Bb4/.5", "高", "Oh! what joy it"),
    (4, 1, 14, "Ab4/.5 Eb5/.5 D5/.5 Eb5/.25 Eb5/.25", "高", "is to ride In a (D に ♮)"),
    (4, 1, 15, "F5/.5 Eb5/.5 Db5/.5 Bb4/.5", "高", "one horse o-pen"),
    (4, 1, 16, "Ab4/1 R/1", "高", "sleigh. (4 分音符と休符・終止線)"),
]
VERSE_1857 = {bar: notes for page, sys_, bar, notes, *_ in SOURCE_1857_AB[:17]}
CHORUS_1857 = {bar: notes for page, sys_, bar, notes, *_ in SOURCE_1857_AB[17:]}


def _1913_halfbars():
    """SOURCE_1913_G (4/4、16 小節) を 2/4 の 32 小節に分ける (前半 16 = ヴァース、後半 16 = サビ)"""
    out, cur, t = [], [], 0.0
    for m, d in parse(SOURCE_1913_G):
        cur.append((m, d))
        t += d
        if abs(t - 2.0) < 1e-9:
            out.append(cur)
            cur, t = [], 0.0
    assert len(out) == 32 and not cur
    return out


H1913 = _1913_halfbars()

# どの版のどの小節を使うか (2/4 の小節ごと)。"1857" は変イ長調 → +2、"1913" はト長調 → +3 で変ロ長調にする
VERSE_PLAN = [
    (1, "1857", "1913 と同じ音"),
    (2, "1857", "1913 は付点 4 分 + 16 分 2 つ。1857 の『4 分・8 分休符・16 分 2 つ』を採る"),
    (3, "1857", "1913 と同じ音"),
    (4, "1857", "1913 は付点 4 分 + 8 分休符。1857 の『付点 4 分 + 8 分の同音』を採る"),
    (5, "1857", "1913 と同じ音"),
    (6, "1857", "1857 は今の形と同じ (ト長調で F#)。1913 は E (今の形と違う)"),
    (7, "1913", "1857 は G4→F5 の 7 度の跳躍で今の形と違う。1913 の『同音 2 つから下がる』形 (今の形と同じ) を採る"),
    (8, "1857", "1913 は付点 4 分 + 8 分休符。1857 の 8 分音符 (2 番の歌詞の音) も弾く"),
    (9, "1857", "1913 と同じ音"),
    (10, "1857", "1913 は付点 4 分 + 8 分休符"),
    (11, "1857", "1913 と同じ音"),
    (12, "1857", "1913 と同じ"),
    (13, "1857", "1913 と同じ音"),
    (14, "1913", "1857 は G4 E♭5 D♮5 E♭5 で今の形と違う。1913 の『同音 4 つ』(今の形と同じ) を採る"),
    (15, "1857", "1913 と同じ音"),
    (16, "1857", "1913 は付点 4 分 + 8 分休符"),
]
CHORUS_PLAN = [(i, "1913", "1857 年版のサビは別の旋律 (CHORUS_1857)。今の形に近い 1908/1913 年版を使う。"
                + ("「o-pen」の 4 つ目は G (今の一般的な形は B)。版のとおり" if i == 7 else ""))
               for i in range(1, 17)]


def plan_melody(plan, base_1857, offset_1913):
    bars = []
    for bar, src, _ in plan:
        if src == "1857":
            notes = [(None if m is None else m + 2, d) for m, d in parse(base_1857[bar])]
        else:
            notes = [(None if m is None else m + TRANSPOSE, d) for m, d in H1913[offset_1913 + bar - 1]]
        assert abs(sum(d for _, d in notes) - 2.0) < 1e-9, (bar, src)
        bars.append((bar, src, notes))
    return bars


# ---------------------------------------------------------------------------------------------
# 和音 (新しく付けたもの)。2/4 の小節 = 2 拍ごとに 1 つ
_Q = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
      "7sus4": (0, 5, 7, 10), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "add9": (0, 4, 7, 2),
      "m9": (0, 3, 7, 10, 2), "9": (0, 4, 7, 10, 2), "maj9": (0, 4, 7, 11, 2), "69": (0, 4, 7, 9, 2)}


def chord(name: str):
    bass = None
    if "/" in name:
        name, b = name.split("/")
        bass = nn(b + "0") % 12
    r = name[0] + (name[1] if name[1:2] in ("#", "b") else "")
    root = nn(r + "0") % 12
    pcs = [(root + i) % 12 for i in _Q[name[len(r):]]]
    return root, (bass if bass is not None else root), pcs


INTRO = ["Bbadd9", "Ebmaj9/Bb", "Cm9", "F7sus4"]
VERSE_CH = ["Bbadd9", "Gm7", "Bb/D", "Cm7", "Cm9", "F", "Eb6", "Dm7",
            "Gm7", "Ebmaj7", "Bb/D", "Cm7", "Cm9", "F7sus4", "F7", "Bb"]
CHORUS_CH = ["Bbmaj7", "Gm7", "Gm7", "Dm7", "Eb6", "Cm9", "Gm7", "F7sus4",
             "Bbmaj7", "D7/F#", "Gm7", "C9", "Eb6", "Cm9", "F7", "Bb"]
# 終わり：最初の動機 (F D C B♭) を 1 オクターブ上で静かに (Gm7) → E♭m6 (同主短調の IV) → B♭ の和音を下から上へ分散。
# 最初は E♭maj7 にしたが、低音 E♭ と旋律 D が半音 (長 7 度) で重なるので Gm7 に替えた
CODA_CH = ["Gm7", "Ebm6", "Bb69", "Bb69"]
CODA_MEL = [[(nn("F5"), .5), (nn("D6"), .5), (nn("C6"), .5), (nn("Bb5"), .5)],
            [(nn("Bb5"), 2.0)], [(None, 2.0)], [(None, 2.0)]]


# ---------------------------------------------------------------------------------------------
def build():
    """拍 (4 分音符) 単位の楽譜。戻り値：notes = [(拍, 長さ, MIDI, 役割, 部分)]、chords = [(拍, 長さ, 名前, 部分)]"""
    verse = plan_melody(VERSE_PLAN, VERSE_1857, 0)
    chorus = plan_melody(CHORUS_PLAN, CHORUS_1857, 16)
    secs = ([("intro", INTRO, [[(None, 2.0)]] * 4)] +
            [("verse", VERSE_CH, [b[2] for b in verse])] +
            [("chorus", CHORUS_CH, [b[2] for b in chorus])] +
            [("coda", CODA_CH, CODA_MEL)])
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
    notes += accompaniment(chords, notes)
    notes.sort(key=lambda n: (n[0], n[2]))
    return notes, chords, t, {"verse": verse, "chorus": chorus}


def _clash(m, pcs):
    return any((m - p) % 12 in (1, 11) for p in pcs)


def accompaniment(chords, notes):
    out = []
    prev_bass = nn("Bb1")
    for s, d, name, sec, i in chords:
        root, bass_pc, pcs = chord(name)
        mel = [n for n in notes if n[0] < s + d and s < n[0] + n[1]]
        mel_pcs = {n[2] % 12 for n in mel}
        top = min((n[2] for n in mel), default=nn("F5"))
        # 低音：前の低音から近い方 (B♭1〜B2)。最初の音は B♭1
        cands = [b for b in range(nn("Bb1"), nn("B2") + 1) if b % 12 == bass_pc]
        bass = min(cands, key=lambda b: (abs(b - prev_bass), b))
        prev_bass = bass
        third = next((p for p in pcs if (p - root) % 12 in (3, 4, 5)), pcs[1])
        fifth = (root + 7) % 12
        seventh = next((p for p in pcs if (p - root) % 12 in (9, 10, 11)), None)
        ninth = next((p for p in pcs if (p - root) % 12 == 2), None)

        def place(pc, lo):
            return lo + (pc - lo) % 12

        tenor_lo = bass + 7 if bass < nn("E2") else bass + 3
        guide = [place(third, tenor_lo)]
        if seventh is not None:
            guide.append(place(seventh, guide[0] + 1))
        else:
            guide.append(place(fifth, guide[0] + 1))
        guide = [g for g in guide if not _clash(g, mel_pcs) and g <= top - 3]
        f5 = bass + 7 if not _clash(bass + 7, mel_pcs) else bass + 12
        ten = place(third, bass + 12) if bass + 12 + 4 <= top - 3 else place(third, bass + 7)
        if _clash(ten, mel_pcs) or ten > top - 3:
            ten = None
        if sec == "intro":
            out.append((s, d, bass, "bass", sec))
            out += [(s + 0.5, d - 0.5, g, "acc", sec) for g in guide]
            if ninth is not None and i % 2 == 0:
                out.append((s + 1.0, d - 1.0, place(ninth, max(guide, default=bass) + 1), "acc", sec))
        elif sec == "verse" and i < 8:
            out.append((s, d, bass, "bass", sec))
            out += [(s + 1.0, d - 1.0, g, "acc", sec) for g in guide]
        elif sec == "verse":
            out.append((s, d, bass, "bass", sec))
            out.append((s + 0.5, d - 0.5, f5, "acc", sec))
            out += [(s + 1.0, d - 1.0, g, "acc", sec) for g in guide]
        elif sec == "chorus":
            out.append((s, d, bass, "bass", sec))
            seq = [f5, ten if ten else f5 + 5, f5]
            for k, m in enumerate(seq):
                if not _clash(m, mel_pcs):
                    out.append((s + 0.5 * (k + 1), d - 0.5 * (k + 1), m, "acc", sec))
            # 旋律の下に 3 度か 6 度 (和音の音で、旋律と半音でぶつからない音)。拍の頭だけ
            for n in [n for n in notes if n[3] == "mel" and s <= n[0] < s + d and abs((n[0] - s) % 1.0) < 1e-9]:
                if i >= 8 or abs(n[0] - s) < 1e-9:
                    h = [n[2] - k for k in (3, 4, 8, 9) if (n[2] - k) % 12 in pcs and not _clash(n[2] - k, mel_pcs)]
                    if h and h[0] > max(guide + [bass + 12]):
                        out.append((n[0], n[1], h[0], "harm", sec))
        else:   # coda：和音をゆっくり下から分散して、そのまま響かせる
            roll = [bass, bass + 7, place(third, bass + 12)] + ([place(seventh, bass + 14)] if seventh is not None else [])
            if name.startswith("Bb69") and i == 2:
                roll = [nn("Bb1"), nn("F2"), nn("D3"), nn("C4"), nn("F4"), nn("G4"), nn("D5")]
            elif name.startswith("Bb69"):
                continue
            roll = [m for m in roll if not _clash(m, mel_pcs)]
            out += [(s + 0.12 * k, (4.0 if i == 2 else d) - 0.12 * k, m, "roll", sec) for k, m in enumerate(roll)]
    return out


# ---------------------------------------------------------------------------------------------
def tempo_map(chords, total):
    """2 拍ごとの速さの係数 (1 より大きいほどゆっくり)。句 (2/4 で 4 小節) の終わりで少しゆるめる"""
    rng = np.random.default_rng(SEED + 1)
    f = []
    for s, d, name, sec, i in chords:
        k = 1.0 + float(rng.normal(0, 0.012))
        if sec in ("verse", "chorus") and i % 4 == 3:
            k *= 1.05
        if sec == "verse" and i == 15:
            k *= 1.06
        if sec == "intro" and i == 3:
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


def velocities(notes, chords):
    """MIDI の強さ (1〜127)。旋律は句の山で強く、句の終わりで弱く。拍の頭を少し強く。伴奏は旋律より 16〜26 弱く"""
    rng = np.random.default_rng(SEED + 2)
    base = {"intro": 44, "verse": 54, "chorus": 59, "coda": 43}
    vel = []
    for q, d, m, role, sec in notes:
        sec_start = min(c[0] for c in chords if c[3] == sec)
        pos = ((q - sec_start) % 8.0) / 8.0                          # 句 (8 拍) の中の位置
        v = base[sec] + 5.0 * np.sin(np.pi * pos)
        if sec == "chorus" and q - sec_start >= 16:
            v += 2.0                                                  # サビの後半を少しだけ大きく
        beat = (q % 4.0)
        v += 3.0 if beat < 1e-9 else 1.0 if abs(beat - 2) < 1e-9 else -2.0 if beat % 1.0 > 1e-9 else 0.0
        if d <= 0.25:
            v -= 3.0
        if role == "mel":
            v += 3.0 + 0.12 * (m - nn("D5"))                          # 旋律を伴奏より前に。高い音は少しだけ強く
        elif role == "harm":
            v -= 20.0
        elif role == "bass":
            v -= 16.0
        elif role == "roll":
            last = q >= chords[-2][0] - 1e-9                          # 最後の和音は、前より大きくならないように弱く
            v = base[sec] - (18.0 if last else 4.0) - 0.6 * (m - nn("Bb1")) / 3.0
        else:
            v -= 26.0
        vel.append(int(np.clip(round(v + rng.normal(0, 2.0)), 18, 90)))
    return vel


def pedal_changes(chords):
    """和音が変わる拍 (同じ和音が続くときは 4 拍ごと)。最後の和音はペダルを踏んだまま"""
    out, prev = [], None
    for s, d, name, sec, i in chords:
        if name != prev or s % 4.0 < 1e-9:
            out.append(s)
        prev = name
    return out


def _stem_ratio(a, b):
    """旋律と、それ以外 (伴奏・低音) の音量差 [dB]。残響を足す前・K 特性の LUFS で測る"""
    la, lb = dsp.lufs_integrated(a), dsp.lufs_integrated(b)
    return {"melody_lufs": round(la, 2), "accompaniment_lufs": round(lb, 2), "melody_minus_accompaniment_db": round(la - lb, 2)}


def render(sr: int = dsp.SR):
    assert sr == dsp.SR
    rng = np.random.default_rng(SEED)
    notes, chords, total, plans = build()
    tm = tempo_map(chords, total)
    vel = velocities(notes, chords)
    piano = Grand()
    changes = [tm(b) for b in pedal_changes(chords)]
    final_hold = 6.0                                      # 最後の和音を 6 秒鳴らしてからペダルを上げる
    end_music = tm(total)
    pedal_up = [c + 0.035 for c in changes[1:]] + [tm(chords[-2][0]) + final_hold]
    lifts = np.array(sorted(pedal_up))

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
            t += 0.012 * (m % 3)                               # 2 音を同時に押すときの、ごくわずかなずれ
        events.append(dict(t=max(0.0, t), q=q, beat_dur=d, m=m, vel=v, role=role, sec=sec,
                           key_up=key_up, sound_end=max(sound_end(key_up), key_up)))

    tail = 2.5                                            # ペダルを上げてから、残響が消えるまで
    n = int((max(e["sound_end"] for e in events) + tail) * sr)
    buf = np.zeros((n, 2), dtype=np.float32)
    mel_buf = np.zeros((n, 2), dtype=np.float32)          # 旋律だけ (旋律と伴奏の音量差を測るため)
    for e in events:
        y = piano.strike(e["m"], e["vel"], e["sound_end"] - e["t"], held_s=e["key_up"] - e["t"])
        if e["role"] == "mel":
            y = y * MELODY_VOICING                         # 旋律に重みをかけて弾く (音色の段は強さで決めたまま、音量だけ少し上げる)
        i0 = int(e["t"] * sr)
        k = min(len(y), n - i0)
        buf[i0:i0 + k] += y[:k]
        if e["role"] == "mel":
            mel_buf[i0:i0 + k] += y[:k]

    dry = buf
    ir = dsp.make_reverb_ir(2.4, rt60=1.5, damp=0.6, predelay=0.018, width=0.7, seed=SEED)
    x = dsp.reverb(dry, ir, mix=0.16, tail=False)[:n]
    x = dsp.shelf(x, 4500.0, -2.0, kind="high")             # 弦の真上で録った明るさを少しだけ抑える
    x = dsp.highpass(x, 30.0, order=2)
    nf = int(0.3 * sr)
    x[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)[:, None]

    # 音量：ピーク (True Peak) が -1 dB を超えない範囲で -14 LUFS に近づける。リミッターで潰さない
    lufs = dsp.lufs_integrated(x)
    tp = dsp.true_peak_db(x)
    gain_db = min(-14.0 - lufs, -1.0 - tp)
    x = (x * dsp.db2lin(gain_db)).astype(np.float32)

    acc = [(e["q"], e["beat_dur"], e["m"], e["vel"]) for e in events if e["role"] != "mel"]
    info = dict(
        mel=[(q, d, m, sec) for q, d, m, role, sec in notes if role == "mel"],
        acc=acc,
        events=events, chords=chords, plans=plans, total_beats=total, end_music_s=end_music,
        gain_db=gain_db, lufs_before_gain=lufs, true_peak_before_gain=tp, limiter="なし (ゲインだけ)",
        lowest_note=min(m for _, _, m, _ in acc),
        section_times=[(c[3], round(tm(c[0]), 2)) for k, c in enumerate(chords) if k == 0 or chords[k - 1][3] != c[3]],
        onsets=sorted({round(e["t"], 3) for e in events}),
        pedal_changes_s=[round(c, 3) for c in changes], pedal_lifts_s=[round(float(c), 3) for c in lifts],
        samples_used=dict(sorted(piano.used.items())),
        tm=tm,
        melody_vs_rest_db=_stem_ratio(mel_buf, buf - mel_buf),
    )
    return x, info
