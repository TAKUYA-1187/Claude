# orig01_winter_reading_piano：曲の構成メモとライセンス一覧

作成：2026-11-07（Claude）。仮題：Winter Reading Piano。
静かな読書や夜の作業のための、歌なしの柔らかなピアノ曲です。

## 1. 曲の構成（試聴版 2:58）

4/4 拍子、F 長調、♩=64。各フレーズの最後の小節はわずかに遅くし、最後の 4 小節は少しずつ遅くして終わります。

| 時刻 | 部分 | 小節数 | 和音 | 中身 |
|---|---|---|---|---|
| 0:00 | 前奏 | 4 | F – Dm7 – B♭maj7 – C7sus4→C7 | 伴奏だけ（8 分音符の分散和音）。最初の音から音楽が始まる |
| 0:15 | A | 8 | F – Dm7 – B♭maj7 – C7 – F/A – B♭ – Gm7 – C | 主題「ラ-ド-ファ」と上がって開く旋律。C（半終止）で次へ |
| 0:45 | A' | 8 | F – Am7 – Dm7 – B♭maj7 – Gm7 – C7 – F – F | 同じ頭で始まり、下りながら主音 F へ閉じる |
| 1:15 | B | 8 | Dm – B♭ – Gm – A7 – Dm – B♭ – Gm7 – C7 | ニ短調。旋律が高い音域へ。伴奏は 4 分音符のゆっくりした分散 |
| 1:45 | つなぎ | 4 | B♭maj7 – Am7 – Gm7 – C7sus4→C7 | 旋律が下りて、主題へ戻る準備 |
| 2:00 | A'' | 8 | A と同じ流れ | 主題の戻り。伴奏に 9 度の音を足して少し豊かに。最高音 B♭5 が頂点 |
| 2:30 | 終わり | 6 | B♭maj7 – F/A – Gm7 – C7 – F – F | 主題の音で静かに下り、最後は伴奏だけの和音で消える |

作りの決まり：
- **旋律**：既存の曲から借りていない、新しい旋律（`bgm_studio/orig01.py` の MELODY）
- **低音**：F2（87 Hz）より下を使わない。和音の 3 度は C3 より上に置く（低音を濁らせない）
- **伴奏**：旋律と半音でぶつかる音は、伴奏の和音から自動で抜く
- **残響**：少なめ（RT60 2.0 秒、ウェット 22%）。輪郭を残す
- **音**：ピアノだけ。雨・暖炉などの環境音は入れていない
- **作曲データ**：`orig01_score.mid`（一定テンポ・演奏の揺らぎなし）。再現は `PYTHONHASHSEED=0 python3 make_orig01.py`

## 2. ライセンス一覧

| 使ったもの | 出所 | 条件 | 保存先 |
|---|---|---|---|
| 旋律・和声・構成 | Claude が新しく作曲（2026-11-07） | 既存の曲・譜面を使っていない | `bgm_studio/orig01.py`、`orig01_score.mid` |
| ピアノの録音 | University of Iowa Electronic Music Studios、Musical Instrument Samples「Piano.mf」（https://theremin.music.uiowa.edu/MIS.html） | 「may be downloaded and used for any projects, without restrictions」 | 文面：`data/licenses/LICENSE_TEXTS.md`、取得したページ：`data/licenses/theremin.music.uiowa.edu_MIS.html.html` |
| 残響・音量・音色の処理 | Claude のコード（`bgm_studio/dsp.py` ほか） | 自作 | リポジトリ |
| 変換 | ffmpeg（WAV → FLAC・MP3） | 変換に使っただけで、音には何も足していない | — |

- 追加の購入・有料サービス・課金のある処理は使っていません
- 推奨のクレジット（必須ではない）：Piano samples: University of Iowa Electronic Music Studios

## 3. 次の段階（オーナーの確認の後）

1. オーナーが試聴版の音色を確認する。直してほしい点（速さ・明るさ・旋律の動き・残響）をもらう
2. 合格したら 15〜30 分の版を作る
   - この曲を主題にして、同じ主題の変奏・別の調の中間部・テンポを少し変えた部分で展開する
   - 同じ 2 小節のくり返しにはしない
3. 必要なら 45〜60 分の本編にする。次の作品は、旋律・展開・聞く用途を変える
