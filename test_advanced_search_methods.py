#!/usr/bin/env python3
"""
Advanced Web Search Methods Test
Tests various non-API web search methods that are more robust than basic HTTP
"""

import os
import sys
import time
import json
import random
from datetime import datetime
from typing import List, Dict, Optional
import requests
from urllib.parse import quote_plus, urljoin
import re

class AdvancedWebSearcher:
    """Advanced web search using multiple robust methods"""
    
    def __init__(self):
        """Initialize with rotating user agents and session management"""
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        self.sessions = {}
        self.proxy_list = []  # Can be populated with working proxies
    
    def get_session(self, engine: str) -> requests.Session:
        """Get or create a session for specific search engine"""
        if engine not in self.sessions:
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
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'DNT': '1'
            })
            self.sessions[engine] = session
        return self.sessions[engine]
    
    def method_1_searx_instances(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 1: Use public SearX instances (meta search engine)"""
        print("Method 1: Testing SearX instances...")
        
        # Public SearX instances (these change over time)
        searx_instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.xyz",
            "https://paulgo.io",
            "https://searx.prvcy.eu",
            "https://search.bus-hit.me",
            "https://searx.tiekoetter.com",
            "https://search.inetol.net",
            "https://searx.lunar.icu"
        ]
        
        for instance in searx_instances:
            try:
                print(f"  Trying {instance}...")
                session = self.get_session('searx')
                
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
                    
                    for result in data.get('results', [])[:max_results]:
                        if result.get('title') and result.get('url'):
                            results.append({
                                'title': result.get('title', '').strip(),
                                'snippet': result.get('content', '').strip(),
                                'url': result.get('url', ''),
                                'source': f'SearX ({instance})'
                            })
                    
                    if results:
                        print(f"  ✓ Found {len(results)} results from {instance}")
                        return results
                
            except Exception as e:
                print(f"  ✗ {instance} failed: {e}")
                continue
        
        return []
    
    def method_2_whoogle_instances(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 2: Use Whoogle instances (Google proxy)"""
        print("Method 2: Testing Whoogle instances...")
        
        whoogle_instances = [
            "https://whoogle.lunar.icu",
            "https://search.garudalinux.org",
            "https://whoogle.dcs0.hu",
            "https://whoogle.privacydev.net",
            "https://whoogle.hostux.net"
        ]
        
        for instance in whoogle_instances:
            try:
                print(f"  Trying {instance}...")
                session = self.get_session('whoogle')
                
                params = {'q': query}
                response = session.get(f"{instance}/search", params=params, timeout=15)
                
                if response.status_code == 200:
                    results = self._parse_whoogle_results(response.text, max_results)
                    if results:
                        print(f"  ✓ Found {len(results)} results from {instance}")
                        return results
                
            except Exception as e:
                print(f"  ✗ {instance} failed: {e}")
                continue
        
        return []
    
    def method_3_startpage_advanced(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 3: Advanced Startpage scraping with session handling"""
        print("Method 3: Testing advanced Startpage scraping...")
        
        try:
            session = self.get_session('startpage')
            
            # First, get the main page to establish session
            session.get("https://www.startpage.com", timeout=15)
            time.sleep(1)
            
            # Perform search with proper parameters
            params = {
                'query': query,
                'cat': 'web',
                'pl': 'opensearch',
                'language': 'english',
                'family_filter': 'off'
            }
            
            response = session.get("https://www.startpage.com/sp/search", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_startpage_advanced(response.text, max_results)
                if results:
                    print(f"  ✓ Found {len(results)} results from Startpage")
                    return results
            
        except Exception as e:
            print(f"  ✗ Startpage advanced failed: {e}")
        
        return []
    
    def method_4_duckduckgo_advanced(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 4: Advanced DuckDuckGo with proper token handling"""
        print("Method 4: Testing advanced DuckDuckGo...")
        
        try:
            session = self.get_session('duckduckgo')
            
            # Get main page to extract tokens
            main_response = session.get("https://duckduckgo.com/", timeout=15)
            
            # Extract VQD token
            vqd_match = re.search(r'vqd=["\']?([^"\'&\s]+)', main_response.text)
            if not vqd_match:
                # Try alternative method
                token_response = session.post("https://duckduckgo.com/", 
                                            data={'q': query}, timeout=15)
                vqd_match = re.search(r'vqd=["\']?([^"\'&\s]+)', token_response.text)
            
            if vqd_match:
                vqd = vqd_match.group(1)
                print(f"  Got VQD token: {vqd[:10]}...")
                
                # Use the token for search
                params = {
                    'q': query,
                    'vqd': vqd,
                    'kl': 'us-en',
                    'l': 'us-en',
                    's': '0',
                    'df': '',
                    'ex': '-1'
                }
                
                search_response = session.get("https://links.duckduckgo.com/d.js", 
                                            params=params, timeout=15)
                
                if search_response.status_code == 200:
                    results = self._parse_duckduckgo_advanced(search_response.text, max_results)
                    if results:
                        print(f"  ✓ Found {len(results)} results from DuckDuckGo advanced")
                        return results
            else:
                # Fallback to HTML search
                return self._duckduckgo_html_fallback(query, max_results, session)
            
        except Exception as e:
            print(f"  ✗ DuckDuckGo advanced failed: {e}")
        
        return []
    
    def method_5_bing_advanced(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 5: Advanced Bing with cookie and session handling"""
        print("Method 5: Testing advanced Bing...")
        
        try:
            session = self.get_session('bing')
            
            # Get Bing homepage first to set cookies
            session.get("https://www.bing.com/", timeout=15)
            time.sleep(1)
            
            # Perform search with advanced parameters
            params = {
                'q': query,
                'count': max_results,
                'first': 0,
                'FORM': 'QBRE',
                'sp': '-1',
                'lq': '0',
                'pq': query[:10],  # Partial query
                'sc': '8-' + str(len(query)),
                'qs': 'n',
                'sk': '',
                'cvid': self._generate_cvid()
            }
            
            response = session.get("https://www.bing.com/search", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_bing_advanced(response.text, max_results)
                if results:
                    print(f"  ✓ Found {len(results)} results from Bing advanced")
                    return results
            
        except Exception as e:
            print(f"  ✗ Bing advanced failed: {e}")
        
        return []
    
    def method_6_yandex(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 6: Yandex search (Russian search engine, often less restricted)"""
        print("Method 6: Testing Yandex search...")
        
        try:
            session = self.get_session('yandex')
            
            params = {
                'text': query,
                'lr': '84',  # English region
                'lang': 'en'
            }
            
            response = session.get("https://yandex.com/search/", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_yandex_results(response.text, max_results)
                if results:
                    print(f"  ✓ Found {len(results)} results from Yandex")
                    return results
            
        except Exception as e:
            print(f"  ✗ Yandex failed: {e}")
        
        return []
    
    def method_7_brave_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Method 7: Brave Search (privacy-focused, often less restricted)"""
        print("Method 7: Testing Brave Search...")
        
        try:
            session = self.get_session('brave')
            
            params = {
                'q': query,
                'source': 'web'
            }
            
            response = session.get("https://search.brave.com/search", params=params, timeout=15)
            
            if response.status_code == 200:
                results = self._parse_brave_results(response.text, max_results)
                if results:
                    print(f"  ✓ Found {len(results)} results from Brave")
                    return results
            
        except Exception as e:
            print(f"  ✗ Brave Search failed: {e}")
        
        return []
    
    # Helper methods for parsing results
    def _parse_whoogle_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Whoogle search results"""
        results = []
        try:
            # Whoogle uses similar structure to Google
            title_pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(title_pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http') and 'whoogle' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Whoogle'
                    })
        except Exception as e:
            print(f"    Error parsing Whoogle results: {e}")
        
        return results
    
    def _parse_startpage_advanced(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Startpage advanced results"""
        results = []
        try:
            # More robust Startpage parsing
            patterns = [
                r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>',
                r'<a[^>]+class="[^"]*w-gl__result-title[^"]*"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for url, title in matches[:max_results]:
                    if url.startswith('http'):
                        results.append({
                            'title': self._clean_text(title),
                            'snippet': '',
                            'url': url,
                            'source': 'Startpage Advanced'
                        })
                if results:
                    break
                    
        except Exception as e:
            print(f"    Error parsing Startpage results: {e}")
        
        return results
    
    def _parse_duckduckgo_advanced(self, response_text: str, max_results: int) -> List[Dict[str, str]]:
        """Parse DuckDuckGo advanced results"""
        results = []
        try:
            if response_text.startswith('DDG.pageLayout.load.searchResults('):
                json_str = response_text[len('DDG.pageLayout.load.searchResults('):-2]
                data = json.loads(json_str)
                
                for item in data.get('results', [])[:max_results]:
                    if item.get('t') and item.get('u'):
                        results.append({
                            'title': self._clean_text(item.get('t', '')),
                            'snippet': self._clean_text(item.get('a', '')),
                            'url': item.get('u', ''),
                            'source': 'DuckDuckGo Advanced'
                        })
        except Exception as e:
            print(f"    Error parsing DuckDuckGo results: {e}")
        
        return results
    
    def _duckduckgo_html_fallback(self, query: str, max_results: int, session) -> List[Dict[str, str]]:
        """DuckDuckGo HTML fallback"""
        try:
            params = {'q': query, 'kl': 'us-en'}
            response = session.get("https://html.duckduckgo.com/html/", params=params, timeout=15)
            
            if response.status_code == 200:
                return self._parse_duckduckgo_html(response.text, max_results)
        except Exception as e:
            print(f"    DuckDuckGo HTML fallback failed: {e}")
        
        return []
    
    def _parse_duckduckgo_html(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse DuckDuckGo HTML results"""
        results = []
        try:
            pattern = r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http'):
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'DuckDuckGo HTML'
                    })
        except Exception as e:
            print(f"    Error parsing DuckDuckGo HTML: {e}")
        
        return results
    
    def _parse_bing_advanced(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Bing advanced results"""
        results = []
        try:
            pattern = r'<h2><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h2>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http') and 'bing.com' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Bing Advanced'
                    })
        except Exception as e:
            print(f"    Error parsing Bing results: {e}")
        
        return results
    
    def _parse_yandex_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Yandex results"""
        results = []
        try:
            pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http') and 'yandex' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Yandex'
                    })
        except Exception as e:
            print(f"    Error parsing Yandex results: {e}")
        
        return results
    
    def _parse_brave_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Brave Search results"""
        results = []
        try:
            pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http') and 'brave.com' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Brave Search'
                    })
        except Exception as e:
            print(f"    Error parsing Brave results: {e}")
        
        return results
    
    def _generate_cvid(self) -> str:
        """Generate a CVID for Bing"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
    
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
    
    def search_all_methods(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Try all methods until one works"""
        methods = [
            self.method_1_searx_instances,
            self.method_2_whoogle_instances,
            self.method_3_startpage_advanced,
            self.method_4_duckduckgo_advanced,
            self.method_5_bing_advanced,
            self.method_6_yandex,
            self.method_7_brave_search
        ]
        
        all_results = []
        for method in methods:
            try:
                results = method(query, max_results)
                if results:
                    all_results.extend(results)
                    if len(all_results) >= max_results:
                        break
                time.sleep(1)  # Be respectful
            except Exception as e:
                print(f"  Method failed: {e}")
                continue
        
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
                if len(unique_results) >= max_results:
                    break
        
        return unique_results
    
    def close(self):
        """Close all sessions"""
        for session in self.sessions.values():
            session.close()

def test_advanced_methods():
    """Test all advanced search methods"""
    print("=" * 60)
    print("ADVANCED WEB SEARCH METHODS TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    searcher = AdvancedWebSearcher()
    
    test_queries = [
        "python programming tutorial",
        "machine learning basics"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 50)
        
        results = searcher.search_all_methods(query, max_results=5)
        
        if results:
            print(f"\n✓ Total results found: {len(results)}")
            print(f"Sources used:")
            sources = {}
            for result in results:
                source = result['source']
                sources[source] = sources.get(source, 0) + 1
            
            for source, count in sources.items():
                print(f"  - {source}: {count} results")
            
            print(f"\nResults:")
            print("-" * 30)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title'][:60]}...")
                print(f"   Source: {result['source']}")
                print(f"   URL: {result['url'][:70]}...")
                if result['snippet']:
                    print(f"   Snippet: {result['snippet'][:80]}...")
                print()
        else:
            print("❌ No results found with any method")
    
    searcher.close()
    
    if results:
        print("\n🎉 Advanced search methods are working!")
        print("\nRecommendations:")
        print("1. SearX instances are often the most reliable")
        print("2. Whoogle provides good Google results without tracking")
        print("3. Yandex and Brave are good fallbacks")
        print("4. Use method rotation to avoid rate limits")
        return True
    else:
        print("\n❌ All advanced methods failed!")
        return False

def main():
    """Main function"""
    success = test_advanced_methods()
    
    if success:
        print("\n✅ Advanced search methods work!")
        print("\nNext steps:")
        print("1. Integrate the working methods into your main search system")
        print("2. Use these as fallbacks when Playwright fails")
        print("3. Consider rotating methods to avoid detection")
    else:
        print("\n❌ Advanced methods failed!")
        print("\nFallback recommendations:")
        print("1. Use Playwright as primary method")
        print("2. Set up your own Searx instance")
        print("3. Consider using VPN/proxy rotation")
    
    return success

if __name__ == "__main__":
    main()