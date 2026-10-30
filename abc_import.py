#!/usr/bin/env python3
"""
ABC 記譜 (楽譜のテキスト形式) から、童謡エンジン (bgm_studio/nursery.py) の旋律と和音を作る。

なぜ: 2026-10-30 にクリスマス曲を一度に 13 曲足すことになった。1 音ずつ手で書き写すと
写し間違いが起きる。パブリックドメインの曲集 (Paul Hardy's Xmas Tunebook など) は
旋律と和音記号が ABC で公開されているので、それを機械的に読んで C 長調 (短調は A 短調) に移す。

対応している記法: 調号 (K:)、臨時記号 (^ _ =, 小節内で持続)、オクターブ (, ')、
音価 (A2 A/2 A3/2 A/)、付点のつなぎ (> <)、タイ (-)、休符 (z)、3 連符 ((3)、
反復 (|: :| ::) と 1・2 番かっこ ([1 [2)、和音記号 ("G" "D7" "F#m")。
装飾 (!..!)、前打音 ({..})、スラー、注釈 ("^..") は読み飛ばす。

    python3 abc_import.py tunebook.abc 4001 --shift 5
    → NURSERY に貼れる tune= と chords= を表示する
"""

from __future__ import annotations

import argparse
import re
from fractions import Fraction

_LETTERS = "CDEFGAB"
_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
# 長調の主音 → 調号 (シャープは +1, フラットは -1)
_SHARPS = "FCGDAEB"
_MAJOR_SIG = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6,
              "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5}
_RELATIVE_MAJOR = {"Am": "C", "Em": "G", "Bm": "D", "F#m": "A", "C#m": "E",
                   "Dm": "F", "Gm": "Bb", "Cm": "Eb", "Fm": "Ab"}


def _key_signature(k: str) -> dict[str, int]:
    k = k.strip().split()[0]
    k = k.replace("min", "m")
    major = _RELATIVE_MAJOR.get(k, k.removesuffix("maj"))
    n = _MAJOR_SIG[major]
    sig = {}
    if n > 0:
        for l in _SHARPS[:n]:
            sig[l] = 1
    else:
        for l in reversed(_SHARPS):
            if len(sig) >= -n:
                break
            sig[l] = -1
    return sig


def _dur(s: str) -> Fraction:
    """'' '2' '/2' '/' '3/2' → 単位音価の何倍か"""
    if not s:
        return Fraction(1)
    if "/" in s:
        num, _, den = s.partition("/")
        num = int(num) if num else 1
        den = int(den) if den else 2
        return Fraction(num, den)
    return Fraction(int(s))


_TOKEN = re.compile(r"""
    (?P<chord>"[^"]*")
  | (?P<deco>![^!]*!|\+[^+]*\+)
  | (?P<grace>\{[^}]*\})
  | (?P<field>\[[A-Za-z]:[^\]]*\])
  | (?P<bar>:\|\]|:\|\||\|\]|\[\||\|\||:\|:|::|:\||\|:|\|)
  | (?P<ending>\[?[12](?=[^/\d]|$))
  | (?P<tuplet>\(\d)
  | (?P<note>(?:\^\^|\^|__|_|=)?[A-Ga-g][,']*(?:\d+)?(?:/+\d*)?)
  | (?P<rest>[zx](?:\d+)?(?:/+\d*)?)
  | (?P<tie>-)
  | (?P<broken>[<>]+)
  | (?P<skip>[\s().\\~HLMOPSTuv`]|\$)
""", re.X)


