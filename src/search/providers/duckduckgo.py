"""DuckDuckGo / HTML scraping provider."""

from __future__ import annotations

from typing import Dict, List, Optional

from ..settings import SearchSettings
from ..types import SearchResult
from .base import SearchProvider

try:
    from ...html_search import HTMLSearcher
except ImportError:  # pragma: no cover - safety fallback
    HTMLSearcher = None  # type: ignore


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def __init__(self, config: SearchSettings):
        self._config = config
        self._searcher: Optional[HTMLSearcher] = None

    def _ensure_searcher(self) -> Optional[HTMLSearcher]:
        if HTMLSearcher is None:
            return None
        if self._searcher is None:
            searcher_config: Dict = {
                "timeout": self._config.request_timeout,
                "max_results": self._config.total_results,
                "delay": 2,
            }
            self._searcher = HTMLSearcher(searcher_config)
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
                    source=item.get("source") or "DuckDuckGo",
                )
            )
        return results
