#!/usr/bin/env python3
"""
On-Page SEO Analyzer

Analyzes on-page SEO elements:
- Title tag (length, keywords)
- Meta description (length, presence)
- Heading hierarchy (H1-H6)
- Content length
- Internal/external links
- Images (alt text)
- Canonical URL
- Open Graph / Twitter Cards
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, urljoin

from ..core.utils import print_success, print_warning, print_error, print_info, Colors


@dataclass
class HeadingAnalysis:
    """Heading hierarchy analysis"""
    h1_count: int = 0
    h1_texts: list = field(default_factory=list)
    h2_count: int = 0
    h3_count: int = 0
    h4_count: int = 0
    h5_count: int = 0
    h6_count: int = 0
    hierarchy_valid: bool = True
    issues: list = field(default_factory=list)


@dataclass
class ImageAnalysis:
    """Image analysis results"""
    total_images: int = 0
    images_with_alt: int = 0
    images_without_alt: int = 0
    missing_alt_srcs: list = field(default_factory=list)


@dataclass
class LinkAnalysis:
    """Link analysis results"""
    internal_links: int = 0
    external_links: int = 0
    broken_links: list = field(default_factory=list)
    nofollow_links: int = 0


@dataclass
class OnPageSEOResult:
    """Complete on-page SEO analysis result"""
    url: str
    status_code: int = 0

    # Title
    title: Optional[str] = None
    title_length: int = 0
    title_issues: list = field(default_factory=list)

    # Meta description
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    meta_description_issues: list = field(default_factory=list)

    # Meta keywords (legacy but still checked)
    meta_keywords: Optional[str] = None

    # Canonical
    canonical_url: Optional[str] = None
    canonical_issues: list = field(default_factory=list)

    # Headings
    headings: HeadingAnalysis = field(default_factory=HeadingAnalysis)

    # Content
    word_count: int = 0
    content_issues: list = field(default_factory=list)

    # Images
    images: ImageAnalysis = field(default_factory=ImageAnalysis)

    # Links
    links: LinkAnalysis = field(default_factory=LinkAnalysis)

    # Open Graph
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_issues: list = field(default_factory=list)

    # Twitter Cards
    twitter_card: Optional[str] = None
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None

    # Robots
    robots_meta: Optional[str] = None
    is_indexable: bool = True

    # Overall
    score: int = 0  # 0-100
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


class OnPageAnalyzer:
    """Analyzes on-page SEO elements"""

    # Optimal ranges
    TITLE_MIN_LENGTH = 30
    TITLE_MAX_LENGTH = 60
    TITLE_OPTIMAL_LENGTH = 55

    META_DESC_MIN_LENGTH = 120
    META_DESC_MAX_LENGTH = 160
    META_DESC_OPTIMAL_LENGTH = 155

    MIN_CONTENT_WORDS = 300

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.0; OnPage Analyzer)'
        })

    def analyze_url(self, url: str) -> OnPageSEOResult:
        """Analyze on-page SEO for a URL"""
        result = OnPageSEOResult(url=url)
        parsed_url = urlparse(url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            result.status_code = response.status_code

            if response.status_code != 200:
                result.issues.append(f"Non-200 status code: {response.status_code}")
                return result

            soup = BeautifulSoup(response.text, 'html.parser')

        except requests.RequestException as e:
            result.issues.append(f"Failed to fetch page: {str(e)}")
            return result

        score = 0
        max_score = 0

        # === TITLE ANALYSIS ===
        max_score += 15
        title_tag = soup.find('title')
        if title_tag:
            result.title = title_tag.get_text().strip()
            result.title_length = len(result.title)

            if result.title_length < self.TITLE_MIN_LENGTH:
                result.title_issues.append(f"Title too short ({result.title_length} chars, min: {self.TITLE_MIN_LENGTH})")
                score += 5
            elif result.title_length > self.TITLE_MAX_LENGTH:
                result.title_issues.append(f"Title too long ({result.title_length} chars, max: {self.TITLE_MAX_LENGTH})")
                score += 8
            else:
                score += 15
        else:
            result.title_issues.append("Missing title tag")
            result.recommendations.append("Add a unique, descriptive title tag (50-60 characters)")

        # === META DESCRIPTION ===
        max_score += 15
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result.meta_description = meta_desc['content'].strip()
            result.meta_description_length = len(result.meta_description)

            if result.meta_description_length < self.META_DESC_MIN_LENGTH:
                result.meta_description_issues.append(
                    f"Meta description too short ({result.meta_description_length} chars, min: {self.META_DESC_MIN_LENGTH})"
                )
                score += 5
            elif result.meta_description_length > self.META_DESC_MAX_LENGTH:
                result.meta_description_issues.append(
                    f"Meta description too long ({result.meta_description_length} chars, max: {self.META_DESC_MAX_LENGTH})"
                )
                score += 8
            else:
                score += 15
        else:
            result.meta_description_issues.append("Missing meta description")
            result.recommendations.append("Add a compelling meta description (120-160 characters)")

        # === META KEYWORDS (legacy) ===
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            result.meta_keywords = meta_keywords['content'].strip()

        # === CANONICAL URL ===
        max_score += 10
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            result.canonical_url = canonical['href']
            # Check if canonical points to self
            if result.canonical_url == url or result.canonical_url == url.rstrip('/'):
                score += 10
            else:
                result.canonical_issues.append(f"Canonical points to different URL: {result.canonical_url}")
                score += 5
        else:
            result.canonical_issues.append("Missing canonical URL")
            result.recommendations.append("Add a canonical URL to prevent duplicate content issues")
            score += 3

        # === HEADING ANALYSIS ===
        max_score += 15
        result.headings = self._analyze_headings(soup)

        if result.headings.h1_count == 1:
            score += 10
        elif result.headings.h1_count == 0:
            result.headings.issues.append("Missing H1 tag")
            result.recommendations.append("Add exactly one H1 tag per page")
        else:
            result.headings.issues.append(f"Multiple H1 tags found ({result.headings.h1_count})")
            score += 5

        if result.headings.hierarchy_valid:
            score += 5
        else:
            result.headings.issues.append("Heading hierarchy is broken (e.g., H3 without H2)")

        # === CONTENT LENGTH ===
        max_score += 10
        text_content = soup.get_text()
        words = re.findall(r'\b\w+\b', text_content)
        result.word_count = len(words)

        if result.word_count >= self.MIN_CONTENT_WORDS:
            score += 10
        elif result.word_count >= 150:
            score += 5
            result.content_issues.append(f"Thin content ({result.word_count} words, recommended: {self.MIN_CONTENT_WORDS}+)")
        else:
            result.content_issues.append(f"Very thin content ({result.word_count} words)")
            result.recommendations.append(f"Add more content (at least {self.MIN_CONTENT_WORDS} words)")

        # === IMAGE ANALYSIS ===
        max_score += 10
        result.images = self._analyze_images(soup)

        if result.images.total_images == 0:
            score += 10  # No images to check
        elif result.images.images_without_alt == 0:
            score += 10
        else:
            ratio = result.images.images_with_alt / result.images.total_images
            score += int(ratio * 10)
            if result.images.images_without_alt > 0:
                result.recommendations.append(
                    f"Add alt text to {result.images.images_without_alt} images"
                )

        # === LINK ANALYSIS ===
        max_score += 5
        result.links = self._analyze_links(soup, base_domain, url)
        if result.links.internal_links >= 3:
            score += 5
        elif result.links.internal_links >= 1:
            score += 3
        else:
            result.recommendations.append("Add internal links to improve site structure")

        # === OPEN GRAPH ===
        max_score += 10
        og_score = 0
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and og_title.get('content'):
            result.og_title = og_title['content']
            og_score += 3

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            result.og_description = og_desc['content']
            og_score += 3

        og_image = soup.find('meta', attrs={'property': 'og:image'})
        if og_image and og_image.get('content'):
            result.og_image = og_image['content']
            og_score += 4
        else:
            result.og_issues.append("Missing og:image")
            result.recommendations.append("Add Open Graph image for social sharing")

        score += og_score

        # === TWITTER CARDS ===
        max_score += 5
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        if twitter_card and twitter_card.get('content'):
            result.twitter_card = twitter_card['content']
            score += 5

            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title:
                result.twitter_title = twitter_title.get('content')

            twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
            if twitter_desc:
                result.twitter_description = twitter_desc.get('content')

            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image:
                result.twitter_image = twitter_image.get('content')

        # === ROBOTS META ===
        max_score += 5
        robots = soup.find('meta', attrs={'name': 'robots'})
        if robots and robots.get('content'):
            result.robots_meta = robots['content'].lower()
            if 'noindex' in result.robots_meta:
                result.is_indexable = False
                result.issues.append("Page is set to noindex")
            else:
                score += 5
        else:
            score += 5  # No robots meta = indexable by default

        # Calculate final score
        result.score = int((score / max_score) * 100) if max_score > 0 else 0

        # Collect all issues
        result.issues.extend(result.title_issues)
        result.issues.extend(result.meta_description_issues)
        result.issues.extend(result.canonical_issues)
        result.issues.extend(result.headings.issues)
        result.issues.extend(result.content_issues)
        result.issues.extend(result.og_issues)

        return result

    def _analyze_headings(self, soup: BeautifulSoup) -> HeadingAnalysis:
        """Analyze heading hierarchy"""
        analysis = HeadingAnalysis()

        for h1 in soup.find_all('h1'):
            analysis.h1_count += 1
            text = h1.get_text().strip()
            if text:
                analysis.h1_texts.append(text[:100])  # Truncate

        analysis.h2_count = len(soup.find_all('h2'))
        analysis.h3_count = len(soup.find_all('h3'))
        analysis.h4_count = len(soup.find_all('h4'))
        analysis.h5_count = len(soup.find_all('h5'))
        analysis.h6_count = len(soup.find_all('h6'))

        # Check hierarchy
        if analysis.h3_count > 0 and analysis.h2_count == 0:
            analysis.hierarchy_valid = False
        if analysis.h4_count > 0 and analysis.h3_count == 0:
            analysis.hierarchy_valid = False

        return analysis

    def _analyze_images(self, soup: BeautifulSoup) -> ImageAnalysis:
        """Analyze images for alt text"""
        analysis = ImageAnalysis()

        for img in soup.find_all('img'):
            analysis.total_images += 1
            alt = img.get('alt', '').strip()
            if alt:
                analysis.images_with_alt += 1
            else:
                analysis.images_without_alt += 1
                src = img.get('src', 'unknown')[:50]
                analysis.missing_alt_srcs.append(src)

        return analysis

    def _analyze_links(self, soup: BeautifulSoup, base_domain: str, current_url: str) -> LinkAnalysis:
        """Analyze internal and external links"""
        analysis = LinkAnalysis()
        current_domain = urlparse(current_url).netloc

        for a in soup.find_all('a', href=True):
            href = a['href']

            # Skip anchors and javascript
            if href.startswith('#') or href.startswith('javascript:'):
                continue

            # Resolve relative URLs
            full_url = urljoin(current_url, href)
            link_domain = urlparse(full_url).netloc

            if link_domain == current_domain:
                analysis.internal_links += 1
            else:
                analysis.external_links += 1

            # Check for nofollow
            rel = a.get('rel', [])
            if isinstance(rel, list) and 'nofollow' in rel:
                analysis.nofollow_links += 1
            elif isinstance(rel, str) and 'nofollow' in rel:
                analysis.nofollow_links += 1

        return analysis

    def print_result(self, result: OnPageSEOResult):
        """Print on-page SEO analysis result"""
        print(f"\n{'='*60}")
        print(f"On-Page SEO Analysis: {result.url}")
        print('='*60)

        # Score
        if result.score >= 80:
            color = Colors.GREEN
        elif result.score >= 60:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        print(f"\nSEO Score: {color}{result.score}/100{Colors.RESET}")

        # Title
        print(f"\n{Colors.BOLD}Title:{Colors.RESET}")
        if result.title:
            status = "✓" if not result.title_issues else "⚠"
            print(f"  {status} {result.title[:60]}{'...' if len(result.title) > 60 else ''}")
            print(f"    Length: {result.title_length} chars (optimal: {self.TITLE_MIN_LENGTH}-{self.TITLE_MAX_LENGTH})")
        else:
            print_error("  ✗ Missing title tag")

        # Meta Description
        print(f"\n{Colors.BOLD}Meta Description:{Colors.RESET}")
        if result.meta_description:
            status = "✓" if not result.meta_description_issues else "⚠"
            print(f"  {status} {result.meta_description[:80]}{'...' if len(result.meta_description) > 80 else ''}")
            print(f"    Length: {result.meta_description_length} chars (optimal: {self.META_DESC_MIN_LENGTH}-{self.META_DESC_MAX_LENGTH})")
        else:
            print_error("  ✗ Missing meta description")

        # Canonical
        print(f"\n{Colors.BOLD}Canonical URL:{Colors.RESET}")
        if result.canonical_url:
            print(f"  ✓ {result.canonical_url}")
        else:
            print_warning("  ⚠ Missing canonical URL")

        # Headings
        print(f"\n{Colors.BOLD}Headings:{Colors.RESET}")
        h1_status = "✓" if result.headings.h1_count == 1 else "✗"
        print(f"  {h1_status} H1: {result.headings.h1_count}")
        if result.headings.h1_texts:
            print(f"    → {result.headings.h1_texts[0][:50]}...")
        print(f"  H2: {result.headings.h2_count} | H3: {result.headings.h3_count} | H4: {result.headings.h4_count}")
        if not result.headings.hierarchy_valid:
            print_warning("    ⚠ Heading hierarchy broken")

        # Content
        print(f"\n{Colors.BOLD}Content:{Colors.RESET}")
        word_status = "✓" if result.word_count >= self.MIN_CONTENT_WORDS else "⚠"
        print(f"  {word_status} Word count: {result.word_count} (recommended: {self.MIN_CONTENT_WORDS}+)")

        # Images
        print(f"\n{Colors.BOLD}Images:{Colors.RESET}")
        print(f"  Total: {result.images.total_images}")
        if result.images.total_images > 0:
            alt_status = "✓" if result.images.images_without_alt == 0 else "⚠"
            print(f"  {alt_status} With alt: {result.images.images_with_alt} | Without: {result.images.images_without_alt}")

        # Links
        print(f"\n{Colors.BOLD}Links:{Colors.RESET}")
        print(f"  Internal: {result.links.internal_links} | External: {result.links.external_links}")
        if result.links.nofollow_links:
            print(f"  Nofollow: {result.links.nofollow_links}")

        # Open Graph
        print(f"\n{Colors.BOLD}Open Graph:{Colors.RESET}")
        og_status = "✓" if result.og_title and result.og_image else "⚠"
        print(f"  {og_status} Title: {'Yes' if result.og_title else 'No'} | Image: {'Yes' if result.og_image else 'No'}")

        # Twitter Cards
        print(f"\n{Colors.BOLD}Twitter Card:{Colors.RESET}")
        print(f"  Type: {result.twitter_card or 'Not set'}")

        # Robots
        if not result.is_indexable:
            print_error(f"\n⚠ Page is NOINDEX: {result.robots_meta}")

        # Issues & Recommendations
        if result.issues:
            print(f"\n{Colors.RED}Issues ({len(result.issues)}):{Colors.RESET}")
            for issue in result.issues[:10]:  # Limit to 10
                print(f"  • {issue}")

        if result.recommendations:
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.RESET}")
            for rec in result.recommendations[:10]:
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
