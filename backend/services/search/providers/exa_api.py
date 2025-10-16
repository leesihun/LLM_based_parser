"""Exa Search API provider - based on Page Assist implementation."""

from __future__ import annotations

import logging
from typing import List, Optional

import requests

from ..types import SearchResult
from .base import SearchProvider

logger = logging.getLogger(__name__)


class ExaAPIProvider(SearchProvider):
    """Search using Exa Search API (requires API key)."""

    name = "exa_api"

    def __init__(self, api_key: str, timeout: int = 20):
        """Initialize Exa API provider.
        
        Args:
            api_key: Exa Search API key
            timeout: Request timeout in seconds
        """
        if not api_key or not api_key.strip():
            raise ValueError("Exa API key is required")
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.base_url = "https://api.exa.ai/search"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform an Exa API search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            payload = {
                "query": query,
                "numResults": max_results,
                "text": True  # Include text content
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Performing Exa API search for: {query}")
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if not response.ok:
                logger.error(f"Exa API error: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            # Extract search results
            search_results = data.get("results", [])
            
            for item in search_results[:max_results]:
                try:
                    # Use text content if available, otherwise use title
                    content = item.get("text", "") or item.get("title", "")
                    
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=content,
                        source="exa_api"
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing Exa API result: {e}")
                    continue
            
            logger.info(f"Exa API returned {len(results)} results")
            return results
            
        except requests.Timeout:
            logger.error("Exa API request timed out")
            return []
        except requests.RequestException as e:
            logger.error(f"Exa API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Exa API search: {e}")
            return []

