# 04. 投稿運用プレイブック

最終更新: 2026-08-08

---

## 1. タイトルの型

### ルール

1. **主要キーワードを最初の5語に入れる**（検索とCTRの両方に効く）
2. **絵文字を1つだけ**。2つ以上は安っぽく見える
3. **時間を必ず入れる**（"2 Hours"）— 「つけっぱなしにできる」ことが最大の訴求
4. **用途を入れる**（Sleep / Study / Work / Relax）— 検索クエリそのもの
5. 全角換算で50〜70文字。モバイルで切れないように

### 型

```
[ジャンル/シーン] [絵文字1つ] [時間] of [雰囲気] for [用途]
```

### 本プロジェクトの10本（そのまま使えます）

| # | タイトル |
|---|---|
| 01 | `Rainy Lofi Beats to Study & Relax 🌧️ 2 Hours of Chill Hip Hop` |
| 02 | `Deep Sleep Music 😴 Fall Asleep Fast — 2 Hours of Calm Ambient & Rain` |
| 03 | `Relaxing Piano & Rain Sounds 🎹 2 Hours for Sleep, Study & Stress Relief` |
| 04 | `Cozy Coffee Shop Jazz ☕ 2 Hours of Warm Jazz Piano for Work & Study` |
| 05 | `Bossa Nova Cafe 🌿 2 Hours of Smooth Brazilian Jazz for a Good Mood` |
| 06 | `432Hz Healing Meditation Music 🧘 2 Hours of Singing Bowls for Deep Relaxation` |
| 07 | `Fireplace Jazz 🔥 2 Hours of Warm Winter Jazz & Crackling Fire` |
| 08 | `Ocean Waves & Ambient Music 🌊 2 Hours of Calm Sea Sounds for Sleep` |
| 09 | `Medieval Tavern Ambience 🍺 2 Hours of Fantasy Music & Crackling Fire` |
| 10 | `Deep Focus Music 🧠 2 Hours of Ambient Flow State Music for Studying & Work` |

> ⚠️ 動画の実尺は 2時間24分です。「2 Hours」表記は
> 「2時間以上ある」という意味で正確なので問題ありませんが、
> 気になる場合は `2.5 Hours` に変えてください（実尺より長い表記はNG）。

---

## 2. サムネイル

### ルール

CTR は YouTube の最重要ランキング要因です。BGMのサムネは
**「一目で用途と雰囲気が分かる」**ことが全てです。

| 項目 | 指針 |
|---|---|
| 文字数 | **3〜4語まで。** それ以上は読まれない |
| フォント | 太いサンセリフ。**モバイルサイズで読めること**が絶対条件 |
| 視覚要素 | **2〜3個まで。** 詰め込むと何も伝わらない |
| 文字の内容 | タイトルの繰り返しにしない。**補完**する |
| コントラスト | 高く。暗い背景 + 明るい文字が基本 |
| 一貫性 | **同じ枠・同じフォント・同じ位置を全動画で守る** |

> 一貫したサムネのブランディングをしているアーティストは、
> バラバラな場合と比べて **CTR が 15〜25% 高い**という報告があります。
> BGMチャンネルでは「並んだときに自分のチャンネルだと分かる」ことが特に重要です。

### 本プロジェクトの実装

`out/thumbnail/*.png` に 1280×720 で出力されます。
全10本で同じレイアウト（下部に暗幕＋2行の中央揃え、太字＋黒縁取り）を使っています。

```
LOFI RAIN            ← 1行目: 白・大（ジャンル）
2 HOURS · STUDY      ← 2行目: 琥珀色・小（時間と用途）
```

---

## 3. 説明文

`out/metadata/*.json` の `description` をそのまま貼れます。構成は次の通り。

```
1行目   タイトルと同じ文言（検索インデックス用に最重要キーワードを冒頭に）
        ↓
概要    何時間の、どういう音楽か。1〜2文
        ↓
▶ WHAT THIS IS       オリジナル制作であることを明示 ← ポリシー対策として重要
▶ ABOUT THIS TRACK   BPM / キー / 調律 / 長さ
▶ HOW TO USE         用途（勉強・睡眠・作業・店舗BGM）
        ↓
CTA     高評価とチャンネル登録の依頼（1文だけ。しつこくしない）
        ↓
#ハッシュタグ 3つ
        ↓
フッター 「この動画の音楽と映像はすべてこのチャンネルのために制作されました」
```

**最後のフッターは必ず残してください。** Inauthentic content ポリシーに対して
「人間の付加価値がある」ことを外形的に示す一文になります。

