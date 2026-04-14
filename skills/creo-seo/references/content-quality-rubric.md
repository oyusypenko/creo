# Content Quality Rubric

E-E-A-T + readability + humanity + specificity scoring for page-level content audits.

## 5-dimension composite

```
Content_Quality =
  (Humanity        × 0.30) +
  (Specificity     × 0.25) +
  (Structure       × 0.20) +
  (SEO_Compliance  × 0.15) +
  (Readability     × 0.10)
```

Pass threshold: ≥ 70/100.

## Dimensions

### 1. Humanity (30%)

Detects AI-generated patterns. See `ai-pattern-detection.md` for full lists.

| Score | Criteria |
|-------|----------|
| 90–100 | Conversational tone, contractions, specific anecdotes, unique voice |
| 70–89 | Mostly human with occasional generic phrases |
| 50–69 | Mixed — several AI phrases, some vagueness |
| 30–49 | Many AI patterns, generic openings, vague quantifiers |
| < 30 | Obviously AI-generated, formulaic |

### 2. Specificity (25%)

Concrete data, named sources, measurable claims.

| Score | Criteria |
|-------|----------|
| 90–100 | 5+ stats per 500 words, all claims sourced, named studies/people |
| 70–89 | 3–4 stats, most claims sourced |
| 50–69 | 1–2 stats, some sources |
| 30–49 | < 1 stat per 500 words, vague |
| < 30 | Nothing verifiable, all hedged with "many", "most", "some" |

### 3. Structure (20%)

Heading hierarchy, paragraph length, tables/lists.

| Score | Criteria |
|-------|----------|
| 90–100 | Single H1, logical H2→H3 descent, paragraphs 2–4 sentences, tables for comparisons |
| 70–89 | Good hierarchy, minor inconsistencies |
| 50–69 | Occasional skipped levels, mixed paragraph lengths |
| 30–49 | Multiple H1s or no hierarchy, long paragraphs |
| < 30 | No structure, wall of text |

### 4. SEO compliance (15%)

Title, meta, keyword placement.

| Check | Deduction |
|-------|-----------|
| Missing H1 | −30 |
| Multiple H1s | −20 |
| Title > 60 or < 30 chars | −15 |
| Meta description missing | −40 |
| Meta description wrong length | −10 |
| Keyword not in H1 | −20 |
| Keyword not in first 100 words | −15 |
| Keyword density < 1% or > 3% | −15 |
| H2 keyword coverage < 33% | −10 |

Starting score: 100. Apply deductions, floor at 0.

### 5. Readability (10%)

Flesch Reading Ease & Flesch-Kincaid Grade Level.

| Target | Value |
|--------|-------|
| Flesch Reading Ease | 60–70 ("Fairly Easy") |
| Flesch-Kincaid Grade | 8–10 |
| Avg sentence length | < 20 words |
| Avg paragraph length | 2–4 sentences |

| Score | Criteria |
|-------|----------|
| 90–100 | Flesch 60–75, avg sentence < 20, paragraphs balanced |
| 70–89 | Flesch 55–80, avg sentence < 25 |
| 50–69 | Flesch 40–55 or 80+, occasional long sentences |
| 30–49 | Flesch < 40, many long sentences |
| < 30 | Flesch < 30, walls of text, dense jargon |

## Word-count gates by page type

| Page type | Minimum | Target | Uniqueness (multi-page) |
|-----------|---------|--------|-------------------------|
| Homepage | 500 | 800–1200 | N/A |
| Service page | 800 | 1200–1800 | 80%+ |
| Blog post | 1500 | 2000–2500 | 60%+ |
| Product page | 300 | 500–800 | Per-SKU variation |
| Category page | 500 | 800–1200 | 60%+ |
| Location page (multi-loc) | 500 | 600–800 | 60%+ (warn at 30, halt at 50 pages) |
| Pricing page | 400 | 600–900 | N/A |

Below minimum → thin content → automatic content-quality fail.

## E-E-A-T alignment

Content Quality score should also map to the E-E-A-T framework (Google QRG Sept 2025):

| E-E-A-T pillar | Content Quality dimensions |
|----------------|---------------------------|
| **Experience** | Specificity (first-hand data, anecdotes) |
| **Expertise** | Specificity + Structure (credentials, depth) |
| **Authoritativeness** | Specificity (citations) + SEO compliance |
| **Trustworthiness** | Specificity (sources) + Humanity (transparency) |

Each pillar scored 0–25, sum 0–100.

## Audit output example

```
Page: /blog/how-to-optimize-react
Content Quality: 68/100 (C)

Dimension breakdown:
  Humanity:        58/100  [WEAK] — 12 AI phrases, 18 vague words
  Specificity:     62/100  [WEAK] — only 2 stats in 1800 words, no sources
  Structure:       80/100  — good H2s, paragraphs slightly long
  SEO compliance:  75/100  — keyword missing from first 100 words
  Readability:     70/100  — Flesch 62, avg sentence 24 words

Top 3 fixes:
1. Replace 12 AI phrases (see detected list)
2. Add 3–5 stats with sources in sections 2, 4, 6
3. Move keyword "React optimization" into opening paragraph
```

## Letter grades

| Score | Grade | Meaning |
|-------|-------|---------|
| 90–100 | A | Publish-ready |
| 80–89 | B | Publish with minor polish |
| 70–79 | C | Needs one focused rewrite pass |
| 60–69 | D | Needs significant rework |
| < 60 | F | Start over |

## Gates

- **Publish gate:** score ≥ 80 AND zero Critical issues
- **Auto-reject:** score < 60
- **Flag for review:** score 60–79

## Related refs

- `ai-pattern-detection.md` — 26 AI phrases, 24 vague words, boosters
- `geo-citability.md` — citability scoring (overlaps with specificity + structure)
- `internal-linking-recipe.md` — link count/placement gates
