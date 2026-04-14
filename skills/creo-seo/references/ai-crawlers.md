# AI Crawler Access Matrix

14+ AI crawlers with allow/block recommendations and robots.txt templates. Configure for maximum AI visibility while protecting what you need to protect.

## Tier 1 — Critical for AI search (ALLOW)

| Crawler | Operator | User-Agent | Purpose | Impact if blocked |
|---------|----------|------------|---------|-------------------|
| **GPTBot** | OpenAI | `GPTBot` | ChatGPT search + browsing + training | Invisible in ChatGPT search (300M+ users) |
| **OAI-SearchBot** | OpenAI | `OAI-SearchBot` | ChatGPT search only, no training | No ChatGPT search results |
| **ChatGPT-User** | OpenAI | `ChatGPT-User` | User-initiated browsing requests | Users can't visit your site via ChatGPT |
| **ClaudeBot** | Anthropic | `ClaudeBot` | Claude web search + analysis | Invisible to Claude search |
| **PerplexityBot** | Perplexity | `PerplexityBot` | Perplexity citations (best referral traffic) | No Perplexity citations, loses referral traffic |

## Tier 2 — Broad ecosystem (ALLOW)

| Crawler | Operator | User-Agent | Purpose | Search-rank impact |
|---------|----------|------------|---------|---|
| **Google-Extended** | Google | `Google-Extended` | Gemini training + AI Overviews improvements | None (separate from Googlebot) |
| **GoogleOther** | Google | `GoogleOther` | Research + experimental features | None |
| **Applebot-Extended** | Apple | `Applebot-Extended` | Apple Intelligence (2B+ devices) | None (separate from Applebot) |
| **Amazonbot** | Amazon | `Amazonbot` | Alexa AI answers | None |
| **FacebookBot** | Meta | `FacebookBot` | Meta AI (3B+ users) | None |

## Tier 3 — Context-dependent

| Crawler | Operator | Purpose | Recommendation |
|---------|----------|---------|----------------|
| **CCBot** | Common Crawl | Dataset for many LLMs' training corpora | Allow for training presence; block for data-control reasons |
| **anthropic-ai** | Anthropic | Training (separate from ClaudeBot) | Allow unless you want to opt out of training |
| **cohere-ai** | Cohere | Cohere model training | Low priority either way |
| **Bytespider** | ByteDance | TikTok AI + Doubao (China-focused) | **BLOCK** — aggressive crawler, low value for most Western sites |

## Maximum AI visibility robots.txt template

```
# --- Standard search engines ---
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# --- AI search & browsing (ALLOW) ---
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: GoogleOther
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: FacebookBot
Allow: /

# --- Block aggressive / low-value crawlers ---
User-agent: Bytespider
Disallow: /

# --- Fallback ---
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /private/

Sitemap: https://acme.com/sitemap.xml
```

## Opt-out of training only (keep search) template

Only permits live-browsing/search bots; blocks training-only crawlers:

```
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: anthropic-ai
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: cohere-ai
Disallow: /

# Still allow live search
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: *
Allow: /
```

Note: GPTBot is used for both training AND browsing. Blocking it removes you from ChatGPT search entirely.

## Meta-tag alternative (per-page opt-out)

```html
<meta name="robots" content="noai, noimageai">
<meta name="GPTBot" content="noindex">
<meta name="ChatGPT-User" content="noindex">
<meta name="ClaudeBot" content="noindex">
<meta name="Google-Extended" content="noindex">
<meta name="PerplexityBot" content="noindex">
```

## HTTP header alternative

```
X-Robots-Tag: noai, noimageai
```

## Crawler access scoring formula

```
score = 100
      − (15 × count of Tier 1 critical crawlers blocked)
      − (5  × count of Tier 2 secondary crawlers blocked)
      − (10 if no sitemap in robots.txt)
      − (5  if no canonical or noindex misconfig detected)
```

Max 100. Interpretation:
- 90–100: excellent AI access
- 70–89: good (minor gaps)
- 50–69: major restrictions
- <50: critically restricted from AI search

## Next.js `robots.ts` with full AI matrix

```ts
// app/robots.ts
import type { MetadataRoute } from 'next'

const allowAll = ['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','PerplexityBot',
                  'Google-Extended','GoogleOther','Applebot-Extended','Amazonbot','FacebookBot']

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      ...allowAll.map(ua => ({ userAgent: ua, allow: '/' })),
      { userAgent: 'Bytespider', disallow: '/' },
      { userAgent: '*', allow: '/', disallow: ['/admin/', '/api/', '/private/'] },
    ],
    sitemap: 'https://acme.com/sitemap.xml',
    host: 'https://acme.com',
  }
}
```

## Verifying crawler access

```bash
# Check GPTBot access
curl -A "GPTBot/1.2 (+https://openai.com/gptbot)" -I https://acme.com

# Check what robots.txt says for a bot
curl https://acme.com/robots.txt | grep -A 2 "GPTBot"

# Test with Google's robots.txt tester (GSC)
# https://search.google.com/search-console
```

## Detection heuristics (check these during audit)

- [ ] `robots.txt` exists and is not 404
- [ ] `robots.txt` references a sitemap
- [ ] No global `Disallow: /` in catch-all
- [ ] Tier 1 crawlers not explicitly blocked
- [ ] No conflicting `noindex` meta on indexable pages
- [ ] No `X-Robots-Tag: noai` header if you want AI visibility
- [ ] Bytespider explicitly blocked (optional but reduces bandwidth costs)

## References

- OpenAI GPTBot docs: https://platform.openai.com/docs/gptbot
- Google-Extended: https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers
- Anthropic ClaudeBot: https://support.anthropic.com/en/articles/8896518
- Perplexity crawlers: https://docs.perplexity.ai/guides/bots
- Apple: https://support.apple.com/en-us/119829
