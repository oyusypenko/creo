# Citability Scoring for AI Search (GEO)

How to score and improve passage-level citability — the probability an AI system (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) cites or quotes your content.

## Optimal passage length

**134–167 words** per citable passage (Bortolato 2025 analysis). Shorter: not enough context. Longer: AI can't cite cleanly.

Each H2/H3 section should contain at least one passage in this range that works as a standalone answer.

## 5-dimension scoring formula

```
Citability = 
  (Answer_Block_Quality     × 0.30) +
  (Self_Containment         × 0.25) +
  (Structural_Readability   × 0.20) +
  (Statistical_Density      × 0.15) +
  (Uniqueness               × 0.10)
```

Each dimension scored 0–100. Composite 0–100.

## Dimension rubrics

### 1. Answer Block Quality (30%)

Does each section open with a clear direct answer in the first 40–60 words?

| Score | Criteria |
|-------|----------|
| 90–100 | Every section opens with 1–2 sentence direct answer. "X is…" definition pattern. First 40–60 words work standalone. |
| 70–89 | Most sections have clear openings. Some definition patterns. |
| 50–69 | Answers present but buried. Few definition patterns. |
| 30–49 | Answers buried in long paragraphs. Inconsistent. |
| 0–29 | No identifiable answers. Entirely narrative. |

**Fix:** For every H2, rewrite first paragraph to answer the heading question in 1–2 sentences before expanding.

### 2. Self-Containment (25%)

Does each passage make sense without surrounding context? Named subjects (not pronouns)?

| Score | Criteria |
|-------|----------|
| 90–100 | 80%+ passages fully self-contained. Explicit subject naming. No pronoun reliance. |
| 70–89 | 60–79% self-contained. Most name subjects. Occasional pronoun refs. |
| 50–69 | 40–59% self-contained. Mixed subjects/pronouns. |
| 30–49 | 20–39% self-contained. Heavy pronoun reliance. |
| 0–29 | < 20% self-contained. Continuous narrative. |

**Fix:** Replace "it", "this", "they" with explicit noun. Each paragraph should read standalone.

### 3. Structural Readability (20%)

Heading hierarchy, paragraph length, tables/lists.

| Score | Criteria |
|-------|----------|
| 90–100 | Clean H1→H2→H3 hierarchy. Question-based headings. Short paragraphs (2–4 sentences). Tables for comparisons. |
| 70–89 | Good hierarchy with minor skips. Some Q-headings. Mostly short paragraphs. Some tables/lists. |
| 50–69 | Inconsistent hierarchy. Few Q-headings. Mixed paragraph lengths. Limited tables. |
| 30–49 | Minimal structure. No Q-headings. Long paragraphs. Rare tables/lists. |
| 0–29 | No hierarchy. Wall of text. No tables or lists. |

**Fix:** Use question-format H2s ("How does X work?"). Break paragraphs at 4 sentences. Convert comparisons to tables.

### 4. Statistical Density (15%)

Specific numbers, sourced claims, named studies.

| Score | Criteria |
|-------|----------|
| 90–100 | 5+ stats per 500 words. All claims sourced. Specific numbers. Named studies. |
| 70–89 | 3–4 stats per 500 words. Most claims sourced. Mostly specific. |
| 50–69 | 1–2 stats per 500 words. Some sourcing. Mixed specificity. |
| 30–49 | < 1 stat per 500 words. Few sourced. Vague quantifiers. |
| 0–29 | No statistics. No sources. All vague ("many", "most"). |

**Fix:** Replace "many" → "63%"; "a lot" → "$2.4M"; "recent study" → "2024 Princeton study (DOI: …)"

### 5. Uniqueness (10%)

Original data, first-party research, unique angles.

| Score | Criteria |
|-------|----------|
| 90–100 | First-party research. Proprietary data. Original surveys. Unique datasets. Clear methodology. |
| 70–89 | Some original insights. Unique analysis. Distinct perspective with original examples. |
| 50–69 | Synthesizes existing data with unique commentary. |
| 30–49 | Largely derivative. Minimal original contribution. |
| 0–29 | Entirely derivative. Available verbatim elsewhere. |

**Fix:** Survey your customers. Publish internal metrics. Contribute novel framing.

## Citation multipliers (research-backed)

| Tactic | Citation increase | Source |
|--------|-------------------|--------|
| Definition patterns ("X is…" first sentence) | **2.1×** | Georgia Tech 2024 |
| Adding statistics | **+40%** | Princeton 2024 |
| Adding authority quotes | **+115%** | IIT Delhi 2024 |
| Fluency optimization (readability, flow) | **+30%** avg | Multiple 2024 studies |

Stack them: a rewrite with all four can improve citation likelihood by 3–5×.

## Practical rewrite checklist

Before publishing content:

- [ ] Every H2 opens with a 1–2 sentence direct answer
- [ ] Each paragraph ≤ 4 sentences
- [ ] ≥ 1 passage per section in the 134–167 word range
- [ ] Explicit subject in every paragraph (no orphan pronouns)
- [ ] ≥ 1 table or list for comparative/structured content
- [ ] Question-format H2 where natural ("How…", "Why…", "What…")
- [ ] ≥ 3 specific numbers per 500 words
- [ ] All claims sourced (linked or cited study)
- [ ] ≥ 1 authority quote or expert attribution
- [ ] First-party data or original analysis included
- [ ] Date + update date visible (AI models favor recent content)

## Score interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 85–100 | Excellent. Highly citable. | Minor polish only |
| 70–84 | Good. Solid citability. | Target weakest dimension |
| 55–69 | Average. Gaps exist. | Significant rewrite |
| 40–54 | Below average. | Major restructure |
| < 40 | Critical. Not citable. | Start over with spec |

## Audit process

1. **Scrape page** → extract main content, headings, paragraphs
2. **Segment** into passages around each H2/H3
3. **Score each passage** on 5 dimensions (0–100 × weight)
4. **Composite** = weighted avg across all passages
5. **Identify weakest passages** and weakest dimensions
6. **Output** prioritized rewrite suggestions with before/after examples

## Example rewrites

### Before (score ~45)

> Hosting your podcast can be challenging. There are many platforms out there, and each has its own features. It's important to pick one that fits your needs, because the wrong choice can really hurt your growth over time.

### After (score ~85)

> Podcast hosts are platforms that store and distribute audio files to services like Apple Podcasts and Spotify. The market has 25+ options in 2025, but 80% of top podcasts use 3 providers: Libsyn, Buzzsprout, and Castos. Choosing wrong costs creators an average of 14 hours migrating later (Castos 2024 customer survey, n=412).

Changes: definition pattern → explicit stats → source → self-contained.

## Integration with creo-seo

Run as part of `/creo seo audit` Phase 5 or standalone:

```
/creo seo citability <url>
```

Output: per-passage score + overall + top-3 rewrite priorities.

## References

- Bortolato, L. (2025). *Optimal passage length for LLM citations* (AI search research)
- Georgia Tech (2024). *Definition patterns in AI retrieval*
- Princeton (2024). *Statistical density and citation likelihood*
- IIT Delhi (2024). *Authority quotes in LLM generation*
