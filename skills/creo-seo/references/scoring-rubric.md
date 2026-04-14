# creo-seo Composite Scoring Rubric

Unified SEO + GEO health score for Next.js apps. Produces a 0–100 composite, letter grade, and revenue impact estimate.

## Composite formula

```
SEO_Health_Score =
  (Technical_SEO       × 0.22) +
  (Content_Quality     × 0.20) +
  (On_Page_SEO         × 0.15) +
  (Schema_StructuredData × 0.10) +
  (Core_Web_Vitals     × 0.10) +
  (AI_Search_Readiness × 0.12) +
  (Images              × 0.05) +
  (Sitemap_Robots      × 0.06)
```

Sum of weights = 1.00. Each dimension is 0–100.

## Dimension scoring

### 1. Technical SEO (22%)

| Check | Points |
|-------|--------|
| Crawlable (no robots.txt block, no noindex on critical pages) | 20 |
| Indexable (canonical present, no orphan pages) | 15 |
| Security (HTTPS, HSTS, no mixed content) | 10 |
| URL structure (clean, lowercase, no params for canonical) | 10 |
| Mobile (viewport meta, touch targets ≥ 48×48, responsive) | 15 |
| JS rendering (content accessible without JS or with SSR) | 15 |
| Redirects (≤ 1 hop, no chains, no loops) | 10 |
| 404 handling (custom 404, no soft 404s) | 5 |

### 2. Content Quality (20%)

E-E-A-T + word count + readability. See `content-quality-rubric.md`.

| Sub-dimension | Weight |
|---|---|
| Experience (first-hand signals) | 25 |
| Expertise (author credentials, depth) | 25 |
| Authoritativeness (citations, backlinks) | 25 |
| Trustworthiness (accuracy, sources, transparency) | 25 |

Plus gates:
- Word count below page-type floor → –30
- Flesch readability outside 55–75 → –10
- Duplicate content / thin content → automatic fail

### 3. On-Page SEO (15%)

| Check | Points |
|-------|--------|
| Unique `<title>` 50–60 chars | 15 |
| Unique meta description 140–160 chars | 15 |
| Single H1 per page | 15 |
| H2/H3 hierarchy logical | 10 |
| Target keyword in title, H1, first 100 words | 15 |
| Internal links: 3–5 relevant per page | 10 |
| Canonical tag present and self-referencing | 10 |
| Open Graph + Twitter Card present | 10 |

### 4. Schema / Structured Data (10%)

| Check | Points |
|-------|--------|
| ≥ 1 valid JSON-LD block per page | 25 |
| Schema type matches page content | 20 |
| No deprecated types (HowTo, SpecialAnnouncement, etc.) | 15 |
| No placeholder text ([Business Name], [URL]) | 15 |
| Required fields present per type | 15 |
| Absolute URLs, ISO-8601 dates | 10 |

See `schema-validation-checklist.md`.

### 5. Core Web Vitals (10%)

Field data from CrUX (75th percentile):

| Metric | Good | Needs improvement | Poor |
|--------|------|-------------------|------|
| LCP | < 2.5 s | 2.5–4.0 s | > 4.0 s |
| INP | < 200 ms | 200–500 ms | > 500 ms |
| CLS | < 0.1 | 0.1–0.25 | > 0.25 |
| FCP | < 1.8 s | 1.8–3.0 s | > 3.0 s |
| TTFB | < 0.8 s | 0.8–1.8 s | > 1.8 s |

Score: 100 if all Good, 70 if mixed, 40 if any Poor.

Note: INP replaced FID in March 2024.

### 6. AI Search Readiness (12%)

| Check | Points |
|-------|--------|
| Citability score (see geo-citability.md) | 40 |
| AI crawler access (see ai-crawlers.md) | 20 |
| llms.txt present and valid | 15 |
| Schema.org Organization + sameAs | 10 |
| Brand authority signals (YouTube, Wikipedia, Reddit) | 15 |

### 7. Images (5%)

| Check | Points |
|-------|--------|
| All images have alt text | 25 |
| Uses `next/image` with proper `sizes` | 20 |
| WebP or AVIF format | 15 |
| LCP image has `priority` prop | 15 |
| No CLS from images (explicit width/height) | 15 |
| Lazy loading for below-fold | 10 |

