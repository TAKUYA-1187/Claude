# x05r Jingle Bells：60〜90 秒の試作（出典と制作の記録）

作成：2026-11-15（Claude）。Genspark の指示書「Claudeへ貼る指示文（x05r Jingle Bells／2026-11-15）」への回答。
制作 ID：`x05r_jingle_bells_piano`（旧 x05 / Mpl70FC93HQ とは別物）。**音色の合否は Claude では判定していません。**

## 1. 曲の情報

| 項目 | 内容 |
|---|---|
| 曲名 | Jingle Bells（原題 The One Horse Open Sleigh、J. Pierpont 作）— 静かな読書向けのピアノ独奏 |
| 長さ | 79.80 秒 |
| 拍子 | 4/4（出典は 2/4。出典の 2 小節を 1 小節にした） |
| テンポ | ♩=66 を基準に、句の終わりで約 5% ゆっくり、最後の 3 小節で 12〜35% ゆっくり（原曲の Allegro を静かな速さに翻案） |
| 調 | 変ロ長調（B♭ major） |
| 小節数 | 4/4 で 20 小節（前奏 2・ヴァース 8・サビ 8・終わり 2）＋最後の和音の余韻 |
| 楽器 | ピアノ独奏のみ（鈴・打楽器・効果音・歌声なし） |
| 基準音 | A4 = 440 Hz、平均律 |

**構成**

| 時刻 | 部分 | 中身 |
|---|---|---|
| 0:00〜7.5 秒 | 前奏（主題） | サビの頭「Jingle bells, jingle bells, jingle all the way」を静かに。和音は B♭maj7 → Dm7 → Gm7 → F6 |
| 7.5〜37.1 秒 | ヴァース | 前半は「低音＋2 音」の 4 分音符、後半は 8 分音符が加わる |
| 37.1〜67.1 秒 | サビ（伴奏の変化） | 左手が 8 分音符の分散和音に変わり、旋律の下に 3 度・6 度を重ねる |
| 67.1 秒〜終わり | 終止と余韻 | 最初の動機（F D C B♭）を 1 オクターブ上で → E♭m6 → B♭ の和音を下から分散。約 6 秒鳴らしてからペダルを上げ、音が消えるまで |

## 2. 音源とライセンス

| 項目 | 内容 |
|---|---|
| ピアノ音源 | Salamander Grand Piano V3（作者 Alexander Holm、Yamaha C5、AKG C414 2 本を弦の上約 12 cm に AB 配置） |
| 版 | 原本 48kHz / 24bit（FreePats `SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz`、sha256 ae30854d2cb686f81dbfae3c0475173838b0053454feb28df0ec425fdc64ad1e） |
| 仕様 | 強さ 16 段階、短 3 度ごとの録音、弦共鳴のリリース（3 段階）、ハンマーノイズのリリース（半音ごと）、ペダルの音（今回は不使用） |
| ライセンス | CC BY 3.0（商用可・無償・表示が必要。NC・SA なし）。同梱の README に「Licence: CC-by http://creativecommons.org/licenses/by/3.0/」 |
| 証拠の保存場所 | `data/licenses/salamander_grand_piano_v3/`（README・sfz・取得ページ・CC BY 3.0 の原文） |
| 費用 | 0 円（追加購入・有料プラン・有料 API なし） |

**概要欄に入れるクレジット（必須）**

```
Piano: Salamander Grand Piano V3 by Alexander Holm (CC BY 3.0)
https://creativecommons.org/licenses/by/3.0/
```

- 人が弾いた録音ではありません（打鍵の時刻・強さ・ペダルはプログラムで作った）。「real piano」「live」とは書かない。AI 使用の開示は「はい」

## 3. サンプルレートと再サンプリング

