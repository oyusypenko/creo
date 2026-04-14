# Search Intent Classification

4-class system for mapping a page or keyword to user intent. Drives content strategy and SEO patterns.

## The 4 classes

| Intent | User goal | Example queries |
|--------|-----------|-----------------|
| **Informational** | Learn / understand | "what is react", "how to cache", "react hooks guide" |
| **Navigational** | Go to specific destination | "vercel login", "next.js docs", "github" |
| **Transactional** | Buy / download / convert | "buy iphone 15", "free trial notion", "next.js template" |
| **Commercial investigation** | Compare before buying | "best CMS", "notion vs obsidian", "airtable alternatives" |

## Keyword signal words

### Informational (13 signals)

what, why, how, guide, tutorial, tips, definition, meaning, explained, introduction, overview, vs (when "X vs Y: what's the difference"), basics

### Navigational (9 signals)

login, sign in, website, dashboard, account, home, homepage, portal, + explicit brand names

### Transactional (13 signals)

buy, purchase, pricing, cost, price, order, shop, deal, coupon, discount, free trial, download, get started

### Commercial investigation (14 signals)

best, top, review, vs, compare, comparison, alternative, similar, recommended, cheapest, fastest, most popular, ranking, rating

## SERP feature mapping

Check SERP for query to infer intent:

| SERP feature | Strongest signal |
|--------------|------------------|
| Featured snippet | Informational |
| Knowledge graph | Informational |
| People Also Ask (PAA) | Informational |
| Video carousel | Informational |
| Image pack | Informational |
| Shopping results | Transactional |
| Local pack | Transactional (local) |
| Ads | Transactional / commercial |
| Carousel (non-video) | Commercial investigation |
| News / Top stories | Informational (time-sensitive) |
| Site links | Navigational |

## Scoring logic

For each query or page:

1. Count keyword signal hits per class
2. Weight SERP features (if SERP data available)
3. Add pattern scoring:
   - Question start (what/why/how) → +3 Informational
   - List patterns ("5 best", "top 10") → +3 Commercial investigation
   - Brand + generic term → +1 Navigational
4. Normalize to percentages
5. **Primary intent** = highest
6. **Secondary intent** = next-highest if within 15% of primary

## Content pattern per intent

### Informational

- Question-format H2s
- Direct-answer opening per section
- Definitions, explanations, mini-stories
- Schema: Article / BlogPosting, FAQ (if gov/health), HowTo (markup, no rich result)
- Target passage length: 134–167 words per section (citability)
- Target readability: Flesch 60–70
- CTAs: educational ("read more", "subscribe for updates") — avoid sales CTAs

### Navigational

- Clear, bold H1 matching brand
- Minimal text — user wants to move
- Schema: Organization, WebSite + SearchAction, sitelinks search box
- CTAs: login, sign up, specific destinations

### Transactional

- Prominent CTA above fold
- Pricing, trust signals, proof points
- Schema: Product + Offer (+AggregateRating), SoftwareApplication
- Short paragraphs, benefit-oriented bullets
- Risk reversal: free trial, guarantee, no credit card

### Commercial investigation

- Comparison tables (feature matrices)
- Pros/cons per option
- "Best for X" framing
- Schema: ItemList + Product, Review, AggregateRating
- Explicit recommendation with reasoning

## Intent mismatch detection

Audit each page for intent mismatch:

- Navigational query landing on long blog post → confusion → high bounce
- Transactional keyword on informational page → missed conversion
- Informational keyword on heavy sales page → Google demotes (low dwell time)

Fix: either rewrite the page to match the keyword intent, or retarget the keyword.

## Example classifications

| Query | Informational | Nav | Trans | Commercial |
|-------|--------------:|----:|------:|-----------:|
| "how to optimize react" | **85** | 5 | 0 | 10 |
| "notion vs obsidian" | 15 | 0 | 0 | **85** |
| "buy iphone 15 pro" | 0 | 5 | **90** | 5 |
| "vercel login" | 5 | **90** | 0 | 5 |
| "best CMS 2026" | 20 | 0 | 5 | **75** |
| "next.js free trial" | 5 | 0 | **85** | 10 |
| "what is SEO" | **95** | 0 | 0 | 5 |
| "next.js docs" | 30 | **60** | 0 | 10 |

## Applying intent to page audit

For each audited page, check:

- [ ] Primary intent matches the page's apparent purpose
- [ ] Content pattern aligns with intent (see section above)
- [ ] Schema type matches intent (Article for info, Product for trans, ItemList for comparison)
- [ ] CTAs match intent (educational vs sales)
- [ ] Secondary intent coverage — does the page satisfy the "+15%" secondary intent too?

Score: 0–100 based on how well the page matches its intent. Feed into `scoring-rubric.md` content quality dimension.
