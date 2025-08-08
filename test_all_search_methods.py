#!/usr/bin/env python3
"""
Comprehensive Web Search Methods Test
Tests all available search methods: HTTP, Playwright, SearX, Whoogle, etc.
Includes proxy support and comprehensive comparison
"""

import os
import sys
import time
import json
import random
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class ComprehensiveSearchTester:
    """Tests all available web search methods"""
    
    def __init__(self, proxy_host: str = None, proxy_port: int = None):
        """Initialize with proxy configuration"""
        self.proxy_config = None
        if proxy_host and proxy_port:
            self.proxy_config = {
                'http': f'http://{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_host}:{proxy_port}'
            }
            print(f"Using proxy: {proxy_host}:{proxy_port}")
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.results_summary = {}
        
    def create_session(self, name: str) -> requests.Session:
        """Create a configured session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'DNT': '1'
        })
        
        if self.proxy_config:
            session.proxies.update(self.proxy_config)
        
        return session
    
    def test_method_1_basic_http(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 1: Basic HTTP requests (current implementation)"""
        method_name = "Basic HTTP (Current)"
        start_time = time.time()
        
        try:
            # Import existing browser search
            from src.browser_search import BrowserSearcher
            searcher = BrowserSearcher()
            
            results = searcher.search(query, max_results=5)
            searcher.close()
            
            elapsed = time.time() - start_time
            success = len(results) > 0
            
            return method_name, success, results, elapsed, "Working" if success else "No results"
            
        except Exception as e:
            elapsed = time.time() - start_time
            return method_name, False, [], elapsed, f"Error: {str(e)}"
    
    def test_method_2_playwright(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 2: Playwright browser automation"""
        method_name = "Playwright Browser"
        start_time = time.time()
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={'server': f'http://{self.proxy_config["http"].split("://")[1]}'} if self.proxy_config else None
                )
                page = browser.new_page()
                
                # Test DuckDuckGo
                page.goto("https://duckduckgo.com", timeout=30000)
                search_box = page.locator('input[name="q"]')
                search_box.fill(query)
                search_box.press("Enter")
                
                try:
                    page.wait_for_selector('[data-testid="result"]', timeout=15000)
                    result_elements = page.locator('[data-testid="result"]').all()
                except:
                    try:
                        page.wait_for_selector('.results .result', timeout=10000)
                        result_elements = page.locator('.results .result').all()
                    except:
                        result_elements = []
                
                results = []
                for i, element in enumerate(result_elements[:5]):
                    try:
                        title_elem = element.locator('h2 a, h3 a, .result__title a').first
                        title = title_elem.text_content().strip() if title_elem.is_visible() else ""
                        url = title_elem.get_attribute('href') or "" if title_elem.is_visible() else ""
                        
                        snippet_elem = element.locator('.result__snippet, [data-testid="result-snippet"]').first
                        snippet = snippet_elem.text_content().strip() if snippet_elem.is_visible() else ""
                        
                        if title and url:
                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'url': url,
                                'source': 'Playwright-DuckDuckGo'
                            })
                    except:
                        continue
                
                browser.close()
                
            elapsed = time.time() - start_time
            success = len(results) > 0
            
            return method_name, success, results, elapsed, f"Found {len(results)} results"
            
        except ImportError:
            elapsed = time.time() - start_time
            return method_name, False, [], elapsed, "Playwright not installed"
        except Exception as e:
            elapsed = time.time() - start_time
            return method_name, False, [], elapsed, f"Error: {str(e)}"
    
    def test_method_3_searx(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 3: SearX instances"""
        method_name = "SearX Instances"
        start_time = time.time()
        
        searx_instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.xyz",
            "https://paulgo.io",
            "https://searx.prvcy.eu",
            "https://search.bus-hit.me",
            "https://searx.tiekoetter.com"
        ]
        
        session = self.create_session('searx')
        
        for instance in searx_instances:
            try:
                params = {
                    'q': query,
                    'format': 'json',
                    'engines': 'google,bing,duckduckgo',
                    'categories': 'general'
                }
                
                response = session.get(f"{instance}/search", params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get('results', [])[:5]:
                        if result.get('title') and result.get('url'):
                            results.append({
                                'title': result.get('title', '').strip(),
                                'snippet': result.get('content', '').strip(),
                                'url': result.get('url', ''),
                                'source': f'SearX ({instance})'
                            })
                    
                    if results:
                        elapsed = time.time() - start_time
                        session.close()
                        return method_name, True, results, elapsed, f"Found {len(results)} via {instance}"
                
            except Exception as e:
                continue
        
        elapsed = time.time() - start_time
        session.close()
        return method_name, False, [], elapsed, "All SearX instances failed"
    
    def test_method_4_whoogle(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 4: Whoogle instances"""
        method_name = "Whoogle Instances"
        start_time = time.time()
        
        whoogle_instances = [
            "https://whoogle.lunar.icu",
            "https://search.garudalinux.org",
            "https://whoogle.dcs0.hu",
            "https://whoogle.privacydev.net",
            "https://whoogle.hostux.net"
        ]
        
        session = self.create_session('whoogle')
        
        for instance in whoogle_instances:
            try:
                params = {'q': query}
                response = session.get(f"{instance}/search", params=params, timeout=15)
                
                if response.status_code == 200:
                    results = self._parse_whoogle_results(response.text)
                    if results:
                        elapsed = time.time() - start_time
                        session.close()
                        return method_name, True, results[:5], elapsed, f"Found {len(results)} via {instance}"
                
            except Exception as e:
                continue
        
        elapsed = time.time() - start_time
        session.close()
        return method_name, False, [], elapsed, "All Whoogle instances failed"
    
    def test_method_5_yandex(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 5: Yandex search"""
        method_name = "Yandex Search"
        start_time = time.time()
        
        try:
            session = self.create_session('yandex')
            
            params = {
                'text': query,
                'lr': '84',  # English region
                'lang': 'en'
            }
            
            response = session.get("https://yandex.com/search/", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_yandex_results(response.text)
                elapsed = time.time() - start_time
                session.close()
                
                success = len(results) > 0
                return method_name, success, results[:5], elapsed, f"Found {len(results)} results" if success else "No results parsed"
            
        except Exception as e:
            pass
        
        elapsed = time.time() - start_time
        return method_name, False, [], elapsed, "Failed to connect or parse"
    
    def test_method_6_brave(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 6: Brave Search"""
        method_name = "Brave Search"
        start_time = time.time()
        
        try:
            session = self.create_session('brave')
            
            params = {
                'q': query,
                'source': 'web'
            }
            
            response = session.get("https://search.brave.com/search", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_brave_results(response.text)
                elapsed = time.time() - start_time
                session.close()
                
                success = len(results) > 0
                return method_name, success, results[:5], elapsed, f"Found {len(results)} results" if success else "No results parsed"
            
        except Exception as e:
            pass
        
        elapsed = time.time() - start_time
        return method_name, False, [], elapsed, "Failed to connect or parse"
    
    def test_method_7_startpage(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 7: Startpage advanced"""
        method_name = "Startpage Advanced"
        start_time = time.time()
        
        try:
            session = self.create_session('startpage')
            
            # Get main page first
            session.get("https://www.startpage.com", timeout=15)
            time.sleep(1)
            
            params = {
                'query': query,
                'cat': 'web',
                'pl': 'opensearch',
                'language': 'english'
            }
            
            response = session.get("https://www.startpage.com/sp/search", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_startpage_results(response.text)
                elapsed = time.time() - start_time
                session.close()
                
                success = len(results) > 0
                return method_name, success, results[:5], elapsed, f"Found {len(results)} results" if success else "No results parsed"
            
        except Exception as e:
            pass
        
        elapsed = time.time() - start_time
        return method_name, False, [], elapsed, "Failed to connect or parse"
    
    def test_method_8_duckduckgo_advanced(self, query: str) -> Tuple[str, bool, List[Dict], float, str]:
        """Test Method 8: DuckDuckGo advanced with token"""
        method_name = "DuckDuckGo Advanced"
        start_time = time.time()
        
        try:
            session = self.create_session('duckduckgo')
            
            # Get VQD token
            main_response = session.get("https://duckduckgo.com/", timeout=15)
            vqd_match = re.search(r'vqd=["\']?([^"\'&\s]+)', main_response.text)
            
            if vqd_match:
                vqd = vqd_match.group(1)
                
                params = {
                    'q': query,
                    'vqd': vqd,
                    'kl': 'us-en',
                    'l': 'us-en',
                    's': '0'
                }
                
                search_response = session.get("https://links.duckduckgo.com/d.js", params=params, timeout=15)
                
                if search_response.status_code == 200:
                    results = self._parse_duckduckgo_json(search_response.text)
                    elapsed = time.time() - start_time
                    session.close()
                    
                    success = len(results) > 0
                    return method_name, success, results[:5], elapsed, f"Found {len(results)} results" if success else "No results parsed"
            
            # Fallback to HTML
            params = {'q': query, 'kl': 'us-en'}
            html_response = session.get("https://html.duckduckgo.com/html/", params=params, timeout=15)
            
            if html_response.status_code == 200:
                results = self._parse_duckduckgo_html(html_response.text)
                elapsed = time.time() - start_time
                session.close()
                
                success = len(results) > 0
                return method_name, success, results[:5], elapsed, f"Found {len(results)} results (HTML fallback)" if success else "HTML fallback failed"
            
        except Exception as e:
            pass
        
        elapsed = time.time() - start_time
        return method_name, False, [], elapsed, "Failed to get token and HTML fallback failed"
    
    # Helper methods for parsing
    def _parse_whoogle_results(self, html: str) -> List[Dict[str, str]]:
        """Parse Whoogle search results"""
        results = []
        try:
            pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches:
                if url.startswith('http') and 'whoogle' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Whoogle'
                    })
        except:
            pass
        return results
    
    def _parse_yandex_results(self, html: str) -> List[Dict[str, str]]:
        """Parse Yandex results"""
        results = []
        try:
            patterns = [
                r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>',
                r'<div[^>]*class="[^"]*organic[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                for url, title in matches:
                    if url.startswith('http') and 'yandex' not in url:
                        results.append({
                            'title': self._clean_text(title),
                            'snippet': '',
                            'url': url,
                            'source': 'Yandex'
                        })
                if results:
                    break
        except:
            pass
        return results
    
    def _parse_brave_results(self, html: str) -> List[Dict[str, str]]:
        """Parse Brave Search results"""
        results = []
        try:
            pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches:
                if url.startswith('http') and 'brave.com' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Brave'
                    })
        except:
            pass
        return results
    
    def _parse_startpage_results(self, html: str) -> List[Dict[str, str]]:
        """Parse Startpage results"""
        results = []
        try:
            patterns = [
                r'<a[^>]+class="[^"]*w-gl__result-title[^"]*"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
                r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for url, title in matches:
                    if url.startswith('http'):
                        results.append({
                            'title': self._clean_text(title),
                            'snippet': '',
                            'url': url,
                            'source': 'Startpage'
                        })
                if results:
                    break
        except:
            pass
        return results
    
    def _parse_duckduckgo_json(self, response_text: str) -> List[Dict[str, str]]:
        """Parse DuckDuckGo JSON response"""
        results = []
        try:
            if response_text.startswith('DDG.pageLayout.load.searchResults('):
                json_str = response_text[len('DDG.pageLayout.load.searchResults('):-2]
                data = json.loads(json_str)
                
                for item in data.get('results', []):
                    if item.get('t') and item.get('u'):
                        results.append({
                            'title': self._clean_text(item.get('t', '')),
                            'snippet': self._clean_text(item.get('a', '')),
                            'url': item.get('u', ''),
                            'source': 'DuckDuckGo-JSON'
                        })
        except:
            pass
        return results
    
    def _parse_duckduckgo_html(self, html: str) -> List[Dict[str, str]]:
        """Parse DuckDuckGo HTML results"""
        results = []
        try:
            pattern = r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches:
                if url.startswith('http'):
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'DuckDuckGo-HTML'
                    })
        except:
            pass
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML text"""
        if not text:
            return ''
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def run_comprehensive_test(self, query: str = "python programming tutorial") -> Dict:
        """Run all search methods and compare results"""
        print("=" * 70)
        print("COMPREHENSIVE WEB SEARCH METHODS TEST")
        print("=" * 70)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Query: '{query}'")
        if self.proxy_config:
            print(f"Using proxy: {self.proxy_config['http']}")
        print()
        
        # List of all test methods
        test_methods = [
            self.test_method_1_basic_http,
            self.test_method_2_playwright,
            self.test_method_3_searx,
            self.test_method_4_whoogle,
            self.test_method_5_yandex,
            self.test_method_6_brave,
            self.test_method_7_startpage,
            self.test_method_8_duckduckgo_advanced
        ]
        
        results = {}
        
        # Run tests with timeout using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_method = {executor.submit(method, query): method.__name__ for method in test_methods}
            
            for future in as_completed(future_to_method, timeout=300):  # 5 minute total timeout
                method_name = future_to_method[future]
                try:
                    name, success, search_results, elapsed, message = future.result(timeout=60)  # 1 minute per method
                    results[name] = {
                        'success': success,
                        'results': search_results,
                        'elapsed_time': elapsed,
                        'message': message,
                        'result_count': len(search_results)
                    }
                    
                    status = "✓" if success else "✗"
                    print(f"{status} {name}: {message} ({elapsed:.2f}s)")
                    
                except Exception as e:
                    results[method_name] = {
                        'success': False,
                        'results': [],
                        'elapsed_time': 0,
                        'message': f"Timeout or error: {str(e)}",
                        'result_count': 0
                    }
                    print(f"✗ {method_name}: Timeout or error")
        
        return results
    
    def print_detailed_results(self, results: Dict):
        """Print detailed test results"""
        print("\n" + "=" * 70)
        print("DETAILED RESULTS")
        print("=" * 70)
        
        # Summary statistics
        successful_methods = [name for name, data in results.items() if data['success']]
        total_results = sum(data['result_count'] for data in results.values())
        
        print(f"Methods tested: {len(results)}")
        print(f"Successful methods: {len(successful_methods)}")
        print(f"Total results found: {total_results}")
        print()
        
        # Rankings by success and speed
        if successful_methods:
            print("🏆 RANKINGS:")
            print("-" * 30)
            
            # Sort by result count, then by speed
            ranked = sorted(
                [(name, data) for name, data in results.items() if data['success']], 
                key=lambda x: (-x[1]['result_count'], x[1]['elapsed_time'])
            )
            
            for i, (name, data) in enumerate(ranked, 1):
                print(f"{i}. {name}")
                print(f"   Results: {data['result_count']} | Time: {data['elapsed_time']:.2f}s")
                print(f"   Status: {data['message']}")
                print()
        
        # Show sample results from best method
        if successful_methods:
            best_method_name = max(
                successful_methods, 
                key=lambda x: results[x]['result_count']
            )
            best_results = results[best_method_name]['results']
            
            print(f"📋 SAMPLE RESULTS FROM BEST METHOD ({best_method_name}):")
            print("-" * 50)
            for i, result in enumerate(best_results[:3], 1):
                print(f"{i}. {result['title'][:60]}...")
                print(f"   URL: {result['url'][:70]}...")
                if result['snippet']:
                    print(f"   Snippet: {result['snippet'][:80]}...")
                print(f"   Source: {result['source']}")
                print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        print("-" * 20)
        
        if successful_methods:
            if len(successful_methods) >= 3:
                print("✅ Multiple methods working - excellent redundancy!")
                print("   Recommended approach: Use fastest method as primary,")
                print("   others as fallbacks.")
            elif len(successful_methods) >= 1:
                print("⚠️  Limited methods working - consider implementing more fallbacks.")
            
            # Specific recommendations
            if "SearX Instances" in successful_methods:
                print("🔥 SearX is working - this is usually the most reliable!")
            if "Playwright Browser" in successful_methods:
                print("🌟 Playwright working - best for handling anti-bot measures")
            if "Basic HTTP (Current)" in successful_methods:
                print("⚡ Your current HTTP method is working - fast and lightweight")
            
        else:
            print("❌ No methods working!")
            print("Possible issues:")
            print("- Network connectivity problems")
            print("- Proxy configuration issues")
            print("- All search engines blocking requests")
            print("- Firewall restrictions")
        
        print()
        print("🎯 NEXT STEPS:")
        if successful_methods:
            print("1. Integrate the top 2-3 working methods into your main system")
            print("2. Use them in order of preference (fastest/most reliable first)")
            print("3. Implement automatic fallback when primary method fails")
            print("4. Add result caching to reduce repeated requests")
        else:
            print("1. Check network connectivity")
            print("2. Verify proxy settings")
            print("3. Try running without proxy")
            print("4. Consider VPN or different network")

def main():
    """Main test function"""
    print("Comprehensive Web Search Methods Test")
    print("Tests all available search methods with your proxy configuration")
    print()
    
    # Configure proxy (your proxy)
    proxy_host = "168.219.61.252"
    proxy_port = 8080
    
    # Create tester
    tester = ComprehensiveSearchTester(proxy_host, proxy_port)
    
    # Test queries
    test_queries = [
        "python programming tutorial",
        "machine learning basics"
    ]
    
    all_results = {}
    
    for query in test_queries:
        print(f"\n🔍 Testing with query: '{query}'")
        print("=" * 50)
        
        results = tester.run_comprehensive_test(query)
        all_results[query] = results
        
        tester.print_detailed_results(results)
        
        # Wait between queries
        if query != test_queries[-1]:
            print("\n⏳ Waiting 5 seconds before next query...")
            time.sleep(5)
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    # Aggregate statistics across all queries
    all_methods = set()
    method_success_rates = {}
    
    for query, results in all_results.items():
        for method_name, data in results.items():
            all_methods.add(method_name)
            if method_name not in method_success_rates:
                method_success_rates[method_name] = []
            method_success_rates[method_name].append(data['success'])
    
    print("📊 SUCCESS RATES ACROSS ALL QUERIES:")
    print("-" * 40)
    for method_name in sorted(all_methods):
        successes = method_success_rates[method_name]
        success_rate = sum(successes) / len(successes) * 100
        status = "🟢" if success_rate >= 75 else "🟡" if success_rate >= 25 else "🔴"
        print(f"{status} {method_name}: {success_rate:.0f}% ({sum(successes)}/{len(successes)})")
    
    # Save results to file
    try:
        with open('comprehensive_search_test_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: comprehensive_search_test_results.json")
    except Exception as e:
        print(f"\n❌ Could not save results file: {e}")
    
    print("\n🎉 Comprehensive test completed!")
    return all_results

if __name__ == "__main__":
    main()