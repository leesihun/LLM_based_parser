#!/usr/bin/env python3
"""
Selenium Browser-Based Search System
Uses actual Chrome/Firefox browser to perform searches, bypassing proxy HTTPS issues
"""

import time
import logging
import os
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
        self.browser_type = None  # Track which browser we're using
        self.setup_failed = False  # Track if setup has permanently failed
        self.last_setup_attempt = None  # Track last setup attempt time

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Initialize browser at startup to fail fast if there's a problem
        try:
            self._setup_browser()
            self.logger.info("SeleniumSearcher initialized successfully")
        except Exception as e:
            self.setup_failed = True
            self.logger.error(f"Failed to initialize browser: {e}")
            self.logger.error("Web search will not be available. Please install Chrome/ChromeDriver or Firefox/GeckoDriver.")
    
    def _is_session_alive(self) -> bool:
        """Check if the current browser session is still alive"""
        if self.driver is None:
            return False

        try:
            # Try to access the session - this will fail if session is dead
            _ = self.driver.title
            return True
        except Exception as e:
            self.logger.warning(f"Browser session is dead: {e}")
            return False

    def _ensure_browser_ready(self):
        """Ensure browser is ready, recreate if session is invalid"""
        # Check if setup has permanently failed
        if self.setup_failed:
            raise Exception("Browser setup failed previously. Web search is not available.")

        if self._is_session_alive():
            return  # Browser is ready

        # Check if we should throttle setup attempts (prevent rapid retry loops)
        import time as time_module
        current_time = time_module.time()
        if self.last_setup_attempt and (current_time - self.last_setup_attempt) < 10:
            raise Exception("Browser setup failed recently. Please wait before retrying.")

        # Session is dead or doesn't exist, need to create/recreate
        if self.driver is not None:
            self.logger.info("Cleaning up dead browser session...")
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

        self.logger.info("Recreating browser session...")
        self.last_setup_attempt = current_time
        try:
            self._setup_browser()
        except Exception as e:
            self.setup_failed = True
            self.logger.error(f"Browser recreation failed: {e}")
            raise

    def _setup_browser(self):
        """Setup browser with appropriate options"""
        # Try Chrome first, then Firefox
        browsers = [
            ('chrome', self._setup_chrome),
            ('firefox', self._setup_firefox)
        ]

        for browser_name, browser_setup in browsers:
            try:
                self.driver = browser_setup()
                if self.driver:
                    self.browser_type = browser_name
                    self.logger.info(f"Successfully initialized {browser_name.capitalize()} WebDriver")
                    return
            except Exception as e:
                self.logger.warning(f"Failed to setup {browser_name}: {e}")
                continue

        raise Exception("Could not initialize any browser. Install Chrome or Firefox.")
    
    def _get_chrome_version(self):
        """Detect installed Chrome version"""
        import subprocess
        import re

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]

        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    # Get Chrome version
                    result = subprocess.run(
                        [chrome_path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    version_output = result.stdout.strip()
                    # Extract version number (e.g., "Google Chrome 131.0.6778.86" -> "131.0.6778.86")
                    match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version_output)
                    if match:
                        version = match.group(0)
                        major_version = match.group(1)
                        self.logger.info(f"Detected Chrome version: {version} (major: {major_version})")
                        return version, major_version
                except Exception as e:
                    self.logger.debug(f"Failed to get Chrome version from {chrome_path}: {e}")
                    continue

        self.logger.warning("Could not detect Chrome version")
        return None, None

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

        # Try system ChromeDriver first to avoid quota issues with webdriver-manager
        try:
            self.logger.info("Attempting to use system ChromeDriver...")
            return webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.logger.warning(f"System ChromeDriver failed: {e}")

        # Detect Chrome version and download matching ChromeDriver
        try:
            chrome_version, major_version = self._get_chrome_version()

            if chrome_version and major_version:
                self.logger.info(f"Downloading ChromeDriver matching Chrome {chrome_version}...")
                from webdriver_manager.chrome import ChromeDriverManager

                # Download ChromeDriver matching the detected Chrome version
                driver_path = ChromeDriverManager(driver_version=chrome_version).install()
                self.logger.info(f"ChromeDriver installed at: {driver_path}")
                return webdriver.Chrome(executable_path=driver_path, options=chrome_options)
            else:
                # If version detection failed, try downloading latest
                self.logger.warning("Chrome version detection failed, attempting to download latest ChromeDriver...")
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                return webdriver.Chrome(executable_path=driver_path, options=chrome_options)

        except Exception as e:
            self.logger.error(f"ChromeDriver setup failed: {e}")
            raise
    
    def _setup_firefox(self):
        """Setup Firefox WebDriver"""
        firefox_options = FirefoxOptions()
        firefox_options.add_argument('--headless')

        # Firefox profile for corporate environment
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 0)  # Use system proxy
        profile.set_preference("security.tls.insecure_fallback_hosts", "")
        profile.set_preference("security.tls.unrestricted_rc4_fallback", True)

        # Try system GeckoDriver first to avoid quota issues
        try:
            self.logger.info("Attempting to use system GeckoDriver...")
            return webdriver.Firefox(options=firefox_options, firefox_profile=profile)
        except Exception as e:
            self.logger.warning(f"System GeckoDriver failed: {e}")

        # Fallback to webdriver-manager (may hit quota limits)
        try:
            self.logger.info("Attempting to download GeckoDriver via webdriver-manager...")
            from webdriver_manager.firefox import GeckoDriverManager
            driver_path = GeckoDriverManager().install()
            return webdriver.Firefox(executable_path=driver_path, options=firefox_options, firefox_profile=profile)
        except Exception as e:
            self.logger.error(f"GeckoDriver download failed (possibly quota exceeded): {e}")
            raise
    
    
    def _search_google(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Bing using Selenium"""
        results = []

        try:
            # Ensure browser session is alive before searching
            self._ensure_browser_ready()

            # Navigate to Bing
            search_url = f"https://www.bing.com/search?q={query}"
            self.logger.info(f"Navigating to: {search_url}")
            self.driver.get(search_url)

            # Wait for results - Bing uses #b_results container
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#b_results"))
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
    
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Perform Bing search using browser automation
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []
        
        max_results = max_results or self.max_results
        
        # Use Bing search only
        results = self._search_google(query, max_results)
        if results:
            self.logger.info(f"Found {len(results)} results from Bing")
            time.sleep(self.delay_between_requests)
        else:
            self.logger.warning("Bing search returned no results")
            
        return results
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Search and format results for LLM context"""
        results = self.search(query, max_results)
        
        if not results:
            return f"No browser search results found for: {query}"
        
        context = f"Bing Search Results for '{query}':\n\n"
        
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
            # Ensure browser is ready before testing
            self._ensure_browser_ready()

            results = self.search(test_query, max_results=3)
            
            return {
                'success': len(results) > 0,
                'result_count': len(results),
                'test_query': test_query,
                'engines_working': ['Bing'],
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
            print("Using Bing search engine")
            
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