# GSC Autofix Loop — Closed-Loop Search Console Remediation

Autonomous weekly cycle that detects Search Console issues, applies only safe
allowlisted fixes, verifies them live, and tracks everything in a ledger so the
same issue is never fixed twice. Scripts live in the `gsc-analyzer` extension
(`extensions/gsc-analyzer/scripts/`, see its `docs/autofix.md`).

## Pipeline

```
detect -> triage vs ledger -> allowlisted fix -> validate -> commit/push
       -> watch deploy -> verify live (origin AND edge) -> notify Google
       -> trigger "Validate Fix" (UI) -> update ledger -> re-arm schedule
```

One run = one commit, max 10 URLs fixed. Every push may trigger a full site
rebuild, so batch fixes into a single commit per run.

## Fix allowlist — the safety core

Auto-fix ONLY additive, mechanically verifiable changes:

| Allowed | Condition |
|---------|-----------|
| Add a redirect entry | Target route provably exists and returns 200 |
| Add missing URL to sitemap | Page exists in the route inventory |
| Fill missing meta title/description (default locale) | Source content exists to derive it from |
| Fill mechanical JSON-LD field | Value derivable from existing page data (e.g. a missing `recipeYield`-class required field) |

BLOCKED — never auto-edit; open a GitHub issue instead:

- robots.txt changes of any kind
- canonical / hreflang logic changes
- wildcard or regex redirects; reordering existing redirect rules
- non-default-locale content edits
- anything in the "Crawled - currently not indexed" bucket (content-quality judgment)
- deleting or rewriting existing rules or content

Rule of thumb: if the fix requires judgment about intent, it is not a fix — it
is a decision. Route decisions to humans via issues.

## Anti-thrash ledger

JSON ledger keyed by `(url, issueType)`. Template:
`extensions/gsc-analyzer/templates/seo-autofix-ledger.example.json`.

Statuses: `fixed_pending_recrawl` | `escalated` | `failed`.

Triage rules (the anti-thrash core):

1. **GSC re-reports a ledgered issue AND the live check passes** — expected.
   GSC recrawl lag is 2-6 weeks. Only bump `gscLastSeen`. Never re-fix.
2. **Ledgered > 30 days, live check passes, GSC still reports** — set
   `escalated`, open an issue with a residual-cause hypothesis (edge cache,
   external links, canonical elsewhere).
3. **Live check fails for a ledgered fix** — the fix regressed. Set `failed`,
   `git revert`, open an issue, stop the run.
4. New issue not in ledger — candidate for the allowlist check.

Record per entry: `fixCommitSha`, `deployedAt`, `verifiedAt` — so "did this
actually ship and did it work" is always answerable.

## Run sequence

1. **Detect** — `gsc_autofix_detect.py`: budgeted URL-inspection sweep
   (ledger entries first, then GSC UI exports, curated lists, rotating sitemap
   slice), sitemap health floor, week-over-week click-anomaly check.
2. **Triage** — apply the ledger rules above; select at most 10 allowlisted,
   actionable issues.
3. **Fix** — apply the code changes; run the project's typecheck + build.
4. **Commit** — exactly one commit; push; watch the deploy to completion.
5. **Verify** — `gsc_autofix_verify.sh`: canary suite + invariants + per-fix
   expectations. Non-zero exit = revert (rule 3 above).
   Always verify at the EDGE, not just origin — see `deploy-verification.md`.
6. **Notify** — `gsc_request_reindex.py`: resubmit sitemap, request indexing
   for fixed URLs. Best-effort, never fails the run.
7. **Validate Fix** — `gsc_validate_fix.mjs` presses the UI-only button.
   Best-effort; exit 2 = session expired: skip and flag the human.
8. **Ledger + changelog** — update ledger entries; append a dated section to
   the SEO changelog (see `seo-program-conventions.md`).
9. **Re-arm** — schedule the next run (see below).

## Scheduling

- Run weekly, one day AFTER the analytics snapshot day, because GSC data lags
  ~2 days (e.g. snapshot Monday, autofix Tuesday).
- If the scheduler only supports expiring one-shot jobs: the LAST step of each
  run schedules the next one-shot with the verbatim run prompt. Store that
  prompt in the project runbook so any session can restart a broken chain
  (missed-run recovery).

## Failure posture

- Browser-automation steps (UI export, Validate Fix) are best-effort. They may
  fail on session expiry or selector drift; log, skip, flag the human. The
  loop must never block on its flakiest step.
- API "notify" steps are non-fatal by design: Google recrawls organically
  whether or not the nudge lands.
- Quota exhaustion mid-detect: write a partial report and continue with what
  was inspected.
- Verify failure is the only hard stop: revert, ledger `failed`, open issue.

## Per-project configuration

The loop needs, per project (put in `.claude/project-config.md` and env):

- `GSC_SITE_URL` (e.g. `sc-domain:example.com`), `GSC_KEY_FILE`
- Production base URL + canary expectations file (one URL per redirect family)
- Sitemap URL + minimum expected URL count (catches silent truncation)
- Ledger path, reports path, changelog path
- The project's build/typecheck commands for the fix-validation step

## Sanity anchors (learned the hard way)

- The GSC API cannot enumerate the example URLs behind "Why pages aren't
  indexed" — those tables are UI-only. Use the drilldown export scripts
  (see gsc-analyzer extension) or curated URL lists.
- Substring-matching coverage states is unsafe: "Crawled - currently not
  indexed" contains "indexed". Compare against an exact allowlist of OK states.
- A sitemap that silently shrinks (missing build env var) looks healthy at
  HTTP level. Enforce a minimum `<loc>` count.
- Most 404/5xx/redirect rows in GSC exports self-heal — always live-check the
  newest-crawled rows before fixing anything (see `coverage-triage.md`).
