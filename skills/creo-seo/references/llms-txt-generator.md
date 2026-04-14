# llms.txt Generator & Validator

The `llms.txt` standard (Answer.ai, 2024) is an emerging convention helping AI systems quickly understand a site's structure and content without full crawling. Lives at `/llms.txt` (short) and optionally `/llms-full.txt` (expanded).

## Spec at a glance

- **Location**: `/llms.txt` (root)
- **Format**: Markdown (not HTML/JSON/XML)
- **Mandatory**: H1 title + blockquote description
- **Recommended**: H2-grouped page entries with URL + description

## Required structure

```markdown
# Project Name

> One-paragraph description (under 200 chars). Factual, specific: what you do + who you serve.

Optional context paragraphs about the project, its history, scope.

## Docs

- [Getting Started](https://acme.com/docs/start): Quick-start guide for first-time users
- [API Reference](https://acme.com/docs/api): Full REST API documentation

## Products

- [Pro Plan](https://acme.com/pricing): Team features, $49/user/month
- [Enterprise](https://acme.com/enterprise): SSO, SLA, dedicated support

## Blog

- [Launch Post](https://acme.com/blog/launch): Company launch story, 2024
- [Architecture Deep Dive](https://acme.com/blog/arch): Technical write-up

## About

- [Team](https://acme.com/about): Founders, engineers, investors
- [Careers](https://acme.com/careers): Open roles

## Key Facts

- Founded 2022 in San Francisco
- 50,000+ customers across 80 countries
- SOC2 Type II certified, GDPR compliant
- Backed by Sequoia, a16z

## Contact

- Website: https://acme.com
- Support: support@acme.com
- Sales: sales@acme.com
```

## Required sections

| Section | Required | Purpose |
|---------|----------|---------|
| H1 title | Yes | Official business/project name |
| Blockquote description | Yes | Under 200 chars. Factual. No marketing fluff |
| H2 sections | Yes (1+) | Logical groupings: Docs, Products, Blog, API, Resources, Legal |
| Page entries | Yes (5+) | Absolute URLs + 10–30 word descriptions |
| Key Facts | Recommended | Founded year, HQ, metrics, certifications |
| Contact | Recommended | Email at minimum |

## Common H2 groupings

Pick what fits your site:
- `## Docs` — documentation pages
- `## API` — API references
- `## Products` — product/feature pages
- `## Services` — service offerings
- `## Blog` — blog posts (top 5–10 most important)
- `## Resources` — guides, whitepapers, tools
- `## About` — team, mission, press
- `## Legal` — terms, privacy, policies
- `## Contact` — how to reach you
- `## Optional` — nice-to-know but not load-bearing

## Next.js generator (App Router)

```ts
// app/llms.txt/route.ts
export const revalidate = 3600 // refresh hourly

export async function GET() {
  const posts = await db.posts.findMany({ where: { featured: true }, take: 10 })
  const docs = await db.docs.findMany({ orderBy: { priority: 'desc' }, take: 15 })

  const body = `# Acme

> ${SITE_DESCRIPTION.slice(0, 199)}

${ABOUT_PARAGRAPH}

## Docs

${docs.map(d => `- [${d.title}](https://acme.com/docs/${d.slug}): ${d.summary}`).join('\n')}

## Blog

${posts.map(p => `- [${p.title}](https://acme.com/blog/${p.slug}): ${p.excerpt}`).join('\n')}

## Products

