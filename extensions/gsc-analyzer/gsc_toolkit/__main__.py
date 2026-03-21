#!/usr/bin/env python3
"""
GSC Toolkit - CLI Entry Point

Usage:
    python -m gsc_toolkit list-sites
    python -m gsc_toolkit inspect <url>
    python -m gsc_toolkit analytics [--days 28] [--dimension query|page|device|country]
    python -m gsc_toolkit sitemaps
    python -m gsc_toolkit batch-inspect <urls_file>
    python -m gsc_toolkit coverage [--path <directory>]
    python -m gsc_toolkit cwv <url>
    python -m gsc_toolkit cwv-batch <urls_file>
    python -m gsc_toolkit index-request <url>
    python -m gsc_toolkit index-batch <sitemap_url>
    python -m gsc_toolkit links [--path <directory>]
    python -m gsc_toolkit full-report
    python -m gsc_toolkit seo-audit [--days 28]

    # Page analyzers
    python -m gsc_toolkit security <url>
    python -m gsc_toolkit onpage <url>
    python -m gsc_toolkit schema <url>
    python -m gsc_toolkit hreflang <url>
    python -m gsc_toolkit robots <base_url>
    python -m gsc_toolkit sitemap-check <sitemap_url>
    python -m gsc_toolkit full-seo <url>

    # Content & Quality analyzers
    python -m gsc_toolkit content <url>           # Content quality (readability, freshness)
    python -m gsc_toolkit mobile <url>            # Mobile SEO analysis
    python -m gsc_toolkit performance <url>       # Performance analysis
    python -m gsc_toolkit url-analysis <url>      # URL structure & anchor text

    # Site-wide analysis
    python -m gsc_toolkit site-audit <start_url> [--max-pages 500] [--max-depth 10]
"""

import argparse
from pathlib import Path

