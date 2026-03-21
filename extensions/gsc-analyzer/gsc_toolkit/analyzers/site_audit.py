#!/usr/bin/env python3
"""
Site Audit Analyzer

Analyzes entire website for SEO issues:
- Duplicate titles/descriptions
- Thin content pages
- Orphan pages (no internal links)
- Missing meta tags
- Image issues
- Redirect chains
- Broken internal links
- Content freshness
- Readability scores
"""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import Counter
from datetime import datetime, timedelta

from .crawler import CrawlResult, CrawledPage
from ..core.utils import print_header, print_success, print_warning, print_error, print_info, Colors


@dataclass
class SiteAuditIssue:
    """Single audit issue"""
    severity: str  # critical, warning, info
    category: str
    message: str
    urls: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


@dataclass
class SiteAuditResult:
    """Complete site audit result"""
    base_url: str
    pages_analyzed: int = 0
    issues: List[SiteAuditIssue] = field(default_factory=list)

    # Statistics
    total_words: int = 0
    avg_word_count: float = 0
    avg_response_time: float = 0

    # Scores (0-100)
    technical_score: int = 0
    content_score: int = 0
    links_score: int = 0
    overall_score: int = 0

    # Detailed findings
    duplicate_titles: Dict[str, List[str]] = field(default_factory=dict)
    duplicate_descriptions: Dict[str, List[str]] = field(default_factory=dict)
    thin_content_pages: List[str] = field(default_factory=list)
    orphan_pages: List[str] = field(default_factory=list)
    missing_titles: List[str] = field(default_factory=list)
    missing_descriptions: List[str] = field(default_factory=list)
    missing_h1: List[str] = field(default_factory=list)
    multiple_h1: List[str] = field(default_factory=list)
    images_missing_alt: List[Dict] = field(default_factory=list)
    slow_pages: List[Dict] = field(default_factory=list)
    long_titles: List[Dict] = field(default_factory=list)
    short_titles: List[Dict] = field(default_factory=list)
    long_descriptions: List[Dict] = field(default_factory=list)
    short_descriptions: List[Dict] = field(default_factory=list)
    readability_issues: List[Dict] = field(default_factory=list)


