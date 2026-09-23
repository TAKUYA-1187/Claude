// 自分の note 商品（有料記事・テンプレート）の一覧。記事の frontmatter で note: 'ID' と指定すると、
// 本文の最後に「note で配布中」の案内が出る。
//
// - url が空のあいだは案内を出さない（note で公開したら URL を入れるだけで全記事に出る）
// - 自社商品なのでアフィリエイトではない。PR表記は付かない
// - 記事にない ID を書くとビルドが止まる（打ち間違い防止）

export interface NoteProduct {
  /** note の記事タイトル */
  title: string;
  /** 税込価格（円）。無料なら 0 */
  price: number;
  /** 公開後の note 記事 URL。空なら案内を出さない */
  url: string;
  /** ブログ読者に向けた1〜2文の案内 */
  pitch: string;
  /** 中身の箇条書き（3〜4個） */
  includes: string[];
}

export const NOTES: Record<string, NoteProduct> = {
  // 原稿と Excel：note/kaitori-shiire-sheet/
  'kaitori-sheet': {
    title: '買取せどりの仕入れ判定・入金管理シート（Excel）',
    price: 980,
    url: '',
    pitch:
      'この記事の計算を、1商品ずつではなく「箱単位・月単位」で回すためのExcelです。運営者が実際に使っている判定基準をそのまま入れてあります。',
    includes: [
      '同じ箱IDの商品で送料を自動で割る仕入れ判定表',
      '買取価格10%下落・減額時の利益を同時に表示',
      '発送〜入金までの立替額と、月別の利益集計',
      '減額の記録表（買取店ごとの傾向が見える）',
    ],
  },
};

export function noteProduct(id: string | undefined): NoteProduct | undefined {
  if (!id) return undefined;
  const product = NOTES[id];
  if (!product) {
    throw new Error(`未登録の note ID「${id}」が記事にあります。src/notes.ts に追加してください。`);
  }
  return product.url ? product : undefined;
}
