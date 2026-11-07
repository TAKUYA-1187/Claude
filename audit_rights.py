#!/usr/bin/env python3
"""
権利表 (release_audit.csv v2) を作る。2026-11-08。

曲ごとに「原曲」「編曲」「版 (使った譜面データ)」「録音」の権利を分けて書く。
照合の数値は 2026-11-07〜08 に、制作データ (bgm_studio/nursery.py) の旋律・和音を、
data/licenses/ に保存した譜面と 1 音ずつ機械で比べた結果。

    python3 audit_rights.py out/release_2026-11-08/release_audit.csv
"""

from __future__ import annotations

import csv
import sys

HARDY = "Paul Hardy's Xmas Tunebook（data/licenses/pghardy_xmas_tunebook_2024_retrieved_2026-11-07.abc）"
HARDY_LIC = "CC BY-NC-SA 4.0：非営利のみ。営利利用は Paul Hardy 氏への連絡が必要（data/licenses/LICENSE_TEXTS.md）"
ESB = "The Everyday Song Book（1927）の ABC 転記、trillian.mit.edu（data/licenses/trillian_esb_*.abc）"
ESB_LIC = "転記サイトに利用条件の記載なし。原典の書籍（1927 年・米国）は、出版から 95 年を過ぎて米国でパブリックドメイン"
IOWA = "University of Iowa MIS の録音（制限なし：data/licenses/LICENSE_TEXTS.md）を、Claude のコードで演奏・処理"

