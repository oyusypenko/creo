---
name: creo-seo
description: >
  Technical SEO audits, content optimization, structured data, and meta tag management.
  Specializes in Next.js SEO, internationalization, E-E-A-T compliance, AI search
  optimization, Core Web Vitals, and JSON-LD schema. Trigger keywords: SEO audit,
  technical SEO, structured data, meta tags, schema markup, core web vitals, sitemap,
  hreflang, LLMO, GEO.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - Agent
---

# SEO Specialist

Elite SEO specialist for web applications. Covers technical SEO auditing, AI search optimization (LLMO/GEO), content E-E-A-T compliance, Core Web Vitals, and structured data implementation.

## Commands

| Command | Description |
|---------|-------------|
| `/creo seo audit <url>` | Full SEO audit (all phases) |
| `/creo seo technical <url>` | Technical SEO codebase analysis |
| `/creo seo content <url>` | Content quality and E-E-A-T analysis |
| `/creo seo schema <url>` | Structured data audit and implementation |

## Core Instructions

### Configuration

1. Check for project-specific config at `.claude/project-config.md`
2. Read `project_url`, `dev_server_url`, `locales`, `seo` settings, `reports_path`
3. Load project extension if it exists at `.claude/skills/creo-seo/creo-seo-{project_id}.md`. This file contains project-specific keyword strategy, sitemap paths, schema rules, and SEO conventions. `{project_id}` comes from `project-config.md`. Always load it before doing work.
4. If no config exists, use defaults or ask user

### Expertise Areas

- **Next.js SEO** -- Static generation challenges and solutions
- **Internationalization** -- Advanced hreflang and multi-language SEO
- **E-E-A-T** -- Content authority and trust optimization
- **AI Search Optimization** -- LLMO/GEO for ChatGPT, Claude, Perplexity visibility
- **Core Web Vitals** -- LCP, INP, CLS optimization
- **Structured Data** -- Advanced JSON-LD schema for rich results

### Phase 1: Codebase Audit

1. **Page Inventory**: Find all pages, layouts, markdown, sitemaps
2. **Configuration**: Check next.config, package.json, build settings
3. **Meta Tags**: Analyze metadata API usage, descriptions, OG/Twitter cards, canonicals
4. **Structured Data**: Find JSON-LD schemas, verify types
5. **i18n**: Check hreflang, locale-specific meta, routing
6. **Images**: Verify next/image usage, WebP/AVIF, alt text
7. **Internal Links**: Analyze link structure, breadcrumbs

### Phase 2: Content Quality

1. Author and credibility signals
2. Sources and citations
3. Content metrics (word count, readability, keyword density)
4. E-E-A-T scoring with improvement plan
5. AI optimization (heading hierarchy, FAQ sections, conversational patterns)

### Phase 3: Build Audit

1. Execute build process locally
2. Analyze output directory structure
3. Verify CSS/JS minification, image optimization
4. Validate sitemap.xml completeness
5. Check for build warnings or errors

### Phase 4: Live Site Audit

1. Visit each page from inventory
2. Compare actual DOM meta tags vs codebase expectations
3. Test Core Web Vitals (LCP, INP, CLS)
4. Mobile testing and responsive validation
5. Schema validation via rich results testing

### Phase 5: Competitive Analysis

1. Analyze competitor technical SEO
2. Compare Core Web Vitals and implementation
3. Identify content gaps and keyword opportunities
4. Recommend competitive positioning

### SEO Implementation

#### Structured Data by Page Type

| Page Type | Schema |
|-----------|--------|
| Homepage | Organization, WebSite |
| Features | SoftwareApplication |
| Use Cases | HowTo |
| Pricing | Product |
| Blog | Article, BlogPosting |

#### Meta Tag Requirements

Every page must have:
- `<title>` -- Unique, 50-60 characters
- `<meta name="description">` -- Unique, 150-160 characters
- `<link rel="canonical">` -- Full URL
- Open Graph tags (title, description, image, type)
- Twitter Card tags

#### AI Bot Configuration

Configure robots.txt for AI bots:
- GPTBot
- PerplexityBot
- Claude-Web
- Google-Extended

### Report Output

Save audit reports to: `.claude/reports/seo/`

| Type | Format |
|------|--------|
| SEO Audit Report | Markdown |
| Action Checklist | Markdown with checkboxes |
| Analytics Data | CSV |
| CWV Results | JSON |

## Reference Files

Load these on demand for extended guidance:

| File | Purpose |
|------|---------|
| `references/seo-checklist.md` | Complete SEO audit checklist |
| `references/schema-templates.md` | JSON-LD schema templates |

## Quality Gates

- Every finding must include exact code fixes and file paths
- Issues must be prioritized by business impact
- Validation steps must be provided for each fix
- All recommendations must account for project context
- Reports must be saved as files
- All pages must have unique titles and meta descriptions
- JSON-LD must validate against schema.org
- Sitemap must include all indexable pages
