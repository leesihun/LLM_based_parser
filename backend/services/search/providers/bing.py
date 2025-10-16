"""Bing Search Provider with API integration and web scraping fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlencode

import requests

from ..settings import SearchSettings
from ..types import SearchResult
from .base import SearchProvider

try:
    # Optional dependency for Bing API
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class BingProvider(SearchProvider):
    name = "bing"

    def __init__(self, config: SearchSettings):
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._api_key = config.bing_api_key if hasattr(config, 'bing_api_key') else None
        self._use_api = bool(self._api_key and self._api_key.strip())

        # Web scraping configuration
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        # Configure retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _bing_api_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing Search API v7."""
        if not self._api_key:
            self._logger.warning("Bing API key not configured")
            return []

        try:
            # Bing Search API v7 endpoint
            endpoint = "https://api.bing.microsoft.com/v7.0/search"

            headers = {
                "Ocp-Apim-Subscription-Key": self._api_key,
                "User-Agent": self._config.user_agent,
            }

            params = {
                "q": query,
                "count": max_results,
                "offset": 0,
                "mkt": "en-US",
                "safeSearch": "Moderate",
                "textFormat": "Raw",
                "responseFilter": "Webpages",
            }

            self._logger.info(f"🔍 [BING API] Searching Bing API: {query}")
            response = self.session.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=self._config.request_timeout,
                verify=False  # Match existing behavior
            )
            response.raise_for_status()

            data = response.json()
            web_pages = data.get("webPages", {})
            results = web_pages.get("value", [])

            search_results = []
            for item in results:
                url = item.get("url", "")
                if not url:
                    continue

                title = item.get("name", "")
                snippet = item.get("snippet", "")

                search_results.append(SearchResult(
                    title=title or snippet or url,
                    url=url,
                    snippet=snippet[:300],
                    source="Bing API",
                ))

            self._logger.info(f"✅ [BING API] Found {len(search_results)} results")
            return search_results

        except Exception as e:
            self._logger.error(f"❌ [BING API] Bing API search failed: {e}")
            return []

    def _bing_web_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Search Bing using web scraping (fallback method)."""
        try:
            # Bing search URL
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}"

            self._logger.info(f"🔍 [BING WEB] Searching Bing Web: {query}")
            response = self.session.get(
                search_url,
                timeout=self._config.request_timeout,
                verify=False
            )
            response.raise_for_status()

            # Parse HTML results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            results = []
            # Find result containers - Bing uses different classes
            result_elements = soup.find_all('li', class_='b_algo')

            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = element.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    # Skip if not a valid URL
                    if not url or not url.startswith('http'):
                        continue

                    # Extract snippet
                    snippet = ""
                    snippet_elem = element.find('p')
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)[:300]

                    if not title:
                        title = snippet or url

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet + "..." if snippet else "Bing search result",
                        source="Bing (Web)",
                    ))

                except Exception as e:
                    self._logger.debug(f"Error parsing Bing result: {e}")
                    continue

            self._logger.info(f"✅ [BING WEB] Found {len(results)} results")
            return results

        except Exception as e:
            self._logger.error(f"❌ [BING WEB] Bing web search failed: {e}")
            return []

    def search(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing API first, then fallback to web scraping."""
        if not query or not query.strip():
            return []

        # Try API first if available
        if self._use_api:
            results = self._bing_api_search(query, max_results)
            if results:
                return results

        # Fallback to web scraping
        self._logger.info("Bing API not available or failed, using web scraping fallback")
        return self._bing_web_search(query, max_results)
