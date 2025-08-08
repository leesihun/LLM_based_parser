#!/usr/bin/env python3
"""
Comprehensive Free Web Search API Testing Tool
Tests all available free search APIs to find working options
"""

import requests
import json
import time
import sys
from urllib.parse import quote_plus, urlencode
import re
from typing import List, Dict, Optional, Any

class SearchAPITester:
    """Test multiple free search APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        self.timeout = 15
        self.test_query = "Python programming tutorial"
        
    def test_all_apis(self):
        """Test all available free search APIs"""
        
        print("=" * 80)
        print("COMPREHENSIVE FREE WEB SEARCH API TESTING")
        print("=" * 80)
        print(f"Test Query: '{self.test_query}'")
        print(f"Timeout: {self.timeout} seconds")
        print()
        
        # List of all free search APIs to test
        apis = [
            ("SerpAPI (Free Tier)", self.test_serpapi),
            ("ScaleSerp (Free Tier)", self.test_scaleserp),
            ("ValueSerp (Free Tier)", self.test_valueserp),
            ("SearchAPI (Free Tier)", self.test_searchapi),
            ("Zenserp (Free Tier)", self.test_zenserp),
            ("RapidAPI Google Search", self.test_rapidapi_google),
            ("RapidAPI Bing Search", self.test_rapidapi_bing),
            ("Contextual Web Search", self.test_contextual_web),
            ("WebSearchAPI", self.test_websearchapi),
            ("Google Custom Search", self.test_google_custom),
            ("Bing Web Search API", self.test_bing_api),
            ("DuckDuckGo Instant Answer", self.test_duckduckgo_instant),
            ("DuckDuckGo HTML", self.test_duckduckgo_html),
            ("Bing HTML Scraping", self.test_bing_html),
            ("Yahoo HTML Scraping", self.test_yahoo_html),
            ("Startpage HTML", self.test_startpage_html),
            ("Searx Public Instances", self.test_searx),
            ("Yandex Search API", self.test_yandex),
            ("Baidu Search (HTML)", self.test_baidu_html),
            ("Wikipedia API", self.test_wikipedia),
            ("Reddit Search API", self.test_reddit),
            ("GitHub Search API", self.test_github),
            ("Stack Overflow API", self.test_stackoverflow),
            ("News API", self.test_newsapi),
            ("JSONBin Search Proxy", self.test_jsonbin_proxy)
        ]
        
        working_apis = []
        failed_apis = []
        
        for name, test_func in apis:
            print(f"Testing: {name}")
            print("-" * 50)
            
            try:
                result = test_func()
                if result and result.get('success'):
                    print(f"✅ SUCCESS: {result.get('message', 'Working')}")
                    if result.get('results'):
                        print(f"   Results: {len(result['results'])} found")
                        for i, res in enumerate(result['results'][:2], 1):
                            print(f"   {i}. {res.get('title', 'No title')[:60]}...")
                    working_apis.append((name, result))
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No response'
                    print(f"❌ FAILED: {error_msg}")
                    failed_apis.append((name, error_msg))
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                failed_apis.append((name, str(e)))
            
            print()
            time.sleep(1)  # Rate limiting
        
        # Summary
        print("=" * 80)
        print("SUMMARY RESULTS")
        print("=" * 80)
        
        if working_apis:
            print(f"✅ WORKING APIs ({len(working_apis)}):")
            for name, result in working_apis:
                print(f"   • {name}")
                if result.get('api_key_required'):
                    print(f"     Note: Requires API key")
                if result.get('setup_instructions'):
                    print(f"     Setup: {result['setup_instructions']}")
        else:
            print("❌ No working APIs found")
        
        print()
        
        if failed_apis:
            print(f"❌ FAILED APIs ({len(failed_apis)}):")
            for name, error in failed_apis:
                print(f"   • {name}: {error}")
        
        print()
        print("RECOMMENDATIONS:")
        print("-" * 40)
        
        if working_apis:
            print("1. Use one of the working APIs above")
            print("2. Implement the top 2-3 working APIs as fallbacks")
            print("3. Check if any require API keys and get them if needed")
        else:
            print("1. Check your internet connection")
            print("2. Verify firewall/proxy settings")
            print("3. Try running from a different network")
            print("4. Consider using manual search fallback")
        
        return working_apis, failed_apis
    
    # API Testing Methods
    
    def test_serpapi(self):
        """Test SerpAPI (requires API key but has free tier)"""
        try:
            url = "https://serpapi.com/search"
            params = {
                'q': self.test_query,
                'api_key': 'demo',  # Demo key for testing
                'engine': 'google'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                for result in data.get('organic_results', [])[:3]:
                    results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': result.get('link', '')
                    })
                
                return {
                    'success': True,
                    'results': results,
                    'api_key_required': True,
                    'setup_instructions': 'Get free API key from serpapi.com'
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'No results'}
    
    def test_duckduckgo_instant(self):
        """Test DuckDuckGo Instant Answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': self.test_query,
                'format': 'json',
                'no_redirect': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                
                results = []
                # Check RelatedTopics
                for topic in data.get('RelatedTopics', [])[:3]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '')[:50] + '...',
                            'snippet': topic.get('Text', ''),
                            'url': topic.get('FirstURL', '')
                        })
                
                if results or data.get('Abstract'):
                    return {
                        'success': True,
                        'results': results,
                        'message': f'DuckDuckGo Instant Answer API working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'No instant answers found'}
    
    def test_duckduckgo_html(self):
        """Test DuckDuckGo HTML search"""
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {'q': self.test_query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                # Simple HTML parsing
                results = self._parse_duckduckgo_html(response.text)
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'DuckDuckGo HTML search working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'HTML parsing failed'}
    
    def test_bing_html(self):
        """Test Bing HTML scraping"""
        try:
            url = "https://www.bing.com/search"
            params = {'q': self.test_query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                results = self._parse_bing_html(response.text)
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'Bing HTML scraping working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Bing HTML parsing failed'}
    
    def test_yahoo_html(self):
        """Test Yahoo HTML scraping"""
        try:
            url = "https://search.yahoo.com/search"
            params = {'p': self.test_query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                results = self._parse_yahoo_html(response.text)
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'Yahoo HTML scraping working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Yahoo HTML parsing failed'}
    
    def test_startpage_html(self):
        """Test Startpage HTML scraping"""
        try:
            url = "https://www.startpage.com/sp/search"
            params = {'query': self.test_query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                results = self._parse_startpage_html(response.text)
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'Startpage HTML scraping working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Startpage HTML parsing failed'}
    
    def test_searx(self):
        """Test Searx public instances"""
        searx_instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.xyz",
            "https://searx.prvcy.eu"
        ]
        
        for instance in searx_instances:
            try:
                url = f"{instance}/search"
                params = {
                    'q': self.test_query,
                    'format': 'json'
                }
                
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for result in data.get('results', [])[:3]:
                        results.append({
                            'title': result.get('title', ''),
                            'snippet': result.get('content', ''),
                            'url': result.get('url', '')
                        })
                    
                    if results:
                        return {
                            'success': True,
                            'results': results,
                            'message': f'Searx instance {instance} working'
                        }
            except:
                continue
        
        return {'success': False, 'error': 'No Searx instances working'}
    
    def test_wikipedia(self):
        """Test Wikipedia API"""
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/search"
            params = {
                'q': self.test_query,
                'limit': 3
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                for page in data.get('pages', []):
                    results.append({
                        'title': page.get('title', ''),
                        'snippet': page.get('description', ''),
                        'url': f"https://en.wikipedia.org/wiki/{page.get('key', '')}"
                    })
                
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'Wikipedia API working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'No Wikipedia results'}
    
    def test_reddit(self):
        """Test Reddit Search API"""
        try:
            url = "https://www.reddit.com/search.json"
            params = {
                'q': self.test_query,
                'limit': 3,
                'sort': 'relevance'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    results.append({
                        'title': post_data.get('title', ''),
                        'snippet': post_data.get('selftext', '')[:100] + '...',
                        'url': f"https://reddit.com{post_data.get('permalink', '')}"
                    })
                
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'Reddit API working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'No Reddit results'}
    
    def test_github(self):
        """Test GitHub Search API"""
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': self.test_query,
                'per_page': 3
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                for repo in data.get('items', []):
                    results.append({
                        'title': repo.get('full_name', ''),
                        'snippet': repo.get('description', ''),
                        'url': repo.get('html_url', '')
                    })
                
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'GitHub API working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'No GitHub results'}
    
    def test_stackoverflow(self):
        """Test Stack Overflow API"""
        try:
            url = "https://api.stackexchange.com/2.3/search"
            params = {
                'order': 'desc',
                'sort': 'relevance',
                'intitle': self.test_query,
                'site': 'stackoverflow'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                for question in data.get('items', [])[:3]:
                    results.append({
                        'title': question.get('title', ''),
                        'snippet': f"Score: {question.get('score', 0)}, Views: {question.get('view_count', 0)}",
                        'url': question.get('link', '')
                    })
                
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'message': 'Stack Overflow API working'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'No Stack Overflow results'}
    
    def test_newsapi(self):
        """Test NewsAPI (requires API key but has free tier)"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': self.test_query,
                'apiKey': 'demo',  # Demo key for testing
                'pageSize': 3
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                for article in data.get('articles', []):
                    results.append({
                        'title': article.get('title', ''),
                        'snippet': article.get('description', ''),
                        'url': article.get('url', '')
                    })
                
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'api_key_required': True,
                        'setup_instructions': 'Get free API key from newsapi.org'
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'NewsAPI demo failed'}
    
    # Placeholder methods for other APIs (would need API keys)
    def test_scaleserp(self):
        return {'success': False, 'error': 'Requires API key from scaleserp.com'}
    
    def test_valueserp(self):
        return {'success': False, 'error': 'Requires API key from valueserp.com'}
    
    def test_searchapi(self):
        return {'success': False, 'error': 'Requires API key from searchapi.io'}
    
    def test_zenserp(self):
        return {'success': False, 'error': 'Requires API key from zenserp.com'}
    
    def test_rapidapi_google(self):
        return {'success': False, 'error': 'Requires RapidAPI key'}
    
    def test_rapidapi_bing(self):
        return {'success': False, 'error': 'Requires RapidAPI key'}
    
    def test_contextual_web(self):
        return {'success': False, 'error': 'Requires API key'}
    
    def test_websearchapi(self):
        return {'success': False, 'error': 'Requires API key'}
    
    def test_google_custom(self):
        return {'success': False, 'error': 'Requires Google API key and search engine ID'}
    
    def test_bing_api(self):
        return {'success': False, 'error': 'Requires Bing Search API key'}
    
    def test_yandex(self):
        return {'success': False, 'error': 'Requires Yandex API key'}
    
    def test_baidu_html(self):
        return {'success': False, 'error': 'Baidu may block non-Chinese IPs'}
    
    def test_jsonbin_proxy(self):
        return {'success': False, 'error': 'Custom proxy implementation needed'}
    
    # HTML Parsing Methods
    
    def _parse_duckduckgo_html(self, html):
        results = []
        try:
            # Simple regex for DuckDuckGo results
            pattern = r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:3]:
                if url.startswith('http'):
                    results.append({
                        'title': title.strip(),
                        'snippet': '',
                        'url': url
                    })
        except:
            pass
        return results
    
    def _parse_bing_html(self, html):
        results = []
        try:
            # Simple regex for Bing results
            pattern = r'<h2><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h2>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:3]:
                if url.startswith('http') and 'bing.com' not in url:
                    results.append({
                        'title': title.strip(),
                        'snippet': '',
                        'url': url
                    })
        except:
            pass
        return results
    
    def _parse_yahoo_html(self, html):
        results = []
        try:
            # Simple regex for Yahoo results
            pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:3]:
                if url.startswith('http') and 'yahoo.com' not in url:
                    results.append({
                        'title': title.strip(),
                        'snippet': '',
                        'url': url
                    })
        except:
            pass
        return results
    
    def _parse_startpage_html(self, html):
        results = []
        try:
            # Simple regex for Startpage results
            pattern = r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*w-gl-title[^"]*"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:3]:
                if url.startswith('http'):
                    results.append({
                        'title': title.strip(),
                        'snippet': '',
                        'url': url
                    })
        except:
            pass
        return results
    
    def close(self):
        """Close the session"""
        self.session.close()

def main():
    """Main function"""
    tester = SearchAPITester()
    try:
        working_apis, failed_apis = tester.test_all_apis()
        
        # Generate implementation suggestions
        if working_apis:
            print("\nIMPLEMENTATION SUGGESTIONS:")
            print("=" * 50)
            print("Based on working APIs, here are implementation options:\n")
            
            for name, result in working_apis[:3]:  # Top 3 working APIs
                print(f"Option {working_apis.index((name, result)) + 1}: {name}")
                if result.get('api_key_required'):
                    print(f"  • Requires API key: {result.get('setup_instructions', 'Check provider website')}")
                else:
                    print(f"  • No API key required")
                print(f"  • Results found: {len(result.get('results', []))}")
                print()
        
    finally:
        tester.close()

if __name__ == "__main__":
    main()
