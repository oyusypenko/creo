# Audit Report Template

The markdown format for `/creo seo audit` output. Save to `{reports_path}/seo-audit-{YYYYMMDD}-{HHMM}.md` (or `.claude/reports/seo/` default).

## Full template

```markdown
# SEO Audit — {site_name}

**Date:** {YYYY-MM-DD}
**URL audited:** {production_url}
**Business type:** {detected_type}
**Composite score:** {score}/100 (Grade {letter})
**Revenue impact estimate:** +${estimate}/mo ({confidence})
**Auditor:** creo-seo

---

## Executive summary

{2–3 sentences: top-line finding, biggest risk, biggest opportunity.}

**Top 3 actions (in order of impact):**

1. {Critical finding} — {expected gain}
2. {High finding} — {expected gain}
3. {High finding} — {expected gain}

---

## Dimension scorecard

| Dimension | Score | Weight | Contribution | Grade |
|-----------|------:|-------:|-------------:|:-----:|
| Technical SEO         | 82 | 22% | 18.0 | B |
| Content Quality       | 74 | 20% | 14.8 | C |
| On-Page SEO           | 80 | 15% | 12.0 | B |
| Schema / Structured   | 65 | 10% |  6.5 | D |
| Core Web Vitals       | 70 | 10% |  7.0 | C |
| AI Search Readiness   | 60 | 12% |  7.2 | D |
| Images                | 85 |  5% |  4.3 | B |
| Sitemap + robots      |100 |  6% |  6.0 | A |
| **Total**             |    |     | **75.8** | **C** |

---

## Page inventory

- **Total pages audited:** {n}
- **Indexable:** {n}
- **noindex:** {n}
- **Errors (404/500):** {n}
- **Redirects in sitemap:** {n}

| Path | Status | Title | Meta desc | Canonical | Schema | CWV |
|------|:------:|-------|-----------|-----------|--------|-----|
| /    | 200    | ✅    | ✅        | ✅        | Org+Site | ✅ |
| /pricing | 200 | ✅ | ⚠ 119 chars | ✅ | ❌ missing | ✅ |
| /blog/x  | 200 | ✅ | ✅ | ✅ | BlogPosting | ⚠ LCP 3.1s |

---

## Findings by priority

### Critical (blocks indexing, security, deprecated schema)

#### 1. {Title}
- **Pages affected:** {count}
- **Evidence:** {file path and line number, or URL}
- **Impact:** {what breaks}
- **Fix:** {concrete code change, with path}
- **Validation:** {how to verify}

### High (significant SEO gaps)

#### 1. {Title}
...

### Medium (optimization opportunities)

#### 1. {Title}
...

### Low (polish)

#### 1. {Title}
...

---

## Dimension deep-dives

### Technical SEO ({score}/100)

**Passed:** {list}
**Failed:** {list}
**Details:**

- Crawlability: {summary}
- Indexability: {summary}
- Security: {summary, incl. HTTPS/HSTS/CSP}
- URL structure: {summary}
- Mobile: {summary}
- JS rendering: {SSR vs CSR breakdown}
- Redirects: {chain depth, loops}
- 404 handling: {custom page, soft 404s}

### Content Quality ({score}/100)

Per-page content scores (sampled {n} of {total}):

| Path | Humanity | Specificity | Structure | SEO | Readability | Score |
|------|---------:|------------:|----------:|----:|------------:|------:|
| /blog/x | 58 | 62 | 80 | 75 | 70 | 68 |

**Patterns detected:**
- AI phrases flagged: {count, top 3}
- Vague quantifiers: {count}
- Below word-count gate: {pages}
- Flesch out of range: {pages}

See references/content-quality-rubric.md and references/ai-pattern-detection.md.

### On-Page SEO ({score}/100)

| Check | Pages affected |
|-------|---------------:|
| Missing title | 0 |
| Title wrong length | 4 |
| Missing meta description | 2 |
| Meta description wrong length | 7 |
| Missing H1 | 1 |
| Multiple H1s | 0 |
| Missing canonical | 0 |
| Missing OG | 0 |
| Missing Twitter Card | 3 |

### Schema / Structured Data ({score}/100)

Detected types:
- Organization: 1 page (✅ homepage)
- WebSite: 1 page
- BlogPosting: 18 pages
- BreadcrumbList: 24 pages

Gaps:
- /pricing missing SoftwareApplication + Offer
- No Product schema on product pages
- No FAQPage (intentional — site is commercial)

Validation issues:
- {deprecated type}
- {placeholder text}
- {required field missing}
- {date format wrong}

See references/schema-validation-checklist.md.

### Core Web Vitals ({score}/100)

Field data (CrUX, 75th percentile):

| Metric | Value | Target | Status |
|--------|------:|-------:|:------:|
| LCP    | 2.3s  | <2.5s  | ✅ |
| INP    | 180ms | <200ms | ✅ |
| CLS    | 0.08  | <0.1   | ✅ |
| FCP    | 1.7s  | <1.8s  | ✅ |
| TTFB   | 0.9s  | <0.8s  | ⚠ |

**Slow pages (LCP > 2.5s):**
- /blog/long-post — LCP 3.1s (hero image not prioritized)
- /features/x — LCP 2.9s

### AI Search Readiness ({score}/100)

- Citability (sampled {n} pages): avg {score} — see per-page scores
- AI crawler access: {allowed/blocked count}, score {/100}
- llms.txt: present ({score}/100) | missing (recommend generate)
- Schema Organization + sameAs: present ({n} profiles)
- Brand authority signals: YouTube {state}, Wikipedia {state}, Reddit {state}

See references/geo-citability.md and references/ai-crawlers.md.

### Images ({score}/100)

- Total images: {n}
- Missing alt text: {n}
- Not using `next/image`: {n}
- Not WebP/AVIF: {n}
- LCP image without priority: {n}
- CLS contributors: {n}

### Sitemap + robots.txt ({score}/100)

- Sitemap URL count: {n}
- URLs returning non-200: {n}
- Duplicate URLs: {n}
- noindex URLs in sitemap: {n}
- hreflang coverage: {yes/no, with fallback}
- lastmod freshness: {avg days}
- robots.txt references sitemap: yes/no

---

## Implementation tasks (prioritized)

Copy-pastable checklist for engineers:

- [ ] **Critical** — Add canonical meta to `/blog/*` (`app/blog/[slug]/page.tsx:L12`)
- [ ] **Critical** — Remove `SpecialAnnouncement` schema (deprecated) from `app/announce/page.tsx`
- [ ] **High** — Add `SoftwareApplication + Offer` JSON-LD to `/pricing` (see references/schema-templates.md)
- [ ] **High** — Migrate `public/robots.txt` to `app/robots.ts` with AI crawler allow-list (see references/ai-crawlers.md)
- [ ] **High** — Generate `/llms.txt` route handler (see references/llms-txt-generator.md)
- [ ] **High** — Add hreflang to sitemap for en/es/fr locales (see references/sitemap-patterns.md §9)
- [ ] **Medium** — Fix 4 pages with title over 60 chars
- [ ] **Medium** — Add `priority` prop to hero `<Image>` on `/blog/long-post`
- [ ] **Low** — Add apple-touch-icon to `public/`

---

## Appendix

- **Auditor version:** creo-seo {version}
- **Project profile loaded:** `.claude/skills/creo-seo/creo-seo-{project_id}.md` (date {x})
- **References consulted:** {list loaded ref files}
- **CrUX dataset:** {month}
- **Tooling used:** Playwright, PSI v5 API, schema.org validator, {others}

---

## Next steps

1. Run `/creo seo audit --implement` to auto-apply Critical and High fixes (review before merge).
2. Re-run audit in 30 days: `/creo seo audit --compare` to track delta.
3. For content-specific deep-dive: `/creo seo-content audit <url>`.
4. For client-facing PDF: `/creo seo report --pdf`.
```

## Companion outputs

Alongside the markdown report, save:

- `{reports_path}/seo-audit-{YYYYMMDD}-{HHMM}.json` — same data in JSON for programmatic consumption
- `{reports_path}/page-scores-{YYYYMMDD}-{HHMM}.csv` — per-page scorecard in CSV

## Brevity mode

For quick audits use `--brief` which trims to:
1. Executive summary
2. Dimension scorecard
3. Critical + High findings
4. Implementation tasks

(Skip page inventory details, deep-dives, appendix.)
