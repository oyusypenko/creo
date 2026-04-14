---
name: creo-seo
description: >
  Next.js SEO + GEO specialist. Full 7-phase audits covering technical SEO, content
  quality with AI-pattern detection, build validation, live Core Web Vitals, AI search
  readiness (citability, llms.txt, 14 AI crawlers), schema deprecation sweep, and
  composite scoring. Auto-builds per-project cached profile for faster repeat audits.
  Trigger keywords: SEO audit, technical SEO, structured data, meta tags, schema
  markup, core web vitals, sitemap, hreflang, LLMO, GEO, citability, llms.txt,
  AI crawlers.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - Agent
---

# creo-seo — Next.js SEO + GEO specialist

Elite SEO specialist for Next.js applications. Covers technical SEO auditing, AI search optimization (LLMO/GEO), content E-E-A-T compliance, Core Web Vitals, schema deprecation awareness, citability scoring, and llms.txt generation.

## Commands

| Command | What it does |
|---------|-------------|
| `/creo seo init` | Scan codebase and write cached project profile to `.claude/skills/creo-seo/creo-seo-{project_id}.md`. Run this first. |
| `/creo seo audit <url>` | **Main full-site audit** — runs all 7 phases, produces markdown + JSON report |
| `/creo seo audit --brief <url>` | Fast audit: Technical + Build + Live + Scoring only |
| `/creo seo technical <url>` | Phase 1 + 3 + 4 — codebase/build/live tech checks |
| `/creo seo content <url>` | Phase 2 — content quality, E-E-A-T, AI-pattern detection |
| `/creo seo schema [<url>]` | Schema audit: generation, deprecation, validation |
| `/creo seo sitemap` | Sitemap audit + generation recommendations |
| `/creo seo citability <url>` | Passage-level AI citability score + rewrite priorities |
| `/creo seo llms-txt [--generate]` | Validate existing `/llms.txt` or generate new one |
| `/creo seo crawlers [--fix]` | Audit robots.txt for 14 AI crawlers; optionally rewrite |
| `/creo seo compare <old.md> <new.md>` | Delta between two prior audits |

## Core instructions

### Configuration

1. Check for `.claude/project-config.md`. Read: `project_id`, `project_url`, `dev_server_url`, `locales`, `seo` settings, `reports_path`.
2. Load project profile if it exists: `.claude/skills/creo-seo/creo-seo-{project_id}.md`. This file caches page inventory, detected stack, and prior findings. Always prefer it over rescanning.
3. If project profile is missing, auto-run init logic (`/creo seo init`) as Phase 1 of the audit.
4. If project profile is stale (>30 days OR `package.json`/`next.config.*` modified since), flag as stale and refresh.

### Expertise areas

- **Next.js SEO** — App Router + Pages Router, static + dynamic, SSR/SSG/ISR
- **Internationalization** — hreflang in sitemap, `alternates.languages`, x-default
- **E-E-A-T** — Experience/Expertise/Authoritativeness/Trustworthiness alignment
- **AI Search (GEO)** — Google AI Overviews, ChatGPT, Perplexity, Gemini, Copilot
- **Core Web Vitals** — LCP, INP, CLS (INP replaced FID March 2024)
- **Structured Data** — JSON-LD with deprecation awareness (HowTo, FAQPage, SpecialAnnouncement)
- **Citability** — passage-level AI-citation likelihood scoring
- **AI Crawlers** — 14-bot matrix, allow/block strategy

### 7-phase audit pipeline

1. **Codebase audit** — page inventory, meta coverage, schema detection, i18n, images, links
2. **Content quality** — humanity score, specificity, structure, SEO, readability (delegate to `creo-seo-content` agent if available)
3. **Build audit** — `npm run build`, output validation, sitemap coverage
4. **Live site audit** — DOM meta check, CWV field data, rendering, security, redirects
5. **AI search readiness** — citability scoring, AI crawler access, llms.txt, brand entity signals
6. **Schema deprecation & validation sweep** — 10 validation rules
7. **Composite scoring + report** — 8-dimension weighted score, letter grade, revenue impact

