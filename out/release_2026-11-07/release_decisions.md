# 公開判断の資料：保留中の 8 本（x03・x04・x05・x07・x08・w01・w02・w04）

作成：2026-11-07（Claude）。曲ごとの詳細は `release_audit.csv`（53 行）にあります。

## 0. 調べた方法と、読めた・読めなかったもの

**実際に読んだ製作ファイル**
- 旋律・和音のデータ：`bgm_studio/nursery.py`（全曲の旋律・和音・出典コメント）
- 動画と曲の対応：`bgm_studio/tracks.py`（MEDLEY_SONGS・CHRISTMAS_SINGLES・各 _ORDER）
- 楽器：`bgm_studio/instruments.py`、`prepare_piano_samples.py`（サンプルの取得 URL）
- 譜面の保存ファイル：`data/xmas_carols_source.abc`（13 曲分）
- git の履歴（2026-10-30・10-31 のコミット）と、過去の作業記録（Claude の会話ログ）

**今日（2026-11-07）に取得して照合した譜面と文面**（`data/licenses/` に保存）
- Paul Hardy's Xmas Tunebook の ABC 全体（60 曲）と、利用条件のページ
- The Everyday Song Book（1927）の ABC 転記（trillian.mit.edu）6 曲と、そのページ
- We Wish You a Merry Christmas の ABC 3 版（trillian.mit.edu）
- Mutopia の Vivaldi「冬」の楽譜情報ページ
- University of Iowa の楽器サンプルのページ

**照合のしかた**：制作データの旋律を、取得した全譜面と 1 音ずつ機械で比べた（調をそろえ、音の高さの動きと長さの比を比べる）。
和音も、譜面の和音記号を同じ調に移して比べた。

**読めなかったもの・確認していないもの**
- YouTube Studio の画面（申し立ての内容、w01 の通知）：Claude は見ていない。GPT からの報告として表に書いた
- Vivaldi の MIDI ファイル本体：制作時に使ったが、リポジトリに保存していなかった（出典 URL は作業記録にある）
- Silent Night（n08）：出典の記録がない（2026-10-23 の子守唄制作時に手入力した）
- 原曲の作曲者・年代：一般的な文献知識で記入した。今回、一次資料では確かめていない
- 動画 ID と制作記号の対応：依頼書の表のとおりとした（Claude は YouTube の動画を見られないので、照合は GPT 側で）

## 1. 結論（8 本とも「許諾または差し替えが必要」）

| 動画 | 動画ID | 判断 | 主な根拠 |
|---|---|---|---|
| x03 Christmas Piano & Sleigh Bells | vaLVTWmRLro | **許諾または差し替えが必要** | 10 曲中 9 曲の旋律が Paul Hardy's Xmas Tunebook と一致（うち 7 曲は和音記号も一致）。この曲集は CC BY-NC-SA（非営利のみ） |
| x04 Calm Christmas Piano | JRm_lJp14Pg | **許諾または差し替えが必要** | 10 曲中 9 曲が Hardy 版と旋律一致。Silent Night は出典の記録なし |
| x05 Jingle Bells | Mpl70FC93HQ | **許諾または差し替えが必要** | 旋律・和音とも Hardy 版と 100% 一致 |
| x07 O Holy Night | XGKX2gVC7z0 | **許諾または差し替えが必要** | 旋律・和音とも Hardy 版と 100% 一致 |
| x08 Christmas Music Box Vol.2 | YqAkk1U7anw | **許諾または差し替えが必要** | 10 曲すべて Hardy 版と旋律・和音 100% 一致 |
| w01 Winter Candlelight | ZLoni33Q3Ts | **許諾または差し替えが必要** | 10 曲中 7 曲が Hardy 版。Vivaldi は Mutopia の CC BY-SA 3.0（表示と継承の条件を満たしていない）。2 曲は転記サイトの条件が不明 |
| w02 Snow-globe Stillness | q6kjWb7OStk | **許諾または差し替えが必要** | w01 と同じ 10 曲（オルゴール版） |
| w04 A Quiet Winter Window | 2kWitysD-Ds | **許諾または差し替えが必要** | What Child Is This（Greensleeves）の旋律・和音が Hardy 版と 100% 一致 |

