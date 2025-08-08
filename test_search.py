#!/usr/bin/env python3
"""
Web Search Diagnostic Tool
Test different search providers and diagnose connectivity issues
"""

import sys
import json
from src.web_search import WebSearcher

def test_search_providers():
    """Test all search providers and report results"""
    
    # Load config
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        search_config = config.get('web_search', {})
    except Exception as e:
        print(f"Error loading config: {e}")
        search_config = {}
    
    print("=" * 60)
    print("WEB SEARCH DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Test query
    test_query = "Python programming"
    print(f"Test Query: {test_query}")
    print()
    
    # Initialize searcher with different provider configurations
    providers_to_test = [
        (['bing'], "Bing Search Only"),
        (['duckduckgo'], "DuckDuckGo Only"),
        (['manual'], "Manual Fallback Only"),
        (['bing', 'duckduckgo', 'manual'], "All Providers (Default Order)")
    ]
    
    for providers, description in providers_to_test:
        print(f"Testing: {description}")
        print("-" * 40)
        
        # Create searcher with specific providers
        test_config = search_config.copy()
        test_config['providers'] = providers
        test_config['max_results'] = 3
        
        searcher = WebSearcher(test_config)
        
        try:
            results = searcher.search(test_query, max_results=3)
            
            if results:
                print(f"✅ SUCCESS: Got {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title'][:50]}...")
                    print(f"     Source: {result['source']}")
                    if result['url']:
                        print(f"     URL: {result['url'][:60]}...")
                    print()
            else:
                print("❌ FAILED: No results returned")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
        
        searcher.close()
        print()
    
    # Network connectivity test
    print("NETWORK CONNECTIVITY TEST")
    print("-" * 40)
    
    import requests
    
    test_urls = [
        ("DuckDuckGo", "https://duckduckgo.com"),
        ("Bing", "https://www.bing.com"),
        ("Google", "https://www.google.com"),
        ("General Internet", "https://httpbin.org/ip")
    ]
    
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: Connected (Status: {response.status_code})")
            else:
                print(f"⚠️  {name}: Connected but status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Failed - {str(e)}")
    
    print()
    print("TROUBLESHOOTING TIPS:")
    print("-" * 40)
    print("1. If all providers fail:")
    print("   - Check your internet connection")
    print("   - Verify firewall allows Python web requests")
    print("   - Check if you're behind a corporate proxy")
    print()
    print("2. If only DuckDuckGo fails:")
    print("   - DuckDuckGo may be blocked in your region")
    print("   - Try changing providers order in config.json")
    print("   - Bing is set as primary fallback")
    print()
    print("3. If Bing fails:")
    print("   - Bing may be blocking automated requests")
    print("   - Try different user agent in config.json")
    print("   - Consider using Google Custom Search API")
    print()
    print("4. For Google Custom Search:")
    print("   - Get API key from Google Cloud Console")
    print("   - Create Custom Search Engine")
    print("   - Add credentials to config.json")

if __name__ == "__main__":
    test_search_providers()
