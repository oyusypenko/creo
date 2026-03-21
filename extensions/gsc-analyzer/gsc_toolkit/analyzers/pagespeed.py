"""PageSpeed Insights API analyzer for Core Web Vitals."""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests

from ..core.config import PAGESPEED_API_KEY
from ..core.utils import Colors, print_error


class PageSpeedAnalyzer:
    """PageSpeed Insights API for Core Web Vitals analysis."""

    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    def __init__(self, api_key: str = PAGESPEED_API_KEY):
        self.api_key = api_key

    def analyze_url(self, url: str, strategy: str = "mobile") -> Dict[str, Any]:
        """
        Analyze a URL with PageSpeed Insights API.

        Args:
            url: URL to analyze
            strategy: "mobile" or "desktop"

        Returns:
            Dict with Core Web Vitals and performance data
        """
        params = {
            "url": url,
            "strategy": strategy,
            "category": ["performance", "accessibility", "best-practices", "seo"],
        }

        if self.api_key:
            params["key"] = self.api_key

        try:
            response = requests.get(self.API_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Extract Core Web Vitals
            lighthouse = data.get("lighthouseResult", {})
            audits = lighthouse.get("audits", {})
            categories = lighthouse.get("categories", {})

            # Field data (real user metrics) if available
            loading_experience = data.get("loadingExperience", {})

            cwv = {
                "url": url,
                "strategy": strategy,
                "fetch_time": datetime.now().isoformat(),

                # Performance scores
                "performance_score": int(categories.get("performance", {}).get("score", 0) * 100),
                "accessibility_score": int(categories.get("accessibility", {}).get("score", 0) * 100),
                "best_practices_score": int(categories.get("best-practices", {}).get("score", 0) * 100),
                "seo_score": int(categories.get("seo", {}).get("score", 0) * 100),

                # Core Web Vitals (lab data)
                "lcp_ms": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
                "fid_ms": audits.get("max-potential-fid", {}).get("numericValue", 0),
                "cls": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
                "fcp_ms": audits.get("first-contentful-paint", {}).get("numericValue", 0),
                "ttfb_ms": audits.get("server-response-time", {}).get("numericValue", 0),
                "tti_ms": audits.get("interactive", {}).get("numericValue", 0),
                "tbt_ms": audits.get("total-blocking-time", {}).get("numericValue", 0),
                "speed_index_ms": audits.get("speed-index", {}).get("numericValue", 0),

                # Field data (if available)
                "field_lcp": self._extract_field_metric(loading_experience, "LARGEST_CONTENTFUL_PAINT_MS"),
                "field_fid": self._extract_field_metric(loading_experience, "FIRST_INPUT_DELAY_MS"),
                "field_cls": self._extract_field_metric(loading_experience, "CUMULATIVE_LAYOUT_SHIFT_SCORE"),
                "field_inp": self._extract_field_metric(loading_experience, "INTERACTION_TO_NEXT_PAINT"),

                # Opportunities
                "opportunities": self._extract_opportunities(audits),

                # Diagnostics
                "diagnostics": self._extract_diagnostics(audits),
            }

            return cwv

        except requests.RequestException as e:
            print_error(f"PageSpeed API error for {url}: {e}")
            return {"url": url, "error": str(e)}

    def _extract_field_metric(self, loading_exp: Dict, metric_name: str) -> Optional[Dict]:
        """Extract field metric data."""
        metrics = loading_exp.get("metrics", {})
        metric = metrics.get(metric_name, {})
        if metric:
            return {
                "percentile": metric.get("percentile"),
                "category": metric.get("category"),
            }
        return None

    def _extract_opportunities(self, audits: Dict) -> List[Dict]:
        """Extract optimization opportunities."""
        opportunities = []
        opportunity_audits = [
            "render-blocking-resources",
            "unused-css-rules",
            "unused-javascript",
            "modern-image-formats",
            "offscreen-images",
            "unminified-css",
            "unminified-javascript",
            "efficient-animated-content",
            "uses-optimized-images",
            "uses-responsive-images",
        ]

        for audit_id in opportunity_audits:
            audit = audits.get(audit_id, {})
            if audit.get("score") is not None and audit.get("score") < 1:
                savings = audit.get("details", {}).get("overallSavingsMs", 0)
                if savings > 0:
                    opportunities.append({
                        "id": audit_id,
                        "title": audit.get("title", ""),
                        "savings_ms": savings,
                        "description": audit.get("description", ""),
                    })

        return sorted(opportunities, key=lambda x: x.get("savings_ms", 0), reverse=True)

    def _extract_diagnostics(self, audits: Dict) -> List[Dict]:
        """Extract diagnostic issues."""
        diagnostics = []
        diagnostic_audits = [
            "dom-size",
            "font-display",
            "uses-passive-event-listeners",
            "no-document-write",
            "long-tasks",
            "critical-request-chains",
        ]

        for audit_id in diagnostic_audits:
            audit = audits.get(audit_id, {})
            if audit.get("score") is not None and audit.get("score") < 1:
                diagnostics.append({
                    "id": audit_id,
                    "title": audit.get("title", ""),
                    "description": audit.get("description", ""),
                    "display_value": audit.get("displayValue", ""),
                })

        return diagnostics

    def analyze_batch(self, urls: List[str], strategy: str = "mobile", delay: float = 2.0) -> List[Dict]:
        """Analyze multiple URLs with rate limiting."""
        results = []

        for i, url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}] Analyzing: {url[:50]}...")
            result = self.analyze_url(url, strategy)
            results.append(result)

            if result.get("performance_score"):
                score = result["performance_score"]
                color = Colors.GREEN if score >= 90 else (Colors.WARNING if score >= 50 else Colors.FAIL)
                print(f"  {color}Performance: {score}/100{Colors.ENDC}")

            if i < len(urls) - 1:
                time.sleep(delay)  # Rate limiting

        return results
