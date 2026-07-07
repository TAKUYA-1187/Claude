# Claude Code Web スケジュール実行 登録用プロンプト

claude.ai/code のスケジュール機能（毎日 07:00 JST）に、以下をそのまま貼り付けて登録する。
これが「セッションが閉じても毎朝動く」唯一の確実な永続化手段。

---

リポジトリ TAKUYA-1187/Claude の `amazon-oem-research/PLAYBOOK.md` を読み、その手順・条件・誠実性ルールに厳密に従って、Amazon物販（中国輸入OEM）の日次リサーチを実施してください。

- 対象: 月販200個以上が狙える中国輸入OEM向き商品 / 仕入原価（送料・関税・FBA手数料込み）が販売価格の50%以内 / 梱包160サイズ以上の大型を優先
- WebSearchで当日の需要トレンドを調査し、有望カテゴリ2〜3件を分析
- `amazon-oem-research/reports/` の過去レポートを読み、切り口の重複を避ける
- 結果を `amazon-oem-research/reports/YYYY-MM-DD.md` に保存し、ブランチ claude/relaxed-mendel-0s7ln5 にコミット＆プッシュ
- 実在ASIN・実売数・仕入単価の捏造は禁止。確認できた事実と仮説を明確に区別すること
- レポート要約を報告して終了
