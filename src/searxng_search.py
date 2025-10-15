#!/usr/bin/env python3
"""
SearXNG Search Integration
Uses SearXNG instance at http://192.168.219.113:8080 for web searches
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime


class SearXNGSearcher:
    """Web search using SearXNG instance"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize SearXNG searcher"""
        self.config = config or {}
        self.searxng_url = self.config.get('searxng_url', 'http://192.168.219.113:8080')
        self.timeout = self.config.get('timeout', 15)
        self.max_results = self.config.get('max_results', 5)

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SearXNGSearcher initialized with URL: {self.searxng_url}")

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Perform web search using SearXNG

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []

        max_results = max_results or self.max_results
        results = []

        try:
            # SearXNG search endpoint
            search_url = f"{self.searxng_url}/search"

            # Parameters for SearXNG API
            params = {
                'q': query,
                'format': 'json',
                'language': 'en',
                'safesearch': 0,
                'categories': 'general'
            }

            self.logger.info(f"Searching SearXNG for: {query}")

            # Make request to SearXNG
            response = requests.get(
                search_url,
                params=params,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract results from SearXNG response
            if 'results' in data:
                for result in data['results'][:max_results]:
                    # Extract relevant fields
                    title = result.get('title', '').strip()
                    url = result.get('url', '').strip()
                    content = result.get('content', '').strip()

                    # Skip if no title or URL
                    if not title or not url:
                        continue

                    results.append({
                        'title': title,
                        'snippet': content[:200] + "..." if len(content) > 200 else content,
                        'url': url,
                        'source': 'SearXNG'
                    })

                self.logger.info(f"SearXNG returned {len(results)} results")
            else:
                self.logger.warning("No results found in SearXNG response")

        except requests.exceptions.Timeout:
            self.logger.error(f"SearXNG request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Could not connect to SearXNG at {self.searxng_url}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"SearXNG request failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during SearXNG search: {e}")

        return results

    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Search and format results for LLM context"""
        results = self.search(query, max_results)

        if not results:
            return f"No SearXNG search results found for: {query}"

        context = f"SearXNG Search Results for '{query}':\n\n"

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

            return {
                'success': len(results) > 0,
                'result_count': len(results),
                'test_query': test_query,
                'searxng_url': self.searxng_url,
                'sample_result': results[0] if results else None,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_query': test_query,
                'searxng_url': self.searxng_url,
                'timestamp': datetime.now().isoformat()
            }

    def close(self):
        """Clean up resources (no-op for HTTP-based searcher)"""
        pass


def test_searxng_search():
    """Test the SearXNG searcher"""
    print("Testing SearXNG Search")
    print("=" * 50)

    try:
        searcher = SearXNGSearcher()

        # Run capability test
        print("Running capability test...")
        test_result = searcher.test_search_capability()
        print(f"Test Status: {'SUCCESS' if test_result['success'] else 'FAILED'}")

        if test_result['success']:
            print(f"Found {test_result['result_count']} results")
            print(f"SearXNG URL: {test_result['searxng_url']}")

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
        print(f"❌ SearXNG search test failed: {e}")
        return False


if __name__ == "__main__":
    test_searxng_search()
