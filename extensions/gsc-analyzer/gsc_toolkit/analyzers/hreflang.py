#!/usr/bin/env python3
"""
Hreflang Analyzer

Validates international SEO hreflang implementation:
- Tag syntax validation
- Self-referential link check
- Return link validation
- x-default implementation
- Language/region code validation
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from ..core.utils import print_success, print_warning, print_error, print_info, Colors


# Valid ISO 639-1 language codes (common ones)
VALID_LANGUAGE_CODES = {
    'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh', 'ko', 'ar', 'hi',
    'nl', 'pl', 'tr', 'vi', 'th', 'id', 'ms', 'sv', 'no', 'da', 'fi', 'cs',
    'el', 'he', 'hu', 'ro', 'sk', 'uk', 'bg', 'hr', 'sr', 'sl', 'et', 'lv',
    'lt', 'ca', 'eu', 'gl', 'cy', 'ga', 'mt', 'is', 'mk', 'sq', 'bs', 'af',
    'sw', 'zu', 'xh', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'ur',
    'fa', 'ps', 'ne', 'si', 'my', 'km', 'lo', 'ka', 'am', 'ti', 'om', 'so',
    'fil', 'tl', 'haw', 'sm', 'to', 'mi', 'hy', 'az', 'be', 'kk', 'ky', 'mn',
    'tg', 'tk', 'uz', 'tt', 'ug', 'bo', 'dz', 'jv', 'su', 'ceb', 'hmn', 'ht'
}

# Valid ISO 3166-1 alpha-2 country codes (common ones)
VALID_COUNTRY_CODES = {
    'US', 'GB', 'CA', 'AU', 'NZ', 'IE', 'ZA', 'IN', 'PK', 'BD', 'NG', 'KE',
    'GH', 'PH', 'SG', 'MY', 'HK', 'TW', 'JP', 'KR', 'CN', 'TH', 'VN', 'ID',
    'BR', 'PT', 'MX', 'ES', 'AR', 'CO', 'CL', 'PE', 'VE', 'EC', 'BO', 'PY',
    'UY', 'CR', 'PA', 'DO', 'CU', 'GT', 'HN', 'NI', 'SV', 'PR', 'FR', 'BE',
    'CH', 'LU', 'MC', 'DE', 'AT', 'LI', 'IT', 'SM', 'VA', 'MT', 'NL', 'PL',
    'CZ', 'SK', 'HU', 'RO', 'BG', 'RS', 'HR', 'SI', 'BA', 'MK', 'ME', 'AL',
    'GR', 'CY', 'TR', 'RU', 'UA', 'BY', 'MD', 'GE', 'AM', 'AZ', 'KZ', 'UZ',
    'TM', 'KG', 'TJ', 'MN', 'SE', 'NO', 'DK', 'FI', 'IS', 'EE', 'LV', 'LT',
    'IL', 'PS', 'JO', 'LB', 'SY', 'IQ', 'IR', 'SA', 'AE', 'QA', 'KW', 'BH',
    'OM', 'YE', 'EG', 'LY', 'TN', 'DZ', 'MA', 'ZW', 'TZ', 'UG', 'RW', 'ET'
}


@dataclass
class HreflangTag:
    """Individual hreflang tag"""
    hreflang: str
    href: str
    language: Optional[str] = None
    region: Optional[str] = None
    is_valid: bool = True
    is_self_referential: bool = False
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class HreflangAnalysisResult:
    """Complete hreflang analysis result"""
    url: str
    tags: list = field(default_factory=list)
    has_x_default: bool = False
    x_default_url: Optional[str] = None
    has_self_reference: bool = False
    total_tags: int = 0
    valid_tags: int = 0
    invalid_tags: int = 0
    languages_found: list = field(default_factory=list)
    regions_found: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    score: int = 0  # 0-100
    return_links_checked: int = 0
    return_links_valid: int = 0


class HreflangAnalyzer:
    """Analyzes hreflang implementation"""

    def __init__(self, timeout: int = 10, check_return_links: bool = True):
        self.timeout = timeout
        self.check_return_links = check_return_links
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.0; Hreflang Analyzer)'
        })

    def analyze_url(self, url: str) -> HreflangAnalysisResult:
        """Analyze hreflang implementation on a page"""
        result = HreflangAnalysisResult(url=url)
        normalized_url = self._normalize_url(url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result.issues.append(f"Failed to fetch page: HTTP {response.status_code}")
                return result

            soup = BeautifulSoup(response.text, 'html.parser')

            # Also check HTTP headers for hreflang
            link_header = response.headers.get('Link', '')

        except requests.RequestException as e:
            result.issues.append(f"Failed to fetch page: {str(e)}")
            return result

        # Extract hreflang from <link> tags
        for link in soup.find_all('link', rel='alternate'):
            hreflang = link.get('hreflang')
            href = link.get('href')

            if hreflang and href:
                tag = self._validate_hreflang_tag(hreflang, href, normalized_url)
                result.tags.append(tag)

                if tag.hreflang == 'x-default':
                    result.has_x_default = True
                    result.x_default_url = href

                if tag.is_self_referential:
                    result.has_self_reference = True

                if tag.language and tag.language not in result.languages_found:
                    result.languages_found.append(tag.language)

                if tag.region and tag.region not in result.regions_found:
                    result.regions_found.append(tag.region)

        # Parse HTTP Link header for hreflang
        if link_header:
            header_tags = self._parse_link_header(link_header, normalized_url)
            result.tags.extend(header_tags)

        # Calculate stats
        result.total_tags = len(result.tags)
        result.valid_tags = sum(1 for t in result.tags if t.is_valid)
        result.invalid_tags = result.total_tags - result.valid_tags

        # Check for common issues
        if result.total_tags > 0:
            if not result.has_self_reference:
                result.issues.append("Missing self-referential hreflang tag")
                result.recommendations.append(
                    f"Add: <link rel=\"alternate\" hreflang=\"...\" href=\"{url}\">"
                )

            if not result.has_x_default:
                result.recommendations.append(
                    "Consider adding x-default hreflang for users outside targeted regions"
                )

            # Check return links (if enabled)
            if self.check_return_links and result.total_tags <= 10:
                self._check_return_links(result, normalized_url)

        else:
            # No hreflang found
            result.recommendations.append(
                "No hreflang tags found. If this is a multilingual site, add hreflang tags."
            )

        # Calculate score
        result.score = self._calculate_score(result)

        return result

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        # Remove trailing slash for comparison
        return url.rstrip('/')

    def _validate_hreflang_tag(self, hreflang: str, href: str, current_url: str) -> HreflangTag:
        """Validate a single hreflang tag"""
        tag = HreflangTag(hreflang=hreflang, href=href)

        # Check if self-referential
        normalized_href = self._normalize_url(href)
        if normalized_href == current_url:
            tag.is_self_referential = True

        # Handle x-default
        if hreflang == 'x-default':
            return tag

        # Parse language-region
        parts = hreflang.lower().split('-')
        tag.language = parts[0]

        if len(parts) > 1:
            tag.region = parts[1].upper()

        # Validate language code
        if tag.language not in VALID_LANGUAGE_CODES:
            tag.errors.append(f"Invalid language code: {tag.language}")
            tag.is_valid = False

        # Validate region code (if present)
        if tag.region and tag.region not in VALID_COUNTRY_CODES:
            # Could be a script code (like zh-Hans), which is valid
            if len(tag.region) != 4:  # Script codes are 4 chars
                tag.warnings.append(f"Unknown region code: {tag.region}")

        # Validate URL
        if not href.startswith(('http://', 'https://', '/')):
            tag.errors.append("href should be an absolute URL")
            tag.is_valid = False

        return tag

    def _parse_link_header(self, header: str, current_url: str) -> list:
        """Parse Link HTTP header for hreflang"""
        tags = []
        # Pattern: <url>; rel="alternate"; hreflang="xx"
        pattern = r'<([^>]+)>;\s*rel="alternate";\s*hreflang="([^"]+)"'

        for match in re.finditer(pattern, header):
            href, hreflang = match.groups()
            tag = self._validate_hreflang_tag(hreflang, href, current_url)
            tags.append(tag)

        return tags

    def _check_return_links(self, result: HreflangAnalysisResult, current_url: str):
        """Check if alternate pages link back to this page"""
        for tag in result.tags:
            if tag.is_self_referential or tag.hreflang == 'x-default':
                continue

            result.return_links_checked += 1

            try:
                response = self.session.get(tag.href, timeout=self.timeout)
                if response.status_code != 200:
                    tag.warnings.append(f"Alternate page returned HTTP {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')

                # Check if it links back
                found_return = False
                for link in soup.find_all('link', rel='alternate'):
                    href = link.get('href', '')
                    if self._normalize_url(href) == current_url:
                        found_return = True
                        result.return_links_valid += 1
                        break

                if not found_return:
                    tag.warnings.append(f"Missing return link from {tag.href}")
                    result.issues.append(
                        f"Alternate page {tag.hreflang} doesn't link back to this page"
                    )

            except requests.RequestException:
                tag.warnings.append(f"Could not verify return link: {tag.href}")

    def _calculate_score(self, result: HreflangAnalysisResult) -> int:
        """Calculate hreflang implementation score"""
        if result.total_tags == 0:
            return 0  # No hreflang = no score

        score = 0
        max_score = 100

        # Valid tags (40 points)
        if result.total_tags > 0:
            validity_ratio = result.valid_tags / result.total_tags
            score += int(validity_ratio * 40)

        # Self-reference (20 points)
        if result.has_self_reference:
            score += 20

        # x-default (15 points)
        if result.has_x_default:
            score += 15

        # Return links (25 points)
        if result.return_links_checked > 0:
            return_ratio = result.return_links_valid / result.return_links_checked
            score += int(return_ratio * 25)
        elif result.total_tags == 1 and result.has_self_reference:
            # Only self-reference, return links not applicable
            score += 25

        return min(score, max_score)

    def print_result(self, result: HreflangAnalysisResult):
        """Print hreflang analysis result"""
        print(f"\n{'='*60}")
        print(f"Hreflang Analysis: {result.url}")
        print('='*60)

        # Score
        if result.score >= 80:
            color = Colors.GREEN
        elif result.score >= 50:
            color = Colors.YELLOW
        else:
            color = Colors.RED

        if result.total_tags == 0:
            print(f"\nNo hreflang tags found")
        else:
            print(f"\nHreflang Score: {color}{result.score}/100{Colors.RESET}")
            print(f"Total Tags: {result.total_tags} (Valid: {result.valid_tags}, Invalid: {result.invalid_tags})")

        # Key indicators
        print(f"\n{Colors.BOLD}Implementation Status:{Colors.RESET}")
        self_status = "✓" if result.has_self_reference else "✗"
        self_color = Colors.GREEN if result.has_self_reference else Colors.RED
        print(f"  {self_color}{self_status}{Colors.RESET} Self-referential tag")

        xdef_status = "✓" if result.has_x_default else "⚠"
        xdef_color = Colors.GREEN if result.has_x_default else Colors.YELLOW
        print(f"  {xdef_color}{xdef_status}{Colors.RESET} x-default tag")

        if result.return_links_checked > 0:
            ret_status = "✓" if result.return_links_valid == result.return_links_checked else "⚠"
            ret_color = Colors.GREEN if result.return_links_valid == result.return_links_checked else Colors.YELLOW
            print(f"  {ret_color}{ret_status}{Colors.RESET} Return links: {result.return_links_valid}/{result.return_links_checked}")

        # Languages and regions
        if result.languages_found:
            print(f"\nLanguages: {', '.join(sorted(result.languages_found))}")
        if result.regions_found:
            print(f"Regions: {', '.join(sorted(result.regions_found))}")

        # Tags detail
        if result.tags:
            print(f"\n{Colors.BOLD}Hreflang Tags:{Colors.RESET}")
            for tag in result.tags:
                status = "✓" if tag.is_valid else "✗"
                color = Colors.GREEN if tag.is_valid else Colors.RED
                self_mark = " [SELF]" if tag.is_self_referential else ""
                xdef_mark = " [DEFAULT]" if tag.hreflang == 'x-default' else ""

                print(f"  {color}{status}{Colors.RESET} {tag.hreflang}{self_mark}{xdef_mark}")
                print(f"    → {tag.href[:60]}{'...' if len(tag.href) > 60 else ''}")

                for error in tag.errors:
                    print(f"      {Colors.RED}ERROR: {error}{Colors.RESET}")
                for warning in tag.warnings:
                    print(f"      {Colors.YELLOW}WARN: {warning}{Colors.RESET}")

        # Issues
        if result.issues:
            print(f"\n{Colors.RED}Issues:{Colors.RESET}")
            for issue in result.issues:
                print(f"  • {issue}")

        # Recommendations
        if result.recommendations:
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.RESET}")
            for rec in result.recommendations:
                print(f"  → {rec}")

        print()

    def analyze_batch(self, urls: list) -> list:
        """Analyze multiple URLs"""
        results = []
        for url in urls:
            print_info(f"Analyzing: {url}")
            result = self.analyze_url(url)
            results.append(result)
            self.print_result(result)
        return results
