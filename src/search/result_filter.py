"""Advanced result filtering and ranking system."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from .types import SearchResult


class ResultFilter:
    """Advanced filtering and ranking for search results."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Configuration options
        self.min_content_length = self.config.get('min_content_length', 100)
        self.max_content_length = self.config.get('max_content_length', 5000)
        self.min_title_length = self.config.get('min_title_length', 5)
        self.max_title_length = self.config.get('max_title_length', 200)
        self.enable_duplicate_detection = self.config.get('enable_duplicate_detection', True)
        self.duplicate_threshold = self.config.get('duplicate_threshold', 0.8)
        self.enable_domain_filtering = self.config.get('enable_domain_filtering', False)
        self.allowed_domains = set(self.config.get('allowed_domains', []))
        self.blocked_domains = set(self.config.get('blocked_domains', []))
        self.enable_relevance_scoring = self.config.get('enable_relevance_scoring', True)
        self.query_weight = self.config.get('query_weight', 2.0)
        self.title_weight = self.config.get('title_weight', 1.5)
        self.content_weight = self.config.get('content_weight', 1.0)

    def filter_and_rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Filter and rank search results based on quality and relevance."""
        if not results:
            return results

        self.logger.info(f"Filtering and ranking {len(results)} results for query: {query}")

        # Step 1: Basic filtering
        filtered_results = self._apply_basic_filters(results)
        self.logger.info(f"After basic filtering: {len(filtered_results)} results")

        # Step 2: Duplicate detection and removal
        if self.enable_duplicate_detection:
            filtered_results = self._remove_duplicates(filtered_results)
            self.logger.info(f"After duplicate removal: {len(filtered_results)} results")

        # Step 3: Domain filtering (if enabled)
        if self.enable_domain_filtering:
            filtered_results = self._apply_domain_filters(filtered_results)
            self.logger.info(f"After domain filtering: {len(filtered_results)} results")

        # Step 4: Relevance scoring and ranking
        if self.enable_relevance_scoring:
            filtered_results = self._rank_by_relevance(filtered_results, query)
            self.logger.info(f"After relevance ranking: {len(filtered_results)} results")

        return filtered_results

    def _apply_basic_filters(self, results: List[SearchResult]) -> List[SearchResult]:
        """Apply basic quality filters."""
        filtered = []

        for result in results:
            # Check URL validity
            if not result.url or not self._is_valid_url(result.url):
                continue

            # Check title length
            title = result.title or ""
            if len(title) < self.min_title_length or len(title) > self.max_title_length:
                continue

            # Check snippet/content length
            content = (result.content or result.snippet or "")
            if len(content) < self.min_content_length or len(content) > self.max_content_length:
                continue

            # Check for spam indicators
            if self._is_spam(result):
                continue

            filtered.append(result)

        return filtered

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def _is_spam(self, result: SearchResult) -> bool:
        """Check for spam indicators in search results."""
        title = (result.title or "").lower()
        snippet = (result.snippet or "").lower()

        # Common spam indicators
        spam_indicators = [
            'click here',
            'buy now',
            'limited time',
            'free download',
            'win a prize',
            'congratulations',
            'urgent',
            'act now',
            'risk free',
            'guaranteed',
        ]

        spam_count = sum(1 for indicator in spam_indicators if indicator in title or indicator in snippet)
        return spam_count >= 2  # Flag as spam if 2+ indicators found

    def _remove_duplicates(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity."""
        if not results:
            return results

        unique_results = []
        seen_hashes: Set[str] = set()

        for result in results:
            # Create hash of normalized content
            content_hash = self._get_content_hash(result)

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(result)

        return unique_results

    def _get_content_hash(self, result: SearchResult) -> str:
        """Generate a hash for duplicate detection."""
        # Normalize content for comparison
        title = (result.title or "").lower().strip()
        snippet = (result.snippet or "").lower().strip()
        url = result.url.lower().strip()

        # Create a normalized string for hashing
        content = f"{title}|{snippet}|{url}"

        # Remove extra whitespace and normalize
        content = re.sub(r'\s+', ' ', content).strip()

        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _apply_domain_filters(self, results: List[SearchResult]) -> List[SearchResult]:
        """Apply domain-based filtering."""
        filtered = []

        for result in results:
            try:
                domain = urlparse(result.url).netloc.lower()

                # Check blocked domains
                if any(blocked in domain for blocked in self.blocked_domains):
                    continue

                # Check allowed domains (if specified)
                if self.allowed_domains and not any(allowed in domain for allowed in self.allowed_domains):
                    continue

                filtered.append(result)

            except Exception as e:
                self.logger.warning(f"Error processing domain for {result.url}: {e}")
                continue

        return filtered

    def _rank_by_relevance(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results by relevance to the query."""
        query_terms = self._extract_query_terms(query)

        # Score each result
        for result in results:
            score = self._calculate_relevance_score(result, query_terms)
            result.relevance_score = score

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.relevance_score or 0, reverse=True)

        return results

    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract meaningful terms from query for relevance scoring."""
        if not query:
            return []

        # Remove common stop words and punctuation
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'do', 'does', 'did', 'what', 'when',
            'where', 'who', 'why', 'how', 'which', 'this', 'these', 'those'
        }

        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', query.lower())

        # Filter out stop words and short words
        terms = [word for word in words if word not in stop_words and len(word) > 2]

        return terms

    def _calculate_relevance_score(self, result: SearchResult, query_terms: List[str]) -> float:
        """Calculate relevance score for a result."""
        if not query_terms:
            return 1.0

        title = (result.title or "").lower()
        snippet = (result.snippet or "").lower()
        content = (result.content or "").lower()

        total_score = 0.0

        for term in query_terms:
            # Title matches (highest weight)
            title_matches = title.count(term)
            total_score += title_matches * self.title_weight

            # Snippet matches
            snippet_matches = snippet.count(term)
            total_score += snippet_matches * 0.7

            # Content matches
            content_matches = content.count(term)
            total_score += content_matches * self.content_weight

        # Normalize by query length
        if total_score > 0:
            # Boost score for exact phrase matches
            exact_phrase_bonus = self._calculate_phrase_bonus(title + " " + snippet, query_terms)
            total_score += exact_phrase_bonus

            # Normalize by the number of query terms
            total_score = total_score / len(query_terms)

        return total_score

    def _calculate_phrase_bonus(self, text: str, query_terms: List[str]) -> float:
        """Calculate bonus for consecutive term matches."""
        if len(query_terms) < 2:
            return 0.0

        text_lower = text.lower()
        bonus = 0.0

        # Check for consecutive pairs
        for i in range(len(query_terms) - 1):
            pair = f"{query_terms[i]} {query_terms[i + 1]}"
            if pair in text_lower:
                bonus += 0.5

        return bonus


def create_result_filter(config: Optional[Dict] = None) -> ResultFilter:
    """Factory function to create a ResultFilter instance."""
    return ResultFilter(config)
