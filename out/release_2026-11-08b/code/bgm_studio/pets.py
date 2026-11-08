"""
ペットのいる静かな夜の Shorts 用の短いオリジナル曲。2026-11-08。

pet02「読書をやめる小さな合図」と pet03「夜の最後の明かり」。どちらも新しく作曲し、
orig01 とも互いとも、調・拍子・旋律を変えてある (色違い・音程違いの複製にしない)。
"""

from __future__ import annotations

from .piano_piece import Piece

# pet02：変ホ長調・3/4・♩=90（1 小節 2 秒）。9 小節 + 響き ≒ 20 秒
# 0 秒：上がる分散和音の主題がすぐ鳴る（読書の場面）
# 4 秒：5 度下がる 2 音（F→B♭）で「本を閉じる」合図
# 6〜12 秒：主題が戻り、高い所へ（視線が隣の猫へ）
# 12〜20 秒：ゆっくり主音へ下りて、和音の響きで終わる（眠る猫）
PET02 = Piece(
    slug="pet02_closing_the_book", bpm=90.0, bar=3.0, seed=8202,
    sections=[("read", "Eb Abmaj7"), ("close", "Bb7sus4"), ("gaze", "Eb/G Cm7 Ab"), ("sleep", "Fm7 Bb7 Eb")],
    melody={
        "read": "G4/1 Bb4/1 Eb5/1 | D5/2 C5/1",
        "close": "F5/1 Bb4/2",
        "gaze": "G4/1 Bb4/1 Eb5/1 | G5/2 F5/1 | Eb5/1 C5/1 Ab4/1",
        "sleep": "C5/2 Ab4/1 | F4/1.5 Ab4/.5 D4/1 | Eb4/3",
    },
    acc_style={"read": "waltz", "close": "waltz", "gaze": "waltz", "sleep": "waltz"},
    mel_vel={"read": 0.42, "close": 0.40, "gaze": 0.42, "sleep": 0.36},
    ritard_bars=2, tail_s=2.6,
)

# pet03：ニ長調・4/4・♩=66（1 小節 3.6 秒）。5 小節 + 響き ≒ 22 秒
# 低音は D3（147Hz）より下を使わず、和音の 3 度は C4 より上（低音を濁らせない）
# 0 秒：F#5 から下りる旋律（窓辺の犬）
# 7 秒：G5 まで上がる頂点（読書灯）
# 14〜22 秒：主音へ下りて、空いた 5 度の低音の上で静かに終わる（本が閉じられた場面）
PET03 = Piece(
    slug="pet03_last_light", bpm=66.0, bar=4.0, seed=8303,
    sections=[("window", "D Gmaj7"), ("lamp", "Em7 A7sus4,A7"), ("closed", "D")],
    melody={
        "window": "F#5/1.5 E5/.5 D5/1 A4/1 | B4/1.5 C#5/.5 D5/2",
        "lamp": "E5/1 G5/1 F#5/1.5 E5/.5 | D5/2 C#5/2",
        "closed": "A4/1 F#4/1 D5/2",
    },
    acc_style={"window": "open5", "lamp": "open5", "closed": "open5"},
    bass_lo=50, upper_lo=60, mel_vel={"window": 0.41, "lamp": 0.40, "closed": 0.36},
    # 1 回目は旋律が伴奏より前に出すぎた（500Hz帯 +6.4、音と音の間で 1 秒ごとの音量が 9dB 上下）
    mel_gain=0.32, acc_gain=0.46,
    ritard_bars=2, tail_s=3.4,
)

# pet03 の比較版：7.3 秒（読書灯の場面）で入る旋律の 2 音だけを弱くしたもの。ほかは同じで、同じ -14 LUFS にそろえる
# （原版は 1 秒ごとの音量が 6〜7 秒の間で +6.4dB。GPT の依頼で、全体を圧縮せずにその発音だけを弱めた版を作る）
import dataclasses as _dc
PET03_SOFT = _dc.replace(PET03, slug="pet03_last_light_soft_lamp",
                         mel_vel={"window": 0.41, "lamp": 0.33, "closed": 0.36})

PIECES = {p.slug: p for p in (PET02, PET03, PET03_SOFT)}
