"""
GSC Toolkit - Complete SEO Analysis Package

A comprehensive toolkit for analyzing website SEO performance with:
- Google Search Console API (analytics, inspection, sitemaps)
- PageSpeed Insights API (Core Web Vitals)
- Indexing API (request indexing)
- CSV export parsing (coverage, links)
- Manual actions checklist generation
- Security headers analysis
- On-page SEO analysis
- Schema/JSON-LD validation
- Hreflang validation
- Robots.txt & Sitemap validation
- Site-wide crawling & audit
- Content quality analysis (readability, freshness, language)
- Mobile SEO analysis (viewport, touch targets, responsive)
- Performance analysis (CSS/JS blocking, images, caching)
- Links & URL structure analysis (anchor text, pagination)
"""

from .core.config import (
    KEY_FILE,
    SITE_URL,
    BASE_URL,
    DEFAULT_DAYS,
    PAGESPEED_API_KEY,
    OUTPUT_DIR,
    SCOPES_READONLY,
    SCOPES_WRITE,
)
from .core.models import Priority, ManualAction, SEOAuditResult
from .core.utils import (
    Colors,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_info,
)
from .analyzers.pagespeed import PageSpeedAnalyzer
from .analyzers.indexing import IndexingAPI
from .analyzers.security import SecurityAnalyzer
from .analyzers.onpage import OnPageAnalyzer
from .analyzers.schema import SchemaAnalyzer
from .analyzers.hreflang import HreflangAnalyzer
from .analyzers.robots import RobotsAnalyzer
from .analyzers.crawler import SiteCrawler, CrawlResult, CrawledPage
from .analyzers.site_audit import SiteAuditor, SiteAuditResult
from .analyzers.content import (
    ContentAnalyzer,
    ContentAnalysisResult,
    ReadabilityMetrics,
    ContentFreshness,
    LanguageAnalysis,
    KeywordAnalysis,
)
from .analyzers.mobile import (
    MobileAnalyzer,
    MobileAnalysisResult,
    ViewportAnalysis,
    TouchTargetAnalysis,
    FontAnalysis,
    ResponsiveAnalysis,
)
from .analyzers.performance import (
    PerformanceAnalyzer,
    PerformanceResult,
    CSSAnalysis,
    JSAnalysis,
    ImageAnalysis,
    CachingAnalysis,
    CompressionAnalysis,
)
from .analyzers.links_analysis import (
    LinksAnalyzer,
    LinksAnalysisResult,
    AnchorTextAnalysis,
    URLStructureAnalysis,
    PaginationAnalysis,
)
from .gsc_client import GSCAnalyzer

__version__ = "2.3.0"
__all__ = [
    # Config
    "KEY_FILE",
    "SITE_URL",
    "BASE_URL",
    "DEFAULT_DAYS",
    "PAGESPEED_API_KEY",
    "OUTPUT_DIR",
    "SCOPES_READONLY",
    "SCOPES_WRITE",
    # Models
    "Priority",
    "ManualAction",
    "SEOAuditResult",
    # Utils
    "Colors",
    "print_header",
    "print_success",
    "print_warning",
    "print_error",
    "print_info",
    # Analyzers - GSC
    "PageSpeedAnalyzer",
    "IndexingAPI",
    # Analyzers - Page
    "SecurityAnalyzer",
    "OnPageAnalyzer",
    "SchemaAnalyzer",
    "HreflangAnalyzer",
    "RobotsAnalyzer",
    # Analyzers - Site-wide
    "SiteCrawler",
    "CrawlResult",
    "CrawledPage",
    "SiteAuditor",
    "SiteAuditResult",
    # Analyzers - Content Quality
    "ContentAnalyzer",
    "ContentAnalysisResult",
    "ReadabilityMetrics",
    "ContentFreshness",
    "LanguageAnalysis",
    "KeywordAnalysis",
    # Analyzers - Mobile SEO
    "MobileAnalyzer",
    "MobileAnalysisResult",
    "ViewportAnalysis",
    "TouchTargetAnalysis",
    "FontAnalysis",
    "ResponsiveAnalysis",
    # Analyzers - Performance
    "PerformanceAnalyzer",
    "PerformanceResult",
    "CSSAnalysis",
    "JSAnalysis",
    "ImageAnalysis",
    "CachingAnalysis",
    "CompressionAnalysis",
    # Analyzers - Links & URL Structure
    "LinksAnalyzer",
    "LinksAnalysisResult",
    "AnchorTextAnalysis",
    "URLStructureAnalysis",
    "PaginationAnalysis",
    # Main client
    "GSCAnalyzer",
]
