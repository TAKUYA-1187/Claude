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

買取スキャナー トップ → **「全データCSV保存」** からエクスポートし、`price_comparison/data/input/` に置く。
複数ファイルを置いた場合は、同一JANは買取価格の高い方を採用してマージされる。

> ⚠ CSV には最低限「JAN列」と「買取価格列」が含まれている必要がある。列名は日本語/英語どちらでもOK（`csv_loader.py` に別名マップあり）。

### 2. API キーを取得する

| サイト | 必要なもの | 取得先 |
| --- | --- | --- |
| Amazon | PA-API 5.0 の AccessKey / SecretKey / PartnerTag | https://affiliate.amazon.co.jp/assoc_credentials/home |
| 楽天市場 | ApplicationID（アフィリエイトIDは任意） | https://webservice.rakuten.co.jp/ |
| Yahoo!ショッピング | Client ID (appid) | https://developer.yahoo.co.jp/webapi/shopping/ |

最低1サイト設定すれば動作する。Amazon は直近のアフィリエイト売上実績がないとAPI利用権限が失われる点に注意。

### 3. ローカル実行

```bash
cd price_comparison
cp .env.example .env   # キーを埋める
pip install -r requirements.txt
python -m src.main --limit 20   # まずは20件で試す
python -m src.main              # 本番 (全件)
```

結果は `data/output/profitable_YYYYMMDD_HHMM.csv` と `profitable_latest.csv`。

### 4. GitHub Actions で自動化する

**リポジトリ Secrets (Settings → Secrets and variables → Actions → Secrets)** に登録:

- `AMAZON_ACCESS_KEY`
- `AMAZON_SECRET_KEY`
- `AMAZON_PARTNER_TAG`
- `RAKUTEN_APP_ID`
- `RAKUTEN_AFFILIATE_ID`（任意）
- `YAHOO_APP_ID`

**Variables (任意、利益計算の調整)**: `SHIPPING_COST`, `MIN_PROFIT`, `MIN_PROFIT_RATE` など。

ワークフロー `.github/workflows/price_comparison.yml` が JST 11:00 / 18:00（UTC 02:00 / 09:00）に起動し、
`data/output/profitable_latest.csv` を自動コミット＋30日間のアーティファクト保存を行う。

手動実行: **Actions タブ → Price Comparison Update → Run workflow**。

---

## 出力フォーマット

`profitable_latest.csv` の列:

| 列 | 意味 |
| --- | --- |
| jan | JAN コード |
| name | 商品名（CSV に含まれていれば） |
| buy_price | 買取店が支払う金額 |
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
    ├── profit_calculator.py
    ├── rakuten_client.py
    └── yahoo_client.py
```
