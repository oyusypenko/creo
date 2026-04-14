# Sitemap & robots.txt Patterns for Next.js

Patterns for static sitemaps, dynamic sitemaps, i18n, news/image/video sitemaps, index splitting, and robots.txt.

## Choice matrix

| Scenario | Solution |
|----------|----------|
| <1000 static pages | Native `app/sitemap.ts` |
| 1000–5000 pages, CMS-backed | Native `app/sitemap.ts` (async fetch) |
| 5000+ pages | `next-sitemap` CLI with index splitting (auto-splits at 5000) |
| Dynamic, per-request | App Router `route.ts` with `getServerSideSitemap` (from next-sitemap) |
| Pages Router dynamic | `getServerSideSitemapLegacy` |
| Multi-lang / hreflang | `alternateRefs` per URL |
| News articles | Google News extension fields |
| Image-heavy (gallery, product) | Image sitemap extension |
| Video-heavy | Video sitemap extension |

## 1. Native Next.js static sitemap (App Router)

```ts
// app/sitemap.ts
import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://acme.com'
  return [
    { url: `${base}/`, lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${base}/pricing`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/blog`, lastModified: new Date(), changeFrequency: 'daily', priority: 0.8 },
  ]
}
```

## 2. Native dynamic sitemap from CMS

```ts
// app/sitemap.ts
import type { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const posts = await fetch('https://cms.acme.com/posts', { next: { revalidate: 3600 } }).then(r => r.json())
  return posts.map((p: any) => ({
    url: `https://acme.com/blog/${p.slug}`,
    lastModified: new Date(p.updatedAt),
    changeFrequency: 'weekly',
    priority: 0.7,
    alternates: {
      languages: {
        en: `https://acme.com/en/blog/${p.slug}`,
        es: `https://acme.com/es/blog/${p.slug}`,
      },
    },
  }))
}
```

## 3. Multiple sitemaps (index pattern)

Over 50,000 URLs or 50 MB requires splitting. Next.js supports via `generateSitemaps`.

```ts
// app/product/sitemap.ts
import type { MetadataRoute } from 'next'

export async function generateSitemaps() {
  return [{ id: 0 }, { id: 1 }, { id: 2 }]
}

export default async function sitemap({ id }: { id: number }): Promise<MetadataRoute.Sitemap> {
  const start = id * 50000
  const products = await db.products.findMany({ skip: start, take: 50000 })
  return products.map(p => ({
    url: `https://acme.com/product/${p.slug}`,
    lastModified: p.updatedAt,
  }))
}
```

Generates `/product/sitemap/0.xml`, `/product/sitemap/1.xml`, etc. Next.js auto-builds the index.

## 4. next-sitemap CLI (recommended for 5000+ URLs or complex needs)

Install and wire to postbuild:

```json
// package.json
{
  "scripts": {
    "build": "next build",
    "postbuild": "next-sitemap"
  },
  "devDependencies": { "next-sitemap": "^4" }
}
```

Config:

```js
// next-sitemap.config.js
/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.SITE_URL || 'https://acme.com',
  generateRobotsTxt: true,
  sitemapSize: 5000,
  autoLastmod: true,
  changefreq: 'weekly',
  priority: 0.7,
  exclude: ['/admin/*', '/api/*', '/private/*', '/draft-*'],
  alternateRefs: [
    { href: 'https://acme.com/en', hreflang: 'en' },
    { href: 'https://acme.com/es', hreflang: 'es' },
    { href: 'https://acme.com', hreflang: 'x-default' },
  ],
  transform: async (config, url) => {
    if (url.includes('/preview')) return null
    return {
      loc: url,
      lastmod: new Date().toISOString(),
      changefreq: url.startsWith('/blog/') ? 'daily' : 'weekly',
      priority: url === '/' ? 1.0 : 0.8,
      alternateRefs: config.alternateRefs,
    }
  },
  additionalPaths: async (config) => {
    const products = await fetch('https://api.acme.com/products').then(r => r.json())
    return Promise.all(products.map(p => config.transform(config, `/products/${p.slug}`)))
  },
  robotsTxtOptions: {
    policies: [
      { userAgent: '*', allow: '/', disallow: ['/admin/*', '/api/*'] },
      { userAgent: 'AdsBot-Google', crawlDelay: 0 },
    ],
    additionalSitemaps: ['https://acme.com/news-sitemap.xml'],
  },
}
```

## 5. Dynamic server-side sitemap (App Router route handler)

For data too dynamic for build-time:

```ts
// app/server-sitemap.xml/route.ts
import { getServerSideSitemap } from 'next-sitemap'