def parse(abc: str) -> dict:
    """ABC 1 曲 → 拍子・単位・音の列 (反復は展開済み)・和音の列"""
    head, body = {}, []
    for line in abc.splitlines():
        line = line.split("%")[0].rstrip()
        m = re.match(r"^([A-Za-z]):(.*)$", line)
        if m and not body and m.group(1) != "|":
            head[m.group(1)] = m.group(2).strip()
            continue
        if m and m.group(1) in "WwNZSBOAHRCDFQTXP":
            continue
        if line:
            body.append(line)
    meter = head.get("M", "4/4").replace("C|", "2/2").replace("C", "4/4")
    mn, md = (int(v) for v in meter.split("/"))
    unit = Fraction(head.get("L", "1/8"))
    sig = _key_signature(head.get("K", "C"))

    # 1) 字句を読んで、反復記号と終わりかっこを含む出来事の列にする
    ev: list[tuple] = []
    text = " ".join(body)
    pos, local_acc, tuplet = 0, {}, 0
    broken = None
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"読めない記号: {text[pos:pos + 20]!r}")
        pos = m.end()
        kind, tok = m.lastgroup, m.group()
        if kind in ("deco", "grace", "field", "skip"):
            continue
        if kind == "chord":
            name = tok.strip('"')
            if name and name[0] in _LETTERS:
                ev.append(("chord", name.split("/")[0]))
            continue
        if kind == "bar":
            local_acc = {}
            ev.append(("bar", tok))
            continue
        if kind == "ending":
            ev.append(("ending", int(tok.lstrip("["))))
            continue
        if kind == "tuplet":
            tuplet = int(tok[1:])
            continue
        if kind == "tie":
            ev.append(("tie",))
            continue
        if kind == "broken":
            broken = tok
            continue
        if kind in ("note", "rest"):
            if kind == "rest":
                d = _dur(tok[1:])
                midi = None
            else:
                mm = re.match(r"(\^\^|\^|__|_|=)?([A-Ga-g])([,']*)(.*)", tok)
                acc, letter, octs, dstr = mm.groups()
                up = letter.upper()
                octave = 4 if letter.isupper() else 5
                octave += octs.count("'") - octs.count(",")
                key = (up, octave)
                if acc:
                    local_acc[key] = {"^^": 2, "^": 1, "__": -2, "_": -1, "=": 0}[acc]
                alter = local_acc.get(key, sig.get(up, 0))
                midi = 12 * (octave + 1) + _PC[up] + alter
                d = _dur(dstr)
            if tuplet:
                d = d * Fraction(2, 3) if tuplet == 3 else d * Fraction(tuplet - 1, tuplet)
                tuplet = tuplet - 1 if tuplet > 1 else 0
                tuplet = 0 if tuplet == 1 else tuplet
            if broken:
                # 直前の音と組で長さを分け合う (> は前が付点)
                k = len(broken)
                frac = 1 - Fraction(1, 2 ** k)
                for j in range(len(ev) - 1, -1, -1):
                    if ev[j][0] == "note":
                        n0 = ev[j]
                        ev[j] = ("note", n0[1], n0[2] * (1 + frac) if broken[0] == ">" else n0[2] * (1 - frac))
                        break
                d = d * (1 - frac) if broken[0] == ">" else d * (1 + frac)
                broken = None
            ev.append(("note", midi, d))
            continue

    # 2) 反復を展開する
    flat: list[tuple] = []
    i, start, second, done = 0, 0, False, set()
    while i < len(ev):
        e = ev[i]
        if e[0] == "bar" and e[1] in ("|:", "[|"):
            start, second = i + 1, False
        elif e[0] == "bar" and e[1] in (":|", ":|]", ":||", ":|:", "::"):
            if i not in done:
                done.add(i)
                i, second = start, True
                continue
            second = False
            start = i + 1
        elif e[0] == "ending" and e[1] == 1 and second:
            # 2 回目は 1 番かっこを飛ばして 2 番へ
            j = i + 1
            while j < len(ev) and not (ev[j][0] == "ending" and ev[j][1] == 2):
                j += 1
            i = j
            continue
        flat.append(e)
        i += 1

    # 3) 音価を 4 分音符 = 1 の単位にし、タイをつなぐ
    q = unit * 4
    notes: list[list] = []
    chords: list[tuple[Fraction, str]] = []
    t = Fraction(0)
    first_bar = None
    tie_next = False
    for e in flat:
        if e[0] == "chord":
            chords.append((t, e[1]))
        elif e[0] == "bar" and first_bar is None and t > 0:
            first_bar = t
        elif e[0] == "tie":
            tie_next = True
        elif e[0] == "note":
            d = e[2] * q
            if tie_next and notes and notes[-1][0] == e[1]:
                notes[-1][1] += d
            else:
                notes.append([e[1], d])
            tie_next = False
            t += d
    bar = Fraction(mn * 4, md)
    return dict(bar=bar, notes=notes, chords=chords, first_bar=first_bar or bar,
                title=head.get("T", ""), key=head.get("K", "C"))


def _chord_name(name: str, shift: int) -> str:
    m = re.match(r"([A-G])([#b]?)(.*)", name)
    root = (_PC[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)] + shift) % 12
    return _NAMES[root] + m.group(3)


def to_song(abc: str, shift: int) -> dict:
    """shift 半音だけ移した tune / chords の文字列と bar を返す"""
    p = parse(abc)
    bar, notes = p["bar"], [list(n) for n in p["notes"]]
    pick = p["first_bar"] % bar
    pad = (bar - pick) % bar
    if pad:
        notes.insert(0, [None, pad])
    total = sum(d for _, d in notes)
    tail = (-total) % bar
    if tail:
        notes.append([None, tail])
        total += tail
    toks = []
    for m, d in notes:
        name = "R" if m is None else (lambda x: _NAMES[x % 12] + str(x // 12 - 1))(m + shift)
        ds = format(float(d), "g")
        toks.append(f"{name}/{ds}")

    # 和音: 各小節を、和音の変わり目がすべて乗るいちばん粗い等分にする
    ch = [(t + pad, _chord_name(n, shift)) for t, n in p["chords"]]
    first = ch[0][1] if ch else "C"

    def at(time):
        cur = first
        for tt, n in ch:
            if tt <= time:
                cur = n
        return cur

    bars = []
    nb = int(total / bar)
    for b in range(nb):
        b0 = b * bar
        changes = [tt - b0 for tt, _ in ch if b0 < tt < b0 + bar]
        for parts in (1, 2, 3, 4, 6, 8, 12):
            g = bar / parts
            if all((c / g).denominator == 1 for c in changes):
                break
        cells = [at(b0 + k * bar / parts) for k in range(parts)]
        if len(set(cells)) == 1:
            bars.append(cells[0])
        elif parts == 4 and cells[0] == cells[1] and cells[2] == cells[3]:
            bars.append(f"{cells[0]},{cells[2]}")
        else:
            bars.append(",".join(cells))
    midis = [m + shift for m, _ in notes if m is not None]
    return dict(bar=float(bar), tune=" ".join(toks), chords=" ".join(bars),
                lo=min(midis), hi=max(midis), title=p["title"])


def tune_from_book(path: str, x: int) -> str:
    text = open(path, encoding="latin-1").read()
    for b in re.split(r"\n(?=X:)", text):
        if re.match(rf"X:\s*{x}\b", b):
            return b
    raise KeyError(x)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("x", type=int)
    ap.add_argument("--shift", type=int, default=0)
    a = ap.parse_args()
    s = to_song(tune_from_book(a.book, a.x), a.shift)
    print(f"# {s['title']}  bar={s['bar']}  range {s['lo']}-{s['hi']}")
    print(f'chords="{s["chords"]}",')
    print(f'tune="{s["tune"]}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