| 段階 | サンプルレート | 処理 |
|---|---|---|
| 準備（音源） | 48,000 Hz / 24 bit | 配布された WAV をそのまま読む。読み込むたびに WAV のヘッダーが 48 kHz・24 bit かを確かめ、違えば止まる。レート変換なし |
| 描画（レンダー） | 44,100 Hz（`bgm_studio/dsp.SR`） | 1 音につき 1 回だけ再サンプリング：音の高さ合わせ（最大 ±1 半音）と 48k→44.1k を同じ `resample_poly` で同時に行う。異なる（録音・高さ）の組み合わせは 189 通り |
| 書き出し | 44,100 Hz / 24 bit（FLAC）、44,100 Hz（MP3 320 kbps） | レート変換なし |
| 実測 | FLAC ヘッダー 44100 Hz、24 bit、2 ch | 基準音 A4 の高さから逆算した実効レート 44082.7・44075.8 Hz（宣言値との差 -0.039・-0.055 %。録音のピアノ自体の調律 約 +1 cent を含む上限値） |

- 曲全体を速くしたり遅くしたりして音程を合わせることはしていません
- 同じ曲を 44.1kHz/16bit 版の音源で鳴らした場合と、単音の高さが 0.01 cent まで一致することを確認しました（48k を 44.1k として読む誤り・二重補正がないことの確認）

## 4. 再現方法

```
git checkout claude/youtube-bgm-marketing-strategy-7yy7kq
python3 prepare_salamander.py --variant 48k24      # 音源の取得と sha256 の確認（約 1.2 GB）
PYTHONHASHSEED=0 python3 make_x05r_v3.py           # 4 点セットを out/release_2026-11-15b/ に書き出し、検収する
```

- コード：`bgm_studio/x05r_v3.py`（構成・テンポ・音量）、`bgm_studio/x05r_v2.py`（採譜・旋律の出典・和声・伴奏・強さ）、`bgm_studio/grand.py`（ピアノ）
- 乱数の種は固定（打鍵の揺れ・強さの揺れ）。同じコマンドで同じ音になることを、2 回書き出して確認

**ハッシュ（SHA-256）**

- x05r_60s.flac：`899caa20aa21b68f6922e2471b3f682da90638a43db629d60a1e6d5a1eb9bc1d`
- x05r_60s.mp3：`f7d7f4be8223575f80856cb98ac39fe1ca5ea2fc3713aad928cf195559ea70a2`

## 5. 原典と採譜

**原典**：Johns Hopkins University, Lester S. Levy Sheet Music Collection, Box 062 Item 044
- 所蔵ページ：https://levysheetmusic.mse.jhu.edu/collection/062/044
- 譜面 PDF（4 ページ）：https://levysheetmusic.mse.jhu.edu/sites/default/files/collection-pdfs/levy-062-044.pdf（2026-11-15 取得、`data/licenses/x05r_jingle_bells/1857_levy_jhu/levy-062-044.pdf`）
- 目録：Written and Composed by J. Peirpont（目録の綴り。印刷は J. PIERPONT）／Boston: Oliver Ditson & Co.／1857／plate 18200／piano and voice／strophic with chorus
- 参照：米国議会図書館 https://www.loc.gov/item/2023812429/ は 403 のまま（取得していない）。同じ版（plate 18200）の議会図書館の画像は Wikimedia Commons 経由で保存済み（`../1857_first_edition_loc/`）

**譜面の様子**（目視）
- PDF 1 ページ目：表紙。2 ページ目（印刷 p.3）：ピアノの前奏（Allegro、2/4、変イ長調）の後に歌のヴァース。1 番と 2 番の歌詞が上下に印刷されている
- 3〜4 ページ目（印刷 p.4〜5）：CHORUS。4 声の合唱とピアノ。ここでは最上声を採譜した。最後にピアノの後奏（8va）。3・4 番の歌詞は p.5 に文字だけで印刷
- 反復記号：見当たらない（有節形式。2〜4 番は同じヴァースをくり返して歌う）
- 弱起：歌の最初の小節は休符の後、最後の 8 分音符に 2 番の歌詞「A」だけが付く。1 番の歌詞は次の小節の頭から（ここでは小節 0 とした）

