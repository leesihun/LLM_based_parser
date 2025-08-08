#!/usr/bin/env python3
"""
Tavily API Test with Configuration File
Uses proxy_config.json for easy proxy configuration
"""

import requests
import json
import sys
import os

def load_config():
    """Load configuration from proxy_config.json"""
    config_file = "proxy_config.json"
    
    if not os.path.exists(config_file):
        print(f"❌ Configuration file {config_file} not found!")
        print("Creating default configuration file...")
        
        default_config = {
            "proxy_settings": {
                "enabled": False,
                "http": "",
                "https": "",
                "username": "",
                "password": ""
            },
            "tavily_settings": {
                "api_key": "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",
                "timeout": 60,
                "max_results": 5,
                "search_depth": "basic"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✅ Created {config_file}")
        print("Please edit the configuration file and run again.")
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return None

def setup_session(proxy_settings):
    """Set up requests session with proxy configuration"""
    session = requests.Session()
    
    # Set headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    # Configure proxy if enabled
    if proxy_settings.get('enabled', False):
        proxies = {}
        
        # Build proxy URLs
        username = proxy_settings.get('username', '')
        password = proxy_settings.get('password', '')
        http_proxy = proxy_settings.get('http', '')
        https_proxy = proxy_settings.get('https', '')
        
        if username and password:
            # Add authentication to proxy URLs if not already present
            if http_proxy and '@' not in http_proxy:
                http_proxy = http_proxy.replace('http://', f'http://{username}:{password}@')
            if https_proxy and '@' not in https_proxy:
                https_proxy = https_proxy.replace('http://', f'http://{username}:{password}@')
        
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        if proxies:
            session.proxies.update(proxies)
            print(f"🌐 Proxy configured: {list(proxies.keys())}")
            # Don't print full proxy URLs as they may contain passwords
            for protocol in proxies:
                proxy_url = proxies[protocol]
                if '@' in proxy_url:
                    # Hide credentials in output
                    parts = proxy_url.split('@')
                    masked_url = f"{parts[0].split('://')[0]}://***:***@{parts[1]}"
                    print(f"   {protocol.upper()}: {masked_url}")
                else:
                    print(f"   {protocol.upper()}: {proxy_url}")
        else:
            print("⚠️  Proxy enabled but no proxy URLs configured")
    else:
        print("🌐 Direct connection (no proxy)")
    
    return session

def test_tavily_api(session, tavily_settings):
    """Test Tavily API with configured session"""
    api_key = tavily_settings.get('api_key')
    if not api_key:
        print("❌ No API key configured!")
        return False
    
    base_url = "https://api.tavily.com/search"
    timeout = tavily_settings.get('timeout', 60)
    
    # Test queries
    test_queries = [
        "Python programming tutorial",
        "artificial intelligence news",
        "web scraping techniques"
    ]
    
    print(f"\n🔍 TESTING TAVILY API")
    print("=" * 40)
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Timeout: {timeout}s")
    print()
    
    successful_tests = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}/{len(test_queries)}: '{query}'")
        
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": tavily_settings.get('search_depth', 'basic'),
            "include_answer": True,
            "max_results": tavily_settings.get('max_results', 5)
        }
        
        try:
            response = session.post(base_url, json=payload, timeout=timeout)
            
            print(f"   Status: {response.status_code}")
            print(f"   Time: {response.elapsed.total_seconds():.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                answer = data.get('answer', '')
                
                print(f"   ✅ Success: {len(results)} results")
                if answer:
                    print(f"   📝 Answer: {answer[:100]}...")
                
                # Show first result
                if results:
                    first_result = results[0]
                    print(f"   🔗 Top result: {first_result.get('title', 'No title')[:60]}...")
                
                successful_tests += 1
                
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                
        except requests.exceptions.ProxyError as e:
            print(f"   ❌ Proxy Error: {str(e)[:100]}...")
            
        except requests.exceptions.Timeout as e:
            print(f"   ❌ Timeout: {str(e)[:100]}...")
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection Error: {str(e)[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}...")
        
        print()
        
        # Don't hammer the API
        if i < len(test_queries):
            import time
            time.sleep(2)
    
    print(f"📊 RESULTS: {successful_tests}/{len(test_queries)} tests successful")
    
    if successful_tests > 0:
        print("🎉 Tavily API is working with your configuration!")
        return True
    else:
        print("💔 All tests failed. Check your network/proxy configuration.")
        return False

def test_basic_connectivity(session):
    """Test basic internet connectivity"""
    print("🌐 Testing basic connectivity...")
    
    test_urls = [
        ("HTTP Bin", "https://httpbin.org/get"),
        ("GitHub API", "https://api.github.com"),
        ("Google", "https://www.google.com")
    ]
    
    working_urls = 0
    
    for name, url in test_urls:
        try:
            response = session.get(url, timeout=10)
            print(f"   ✅ {name}: {response.status_code}")
            working_urls += 1
        except Exception as e:
            print(f"   ❌ {name}: {str(e)[:50]}...")
    
    print(f"   📊 {working_urls}/{len(test_urls)} connectivity tests passed")
    print()
    
    return working_urls > 0

def main():
    """Main function"""
    print("TAVILY API CONFIGURATION-BASED TESTER")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    if not config:
        return 1
    
    proxy_settings = config.get('proxy_settings', {})
    tavily_settings = config.get('tavily_settings', {})
    
    print(f"📁 Configuration loaded from proxy_config.json")
    print(f"🌐 Proxy enabled: {proxy_settings.get('enabled', False)}")
    print()
    
    # Set up session
    session = setup_session(proxy_settings)
    
    # Test basic connectivity first
    if not test_basic_connectivity(session):
        print("⚠️  Basic connectivity issues detected")
        print("This might affect Tavily API access")
        print()
    
    # Test Tavily API
    success = test_tavily_api(session, tavily_settings)
    
    if success:
        print("\n✅ SUCCESS: Tavily API is working!")
        print("You can now integrate Tavily into your search system.")
        
        # Save a simple integration example
        integration_example = {
            "proxy_config": proxy_settings if proxy_settings.get('enabled') else None,
            "tavily_config": tavily_settings,
            "integration_notes": [
                "Use the proxy configuration in your main application",
                "Tavily API key is working and valid",
                "Consider implementing fallback search providers",
                "Monitor API usage and rate limits"
            ]
        }
        
        with open('tavily_integration_config.json', 'w') as f:
            json.dump(integration_example, f, indent=2)
        
        print("💾 Integration config saved to tavily_integration_config.json")
        
    else:
        print("\n❌ FAILED: Tavily API test unsuccessful")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Check your proxy settings in proxy_config.json")
        print("2. Verify your company's proxy host and port")
        print("3. Confirm proxy username/password if required")
        print("4. Test with different proxy configurations")
        print("5. Contact your IT department for proxy details")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