「公開判断に必要な資料が揃った」「クレジット修正で対応可能」に入る動画は、ありません。

### なぜ「古い曲」でも使えないか

- 旋律そのもの（Jingle Bells は 1857 年など）は、どれも著作権が切れている可能性が高い
- しかし Claude が実際に使ったのは、Paul Hardy 氏が作った**譜面データ**（旋律の写しと、氏が見直した和音記号）
- 曲集の説明に「2019 年版で和音記号を大きく見直した」とあり、和音記号には氏の手が入っている
- その利用条件は「非営利のみ。営利利用は Paul Hardy 氏に連絡」（原文は `data/licenses/LICENSE_TEXTS.md`）
- 収益化を目指すチャンネルの動画は営利利用にあたるので、クレジットを書き足すだけでは条件を満たせない

### 申し立てについて（x03・x05）

- 「Jingle Bell の申し立て記録あり」は GPT の報告。Claude は現在の状態を確認していない
- 申し立て（Content ID）は、著作権侵害の警告（ストライク）とは別のもの。過去の記録を、今の状態と断定しない
- 上の権利の問題は、申し立ての有無とは関係なく残る。異議申し立ては、差し替えか許諾で譜面の問題が解決してから判断するのがよい

## 2. 解決の方法（どれを選ぶかはオーナーと GPT が判断）

既存の音源の変更や、同じ動画の再投稿は、判断が出るまで行いません。

### 方法 A：Paul Hardy 氏に営利利用の許諾を求める
- 曲集のページに「Contact Paul Hardy for commercial licensing」とある
- 許諾が得られれば、今の音源のまま、指定どおりのクレジットで公開できる
- 費用・期間は不明。返事が来るまで公開できない

### 方法 B：該当曲だけを置き換える（旋律の出典を取り直し、和音を自作する）
曲ごとに次のどちらかにします。
1. **同じ曲を、別の資料から作り直す**：
   - 旋律は、出版から 95 年を超えた原典の楽譜（19 世紀〜1920 年代の讃美歌集など）か、
     Public Domain・CC BY の譜面から取り直す
   - 和音は、Hardy 版を見ずに自分で付ける
   - 原典の画像やページを保存し、照合結果を表に残す
2. **別の曲に入れ替える**：出典の条件がはっきりしている曲（Public Domain・CC BY の譜面がある曲）にする

- 音色・テンポ・伴奏の型はそのまま使えるので、音の印象は大きく変わらない
- YouTube では、アップロード済みの動画ファイルを差し替えることはできない。
  作り直した動画は**新しい動画**として上げ、古い非公開の動画は公開しない（削除するかはオーナーが判断）

曲ごとの案：

| 曲 | 使っている動画 | 置き換え案（同じ曲を作り直す場合の旋律の出典候補） |
|---|---|---|
| Jingle Bells | x03・x05・x08 | The Everyday Song Book（1927）No.62。ただし転記サイトの条件が不明なので、書籍のスキャン（米ピッツバーグ大学図書館の PDF）で照合する |
| Deck the Halls | x03 | 同書 No.105（同じ注意） |
| Ding Dong Merrily on High | x03・x08 | 1924 年の Woodward 編の原典を探す。見つからなければ別の曲に |
| I Saw Three Ships、Good King Wenceslas、God Rest Ye Merry、Go Tell It、Joy to the World、O Little Town、Away in a Manger、The First Noel、It Came Upon the Midnight Clear、Once in Royal David's City、Infant Holy、O Holy Night、In the Bleak Midwinter、What Child Is This、The Holly and the Ivy、Huron Carol、Coventry Carol、See Amid the Winter's Snow、O Christmas Tree | 各動画 | 1928 年より前に出版された讃美歌集・キャロル集のスキャン（例：Hymnary.org・IMSLP にある Public Domain の版）から旋律を取り、和音は自作する。1 曲ずつ、原典のページを保存する |
| Silent Night | x04 | 原典の楽譜と照合する |
| Vivaldi「冬」 | w01・w02（と w03） | CC BY-SA 3.0 の条件（表示・同じライセンスでの公開）を満たすか、Public Domain の版に替える。Mutopia の別の版、または初版の楽譜（IMSLP）から旋律を取り直す |
| Der Lindenbaum、Auld Lang Syne | w01・w02（Auld Lang Syne は w05 も） | The Everyday Song Book の書籍スキャンで照合し、照合記録を残す |

