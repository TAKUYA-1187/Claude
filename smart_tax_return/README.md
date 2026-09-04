# スマート確定申告 — 運用一式

確定申告代行サービス「スマート確定申告」への四半期資料提出を、チャットではなく
**ワーク（このリポジトリ）で回すための一式**。チャット側で運用していたスキルと作業記録を
2026年9月5日にここへ移した。

---

## まずここを見る

| 知りたいこと | 見る場所 |
|---|---|
| 次に何をすればいいか | このリポジトリでセッションを開き「スマート確定申告の7-12月分を始めたい」と言う。スキルが Phase 1（棚卸し）から案内する |
| 直近の状態 | [`records/2026-04-06.md`](records/2026-04-06.md) — 4〜6月分は提出済み。**未解決1件あり** |
| 次の期限 | 2027年1月10日（7〜12月分・`.07-12月分(1月10日まで厳守)`） |

---

## 置き場所

| パス | 中身 |
|---|---|
| `.claude/skills/smart-tax-return/SKILL.md` | Phase 1〜5 の本体手順。このリポジトリでセッションを開くと自動で読み込まれる |
| `.claude/skills/smart-tax-return/references/` | Drive構造 / 取得元サイト別の手順 / ブラウザ操作 / MF連携 / 会計士への連絡文 |
| `.claude/skills/smart-tax-return/scripts/` | 四半期差分の監査、重複検出、Numbers→CSV変換、スクレイプ雛形、Drive列挙 |
| `.claude/skills/smart-tax-return/evals/` | スキルの精度検証用プロンプトとフィクスチャ |
| `smart_tax_return/records/` | 四半期ごとの作業記録。着手前に前回分を読み、終わったら追記する |
| `smart_tax_return/evals/` | 検証結果へのフィードバック |
| `smart_tax_return/tools/build_skill.sh` | スキルを `.skill`（zip）に固める |
| `smart_tax_return/dist/smart-tax-return.skill` | インストール用バンドル |

---

## 名前について

運用上の正式名称は**スマート確定申告**。過去のやりとりでは「スマカク」と略していたが同じサービス。
ただし **OneDrive / Google Drive 上の実フォルダ名は `確定申告　スマカク` のまま**なので、
パスは読み替えずにそのまま使う。

---

## 個人情報の扱い（重要）

**このリポジトリは公開（public）。** そのため以下はプレースホルダに置き換えてある。

| 伏せたもの | 表記 |
|---|---|
| macOSのユーザー名 | `/Users/<ユーザー名>/Library/CloudStorage/...` |
| 氏名・スマート確定申告の顧客番号 | `<氏名>` / `<顧客番号>` |
| PayPay口座番号（16口座分の一覧） | 件数と名義の内訳のみ。実際の番号は提出状況報告シートを正とする |
| カード末尾4桁 | `(下4桁)` / 例示はダミー番号 |

手順・判断基準・スクリプトはそのまま残っているので運用に支障はない。実値は
Drive/OneDriveの実フォルダと提出状況報告シートを開けば分かる。
**これらの実値をこのリポジトリに書き戻さないこと。**

---

## 引き継いだもの / 引き継いでいないもの

| チャット側 | ワーク側 | |
|---|---|---|
| `スキル/`（SKILL.md・references・evals） | `.claude/skills/smart-tax-return/` | ✅ 移送済み |
| `スクリプト/`（numbers_to_csv.py 等） | `.claude/skills/smart-tax-return/scripts/` | ✅ 移送済み |
| 作業記録 README（4〜6月分） | `records/2026-04-06.md` | ✅ 移送済み |
| `評価結果/feedback.json` | `evals/feedback-2026-09-04.json` | ✅ 移送済み |
| `生成CSV/`（提出済みCSVの控え） | — | ❌ 未移送。提出先のGoogle Driveに投入済みで、控えはチャット側フォルダに残っている。口座番号を含むため公開リポジトリには置かない |
| `評価結果/スキル検証結果.html` | — | ❌ 未移送。中身はfeedback.jsonと同じ実行結果のレポート |

---

## スキルを直したとき

```bash
# 1. .claude/skills/smart-tax-return/ を編集する
# 2. バンドルを作り直す
bash smart_tax_return/tools/build_skill.sh
# 3. コミットする
```

チャット側や他の環境にも同じ内容を入れたいときは、`dist/smart-tax-return.skill` を
アップロードしてインストールする。

---

## 検証（evals）

`.claude/skills/smart-tax-return/evals/evals.json` に3件（段取り提示 / 監査 / 楽天ポイント抽出）。
監査ケースのフィクスチャは `evals/fixtures/prev.json` `curr.json` で、単体でも動かせる。

```bash
python3 .claude/skills/smart-tax-return/scripts/compare_quarters.py \
  .claude/skills/smart-tax-return/evals/fixtures/prev.json \
  .claude/skills/smart-tax-return/evals/fixtures/curr.json --months 7 8 9 10 11 12
```

`evals/feedback-2026-09-04.json` は 2026年9月5日に回した検証（各ケースを
スキルあり／なしで実行）へのレビュー記録。コメントは未記入のまま。
