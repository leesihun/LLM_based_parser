#!/usr/bin/env python3
"""
Network Connectivity Diagnostic Tool
Diagnoses network issues preventing web search from working
"""

import requests
import time
import socket
from datetime import datetime
from urllib.parse import urlparse
import subprocess
import platform
import json

class NetworkDiagnostics:
    """Comprehensive network diagnostics for web search issues"""
    
    def __init__(self, proxy_host="168.219.61.252", proxy_port=8080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_config = {
            'http': f'http://{proxy_host}:{proxy_port}',
            'https': f'http://{proxy_host}:{proxy_port}'
        }
        
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        self.test_urls = [
            'https://www.google.com',
            'https://duckduckgo.com',
            'https://www.bing.com',
            'https://search.yahoo.com',
            'https://www.startpage.com',
            'https://searx.be',
            'https://httpbin.org/ip',  # Shows your IP
            'https://httpbin.org/headers'  # Shows headers
        ]
    
    def test_basic_connectivity(self):
        """Test basic internet connectivity"""
        print("=" * 60)
        print("BASIC CONNECTIVITY TEST")
        print("=" * 60)
        
        # Test DNS resolution
        print("1. DNS Resolution Test:")
        test_domains = ['google.com', 'duckduckgo.com', 'bing.com']
        
        for domain in test_domains:
            try:
                ip = socket.gethostbyname(domain)
                print(f"   ✓ {domain} → {ip}")
            except Exception as e:
                print(f"   ✗ {domain} → DNS Error: {e}")
        
        # Test ping (basic reachability)
        print("\n2. Ping Test:")
        ping_hosts = ['8.8.8.8', 'google.com', 'duckduckgo.com']
        
        for host in ping_hosts:
            try:
                if platform.system().lower() == 'windows':
                    result = subprocess.run(['ping', '-n', '1', host], 
                                          capture_output=True, text=True, timeout=10)
                else:
                    result = subprocess.run(['ping', '-c', '1', host], 
                                          capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"   ✓ {host} - Reachable")
                else:
                    print(f"   ✗ {host} - Unreachable")
                    
            except Exception as e:
                print(f"   ✗ {host} - Ping failed: {e}")
        
        print()
    
    def test_proxy_connectivity(self):
        """Test proxy server connectivity"""
        print("=" * 60)
        print("PROXY CONNECTIVITY TEST")
        print("=" * 60)
        print(f"Testing proxy: {self.proxy_host}:{self.proxy_port}")
        print()
        
        # Test proxy server reachability
        print("1. Proxy Server Reachability:")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.proxy_host, self.proxy_port))
            sock.close()
            
            if result == 0:
                print(f"   ✓ Proxy server {self.proxy_host}:{self.proxy_port} is reachable")
            else:
                print(f"   ✗ Proxy server {self.proxy_host}:{self.proxy_port} is NOT reachable")
                print(f"   Error code: {result}")
                return False
                
        except Exception as e:
            print(f"   ✗ Cannot connect to proxy: {e}")
            return False
        
        # Test HTTP requests through proxy
        print("\n2. HTTP Requests Through Proxy:")
        session = requests.Session()
        session.proxies.update(self.proxy_config)
        session.headers.update({'User-Agent': self.user_agent})
        
        test_sites = [
            ('httpbin.org/ip', 'IP check'),
            ('google.com', 'Google homepage'),
            ('duckduckgo.com', 'DuckDuckGo homepage')
        ]
        
        for url, description in test_sites:
            try:
                full_url = f'https://{url}' if not url.startswith('http') else url
                response = session.get(full_url, timeout=15)
                
                if response.status_code == 200:
                    print(f"   ✓ {description}: HTTP {response.status_code} - Success")
                    
                    # Special handling for IP check
                    if 'httpbin.org/ip' in url:
                        try:
                            ip_data = response.json()
                            print(f"     Your IP via proxy: {ip_data.get('origin', 'Unknown')}")
                        except:
                            pass
                else:
                    print(f"   ⚠ {description}: HTTP {response.status_code}")
                    
            except requests.exceptions.ProxyError as e:
                print(f"   ✗ {description}: Proxy Error - {e}")
                return False
            except requests.exceptions.ConnectTimeout as e:
                print(f"   ✗ {description}: Timeout - {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"   ✗ {description}: Connection Error - {e}")
            except Exception as e:
                print(f"   ✗ {description}: Error - {e}")
        
        session.close()
        return True
    
    def test_direct_connectivity(self):
        """Test direct connectivity (without proxy)"""
        print("=" * 60)
        print("DIRECT CONNECTIVITY TEST (NO PROXY)")
        print("=" * 60)
        
        session = requests.Session()
        session.headers.update({'User-Agent': self.user_agent})
        
        for url in self.test_urls[:5]:  # Test first 5 URLs
            try:
                print(f"Testing {url}...")
                response = session.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"   ✓ {url}: HTTP {response.status_code} - Success")
                else:
                    print(f"   ⚠ {url}: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectTimeout:
                print(f"   ✗ {url}: Timeout")
            except requests.exceptions.ConnectionError as e:
                print(f"   ✗ {url}: Connection Error - {e}")
            except Exception as e:
                print(f"   ✗ {url}: Error - {e}")
        
        session.close()
    
    def test_search_engines_detailed(self):
        """Test search engines with detailed analysis"""
        print("=" * 60)
        print("DETAILED SEARCH ENGINE TEST")
        print("=" * 60)
        
        search_tests = [
            {
                'name': 'DuckDuckGo HTML',
                'url': 'https://html.duckduckgo.com/html/',
                'params': {'q': 'test search'},
                'success_indicators': ['result', 'search', 'web']
            },
            {
                'name': 'Bing Search',
                'url': 'https://www.bing.com/search',
                'params': {'q': 'test search'},
                'success_indicators': ['results', 'search', 'web']
            },
            {
                'name': 'Startpage',
                'url': 'https://www.startpage.com/sp/search',
                'params': {'query': 'test search'},
                'success_indicators': ['result', 'search']
            },
            {
                'name': 'SearX Instance',
                'url': 'https://searx.be/search',
                'params': {'q': 'test search', 'format': 'json'},
                'success_indicators': ['results', 'query']
            }
        ]
        
        # Test with proxy
        print("1. Testing with proxy:")
        session_proxy = requests.Session()
        session_proxy.proxies.update(self.proxy_config)
        session_proxy.headers.update({'User-Agent': self.user_agent})
        
        for test in search_tests:
            try:
                print(f"   Testing {test['name']}...")
                response = session_proxy.get(test['url'], params=test['params'], timeout=20)
                
                if response.status_code == 200:
                    content = response.text.lower()
                    indicators_found = [ind for ind in test['success_indicators'] if ind in content]
                    
                    if indicators_found:
                        print(f"      ✓ Success - Found indicators: {indicators_found}")
                    else:
                        print(f"      ⚠ HTTP 200 but no search indicators found")
                        print(f"      Content preview: {content[:100]}...")
                else:
                    print(f"      ✗ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"      ✗ Error: {e}")
        
        session_proxy.close()
        
        # Test without proxy
        print("\n2. Testing without proxy:")
        session_direct = requests.Session()
        session_direct.headers.update({'User-Agent': self.user_agent})
        
        for test in search_tests:
            try:
                print(f"   Testing {test['name']}...")
                response = session_direct.get(test['url'], params=test['params'], timeout=20)
                
                if response.status_code == 200:
                    content = response.text.lower()
                    indicators_found = [ind for ind in test['success_indicators'] if ind in content]
                    
                    if indicators_found:
                        print(f"      ✓ Success - Found indicators: {indicators_found}")
                    else:
                        print(f"      ⚠ HTTP 200 but no search indicators found")
                else:
                    print(f"      ✗ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"      ✗ Error: {e}")
        
        session_direct.close()
    
    def test_current_browser_search(self):
        """Test the current browser search implementation"""
        print("=" * 60)
        print("CURRENT BROWSER SEARCH TEST")
        print("=" * 60)
        
        try:
            # Import and test current implementation
            from src.browser_search import BrowserSearcher
            
            print("Testing current BrowserSearcher implementation...")
            searcher = BrowserSearcher()
            
            # Test with simple query
            test_query = "python"
            print(f"Query: '{test_query}'")
            
            results = searcher.search(test_query, max_results=3)
            
            if results:
                print(f"✓ Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['title'][:50]}...")
                    print(f"      Source: {result['source']}")
                    print(f"      URL: {result['url'][:60]}...")
            else:
                print("✗ No results returned")
            
            # Test capability check
            print("\nTesting capability check...")
            capability = searcher.test_search_capability()
            
            if capability['success']:
                print(f"✓ Capability test passed")
                print(f"   Engines working: {capability.get('engines_working', [])}")
            else:
                print(f"✗ Capability test failed: {capability.get('error', 'Unknown error')}")
            
            searcher.close()
            
        except ImportError:
            print("✗ Cannot import BrowserSearcher - module not found")
        except Exception as e:
            print(f"✗ Error testing BrowserSearcher: {e}")
    
    def get_network_info(self):
        """Get detailed network information"""
        print("=" * 60)
        print("NETWORK CONFIGURATION INFO")
        print("=" * 60)
        
        try:
            # Get IP without proxy
            session_direct = requests.Session()
            response = session_direct.get('https://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                ip_info = response.json()
                print(f"Direct IP: {ip_info.get('origin', 'Unknown')}")
            session_direct.close()
        except:
            print("Direct IP: Could not determine")
        
        try:
            # Get IP with proxy
            session_proxy = requests.Session()
            session_proxy.proxies.update(self.proxy_config)
            response = session_proxy.get('https://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                ip_info = response.json()
                print(f"Proxy IP: {ip_info.get('origin', 'Unknown')}")
            session_proxy.close()
        except:
            print("Proxy IP: Could not determine")
        
        # System info
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python version: {platform.python_version()}")
        
        # Check if behind corporate firewall indicators
        print("\n🔍 Checking for corporate firewall indicators...")
        
        corporate_indicators = [
            ('Proxy required for internet access', True),  # You're using proxy
            ('Specific proxy server', self.proxy_host not in ['localhost', '127.0.0.1']),
            ('Enterprise network', True if ':8080' in f"{self.proxy_host}:{self.proxy_port}" else False)
        ]
        
        for indicator, detected in corporate_indicators:
            status = "🟡 Detected" if detected else "🟢 Not detected"
            print(f"   {status}: {indicator}")
    
    def run_full_diagnostics(self):
        """Run complete diagnostics suite"""
        print("🔧 NETWORK CONNECTIVITY DIAGNOSTICS")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Proxy: {self.proxy_host}:{self.proxy_port}")
        print()
        
        # Run all tests
        self.test_basic_connectivity()
        time.sleep(2)
        
        self.get_network_info()
        time.sleep(2)
        
        proxy_works = self.test_proxy_connectivity()
        time.sleep(2)
        
        self.test_direct_connectivity()
        time.sleep(2)
        
        self.test_search_engines_detailed()
        time.sleep(2)
        
        self.test_current_browser_search()
        
        # Summary and recommendations
        print("\n" + "=" * 70)
        print("DIAGNOSTIC SUMMARY & RECOMMENDATIONS")
        print("=" * 70)
        
        if not proxy_works:
            print("🚨 PROXY ISSUES DETECTED")
            print("Recommendations:")
            print("1. Verify proxy server is running and accessible")
            print("2. Check proxy authentication if required")
            print("3. Try without proxy to test direct connectivity")
            print("4. Contact network administrator")
        else:
            print("🔍 SEARCH ENGINE RESTRICTIONS DETECTED")
            print("Likely causes:")
            print("- Corporate firewall blocking search engines")
            print("- Content filtering policies")
            print("- Anti-bot measures by search engines")
            print("- Rate limiting")
            print()
            print("💡 SOLUTIONS TO TRY:")
            print("1. Use different search engines (Yandex, Brave)")
            print("2. Implement request delays and rotation")
            print("3. Use SearX instances (meta-search)")
            print("4. Try Playwright with stealth mode")
            print("5. Use different user agents")
            print("6. Consider VPN or different proxy")
        
        return proxy_works

def main():
    """Main diagnostic function"""
    print("Network Connectivity Diagnostics for Web Search")
    print("This will help identify why web search methods are failing")
    print()
    
    # Initialize diagnostics
    diagnostics = NetworkDiagnostics()
    
    # Run full diagnostic suite
    proxy_works = diagnostics.run_full_diagnostics()
    
    print(f"\n🎯 NEXT STEPS:")
    if proxy_works:
        print("1. Try the alternative search methods script with delays")
        print("2. Implement user agent rotation")
        print("3. Use SearX instances as primary method")
        print("4. Consider Playwright with stealth plugins")
    else:
        print("1. Fix proxy connectivity issues first")
        print("2. Test with direct connection")
        print("3. Contact network administrator")
        print("4. Consider alternative network setup")
    
    print("\n✅ Diagnostics completed!")
    return proxy_works

if __name__ == "__main__":
    main()