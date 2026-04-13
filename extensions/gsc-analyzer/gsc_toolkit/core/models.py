"""Data models for GSC Toolkit."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any


class Priority(Enum):
    """Priority levels for actions."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class ManualAction:
    """Action that requires manual intervention."""
    priority: Priority
    category: str
    title: str
    description: str
    steps: List[str] = field(default_factory=list)
    affected_urls: List[str] = field(default_factory=list)
    gsc_link: str = ""


@dataclass
class SEOAuditResult:
    """Complete SEO audit result."""
    generated_at: str
    site_url: str

    # Collected data
    sitemaps: List[Dict] = field(default_factory=list)
    analytics: Dict = field(default_factory=dict)
    inspection_results: List[Dict] = field(default_factory=list)
    coverage_issues: Dict = field(default_factory=dict)
    core_web_vitals: List[Dict] = field(default_factory=list)
    links_analysis: Dict = field(default_factory=dict)
    indexing_buckets: Dict[str, List[str]] = field(default_factory=dict)

    # Issues found
    issues_found: List[Dict] = field(default_factory=list)

    # Manual actions required
    manual_actions: List[ManualAction] = field(default_factory=list)

    # Summary
    total_pages_in_sitemap: int = 0
    total_pages_indexed: int = 0
    total_issues: int = 0
    seo_score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'generated_at': self.generated_at,
            'site_url': self.site_url,
            'seo_score': self.seo_score,
            'total_pages_in_sitemap': self.total_pages_in_sitemap,
            'total_pages_indexed': self.total_pages_indexed,
            'total_issues': self.total_issues,
            'analytics': self.analytics,
            'sitemaps': self.sitemaps,
            'coverage_issues': self.coverage_issues,
            'core_web_vitals': self.core_web_vitals,
            'links_analysis': self.links_analysis,
            'indexing_buckets': self.indexing_buckets,
            'issues_found': self.issues_found,
            'manual_actions': [
                {
                    'priority': a.priority.value,
                    'category': a.category,
                    'title': a.title,
                    'description': a.description,
                    'steps': a.steps,
                    'affected_urls': a.affected_urls,
                    'gsc_link': a.gsc_link,
                }
                for a in self.manual_actions
            ],
        }