### タイムスタンプについて

**2時間のループBGMにチャプターは付けないでください。**

- 曲が切り替わるコンピレーションなら有効ですが、
- 本プロジェクトのようなシームレスなループでは、チャプターを付けると
  **視聴者がスキップし始めて総再生時間が落ちます。**

「つけっぱなしにさせる」ことが目的なので、区切りを見せないほうが有利です。

---

## 4. タグ・設定

| 項目 | 設定 |
|---|---|
| カテゴリ | **音楽** |
| 動画の言語 | **英語** |
| 字幕 | 不要（歌詞なし） |
| 子ども向け | **いいえ**（重要。「はい」にすると広告単価が激減する） |
| タグ | `out/metadata/*.json` の `tags`（6〜8個。詰め込みすぎない） |
| 再生リスト | 用途別に4つ（Sleep / Study / Work / Relax） |
| 終了画面 | **同じ用途の別動画**へ誘導（連続再生を狙う） |
| AI開示 | 該当なし（実在の人物・場所を模した合成コンテンツではないため） |

---

## 5. 投稿時刻 — 日本から運用する場合の最適解

BGMは「これから寝る/作業する」タイミングで検索されます。
**現地の 20:00〜24:00** に公開のピークを合わせるのが基本です。

| 狙う市場 | 現地時刻 | **日本時間（JST）** | 割り当てるジャンル |
|---|---|---|---|
| **アメリカ東部** | 22:00 EST | **翌 12:00**（昼） | 睡眠・リラックス系 |
| **アメリカ西部** | 22:00 PST | **翌 15:00**（午後） | 睡眠系 |
| **オーストラリア** | 22:00 AEST | **21:00**（夜） | 睡眠系 |
| **オーストラリア（朝）** | 08:00 AEST | **07:00**（朝） | 作業・カフェ系 |
| **イギリス** | 21:00 GMT | **翌 06:00**（早朝） | ※予約投稿で対応 |

> **これが日本発チャンネルの最大の利点です。**
> アメリカ向けの睡眠BGMは「日本の昼」に投稿すればよく、深夜作業が一切要りません。
> オーストラリア向けは「日本の夜21時」でちょうど良い。
> どちらも生活リズムを壊さずに主要市場のゴールデンタイムを取れます。

（夏時間の期間はAUが+1時間ずれます。JST 20:00 に読み替えてください）

---

## 6. 投稿ペース

### 絶対に守ること

**週2〜4本。1日1本を超えない。**

コードで量産できるからといって1日に何本も投下すると、
その瞬間に「mass-produced」の外形要件に当てはまり、収益化が飛びます。
ここが本プロジェクト最大の落とし穴です。

### 推奨スケジュール（週3本）

| 曜日 | 時刻(JST) | 枠 | 内容 |
|---|---|---|---|
| 火 | 12:00 | US睡眠枠 | Sleep / Piano & Rain / Ocean |
| 木 | 21:00 | AU睡眠枠 | Sleep / Healing |
| 土 | 07:00 | AU朝＋US夕方 | Cafe Jazz / Bossa / Lofi / Focus |

---

## 7. 90日プラン

### 0〜30日: 土台

- [ ] 10本すべてを公開（週3本ペースなので約3.5週間）
- [ ] チャンネルアート・アイコン・概要欄を英語で整備
- [ ] 用途別の再生リスト4つを作成し、全動画を登録
- [ ] 終了画面を全動画に設定（同用途の別動画へ）
- [ ] **Shorts を週3本**（§8）

### 31〜60日: 検証

- [ ] アナリティクスで**視聴者の上位地域**を確認 → US/AU/UK/CA が上位か
- [ ] インプレッションのCTRを確認 → 3%未満のものはサムネを差し替え
- [ ] 平均視聴時間を確認 → 極端に短い動画は冒頭30秒を疑う
- [ ] 伸びた1〜2ジャンルを特定し、**seedを変えた第2弾**を作る
- [ ] 収益化条件（登録者1,000 / 4,000時間）の進捗を確認

### 61〜90日: 集中

- [ ] 勝ちジャンルに投稿を寄せる（当たったジャンルを3本に1本の比率へ）
- [ ] 8時間版を1本作る（`--repeats 20`）→ 再生時間を一気に稼ぐ
- [ ] 11月が近ければ **Fireplace Winter Jazz を前倒しで強化**（季節単価が跳ねる）
- [ ] 音源をディストリビューター経由で配信登録（§9）

