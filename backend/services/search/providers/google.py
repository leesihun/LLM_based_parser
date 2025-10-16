"""Google Search Provider - improved based on Page Assist implementation."""

from __future__ import annotations

import logging
import time
from typing import List, Set
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from ..types import SearchResult
from .base import SearchProvider

logger = logging.getLogger(__name__)


class GoogleProvider(SearchProvider):
    """Search using Google (web scraping with pagination and deduplication)."""

    name = "google"

    def __init__(self, domain: str = "google.com", timeout: int = 10):
        """Initialize Google provider.
        
        Args:
            domain: Google domain to use (e.g., google.com, google.co.kr)
            timeout: Request timeout in seconds
        """
        self.domain = domain
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        })

    def _search_page(self, query: str, start: int = 0) -> List[dict]:
        """Search a single Google results page.
        
        Args:
            query: Search query
            start: Starting index for pagination
            
        Returns:
            List of result dictionaries
        """
        try:
            url = f"https://www.{self.domain}/search"
            params = {
                "hl": "en",
                "q": query,
                "start": start
            }
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            # Find all search result divs
            for result_div in soup.find_all("div", class_="g"):
                try:
                    # Extract title
                    title_elem = result_div.find("h3")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Extract link
                    link_elem = result_div.find("a")
                    link = link_elem.get("href") if link_elem else ""
                    
                    # Extract snippet from all spans
                    content_parts = []
                    for span in result_div.find_all("span"):
                        text = span.get_text(strip=True)
                        if text:
                            content_parts.append(text)
                    content = " ".join(content_parts)
                    
                    if title and link:
                        results.append({
                            "title": title,
                            "link": link,
                            "content": content
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing Google result: {e}")
                    continue
            
            return results
            
        except requests.Timeout:
            logger.error("Google search request timed out")
            return []
        except requests.RequestException as e:
            logger.error(f"Google search request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Google search: {e}")
            return []

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a Google search with pagination and deduplication.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            logger.info(f"Performing Google search for: {query}")
            
            all_results = []
            seen_links: Set[str] = set()
            current_page = 0
            
            # Paginate until we have enough results
            while len(all_results) < max_results:
                start = current_page * 10
                page_results = self._search_page(query, start)
                
                # Filter duplicates within current page
                for result in page_results:
                    link = result.get("link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        all_results.append(result)
                
                # Stop if no more results
                if not page_results:
                    break
                
                # Add delay between requests (1-3 seconds)
                if len(all_results) < max_results:
                    time.sleep(1.0 + (time.time() % 2.0))
                
                current_page += 1
                
                # Safety limit to prevent infinite loops
                if current_page > 10:
                    break
            
            # Convert to SearchResult objects
            search_results = []
            for item in all_results[:max_results]:
                try:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("content", ""),
                        source="google"
                    )
                    search_results.append(result)
                except Exception as e:
                    logger.warning(f"Error creating SearchResult: {e}")
                    continue
            
            logger.info(f"Google search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Unexpected error in Google search: {e}")
            return []

