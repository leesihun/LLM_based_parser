#!/usr/bin/env python3
"""
Simple Tavily API Test with Proxy Support
Quick test script for corporate proxy environments
"""

import requests
import json
import sys

def test_tavily_with_proxy():
    """Simple Tavily test with proxy configuration"""
    
    # API Configuration
    api_key = "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"
    base_url = "https://api.tavily.com/search"
    
    # Test query
    query = "Python programming tutorial"
    
    print("🔍 SIMPLE TAVILY API TEST")
    print("=" * 40)
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Query: {query}")
    print()
    
    # Proxy configuration options
    print("PROXY CONFIGURATION OPTIONS:")
    print("1. No proxy (direct connection)")
    print("2. HTTP proxy without authentication")
    print("3. HTTP proxy with authentication")
    print("4. Use system proxy settings")
    print()
    
    choice = input("Select option (1-4): ").strip()
    
    # Configure session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json'
    })
    
    # Set up proxy based on choice
    if choice == "2":
        proxy_host = input("Proxy host: ").strip()
        proxy_port = input("Proxy port (default 8080): ").strip() or "8080"
        proxy_url = f"http://{proxy_host}:{proxy_port}"
        session.proxies = {'http': proxy_url, 'https': proxy_url}
        print(f"✅ Using proxy: {proxy_url}")
        
    elif choice == "3":
        proxy_host = input("Proxy host: ").strip()
        proxy_port = input("Proxy port (default 8080): ").strip() or "8080"
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        proxy_url = f"http://{username}:{password}@{proxy_host}:{proxy_port}"
        session.proxies = {'http': proxy_url, 'https': proxy_url}
        print(f"✅ Using authenticated proxy: http://{username}:***@{proxy_host}:{proxy_port}")
        
    elif choice == "4":
        import os
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        if http_proxy or https_proxy:
            session.proxies = {}
            if http_proxy:
                session.proxies['http'] = http_proxy
            if https_proxy:
                session.proxies['https'] = https_proxy
            print(f"✅ Using system proxy: {session.proxies}")
        else:
            print("❌ No system proxy found")
            
    else:
        print("✅ Using direct connection (no proxy)")
    
    print()
    print("🚀 Testing connection...")
    
    # Prepare request
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 3
    }
    
    try:
        # Make request with longer timeout
        response = session.post(base_url, json=payload, timeout=60)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print()
            
            # Display answer
            if data.get('answer'):
                print(f"🤖 Answer: {data['answer']}")
                print()
            
            # Display results
            results = data.get('results', [])
            print(f"📄 Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.get('title', 'No title')}")
                print(f"   URL: {result.get('url', 'No URL')}")
                print(f"   Score: {result.get('score', 0)}")
                print()
            
            # Save results
            with open('tavily_simple_test_results.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("💾 Results saved to tavily_simple_test_results.json")
            
            return True
            
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ProxyError as e:
        print(f"❌ Proxy Error: {e}")
        print("💡 Check your proxy settings and credentials")
        return False
        
    except requests.exceptions.ConnectTimeout as e:
        print(f"❌ Connection Timeout: {e}")
        print("💡 Try increasing timeout or check network connection")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Check internet connection and proxy settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_connection_only():
    """Test basic internet connectivity"""
    print("🌐 Testing basic internet connectivity...")
    
    test_urls = [
        "https://httpbin.org/get",
        "https://api.github.com",
        "https://www.google.com"
    ]
    
    session = requests.Session()
    
    for url in test_urls:
        try:
            response = session.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")
    
    print()

def main():
    """Main function"""
    print("TAVILY API PROXY TEST TOOL")
    print("=" * 50)
    print()
    
    # First test basic connectivity
    test_connection_only()
    
    # Then test Tavily
    success = test_tavily_with_proxy()
    
    if success:
        print("🎉 Tavily API test completed successfully!")
        print("You can now integrate Tavily into your search system.")
    else:
        print("💔 Tavily API test failed.")
        print("Please check the error messages above and try different proxy settings.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
