"""Central coordinator that mirrors Page Assist style web search orchestration."""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List, Optional

from .analytics import SearchAnalytics
from .cache import SearchCache
from .content_loader import ContentLoader
from .providers import BingProvider, DuckDuckGoProvider, SearchProvider, SearxngProvider
from .result_filter import ResultFilter
from .settings import SearchSettings
from .types import SearchExecution, SearchResult
from .utils import (
    choose_relevant_snippet,
    detect_urls_in_query,
    escape_for_prompt,
    hostname_from_url,
)


class SearchManager:
    """Facade responsible for selecting providers and shaping structured prompts."""

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.settings = SearchSettings.from_config(config or {})
        self.providers: Dict[str, SearchProvider] = {}
        self._register_providers()
        self.content_loader = ContentLoader(
            user_agent=self.settings.user_agent,
            timeout=self.settings.request_timeout,
        )
        self.result_filter = ResultFilter(config)
        cache_config = config.get('cache', {}) if config else {}
        self.cache = SearchCache(cache_config)
        analytics_config = config.get('analytics', {}) if config else {}
        self.analytics = SearchAnalytics(analytics_config)

    def _register_providers(self) -> None:
        searxng_toggle = self.settings.provider_toggles.get("searxng")
        if searxng_toggle is None or searxng_toggle.enabled:
            self.providers["searxng"] = SearxngProvider(self.settings)
        duck_toggle = self.settings.provider_toggles.get("duckduckgo")
        if duck_toggle is None or duck_toggle.enabled:
            self.providers["duckduckgo"] = DuckDuckGoProvider(self.settings)
        bing_toggle = self.settings.provider_toggles.get("bing")
        if bing_toggle is None or bing_toggle.enabled:
            self.providers["bing"] = BingProvider(self.settings)

    def _select_provider(self, override: Optional[str] = None) -> Optional[SearchProvider]:
        provider_name = (override or self.settings.default_provider or "").lower()
        provider = self.providers.get(provider_name)
        if provider:
            return provider
        # If fallbacks are disabled, do not select any alternative provider
        if self.settings.disable_fallbacks:
            return None
        # fallback ordering similar to Page Assist
        for candidate in ("searxng", "duckduckgo", "bing"):
            if candidate in self.providers:
                return self.providers[candidate]
        return None

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

        provider = self._select_provider(provider_override)
        if provider is None:
            return SearchExecution(
                query=query,
                provider="unknown",
                success=False,
                error="No search providers are available.",
            )

        # Check cache first
        cached_results = self.cache.get(query, max_results, provider.name)
        if cached_results:
            self.logger.info(f"Cache hit for query: {query} (provider: {provider.name})")
            prompt = self.build_prompt(cached_results)
            sources = self.build_sources(cached_results)
            execution = SearchExecution(
                query=query,
                provider=f"{provider.name} (cached)",
                success=True,
                results=cached_results,
                prompt=prompt,
                sources=sources,
            )
            self.analytics.record_search(execution, time.time() - start_time, cache_hit=True)
            return execution

        results = provider.search(query, max_results)
        if (
            not self.settings.disable_fallbacks
            and not results
            and provider.name != "duckduckgo"
        ):
            fallback = self.providers.get("duckduckgo")
            if fallback:
                self.logger.info(
                    "Primary provider %s returned no results. Falling back to DuckDuckGo.",
                    provider.name,
                )
                results = fallback.search(query, max_results)
                provider = fallback

        results = results[:max_results]

        if not results:
            execution = SearchExecution(
                query=query,
                provider=provider.name,
                success=False,
                error="No results returned from provider.",
            )
            self.analytics.record_search(execution, time.time() - start_time)
            return execution

        # Apply advanced filtering and ranking
        original_result_count = len(results)
        results = self.result_filter.filter_and_rank_results(results, query)
        filtered_count = original_result_count - len(results)

        if not results:
            execution = SearchExecution(
                query=query,
                provider=provider.name,
                success=False,
                error="No results remained after filtering.",
            )
            self.analytics.record_search(execution, time.time() - start_time, filtered_count=filtered_count)
            return execution

        if self.settings.simple_mode:
            for result in results:
                result.content = result.snippet
        else:
            self.enrich_results(results, query)

        prompt = self.build_prompt(results)
        sources = self.build_sources(results)

        # Cache successful results
        if results:
            cache_ttl = self.settings.cache_ttl if hasattr(self.settings, 'cache_ttl') else None
            self.cache.set(query, max_results, provider.name, results, cache_ttl)

        execution = SearchExecution(
            query=query,
            provider=provider.name,
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
