#!/usr/bin/env python3
"""
Robots.txt & Sitemap Validator

Validates:
- robots.txt syntax and directives
- Sitemap XML format and content
- URL accessibility
- Common misconfigurations
"""

import re
import requests
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime

from ..core.utils import print_success, print_warning, print_error, print_info, Colors


@dataclass
class RobotsTxtRule:
    """Individual robots.txt rule"""
    user_agent: str
    directive: str  # allow, disallow, crawl-delay, sitemap
    value: str
    line_number: int
    is_valid: bool = True
    warning: Optional[str] = None


@dataclass
class RobotsTxtResult:
    """Robots.txt analysis result"""
    url: str
    exists: bool = False
    status_code: int = 0
    content: str = ""
    size_bytes: int = 0
    rules: list = field(default_factory=list)
    sitemaps: list = field(default_factory=list)
    user_agents: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    blocks_googlebot: bool = False
    blocks_all: bool = False
    score: int = 0


@dataclass
class SitemapUrl:
    """Individual sitemap URL"""
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None
    is_valid: bool = True
    issues: list = field(default_factory=list)


@dataclass
class SitemapResult:
    """Sitemap analysis result"""
    url: str
    exists: bool = False
    status_code: int = 0
    is_index: bool = False
    format_valid: bool = True
    urls: list = field(default_factory=list)
    child_sitemaps: list = field(default_factory=list)
    total_urls: int = 0
    urls_with_lastmod: int = 0
    issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    score: int = 0


