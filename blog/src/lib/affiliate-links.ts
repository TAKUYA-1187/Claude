import { AFFILIATES } from '../affiliates';

const PREFIX = 'aff:';

/** 記事本文（Markdown）に出てくるアフィリエイト ID を返す。 */
export function affiliateIds(markdown: string): string[] {
  return [...markdown.matchAll(/\]\(aff:([\w-]+)\)/g)].map((m) => m[1]);
}

/** 提携済み（URL あり）の案件を含むか。PR表記の自動付与に使う。 */
export function hasActiveAffiliate(markdown: string): boolean {
  return affiliateIds(markdown).some((id) => Boolean(AFFILIATES[id]?.url));
}

/**
 * Markdown の [テキスト](aff:ID) を、提携済みなら広告リンク（rel="sponsored"）に、
 * 未提携ならただのテキストに変換する Sätteri の hast プラグイン。
 */
export const affiliateLinks = {
  name: 'affiliate-links',
  element: {
    filter: ['a'],
    visit(node: any, ctx: any) {
      const href = node.properties?.href;
      if (typeof href !== 'string' || !href.startsWith(PREFIX)) return;
      const id = href.slice(PREFIX.length);
      const program = AFFILIATES[id];
      if (!program) {
        throw new Error(`未登録のアフィリエイトID「${id}」が記事にあります。src/affiliates.ts に追加してください。`);
      }
      if (!program.url) {
        ctx.replaceNode(node, [...node.children]);
        return;
      }
      ctx.setProperty(node, 'href', program.url);
      ctx.setProperty(node, 'rel', 'sponsored nofollow noopener');
      ctx.setProperty(node, 'target', '_blank');
      if (program.pixel) {
        ctx.insertAfter(node, {
          type: 'element',
          tagName: 'img',
          properties: { src: program.pixel, width: 1, height: 1, alt: '', style: 'border:0' },
          children: [],
        });
      }
    },
  },
};
