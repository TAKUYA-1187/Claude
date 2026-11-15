# Quiet Hours Music：制作の共通ルールと現状

チャンネル：Quiet Hours Music（@quiethoursmusic1187、UCXkOUfDDRCUjA08kfCmcm3w）。
目標：世界の視聴者に届けて収益化し、将来は月間の事業利益 100 万円。達成時期や利益は保証しない。実測で改善する。

## 分担（GPT 指示書 §26、2026-11-15：BGM は Claude、画像と映像は GPT）
- **Claude**：作曲・編曲・音源の制作と修正・音質検査・権利資料・Shorts 用の区間の指定。BGM はすべて Claude が作る
- **GPT**：画像・動画の編集・字幕・タイトルと翻訳・サムネイル・YouTube Studio への投稿と設定・実績の分析。作曲・合成はしない。試聴が承認された音源を受け取ってから動画を組み立てる
- **オーナー**：本人認証、音色の好みの最終判断、公開日時の決定、費用のかかる判断

- **Genspark**（2026-11-15 から）：GPT と同じく、指示書と実ファイルでやり取りする相手。x05r の 60〜90 秒の試作の指示書を受け取った（4 点セット：`x05r_60s.flac`・`x05r_60s.mp3`・`x05r_provenance.md`・`x05r_qa.json`）

GPT・Genspark と Claude は直接つながっていない。文書と実ファイルで引き継ぐ。Claude は YouTube Studio を見られないので、GPT の報告は「GPT の報告」として書く。

## 必ず守ること
- AI 使用の開示は常に「はい」。開示を隠すための加工はしない
- 子ども向けは、内容ごとに正直に判断する（子守唄は「はい」、それ以外は「いいえ」）
- 健康の効果をうたわない
- 保留中の動画を再公開しない。同じ動画を二重に上げない。既存の予約や設定を一括で変えない
- 追加の課金・クレジットの購入・プランの変更をしない
- 譜面は、条件のはっきりしたパブリックドメインか CC BY だけを使う（NC・SA は使わない）。出典ファイルを `data/licenses/` に保存し、照合する
- 「古い曲だから」「自作だから」「申し立てがないから」だけで公開可と判断しない
- 検査したこと・人が聞いたこと・未検証のことを分けて報告する（Claude は音を聞けない）
- 長尺は 1 日 1 本まで。5 分おきの大量公開はしない
- コミットの末尾には、指示された共同作成者の行を付ける。モデル名は書かない

## 音源エンジンの注意
- 音源エンジンのサンプリングレートは 44.1 kHz（`bgm_studio/dsp.SR`）
- 録音サンプルは `prepare_piano_samples.py` で 44.1 kHz に保存する
  - 2026-11-07 まで 48 kHz で保存していて、10/28〜11/7 に作った録音の楽器が約 1.47 半音低かった
  - 影響した動画の一覧：`out/release_2026-11-08/audio_impact.csv`
- ピアノの録音は、音ごとの音量を隣の音にそろえて使う（`instruments._even_out`）
- **2026-11-15 から、新しいピアノ曲は Salamander Grand Piano V3（`bgm_studio/grand.py`、CC BY 3.0、16 段階の強さ・ペダル・ダンパー）で作る**
  - 取得：`python3 prepare_salamander.py --variant 48k24`（原本 48kHz/24bit。読み込み時にヘッダーの 48kHz・24bit を確かめ、鳴らすときに音の高さ合わせと 48k→44.1k を 1 回の再サンプリングで行う）。v2 は `--variant` なし（44.1kHz/16bit 版）
  - 離鍵の弦共鳴（harm）とハンマーノイズ（rel）の録音も鳴らす（`Grand("48k24", hammer=True)`）
  - 説明欄に表示が必要：「Piano: Salamander Grand Piano V3 by Alexander Holm (CC BY 3.0)」と https://creativecommons.org/licenses/by/3.0/
  - 旧 Iowa の mf 1 段階のピアノ（`instruments.SampleBank` の soft_piano）は、強さで音色が変わらず「薄い」と評価された。新しい曲には使わない
- 再現：`PYTHONHASHSEED=0` で実行する

## 毎回の作業の始めに確かめること
1. 前回の未完了の項目（下の「未完了」）と、そのファイルが実在するか（`ls`・ハッシュ）
2. 書き出しやアップロードが本当に終わったか。前回の自分の発言だけで判断しない
3. 渡したはずのファイルが、相手（GPT）に届いているか。作業場所にあることと、相手が受け取ったことは別

