"""Complete SEO Audit implementation."""

import time
import json
from datetime import datetime
from typing import List, Optional

from ..core.config import DEFAULT_DAYS, OUTPUT_DIR
from ..core.models import Priority, ManualAction, SEOAuditResult
from ..core.utils import (
    Colors,
    print_header,
    print_success,
    print_warning,
    print_info,
)
from ..gsc_client import GSCAnalyzer


class SEOAuditor:
    """Complete SEO Audit runner."""

    def __init__(self, analyzer: GSCAnalyzer):
        self.analyzer = analyzer

    def run_audit(self, days: int = DEFAULT_DAYS, key_urls: List[str] = None) -> SEOAuditResult:
        """
        Run a complete SEO audit with:
        1. Data collection from all available sources
        2. Issue identification
        3. Manual action checklist generation
        """
        print_header("🔍 COMPLETE SEO AUDIT")
        print_info(f"Property: {self.analyzer.site_url}")
        print_info(f"Period: Last {days} days")
        print_info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        audit = SEOAuditResult(
            generated_at=datetime.now().isoformat(),
            site_url=self.analyzer.site_url
        )

        # PHASE 1: DATA COLLECTION
        self._collect_data(audit, days, key_urls)

        # PHASE 2: ISSUE IDENTIFICATION
        self._identify_issues(audit)

        # PHASE 3: REPORT GENERATION
        self._generate_report(audit)

        return audit

    def _collect_data(self, audit: SEOAuditResult, days: int, key_urls: Optional[List[str]]):
        """Phase 1: Collect data from all sources."""
        print_header("📊 PHASE 1: DATA COLLECTION")

        # 1.1 Sitemaps
        print(f"\n{Colors.CYAN}[1/7] Collecting sitemap data...{Colors.ENDC}")
        audit.sitemaps = self.analyzer.list_sitemaps(silent=True)
        for sm in audit.sitemaps:
            for content in sm.get('contents', []):
                audit.total_pages_in_sitemap += int(content.get('submitted', 0) or 0)
                audit.total_pages_indexed += int(content.get('indexed', 0) or 0)
        print_success(f"Sitemaps: {len(audit.sitemaps)} found, {audit.total_pages_in_sitemap} URLs submitted, {audit.total_pages_indexed} indexed")

        # 1.2 Search Analytics
        print(f"\n{Colors.CYAN}[2/7] Collecting search analytics...{Colors.ENDC}")
        queries_df = self.analyzer.get_analytics(days=days, dimensions=['query'], row_limit=500, silent=True)
        pages_df = self.analyzer.get_analytics(days=days, dimensions=['page'], row_limit=500, silent=True)

        audit.analytics = {
            'queries': queries_df.to_dict('records') if not queries_df.empty else [],
            'pages': pages_df.to_dict('records') if not pages_df.empty else [],
            'total_clicks': int(queries_df['clicks'].sum()) if not queries_df.empty else 0,
            'total_impressions': int(queries_df['impressions'].sum()) if not queries_df.empty else 0,
            'avg_ctr': float(queries_df['ctr'].mean()) if not queries_df.empty else 0,
            'avg_position': float(queries_df['position'].mean()) if not queries_df.empty else 0,
        }
        print_success(f"Analytics: {audit.analytics['total_clicks']} clicks, {audit.analytics['total_impressions']} impressions")

        # 1.3 Coverage Issues
        print(f"\n{Colors.CYAN}[3/7] Analyzing coverage exports...{Colors.ENDC}")
        audit.coverage_issues = self.analyzer.analyze_coverage(silent=True)
        coverage_total = audit.coverage_issues.get('total_issues', 0)
        print_success(f"Coverage issues: {coverage_total} found")

        # 1.4 Links Analysis
        print(f"\n{Colors.CYAN}[4/7] Analyzing links exports...{Colors.ENDC}")
        audit.links_analysis = self.analyzer.analyze_links(silent=True)
        links_total = len(audit.links_analysis.get('external_links', [])) + len(audit.links_analysis.get('internal_links', []))
        print_success(f"Links data: {links_total} records")

        # 1.5 URL Inspection
        print(f"\n{Colors.CYAN}[5/7] Inspecting key URLs...{Colors.ENDC}")
        if key_urls:
            urls_to_inspect = key_urls[:20]
        elif not pages_df.empty:
            urls_to_inspect = pages_df.head(10)['page'].tolist()
        else:
            urls_to_inspect = []

        if urls_to_inspect:
            for url in urls_to_inspect:
                result = self.analyzer.inspect_url(url, silent=True)
                if result:
                    audit.inspection_results.append({
                        'url': url,
                        'result': result
                    })
                time.sleep(0.3)
            print_success(f"Inspected: {len(audit.inspection_results)} URLs")
        else:
            print_warning("No URLs to inspect")

        # 1.6 Core Web Vitals
        print(f"\n{Colors.CYAN}[6/7] Analyzing Core Web Vitals...{Colors.ENDC}")
        cwv_urls = urls_to_inspect[:5] if urls_to_inspect else []
        if cwv_urls:
            for url in cwv_urls:
                result = self.analyzer.pagespeed.analyze_url(url, "mobile")
                if result and 'error' not in result:
                    audit.core_web_vitals.append(result)
                time.sleep(2)
            print_success(f"CWV analyzed: {len(audit.core_web_vitals)} URLs")
        else:
            print_warning("No URLs for CWV analysis")

        # 1.7 Other GSC exports
        print(f"\n{Colors.CYAN}[7/7] Checking for other GSC exports...{Colors.ENDC}")
        other_exports = self.analyzer.find_gsc_exports(pattern="")
        print_success(f"Found: {len(other_exports)} export folders")

    def _identify_issues(self, audit: SEOAuditResult):
        """Phase 2: Identify issues and create manual actions."""
        print_header("🔎 PHASE 2: ISSUE IDENTIFICATION")

        issues = []
        manual_actions = []

        # 2.1 Indexing Issues
        not_indexed = []
        for insp in audit.inspection_results:
            result = insp.get('result', {})
            index_status = result.get('indexStatusResult', {})
            verdict = index_status.get('verdict', '')
            if verdict != 'PASS':
                not_indexed.append(insp['url'])
                issues.append({
                    'type': 'indexing',
                    'severity': 'high',
                    'url': insp['url'],
                    'issue': f"Not indexed: {index_status.get('coverageState', 'Unknown')}"
                })

        if not_indexed:
            print_warning(f"Found {len(not_indexed)} pages not indexed")
            manual_actions.append(ManualAction(
                priority=Priority.HIGH,
                category="Indexing",
                title=f"{len(not_indexed)} pages not indexed",
                description="These pages are not in Google's index",
                steps=[
                    "Go to GSC → URL Inspection",
                    "Enter each URL and click 'Request Indexing'",
                    "Or use: python -m gsc_toolkit index-request <url>",
                ],
                affected_urls=not_indexed[:20],
                gsc_link="https://search.google.com/search-console/index"
            ))

        # 2.2 Coverage/Redirect Issues
        coverage_categorized = audit.coverage_issues.get('categorized', {})

        www_redirects = coverage_categorized.get('www_to_non_www', [])
        if www_redirects:
            print_warning(f"Found {len(www_redirects)} WWW redirect issues")
            manual_actions.append(ManualAction(
                priority=Priority.MEDIUM,
                category="Redirects",
                title=f"{len(www_redirects)} WWW → non-WWW redirects",
                description="Google is finding www URLs that redirect to non-www",
                steps=[
                    "Update internal links to use non-www URLs",
                    "Check canonical tags point to non-www",
                    "Verify sitemap.xml uses non-www URLs",
                    "Update any hardcoded www links in content",
                ],
                affected_urls=www_redirects[:10],
            ))

        trailing_slash = coverage_categorized.get('missing_trailing_slash', [])
        if trailing_slash:
            print_warning(f"Found {len(trailing_slash)} trailing slash issues")
            manual_actions.append(ManualAction(
                priority=Priority.MEDIUM,
                category="Redirects",
                title=f"{len(trailing_slash)} missing trailing slash redirects",
                description="URLs without trailing slash are redirecting",
                steps=[
                    "Verify trailingSlash: true in next.config.js",
                    "Update all internal links to include trailing slashes",
                    "Update sitemap.xml to include trailing slashes",
                    "Check components like not-found.tsx for hardcoded links",
                ],
                affected_urls=trailing_slash[:10],
            ))

        # 2.3 Core Web Vitals Issues
        poor_cwv = []
        for cwv in audit.core_web_vitals:
            score = cwv.get('performance_score', 100)
            if score < 50:
                poor_cwv.append(cwv['url'])
                issues.append({
                    'type': 'performance',
                    'severity': 'high',
                    'url': cwv['url'],
                    'issue': f"Poor performance score: {score}/100"
                })

        if poor_cwv:
            print_warning(f"Found {len(poor_cwv)} pages with poor CWV")
            manual_actions.append(ManualAction(
                priority=Priority.HIGH,
                category="Performance",
                title=f"{len(poor_cwv)} pages with poor Core Web Vitals",
                description="These pages have performance scores below 50",
                steps=[
                    "Run: python -m gsc_toolkit cwv <url> for detailed analysis",
                    "Optimize images (use WebP/AVIF, lazy loading)",
                    "Reduce JavaScript bundle size",
                    "Implement code splitting",
                    "Use CDN for static assets",
                ],
                affected_urls=poor_cwv,
            ))

        # 2.4 High impressions, low clicks (CTR issues)
        pages_data = audit.analytics.get('pages', [])
        if pages_data:
            import pandas as pd
            pages_df = pd.DataFrame(pages_data)
            if not pages_df.empty and 'impressions' in pages_df.columns and 'ctr' in pages_df.columns:
                low_ctr_pages = pages_df[(pages_df['impressions'] > 100) & (pages_df['ctr'] < 2)].head(10)
                if not low_ctr_pages.empty:
                    low_ctr_urls = low_ctr_pages['page'].tolist()
                    print_warning(f"Found {len(low_ctr_urls)} pages with low CTR")
                    manual_actions.append(ManualAction(
                        priority=Priority.MEDIUM,
                        category="CTR Optimization",
                        title=f"{len(low_ctr_urls)} pages with high impressions but low CTR",
                        description="These pages appear in search results but get few clicks",
                        steps=[
                            "Review and improve meta titles (make them compelling)",
                            "Optimize meta descriptions (add call-to-action)",
                            "Consider adding structured data for rich snippets",
                            "A/B test different title formats",
                        ],
                        affected_urls=low_ctr_urls,
                    ))

        # 2.5 Manual GSC checks required
        manual_actions.append(ManualAction(
            priority=Priority.INFO,
            category="Manual Review",
            title="Manual GSC checks required (not available via API)",
            description="These reports must be checked manually in Google Search Console",
            steps=[
                "Check Manual Actions: GSC → Security & Manual Actions → Manual actions",
                "Check Security Issues: GSC → Security & Manual Actions → Security issues",
                "Check Mobile Usability: GSC → Experience → Mobile Usability",
                "Check Rich Results: GSC → Enhancements → (various rich result types)",
                "Review Index Coverage: GSC → Pages → Why pages aren't indexed",
            ],
            gsc_link="https://search.google.com/search-console"
        ))

        audit.issues_found = issues
        audit.manual_actions = manual_actions
        audit.total_issues = len(issues)

        # Calculate SEO score
        score = 100
        score -= len(not_indexed) * 5
        score -= len(www_redirects) * 0.5
        score -= len(trailing_slash) * 0.5
        score -= len(poor_cwv) * 10
        audit.seo_score = max(0, min(100, int(score)))

    def _generate_report(self, audit: SEOAuditResult):
        """Phase 3: Generate and save reports."""
        print_header("📋 PHASE 3: AUDIT RESULTS")

        # Summary
        print(f"\n{Colors.BOLD}SEO SCORE: ", end="")
        score_color = Colors.GREEN if audit.seo_score >= 80 else (Colors.WARNING if audit.seo_score >= 50 else Colors.FAIL)
        print(f"{score_color}{audit.seo_score}/100{Colors.ENDC}")

        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Pages in Sitemap:  {audit.total_pages_in_sitemap}")
        print(f"  Pages Indexed:     {audit.total_pages_indexed}")
        print(f"  Total Clicks:      {audit.analytics.get('total_clicks', 0):,}")
        print(f"  Total Impressions: {audit.analytics.get('total_impressions', 0):,}")
        print(f"  Issues Found:      {audit.total_issues}")

        # Manual Actions Checklist
        print_header("✅ MANUAL ACTIONS REQUIRED")

        for action in sorted(audit.manual_actions, key=lambda x: list(Priority).index(x.priority)):
            print(f"\n{action.priority.value} [{action.category}]")
            print(f"   {Colors.BOLD}{action.title}{Colors.ENDC}")
            print(f"   {action.description}")

            if action.steps:
                print(f"\n   {Colors.CYAN}Steps:{Colors.ENDC}")
                for i, step in enumerate(action.steps, 1):
                    print(f"   {i}. {step}")

            if action.affected_urls:
                print(f"\n   {Colors.CYAN}Affected URLs:{Colors.ENDC}")
                for url in action.affected_urls[:5]:
                    print(f"   • {url}")
                if len(action.affected_urls) > 5:
                    print(f"   ... and {len(action.affected_urls) - 5} more")

            if action.gsc_link:
                print(f"\n   {Colors.BLUE}Link: {action.gsc_link}{Colors.ENDC}")

        # Save audit report
        output_file = OUTPUT_DIR / f"seo_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(audit.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        print_success(f"\n📁 Full audit report saved to: {output_file}")

        # Generate markdown checklist
        checklist_file = OUTPUT_DIR / f"seo_checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_markdown_checklist(audit, checklist_file)
        print_success(f"📝 Checklist saved to: {checklist_file}")

    def _write_markdown_checklist(self, audit: SEOAuditResult, filepath):
        """Generate markdown checklist file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# SEO Audit Checklist\n\n")
            f.write(f"**Site:** {audit.site_url}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**SEO Score:** {audit.seo_score}/100\n\n")

            f.write("## Manual Actions Required\n\n")

            for action in sorted(audit.manual_actions, key=lambda x: list(Priority).index(x.priority)):
                f.write(f"### {action.priority.value} {action.title}\n\n")
                f.write(f"{action.description}\n\n")

                if action.steps:
                    f.write("**Steps:**\n")
                    for step in action.steps:
                        f.write(f"- [ ] {step}\n")
                    f.write("\n")

                if action.affected_urls:
                    f.write("**Affected URLs:**\n")
                    for url in action.affected_urls[:10]:
                        f.write(f"- {url}\n")
                    if len(action.affected_urls) > 10:
                        f.write(f"- ... and {len(action.affected_urls) - 10} more\n")
                    f.write("\n")

                if action.gsc_link:
                    f.write(f"**Link:** {action.gsc_link}\n\n")

                f.write("---\n\n")
