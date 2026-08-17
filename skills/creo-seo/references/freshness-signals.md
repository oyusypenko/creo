# Freshness Signals — One Source of Truth, Year Policy, CI Guards

Freshness leaks are invisible in the browser and expensive in the SERP. Google
cross-reads the title, `dateModified` in JSON-LD, and sitemap `lastmod`; when
they diverge, the page reads as stale or dishonest.

## The divergence failure mode

Real incident triangle:

- Title advertises the current year ("Best X 2026")
- `Article.dateModified` is 86 days stale
- Sitemap `lastmod` is a hardcoded global constant disagreeing with both

Result: -72% impressions on the year-stamped head query. Each signal was set
in a different file by a different person. The fix is structural, not
editorial.

## One source of truth: content-file git mtime

Derive every freshness signal from the same value — the content file's last
commit date:

```bash
git log -1 --format=%cI -- <content-file>
```

Apply it in ONE helper used by both the sitemap generator and every metadata/
JSON-LD builder. Notes:

- CI checkouts need full history (`fetch-depth: 0`); a shallow clone makes
  git-mtime fall back to filesystem stat = "now" and silently breaks the
  signal.
- Never `lastmod = new Date()` on every build — an always-now lastmod is
  discounted by Google exactly like a stale one.
- Never retroactively rewrite `datePublished`. Only `dateModified` moves, and
  only on a real content update.
- A visible "Last updated" stamp on the page should read from the same helper.

## Year-modifier policy (choose per page, record the choice)

**Decision rule: keep the year in the title ONLY if the head query itself
carries the year.** ("best X apps 2026" -> year-stamped; "keto meal plan" ->
evergreen). Year-stamping a page whose query has no year sacrifices the
unmodified head term and buys an annual maintenance obligation.

- **Policy A — year-stamped** (comparison/"best of" pages): commit to the
  January rollover runbook below.
- **Policy B — evergreen** (guides, feature pages, topical content): never add
  a year to title/H1; years may appear in body text only next to dated facts.

Rejected alternative, for the record: a `{{currentYear}}` template macro. The
year is part of the search-term match and the honesty contract ("2026" must
mean re-verified in 2026), not a display value.

## January rollover runbook (Policy A pages)

Complete by Jan 15; a page still showing the prior year on Jan 16 is a
liability:

1. Re-verify the page's claims (competitor pricing, availability, features).
2. Update the year in title/H1/intro.
3. Add a "What changed in <YEAR>" section with 4-6 dated bullets — the refresh
   must be substantive, not cosmetic.
4. Bump `dateModified` (via a real commit to the content file).
5. Rotate `<YEAR+1>` query variants into an H2/FAQ once search volume appears.
6. Re-pull GSC after 2 weeks to confirm the head query recovered.

## CI guard: the conjunctive staleness check

Flag a page only when BOTH conditions hold:

- a string contains the current or previous year, AND
- the page's `dateModified` is > 90 days old

Neither alone fires (years in fresh pages are fine; stale pages without year
claims are a different problem), which keeps false positives near zero.

Implementation details that matter (script:
gsc-analyzer extension `check_year_staleness.mjs`):

- Year regex with lookarounds so `12026` never matches:
  `(?<![0-9])(20\d{2})(?![0-9])`
- Suppress date-field paths (`dateModified`, `datePublished`,
  `foundingDate`…) — they legitimately contain years.
- Allow-list copyright strings and explicitly whitelisted paths.
- If a file has multiple `dateModified` values, use the most recent; if none,
  skip (git-mtime covers it).
- Exit codes: 0 clean / 1 findings / 2 script error. Emit a header-only CSV
  even when clean so downstream consumers never hit a missing file.

Run it weekly (see extension `templates/seo-weekly.yml`) as inform-only in the
snapshot PR, and optionally as a hard CI gate in December-January.

## Inventory command

Find hardcoded years outside date fields:

```bash
git grep -nE '(?<![0-9])20[0-9]{2}' -- 'content/**' 'messages/**' \
  | grep -viE 'datemodified|datepublished'
```

## Quick checklist

- [ ] Sitemap lastmod, JSON-LD dateModified, and visible stamp share one
      git-mtime helper
- [ ] No `new Date()` lastmod; no hardcoded lastmod constants
- [ ] Every year-stamped page has a Policy A/B decision recorded
- [ ] Staleness check wired into the weekly snapshot
- [ ] CI has full git history where the helper runs