## 自分の失敗の記録（次回の確認項目）
| 日付 | 失敗 | 次回からの確認 |
|---|---|---|
| 10/28〜11/7 | 録音サンプルを 48kHz で保存し、44.1kHz として鳴らした（約 1.47 半音低い） | 新しいサンプルを足したら `verify_pitch.py` で A4 を測る |
| 10/30〜31 | 営利不可（CC BY-NC-SA）の曲集の譜面と和音記号を使った | 譜面を取り込む前にライセンスの原文を保存し、NC・SA なら使わない |
| 11/7 | QA の「ぶつかり」の時刻を拍で書き、秒と取り違えられた | 時刻は必ず秒で書き、拍は別の欄に |
| 11/7 | 子守唄の合成パッドも濁ると書いたが、実際は使われていなかった | 影響の説明は、コードで呼ばれているかを確かめてから書く |
| 11/8 | 音声本体を ZIP に入れず、相手に届かなかった | 音声は音声だけの ZIP にして、ファイル名とハッシュを一覧に書く |
| 11/8 | pet03 比較版の変更範囲を「2 音」と書いたが、実際は 6 音・全体の音量にも差 | 説明を書く前に、コードの変更範囲と、実際の音の差を測る |
| 11/9 | x05r の 1 回目の和声で、低音と旋律が長 7 度・短 9 度でぶつかる所が 10 か所 | 和音を付けたら、必ず melody_accomp_semitone_overlaps を見る |
| 11/15 | x05r v2 の表の注記で、1913 年版の「o-pen」の違いをサビ 4・12 小節目と書いた（正しくは 7 小節目だけ。納品前に表を見て直した） | 出典の違いは、表の音を 1 小節ずつ見て書く。推測で小節番号を書かない |

## 現状（2026-11-15：§26 の後）

**GPT 指示書 §19〜§26 の要点**（GPT の報告。Claude は Studio を見ていない）
- §19〜20：dnOzVffF1ZA・rrtGfjSd6Ao の説明欄は、11/10 朝と 11/11 朝の読み取りで新しい説明と全文一致。432Hz の句はなし。§18 の「反映未確認」は解消
- §22・§24・§25：GPT が自分で作曲・合成したオリジナル 3 本（Lanterns in the Snow、Christmas Bookshop、The Paper Star）を作った
- §26：オーナーの評価は「画像はよいが BGM がチープ」。GPT 音源の 3 本は投稿しない（非公開アップロードも不可）。絵とサムネイルは残し、曲に合えば使う。BGM は Claude が作る
- 新しい公開・予約・アップロードは 0 件（§19〜§26 の時点）

**優先順位（GPT 指示書 §17、2026-11-10 JST）**
クリスマスを最優先にする。順番は次のとおり：
1. x05r Jingle Bells の新録
2. x06r Silent Night の新録
3. O Holy Night（独立した原典が揃った場合だけ）

orig01・pet02・pet03・Velmora・新しいジャンルは後回し。

**新しい曲**
| 制作ID | 状態 | ファイル |
|---|---|---|
| x05r_60s（x05r v3） | **60〜90 秒の試作（79.8 秒）。人の耳での確認待ち。これが最新**。Genspark の指示書への回答。原本 48k/24bit の Salamander、ハンマーノイズ、前奏で主題、♩=66、-14.5 LUFS（リミッター最大 1.9 dB）。旋律・和声は v2 と同じ | `out/release_2026-11-15b/`（4 点セット）、`make_x05r_v3.py`、`bgm_studio/x05r_v3.py` |
| x05r_jingle_bells_piano_v2 | 試聴版（73.5 秒）。v3 で置き換え。Salamander のピアノ。ヴァースは 1857 年版（Levy 所蔵譜）を基本に 2 小節だけ 1913 年版、サビは 1913 年版。和声は新しく付けた | `out/release_2026-11-15/`、`make_x05r_v2.py`、`verify_x05r_v2.py`、`bgm_studio/x05r_v2.py` |
| x05r_jingle_bells_piano | 試作 v1（67 秒、Iowa のピアノ）。v2 で置き換え | `out/release_2026-11-09/`、`make_x05r.py`、`verify_x05r.py` |
| orig01_winter_reading_piano | 3 分の試聴版。オーナーの音色の確認待ち | `out/release_2026-11-07/`、`make_orig01.py` |
| pet02_closing_the_book | 企画と 21 秒の試作音源 | `out/release_2026-11-08/`、`make_pets.py` |
| pet03_last_light | 企画と 22 秒の試作音源 | 同上 |
| pet03_last_light_soft_lamp | pet03 の比較版 | 同上 |

pet03_last_light_soft_lamp についての訂正（GPT の報告 §14.4）：
- 「旋律の 2 音だけ弱めた」と説明したのは誤り。実際は lamp の部分の旋律 6 音すべてを弱めていた
- 最後の音量正規化で、全体にも +0.25 dB の差が出ている
- 6〜7 秒から 7〜8 秒への上昇は +6.41 → +5.99 dB で、改善は約 0.4 dB。段差がなくなったわけではない

