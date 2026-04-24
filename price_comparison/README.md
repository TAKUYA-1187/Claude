# 買取せどり 利益商品抽出ツール

買取スキャナーの商品マスタ（全データCSV保存）と、Amazon / 楽天市場 / Yahoo!ショッピングの販売価格を突合し、
**「ECで仕入れて買取店に売ると利益が出る商品」** を自動で抽出する。

GitHub Actions で **毎日 JST 11:00 / 18:00** に更新され、最新結果は `data/output/profitable_latest.csv` にコミットされる。

---

## 全体の流れ

```
買取スキャナー ──(全データCSV保存)──> data/input/*.csv
                                          │
                                          ▼
                          ┌──────────── main.py ────────────┐
                          │  JAN で各 EC を API 検索         │
                          │  最安値を選び、利益を計算        │
                          └──────────────┬───────────────────┘
                                          ▼
                   data/output/profitable_latest.{csv,json}
```

---

## セットアップ

### 1. 買取スキャナーから CSV を取り出す

買取スキャナー トップ → **「全データCSV保存」** からエクスポートし、以下のいずれかに配置する。

#### 方法A (推奨): OneDrive 共有フォルダに置く

OneDrive の「買取スキャナーCSV」フォルダを **「リンクを知っている全員」で共有** し、得られたリンク
（例: `https://1drv.ms/f/...`) を GitHub Secrets の `ONEDRIVE_SHARE_URL` に登録する。
GitHub Actions が実行のたびにフォルダ内の `.csv` をすべて取得してくる。
ローカル実行の場合は `.env` の `ONEDRIVE_SHARE_URL` に同じURLを入れれば自動取得される。

#### 方法B: リポジトリに置く

`price_comparison/data/input/*.csv` に置く（`.gitignore` 対象なのでコミットされない。自分で管理する場合は .gitignore から外す）。

複数ファイルを置いた場合は、同一JANは買取価格の高い方を採用してマージされる。

> ⚠ CSV には最低限「JAN列」と、対象店舗の買取価格列が含まれている必要がある（列名に店舗名が入っていればOK）。

### 2. 対象にする買取店を設定する

デフォルトでは **買取商店** と **ウィキ** の買取価格が付いた商品だけを抽出する。
買取スキャナーのCSVは店舗ごとに列が分かれており、列名に「買取商店」「ウィキ」を含む列を自動検出する。
他の店舗を足したい場合は `ENABLED_SHOPS` を上書きする:

```
ENABLED_SHOPS=買取商店,ウィキ,ブックオフ,駿河屋
```

### 3. API キーを取得する

| サイト | 必要なもの | 取得先 |
| --- | --- | --- |
| Amazon | PA-API 5.0 の AccessKey / SecretKey / PartnerTag | https://affiliate.amazon.co.jp/assoc_credentials/home |
| 楽天市場 | ApplicationID（アフィリエイトIDは任意） | https://webservice.rakuten.co.jp/ |
| Yahoo!ショッピング | Client ID (appid) | https://developer.yahoo.co.jp/webapi/shopping/ |

最低1サイト設定すれば動作する。Amazon は直近のアフィリエイト売上実績がないとAPI利用権限が失われる点に注意。

### 4. ローカル実行

```bash
cd price_comparison
cp .env.example .env   # キーを埋める
pip install -r requirements.txt
python -m src.main --limit 20   # まずは20件で試す
python -m src.main              # 本番 (全件)
```

結果は `data/output/profitable_YYYYMMDD_HHMM.csv` と `profitable_latest.csv`。

### 5. GitHub Actions で自動化する（ステップバイステップ）

#### 5.1 OneDrive 共有リンクを用意する
1. OneDrive で「買取スキャナーCSV」フォルダを右クリック → **共有**
2. リンク設定を **「リンクを知っている全員」** に変更
3. 表示された `https://1drv.ms/f/...` をコピー

#### 5.2 API キーを発行する
| サイト | 取得ページ | 必要な値 |
| --- | --- | --- |
| Amazon | https://affiliate.amazon.co.jp/assoc_credentials/home | Access Key / Secret Key / Tracking ID（PartnerTag） |
| 楽天 | https://webservice.rakuten.co.jp/ → 「アプリID発行」 | applicationId（必須） / affiliateId（任意） |
| Yahoo! | https://developer.yahoo.co.jp/ → 「アプリケーションの管理」でクライアントID発行 | Client ID |

#### 5.3 リポジトリに Secrets を登録する
GitHub 上でリポジトリを開き、**Settings → Secrets and variables → Actions → New repository secret** を押して以下を1つずつ追加:

