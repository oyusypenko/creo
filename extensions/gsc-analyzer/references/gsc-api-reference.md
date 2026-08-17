# Google Search Console API - Documentation

Complete guide for using Google Search Console API to check indexation status, crawl errors, and search analytics.

## Table of Contents

1. [Overview](#overview)
2. [Setup & Authentication](#setup--authentication)
3. [API Endpoints](#api-endpoints)
4. [Python Examples](#python-examples)
5. [Use Cases](#use-cases)
6. [Quotas & Limits](#quotas--limits)
7. [Troubleshooting](#troubleshooting)

---

## Overview

Google Search Console API provides programmatic access to:

| Feature | Description |
|---------|-------------|
| **Search Analytics** | Query clicks, impressions, CTR, position data |
| **URL Inspection** | Check indexation status, crawl errors, canonical URLs |
| **Sitemaps** | Submit, list, delete sitemaps |
| **Sites** | Manage Search Console properties |

### API Versions

- **webmasters v3** - Search Analytics, Sites, Sitemaps
- **searchconsole v1** - URL Inspection API

---

## Setup & Authentication

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Note your Project ID

### Step 2: Enable APIs

1. Go to **APIs & Services > Library**
2. Search and enable:
   - `Google Search Console API`
   - `Indexing API` (optional, for faster indexing)

### Step 3: Create Service Account

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > Service Account**
3. Fill in details:
   - Name: `search-console-api`
   - Description: `Service account for Search Console API`
4. Click **Create and Continue**
5. Skip role assignment (not needed for GSC)
6. Click **Done**

### Step 4: Generate Key File

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key > Create new key**
4. Select **JSON** format
5. Download and save as `service-account-key.json`

> **Security:** Never commit this file to git. Add to `.gitignore`

### Step 5: Add Service Account to Search Console

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select your property
3. Go to **Settings > Users and permissions**
4. Click **Add user**
5. Enter service account email (e.g., `search-console-api@your-project-id.iam.gserviceaccount.com`)
6. Set permission: **Full** (for write access) or **Restricted** (read-only)
7. Click **Add**

### OAuth Scopes

| Scope | Permission |
|-------|------------|
| `https://www.googleapis.com/auth/webmasters` | Read/Write |
| `https://www.googleapis.com/auth/webmasters.readonly` | Read-only |

---

## API Endpoints

### Search Analytics

```
POST /sites/{siteUrl}/searchAnalytics/query
```

Query search traffic data with filters.

**Request Body:**

```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "dimensions": ["query", "page", "country", "device", "date"],
  "type": "web",
  "rowLimit": 25000,
  "startRow": 0,
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "page",
      "operator": "contains",
      "expression": "/blog/"
    }]
  }]
}
```

**Available Dimensions:**

| Dimension | Description |
|-----------|-------------|
| `query` | Search query |
| `page` | URL of the page |
| `country` | Country code (ISO 3166-1 alpha-3) |
| `device` | DESKTOP, MOBILE, TABLET |
| `date` | Date (YYYY-MM-DD) |
| `searchAppearance` | Special search result type |

**Filter Operators:**

- `contains`, `equals`, `notContains`, `notEquals`
- `includingRegex`, `excludingRegex`

**Response Metrics:**

| Metric | Description |
|--------|-------------|
| `clicks` | Number of clicks |
| `impressions` | Number of impressions |
| `ctr` | Click-through rate (0-1) |
| `position` | Average position in search results |

---

### URL Inspection

```
POST /urlInspection/index:inspect
```

Check indexation status of a URL.

**Request Body:**

```json
{
  "inspectionUrl": "https://example.com/page",
  "siteUrl": "sc-domain:example.com",
  "languageCode": "en-US"
}
```

**Response Structure:**

```json
{
  "inspectionResult": {
    "inspectionResultLink": "https://search.google.com/...",
    "indexStatusResult": {
      "verdict": "PASS",
      "coverageState": "Submitted and indexed",
      "robotsTxtState": "ALLOWED",
      "indexingState": "INDEXING_ALLOWED",
      "lastCrawlTime": "2024-01-15T10:30:00Z",
      "pageFetchState": "SUCCESSFUL",
      "googleCanonical": "https://example.com/page",
      "userCanonical": "https://example.com/page",
      "crawledAs": "MOBILE",
      "sitemap": ["https://example.com/sitemap.xml"],
      "referringUrls": ["https://example.com/"]
    },
    "mobileUsabilityResult": {
      "verdict": "PASS",
      "issues": []
    },
    "richResultsResult": {
      "verdict": "PASS",
      "detectedItems": []
    }
  }
}
```

**Verdict Values:**

| Value | Meaning |
|-------|---------|
| `PASS` | Indexed or indexable |
| `NEUTRAL` | Excluded (alternate canonical, discovered but not indexed) |
| `FAIL` | Error state |
| `PARTIAL` | Partial issues |

**pageFetchState Values:**

| Value | Description |
|-------|-------------|
| `SUCCESSFUL` | Page fetched successfully |
| `SOFT_404` | Soft 404 detected |
| `BLOCKED_ROBOTS_TXT` | Blocked by robots.txt |
| `NOT_FOUND` | 404 error |
| `ACCESS_DENIED` | 401 error |
| `SERVER_ERROR` | 5xx error |
| `REDIRECT_ERROR` | Redirect loop/chain issue |
| `BLOCKED_4XX` | Other 4xx error |

---

### Sitemaps

**List sitemaps:**
```
GET /sites/{siteUrl}/sitemaps
```

**Submit sitemap:**
```
PUT /sites/{siteUrl}/sitemaps/{feedpath}
```

**Delete sitemap:**
```
DELETE /sites/{siteUrl}/sitemaps/{feedpath}
```

**Get sitemap details:**
```
GET /sites/{siteUrl}/sitemaps/{feedpath}
```

---

### Sites

**List all sites:**
```
GET /sites
```

**Add site:**
```
PUT /sites/{siteUrl}
```

**Delete site:**
```
DELETE /sites/{siteUrl}
```

**Get site info:**
```
GET /sites/{siteUrl}
```

---

## Python Examples

### Installation

```bash
pip install google-api-python-client google-auth pandas
```

### Authentication

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
KEY_FILE = './service-account-key.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# For URL Inspection API use 'searchconsole' v1
# For Search Analytics use 'webmasters' v3

def get_webmasters_service():
    """Get webmasters service for Search Analytics, Sitemaps, Sites"""
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=SCOPES
    )
    return build('webmasters', 'v3', credentials=credentials)

def get_searchconsole_service():
    """Get searchconsole service for URL Inspection"""
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=SCOPES
    )
    return build('searchconsole', 'v1', credentials=credentials)
```

### List All Properties

```python
def list_sites():
    """List all Search Console properties"""
    service = get_webmasters_service()
    sites = service.sites().list().execute()

    for site in sites.get('siteEntry', []):
        print(f"Site: {site['siteUrl']}")
        print(f"  Permission: {site['permissionLevel']}")

    return sites

# Usage
list_sites()
```

### Search Analytics Query

```python
import pandas as pd
from datetime import datetime, timedelta

def query_search_analytics(
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: list = ['query', 'page'],
    row_limit: int = 25000
) -> pd.DataFrame:
    """
    Query search analytics data

    Args:
        site_url: Property URL (e.g., 'sc-domain:example.com' or 'https://example.com/')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dimensions: List of dimensions to group by
        row_limit: Max rows per request (max 25000)

    Returns:
        DataFrame with search analytics data
    """
    service = get_webmasters_service()
    all_rows = []
    start_row = 0

    while True:
        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': row_limit,
            'startRow': start_row
        }

        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=payload
        ).execute()

        rows = response.get('rows', [])
        if not rows:
            break

        all_rows.extend(rows)
        start_row += row_limit

        # Safety check
        if len(rows) < row_limit:
            break

    if not all_rows:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(all_rows)

    # Extract dimension values from 'keys' column
    if 'keys' in df.columns:
        for i, dim in enumerate(dimensions):
            df[dim] = df['keys'].apply(lambda x: x[i] if i < len(x) else None)
        df = df.drop('keys', axis=1)

    return df

# Usage
df = query_search_analytics(
    site_url='sc-domain:example.com',
    start_date='2024-01-01',
    end_date='2024-01-31',
    dimensions=['query', 'page', 'device']
)
print(df.head())
```

### URL Inspection

```python
def inspect_url(url: str, site_url: str) -> dict:
    """
    Inspect a URL's indexation status

    Args:
        url: Full URL to inspect
        site_url: Property URL (e.g., 'sc-domain:example.com')

    Returns:
        Inspection result dictionary
    """
    service = get_searchconsole_service()

    request = {
        'inspectionUrl': url,
        'siteUrl': site_url,
        'languageCode': 'en-US'
    }

    response = service.urlInspection().index().inspect(body=request).execute()
    return response.get('inspectionResult', {})

def parse_inspection_result(result: dict) -> dict:
    """Parse inspection result into readable format"""
    index_status = result.get('indexStatusResult', {})
    mobile = result.get('mobileUsabilityResult', {})
    rich = result.get('richResultsResult', {})

    return {
        'is_indexed': index_status.get('verdict') == 'PASS',
        'coverage_state': index_status.get('coverageState'),
        'verdict': index_status.get('verdict'),
        'robots_txt': index_status.get('robotsTxtState'),
        'indexing_state': index_status.get('indexingState'),
        'page_fetch': index_status.get('pageFetchState'),
        'last_crawl': index_status.get('lastCrawlTime'),
        'crawled_as': index_status.get('crawledAs'),
        'google_canonical': index_status.get('googleCanonical'),
        'user_canonical': index_status.get('userCanonical'),
        'sitemaps': index_status.get('sitemap', []),
        'mobile_friendly': mobile.get('verdict') == 'PASS',
        'mobile_issues': [i.get('issueType') for i in mobile.get('issues', [])],
        'rich_results': rich.get('verdict'),
        'inspection_link': result.get('inspectionResultLink')
    }

# Usage
result = inspect_url(
    url='https://example.com/page',
    site_url='sc-domain:example.com'
)
parsed = parse_inspection_result(result)
print(f"Indexed: {parsed['is_indexed']}")
print(f"Coverage: {parsed['coverage_state']}")
print(f"Last Crawl: {parsed['last_crawl']}")
```

### Batch URL Inspection

```python
import time

def batch_inspect_urls(urls: list, site_url: str, delay: float = 0.1) -> list:
    """
    Inspect multiple URLs with rate limiting

    Args:
        urls: List of URLs to inspect
        site_url: Property URL
        delay: Delay between requests (seconds)

    Returns:
        List of parsed inspection results
    """
    results = []

    for i, url in enumerate(urls):
        try:
            result = inspect_url(url, site_url)
            parsed = parse_inspection_result(result)
            parsed['url'] = url
            results.append(parsed)

            print(f"[{i+1}/{len(urls)}] {url}: {parsed['verdict']}")

        except Exception as e:
            results.append({
                'url': url,
                'error': str(e),
                'is_indexed': None
            })
            print(f"[{i+1}/{len(urls)}] {url}: ERROR - {e}")

        time.sleep(delay)

    return results

# Usage
urls_to_check = [
    'https://example.com/page1',
    'https://example.com/page2',
    'https://example.com/page3'
]

results = batch_inspect_urls(urls_to_check, 'sc-domain:example.com')
df = pd.DataFrame(results)
print(df[['url', 'is_indexed', 'coverage_state', 'last_crawl']])
```

### Check Non-Indexed Pages

```python
def find_non_indexed_pages(site_url: str, urls: list) -> pd.DataFrame:
    """Find pages that are not indexed"""
    results = batch_inspect_urls(urls, site_url)
    df = pd.DataFrame(results)

    non_indexed = df[df['is_indexed'] == False]

    # Group by coverage state
    summary = df.groupby('coverage_state').size().reset_index(name='count')
    print("\nIndexation Summary:")
    print(summary)

    return non_indexed

# Get URLs from sitemap or other source
# Then check indexation status
```

### Sitemaps Management

```python
def list_sitemaps(site_url: str) -> list:
    """List all sitemaps for a site"""
    service = get_webmasters_service()
    response = service.sitemaps().list(siteUrl=site_url).execute()
    return response.get('sitemap', [])

def submit_sitemap(site_url: str, sitemap_url: str):
    """Submit a sitemap"""
    service = get_webmasters_service()
    service.sitemaps().submit(
        siteUrl=site_url,
        feedpath=sitemap_url
    ).execute()
    print(f"Submitted: {sitemap_url}")

def delete_sitemap(site_url: str, sitemap_url: str):
    """Delete a sitemap"""
    service = get_webmasters_service()
    service.sitemaps().delete(
        siteUrl=site_url,
        feedpath=sitemap_url
    ).execute()
    print(f"Deleted: {sitemap_url}")

# Usage
sitemaps = list_sitemaps('sc-domain:example.com')
for sm in sitemaps:
    print(f"Sitemap: {sm['path']}")
    print(f"  Last submitted: {sm.get('lastSubmitted')}")
    print(f"  URLs: {sm.get('contents', [{}])[0].get('submitted', 'N/A')}")
```

---

## Use Cases

### 1. Daily Indexation Report

```python
def daily_indexation_report(site_url: str, urls: list):
    """Generate daily indexation status report"""
    from datetime import datetime

    results = batch_inspect_urls(urls, site_url)
    df = pd.DataFrame(results)

    report = {
        'date': datetime.now().isoformat(),
        'total_urls': len(urls),
        'indexed': len(df[df['is_indexed'] == True]),
        'not_indexed': len(df[df['is_indexed'] == False]),
        'errors': len(df[df['is_indexed'].isna()])
    }

    report['index_rate'] = f"{(report['indexed'] / report['total_urls']) * 100:.1f}%"

    # Non-indexed pages details
    non_indexed = df[df['is_indexed'] == False][['url', 'coverage_state', 'page_fetch']]

    print("\n=== Indexation Report ===")
    print(f"Date: {report['date']}")
    print(f"Total URLs: {report['total_urls']}")
    print(f"Indexed: {report['indexed']} ({report['index_rate']})")
    print(f"Not Indexed: {report['not_indexed']}")

    if len(non_indexed) > 0:
        print("\nNon-Indexed Pages:")
        print(non_indexed.to_string(index=False))

    return report, df
```

### 2. Top Queries Performance

```python
def top_queries_report(site_url: str, days: int = 28, limit: int = 50):
    """Get top performing queries"""
    from datetime import datetime, timedelta

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    df = query_search_analytics(
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=['query']
    )

    # Sort by clicks
    df = df.sort_values('clicks', ascending=False).head(limit)

    print(f"\nTop {limit} Queries ({start_date} to {end_date}):")
    print(df[['query', 'clicks', 'impressions', 'ctr', 'position']].to_string(index=False))

    return df
```

### 3. Page Performance by Device

```python
def device_performance_report(site_url: str, page_filter: str = None):
    """Compare performance across devices"""
    from datetime import datetime, timedelta

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')

    df = query_search_analytics(
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=['device']
    )

    print("\nPerformance by Device:")
    print(df[['device', 'clicks', 'impressions', 'ctr', 'position']].to_string(index=False))

    return df
```

---

## Quotas & Limits

| Resource | Limit |
|----------|-------|
| Search Analytics rows | 25,000 per request |
| URL Inspection | 2,000 requests/day per property |
| URL Inspection | 600 requests/minute |
| API calls | Varies by method |

### Rate Limiting Best Practices

```python
import time
from functools import wraps

def rate_limit(max_per_minute: int = 600):
    """Decorator for rate limiting API calls"""
    min_interval = 60.0 / max_per_minute

    def decorator(func):
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed

            if wait_time > 0:
                time.sleep(wait_time)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper
    return decorator

@rate_limit(max_per_minute=500)  # Leave some buffer
def inspect_url_with_rate_limit(url: str, site_url: str):
    return inspect_url(url, site_url)
```

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `HttpError 403` | Insufficient permissions | Add service account to GSC with proper permissions |
| `HttpError 404` | Property not found | Check siteUrl format (use `sc-domain:` for domain properties) |
| `googleapiclient.errors.HttpError: 429` | Rate limit exceeded | Implement rate limiting, wait and retry |
| `urlInspection() not found` | Wrong API version | Use `searchconsole` v1 for URL Inspection |

### Property URL Format

| Type | Format | Example |
|------|--------|---------|
| Domain property | `sc-domain:domain.com` | `sc-domain:example.com` |
| URL prefix (https) | `https://www.domain.com/` | `https://www.example.com/` |
| URL prefix (http) | `http://www.domain.com/` | `http://www.example.com/` |

> **Note:** URL prefix properties MUST include trailing slash!

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or for Google API specifically
import httplib2
httplib2.debuglevel = 1
```

---

## Official Resources

- [Search Console API Overview](https://developers.google.com/webmaster-tools/about)
- [API Reference](https://developers.google.com/webmaster-tools/v1/api_reference_index)
- [Python Quickstart](https://developers.google.com/webmaster-tools/v1/quickstart/quickstart-python)
- [Authorization Guide](https://developers.google.com/webmaster-tools/v1/how-tos/authorizing)
- [URL Inspection API Announcement](https://developers.google.com/search/blog/2022/01/url-inspection-api)

---

## Complete Script Example

Save as `gsc_checker.py`:

```python
#!/usr/bin/env python3
"""
Google Search Console API Checker

Usage:
    python gsc_checker.py --site sc-domain:example.com --action list-sites
    python gsc_checker.py --site sc-domain:example.com --action inspect --url https://example.com/page
    python gsc_checker.py --site sc-domain:example.com --action analytics --days 28
    python gsc_checker.py --site sc-domain:example.com --action sitemaps
"""

import argparse
import json
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

# Configuration
KEY_FILE = './service-account-key.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def get_service(api: str, version: str):
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=SCOPES
    )
    return build(api, version, credentials=credentials)


def list_sites():
    service = get_service('webmasters', 'v3')
    sites = service.sites().list().execute()

    print("\n=== Your Search Console Properties ===\n")
    for site in sites.get('siteEntry', []):
        print(f"  {site['siteUrl']}")
        print(f"    Permission: {site['permissionLevel']}")

    return sites


def inspect_url(site_url: str, url: str):
    service = get_service('searchconsole', 'v1')

    request = {
        'inspectionUrl': url,
        'siteUrl': site_url,
        'languageCode': 'en-US'
    }

    response = service.urlInspection().index().inspect(body=request).execute()
    result = response.get('inspectionResult', {})
    index_status = result.get('indexStatusResult', {})

    print(f"\n=== URL Inspection: {url} ===\n")
    print(f"  Verdict: {index_status.get('verdict')}")
    print(f"  Coverage: {index_status.get('coverageState')}")
    print(f"  Robots.txt: {index_status.get('robotsTxtState')}")
    print(f"  Indexing: {index_status.get('indexingState')}")
    print(f"  Page Fetch: {index_status.get('pageFetchState')}")
    print(f"  Crawled As: {index_status.get('crawledAs')}")
    print(f"  Last Crawl: {index_status.get('lastCrawlTime')}")
    print(f"  Google Canonical: {index_status.get('googleCanonical')}")
    print(f"  User Canonical: {index_status.get('userCanonical')}")
    print(f"  Link: {result.get('inspectionResultLink')}")

    return result


def get_analytics(site_url: str, days: int = 28):
    service = get_service('webmasters', 'v3')

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    payload = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query'],
        'rowLimit': 25
    }

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body=payload
    ).execute()

    print(f"\n=== Top Queries ({start_date} to {end_date}) ===\n")
    print(f"{'Query':<50} {'Clicks':>8} {'Impr':>8} {'CTR':>8} {'Pos':>6}")
    print("-" * 84)

    for row in response.get('rows', []):
        query = row['keys'][0][:47] + '...' if len(row['keys'][0]) > 50 else row['keys'][0]
        print(f"{query:<50} {row['clicks']:>8.0f} {row['impressions']:>8.0f} {row['ctr']*100:>7.1f}% {row['position']:>6.1f}")

    return response