orig01 の試作品について：GPT が rHrUJs0h6bU で非公開アップロード済み（§15）。もう一度アップロードしない


**投稿済み・GPT の担当**
- pet01（GPT 制作）：Z8rNJFpXkAM、非公開。音源は Velmora ep01 の 84〜102 秒で、Claude のエンジン由来ではない

**公開の状態**（GPT の 11/7 の報告。Claude は Studio を見ていない）
- **公開中**：x06 Silent Night（dnOzVffF1ZA）と、その Shorts（rrtGfjSd6Ao）、ep01（OeGDYhGTp9U）
  - ep01 について、11/7 夜にオーナーから「映像が止まる・ずっと雑音」という申告と削除の希望があった
- **非公開**：
  - 11/7 に GPT が予約・公開から非公開に変更：x01（V36WnCN9KW8）、x02（e7_aVz7byxE）、w03（367csO2msJg）、x09（vDHxOVufT1k）、Shorts sg26nMcWDeM・VPE6z6MmnmY
  - 以前からの保留：x03・x04・x05・x07・x08・w01・w02・w04
  - その他：k01（t1RntqxDe2I）、k02（6LPA7TH_VdE）、n04 オルゴール（mv-rDt0-7YY）、pet01（Z8rNJFpXkAM）、Velmora Shorts（Jw5x27D811s）
- pet01 と Jw5x27D811s は ep01 と同じ音源なので、ep01 の申告の確認が済むまで非公開のまま

**GPT が YouTube で行った変更**（§15・§18、GPT の報告。Claude は Studio を見ていない）
- f01 と思われる aus8kpTQ28E（2027/1/4 に予約）、h01 と思われる Th9Hc5hn9Fo（2026/12/20 に予約）：予約は変えていない。音程と表記の問題は未解決
- 11/10 00:45〜00:50 JST の変更：
  - dnOzVffF1ZA（Silent Night）と rrtGfjSd6Ao（その Shorts）：説明欄から「A=432Hz」と「real piano」を除く書き込みをした。直後の読み戻しは古いままだったが、11/10 朝・11/11 朝の読み取りで新しい説明と全文一致（§19〜20）。同じ書き込みを繰り返さない
  - dnOzVffF1ZA：サムネイルを silent_night_thumbnail_v2.jpg に変更。配信されていることを確認済み
- 新しい公開・予約・アップロードは 0 件

**権利**（`out/release_2026-11-08b/rights/release_audit.csv` v3、`python3 audit_rights.py` と `python3 verify_sources.py` で作り直せる）
- 公開判断の資料が揃った：x06 Silent Night（説明欄の「A=432Hz」は要修正）
- 資料が足りない：x09、w05
- 許諾または差し替えが必要：x01〜x05、x07、x08、w01〜w04

**音程**（`verify_pitch.py`、`out/release_2026-11-08b/pitch_verification/`）：修正済み・二重補正なし
- 例外：`jazz._bass_note` は A の設定を使っていない

**未完了**
- 人の耳での確認（x05r v2・orig01・pet02・pet03）
- x05r：1908/1913 年版のサビ（1857 年版と違う旋律）の来歴。米国以外での扱い。Levy（JHU）の画像の利用条件のページは Cloudflare で取れていない
- x05r：試作（x05r_60s）が合格したら、本番用のマスターと 15〜30 分の展開版を作る。未承認のまま x06r に進まない
- orig01・pet02・pet03 は Iowa のピアノで作ったもの。作り直すなら Salamander で
- x06r Silent Night の新録（x05r の次）
- x09・w05 の書籍原本との照合

**オーナーの判断待ち**
1. x05r_60s（v3）の音色（`out/release_2026-11-15b/x05r_provenance.md` の 9 節「まだ人の耳で聴いていない項目」）。合格するまで長尺と x06r には進まない（Genspark の指示書）
2. orig01 の音色
3. pet03 の原版か比較版か

## 記録の分け方
企画・素材・音質・権利・投稿・実績・次の改善を、同じ制作 ID で結ぶ。別名の指示書を毎回作り直さず、この CLAUDE.md と `out/release_*/` の一覧（manifest）に追記する。

## 制作 ID で結ぶもの
企画 → 素材 → 音質検査（`*_qa.json`）→ 権利（`release_audit.csv`）→ 投稿（GPT の upload_receipt）→ 実績（`pilot_metrics.csv`）を、同じ制作 ID で結ぶ。
非公開の 0 再生を失敗とは判断しない。次の回で変える点は 1 つにする。
