#!/usr/bin/env python3
"""
Site Crawler

Crawls entire website and collects data for analysis:
- All internal pages
- Internal/external links
- Response codes
- Redirect chains
- Page metadata
"""

import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional, Set, Dict, List
from urllib.parse import urlparse, urljoin
from collections import deque

from ..core.utils import print_info, print_warning, print_success, print_error, Colors


@dataclass
class CrawledPage:
    """Data for a single crawled page"""
    url: str
    status_code: int
    content_type: str = ''
    title: str = ''
    meta_description: str = ''
    canonical: str = ''
    h1: str = ''
    word_count: int = 0
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    images: List[Dict] = field(default_factory=list)
    redirect_url: str = ''
    redirect_chain: List[str] = field(default_factory=list)
    response_time: float = 0.0
    last_modified: str = ''
    content_length: int = 0
    depth: int = 0
    linked_from: List[str] = field(default_factory=list)
    error: str = ''


@dataclass
class CrawlResult:
    """Complete crawl result"""
    base_url: str
    pages: Dict[str, CrawledPage] = field(default_factory=dict)
    broken_links: List[Dict] = field(default_factory=list)
    redirect_chains: List[Dict] = field(default_factory=list)
    external_links: Set[str] = field(default_factory=set)
    crawl_time: float = 0.0
    pages_crawled: int = 0
    pages_failed: int = 0