**採譜表**（歌声パートのみ。実際の高さ、変イ長調。音価は 4 分音符 = 1）

| PDF ページ | 段 | 小節 | 音（音価） | 1 番の歌詞 | 2 番の歌詞 | 確かさ・備考 |
|---|---|---|---|---|---|---|
| 2 | 2 | ヴァース 0 | R/1 R/.5 Eb4/.5 | — | A | 確か。弱起。上の歌詞「2. A」は 2 番だけの音 (1 番の歌詞は次の小節から) |
| 2 | 2 | ヴァース 1 | Eb4/.5 C5/.5 Bb4/.5 Ab4/.5 | Dash- ing thro' the | day or two a- | 確か。1. Dash-ing thro' the |
| 2 | 2 | ヴァース 2 | Eb4/1 R/.5 Eb4/.25 Eb4/.25 | snow, In a | go, I 〃 | 確か。snow, In a (16 分音符 2 つ) |
| 2 | 2 | ヴァース 3 | Eb4/.5 C5/.5 Bb4/.5 Ab4/.5 | one horse o- pen | tho't I'd take a | 確か。one horse o-pen |
| 2 | 2 | ヴァース 4 | F4/1.5 F4/.5 | sleigh, 〃 | ride And | 確か。sleigh, (付点 4 分と 8 分をスラーで結ぶ) |
| 2 | 2 | ヴァース 5 | F4/.5 Db5/.5 C5/.5 Bb4/.5 | O'er the hills we | soon miss Fan- nie | 確か。O'er the hills we |
| 2 | 3 | ヴァース 6 | G4/1.5 G4/.5 | go, 〃 | Bright Was | 確か。go, (スラー) |
| 2 | 3 | ヴァース 7 | G4/.5 F5/.5 Eb5/.5 Db5/.5 | Laugh- ing all the | seat- ed by my | 確か。Laugh-ing all the。低い G4 から F5 へ 7 度跳ぶ (今の形とは違う) |
| 2 | 3 | ヴァース 8 | C5/1.5 Eb4/.5 | way; — (未確認) | side, The | 確か。way; の後の 8 分音符は 2 番の歌詞「The」の音 |
| 2 | 3 | ヴァース 9 | Eb4/.5 C5/.5 Bb4/.5 Ab4/.5 | Bells on bob tail | horse was lean and | 確か。Bells on bob tail |
| 2 | 3 | ヴァース 10 | Eb4/1.5 Eb4/.5 | ring, 〃 | lank Mis- | 確か。ring, (スラー) |
| 2 | 3 | ヴァース 11 | Eb4/.5 C5/.5 Bb4/.5 Ab4/.5 | Mak- ing spir- its | for- tune seem'd his | 確か。Mak-ing spir-its |
| 2 | 4 | ヴァース 12 | F4/1.5 F4/.5 | bright, 〃 | lot He | 確か。bright, (スラー) |
| 2 | 4 | ヴァース 13 | F4/.5 Db5/.5 C5/.5 Bb4/.5 | Oh what sport to | got in- to a | 確か。Oh what sport to |
| 2 | 4 | ヴァース 14 | G4/.5 Eb5/.5 D5/.5 Eb5/.5 | ride and sing A | drift- ed bank And | 確か。ride and sing A。3 つ目の D に ♮ (D♮5)。今の形 (同じ音を 4 回) とは違う |
| 2 | 4 | ヴァース 15 | F5/.5 Eb5/.5 Db5/.5 Bb4/.5 | sleigh- ing song to | we— we got up | 確か。sleigh-ing song to |
| 2 | 4 | ヴァース 16 | Ab4/2 | night. | sot. | 確か。night. (2 分音符・複縦線) |
| 3 | 1 | サビ 1 | C5/.5 C5/.5 C5/1 | Jin- gle bells, | （サビは歌詞 1 つ） | 確か。Jin-gle bells, |
| 3 | 1 | サビ 2 | Eb5/.5 Eb5/.5 Eb5/1 | Jin- gle bells, | （サビは歌詞 1 つ） | 確か。Jin-gle bells, |
| 3 | 1 | サビ 3 | C5/.5 C5/.5 F5/.75 F5/.25 | Jin- gle all the | （サビは歌詞 1 つ） | 確か。Jin-gle all the (付点 8 分と 16 分) |
| 3 | 1 | サビ 4 | E5/2 | way; | （サビは歌詞 1 つ） | 確か。way; (E に ♮。E♮5) |
| 3 | 1 | サビ 5 | F5/.5 Db5/.5 Ab4/.5 F5/.5 | Oh! what joy it | （サビは歌詞 1 つ） | 未確認（候補 A♭4。3 つ目の音の位置がかすれている）。Oh! what joy it。400 dpi の画像で見た |
| 3 | 2 | サビ 6 | Eb5/.5 C5/.5 Ab4/.5 Ab4/.25 Bb4/.25 | is to ride In a | （サビは歌詞 1 つ） | 確か。is to ride In a |
| 3 | 2 | サビ 7 | C5/.5 Bb4/.5 Ab4/.5 Bb4/.5 | one horse o- pen | （サビは歌詞 1 つ） | 確か。one horse o-pen |
| 3 | 2 | サビ 8 | C5/2 | sleigh. | （サビは歌詞 1 つ） | 確か。sleigh. |
| 3 | 2 | サビ 9 | C5/.5 C5/.5 C5/1 | Jin- gle bells, | （サビは歌詞 1 つ） | 確か。Jin-gle bells, |
| 3 | 2 | サビ 10 | Eb5/.5 Eb5/.5 Eb5/1 | Jin- gle bells, | （サビは歌詞 1 つ） | 確か。Jin-gle bells, |
| 4 | 1 | サビ 11 | C5/.5 C5/.5 F5/.5 F5/.5 | Jin- gle all the | （サビは歌詞 1 つ） | 確か。Jin-gle all the |
| 4 | 1 | サビ 12 | E5/2 | way, | （サビは歌詞 1 つ） | 確か。way, (E♮5) |
| 4 | 1 | サビ 13 | F4/.5 Db5/.5 C5/.5 Bb4/.5 | Oh! what joy it | （サビは歌詞 1 つ） | 確か。Oh! what joy it |
| 4 | 1 | サビ 14 | Ab4/.5 Eb5/.5 D5/.5 Eb5/.25 Eb5/.25 | is to ride In a | （サビは歌詞 1 つ） | 確か。is to ride In a (D に ♮) |
| 4 | 1 | サビ 15 | F5/.5 Eb5/.5 Db5/.5 Bb4/.5 | one horse o- pen | （サビは歌詞 1 つ） | 確か。one horse o-pen |
| 4 | 1 | サビ 16 | Ab4/1 R/1 | sleigh. | （サビは歌詞 1 つ） | 確か。sleigh. (4 分音符と休符・終止線) |

