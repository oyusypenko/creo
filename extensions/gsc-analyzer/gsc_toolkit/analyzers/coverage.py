"""Coverage CSV export analyzer."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse

import pandas as pd

from ..core.utils import print_warning


class CoverageAnalyzer:
    """Analyzer for GSC Coverage CSV exports."""

    CATEGORY_LABELS = {
        # Indexing status buckets (from GSC Pages → Why pages aren't indexed)
        'not_found_404': 'Not found (404)',
        'soft_404': 'Soft 404',
        'server_error': 'Server error (5xx)',
        'blocked_robots': 'Blocked by robots.txt',
        'blocked_unauthorized': 'Blocked due to access forbidden (401/403)',
        'noindex': 'Excluded by noindex tag',
        'crawled_not_indexed': 'Crawled - currently not indexed',
        'discovered_not_indexed': 'Discovered - currently not indexed',
        'duplicate_no_canonical': 'Duplicate without user-selected canonical',
        'duplicate_google_canonical': 'Duplicate, Google chose different canonical',
        'redirect_error': 'Redirect error',
        # Redirect type buckets (pattern-based)
        'www_to_non_www': 'WWW → non-WWW redirect',
        'non_www_to_www': 'non-WWW → WWW redirect',
        'missing_trailing_slash': 'Missing trailing slash',
        'extra_trailing_slash': 'Extra trailing slash',
        'http_to_https': 'HTTP → HTTPS redirect',
        'path_redirect': 'Path redirect',
        'page_with_redirect': 'Page with redirect',
        'other': 'Other',
    }

    # Map lowercase issue_type strings from GSC Metadata.csv to bucket keys.
    ISSUE_TYPE_BUCKETS = {
        'not found (404)': 'not_found_404',
        'not found': 'not_found_404',
        '404': 'not_found_404',
        'soft 404': 'soft_404',
        'server error (5xx)': 'server_error',
        'server error': 'server_error',
        '5xx': 'server_error',
        'blocked by robots.txt': 'blocked_robots',
        'blocked due to access forbidden (403)': 'blocked_unauthorized',
        'blocked due to unauthorized request (401)': 'blocked_unauthorized',
        'excluded by \u2018noindex\u2019 tag': 'noindex',
        "excluded by 'noindex' tag": 'noindex',
        'excluded by noindex tag': 'noindex',
        'crawled - currently not indexed': 'crawled_not_indexed',
        'discovered - currently not indexed': 'discovered_not_indexed',
        'duplicate without user-selected canonical': 'duplicate_no_canonical',
        'duplicate, google chose different canonical than user': 'duplicate_google_canonical',
        'redirect error': 'redirect_error',
        'page with redirect': 'page_with_redirect',
    }

    def parse_coverage_csv(self, folder: Path) -> Dict[str, Any]:
        """Parse Coverage export CSV files."""
        result = {
            'folder': str(folder),
            'issue_type': None,
            'issue_bucket': None,
            'urls': [],
            'history': [],
            'categorized': {key: [] for key in self.CATEGORY_LABELS},
            'summary': {}
        }

        # Parse Metadata.csv — this carries the GSC-reported indexing issue
        # (e.g. "Not found (404)", "Soft 404"). We use it to bucket every URL
        # in Table.csv, because GSC's CSV export is per-issue: one folder =
        # one issue type applied to every listed URL.
        metadata_file = folder / 'Metadata.csv'
        if metadata_file.exists():
            try:
                metadata_df = pd.read_csv(metadata_file)
                for _, row in metadata_df.iterrows():
                    prop = row.get('Property', '')
                    value = row.get('Value', '')
                    if prop == 'Issue':
                        result['issue_type'] = value
                        result['issue_bucket'] = self._bucket_for_issue(value)
            except Exception as e:
                print_warning(f"Error parsing Metadata.csv: {e}")

        issue_bucket = result.get('issue_bucket')

        # Parse Table.csv (main URLs)
        table_file = folder / 'Table.csv'
        if table_file.exists():
            try:
                table_df = pd.read_csv(table_file)
                for _, row in table_df.iterrows():
                    url = row.get('URL', '')
                    last_crawled = row.get('Last crawled', '')
                    if url:
                        # Prefer the GSC-reported issue type; fall back to
                        # URL-pattern heuristics only when the export does
                        # not declare an issue (e.g. ad-hoc redirect audits).
                        if issue_bucket:
                            category = issue_bucket
                        else:
                            category = self._categorize_redirect(url)

                        url_info = {
                            'url': url,
                            'last_crawled': last_crawled,
                            'category': category,
                            'issue_type': result.get('issue_type'),
                        }
                        result['urls'].append(url_info)

                        if category in result['categorized']:
                            result['categorized'][category].append(url)
                        else:
                            result['categorized'].setdefault('other', []).append(url)

            except Exception as e:
                print_warning(f"Error parsing Table.csv: {e}")

        # Parse Chart.csv (historical data)
        chart_file = folder / 'Chart.csv'
        if chart_file.exists():
            try:
                chart_df = pd.read_csv(chart_file)
                for _, row in chart_df.iterrows():
                    date = row.get('Date', '')
                    affected = row.get('Affected pages', 0)
                    if date:
                        result['history'].append({
                            'date': date,
                            'affected_pages': int(affected) if pd.notna(affected) else 0
                        })
            except Exception as e:
                print_warning(f"Error parsing Chart.csv: {e}")

        # Generate summary
        cats = result['categorized']
        result['summary'] = {
            'total_urls': len(result['urls']),
            'not_found_404': len(cats.get('not_found_404', [])),
            'soft_404': len(cats.get('soft_404', [])),
            'server_error': len(cats.get('server_error', [])),
            'blocked': len(cats.get('blocked_robots', [])) + len(cats.get('blocked_unauthorized', [])),
            'noindex': len(cats.get('noindex', [])),
            'crawled_not_indexed': len(cats.get('crawled_not_indexed', [])),
            'discovered_not_indexed': len(cats.get('discovered_not_indexed', [])),
            'duplicate': len(cats.get('duplicate_no_canonical', [])) + len(cats.get('duplicate_google_canonical', [])),
            'www_redirects': len(cats.get('www_to_non_www', [])) + len(cats.get('non_www_to_www', [])),
            'trailing_slash_issues': len(cats.get('missing_trailing_slash', [])) + len(cats.get('extra_trailing_slash', [])),
            'http_redirects': len(cats.get('http_to_https', [])),
            'path_redirects': len(cats.get('path_redirect', [])),
            'other': len(cats.get('other', [])),
        }

        return result

    def _bucket_for_issue(self, issue_text: str) -> str:
        """Map GSC Metadata.csv 'Issue' string to a canonical bucket key."""
        if not issue_text:
            return None
        normalized = issue_text.strip().lower()
        if normalized in self.ISSUE_TYPE_BUCKETS:
            return self.ISSUE_TYPE_BUCKETS[normalized]
        for fragment, bucket in self.ISSUE_TYPE_BUCKETS.items():
            if fragment in normalized:
                return bucket
        return 'other'

    def _categorize_redirect(self, url: str) -> str:
        """Categorize a URL's redirect type."""
        parsed = urlparse(url)

        if parsed.netloc.startswith('www.'):
            return 'www_to_non_www'

        if parsed.scheme == 'http':
            return 'http_to_https'

        path = parsed.path
        if path and not path.endswith('/') and '.' not in path.split('/')[-1]:
            return 'missing_trailing_slash'

        if '//' in path[1:]:
            return 'path_redirect'

        return 'other'

    def analyze_exports(self, export_folders: List[Path]) -> Dict[str, Any]:
        """Analyze multiple Coverage export folders."""
        all_results = []
        total_issues = 0
        all_categorized = {key: [] for key in self.CATEGORY_LABELS}

        for folder in export_folders:
            result = self.parse_coverage_csv(folder)
            all_results.append(result)

            url_count = result['summary']['total_urls']
            total_issues += url_count

            for category, urls in result['categorized'].items():
                all_categorized.setdefault(category, []).extend(urls)

        return {
            'generated_at': datetime.now().isoformat(),
            'total_issues': total_issues,
            'exports': all_results,
            'categorized': {k: v for k, v in all_categorized.items() if v},
        }
