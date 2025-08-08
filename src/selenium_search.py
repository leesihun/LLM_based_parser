#!/usr/bin/env python3
"""
Selenium Browser-Based Search System
Uses actual Chrome/Firefox browser to perform searches, bypassing proxy HTTPS issues
"""

import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class SeleniumSearcher:
    """Web search using Selenium WebDriver with real browser"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Selenium searcher"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available. Install with: pip install selenium webdriver-manager")
        
        self.config = config or {}
        self.driver = None
        self.timeout = self.config.get('timeout', 15)
        self.max_results = self.config.get('max_results', 5)
        self.delay_between_requests = self.config.get('delay', 2)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize browser
        self._setup_browser()
    
    def _setup_browser(self):
        """Setup browser with appropriate options"""
        # Try Chrome first, then Firefox
        browsers = [self._setup_chrome, self._setup_firefox]
        
        for browser_setup in browsers:
            try:
                self.driver = browser_setup()
                if self.driver:
                    browser_name = "Chrome" if "chrome" in str(type(self.driver)).lower() else "Firefox"
                    self.logger.info(f"Successfully initialized {browser_name} WebDriver")
                    return
            except Exception as e:
                self.logger.warning(f"Failed to setup browser: {e}")
                continue
        
        raise Exception("Could not initialize any browser. Install Chrome or Firefox.")
    
    def _setup_chrome(self):
        """Setup Chrome WebDriver"""
        chrome_options = ChromeOptions()
        
        # Add options for corporate environment
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors-list')
        
        # User agent to avoid detection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Browser will use system proxy settings automatically
        # No need to configure proxy manually - it inherits from Windows
        
        try:
            # Use webdriver-manager to auto-download ChromeDriver
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            return webdriver.Chrome(executable_path=driver_path, options=chrome_options)
        except:
            # Fallback to system ChromeDriver
            return webdriver.Chrome(options=chrome_options)
    
    def _setup_firefox(self):
        """Setup Firefox WebDriver"""
        firefox_options = FirefoxOptions()
        firefox_options.add_argument('--headless')
        
        # Firefox profile for corporate environment
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 0)  # Use system proxy
        profile.set_preference("security.tls.insecure_fallback_hosts", "")
        profile.set_preference("security.tls.unrestricted_rc4_fallback", True)
        
        try:
            from webdriver_manager.firefox import GeckoDriverManager
            driver_path = GeckoDriverManager().install()
            return webdriver.Firefox(executable_path=driver_path, options=firefox_options, firefox_profile=profile)
        except:
            return webdriver.Firefox(options=firefox_options, firefox_profile=profile)
    
    def _search_google(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Google using Selenium"""
        results = []
        
        try:
            # Navigate to Google
            self.driver.get(f"https://www.google.com/search?q={query}")
            
            # Wait for results to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3"))
            )
            
            # Find result containers
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL
                    title_element = element.find_element(By.CSS_SELECTOR, "h3")
                    title = title_element.text.strip()
                    
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    url = link_element.get_attribute("href")
                    
                    # Extract snippet
                    snippet = ""
                    try:
                        snippet_elements = element.find_elements(By.CSS_SELECTOR, "span")
                        for span in snippet_elements:
                            span_text = span.text.strip()
                            if len(span_text) > 20:  # Likely a description
                                snippet = span_text[:200]
                                break
                    except:
                        pass
                    
                    if title and url and not url.startswith("javascript:"):
                        results.append({
                            'title': title,
                            'snippet': snippet + "..." if snippet else "Google search result",
                            'url': url,
                            'source': 'Google'
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing Google result: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Google search failed: {e}")
        
        return results
    
    def _search_bing(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Bing using Selenium"""
        results = []
        
        try:
            # Navigate to Bing
            self.driver.get(f"https://www.bing.com/search?q={query}")
            
            # Wait for results
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".b_algo"))
            )
            
            # Find result containers
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".b_algo")
            
            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL
                    title_element = element.find_element(By.CSS_SELECTOR, "h2 a")
                    title = title_element.text.strip()
                    url = title_element.get_attribute("href")
                    
                    # Extract snippet
                    snippet = ""
                    try:
                        snippet_element = element.find_element(By.CSS_SELECTOR, ".b_caption p")
                        snippet = snippet_element.text.strip()[:200]
                    except:
                        pass
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'snippet': snippet + "..." if snippet else "Bing search result",
                            'url': url,
                            'source': 'Bing'
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing Bing result: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Bing search failed: {e}")
        
        return results
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo using Selenium"""
        results = []
        
        try:
            # Navigate to DuckDuckGo
            self.driver.get(f"https://duckduckgo.com/?q={query}")
            
            # Wait for results
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-result]"))
            )
            
            # Find result containers
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-result]")
            
            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL
                    title_element = element.find_element(By.CSS_SELECTOR, "h2 a")
                    title = title_element.text.strip()
                    url = title_element.get_attribute("href")
                    
                    # Extract snippet
                    snippet = ""
                    try:
                        snippet_element = element.find_element(By.CSS_SELECTOR, "[data-result] > div > div")
                        snippet = snippet_element.text.strip()[:200]
                    except:
                        pass
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'snippet': snippet + "..." if snippet else "DuckDuckGo search result",
                            'url': url,
                            'source': 'DuckDuckGo'
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing DuckDuckGo result: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
        
        return results
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Perform web search using browser automation
        
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
            self._search_google,
            self._search_bing,
            self._search_duckduckgo
        ]
        
        for search_func in search_engines:
            try:
                results = search_func(query, max_results)
                if results:
                    self.logger.info(f"Found {len(results)} results using {search_func.__name__}")
                    time.sleep(self.delay_between_requests)  # Be respectful
                    return results
            except Exception as e:
                self.logger.warning(f"Search engine {search_func.__name__} failed: {str(e)}")
                continue
        
        # Return fallback if all engines fail
        return [{
            'title': 'Browser Search Unavailable',
            'snippet': f'Unable to search for "{query}" using browser automation. This may be due to network issues or browser configuration problems.',
            'url': f'https://www.google.com/search?q={query}',
            'source': 'Fallback'
        }]
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Search and format results for LLM context"""
        results = self.search(query, max_results)
        
        if not results:
            return f"No browser search results found for: {query}"
        
        context = f"Browser Search Results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            context += f"{i}. **{result['title']}**\n"
            if result['snippet']:
                context += f"   {result['snippet']}\n"
            if result['url']:
                context += f"   URL: {result['url']}\n"
            context += f"   Engine: {result['source']}\n"
            context += "\n"
        
        return context
    
    def test_search_capability(self) -> Dict:
        """Test search functionality and return status"""
        test_query = "python programming"
        
        try:
            results = self.search(test_query, max_results=3)
            
            return {
                'success': len(results) > 0 and not any('Fallback' in r.get('source', '') for r in results),
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
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


def test_selenium_search():
    """Test the selenium searcher"""
    print("Testing Selenium Browser Search")
    print("=" * 50)
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not available. Install with:")
        print("pip install selenium webdriver-manager")
        return False
    
    try:
        searcher = SeleniumSearcher()
        
        # Run capability test
        print("Running capability test...")
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
        print(f"❌ Selenium search test failed: {e}")
        return False


if __name__ == "__main__":
    test_selenium_search()