### 8. Sitemap + robots.txt (6%)

| Check | Points |
|-------|--------|
| sitemap.xml present, valid XML | 25 |
| All URLs in sitemap return 200 | 20 |
| Sitemap referenced in robots.txt | 15 |
| robots.txt accessible at /robots.txt | 15 |
| hreflang present for i18n sites | 15 |
| lastmod accurate (ISO 8601) | 10 |

## Letter grade

| Composite | Grade | Meaning |
|-----------|-------|---------|
| 90–100 | A | Excellent. Minor optimizations only. |
| 80–89 | B | Good. Clear improvement opportunities. |
| 70–79 | C | Average. Significant gaps. |
| 60–69 | D | Below average. Major overhaul. |
| < 60 | F | Critical. Fundamental issues. |

## Revenue impact estimate

```
Monthly_Revenue_Impact = 
  Current_Monthly_Organic_Traffic 
  × Conversion_Rate_Improvement 
  × Average_Deal_Value

Example: 10,000 visitors × 0.5% conv lift × $99 ARPU = $4,950/month
```

Impact classifications:

| Level | Monthly lift | Confidence |
|-------|--------------|------------|
| High | > $5,000/mo OR > 20% traffic lift | Evidence-based from audit |
| Medium | $1,000–$5,000/mo OR 5–20% lift | Industry benchmarks |
| Low | < $1,000/mo OR < 5% lift | Incremental optimization |

## Business-type detection (adjust weights)

Detection heuristics:

| Business type | Signals in codebase |
|---------------|---------------------|
| **SaaS** | /pricing page, /docs, /api, "Start free trial" CTA, Stripe integration |
| **E-commerce** | Product routes, cart, checkout, reviews, next-commerce or Shopify deps |
| **Agency/services** | /portfolio, /case-studies, "Work with us", contact forms |
| **Local business** | Address in footer, phone, hours, Maps embed, LocalBusiness schema |
| **Creator/media** | Blog-heavy, newsletter signup, podcast links, high article count |
| **Marketplace** | Buyer + seller flows, listings, reviews on both sides |

Weight adjustments:

| Type | Technical | Content | On-Page | Schema | CWV | AI | Images | Sitemap |
|------|-----------|---------|---------|--------|-----|-----|--------|---------|
| SaaS | 22 | 20 | 15 | 10 | 10 | 12 | 5 | 6 |
| E-commerce | 20 | 15 | 15 | 15 | 10 | 8 | 10 | 7 |
| Agency | 18 | 25 | 18 | 8 | 8 | 12 | 5 | 6 |
| Local | 20 | 15 | 15 | 15 | 8 | 10 | 7 | 10 |
| Creator/media | 15 | 30 | 15 | 10 | 10 | 15 | 3 | 2 |
| Marketplace | 25 | 10 | 15 | 12 | 12 | 10 | 10 | 6 |

(All must sum to 100.)

## Priority tiers for findings

| Priority | When |
|----------|------|
| **Critical** | Blocks indexing, breaks CWV, deprecated schema, security issue |
| **High** | Missing key meta/schema, duplicate content, significant CWV gap |
| **Medium** | Suboptimal title/description length, missing alt text, weak internal linking |
| **Low** | Cosmetic, minor optimization opportunities |

## Report output

Each audit produces:

```
# SEO Audit — acme.com
**Date:** 2026-04-14
**Business type:** SaaS
**Composite score:** 78/100 (Grade B)
**Revenue impact estimate:** +$3,200/mo (Medium confidence)

## Dimension scores
| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Technical SEO | 82 | 22% | 18.0 |
| Content Quality | 74 | 20% | 14.8 |
| On-Page SEO | 80 | 15% | 12.0 |
| Schema | 65 | 10% | 6.5 |
| Core Web Vitals | 70 | 10% | 7.0 |
| AI Search | 60 | 12% | 7.2 |
| Images | 85 | 5% | 4.3 |
| Sitemap | 100 | 6% | 6.0 |
| **Total** | | | **75.8** |

## Critical issues (3)
...

## High priority (8)
...

## Implementation tasks (prioritized)
- [ ] [Critical] Add canonical to /blog/* — file: app/blog/[slug]/page.tsx:12
...
```
