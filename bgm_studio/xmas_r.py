"""
クリスマス曲の作り直し（制作 ID の末尾 r）。2026-11-09。

旧版（x05 など）は、営利不可の曲集（Paul Hardy's Xmas Tunebook, CC BY-NC-SA）の旋律と和音記号を使っていた。
作り直しでは、旋律を出版から 95 年以上たった米国の一次資料（楽譜の画像）から Claude が読み取り、
和音・伴奏はすべて新しく付ける。出典と読み取りの記録は data/licenses/x05r_jingle_bells/。

x05r_jingle_bells_piano：
  旋律 = "Jingle, Bells", arranged by George Rosey, Copyright 1908 by Hinds, Noble & Eldredge
         『The Most Popular Home Songs』(New York: Hinds, Hayden & Eldredge, 1913) p.54-55 の声楽譜の上声。
         Internet Archive の画像 (mostpopularhomes00nobl, leaf 61-62) から読み取った。原調 ト長調 → 変ロ長調へ移調（+3 半音）
  参考 = 1857 年の初版（Boston: Oliver Ditson, plate 18200。米国議会図書館の画像を Wikimedia Commons で閲覧）。
         ヴァース（Dashing thro' the snow）はほぼ同じだが、サビは今と違う旋律（xmas_r の JINGLE_1857_NOTES を参照）
  和音・伴奏 = Claude が新しく付けた（Rosey の伴奏・他の曲集の和音記号は使っていない）
"""

from __future__ import annotations

from .piano_piece import Piece

# 4/4・♩=76。前奏 2 小節 + ヴァース 8 + サビ 8 + 終わり 2 = 20 小節 ≒ 64 秒 + 響き
X05R = Piece(
    slug="x05r_jingle_bells_piano", bpm=76.0, bar=4.0, seed=10501,
    sections=[
        ("intro", "Ebmaj7,Bb/D Cm7,F7sus4"),
        # 1 回目は低い E♭・D の低音の上で旋律 D5・E♭5 が長 7 度・短 9 度でぶつかる所が 10 か所あった。
        # 旋律が必ず和音の音か 9 度に乗るように付け直した
        ("verse", "Bbmaj7,Gm7 Bb/D,Cm7 Cm7,F7sus4 F7,Gm7 Gm7,Ebmaj7 Cm7,Ebmaj7 Cm7,F7 Cm7/F,Bb"),
        ("chorus", "Bbmaj7,Gm7 Gm7,Bb/D Eb6,Cm7 Cm7,F7 Bbmaj7,Gm7 Gm7,Bb/D Eb6,Cm7 Cm7/F,Bb"),
        ("coda", "Gm7,Ebm6 Bbmaj7"),
    ],
    melody={
        "intro": "R/8",
        "verse": "F4/.5 D5/.5 C5/.5 Bb4/.5 F4/1.5 F4/.25 F4/.25 | F4/.5 D5/.5 C5/.5 Bb4/.5 G4/1.5 R/.5 | "
                 "G4/.5 Eb5/.5 D5/.5 C5/.5 G4/1.5 R/.5 | F5/.5 F5/.5 Eb5/.5 C5/.5 D5/1.5 R/.5 | "
                 "F4/.5 D5/.5 C5/.5 Bb4/.5 F4/1.5 R/.5 | F4/.5 D5/.5 C5/.5 Bb4/.5 G4/1.5 G4/.5 | "
                 "G4/.5 Eb5/.5 D5/.5 C5/.5 F5/.5 F5/.5 F5/.5 F5/.5 | G5/.5 F5/.5 Eb5/.5 C5/.5 Bb4/1.5 R/.5",
        "chorus": "D5/.5 D5/.5 D5/1 D5/.5 D5/.5 D5/1 | D5/.5 F5/.5 Bb4/.75 C5/.25 D5/1.5 R/.5 | "
                  "Eb5/.5 Eb5/.5 Eb5/.75 Eb5/.25 Eb5/.5 D5/.5 D5/.5 D5/.25 D5/.25 | D5/.5 C5/.5 C5/.5 Bb4/.5 C5/.5 F5/1.5 | "
                  "D5/.5 D5/.5 D5/1 D5/.5 D5/.5 D5/1 | D5/.5 F5/.5 Bb4/.75 C5/.25 D5/1.5 R/.5 | "
                  "Eb5/.5 Eb5/.5 Eb5/.75 Eb5/.25 Eb5/.5 D5/.5 D5/.5 D5/.25 D5/.25 | F5/.5 F5/.5 Eb5/.5 C5/.5 Bb4/1.5 R/.5",
        "coda": "D5/.5 D5/.5 D5/1 C5/2 | Bb4/4",
    },
    acc_style={"intro": "quarters", "verse": "quarters", "chorus": "quarters", "coda": "quarters"},
    # 和音の音は D3 より上。G3 からにすると、500Hz帯が +5.5 に増え、1 秒ごとの音量差も増えた（2 回目の試し）
    bass_lo=41, upper_lo=50,
    mel_vel={"intro": 0.38, "verse": 0.39, "chorus": 0.41, "coda": 0.35},
    # 1 回目は旋律が伴奏より前に出すぎた（500Hz帯 +5.3）
    mel_gain=0.33, acc_gain=0.40, ritard_bars=2, tail_s=3.2, reverb_send=0.20,
)

# 出典の旋律（移調前・ト長調、1 拍 = 4 分音符）。1908/1913 年版の声楽譜の上声を読み取ったもの。
# 照合用に、移調前の形のまま残す（verify は x05r の旋律から -3 半音して一致を確かめる）
SOURCE_1913_G = (
    "D4/.5 B4/.5 A4/.5 G4/.5 D4/1.5 D4/.25 D4/.25 | D4/.5 B4/.5 A4/.5 G4/.5 E4/1.5 R/.5 | "
    "E4/.5 C5/.5 B4/.5 A4/.5 E4/1.5 R/.5 | D5/.5 D5/.5 C5/.5 A4/.5 B4/1.5 R/.5 | "
    "D4/.5 B4/.5 A4/.5 G4/.5 D4/1.5 R/.5 | D4/.5 B4/.5 A4/.5 G4/.5 E4/1.5 E4/.5 | "
    "E4/.5 C5/.5 B4/.5 A4/.5 D5/.5 D5/.5 D5/.5 D5/.5 | E5/.5 D5/.5 C5/.5 A4/.5 G4/1.5 R/.5 | "
    "B4/.5 B4/.5 B4/1 B4/.5 B4/.5 B4/1 | B4/.5 D5/.5 G4/.75 A4/.25 B4/1.5 R/.5 | "
    "C5/.5 C5/.5 C5/.75 C5/.25 C5/.5 B4/.5 B4/.5 B4/.25 B4/.25 | B4/.5 A4/.5 A4/.5 G4/.5 A4/.5 D5/1.5 | "
    "B4/.5 B4/.5 B4/1 B4/.5 B4/.5 B4/1 | B4/.5 D5/.5 G4/.75 A4/.25 B4/1.5 R/.5 | "
    "C5/.5 C5/.5 C5/.75 C5/.25 C5/.5 B4/.5 B4/.5 B4/.25 B4/.25 | D5/.5 D5/.5 C5/.5 A4/.5 G4/1.5 R/.5"
)
PIECES = {X05R.slug: X05R}
