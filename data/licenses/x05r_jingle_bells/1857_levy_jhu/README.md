# 1857 年版「The One Horse Open Sleigh」（Levy Sheet Music Collection）

取得日：2026-11-15（Claude）。GPT 指示書 §23 で示された所蔵譜。

| ファイル | 中身 | 取得元 |
|---|---|---|
| levy-062-044.pdf | 所蔵譜の 4 ページ（表紙・ヴァース・サビ 2 ページ） | https://levysheetmusic.mse.jhu.edu/sites/default/files/collection-pdfs/levy-062-044.pdf |
| levy_062_044_item.html | 目録のページ | https://levysheetmusic.mse.jhu.edu/collection/062/044 |
| musicians.html | 「Using the Collection → Musicians」のページ（演奏者向けの説明） | https://levysheetmusic.mse.jhu.edu/using-collection/musicians |

目録の記載（levy_062_044_item.html より）
- 題：The One Horse Open Sleigh. Song and Chorus.
- 作者：Written and Composed by J. Peirpont（目録の綴り。譜面の印刷は J. PIERPONT）
- 出版：Oliver Ditson & Co., 277 Washington St., Boston、1857
- プレート番号：18200
- 献呈：To John P. Ordway, Esq.
- 形式：strophic with chorus（有節形式とコーラス）、piano and voice

確認できなかったこと
- サイトの下にある「Copyright Information」のリンク先（https://www.library.jhu.edu/policies/rights-and-reproductions/）は、Cloudflare の確認画面が出て取得できなかった。回避はしていない
- そのため、所蔵館がデジタル画像の利用に独自の条件を付けているかは未確認。x05r では画像を配布・掲載せず、Claude が読み取った音の並びだけを使う

採譜：`bgm_studio/x05r_v2.py` の `SOURCE_1857_AB`、表は `out/release_2026-11-15/x05r_v2_transcription_1857.csv`。
1857 年版は米国議会図書館の画像（Wikimedia Commons 経由、`../1857_first_edition_loc/`）と同じ版（plate 18200）。
