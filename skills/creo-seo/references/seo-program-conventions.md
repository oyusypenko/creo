# SEO Program Conventions — Plans, Reports, and Changelogs That Compound

Conventions that make multi-session SEO work survivable: every session knows
what was done, what is deliberate, what is blocked, and what to verify.
Without them, repeat audits restate instead of compounding.

## Ownership tags: DEV vs YOU

Tag every open item with who can close it:

- **DEV** — the agent can do it (code, config, content files, API calls with
  existing credentials).
- **YOU** — will always block on a human: GSC/analytics UI clicks, org-admin
  permission grants, billing, contracts, directory submissions, production
  write credentials the agent does not hold.

Add a time estimate to YOU items ("YOU, ~5 min"). This is the single most
useful convention for agentic SEO: the agent closes DEV items autonomously and
hands off a short, costed YOU list instead of a wall of mixed tasks.

## Status legend: bug vs by-design

Every finding/plan item carries one of:

- FIXED — shipped, with commit/PR reference
- BY-DESIGN — intentional, not a bug (deliberate noindex facets, expected
  redirects, robots-blocked search pages). Recording this stops future
  sessions from "fixing" intentional behavior forever.
- NEEDS-DECISION — requires a content/product judgment; parked with the
  question stated
- OPEN — actionable defect

## Problem / Fix / Verify triplets

Every plan entry is self-closing:

```
Problem: /pricing emits Product schema; ranking query says "software"
Fix: switch to SoftwareApplication + offers + featureList in pricing/page.tsx
Verify: curl -sL https://example.com/pricing | grep -o '"@type":"[^"]*"'
```

No entry without a one-line verify command. Findings additionally carry
file:line and a code diff.

## The SEO changelog (append-only)

`{reports_path}/CHANGELOG.md`. Rules:

1. READ it at the start of every session — it is the memory.
2. APPEND a dated section at the top after completing work. Include: fixes
   applied (commit hash, files, description), issues found, GSC actions taken
   (indexing requests, sitemap resubmits), remaining issues as checkboxes,
   and — critically — **what was deferred and why** (blocked by policy,
   needs human, needs decision).
3. Never delete old entries. Annotate resolved items in place
   (RESOLVED - see <newer doc>) rather than rewriting — annotate-don't-delete
   keeps history legible.
4. Per fix, record `fixCommitSha` + `deployedAt` + `verifiedAt` so "did it
   actually ship and work" is always answerable (pairs with the autofix
   ledger, `gsc-autofix-loop.md`).

## Repeat-audit reports

Beyond the base template (`audit-report-template.md`), a repeat audit adds:

- **Scope declaration** up front: what is audited, what is excluded and WHY,
  which prior report is the baseline.
- **Progress-vs-prior table**: prior issue | RESOLVED / PARTIAL /
  STILL PRESENT / PENDING-external | evidence. Plus an explicit "no
  regressions against previously-green items" statement.
- **Deferred phases stated with reasons** ("Phase 3 build skipped: 12k-page
  build takes 15 min and the live artifact was verified") — honest scope cuts
  beat silent ones.
- **Live spot-check table**: URL | HTTP | title (+char count) | canonical |
  hreflang | notes.
- **JSON-LD inventory by page type** with a Gaps column.

## Evidence discipline

- Prove claims with pasted command output (`curl | grep canonical` blocks),
  and record DISPROVEN hypotheses too ("canonical tags verified correct;
  this bucket is not a tag bug") — disproof prevents re-investigation.
- Mark unverified claims inline: `[verify]` for a one-minute fact check,
  `[blocked: <reason>]` for genuinely blocked items. Grep-able, and the two
  must not be confused.
- Record REJECTED proposals with reasoning and a revisit condition ("UTM-strip
  middleware rejected: 308 breaks referrer attribution; canonical already
  consolidates; revisit if param URLs start indexing").
- **Config-vs-code drift is an SEO bug**: a project config claiming 3 locales
  while code ships 1 feeds false context to every downstream agent session.
  Check for it explicitly; fix the config or the code.

## Recovery programs (when trends collapse)

Structure a recovery as three documents:

- Master plan: trend evidence on the FOCUSED core (see `semantic-core.md`),
  named root causes, phased schedule (week 1 -> week 4+), numbered actions
  with owner tags, and a "what this plan deliberately does NOT do" fence.
- Technical companion: verified findings (file:line + live evidence +
  ruled-out hypotheses), fixes ordered by ROI, each with a validation window
  (see `deploy-verification.md`).
- Content companion: per-page rewrite briefs — offending passages quoted with
  line numbers, rubric score, directives (title/H1/intro/sections/removals/
  word count), affected queries x trend, lift estimate + effort.

The two companions each declare what the other owns — a natural parallel-agent
decomposition.

Forecast discipline: baseline -> Day 30 -> Day 90 per metric, conservative
floors not aspirations, and the stated haircut rule ("if only on-page ships,
halve every Day-90 number"). Prefer "0 new pages in Phase 1" when the data
says the wins are in fixing existing pages.

## Diagnose before you build

Never author content for a route family until you have proven whether the
problem is empty data, unreachable infrastructure, or content quality — the
three have disjoint fixes. Use the hypothesis-branch runbook
(`indexation-runbook.md`).
