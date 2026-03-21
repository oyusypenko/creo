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
        'www_to_non_www': 'WWW → non-WWW redirect',
        'non_www_to_www': 'non-WWW → WWW redirect',
        'missing_trailing_slash': 'Missing trailing slash',
        'extra_trailing_slash': 'Extra trailing slash',
        'http_to_https': 'HTTP → HTTPS redirect',
        'path_redirect': 'Path redirect',
        'other': 'Other redirects',
    }

    def parse_coverage_csv(self, folder: Path) -> Dict[str, Any]:
        """Parse Coverage export CSV files."""
        result = {
            'folder': str(folder),
            'issue_type': None,
            'urls': [],
            'history': [],
            'categorized': {
                'www_to_non_www': [],
                'non_www_to_www': [],
                'missing_trailing_slash': [],
                'extra_trailing_slash': [],
                'http_to_https': [],
                'path_redirect': [],
                'other': [],
            },
            'summary': {}
        }

        # Parse Metadata.csv
        metadata_file = folder / 'Metadata.csv'
        if metadata_file.exists():
            try:
                metadata_df = pd.read_csv(metadata_file)
                for _, row in metadata_df.iterrows():
                    prop = row.get('Property', '')
                    value = row.get('Value', '')
                    if prop == 'Issue':
                        result['issue_type'] = value
            except Exception as e:
                print_warning(f"Error parsing Metadata.csv: {e}")

        # Parse Table.csv (main URLs)
        table_file = folder / 'Table.csv'
        if table_file.exists():
            try:
                table_df = pd.read_csv(table_file)
                for _, row in table_df.iterrows():
                    url = row.get('URL', '')
                    last_crawled = row.get('Last crawled', '')
                    if url:
                        url_info = {
                            'url': url,
                            'last_crawled': last_crawled,
                            'redirect_type': self._categorize_redirect(url)
                        }
                        result['urls'].append(url_info)

                        category = url_info['redirect_type']
                        if category in result['categorized']:
                            result['categorized'][category].append(url)
                        else:
                            result['categorized']['other'].append(url)

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
        result['summary'] = {
            'total_urls': len(result['urls']),
            'www_redirects': len(result['categorized']['www_to_non_www']) + len(result['categorized']['non_www_to_www']),
            'trailing_slash_issues': len(result['categorized']['missing_trailing_slash']) + len(result['categorized']['extra_trailing_slash']),
            'http_redirects': len(result['categorized']['http_to_https']),
            'path_redirects': len(result['categorized']['path_redirect']),
            'other': len(result['categorized']['other']),
        }

        return result

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
        all_categorized = {
            'www_to_non_www': [],
            'non_www_to_www': [],
            'missing_trailing_slash': [],
            'extra_trailing_slash': [],
            'http_to_https': [],
            'path_redirect': [],
            'other': [],
        }

        for folder in export_folders:
            result = self.parse_coverage_csv(folder)
            all_results.append(result)

            url_count = result['summary']['total_urls']
            total_issues += url_count

            for category, urls in result['categorized'].items():
                all_categorized[category].extend(urls)

        return {
            'generated_at': datetime.now().isoformat(),
            'total_issues': total_issues,
            'exports': all_results,
            'categorized': {k: v for k, v in all_categorized.items() if v},
        }
