#!/usr/bin/env python3
"""
Playwright Web Search Test Script
Tests web search functionality using Playwright browser automation
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional

def check_playwright_installation():
    """Check if Playwright is properly installed"""
    print("Checking Playwright installation...")
    
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright module found")
        return True
    except ImportError:
        print("✗ Playwright not installed")
        print("To install Playwright:")
        print("  pip install playwright")
        print("  playwright install")
        return False

class PlaywrightWebSearcher:
    """Web searcher using Playwright browser automation"""
    
    def __init__(self, headless: bool = True):
        """Initialize Playwright searcher"""
        self.headless = headless
        self.results = []
        
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search DuckDuckGo using Playwright"""
        print(f"Searching DuckDuckGo for: {query}")
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                # Set user agent
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                print("  - Browser launched")
                
                # Navigate to DuckDuckGo
                page.goto("https://duckduckgo.com", timeout=30000)
                print("  - Navigated to DuckDuckGo")
                
                # Find search box and enter query
                search_box = page.locator('input[name="q"]')
                search_box.fill(query)
                search_box.press("Enter")
                print("  - Search submitted")
                
                # Wait for results to load
                try:
                    page.wait_for_selector('[data-testid="result"]', timeout=15000)
                    print("  - Results loaded")
                except Exception:
                    # Try alternative selector
                    try:
                        page.wait_for_selector('.results .result', timeout=10000)
                        print("  - Results loaded (alternative selector)")
                    except Exception:
                        print("  - Timeout waiting for results")
                        browser.close()
                        return []
                
                # Extract results
                results = []
                
                # Try different selectors for DuckDuckGo results
                selectors_to_try = [
                    '[data-testid="result"]',
                    '.results .result',
                    '.web-result',
                    'article[data-testid="result"]'
                ]
                
                for selector in selectors_to_try:
                    try:
                        result_elements = page.locator(selector).all()
                        if result_elements:
                            print(f"  - Found {len(result_elements)} elements with selector: {selector}")
                            break
                    except Exception:
                        continue
                else:
                    print("  - No results found with any selector")
                    browser.close()
                    return []
                
                # Extract data from result elements
                for i, element in enumerate(result_elements[:max_results]):
                    try:
                        # Try to get title
                        title = ""
                        title_selectors = ['h2 a', 'h3 a', '.result__title a', '[data-testid="result-title-a"]']
                        for title_sel in title_selectors:
                            try:
                                title_elem = element.locator(title_sel).first
                                if title_elem.is_visible():
                                    title = title_elem.text_content().strip()
                                    break
                            except Exception:
                                continue
                        
                        # Try to get URL
                        url = ""
                        for title_sel in title_selectors:
                            try:
                                title_elem = element.locator(title_sel).first
                                if title_elem.is_visible():
                                    url = title_elem.get_attribute('href') or ""
                                    break
                            except Exception:
                                continue
                        
                        # Try to get snippet
                        snippet = ""
                        snippet_selectors = ['.result__snippet', '[data-testid="result-snippet"]', '.result-snippet']
                        for snippet_sel in snippet_selectors:
                            try:
                                snippet_elem = element.locator(snippet_sel).first
                                if snippet_elem.is_visible():
                                    snippet = snippet_elem.text_content().strip()
                                    break
                            except Exception:
                                continue
                        
                        if title and url:
                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'url': url,
                                'source': 'DuckDuckGo (Playwright)'
                            })
                            print(f"    {len(results)}. {title[:50]}...")
                    
                    except Exception as e:
                        print(f"    Error extracting result {i+1}: {e}")
                        continue
                
                browser.close()
                print(f"  - Extracted {len(results)} results")
                return results
                
        except Exception as e:
            print(f"  ✗ DuckDuckGo search failed: {e}")
            return []
    
    def search_bing(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search Bing using Playwright"""
        print(f"Searching Bing for: {query}")
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                print("  - Browser launched")
                
                # Navigate to Bing
                page.goto("https://www.bing.com", timeout=30000)
                print("  - Navigated to Bing")
                
                # Find search box and enter query
                search_box = page.locator('input[name="q"]')
                search_box.fill(query)
                search_box.press("Enter")
                print("  - Search submitted")
                
                # Wait for results
                try:
                    page.wait_for_selector('.b_algo', timeout=15000)
                    print("  - Results loaded")
                except Exception:
                    print("  - Timeout waiting for results")
                    browser.close()
                    return []
                
                # Extract results
                results = []
                result_elements = page.locator('.b_algo').all()
                
                print(f"  - Found {len(result_elements)} result elements")
                
                for i, element in enumerate(result_elements[:max_results]):
                    try:
                        # Get title and URL
                        title_elem = element.locator('h2 a').first
                        title = title_elem.text_content().strip() if title_elem.is_visible() else ""
                        url = title_elem.get_attribute('href') or "" if title_elem.is_visible() else ""
                        
                        # Get snippet
                        snippet = ""
                        snippet_selectors = ['.b_caption p', '.b_snippet']
                        for snippet_sel in snippet_selectors:
                            try:
                                snippet_elem = element.locator(snippet_sel).first
                                if snippet_elem.is_visible():
                                    snippet = snippet_elem.text_content().strip()
                                    break
                            except Exception:
                                continue
                        
                        if title and url and not url.startswith('javascript:'):
                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'url': url,
                                'source': 'Bing (Playwright)'
                            })
                            print(f"    {len(results)}. {title[:50]}...")
                    
                    except Exception as e:
                        print(f"    Error extracting result {i+1}: {e}")
                        continue
                
                browser.close()
                print(f"  - Extracted {len(results)} results")
                return results
                
        except Exception as e:
            print(f"  ✗ Bing search failed: {e}")
            return []
    
    def search_google(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search Google using Playwright"""
        print(f"Searching Google for: {query}")
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                print("  - Browser launched")
                
                # Navigate to Google
                page.goto("https://www.google.com", timeout=30000)
                print("  - Navigated to Google")
                
                # Handle consent/cookie banner if present
                try:
                    # Look for accept buttons
                    accept_selectors = [
                        'button:has-text("Accept")',
                        'button:has-text("I agree")',
                        'button:has-text("Accept all")',
                        '#L2AGLb'  # Google's accept button ID
                    ]
                    
                    for selector in accept_selectors:
                        try:
                            accept_btn = page.locator(selector).first
                            if accept_btn.is_visible():
                                accept_btn.click()
                                print("  - Accepted cookies/terms")
                                time.sleep(1)
                                break
                        except Exception:
                            continue
                            
                except Exception:
                    pass
                
                # Find search box and enter query
                search_selectors = ['input[name="q"]', 'textarea[name="q"]']
                search_box = None
                
                for selector in search_selectors:
                    try:
                        search_box = page.locator(selector).first
                        if search_box.is_visible():
                            break
                    except Exception:
                        continue
                
                if not search_box:
                    print("  - Could not find search box")
                    browser.close()
                    return []
                
                search_box.fill(query)
                search_box.press("Enter")
                print("  - Search submitted")
                
                # Wait for results
                try:
                    page.wait_for_selector('.g', timeout=15000)
                    print("  - Results loaded")
                except Exception:
                    print("  - Timeout waiting for results")
                    browser.close()
                    return []
                
                # Extract results
                results = []
                result_elements = page.locator('.g').all()
                
                print(f"  - Found {len(result_elements)} result elements")
                
                for i, element in enumerate(result_elements[:max_results]):
                    try:
                        # Get title and URL
                        title_elem = element.locator('h3').first
                        title = title_elem.text_content().strip() if title_elem.is_visible() else ""
                        
                        # Get URL from parent link
                        url = ""
                        try:
                            link_elem = element.locator('a').first
                            if link_elem.is_visible():
                                url = link_elem.get_attribute('href') or ""
                        except Exception:
                            pass
                        
                        # Get snippet
                        snippet = ""
                        snippet_selectors = ['.VwiC3b', '.s3v9rd', '.st']
                        for snippet_sel in snippet_selectors:
                            try:
                                snippet_elem = element.locator(snippet_sel).first
                                if snippet_elem.is_visible():
                                    snippet = snippet_elem.text_content().strip()
                                    break
                            except Exception:
                                continue
                        
                        if title and url and not url.startswith('javascript:'):
                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'url': url,
                                'source': 'Google (Playwright)'
                            })
                            print(f"    {len(results)}. {title[:50]}...")
                    
                    except Exception as e:
                        print(f"    Error extracting result {i+1}: {e}")
                        continue
                
                browser.close()
                print(f"  - Extracted {len(results)} results")
                return results
                
        except Exception as e:
            print(f"  ✗ Google search failed: {e}")
            return []

