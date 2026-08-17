# SEO Onboarding — One Command From Zero to Operated

Flow for `/creo seo onboard <url>`: take a project from "no SEO process" to a
fully operated lifecycle — audit, implementation plan, Search Console
configuration (guided human steps), and standing monitoring/autofix. This is
the main entry point; every stage delegates to an existing command/reference.

`/creo seo plan <url>` runs Stages 1-2 only (analyze + implementation plan).

## Stage 1 — Analyze

1. `/creo seo init` — build/refresh the project profile.
2. `/creo seo audit <url>` — full 7-phase audit (or `--brief` if the user asks
   for speed). Produces the scored report + issue list.
3. If GSC access already exists: pull top queries/pages and run the
   semantic-core build (`semantic-core.md`) so the plan is query-driven, not
   just code-driven. If not, note it — Stage 3 unlocks this and the plan gets
   a refresh task.

## Stage 2 — Implementation plan

Produce `{reports_path}/seo-plan-{YYYYMMDD}.md` following
`seo-program-conventions.md`:

- Every item is a Problem / Fix / Verify triplet with file:line.
- Every item tagged **DEV** (agent-doable) or **YOU** (human-only, with a
  time estimate).
- Prioritized P0-P3 by business impact; falling/lost queries marked URGENT.
- Status legend includes BY-DESIGN so intentional behavior is recorded once.
- Phased schedule (week 1 / week 2-4 / month 2+) with conservative forecast
  (baseline -> Day 30 -> Day 90) and the on-page-only haircut rule.
- End with the "deliberately not doing" fence.

Get user confirmation on the plan before executing DEV items.

## Stage 3 — Search Console + engine configuration (guided, browser-driven)

Do this WITH the user, not as a handed-off checklist. When browser tools are
available, open the exact Search Console / GCP console page in the user's
signed-in Chrome (deep-link map in the gsc-analyzer agent doc), read the
current state, and drive or narrate each step; the user handles sign-in and
account-level clicks. Verify every step programmatically where possible:

| # | Step | Verify by |
|---|------|-----------|
| 1 | Create/confirm GSC property (prefer `sc-domain:`) | `list-sites` after step 4 |
| 2 | Create GCP project; enable Search Console API (+ Indexing API, optional PageSpeed API) | API call succeeds later |
| 3 | Create service account + JSON key; store OUTSIDE the repo; set `GSC_KEY_FILE` in `.env` (gitignored) | file exists, not tracked by git |
| 4 | Add the service-account email to the GSC property (Settings -> Users; FULL for autofix, restricted for read-only) | `python -m gsc_toolkit list-sites` |
| 5 | Submit sitemap(s) in GSC | Sitemaps API shows them |
| 6 | Register site in Bing Webmaster Tools (ChatGPT leans on Bing); optional API key | key set or explicitly skipped |
| 7 | (If using weekly workflow) add repo secrets: `GSC_SERVICE_ACCOUNT_JSON`, optional `BING_WEBMASTER_API_KEY`, `DATAFORSEO_LOGIN/PASSWORD` | workflow dry run |
| 8 | (If using UI automation) one-time `gsc_ui_export.mjs --setup` sign-in | script exits 0 |

Full setup detail: gsc-analyzer extension `references/gsc-api-reference.md`.
Never accept a key file into the repo; if one is pasted, move it out and
gitignore the path immediately.

## Stage 4 — Monitoring + operations scaffold

1. Write `seo-site-config.json` from the extension template: target domain,
   locales, cluster prefix rules, noise patterns, commercial signals, P0/P2
   clusters. Derive first-pass clusters from the route inventory; refine with
   the user.
2. Copy `templates/seo-weekly.yml` into `.github/workflows/`, adjusting the
   `# ADJUST:` markers. Snapshot lands Mondays (GSC lag ~2 days).
3. Create the ledger from `templates/seo-autofix-ledger.example.json` and a
   canary file from `templates/seo-canaries.example.txt` (root, each locale
   home, one URL per redirect family). Set the sitemap URL floor.
4. Initialize `{reports_path}/CHANGELOG.md` (append-only, per
   `seo-program-conventions.md`).
5. Run the first snapshot + semantic-core build now for a baseline.
6. `/creo seo page-rules` — write the project-scoped page-creation rules so
   new pages are born compliant.

## Stage 5 — Standing cadence

Record in the project config / changelog header:

| Cadence | Action |
|---------|--------|
| Weekly (Mon, automated) | Rank snapshot + LLM citability + year staleness (PR) |
| Weekly (Tue) | `/creo seo autofix` — one day after the snapshot |
| Monthly | Semantic-core refresh + 12-week trend pull + directory tracker review |
| Quarterly | Full re-audit (`/creo seo audit`) with progress-vs-prior table |
| January (by Jan 15) | Year-rollover runbook for Policy A pages |

## Degraded modes

- **No gsc-analyzer extension**: Stages 1-2 fully work; Stage 3 still guides
  the human; Stage 4 monitoring falls back to manual GSC CSV exports read via
  `/creo seo triage`; autofix runs as a manual checklist per
  `gsc-autofix-loop.md`.
- **No GSC access at all** (new site): skip Stages 3-5 monitoring, run the
  audit + plan, submit the site, and schedule onboarding completion for when
  data exists (impressions need ~2-4 weeks to accumulate).

## Completion criteria

Onboarding is done when: plan exists and DEV items are scheduled or shipped;
`list-sites` succeeds; sitemap submitted; baseline snapshot + semantic core
saved; weekly workflow merged; ledger + canaries + changelog exist; cadence
recorded. Report the YOU items still open with time estimates.
