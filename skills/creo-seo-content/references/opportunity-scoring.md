# Content Opportunity Scoring

8-factor weighted score (0–100) for prioritizing which content to create or update. Requires GSC or DataForSEO data for best results.

## Formula

```
Opportunity = 
  Volume(25%) + Position(20%) + Intent(20%) + Competition(15%)
  + Cluster(10%) + CTR(5%) + Freshness(5%) + Trend(5%)
```

## Factor rubrics

### 1. Volume score (25%)

Search volume → 0–100:

| Monthly volume | Score |
|----------------|------:|
| ≥ 5,000 | 100 |
| ≥ 2,000 | 90 |
| ≥ 1,000 | 80 |
| ≥ 500 | 65 |
| ≥ 250 | 50 |
| ≥ 100 | 35 |
| ≥ 50 | 20 |
| < 50 | 10 |

### 2. Position score (20%)

Proximity to target rank. Varies by opportunity type:

| Type | Rule |
|------|------|
| **Quick Win** (currently 11–20, target 1–10) | pos ≤ 12 → 100, ≤ 15 → 85, ≤ 18 → 70, ≤ 20 → 55, > 20 → 30 |
| **Improvement** (currently 1–10, target 1–3) | pos 4–5 → 100, ≤ 7 → 85, ≤ 10 → 70, > 10 → 40 |
| **Medium-Term** (21–50) | ≤ 30 → 70, ≤ 40 → 50, ≤ 50 → 30, > 50 → 10 |
| **New Content** | 60 default |
| **Declining** (dropping positions) | custom per drop rate |

### 3. Intent score (20%)

Commercial value of the intent:

```
intent_score = (commercial_intent / 3.0) × 100
```

commercial_intent 0.1–3.0:
- 0.1–0.5: Pure informational (low intent to buy)
- 0.5–1.5: Educational with mild conversion potential
- 1.5–2.5: Commercial investigation
- 2.5–3.0: High commercial intent (transactional)

Commercial keyword signals boost: "buy", "pricing", "best", "review", "vs", "alternative".

### 4. Competition score (15%)

Inverted SEO difficulty (easier = higher opportunity):

| Difficulty | Score |
|-----------:|------:|
| ≤ 20 | 100 |
| ≤ 35 | 85 |
| ≤ 50 | 70 |
| ≤ 65 | 50 |
| ≤ 80 | 30 |
| > 80 | 10 |

Source: Ahrefs KD, SEMrush KD, or Moz difficulty — pick one and stick with it.

### 5. Cluster score (10%)

Strategic topical-cluster value. Manually assigned 0–100 based on:
- Is this keyword in a priority pillar cluster?
- Does ranking here lift related pages?
- Does the cluster drive downstream conversions?

Defaults:
- Core product pillar → 90–100
- Adjacent pillar → 60–80
- Supporting topic → 30–50
- Unrelated → 10–20

### 6. CTR score (5%)

Gap between actual CTR and expected CTR at current position. Uses standard position-based CTR lookup:

| Position | Expected CTR |
|---------:|-------------:|
| 1 | 31.6% |
| 2 | 15.8% |
| 3 | 10.5% |
| 4 | 7.4% |
| 5 | 5.5% |
| 6 | 4.3% |
| 7 | 3.5% |
| 8 | 3.0% |
| 9 | 2.7% |
| 10 | 2.5% |
| 11–20 | 2.0% → 0.7% (linear decay) |

Scoring:
- Actual < expected × 0.3 → 100 (huge gap to close)
- < expected × 0.5 → 85
- < expected × 0.7 → 70
- < expected × 0.9 → 50
- ≥ expected → 30 (already performing)

### 7. Freshness score (5%)

SERP feature indicators for freshness demand:

- Top Stories / News / Video in SERP → 90
- No freshness signals → 50

Query word patterns: "2026", "this year", "latest", "new", "recent" → boost freshness weight.

### 8. Trend score (5%)

Search volume trajectory:

| Trend | Score |
|-------|------:|
| Rising ≥ 100% YoY | 100 |
| Rising ≥ 50% | 85 |
| Rising ≥ 20% | 70 |
| Rising < 20% | 60 |
| Stable | 50 |
| Declining ≥ 20% | 35 |
| Declining ≥ 50% | 25 |
| Declining ≥ 80% | 10 |

Source: Google Trends, DataForSEO trend data, or GSC 90d-vs-prior-90d comparison.

## Final score and priority

Weighted sum → 0–100 → priority tier:

| Score | Priority |
|-------|----------|
| ≥ 80 | CRITICAL |
| ≥ 65 | HIGH |
| ≥ 45 | MEDIUM |
| ≥ 25 | LOW |
| < 25 | SKIP |

## Traffic projection

Estimate clicks gained by moving from current → target position:

```
clicks_gained = monthly_volume × (expected_ctr[target] − expected_ctr[current])
```

Example: 2,000 volume, pos 11 (CTR 2.0%), target pos 5 (CTR 5.5%)
- Current: 2,000 × 2.0% = 40 clicks/mo
- Target: 2,000 × 5.5% = 110 clicks/mo
- Projected gain: +70 clicks/mo

Multiply by average conversion rate and deal value for revenue projection.

## Opportunity types

### Quick wins (best ROI for short-term)

- Currently ranking 11–20 for commercial keywords
- Low–medium competition
- Already indexed, small content tweaks + stronger internal linking can lift

### Improvements (double down on what works)

- Ranking 4–10 for high-volume commercial keywords
- Content needs depth + freshness to break top 3
- Priority: refresh existing pages

### Declining (stop the bleeding)

- Lost positions in last 90 days
- Competitors published fresher / better content
- Priority: update immediately

### New content (pillar + cluster strategy)

- High-volume keyword with no ranking yet
- Strong topic-cluster fit
- Commercial intent
- Priority: plan full pillar

### Skip (don't waste effort)

- Low volume + high competition + low intent
- Keyword cannibalization risk with existing pages
- Brand-navigational for another company

## Output format

```markdown
## Content opportunity matrix

| Keyword | Volume | Pos | Intent | Comp | Cluster | CTR gap | Fresh | Trend | Score | Priority |
|---------|-------:|----:|-------:|-----:|--------:|--------:|------:|------:|------:|:--------:|
| best react hosting | 2,400 | 14 | 2.8 | 45 | 85 | 100 | 50 | 70 | 78 | CRITICAL |
| what is react | 18,000 | 8 | 0.5 | 82 | 60 | 50 | 50 | 50 | 55 | MEDIUM |
| react performance | 1,900 | 22 | 1.8 | 55 | 75 | 85 | 50 | 85 | 72 | HIGH |

## Top 5 actions (ranked by projected traffic)

1. Refresh `/best-react-hosting` — projected +140 clicks/mo ($1,400/mo est.)
2. Create pillar at `/react-performance` — projected +80 clicks/mo
...
```