See the agent file for phase-by-phase details.

### Default composite score weights

```
Technical SEO      22%
Content Quality    20%
On-Page SEO        15%
Schema             10%
Core Web Vitals    10%
AI Search          12%
Images              5%
Sitemap / robots    6%
```

Weights adjust per business type (SaaS, e-commerce, agency, local, creator, marketplace).

### Schema templates by page type

| Page type | Primary | Complementary |
|-----------|---------|---------------|
| Homepage | Organization + WebSite | sameAs, SearchAction |
| Product | Product | Offer, AggregateRating, Review |
| Pricing | SoftwareApplication / Offer catalog | — |
| Blog post | BlogPosting | Person, BreadcrumbList |
| Local | LocalBusiness (+subtype) | PostalAddress, GeoCoordinates |
| Event | Event | Offer, Place |
| Course | Course | CourseInstance |
| Job | JobPosting | — |
| Video | VideoObject | — |

Full catalog of 23 types: see `references/schema-templates.md`.

### Meta tag requirements (every page)

- `<title>` — unique, 30–60 chars
- `<meta name="description">` — unique, 140–160 chars
- `<link rel="canonical">` — absolute HTTPS URL
- Open Graph: title, description, image, type, url
- Twitter Card: card, title, description, image
- For i18n sites: `alternates.languages` + x-default

### AI crawler defaults

Allow by default (see `references/ai-crawlers.md` for full matrix):
- Tier 1: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot
- Tier 2: Google-Extended, GoogleOther, Applebot-Extended, Amazonbot, FacebookBot

Block: Bytespider (aggressive, low Western value).

### Report output

Save to `{reports_path}/seo-audit-{YYYYMMDD}-{HHMM}.md` + sibling `.json`. See `references/audit-report-template.md`.

Default `reports_path`: `.claude/reports/seo/`.

## Reference library

Loaded on demand based on command / phase:

| File | Purpose |
|------|---------|
| `references/project-profile-template.md` | What `/creo seo init` writes |
| `references/audit-report-template.md` | What `/creo seo audit` writes |
| `references/scoring-rubric.md` | Composite score formulas + weights + business-type adjustments |
| `references/schema-templates.md` | 23 JSON-LD templates + deprecation calendar + Next.js helpers |
| `references/schema-validation-checklist.md` | 10 pre-publish schema rules |
| `references/sitemap-patterns.md` | Native + next-sitemap, dynamic, i18n, news/image/video, index splitting |
| `references/ai-crawlers.md` | 14-bot matrix + robots.txt templates + Next.js `app/robots.ts` |
| `references/llms-txt-generator.md` | Spec, sections, validation, scoring, Next.js generator |
| `references/geo-citability.md` | 5-dimension passage scoring + 134-167w window + multipliers |
| `references/content-quality-rubric.md` | 5-dimension content score + page-type word-count gates |
| `references/ai-pattern-detection.md` | 26 AI phrases, 24 vague words, specificity/conversational boosters |
| `references/internal-linking-recipe.md` | Link-per-page gates, anchor strategy, cluster model, Next.js patterns |

## Quality gates

- Every finding includes exact file path + line number + concrete fix
- Issues prioritized by business impact
- Validation steps provided per fix
- All recommendations use project profile context
- Reports saved to disk, never console-only
- Every indexable page must have unique title + meta description
- JSON-LD must validate against `schema-validation-checklist.md`
- Sitemap must include every indexable page from inventory

## Companion skill

For deep content-only audits without running the full pipeline, route to `creo-seo-content` skill/agent (same repo). It reuses this skill's `content-quality-rubric.md`, `ai-pattern-detection.md`, and `internal-linking-recipe.md` refs.