### 方法 C：新しいオリジナル曲にする
- 季節の雰囲気（冬の窓辺、鈴、オルゴール）はそのままに、旋律・和声・構成を新しく作る
- 権利の確認は、サンプル（Iowa の録音：制限なし）と自作コードだけで済む
- 「有名なクリスマス曲で探されたい」という検索の狙いは弱くなる。そこは、曲名で探す人向けの方法 B と使い分ける
- 今回の orig01（冬の読書のピアノ）が、この方法の試作にあたる

### Claude のおすすめ
- まずは方法 B-1（同じ曲を Public Domain の原典から作り直す）を、公開予定の早い x03・x05 の Jingle Bells から 1 曲ずつ行う
- 原典のページと照合の結果を、1 曲ごとに表へ追加する
- 有名な曲名で探されるクリスマス動画は検索で強いので、曲は残す価値が高い
- 方法 A は返事待ちの間に並行して出してよい

## 3. 対象の 8 本以外で、同じ問題が見つかったもの（要確認）

| 動画 | 状態（依頼書・GPT の報告による） | 見つかったこと |
|---|---|---|
| x01 Christmas Piano・x02 Christmas Music Box | e7_aVz7byxE「Christmas Music Box」は**公開中**（x02 と思われる。GPT 側で対応を確認してほしい） | 10 曲中 5 曲（O Christmas Tree・Joy to the World・First Noel・Away in a Manger・O Come All Ye Faithful）の旋律が Hardy 版と 100% 一致、和音も一部一致 |
| x06 Silent Night | dnOzVffF1ZA は**公開中**（x06 と思われる） | 旋律の出典の記録がない。原典との照合が必要 |
| w03 Vivaldi Winter | 予約・保留の状態は不明 | Mutopia の CC BY-SA 3.0。表示と継承の条件を満たしていない |
| x09 We Wish You（鈴） | 不明 | 転記サイト 3 版から手で作成。転記サイトの条件が不明 |
| w05 Auld Lang Syne | 不明 | 転記サイトの条件が不明（原典は 1927 年の書籍） |
| Christmas Shorts・Winter Shorts | rrtGfjSd6Ao「a quiet christmas moment」は**公開中**（どの曲かは Claude には分からない） | 上の長尺から切り出しているので、元の曲と同じ判断になる |

公開中の動画をどうするか（非公開に戻す・そのまま・差し替え）は、オーナーの判断事項です。Claude は変更していません。

## 4. 問題のない部分（根拠つき）

- 楽器の録音：University of Iowa の楽器サンプル。ページに「may be downloaded and used for any projects, without restrictions」とある（`data/licenses/LICENSE_TEXTS.md`）
- 伴奏型・音色・テンポ・残響・音量の処理：Claude のコード（`bgm_studio/`）
- Satie・Debussy・Schubert・Gounod の譜面（k01〜k03）：`data/classical/SOURCES.md` に記録済み。Bach Arioso は CC BY 3.0（表示が必要。GPT が説明欄へ追記済みと報告）
- ジャズ（j01）の譜面：`data/jazz/SOURCES.md`（Mutopia の Public Domain 版）
  - All Through the Night は The Everyday Song Book（1927）No.108 の転記と 96% 一致（転記サイトの条件は不明）
  - Amazing Grace は出典の記録がなく、Silent Night と同じく原典との照合が残っている
