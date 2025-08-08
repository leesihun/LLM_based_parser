#!/usr/bin/env python3
"""
Tavily Search API Testing Tool
Tests Tavily search API with the provided API key
"""

import requests
import json
import time
import sys
from typing import List, Dict, Optional, Any

class TavilyTester:
    """Test Tavily Search API"""
    
    def __init__(self, api_key: str, proxy_config: Optional[Dict[str, str]] = None):
        """Initialize with Tavily API key and optional proxy configuration"""
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
        self.session = requests.Session()
        
        # Configure proxy if provided
        if proxy_config:
            print(f"🌐 Configuring proxy: {proxy_config}")
            self.session.proxies.update(proxy_config)
            
        # Configure session with retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json'
        })
        self.timeout = 60  # Increased timeout for proxy environments
        self.test_queries = [
            "Python programming tutorial",
            "artificial intelligence latest news",
            "web scraping best practices",
            "machine learning frameworks comparison",
            "API testing tools"
        ]
    
    def test_basic_search(self, query: str = None) -> Dict[str, Any]:
        """Test basic Tavily search functionality"""
        test_query = query or self.test_queries[0]
        
        try:
            url = f"{self.base_url}/search"
            payload = {
                "api_key": self.api_key,
                "query": test_query,
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": 5
            }
            
            print(f"Testing basic search with query: '{test_query}'")
            print(f"API URL: {url}")
            print(f"Payload: {json.dumps({k: v for k, v in payload.items() if k != 'api_key'}, indent=2)}")
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Data Keys: {list(data.keys())}")
                
                results = []
                for result in data.get('results', []):
                    results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('content', '')[:200] + '...' if result.get('content') else '',
                        'url': result.get('url', ''),
                        'score': result.get('score', 0),
                        'published_date': result.get('published_date', '')
                    })
                
                return {
                    'success': True,
                    'results': results,
                    'answer': data.get('answer', ''),
                    'query': data.get('query', test_query),
                    'response_time': data.get('response_time', 0),
                    'total_results': len(results),
                    'message': f'Tavily basic search successful - {len(results)} results'
                }
            else:
                error_text = response.text
                print(f"Error Response: {error_text}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {error_text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def test_advanced_search(self, query: str = None) -> Dict[str, Any]:
        """Test advanced Tavily search with more parameters"""
        test_query = query or self.test_queries[1]
        
        try:
            url = f"{self.base_url}/search"
            payload = {
                "api_key": self.api_key,
                "query": test_query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_raw_content": True,
                "max_results": 10,
                "include_domains": [],
                "exclude_domains": ["reddit.com", "twitter.com"]
            }
            
            print(f"Testing advanced search with query: '{test_query}'")
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                results = []
                for result in data.get('results', []):
                    results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('content', '')[:300] + '...' if result.get('content') else '',
                        'url': result.get('url', ''),
                        'score': result.get('score', 0),
                        'published_date': result.get('published_date', ''),
                        'raw_content': len(result.get('raw_content', '')) if result.get('raw_content') else 0
                    })
                
                return {
                    'success': True,
                    'results': results,
                    'answer': data.get('answer', ''),
                    'query': data.get('query', test_query),
                    'response_time': data.get('response_time', 0),
                    'total_results': len(results),
                    'message': f'Tavily advanced search successful - {len(results)} results'
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_news_search(self, query: str = None) -> Dict[str, Any]:
        """Test Tavily news search"""
        test_query = query or "latest technology news"
        
        try:
            url = f"{self.base_url}/search"
            payload = {
                "api_key": self.api_key,
                "query": test_query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 8,
                "include_domains": ["news.google.com", "reuters.com", "bbc.com", "cnn.com", "techcrunch.com"],
                "days": 7  # Last 7 days
            }
            
            print(f"Testing news search with query: '{test_query}'")
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                results = []
                for result in data.get('results', []):
                    results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('content', '')[:200] + '...' if result.get('content') else '',
                        'url': result.get('url', ''),
                        'score': result.get('score', 0),
                        'published_date': result.get('published_date', ''),
                        'domain': result.get('url', '').split('/')[2] if result.get('url') else ''
                    })
                
                return {
                    'success': True,
                    'results': results,
                    'answer': data.get('answer', ''),
                    'query': data.get('query', test_query),
                    'response_time': data.get('response_time', 0),
                    'total_results': len(results),
                    'message': f'Tavily news search successful - {len(results)} results'
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_multiple_queries(self) -> Dict[str, Any]:
        """Test multiple queries to assess consistency"""
        results = {}
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n--- Testing Query {i}/{len(self.test_queries)} ---")
            result = self.test_basic_search(query)
            results[f"query_{i}"] = {
                'query': query,
                'success': result.get('success', False),
                'results_count': len(result.get('results', [])),
                'has_answer': bool(result.get('answer', '')),
                'error': result.get('error', None)
            }
            
            if result.get('success'):
                print(f"✅ Success: {result['total_results']} results")
                if result.get('answer'):
                    print(f"📝 Answer: {result['answer'][:100]}...")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(2)  # Rate limiting
        
        successful_queries = sum(1 for r in results.values() if r['success'])
        
        return {
            'success': successful_queries > 0,
            'total_queries': len(self.test_queries),
            'successful_queries': successful_queries,
            'success_rate': successful_queries / len(self.test_queries) * 100,
            'results': results,
            'message': f'Tested {len(self.test_queries)} queries, {successful_queries} successful ({successful_queries/len(self.test_queries)*100:.1f}%)'
        }
    
    def test_api_limits(self) -> Dict[str, Any]:
        """Test API rate limits and quotas"""
        try:
            # Make rapid requests to test rate limiting
            rapid_results = []
            for i in range(5):
                result = self.test_basic_search(f"test query {i}")
                rapid_results.append({
                    'request': i + 1,
                    'success': result.get('success', False),
                    'error': result.get('error', None),
                    'status_code': result.get('status_code', None)
                })
                time.sleep(0.5)  # Small delay
            
            successful_rapid = sum(1 for r in rapid_results if r['success'])
            
            return {
                'success': True,
                'rapid_requests': rapid_results,
                'successful_rapid_requests': successful_rapid,
                'rate_limit_issues': any(r.get('status_code') == 429 for r in rapid_results),
                'message': f'Rate limit test: {successful_rapid}/5 requests successful'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all Tavily tests"""
        print("=" * 80)
        print("COMPREHENSIVE TAVILY API TESTING")
        print("=" * 80)
        print(f"API Key: {self.api_key[:10]}...{self.api_key[-4:]}")
        print(f"Base URL: {self.base_url}")
        print()
        
        test_results = {}
        
        # Test 1: Basic Search
        print("🔍 Test 1: Basic Search")
        print("-" * 40)
        basic_result = self.test_basic_search()
        test_results['basic_search'] = basic_result
        
        if basic_result.get('success'):
            print(f"✅ SUCCESS: {basic_result['message']}")
            print(f"   Answer: {basic_result.get('answer', 'No answer provided')[:100]}...")
            print(f"   Results: {basic_result['total_results']}")
            for i, result in enumerate(basic_result['results'][:2], 1):
                print(f"   {i}. {result['title'][:60]}...")
                print(f"      URL: {result['url']}")
                print(f"      Score: {result['score']}")
        else:
            print(f"❌ FAILED: {basic_result.get('error', 'Unknown error')}")
        
        print()
        time.sleep(3)
        
        # Test 2: Advanced Search
        print("🔍 Test 2: Advanced Search")
        print("-" * 40)
        advanced_result = self.test_advanced_search()
        test_results['advanced_search'] = advanced_result
        
        if advanced_result.get('success'):
            print(f"✅ SUCCESS: {advanced_result['message']}")
            print(f"   Answer: {advanced_result.get('answer', 'No answer provided')[:100]}...")
            print(f"   Results: {advanced_result['total_results']}")
        else:
            print(f"❌ FAILED: {advanced_result.get('error', 'Unknown error')}")
        
        print()
        time.sleep(3)
        
        # Test 3: News Search
        print("🔍 Test 3: News Search")
        print("-" * 40)
        news_result = self.test_news_search()
        test_results['news_search'] = news_result
        
        if news_result.get('success'):
            print(f"✅ SUCCESS: {news_result['message']}")
            print(f"   Answer: {news_result.get('answer', 'No answer provided')[:100]}...")
            print(f"   Results: {news_result['total_results']}")
        else:
            print(f"❌ FAILED: {news_result.get('error', 'Unknown error')}")
        
        print()
        time.sleep(3)
        
        # Test 4: Multiple Queries
        print("🔍 Test 4: Multiple Query Consistency")
        print("-" * 40)
        multi_result = self.test_multiple_queries()
        test_results['multiple_queries'] = multi_result
        
        if multi_result.get('success'):
            print(f"✅ SUCCESS: {multi_result['message']}")
            print(f"   Success Rate: {multi_result['success_rate']:.1f}%")
        else:
            print(f"❌ FAILED: Multiple query test failed")
        
        print()
        time.sleep(3)
        
        # Test 5: Rate Limits
        print("🔍 Test 5: Rate Limit Testing")
        print("-" * 40)
        limit_result = self.test_api_limits()
        test_results['rate_limits'] = limit_result
        
        if limit_result.get('success'):
            print(f"✅ SUCCESS: {limit_result['message']}")
            if limit_result.get('rate_limit_issues'):
                print("   ⚠️  Rate limiting detected")
            else:
                print("   ✅ No rate limit issues")
        else:
            print(f"❌ FAILED: {limit_result.get('error', 'Unknown error')}")
        
        # Summary
        print()
        print("=" * 80)
        print("TAVILY API TEST SUMMARY")
        print("=" * 80)
        
        successful_tests = sum(1 for result in test_results.values() if result.get('success'))
        total_tests = len(test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Success Rate: {successful_tests/total_tests*100:.1f}%")
        print()
        
        if successful_tests > 0:
            print("✅ TAVILY API IS WORKING!")
            print()
            print("RECOMMENDATIONS:")
            print("- Tavily API can be integrated into your search system")
            print("- Consider using it as a primary or fallback search provider")
            print("- The API provides both search results and direct answers")
            print("- Rate limiting appears to be reasonable for normal usage")
        else:
            print("❌ TAVILY API ISSUES DETECTED")
            print()
            print("TROUBLESHOOTING:")
            print("- Check if the API key is valid and active")
            print("- Verify network connectivity")
            print("- Check if you have exceeded your quota")
            print("- Review the error messages above for specific issues")
        
        return {
            'success': successful_tests > 0,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': successful_tests/total_tests*100,
            'test_results': test_results,
            'overall_status': 'WORKING' if successful_tests > 0 else 'FAILED'
        }

def detect_proxy_settings():
    """Detect proxy settings from environment variables"""
    import os
    
    proxy_config = {}
    
    # Check common proxy environment variables
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy:
        proxy_config['http'] = http_proxy
    if https_proxy:
        proxy_config['https'] = https_proxy
        
    return proxy_config if proxy_config else None

def get_manual_proxy_config():
    """Get manual proxy configuration from user"""
    print("\n🌐 PROXY CONFIGURATION")
    print("=" * 40)
    print("Enter your company's proxy settings:")
    print("(Leave blank if you don't know or want to skip)")
    print()
    
    proxy_host = input("Proxy Host (e.g., proxy.company.com): ").strip()
    if not proxy_host:
        return None
        
    proxy_port = input("Proxy Port (e.g., 8080): ").strip()
    if not proxy_port:
        proxy_port = "8080"
    
    username = input("Username (optional): ").strip()
    password = input("Password (optional): ").strip()
    
    # Build proxy URL
    if username and password:
        proxy_url = f"http://{username}:{password}@{proxy_host}:{proxy_port}"
    else:
        proxy_url = f"http://{proxy_host}:{proxy_port}"
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }

def main():
    """Main function"""
    # Use the provided API key
    api_key = "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"
    
    if not api_key:
        print("❌ Error: No API key provided")
        print("Usage: python test_tavily.py")
        print("Make sure to set the API key in the script")
        sys.exit(1)
    
    print("🔍 TAVILY API TESTER")
    print("=" * 40)
    print("Detecting proxy configuration...")
    
    # Try to detect proxy settings
    proxy_config = detect_proxy_settings()
    
    if proxy_config:
        print(f"✅ Auto-detected proxy: {proxy_config}")
        use_detected = input("Use detected proxy? (y/n): ").strip().lower()
        if use_detected != 'y':
            proxy_config = None
    
    if not proxy_config:
        print("❌ No proxy auto-detected")
        manual_setup = input("Configure proxy manually? (y/n): ").strip().lower()
        if manual_setup == 'y':
            proxy_config = get_manual_proxy_config()
    
    if not proxy_config:
        print("⚠️  No proxy configured - trying direct connection...")
        print("If you get connection errors, restart and configure proxy settings.")
        print()
    
    tester = TavilyTester(api_key, proxy_config)
    
    try:
        results = tester.run_comprehensive_test()
        
        # Save results to file
        with open('tavily_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: tavily_test_results.json")
        
        return 0 if results['success'] else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
