"""DuckDuckGo / HTML scraping provider."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..settings import SearchSettings
from ..types import SearchResult
from .base import SearchProvider

try:
    from ..html_search import HTMLSearcher
except ImportError:  # pragma: no cover - safety fallback
    HTMLSearcher = None  # type: ignore

try:
    from duckduckgo_search import DDGS  # type: ignore

    DDGS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    DDGS = None  # type: ignore
    DDGS_AVAILABLE = False


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def __init__(self, config: SearchSettings):
        self._config = config
        self._searcher: Optional[HTMLSearcher] = None
        self._logger = logging.getLogger(__name__)

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

    def _ddgs_search(self, query: str, max_results: int) -> List[SearchResult]:
        if not DDGS_AVAILABLE:
            self._logger.debug("duckduckgo_search package not available; skipping DDGS fallback.")
            return []

        try:
            with DDGS(timeout=self._config.request_timeout) as ddgs:  # type: ignore[attr-defined]
                api_results = ddgs.text(query, max_results=max_results)
        except Exception as exc:  # pragma: no cover - network fallback
            self._logger.warning("DDGS fallback failed: %s", exc)
            return []

        results: List[SearchResult] = []
        for item in api_results:
            url = item.get("href") or item.get("url") or ""
            if not url:
                continue
            title = item.get("title") or item.get("body") or url
            snippet = (item.get("body") or "")[:300]
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="DuckDuckGo (API)",
                )
            )
        return results

    def search(self, query: str, max_results: int) -> List[SearchResult]:
        searcher = self._ensure_searcher()
        if searcher is None:
            self._logger.warning(
                "HTML DuckDuckGo searcher unavailable; attempting DDGS fallback for query '%s'.",
                query,
            )
            return self._ddgs_search(query, max_results)

        raw_results = searcher.search(query, max_results)
        if not raw_results:
            self._logger.info(
                "DuckDuckGo HTML returned no results for '%s'; attempting DDGS fallback.", query
            )
            return self._ddgs_search(query, max_results)

        results: List[SearchResult] = []
        for item in raw_results[:max_results]:
            url = item.get("url", "")
            title = item.get("title") or item.get("snippet") or url
            if not url:
                continue
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=item.get("snippet", ""),
                    source=item.get("source") or "DuckDuckGo",
                )
            )

        if results:
            return results

        self._logger.info(
            "DuckDuckGo HTML produced non-convertible entries for '%s'; retrying with DDGS.", query
        )
        return self._ddgs_search(query, max_results)
