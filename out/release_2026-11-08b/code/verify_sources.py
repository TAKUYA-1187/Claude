#!/usr/bin/env python3
"""
権利表の「照合結果」を、保存した譜面から計算し直す (2026-11-08)。

    python3 verify_sources.py --out <フォルダ>

制作データ (bgm_studio/nursery.py の旋律 tune と和音 chords) を、data/licenses/ に保存した譜面すべてと比べる。
- 旋律: 隣り合う 2 音の「音の高さの差 (半音)」と「長さの比」の列を作り、difflib.SequenceMatcher の一致率を出す
  (調と、全体の速さが違っても比べられる)。「音の高さの動きだけ」の一致率も出す
- 和音: 譜面に和音記号があるときは、旋律の最初の音で調をそろえて abc_import.to_song で C 長調 (A 短調) の
  1 小節ごとの和音名にし、制作データの和音と一致率を出す
出力: source_match.csv (全曲)、silent_night_alignment.md (Silent Night の 1 音ずつの対応表)、silent_night_production.json
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import abc_import as AI                                    # noqa: E402
from bgm_studio.nursery import NURSERY, parse_tune         # noqa: E402
from bgm_studio.jazz import score as midi_score, skyline   # noqa: E402

LIC = ROOT / "data" / "licenses"
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def load_sources():
    """[(ファイル, 番号, 題名, [(音, 長さ)], ABC の本文 or None)]"""
    out = []
    for f in sorted(LIC.rglob("*.abc")):
        text = f.read_text(encoding="latin-1")
        for b in re.split(r"\n(?=X:)", text):
            if not re.match(r"X:\s*\d+", b):
                continue
            try:
                p = AI.parse(b)
            except Exception:
                continue
            notes = [(m, float(d)) for m, d in p["notes"] if m is not None]
            if len(notes) > 8:
                out.append((str(f.relative_to(ROOT)), re.match(r"X:\s*(\d+)", b).group(1), p["title"], notes, b))
    for f in sorted(LIC.rglob("*.mid")):
        notes, _ = midi_score(f)
        for t in sorted({n[0] for n in notes}):
            sk = skyline(notes, t)
            if len(sk) > 20:
                out.append((str(f.relative_to(ROOT)), f"track{t}", f.stem, [(m, e - s) for s, e, m in sk], None))
    return out


def seq(n, with_dur=True):
    return [((b[0] - a[0]), round(b[1] / a[1], 3)) if with_dur else (b[0] - a[0]) for a, b in zip(n, n[1:])]


def ratio(a, b, with_dur=True) -> float:
    return difflib.SequenceMatcher(None, seq(a, with_dur), seq(b, with_dur), autojunk=False).ratio()


def ours(key):
    return [(m, d) for m, d in parse_tune(NURSERY[key]["tune"]) if m is not None]


def chord_match(key, abc_block):
    if not abc_block:
        return None
    p = AI.parse(abc_block)
    if not p["chords"]:
        return None
    src = [m for m, d in p["notes"] if m is not None]
    shift = ours(key)[0][0] - src[0]
    s = AI.to_song(abc_block, shift)
    a, c = NURSERY[key].get("chords", "").split(), s["chords"].split()
    return round(difflib.SequenceMatcher(None, a, c, autojunk=False).ratio(), 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    srcs = load_sources()
    keys = [k for k in NURSERY if re.match(r"(c\d\d|d0[2-7]|n08|n10)_", k)]
    rows = [["制作データ", "曲名", "音の数", "1 位の譜面", "番号", "題名", "音高+長さの一致率", "音高の動きだけの一致率",
             "和音記号の一致率", "2 位の譜面", "2 位の一致率"]]
    for k in keys:
        mine = ours(k)
        ranked = sorted(srcs, key=lambda s: -ratio(mine, s[3]))
        b1, b2 = ranked[0], ranked[1]
        rows.append([k, NURSERY[k]["title"], len(mine), b1[0], b1[1], b1[2], round(ratio(mine, b1[3]), 3),
                     round(ratio(mine, b1[3], False), 3), chord_match(k, b1[4]), f"{b2[0]} {b2[1]}",
                     round(ratio(mine, b2[3]), 3)])
    with open(a.out / "source_match.csv", "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)

    # ── Silent Night：制作データと Mutopia 1295 の 1 音ずつの対応 ──
    sn = ours("n08_silent_night_lullaby")
    mut = next(s for s in srcs if "1295" in s[0] and s[1] == "track1")
    sm = difflib.SequenceMatcher(None, seq(sn, False), seq(mut[3], False), autojunk=False)
    lines = ["# Silent Night：制作データと Mutopia 1295（Public Domain）の 1 音ずつの対応\n",
             f"- 制作データ：`bgm_studio/nursery.py` の `n08_silent_night_lullaby`（{len(sn)} 音）",
             f"- 照合した版：`{mut[0]}` の旋律トラック（{len(mut[3])} 音）",
             f"- 音の高さの動きの一致率：{ratio(sn, mut[3], False):.3f}、長さを含めた一致率：{ratio(sn, mut[3]):.3f}",
             f"- 調の違い：制作データは {NAMES[sn[0][0] % 12]} から、Mutopia は {NAMES[mut[3][0][0] % 12]} から始まる"
             f"（{(sn[0][0] - mut[3][0][0]) % 12} 半音の移調。比較は音の高さの差で行うので影響しない）\n",
             "| # | 制作の音 | 制作の長さ（拍） | Mutopia の音 | Mutopia の長さ（拍） | 音の高さの動き | 長さの比 |",
             "|---|---|---|---|---|---|---|"]
    shift = sn[0][0] - mut[3][0][0]
    for i, ((m1, d1), (m2, d2)) in enumerate(zip(sn, mut[3])):
        nm = lambda m: NAMES[m % 12] + str(m // 12 - 1)
        same_step = "—" if i == 0 else ("一致" if (sn[i][0] - sn[i - 1][0]) == (mut[3][i][0] - mut[3][i - 1][0]) else "違う")
        lines.append(f"| {i + 1} | {nm(m1)} | {d1:g} | {nm(m2 + shift)}（原調 {nm(m2)}） | {d2:g} | {same_step} | "
                     f"{d1 / d2:.2f} |")
    diffs = [op for op in sm.get_opcodes() if op[0] != "equal"]
    lines.append(f"\n音の高さの動きで違う所：{len(diffs)} か所")
    lines.append("\n長さの比が 1 でない所は、楽譜の書き方（拍の単位）の違い。制作データは 1 拍 = 8 分音符で書いている")
    (a.out / "silent_night_alignment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    hist = subprocess.run(["git", "log", "--format=%h %ad %s", "--date=iso", "-L",
                           '/"n08_silent_night_lullaby": dict(/,+14:bgm_studio/nursery.py', "--no-patch"],
                          capture_output=True, text=True, cwd=ROOT).stdout.strip().splitlines()
    (a.out / "silent_night_production.json").write_text(json.dumps({
        "production_id": "n08_silent_night_lullaby（x06 と x04 の 1 曲目、関連 Shorts で使用）",
        "source_file": "bgm_studio/nursery.py",
        "title": NURSERY["n08_silent_night_lullaby"]["title"],
        "bar_beats": NURSERY["n08_silent_night_lullaby"]["bar"],
        "tune_as_used": NURSERY["n08_silent_night_lullaby"]["tune"],
        "chords_as_used": NURSERY["n08_silent_night_lullaby"]["chords"],
        "git_history_of_this_entry": hist,
        "how_it_was_made": "2026-10-23 に Claude が手で入力。入力時に参照した譜面の記録はない（作業記録にも出典 URL がない）",
        "what_the_match_shows": "旋律が、パブリックドメインの讃美歌の形（Mutopia 1295）と同じであること",
        "what_the_match_does_not_show": "入力時に他の版・編曲を一度も見なかったこと（記録がないので証明できない）",
        "chords": "C・F・G・G7 だけの 1 小節ごとの和音（手で付けた）。特定の版の和音記号と照合する対象はない",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print((a.out / "source_match.csv").read_text(encoding="utf-8-sig"))
    print("\n".join(lines[:6]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
