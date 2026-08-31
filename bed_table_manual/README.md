# 昇降式 折りたたみ サイドテーブル / ベッドテーブル — 取扱説明書

A4 4ページの取扱説明書兼組立説明書を、HTML から生成します。
図版はすべてこのリポジトリ内で SVG として描き起こしているため、
拡大・改変・多言語化しても劣化しません。

## 生成物

| ファイル | 内容 |
|---|---|
| `bed-table-manual.pdf` | 入稿・同梱用（A4 / 4ページ / フォント埋め込み済み） |
| `bed-table-manual.html` | 上記と同一内容。ブラウザの印刷でも同じ体裁で出ます |

## ビルド

```bash
pip install pymupdf playwright fonttools brotli qrcode pillow
python3 build.py        # HTML を生成
python3 make_fonts.py   # 本文で使う文字だけに Noto Sans JP をサブセットして埋め込む
python3 build.py        # 埋め込みフォント入りで再生成
```

PDF は Chromium の印刷機能で出力します（`--no-sandbox`、A4、余白 0、背景印刷 ON）。

## 構成

| ファイル | 役割 |
|---|---|
| `iso.py` | アイソメ投影のプリミティブ（直方体・穴・線） |
| `parts.py` | 製品そのもののモデル（ベース／伸縮ポール／天板ユニット／天板／レバー） |
| `glyph.py` | 矢印・手・ボルト・ワッシャー・六角レンチなどの2D記号 |
| `figures.py` | 各挿図（部品アイコン、STEP 1〜5、昇降操作、折りたたみ） |
| `canvas.py` | transform を考慮した bbox 計算と `<svg>` ラッパー |
| `build.py` | 本文テキストとページ組版 |
| `make_fonts.py` | フォントのサブセット化と base64 埋め込み |
| `style.css` | 体裁（A4・印刷用 `@page` 指定を含む） |
| `qr.svg` | 組立動画への QR コード |

## 文言・仕様を直すとき

本文は `build.py` の `PARTS` / `STEPS` / `TROUBLE` / `FAQ` と各 `page*()` 関数に
まとまっています。テキストを直したら `make_fonts.py` を再実行してください
（使用文字が変わるとサブセットも変わるため）。
