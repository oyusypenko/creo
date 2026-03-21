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

## Uninstall

```bash
# macOS / Linux
./uninstall.sh

# Windows (PowerShell)
.\uninstall.ps1
```

This removes `~/.claude/skills/creo-gsc/` and `~/.claude/agents/creo-gsc.md`.
