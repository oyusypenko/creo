#!/usr/bin/env python3
"""
Content Quality Analyzer

Analyzes content quality metrics:
- Readability scores (Flesch-Kincaid, Gunning Fog, etc.)
- Content freshness (dates, Last-Modified)
- Text quality issues
- Keyword analysis
- Language detection
"""

import re
import math
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from urllib.parse import urlparse

from ..core.utils import print_header, print_success, print_warning, print_error, print_info, Colors

# Try to import optional dependencies
try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False

try:
    from langdetect import detect, detect_langs
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False


@dataclass
class ReadabilityMetrics:
    """Readability analysis results"""
    flesch_reading_ease: float = 0.0  # 0-100, higher = easier
    flesch_kincaid_grade: float = 0.0  # US grade level
    gunning_fog: float = 0.0  # Years of education needed
    smog_index: float = 0.0
    coleman_liau_index: float = 0.0
    automated_readability_index: float = 0.0
    dale_chall_score: float = 0.0
    reading_time_minutes: float = 0.0
    speaking_time_minutes: float = 0.0

    # Text statistics
    sentence_count: int = 0
    word_count: int = 0
    char_count: int = 0
    syllable_count: int = 0
    avg_sentence_length: float = 0.0
    avg_word_length: float = 0.0
    difficult_words_count: int = 0
    difficult_words_percentage: float = 0.0


@dataclass
class ContentFreshness:
    """Content freshness analysis"""
    last_modified_header: str = ''
    last_modified_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    content_age_days: int = -1
    freshness_status: str = 'unknown'  # fresh, aging, stale, unknown
    date_sources: List[str] = field(default_factory=list)


@dataclass
class LanguageAnalysis:
    """Language detection results"""
    detected_language: str = ''
    confidence: float = 0.0
    url_language: str = ''
    html_lang: str = ''
    meta_language: str = ''
    language_match: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class TextQuality:
    """Text quality issues"""
    has_spelling_issues: bool = False
    spelling_errors: List[str] = field(default_factory=list)
    has_all_caps_text: bool = False
    all_caps_count: int = 0
    has_excessive_punctuation: bool = False
    duplicate_sentences: List[str] = field(default_factory=list)
    very_long_sentences: List[str] = field(default_factory=list)
    very_short_paragraphs: int = 0


@dataclass
class KeywordAnalysis:
    """Basic keyword analysis"""
    top_words: List[Dict] = field(default_factory=list)  # [{word, count, density}]
    top_phrases: List[Dict] = field(default_factory=list)  # 2-3 word phrases
    title_keywords: List[str] = field(default_factory=list)
    h1_keywords: List[str] = field(default_factory=list)
    first_100_words: List[str] = field(default_factory=list)


@dataclass
class ContentAnalysisResult:
    """Complete content analysis result"""
    url: str
    readability: ReadabilityMetrics = field(default_factory=ReadabilityMetrics)
    freshness: ContentFreshness = field(default_factory=ContentFreshness)
    language: LanguageAnalysis = field(default_factory=LanguageAnalysis)
    text_quality: TextQuality = field(default_factory=TextQuality)
    keywords: KeywordAnalysis = field(default_factory=KeywordAnalysis)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: int = 0


