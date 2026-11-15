#!/usr/bin/env python3
"""
x05r_jingle_bells_piano_v2 の出典・独立性・音程の確認。2026-11-15。

    PYTHONHASHSEED=0 python3 verify_x05r_v2.py --out <フォルダ>

1. 旋律：制作データ (x05r_v2.build) の旋律を、2/4 の小節ごとに、採譜の文字列 (1857 年版 +2 半音 /
   1913 年版 +3 半音) を別の読み取り関数 (nursery.parse_tune) で読んだものと 1 音ずつ比べる
2. 和音：旧 c09 (Paul Hardy 版の和音記号) と、旋律の同じ音の上で比べた一致率 (verify_x05r.py と同じ方法)
3. 音程：ピアノ音源の単音 (A4・B♭4・D5・F5、強さ 40 と 62) を FFT で測る
4. ハッシュ：出典の PDF・画像、ピアノ音源のアーカイブ、ライセンス資料
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio import dsp, grand                              # noqa: E402
from bgm_studio import x05r_v2 as X                             # noqa: E402
from bgm_studio.nursery import NURSERY, parse_tune, chords_from_spec   # noqa: E402
from bgm_studio.xmas_r import SOURCE_1913_G                     # noqa: E402

NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def halfbars(notes):
    out, cur, t = [], [], 0.0
    for m, d in notes:
        cur.append((m, d))
        t += d
        if abs(t - 2.0) < 1e-9:
            out.append(cur)
            cur, t = [], 0.0
    return out


def expected():
    """採譜の文字列だけから、使うはずの旋律を作る (x05r_v2 の plan_melody を通さない)"""
    v1857 = {bar: parse_tune(notes) for _, _, bar, notes, *_ in X.SOURCE_1857_AB[:17]}
    h1913 = halfbars(parse_tune(SOURCE_1913_G))
    out = []
    for part, plan, off in (("verse", X.VERSE_PLAN, 0), ("chorus", X.CHORUS_PLAN, 16)):
        for bar, src, _ in plan:
            if src == "1857":
                ns = [(m + 2 if m is not None else None, d) for m, d in v1857[bar]]
            else:
                ns = [(m + 3 if m is not None else None, d) for m, d in h1913[off + bar - 1]]
            out.append((part, bar, src, [(m, d) for m, d in ns]))
    return out


def produced(notes, chords):
    """制作データの旋律を、2 拍ごとに切り分ける (休符も入れる)"""
    mel = [(q, d, m) for q, d, m, role, sec in notes if role == "mel" and sec in ("verse", "chorus")]
    out = []
    for s, d, name, sec, i in chords:
        if sec not in ("verse", "chorus"):
            continue
        ns, t = [], s
        for q, dd, m in [n for n in mel if s - 1e-9 <= n[0] < s + d - 1e-9]:
            if q > t + 1e-9:
                ns.append((None, q - t))
            ns.append((m, dd))
            t = q + dd
        if t < s + d - 1e-9:
            ns.append((None, s + d - t))
        out.append(ns)
    return out


def norm(ns):
    """連続する休符をまとめる (休符の書き方の違いは比べない)"""
    out = []
    for m, d in ns:
        if m is None and out and out[-1][0] is None:
            out[-1] = (None, out[-1][1] + d)
        else:
            out.append((m, round(d, 6)))
    return out


def f0_cents(x, m):
    x = x.mean(1)[int(0.15 * dsp.SR):int(0.15 * dsp.SR) + 32768].astype(np.float64)
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x)), 8 * len(x)))
    f = np.fft.rfftfreq(8 * len(x), 1 / dsp.SR)
    t = 440 * 2 ** ((m - 69) / 12)
    sel = (f > t * 2 ** (-2 / 12)) & (f < t * 2 ** (1 / 12))
    i = int(np.argmax(sp * sel))
    a, b, c = np.log(sp[i - 1:i + 2] + 1e-20)
    p = 0.5 * (a - c) / (a - 2 * b + c)
    fr = (i + p) * (f[1] - f[0])
    return fr, 1200 * np.log2(fr / t)


def rootq(name, shift):
    root, bass, pcs = X.chord(name.split("/")[0])
    rel = tuple(sorted((p - root) % 12 for p in pcs))
    minor = 3 in rel and 4 not in rel
    return NAMES[(root + shift) % 12], ("m" if minor else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    dsp.set_tuning(440.0)

    notes, chords, total, _ = X.build()
    exp, got = expected(), produced(notes, chords)
    rows, ok = [], True
    for (part, bar, src, e), g in zip(exp, got):
        same = norm(e) == norm(g)
        ok &= same
        rows.append({"part": part, "bar_2_4": bar, "source": src, "same": same})
    n1857 = sum(len([m for m, _ in e if m is not None]) for _, _, s, e in exp if s == "1857")
    n1913 = sum(len([m for m, _ in e if m is not None]) for _, _, s, e in exp if s == "1913")

    # 旧 c09 との和音の比較 (旋律の音高の動きで音を対応させる)
    body = [(q, m) for q, d, m, role, sec in notes if role == "mel" and sec in ("verse", "chorus")]
    c09 = NURSERY["c09_jingle_bells_full"]
    t, c09_notes = 0.0, []
    for m, d in parse_tune(c09["tune"]):
        if m is not None:
            c09_notes.append((t, m))
        t += d
    c09_chs = list(chords_from_spec(c09["chords"], 4))
    a_seq = [b[1] - x[1] for x, b in zip(body, body[1:])]
    b_seq = [b[1] - x[1] for x, b in zip(c09_notes, c09_notes[1:])]
    sm = difflib.SequenceMatcher(None, a_seq, b_seq, autojunk=False)
    pairs, seen = [], set()
    for blk in sm.get_matching_blocks():
        for k in range(blk.size + 1 if blk.size else 0):
            i, j = blk.a + k, blk.b + k
            if i < len(body) and j < len(c09_notes) and i not in seen:
                seen.add(i)
                pairs.append((i, j))
    same_chord = same_root = n_cmp = 0
    for i, j in pairs:
        ours = next((c[2] for c in chords if c[0] <= body[i][0] < c[0] + c[1]), None)
        theirs = next((n for s, d, n in c09_chs if s <= c09_notes[j][0] < s + d), None)
        if ours is None or theirs is None:
            continue
        n_cmp += 1
        o = rootq(ours, 2)                                     # B♭ → C
        h_root = theirs[0] + (theirs[1] if theirs[1:2] in ("#", "b") else "")
        h_q = "m" if theirs[len(h_root):].startswith("m") and not theirs[len(h_root):].startswith("maj") else ""
        h_pc = X.nn(h_root + "0") % 12
        same_root += int(NAMES.index(o[0]) == h_pc)
        same_chord += int(NAMES.index(o[0]) == h_pc and o[1] == h_q)

    # 音程
    piano = grand.Grand()
    pitch = []
    for m in (X.nn("A4"), X.nn("Bb4"), X.nn("D5"), X.nn("F5"), X.nn("Bb2")):
        for v in (40, 62):
            fr, c = f0_cents(piano.strike(m, v, 3.0), m)
            pitch.append({"note": m, "velocity": v, "expected_hz": round(440 * 2 ** ((m - 69) / 12), 3),
                          "measured_hz": round(fr, 3), "cents": round(c, 2)})

    files = {}
    for base in (ROOT / "data" / "licenses" / "x05r_jingle_bells", ROOT / "data" / "licenses" / "salamander_grand_piano_v3"):
        for p in sorted(base.rglob("*")):
            if p.is_file():
                files[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    arch = grand.SAL_DIR.parent / "SalamanderGrandPianoV3_44khz16bit.tar.xz"
    files["samples/salamander_raw/SalamanderGrandPianoV3_44khz16bit.tar.xz (git には入れない)"] = (
        hashlib.sha256(arch.read_bytes()).hexdigest() if arch.exists() else "未取得")

    res = {
        "melody_matches_sources_bar_by_bar": ok,
        "melody_bars": rows,
        "melody_notes_from_1857": n1857,
        "melody_notes_from_1913": n1913,
        "chord_comparison_vs_old_c09": {
            "method": "旋律の音高の動きで v2 と旧 c09 の音を対応させ、それぞれの音の上の和音を C 長調の根音と長短でそろえて比べた",
            "aligned_notes": n_cmp, "same_root_and_major_minor": same_chord,
            "same_ratio": round(same_chord / max(1, n_cmp), 3),
            "same_root": same_root, "same_root_ratio": round(same_root / max(1, n_cmp), 3),
            "note": "根音だけの一致は、主和音・属和音など、どの編曲でも重なりやすい所を含む。旧 c09 の和音は Paul Hardy 版の和音記号",
        },
        "piano_single_note_pitch": pitch,
        "files_sha256": files,
    }
    (a.out / "x05r_v2_verification.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("files_sha256", "melody_bars")}, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
