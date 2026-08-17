# SEO Monitoring Scripts

Rank-tracking and trend-analysis tooling in `extensions/gsc-analyzer/scripts/`.
All scripts are project-agnostic: site knowledge comes from a per-project
config file, credentials come from env vars, and paths come from CLI flags.

## The site config

Every script loads a JSON site config through `seo_site_config.py`:

1. `--site-config PATH` flag, else
2. `SEO_SITE_CONFIG` env var, else
3. `./seo-site-config.json` in the working directory.

Copy `templates/seo-site-config.example.json` to your project root and edit
it. It defines: `target_domain`, `known_locales`, `clusters` (ordered
URL-path -> cluster-name rules, first match wins, fallback `other`),
`commercial_paths`, `commercial_signals` (substrings that always override
noise), `noise_patterns` / `purpose_patterns` (regexes on the lowercased
query), and `p0_clusters` / `p2_clusters` for the P0-P3 priority rubric.

Without a config the scripts still run, degraded: everything clusters to
`other`, the noise filter is off, and priorities use impressions/position
only. A stderr warning reminds you to create one.

## Common environment

| Variable | Used by | Purpose |
|----------|---------|---------|
| `GSC_SITE_URL` | all GSC pulls | property, e.g. `sc-domain:example.com` |
| `GSC_KEY_FILE` or `GOOGLE_APPLICATION_CREDENTIALS` | all GSC pulls | service-account JSON key path |
| `BING_WEBMASTER_API_KEY`, `BING_SITE_URL` | weekly snapshot | optional Bing merge |
| `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | LLM visibility | DataForSEO auth (exit 2 if missing) |
| `SEO_TARGET_DOMAIN` | LLM visibility | overrides `target_domain` from the config |
| `LLM_PRIORITY_FILTER` | LLM visibility | default `P0,P1` |

Python deps: `pip install google-api-python-client google-auth requests`.

## The scripts

**pull_semantic_core.py** — pulls 90 days of query x page x country data,
aggregates with impression-weighted position, clusters by taxonomy, assigns
a first-pass priority, writes `--out` (default
`./seo-reports/semantic-core.csv`) plus a JSON summary on stdout.

**filter_semantic_core.py** — splits that pull into
`semantic-core.raw.csv` (all rows + `is_noise`) and the focused core
(noise dropped, re-ranked P0-P3, sorted by opportunity score =
impressions / position). Prints a top-25 table. Flags: `--in`, `--raw-out`,
`--out` (defaults under `./seo-reports/`).

**pull_weekly_snapshot.py** — one CSV per ISO week (Mon-Sun) named by its
Sunday under `--out-dir` (default `./seo-reports/rank-history/`).
Re-running for the same week overwrites the file: GSC backfills late data,
so the latest pull wins. Uses a 1-impression floor (weekly buckets are
small) and tags `is_in_focused_core` from `--core-csv` when given. Bing
rows merge in when the Bing env vars are set; Bing failures degrade
gracefully to a GSC-only snapshot.

**pull_trends_12w.py** — 12 ISO weeks (rolling: end = today - 3 days;
override with `--start` / `--end`), aggregated into weekly buckets, then
compared half-over-half. Labels each query/page `rising` / `falling` /
`new` / `lost` / `stable` with volume-gated asymmetric rules, and writes
`queries-12w.csv`, `pages-12w.csv`, and `_trend-summary.json` (includes the
aggregate focused-core trajectory) under `--out-dir` (default
`./seo-reports/trends/`).

**track_llm_visibility.py** — checks whether your domain is cited in
Google AI Overview, ChatGPT, and Perplexity SERPs (DataForSEO Live) for
each P0/P1 core query. Prints a cost estimate to stderr before spending.
Output: `--out-dir` (default `./seo-reports/llm-visibility/`) dated CSV
with per-surface cited/position/error columns. `--location-code` defaults
to 2840 (US).

**check_year_staleness.mjs** — walks JSON content under `--root` (required)
and flags strings containing the current/previous year when the file's
`--date-field` (default `dateModified`) is older than `--max-age-days`
(default 90). Both conditions must hold. Exit 0 clean / 1 findings / 2
script error; always writes the CSV (header-only when clean) to `--out`.

Typical sequence:

```bash
export GSC_SITE_URL="sc-domain:example.com"
export GSC_KEY_FILE="/path/to/service-account.json"
python3 scripts/pull_semantic_core.py
python3 scripts/filter_semantic_core.py
python3 scripts/pull_weekly_snapshot.py --core-csv ./seo-reports/semantic-core.csv
python3 scripts/pull_trends_12w.py
node scripts/check_year_staleness.mjs --root=content/en/pages
```

## Weekly workflow

Copy `templates/seo-weekly.yml` to `.github/workflows/seo-weekly.yml` and
edit the `# ADJUST:` lines (property, script paths, content root, default
branch). It runs Monday 08:00 UTC (after the ~2-day GSC lag closes the
prior ISO week) and opens a PR with the new snapshot plus a top-movers
table. Repository secrets:

- `GSC_SERVICE_ACCOUNT_JSON` (required) — the full key JSON, written to a
  temp file and deleted before commit
- `BING_WEBMASTER_API_KEY` (optional)
- `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` (optional; the step is
  continue-on-error so SERP API outages never block the GSC snapshot)

## Reading the data

- Filter on `is_in_focused_core=true` (or `in_focused_core`) first — that
  is the query set you chose to compete on; the rest is context.
- `current_position` is impression-weighted across days/countries, so a
  single high-volume bad day moves it more than several quiet good days.
- Read direction over level: a P2 query moving 28 -> 14 matters more than a
  stable P1 sitting at 6. The trend labels and weekly deltas exist for
  exactly this.
- `inf` in `delta_impressions_pct` means the first half had zero
  impressions (new visibility, not an error).
