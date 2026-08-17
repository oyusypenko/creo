# Deploy Verification — Proving an SEO Fix Actually Shipped

A deploy is not "live" for Google until the bytes Google fetches are the new
bytes. Origin-correct but edge-stale is the most common silent failure. Every
SEO fix ends with this sequence, not with the merge.

## The sequence

```
deploy completes -> verify at ORIGIN -> verify at EDGE -> purge if stale
                 -> request recrawl -> record verifiedAt in ledger/changelog
```

Deploy alone never closes a GSC issue. Verify live, then request recrawl.

## Origin vs edge (the CDN cache trap)

Real incident pattern: sitemap fixed and deployed correctly, but the CDN kept
serving the old response for weeks because it was cached with a long `max-age`
and no `s-maxage`. Google saw the stale sitemap the whole time.

**Check:**

```bash
# Edge response (what Google sees)
curl -s https://example.com/sitemap.xml -o edge.out
# Origin response (cache-busted)
curl -s "https://example.com/sitemap.xml?cb=$(date +%s)" -o origin.out
diff -q edge.out origin.out || echo "EDGE STALE - purge required"
```

**If edge is stale:**

1. Purge the specific URL only — never "purge everything".
2. No purge-capable credential? Route around it:
   - Submit the new URLs / sitemap shards directly to GSC so Google gets
     correct data immediately.
   - Report the exact dashboard click-path to the human.
   - Note the stale entry self-heals at TTL expiry.
3. Prevent recurrence: set a short `s-maxage` (minutes-hours) on sitemap.xml,
   robots.txt, and llms.txt responses. These files must never be cached for
   days.

## Redirect assertions — three-part, not "is it 200"

For every fixed or canary URL, assert all three:

1. Final status is exactly 200
2. Final URL matches the expected canonical URL **exactly**
3. Redirect hops <= 2 (Google follows ~5 but penalizes chains)

One curl gives all three:

```bash
read -r code hops final < <(curl -s -o /dev/null -L \
  -w "%{http_code} %{num_redirects} %{url_effective}" "$URL")
```

A 200 that lands on the wrong destination, or a 200 after 4 hops, is a
regression that a status-only check waves through.

## Canary suite — always run, regardless of what changed

A permanent expectations list that runs on every verification, independent of
the fix being verified:

- the root URL
- each locale homepage
- **one URL per redirect family** (www, trailing slash, locale prefix, legacy
  route, protocol)

A targeted fix that breaks an unrelated redirect group gets caught immediately.
Keep the list in a versioned file: `<url> <expected_final_url>` per line
(template: gsc-analyzer extension `templates/seo-canaries.example.txt`).

## Invariant checks — catastrophic-but-silent failures

Run with every verification:

| Invariant | Failure it catches |
|-----------|-------------------|
| `robots.txt` returns 200 and contains no blanket `Disallow: /` | Staging robots shipped to production |
| `sitemap.xml` returns 200 with `<loc>` count >= project floor | Silent truncation (missing build env var shrinking the sitemap while HTTP stays 200) |
| Key page contains `<script type="application/ld+json">` | Schema rendering path silently dropped |

Set the sitemap floor per project (slightly below the known-good count).

## Failure handling

- Exit code = failure count (trivially consumable by the orchestrating agent).
- Any verify failure after an autofix run: `git revert`, push, mark the ledger
  entry `failed`, open an issue, stop. Never "fix the fix" inside the same
  automated run.

## Validation windows — when to expect GSC to reflect the fix

Calibrated expectations per fix class; re-check on this schedule, not daily:

| Fix class | Window |
|-----------|--------|
| Indexation (new/resubmitted URLs) | ~7 days |
| Freshness signals (lastmod, dateModified) | ~14 days |
| Internal-link changes | ~30 days |
| Schema / rich-result changes | ~60 days |

GSC re-reporting an already-fixed issue inside these windows is expected
recrawl lag, not a failed fix (see `gsc-autofix-loop.md` ledger rules).

## Lift priors — sanity-checking impact estimates

Defaults for forecasting, derived from observed movements:

- Moving up 5 positions on page 1: roughly +30-60% impressions
- Position 30 -> 15: roughly doubles impressions
- Position 80 -> 25: 3-5x over 8-12 weeks
- If only on-page work ships (no off-page), halve every 90-day forecast

Queries stuck beyond ~position 40 after on-page work are off-page-limited:
stop rewriting, start authority building (see `offpage-authority.md`).
