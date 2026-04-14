# AI-Pattern Detection (Humanity Score)

Phrases, vague words, and anti-patterns that signal AI-generated content. Plus specificity and conversational boosters that signal human authorship.

## Detection flow

1. Run regex matches against page text
2. Count AI phrases, vague words, boosters
3. Compute humanity score
4. Flag passages with high density for rewrite

## AI phrases (flag each occurrence)

| Phrase | Why it's flagged |
|--------|------------------|
| "in today's digital world" | Generic LLM opener |
| "in today's modern world" | Generic LLM opener |
| "in today's fast-paced world" | Generic LLM opener |
| "when it comes to" | LLM filler |
| "let's dive in" / "let's dive into" | LLM transition |
| "furthermore" | Over-used in LLM output |
| "moreover" | Over-used in LLM output |
| "additionally" | Over-used in LLM output |
| "leverage" | Corporate-LLM word |
| "utilize" (when "use" works) | LLM substitution |
| "synergy" | Corporate fluff |
| "holistic" | LLM buzzword |
| "robust" (unqualified) | LLM filler adjective |
| "seamless" | LLM filler adjective |
| "game-changer" / "game-changing" | Cliché |
| "unlock the power" | LLM marketing phrase |
| "take it to the next level" | Cliché |
| "journey" (as solo metaphor) | LLM overuse |
| "landscape" (as metaphor) | LLM overuse |
| "paradigm" / "paradigm shift" | LLM buzzword |
| "at the end of the day" | Filler |
| "it's important to note" | LLM hedge |
| "it's worth mentioning" | LLM hedge |
| "the fact of the matter is" | Filler |
| "in conclusion" | Generic closer (delete or replace) |
| "to sum up" | Generic closer |

Target: **< 1 occurrence per 500 words**. Over 5/500w = fail humanity check.

## Vague quantifiers (replace with specifics)

| Word | Preferred replacement |
|------|----------------------|
| many | "63%", "12 of 20", "most" + specific group |
| some | specific count or proportion |
| various | list them |
| numerous | specific count |
| often | "60% of the time", "typically X/week" |
| sometimes | specific frequency |
| usually | measured frequency |
| typically | measured baseline |
| significant | specific quantity |
| substantial | specific quantity |
| great | specific benefit |
| very | delete or intensify specifically |
| quite | delete |
| rather | delete |
| effective | measured outcome |
| important | measured stakes |
| essential | measured dependency |
| powerful | measured capability |
| advanced | measured version/vs baseline |

Target: **< 3 per 500 words**. Over 10/500w = fail specificity check.

## Specificity boosters (increase score)

Regex patterns to count:

| Pattern | What it catches |
|---------|----------------|
| `\b\d{1,3}%\b` | Percentages ("63%") |
| `\$[\d,]+(?:\.\d{2})?` | Dollar amounts ("$2,400") |
| `\b\d{4}\b` | Years ("2024") |
| `\d+(?:,\d{3})*\s*(?:users|customers|downloads|listeners|subscribers)` | Counts with units |
| `\b\d+(?:\.\d+)?x\b` | Multipliers ("3.2x") |
| `\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b` | Time units |
| `\b[A-Z][a-z]+\s+(?:said|explained|noted|wrote|found)` | Named attributions |
| `\bet al\.\s*\(\d{4}\)` | Academic citations |
| `DOI:\s*\S+` | DOI references |
| `\bv?\d+\.\d+(?:\.\d+)?\b` | Version numbers |

Target: **≥ 5 per 500 words**.

## Conversational boosters (human signal)

| Pattern | Example |
|---------|---------|
| Parenthetical asides (5–50 chars) | "(and honestly, who doesn't?)" |
| Questions mid-paragraph | "Why does this matter?" |
| Contractions | "don't", "can't", "won't", "it's", "that's", "I've" |
| Casual openers | "Look", "Here's the thing", "The truth is", "Trust me" |
| Direct address | "you'll notice", "your team" |
| Short declarative ≤ 5 words | "It works." "Period." |
| First-person experience | "when we tried this", "I shipped" |

Target: **≥ 3 conversational markers per 500 words**.

## Sentence-shape red flags

| Pattern | Issue |
|---------|-------|
| 3+ sentences in a row opening with same transition word | Monotonous LLM rhythm |
| All paragraphs 4–5 sentences (no variance) | Formulaic structure |
| Perfect H2→content ratio (every section same length) | Template-generated |
| Em-dash in every section — used exactly once | GPT-4 signature |
| Bullet lists with 3 identical-length items | LLM output pattern |
| Title-case headings with all words capitalized | Old LLM default |

## Humanity score formula

```
Humanity = 100 
  − (ai_phrases × 3) 
  − (vague_words × 1.5) 
  − (red_flags × 5) 
  + min(specificity_boosters × 2, 20) 
  + min(conversational_boosters × 3, 15)
```

Floor at 0, cap at 100. Normalized per 500 words.

## Rewrite checklist

Before publishing, for each passage:

- [ ] Zero phrases from the AI phrase list
- [ ] < 3 vague quantifiers per 500 words
- [ ] ≥ 5 specificity boosters per 500 words
- [ ] ≥ 3 conversational markers per 500 words
- [ ] No sentence-shape red flags
- [ ] At least one first-person or named-source moment per 500 words
- [ ] Natural variance in paragraph length

## Example

### Before (humanity 42)

> In today's digital world, when it comes to podcast hosting, there are many robust platforms that can help you leverage your content. It's important to note that utilizing the right host can unlock the power of your podcast journey. Furthermore, a seamless experience is essential for growth.

Problems: 6 AI phrases, 4 vague words, 0 specifics, 0 conversational markers.

### After (humanity 88)

> Picking a podcast host sounds boring until you realize the wrong choice costs 14 hours of migration work (Castos 2024 survey, n=412). Three providers dominate: Libsyn launched 2004, Buzzsprout in 2009, Castos in 2016. Between them they host 67% of the top 1,000 shows. Here's how they differ — and when each one actually wins.

Improvements: 0 AI phrases, 0 vague words, 6 specifics, 1 conversational marker ("Here's how").

## False positives to allow

Some flagged words have legitimate uses. Allow when:
- "leverage" in financial context (actual leverage, ratios)
- "utilize" in technical docs (distinguishes from general "use")
- "significant" in statistics (p-value, statistical significance)
- "holistic" in healthcare (actual holistic medicine)

Context-aware: allow if the surrounding sentence defines or requires the term.

## Tools

- Manual scan: `grep -oiE "in today's|leverage|synergy|game-changer" content.md | wc -l`
- Use `creo-seo-content` skill for automated scoring
- Flesch analysis: `textstat` (Python) or online calculators