- 「〃」はスラーで前の音節を伸ばす音。「— (未確認)」は 1 番の歌詞が付いていない音で、1 番で歌うのか休むのかは印刷からは分からない
- サビ 5 小節目の 3 つ目の音は、400 dpi で見ても A♭4 か B♭4 か確定できなかった。制作にはこの小節を使っていない

## 6. 実際に使った旋律と、今の一般的な形との差分表

比べ方：ト長調にそろえ、各小節（2/4）の音の高さの並びを比べた（同じ音の連続は 1 つにまとめ、リズムは比べない）。「今の一般的な形」は Claude が書いた参照で、特定の出版物ではありません。

| 部分 | 小節 | 使った版 | 1857 年版 | 1908/1913 年版 | 今の一般的な形 | 差（使った旋律 vs 今の形） |
|---|---|---|---|---|---|---|
| ヴァース | 1 | 1857 | D B A G | D B A G | D B A G | 同じ |
| ヴァース | 2 | 1857 | D | D | D | 同じ |
| ヴァース | 3 | 1857 | D B A G | D B A G | D B A G | 同じ |
| ヴァース | 4 | 1857 | E | E | E | 同じ |
| ヴァース | 5 | 1857 | E C B A | E C B A | E C B A | 同じ |
| ヴァース | 6 | 1857 | F# | E | F# | 同じ |
| ヴァース | 7 | 1913 | F# E D C | D C A | D C A | 同じ |
| ヴァース | 8 | 1857 | B D | B | B | 違う（B D / 今の形 B） |
| ヴァース | 9 | 1857 | D B A G | D B A G | D B A G | 同じ |
| ヴァース | 10 | 1857 | D | D | D | 同じ |
| ヴァース | 11 | 1857 | D B A G | D B A G | D B A G | 同じ |
| ヴァース | 12 | 1857 | E | E | E | 同じ |
| ヴァース | 13 | 1857 | E C B A | E C B A | E C B A | 同じ |
| ヴァース | 14 | 1913 | F# D C# D | D | D | 同じ |
| ヴァース | 15 | 1857 | E D C A | E D C A | E D C A | 同じ |
| ヴァース | 16 | 1857 | G | G | G | 同じ |
| サビ | 1 | 1913 | B | B | B | 同じ |
| サビ | 2 | 1913 | D | B | B | 同じ |
| サビ | 3 | 1913 | B E | B D G A | B D G A | 同じ |
| サビ | 4 | 1913 | Eb | B | B | 同じ |
| サビ | 5 | 1913 | E C G E | C | C | 同じ |
| サビ | 6 | 1913 | D B G A | C B | C B | 同じ |
| サビ | 7 | 1913 | B A G A | B A G | B A B | 違う（B A G / 今の形 B A B） |
| サビ | 8 | 1913 | B | A D | A D | 同じ |
| サビ | 9 | 1913 | B | B | B | 同じ |
| サビ | 10 | 1913 | D | B | B | 同じ |
| サビ | 11 | 1913 | B E | B D G A | B D G A | 同じ |
| サビ | 12 | 1913 | Eb | B | B | 同じ |
| サビ | 13 | 1913 | E C B A | C | C | 同じ |
| サビ | 14 | 1913 | G D C# D | C B | C B | 同じ |
| サビ | 15 | 1913 | E D C A | D C A | D C A | 同じ |
| サビ | 16 | 1913 | G | G | G | 同じ |

