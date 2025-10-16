#!/usr/bin/env python3
"""
SearXNG Search Integration
Uses SearXNG instance for web searches with robust error handling and fallback
"""

import logging
import subprocess
import json
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from urllib import error, parse, request as urllib_request
import sys
import os

# Import restart manager
try:
    # Add scripts directory to path for restart manager import
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from restart_searxng import SearXNGManager
except ImportError:
    # Fallback if restart manager not available
    SearXNGManager = None


class SearXNGSearcher:
    """Web search using SearXNG instance with multiple connection methods"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize SearXNG searcher"""
        self.config = config or {}
        self.searxng_url = self.config.get('searxng_url', 'http://192.168.219.113:8080')
        self.timeout = self.config.get('timeout', 15)
        self.max_results = self.config.get('max_results', 5)

        # Auto-restart configuration
        self.auto_restart = self.config.get('auto_restart_searxng', True)
        self.restart_on_failure = self.config.get('restart_on_search_failure', True)

        # Connection method priority: wsl (for Windows), urllib (cross-platform), curl (fallback)
        self.connection_methods = ['wsl', 'urllib', 'curl']
        self.preferred_method = None  # Will be determined on first successful connection

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SearXNGSearcher initialized with URL: {self.searxng_url}")

        # Initialize restart manager if available
        self.manager = SearXNGManager() if SearXNGManager else None

        # Ensure SearXNG is ready on initialization if auto_restart enabled
        if self.auto_restart and self.manager:
            self.logger.info("Auto-restart enabled, ensuring SearXNG is ready...")
            ready_result = self.manager.ensure_searxng_ready(max_retries=1)
            if ready_result['success']:
                self.logger.info("SearXNG is ready")
            else:
                self.logger.warning(f"SearXNG may not be ready: {ready_result.get('error')}")

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

        # Try search, with auto-restart on failure if enabled
        max_attempts = 2 if (self.restart_on_failure and self.manager) else 1

        for attempt in range(max_attempts):
            try:
                results = self._perform_search(query, max_results)

                # If successful, return results
                if results:
                    return results

                # No results - try restart if enabled and this is first attempt
                if attempt == 0 and self.restart_on_failure and self.manager:
                    self.logger.warning("Search returned no results, attempting restart...")
                    restart_result = self.manager.restart_searxng(wait_seconds=5)
                    if restart_result['success']:
                        self.logger.info("Restart successful, retrying search...")
                        continue
                    else:
                        self.logger.warning(f"Restart failed: {restart_result.get('error')}")
                        return []
                else:
                    return []

            except Exception as e:
                self.logger.error(f"Search attempt {attempt + 1} failed: {e}")

                # Try restart on exception if enabled and this is first attempt
                if attempt == 0 and self.restart_on_failure and self.manager:
                    self.logger.warning("Search failed with exception, attempting restart...")
                    restart_result = self.manager.restart_searxng(wait_seconds=5)
                    if restart_result['success']:
                        self.logger.info("Restart successful, retrying search...")
                        continue
                    else:
                        self.logger.warning(f"Restart failed: {restart_result.get('error')}")
                        return []
                else:
                    return []

        return results

    def _perform_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """
        Internal method to perform the actual search with multiple connection methods

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        # If we have a preferred method, try it first
        if self.preferred_method:
            success, results = self._try_connection_method(self.preferred_method, query, max_results)
            if success:
                return results
            else:
                self.logger.warning(f"Preferred method '{self.preferred_method}' failed, trying alternatives...")
                self.preferred_method = None  # Reset preferred method

        # Try all connection methods until one succeeds
        for method in self.connection_methods:
            success, results = self._try_connection_method(method, query, max_results)
            if success:
                self.preferred_method = method  # Remember successful method
                self.logger.info(f"Connection method '{method}' succeeded, setting as preferred")
                return results

        self.logger.error("All connection methods failed")
        return []

    def _try_connection_method(self, method: str, query: str, max_results: int) -> Tuple[bool, List[Dict[str, str]]]:
        """
        Try a specific connection method to fetch search results

        Args:
            method: Connection method ('wsl', 'urllib', 'curl')
            query: Search query
            max_results: Maximum results

        Returns:
            Tuple of (success: bool, results: List)
        """
        try:
            self.logger.debug(f"Trying connection method: {method}")

            if method == 'wsl':
                return self._search_via_wsl(query, max_results)
            elif method == 'urllib':
                return self._search_via_urllib(query, max_results)
            elif method == 'curl':
                return self._search_via_curl(query, max_results)
            else:
                self.logger.warning(f"Unknown connection method: {method}")
                return False, []

        except Exception as e:
            self.logger.error(f"Connection method '{method}' failed: {e}")
            return False, []

    def _search_via_wsl(self, query: str, max_results: int) -> Tuple[bool, List[Dict[str, str]]]:
        """Search using WSL curl (best for Windows WSL2 environments)"""
        try:
            query_encoded = parse.quote_plus(query)
            curl_cmd_str = f"curl -s --max-time {int(self.timeout)} 'http://localhost:8080/search?q={query_encoded}&format=json&language=en&safesearch=0'"

            result = subprocess.run(
                ['wsl', 'bash', '-c', curl_cmd_str],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=self.timeout + 5
            )

            if result.returncode != 0:
                self.logger.debug(f"WSL curl failed: {result.stderr}")
                return False, []

            return True, self._parse_searxng_response(result.stdout, max_results)

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.debug(f"WSL method unavailable: {e}")
            return False, []

    def _search_via_urllib(self, query: str, max_results: int) -> Tuple[bool, List[Dict[str, str]]]:
        """Search using Python's urllib (cross-platform)"""
        try:
            query_encoded = parse.quote_plus(query)
            url = f"{self.searxng_url}/search?q={query_encoded}&format=json&language=en&safesearch=0"

            req = urllib_request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; SearXNG-Client/1.0)'}
            )

            with urllib_request.urlopen(req, timeout=self.timeout) as response:
                data = response.read().decode('utf-8')
                return True, self._parse_searxng_response(data, max_results)

        except (error.URLError, error.HTTPError, TimeoutError) as e:
            self.logger.debug(f"urllib method failed: {e}")
            return False, []

    def _search_via_curl(self, query: str, max_results: int) -> Tuple[bool, List[Dict[str, str]]]:
        """Search using system curl (fallback)"""
        try:
            query_encoded = parse.quote_plus(query)
            url = f"{self.searxng_url}/search?q={query_encoded}&format=json&language=en&safesearch=0"

            result = subprocess.run(
                ['curl', '-s', '--max-time', str(int(self.timeout)), url],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=self.timeout + 5
            )

            if result.returncode != 0:
                self.logger.debug(f"curl failed: {result.stderr}")
                return False, []

            return True, self._parse_searxng_response(result.stdout, max_results)

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.debug(f"curl method unavailable: {e}")
            return False, []

    def _parse_searxng_response(self, response_data: str, max_results: int) -> List[Dict[str, str]]:
        """
        Parse SearXNG JSON response into standardized result format

        Args:
            response_data: JSON response string from SearXNG
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        results = []

        try:
            if not response_data or not response_data.strip():
                self.logger.warning("Empty response from SearXNG")
                return []

            data = json.loads(response_data)

            # Extract results from SearXNG response
            if 'results' in data and isinstance(data['results'], list):
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
                self.logger.warning("No 'results' field in SearXNG response")

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response from SearXNG: {e}")
            self.logger.debug(f"Response data: {response_data[:500]}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing SearXNG response: {e}")

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
