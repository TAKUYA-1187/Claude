# Amazon 刈り取り 値下がりアラート

Amazon.co.jp 全商品の価格推移を **Keepa API** でモニターし、大幅な値下がりが発生したら
**即時メール通知** する。通常価格に戻ったときに売り捌く「刈り取り」仕入れの起点となるツール。

- 監視対象: Keepa がトラッキングしている Amazon.co.jp 全商品（Deal API で横断検索）
- 通知条件: **30日平均から 30% 以上 かつ 1,000円以上** の値下がり（変更可）
- 絞り込み: **新品出品者 3名以上**（独占販売・メーカー直販のみの商品は除外）
- 通知先: `taku.ino.19811014@gmail.com`（不動産の朝レポートと同じ宛先。`ALERT_EMAIL_TO` で変更可）
- 実行間隔: GitHub Actions で **15分ごと**（Actions のスケジュール実行の実用最短間隔）

---

## 仕組み

```
Keepa Deal API ──(直近24hに新品価格が大幅下落した商品)──> 候補ASIN
                                │
                                ▼
Keepa Product API ──(現在価格 / 30日平均 / 新品出品者数を検証)
                                │
                                ▼
   フィルタ: 下落率30%以上 & 下落額1,000円以上 & 出品者3名以上
                                │
                                ▼
        未通知のものだけ Gmail SMTP で即時メール送信
        (data/alerted_asins.json に記録し、72時間は同一ASINを再通知しない。
         ただし前回通知よりさらに5%以上下がったら再通知)
```

> **なぜ Keepa か**: Amazon 公式 API (PA-API/SP-API) には「全商品の値下がり検索」も価格履歴もない。
> 刈り取りせどらーが実運用しているのは Keepa の価格トラッキングで、
> Deal API はまさに「直近で大きく下がった商品」を全カテゴリ横断で返してくれる。

---

## セットアップ

### 1. Keepa API キーを取得（必須・有料）

1. https://keepa.com/#!api で API プランを契約（トークン制の月額サブスク。一番安いプランでOK）
2. 発行された API キーをコピー

> 15分間隔の実行なら 1日 ≈ 96回 × (Deal 5トークン + Product 検証分) 程度。
> 最小プラン（20トークン/分）で十分収まる。

### 2. Gmail アプリパスワードを発行

1. Google アカウント → セキュリティ → 2段階認証 を有効化
2. 「アプリパスワード」で16桁のパスワードを発行（extract_receipts で発行済みならそれを流用可）

### 3. GitHub Secrets / Variables を登録

**Settings → Secrets and variables → Actions** で以下を登録:

| 種別 | Name | Value |
| --- | --- | --- |
| Secret | `KEEPA_API_KEY` | Keepa の API キー |
| Secret | `SMTP_USER` | 送信元 Gmail アドレス |
| Secret | `SMTP_PASSWORD` | Gmail アプリパスワード（16桁） |
| Variable (任意) | `ALERT_EMAIL_TO` | 通知先（省略時: taku.ino.19811014@gmail.com、カンマ区切りで複数可） |

抽出条件を変えたい場合は Variables に追加（省略時はデフォルト値）:

| Name | デフォルト | 意味 |
| --- | --- | --- |
| `MIN_DROP_PERCENT` | `30` | 30日平均からの下落率(%) |
| `MIN_DROP_YEN` | `1000` | 下落額(円) |
| `MIN_SELLERS` | `3` | 新品出品者数の下限（独占販売除外） |
| `MIN_PRICE` | `1500` | 現在価格の下限（低単価ノイズ除外） |
| `MAX_PRICE` | `300000` | 現在価格の上限 |
| `MAX_SALES_RANK` | `80000` | 売れ筋ランキング上限（回転しない商品を除外） |

### 4. 動作確認

1. **Actions** タブ → **Amazon Price Drop Alerts** → **Run workflow**
2. まず `dry_run` に `1` を入れて実行 → ログで抽出結果を確認
3. 問題なければ `dry_run` を空にして実行 → メールが届くことを確認
4. あとは15分ごとの自動実行に任せる

### ローカル実行

```bash
cd amazon_price_alerts
cp .env.example .env   # キーを埋める
pip install -r requirements.txt
python -m src.main --dry-run   # まず送信なしで確認
python -m src.main             # 本番
```

---

## 運用のヒント

- **即時性**: GitHub Actions の schedule は最短でも数分〜15分の粒度で、高負荷時は遅延する。
  秒単位の即時性が必要になったら、Keepa 本体の「トラッキング機能」（Webhook/メール通知）併用か、
  常時起動サーバー（VPS等）での実行に移行する。
- **仕入れ判断**: メール内の Keepa グラフリンクで「戻り価格」（下落前の安定価格）と
  ランキング推移（回転数）を必ず確認。瞬間的な価格エラーは規約リスクがあるので深追いしない。
- **出品者数フィルタ**: 出品者3名以上 = 相乗り可能なカート争いのある商品。
  独占販売（メーカー直販のみ・出品規制）の商品は自動で除外される。

## ファイル構成

```
amazon_price_alerts/
├── README.md
├── .env.example
├── requirements.txt
├── data/
│   └── alerted_asins.json   # 通知済み記録 (workflow が自動コミット)
└── src/
    ├── config.py       # 環境変数の読み込み・閾値設定
    ├── keepa_client.py # Keepa Deal / Product API クライアント
    ├── deal_filter.py  # 刈り取り条件フィルタ (下落率・出品者数)
    ├── state.py        # 再通知抑制の状態管理
    ├── emailer.py      # Gmail SMTP でアラート送信
    └── main.py         # エントリポイント
```
