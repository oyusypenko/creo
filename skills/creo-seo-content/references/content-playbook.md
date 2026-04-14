# Content Playbook — Writing Patterns for AI + Human Readers

Concrete patterns that improve citability (AI search), dwell time (humans), and rankings (search engines). Apply these to every piece of long-form content.

## 1. Direct-answer opening (per section)

**Rule:** Every H2 and H3 opens with a 1–2 sentence direct answer *before* expanding.

Pattern: **"X is Y. It does Z."**

### Example

**Weak:**
```
## How does caching work?

Caching is one of those concepts that sounds simple but has a lot of nuance. 
Let's dive in and explore all the details so you really understand it...
```

**Strong:**
```
## How does caching work?

Caching stores frequent-request results in fast memory so the system skips 
slow work. Done well, it cuts response times 10–100×. Done badly, it serves 
stale data.
```

Why: AI models prefer cleanly extractable passages. Humans scanning for answers love them too.

## 2. Key Takeaways block

**Location:** After the intro paragraph, before the first H2.

**Length:** 3–5 bullets of *actual conclusions* (not a table of contents).

**Purpose:** AI summaries pull from here. Humans who won't read the full piece get value.

### Example

```markdown
**Key takeaways**

- Caching is fastest when invalidation is simple — choose the strategy that makes stale data cheap.
- Most systems get 80% of the win from Redis + HTTP caching; skip exotic tiers unless profiled.
- TTL-based invalidation fails at scale; event-driven invalidation is what separates good caches.
- Measure cache hit rate and p99 latency, not raw request count.
```

Write this block **after** the rest of the article — it needs to reflect actual conclusions.

## 3. Mini-story injection

**Rule:** 2–3 mini-scenarios per long-form piece.

**Structure:** Named person + concrete situation (dates, numbers, names) + clear outcome.

Research: facts wrapped in stories are **22× more memorable** (various psych research).

### Example

**Weak:**
```
Many teams see significant improvements when they adopt better caching strategies.
```

**Strong:**
```
Stripe's infrastructure team cut p99 latency 47% in Q3 2023 after switching from 
Redis TTL to event-driven invalidation via their internal pub/sub (from their 
2024 engineering blog post, "Caching at scale").
```

## 4. YouTube embed (for long-form)

**Rule:** ≥ 1 relevant video per article of 1500+ words.

Prefer:
1. Your own brand's video
2. Authoritative third-party (conference talk, creator with credentials)

Why: AI models cross-reference video + article for topic relevance. Humans engage longer.

## 5. Citation bricks

**Rule:** ≥ 1 authority quote or named study per 500 words.

Patterns:
- "According to [Source, Year], …"
- "[Expert Name], [credential], notes that …"
- "A [Institution] study of N=X found …"

AI models cite content that itself cites authority — it's a signal of trustworthiness.

## 6. Stats density

**Rule:** ≥ 3 specific numbers per 500 words.

Replace:
- "many" → "63%"
- "a lot" → "$2.4M"
- "recently" → "Q1 2026"

Every number should have a source (inline link, citation footnote, or parenthetical).

## 7. Question-format H2s

**Rule:** When natural, cast H2s as questions.

Why: matches how users search. Matches PAA questions in SERPs.

### Example

Weak:
```
## Database Choice
## Caching Strategy
## Monitoring
```

Strong:
```
## Which database should I use?
## How should I cache?
## What should I monitor?
```

## 8. Short paragraphs

**Rule:** 2–4 sentences per paragraph. No paragraph > 6 sentences unless demonstrably needed.

Why: mobile readers scan; AI passage extraction works better on coherent short blocks.

## 9. Tables for comparisons

**Rule:** Any "A vs B" or feature comparison → table.

Why: tables are AI-extractable structured data. Google may surface them as rich comparison snippets. Humans prefer them over walls of prose.

### Example

```markdown
| Feature | Redis | Memcached |
|---------|:-----:|:---------:|
| Persistence | ✅ | ❌ |
| Pub/sub | ✅ | ❌ |
| Memory-only | optional | always |
| Data structures | 10+ types | strings only |
```

## 10. Self-contained passages

**Rule:** Every paragraph should make sense when pulled out of context. Use named subjects, not pronouns.

Weak:
```
It solves this problem by using an LRU policy. They keep the most recent 
entries in memory.
```

Strong:
```
Redis solves the cache-eviction problem by using an LRU (least-recently-used) 
policy. LRU keeps the most recently accessed entries in memory.
```

Why: AI passage extraction can't reach back for context when citing a snippet.

## 11. Passage length 134–167 words

**Rule:** Aim for at least one passage per section in the **134–167 word range** (Bortolato 2025).

Why: the empirical sweet spot for AI citation extraction. Too short = lacks context. Too long = AI can't cleanly cite.

## 12. Date freshness

**Rule:** Show `datePublished` and `dateModified` visibly on long-form. Update dates at least every 12 months.

Fresh content is a major AI and Google ranking signal. Stale content (> 2 years without update) gets demoted.

## 13. Author byline with credentials

**Rule:** Every long-form piece has:
- Author name (real person, not "Acme Team")
- Credential line (title, years in field, notable achievement)
- Link to author page with bio + sameAs social profiles + Person schema

E-E-A-T "Expertise" and "Authoritativeness" both rely on this.

## 14. External authority links

**Rule:** 2–4 outbound links to authoritative sources per article.

Which sources count:
- Official documentation (Mozilla MDN, language docs, cloud provider docs)
- Peer-reviewed studies
- Named industry reports (Gartner, Forrester, company-branded)
- Wikipedia (measured use — not the star source)

Outbound links to authority = trust signal. Not SEO "leaking PageRank" myth.

## 15. Internal linking (see internal-linking-recipe.md)

- 3–5 contextual internal links per article
- Mix of pillar + cluster + product/tool
- Descriptive anchors, not "click here"
- Every cluster article links up to pillar

## Post-write checklist

Before publishing, verify:

- [ ] Each H2 opens with direct-answer pattern
- [ ] Key Takeaways block present (3–5 bullets)
- [ ] 2+ mini-stories with named people/numbers/dates
- [ ] ≥ 1 YouTube embed (if 1500w+)
- [ ] ≥ 1 authority quote or named study per 500 words
- [ ] ≥ 3 specific numbers per 500 words
- [ ] No vague quantifiers without replacement
- [ ] Zero phrases from AI phrase list
- [ ] Paragraphs 2–4 sentences
- [ ] ≥ 1 comparison table (if content warrants)
- [ ] Self-contained passages (no orphan pronouns)
- [ ] ≥ 1 passage in 134–167w range per section
- [ ] datePublished + dateModified visible
- [ ] Author byline + credentials + Person schema
- [ ] 2–4 outbound authority links
- [ ] 3–5 internal links following cluster model

## References

- `../../creo-seo/references/content-quality-rubric.md` — scoring
- `../../creo-seo/references/ai-pattern-detection.md` — phrases to avoid
- `../../creo-seo/references/geo-citability.md` — citability rubric
- `../../creo-seo/references/internal-linking-recipe.md` — linking rules
- `./rewrite-templates.md` — before/after examples
