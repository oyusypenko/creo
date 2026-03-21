#!/usr/bin/env python3
"""
Schema/Structured Data Analyzer

Validates JSON-LD, Microdata, and RDFa structured data:
- Syntax validation
- Required fields check
- Schema.org compliance
- Common schema types validation
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional, Any

from ..core.utils import print_success, print_warning, print_error, print_info, Colors


@dataclass
class SchemaItem:
    """Individual schema item"""
    schema_type: str
    format: str  # json-ld, microdata, rdfa
    data: dict = field(default_factory=dict)
    is_valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    missing_recommended: list = field(default_factory=list)


@dataclass
class SchemaAnalysisResult:
    """Complete schema analysis result"""
    url: str
    schemas: list = field(default_factory=list)
    total_schemas: int = 0
    valid_schemas: int = 0
    invalid_schemas: int = 0
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    score: int = 0  # 0-100


class SchemaAnalyzer:
    """Analyzes structured data on web pages"""

    # Required and recommended fields for common schema types
    SCHEMA_REQUIREMENTS = {
        'Article': {
            'required': ['headline', 'author', 'datePublished'],
            'recommended': ['image', 'dateModified', 'publisher', 'description'],
        },
        'NewsArticle': {
            'required': ['headline', 'author', 'datePublished'],
            'recommended': ['image', 'dateModified', 'publisher', 'description'],
        },
        'BlogPosting': {
            'required': ['headline', 'author', 'datePublished'],
            'recommended': ['image', 'dateModified', 'publisher', 'description'],
        },
        'Product': {
            'required': ['name'],
            'recommended': ['image', 'description', 'offers', 'brand', 'sku', 'review', 'aggregateRating'],
        },
        'Organization': {
            'required': ['name'],
            'recommended': ['url', 'logo', 'description', 'sameAs', 'contactPoint'],
        },
        'LocalBusiness': {
            'required': ['name', 'address'],
            'recommended': ['telephone', 'openingHours', 'geo', 'image', 'priceRange'],
        },
        'Person': {
            'required': ['name'],
            'recommended': ['image', 'jobTitle', 'worksFor', 'url', 'sameAs'],
        },
        'WebSite': {
            'required': ['name', 'url'],
            'recommended': ['potentialAction', 'description'],
        },
        'WebPage': {
            'required': ['name'],
            'recommended': ['description', 'breadcrumb', 'mainEntity'],
        },
        'FAQPage': {
            'required': ['mainEntity'],
            'recommended': [],
        },
        'HowTo': {
            'required': ['name', 'step'],
            'recommended': ['image', 'totalTime', 'supply', 'tool'],
        },
        'Recipe': {
            'required': ['name', 'recipeIngredient', 'recipeInstructions'],
            'recommended': ['image', 'author', 'datePublished', 'prepTime', 'cookTime', 'nutrition', 'aggregateRating'],
        },
        'Event': {
            'required': ['name', 'startDate', 'location'],
            'recommended': ['description', 'image', 'endDate', 'performer', 'offers'],
        },
        'BreadcrumbList': {
            'required': ['itemListElement'],
            'recommended': [],
        },
        'VideoObject': {
            'required': ['name', 'description', 'thumbnailUrl', 'uploadDate'],
            'recommended': ['duration', 'contentUrl', 'embedUrl'],
        },
        'SoftwareApplication': {
            'required': ['name'],
            'recommended': ['applicationCategory', 'operatingSystem', 'offers', 'aggregateRating'],
        },
        'WebApplication': {
            'required': ['name'],
            'recommended': ['applicationCategory', 'operatingSystem', 'offers', 'url'],
        },
        'Review': {
            'required': ['itemReviewed', 'reviewRating', 'author'],
            'recommended': ['reviewBody', 'datePublished'],
        },
        'AggregateRating': {
            'required': ['ratingValue', 'reviewCount'],
            'recommended': ['bestRating', 'worstRating'],
        },
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.0; Schema Analyzer)'
        })

    def analyze_url(self, url: str) -> SchemaAnalysisResult:
        """Analyze structured data on a page"""
        result = SchemaAnalysisResult(url=url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result.issues.append(f"Failed to fetch page: HTTP {response.status_code}")
                return result

            soup = BeautifulSoup(response.text, 'html.parser')

        except requests.RequestException as e:
            result.issues.append(f"Failed to fetch page: {str(e)}")
            return result

        # Extract JSON-LD schemas
        json_ld_schemas = self._extract_json_ld(soup)
        result.schemas.extend(json_ld_schemas)

        # Extract Microdata (basic detection)
        microdata_count = self._count_microdata(soup)
        if microdata_count > 0:
            result.recommendations.append(
                f"Found {microdata_count} microdata items. Consider migrating to JSON-LD for easier maintenance."
            )

        # Calculate stats
        result.total_schemas = len(result.schemas)
        result.valid_schemas = sum(1 for s in result.schemas if s.is_valid)
        result.invalid_schemas = result.total_schemas - result.valid_schemas

        # Generate recommendations
        if result.total_schemas == 0:
            result.recommendations.append("No structured data found. Consider adding JSON-LD schemas.")
            result.recommendations.append("Recommended schemas: Organization, WebSite, BreadcrumbList")

        # Check for common missing schemas
        schema_types = [s.schema_type for s in result.schemas]
        if 'Organization' not in schema_types and 'LocalBusiness' not in schema_types:
            result.recommendations.append("Consider adding Organization schema for brand identity")
        if 'WebSite' not in schema_types:
            result.recommendations.append("Consider adding WebSite schema with SearchAction for sitelinks")
        if 'BreadcrumbList' not in schema_types:
            result.recommendations.append("Consider adding BreadcrumbList for navigation in search results")

        # Calculate score
        if result.total_schemas == 0:
            result.score = 0
        else:
            base_score = (result.valid_schemas / result.total_schemas) * 70

            # Bonus for having important schemas
            bonus = 0
            for important in ['Organization', 'WebSite', 'BreadcrumbList']:
                if important in schema_types:
                    bonus += 10

            result.score = min(100, int(base_score + bonus))

        return result

    def _extract_json_ld(self, soup: BeautifulSoup) -> list:
        """Extract and validate JSON-LD schemas"""
        schemas = []

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                content = script.string
                if not content:
                    continue

                # Try to parse JSON
                data = json.loads(content)

                # Handle @graph structure
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        schema = self._validate_schema(item, 'json-ld')
                        schemas.append(schema)
                elif isinstance(data, list):
                    for item in data:
                        schema = self._validate_schema(item, 'json-ld')
                        schemas.append(schema)
                else:
                    schema = self._validate_schema(data, 'json-ld')
                    schemas.append(schema)

            except json.JSONDecodeError as e:
                schemas.append(SchemaItem(
                    schema_type='Unknown',
                    format='json-ld',
                    is_valid=False,
                    errors=[f"Invalid JSON syntax: {str(e)}"]
                ))

        return schemas

    def _validate_schema(self, data: dict, format_type: str) -> SchemaItem:
        """Validate a single schema item"""
        schema_type = data.get('@type', 'Unknown')

        # Handle array types
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else 'Unknown'

        schema = SchemaItem(
            schema_type=schema_type,
            format=format_type,
            data=data
        )

        # Check for @context
        if '@context' not in data:
            schema.warnings.append("Missing @context (should be 'https://schema.org')")

        # Validate against known schema requirements
        if schema_type in self.SCHEMA_REQUIREMENTS:
            reqs = self.SCHEMA_REQUIREMENTS[schema_type]

            # Check required fields
            for field in reqs['required']:
                if not self._has_field(data, field):
                    schema.errors.append(f"Missing required field: {field}")
                    schema.is_valid = False

            # Check recommended fields
            for field in reqs['recommended']:
                if not self._has_field(data, field):
                    schema.missing_recommended.append(field)

        # Special validations for specific types
        if schema_type == 'FAQPage':
            self._validate_faq_page(data, schema)
        elif schema_type == 'BreadcrumbList':
            self._validate_breadcrumb(data, schema)
        elif schema_type in ['Article', 'NewsArticle', 'BlogPosting']:
            self._validate_article(data, schema)

        return schema

    def _has_field(self, data: dict, field: str) -> bool:
        """Check if a field exists and has a value"""
        if field not in data:
            return False
        value = data[field]
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        return True

    def _validate_faq_page(self, data: dict, schema: SchemaItem):
        """Validate FAQPage specific requirements"""
        main_entity = data.get('mainEntity', [])
        if not main_entity:
            return

        if not isinstance(main_entity, list):
            main_entity = [main_entity]

        for i, qa in enumerate(main_entity):
            qa_type = qa.get('@type', '')
            if qa_type != 'Question':
                schema.warnings.append(f"FAQ item {i+1}: @type should be 'Question'")

            if not qa.get('name'):
                schema.errors.append(f"FAQ item {i+1}: Missing question text (name)")
                schema.is_valid = False

            accepted_answer = qa.get('acceptedAnswer', {})
            if not accepted_answer:
                schema.errors.append(f"FAQ item {i+1}: Missing acceptedAnswer")
                schema.is_valid = False
            elif not accepted_answer.get('text'):
                schema.errors.append(f"FAQ item {i+1}: Missing answer text")
                schema.is_valid = False

    def _validate_breadcrumb(self, data: dict, schema: SchemaItem):
        """Validate BreadcrumbList specific requirements"""
        items = data.get('itemListElement', [])
        if not items:
            return

        for i, item in enumerate(items):
            if not item.get('position'):
                schema.warnings.append(f"Breadcrumb item {i+1}: Missing position")
            if not item.get('name') and not item.get('item', {}).get('name'):
                schema.warnings.append(f"Breadcrumb item {i+1}: Missing name")

    def _validate_article(self, data: dict, schema: SchemaItem):
        """Validate Article specific requirements"""
        # Check author format
        author = data.get('author')
        if author:
            if isinstance(author, str):
                schema.warnings.append("author should be a Person or Organization object, not a string")
            elif isinstance(author, dict):
                if '@type' not in author:
                    schema.warnings.append("author object missing @type")

        # Check date format
        date_published = data.get('datePublished', '')
        if date_published and not re.match(r'\d{4}-\d{2}-\d{2}', date_published):
            schema.warnings.append("datePublished should be in ISO 8601 format (YYYY-MM-DD)")

    def _count_microdata(self, soup: BeautifulSoup) -> int:
        """Count microdata items"""
        return len(soup.find_all(attrs={'itemscope': True}))

    def print_result(self, result: SchemaAnalysisResult):
        """Print schema analysis result"""
        print(f"\n{'='*60}")
        print(f"Schema Analysis: {result.url}")
        print('='*60)

        # Score
        if result.score >= 80:
            color = Colors.GREEN
        elif result.score >= 50:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        print(f"\nSchema Score: {color}{result.score}/100{Colors.RESET}")
        print(f"Total Schemas: {result.total_schemas} (Valid: {result.valid_schemas}, Invalid: {result.invalid_schemas})")

        # Schema details
        if result.schemas:
            print(f"\n{Colors.BOLD}Found Schemas:{Colors.RESET}")
            for schema in result.schemas:
                status = "✓" if schema.is_valid else "✗"
                color = Colors.GREEN if schema.is_valid else Colors.RED
                print(f"\n  {color}{status}{Colors.RESET} {schema.schema_type} ({schema.format})")

                if schema.errors:
                    for error in schema.errors:
                        print(f"    {Colors.RED}ERROR: {error}{Colors.RESET}")

                if schema.warnings:
                    for warning in schema.warnings:
                        print(f"    {Colors.YELLOW}WARN: {warning}{Colors.RESET}")

                if schema.missing_recommended:
                    print(f"    Missing recommended: {', '.join(schema.missing_recommended)}")

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
