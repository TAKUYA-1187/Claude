import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { satteri } from '@astrojs/markdown-satteri';
import { SITE } from './src/site.config.ts';
import { affiliateLinks } from './src/lib/affiliate-links.ts';

export default defineConfig({
  site: SITE.url,
  integrations: [sitemap()],
  markdown: {
    processor: satteri({ hastPlugins: [affiliateLinks] }),
  },
});
