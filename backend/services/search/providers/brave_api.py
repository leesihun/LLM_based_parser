"""Brave Search API provider - based on Page Assist implementation."""

from __future__ import annotations

import logging
from typing import List, Optional

import requests

from ..types import SearchResult
from .base import SearchProvider

logger = logging.getLogger(__name__)


class BraveAPIProvider(SearchProvider):
    """Search using Brave Search API (requires API key)."""

    name = "brave_api"

    def __init__(self, api_key: str, timeout: int = 20):
        """Initialize Brave API provider.
        
        Args:
            api_key: Brave Search API key
            timeout: Request timeout in seconds
        """
        if not api_key or not api_key.strip():
            raise ValueError("Brave API key is required")
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a Brave API search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            params = {
                "q": query,
                "count": max_results
            }
            
            headers = {
                "X-Subscription-Token": self.api_key,
                "Accept": "application/json"
            }
            
            logger.info(f"Performing Brave API search for: {query}")
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            if not response.ok:
                logger.error(f"Brave API error: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            # Extract web results
            web_results = data.get("web", {}).get("results", [])
            
            for item in web_results[:max_results]:
                try:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        source="brave_api"
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing Brave API result: {e}")
                    continue
            
            logger.info(f"Brave API returned {len(results)} results")
            return results
            
        except requests.Timeout:
            logger.error("Brave API request timed out")
            return []
        except requests.RequestException as e:
            logger.error(f"Brave API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Brave API search: {e}")
            return []