class SiteCrawler:
    """Crawls website collecting SEO-relevant data"""

    def __init__(
        self,
        max_pages: int = 500,
        max_depth: int = 10,
        delay: float = 0.2,
        timeout: int = 10,
        respect_robots: bool = True,
        follow_external: bool = False
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.follow_external = follow_external

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.1; Site Crawler)'
        })

        self.visited: Set[str] = set()
        self.queue: deque = deque()
        self.disallowed_paths: Set[str] = set()

    def crawl(self, start_url: str) -> CrawlResult:
        """Crawl website starting from URL"""
        start_time = time.time()

        # Parse base URL
        parsed = urlparse(start_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        result = CrawlResult(base_url=base_url)

        # Parse robots.txt
        if self.respect_robots:
            self._parse_robots(base_url)

        # Initialize queue with start URL
        self.queue.append((self._normalize_url(start_url), 0, ''))  # (url, depth, referrer)

        print_info(f"Starting crawl of {base_url}")
        print_info(f"Max pages: {self.max_pages}, Max depth: {self.max_depth}")

        while self.queue and len(self.visited) < self.max_pages:
            url, depth, referrer = self.queue.popleft()

            # Skip if already visited or too deep
            if url in self.visited or depth > self.max_depth:
                continue

            # Skip if disallowed by robots.txt
            if self._is_disallowed(url):
                continue

            self.visited.add(url)

            # Crawl the page
            page = self._crawl_page(url, depth, referrer)

            if page:
                result.pages[url] = page
                result.pages_crawled += 1

                # Track broken links
                if page.status_code >= 400:
                    result.broken_links.append({
                        'url': url,
                        'status_code': page.status_code,
                        'linked_from': page.linked_from
                    })
                    result.pages_failed += 1

                # Track redirect chains
                if page.redirect_chain and len(page.redirect_chain) > 1:
                    result.redirect_chains.append({
                        'original': url,
                        'chain': page.redirect_chain,
                        'final': page.redirect_url
                    })

                # Add internal links to queue
                for link in page.internal_links:
                    if link not in self.visited:
                        self.queue.append((link, depth + 1, url))

                # Collect external links
                result.external_links.update(page.external_links)

                # Progress
                if result.pages_crawled % 10 == 0:
                    print_info(f"Crawled {result.pages_crawled} pages...")

            # Respect delay
            time.sleep(self.delay)

        result.crawl_time = time.time() - start_time
        print_success(f"Crawl complete: {result.pages_crawled} pages in {result.crawl_time:.1f}s")

        return result

    def _crawl_page(self, url: str, depth: int, referrer: str) -> Optional[CrawledPage]:
        """Crawl single page and extract data"""
        page = CrawledPage(url=url, depth=depth, status_code=0)

        if referrer:
            page.linked_from.append(referrer)

        try:
            start = time.time()
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            page.response_time = time.time() - start
            page.status_code = response.status_code
            page.content_type = response.headers.get('Content-Type', '')
            page.last_modified = response.headers.get('Last-Modified', '')
            page.content_length = len(response.content)

            # Track redirects
            if response.history:
                page.redirect_chain = [r.url for r in response.history] + [response.url]
                page.redirect_url = response.url

            # Parse HTML content
            if 'text/html' in page.content_type and response.status_code == 200:
                self._parse_html(page, response.text, url)

        except requests.Timeout:
            page.error = 'Timeout'
            page.status_code = 0
        except requests.ConnectionError:
            page.error = 'Connection Error'
            page.status_code = 0
        except Exception as e:
            page.error = str(e)
            page.status_code = 0

        return page

    def _parse_html(self, page: CrawledPage, html: str, base_url: str):
        """Parse HTML and extract SEO data"""
        soup = BeautifulSoup(html, 'html.parser')

        # Title
        title_tag = soup.find('title')
        page.title = title_tag.get_text(strip=True) if title_tag else ''

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        page.meta_description = meta_desc.get('content', '') if meta_desc else ''

        # Canonical
        canonical = soup.find('link', rel='canonical')
        page.canonical = canonical.get('href', '') if canonical else ''

        # H1
        h1_tag = soup.find('h1')
        page.h1 = h1_tag.get_text(strip=True) if h1_tag else ''

        # Word count (visible text)
        text = soup.get_text(separator=' ', strip=True)
        page.word_count = len(text.split())

        # Links
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        for a in soup.find_all('a', href=True):
            href = a.get('href', '').strip()
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            full_url = self._normalize_url(full_url)

            parsed_link = urlparse(full_url)

            # Classify as internal or external
            if parsed_link.netloc == base_domain:
                if full_url not in page.internal_links:
                    page.internal_links.append(full_url)
            else:
                if full_url not in page.external_links:
                    page.external_links.append(full_url)

        # Images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                page.images.append({
                    'src': urljoin(base_url, src),
                    'alt': img.get('alt', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                })

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        parsed = urlparse(url)
        # Remove fragment, normalize path
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        # Remove trailing slash for consistency (except root)
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        return normalized

    def _parse_robots(self, base_url: str):
        """Parse robots.txt for disallowed paths"""
        robots_url = f"{base_url}/robots.txt"
        try:
            response = self.session.get(robots_url, timeout=5)
            if response.status_code == 200:
                current_agent = None
                for line in response.text.split('\n'):
                    line = line.strip().lower()
                    if line.startswith('user-agent:'):
                        agent = line.split(':', 1)[1].strip()
                        current_agent = agent
                    elif line.startswith('disallow:') and current_agent in ('*', 'gsctoolkit'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            self.disallowed_paths.add(path)
        except:
            pass

    def _is_disallowed(self, url: str) -> bool:
        """Check if URL is disallowed by robots.txt"""
        if not self.disallowed_paths:
            return False

        parsed = urlparse(url)
        path = parsed.path

        for disallowed in self.disallowed_paths:
            if path.startswith(disallowed):
                return True
        return False

    def print_summary(self, result: CrawlResult):
        """Print crawl summary"""
        print(f"\n{'='*60}")
        print(f"Crawl Summary: {result.base_url}")
        print('='*60)

        print(f"\n{Colors.BOLD}Statistics:{Colors.RESET}")
        print(f"  Pages crawled: {result.pages_crawled}")
        print(f"  Pages failed:  {result.pages_failed}")
        print(f"  External links: {len(result.external_links)}")
        print(f"  Crawl time:    {result.crawl_time:.1f}s")

        if result.broken_links:
            print(f"\n{Colors.RED}Broken Links ({len(result.broken_links)}):{Colors.RESET}")
            for bl in result.broken_links[:10]:
                print(f"  {bl['status_code']} {bl['url'][:60]}")
                if bl['linked_from']:
                    print(f"      ← from: {bl['linked_from'][0][:50]}")

        if result.redirect_chains:
            print(f"\n{Colors.YELLOW}Redirect Chains ({len(result.redirect_chains)}):{Colors.RESET}")
            for rc in result.redirect_chains[:5]:
                print(f"  {rc['original'][:50]}")
                print(f"    → {' → '.join([u[-30:] for u in rc['chain']])}")

        print()
