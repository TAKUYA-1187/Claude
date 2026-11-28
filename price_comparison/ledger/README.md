# 商品管理台帳への自動取込

朝レポート（買取商店×Yahoo!）の出力を、台帳（price_comparison/ledger_data/）へ取り込みます。

## 自動で行われること（GitHub Actions「Price Comparison Update」の中）
1. 買取商店のカタログ取得とYahoo!価格の突合（既存の処理）
2. import_kaitori_report.py がデータ日時を特定する
   - 今回の実行で更新されたファイル → ファイルの更新日時
   - 更新されなかったファイル → gitの最終コミット日時（＝前回取得時点）
3. データ日時が36時間より古い場合は取り込まずに終了（台帳は変わらない）
4. 新しい場合は ledger.py のルールで取込
   - 中古の行は抽出基準外のため取り込まない（件数だけログに出す）
   - 除外リスト（excluded.csv）にある商品は取り込まない
   - JAN・ASIN・型番で同じ商品をまとめる。価格が変わったときだけ history.csv に記録する
   - 仕入送料・振込手数料・在庫はレポートに無いので「未確認（暫定）」になる
5. master.csv / history.csv / excluded.csv をコミットする

## 手作業で残る箇所：Googleスプレッドシートへの反映
この環境にはGoogleスプレッドシートを直接編集するコネクタがないため、反映は手作業です。

1. GitHubで TAKUYA-1187/Claude を開き、ブランチを claude/resale-profit-analysis-nhbnaz に切り替える
2. price_comparison/ledger_data/master.csv を開き、右上の「Download raw file」（下向き矢印のアイコン）をクリックしてダウンロードする
3. 台帳 https://docs.google.com/spreadsheets/d/129FFpJ7kVOGE0rPRcVWZ7NVXdBTLZqxSMA5dfH7wUoM/edit を開き、下部の「商品台帳」タブをクリックする
4. メニューの「ファイル」→「インポート」→「アップロード」で、2のファイルを選ぶ
5. 「インポート場所」で「現在のシートを置換する」を選び、「データをインポート」をクリックする
   - 成功すると1行目が見出し（商品キー、調査日時、商品名…）、2行目以降に商品が並ぶ
   - 「現在のシートを置換する」以外を選ぶと新しいタブや重複行ができる。間違えた場合は「編集」→「元に戻す」
6. 価格履歴は history.csv を使い、「価格履歴」タブで同じ手順を行う
7. 除外リストを変更したいときは、シートではなく excluded.csv を編集する（シートは表示用。正はCSV）

文字化けする場合：インポート画面の「区切り文字の種類」を「カンマ」にし、それでも崩れる場合はファイルをGoogleドライブにアップロードしてから「Googleスプレッドシートで開く」で確認してください。

## 手動で動かす場合
```
cd price_comparison/ledger
python3 import_kaitori_report.py --report ../data/output/kaitorishouten_all_latest.csv --ledger-dir ../ledger_data
python3 -m unittest test_ledger test_import
```
終了コード: 0=取込完了 / 1=要確認の行あり（台帳は更新済み）/ 2=データが古いため取込中止
