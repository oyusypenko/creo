"""Main Google Search Console API client."""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from tabulate import tabulate

from .core.config import (
    KEY_FILE,
    SITE_URL,
    DEFAULT_DAYS,
    OUTPUT_DIR,
    SCOPES_READONLY,
)
from .core.models import Priority, ManualAction, SEOAuditResult
from .core.utils import (
    Colors,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_info,
)
from .analyzers.pagespeed import PageSpeedAnalyzer
from .analyzers.indexing import IndexingAPI
from .analyzers.coverage import CoverageAnalyzer
from .analyzers.links import LinksAnalyzer


class GSCAnalyzer:
    """Google Search Console API wrapper - main entry point."""

    def __init__(self, key_file: str = KEY_FILE, site_url: str = SITE_URL):
        self.key_file = key_file
        self.site_url = site_url
        self._webmasters_service: Optional[Resource] = None
        self._searchconsole_service: Optional[Resource] = None

        # Initialize sub-analyzers
        self.pagespeed = PageSpeedAnalyzer()
        self.indexing = IndexingAPI(key_file)
        self.coverage_analyzer = CoverageAnalyzer()
        self.links_analyzer = LinksAnalyzer()

    def _get_credentials(self, scopes=SCOPES_READONLY):
        """Get service account credentials."""
        if not Path(self.key_file).exists():
            print_error(f"Key file not found: {self.key_file}")
            print_info("Please follow setup instructions in README.md")
            sys.exit(1)

        return service_account.Credentials.from_service_account_file(
            self.key_file, scopes=scopes
        )

    @property
    def webmasters(self) -> Resource:
        """Get webmasters service (v3) for Search Analytics, Sites, Sitemaps."""
        if not self._webmasters_service:
            credentials = self._get_credentials()
            self._webmasters_service = build('webmasters', 'v3', credentials=credentials)
        return self._webmasters_service

    @property
    def searchconsole(self) -> Resource:
        """Get searchconsole service (v1) for URL Inspection."""
        if not self._searchconsole_service:
            credentials = self._get_credentials()
            self._searchconsole_service = build('searchconsole', 'v1', credentials=credentials)
        return self._searchconsole_service

    def list_sites(self) -> List[Dict]:
        """List all Search Console properties."""
        print_header("Your Search Console Properties")

        try:
            response = self.webmasters.sites().list().execute()
            sites = response.get('siteEntry', [])

            if not sites:
                print_warning("No sites found. Make sure service account has access.")
                return []

            data = []
            for site in sites:
                data.append({
                    'Site URL': site['siteUrl'],
                    'Permission': site['permissionLevel']
                })

            print(tabulate(data, headers='keys', tablefmt='grid'))
            return sites

        except HttpError as e:
            print_error(f"API Error: {e}")
            return []

    def inspect_url(self, url: str, silent: bool = False) -> Dict:
        """Inspect a single URL's indexation status."""
        if not silent:
            print_header("URL Inspection")
            print_info(f"URL: {url}")
            print_info(f"Property: {self.site_url}")

        if not self.site_url:
            print_error("Site URL not configured. Set GSC_SITE_URL in .env")
            return {}

        try:
            request = {
                'inspectionUrl': url,
                'siteUrl': self.site_url,
                'languageCode': 'en-US'
            }

            response = self.searchconsole.urlInspection().index().inspect(body=request).execute()
            result = response.get('inspectionResult', {})

            if not silent:
                self._print_inspection_result(result)

            return result

        except HttpError as e:
            print_error(f"API Error: {e}")
            return {}

    def _print_inspection_result(self, result: Dict):
        """Pretty print URL inspection result."""
        index_status = result.get('indexStatusResult', {})
        mobile = result.get('mobileUsabilityResult', {})
        rich = result.get('richResultsResult', {})

        verdict = index_status.get('verdict', 'UNKNOWN')
        verdict_color = Colors.GREEN if verdict == 'PASS' else (
            Colors.WARNING if verdict == 'NEUTRAL' else Colors.FAIL
        )

        print(f"\n{Colors.BOLD}Index Status:{Colors.ENDC}")
        print(f"  Verdict:        {verdict_color}{verdict}{Colors.ENDC}")
        print(f"  Coverage:       {index_status.get('coverageState', 'N/A')}")
        print(f"  Robots.txt:     {index_status.get('robotsTxtState', 'N/A')}")
        print(f"  Indexing:       {index_status.get('indexingState', 'N/A')}")
        print(f"  Page Fetch:     {index_status.get('pageFetchState', 'N/A')}")
        print(f"  Crawled As:     {index_status.get('crawledAs', 'N/A')}")
        print(f"  Last Crawl:     {index_status.get('lastCrawlTime', 'N/A')}")

        print(f"\n{Colors.BOLD}Canonicals:{Colors.ENDC}")
        print(f"  Google:         {index_status.get('googleCanonical', 'N/A')}")
        print(f"  User-declared:  {index_status.get('userCanonical', 'N/A')}")

        sitemaps = index_status.get('sitemap', [])
        if sitemaps:
            print(f"\n{Colors.BOLD}Found in Sitemaps:{Colors.ENDC}")
            for sm in sitemaps:
                print(f"  - {sm}")

        referring = index_status.get('referringUrls', [])
        if referring:
            print(f"\n{Colors.BOLD}Referring URLs:{Colors.ENDC}")
            for ref in referring[:5]:
                print(f"  - {ref}")

        if mobile:
            mobile_verdict = mobile.get('verdict', 'N/A')
            mobile_color = Colors.GREEN if mobile_verdict == 'PASS' else Colors.WARNING
            print(f"\n{Colors.BOLD}Mobile Usability:{Colors.ENDC} {mobile_color}{mobile_verdict}{Colors.ENDC}")

        if rich:
            rich_verdict = rich.get('verdict', 'N/A')
            print(f"\n{Colors.BOLD}Rich Results:{Colors.ENDC} {rich_verdict}")

        link = result.get('inspectionResultLink', '')
        if link:
            print(f"\n{Colors.CYAN}Full report: {link}{Colors.ENDC}")

    def batch_inspect(self, urls: List[str], delay: float = 0.2) -> pd.DataFrame:
        """Inspect multiple URLs and return DataFrame."""
        print_header(f"Batch URL Inspection ({len(urls)} URLs)")

        if not self.site_url:
            print_error("Site URL not configured. Set GSC_SITE_URL in .env")
            return pd.DataFrame()

        results = []
        for i, url in enumerate(urls):
            try:
                print(f"[{i+1}/{len(urls)}] Inspecting: {url[:60]}...")

                request = {
                    'inspectionUrl': url,
                    'siteUrl': self.site_url,
                    'languageCode': 'en-US'
                }

                response = self.searchconsole.urlInspection().index().inspect(body=request).execute()
                result = response.get('inspectionResult', {})
                index_status = result.get('indexStatusResult', {})

                verdict = index_status.get('verdict', 'UNKNOWN')

                results.append({
                    'url': url,
                    'verdict': verdict,
                    'coverage_state': index_status.get('coverageState', ''),
                    'robots_txt': index_status.get('robotsTxtState', ''),
                    'indexing_state': index_status.get('indexingState', ''),
                    'page_fetch': index_status.get('pageFetchState', ''),
                    'crawled_as': index_status.get('crawledAs', ''),
                    'last_crawl': index_status.get('lastCrawlTime', ''),
                    'google_canonical': index_status.get('googleCanonical', ''),
                    'user_canonical': index_status.get('userCanonical', ''),
                })

                color = Colors.GREEN if verdict == 'PASS' else (Colors.WARNING if verdict == 'NEUTRAL' else Colors.FAIL)
                print(f"  {color}{'✓' if verdict == 'PASS' else '✗'} {verdict} - {index_status.get('coverageState', 'N/A')}{Colors.ENDC}")

                time.sleep(delay)

            except HttpError as e:
                print_error(f"  Error: {e}")
                results.append({
                    'url': url,
                    'verdict': 'ERROR',
                    'coverage_state': str(e),
                })

        df = pd.DataFrame(results)

        # Summary
        print_header("Inspection Summary")
        summary = df['verdict'].value_counts()
        for verdict, count in summary.items():
            color = Colors.GREEN if verdict == 'PASS' else (
                Colors.WARNING if verdict == 'NEUTRAL' else Colors.FAIL
            )
            print(f"  {color}{verdict}: {count}{Colors.ENDC}")

        # Save to CSV
        output_file = OUTPUT_DIR / f"inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        print_success(f"Results saved to: {output_file}")

        return df

    def get_analytics(
        self,
        days: int = DEFAULT_DAYS,
        dimensions: List[str] = None,
        row_limit: int = 1000,
        silent: bool = False
    ) -> pd.DataFrame:
        """Get search analytics data."""
        if dimensions is None:
            dimensions = ['query']

        if not silent:
            print_header(f"Search Analytics (Last {days} days)")
            print_info(f"Dimensions: {', '.join(dimensions)}")

        if not self.site_url:
            print_error("Site URL not configured. Set GSC_SITE_URL in .env")
            return pd.DataFrame()

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            all_rows = []
            start_row = 0

            while True:
                payload = {
                    'startDate': start_date,
                    'endDate': end_date,
                    'dimensions': dimensions,
                    'rowLimit': min(row_limit, 25000),
                    'startRow': start_row
                }

                response = self.webmasters.searchanalytics().query(
                    siteUrl=self.site_url,
                    body=payload
                ).execute()

                rows = response.get('rows', [])
                if not rows:
                    break

                all_rows.extend(rows)
                if not silent:
                    print_info(f"Fetched {len(all_rows)} rows...")

                if len(rows) < 25000 or len(all_rows) >= row_limit:
                    break

                start_row += 25000

            if not all_rows:
                if not silent:
                    print_warning("No data found for the specified period")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(all_rows)

            # Extract dimension values
            for i, dim in enumerate(dimensions):
                df[dim] = df['keys'].apply(lambda x: x[i] if i < len(x) else None)

            df = df.drop('keys', axis=1)

            # Format numbers
            df['ctr'] = df['ctr'] * 100  # Convert to percentage

            # Sort by clicks
            df = df.sort_values('clicks', ascending=False)

            if not silent:
                self._print_analytics_summary(df, dimensions)

            return df

        except HttpError as e:
            print_error(f"API Error: {e}")
            return pd.DataFrame()

    def _print_analytics_summary(self, df: pd.DataFrame, dimensions: List[str]):
        """Print analytics summary."""
        display_df = df.head(20).copy()
        display_df['ctr'] = display_df['ctr'].apply(lambda x: f"{x:.1f}%")
        display_df['position'] = display_df['position'].apply(lambda x: f"{x:.1f}")

        print(f"\n{Colors.BOLD}Top 20 Results:{Colors.ENDC}\n")
        print(tabulate(display_df, headers='keys', tablefmt='grid', showindex=False))

        # Summary stats
        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Total Clicks:      {df['clicks'].sum():,.0f}")
        print(f"  Total Impressions: {df['impressions'].sum():,.0f}")
        print(f"  Average CTR:       {df['ctr'].mean():.2f}%")
        print(f"  Average Position:  {df['position'].mean():.1f}")

        # Save full results
        output_file = OUTPUT_DIR / f"analytics_{dimensions[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        print_success(f"Full results saved to: {output_file}")

    def list_sitemaps(self, silent: bool = False) -> List[Dict]:
        """List all sitemaps for the site."""
        if not silent:
            print_header("Sitemaps")

        if not self.site_url:
            print_error("Site URL not configured. Set GSC_SITE_URL in .env")
            return []

        try:
            response = self.webmasters.sitemaps().list(siteUrl=self.site_url).execute()
            sitemaps = response.get('sitemap', [])

            if not sitemaps:
                if not silent:
                    print_warning("No sitemaps found")
                return []

            if not silent:
                for sm in sitemaps:
                    path = sm.get('path', 'Unknown')
                    print(f"\n{Colors.BOLD}{path}{Colors.ENDC}")
                    print(f"  Last Submitted:  {sm.get('lastSubmitted', 'N/A')}")
                    print(f"  Last Downloaded: {sm.get('lastDownloaded', 'N/A')}")
                    print(f"  Warnings:        {sm.get('warnings', 0)}")
                    print(f"  Errors:          {sm.get('errors', 0)}")

                    for content in sm.get('contents', []):
                        content_type = content.get('type', 'Unknown')
                        submitted = content.get('submitted', 0)
                        indexed = content.get('indexed', 0)
                        print(f"  {content_type}: {indexed}/{submitted} indexed")

            return sitemaps

        except HttpError as e:
            print_error(f"API Error: {e}")
            return []

    def find_gsc_exports(self, search_path: str = None, pattern: str = "*") -> List[Path]:
        """Find GSC export folders matching pattern."""
        if search_path is None:
            search_paths = [
                Path.cwd(),
                Path.cwd().parent,
                Path.home() / 'Downloads',
                Path.home() / 'Desktop',
            ]
        else:
            search_paths = [Path(search_path)]

        export_folders = []
        patterns = [f'*{pattern}*']

        for base_path in search_paths:
            if not base_path.exists():
                continue
            for p in patterns:
                for folder in base_path.glob(p):
                    if folder.is_dir() and (folder / 'Table.csv').exists():
                        export_folders.append(folder)

        return list(set(export_folders))

    def analyze_coverage(self, search_path: str = None, silent: bool = False) -> Dict[str, Any]:
        """Find and analyze Coverage exports."""
        if not silent:
            print_header("Coverage Report Analysis")

        export_folders = self.find_gsc_exports(search_path, "Coverage")

        if not export_folders:
            if not silent:
                print_warning("No Coverage export folders found.")
                print_info("Export from GSC: Pages → Not Indexed → Export")
            return {'exports': [], 'total_issues': 0}

        if not silent:
            print_success(f"Found {len(export_folders)} Coverage export(s)")

        report = self.coverage_analyzer.analyze_exports(export_folders)

        if not silent:
            self._print_coverage_summary(report, export_folders)

        return report

    def _print_coverage_summary(self, report: Dict, export_folders: List[Path]):
        """Print coverage analysis summary."""
        for folder, result in zip(export_folders, report['exports']):
            print(f"\n{Colors.BOLD}Analyzing: {folder.name}{Colors.ENDC}")
            print(f"  Issue Type: {Colors.WARNING}{result.get('issue_type', 'Unknown')}{Colors.ENDC}")
            print(f"  Total URLs: {Colors.FAIL}{result['summary']['total_urls']}{Colors.ENDC}")

        total_issues = report['total_issues']
        print_header("Coverage Issues Summary")
        print(f"\n{Colors.BOLD}Total Issues: {Colors.FAIL}{total_issues}{Colors.ENDC}\n")

        summary_data = []
        for category, urls in report.get('categorized', {}).items():
            if urls:
                count = len(urls)
                label = CoverageAnalyzer.CATEGORY_LABELS.get(category, category)
                summary_data.append({
                    'Issue Type': label,
                    'Count': count,
                    'Percentage': f"{count/total_issues*100:.1f}%" if total_issues > 0 else "0%"
                })

        if summary_data:
            print(tabulate(summary_data, headers='keys', tablefmt='grid'))

        output_file = OUTPUT_DIR / f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print_success(f"\nReport saved to: {output_file}")

    def analyze_links(self, search_path: str = None, silent: bool = False) -> Dict[str, Any]:
        """Parse Links export from GSC."""
        if not silent:
            print_header("Links Report Analysis")

        export_folders = self.find_gsc_exports(search_path, "Links")

        if not export_folders:
            if not silent:
                print_warning("No Links export folders found.")
                print_info("Export from GSC: Links → Export")
            return {'external_links': [], 'internal_links': []}

        if not silent:
            for folder in export_folders:
                print(f"\n{Colors.BOLD}Analyzing: {folder.name}{Colors.ENDC}")

        result = self.links_analyzer.analyze_links(export_folders)

        if not silent:
            output_file = OUTPUT_DIR / f"links_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print_success(f"\nReport saved to: {output_file}")

        return result

    def analyze_cwv(self, url: str, strategy: str = "mobile") -> Dict:
        """Analyze Core Web Vitals for a single URL."""
        print_header(f"Core Web Vitals Analysis ({strategy})")
        print_info(f"URL: {url}")

        result = self.pagespeed.analyze_url(url, strategy)

        if "error" in result:
            print_error(f"Error: {result['error']}")
            return result

        self._print_cwv_result(result)

        # Save result
        output_file = OUTPUT_DIR / f"cwv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print_success(f"\nReport saved to: {output_file}")

        return result

    def _print_cwv_result(self, result: Dict):
        """Print Core Web Vitals result."""
        perf = result.get('performance_score', 0)
        perf_color = Colors.GREEN if perf >= 90 else (Colors.WARNING if perf >= 50 else Colors.FAIL)

        print(f"\n{Colors.BOLD}Scores:{Colors.ENDC}")
        print(f"  Performance:    {perf_color}{perf}/100{Colors.ENDC}")
        print(f"  Accessibility:  {result.get('accessibility_score', 0)}/100")
        print(f"  Best Practices: {result.get('best_practices_score', 0)}/100")
        print(f"  SEO:            {result.get('seo_score', 0)}/100")

        print(f"\n{Colors.BOLD}Core Web Vitals:{Colors.ENDC}")

        lcp = result.get('lcp_ms', 0) / 1000
        lcp_color = Colors.GREEN if lcp <= 2.5 else (Colors.WARNING if lcp <= 4 else Colors.FAIL)
        print(f"  LCP:  {lcp_color}{lcp:.2f}s{Colors.ENDC} (target: ≤2.5s)")

        fid = result.get('fid_ms', 0)
        fid_color = Colors.GREEN if fid <= 100 else (Colors.WARNING if fid <= 300 else Colors.FAIL)
        print(f"  FID:  {fid_color}{fid:.0f}ms{Colors.ENDC} (target: ≤100ms)")

        cls_val = result.get('cls', 0)
        cls_color = Colors.GREEN if cls_val <= 0.1 else (Colors.WARNING if cls_val <= 0.25 else Colors.FAIL)
        print(f"  CLS:  {cls_color}{cls_val:.3f}{Colors.ENDC} (target: ≤0.1)")

        ttfb = result.get('ttfb_ms', 0)
        print(f"  TTFB: {ttfb:.0f}ms")

        # Opportunities
        opportunities = result.get('opportunities', [])
        if opportunities:
            print(f"\n{Colors.BOLD}Top Optimization Opportunities:{Colors.ENDC}")
            for opp in opportunities[:5]:
                print(f"  • {opp['title']} (save {opp['savings_ms']:.0f}ms)")

    def analyze_cwv_batch(self, urls: List[str], strategy: str = "mobile") -> List[Dict]:
        """Analyze Core Web Vitals for multiple URLs."""
        print_header(f"Batch Core Web Vitals Analysis ({len(urls)} URLs)")

        results = self.pagespeed.analyze_batch(urls, strategy)

        # Summary
        print_header("CWV Summary")

        scores = [r.get('performance_score', 0) for r in results if 'performance_score' in r]
        if scores:
            avg_perf = sum(scores) / len(scores)
            good = sum(1 for s in scores if s >= 90)
            needs_improvement = sum(1 for s in scores if 50 <= s < 90)
            poor = sum(1 for s in scores if s < 50)

            print(f"\n{Colors.BOLD}Performance Distribution:{Colors.ENDC}")
            print(f"  {Colors.GREEN}Good (90+): {good}{Colors.ENDC}")
            print(f"  {Colors.WARNING}Needs Improvement (50-89): {needs_improvement}{Colors.ENDC}")
            print(f"  {Colors.FAIL}Poor (<50): {poor}{Colors.ENDC}")
            print(f"\n  Average Score: {avg_perf:.0f}/100")

        # Save results
        output_file = OUTPUT_DIR / f"cwv_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print_success(f"\nResults saved to: {output_file}")

        return results

    def request_indexing(self, url: str) -> Dict:
        """Request indexing for a URL."""
        print_header("Request Indexing")
        print_info(f"URL: {url}")

        result = self.indexing.request_indexing(url)

        if "error" in result:
            print_error(f"Error: {result['error']}")
        else:
            print_success("Indexing requested successfully!")
            metadata = result.get('urlNotificationMetadata', {})
            print(f"  URL: {metadata.get('url', url)}")
            latest = metadata.get('latestUpdate', {})
            print(f"  Notify Time: {latest.get('notifyTime', 'N/A')}")

        return result

    def request_indexing_from_sitemap(self, sitemap_url: str, limit: int = 200) -> List[Dict]:
        """Request indexing for URLs from a sitemap."""
        print_header("Batch Indexing from Sitemap")
        print_info(f"Sitemap: {sitemap_url}")

        urls = self.indexing.get_urls_from_sitemap(sitemap_url)

        if not urls:
            print_error("No URLs found in sitemap")
            return []

        print_info(f"Found {len(urls)} URLs in sitemap")

        if len(urls) > limit:
            print_warning(f"Limiting to {limit} URLs (daily quota)")
            urls = urls[:limit]

        results = self.indexing.request_batch_indexing(urls)

        # Summary
        success = sum(1 for r in results if 'error' not in r)
        failed = sum(1 for r in results if 'error' in r)

        print_header("Indexing Summary")
        print(f"  {Colors.GREEN}Successful: {success}{Colors.ENDC}")
        print(f"  {Colors.FAIL}Failed: {failed}{Colors.ENDC}")

        return results

    def generate_full_report(self, days: int = DEFAULT_DAYS) -> Dict:
        """Generate a comprehensive SEO report."""
        print_header("Full SEO Report")
        print_info(f"Property: {self.site_url}")
        print_info(f"Period: Last {days} days")
        print_info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        report = {
            'generated_at': datetime.now().isoformat(),
            'site_url': self.site_url,
            'period_days': days,
        }

        # 1. Sitemaps
        print("\n" + "="*40)
        print("1. SITEMAPS ANALYSIS")
        print("="*40)
        sitemaps = self.list_sitemaps()
        report['sitemaps'] = sitemaps

        # 2. Top Queries
        print("\n" + "="*40)
        print("2. TOP QUERIES")
        print("="*40)
        queries_df = self.get_analytics(days=days, dimensions=['query'], row_limit=100)
        if not queries_df.empty:
            report['top_queries'] = queries_df.head(20).to_dict('records')

        # 3. Top Pages
        print("\n" + "="*40)
        print("3. TOP PAGES")
        print("="*40)
        pages_df = self.get_analytics(days=days, dimensions=['page'], row_limit=100)
        if not pages_df.empty:
            report['top_pages'] = pages_df.head(20).to_dict('records')

        # 4. Device Distribution
        print("\n" + "="*40)
        print("4. DEVICE DISTRIBUTION")
        print("="*40)
        devices_df = self.get_analytics(days=days, dimensions=['device'], row_limit=10)
        if not devices_df.empty:
            report['devices'] = devices_df.to_dict('records')

        # 5. Country Distribution
        print("\n" + "="*40)
        print("5. TOP COUNTRIES")
        print("="*40)
        countries_df = self.get_analytics(days=days, dimensions=['country'], row_limit=20)
        if not countries_df.empty:
            report['countries'] = countries_df.to_dict('records')

        # 6. Coverage Issues
        print("\n" + "="*40)
        print("6. COVERAGE ISSUES")
        print("="*40)
        coverage_report = self.analyze_coverage()
        if coverage_report.get('total_issues', 0) > 0:
            report['coverage_issues'] = coverage_report

        # Save report
        output_file = OUTPUT_DIR / f"full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print_success(f"\nFull report saved to: {output_file}")

        return report