**差の説明**
- ヴァース 8 小節目：1857 年版の最後の 8 分音符（D）は 2 番の歌詞「The」の音。版のとおり弾いた
- サビ 7 小節目「one-horse o-pen」の 4 つ目の音：1908/1913 年版は G、今の一般的な形は B。版のとおりにした（変ロ長調では B♭4）
- 1857 年版と今の形が違う所（使わなかった所）：ヴァース 7 小節目（G から 7 度跳び上がる）、ヴァース 14 小節目（G E♭ D♮ E♭）、サビ全体（別の旋律）。この 3 か所は 1908/1913 年版を使った
- 1908/1913 年版：『The Most Popular Home Songs』（1913）p.54–55、George Rosey 編曲、Copyright 1908 by Hinds, Noble & Eldredge（Internet Archive `mostpopularhomes00nobl`、`data/licenses/x05r_jingle_bells/1913_most_popular_home_songs/`）
- 照合：採譜の文字列だけから期待される旋律を作り、制作データと 32 小節すべて一致することを機械で確認（`verify_x05r_v2.py`、前奏の 4 小節は 1913 年版のサビ 1〜4 小節と同じ）

## 7. 権利の分け方

| 層 | 何を使ったか | 状態 |
|---|---|---|
| 作曲（旋律） | J. Pierpont、1857 年出版 | 米国でパブリックドメイン（1929 年より前の出版）。米国以外の各国は個別に確認していない |
| 版（印刷譜）① | 1857 年 Ditson 版（Levy 所蔵）から 42 音 | 米国でパブリックドメイン。所蔵館の画像の利用条件のページ（library.jhu.edu）は Cloudflare の確認画面で取得できず、回避していない。使ったのは画像ではなく、読み取った音の並び |
| 版（印刷譜）② | 1908/1913 年 Rosey 編曲版から 59 音＋前奏 | 米国でパブリックドメイン（1929 年より前の出版）。米国以外は未確認 |
| 編曲（和声・伴奏・前奏・終わり） | Claude が新しく作った | 旧 x05 の音源・伴奏、Hardy／England 等の ABC・和音記号・編曲、Rosey の伴奏、既存の録音は使っていない |
| 録音（音源） | Salamander Grand Piano V3 | CC BY 3.0。クレジットが必要 |
| 演奏 | プログラムで作った打鍵・強さ・ペダル | 新しい制作物。AI 使用として開示する |

