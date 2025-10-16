"""Tavily Search API provider - based on Page Assist implementation."""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

import requests

from ..types import SearchResult
from .base import SearchProvider

logger = logging.getLogger(__name__)


class TavilyAPIProvider(SearchProvider):
    """Search using Tavily Search API (requires API key)."""

    name = "tavily_api"

    def __init__(self, api_key: str, timeout: int = 20, include_answer: bool = True):
        """Initialize Tavily API provider.
        
        Args:
            api_key: Tavily Search API key
            timeout: Request timeout in seconds
            include_answer: Whether to include AI-generated answer
        """
        if not api_key or not api_key.strip():
            raise ValueError("Tavily API key is required")
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.include_answer = include_answer
        self.base_url = "https://api.tavily.com/search"
        self.last_answer: Optional[str] = None

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a Tavily API search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": self.include_answer
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info(f"Performing Tavily API search for: {query}")
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if not response.ok:
                error_body = response.text
                logger.error(f"Tavily API error: {response.status_code} - {error_body}")
                return []
            
            data = response.json()
            
            # Store the AI-generated answer if available
            self.last_answer = data.get("answer", "")
            
            # Validate response
            if not data.get("results") or not isinstance(data["results"], list):
                logger.error("Invalid response from Tavily API")
                return []
            
            results = []
            
            for item in data["results"][:max_results]:
                try:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        source="tavily_api"
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing Tavily API result: {e}")
                    continue
            
            logger.info(f"Tavily API returned {len(results)} results")
            if self.last_answer:
                logger.info(f"Tavily API provided an answer summary")
            
            return results
            
        except requests.Timeout:
            logger.error("Tavily API request timed out")
            return []
        except requests.RequestException as e:
            logger.error(f"Tavily API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Tavily API search: {e}")
            return []

    def get_last_answer(self) -> Optional[str]:
        """Get the AI-generated answer from the last search.
        
        Returns:
            The answer string or None if not available
        """
        return self.last_answer