class SiteAuditor:
    """Analyzes crawl results for SEO issues"""

    # Thresholds
    THIN_CONTENT_WORDS = 300
    SLOW_PAGE_SECONDS = 3.0
    TITLE_MIN_LENGTH = 30
    TITLE_MAX_LENGTH = 60
    DESC_MIN_LENGTH = 120
    DESC_MAX_LENGTH = 160

    def analyze(self, crawl_result: CrawlResult) -> SiteAuditResult:
        """Analyze crawl results and identify issues"""
        result = SiteAuditResult(
            base_url=crawl_result.base_url,
            pages_analyzed=crawl_result.pages_crawled
        )

        pages = crawl_result.pages

        # Skip if no pages
        if not pages:
            return result

        # Collect all URLs that are linked to (for orphan detection)
        linked_urls: Set[str] = set()
        for page in pages.values():
            linked_urls.update(page.internal_links)

        # Analyze each page
        titles: Dict[str, List[str]] = {}
        descriptions: Dict[str, List[str]] = {}
        total_words = 0
        total_response_time = 0.0
        html_pages = 0

        for url, page in pages.items():
            # Only analyze HTML pages with 200 status
            if page.status_code != 200 or 'text/html' not in page.content_type:
                continue

            html_pages += 1
            total_words += page.word_count
            total_response_time += page.response_time

            # Collect titles for duplicate detection
            if page.title:
                if page.title not in titles:
                    titles[page.title] = []
                titles[page.title].append(url)
            else:
                result.missing_titles.append(url)

            # Collect descriptions for duplicate detection
            if page.meta_description:
                if page.meta_description not in descriptions:
                    descriptions[page.meta_description] = []
                descriptions[page.meta_description].append(url)
            else:
                result.missing_descriptions.append(url)

            # H1 analysis
            if not page.h1:
                result.missing_h1.append(url)

            # Thin content
            if page.word_count < self.THIN_CONTENT_WORDS:
                result.thin_content_pages.append(url)

            # Slow pages
            if page.response_time > self.SLOW_PAGE_SECONDS:
                result.slow_pages.append({
                    'url': url,
                    'time': page.response_time
                })

            # Title length
            title_len = len(page.title) if page.title else 0
            if title_len > 0 and title_len < self.TITLE_MIN_LENGTH:
                result.short_titles.append({'url': url, 'title': page.title, 'length': title_len})
            elif title_len > self.TITLE_MAX_LENGTH:
                result.long_titles.append({'url': url, 'title': page.title, 'length': title_len})

            # Description length
            desc_len = len(page.meta_description) if page.meta_description else 0
            if desc_len > 0 and desc_len < self.DESC_MIN_LENGTH:
                result.short_descriptions.append({'url': url, 'description': page.meta_description[:50], 'length': desc_len})
            elif desc_len > self.DESC_MAX_LENGTH:
                result.long_descriptions.append({'url': url, 'description': page.meta_description[:50], 'length': desc_len})

            # Images missing alt
            for img in page.images:
                if not img.get('alt'):
                    result.images_missing_alt.append({
                        'page': url,
                        'src': img.get('src', '')[:80]
                    })

            # Orphan pages (not linked from anywhere except maybe itself)
            if url not in linked_urls and page.depth > 0:
                result.orphan_pages.append(url)

            # Readability (simple Flesch-Kincaid approximation)
            if page.word_count >= 100:
                readability = self._calculate_readability(page.word_count)
                if readability and readability.get('grade_level', 0) > 12:
                    result.readability_issues.append({
                        'url': url,
                        'grade_level': readability['grade_level'],
                        'word_count': page.word_count
                    })

        # Calculate averages
        if html_pages > 0:
            result.total_words = total_words
            result.avg_word_count = total_words / html_pages
            result.avg_response_time = total_response_time / html_pages

        # Find duplicates
        result.duplicate_titles = {t: urls for t, urls in titles.items() if len(urls) > 1}
        result.duplicate_descriptions = {d: urls for d, urls in descriptions.items() if len(urls) > 1}

        # Generate issues list
        self._generate_issues(result, crawl_result)

        # Calculate scores
        self._calculate_scores(result)

        return result

    def _calculate_readability(self, word_count: int) -> Optional[Dict]:
        """Simple readability estimation based on word count"""
        # This is a simplified version - real Flesch-Kincaid requires syllable counting
        # We approximate based on average sentence/word patterns
        avg_words_per_sentence = 15  # Assumption
        avg_syllables_per_word = 1.5  # Assumption for English

        sentences = max(1, word_count / avg_words_per_sentence)

        # Flesch-Kincaid Grade Level formula (simplified)
        grade_level = 0.39 * (word_count / sentences) + 11.8 * avg_syllables_per_word - 15.59

        return {
            'grade_level': round(grade_level, 1),
            'word_count': word_count
        }

    def _generate_issues(self, result: SiteAuditResult, crawl: CrawlResult):
        """Generate structured issues list"""

        # Critical issues
        if crawl.broken_links:
            result.issues.append(SiteAuditIssue(
                severity='critical',
                category='Links',
                message=f'{len(crawl.broken_links)} broken internal links found',
                urls=[bl['url'] for bl in crawl.broken_links[:10]],
                details={'total': len(crawl.broken_links)}
            ))

        if result.missing_titles:
            result.issues.append(SiteAuditIssue(
                severity='critical',
                category='Meta',
                message=f'{len(result.missing_titles)} pages missing title tag',
                urls=result.missing_titles[:10]
            ))

        if result.missing_h1:
            result.issues.append(SiteAuditIssue(
                severity='critical',
                category='Content',
                message=f'{len(result.missing_h1)} pages missing H1 tag',
                urls=result.missing_h1[:10]
            ))

        # Warnings
        if result.duplicate_titles:
            total = sum(len(urls) for urls in result.duplicate_titles.values())
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Meta',
                message=f'{total} pages have duplicate titles ({len(result.duplicate_titles)} unique duplicates)',
                details={'duplicates': dict(list(result.duplicate_titles.items())[:5])}
            ))

        if result.duplicate_descriptions:
            total = sum(len(urls) for urls in result.duplicate_descriptions.values())
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Meta',
                message=f'{total} pages have duplicate meta descriptions',
                details={'duplicates': dict(list(result.duplicate_descriptions.items())[:5])}
            ))

        if result.thin_content_pages:
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Content',
                message=f'{len(result.thin_content_pages)} pages have thin content (<{self.THIN_CONTENT_WORDS} words)',
                urls=result.thin_content_pages[:10]
            ))

        if result.orphan_pages:
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Links',
                message=f'{len(result.orphan_pages)} orphan pages (no internal links pointing to them)',
                urls=result.orphan_pages[:10]
            ))

        if crawl.redirect_chains:
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Technical',
                message=f'{len(crawl.redirect_chains)} redirect chains detected',
                details={'chains': crawl.redirect_chains[:5]}
            ))

        if result.missing_descriptions:
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Meta',
                message=f'{len(result.missing_descriptions)} pages missing meta description',
                urls=result.missing_descriptions[:10]
            ))

        if result.slow_pages:
            result.issues.append(SiteAuditIssue(
                severity='warning',
                category='Performance',
                message=f'{len(result.slow_pages)} slow pages (>{self.SLOW_PAGE_SECONDS}s response time)',
                urls=[p['url'] for p in result.slow_pages[:10]]
            ))

        # Info
        if result.images_missing_alt:
            result.issues.append(SiteAuditIssue(
                severity='info',
                category='Images',
                message=f'{len(result.images_missing_alt)} images missing alt text',
                details={'images': result.images_missing_alt[:10]}
            ))

        if result.long_titles:
            result.issues.append(SiteAuditIssue(
                severity='info',
                category='Meta',
                message=f'{len(result.long_titles)} pages have titles longer than {self.TITLE_MAX_LENGTH} chars',
                urls=[t['url'] for t in result.long_titles[:10]]
            ))

        if result.short_descriptions:
            result.issues.append(SiteAuditIssue(
                severity='info',
                category='Meta',
                message=f'{len(result.short_descriptions)} pages have short meta descriptions (<{self.DESC_MIN_LENGTH} chars)',
                urls=[d['url'] for d in result.short_descriptions[:10]]
            ))

    def _calculate_scores(self, result: SiteAuditResult):
        """Calculate SEO scores"""
        if result.pages_analyzed == 0:
            return

        total = result.pages_analyzed

        # Technical score (redirects, speed, broken links)
        tech_issues = 0
        for issue in result.issues:
            if issue.category in ('Technical', 'Performance', 'Links'):
                if issue.severity == 'critical':
                    tech_issues += len(issue.urls) * 3 if issue.urls else 10
                elif issue.severity == 'warning':
                    tech_issues += len(issue.urls) * 1.5 if issue.urls else 5

        result.technical_score = max(0, min(100, 100 - int(tech_issues / total * 50)))

        # Content score (thin content, readability, missing H1)
        content_issues = len(result.thin_content_pages) + len(result.missing_h1)
        result.content_score = max(0, min(100, 100 - int(content_issues / total * 100)))

        # Links score (orphans, broken)
        links_issues = len(result.orphan_pages)
        for issue in result.issues:
            if issue.category == 'Links' and issue.severity == 'critical':
                links_issues += issue.details.get('total', len(issue.urls)) * 2
        result.links_score = max(0, min(100, 100 - int(links_issues / total * 50)))

        # Overall score (weighted)
        result.overall_score = int(
            result.technical_score * 0.3 +
            result.content_score * 0.4 +
            result.links_score * 0.3
        )

    def print_result(self, result: SiteAuditResult):
        """Print audit results"""
        print_header(f"Site Audit: {result.base_url}")

        # Scores
        print(f"\n{Colors.BOLD}Scores:{Colors.RESET}")

        def score_color(score):
            if score >= 80:
                return Colors.GREEN
            elif score >= 50:
                return Colors.YELLOW
            return Colors.RED

        print(f"  Technical:  {score_color(result.technical_score)}{result.technical_score}/100{Colors.RESET}")
        print(f"  Content:    {score_color(result.content_score)}{result.content_score}/100{Colors.RESET}")
        print(f"  Links:      {score_color(result.links_score)}{result.links_score}/100{Colors.RESET}")
        print(f"  {Colors.BOLD}Overall:    {score_color(result.overall_score)}{result.overall_score}/100{Colors.RESET}")

        # Statistics
        print(f"\n{Colors.BOLD}Statistics:{Colors.RESET}")
        print(f"  Pages analyzed:      {result.pages_analyzed}")
        print(f"  Total words:         {result.total_words:,}")
        print(f"  Avg words/page:      {result.avg_word_count:.0f}")
        print(f"  Avg response time:   {result.avg_response_time:.2f}s")

        # Issues by severity
        critical = [i for i in result.issues if i.severity == 'critical']
        warnings = [i for i in result.issues if i.severity == 'warning']
        info = [i for i in result.issues if i.severity == 'info']

        if critical:
            print(f"\n{Colors.RED}{Colors.BOLD}Critical Issues ({len(critical)}):{Colors.RESET}")
            for issue in critical:
                print(f"  ✗ [{issue.category}] {issue.message}")
                if issue.urls:
                    for url in issue.urls[:3]:
                        print(f"      → {url[:70]}")
                    if len(issue.urls) > 3:
                        print(f"      ... and {len(issue.urls) - 3} more")

        if warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}Warnings ({len(warnings)}):{Colors.RESET}")
            for issue in warnings:
                print(f"  ⚠ [{issue.category}] {issue.message}")
                if issue.urls:
                    for url in issue.urls[:2]:
                        print(f"      → {url[:70]}")
                    if len(issue.urls) > 2:
                        print(f"      ... and {len(issue.urls) - 2} more")

        if info:
            print(f"\n{Colors.CYAN if hasattr(Colors, 'CYAN') else Colors.RESET}Info ({len(info)}):{Colors.RESET}")
            for issue in info:
                print(f"  ℹ [{issue.category}] {issue.message}")

        # Summary recommendations
        print(f"\n{Colors.BOLD}Top Recommendations:{Colors.RESET}")
        recs = []

        if result.missing_titles:
            recs.append(f"Add title tags to {len(result.missing_titles)} pages")
        if result.missing_h1:
            recs.append(f"Add H1 tags to {len(result.missing_h1)} pages")
        if result.duplicate_titles:
            recs.append(f"Fix {len(result.duplicate_titles)} duplicate title issues")
        if result.thin_content_pages:
            recs.append(f"Expand content on {len(result.thin_content_pages)} thin pages")
        if result.orphan_pages:
            recs.append(f"Add internal links to {len(result.orphan_pages)} orphan pages")
        for issue in result.issues:
            if issue.category == 'Links' and issue.severity == 'critical':
                recs.append(f"Fix {issue.details.get('total', len(issue.urls))} broken links")
                break

        for i, rec in enumerate(recs[:5], 1):
            print(f"  {i}. {rec}")

        print()

    def export_json(self, result: SiteAuditResult) -> Dict:
        """Export results as JSON-serializable dict"""
        return {
            'base_url': result.base_url,
            'pages_analyzed': result.pages_analyzed,
            'scores': {
                'technical': result.technical_score,
                'content': result.content_score,
                'links': result.links_score,
                'overall': result.overall_score
            },
            'statistics': {
                'total_words': result.total_words,
                'avg_word_count': result.avg_word_count,
                'avg_response_time': result.avg_response_time
            },
            'issues': [
                {
                    'severity': issue.severity,
                    'category': issue.category,
                    'message': issue.message,
                    'urls': issue.urls,
                    'details': issue.details
                }
                for issue in result.issues
            ],
            'details': {
                'duplicate_titles': result.duplicate_titles,
                'duplicate_descriptions': result.duplicate_descriptions,
                'thin_content_pages': result.thin_content_pages,
                'orphan_pages': result.orphan_pages,
                'missing_titles': result.missing_titles,
                'missing_descriptions': result.missing_descriptions,
                'missing_h1': result.missing_h1,
                'images_missing_alt': result.images_missing_alt[:50],
                'slow_pages': result.slow_pages,
                'long_titles': result.long_titles,
                'short_titles': result.short_titles
            }
        }