from .core.config import DEFAULT_DAYS, BASE_URL
from .core.utils import print_error, print_header, print_info
from .gsc_client import GSCAnalyzer
from .audit.seo_audit import SEOAuditor
from .analyzers.security import SecurityAnalyzer
from .analyzers.onpage import OnPageAnalyzer
from .analyzers.schema import SchemaAnalyzer
from .analyzers.hreflang import HreflangAnalyzer
from .analyzers.robots import RobotsAnalyzer
from .analyzers.crawler import SiteCrawler
from .analyzers.site_audit import SiteAuditor
from .analyzers.content import ContentAnalyzer
from .analyzers.mobile import MobileAnalyzer
from .analyzers.performance import PerformanceAnalyzer
from .analyzers.links_analysis import LinksAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description='GSC Toolkit - Complete SEO Analysis Package',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # GSC Commands
  python -m gsc_toolkit list-sites
  python -m gsc_toolkit inspect https://example.com/page
  python -m gsc_toolkit analytics --days 28 --dimension query
  python -m gsc_toolkit sitemaps
  python -m gsc_toolkit batch-inspect urls.txt
  python -m gsc_toolkit coverage [--path /path/to/exports]
  python -m gsc_toolkit links [--path /path/to/exports]
  python -m gsc_toolkit cwv https://example.com/page
  python -m gsc_toolkit cwv-batch urls.txt
  python -m gsc_toolkit index-request https://example.com/page
  python -m gsc_toolkit index-batch https://example.com/sitemap.xml
  python -m gsc_toolkit full-report --days 30
  python -m gsc_toolkit seo-audit --days 28

  # Page Analysis Commands
  python -m gsc_toolkit security https://example.com/
  python -m gsc_toolkit onpage https://example.com/page
  python -m gsc_toolkit schema https://example.com/page
  python -m gsc_toolkit hreflang https://example.com/page
  python -m gsc_toolkit robots https://example.com
  python -m gsc_toolkit sitemap-check https://example.com/sitemap.xml
  python -m gsc_toolkit full-seo https://example.com/page

  # Content & Quality Analysis Commands
  python -m gsc_toolkit content https://example.com/page
  python -m gsc_toolkit mobile https://example.com/page
  python -m gsc_toolkit performance https://example.com/page
  python -m gsc_toolkit url-analysis https://example.com/page

  # Site-wide Analysis Commands
  python -m gsc_toolkit site-audit https://example.com --max-pages 100
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ===== GSC COMMANDS =====

    # list-sites
    subparsers.add_parser('list-sites', help='List all Search Console properties')

    # inspect
    inspect_parser = subparsers.add_parser('inspect', help='Inspect a URL')
    inspect_parser.add_argument('url', help='URL to inspect')

    # analytics
    analytics_parser = subparsers.add_parser('analytics', help='Get search analytics')
    analytics_parser.add_argument('--days', type=int, default=DEFAULT_DAYS, help='Number of days')
    analytics_parser.add_argument('--dimension', default='query',
                                  choices=['query', 'page', 'device', 'country', 'date'],
                                  help='Dimension to group by')
    analytics_parser.add_argument('--limit', type=int, default=1000, help='Max rows to fetch')

    # sitemaps
    subparsers.add_parser('sitemaps', help='List sitemaps')

    # batch-inspect
    batch_parser = subparsers.add_parser('batch-inspect', help='Inspect multiple URLs from file')
    batch_parser.add_argument('file', help='File with URLs (one per line)')

    # coverage
    coverage_parser = subparsers.add_parser('coverage', help='Analyze Coverage CSV exports from GSC')
    coverage_parser.add_argument('--path', help='Path to search for export folders')

    # links
    links_parser = subparsers.add_parser('links', help='Analyze Links CSV exports from GSC')
    links_parser.add_argument('--path', help='Path to search for export folders')

    # cwv (Core Web Vitals)
    cwv_parser = subparsers.add_parser('cwv', help='Analyze Core Web Vitals for a URL')
    cwv_parser.add_argument('url', help='URL to analyze')
    cwv_parser.add_argument('--strategy', default='mobile', choices=['mobile', 'desktop'], help='Strategy')

    # cwv-batch
    cwv_batch_parser = subparsers.add_parser('cwv-batch', help='Analyze Core Web Vitals for multiple URLs')
    cwv_batch_parser.add_argument('file', help='File with URLs (one per line)')
    cwv_batch_parser.add_argument('--strategy', default='mobile', choices=['mobile', 'desktop'], help='Strategy')

    # index-request
    index_parser = subparsers.add_parser('index-request', help='Request indexing for a URL')
    index_parser.add_argument('url', help='URL to request indexing for')

    # index-batch
    index_batch_parser = subparsers.add_parser('index-batch', help='Request indexing for URLs from sitemap')
    index_batch_parser.add_argument('sitemap', help='Sitemap URL')
    index_batch_parser.add_argument('--limit', type=int, default=200, help='Max URLs (daily quota is 200)')

    # full-report
    report_parser = subparsers.add_parser('full-report', help='Generate full SEO report')
    report_parser.add_argument('--days', type=int, default=DEFAULT_DAYS, help='Number of days')

    # seo-audit
    audit_parser = subparsers.add_parser('seo-audit', help='Complete SEO audit with action checklist')
    audit_parser.add_argument('--days', type=int, default=DEFAULT_DAYS, help='Number of days')
    audit_parser.add_argument('--urls-file', help='File with key URLs to analyze')

    # ===== PAGE ANALYSIS COMMANDS =====

    # security
    security_parser = subparsers.add_parser('security', help='Analyze HTTP security headers')
    security_parser.add_argument('url', help='URL to analyze')

    # security-batch
    security_batch_parser = subparsers.add_parser('security-batch', help='Analyze security headers for multiple URLs')
    security_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # onpage
    onpage_parser = subparsers.add_parser('onpage', help='Analyze on-page SEO elements')
    onpage_parser.add_argument('url', help='URL to analyze')

    # onpage-batch
    onpage_batch_parser = subparsers.add_parser('onpage-batch', help='Analyze on-page SEO for multiple URLs')
    onpage_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # schema
    schema_parser = subparsers.add_parser('schema', help='Validate structured data (JSON-LD)')
    schema_parser.add_argument('url', help='URL to analyze')

    # schema-batch
    schema_batch_parser = subparsers.add_parser('schema-batch', help='Validate schema for multiple URLs')
    schema_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # hreflang
    hreflang_parser = subparsers.add_parser('hreflang', help='Validate hreflang implementation')
    hreflang_parser.add_argument('url', help='URL to analyze')
    hreflang_parser.add_argument('--no-return-check', action='store_true',
                                  help='Skip return link validation (faster)')

    # hreflang-batch
    hreflang_batch_parser = subparsers.add_parser('hreflang-batch', help='Validate hreflang for multiple URLs')
    hreflang_batch_parser.add_argument('file', help='File with URLs (one per line)')
    hreflang_batch_parser.add_argument('--no-return-check', action='store_true',
                                        help='Skip return link validation')

    # robots
    robots_parser = subparsers.add_parser('robots', help='Analyze robots.txt')
    robots_parser.add_argument('url', help='Base URL (e.g., https://example.com)')

    # sitemap-check
    sitemap_check_parser = subparsers.add_parser('sitemap-check', help='Validate sitemap XML')
    sitemap_check_parser.add_argument('url', help='Sitemap URL')
    sitemap_check_parser.add_argument('--max-urls', type=int, default=1000, help='Max URLs to parse')

    # full-seo (combines all page analyzers)
    full_seo_parser = subparsers.add_parser('full-seo', help='Run all page SEO analyzers on a URL')
    full_seo_parser.add_argument('url', help='URL to analyze')

    # ===== CONTENT & QUALITY ANALYSIS COMMANDS =====

    # content
    content_parser = subparsers.add_parser('content', help='Analyze content quality (readability, freshness, language)')
    content_parser.add_argument('url', help='URL to analyze')

    # content-batch
    content_batch_parser = subparsers.add_parser('content-batch', help='Analyze content quality for multiple URLs')
    content_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # mobile
    mobile_parser = subparsers.add_parser('mobile', help='Analyze mobile SEO (viewport, touch targets, responsive)')
    mobile_parser.add_argument('url', help='URL to analyze')

    # mobile-batch
    mobile_batch_parser = subparsers.add_parser('mobile-batch', help='Analyze mobile SEO for multiple URLs')
    mobile_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # performance
    performance_parser = subparsers.add_parser('performance', help='Analyze performance (CSS/JS blocking, images, caching)')
    performance_parser.add_argument('url', help='URL to analyze')

    # performance-batch
    performance_batch_parser = subparsers.add_parser('performance-batch', help='Analyze performance for multiple URLs')
    performance_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # url-analysis (anchor text, URL structure, pagination)
    url_analysis_parser = subparsers.add_parser('url-analysis', help='Analyze URL structure and anchor text quality')
    url_analysis_parser.add_argument('url', help='URL to analyze')

    # url-analysis-batch
    url_analysis_batch_parser = subparsers.add_parser('url-analysis-batch', help='Analyze URL structure for multiple URLs')
    url_analysis_batch_parser.add_argument('file', help='File with URLs (one per line)')

    # ===== SITE-WIDE ANALYSIS COMMANDS =====

    # site-audit
    site_audit_parser = subparsers.add_parser('site-audit', help='Crawl and audit entire website')
    site_audit_parser.add_argument('url', help='Start URL for crawling')
    site_audit_parser.add_argument('--max-pages', type=int, default=500, help='Maximum pages to crawl (default: 500)')
    site_audit_parser.add_argument('--max-depth', type=int, default=10, help='Maximum crawl depth (default: 10)')
    site_audit_parser.add_argument('--delay', type=float, default=0.2, help='Delay between requests in seconds (default: 0.2)')
    site_audit_parser.add_argument('--output', help='Output JSON file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # ===== GSC COMMANDS EXECUTION =====

    if args.command in ['list-sites', 'inspect', 'analytics', 'sitemaps', 'batch-inspect',
                        'coverage', 'links', 'cwv', 'cwv-batch', 'index-request',
                        'index-batch', 'full-report', 'seo-audit']:
        analyzer = GSCAnalyzer()

        if args.command == 'list-sites':
            analyzer.list_sites()

        elif args.command == 'inspect':
            analyzer.inspect_url(args.url)

        elif args.command == 'analytics':
            analyzer.get_analytics(
                days=args.days,
                dimensions=[args.dimension],
                row_limit=args.limit
            )

        elif args.command == 'sitemaps':
            analyzer.list_sitemaps()

        elif args.command == 'batch-inspect':
            urls = _read_urls_file(args.file)
            if urls:
                analyzer.batch_inspect(urls)

        elif args.command == 'coverage':
            analyzer.analyze_coverage(search_path=args.path)

        elif args.command == 'links':
            analyzer.analyze_links(search_path=args.path)

        elif args.command == 'cwv':
            analyzer.analyze_cwv(args.url, args.strategy)

        elif args.command == 'cwv-batch':
            urls = _read_urls_file(args.file)
            if urls:
                analyzer.analyze_cwv_batch(urls, args.strategy)

        elif args.command == 'index-request':
            analyzer.request_indexing(args.url)

        elif args.command == 'index-batch':
            analyzer.request_indexing_from_sitemap(args.sitemap, args.limit)

        elif args.command == 'full-report':
            analyzer.generate_full_report(days=args.days)

        elif args.command == 'seo-audit':
            key_urls = None
            if args.urls_file and Path(args.urls_file).exists():
                with open(args.urls_file, 'r') as f:
                    key_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            auditor = SEOAuditor(analyzer)
            auditor.run_audit(days=args.days, key_urls=key_urls)

    # ===== PAGE ANALYSIS COMMANDS EXECUTION =====

    elif args.command == 'security':
        analyzer = SecurityAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'security-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = SecurityAnalyzer()
            analyzer.analyze_batch(urls)

    elif args.command == 'onpage':
        analyzer = OnPageAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'onpage-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = OnPageAnalyzer()
            analyzer.analyze_batch(urls)

    elif args.command == 'schema':
        analyzer = SchemaAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'schema-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = SchemaAnalyzer()
            analyzer.analyze_batch(urls)

    elif args.command == 'hreflang':
        check_return = not args.no_return_check
        analyzer = HreflangAnalyzer(check_return_links=check_return)
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'hreflang-batch':
        urls = _read_urls_file(args.file)
        if urls:
            check_return = not args.no_return_check
            analyzer = HreflangAnalyzer(check_return_links=check_return)
            analyzer.analyze_batch(urls)

    elif args.command == 'robots':
        analyzer = RobotsAnalyzer()
        result = analyzer.analyze_robots_txt(args.url)
        analyzer.print_robots_result(result)

    elif args.command == 'sitemap-check':
        analyzer = RobotsAnalyzer()
        result = analyzer.analyze_sitemap(args.url, max_urls=args.max_urls)
        analyzer.print_sitemap_result(result)

    elif args.command == 'full-seo':
        _run_full_seo_analysis(args.url)

    # ===== CONTENT & QUALITY ANALYSIS COMMANDS EXECUTION =====

    elif args.command == 'content':
        analyzer = ContentAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'content-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = ContentAnalyzer()
            analyzer.analyze_batch(urls)

    elif args.command == 'mobile':
        analyzer = MobileAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'mobile-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = MobileAnalyzer()
            analyzer.analyze_batch(urls)

    elif args.command == 'performance':
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'performance-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = PerformanceAnalyzer()
            analyzer.analyze_batch(urls)

    elif args.command == 'url-analysis':
        analyzer = LinksAnalyzer()
        result = analyzer.analyze_url(args.url)
        analyzer.print_result(result)

    elif args.command == 'url-analysis-batch':
        urls = _read_urls_file(args.file)
        if urls:
            analyzer = LinksAnalyzer()
            analyzer.analyze_batch(urls)

    # ===== SITE-WIDE ANALYSIS COMMANDS EXECUTION =====

    elif args.command == 'site-audit':
        _run_site_audit(
            args.url,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            delay=args.delay,
            output_path=args.output
        )


def _read_urls_file(filepath: str) -> list:
    """Read URLs from file"""
    if not Path(filepath).exists():
        print_error(f"File not found: {filepath}")
        return []

    with open(filepath, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not urls:
        print_error("No URLs found in file")
        return []

    return urls


def _run_full_seo_analysis(url: str):
    """Run all page SEO analyzers on a URL"""
    print_header(f"Full SEO Analysis: {url}")

    # 1. Security Headers
    print_info("\n[1/9] Security Headers Analysis...")
    security = SecurityAnalyzer()
    security_result = security.analyze_url(url)
    security.print_result(security_result)

    # 2. On-Page SEO
    print_info("\n[2/9] On-Page SEO Analysis...")
    onpage = OnPageAnalyzer()
    onpage_result = onpage.analyze_url(url)
    onpage.print_result(onpage_result)

    # 3. Schema Validation
    print_info("\n[3/9] Schema/Structured Data Validation...")
    schema = SchemaAnalyzer()
    schema_result = schema.analyze_url(url)
    schema.print_result(schema_result)

    # 4. Hreflang
    print_info("\n[4/9] Hreflang Analysis...")
    hreflang = HreflangAnalyzer()
    hreflang_result = hreflang.analyze_url(url)
    hreflang.print_result(hreflang_result)

    # 5. Robots & Sitemap
    print_info("\n[5/9] Robots.txt Analysis...")
    robots = RobotsAnalyzer()
    robots_result = robots.analyze_robots_txt(url)
    robots.print_robots_result(robots_result)

    # 6. Content Quality
    print_info("\n[6/9] Content Quality Analysis...")
    content = ContentAnalyzer()
    content_result = content.analyze_url(url)
    content.print_result(content_result)

    # 7. Mobile SEO
    print_info("\n[7/9] Mobile SEO Analysis...")
    mobile = MobileAnalyzer()
    mobile_result = mobile.analyze_url(url)
    mobile.print_result(mobile_result)

    # 8. Performance
    print_info("\n[8/9] Performance Analysis...")
    performance = PerformanceAnalyzer()
    performance_result = performance.analyze_url(url)
    performance.print_result(performance_result)

    # 9. URL & Links Analysis
    print_info("\n[9/9] URL & Links Analysis...")
    links = LinksAnalyzer()
    links_result = links.analyze_url(url)
    links.print_result(links_result)

    # Summary
    print_header("Summary")
    print(f"  Security Score:     {security_result.score}/100")
    print(f"  On-Page Score:      {onpage_result.score}/100")
    print(f"  Schema Score:       {schema_result.score}/100")
    print(f"  Hreflang Score:     {hreflang_result.score}/100")
    print(f"  Robots Score:       {robots_result.score}/100")
    print(f"  Content Score:      {content_result.score}/100")
    print(f"  Mobile Score:       {mobile_result.score}/100")
    print(f"  Performance Score:  {performance_result.score}/100")
    print(f"  Links Score:        {links_result.score}/100")

    total_score = (
        security_result.score +
        onpage_result.score +
        schema_result.score +
        hreflang_result.score +
        robots_result.score +
        content_result.score +
        mobile_result.score +
        performance_result.score +
        links_result.score
    ) / 9
    print(f"\n  Overall Score:      {total_score:.0f}/100")
    print()


def _run_site_audit(url: str, max_pages: int = 500, max_depth: int = 10, delay: float = 0.2, output_path: str = None):
    """Crawl website and run full site audit"""
    import json
    from datetime import datetime

    print_header(f"Site Audit: {url}")
    print_info(f"Settings: max_pages={max_pages}, max_depth={max_depth}, delay={delay}s")

    # Step 1: Crawl the site
    print_info("\n[1/2] Crawling website...")
    crawler = SiteCrawler(
        max_pages=max_pages,
        max_depth=max_depth,
        delay=delay
    )
    crawl_result = crawler.crawl(url)
    crawler.print_summary(crawl_result)

    # Step 2: Analyze crawl results
    print_info("\n[2/2] Analyzing crawl data...")
    auditor = SiteAuditor()
    audit_result = auditor.analyze(crawl_result)
    auditor.print_result(audit_result)

    # Export to JSON if output path specified
    if output_path:
        output_data = auditor.export_json(audit_result)
        output_data['crawl_stats'] = {
            'pages_crawled': crawl_result.pages_crawled,
            'pages_failed': crawl_result.pages_failed,
            'external_links': len(crawl_result.external_links),
            'crawl_time': crawl_result.crawl_time,
            'broken_links': crawl_result.broken_links,
            'redirect_chains': crawl_result.redirect_chains
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print_info(f"\nReport saved to: {output_path}")
    else:
        # Auto-generate output path
        from .core.config import OUTPUT_DIR
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        auto_path = Path(OUTPUT_DIR) / f"site_audit_{timestamp}.json"
        auto_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = auditor.export_json(audit_result)
        output_data['crawl_stats'] = {
            'pages_crawled': crawl_result.pages_crawled,
            'pages_failed': crawl_result.pages_failed,
            'external_links': len(crawl_result.external_links),
            'crawl_time': crawl_result.crawl_time,
            'broken_links': crawl_result.broken_links,
            'redirect_chains': crawl_result.redirect_chains
        }
        with open(auto_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print_info(f"\nReport saved to: {auto_path}")


if __name__ == '__main__':
    main()
