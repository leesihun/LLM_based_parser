#!/usr/bin/env python3
"""
Selenium Browser-Based Search System
Uses actual Chrome/Firefox browser to perform searches, bypassing proxy HTTPS issues
"""

import time
import logging
import os
import random
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

        # Search engine preferences
        self.preferred_engine = self.config.get('search_engine', 'google').lower()
        self.fallback_to_google = self.config.get('fallback_to_google', True)

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Initialize browser at startup to fail fast if there's a problem
        try:
            self._setup_browser()
            # Hide webdriver property to avoid CAPTCHA detection
            self._hide_webdriver()
            self.logger.info("SeleniumSearcher initialized successfully with anti-detection measures")
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

    def _human_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _hide_webdriver(self):
        """Hide webdriver property to avoid CAPTCHA detection"""
        try:
            # Execute JavaScript to remove webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Override permissions API
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: () => Promise.resolve({ state: 'granted' })
                        })
                    });

                    // Override plugins to appear more real
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });

                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                '''
            })
            self.logger.debug("Webdriver property hidden successfully")
        except Exception as e:
            self.logger.warning(f"Could not hide webdriver property: {e}")

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

        # Get headless setting from config (default: true)
        selenium_config = self.config.get('selenium', {})
        headless = selenium_config.get('headless', True)

        # Add options for corporate environment
        if headless:
            chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors-list')

        # Disable Google services and background network requests
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-sync')  # Disable Chrome sync
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--mute-audio')

        # CRITICAL: Disable Google Cloud Messaging (GCM) and related services
        # This prevents the "google_apis/gcm/engine" error you're experiencing
        chrome_options.add_argument('--disable-features=GCMChannelStatusRequest')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-domain-reliability')

        # Disable logging to prevent stderr noise
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,  # Block notifications
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_settings.popups': 0,
            'gcm.channel_status_request_enabled': False,  # Disable GCM channel status
            'gcm.channel_enabled': False,  # Disable GCM channel
        })

        # Suppress DevTools listening message
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # User agent to avoid detection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Suppress all Chrome logs to avoid GCM and other error messages
        chrome_options.add_argument('--log-level=3')  # Only show fatal errors
        chrome_options.add_argument('--silent')

        # ADVANCED: Anti-detection measures to avoid CAPTCHA
        # These make Chrome appear more like a real user
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Hide webdriver flag
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Additional stealth options
        chrome_options.add_argument('--start-maximized')  # Real users typically maximize
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--window-size=1920,1080')  # Common resolution

        # Browser will use system proxy settings automatically
        # No need to configure proxy manually - it inherits from Windows

        # Set service log path to suppress output
        import os
        service_log_path = os.devnull  # Redirect logs to null device

        # Try system ChromeDriver first to avoid quota issues with webdriver-manager
        try:
            self.logger.info("Attempting to use system ChromeDriver...")
            from selenium.webdriver.chrome.service import Service
            service = Service(log_path=service_log_path)
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            self.logger.warning(f"System ChromeDriver failed: {e}")

        # Detect Chrome version and download matching ChromeDriver
        try:
            chrome_version, major_version = self._get_chrome_version()

            if chrome_version and major_version:
                self.logger.info(f"Downloading ChromeDriver matching Chrome {chrome_version}...")
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service

                # Download ChromeDriver matching the detected Chrome version
                driver_path = ChromeDriverManager(driver_version=chrome_version).install()
                self.logger.info(f"ChromeDriver installed at: {driver_path}")
                service = Service(executable_path=driver_path, log_path=service_log_path)
                return webdriver.Chrome(service=service, options=chrome_options)
            else:
                # If version detection failed, try downloading latest
                self.logger.warning("Chrome version detection failed, attempting to download latest ChromeDriver...")
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                driver_path = ChromeDriverManager().install()
                service = Service(executable_path=driver_path, log_path=service_log_path)
                return webdriver.Chrome(service=service, options=chrome_options)

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
    
    
    def _save_debug_screenshot(self, filename="debug.png"):
        """Save screenshot for debugging"""
        try:
            screenshot_path = os.path.join(os.getcwd(), filename)
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Debug screenshot saved to: {screenshot_path}")
        except Exception as e:
            self.logger.warning(f"Failed to save debug screenshot: {e}")

    def _search_google(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Google using Selenium"""
        results = []

        try:
            # Ensure browser session is alive before searching
            self._ensure_browser_ready()

            # Navigate to Google
            search_url = f"https://www.google.com/search?q={query}"
            self.logger.info(f"Navigating to: {search_url}")
            self.driver.get(search_url)

            # Add human-like delay before interacting with page
            self._human_delay(0.5, 1.5)

            # Save screenshot for debugging
            self._save_debug_screenshot("google_search_debug.png")

            # Wait for results - Try multiple selectors in case Google layout changed
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#search"))
                )
            except TimeoutException:
                # Google might be blocking us or showing CAPTCHA
                # Try alternative selector or log page source
                self.logger.warning("Could not find #search element, trying alternative...")
                page_title = self.driver.title
                self.logger.warning(f"Page title: {page_title}")

                # Check if we're blocked or got CAPTCHA
                if "captcha" in page_title.lower() or "unusual traffic" in self.driver.page_source.lower():
                    self.logger.error("Google detected automated traffic (CAPTCHA). Switching to DuckDuckGo.")
                    raise Exception("Google CAPTCHA detected")

                # Try waiting for body at least
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

            # Find result containers - Google uses div.g for each result
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")

            for element in result_elements[:max_results]:
                try:
                    # Extract title - Google uses h3 inside a link
                    title_element = element.find_element(By.CSS_SELECTOR, "h3")
                    title = title_element.text.strip()

                    # Get the parent anchor tag for URL
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    url = link_element.get_attribute("href")

                    # Extract snippet - Google uses various classes for snippets
                    snippet = ""
                    try:
                        snippet_element = element.find_element(By.CSS_SELECTOR, ".VwiC3b")
                        snippet = snippet_element.text.strip()[:200]
                    except:
                        try:
                            # Alternative selector
                            snippet_element = element.find_element(By.CSS_SELECTOR, "[data-sncf]")
                            snippet = snippet_element.text.strip()[:200]
                        except:
                            try:
                                # Fallback: another common snippet class
                                snippet_element = element.find_element(By.CSS_SELECTOR, ".lEBKkf")
                                snippet = snippet_element.text.strip()[:200]
                            except:
                                pass

                    # Skip if no title or URL, or URL is not a valid http(s) link
                    if not title or not url or not url.startswith('http'):
                        continue

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
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        return results

    def _search_bing(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Bing using Selenium (no CAPTCHA, works reliably)"""
        results = []

        try:
            # Ensure browser session is alive before searching
            self._ensure_browser_ready()

            # Navigate to Bing
            search_url = f"https://www.bing.com/search?q={query}"
            self.logger.info(f"Navigating to Bing: {search_url}")
            self.driver.get(search_url)

            # Save screenshot for debugging
            self._save_debug_screenshot("bing_search_debug.png")

            # Wait for results - Bing uses #b_results container
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#b_results"))
                )
            except TimeoutException:
                # Bing might have issues, log for debugging
                self.logger.warning("Could not find #b_results element")
                page_title = self.driver.title
                self.logger.warning(f"Page title: {page_title}")
                raise

            # Find result containers - Bing uses li.b_algo for organic results
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.b_algo")

            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL - Bing structure
                    link_element = element.find_element(By.CSS_SELECTOR, "h2 a")
                    title = link_element.text.strip()
                    url = link_element.get_attribute("href")

                    # Extract snippet
                    snippet = ""
                    try:
                        # Bing uses p.b_algoSlug or .b_caption p for snippets
                        snippet_element = element.find_element(By.CSS_SELECTOR, ".b_caption p")
                        snippet = snippet_element.text.strip()[:200]
                    except:
                        try:
                            # Alternative selector
                            snippet_element = element.find_element(By.CSS_SELECTOR, ".b_algoSlug")
                            snippet = snippet_element.text.strip()[:200]
                        except:
                            pass

                    # Skip if no title or URL
                    if not title or not url or not url.startswith('http'):
                        continue

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
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        return results

    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo using Selenium (fallback when Google fails)"""
        results = []

        try:
            # Ensure browser session is alive before searching
            self._ensure_browser_ready()

            # Navigate to DuckDuckGo
            search_url = f"https://duckduckgo.com/?q={query}"
            self.logger.info(f"Navigating to DuckDuckGo: {search_url}")
            self.driver.get(search_url)

            # Save screenshot for debugging
            self._save_debug_screenshot("duckduckgo_search_debug.png")

            # Wait for results - DuckDuckGo uses different selectors
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
                )
            except TimeoutException:
                # DuckDuckGo might have issues, log for debugging
                self.logger.warning("Could not find DuckDuckGo result elements")
                page_title = self.driver.title
                self.logger.warning(f"Page title: {page_title}")
                raise

            # Find result containers
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']")

            for element in result_elements[:max_results]:
                try:
                    # Extract title and URL - DuckDuckGo structure
                    link_element = element.find_element(By.CSS_SELECTOR, "article h2 a")
                    title = link_element.text.strip()
                    url = link_element.get_attribute("href")

                    # Extract snippet
                    snippet = ""
                    try:
                        snippet_elements = element.find_elements(By.CSS_SELECTOR, "[data-result='snippet']")
                        if snippet_elements:
                            snippet = snippet_elements[0].text.strip()[:200]
                    except:
                        pass

                    # Skip if no title or URL
                    if not title or not url or not url.startswith('http'):
                        continue

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
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        return results


    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Perform web search using browser automation with configurable search engine

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []

        max_results = max_results or self.max_results

        # Try preferred search engine first
        if self.preferred_engine == 'bing':
            results = self._search_bing(query, max_results)
            if results:
                self.logger.info(f"Found {len(results)} results from Bing")
                time.sleep(self.delay_between_requests)
                return results

            # Fallback to Google if configured
            if self.fallback_to_google:
                self.logger.warning("Bing search returned no results, trying Google...")
                results = self._search_google(query, max_results)
                if results:
                    self.logger.info(f"Found {len(results)} results from Google")
                    time.sleep(self.delay_between_requests)
                    return results

        elif self.preferred_engine == 'duckduckgo':
            results = self._search_duckduckgo(query, max_results)
            if results:
                self.logger.info(f"Found {len(results)} results from DuckDuckGo")
                time.sleep(self.delay_between_requests)
                return results

            # Fallback to Bing or Google if configured
            if self.fallback_to_google:
                self.logger.warning("DuckDuckGo search returned no results, trying Bing...")
                results = self._search_bing(query, max_results)
                if results:
                    self.logger.info(f"Found {len(results)} results from Bing")
                    time.sleep(self.delay_between_requests)
                    return results
        else:
            # Default: Try Google first
            results = self._search_google(query, max_results)
            if results:
                self.logger.info(f"Found {len(results)} results from Google")
                time.sleep(self.delay_between_requests)
                return results

            # Fallback to Bing first, then DuckDuckGo
            self.logger.warning("Google search returned no results, trying Bing...")
            results = self._search_bing(query, max_results)
            if results:
                self.logger.info(f"Found {len(results)} results from Bing")
                time.sleep(self.delay_between_requests)
                return results

            self.logger.warning("Bing search returned no results, trying DuckDuckGo...")
            results = self._search_duckduckgo(query, max_results)
            if results:
                self.logger.info(f"Found {len(results)} results from DuckDuckGo")
                time.sleep(self.delay_between_requests)
                return results

        self.logger.warning("All search engines returned no results")
        return results
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Search and format results for LLM context"""
        results = self.search(query, max_results)

        if not results:
            return f"No browser search results found for: {query}"

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
            # Ensure browser is ready before testing
            self._ensure_browser_ready()

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
            print("Using Google search engine")
            
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