#!/usr/bin/env python3
"""
Browser Automation Test Script
Tests Chrome browser automation to perform web searches when APIs are blocked
"""

import time
import json
import sys
import traceback
from datetime import datetime

def test_selenium_chrome():
    """Test Selenium with Chrome browser"""
    print("\n=== Testing Selenium Chrome Automation ===")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        print("✓ Selenium modules imported successfully")
        
        # Configure Chrome options
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        print("✓ Chrome options configured")
        
        # Initialize driver
        driver = webdriver.Chrome(options=options)
        print("✓ Chrome driver initialized")
        
        # Test search query
        query = "python programming tutorial"
        print(f"Searching for: {query}")
        
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(2)
        print("✓ Navigated to Google")
        
        # Find and fill search box
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(3)
        print("✓ Search submitted")
        
        # Extract results
        results = []
        try:
            # Wait for results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3"))
            )
            
            # Find result elements
            result_elements = driver.find_elements(By.CSS_SELECTOR, "div.g")[:5]
            
            for element in result_elements:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, "h3")
                    title = title_elem.text
                    
                    # Try to get snippet
                    snippet = ""
                    try:
                        snippet_elem = element.find_element(By.CSS_SELECTOR, "[data-salhash] span")
                        snippet = snippet_elem.text
                    except:
                        pass
                    
                    # Try to get URL
                    url = ""
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, "a")
                        url = link_elem.get_attribute("href")
                    except:
                        pass
                    
                    if title:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": url
                        })
                except Exception as e:
                    continue
            
            print(f"✓ Found {len(results)} search results")
            
        except Exception as e:
            print(f"⚠ Warning: Could not extract results - {str(e)}")
        
        driver.quit()
        print("✓ Chrome driver closed")
        
        return {
            "success": True,
            "method": "Selenium Chrome",
            "results": results,
            "result_count": len(results)
        }
        
    except ImportError as e:
        return {
            "success": False,
            "method": "Selenium Chrome",
            "error": f"Import Error: {str(e)}. Run: pip install selenium",
            "results": []
        }
    except Exception as e:
        return {
            "success": False,
            "method": "Selenium Chrome",
            "error": f"Error: {str(e)}",
            "results": []
        }

def test_playwright():
    """Test Playwright browser automation"""
    print("\n=== Testing Playwright Automation ===")
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("✓ Playwright modules imported successfully")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print("✓ Playwright browser launched")
            
            # Test search query
            query = "artificial intelligence basics"
            print(f"Searching for: {query}")
            
            # Navigate to DuckDuckGo (often less restrictive)
            page.goto("https://duckduckgo.com")
            time.sleep(2)
            print("✓ Navigated to DuckDuckGo")
            
            # Perform search
            search_input = page.locator('input[name="q"]')
            search_input.fill(query)
            search_input.press("Enter")
            
            # Wait for results
            page.wait_for_selector('.results', timeout=10000)
            print("✓ Search results loaded")
            
            # Extract results
            results = []
            result_elements = page.locator('.results .result').all()[:5]
            
            for element in result_elements:
                try:
                    title = element.locator('.result__title a').text_content()
                    snippet = element.locator('.result__snippet').text_content() or ""
                    url = element.locator('.result__title a').get_attribute('href') or ""
                    
                    if title:
                        results.append({
                            "title": title.strip(),
                            "snippet": snippet.strip(),
                            "url": url
                        })
                except Exception as e:
                    continue
            
            browser.close()
            print(f"✓ Found {len(results)} search results")
            print("✓ Playwright browser closed")
            
            return {
                "success": True,
                "method": "Playwright",
                "results": results,
                "result_count": len(results)
            }
            
    except ImportError as e:
        return {
            "success": False,
            "method": "Playwright",
            "error": f"Import Error: {str(e)}. Run: pip install playwright && playwright install",
            "results": []
        }
    except Exception as e:
        return {
            "success": False,
            "method": "Playwright",
            "error": f"Error: {str(e)}",
            "results": []
        }

def test_requests_baseline():
    """Test basic requests to compare with browser automation"""
    print("\n=== Testing Baseline HTTP Requests ===")
    
    try:
        import requests
        from urllib.parse import quote_plus
        
        print("✓ Requests module imported")
        
        # Test simple request to Google
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = "machine learning guide"
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        
        print(f"Testing HTTP request to Google search")
        response = requests.get(url, headers=headers, timeout=10)
        
        return {
            "success": response.status_code == 200,
            "method": "HTTP Requests",
            "status_code": response.status_code,
            "content_length": len(response.text),
            "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "HTTP Requests",
            "error": f"Error: {str(e)}"
        }

def main():
    """Run all browser automation tests"""
    print("Browser Automation Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    
    # Store all test results
    all_results = []
    
    # Test 1: Basic HTTP requests (baseline)
    baseline_result = test_requests_baseline()
    all_results.append(baseline_result)
    
    # Test 2: Selenium Chrome
    selenium_result = test_selenium_chrome()
    all_results.append(selenium_result)
    
    # Test 3: Playwright
    playwright_result = test_playwright()
    all_results.append(playwright_result)
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for result in all_results:
        method = result.get('method', 'Unknown')
        success = result.get('success', False)
        status = "SUCCESS" if success else "FAILED"
        
        print(f"{method}: {status}")
        
        if success:
            if 'result_count' in result:
                print(f"   → Found {result['result_count']} search results")
            if 'status_code' in result:
                print(f"   → HTTP Status: {result['status_code']}")
                print(f"   → Content Length: {result['content_length']} chars")
        else:
            print(f"   → Error: {result.get('error', 'Unknown error')}")
        print()
    
    # Show sample results if available
    for result in all_results:
        if result.get('success') and result.get('results'):
            print(f"Sample Results from {result['method']}:")
            print("-" * 40)
            for i, res in enumerate(result['results'][:2], 1):
                print(f"{i}. {res.get('title', 'No title')}")
                if res.get('snippet'):
                    print(f"   {res['snippet'][:100]}...")
                if res.get('url'):
                    print(f"   URL: {res['url']}")
                print()
            break
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print("-" * 20)
    
    successful_methods = [r for r in all_results if r.get('success')]
    
    if successful_methods:
        best_method = max(successful_methods, key=lambda x: x.get('result_count', 0))
        print(f"Best method: {best_method['method']}")
        
        if any('Selenium' in r['method'] for r in successful_methods):
            print("Selenium Chrome works - good for complex interactions")
        
        if any('Playwright' in r['method'] for r in successful_methods):
            print("Playwright works - faster and more modern")
        
        print("\nNext steps:")
        print("1. Install required packages for successful method(s)")
        print("2. Integrate browser automation into your web search system")
        print("3. Add error handling and rate limiting")
        
    else:
        print("No methods worked. Possible issues:")
        print("- Corporate firewall blocking all web access")
        print("- Chrome/Chromium not installed")
        print("- Network connectivity issues")
        print("- Missing dependencies")
    
    # Save detailed results to file
    try:
        with open('browser_test_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: browser_test_results.json")
    except Exception as e:
        print(f"\nCould not save results file: {e}")

if __name__ == "__main__":
    main()