## 8. 未確認のこと

1. 1908/1913 年版のサビ（1857 年版と違う旋律）が、いつ・誰によって今の形になったか。米国以外の国での扱い
2. Levy コレクション（JHU）の画像の利用条件（条件のページが Cloudflare の確認画面で取得できなかった）
3. 1857 年版の 2 か所：サビ 5 小節目の 3 つ目の音（A♭4 か B♭4 か）、ヴァース 8 小節目の 8 分音符を 1 番で歌うか（どちらも制作には影響しない）
4. 音色・打鍵・ペダル・余韻・リミッターの効き：人の耳で聴いていない（`x05r_qa.json` の not_listened_by_human）

## 9. 機械で確認した項目と、まだ聴いていない項目

| 項目 | 結果 | 基準 |
|---|---|---|
| サンプルレート | ヘッダー 44100 Hz（MP3 も 44100 Hz）、実効 44082.7・44075.8 Hz（差 -0.039・-0.055 %） | 差 0.5% 未満 |
| Integrated LUFS | FLAC -14.5、MP3 -14.5（ffmpeg）／自前 -14.06 | -14±1（目安） |
| True Peak | FLAC -1.2 dBTP、MP3 -1.2 dBTP（ffmpeg）／自前 -1.2 | -1.0 dBTP 以下 |
| クリップ（\|x\|≥0.9999） | FLAC 0、MP3 0 | 0 |
| 孤立クリック | 0（検出器の生の結果は 2 件：79.75 秒・段差 なし（デジタルの無音の中で検出器が反応したもの）、79.75 秒・段差 なし（デジタルの無音の中で検出器が反応したもの）。曲の最後の無音の所。-90 dBFS 未満の段差は聞こえないので数えない） | 0 |
| 曲中の無音（-55 dBFS が 0.45 秒以上） | 0 | 0（末尾の余韻は可） |
| 基準音 A4 | 440.174 Hz（+0.68 cent、強さ 40）、440.241 Hz（+0.95 cent、強さ 62） | ±10 cent 以内 |
| ループ・継ぎ目 | ループ納品ではない | — |
| LRA | 7.3 LU | （参考） |
| リミッター | 最大 1.9 dB、1 dB を超えて圧縮した時間 0.4 秒、3 dB 超 0.0 秒、天井で切ったサンプル 0 | （参考） |
| 旋律と伴奏の半音のぶつかり | 0 | （参考） |
| 1 秒ごとの音量が 6 dB 以上上がる所 | 0 | （参考） |
| 帯域（250〜500 Hz を 0） | 500 Hz +3.5 / 1000 Hz -11.1 / 2000 Hz -19.8 / 4000 Hz -41.2 / 8000 Hz -70.7 | （参考） |
| 旋律と伴奏の音量差 | 旋律が +2.34 dB（残響の前で測定） | （参考） |

**まだ人の耳で聴いていない項目**：音色 (チープさが消えたか)、打鍵の自然さ、旋律の大きさ、低音の濁り、ペダルの濁り・切れ、残響の長さ、リミッターの効き (最大の圧縮量は limiter を参照)、前奏の主題の分かりやすさ、終わりの余韻。音色の合否は Claude では判定していません。