---

## 8. Shorts — 登録者1,000人を突破する唯一の現実的手段

### なぜ必要か

BGMチャンネルのボトルネックは**再生時間ではなく登録者数**です。

- 2時間動画なら **2,000回の完全視聴で4,000時間**に届きます
- 一方でBGMは「つけっぱなしにして去る」ので、**登録ボタンが押されにくい**

### 注意点

**Shorts の再生時間は 4,000時間 にカウントされません。**
Shorts は「登録者を集める装置」と割り切ってください。

### 作り方

- 長尺動画から**最も気持ちいい30〜45秒**を切り出す
- 縦型（1080×1920）にトリミング
- 冒頭2秒でジャンルが分かる文字を入れる（例: "2 hours of coffee shop jazz ☕"）
- 概要に「full 2-hour version on the channel」

```bash
# 長尺から Shorts 用の縦動画を切り出す例
ffmpeg -ss 300 -t 40 -i out/video/04_cozy_coffee_jazz.mp4 \
  -vf "crop=608:1080:656:0,scale=1080:1920" -c:a copy shorts_04.mp4
```

---

## 9. AdSense だけで終わらせない

音楽の広告単価は全カテゴリでも下位です。同じ制作物で収益源を増やしてください。

| 収益源 | 内容 | 備考 |
|---|---|---|
| **AdSense** | YouTube広告 | RPM $1.5〜5 |
| **ストリーミング配信** | Spotify / Apple Music に24分音源を分割配信 | ディストリビューター経由 |
| **Content ID 登録** | 自分の音源を登録しておく | **他人からの誤申立てが約90%減る**という報告あり |
| **商用BGMライセンス** | 店舗・飲食店・オフィス向け | Cafe Music BGM channel の主力事業 |
| **メンバーシップ / Patreon** | 広告なし版・先行公開 | 登録者1万人以降 |

### Content ID について

自作音源でも、**他人が先に登録していると誤申立てを受ける**ことがあります。
ディストリビューター経由で自分の音源を Content ID に登録しておくと、

- 誤申立てが大幅に減る
- 万一の紛争も平均12日程度で解決（未登録だと30日以上）

本プロジェクトの音源は**生成コードが丸ごと残っている**ので、
制作の証明が必要になった場合はリポジトリの履歴とシードを提示できます。

---

## 10. 絶対にやってはいけないこと

1. **同じ音源をタイトル・サムネだけ変えて複数本アップする** ← 一発でアウト
2. **1日に何本も投稿する** ← mass-produced 判定
3. **フリー素材のBGMをそのまま束ねる** ← オリジナリティ皆無＋Content IDリスク
4. **医療的な効能を断定する**（「不眠症が治る」「432Hzが病を癒す」）
   ← ポリシー違反＋広告単価の低下
5. **子ども向け「はい」に設定する** ← 広告単価が激減
6. **−14 LUFS を超えて音圧を上げる** ← YouTubeに下げられるだけで無意味
7. **2時間ループにチャプターを付ける** ← スキップを誘発し総再生時間が落ちる
8. **サムネのフォーマットを毎回変える** ← ブランドが育たずCTRが落ちる
9. **日本語をタイトル・説明文に混ぜる** ← 英語圏の検索から外れる
10. **3ヶ月で結果が出ないと諦める** ← BGMはストック型。伸びるのは6ヶ月以降

---

## 出典

- [YouTube Thumbnail Best Practices for Higher CTR in 2026 – GrowthOS](https://growthos.in/blog/youtube-thumbnail-best-practices)
- [YouTube Thumbnail Strategy for Music Videos (2026) – Chartlex](https://www.chartlex.com/blog/marketing/youtube-thumbnail-strategy-music-videos-2026)
- [YouTube SEO for Musicians 2026 – Chartlex](https://www.chartlex.com/blog/marketing/youtube-channel-seo-musicians-2026)
- [YouTube Partner Program Requirements (2026) – vidIQ](https://vidiq.com/blog/post/youtube-partner-program-guide/)
- [YouTube Partner Program Requirements 2026 – YouTube Tools Hub](https://www.youtubetoolshub.com/blog/youtube-partner-program-requirements-2026)
- [Content ID Music: 2026 YouTube Guide To Monetization – Foxi](https://www.foximusic.com/blog/content-id-music-guide-monetization/)
- [YouTube Loudness Target – APU Software](https://apu.software/youtube-audio-loudness-target/)
- [Cafe Music BGM channel / BGMC Records](https://www.bgmcrecords.com/)
