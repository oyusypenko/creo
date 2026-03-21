#!/usr/bin/env python3
"""
Security Headers Analyzer

Checks HTTP security headers for web pages:
- Strict-Transport-Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Content-Security-Policy
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

import requests
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from ..core.utils import print_success, print_warning, print_error, print_info, Colors


class SecurityLevel(Enum):
    """Security level assessment"""
    EXCELLENT = "excellent"  # All critical headers present with good values
    GOOD = "good"           # Most headers present
    FAIR = "fair"           # Some headers missing
    POOR = "poor"           # Critical headers missing
    CRITICAL = "critical"   # No security headers


@dataclass
class SecurityHeader:
    """Individual security header result"""
    name: str
    present: bool
    value: Optional[str] = None
    recommendation: Optional[str] = None
    is_critical: bool = False


@dataclass
class SecurityAnalysisResult:
    """Complete security analysis result"""
    url: str
    https: bool
    headers: list = field(default_factory=list)
    level: SecurityLevel = SecurityLevel.POOR
    score: int = 0  # 0-100
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


class SecurityAnalyzer:
    """Analyzes HTTP security headers"""

    # Critical headers that should always be present
    CRITICAL_HEADERS = {
        'Strict-Transport-Security': {
            'description': 'HSTS - Forces HTTPS connections',
            'recommendation': 'Add: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload',
            'good_values': ['max-age=31536000', 'max-age=63072000'],
        },
        'X-Content-Type-Options': {
            'description': 'Prevents MIME type sniffing',
            'recommendation': 'Add: X-Content-Type-Options: nosniff',
            'good_values': ['nosniff'],
        },
        'X-Frame-Options': {
            'description': 'Prevents clickjacking attacks',
            'recommendation': 'Add: X-Frame-Options: DENY or SAMEORIGIN',
            'good_values': ['DENY', 'SAMEORIGIN'],
        },
    }

    # Recommended headers
    RECOMMENDED_HEADERS = {
        'Content-Security-Policy': {
            'description': 'CSP - Controls resource loading',
            'recommendation': 'Add Content-Security-Policy with appropriate directives',
            'good_values': [],  # Too complex to validate simply
        },
        'Referrer-Policy': {
            'description': 'Controls referrer information',
            'recommendation': 'Add: Referrer-Policy: strict-origin-when-cross-origin',
            'good_values': ['strict-origin-when-cross-origin', 'no-referrer', 'same-origin'],
        },
        'Permissions-Policy': {
            'description': 'Controls browser features',
            'recommendation': 'Add Permissions-Policy to restrict features like geolocation, camera',
            'good_values': [],
        },
        'X-XSS-Protection': {
            'description': 'XSS filter (legacy, but still useful)',
            'recommendation': 'Add: X-XSS-Protection: 1; mode=block',
            'good_values': ['1; mode=block'],
        },
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.0; Security Analyzer)'
        })

    def analyze_url(self, url: str) -> SecurityAnalysisResult:
        """Analyze security headers for a URL"""
        result = SecurityAnalysisResult(url=url, https=url.startswith('https://'))

        if not result.https:
            result.issues.append("Site not using HTTPS")
            result.recommendations.append("Migrate to HTTPS immediately")
            result.level = SecurityLevel.CRITICAL
            result.score = 0
            return result

        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            headers = response.headers
        except requests.RequestException as e:
            result.issues.append(f"Failed to fetch headers: {str(e)}")
            result.level = SecurityLevel.CRITICAL
            return result

        score = 0
        max_score = 0

        # Check critical headers (weighted more heavily)
        for header_name, config in self.CRITICAL_HEADERS.items():
            max_score += 20
            header_result = SecurityHeader(
                name=header_name,
                present=header_name in headers,
                is_critical=True
            )

            if header_result.present:
                header_result.value = headers[header_name]
                # Check if value is good
                if config['good_values']:
                    if any(gv in header_result.value for gv in config['good_values']):
                        score += 20
                    else:
                        score += 10  # Present but suboptimal
                        header_result.recommendation = f"Consider: {config['recommendation']}"
                else:
                    score += 15
            else:
                result.issues.append(f"Missing critical header: {header_name}")
                header_result.recommendation = config['recommendation']
                result.recommendations.append(config['recommendation'])

            result.headers.append(header_result)

        # Check recommended headers
        for header_name, config in self.RECOMMENDED_HEADERS.items():
            max_score += 10
            header_result = SecurityHeader(
                name=header_name,
                present=header_name in headers,
                is_critical=False
            )

            if header_result.present:
                header_result.value = headers[header_name]
                if config['good_values']:
                    if any(gv in header_result.value for gv in config['good_values']):
                        score += 10
                    else:
                        score += 5
                else:
                    score += 8
            else:
                header_result.recommendation = config['recommendation']
                if header_name == 'Content-Security-Policy':
                    result.issues.append(f"Missing recommended header: {header_name}")
                    result.recommendations.append(config['recommendation'])

            result.headers.append(header_result)

        # Calculate final score (0-100)
        result.score = int((score / max_score) * 100) if max_score > 0 else 0

        # Determine security level
        if result.score >= 90:
            result.level = SecurityLevel.EXCELLENT
        elif result.score >= 70:
            result.level = SecurityLevel.GOOD
        elif result.score >= 50:
            result.level = SecurityLevel.FAIR
        elif result.score >= 30:
            result.level = SecurityLevel.POOR
        else:
            result.level = SecurityLevel.CRITICAL

        return result

    def print_result(self, result: SecurityAnalysisResult):
        """Print security analysis result"""
        print(f"\n{'='*60}")
        print(f"Security Analysis: {result.url}")
        print('='*60)

        # HTTPS status
        if result.https:
            print_success("HTTPS: Enabled")
        else:
            print_error("HTTPS: NOT ENABLED - CRITICAL SECURITY ISSUE")

        # Score and level
        level_colors = {
            SecurityLevel.EXCELLENT: Colors.GREEN,
            SecurityLevel.GOOD: Colors.GREEN,
            SecurityLevel.FAIR: Colors.YELLOW,
            SecurityLevel.POOR: Colors.RED,
            SecurityLevel.CRITICAL: Colors.RED,
        }
        color = level_colors.get(result.level, Colors.WHITE)
        print(f"\nSecurity Score: {color}{result.score}/100 ({result.level.value.upper()}){Colors.RESET}")

        # Headers table
        print(f"\n{Colors.BOLD}Security Headers:{Colors.RESET}")
        print("-" * 50)

        for header in result.headers:
            status = "✓" if header.present else "✗"
            color = Colors.GREEN if header.present else Colors.RED
            critical = " [CRITICAL]" if header.is_critical and not header.present else ""

            print(f"{color}{status}{Colors.RESET} {header.name}{critical}")
            if header.value:
                # Truncate long values
                value = header.value[:60] + "..." if len(header.value) > 60 else header.value
                print(f"  Value: {value}")

        # Issues
        if result.issues:
            print(f"\n{Colors.RED}Issues Found:{Colors.RESET}")
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
