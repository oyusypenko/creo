# Internal Linking Recipe

Strategy for internal links that move authority, strengthen clusters, and guide user journeys. Tuned for Next.js apps with mixed static + dynamic routes.

## Link budget per page

| Page type | Target link count | Mix |
|-----------|-------------------|-----|
| Homepage | 8–15 | Products, key blog posts, pricing, about |
| Blog post | 3–5 | 1–2 pillar, 2–3 cluster siblings, 0–1 product |
| Pillar page | 12–20 | All cluster articles + key product pages |
| Product page | 5–8 | Related products, docs, case studies |
| Feature page | 4–6 | Use cases, docs, pricing |
| Docs page | 6–12 | Related docs, examples, API ref |
| Location page (multi-loc) | 4–8 | Other locations, services, contact |
| Landing page | 2–4 | Related content, pricing (minimal to stay focused) |

Under-linked pages (< 3 links) = authority dead-end. Over-linked (> 50 links) = link equity dilution.

## Placement priority

```
1. Contextual body  ← primary, most SEO value
2. Introduction    ← 1 max (pillar reference)
3. Conclusion      ← 1–2 (next steps)
4. List items      ← natural when pages are being listed
5. Sidebar/related  ← automated, low priority
6. Footer          ← sitewide boilerplate, lowest value
```

## Anchor text strategy

| Type | When to use | Example |
|------|-------------|---------|
| **Exact match** | Sparingly, for pillar targets | "podcast hosting" → /podcast-hosting |
| **Partial match** | Most common | "choosing the right podcast host" → /guide/choosing-host |
| **Branded** | Product pages, case studies | "Castos analytics" → /features/analytics |
| **Descriptive** | Tools, resources | "free podcast idea generator" → /tools/idea-generator |
| **Natural phrase** | In-content flow | "read our launch post" → /blog/launch |

### Avoid

- "click here" / "read more" / "this" / "here"
- Over-optimized exact-match repeated 3+ times sitewide
- All-caps anchors
- URL-as-anchor unless the URL is memorable

## Topic cluster model

```
              ┌──────────────────────┐
              │   PILLAR: "Podcast"  │ ← Long, comprehensive
              │   (5000+ words)      │
              └──────────▲──▲────────┘
                   ┌─────┘  └─────┐
                   │              │
        ┌──────────▼────┐  ┌──────▼──────────┐
        │ Cluster post  │  │ Cluster post    │
        │ "How to host" │  │ "Best mics"     │
        └───────▲───────┘  └────────▲────────┘
                │                   │
                └──── cross-link ───┘
```

Rules:
- Every cluster article **must** link up to pillar
- Pillar **should** link down to 3–5 key cluster articles
- Cluster articles **can** cross-link to siblings (2–3 max)
- No links to unrelated content from cluster articles

## Link placement patterns

### Contextual body (preferred)

> Choosing the right [podcast host](/podcast-hosting) matters because [migrations cost teams 14 hours on average](/blog/migration-cost-study). Here's how they differ...

### Introduction pillar reference (1 max)

> This guide is part of our [complete podcast hosting breakdown](/podcast-hosting) — come back to the pillar for the full decision framework.

### Conclusion next-steps

> Ready to pick a host? [Compare our top 3 picks](/blog/best-hosts-comparison) or [try Castos free for 30 days](/pricing).

### List items (natural)

Featured tools:
- [Free idea generator](/tools/idea-generator) — topic ideation
- [Episode title tester](/tools/title-tester) — A/B headline preview

## Next.js implementation patterns

### Type-safe internal link helper

```ts
// lib/links.ts
export const routes = {
  home: '/',
  blog: (slug: string) => `/blog/${slug}`,
  pillar: (topic: string) => `/${topic}`,
  product: (slug: string) => `/products/${slug}`,
} as const

// Usage
import Link from 'next/link'
import { routes } from '@/lib/links'

<Link href={routes.blog('launch-post')}>Launch post</Link>
```

### Related-posts component (auto-placement)

```tsx
// components/RelatedPosts.tsx
export async function RelatedPosts({ currentSlug, tags }: Props) {
  const related = await db.posts.findMany({
    where: {
      tags: { some: { name: { in: tags } } },
      slug: { not: currentSlug },
    },
    take: 3,
    orderBy: { publishedAt: 'desc' },
  })
  return (
    <aside>
      <h2>Keep reading</h2>
      <ul>
        {related.map(p => (
          <li key={p.slug}>
            <Link href={`/blog/${p.slug}`}>{p.title}</Link>
            <span>{p.excerpt}</span>
          </li>
        ))}
      </ul>
    </aside>
  )
}
```

### Breadcrumbs (paired with schema)

```tsx
// components/Breadcrumbs.tsx
import Link from 'next/link'

export function Breadcrumbs({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol>
        {items.map((item, i) => (
          <li key={i}>
            {item.href ? <Link href={item.href}>{item.label}</Link> : <span>{item.label}</span>}
            {i < items.length - 1 && <span aria-hidden> / </span>}
          </li>
        ))}
      </ol>
    </nav>
  )
}
```

Always pair with `BreadcrumbList` JSON-LD (see `schema-templates.md`).

## Detection & audit rules

Flag pages with:

- [ ] < 3 internal links
- [ ] > 50 internal links
- [ ] Orphan (no inbound internal links)
- [ ] Orphan pillar (pillar page with < 5 inbound from its cluster)
- [ ] Cluster article not linking up to pillar
- [ ] > 3 anchors with the same exact-match text
- [ ] Any "click here" / "read more" anchors
- [ ] External links with no internal links (content dead-end)
- [ ] Circular references (A → B → A) on same topic

## Anchor diversity targets per URL

If a page has 20 inbound internal links:
- Exact-match: ≤ 3 (15%)
- Partial-match: 8–12 (40–60%)
- Branded/natural: 5–9 (25–45%)

Over-optimized exact-match looks manipulative to search engines.

## Authority flow heuristics

Most authority flows to:
1. Sitewide header nav (every page)
2. Sitewide footer (every page)
3. Breadcrumbs (conditional)
4. Body copy links (per-page)

Pages you want to rank need body copy links. Nav/footer alone = weak signal.

## Audit output

```
Page: /blog/react-optimization
Internal links: 2 of 3–5 target [BELOW MINIMUM]
Inbound internal: 0 [ORPHAN]
Anchor diversity: N/A (no inbound)
Pillar link: missing — expected link to /react-guide

Fixes:
1. Add 1–3 outbound links to: /react-guide, /blog/react-patterns, /blog/react-hooks
2. Add inbound link from /react-guide (currently 0 refs)
3. Ensure pillar /react-guide lists this post in related cluster
```

## Next.js-specific gotchas

- `<Link prefetch={false}>` on rarely-clicked links (footer, sidebar) saves bandwidth
- `<Link scroll={false}>` for same-page anchors to prevent scroll jump
- Avoid `<a href="/path">` over `<Link>` for internal routes (breaks prefetch + client nav)
- In MDX blog content: use a Markdown-to-Link transformer to auto-rewrite `[text](/path)` into `<Link>`
- Dynamic routes: verify the `href` resolves to a generated page (not a 404)

## References

- `geo-citability.md` — structure scoring (links count toward structural readability)
- `scoring-rubric.md` — internal linking weight in On-Page SEO dimension
