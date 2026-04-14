# Rewrite Templates — Before/After

Copy-pasteable transformations for common content problems. Use during `/creo seo-content rewrite <url>`.

## Problem 1: Generic LLM opener

**Before (humanity 35):**
> In today's digital world, when it comes to podcast hosting, there are many robust platforms that can help you leverage your content. It's important to note that utilizing the right host can unlock the power of your journey.

**After (humanity 88):**
> Picking a podcast host sounds boring until you realize the wrong choice costs an average 14 hours of migration work (Castos 2024 survey, n=412). Three providers dominate in 2026: Libsyn (launched 2004), Buzzsprout (2009), Castos (2016). Between them they host 67% of the top 1,000 shows.

**Changes:**
- Removed: "in today's digital world", "when it comes to", "many", "robust", "leverage", "unlock the power", "journey"
- Added: specific stat (14 hours), source (Castos 2024, n=412), named products + founding years, specific share (67%)

---

## Problem 2: Vague feature list

**Before (specificity 30):**
> Our platform offers many great features including powerful analytics, a robust API, and seamless integrations that help you scale effectively.

**After (specificity 82):**
> Acme ships 3 features most teams use daily: analytics dashboards updated every 60s, a REST+GraphQL API with 99.95% uptime SLA, and 47 pre-built integrations (Slack, Notion, Linear, Salesforce, and 43 more). Teams process 2.3M events/day on average across the customer base.

**Changes:**
- Removed: "many", "great", "powerful", "robust", "seamless", "help you scale effectively"
- Added: named features, refresh rate, uptime SLA, integration count + examples, daily event volume

---

## Problem 3: Buried answer

**Before (citability 28):**
```
## What is caching?

Caching is one of those computer science concepts that sounds simple on the 
surface but actually has tons of nuance depending on the context. Let's dive 
in and explore all the details, because understanding caching properly is 
really important for any developer working on performance-critical systems. 
It comes up in web servers, databases, CDNs, and many other places...
```

**After (citability 85):**
```
## What is caching?

Caching stores the result of an expensive computation so the system can 
reuse it without redoing the work. A typical cache hit is 100–1000× 
faster than the underlying operation — this is why every performance-
critical system uses caching somewhere.

Three layers show up most often: HTTP caches (CDN, browser), application 
caches (Redis, in-process), and database caches (query plan, row cache).
```

**Changes:**
- Direct-answer first sentence
- Specific multiplier (100–1000×)
- Named layers with examples
- Removed: "one of those concepts", "tons of nuance", "let's dive in", "really important"

---

## Problem 4: Missing Key Takeaways

**Before:** Article jumps from intro to first H2.

**After:** Add Key Takeaways block after intro:

```markdown
The old [topic] approach falls apart above [scale threshold], which is 
why teams at [named company 1] and [named company 2] switched to [new 
approach] in [year].

**Key takeaways**

- [Conclusion 1 with specific outcome]
- [Conclusion 2 with specific benefit]
- [Conclusion 3 with specific trade-off]
- [Conclusion 4 — what NOT to do]

## First H2
```

---

## Problem 5: Pronoun-dependent paragraph

**Before (self-containment 30):**
> It's the fastest option if you don't need persistence. They're also easier 
> to operate. This makes it a great choice for small teams.

**After (self-containment 90):**
> Memcached is the fastest cache option when persistence isn't required. 
> Memcached's operational model (stateless nodes, no replication) makes it 
> easier to operate than Redis. For small teams without a dedicated ops 
> engineer, Memcached is the better default.

**Changes:**
- Replaced "It's" → "Memcached is"
- Replaced "They're" → "Memcached's operational model"
- Replaced "This" → "For small teams without a dedicated ops engineer"

---

## Problem 6: No comparison table

**Before:** 3 paragraphs comparing Redis and Memcached prose-style.

**After:** Add comparison table:

```markdown
| Feature | Redis | Memcached |
|---------|:-----:|:---------:|
| Persistence to disk | ✅ | ❌ |
| Data structures | 10+ | strings only |
| Pub/sub | ✅ | ❌ |
| Replication | ✅ | ❌ |
| Memory efficiency | Good | Better |
| Operations complexity | Medium | Low |
| Typical use case | Full cache + queue + pub/sub | Pure cache |
```

Follow with 2–3 sentences of prose explaining the trade-offs that the table surfaces.

---

## Problem 7: Weak CTA

**Before:**
> If you want to learn more, feel free to reach out.

**After (transactional intent page):**
> Start a 14-day free trial (no credit card) or book a 20-minute demo with an engineer.

**After (informational intent page):**
> Next up: [How to profile cache hit rate](/blog/profile-cache-hit-rate) — a 
> 6-minute guide to measuring cache effectiveness in production.

**Changes:**
- Specific offer / specific next action
- Removed: "if you want", "feel free"

---

## Problem 8: Monotone paragraph rhythm

**Before:** 8 paragraphs all 4 sentences long.

**After:** Vary paragraph length:

```
[Paragraph 1: 4 sentences, sets context]

[One-sentence paragraph for emphasis.]

[Paragraph 3: 2 sentences, tight follow-up]

[Paragraph 4: 5 sentences, deeper dive with mini-story]
```

Paragraph rhythm variance signals human authorship.

---

## Problem 9: No author E-E-A-T signals

**Before:**
> By The Acme Team

**After:**
```markdown
By [Jane Doe](/author/jane-doe), Senior Engineer at Acme

Jane has worked on distributed caching systems at Stripe (2019–2023) and 
Acme (2023–present), and previously published [Caching at Scale: Lessons 
from 50 Billion Requests](https://link) at QCon 2024.

**Reviewed by:** [Dr. John Smith](/author/john-smith), Principal Engineer
```

Pair with Person schema in JSON-LD (see `../../creo-seo/references/schema-templates.md`).

---

## Problem 10: Thin / under word count

**Before:** Blog post 450 words targeting "how to choose a podcast host" (1500w minimum).

**After:** Expand with these sections (minimum content):

1. **What a podcast host actually does** (150w) — direct definition + diagram
2. **Key decision factors** (300w) — table of 5–7 criteria
3. **Top 3 options compared** (400w) — feature matrix + short pros/cons
4. **How to migrate** (200w) — 5-step checklist
5. **FAQs** (200w) — top questions (not FAQ schema unless eligible)
6. **Next steps** (50w) — internal link to pillar + product CTA

Total target: 1500–1800w. Adds depth, citability, and internal-linking opportunities.

---

## Pattern: "X vs Y" page rewrite

### Before-section structure

```
## X

[Marketing copy about X, 400w]

## Y

[Marketing copy about Y, 400w]

## Conclusion

[Vague recommendation]
```

### After-section structure

```
## Quick comparison

[Table: 8–12 criteria]

## When X wins

[Direct scenarios + named customers if possible]

## When Y wins

[Direct scenarios + named customers]

## Side-by-side deep dive

[Detailed feature breakdown per category]

## Pricing compared

[Table with 3 tiers each]

## Migration considerations

[What changes when you switch]

## Verdict

[Explicit recommendation with reasoning + "for X, pick A; for Y, pick B"]
```

Apply direct-answer, citation, and stats patterns throughout.

---

## Usage

When `/creo seo-content rewrite <url>` runs:

1. Audit identifies problems (humanity, specificity, structure, etc.)
2. For each problem type, select matching template from above
3. Generate site-specific BEFORE (current content) and AFTER (template-applied rewrite)
4. Save to report with instructions: "Apply to `app/blog/post.mdx` lines 14–27"
