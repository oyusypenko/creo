# GSC Coverage Triage — Reading Indexing Reports Without Manufacturing Work

Doctrine for interpreting Search Console Page-Indexing buckets. The core rule:
**a non-zero count in a coverage bucket is not necessarily a bug.** Many buckets
report expected, healthy canonicalization behavior. Triage before fixing.

## The triage method

1. **Export the bucket** (UI drilldown export — see gsc-analyzer extension).
2. **Categorize every URL** against the config rule that produces it.
3. **Verdict each category**: EXPECTED or CONCERN.
4. **Chart the count over time** (Chart.csv in the export gives the daily
   trend) and project the trajectory.
5. **Live-check before filing**: `curl -sIL` the newest-crawled rows first.
   GSC recrawl lag is 2-6 weeks — most 404/5xx/redirect rows have already
   self-healed. The per-row `Last crawled` date is decisive.
6. **Define the alarm condition** instead of acting on a stable/declining
   count.

## Direction over level

For coverage buckets, the trend matters more than the number. A "Page with
redirect" count declining week over week (e.g. 141 -> 121 -> 90 -> 75) as
Google digests canonicalization needs **zero action**. The same count rising
needs investigation:

- new external backlinks pointing at non-canonical URLs?
- new pages added without the canonical URL format?
- sitemap changes introducing non-canonical variants?

Write those alarm conditions into the report instead of "fixing" a healthy
decline.

## "Page with redirect" — expected categories

All of these are correct canonicalization artifacts, not errors:

| Category | Produced by | Verdict |
|----------|-------------|---------|
| www -> non-www (or reverse) | host-canonicalization redirect | EXPECTED |
| HTTP -> HTTPS | protocol redirect | EXPECTED |
| Missing locale prefix | i18n middleware redirect | EXPECTED |
| Missing/extra trailing slash | trailingSlash normalization | EXPECTED |
| Root -> default locale | locale routing | EXPECTED |
| Removed legacy route -> replacement | intentional 301/308 | EXPECTED |
| 2+ hop chains (e.g. www AND slash) | stacked normalizations | CONCERN if common |

Google follows up to ~5 hops but prefers 1. Flag chains > 2 hops; collapse
stacked normalizations into a single redirect where they are frequent.

Where do non-canonical URLs come from if internal links are clean? External
backlinks, social shares, and historical pre-normalization crawl data. Verify
internal links route through a canonical URL builder and the sitemap contains
only canonical URLs — then the bucket is externally driven and self-limiting.

## Bucket-by-bucket defaults

| Bucket | Default posture |
|--------|----------------|
| Page with redirect | Usually EXPECTED (see above) |
| Alternate page with proper canonical tag | EXPECTED — canonicalization working |
| Excluded by 'noindex' | EXPECTED if the noindex is deliberate (facets, search, thin locales); CONCERN otherwise |
| Not found (404) | Live-check first; fix only reproducible 404s with real inbound links |
| Server error (5xx) | Live-check; transient deploy blips self-heal, repeated URLs are real |
| Duplicate without user-selected canonical | CONCERN — add explicit canonicals |
| Duplicate, Google chose different canonical | Verify the tag first; if the tag is correct, cause is usually content similarity (e.g. locale pages serving fallback content), not a tag bug |
| Crawled - currently not indexed | Content-quality signal; never mechanical. Needs content/link work |
| Discovered - currently not indexed | Crawl-budget / internal-link signal |
| Blocked by robots.txt | EXPECTED if the block is deliberate; audit robots paths against the real route table (they drift) |

## Recurring root causes worth grepping for

- **Bare internal hrefs** missing locale prefix or trailing slash: every click
  costs a 308, shows up as "Page with redirect", wastes crawl budget. Sweep:
  grep internal `href="/..."` and route all links through a canonical URL
  helper/enum.
- **Body-copy URL extraction**: Googlebot extracts `/segment` substrings from
  plain text as relative URLs. `$9.99/month` gets crawled as `/month` -> 404.
  Write `$9.99 / month` or "per month"; keep path-like strings out of JSON-LD
  descriptions.
- **Facet/query-string URLs** in exports: split them from clean paths first;
  they are usually deliberate noindex/robots territory.
- **Locale deep-merge fallback**: a locale that serves default-language content
  under its own URL generates "duplicate" buckets. Either noindex the locale
  until translated, or canonical each page to its translated counterpart.

## Redirect health rubric

Score these six dimensions when auditing redirects (0-10 each):

1. Redirect correctness (every entry lands on the canonical URL)
2. Chain depth (target: 1 hop; flag > 2)
3. Sitemap hygiene (canonical URLs only)
4. Internal-link hygiene (no internally generated redirects)
5. Robots/allow-list consistency with the real route table
6. Trend direction of the coverage bucket

## Report the verdict, not just the count

A triage report ends with one of:

- "All N entries expected; alarm condition: count rising or new category
  appearing." (no action)
- "Category X (n=…) is a defect: root cause, fix, validation command."

This prevents the most common SEO-agent failure mode: generating make-work
from healthy reports.
