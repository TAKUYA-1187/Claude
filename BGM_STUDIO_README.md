# BGM Studio — 海外向け YouTube BGM チャンネル一式

英語圏（アメリカ・オーストラリア・イギリス・カナダ）向けの BGM チャンネルを
立ち上げるための **市場戦略 + 音源・映像の生成システム** です。

外部の音源素材・ストック映像を**一切使わず**、numpy だけで
音楽・環境音・映像をすべて手続き的に合成します。

---

## これは何を作るのか

**2時間24分のループBGM動画を10本**、それぞれ別ジャンルで。

| # | 動画 | 用途 | BPM | キー |
|---|---|---|---|---|
| 01 | Rainy Lofi Study Beats | 勉強 | 78 | Am |
| 02 | Deep Sleep Ambient | 睡眠 | 52 | Am |
| 03 | Piano & Rain | くつろぎ | 62 | C |
| 04 | Cozy Coffee Shop Jazz | 作業 | 96 | C |
| 05 | Bossa Nova Cafe | 作業 | 124 | G |
| 06 | Healing Meditation 432Hz | 睡眠 | 48 | Dm |
| 07 | Fireplace Winter Jazz | くつろぎ | 88 | F |
| 08 | Ocean Waves Ambient | 睡眠 | 50 | G |
| 09 | Fantasy Tavern Ambience | 作業 | 84 | Dm |
| 10 | Deep Focus Flow | 勉強 | 60 | Am |

各動画には次が付属します。

- 24分の完全ループ音源（−14 LUFS / −1 dBTP でマスタリング済み）
- 20秒ループの1080p映像（ジャンルごとに別シーン）
- サムネイル（1280×720）
- タイトル・説明文・タグ（そのままYouTubeに貼れる）

---

## ドキュメント

| ファイル | 内容 |
|---|---|
| [docs/01_market_research.md](docs/01_market_research.md) | **どの国を狙うか。** RPM/CPMの実勢、収益化ポリシー、収益シミュレーション |
| [docs/02_genre_strategy.md](docs/02_genre_strategy.md) | **どのジャンルが効くか。** 飽和度の分析、動画尺の設計、10本の選定理由 |
| [docs/03_production_spec.md](docs/03_production_spec.md) | **制作仕様。** ループを継ぎ目なく作る仕組み、モジュール構成 |
| [docs/04_upload_playbook.md](docs/04_upload_playbook.md) | **運用。** タイトル/サムネ/説明文の型、投稿時刻、90日プラン |
| [docs/05_launch_runbook.md](docs/05_launch_runbook.md) | **ゼロから収益化までの完全手順書。** アカウント開設・電話確認・AdSense・米国税務情報・振込まで |

> 🚀 **これから始める方は [docs/05_launch_runbook.md](docs/05_launch_runbook.md) から読んでください。**
> 「今日やること」から順に並べてあります。

### 3行でまとめると

1. **主戦場はアメリカ。** オーストラリアは単価が高く時差の相性も良いが、市場規模がUSの1/12なので主軸にはしない。
2. **Lofiと自然音の直球参入はしない。** 需要は最大だが飽和も最大。カフェジャズ・ボサノヴァ・ファンタジー系が穴場。
3. **2025年7月の「Inauthentic content」ポリシーが最大のリスク。** 全部オリジナル生成＋週2〜4本のペース厳守で回避する。

---

## セットアップ

```bash
pip install -r requirements.txt
```

必要なのは `numpy`, `pillow`, `imageio-ffmpeg` だけです。
`imageio-ffmpeg` に ffmpeg 本体が同梱されるので、別途インストールは不要です。

## 実行

```bash
# 全10本を書き出す（2〜3時間、ディスク10〜12GB）
python3 render_bgm.py

# 音源とメタデータだけ（映像をスキップ）
python3 render_bgm.py --no-video

# 動作確認（3分の動画が1本できる）
python3 render_bgm.py --tracks 04_cozy_coffee_jazz --seconds 60 --repeats 3

# 8時間版（同じ24分音源を20周）
python3 render_bgm.py --repeats 20
```

出力は `out/` 以下に生成されます（Git管理外）。

```
out/
  audio/      24分のループ音源 (WAV 24bit)
  video/      2時間24分の本編 (MP4)      ← これをアップロードする
  visual/     20秒のループ映像
  thumbnail/  サムネイル (PNG)
  metadata/   タイトル・説明文・タグ (JSON)
  preview/    90秒の試聴用 (MP3)
  report.json 検証結果
```

---

## リポジトリに入っているもの / 入っていないもの

| | |
|---|---|
| ✅ 入っている | 生成コード、戦略ドキュメント、サムネイル、メタデータ、90秒プレビュー音源 |
| ❌ 入っていない | 2時間24分のMP4本編、24分のWAVマスター（合計10GB超のため） |

**本編の動画は手元で `python3 render_bgm.py` を実行して生成してください。**
シードが固定されているので、何度実行しても同じ音源・同じ映像が再現されます。

---

## 別バージョンを作る

同じジャンルで違う曲が欲しいときは `bgm_studio/tracks.py` の `seed` を変えるだけです。
コード進行・メロディ・ドラムパターン・環境音がすべて別物になります。

```python
TrackSpec(slug="01b_lofi_rainy_study", ..., seed=1012)   # 1011 → 1012
```

> ⚠️ **同じ音源を使い回して複数本アップするのは絶対にNG**です。
> YouTubeの Inauthentic content ポリシー違反になり、収益化が取り消されます。
> 必ず seed を変えて別の曲として生成してください。

---

## 技術的にいちばん難しかったところ

**「2時間ループしても継ぎ目でプチッと鳴らない」**を成立させること。
普通に作ると必ず鳴ります。対策は4つ入っています。

1. **ループ長を秒で固定し、BPMを逆算する** — サンプル数に端数を出さない
2. **残響を先頭へ折り返す（fold_tail）** — 末尾の余韻を次の周回の頭として巡回加算
3. **環境音を周期信号として生成する** — ノイズもフィルタも巡回版で作る
4. **マスタリングも巡回で適用する** — EQもリミッタも前後を巻き付けてから処理

詳細は [docs/03_production_spec.md](docs/03_production_spec.md) の §2 に書いてあります。
検証結果は `out/report.json` の `loop_seam_db`（0dB以下が合格）で確認できます。
