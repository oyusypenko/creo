#!/usr/bin/env python3
"""
Performance Analyzer

Analyzes page performance factors:
- CSS/JS render-blocking resources
- Image optimization (format, lazy loading, srcset)
- Resource loading (async/defer)
- Caching headers
- Compression
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from ..core.utils import print_header, print_success, print_warning, Colors


@dataclass
class ResourceInfo:
    """Information about a resource"""
    url: str
    resource_type: str  # css, js, image, font
    size_bytes: int = 0
    is_external: bool = False
    is_render_blocking: bool = False
    has_async: bool = False
    has_defer: bool = False
    in_head: bool = False
    load_time_ms: float = 0.0


@dataclass
class CSSAnalysis:
    """CSS resource analysis"""
    total_stylesheets: int = 0
    external_stylesheets: int = 0
    inline_styles: int = 0
    render_blocking: int = 0
    total_size_bytes: int = 0
    has_critical_css: bool = False
    stylesheets: List[ResourceInfo] = field(default_factory=list)


@dataclass
class JSAnalysis:
    """JavaScript resource analysis"""
    total_scripts: int = 0
    external_scripts: int = 0
    inline_scripts: int = 0
    render_blocking: int = 0
    async_scripts: int = 0
    defer_scripts: int = 0
    module_scripts: int = 0
    total_size_bytes: int = 0
    scripts: List[ResourceInfo] = field(default_factory=list)


@dataclass
class ImageAnalysis:
    """Image optimization analysis"""
    total_images: int = 0
    images_with_alt: int = 0
    images_without_alt: int = 0
    images_with_dimensions: int = 0
    images_with_lazy: int = 0
    images_with_srcset: int = 0
    modern_formats: int = 0  # webp, avif
    legacy_formats: int = 0  # jpg, png, gif
    large_images: List[Dict] = field(default_factory=list)
    missing_dimensions: List[str] = field(default_factory=list)
    format_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class CachingAnalysis:
    """HTTP caching analysis"""
    has_cache_control: bool = False
    cache_control_value: str = ''
    has_etag: bool = False
    has_last_modified: bool = False
    has_expires: bool = False
    max_age_seconds: int = 0
    is_cacheable: bool = False
    caching_score: int = 0


@dataclass
class CompressionAnalysis:
    """Compression analysis"""
    has_gzip: bool = False
    has_brotli: bool = False
    content_encoding: str = ''
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0


@dataclass
class PerformanceResult:
    """Complete performance analysis result"""
    url: str
    css: CSSAnalysis = field(default_factory=CSSAnalysis)
    js: JSAnalysis = field(default_factory=JSAnalysis)
    images: ImageAnalysis = field(default_factory=ImageAnalysis)
    caching: CachingAnalysis = field(default_factory=CachingAnalysis)
    compression: CompressionAnalysis = field(default_factory=CompressionAnalysis)

    # Timing
    ttfb_ms: float = 0.0  # Time to first byte
    total_size_bytes: int = 0

    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: int = 0


class PerformanceAnalyzer:
    """Analyzes page performance factors"""

    # Large image threshold (100KB)
    LARGE_IMAGE_BYTES = 100 * 1024

    def __init__(self, timeout: int = 10, check_resources: bool = False):
        self.timeout = timeout
        self.check_resources = check_resources  # Whether to fetch each resource
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.2; Performance Analyzer)',
            'Accept-Encoding': 'gzip, deflate, br'
        })

    def analyze_url(self, url: str) -> PerformanceResult:
        """Analyze page performance"""
        result = PerformanceResult(url=url)
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        try:
            # Fetch main page
            response = self.session.get(url, timeout=self.timeout)

            # Calculate TTFB
            if hasattr(response, 'elapsed'):
                result.ttfb_ms = response.elapsed.total_seconds() * 1000

            result.total_size_bytes = len(response.content)

            if response.status_code != 200:
                result.issues.append(f"Failed to fetch: HTTP {response.status_code}")
                return result

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            head = soup.find('head')

            # Analyze CSS
            result.css = self._analyze_css(soup, head, base_url)

            # Analyze JavaScript
            result.js = self._analyze_js(soup, head, base_url)

            # Analyze images
            result.images = self._analyze_images(soup, base_url)

            # Analyze caching
            result.caching = self._analyze_caching(response)

            # Analyze compression
            result.compression = self._analyze_compression(response)

            # Generate issues and recommendations
            self._generate_issues(result)

            # Calculate score
            result.score = self._calculate_score(result)

        except requests.RequestException as e:
            result.issues.append(f"Request failed: {str(e)}")

        return result

    def _analyze_css(self, soup: BeautifulSoup, head, base_url: str) -> CSSAnalysis:
        """Analyze CSS resources"""
        analysis = CSSAnalysis()

        # Find all stylesheet links
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if not href:
                continue

            analysis.total_stylesheets += 1

            resource = ResourceInfo(
                url=urljoin(base_url, href),
                resource_type='css',
                is_external=href.startswith(('http://', 'https://', '//')),
                in_head=link.find_parent('head') is not None
            )

            # Check if render-blocking (in head without media query or preload)
            media = link.get('media', 'all')
            is_preload = link.get('rel') == 'preload'

            if resource.in_head and media == 'all' and not is_preload:
                resource.is_render_blocking = True
                analysis.render_blocking += 1

            if resource.is_external:
                analysis.external_stylesheets += 1

            analysis.stylesheets.append(resource)

        # Count inline styles
        analysis.inline_styles = len(soup.find_all('style'))

        # Check for critical CSS indicator
        for style in soup.find_all('style'):
            style_text = style.string or ''
            if len(style_text) > 500 and len(style_text) < 15000:
                # Likely critical CSS inlined
                analysis.has_critical_css = True
                break

        return analysis

    def _analyze_js(self, soup: BeautifulSoup, head, base_url: str) -> JSAnalysis:
        """Analyze JavaScript resources"""
        analysis = JSAnalysis()

        for script in soup.find_all('script'):
            src = script.get('src')

            if src:
                # External script
                analysis.total_scripts += 1
                analysis.external_scripts += 1

                resource = ResourceInfo(
                    url=urljoin(base_url, src),
                    resource_type='js',
                    is_external=True,
                    in_head=script.find_parent('head') is not None,
                    has_async=script.has_attr('async'),
                    has_defer=script.has_attr('defer')
                )

                # Check type
                script_type = script.get('type', '')
                if script_type == 'module':
                    analysis.module_scripts += 1

                # Check if render-blocking
                if resource.in_head and not resource.has_async and not resource.has_defer:
                    resource.is_render_blocking = True
                    analysis.render_blocking += 1

                if resource.has_async:
                    analysis.async_scripts += 1
                if resource.has_defer:
                    analysis.defer_scripts += 1

                analysis.scripts.append(resource)
            else:
                # Inline script
                if script.string and len(script.string.strip()) > 0:
                    analysis.inline_scripts += 1
                    analysis.total_scripts += 1

        return analysis

    def _analyze_images(self, soup: BeautifulSoup, base_url: str) -> ImageAnalysis:
        """Analyze image optimization"""
        analysis = ImageAnalysis()

        for img in soup.find_all('img'):
            analysis.total_images += 1
            src = img.get('src', '')

            # Alt text
            if img.get('alt'):
                analysis.images_with_alt += 1
            else:
                analysis.images_without_alt += 1

            # Dimensions
            if img.get('width') and img.get('height'):
                analysis.images_with_dimensions += 1
            else:
                if src:
                    analysis.missing_dimensions.append(src[:80])

            # Lazy loading
            loading = img.get('loading', '')
            if loading == 'lazy':
                analysis.images_with_lazy += 1

            # Srcset (responsive)
            if img.get('srcset'):
                analysis.images_with_srcset += 1

            # Image format
            if src:
                ext = src.split('?')[0].split('.')[-1].lower()
                analysis.format_breakdown[ext] = analysis.format_breakdown.get(ext, 0) + 1

                if ext in ('webp', 'avif'):
                    analysis.modern_formats += 1
                elif ext in ('jpg', 'jpeg', 'png', 'gif'):
                    analysis.legacy_formats += 1

        # Check picture elements for modern format support
        picture_elements = soup.find_all('picture')
        for picture in picture_elements:
            sources = picture.find_all('source')
            for source in sources:
                srcset = source.get('srcset', '')
                if 'webp' in srcset or 'avif' in srcset:
                    analysis.modern_formats += 1

        return analysis

    def _analyze_caching(self, response: requests.Response) -> CachingAnalysis:
        """Analyze caching headers"""
        analysis = CachingAnalysis()
        headers = response.headers

        # Cache-Control
        cache_control = headers.get('Cache-Control', '')
        if cache_control:
            analysis.has_cache_control = True
            analysis.cache_control_value = cache_control

            # Parse max-age
            max_age_match = re.search(r'max-age=(\d+)', cache_control)
            if max_age_match:
                analysis.max_age_seconds = int(max_age_match.group(1))

            # Check if cacheable
            if 'no-store' not in cache_control and 'no-cache' not in cache_control:
                analysis.is_cacheable = True

        # ETag
        if headers.get('ETag'):
            analysis.has_etag = True
            analysis.is_cacheable = True

        # Last-Modified
        if headers.get('Last-Modified'):
            analysis.has_last_modified = True

        # Expires
        if headers.get('Expires'):
            analysis.has_expires = True

        # Calculate caching score
        score = 0
        if analysis.has_cache_control:
            score += 30
        if analysis.has_etag:
            score += 25
        if analysis.has_last_modified:
            score += 15
        if analysis.max_age_seconds > 86400:  # > 1 day
            score += 20
        elif analysis.max_age_seconds > 3600:  # > 1 hour
            score += 10

        if analysis.is_cacheable:
            score += 10

        analysis.caching_score = min(100, score)

        return analysis

    def _analyze_compression(self, response: requests.Response) -> CompressionAnalysis:
        """Analyze response compression"""
        analysis = CompressionAnalysis()
        headers = response.headers

        content_encoding = headers.get('Content-Encoding', '')
        analysis.content_encoding = content_encoding

        if 'gzip' in content_encoding:
            analysis.has_gzip = True
        if 'br' in content_encoding:
            analysis.has_brotli = True

        # Size info
        analysis.compressed_size = len(response.content)

        # Try to get original size from headers
        content_length = headers.get('Content-Length')
        if content_length:
            analysis.original_size = int(content_length)

        # Estimate compression ratio
        if analysis.has_gzip or analysis.has_brotli:
            # Typical compression ratios
            if analysis.has_brotli:
                analysis.compression_ratio = 0.8  # ~80% reduction typical
            else:
                analysis.compression_ratio = 0.7  # ~70% reduction typical

        return analysis

    def _generate_issues(self, result: PerformanceResult):
        """Generate issues and recommendations"""

        # CSS issues
        if result.css.render_blocking > 0:
            result.issues.append(
                f"{result.css.render_blocking} render-blocking CSS files"
            )
            result.recommendations.append(
                "Consider inlining critical CSS and deferring non-critical styles"
            )

        if not result.css.has_critical_css and result.css.external_stylesheets > 2:
            result.recommendations.append(
                "Consider inlining critical CSS for faster first paint"
            )

        # JS issues
        if result.js.render_blocking > 0:
            result.issues.append(
                f"{result.js.render_blocking} render-blocking JavaScript files"
            )
            result.recommendations.append(
                "Add 'async' or 'defer' attribute to non-critical scripts"
            )

        if result.js.external_scripts > 10:
            result.issues.append(
                f"Too many external scripts ({result.js.external_scripts})"
            )
            result.recommendations.append(
                "Consider bundling scripts to reduce HTTP requests"
            )

        # Image issues
        if result.images.images_without_alt > 0:
            result.issues.append(
                f"{result.images.images_without_alt} images missing alt text"
            )

        if result.images.missing_dimensions:
            result.issues.append(
                f"{len(result.images.missing_dimensions)} images missing width/height"
            )
            result.recommendations.append(
                "Add width and height attributes to prevent layout shifts (CLS)"
            )

        if result.images.legacy_formats > 0 and result.images.modern_formats == 0:
            result.issues.append(
                "No modern image formats (WebP/AVIF) detected"
            )
            result.recommendations.append(
                "Use WebP/AVIF formats with fallback for better compression"
            )

        lazy_ratio = (result.images.images_with_lazy / result.images.total_images * 100
                     if result.images.total_images > 0 else 0)
        if result.images.total_images > 3 and lazy_ratio < 50:
            result.recommendations.append(
                f"Add loading=\"lazy\" to below-fold images ({result.images.images_with_lazy}/{result.images.total_images} use lazy loading)"
            )

        # Caching issues
        if not result.caching.has_cache_control:
            result.issues.append("Missing Cache-Control header")
            result.recommendations.append(
                "Add Cache-Control header for static assets"
            )

        if result.caching.max_age_seconds < 3600 and result.caching.has_cache_control:
            result.recommendations.append(
                "Consider increasing cache max-age for static content"
            )

        # Compression issues
        if not result.compression.has_gzip and not result.compression.has_brotli:
            result.issues.append("No compression detected")
            result.recommendations.append(
                "Enable gzip or Brotli compression on the server"
            )

        # TTFB issues
        if result.ttfb_ms > 600:
            result.issues.append(f"Slow TTFB: {result.ttfb_ms:.0f}ms (target: <600ms)")
        elif result.ttfb_ms > 400:
            result.recommendations.append(
                f"TTFB could be improved: {result.ttfb_ms:.0f}ms"
            )

    def _calculate_score(self, result: PerformanceResult) -> int:
        """Calculate performance score"""
        score = 100

        # CSS (20 points)
        if result.css.render_blocking > 2:
            score -= 15
        elif result.css.render_blocking > 0:
            score -= 8

        # JS (25 points)
        if result.js.render_blocking > 3:
            score -= 20
        elif result.js.render_blocking > 0:
            score -= 10

        if result.js.external_scripts > 15:
            score -= 5

        # Images (25 points)
        if result.images.total_images > 0:
            # Missing dimensions
            missing_ratio = len(result.images.missing_dimensions) / result.images.total_images
            score -= int(missing_ratio * 10)

            # No modern formats
            if result.images.modern_formats == 0 and result.images.legacy_formats > 3:
                score -= 10

            # No lazy loading
            lazy_ratio = result.images.images_with_lazy / result.images.total_images
            if lazy_ratio < 0.3:
                score -= 5

        # Caching (15 points)
        score -= (15 - int(result.caching.caching_score * 0.15))

        # Compression (10 points)
        if not result.compression.has_gzip and not result.compression.has_brotli:
            score -= 10

        # TTFB (5 points)
        if result.ttfb_ms > 800:
            score -= 5
        elif result.ttfb_ms > 500:
            score -= 3

        return max(0, min(100, score))

    def print_result(self, result: PerformanceResult):
        """Print performance analysis result"""
        print_header(f"Performance Analysis: {result.url}")

        # Score
        score_color = Colors.GREEN if result.score >= 80 else Colors.YELLOW if result.score >= 50 else Colors.RED
        print(f"\nPerformance Score: {score_color}{result.score}/100{Colors.RESET}")

        # Basic metrics
        print(f"\n{Colors.BOLD}Page Metrics:{Colors.RESET}")
        print(f"  TTFB: {result.ttfb_ms:.0f}ms")
        print(f"  Page size: {result.total_size_bytes / 1024:.1f} KB")

        # CSS
        c = result.css
        print(f"\n{Colors.BOLD}CSS:{Colors.RESET}")
        print(f"  Total stylesheets: {c.total_stylesheets}")
        print(f"  Render-blocking: {c.render_blocking}")
        print(f"  Inline styles: {c.inline_styles}")
        if c.has_critical_css:
            print(f"  {Colors.GREEN}✓ Critical CSS detected{Colors.RESET}")

        # JavaScript
        j = result.js
        print(f"\n{Colors.BOLD}JavaScript:{Colors.RESET}")
        print(f"  Total scripts: {j.total_scripts} ({j.external_scripts} external)")
        print(f"  Render-blocking: {j.render_blocking}")
        print(f"  Async: {j.async_scripts}, Defer: {j.defer_scripts}")
        if j.module_scripts > 0:
            print(f"  ES Modules: {j.module_scripts}")

        # Images
        i = result.images
        print(f"\n{Colors.BOLD}Images:{Colors.RESET}")
        print(f"  Total: {i.total_images}")
        print(f"  With alt text: {i.images_with_alt}/{i.total_images}")
        print(f"  With dimensions: {i.images_with_dimensions}/{i.total_images}")
        print(f"  Lazy loading: {i.images_with_lazy}/{i.total_images}")
        print(f"  Responsive (srcset): {i.images_with_srcset}/{i.total_images}")
        if i.format_breakdown:
            formats = ', '.join([f"{fmt}: {count}" for fmt, count in i.format_breakdown.items()])
            print(f"  Formats: {formats}")

        # Caching
        cache = result.caching
        print(f"\n{Colors.BOLD}Caching:{Colors.RESET}")
        print(f"  Cache-Control: {'✓' if cache.has_cache_control else '✗'}")
        if cache.cache_control_value:
            print(f"    Value: {cache.cache_control_value[:50]}")
        print(f"  ETag: {'✓' if cache.has_etag else '✗'}")
        print(f"  Last-Modified: {'✓' if cache.has_last_modified else '✗'}")
        print(f"  Caching score: {cache.caching_score}/100")

        # Compression
        comp = result.compression
        print(f"\n{Colors.BOLD}Compression:{Colors.RESET}")
        if comp.has_brotli:
            print(f"  {Colors.GREEN}✓ Brotli compression{Colors.RESET}")
        elif comp.has_gzip:
            print(f"  {Colors.GREEN}✓ Gzip compression{Colors.RESET}")
        else:
            print(f"  {Colors.RED}✗ No compression{Colors.RESET}")

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

    def analyze_batch(self, urls: List[str]) -> List[PerformanceResult]:
        """Analyze multiple URLs"""
        results = []
        for url in urls:
            result = self.analyze_url(url)
            results.append(result)
            self.print_result(result)
        return results