class ContentAnalyzer:
    """Analyzes content quality metrics"""

    # Stop words for keyword analysis
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose',
        'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GSCToolkit/2.2; Content Analyzer)'
        })

    def analyze_url(self, url: str) -> ContentAnalysisResult:
        """Analyze content quality of a URL"""
        result = ContentAnalysisResult(url=url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                result.issues.append(f"Failed to fetch: HTTP {response.status_code}")
                return result

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract text content
            text = self._extract_text(soup)

            # Analyze readability
            result.readability = self._analyze_readability(text)

            # Analyze freshness
            result.freshness = self._analyze_freshness(response, soup)

            # Analyze language
            result.language = self._analyze_language(url, soup, text)

            # Analyze text quality
            result.text_quality = self._analyze_text_quality(text, soup)

            # Analyze keywords
            result.keywords = self._analyze_keywords(soup, text)

            # Generate issues and recommendations
            self._generate_issues(result)

            # Calculate score
            result.score = self._calculate_score(result)

        except requests.RequestException as e:
            result.issues.append(f"Request failed: {str(e)}")

        return result

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract visible text from HTML"""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)

        return text

    def _analyze_readability(self, text: str) -> ReadabilityMetrics:
        """Analyze text readability"""
        metrics = ReadabilityMetrics()

        if not text or len(text) < 100:
            return metrics

        # Count basic statistics
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()

        metrics.sentence_count = len(sentences)
        metrics.word_count = len(words)
        metrics.char_count = len(text)

        if metrics.sentence_count > 0:
            metrics.avg_sentence_length = metrics.word_count / metrics.sentence_count

        if metrics.word_count > 0:
            metrics.avg_word_length = sum(len(w) for w in words) / metrics.word_count

        # Reading time (avg 200-250 words per minute)
        metrics.reading_time_minutes = round(metrics.word_count / 225, 1)
        metrics.speaking_time_minutes = round(metrics.word_count / 150, 1)

        # Use textstat if available
        if HAS_TEXTSTAT:
            try:
                metrics.flesch_reading_ease = textstat.flesch_reading_ease(text)
                metrics.flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
                metrics.gunning_fog = textstat.gunning_fog(text)
                metrics.smog_index = textstat.smog_index(text)
                metrics.coleman_liau_index = textstat.coleman_liau_index(text)
                metrics.automated_readability_index = textstat.automated_readability_index(text)
                metrics.dale_chall_score = textstat.dale_chall_readability_score(text)
                metrics.syllable_count = textstat.syllable_count(text)
                metrics.difficult_words_count = textstat.difficult_words(text)

                if metrics.word_count > 0:
                    metrics.difficult_words_percentage = (
                        metrics.difficult_words_count / metrics.word_count * 100
                    )
            except:
                pass
        else:
            # Fallback: simple Flesch-Kincaid approximation
            metrics.syllable_count = self._count_syllables(text)
            if metrics.sentence_count > 0 and metrics.word_count > 0:
                asl = metrics.word_count / metrics.sentence_count
                asw = metrics.syllable_count / metrics.word_count
                metrics.flesch_reading_ease = 206.835 - (1.015 * asl) - (84.6 * asw)
                metrics.flesch_kincaid_grade = (0.39 * asl) + (11.8 * asw) - 15.59

        return metrics

    def _count_syllables(self, text: str) -> int:
        """Simple syllable counter"""
        text = text.lower()
        count = 0
        vowels = 'aeiouy'
        words = text.split()

        for word in words:
            word_count = 0
            prev_was_vowel = False

            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_was_vowel:
                    word_count += 1
                prev_was_vowel = is_vowel

            # Handle silent e
            if word.endswith('e') and word_count > 1:
                word_count -= 1

            count += max(1, word_count)

        return count

    def _analyze_freshness(self, response: requests.Response, soup: BeautifulSoup) -> ContentFreshness:
        """Analyze content freshness"""
        freshness = ContentFreshness()

        # Check Last-Modified header
        last_modified = response.headers.get('Last-Modified')
        if last_modified:
            freshness.last_modified_header = last_modified
            freshness.date_sources.append('Last-Modified header')
            try:
                # Parse RFC 2822 date
                from email.utils import parsedate_to_datetime
                freshness.last_modified_date = parsedate_to_datetime(last_modified)
            except:
                pass

        # Check schema.org dates
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}

                # datePublished
                if 'datePublished' in data:
                    date_str = data['datePublished']
                    freshness.published_date = self._parse_date(date_str)
                    freshness.date_sources.append('Schema.org datePublished')

                # dateModified
                if 'dateModified' in data:
                    date_str = data['dateModified']
                    freshness.modified_date = self._parse_date(date_str)
                    freshness.date_sources.append('Schema.org dateModified')
            except:
                pass

        # Check meta tags
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '') or meta.get('name', '')
            content = meta.get('content', '')

            if prop in ['article:published_time', 'og:published_time']:
                freshness.published_date = self._parse_date(content)
                freshness.date_sources.append(f'Meta {prop}')
            elif prop in ['article:modified_time', 'og:updated_time']:
                freshness.modified_date = self._parse_date(content)
                freshness.date_sources.append(f'Meta {prop}')

        # Check time elements
        for time_el in soup.find_all('time'):
            datetime_attr = time_el.get('datetime')
            if datetime_attr:
                parsed = self._parse_date(datetime_attr)
                if parsed and not freshness.published_date:
                    freshness.published_date = parsed
                    freshness.date_sources.append('HTML time element')

        # Calculate content age
        reference_date = (
            freshness.modified_date or
            freshness.published_date or
            freshness.last_modified_date
        )

        if reference_date:
            now = datetime.now(reference_date.tzinfo) if reference_date.tzinfo else datetime.now()
            age = now - reference_date
            freshness.content_age_days = age.days

            # Determine freshness status
            if age.days <= 30:
                freshness.freshness_status = 'fresh'
            elif age.days <= 180:
                freshness.freshness_status = 'recent'
            elif age.days <= 365:
                freshness.freshness_status = 'aging'
            else:
                freshness.freshness_status = 'stale'

        return freshness

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%d %B %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:26], fmt)
            except:
                continue

        return None

    def _analyze_language(self, url: str, soup: BeautifulSoup, text: str) -> LanguageAnalysis:
        """Analyze language consistency"""
        analysis = LanguageAnalysis()

        # Extract URL language (e.g., /en/, /uk/, /fr/)
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and len(path_parts[0]) == 2:
            analysis.url_language = path_parts[0].lower()

        # HTML lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            analysis.html_lang = html_tag.get('lang', '').split('-')[0].lower()

        # Meta language
        meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if meta_lang:
            analysis.meta_language = meta_lang.get('content', '').split('-')[0].lower()

        # Detect content language
        if HAS_LANGDETECT and text and len(text) > 50:
            try:
                analysis.detected_language = detect(text)
                langs = detect_langs(text)
                if langs:
                    analysis.confidence = langs[0].prob
            except:
                pass

        # Check for mismatches
        languages = [
            analysis.url_language,
            analysis.html_lang,
            analysis.detected_language
        ]
        languages = [l for l in languages if l]

        if len(set(languages)) > 1:
            analysis.language_match = False
            analysis.issues.append(
                f"Language mismatch: URL={analysis.url_language}, "
                f"HTML={analysis.html_lang}, Detected={analysis.detected_language}"
            )

        return analysis

    def _analyze_text_quality(self, text: str, soup: BeautifulSoup) -> TextQuality:
        """Analyze text quality issues"""
        quality = TextQuality()

        if not text:
            return quality

        # Check for ALL CAPS text (words with 4+ characters)
        words = text.split()
        all_caps_words = [w for w in words if len(w) >= 4 and w.isupper()]
        quality.all_caps_count = len(all_caps_words)
        quality.has_all_caps_text = quality.all_caps_count > 5

        # Check for excessive punctuation
        punct_count = sum(1 for c in text if c in '!?')
        quality.has_excessive_punctuation = punct_count > 10

        # Find very long sentences (>40 words)
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > 40:
                quality.very_long_sentences.append(sentence[:100] + '...')

        # Check paragraph lengths
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            p_text = p.get_text(strip=True)
            if p_text and len(p_text.split()) < 20:
                quality.very_short_paragraphs += 1

        # Find duplicate sentences
        seen_sentences = {}
        for sentence in sentences:
            sentence = sentence.strip().lower()
            if len(sentence) > 30:  # Only check substantial sentences
                if sentence in seen_sentences:
                    quality.duplicate_sentences.append(sentence[:80])
                else:
                    seen_sentences[sentence] = True

        return quality

    def _analyze_keywords(self, soup: BeautifulSoup, text: str) -> KeywordAnalysis:
        """Analyze keyword usage"""
        keywords = KeywordAnalysis()

        if not text:
            return keywords

        # Get words from text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.STOP_WORDS]

        # Count word frequency
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Top words with density
        total_words = len(words)
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        for word, count in sorted_words[:15]:
            density = (count / total_words * 100) if total_words > 0 else 0
            keywords.top_words.append({
                'word': word,
                'count': count,
                'density': round(density, 2)
            })

        # Extract title keywords
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True).lower()
            keywords.title_keywords = [
                w for w in re.findall(r'\b[a-zA-Z]{3,}\b', title_text)
                if w not in self.STOP_WORDS
            ]

        # Extract H1 keywords
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.get_text(strip=True).lower()
            keywords.h1_keywords = [
                w for w in re.findall(r'\b[a-zA-Z]{3,}\b', h1_text)
                if w not in self.STOP_WORDS
            ]

        # First 100 words
        first_100 = words[:100]
        keywords.first_100_words = list(set(first_100))[:20]

        # Find 2-word phrases
        phrase_counts = {}
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        for phrase, count in sorted_phrases[:10]:
            if count >= 2:
                keywords.top_phrases.append({
                    'phrase': phrase,
                    'count': count
                })

        return keywords

    def _generate_issues(self, result: ContentAnalysisResult):
        """Generate issues and recommendations"""

        # Readability issues
        r = result.readability
        if r.flesch_kincaid_grade > 12:
            result.issues.append(f"Content is too complex (Grade {r.flesch_kincaid_grade:.1f}, target: 6-8)")
            result.recommendations.append("Simplify text: use shorter sentences and simpler words")

        if r.avg_sentence_length > 25:
            result.issues.append(f"Sentences too long (avg {r.avg_sentence_length:.0f} words)")
            result.recommendations.append("Break long sentences into shorter ones")

        if r.word_count < 300:
            result.issues.append(f"Thin content ({r.word_count} words)")
            result.recommendations.append("Expand content to at least 300-500 words")

        # Freshness issues
        f = result.freshness
        if f.freshness_status == 'stale':
            result.issues.append(f"Content is stale ({f.content_age_days} days old)")
            result.recommendations.append("Update content with fresh information")
        elif f.freshness_status == 'unknown' and not f.date_sources:
            result.issues.append("No publication date found")
            result.recommendations.append("Add datePublished/dateModified to schema markup")

        # Language issues
        if result.language.issues:
            result.issues.extend(result.language.issues)
            result.recommendations.append("Ensure HTML lang attribute matches content language")

        # Text quality issues
        q = result.text_quality
        if q.has_all_caps_text:
            result.issues.append(f"Excessive ALL CAPS text ({q.all_caps_count} words)")
            result.recommendations.append("Avoid using all caps for emphasis")

        if q.duplicate_sentences:
            result.issues.append(f"Duplicate sentences found ({len(q.duplicate_sentences)})")
            result.recommendations.append("Remove or rewrite duplicate content")

        if q.very_long_sentences:
            result.issues.append(f"Very long sentences found ({len(q.very_long_sentences)})")

    def _calculate_score(self, result: ContentAnalysisResult) -> int:
        """Calculate overall content score"""
        score = 100

        # Readability (30 points)
        r = result.readability
        if r.flesch_kincaid_grade > 12:
            score -= 15
        elif r.flesch_kincaid_grade > 10:
            score -= 8
        elif r.flesch_kincaid_grade > 8:
            score -= 3

        if r.word_count < 300:
            score -= 15
        elif r.word_count < 500:
            score -= 5

        # Freshness (25 points)
        f = result.freshness
        if f.freshness_status == 'stale':
            score -= 15
        elif f.freshness_status == 'aging':
            score -= 8
        elif f.freshness_status == 'unknown':
            score -= 10

        # Language (15 points)
        if not result.language.language_match:
            score -= 15

        # Text quality (30 points)
        q = result.text_quality
        if q.has_all_caps_text:
            score -= 10
        if q.duplicate_sentences:
            score -= 10
        if q.very_long_sentences:
            score -= 5
        if q.has_excessive_punctuation:
            score -= 5

        return max(0, min(100, score))

    def print_result(self, result: ContentAnalysisResult):
        """Print content analysis result"""
        print_header(f"Content Analysis: {result.url}")

        # Score
        score_color = Colors.GREEN if result.score >= 80 else Colors.YELLOW if result.score >= 50 else Colors.RED
        print(f"\nContent Score: {score_color}{result.score}/100{Colors.RESET}")

        # Readability
        r = result.readability
        print(f"\n{Colors.BOLD}Readability:{Colors.RESET}")
        print(f"  Word count:          {r.word_count}")
        print(f"  Sentence count:      {r.sentence_count}")
        print(f"  Avg sentence length: {r.avg_sentence_length:.1f} words")
        print(f"  Reading time:        {r.reading_time_minutes} min")

        if HAS_TEXTSTAT:
            print(f"  Flesch Reading Ease: {r.flesch_reading_ease:.1f}")
            print(f"  Flesch-Kincaid Grade:{r.flesch_kincaid_grade:.1f}")
            print(f"  Gunning Fog Index:   {r.gunning_fog:.1f}")
            print(f"  Difficult words:     {r.difficult_words_percentage:.1f}%")

        # Freshness
        f = result.freshness
        print(f"\n{Colors.BOLD}Content Freshness:{Colors.RESET}")
        status_color = {
            'fresh': Colors.GREEN,
            'recent': Colors.GREEN,
            'aging': Colors.YELLOW,
            'stale': Colors.RED,
            'unknown': Colors.YELLOW
        }.get(f.freshness_status, Colors.RESET)
        print(f"  Status: {status_color}{f.freshness_status}{Colors.RESET}")

        if f.content_age_days >= 0:
            print(f"  Age: {f.content_age_days} days")
        if f.date_sources:
            print(f"  Sources: {', '.join(f.date_sources)}")

        # Language
        l = result.language
        if l.detected_language or l.html_lang:
            print(f"\n{Colors.BOLD}Language:{Colors.RESET}")
            if l.detected_language:
                print(f"  Detected: {l.detected_language} (confidence: {l.confidence:.0%})")
            if l.html_lang:
                print(f"  HTML lang: {l.html_lang}")
            if l.url_language:
                print(f"  URL language: {l.url_language}")
            if not l.language_match:
                print(f"  {Colors.RED}⚠ Language mismatch detected{Colors.RESET}")

        # Keywords
        k = result.keywords
        if k.top_words:
            print(f"\n{Colors.BOLD}Top Keywords:{Colors.RESET}")
            for kw in k.top_words[:10]:
                print(f"  {kw['word']}: {kw['count']}x ({kw['density']}%)")

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

    def analyze_batch(self, urls: List[str]) -> List[ContentAnalysisResult]:
        """Analyze multiple URLs"""
        results = []
        for url in urls:
            print_info(f"Analyzing: {url}")
            result = self.analyze_url(url)
            results.append(result)
            self.print_result(result)
        return results