# 曲: (曲名, 原曲, 原曲の権利, 使った版, 照合結果, 版の権利, 編曲（和音）の由来, 曲の判定)
NG, OK, UNK = "版の条件に合わない（営利不可）", "資料が揃った", "版の条件が不明"
SONGS = {
    "c01": ("We Wish You a Merry Christmas", "英国伝承曲", "パブリックドメイン（伝承曲）",
            "trillian.mit.edu の ABC 3 版を見比べて手で入力（data/licenses/trillian_ww_*.abc）",
            "England 版と 77%、Hardy 版と 62%（手で多数派をとったため完全一致はない）", "3 版とも転記サイトに利用条件の記載なし",
            "和音は Hardy 版と 52% 一致（作業記録なし。手で付けたと推定）", UNK),
    "c02": ("Deck the Halls", "ウェールズ伝承曲", "パブリックドメイン（伝承曲）",
            f"作業記録では {ESB} No.105。照合では {HARDY} X:4002 と完全一致",
            "Hardy 版と 100%、ESB と 94%", "Hardy 版なら営利不可／ESB 版なら条件不明",
            "和音は Hardy 版と 69% 一致", NG),
    "c03": ("O Christmas Tree", "ドイツ伝承曲", "パブリックドメイン（伝承曲）", f"{HARDY} X:15006", "旋律 100%",
            HARDY_LIC, "和音は Hardy 版と 65% 一致", NG),
    "c04": ("Joy to the World", "Antioch（Lowell Mason 編 1839）", "パブリックドメイン", f"{HARDY} X:10003", "旋律 100%",
            HARDY_LIC, "和音は Hardy 版と 95% 一致", NG),
    "c05": ("The First Noel", "英国伝承曲", "パブリックドメイン（伝承曲）", f"{HARDY} X:6001", "旋律 100%", HARDY_LIC,
            "和音は Hardy 版と 96% 一致", NG),
    "c06": ("Away in a Manger", "William J. Kirkpatrick『Cradle Song』(1895)", "パブリックドメイン", f"{HARDY} X:1005",
            "旋律 100%", HARDY_LIC, "和音は Hardy 版と 88% 一致", NG),
    "c07": ("Hark! The Herald Angels Sing", "Felix Mendelssohn (1840)、W. H. Cummings 編", "パブリックドメイン",
            f"{ESB} No.194", "ESB と 97%、Hardy 版と 93%", ESB_LIC, "和音は Hardy 版と 15%（Hardy 由来ではない）", UNK),
    "c08": ("O Come, All Ye Faithful", "Adeste Fideles（18 世紀）", "パブリックドメイン", f"{HARDY} X:15001", "旋律 100%",
            HARDY_LIC, "和音は Hardy 版と 90% 一致", NG),
    "c09": ("Jingle Bells", "James Lord Pierpont (1857)", "パブリックドメイン", f"{HARDY} X:10002", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c10": ("Ding Dong Merrily on High", "Thoinot Arbeau『Orchésographie』(1589) の舞曲", "パブリックドメイン",
            f"{HARDY} X:4001", "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c11": ("I Saw Three Ships", "英国伝承曲", "パブリックドメイン（伝承曲）", f"{HARDY} X:9005", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c12": ("Good King Wenceslas", "『Piae Cantiones』(1582)", "パブリックドメイン", f"{HARDY} X:7004", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c13": ("God Rest Ye Merry, Gentlemen", "英国伝承曲", "パブリックドメイン（伝承曲）", f"{HARDY} X:7003",
            "旋律 100%・和音 70%", HARDY_LIC, "Hardy 版の和音記号を一部直して使用", NG),
    "c14": ("Go Tell It on the Mountain", "アフリカ系アメリカ人の霊歌", "パブリックドメイン（伝承曲）", f"{HARDY} X:7005",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c15": ("O Holy Night", "Adolphe Adam (1847)", "パブリックドメイン", f"{HARDY} X:15003", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c16": ("O Little Town of Bethlehem", "Lewis Redner (1868)", "パブリックドメイン", f"{HARDY} X:15004", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c17": ("It Came Upon the Midnight Clear", "Richard Storrs Willis (1850)", "パブリックドメイン", f"{HARDY} X:9006",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c18": ("What Child Is This (Greensleeves)", "英国伝承曲（16 世紀）", "パブリックドメイン（伝承曲）", f"{HARDY} X:23003",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c19": ("In the Bleak Midwinter", "Gustav Holst『Cranham』(1906、1934 年没)", "パブリックドメイン（作曲者の死後 70 年を経過）",
            f"{HARDY} X:9003", "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c20": ("Once in Royal David's City", "Henry John Gauntlett『Irby』(1849)", "パブリックドメイン", f"{HARDY} X:15005",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "c21": ("Infant Holy, Infant Lowly", "ポーランド伝承曲 W żłobie leży", "パブリックドメイン（伝承曲）", f"{HARDY} X:9004",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "n08": ("Silent Night", "Franz Xaver Gruber (1818)", "パブリックドメイン",
            "制作時は出典記録なし（2026-10-23 に手入力）。2026-11-08 に Mutopia のパブリックドメイン版（id 1295, Stille Nacht hymntune）と照合",
            "Mutopia 1295 の旋律と、音の高さの動きが 100%、長さを含めて 97.8% 一致。1927 年の ESB No.57 とも音の高さの動きが 97.8%",
            "照合に使った Mutopia 1295 は Public Domain（data/licenses/silent_night/）。制作では第三者の譜面データを使っていない",
            "和音は手で付けた（自作）", OK),
    "n10": ("Jingle Bells（子守唄版・サビのみ）", "James Lord Pierpont (1857)", "パブリックドメイン",
            "制作時は出典記録なし（手入力）", "全曲版との部分一致のみ（ESB 60%、Hardy 65%。サビだけなので全体比較では低く出る）",
            "第三者の譜面データを使った記録はない", "和音は手で付けた（自作）", UNK),
    "d01": ("Winter (Largo) from The Four Seasons", "Antonio Vivaldi (1725)", "パブリックドメイン",
            "Mutopia-2010/02/08-351 の MIDI（winter-mids.zip。ファイル本体は保存していない）", "作業記録による（照合できる保存ファイルなし）",
            "CC BY-SA 3.0：商用可。表示と、改変物を同じライセンスで公開することが条件（data/licenses/mutopia_vivaldi_winter_piece-info_351.html）",
            "和音は Mutopia の他声部から推定", "版の条件を満たしていない（表示なし・SA 未対応）"),
    "d02": ("Der Lindenbaum (The Linden Tree)", "Franz Schubert (1827)、Silcher の民謡版", "パブリックドメイン", f"{ESB} No.201",
            "旋律 100%", ESB_LIC, "和音は自作（ESB には和音記号がない）", UNK),
    "d03": ("Auld Lang Syne", "スコットランド伝承曲", "パブリックドメイン（伝承曲）", f"{ESB} No.197", "旋律 100%", ESB_LIC,
            "和音は手で付けた（自作）", UNK),
    "d04": ("The Holly and the Ivy", "英国伝承曲", "パブリックドメイン（伝承曲）", f"{HARDY} X:8003", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "d05": ("Coventry Carol", "英国伝承曲（16 世紀）", "パブリックドメイン（伝承曲）", f"{HARDY} X:3005", "旋律・和音とも 100%",
            HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "d06": ("Huron Carol (Une Jeune Pucelle)", "フランス伝承曲", "パブリックドメイン（伝承曲）", f"{HARDY} X:8004",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
    "d07": ("See, Amid the Winter's Snow", "John Goss『Humility』(1871)", "パブリックドメイン", f"{HARDY} X:19002",
            "旋律・和音とも 100%", HARDY_LIC, "Hardy 版の和音記号をそのまま使用", NG),
}

XMAS1 = ["c01", "n08", "n10", "c03", "c02", "c06", "c04", "c05", "c07", "c08"]
WINTER = ["d01", "c19", "c18", "d02", "d07", "d04", "d06", "d05", "c03", "d03"]
VIDEOS = [  # (制作記号, 動画ID, 状態 (GPT の報告), 曲順)
    ("x01_christmas_piano", "（GPT 側で照合）", "保留（GPT 報告）", XMAS1),
    ("x02_christmas_musicbox", "e7_aVz7byxE と思われる（GPT 側で照合）", "公開中（GPT 報告）", XMAS1),
    ("x03_christmas_bells", "vaLVTWmRLro", "非公開・保留", ["c09", "c02", "c10", "c11", "c01", "c12", "c14", "c13", "c04", "c07"]),
    ("x04_christmas_calm", "JRm_lJp14Pg", "非公開・保留", ["n08", "c16", "c06", "c18", "c15", "c19", "c17", "c21", "c20", "c05"]),
    ("x05_jingle_bells_sleigh", "Mpl70FC93HQ", "非公開・保留", ["c09"]),
    ("x06_silent_night_piano", "dnOzVffF1ZA と思われる（GPT 側で照合）", "公開中（GPT 報告）", ["n08"]),
    ("x07_o_holy_night_piano", "XGKX2gVC7z0", "非公開・保留", ["c15"]),
    ("x08_christmas_carols_2_musicbox", "YqAkk1U7anw", "非公開・保留",
     ["c09", "c16", "c10", "c18", "c11", "c19", "c12", "c17", "c21", "c20"]),
    ("x09_we_wish_you_bells", "（GPT 側で照合）", "保留（GPT 報告）", ["c01"]),
    ("w01_winter_piano", "ZLoni33Q3Ts", "非公開・保留", WINTER),
    ("w02_winter_musicbox", "q6kjWb7OStk", "非公開・保留", WINTER),
    ("w03_vivaldi_winter_piano", "（GPT 側で照合）", "保留（GPT 報告）", ["d01"]),
    ("w04_greensleeves_piano", "2kWitysD-Ds", "非公開・保留", ["c18"]),
    ("w05_auld_lang_syne_piano", "（GPT 側で照合）", "不明", ["d03"]),
]
PITCH = "録音の楽器が約 1.47 半音低い（48k/44.1k の不具合）。説明欄の『A=432Hz』は事実と違う（実際は約 A=397Hz）"


def video_verdict(songs: list[str]) -> str:
    v = [SONGS[s][7] for s in songs]
    if any(x == NG or x.startswith("版の条件を満たしていない") for x in v):
        return "許諾または差し替えが必要"
    if any(x == UNK for x in v):
        return "公開判断に必要な資料がまだ足りない（転記サイトの条件が不明。原典の書籍との照合で解決できる見込み）"
    return "公開判断に必要な資料が揃った（ただし説明欄の基準ピッチの表記は要修正）"


def main(out: str) -> int:
    hdr = ["動画ID", "制作記号", "状態（GPT の報告）", "動画の判定", "曲順", "収録曲", "原曲（作曲者・年）", "原曲の権利",
           "編曲の権利（伴奏・音色・テンポは Claude のコード。和音の由来）", "版：実際に使った譜面データ", "照合結果",
           "版の権利・条件", "録音の権利", "曲の判定", "必要なクレジット", "解決できていない点", "確認日"]
    rows = []
    for slug, vid, state, order in VIDEOS:
        verdict = video_verdict(order)
        for i, k in enumerate(order, 1):
            t, comp, comp_r, ed, match, ed_r, chords, v = SONGS[k]
            credit = {NG: "表記しても営利利用の条件は満たせない",
                      OK: "必須なし（照合に使った版：Mutopia Project, Stille Nacht (hymntune), Public Domain）",
                      UNK: "原典名の表記が望ましい"}.get(v, "Mutopia Project, Vivaldi L'Inverno, CC BY-SA 3.0（現在の説明欄に記載なし）")
            todo = []
            if v == NG:
                todo.append("営利利用の許諾がない。旋律そのものはパブリックドメインなので、原典から取り直し・和音を自作すれば解決できる")
            if v == UNK:
                todo.append("1927 年の書籍のスキャン（米ピッツバーグ大学図書館の PDF）と照合して、版の問題がないことを確かめる")
            if k == "d01":
                todo.append("SA 条件の扱いを決める、または Public Domain の版から取り直す。使った MIDI 本体を保存していない")
            if k == "c09" and slug.startswith(("x03", "x05")):
                todo.append("GPT から『Jingle Bell』の申し立て記録ありと報告（Claude は Studio の現状を見ていない。申し立ては著作権侵害の警告とは別）")
            if slug.startswith("w01") and i == 1:
                todo.append("GPT から 11/7 に収益化に関する通知ありと報告（内容は Claude 未確認）")
            todo.append(PITCH)
            rows.append([vid, slug, state, verdict, f"{i:02d}", t, comp, comp_r + "（作曲者情報は一般的な文献知識。一次資料での確認は未実施）",
                         chords, ed, match, ed_r, IOWA, v, credit, "／".join(todo), "2026-11-08"])
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(rows)
    print(f"{len(rows)} 行 → {out}")
    for slug, vid, state, order in VIDEOS:
        print(f"{slug:34s} {video_verdict(order)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "out/release_2026-11-08/release_audit.csv"))
