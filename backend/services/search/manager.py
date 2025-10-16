"""Central coordinator using TypeScript search (Page Assist original code)."""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List, Optional

from .analytics import SearchAnalytics
from .cache import SearchCache
from .content_loader import ContentLoader
from .result_filter import ResultFilter
from .settings import SearchSettings
from .typescript_bridge import TypeScriptSearchBridge
from .types import SearchExecution, SearchResult
from .utils import (
    choose_relevant_snippet,
    detect_urls_in_query,
    escape_for_prompt,
    hostname_from_url,
)


class SearchManager:
    """Search manager using TypeScript providers only (Page Assist original code)."""

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.settings = SearchSettings.from_config(config or {})
        self.content_loader = ContentLoader(
            user_agent=self.settings.user_agent,
            timeout=self.settings.request_timeout,
        )
        self.result_filter = ResultFilter(config)
        cache_config = config.get('cache', {}) if config else {}
        self.cache = SearchCache(cache_config)
        analytics_config = config.get('analytics', {}) if config else {}
        self.analytics = SearchAnalytics(analytics_config)

        # TypeScript bridge - ONLY search method (removed Python providers)
        try:
            self.ts_bridge = TypeScriptSearchBridge(config or {})
            self.logger.info("✅ TypeScript search bridge initialized (Page Assist original code)")
        except Exception as e:
            self.logger.error(f"TypeScript bridge failed to initialize: {e}")
            raise RuntimeError("TypeScript search bridge is required but failed to initialize")

    def _get_provider_name(self, override: Optional[str] = None) -> str:
        """Get provider name from override or default settings."""
        provider_name = (override or self.settings.default_provider or "google").lower()

        # Validate provider is supported by TypeScript
        supported_providers = ["google", "duckduckgo", "brave_api", "tavily_api", "exa_api"]
        if provider_name not in supported_providers:
            self.logger.warning(f"Provider '{provider_name}' not supported, falling back to 'google'")
            return "google"

        return provider_name

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        provider_override: Optional[str] = None,
    ) -> SearchExecution:
        max_results = max_results or self.settings.total_results
        start_time = time.time()

        if not self.settings.enabled:
            execution = SearchExecution(
                query=query,
                provider="disabled",
                success=False,
                error="Web search is disabled in configuration.",
            )
            self.analytics.record_search(execution, time.time() - start_time)
            return execution

        # Handle direct website visits
        website_detection = detect_urls_in_query(query)
        if self.settings.visit_specific_website and website_detection.urls:
            self.logger.info("Processing direct website visit for %s", website_detection.urls)
            results = self._process_direct_websites(
                website_detection.urls,
                website_detection.cleaned_query or query,
                max_results,
            )
            prompt = self.build_prompt(results)
            sources = self.build_sources(results)
            return SearchExecution(
                query=query,
                provider="direct-url",
                success=len(results) > 0,
                results=results,
                prompt=prompt,
                sources=sources,
            )

        # Get provider name
        provider_name = self._get_provider_name(provider_override)

        # Check cache first
        cached_results = self.cache.get(query, max_results, provider_name)
        if cached_results:
            self.logger.info(f"Cache hit for query: {query} (provider: {provider_name})")
            prompt = self.build_prompt(cached_results)
            sources = self.build_sources(cached_results)
            execution = SearchExecution(
                query=query,
                provider=f"{provider_name} (cached)",
                success=True,
                results=cached_results,
                prompt=prompt,
                sources=sources,
            )
            self.analytics.record_search(execution, time.time() - start_time, cache_hit=True)
            return execution

        # Use TypeScript bridge (Page Assist original code - ONLY METHOD)
        try:
            self.logger.info(f"🚀 Using TypeScript search (Page Assist original): {provider_name}")
            ts_result = self.ts_bridge.search(query, provider_name, max_results)

            if not ts_result.get("success"):
                error_msg = ts_result.get("error", "Unknown error")
                self.logger.error(f"TypeScript search failed: {error_msg}")
                execution = SearchExecution(
                    query=query,
                    provider=provider_name,
                    success=False,
                    error=f"TypeScript search failed: {error_msg}",
                )
                self.analytics.record_search(execution, time.time() - start_time)
                return execution

            # Convert to SearchResult objects
            results = []
            for item in ts_result.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("source", provider_name)
                ))

            self.logger.info(f"✅ TypeScript search returned {len(results)} results")

        except Exception as e:
            self.logger.error(f"TypeScript search error: {e}")
            execution = SearchExecution(
                query=query,
                provider=provider_name,
                success=False,
                error=f"TypeScript search exception: {str(e)}",
            )
            self.analytics.record_search(execution, time.time() - start_time)
            return execution

        # Handle no results
        if not results:
            execution = SearchExecution(
                query=query,
                provider=provider_name,
                success=False,
                error="No results returned from provider.",
            )
            self.analytics.record_search(execution, time.time() - start_time)
            return execution

        # Limit results
        results = results[:max_results]

        # Apply advanced filtering and ranking
        original_result_count = len(results)
        results = self.result_filter.filter_and_rank_results(results, query)
        filtered_count = original_result_count - len(results)

        if not results:
            execution = SearchExecution(
                query=query,
                provider=provider_name,
                success=False,
                error="No results remained after filtering.",
            )
            self.analytics.record_search(execution, time.time() - start_time, filtered_count=filtered_count)
            return execution

        # Enrich results with content
        if self.settings.simple_mode:
            for result in results:
                result.content = result.snippet
        else:
            self.enrich_results(results, query)

        # Build prompt and sources
        prompt = self.build_prompt(results)
        sources = self.build_sources(results)

        # Cache successful results
        if results:
            cache_ttl = self.settings.cache_ttl if hasattr(self.settings, 'cache_ttl') else None
            self.cache.set(query, max_results, provider_name, results, cache_ttl)

        execution = SearchExecution(
            query=query,
            provider=provider_name,
            success=True,
            results=results,
            prompt=prompt,
            sources=sources,
        )
        self.analytics.record_search(execution, time.time() - start_time, filtered_count=filtered_count)
        return execution

    def enrich_results(self, results: List[SearchResult], query: str) -> None:
        for result in results:
            if not result.url:
                continue
            text = self.content_loader.load(result.url)
            if not text:
                continue
            relevant = choose_relevant_snippet(text, query)
            result.content = relevant
            # Provide an updated snippet that reflects the richer content.
            result.snippet = relevant[:300]

    def _process_direct_websites(
        self,
        urls: Iterable[str],
        cleaned_query: str,
        max_results: int,
    ) -> List[SearchResult]:
        processed: List[SearchResult] = []
        for url in urls:
            if len(processed) >= max_results:
                break
            text = self.content_loader.load(url)
            if not text:
                continue
            snippet = choose_relevant_snippet(text, cleaned_query or url)
            processed.append(
                SearchResult(
                    title=url,
                    url=url,
                    snippet=snippet[:300],
                    source="direct",
                    content=snippet,
                )
        )
        return processed

    def build_prompt(self, results: List[SearchResult]) -> str:
        prompt_segments = []
        for idx, result in enumerate(results):
            body = result.content or result.snippet or ""
            prompt_segments.append(
                f'<result source="{escape_for_prompt(result.url)}" id="{idx}">'
                f"{escape_for_prompt(body)}</result>"
            )
        return "\n".join(prompt_segments)

    def build_sources(self, results: List[SearchResult]) -> List[Dict[str, str]]:
        sources = []
        for result in results:
            if not result.url:
                continue
            sources.append(
                {
                    "url": result.url,
                    "name": hostname_from_url(result.url),
                    "type": "url",
                }
            )
        return sources

    def get_analytics_report(self) -> Dict[str, Any]:
        """Get comprehensive analytics report."""
        return self.analytics.get_performance_report()

    def get_search_stats(self) -> Dict[str, Any]:
        """Get basic search statistics."""
        return self.analytics.get_overall_stats()

    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently searched queries."""
        return self.analytics.get_top_queries(limit)

    def clear_analytics(self) -> None:
        """Clear all analytics data."""
        self.analytics.reset_stats()
        self.logger.info("Search analytics cleared")

    def cleanup_analytics(self) -> None:
        """Clean up old analytics data."""
        self.analytics.cleanup_old_data()
