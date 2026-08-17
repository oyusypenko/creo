# Semantic Core — Focused Query Set, Noise Filtering, Opportunity Buckets

Method for turning thousands of GSC queries into the short list actually worth
optimizing. Scripts: gsc-analyzer extension (`pull_semantic_core.py`,
`filter_semantic_core.py`, `pull_trends_12w.py`); per-project taxonomy lives in
`seo-site-config.json` (template in the extension).

## Why: the noise problem

A site can rank for thousands of queries that will never convert (database
lookups, celebrity names, homework questions). Measuring trend on the raw set
hides the commercial bleed — a real case: 3,585 raw queries reduced to a
67-query focused core; the raw aggregate looked flat while the core was down
29%. **Filter first, then measure.**

## The two-artifact model

- `semantic-core.raw.csv` — every query, with an `is_noise` boolean column.
  Nothing is deleted; filter changes stay auditable and reversible.
- `semantic-core.csv` — noise-free focused core, re-prioritized and sorted.

Weekly rank snapshots keep the full tail but tag rows `is_in_focused_core`
so one artifact serves both monitoring (all rows) and action (filter first).

## Noise classification (layered, override-aware)

Per-project rules in site config:

1. **Noise patterns** — regexes for query shapes that never convert for you
   (pure data lookups, brand-of-someone-else, unit conversions, trailing-
   numeric answer-snippet queries, short lookups with no intent).
2. **Commercial-signal overrides** — a noise match is CANCELLED by intent
   markers (`best`, `vs`, `app`, `for <goal>`, `recipe`, price terms…).
   "chicken protein per 100g" is noise; "chicken per 100g for muscle" is not.
3. **Judgement-calls log** — record borderline keeps/drops with a one-line
   rationale in the core's README so the next run does not re-litigate them.
4. Record negative findings explicitly ("cluster X reports zero impressions —
   genuine, not a classification bug") to stop future phantom-bug hunts.

## Priority rubric (P0-P3)

Assigned per `(query, target_url)` row on the focused core:

| Priority | Rule |
|----------|------|
| P0 | Money cluster AND (impressions >= 50 OR position <= 20) |
| P1 | Impressions >= 100 AND position 4-30 (page-1 fringe / page 2-3 — biggest ROI to push) |
| P2 | Informational cluster AND impressions >= 30 |
| P3 | Everything else retained |

Within a priority, sort by **opportunity score = impressions / position**
(dead simple; reliably surfaces "page 2 with volume" wins).

Always use **impression-weighted average position**
(`sum(position*impressions) / sum(impressions)`) when collapsing GSC rows
across dates/countries — a naive mean is wrong.

## Opportunity buckets (what to actually do per row)

| Bucket | Signal | Action |
|--------|--------|--------|
| A | Position 11-30 | Push to page 1: on-page work + 1-2 internal links |
| B | Position 4-10, high impressions, low CTR | Title/meta rewrite + snippet-targeting schema |
| C | Position > 30 with big impressions | New sections, link rails, or a dedicated page |
| D | Page exists but ZERO impressions | Indexation diagnostics (URL inspection, sitemap membership, canonical, noindex) — NOT content work |
| E | Query has volume but no page targets it | Content gap: create or extend a page |

Misrouting D into A (rewriting a page Google has not indexed) and C into E
(creating a duplicate page that cannibalizes an existing one) are the two
classic misdiagnoses. For near-duplicate commercial terms, extend the existing
canonical landing page — never create a second URL.

## Trend labeling (half-over-half)

Compare two 6-week halves of a 12-week window (smooths weekly noise, still
catches quarter-scale direction changes). End the window at `today - 3 days`
for GSC lag. Labels, with absolute-volume gates:

| Label | Rule |
|-------|------|
| new | H1 = 0 and H2 >= 30 impressions |
| lost | H1 >= 30 and H2 <= 10 |
| rising | Impressions +25% or more AND (position improved >= 2 OR H2 position <= 10) |
| falling | Impressions -25% or more OR position worsened >= 5 |
| stable | Everything else (floor: >= 10 impressions to be labeled at all) |

Asymmetry is deliberate: rising requires position confirmation, falling fires
on either signal — biased toward catching decay early.

**Two-pass targeting:** first bucket by opportunity (A-E), then overlay trend
labels and mark every `falling`/`lost` row URGENT — opportunity size and
urgency are different axes. Finish with a concentration analysis: if most
falling queries land on one URL, that URL is Priority 0 this week.

Track one aggregate health number: focused-core H1 vs H2 impressions plus
weighted position ("are we winning?").

## Refresh cadence

- Semantic core rebuild: monthly, or after major content launches.
- Weekly rank snapshot: automated (see extension `templates/seo-weekly.yml`),
  filename = ISO-week Sunday, idempotent overwrite (GSC backfills ~2 days).
- 12-week trend pull: monthly or when the weekly snapshot shows movement.
- LLM citability snapshot (are AI engines citing you for P0/P1 queries):
  weekly alongside rank history; see `offpage-authority.md`.
