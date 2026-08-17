# Off-Page Authority — Directories, LLM Citation Slots, Trust Signals

When to stop rewriting and start building authority, and how to do it without
poisoning E-E-A-T. Complements `geo-citability.md` (on-page citability) with
the off-page half of AI visibility.

## The decision rule

**Queries stuck beyond ~position 40 after solid on-page work are off-page
limited.** More rewriting will not move them. The levers are: directory
listings, reviews, organic community answers, and real backlinks. Conversely,
positions 4-30 are on-page territory — do not buy links for problems a title
rewrite solves (see opportunity buckets in `semantic-core.md`).

## Directories as LLM citation slots

AI answer engines (AI Overviews, ChatGPT, Perplexity) cite G2, Capterra,
AlternativeTo, and category directories far more often than product blogs for
"best X software" queries. A directory listing is not just a backlink — it is
a citation slot in model RAG systems. AI-tool directories (There's An AI For
That, Futurepedia, Product Hunt) are likewise indexed by answer engines.

Track it: run an LLM-citability snapshot (gsc-analyzer extension
`track_llm_visibility.py`) weekly over your P0/P1 queries — cited/not-cited
per surface becomes a time series next to rank history.

## Submission sequencing (the order has causal reasons)

1. **Week 1 — fast-approval, free directories** (SaaSHub, AlternativeTo-class,
   niche catalogs): quick backlinks + they seed scrapers.
2. **Week 2 — slow manual-review directories** (Crozdesk-class, editorial
   catalogs): submit early so they are live by week 4.
3. **After first real reviews exist — review platforms** (G2, Capterra,
   GetApp). G2 is the single biggest LLM-citation source for "best X
   software"; it is worthless empty, so gate on having honest reviews.
4. **Last — launch platforms** (Product Hunt): launch once social proof
   exists elsewhere; aggregators scrape existing listings.

Per-directory metadata to track: effort (S/M/L), link type (do-follow /
no-follow / sponsored — verify `rel=` BEFORE submitting), time-to-listing,
cost, referral visits.

## The fill-once listing brief

Write one reusable brief, then adapt (never paste identically — duplicate
descriptions get filtered):

- Tagline <= 60 chars; short description ~160 chars; long 500-800 words
- Logo + screenshot specs; pricing summary; feature list; personas
- One-sentence differentiator; 50/100/200-word press snippets

If the product serves two audiences (consumer + B2B), maintain two framings
pointing at different landing pages — two citation slots, not duplicate
content.

## Tracker and kill criteria

Track: directory | status (todo/submitted/live/rejected) | date | URL | link
type | referral visits. Monthly review: chase anything >14 days in
`submitted`; deprioritize anything with <5 referral visits after 60 days.

## Hard DON'Ts (guardrails for autonomous agents)

- No fabricated or paid reviews. Ever. Offer a free month for an HONEST
  review instead.
- No "submit to 100 directories" services — that is a PBN footprint.
- No paid placements before 60 days of free-tier data.
- No identical descriptions across listings.
- Verify a directory is alive and indexed before submitting (dead domains in
  directory lists are common).

## Answer-engine coverage beyond Google

Different assistants use different indexes: ChatGPT leans on Bing. Register
the site in **Bing Webmaster Tools** and track Bing separately — long-tail
visibility there diverges from Google in both directions. (The weekly
snapshot script merges Bing data when a key is configured.)

Discovery ladder for AI agents, cheapest first: `llms.txt` (see
`llms-txt-generator.md`) -> public API -> MCP server wrapping it -> OpenAPI
spec. Write llms.txt to persuade the MODEL: state capabilities, free-tier
limits, and why calling you beats answering from parametric memory
(verified/validated data, persistence, next-step pipeline). Publish sample
artifacts in plain HTML, not behind a login — models cite what they can read.

## Trust-killer inventory (audit these before building authority)

Authority work amplifies whatever trust signals exist — including the fake
ones. Sweep and fix first:

| Trust killer | Rule |
|--------------|------|
| Stock/invented testimonials ("Early user feedback", SVG avatars) | E-E-A-T poison. Real and named, or remove. Emptiness beats fake |
| Unsourced stats ("156% revenue increase") | Add source + n= + methodology, or strip |
| Fabricated `aggregateRating` in schema | Manual-action risk. Remove until real ratings exist |
| Compliance claims not held ("HIPAA Compliant", "RD Reviewed") | Legal exposure, not just SEO. Remove or obtain |
| Claimed-but-unshipped features | Soften to the truth |
| Copy/pricing mismatch (promise exceeds what the tier delivers) | Bait-and-switch signal; align copy to product |
| "Join thousands of users" without the users | Remove |
| Causal health/medical claims | Soften to educational framing; add reviewer (YMYL) |

Authorship model for content authority: one real named founder/author plus a
credentialed reviewer (`author` Person + `reviewedBy` Person), a public
editorial-policy page, and a gating list of YMYL URLs that cannot publish
without a reviewer byline. "{Brand} Team" bylines are discounted.

## Community answers

Organic, genuinely helpful Reddit/Quora/Stack answers outrank ads for AI
discovery — community threads are heavily represented in answer-engine
citations. One honest, detailed answer per relevant recurring question;
disclose affiliation; never astroturf.
