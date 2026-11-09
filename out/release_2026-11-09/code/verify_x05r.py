#!/usr/bin/env python3
"""
x05r_jingle_bells_piano の出典と独立性の確認。2026-11-09。

    python3 verify_x05r.py --out <フォルダ>

1. 旋律：制作データ (bgm_studio/xmas_r.py の X05R) が、1913 年版から読み取った旋律 (SOURCE_1913_G) を
   +3 半音 移しただけであること (音の高さ・長さとも 1 音ずつ一致)
2. 和音：新しく付けた和音が、旧版 c09 (Paul Hardy 版の和音記号) と、どれだけ違うか
   (同じ調・同じ小節割りにそろえて比べる。旋律の同じ所に置いた和音名の一致率)
3. 保存した出典ファイルの sha256
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bgm_studio.nursery import NURSERY, parse_tune      # noqa: E402
from bgm_studio.piano_piece import score                 # noqa: E402
from bgm_studio.xmas_r import X05R, SOURCE_1913_G        # noqa: E402
from bgm_studio.orig01 import chord                       # noqa: E402

NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def chord_at(chs, t):
    for s, d, name, _ in chs:
        if s <= t < s + d:
            return name
    return None


def root_quality(name: str, shift: int) -> str:
    """和音名を、根音を shift 半音動かした「根音+種類」にそろえる (分数和音の低音は無視)"""
    base = name.split("/")[0]
    r = base[0] + (base[1] if len(base) > 1 and base[1] in "#b" else "")
    q = base[len(r):]
    pc = (chord(r)[0] + shift) % 12
    return NAMES[pc] + q


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    mel, chs, total = score(X05R)
    body = [(s, d, m) for s, d, m, sec in mel if sec in ("verse", "chorus")]
    src = [(m, d) for m, d in parse_tune(SOURCE_1913_G) if m is not None]
    same = len(body) == len(src) and all(m - sm == 3 and abs(d - sd) < 1e-9 for (_, d, m), (sm, sd) in zip(body, src))

    # 旧版 c09 (Hardy 由来) の和音を、x05r と同じ拍の位置で比べる。
    # c09 は C 長調・前奏の歌 (Dashing...) から始まる 32 小節 (4/4)。x05r は B♭ 長調・前奏 2 小節の後にヴァース 8 小節
    # (1 小節 = c09 の 2 小節分の長さ…ではなく、x05r は 4/4 で 8 分音符単位、c09 も 4/4 で 4 分音符単位なので、
    #  x05r の 1 拍 = c09 の 2 拍)。旋律の同じ音の上の和音を比べる
    c09 = NURSERY["c09_jingle_bells_full"]
    c09_mel = parse_tune(c09["tune"])
    from bgm_studio.nursery import chords_from_spec
    c09_chs = [(s, d, n, "") for s, d, n in chords_from_spec(c09["chords"], 4)]
    t, c09_notes = 0.0, []
    for m, d in c09_mel:
        if m is not None:
            c09_notes.append((t, m))
        t += d
    # 旋律の音の並びで対応をとる (x05r の旋律 → c09 の旋律、音の高さの差の列で合わせる)
    a_seq = [b[2] - a_[2] for a_, b in zip(body, body[1:])]
    b_seq = [b[1] - a_[1] for a_, b in zip(c09_notes, c09_notes[1:])]
    sm = difflib.SequenceMatcher(None, a_seq, b_seq, autojunk=False)
    pairs = set()
    for blk in sm.get_matching_blocks():
        for k in range(blk.size + 1 if blk.size else 0):   # 差の列の一致 n 個 = 音 n+1 個の一致
            i, j = blk.a + k, blk.b + k
            if i < len(body) and j < len(c09_notes):
                pairs.add((i, j))
    seen, uniq = set(), []
    for i, j in sorted(pairs):          # 1 つの音が 2 か所に対応したら、先の方だけ使う
        if i not in seen:
            seen.add(i)
            uniq.append((i, j))
    pairs = uniq
    same_chord = same_root = 0
    rows = []
    for i, j in pairs:
        ours = chord_at(chs, body[i][0])
        theirs = chord_at(c09_chs, c09_notes[j][0])
        if ours is None or theirs is None:
            continue
        o, h = root_quality(ours, 2), root_quality(theirs, 0)   # B♭ → C は +2 半音
        rows.append((round(body[i][0], 2), o, h))
        same_chord += int(o == h)
        same_root += int(chord(o.replace("maj7", "").replace("m7", "m").replace("m6", "m").replace("7sus4", "")
                               .replace("7", "").replace("6", ""))[0] == chord(h.replace("7", ""))[0])
    files = {}
    for p in sorted((ROOT / "data" / "licenses" / "x05r_jingle_bells").rglob("*")):
        if p.is_file():
            files[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    res = {
        "melody_equals_1913_source_transposed_plus3": same,
        "melody_notes_compared": len(src),
        "melody_vs_old_c09_pitch_steps_ratio": round(sm.ratio(), 3),
        "chord_comparison_vs_old_c09": {
            "method": "旋律の音高の動きで x05r と旧 c09 の音を対応させ、それぞれの音の上で鳴る和音を C 長調の『根音+種類』にそろえて比べた（分数和音の低音は無視）",
            "melody_notes_aligned": len(rows),
            "same_chord_at_aligned_notes": same_chord,
            "same_ratio": round(same_chord / max(1, len(rows)), 3),
            "same_root_at_aligned_notes": same_root,
            "same_root_ratio": round(same_root / max(1, len(rows)), 3),
            "root_note": "根音だけ同じ（種類は違ってもよい）の割合。主和音・属和音など、どの編曲でも重なりやすい所を含む",
            "note": "旧 c09 の和音は Paul Hardy 版の和音記号そのもの。x05r は 7 の和音・maj7・m7 などの 4 和音で付け直した",
            "first_20_pairs_(beat, x05r_in_C, c09)": rows[:20],
        },
        "source_files_sha256": files,
    }
    (a.out / "x05r_verification.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "source_files_sha256"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
