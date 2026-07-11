# Pharma News Digest（腎臓領域 日次ニュースダイジェスト）

ノバルティス 腎臓領域（**ファビハルタ／IgA腎症**）担当者向けに、関連ニュース・
医療業界動向・最新論文を **毎朝 7:00 (JST)** に自動でメール配信するツールです。

- 送信元：Gmail（`taku.ino.19811014@gmail.com`）または iCloud（`takuya0.0@icloud.com`）
- 配信先：`takuya.inoue@novartis.com`

## 配信内容（メール構成）

| セクション | 内容 | ソース |
|---|---|---|
| 🎯 ファビハルタ／IgA腎症 | 自社製品・注目領域の直近ニュース | Google ニュース |
| 🧬 腎臓・競合パイプライン | フィルスパリ／ネフェコン／sibeprenlimab 等 | Google ニュース |
| 🏛 国内 医療・製薬業界 | ノバルティス・薬価・規制・情報誌（RISFAX 等）関連の公開見出し | Google ニュース |
| 🌏 世界のアップデート | グローバル承認・規制・企業動向 | Google ニュース（英語） |
| 📄 最新論文 | iptacopan / IgA nephropathy / 補体 等の新着論文 | PubMed・Europe PMC |

前日までに配信した記事は `state/seen_ids.json` で管理し、**再掲しません**。

## アーキテクチャ

毎朝の配信は **GitHub Actions のスケジュール実行**で動きます。特定の PC や
サーバーを常時起動しておく必要はありません（`.github/workflows/pharma_news_digest.yml`）。

```
GitHub Actions (毎日 22:00 UTC = 07:00 JST)
  └─ python -m src.main
       ├─ Google ニュース RSS / PubMed / Europe PMC から収集
       ├─ 重複・既読を除外し HTML ダイジェストを生成
       └─ Gmail SMTP で 2 アドレスへ送信
```

## セットアップ（初回のみ）

### 1. 送信元のアプリパスワードを発行

送信元は Gmail か iCloud のどちらでも構いません。**通常のログインパスワードでは SMTP 送信できない**ため、必ず専用のアプリパスワードを発行してください。

- **Gmail の場合**：Google アカウント → **セキュリティ** → **2 段階認証** を有効化 → **アプリパスワード**（16 桁）を発行
- **iCloud の場合**：appleid.apple.com → **サインインとセキュリティ** → **App 用パスワード** を発行

### 2. GitHub リポジトリに Secrets / Variables を登録

リポジトリの **Settings → Secrets and variables → Actions** で登録します。

| 種別 | 名前 | 値 |
|---|---|---|
| Secret | `SENDER_EMAIL` | 送信元アドレス（Gmail か iCloud） |
| Secret | `SENDER_APP_PASSWORD` | 上記で発行したアプリパスワード |
| Secret | `NCBI_API_KEY` | （任意）PubMed のレート制限緩和用 |
| Variable | `SMTP_HOST` | iCloud 送信時のみ `smtp.mail.me.com`（Gmail は不要） |
| Variable | `SMTP_PORT` | iCloud 送信時のみ `587`（Gmail は不要、既定 465） |
| Variable | `RECIPIENTS` | （任意）配信先を変える場合のみ。既定 `takuya.inoue@novartis.com` |

Gmail を使う場合は `SENDER_EMAIL` と `SENDER_APP_PASSWORD` の 2 つだけで動きます。
iCloud を使う場合のみ `SMTP_HOST` / `SMTP_PORT` の Variable を追加してください。
登録すれば翌朝から自動配信が始まります。

### 3. 手動テスト

- GitHub 上：**Actions → Pharma News Digest → Run workflow**（`dry_run=true` で送信せず HTML を artifact に出力）
- ローカル：

```bash
cd pharma_news_digest
pip install -r requirements.txt
cp .env.example .env   # 値を編集
python -m src.main --dry-run   # out.html を生成、送信しない
python -m src.main             # 実際に送信
```

## 配信時刻の変更

`.github/workflows/pharma_news_digest.yml` の cron を編集します（UTC 指定）。

```yaml
- cron: "0 22 * * *"   # 07:00 JST。例えば 06:00 JST にするなら "0 21 * * *"
```

## RISFAX など情報誌について

RISFAX（じほう）等の情報誌は**有料購読**が前提で、本文の自動取得・再配布はできません。
本ツールでは公開インデックスされた**見出し**のみを「国内 医療・製薬業界ニュース」に含めています。
本文は各媒体のご購読でご確認ください。

## 注意

- Google ニュース RSS は非公式利用のため、仕様変更で取得できなくなる可能性があります。
- 各ソースは個別に例外処理しており、1 つが失敗しても他のセクションは配信されます。
