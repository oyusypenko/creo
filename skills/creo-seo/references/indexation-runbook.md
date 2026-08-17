# Indexation Runbook — Hypothesis-Branch Template for "N URLs Missing"

Template for any incident of the shape "a route family is not indexed /
missing from the sitemap / returning empty". The discipline: prove which
hypothesis holds BEFORE building anything, using tests whose output
discriminates between causes.

## When to use

- A route family (e.g. `/recipes/*`, `/blog/*`) shows zero impressions
  (opportunity bucket D in `semantic-core.md`)
- Sitemap contains far fewer URLs of a family than expected
- A listing endpoint returns empty on production but not locally

## Runbook structure (write one per incident)

### 1. Symptom recap with live evidence

State the observable facts with commands and outputs, and explicitly note
what is HEALTHY so nobody re-audits it:

```
Symptom: /api/recipes returns {"total":0} on production; sitemap has 6
recipe URLs, expected ~5,000.
Healthy: the rendering code path is correct (app/recipes/[slug]/page.tsx:40
guards on isPublic; robots.ts:43 only blocks /recipes/search).
```

### 2. Named hypothesis branches, each with ONE discriminating test

| Branch | Hypothesis | Discriminating test | If it fires |
|--------|-----------|--------------------:|-------------|
| A | Data layer is empty (seed/migration never ran) | `SELECT COUNT(*) FROM recipes WHERE is_public = true` | 0 rows -> Branch A |
| B | Build-time env var unresolvable (API base blank/localhost in CI) | grep the build log for the fetch attempt | No attempt logged -> Branch B |
| C | Upstream API erroring at build | Build log shows the request + non-200 | Error logged -> Branch C |

Design tests so the OUTPUT tells you the branch — log distinctly at each
failure point so the log itself discriminates hypotheses.

### 3. Diagnostics as literal commands with expected-vs-current values

```bash
curl -s https://example.com/sitemap.xml | grep -oE '/recipes/[^"<]+' | wc -l
# Expected after fix: >100.  Currently: 6.
```

Every diagnostic states both numbers. "Check the sitemap" is not a
diagnostic; "this command should print >100 and prints 6" is.

### 4. Remediation, dry-run first

- Run the fix (seed script, env var, redeploy) in dry-run mode first where
  one exists.
- State the idempotency guarantee ("early-skip + upsert on conflict — safe to
  re-run") or add one before running.
- One fix per branch; do not fix a branch you have not proven.

### 5. Validation: ordered checklist, no skipping ahead

```
[ ] Data layer: COUNT(*) returns expected volume
[ ] Live API: /api/recipes total > 0
[ ] Rebuild triggered and completed
[ ] Sitemap URL count for the family: >100
[ ] Spot-check 3 URLs return 200 with correct meta + JSON-LD
[ ] Submit sitemap / request indexing for sample URLs
[ ] +7 days: URL Inspection shows sample URLs indexed
[ ] +7 days: GSC impressions for the family > 0
```

Do not move to the next box until the current one passes. The last two boxes
are why the runbook stays open for a week — closing on deploy is the classic
premature victory (see `deploy-verification.md` validation windows).

### 6. Out-of-scope fence

List the adjacent temptations NOT touched, with reasons ("slug redesign
deferred: needs a decision on human-friendly slugs before generating more
URLs"). This keeps the incident scoped and records deliberate deferrals.

## Standing prevention rules

- **Fail the build loudly** when a build-time API base URL is blank or
  resolves to localhost under production builds. Silent fallbacks are how a
  0-URL sitemap ships with a green pipeline.
- **Sitemap floor invariant**: enforce a minimum URL count in the verify
  suite (see `deploy-verification.md`) — the same incident class caught at
  deploy time instead of weeks later in GSC.
- **Pagination caps**: when the sitemap or a pull script paginates an API,
  the page size must match the server's actual cap; a mismatched cap silently
  truncates (observed: 1,155 URLs capped at 100).
- **Sitemap scale limits**: 50,000 URLs / 50 MB per file is a hard Google
  limit. If inventory times locales approaches it, shard into a
  `<sitemapindex>` BEFORE it breaks — the failure mode is `errors: 1` in GSC
  and silently dropped URLs (see `sitemap-patterns.md`).

## Anti-patterns

- Writing content or building links for pages that are not indexed (bucket D
  misrouted as bucket A/C).
- Fixing two hypotheses at once — you learn nothing and cannot attribute the
  recovery.
- Closing the incident at "deployed" instead of "verified in GSC".
