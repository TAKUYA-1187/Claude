import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    // アフィリエイトリンク・広告を含む記事は true（景品表示法のステマ規制対応でPR表記を出す）
    pr: z.boolean().default(false),
    draft: z.boolean().default(false),
    // public/ 配下の追加スクリプト（例: 計算ツール）
    scripts: z.array(z.string()).default([]),
  }),
});

export const collections = { posts };
