"""SearXNG-backed provider."""

from __future__ import annotations

from typing import Dict, List, Optional

from ..settings import SearchSettings
from ..types import SearchResult
from .base import SearchProvider

try:
    from ...searxng_search import SearXNGSearcher
except ImportError:  # pragma: no cover - defensive fallback
    SearXNGSearcher = None  # type: ignore


class SearxngProvider(SearchProvider):
    name = "searxng"

    def __init__(self, config: SearchSettings):
        self._config = config
        self._searcher: Optional[SearXNGSearcher] = None

    def _ensure_searcher(self) -> Optional[SearXNGSearcher]:
        if SearXNGSearcher is None:
            return None
        if self._searcher is None:
            searcher_config: Dict = {
                "searxng_url": self._config.searxng.url,
                "timeout": self._config.request_timeout,
                "max_results": self._config.total_results,
                "auto_restart_searxng": True,
                "restart_on_search_failure": True,
            }
            self._searcher = SearXNGSearcher(searcher_config)
        return self._searcher

    def search(self, query: str, max_results: int) -> List[SearchResult]:
        searcher = self._ensure_searcher()
        if searcher is None:
            return []

        raw_results = searcher.search(query, max_results)
        results: List[SearchResult] = []
        for item in raw_results[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title") or item.get("snippet") or item.get("url", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("source") or "SearXNG",
                )
            )
        return results
