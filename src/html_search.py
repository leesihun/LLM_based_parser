#!/usr/bin/env python3
"""
HTML-Based Search (No Selenium)
Uses simple HTTP requests to avoid CAPTCHA entirely
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote_plus
import time
import random

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class HTMLSearcher:
    """Web search using simple HTTP requests (no Selenium, no CAPTCHA)"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize HTML searcher"""
        if not BS4_AVAILABLE:
            raise ImportError("BeautifulSoup4 not available. Install with: pip install beautifulsoup4")

        self.config = config or {}
        self.timeout = self.config.get('timeout', 15)
        self.max_results = self.config.get('max_results', 5)
        self.delay_between_requests = self.config.get('delay', 2)

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        self.logger.info("HTMLSearcher initialized successfully")

    def _human_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to avoid rate limiting"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _search_duckduckgo_html(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo using HTML (no JavaScript, no CAPTCHA)"""
        results = []

        try:
            # DuckDuckGo HTML endpoint
            url = "https://html.duckduckgo.com/html/"
            params = {'q': query}

            self.logger.info(f"Searching DuckDuckGo HTML: {query}")
            response = self.session.post(url, data=params, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find result containers
            result_elements = soup.find_all('div', class_='result')

            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = element.find('a', class_='result__a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    # Extract snippet
                    snippet = ""
                    snippet_elem = element.find('a', class_='result__snippet')
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)[:200]

                    # Skip if no title or URL
                    if not title or not url:
                        continue

                    results.append({
                        'title': title,
                        'snippet': snippet + "..." if snippet else "DuckDuckGo search result",
                        'url': url,
                        'source': 'DuckDuckGo (HTML)'
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing result: {e}")
                    continue

            self.logger.info(f"Found {len(results)} results from DuckDuckGo HTML")

        except Exception as e:
            self.logger.error(f"DuckDuckGo HTML search failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        return results

    def _search_brave(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Brave using simple HTTP (no CAPTCHA)"""
        results = []

        try:
            # Brave search URL
            url = f"https://search.brave.com/search?q={quote_plus(query)}"

            self.logger.info(f"Searching Brave: {query}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find result containers (Brave uses different structure)
            result_elements = soup.find_all('div', class_='snippet')

            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = element.find('a', class_='result-header')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    # Extract snippet
                    snippet = ""
                    snippet_elem = element.find('p', class_='snippet-description')
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)[:200]

                    # Skip if no title or URL
                    if not title or not url or not url.startswith('http'):
                        continue

                    results.append({
                        'title': title,
                        'snippet': snippet + "..." if snippet else "Brave search result",
                        'url': url,
                        'source': 'Brave'
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing Brave result: {e}")
                    continue

            self.logger.info(f"Found {len(results)} results from Brave")

        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")

        return results

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Perform web search using HTTP requests (no Selenium, no CAPTCHA)

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []

        max_results = max_results or self.max_results

        # Try DuckDuckGo HTML first
        results = self._search_duckduckgo_html(query, max_results)
        if results:
            time.sleep(self.delay_between_requests)
            return results

        # Fallback to Brave if DuckDuckGo fails
        self.logger.warning("DuckDuckGo HTML failed, trying Brave...")
        results = self._search_brave(query, max_results)
        if results:
            time.sleep(self.delay_between_requests)
        else:
            self.logger.warning("All HTML search engines failed")

        return results

    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Search and format results for LLM context"""
        results = self.search(query, max_results)

        if not results:
            return f"No search results found for: {query}"

        # Determine which search engine was used
        search_engine = results[0].get('source', 'Web') if results else 'Web'
        context = f"{search_engine} Search Results for '{query}':\n\n"

        for i, result in enumerate(results, 1):
            context += f"{i}. **{result['title']}**\n"
            if result['snippet']:
                context += f"   {result['snippet']}\n"
            if result['url']:
                context += f"   URL: {result['url']}\n"
            context += "\n"

        return context

    def test_search_capability(self) -> Dict:
        """Test search functionality and return status"""
        test_query = "python programming"

        try:
            results = self.search(test_query, max_results=3)

            # Determine which engines worked
            engines_working = []
            if results:
                engine = results[0].get('source', 'Unknown')
                engines_working = [engine]

            return {
                'success': len(results) > 0,
                'result_count': len(results),
                'test_query': test_query,
                'engines_working': engines_working,
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
        if self.session:
            self.session.close()


def test_html_search():
    """Test the HTML searcher"""
    print("Testing HTML-Based Search (No Selenium)")
    print("=" * 50)

    if not BS4_AVAILABLE:
        print("❌ BeautifulSoup4 not available. Install with:")
        print("pip install beautifulsoup4")
        return False

    try:
        searcher = HTMLSearcher()

        # Run capability test
        print("Running capability test...")
        test_result = searcher.test_search_capability()
        print(f"Test Status: {'SUCCESS' if test_result['success'] else 'FAILED'}")

        if test_result['success']:
            print(f"Found {test_result['result_count']} results")
            print(f"Using: {test_result['engines_working']}")

            if test_result['sample_result']:
                sample = test_result['sample_result']
                print(f"\nSample result:")
                print(f"Title: {sample['title']}")
                print(f"Source: {sample['source']}")
                print(f"URL: {sample['url'][:60]}...")
        else:
            print(f"Error: {test_result.get('error', 'Unknown error')}")

        # Manual test
        print("\n" + "=" * 50)
        print("Manual Search Test")

        query = "artificial intelligence tutorial"
        print(f"\nSearching for: {query}")
        results = searcher.search(query, max_results=3)

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
        return test_result['success']

    except Exception as e:
        print(f"❌ HTML search test failed: {e}")
        return False


if __name__ == "__main__":
    test_html_search()
