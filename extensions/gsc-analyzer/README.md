# GSC Analyzer Extension for Creo

A self-contained optional extension that adds Google Search Console analysis and comprehensive SEO auditing capabilities to Creo.

## What It Does

- **Google Search Console API** - Search analytics, URL inspection, sitemaps, coverage reports
- **PageSpeed Insights API** - Core Web Vitals analysis (LCP, FID, CLS, TTFB)
- **Google Indexing API** - Request URL indexing (200/day quota)
- **Security Headers Analysis** - HSTS, CSP, X-Frame-Options, Referrer-Policy
- **On-Page SEO Analysis** - Title, meta description, headings, images, canonical, Open Graph
- **Schema/Structured Data Validation** - JSON-LD parsing, required/recommended fields
- **Hreflang Validation** - International SEO, return link checking, language codes
- **Robots.txt & Sitemap Validation** - Syntax, directives, blocking detection
- **Content Quality Analysis** - Readability metrics (Flesch-Kincaid, Gunning Fog), freshness, language detection
- **Mobile SEO Analysis** - Viewport, touch targets, font sizes, responsive design
- **Performance Analysis** - Render-blocking CSS/JS, image optimization, caching, compression
- **URL & Links Analysis** - Anchor text quality, URL structure, pagination
- **Site-wide Crawling & Audit** - Duplicate content, thin pages, orphan pages, broken links
- **GSC UI Automation** - Page Indexing drilldown exports and "Validate Fix" (surfaces with no API)
- **Closed-Loop Autofix** - Detect, allowlisted fix, live verification, reindex requests, anti-thrash ledger
- **Monitoring** - Weekly rank history, semantic core with noise filtering, 12-week trends, LLM-citability tracking, year-staleness guard

## Prerequisites

- **Python 3.8+**
- **Creo core** must be installed first
- **Google service account** (only for GSC API commands -- page analysis commands work without credentials)

### Optional Python Packages

```bash
pip install beautifulsoup4   # Required for page analysis commands
pip install textstat          # Enhanced readability metrics
pip install langdetect        # Language detection
```

## Install

```bash
# macOS / Linux
./install.sh

# Windows (PowerShell)
.\install.ps1
```

The installer:
1. Checks that Creo core is installed
2. Copies the gsc_toolkit package to `~/.claude/skills/creo-gsc/`
3. Copies the agent to `~/.claude/agents/creo-gsc.md`
4. Creates a Python virtual environment and installs dependencies

## Usage

After installation, use via Creo:

```
/creo gsc full-seo https://example.com
/creo gsc site-audit https://example.com
/creo gsc security https://example.com
/creo gsc onpage https://example.com/page
/creo gsc schema https://example.com
```

Or run the toolkit directly:

```bash
# Activate the venv
source ~/.claude/skills/creo-gsc/.venv/bin/activate

# Run any command
python -m gsc_toolkit full-seo https://example.com
python -m gsc_toolkit site-audit https://example.com --max-pages 100
python -m gsc_toolkit security https://example.com
python -m gsc_toolkit onpage https://example.com/page
python -m gsc_toolkit schema https://example.com
python -m gsc_toolkit hreflang https://example.com
python -m gsc_toolkit robots https://example.com
python -m gsc_toolkit content https://example.com/page
python -m gsc_toolkit mobile https://example.com
python -m gsc_toolkit performance https://example.com
python -m gsc_toolkit url-analysis https://example.com/page
```

### GSC API Commands (require service account)

```bash
python -m gsc_toolkit list-sites
python -m gsc_toolkit inspect <url>
python -m gsc_toolkit analytics [--days 28] [--dimension query|page]
python -m gsc_toolkit sitemaps
python -m gsc_toolkit cwv <url>
python -m gsc_toolkit index-request <url>
python -m gsc_toolkit seo-audit [--days 28]
python -m gsc_toolkit full-report
```

For GSC API access, configure a `.env` file in your working directory:

```
GSC_KEY_FILE=./service-account-key.json
GSC_SITE_URL=sc-domain:your-domain.com
GSC_DEFAULT_DAYS=28
PAGESPEED_API_KEY=your_api_key
```

## Available Analyzers

