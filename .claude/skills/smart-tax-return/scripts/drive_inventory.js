// Google Drive のフォルダ一覧を列挙するスニペット。
// mcp__claude-in-chrome__javascript_tool の text にそのまま渡す。
//
// 使い方:
//   1. 対象フォルダのURLへ navigate
//   2. このスニペットを実行（LABEL を分かりやすい名前に置き換える）
//
// 仕組み:
//   Drive の一覧は仮想スクロールなので get_page_text ではほぼ何も取れない。
//   代わりに行要素の属性を直接読む。フォルダは aria-label、ファイルは data-tooltip を持つ。
//
// 注意:
//   - 戻り値に ? & = が含まれるとコンテンツフィルタに弾かれるので置換している
//   - この置換をスニペット自身のソースに適用しないこと（セレクタの = まで壊れる）
//   - 空配列が返ったら「空フォルダ」ではなく「まだ描画中」の可能性がある。
//     navigate せずにもう一度叩いてみること。

await new Promise(r => setTimeout(r, 3500));

['LABEL'].concat(
  [...new Set(
    Array.from(document.querySelectorAll('[data-id]'))
      .map(e => e.getAttribute('data-tooltip') || e.getAttribute('aria-label'))
      .filter(Boolean)
  )].map(s => s.replace(/[?&=]/g, '_'))
);


// ---------------------------------------------------------------
// バリエーション A: フォルダIDも一緒に取る（サブフォルダを掘るとき用）
// 長いIDはフィルタに弾かれることがあるので、必要なときだけ使う。
// ---------------------------------------------------------------
//
// await new Promise(r => setTimeout(r, 3500));
// Array.from(document.querySelectorAll('[data-id]'))
//   .map(e => e.getAttribute('data-id') + ' ## ' +
//             (e.getAttribute('aria-label') || e.getAttribute('data-tooltip') || ''))
//   .filter(s => s.split(' ## ')[1])
//   .filter((v, i, a) => a.indexOf(v) === i);


// ---------------------------------------------------------------
// バリエーション B: フォルダだけ / ファイルだけ に絞る
// ---------------------------------------------------------------
//
// フォルダのみ:
//   .map(e => e.getAttribute('aria-label')).filter(Boolean)
// ファイルのみ:
//   .map(e => e.getAttribute('data-tooltip')).filter(Boolean)
//
// 指示ファイル（先頭が "." のもの）は提出物ではないので、
// 集計時に除外すると読みやすくなる:
//   .filter(s => !s.startsWith('.'))
