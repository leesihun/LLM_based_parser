#!/usr/bin/env python3
"""
HTML-Based Search (No Selenium)
Uses simple HTTP requests to avoid CAPTCHA entirely
"""

import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from duckduckgo_search import DDGS  # type: ignore

    DDGS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    DDGS = None  # type: ignore
    DDGS_AVAILABLE = False


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
        self.verify_ssl = self.config.get('verify_ssl', False)  # Disable SSL verification by default for corporate networks

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Disable SSL warnings if verification is disabled
        if not self.verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.logger.info("🔓 SSL verification disabled for corporate network compatibility")

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

        # Configure retries with backoff
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

        self.logger.info("✅ HTMLSearcher initialized successfully")

    def _human_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to avoid rate limiting"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _search_duckduckgo_html(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo using HTML (no JavaScript, no CAPTCHA)."""

        def _normalise_url(raw_url: str) -> str:
            """Unwrap DuckDuckGo redirect URLs and ensure they are absolute."""
            if not raw_url:
                return ""
            url = raw_url.strip()
            if url.startswith("//"):
                url = f"https:{url}"
            parsed = urlparse(url)
            if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
                uddg = parse_qs(parsed.query).get("uddg")
                if uddg:
                    return unquote(uddg[0])
            return url

        def _parse_results(soup: BeautifulSoup) -> List[Dict[str, str]]:
            containers = soup.find_all("div", class_="result")
            if not containers:
                containers = soup.select("article[data-testid='result']")

            parsed_results: List[Dict[str, str]] = []
            for element in containers[:max_results]:
                title_elem = (
                    element.find("a", class_="result__a")
                    or element.select_one("h2 a")
                    or element.select_one("a[data-testid='result-title-a']")
                )
                if not title_elem:
                    continue

                title = title_elem.get_text(" ", strip=True)
                url = _normalise_url(title_elem.get("href", ""))

                snippet_elem = (
                    element.find("a", class_="result__snippet")
                    or element.find("div", class_="result__snippet")
                    or element.find("p", class_="result__snippet")
                    or element.select_one("[data-testid='result-snippet']")
                )
                snippet = ""
                if snippet_elem:
                    snippet = snippet_elem.get_text(" ", strip=True)[:300]

                if not title or not url:
                    continue

                parsed_results.append(
                    {
                        "title": title,
                        "snippet": (snippet + "...") if snippet else "DuckDuckGo search result",
                        "url": url,
                        "source": "DuckDuckGo (HTML)",
                    }
                )

            return parsed_results

        results: List[Dict[str, str]] = []
        endpoint = "https://html.duckduckgo.com/html/"
        params = {"q": query}

        for method in ("get", "post"):
            try:
                self.logger.info(f"??? [DUCKDUCKGO] Searching DuckDuckGo HTML via {method.upper()}: {query}")
                if method == "get":
                    response = self.session.get(
                        endpoint, params=params, timeout=self.timeout, verify=self.verify_ssl
                    )
                else:
                    response = self.session.post(
                        endpoint, data=params, timeout=self.timeout, verify=self.verify_ssl
                    )
                response.raise_for_status()
            except Exception as exc:
                self.logger.warning(f"??[DUCKDUCKGO] {method.upper()} request failed: {exc}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            results = _parse_results(soup)
            if results:
                self.logger.info(
                    f"??[DUCKDUCKGO] Found {len(results)} results from DuckDuckGo HTML ({method.upper()})"
                )
                break

        if not results and DDGS_AVAILABLE:
            try:
                self.logger.info("DuckDuckGo HTML returned no results, trying duckduckgo_search fallback")
                with DDGS(timeout=self.timeout) as ddgs:  # type: ignore[attr-defined]
                    api_results = ddgs.text(query, max_results=max_results)
                for item in api_results:
                    url = _normalise_url(item.get("href") or item.get("url") or "")
                    if not url:
                        continue
                    title = item.get("title") or item.get("body") or url
                    snippet = (item.get("body") or "")[:300]
                    results.append(
                        {
                            "title": title,
                            "snippet": snippet + "..." if snippet else "DuckDuckGo search result",
                            "url": url,
                            "source": "DuckDuckGo (API)",
                        }
                    )
                if results:
                    self.logger.info(
                        f"??[DUCKDUCKGO] duckduckgo_search fallback returned {len(results)} results"
                    )
            except Exception as exc:  # pragma: no cover - network fallback
                self.logger.error(f"??[DUCKDUCKGO] duckduckgo_search fallback failed: {exc}")

        return results

    def _search_brave(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Brave using simple HTTP (no CAPTCHA)"""
        results = []

        try:
            # Brave search URL
            url = f"https://search.brave.com/search?q={quote_plus(query)}"

            self.logger.info(f"🔍 [BRAVE] Searching Brave: {query}")
            response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            self.logger.info(f"✅ [BRAVE] Received response: {response.status_code}")

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
            self.logger.error(f"❌ [BRAVE] Brave search failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

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