| Name | Value |
| --- | --- |
| `ONEDRIVE_SHARE_URL` | 5.1 でコピーした URL |
| `AMAZON_ACCESS_KEY` | Amazon の Access Key |
| `AMAZON_SECRET_KEY` | Amazon の Secret Key |
| `AMAZON_PARTNER_TAG` | Amazon の Tracking ID（例: `yourtag-22`） |
| `RAKUTEN_APP_ID` | 楽天の applicationId |
| `RAKUTEN_AFFILIATE_ID` | 楽天の affiliateId（任意） |
| `YAHOO_APP_ID` | Yahoo! の Client ID |

#### 5.4 （任意）利益計算の閾値を調整する
**Settings → Secrets and variables → Actions → Variables → New repository variable** で以下を追加すると動作が変わる（未設定ならデフォルト値）。

| Name | デフォルト | 意味 |
| --- | --- | --- |
| `ENABLED_SHOPS` | `買取商店,ウィキ` | 対象とする買取店（列名マッチ） |
| `SHIPPING_COST` | `600` | 買取店への送料想定（円） |
| `MIN_PROFIT` | `500` | これ以上の利益だけ抽出（円） |
| `MIN_PROFIT_RATE` | `0.15` | これ以上の利益率だけ抽出（0〜1） |

#### 5.5 手動で1回実行して動作確認する
1. リポジトリの **Actions** タブを開く
2. 左カラムの **Price Comparison Update** を選択
3. 右上の **Run workflow** → ブランチを `claude/price-comparison-profit-tool-PQeYK` にして
   **limit** に `20` を入れて **Run workflow**（20件だけで通しテスト）
4. ジョブが緑になったら:
   - **Artifacts** に `profitable-*.zip` が出ている
   - `price_comparison/data/output/profitable_latest.csv` が自動コミットされている
5. 問題なければ `limit` を空にして本番実行、または cron に任せる

#### 5.6 スケジュール運用
ワークフローは **JST 11:00 / 18:00**（UTC 02:00 / 09:00）に自動起動する。cron 定義:
```yaml
schedule:
  - cron: "0 2,9 * * *"
```
GitHub の schedule は UTC かつ高負荷時に数分遅延することがある。時刻を変えたい場合は `.github/workflows/price_comparison.yml` を書き換えて push。

> ⚠ public リポジトリの場合、Actions のログにキーが出る心配はない（Secrets は `***` でマスクされる）が、OneDrive の共有 URL は Secrets に入れておくのが安全。

---

## 出力フォーマット

`profitable_latest.csv` の列:

| 列 | 意味 |
| --- | --- |
| jan | JAN コード |
| name | 商品名（CSV に含まれていれば） |
| buy_price | 買取店が支払う金額（対象店舗の最高値） |
| buy_shop | 最高値を付けた店舗 (`買取商店` / `ウィキ` 等) |
| purchase_price | EC 最安仕入れ価格 |
| purchase_source | 最安サイト (amazon / rakuten / yahoo) |
| amazon_price / rakuten_price / yahoo_price | 各サイト価格（取得できたもの） |
| shipping | 送料の概算 |
| profit | 利益 = 買取 − 仕入れ − 送料 |
| profit_rate | 利益率 = profit / purchase_price |

並び順は `profit` 降順。

---

## 利益計算モデル

```
profit = buy_price − purchase_price − SHIPPING_COST
profit_rate = profit / purchase_price
```

抽出条件: `profit >= MIN_PROFIT` **かつ** `profit_rate >= MIN_PROFIT_RATE`（両方環境変数で調整可）。

※ 買取時の送料・決済手数料・税は送料枠に丸めている。厳密な計算が必要な場合は `profit_calculator.py` を拡張する。

---

## 家電量販店の対応について

ヨドバシ・ビックカメラ・ヤマダ電機などは公式価格APIを提供していないため、初期スコープ外。
必要になったら `価格.com API` や各社の RSS / 公開エンドポイントを使った取得モジュールを `src/` に追加する想定。

---

## ファイル構成

```
price_comparison/
├── .env.example
├── README.md
├── requirements.txt
├── data/
│   ├── input/          # ここに買取スキャナーの CSV を置く
│   └── output/         # 結果 (latest は git commit される)
└── src/
    ├── amazon_client.py
    ├── config.py
    ├── csv_loader.py
    ├── main.py
    ├── onedrive_fetcher.py
    ├── profit_calculator.py
    ├── rakuten_client.py
    └── yahoo_client.py
```