class RobotsAnalyzer:
    """Analyzes robots.txt and sitemap files"""

    VALID_DIRECTIVES = {
        'user-agent', 'disallow', 'allow', 'sitemap',
        'crawl-delay', 'host', 'clean-param'
    }

    VALID_CHANGEFREQ = {
        'always', 'hourly', 'daily', 'weekly',
        'monthly', 'yearly', 'never'
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.0; Robots Analyzer)'
        })

    def analyze_robots_txt(self, base_url: str) -> RobotsTxtResult:
        """Analyze robots.txt for a domain"""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        result = RobotsTxtResult(url=robots_url)

        try:
            response = self.session.get(robots_url, timeout=self.timeout)
            result.status_code = response.status_code

            if response.status_code == 200:
                result.exists = True
                result.content = response.text
                result.size_bytes = len(response.content)
                self._parse_robots_txt(result)
            elif response.status_code == 404:
                result.exists = False
                result.recommendations.append(
                    "No robots.txt found. Consider creating one to control crawler access."
                )
            else:
                result.issues.append(f"Unexpected status code: {response.status_code}")

        except requests.RequestException as e:
            result.issues.append(f"Failed to fetch robots.txt: {str(e)}")

        # Calculate score
        result.score = self._calculate_robots_score(result)

        return result

    def _parse_robots_txt(self, result: RobotsTxtResult):
        """Parse robots.txt content"""
        current_user_agent = None
        lines = result.content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse directive
            match = re.match(r'^([a-zA-Z-]+)\s*:\s*(.*)$', line)
            if not match:
                result.warnings.append(f"Line {i}: Invalid syntax: {line[:50]}")
                continue

            directive = match.group(1).lower()
            value = match.group(2).strip()

            # Validate directive
            if directive not in self.VALID_DIRECTIVES:
                result.warnings.append(f"Line {i}: Unknown directive: {directive}")

            rule = RobotsTxtRule(
                user_agent=current_user_agent or '*',
                directive=directive,
                value=value,
                line_number=i
            )

            if directive == 'user-agent':
                current_user_agent = value
                if value not in result.user_agents:
                    result.user_agents.append(value)

            elif directive == 'sitemap':
                result.sitemaps.append(value)
                # Validate sitemap URL
                if not value.startswith(('http://', 'https://')):
                    rule.warning = "Sitemap should be an absolute URL"
                    result.warnings.append(f"Line {i}: {rule.warning}")

            elif directive == 'disallow':
                if value == '/':
                    if current_user_agent == '*':
                        result.blocks_all = True
                        result.issues.append("robots.txt blocks ALL crawlers from entire site")
                    elif current_user_agent and 'googlebot' in current_user_agent.lower():
                        result.blocks_googlebot = True
                        result.issues.append("robots.txt blocks Googlebot from entire site")

            elif directive == 'crawl-delay':
                try:
                    delay = float(value)
                    if delay > 10:
                        rule.warning = f"High crawl-delay ({delay}s) may slow indexing"
                        result.warnings.append(f"Line {i}: {rule.warning}")
                except ValueError:
                    rule.is_valid = False
                    result.warnings.append(f"Line {i}: Invalid crawl-delay value: {value}")

            result.rules.append(rule)

        # Check for common issues
        if not result.sitemaps:
            result.recommendations.append(
                "Consider adding Sitemap directive to help search engines find your sitemap"
            )

        if result.size_bytes > 500000:  # 500KB
            result.warnings.append(
                f"robots.txt is large ({result.size_bytes / 1024:.1f}KB). Consider simplifying."
            )

    def _calculate_robots_score(self, result: RobotsTxtResult) -> int:
        """Calculate robots.txt implementation score"""
        if not result.exists:
            return 50  # No robots.txt is okay but not ideal

        score = 70  # Base score for having robots.txt

        # Sitemaps declared (+15)
        if result.sitemaps:
            score += 15

        # No critical blocks (+10)
        if not result.blocks_all and not result.blocks_googlebot:
            score += 10

        # No issues (+5)
        if not result.issues:
            score += 5

        # Deductions
        if result.warnings:
            score -= min(len(result.warnings) * 2, 10)

        return max(0, min(100, score))

    def analyze_sitemap(self, sitemap_url: str, max_urls: int = 1000) -> SitemapResult:
        """Analyze a sitemap XML file"""
        result = SitemapResult(url=sitemap_url)

        try:
            response = self.session.get(sitemap_url, timeout=self.timeout)
            result.status_code = response.status_code

            if response.status_code != 200:
                result.exists = False
                result.issues.append(f"Sitemap returned HTTP {response.status_code}")
                return result

            result.exists = True

            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'xml' not in content_type.lower() and 'text' not in content_type.lower():
                result.warnings.append(f"Unexpected Content-Type: {content_type}")

            # Parse XML
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                result.format_valid = False
                result.issues.append(f"Invalid XML syntax: {str(e)}")
                return result

            # Detect sitemap type
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Check for sitemap index
            if root.tag.endswith('sitemapindex') or root.find('.//sm:sitemap', ns) is not None:
                result.is_index = True
                self._parse_sitemap_index(root, ns, result)
            else:
                self._parse_urlset(root, ns, result, max_urls)

        except requests.RequestException as e:
            result.issues.append(f"Failed to fetch sitemap: {str(e)}")

        # Calculate score
        result.score = self._calculate_sitemap_score(result)

        return result

    def _parse_sitemap_index(self, root: ET.Element, ns: dict, result: SitemapResult):
        """Parse sitemap index file"""
        for sitemap in root.findall('.//sm:sitemap', ns):
            loc = sitemap.find('sm:loc', ns)
            if loc is not None and loc.text:
                result.child_sitemaps.append(loc.text)

        result.total_urls = len(result.child_sitemaps)

        if not result.child_sitemaps:
            result.issues.append("Sitemap index contains no child sitemaps")

    def _parse_urlset(self, root: ET.Element, ns: dict, result: SitemapResult, max_urls: int):
        """Parse URL sitemap file"""
        urls_parsed = 0

        for url_elem in root.findall('.//sm:url', ns):
            if urls_parsed >= max_urls:
                break

            loc = url_elem.find('sm:loc', ns)
            if loc is None or not loc.text:
                continue

            sitemap_url = SitemapUrl(loc=loc.text)

            # Parse optional elements
            lastmod = url_elem.find('sm:lastmod', ns)
            if lastmod is not None and lastmod.text:
                sitemap_url.lastmod = lastmod.text
                result.urls_with_lastmod += 1

                # Validate lastmod format
                if not self._is_valid_date(lastmod.text):
                    sitemap_url.issues.append("Invalid lastmod date format")

            changefreq = url_elem.find('sm:changefreq', ns)
            if changefreq is not None and changefreq.text:
                sitemap_url.changefreq = changefreq.text.lower()
                if sitemap_url.changefreq not in self.VALID_CHANGEFREQ:
                    sitemap_url.issues.append(f"Invalid changefreq: {sitemap_url.changefreq}")

            priority = url_elem.find('sm:priority', ns)
            if priority is not None and priority.text:
                try:
                    sitemap_url.priority = float(priority.text)
                    if not 0 <= sitemap_url.priority <= 1:
                        sitemap_url.issues.append("Priority must be between 0.0 and 1.0")
                except ValueError:
                    sitemap_url.issues.append(f"Invalid priority value: {priority.text}")

            result.urls.append(sitemap_url)
            urls_parsed += 1

        result.total_urls = len(result.urls)

        # Check for issues
        if result.total_urls == 0:
            result.issues.append("Sitemap contains no URLs")

        if result.total_urls > 50000:
            result.warnings.append(
                f"Sitemap has {result.total_urls} URLs. Consider splitting into multiple sitemaps (max 50,000)."
            )

        # Check lastmod coverage
        if result.total_urls > 0:
            lastmod_ratio = result.urls_with_lastmod / result.total_urls
            if lastmod_ratio < 0.5:
                result.recommendations.append(
                    f"Only {lastmod_ratio*100:.0f}% of URLs have lastmod. Consider adding lastmod for all URLs."
                )

    def _is_valid_date(self, date_str: str) -> bool:
        """Validate ISO 8601 date format"""
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # YYYY-MM-DDTHH:MM:SS
        ]
        return any(re.match(p, date_str) for p in patterns)

    def _calculate_sitemap_score(self, result: SitemapResult) -> int:
        """Calculate sitemap implementation score"""
        if not result.exists:
            return 0

        if not result.format_valid:
            return 20

        score = 60  # Base score for valid sitemap

        # URLs present (+15)
        if result.total_urls > 0:
            score += 15

        # Lastmod coverage (+15)
        if result.total_urls > 0:
            lastmod_ratio = result.urls_with_lastmod / result.total_urls
            score += int(lastmod_ratio * 15)

        # No issues (+10)
        if not result.issues:
            score += 10

        return max(0, min(100, score))

    def print_robots_result(self, result: RobotsTxtResult):
        """Print robots.txt analysis result"""
        print(f"\n{'='*60}")
        print(f"Robots.txt Analysis: {result.url}")
        print('='*60)

        # Status
        if result.exists:
            print_success(f"Status: Found (HTTP {result.status_code})")
            print(f"Size: {result.size_bytes} bytes")
        else:
            print_warning("Status: Not found")

        # Score
        if result.score >= 80:
            color = Colors.GREEN
        elif result.score >= 50:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        print(f"\nRobots.txt Score: {color}{result.score}/100{Colors.RESET}")

        # User agents
        if result.user_agents:
            print(f"\n{Colors.BOLD}User-Agents:{Colors.RESET}")
            for ua in result.user_agents:
                print(f"  • {ua}")

        # Sitemaps
        if result.sitemaps:
            print(f"\n{Colors.BOLD}Sitemaps Declared:{Colors.RESET}")
            for sitemap in result.sitemaps:
                print(f"  • {sitemap}")
        else:
            print_warning("\nNo sitemaps declared in robots.txt")

        # Critical blocks
        if result.blocks_all:
            print_error("\n⚠ CRITICAL: Blocks ALL crawlers from entire site!")
        if result.blocks_googlebot:
            print_error("\n⚠ CRITICAL: Blocks Googlebot from entire site!")

        # Issues & Warnings
        if result.issues:
            print(f"\n{Colors.RED}Issues:{Colors.RESET}")
            for issue in result.issues:
                print(f"  • {issue}")

        if result.warnings:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.RESET}")
            for warning in result.warnings:
                print(f"  • {warning}")

        if result.recommendations:
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.RESET}")
            for rec in result.recommendations:
                print(f"  → {rec}")

        print()

    def print_sitemap_result(self, result: SitemapResult):
        """Print sitemap analysis result"""
        print(f"\n{'='*60}")
        print(f"Sitemap Analysis: {result.url}")
        print('='*60)

        # Status
        if result.exists:
            sitemap_type = "Index" if result.is_index else "URL Set"
            print_success(f"Status: Found ({sitemap_type})")
            print(f"Format Valid: {'Yes' if result.format_valid else 'No'}")
        else:
            print_error("Status: Not found or error")

        # Score
        if result.score >= 80:
            color = Colors.GREEN
        elif result.score >= 50:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        print(f"\nSitemap Score: {color}{result.score}/100{Colors.RESET}")

        # Content summary
        if result.is_index:
            print(f"\n{Colors.BOLD}Child Sitemaps:{Colors.RESET} {len(result.child_sitemaps)}")
            for sitemap in result.child_sitemaps[:5]:
                print(f"  • {sitemap}")
            if len(result.child_sitemaps) > 5:
                print(f"  ... and {len(result.child_sitemaps) - 5} more")
        else:
            print(f"\n{Colors.BOLD}URLs:{Colors.RESET} {result.total_urls}")
            print(f"URLs with lastmod: {result.urls_with_lastmod} ({result.urls_with_lastmod/max(1,result.total_urls)*100:.0f}%)")

            # Sample URLs
            if result.urls:
                print(f"\n{Colors.BOLD}Sample URLs:{Colors.RESET}")
                for url in result.urls[:5]:
                    lastmod_str = f" (lastmod: {url.lastmod})" if url.lastmod else ""
                    print(f"  • {url.loc[:60]}{'...' if len(url.loc) > 60 else ''}{lastmod_str}")

        # Issues
        if result.issues:
            print(f"\n{Colors.RED}Issues:{Colors.RESET}")
            for issue in result.issues:
                print(f"  • {issue}")

        if result.warnings:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.RESET}")
            for warning in result.warnings:
                print(f"  • {warning}")

        if result.recommendations:
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.RESET}")
            for rec in result.recommendations:
                print(f"  → {rec}")

        print()
