#!/usr/bin/env python3
"""
Links & URL Structure Analyzer

Analyzes:
- Anchor text quality and patterns
- URL structure and optimization
- Pagination implementation
- Internal/external link analysis
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse, urljoin, parse_qs
from collections import Counter

from ..core.utils import print_header, print_success, print_warning, Colors


@dataclass
class AnchorTextAnalysis:
    """Anchor text quality analysis"""
    total_links: int = 0
    internal_links: int = 0
    external_links: int = 0

    # Anchor text quality
    descriptive_anchors: int = 0
    generic_anchors: int = 0
    image_links: int = 0
    empty_anchors: int = 0

    # Patterns
    generic_anchor_list: List[Dict] = field(default_factory=list)
    anchor_text_distribution: Dict[str, int] = field(default_factory=dict)
    keyword_anchors: List[str] = field(default_factory=list)

    # Issues
    nofollow_internal: int = 0
    nofollow_external: int = 0
    sponsored_links: int = 0
    ugc_links: int = 0


@dataclass
class URLStructureAnalysis:
    """URL structure analysis"""
    url: str
    protocol: str = ''
    domain: str = ''
    path: str = ''
    path_depth: int = 0
    url_length: int = 0
    has_parameters: bool = False
    parameter_count: int = 0
    has_fragment: bool = False

    # Quality indicators
    has_keywords: bool = False
    keywords_in_url: List[str] = field(default_factory=list)
    uses_hyphens: bool = True
    uses_underscores: bool = False
    has_numbers: bool = False
    has_uppercase: bool = False
    has_special_chars: bool = False

    # Issues
    is_too_long: bool = False
    is_too_deep: bool = False
    has_session_id: bool = False
    has_tracking_params: bool = False

    issues: List[str] = field(default_factory=list)


@dataclass
class PaginationAnalysis:
    """Pagination SEO analysis"""
    has_pagination: bool = False
    has_rel_next: bool = False
    has_rel_prev: bool = False
    next_url: str = ''
    prev_url: str = ''

    # Pagination patterns
    pagination_type: str = ''  # numbered, load-more, infinite-scroll
    page_numbers_found: List[int] = field(default_factory=list)
    pagination_links: List[str] = field(default_factory=list)

    # Issues
    issues: List[str] = field(default_factory=list)


@dataclass
class LinksAnalysisResult:
    """Complete links analysis result"""
    url: str
    anchor_text: AnchorTextAnalysis = field(default_factory=AnchorTextAnalysis)
    url_structure: Optional[URLStructureAnalysis] = None
    pagination: PaginationAnalysis = field(default_factory=PaginationAnalysis)

    # Outbound links
    external_domains: Set[str] = field(default_factory=set)
    broken_links: List[str] = field(default_factory=list)

    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: int = 0


class LinksAnalyzer:
    """Analyzes link structure and anchor text"""

    # Generic anchor texts to flag
    GENERIC_ANCHORS = {
        'click here', 'here', 'read more', 'more', 'link', 'this',
        'click', 'learn more', 'see more', 'view more', 'continue',
        'go', 'visit', 'check it out', 'details', 'info', 'download',
        'article', 'page', 'website', 'site', 'read', 'view'
    }

    # Session ID patterns
    SESSION_PATTERNS = [
        r'session[_-]?id', r'sess[_-]?id', r'jsession', r'phpsess',
        r'sid=', r'aspsession', r'cfid', r'cftoken'
    ]

    # Tracking parameters to detect
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'fbclid', 'gclid', 'msclkid', 'dclid', 'mc_cid', 'mc_eid',
        'ref', 'source', 'affiliate'
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.2; Links Analyzer)'
        })

    def analyze_url(self, url: str) -> LinksAnalysisResult:
        """Analyze links and URL structure"""
        result = LinksAnalysisResult(url=url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result.issues.append(f"Failed to fetch: HTTP {response.status_code}")
                return result

            soup = BeautifulSoup(response.text, 'html.parser')
            parsed_url = urlparse(url)
            base_domain = parsed_url.netloc

            # Analyze URL structure
            result.url_structure = self._analyze_url_structure(url)

            # Analyze anchor text
            result.anchor_text = self._analyze_anchor_text(soup, base_domain, url)

            # Analyze pagination
            result.pagination = self._analyze_pagination(soup, url)

            # Collect external domains
            result.external_domains = self._get_external_domains(soup, base_domain, url)

            # Generate issues and recommendations
            self._generate_issues(result)

            # Calculate score
            result.score = self._calculate_score(result)

        except requests.RequestException as e:
            result.issues.append(f"Request failed: {str(e)}")

        return result

    def _analyze_url_structure(self, url: str) -> URLStructureAnalysis:
        """Analyze URL structure"""
        analysis = URLStructureAnalysis(url=url)
        parsed = urlparse(url)

        analysis.protocol = parsed.scheme
        analysis.domain = parsed.netloc
        analysis.path = parsed.path
        analysis.url_length = len(url)

        # Path depth
        path_parts = [p for p in parsed.path.split('/') if p]
        analysis.path_depth = len(path_parts)

        # Parameters
        if parsed.query:
            analysis.has_parameters = True
            params = parse_qs(parsed.query)
            analysis.parameter_count = len(params)

            # Check for session IDs
            query_lower = parsed.query.lower()
            for pattern in self.SESSION_PATTERNS:
                if re.search(pattern, query_lower):
                    analysis.has_session_id = True
                    analysis.issues.append("Session ID detected in URL")
                    break

            # Check for tracking parameters
            for param in params.keys():
                if param.lower() in self.TRACKING_PARAMS:
                    analysis.has_tracking_params = True

        # Fragment
        if parsed.fragment:
            analysis.has_fragment = True

        # Quality checks
        path_lower = parsed.path.lower()

        # Keywords in URL
        words = re.findall(r'[a-z]+', path_lower)
        if words:
            analysis.has_keywords = True
            analysis.keywords_in_url = [w for w in words if len(w) > 3][:5]

        # Formatting
        if '_' in parsed.path:
            analysis.uses_underscores = True
        if '-' in parsed.path:
            analysis.uses_hyphens = True
        if re.search(r'\d', parsed.path):
            analysis.has_numbers = True
        if parsed.path != parsed.path.lower():
            analysis.has_uppercase = True
        if re.search(r'[^a-zA-Z0-9/_\-.]', parsed.path):
            analysis.has_special_chars = True

        # Issues
        if analysis.url_length > 75:
            analysis.is_too_long = True
            analysis.issues.append(f"URL too long: {analysis.url_length} chars (target: <75)")

        if analysis.path_depth > 4:
            analysis.is_too_deep = True
            analysis.issues.append(f"URL too deep: {analysis.path_depth} levels (target: ≤4)")

        if analysis.uses_underscores:
            analysis.issues.append("URL uses underscores (prefer hyphens)")

        if analysis.has_uppercase:
            analysis.issues.append("URL contains uppercase characters")

        return analysis

    def _analyze_anchor_text(self, soup: BeautifulSoup, base_domain: str, base_url: str) -> AnchorTextAnalysis:
        """Analyze anchor text quality"""
        analysis = AnchorTextAnalysis()
        anchor_texts = Counter()

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            analysis.total_links += 1

            # Resolve URL
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Internal vs external
            is_internal = parsed.netloc == base_domain or not parsed.netloc
            if is_internal:
                analysis.internal_links += 1
            else:
                analysis.external_links += 1

            # Get anchor text
            anchor_text = a.get_text(strip=True)
            img = a.find('img')

            if img and not anchor_text:
                # Image link
                analysis.image_links += 1
                anchor_text = img.get('alt', '')

            if not anchor_text:
                analysis.empty_anchors += 1
                continue

            anchor_lower = anchor_text.lower().strip()
            anchor_texts[anchor_lower] += 1

            # Check if generic
            if anchor_lower in self.GENERIC_ANCHORS or len(anchor_lower) <= 3:
                analysis.generic_anchors += 1
                analysis.generic_anchor_list.append({
                    'text': anchor_text[:50],
                    'href': href[:80],
                    'is_internal': is_internal
                })
            else:
                analysis.descriptive_anchors += 1
                if len(anchor_text) >= 3 and len(anchor_text) <= 50:
                    analysis.keyword_anchors.append(anchor_text)

            # Check rel attributes
            rel = a.get('rel', [])
            if isinstance(rel, str):
                rel = rel.split()

            if 'nofollow' in rel:
                if is_internal:
                    analysis.nofollow_internal += 1
                else:
                    analysis.nofollow_external += 1
            if 'sponsored' in rel:
                analysis.sponsored_links += 1
            if 'ugc' in rel:
                analysis.ugc_links += 1

        # Top anchor texts
        analysis.anchor_text_distribution = dict(anchor_texts.most_common(10))

        return analysis

    def _analyze_pagination(self, soup: BeautifulSoup, base_url: str) -> PaginationAnalysis:
        """Analyze pagination implementation"""
        analysis = PaginationAnalysis()

        # Check for rel="next" and rel="prev"
        for link in soup.find_all('link', rel=True):
            rel = link.get('rel', [])
            if isinstance(rel, str):
                rel = [rel]

            if 'next' in rel:
                analysis.has_rel_next = True
                analysis.next_url = link.get('href', '')
                analysis.has_pagination = True

            if 'prev' in rel:
                analysis.has_rel_prev = True
                analysis.prev_url = link.get('href', '')
                analysis.has_pagination = True

        # Look for pagination patterns in links
        pagination_patterns = [
            r'/page/(\d+)',
            r'[?&]page=(\d+)',
            r'[?&]p=(\d+)',
            r'/(\d+)/?$',
        ]

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            for pattern in pagination_patterns:
                match = re.search(pattern, href)
                if match:
                    analysis.has_pagination = True
                    page_num = int(match.group(1))
                    if page_num not in analysis.page_numbers_found:
                        analysis.page_numbers_found.append(page_num)
                        analysis.pagination_links.append(href)

        # Detect pagination type
        if analysis.has_pagination:
            if analysis.page_numbers_found:
                analysis.pagination_type = 'numbered'
            elif soup.find(class_=re.compile(r'load[-_]?more|infinite', re.I)):
                analysis.pagination_type = 'load-more'

        # Issues
        if analysis.has_pagination:
            if not analysis.has_rel_next and not analysis.has_rel_prev:
                analysis.issues.append(
                    "Pagination detected but missing rel=\"next\"/rel=\"prev\""
                )

        return analysis

    def _get_external_domains(self, soup: BeautifulSoup, base_domain: str, base_url: str) -> Set[str]:
        """Get set of external domains linked to"""
        domains = set()

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if not href:
                continue

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc and parsed.netloc != base_domain:
                domains.add(parsed.netloc)

        return domains

    def _generate_issues(self, result: LinksAnalysisResult):
        """Generate issues and recommendations"""

        # URL structure issues
        result.issues.extend(result.url_structure.issues)

        if result.url_structure.has_parameters and not result.url_structure.has_tracking_params:
            result.recommendations.append(
                "Consider using URL rewriting for cleaner URLs"
            )

        # Anchor text issues
        a = result.anchor_text
        if a.total_links > 0:
            generic_ratio = a.generic_anchors / a.total_links * 100
            if generic_ratio > 20:
                result.issues.append(
                    f"{generic_ratio:.0f}% of links use generic anchor text"
                )
                result.recommendations.append(
                    "Replace generic anchors ('click here', 'read more') with descriptive text"
                )

        if a.empty_anchors > 0:
            result.issues.append(f"{a.empty_anchors} links have empty anchor text")
            result.recommendations.append(
                "Add descriptive text or alt text for image links"
            )

        if a.nofollow_internal > 0:
            result.issues.append(
                f"{a.nofollow_internal} internal links have nofollow attribute"
            )
            result.recommendations.append(
                "Remove nofollow from internal links to allow PageRank flow"
            )

        # Pagination issues
        result.issues.extend(result.pagination.issues)

        if result.pagination.has_pagination and not result.pagination.has_rel_next:
            result.recommendations.append(
                "Add rel=\"next\" and rel=\"prev\" to pagination links"
            )

    def _calculate_score(self, result: LinksAnalysisResult) -> int:
        """Calculate links quality score"""
        score = 100

        # URL structure (25 points)
        u = result.url_structure
        if u.is_too_long:
            score -= 10
        if u.is_too_deep:
            score -= 8
        if u.uses_underscores:
            score -= 5
        if u.has_session_id:
            score -= 10
        if u.has_uppercase:
            score -= 2

        # Anchor text (40 points)
        a = result.anchor_text
        if a.total_links > 0:
            # Generic anchors
            generic_ratio = a.generic_anchors / a.total_links
            if generic_ratio > 0.3:
                score -= 20
            elif generic_ratio > 0.15:
                score -= 10

            # Empty anchors
            empty_ratio = a.empty_anchors / a.total_links
            if empty_ratio > 0.1:
                score -= 10
            elif empty_ratio > 0.05:
                score -= 5

            # Internal nofollow
            if a.nofollow_internal > 0:
                score -= 10

        # Pagination (15 points)
        p = result.pagination
        if p.has_pagination and not p.has_rel_next:
            score -= 15

        return max(0, min(100, score))

    def print_result(self, result: LinksAnalysisResult):
        """Print links analysis result"""
        print_header(f"Links Analysis: {result.url}")

        # Score
        score_color = Colors.GREEN if result.score >= 80 else Colors.YELLOW if result.score >= 50 else Colors.RED
        print(f"\nLinks Score: {score_color}{result.score}/100{Colors.RESET}")

        # URL Structure
        u = result.url_structure
        print(f"\n{Colors.BOLD}URL Structure:{Colors.RESET}")
        print(f"  Length: {u.url_length} chars {'⚠' if u.is_too_long else '✓'}")
        print(f"  Depth: {u.path_depth} levels {'⚠' if u.is_too_deep else '✓'}")
        print(f"  Parameters: {'Yes' if u.has_parameters else 'No'}")
        if u.keywords_in_url:
            print(f"  Keywords: {', '.join(u.keywords_in_url)}")

        status_items = []
        if u.uses_hyphens:
            status_items.append("hyphens ✓")
        if u.uses_underscores:
            status_items.append("underscores ⚠")
        if u.has_uppercase:
            status_items.append("uppercase ⚠")
        if status_items:
            print(f"  Format: {', '.join(status_items)}")

        # Anchor Text
        a = result.anchor_text
        print(f"\n{Colors.BOLD}Anchor Text:{Colors.RESET}")
        print(f"  Total links: {a.total_links} ({a.internal_links} internal, {a.external_links} external)")
        print(f"  Descriptive: {a.descriptive_anchors}")
        print(f"  Generic: {a.generic_anchors}")
        print(f"  Image links: {a.image_links}")
        print(f"  Empty: {a.empty_anchors}")

        if a.nofollow_internal > 0:
            print(f"  {Colors.YELLOW}⚠ Internal nofollow: {a.nofollow_internal}{Colors.RESET}")

        if a.generic_anchor_list:
            print(f"\n  Generic anchors found:")
            for ga in a.generic_anchor_list[:5]:
                print(f"    \"{ga['text']}\" → {ga['href'][:50]}")

        if a.anchor_text_distribution:
            print(f"\n  Top anchor texts:")
            for text, count in list(a.anchor_text_distribution.items())[:5]:
                print(f"    \"{text[:40]}\" ({count}x)")

        # Pagination
        p = result.pagination
        if p.has_pagination:
            print(f"\n{Colors.BOLD}Pagination:{Colors.RESET}")
            print(f"  Type: {p.pagination_type or 'detected'}")
            print(f"  rel=next: {'✓ ' + p.next_url[:50] if p.has_rel_next else '✗'}")
            print(f"  rel=prev: {'✓ ' + p.prev_url[:50] if p.has_rel_prev else '✗'}")
            if p.page_numbers_found:
                print(f"  Pages found: {sorted(p.page_numbers_found)[:10]}")

        # External domains
        if result.external_domains:
            print(f"\n{Colors.BOLD}External Domains ({len(result.external_domains)}):{Colors.RESET}")
            for domain in sorted(result.external_domains)[:10]:
                print(f"  → {domain}")

        # Issues
        if result.issues:
            print(f"\n{Colors.RED}Issues:{Colors.RESET}")
            for issue in result.issues:
                print(f"  ✗ {issue}")

        # Recommendations
        if result.recommendations:
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.RESET}")
            for rec in result.recommendations:
                print(f"  → {rec}")

        print()

    def analyze_batch(self, urls: List[str]) -> List[LinksAnalysisResult]:
        """Analyze multiple URLs"""
        results = []
        for url in urls:
            result = self.analyze_url(url)
            results.append(result)
            self.print_result(result)
        return results
