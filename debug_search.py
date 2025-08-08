#!/usr/bin/env python3
"""
Debug Search Issues
Test each search engine individually to see what's being blocked
"""

import requests
import json
import sys
from bs4 import BeautifulSoup

def load_config():
    """Load search configuration"""
    try:
        with open('config/search_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not load config: {e}")
        return None

def test_basic_connectivity():
    """Test basic HTTP connectivity through proxy"""
    print("=" * 50)
    print("TESTING BASIC CONNECTIVITY")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return False
    
    proxy_config = config.get('web_search', {}).get('proxy', {})
    proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
    
    session = requests.Session()
    session.proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Test simple HTTP request
    try:
        print(f"Testing HTTP through proxy: {proxy_url}")
        response = session.get('http://httpbin.org/ip', timeout=10)
        print(f"✓ HTTP works: {response.status_code}")
        if response.status_code == 200:
            print(f"  Your IP: {response.json().get('origin', 'Unknown')}")
    except Exception as e:
        print(f"✗ HTTP failed: {e}")
        return False
    
    # Test HTTPS request
    try:
        print("Testing HTTPS through proxy...")
        response = session.get('https://httpbin.org/ip', timeout=10)
        print(f"✓ HTTPS works: {response.status_code}")
    except Exception as e:
        print(f"✗ HTTPS failed: {e}")
    
    session.close()
    return True

def test_search_engines():
    """Test each search engine individually"""
    print("\n" + "=" * 50)
    print("TESTING SEARCH ENGINES")
    print("=" * 50)
    
    config = load_config()
    proxy_config = config.get('web_search', {}).get('proxy', {})
    proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
    
    session = requests.Session()
    session.proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Test DuckDuckGo
    print("\n1. Testing DuckDuckGo...")
    try:
        response = session.get('https://html.duckduckgo.com/html/?q=python+tutorial', timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='result')
            print(f"   Results found: {len(results)}")
            if len(results) > 0:
                first_title = results[0].find('a', class_='result__a')
                if first_title:
                    print(f"   First result: {first_title.get_text(strip=True)[:50]}...")
        else:
            print(f"   Response content preview: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Bing
    print("\n2. Testing Bing...")
    try:
        response = session.get('https://www.bing.com/search?q=python+tutorial', timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('li', class_='b_algo')
            print(f"   Results found: {len(results)}")
            if len(results) > 0:
                first_title = results[0].find('h2')
                if first_title:
                    link = first_title.find('a')
                    if link:
                        print(f"   First result: {link.get_text(strip=True)[:50]}...")
        else:
            print(f"   Response content preview: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Google (simple)
    print("\n3. Testing Google...")
    try:
        response = session.get('https://www.google.com/search?q=python+tutorial', timeout=15)
        print(f"   Status: {response.status_code}")
        if "blocked" in response.text.lower() or "captcha" in response.text.lower():
            print("   Google is blocking or requiring CAPTCHA")
        elif response.status_code == 200:
            print("   Google responded successfully")
        else:
            print(f"   Response content preview: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    session.close()

def test_alternative_endpoints():
    """Test alternative search endpoints"""
    print("\n" + "=" * 50)
    print("TESTING ALTERNATIVE ENDPOINTS")
    print("=" * 50)
    
    config = load_config()
    proxy_config = config.get('web_search', {}).get('proxy', {})
    proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
    
    session = requests.Session()
    session.proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Test Wikipedia API
    print("\n1. Testing Wikipedia API...")
    try:
        response = session.get('https://en.wikipedia.org/api/rest_v1/page/search/python+programming', timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            pages = data.get('pages', [])
            print(f"   Wikipedia results: {len(pages)}")
            if pages:
                print(f"   First result: {pages[0].get('title', 'No title')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test a SearX instance
    print("\n2. Testing SearX instance...")
    try:
        response = session.get('https://searx.be/search?q=python+tutorial&format=json', timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   SearX results: {len(results)}")
            if results:
                print(f"   First result: {results[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    session.close()

def main():
    """Main debug function"""
    print("SEARCH ENGINE DEBUG TEST")
    print("=" * 50)
    
    # Test basic connectivity first
    if not test_basic_connectivity():
        print("Basic connectivity failed - stopping tests")
        return
    
    # Test search engines
    test_search_engines()
    
    # Test alternatives
    test_alternative_endpoints()
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")
    print("=" * 50)
    print("If search engines show 0 results but basic connectivity works,")
    print("your corporate proxy may be filtering/blocking search engine content.")

if __name__ == "__main__":
    main()