def list_sitemaps(site_url: str):
    service = get_service('webmasters', 'v3')
    response = service.sitemaps().list(siteUrl=site_url).execute()

    print(f"\n=== Sitemaps for {site_url} ===\n")

    for sm in response.get('sitemap', []):
        print(f"  {sm['path']}")
        print(f"    Last submitted: {sm.get('lastSubmitted', 'N/A')}")
        print(f"    Last downloaded: {sm.get('lastDownloaded', 'N/A')}")
        print(f"    Warnings: {sm.get('warnings', 0)}")
        print(f"    Errors: {sm.get('errors', 0)}")

        for content in sm.get('contents', []):
            print(f"    Type: {content.get('type')} - Submitted: {content.get('submitted', 0)}, Indexed: {content.get('indexed', 0)}")
        print()

    return response


def main():
    parser = argparse.ArgumentParser(description='Google Search Console API Checker')
    parser.add_argument('--site', help='Site URL (e.g., sc-domain:example.com)')
    parser.add_argument('--action', required=True,
                       choices=['list-sites', 'inspect', 'analytics', 'sitemaps'],
                       help='Action to perform')
    parser.add_argument('--url', help='URL to inspect (for inspect action)')
    parser.add_argument('--days', type=int, default=28, help='Days for analytics (default: 28)')

    args = parser.parse_args()

    if args.action == 'list-sites':
        list_sites()
    elif args.action == 'inspect':
        if not args.site or not args.url:
            print("Error: --site and --url required for inspect action")
            return
        inspect_url(args.site, args.url)
    elif args.action == 'analytics':
        if not args.site:
            print("Error: --site required for analytics action")
            return
        get_analytics(args.site, args.days)
    elif args.action == 'sitemaps':
        if not args.site:
            print("Error: --site required for sitemaps action")
            return
        list_sitemaps(args.site)


if __name__ == '__main__':
    main()
```

### Usage Examples

```bash
# List all properties
python gsc_checker.py --action list-sites

# Inspect a URL
python gsc_checker.py --site sc-domain:example.com --action inspect --url https://example.com/page

# Get search analytics
python gsc_checker.py --site sc-domain:example.com --action analytics --days 28

# List sitemaps
python gsc_checker.py --site sc-domain:example.com --action sitemaps
```