| Analyzer | Command | API Required |
|----------|---------|:---:|
| Security Headers | `security <url>` | No |
| On-Page SEO | `onpage <url>` | No |
| Schema Validation | `schema <url>` | No |
| Hreflang Validation | `hreflang <url>` | No |
| Robots.txt & Sitemap | `robots <url>` / `sitemap-check <url>` | No |
| Content Quality | `content <url>` | No |
| Mobile SEO | `mobile <url>` | No |
| Performance | `performance <url>` | No |
| URL & Links | `url-analysis <url>` | No |
| Full Page SEO (all 9) | `full-seo <url>` | No |
| Site Crawl + Audit | `site-audit <url>` | No |
| Core Web Vitals | `cwv <url>` | Optional |
| Search Analytics | `analytics` | Yes |
| URL Inspection | `inspect <url>` | Yes |
| Indexing Requests | `index-request <url>` | Yes |
| Full SEO Audit | `seo-audit` | Yes |

## UI Automation Scripts

Two surfaces of Search Console have no API at all: the Page Indexing
drilldowns' example-URL lists, and the "Validate Fix" button. The `scripts/`
directory ships two Playwright scripts that automate them through the real UI:

- `scripts/gsc_ui_export.mjs` - exports each indexing issue's URL list
  (Table.csv) into `./gsc-exports` (or `--out=<dir>` / `GSC_EXPORTS_DIR`).
- `scripts/gsc_validate_fix.mjs` - clicks "Validate Fix" for the given issue
  classes (`--issues="Not found (404),Server error (5xx)"` is the default).
  Supports `--dry-run` and `--cdp` (attach to a running Chrome).

Prerequisite: Playwright installed in the project you run them from:

```bash
npm i -D playwright && npx playwright install chromium
```

Setup flow (Google blocks scripted logins, so login is a one-time manual step):

```bash
export GSC_SITE_URL="sc-domain:example.com"

# 1. One-time headed login; saves cookies to ~/.cache/gsc-ui-profile
#    (override with GSC_UI_PROFILE_DIR). One setup serves both scripts.
node scripts/gsc_ui_export.mjs --setup

# 2. Recurring runs (headless-capable) reuse the saved session:
node scripts/gsc_ui_export.mjs
node scripts/gsc_validate_fix.mjs --dry-run
```

Exit codes: 0 = ran, 2 = Google session expired (re-run `--setup`), 1 = other
failure. Treat non-zero as "skip this step and flag a human" - never fail a
surrounding workflow on it.

## Autofix Loop Scripts

Closed-loop Search Console remediation (detect -> allowlisted fix -> verify ->
notify -> validate -> ledger). See `docs/autofix.md` for the full pipeline and
`skills/creo-seo/references/gsc-autofix-loop.md` (Creo core) for the fix
policy:

- `scripts/gsc_autofix_detect.py` - budgeted URL-inspection sweep with
  multi-issue classification, sitemap health floor, and click-anomaly check.
- `scripts/gsc_request_reindex.py` - sitemap resubmit + Indexing API
  notifications (best-effort, never fails the run).
- `scripts/gsc_autofix_verify.sh` - live verification: 3-part redirect
  assertions, canary suite, robots/sitemap invariants; exit code = failures.

Templates: `templates/seo-autofix-ledger.example.json`,
`templates/seo-canaries.example.txt`.

## Monitoring Scripts

Weekly rank history, semantic core, trends, LLM citability, and freshness
guards. See `docs/monitoring.md`:

- `scripts/seo_site_config.py` - shared per-project taxonomy module
  (template: `templates/seo-site-config.example.json`).
- `scripts/pull_weekly_snapshot.py` - weekly GSC (+ optional Bing) rank
  snapshot, idempotent per ISO week.
- `scripts/pull_semantic_core.py` + `scripts/filter_semantic_core.py` -
  focused query core with noise filtering and P0-P3 priorities.
- `scripts/pull_trends_12w.py` - rolling 12-week half-over-half trend labels.
- `scripts/track_llm_visibility.py` - AI answer-engine citation tracking
  (DataForSEO) with pre-spend cost estimate.
- `scripts/check_year_staleness.mjs` - year-staleness CI guard.

Workflow template: `templates/seo-weekly.yml` (copy into
`.github/workflows/`, adjust the `# ADJUST:` markers).

## References

- `references/gsc-api-reference.md` - complete Search Console API guide:
  service-account setup, endpoint reference, Python examples, quotas,
  rate limiting, and troubleshooting.
- `docs/autofix.md` - closed-loop autofix pipeline and script usage.
- `docs/monitoring.md` - monitoring scripts, weekly workflow, site config.

## Uninstall

```bash
# macOS / Linux
./uninstall.sh

# Windows (PowerShell)
.\uninstall.ps1
```

This removes `~/.claude/skills/creo-gsc/` and `~/.claude/agents/creo-gsc.md`.
