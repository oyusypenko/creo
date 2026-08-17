# Page SEO Rules — Enforce at Creation Time, Not Audit Time

Rules for every NEW page in a Next.js marketing/content site. Auditing catches
mistakes after they ship; this file prevents them. Generate a project-scoped
copy as `.claude/rules/seo-page-rule.md` (scoped to the marketing package
path) via `/creo seo page-rules` so it loads whenever pages are edited.

## Rule 1 — Metadata and JSON-LD are two separate rendering paths

The most common structural bug: assuming the metadata builder emits schemas.

- `generateMetadata()` / the metadata helper produces `<meta>` tags ONLY
  (title, description, OG, Twitter, canonical, alternates).
- JSON-LD must be rendered as `<script type="application/ld+json">` in the
  page component's JSX — via a `<JsonLd data={...} />` component or
  equivalent. Passing schema data to the metadata builder computes it and then
  silently drops it from the HTML.

**Audit check:** every indexable page's rendered HTML must contain at least
one `application/ld+json` script tag. If schemas are missing live but present
in code, the page is building them without rendering them.

## Rule 2 — Zero hardcoded SEO strings (i18n sites)

All SEO surfaces live in the locale files under a uniform structure:

```
pages.{page}.seo.meta        title / description / keywords
pages.{page}.seo.schemas     per-schema localized fields
pages.{page}.hero            title / subtitle / description
```

- `title: t('seo.meta.title')` — never a literal string.
- JSON-LD fields (headline, FAQ questions/answers, HowTo steps) localize the
  same way; schemas in the default language on non-default locales are a
  duplicate-content generator.
- Canonical and hreflang URLs must include the locale prefix consistently with
  the routing config (`localePrefix` setting), including x-default.

## Rule 3 — Schema selection by page type

| Page type | Mandatory | Complementary |
|-----------|-----------|---------------|
| Core (about, privacy, terms) | Organization + WebSite | — |
| Contact | Organization + WebSite | LocalBusiness (if physical) |
| Article (guides, topical pages) | Organization + Article | BreadcrumbList |
| FAQ | Organization + FAQPage | — |
| Feature / how-to | Organization + SoftwareApplication | HowTo (deprecated for rich results — body content only) |
| Tool / calculator | Organization + WebApplication | FAQPage |
| Landing / homepage | Organization + WebSite + SoftwareApplication | SearchAction |

Use shared builders (`buildOrganizationLd()`, `buildWebsiteLd()`, per-type
`buildXxxStructuredData()` helpers) — never inline raw schema objects in
pages. Full templates and deprecation calendar: `schema-templates.md`.

Schema honesty rules (manual-action territory):

- No `aggregateRating` unless real collected ratings exist.
- No `SearchAction` pointing at a URL that ignores the query parameter —
  worse than no schema.
- Match the entity to the QUERY, not your mental model: if the ranking query
  says "software/app", the page is `SoftwareApplication` with
  `applicationCategory` + `offers` + `featureList`, not `Product`.
- `author` is a `Person` with `jobTitle`/`url` (and `hasCredential` for YMYL),
  never a bare string; YMYL pages add `reviewedBy`.

## Rule 4 — Internal links through a route enum

Every internal `href` goes through the site's route constant/enum (e.g.
`SitePages.PRICING`), which emits the canonical form: correct locale prefix,
correct trailing-slash policy. Bare string hrefs are how 308-redirect chains
enter the crawl (each one wastes crawl budget and lands in the "Page with
redirect" bucket).

## Rule 5 — The body-copy URL-extraction trap

Googlebot extracts `/segment` substrings from plain text as relative URLs and
crawls them. Confirmed in production: the string `$9.99/month` produced a
crawl of `/month`, reported as a 404.

- Write prices/ratios with spaces or words: `$9.99 / month`, "per day".
- Keep path-like strings out of JSON-LD `description`/`headline` unless they
  are real URLs.

## Rule 6 — Images

- Every content image through the optimized image component with explicit
  `width`/`height` (CLS) and a localized `alt`.
- Every page declares an `ogImage` (1200x630 minimum) in the central images
  config; auto-derive a fallback per route rather than shipping pages with no
  OG image.
- Article-class schemas include an `image` field sourced from the same config.

## Rule 7 — Titles and templates

- Title 30-60 chars including the brand ONCE. If the layout applies a
  `%s | Brand` template, page titles must NOT contain the brand — grep all
  title strings for the brand suffix to catch double-brand collisions
  (`Page | Brand | Brand`). Use `title: { absolute }` where the template must
  be bypassed.
- One brand name everywhere. Mixed naming across pages splits the entity.
- Description 140-160 chars, unique per page.
- Article-class pages set `openGraph.type: "article"` (otherwise
  `article:published_time` / `modified_time` never emit).

## Rule 8 — Shared templates are N pages

One layout/template component renders many URLs. A duplicate `<h1>`, a
missing schema, or a wrong OG type in a shared template is N page bugs. When
auditing or fixing, always fix the template, then spot-check two pages using
it.

## Per-page checklist (copy into PR description)

- [ ] Locale JSON: `seo.meta` (title/description/keywords) + `seo.schemas`
- [ ] Metadata builder called with locale + route enum path
- [ ] `<JsonLd>` rendered in page JSX with the page-type schemas
- [ ] Zero hardcoded SEO strings; all content via translation keys
- [ ] Internal links via route enum only
- [ ] Images: optimized component, alt text, ogImage in config
- [ ] No path-like strings in body copy or schema descriptions
- [ ] Title has brand exactly once after template application
- [ ] Page present in sitemap with git-mtime lastmod (`freshness-signals.md`)
- [ ] Build passes; rendered HTML spot-checked for meta + ld+json
