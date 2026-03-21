#!/usr/bin/env python3
"""
Mobile SEO Analyzer

Analyzes mobile-specific SEO issues:
- Viewport configuration
- Touch target sizes
- Font sizes
- Mobile-friendly features
- Responsive design indicators
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from ..core.utils import print_header, print_success, print_warning, print_error, Colors


@dataclass
class ViewportAnalysis:
    """Viewport meta tag analysis"""
    has_viewport: bool = False
    viewport_content: str = ''
    has_width_device: bool = False
    has_initial_scale: bool = False
    has_user_scalable: bool = False
    user_scalable_disabled: bool = False
    has_maximum_scale: bool = False
    maximum_scale_restrictive: bool = False
    issues: List[str] = field(default_factory=list)


@dataclass
class TouchTargetAnalysis:
    """Touch target (buttons, links) analysis"""
    total_interactive: int = 0
    small_targets: int = 0
    small_target_elements: List[Dict] = field(default_factory=list)
    close_targets: int = 0  # Too close together


@dataclass
class FontAnalysis:
    """Font size analysis for mobile"""
    has_font_size_adjust: bool = False
    uses_relative_units: bool = True
    small_font_detected: bool = False
    small_font_elements: List[Dict] = field(default_factory=list)
    base_font_size: str = ''


@dataclass
class ResponsiveAnalysis:
    """Responsive design indicators"""
    has_media_queries: bool = False
    has_responsive_images: bool = False
    has_srcset: bool = False
    has_picture_element: bool = False
    has_mobile_stylesheet: bool = False
    uses_flexbox: bool = False
    uses_grid: bool = False


@dataclass
class MobileFeatures:
    """Mobile-specific features"""
    has_apple_touch_icon: bool = False
    has_theme_color: bool = False
    has_manifest: bool = False
    has_mobile_app_links: bool = False
    apple_app_id: str = ''
    google_play_id: str = ''
    has_tap_highlight_disabled: bool = False


@dataclass
class MobileAnalysisResult:
    """Complete mobile analysis result"""
    url: str
    viewport: ViewportAnalysis = field(default_factory=ViewportAnalysis)
    touch_targets: TouchTargetAnalysis = field(default_factory=TouchTargetAnalysis)
    fonts: FontAnalysis = field(default_factory=FontAnalysis)
    responsive: ResponsiveAnalysis = field(default_factory=ResponsiveAnalysis)
    features: MobileFeatures = field(default_factory=MobileFeatures)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: int = 0


class MobileAnalyzer:
    """Analyzes mobile SEO factors"""

    # Minimum touch target size (Google recommendation: 48x48px, Apple: 44x44px)
    MIN_TOUCH_TARGET = 44

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
                         'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        })

    def analyze_url(self, url: str) -> MobileAnalysisResult:
        """Analyze mobile-friendliness of a URL"""
        result = MobileAnalysisResult(url=url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result.issues.append(f"Failed to fetch: HTTP {response.status_code}")
                return result

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # Analyze viewport
            result.viewport = self._analyze_viewport(soup)

            # Analyze touch targets
            result.touch_targets = self._analyze_touch_targets(soup)

            # Analyze fonts
            result.fonts = self._analyze_fonts(soup, html)

            # Analyze responsive features
            result.responsive = self._analyze_responsive(soup, html)

            # Analyze mobile features
            result.features = self._analyze_features(soup)

            # Generate issues and recommendations
            self._generate_issues(result)

            # Calculate score
            result.score = self._calculate_score(result)

        except requests.RequestException as e:
            result.issues.append(f"Request failed: {str(e)}")

        return result

    def _analyze_viewport(self, soup: BeautifulSoup) -> ViewportAnalysis:
        """Analyze viewport meta tag"""
        viewport = ViewportAnalysis()

        meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
        if not meta_viewport:
            viewport.issues.append("Missing viewport meta tag")
            return viewport

        viewport.has_viewport = True
        content = meta_viewport.get('content', '')
        viewport.viewport_content = content

        # Parse viewport directives
        directives = {}
        for part in content.split(','):
            if '=' in part:
                key, value = part.split('=', 1)
                directives[key.strip().lower()] = value.strip().lower()

        # Check width
        if 'width' in directives:
            if directives['width'] == 'device-width':
                viewport.has_width_device = True
            else:
                viewport.issues.append(f"Viewport width set to fixed value: {directives['width']}")

        # Check initial-scale
        if 'initial-scale' in directives:
            viewport.has_initial_scale = True

        # Check user-scalable
        if 'user-scalable' in directives:
            viewport.has_user_scalable = True
            if directives['user-scalable'] in ('no', '0'):
                viewport.user_scalable_disabled = True
                viewport.issues.append("Pinch-to-zoom disabled (user-scalable=no)")

        # Check maximum-scale
        if 'maximum-scale' in directives:
            viewport.has_maximum_scale = True
            try:
                max_scale = float(directives['maximum-scale'])
                if max_scale < 2.0:
                    viewport.maximum_scale_restrictive = True
                    viewport.issues.append(f"Maximum scale too restrictive: {max_scale}")
            except:
                pass

        return viewport

    def _analyze_touch_targets(self, soup: BeautifulSoup) -> TouchTargetAnalysis:
        """Analyze touch target sizes"""
        analysis = TouchTargetAnalysis()

        # Find all interactive elements
        interactive_elements = (
            soup.find_all('a', href=True) +
            soup.find_all('button') +
            soup.find_all('input', type=['submit', 'button', 'checkbox', 'radio']) +
            soup.find_all(['select'])
        )

        analysis.total_interactive = len(interactive_elements)

        # Check for inline styles with small sizes
        for el in interactive_elements:
            style = el.get('style', '')
            classes = el.get('class', [])

            # Check inline styles for small sizes
            width_match = re.search(r'width:\s*(\d+)px', style)
            height_match = re.search(r'height:\s*(\d+)px', style)

            is_small = False
            if width_match and int(width_match.group(1)) < self.MIN_TOUCH_TARGET:
                is_small = True
            if height_match and int(height_match.group(1)) < self.MIN_TOUCH_TARGET:
                is_small = True

            # Check for icon-only buttons (likely small)
            text = el.get_text(strip=True)
            if len(text) <= 2 and not el.find('img'):
                # Single character or icon button, might be small
                pass

            if is_small:
                analysis.small_targets += 1
                analysis.small_target_elements.append({
                    'tag': el.name,
                    'text': text[:30] if text else '',
                    'style': style[:50] if style else ''
                })

        return analysis

    def _analyze_fonts(self, soup: BeautifulSoup, html: str) -> FontAnalysis:
        """Analyze font sizes for mobile readability"""
        analysis = FontAnalysis()

        # Check for font-size-adjust
        if 'font-size-adjust' in html:
            analysis.has_font_size_adjust = True

        # Check for relative units in styles
        style_tags = soup.find_all('style')
        inline_styles = [el.get('style', '') for el in soup.find_all(style=True)]

        all_styles = '\n'.join([s.string or '' for s in style_tags] + inline_styles)

        # Check for px-based font sizes
        px_fonts = re.findall(r'font-size:\s*(\d+)px', all_styles)
        for size in px_fonts:
            if int(size) < 14:
                analysis.small_font_detected = True
                analysis.small_font_elements.append({'size': f'{size}px'})

        # Check for relative units
        if 'rem' in all_styles or 'em' in all_styles or '%' in all_styles:
            analysis.uses_relative_units = True

        # Check base font size in html/body
        html_style = soup.find('html')
        if html_style:
            style = html_style.get('style', '')
            font_match = re.search(r'font-size:\s*([^;]+)', style)
            if font_match:
                analysis.base_font_size = font_match.group(1)

        return analysis

    def _analyze_responsive(self, soup: BeautifulSoup, html: str) -> ResponsiveAnalysis:
        """Analyze responsive design features"""
        analysis = ResponsiveAnalysis()

        # Check for media queries in styles
        if '@media' in html:
            analysis.has_media_queries = True

        # Check for responsive images
        imgs = soup.find_all('img')
        for img in imgs:
            if img.get('srcset'):
                analysis.has_srcset = True
                analysis.has_responsive_images = True
                break

        # Check for picture elements
        if soup.find('picture'):
            analysis.has_picture_element = True
            analysis.has_responsive_images = True

        # Check for mobile stylesheet
        for link in soup.find_all('link', rel='stylesheet'):
            media = link.get('media', '')
            if 'handheld' in media or 'max-width' in media:
                analysis.has_mobile_stylesheet = True

        # Check for flexbox/grid
        if 'display: flex' in html or 'display:flex' in html:
            analysis.uses_flexbox = True
        if 'display: grid' in html or 'display:grid' in html:
            analysis.uses_grid = True

        return analysis

    def _analyze_features(self, soup: BeautifulSoup) -> MobileFeatures:
        """Analyze mobile-specific features"""
        features = MobileFeatures()

        # Apple touch icon
        if soup.find('link', rel=re.compile('apple-touch-icon')):
            features.has_apple_touch_icon = True

        # Theme color
        if soup.find('meta', attrs={'name': 'theme-color'}):
            features.has_theme_color = True

        # Web app manifest
        if soup.find('link', rel='manifest'):
            features.has_manifest = True

        # iOS app link
        ios_app = soup.find('meta', attrs={'name': 'apple-itunes-app'})
        if ios_app:
            features.has_mobile_app_links = True
            content = ios_app.get('content', '')
            id_match = re.search(r'app-id=(\d+)', content)
            if id_match:
                features.apple_app_id = id_match.group(1)

        # Android app link
        android_link = soup.find('link', rel='alternate', href=re.compile(r'android-app://'))
        if android_link:
            features.has_mobile_app_links = True

        # Tap highlight disabled
        style_content = ''.join([s.string or '' for s in soup.find_all('style')])
        if '-webkit-tap-highlight-color' in style_content:
            features.has_tap_highlight_disabled = True

        return features

    def _generate_issues(self, result: MobileAnalysisResult):
        """Generate issues and recommendations"""

        # Viewport issues
        if not result.viewport.has_viewport:
            result.issues.append("Missing viewport meta tag")
            result.recommendations.append(
                "Add: <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            )
        else:
            if not result.viewport.has_width_device:
                result.issues.append("Viewport width not set to device-width")
            if result.viewport.user_scalable_disabled:
                result.issues.append("Pinch-to-zoom is disabled (accessibility issue)")
                result.recommendations.append("Remove user-scalable=no to allow zooming")
            if result.viewport.maximum_scale_restrictive:
                result.issues.append("Maximum scale is too restrictive")

        # Viewport issues from analysis
        result.issues.extend(result.viewport.issues)

        # Touch target issues
        if result.touch_targets.small_targets > 0:
            result.issues.append(
                f"{result.touch_targets.small_targets} touch targets may be too small (<{self.MIN_TOUCH_TARGET}px)"
            )
            result.recommendations.append(
                f"Ensure touch targets are at least {self.MIN_TOUCH_TARGET}x{self.MIN_TOUCH_TARGET}px"
            )

        # Font issues
        if result.fonts.small_font_detected:
            result.issues.append("Small font sizes detected (<14px)")
            result.recommendations.append("Use minimum 16px font size for body text on mobile")

        # Responsive issues
        if not result.responsive.has_media_queries:
            result.issues.append("No media queries detected")
            result.recommendations.append("Add responsive breakpoints for mobile devices")

        if not result.responsive.has_responsive_images:
            result.recommendations.append("Consider using srcset for responsive images")

        # Feature recommendations
        if not result.features.has_apple_touch_icon:
            result.recommendations.append("Add apple-touch-icon for iOS home screen")

        if not result.features.has_theme_color:
            result.recommendations.append("Add theme-color meta tag for mobile browsers")

        if not result.features.has_manifest:
            result.recommendations.append("Consider adding a web app manifest for PWA support")

    def _calculate_score(self, result: MobileAnalysisResult) -> int:
        """Calculate mobile-friendliness score"""
        score = 100

        # Viewport (30 points)
        if not result.viewport.has_viewport:
            score -= 30
        else:
            if not result.viewport.has_width_device:
                score -= 15
            if result.viewport.user_scalable_disabled:
                score -= 10
            if result.viewport.maximum_scale_restrictive:
                score -= 5

        # Touch targets (25 points)
        if result.touch_targets.small_targets > 5:
            score -= 15
        elif result.touch_targets.small_targets > 0:
            score -= 8

        # Fonts (15 points)
        if result.fonts.small_font_detected:
            score -= 15

        # Responsive (20 points)
        if not result.responsive.has_media_queries:
            score -= 15
        if not result.responsive.has_responsive_images:
            score -= 5

        # Features (10 points)
        if not result.features.has_apple_touch_icon:
            score -= 3
        if not result.features.has_theme_color:
            score -= 2
        if not result.features.has_manifest:
            score -= 5

        return max(0, min(100, score))

    def print_result(self, result: MobileAnalysisResult):
        """Print mobile analysis result"""
        print_header(f"Mobile Analysis: {result.url}")

        # Score
        score_color = Colors.GREEN if result.score >= 80 else Colors.YELLOW if result.score >= 50 else Colors.RED
        print(f"\nMobile Score: {score_color}{result.score}/100{Colors.RESET}")

        # Viewport
        v = result.viewport
        print(f"\n{Colors.BOLD}Viewport:{Colors.RESET}")
        status = "✓" if v.has_viewport else "✗"
        color = Colors.GREEN if v.has_viewport else Colors.RED
        print(f"  {color}{status}{Colors.RESET} Viewport meta tag")

        if v.has_viewport:
            print(f"      Content: {v.viewport_content[:60]}")
            print(f"      width=device-width: {'✓' if v.has_width_device else '✗'}")
            print(f"      initial-scale: {'✓' if v.has_initial_scale else '✗'}")

            if v.user_scalable_disabled:
                print(f"      {Colors.RED}⚠ Zoom disabled{Colors.RESET}")

        # Touch targets
        t = result.touch_targets
        print(f"\n{Colors.BOLD}Touch Targets:{Colors.RESET}")
        print(f"  Interactive elements: {t.total_interactive}")
        if t.small_targets > 0:
            print(f"  {Colors.YELLOW}⚠ Small targets: {t.small_targets}{Colors.RESET}")

        # Responsive
        r = result.responsive
        print(f"\n{Colors.BOLD}Responsive Design:{Colors.RESET}")
        print(f"  Media queries: {'✓' if r.has_media_queries else '✗'}")
        print(f"  Responsive images: {'✓' if r.has_responsive_images else '✗'}")
        print(f"  Flexbox: {'✓' if r.uses_flexbox else '—'}")
        print(f"  CSS Grid: {'✓' if r.uses_grid else '—'}")

        # Mobile features
        f = result.features
        print(f"\n{Colors.BOLD}Mobile Features:{Colors.RESET}")
        print(f"  Apple touch icon: {'✓' if f.has_apple_touch_icon else '✗'}")
        print(f"  Theme color: {'✓' if f.has_theme_color else '✗'}")
        print(f"  Web manifest: {'✓' if f.has_manifest else '✗'}")
        if f.has_mobile_app_links:
            print(f"  App links: ✓")

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

    def analyze_batch(self, urls: List[str]) -> List[MobileAnalysisResult]:
        """Analyze multiple URLs"""
        results = []
        for url in urls:
            result = self.analyze_url(url)
            results.append(result)
            self.print_result(result)
        return results