- [Pricing](https://acme.com/pricing): Plans from free to enterprise
- [Features](https://acme.com/features): Product overview

## Key Facts

- Founded 2022
- 50,000+ customers
- SOC2 Type II certified

## Contact

- Website: https://acme.com
- Support: support@acme.com
`
  return new Response(body, { headers: { 'Content-Type': 'text/markdown; charset=utf-8' } })
}
```

## llms-full.txt (optional expanded version)

Same structure but with full content inline (markdown copy of each doc/page). Useful for smaller sites (<100 pages). Skip if your site is large — the short version with links is fine.

## Validation criteria

| Check | Severity | Pass if |
|-------|----------|---------|
| File present at `/llms.txt` | Critical | HTTP 200 |
| Content-Type is text/markdown or text/plain | High | MIME correct |
| H1 present in first non-empty line | Critical | Starts with `# ` |
| Blockquote description present | High | Line starting with `> ` within first 10 lines |
| Description ≤ 200 chars | Medium | `len(description) ≤ 200` |
| At least 1 H2 section | Critical | `^## ` matches ≥ 1 |
| ≥ 5 page entries with URLs | High | `- [.*](https?://...)` matches ≥ 5 |
| All URLs are absolute | High | No relative `/path` links |
| All URLs return 200 | Medium | HTTP HEAD check |
| Each entry has a description | Medium | `- [link](url): description` pattern |
| No markdown syntax errors | Low | Linter clean |

## Scoring formula

```
llms_score = (Completeness × 0.40) + (Accuracy × 0.35) + (Usefulness × 0.25)
```

**Completeness (40%)** — 0–100:
- 100: H1, description, 4+ H2 sections, Key Facts, Contact
- 80: H1, description, 3 H2, Contact
- 60: H1, description, 2 H2
- 40: H1, description, 1 H2
- 20: H1 only
- 0: missing file

**Accuracy (35%)** — 0–100:
- All URLs return 200
- Descriptions match actual page content (sample 3)
- Key Facts are verifiable
- Business name matches schema.org Organization

**Usefulness (25%)** — 0–100:
- Descriptions are concrete not marketing fluff
- Important pages (docs, pricing, key blog posts) included
- Logical section ordering (most important first)
- No dead/redirected URLs

## Anti-patterns

Do NOT include:
- Marketing fluff ("world-class", "best-in-class", "revolutionary")
- Emoji decorations (some parsers choke)
- Relative URLs
- Pages that require auth
- Pages that are `noindex`
- Outdated/redirect URLs
- Duplicated entries
- Long descriptions over 30 words

## Placement

Also reference in robots.txt (not required but helpful):

```
# robots.txt
Sitemap: https://acme.com/sitemap.xml
# llms.txt: https://acme.com/llms.txt    (no official directive yet)
```

Some sites link it in `<head>`:
```html
<link rel="alternate" type="text/markdown" href="/llms.txt" title="LLM guide">
```

## Priority: which pages to include

Rank pages by this heuristic and take top 10–30:

1. Homepage + core landing pages (pricing, features, about)
2. Top documentation (quick start, API reference, key guides)
3. Featured blog posts (evergreen, highly trafficked)
4. Case studies / success stories (if you have proof)
5. Legal (terms, privacy) — brief mention
6. Contact / support

Skip: thin pages, tag/category archives, paginated listings, session-dependent pages.

## CI validation snippet

```bash
#!/bin/sh
# validate-llms-txt.sh
curl -fsSL https://acme.com/llms.txt -o /tmp/llms.txt

grep -qE '^# ' /tmp/llms.txt || { echo "Missing H1"; exit 1; }
grep -qE '^> ' /tmp/llms.txt || { echo "Missing blockquote description"; exit 1; }
grep -cE '^## ' /tmp/llms.txt | awk '{ if ($1 < 1) exit 1 }' || { echo "No H2 sections"; exit 1; }

# Check all linked URLs return 200
grep -oE '\(https?://[^)]+\)' /tmp/llms.txt | tr -d '()' | while read url; do
  code=$(curl -o /dev/null -s -w "%{http_code}" -L "$url")
  [ "$code" = "200" ] || echo "Bad: $url ($code)"
done
```

## References

- llms.txt spec: https://llmstxt.org
- Answer.ai proposal (2024): https://llmstxt.org/about
- Adoption tracker: https://llmstxt.site