def test_playwright_search():
    """Test Playwright web search functionality"""
    print("=" * 60)
    print("PLAYWRIGHT WEB SEARCH TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if Playwright is installed
    if not check_playwright_installation():
        return False
    
    print("\n" + "-" * 40)
    print("PLAYWRIGHT SEARCH TESTS")
    print("-" * 40)
    
    # Create searcher instance
    searcher = PlaywrightWebSearcher(headless=True)
    
    test_queries = [
        "python programming tutorial",
        "machine learning basics"
    ]
    
    all_results = []
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 50)
        
        # Test DuckDuckGo
        print("\n1. Testing DuckDuckGo...")
        ddg_results = searcher.search_duckduckgo(query, max_results=3)
        if ddg_results:
            print(f"✓ DuckDuckGo: Found {len(ddg_results)} results")
            all_results.extend(ddg_results)
        else:
            print("✗ DuckDuckGo: No results")
        
        # Test Bing
        print("\n2. Testing Bing...")
        bing_results = searcher.search_bing(query, max_results=3)
        if bing_results:
            print(f"✓ Bing: Found {len(bing_results)} results")
            all_results.extend(bing_results)
        else:
            print("✗ Bing: No results")
        
        # Test Google (might be blocked by anti-bot measures)
        print("\n3. Testing Google...")
        google_results = searcher.search_google(query, max_results=3)
        if google_results:
            print(f"✓ Google: Found {len(google_results)} results")
            all_results.extend(google_results)
        else:
            print("✗ Google: No results (possibly blocked)")
    
    # Display summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if all_results:
        print(f"✓ Total results found: {len(all_results)}")
        print(f"✓ Search engines that worked:")
        
        sources = set(result['source'] for result in all_results)
        for source in sources:
            count = sum(1 for r in all_results if r['source'] == source)
            print(f"  - {source}: {count} results")
        
        print(f"\nSample results:")
        print("-" * 30)
        for i, result in enumerate(all_results[:5], 1):
            print(f"{i}. {result['title'][:60]}...")
            print(f"   Source: {result['source']}")
            print(f"   URL: {result['url'][:70]}...")
            if result['snippet']:
                print(f"   Snippet: {result['snippet'][:80]}...")
            print()
        
        print("🎉 Playwright web search is working!")
        return True
        
    else:
        print("❌ No results found from any search engine")
        print("\nPossible issues:")
        print("- Network connectivity problems")
        print("- Corporate firewall blocking requests")
        print("- Anti-bot measures by search engines")
        print("- Playwright browser installation issues")
        return False

def main():
    """Main test function"""
    print("Playwright Web Search Test Script")
    print("This script tests web search using browser automation")
    print()
    
    success = test_playwright_search()
    
    if success:
        print("\n✅ Playwright web search tests completed successfully!")
        print("\nNext steps:")
        print("1. You can integrate Playwright search into your main application")
        print("2. Consider using it as a fallback when HTTP requests fail")
        print("3. Be aware that Playwright is slower than HTTP requests")
        
    else:
        print("\n❌ Playwright web search tests failed!")
        print("\nTroubleshooting:")
        print("1. Install Playwright: pip install playwright")
        print("2. Install browsers: playwright install")
        print("3. Check your internet connection")
        print("4. Try running with headless=False to see what's happening")
    
    return success

if __name__ == "__main__":
    main()