export async function GET() {
  const posts = await fetch('https://cms.acme.com/posts').then(r => r.json())
  return getServerSideSitemap(posts.map((p: any) => ({
    loc: `https://acme.com/blog/${p.slug}`,
    lastmod: p.updatedAt,
    changefreq: 'weekly',
    priority: 0.8,
  })))
}
```

Pages Router equivalent: `getServerSideSitemapLegacy` in `pages/server-sitemap.xml/index.ts`.

Index of multiple dynamic sitemaps:

```ts
// app/server-sitemap-index.xml/route.ts
import { getServerSideSitemapIndex } from 'next-sitemap'

export async function GET() {
  return getServerSideSitemapIndex([
    'https://acme.com/server-sitemap-posts.xml',
    'https://acme.com/server-sitemap-products.xml',
  ])
}
```

## 6. Google News sitemap

```ts
{
  loc: 'https://acme.com/news/breaking-story',
  lastmod: '2026-04-14T10:00:00+00:00',
  news: {
    title: 'Breaking Story',
    date: '2026-04-14',
    publicationName: 'Acme News',
    publicationLanguage: 'en',
  },
}
```

News sitemap must contain **only articles published in the last 48h**. Keep a separate sitemap and reference it in robots.txt via `additionalSitemaps`.

## 7. Image sitemap extension

```ts
{
  loc: 'https://acme.com/products/wh-1000',
  images: [
    { loc: 'https://cdn.acme.com/hp-front.jpg', title: 'Front view', caption: 'Wireless Headphones Pro', license: 'https://acme.com/license' },
    { loc: 'https://cdn.acme.com/hp-side.jpg', title: 'Side view' },
  ],
}
```

Up to 1000 images per URL. Useful for product/gallery sites.

## 8. Video sitemap extension

```ts
{
  loc: 'https://acme.com/tutorials/coffee',
  videos: [{
    title: 'How to Make Coffee',
    thumbnailLoc: 'https://cdn.acme.com/thumb.jpg',
    description: 'Quick brewing tutorial',
    contentLoc: 'https://cdn.acme.com/coffee.mp4',
    playerLoc: 'https://acme.com/embed/coffee',
    duration: 330,
    publicationDate: '2026-04-01',
    familyFriendly: true,
    requiresSubscription: false,
    live: false,
    uploader: { name: 'Acme', info: 'https://acme.com' },
  }],
}
```

## 9. hreflang via alternateRefs

```ts
alternateRefs: [
  { href: 'https://acme.com/en/about', hreflang: 'en' },
  { href: 'https://acme.com/es/about', hreflang: 'es' },
  { href: 'https://acme.com/fr/about', hreflang: 'fr' },
  { href: 'https://acme.com/about', hreflang: 'x-default' },  // fallback
]
```

Always include `x-default`. Each language must self-reference (if `/en/about` points to `/es/about` as Spanish, `/es/about` must also declare both).

## 10. robots.txt

### Generated by next-sitemap

See §4 — enable `generateRobotsTxt: true` and define `robotsTxtOptions.policies`.

### Native Next.js `app/robots.ts`

```ts
// app/robots.ts
import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow: ['/admin/', '/api/'] },
      { userAgent: 'AdsBot-Google', crawlDelay: 0 },
    ],
    sitemap: 'https://acme.com/sitemap.xml',
    host: 'https://acme.com',
  }
}
```

### AI crawler rules

See `ai-crawlers.md` for the full 14-bot matrix and maximum-visibility template.

## 11. Index auto-splitting (next-sitemap)

With `sitemapSize: 5000` and 12,500 URLs:
- `sitemap-0.xml` (5000 URLs)
- `sitemap-1.xml` (5000)
- `sitemap-2.xml` (2500)
- `sitemap.xml` = index referencing all three
- robots.txt references only `sitemap.xml` (the index)

## 12. Common gotchas

- **Absolute URLs only** in `<loc>`. Relative URLs are invalid.
- **ISO 8601 dates** in `lastmod`. Invalid: `04/14/2026`. Valid: `2026-04-14T10:00:00+00:00`.
- **trailingSlash** must match Next.js config — mismatch causes duplicate-URL indexing.
- **UTF-8 only**. Escape ampersands as `&amp;`, quotes as `&quot;`.
- **One sitemap entry per URL**. Don't put both trailing-slash and non-trailing versions.
- **`priority` is advisory** — Google mostly ignores it. Don't over-weight.
- **News sitemap** must be updated within minutes; build-time won't work — use dynamic route.
- **noindex pages excluded**: a URL in sitemap but with `robots: noindex` = conflicting signals.

## 13. Validation checklist

- [ ] All URLs return 200 (no redirects, 404s, blocked by robots.txt)
- [ ] No duplicate URLs
- [ ] No URLs with query strings (canonicalize them out)
- [ ] `lastmod` is recent and ISO 8601
- [ ] Sitemap is linked from robots.txt
- [ ] Sitemap submitted in GSC and Bing Webmaster
- [ ] Index sitemap splits correctly at 5000 / 50 MB
- [ ] hreflang entries reciprocate across languages
- [ ] `x-default` present for i18n sites
- [ ] No sitemap entry for pages marked `noindex`
