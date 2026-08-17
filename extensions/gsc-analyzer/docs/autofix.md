# GSC Auto-Fix Loop

A closed loop that detects Google Search Console issues, applies a narrow set
of allowlisted fixes, verifies them live, nudges Google to recrawl, and tracks
everything in an anti-thrash ledger so the same issue is never "fixed" twice
while Google's 2-6 week recrawl lag plays out.

The fix policy (what may be auto-fixed vs. what must become a GitHub issue)
lives in the creo-seo skill reference: `skills/creo-seo/references/gsc-autofix-loop.md`.
This document covers the mechanics of the three scripts in `scripts/`.

## Pipeline

```
detect -> triage vs ledger -> allowlisted fix -> deploy -> verify (origin + edge)
      -> notify Google -> request GSC "Validate Fix" (manual/UI) -> update ledger
      -> re-arm the next scheduled run
```

1. **Detect** (`gsc_autofix_detect.py`): budgeted URL Inspection sweep plus a
   sitemap health check and a week-over-week click-anomaly check. Emits a JSON
   issues report.
2. **Triage vs ledger**: for each actionable issue, key `(url, issueType)`.
   Not in the ledger -> fix candidate. In the ledger as
   `fixed_pending_recrawl` and the live check still passes -> update
   `gscLastSeen` only, never re-fix (GSC re-reporting during recrawl lag is
   expected). Live for > 30 days and GSC still reports it -> mark `escalated`
   and open an issue instead of editing code.
3. **Allowlisted fix**: apply only fixes permitted by the policy reference
   above; batch into one commit; validate/lint/test before pushing. On
   failure, revert and record `failed` in the ledger.
4. **Verify** (`gsc_autofix_verify.sh`): assert every fixed URL resolves
   200 at the exact expected final URL in at most 2 redirect hops, plus the
   robots.txt and sitemap invariants. If a CDN fronts the site, also compare
   the edge response against a cache-busted origin request and purge stale
   URLs - a deploy alone does not make a fix live for Google.
5. **Notify** (`gsc_request_reindex.py`): resubmit the sitemap and optionally
   send Indexing API notifications for the fixed URLs. Best-effort, never
   fatal.
6. **Validate fix**: the GSC UI "Validate Fix" button has no public API - it
   stays a one-click manual step the run report calls out.
7. **Ledger update**: new entries as `fixed_pending_recrawl` with the commit
   SHA, deploy time, and verify time; commit the ledger change.
8. **Re-arm**: schedule the next run (e.g. weekly, the day after your GSC
   snapshot lands, respecting GSC's ~2-day data lag).

## Scripts

### gsc_autofix_detect.py

```bash
export GSC_SITE_URL="sc-domain:example.com"        # required
export GSC_KEY_FILE="/path/to/service-account.json"

python3 scripts/gsc_autofix_detect.py \
    --budget 300 \
    --ledger ./seo-autofix-ledger.json \
    --exports-dir ./gsc-exports \
    --urls-file ./unindexed-urls.txt,./priority-urls.txt \
    --sitemap-url https://example.com/sitemap.xml \
    --sitemap-min-urls 35000 \
    --out ./gsc-autofix-report.json
```

Sample assembly is priority-ordered: ledger URLs first (prior fixes are always
re-verified), then GSC UI CSV exports from `--exports-dir`, then curated
`--urls-file` lists, then a rotating slice of the sitemap keyed by ISO week -
consecutive weekly runs cover different slices with no state. The sweep stays
quota-aware (0.2s delay, default budget 300 of the 2,000/day URL Inspection
quota) and on a 429 it stops early but still writes a partial report.

Each inspected URL can yield multiple issues: broken fetch states, noindex,
robots disallow, canonical mismatch, rich-results FAIL/PARTIAL. Coverage-state
observations outside the known-good set are recorded as `informational` -
the fix phase uses them to update the ledger, never to edit code.

`--sitemap-min-urls` defaults to 1 (only "non-empty"); set a real floor for
your site so silent sitemap truncation is caught.

### gsc_request_reindex.py

```bash
export GSC_SITE_URL="sc-domain:example.com"
export GSC_SITEMAP_FEED="https://example.com/sitemap.xml"

python3 scripts/gsc_request_reindex.py --resubmit-sitemap
python3 scripts/gsc_request_reindex.py --urls ./fixed-urls.txt
```

Always exits 0: the loop continues even when Google declines the nudge, since
recrawl happens organically anyway. Errors are mapped to actionable hints
(missing FULL property permission, Indexing API not enabled on the GCP
project, service account not a verified owner). Sitemap resubmission uses the
webmasters scope; URL notifications use the indexing scope. Note the Indexing
API is officially only for JobPosting/BroadcastEvent pages - treat URL
notifications as best-effort.

### gsc_autofix_verify.sh

```bash
BASE_URL=https://example.com bash scripts/gsc_autofix_verify.sh \
    --canaries ./seo-canaries.txt \
    --expectations ./this-run-fixes.txt
```

Runs three groups of checks and exits with the failure count:

- Canary suite (`--canaries`): a stable expectations file you maintain - see
  `templates/seo-canaries.example.txt` (root, each locale home, one URL per
  redirect family).
- Invariants (always run): robots.txt returns 200 with no blanket
  `Disallow: /`; sitemap.xml returns 200 with at least `SEO_SITEMAP_MIN_URLS`
  `<loc>` entries (default 1).
- Per-run fixes (`--expectations`): the URLs this run changed, same
  `<url> <expected_final_url>` format.

## Environment variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `GSC_SITE_URL` | detect, reindex | GSC property (required), e.g. `sc-domain:example.com` |
| `GSC_SERVICE_ACCOUNT_JSON` | detect, reindex | service-account JSON content (checked first) |
| `GSC_KEY_FILE` | detect, reindex | path to service-account JSON (checked second) |
| `GOOGLE_APPLICATION_CREDENTIALS` | detect, reindex | path to service-account JSON (checked last) |
| `SEO_SITEMAP_URL` | detect | sitemap URL (or `--sitemap-url`) |
| `SEO_SITEMAP_MIN_URLS` | detect, verify | sitemap URL-count floor (default 1) |
| `GSC_SITEMAP_FEED` | reindex | sitemap URL to resubmit (or `--sitemap-feed`) |
| `BASE_URL` | verify | site base URL (or `--base`) |

## Templates

- `templates/seo-autofix-ledger.example.json` - ledger schema with two example
  entries; copy to your project as `seo-autofix-ledger.json`.
- `templates/seo-canaries.example.txt` - canary expectations file format and
  recommendations; copy and fill with URLs verified against production.
