# WordPress で「せどり実務ノート」を運営する

記事は今までどおり `blog/src/content/posts/*.md` に書く。push すると GitHub Actions が WordPress に自動で投稿・更新する。
Claude は WordPress にログインできない（reCAPTCHA・二段階認証で止まる）ため、**ログインを使わない REST API（アプリケーションパスワード）** で投稿する。

```
Claude が記事を書く（blog/src/content/posts/*.md）→ git push
  → GitHub Actions「WordPress Publish」
      1. blog をビルド（アフィリエイトリンク・PR表記・note 案内・計算ツールを組み込んだ HTML）
      2. wordpress/build_wp.py：WordPress 用の本文に変換
      3. wordpress/publish_wp.py：REST API で作成・更新（変更のない記事は触らない）
```

## 使ってはいけない WordPress

**WordPress.com（〜.wordpress.com）は使わない。** 利用規約で「アフィリエイトへの送客を主目的とするブログ」を禁止しており、以前の3サイトはこれで停止された。
使うのは、レンタルサーバーに自分で入れる **WordPress（WordPress.org 版）**。こちらは広告・アフィリエイトの制限がなく、国内のアフィリエイトブログの大半がこの形。

## ファイル

| ファイル | 役割 |
| --- | --- |
| `sedori-note-kit/` | WordPress プラグイン。要点ボックス・計算ツール・note 案内・PR表記の見た目と、同期用の目印（`sedori_source_hash`） |
| `build_wp.py` | ブログのビルド結果を WordPress 用に変換する |
| `publish_wp.py` | REST API で投稿・更新する |
| `dist/sedori-note-kit.zip` | プラグインのアップロード用 zip（`build_wp.py` が作る） |
| `dist/sedori-note-import.xml` | 手動で取り込む場合のインポートファイル（`build_wp.py` が作る） |

---

## オーナーがやること（初回だけ・約40分）

### ① レンタルサーバーと独自ドメイン

エックスサーバー、ConoHa WING など、「WordPress 簡単インストール」と独自ドメインがセットになったプランを選ぶ（料金は各社の公式ページで確認）。
Google AdSense は独自ドメインが必要なので、最初から独自ドメインにする。申し込みの画面で WordPress のインストールまで済ませる。

### ② WordPress の初期設定

管理画面（`https://ドメイン/wp-admin/`）で次を設定する。

| 場所 | 設定 |
| --- | --- |
| 設定 → 一般 | サイトのタイトル：せどり実務ノート／タイムゾーン：東京 |
| 設定 → パーマリンク | 「カスタム構造」に `/posts/%postname%/` と入れて保存（記事同士のリンクがこの形なので、**必ずこれにする**） |
| 設定 → ディスカッション | 「新しい投稿へのコメントを許可」のチェックを外す（スパム対策） |
| 外観 → テーマ | 好きなテーマでよい。無料なら Cocoon、有料なら SWELL が定番。目次はテーマの機能を使う |
| プラグイン → 新規追加 → プラグインのアップロード | `wordpress/dist/sedori-note-kit.zip` を選んでインストール → **有効化** |

zip は GitHub のこのリポジトリで `wordpress/dist/sedori-note-kit.zip` を開き、「Download raw file」（↓のマーク）で保存できる。

### ③ 投稿用のユーザーとアプリケーションパスワード

管理者のアカウントを GitHub に預けないよう、投稿専用のユーザーを作る。

1. ユーザー → 新規追加：ユーザー名 `sedori-bot`、権限グループ **編集者**（パスワードは自動生成のままでよい）
2. ユーザー一覧で `sedori-bot` を開き、ページ下の「アプリケーションパスワード」に `github` と入れて「新しいアプリケーションパスワードを追加」
3. 表示された `xxxx xxxx xxxx xxxx xxxx xxxx` をコピーする（**この画面でしか表示されない**）

### ④ サーバーの「海外からのアクセス制限」を確認する

GitHub Actions は海外のサーバーから接続する。エックスサーバーの「国外IPアクセス制限」のように、海外からの REST API を初期状態で止めるサーバーがある。
サーバーのパネルで、**REST API の国外IPアクセス制限をOFF** にする（ログイン画面や XML-RPC の制限はONのままでよい）。
SiteGuard などのセキュリティプラグインで REST API を無効にしている場合も、有効に戻す。

### ⑤ GitHub に3つの値を登録する

GitHub のこのリポジトリ → Settings → Secrets and variables → Actions → 「New repository secret」で、次の3つを登録する。

| Name | Secret |
| --- | --- |
| `WP_URL` | `https://ドメイン`（最後の / なし） |
| `WP_USER` | `sedori-bot` |
| `WP_APP_PASSWORD` | ③でコピーした文字列（空白ごと貼ってよい） |

登録したら Claude に「WordPress の登録をした」と伝える。Claude が同期を実行して、公開された記事を確認する。

---

## 同期のルール

- 同じスラッグ（URL の最後の部分）の記事があれば更新、なければ作成する
- 内容が変わっていない記事は更新しない（WordPress の「更新日」が無駄に変わらない）
- 公開日時が未来の記事は、WordPress の**予約投稿**になる。まとめて書いて、週2〜3本ずつ公開できる
- WordPress 側で非公開にした記事・削除した記事を、同期で元に戻したり消したりはしない
- WordPress の管理画面で本文を直しても、次にその記事を同期すると GitHub 側の内容で上書きされる。直したいときは Claude に頼む
- 固定ページ（運営者情報・プライバシーポリシー・お問い合わせ）も同じ仕組みで作られる

## 手動で取り込む場合（Secrets を登録しない場合）

ツール → インポート → WordPress（初回は「今すぐインストール」）→ `wordpress/dist/sedori-note-import.xml` を選ぶ。
投稿者の割り当ては、既存のユーザーを選べばよい。取り込んだ後の更新は手動になるので、通常は自動同期を使う。

## ローカルで試す

```bash
cd blog && npm ci && SITE_URL=https://ドメイン npm run build && cd ..
python wordpress/build_wp.py
WP_URL=https://ドメイン WP_USER=sedori-bot WP_APP_PASSWORD='xxxx ...' python wordpress/publish_wp.py
```

環境変数がなければ `publish_wp.py` は投稿対象の一覧を表示するだけで終わる。
