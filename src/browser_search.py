#!/usr/bin/env python3
"""
Browser-style Web Search System
Uses HTTP requests to mimic browser behavior and extract search results
Works when traditional search APIs are blocked by corporate proxies
"""

import requests
import re
import time
import json
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime


class BrowserSearcher:
    """Web search using browser-like HTTP requests"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize browser searcher with configuration"""
        self.config = config or {}
        self.timeout = self.config.get('timeout', 10)
        self.max_results = self.config.get('max_results', 5)
        self.delay_between_requests = self.config.get('delay', 1)
        
        # Browser headers to mimic real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Create session for cookie persistence
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Perform web search using multiple search engines
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []
            
        max_results = max_results or self.max_results
        
        # Try search engines in order of preference
        search_engines = [
            self._search_duckduckgo,
            self._search_bing,
            self._search_startpage,
        ]
        
        for search_func in search_engines:
            try:
                results = search_func(query, max_results)
                if results:
                    self.logger.info(f"Found {len(results)} results using {search_func.__name__}")
                    return results
                    
            except Exception as e:
                self.logger.warning(f"Search engine {search_func.__name__} failed: {str(e)}")
                continue
        
        # Return fallback message if all engines fail
        return [{
            'title': 'Search Temporarily Unavailable',
            'snippet': f'Unable to search for "{query}" at this time. This may be due to network restrictions or temporary service issues.',
            'url': f'https://www.google.com/search?q={quote_plus(query)}',
            'source': 'Fallback'
        }]
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo using HTTP requests"""
        try:
            # DuckDuckGo search URL
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en',
                's': '0',
                'dc': max_results
            }
            
            # Make search request
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse results
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Find result containers
            result_containers = soup.find_all('div', class_='result')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_link = container.find('a', class_='result__a')
                    if not title_link:
                        continue
                        
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = container.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    if title and url:
                        results.append({
                            'title': self._clean_text(title),
                            'snippet': self._clean_text(snippet),
                            'url': url,
                            'source': 'DuckDuckGo'
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing DuckDuckGo result: {e}")
                    continue
            
            time.sleep(self.delay_between_requests)
            return results
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _search_bing(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Bing using HTTP requests"""
        try:
            search_url = "https://www.bing.com/search"
            params = {
                'q': query,
                'count': max_results,
                'first': 0,
                'FORM': 'PERE',
                'pc': 'MOZO'
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Find Bing result containers
            result_containers = soup.find_all('li', class_='b_algo')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = container.find('h2')
                    if not title_elem:
                        continue
                        
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                        
                    title = link_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = container.find('div', class_='b_caption')
                    snippet = ''
                    if snippet_elem:
                        snippet_text = snippet_elem.find('p')
                        if snippet_text:
                            snippet = snippet_text.get_text(strip=True)
                    
                    if title and url and not url.startswith('javascript:'):
                        results.append({
                            'title': self._clean_text(title),
                            'snippet': self._clean_text(snippet),
                            'url': url,
                            'source': 'Bing'
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing Bing result: {e}")
                    continue
            
            time.sleep(self.delay_between_requests)
            return results
            
        except Exception as e:
            self.logger.error(f"Bing search failed: {e}")
            return []
    
    def _search_startpage(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Startpage using HTTP requests"""
        try:
            search_url = "https://www.startpage.com/sp/search"
            params = {
                'query': query,
                'cat': 'web',
                'pl': 'opensearch',
                'language': 'english'
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Find Startpage result containers
            result_containers = soup.find_all('div', class_='w-gl__result')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = container.find('a', class_='w-gl__result-title')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = container.find('p', class_='w-gl__description')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    if title and url:
                        results.append({
                            'title': self._clean_text(title),
                            'snippet': self._clean_text(snippet),
                            'url': url,
                            'source': 'Startpage'
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing Startpage result: {e}")
                    continue
            
            time.sleep(self.delay_between_requests)
            return results
            
        except Exception as e:
            self.logger.error(f"Startpage search failed: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ''
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove common HTML artifacts
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text.strip()
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Search and format results for LLM context
        
        Args:
            query: Search query
            max_results: Maximum results to include
            
        Returns:
            Formatted search results as context string
        """
        results = self.search(query, max_results)
        
        if not results:
            return f"No search results found for: {query}"
        
        context = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            context += f"{i}. **{result['title']}**\n"
            if result['snippet']:
                context += f"   {result['snippet']}\n"
            if result['url']:
                context += f"   Source: {result['url']}\n"
            context += f"   Engine: {result['source']}\n"
            context += "\n"
        
        return context
    
    def test_search_capability(self) -> Dict[str, any]:
        """Test search functionality and return status"""
        test_query = "python programming"
        
        try:
            results = self.search(test_query, max_results=3)
            
            return {
                'success': len(results) > 0,
                'result_count': len(results),
                'test_query': test_query,
                'engines_working': list(set([r.get('source', 'Unknown') for r in results])),
                'sample_result': results[0] if results else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_query': test_query,
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()


# Test function
def main():
    """Test the browser searcher"""
    print("Testing Browser Search System")
    print("=" * 50)
    
    searcher = BrowserSearcher()
    
    # Run capability test
    test_result = searcher.test_search_capability()
    print(f"Test Status: {'SUCCESS' if test_result['success'] else 'FAILED'}")
    
    if test_result['success']:
        print(f"Found {test_result['result_count']} results")
        print(f"Working engines: {', '.join(test_result['engines_working'])}")
        
        if test_result['sample_result']:
            sample = test_result['sample_result']
            print(f"\nSample result:")
            print(f"Title: {sample['title']}")
            print(f"Source: {sample['source']}")
            print(f"URL: {sample['url']}")
    else:
        print(f"Error: {test_result.get('error', 'Unknown error')}")
    
    # Manual test
    print("\n" + "=" * 50)
    print("Manual Search Test")
    print("=" * 50)
    
    query = input("Enter search query (or press Enter for default): ").strip()
    if not query:
        query = "artificial intelligence machine learning"
    
    print(f"\nSearching for: {query}")
    results = searcher.search(query, max_results=5)
    
    print(f"\nFound {len(results)} results:")
    print("-" * 40)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        if result['snippet']:
            snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
            print(f"   {snippet}")
        print(f"   URL: {result['url']}")
        print(f"   Source: {result['source']}")
        print()
    
    searcher.close()


if __name__ == "__main__":
    main()