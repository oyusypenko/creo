# Schema Validation Checklist

Pre-publish validation for JSON-LD schema in Next.js apps. Catches placeholders, deprecated types, missing required fields, and format errors.

## Automated detection rules

### Rule 1: Placeholder text

Flag any `@type` block containing:

```
[Business Name]   [City]           [INSERT]
[Company]         [ZIP]            [TODO]
[Your ...]        [YYYY-MM-DD]     [URL]
<placeholder>     example.com      your-domain.tld
```

**Severity:** Critical (always block publish)

### Rule 2: Deprecated types

| @type | Status | Action |
|-------|--------|--------|
| `HowTo` | Rich results removed Sept 2023 | Warn, keep markup |
| `SpecialAnnouncement` | Removed July 2025 | Replace with Article |
| `CourseInfo` | Removed 2024 | Use Course |
| `EstimatedSalary` | Removed 2024 | Remove |
| `LearningVideo` | Removed 2024 | Use VideoObject |
| `ClaimReview` | Restricted to accredited fact-checkers | Remove unless accredited |
| `Recipe` with nested `HowTo` steps | Valid — steps use HowToStep | OK |

**Severity:** High (warn) for deprecated, Critical (block) for removed.

### Rule 3: Restricted types

`FAQPage` rich results restricted to:
- Government sites (.gov)
- Health authority sites
- Official consumer protection sites

If your site is commercial → remove FAQPage or expect no rich snippet.

**Severity:** Medium (warn, no rich result expected).

### Rule 4: Required fields per @type

| @type | Missing → fail |
|-------|----------------|
| Article, BlogPosting, NewsArticle | headline, image, datePublished, author |
| Product | name, image, (offers OR aggregateRating OR review) |
| Offer | price, priceCurrency, availability |
| LocalBusiness | name, address, telephone |
| Event | name, startDate, location |
| JobPosting | title, description, datePosted, hiringOrganization, jobLocation |
| Recipe | name, image, recipeIngredient, recipeInstructions |
| VideoObject | name, thumbnailUrl, uploadDate |
| Course | name, description, provider |
| Organization | name, url |
| BreadcrumbList | itemListElement (≥ 1) |
| FAQPage | mainEntity (≥ 1 Question) |
| Person | name |
| Review | itemReviewed, reviewRating, author |
| AggregateRating | itemReviewed, ratingValue, (ratingCount OR reviewCount) |

**Severity:** Critical.

### Rule 5: URL format

All URLs in schema must be:
- Absolute (start with `http://` or `https://`)
- HTTPS preferred for canonical/image URLs
- No trailing whitespace
- Properly URL-encoded

Relative URLs (`/image.jpg`) → fail.

**Severity:** Critical.

### Rule 6: Date format

All date fields must be ISO 8601:
- Valid: `2026-04-14`, `2026-04-14T10:00:00+00:00`, `2026-04-14T10:00:00Z`
- Invalid: `04/14/2026`, `April 14, 2026`, `2026-04-14 10:00`

Fields to check: `datePublished`, `dateModified`, `startDate`, `endDate`, `uploadDate`, `datePosted`, `validThrough`, `birthDate`, `foundingDate`.

**Severity:** High.

### Rule 7: Numeric field types

- `price`, `priceCurrency` → price is string or number, currency is ISO 4217 code (`"USD"`, not `"$"`)
- `ratingValue`, `bestRating`, `worstRating` → numeric range
- `ratingCount`, `reviewCount` → positive integer
- `duration` → ISO 8601 duration (`"PT5M30S"`, not `"5:30"`)

**Severity:** High.

### Rule 8: Image object dimensions (for Article)

Article schema benefits from images with:
- Aspect ratios: 16:9, 4:3, or 1:1
- Min width 1200px (for AMP/high-quality rich results)
- At least 3 sizes for carousel eligibility

**Severity:** Low (rich result enhancement only).

### Rule 9: Structural validity

- Valid JSON (parse it)
- Root `@context` = `"https://schema.org"` (or array including it)
- Root `@type` present
- No unknown properties (validate against schema.org)
- No circular references
- Proper nesting (e.g., Author must be Person or Organization, not string for rich results)

**Severity:** Critical.

### Rule 10: Consistency with page content

- `headline` in Article matches visible H1 (within 10% string similarity)
- `offers.price` matches visible price on page
- `aggregateRating.ratingValue` matches visible star display
- `address` in LocalBusiness matches visible address

**Severity:** High. Mismatches = Google can flag as spam.

## CI pre-commit validator

```bash
#!/bin/sh
# validate-schema.sh — runs in CI on any page change

# Fetch all JSON-LD blocks
pages=$(find app -name "*.tsx" | xargs grep -l "application/ld+json")

for f in $pages; do
  # Extract JSON-LD content (approximate)
  jq empty <(node -e "require('$f')") 2>/dev/null || { echo "Invalid JSON in $f"; exit 1; }
done

# Placeholder detection
if grep -rE "\[Business Name\]|\[City\]|\[INSERT|\[TODO|example\.com" app/ --include="*.tsx"; then
  echo "Placeholder text detected in schema"; exit 1
fi

# Deprecated type detection
if grep -rE '"@type":\s*"(SpecialAnnouncement|CourseInfo|EstimatedSalary|LearningVideo)"' app/ --include="*.tsx"; then
  echo "Deprecated schema type detected"; exit 1
fi
```

## Manual validation tools

| Tool | URL | What it checks |
|------|-----|----------------|
| Google Rich Results Test | https://search.google.com/test/rich-results | Rich-result eligibility per URL |
| Schema.org Validator | https://validator.schema.org | Generic schema validity |
| Bing URL Inspection | https://www.bing.com/webmasters | Bing's parsing |
| Yandex Structured Data | https://webmaster.yandex.com/tools/microtest | Yandex's view |
| GSC URL Inspection | https://search.google.com/search-console | Live rendered state |

## Testing schema in Next.js

```ts
// __tests__/schema.test.ts
import { test, expect } from 'vitest'

test('homepage has Organization schema', async () => {
  const res = await fetch('http://localhost:3000')
  const html = await res.text()
  const match = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)
  expect(match).toBeTruthy()
  const data = JSON.parse(match![1])
  expect(data['@type']).toBe('Organization')
  expect(data.name).toBeTruthy()
  expect(data.url).toMatch(/^https:\/\//)
  expect(data.sameAs).toBeInstanceOf(Array)
})
```

## Checklist summary (pre-publish)

- [ ] JSON parses (no syntax errors)
- [ ] `@context` present
- [ ] `@type` matches page content
- [ ] No deprecated / removed types
- [ ] No placeholder text
- [ ] All required fields for @type present
- [ ] All URLs absolute and HTTPS
- [ ] All dates ISO 8601
- [ ] Schema content matches visible page content
- [ ] Tested on Google Rich Results Test (for relevant types)
- [ ] `</script>` escaped in serialized output (use `\u003c`)
- [ ] One root @type per block (or `@graph` array if multiple)
