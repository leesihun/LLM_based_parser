#!/usr/bin/env python3
"""
Test Working Search System
Tests the updated web search system with working proxy configuration
"""

import json
import time
from datetime import datetime
from typing import Dict, List

def load_search_config():
    """Load search configuration"""
    try:
        with open('config/search_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not load search config: {e}")
        return None

def test_browser_search_with_config():
    """Test the updated browser search with proxy configuration"""
    print("=" * 60)
    print("TESTING BROWSER SEARCH WITH WORKING PROXY")
    print("=" * 60)
    
    try:
        from src.browser_search import BrowserSearcher
        
        # Load configuration
        config = load_search_config()
        if not config:
            print("❌ Could not load configuration")
            return False
        
        # Create searcher with configuration
        search_config = config.get('web_search', {})
        searcher = BrowserSearcher(search_config)
        
        print(f"✓ BrowserSearcher initialized with proxy: {search_config.get('proxy', {}).get('host')}:{search_config.get('proxy', {}).get('port')}")
        
        # Test queries
        test_queries = [
            "python programming",
            "web development tutorial", 
            "machine learning basics"
        ]
        
        all_successful = True
        total_results = 0
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            print("-" * 40)
            
            start_time = time.time()
            results = searcher.search(query, max_results=3)
            elapsed_time = time.time() - start_time
            
            if results and len(results) > 0:
                print(f"✅ Found {len(results)} results ({elapsed_time:.2f}s)")
                total_results += len(results)
                
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['title'][:50]}...")
                    print(f"      Source: {result['source']}")
                    print(f"      URL: {result['url'][:60]}...")
                
            else:
                print(f"❌ No results found")
                all_successful = False
            
            # Small delay between requests
            time.sleep(2)
        
        searcher.close()
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total results: {total_results}")
        print(f"   Success rate: {'100%' if all_successful else 'Partial'}")
        
        return all_successful
        
    except Exception as e:
        print(f"❌ Browser search test failed: {e}")
        return False

def test_web_search_feature():
    """Test the web search feature integration"""
    print("\n" + "=" * 60)
    print("TESTING WEB SEARCH FEATURE INTEGRATION")
    print("=" * 60)
    
    try:
        from src.web_search_feature import WebSearchFeature
        
        # Load configuration
        config = load_search_config()
        if not config:
            print("❌ Could not load configuration")
            return False
        
        search_config = config.get('web_search', {})
        feature = WebSearchFeature(search_config)
        
        print("✓ WebSearchFeature initialized")
        
        # Test search with LLM formatting
        test_query = "artificial intelligence tutorial"
        print(f"\n🔍 Testing formatted search: '{test_query}'")
        
        result = feature.search_web(test_query, max_results=3, format_for_llm=True)
        
        if result['success']:
            print(f"✅ Search successful: {result['result_count']} results")
            
            # Show formatted context
            formatted_context = result.get('formatted_context', '')
            if formatted_context:
                print(f"\n📝 Formatted for LLM (first 200 chars):")
                print(f"   {formatted_context[:200]}...")
            
            return True
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Web search feature test failed: {e}")
        return False

def test_search_capabilities():
    """Test search capabilities and status"""
    print("\n" + "=" * 60)
    print("TESTING SEARCH CAPABILITIES")
    print("=" * 60)
    
    try:
        from src.web_search_feature import WebSearchFeature
        
        config = load_search_config()
        if not config:
            return False
        
        search_config = config.get('web_search', {})
        feature = WebSearchFeature(search_config)
        
        # Test capabilities
        capabilities = feature.get_search_capabilities()
        
        print(f"Search enabled: {capabilities['enabled']}")
        print(f"Test status: {'SUCCESS' if capabilities['test_status']['success'] else 'FAILED'}")
        
        if capabilities['test_status']['success']:
            engines = capabilities['test_status'].get('engines_working', [])
            print(f"Working engines: {', '.join(engines)}")
            print(f"Result count: {capabilities['test_status'].get('result_count', 0)}")
        
        feature.close()
        return capabilities['test_status']['success']
        
    except Exception as e:
        print(f"❌ Capabilities test failed: {e}")
        return False

def test_advanced_search_methods():
    """Test additional search methods"""
    print("\n" + "=" * 60)
    print("TESTING ADVANCED SEARCH METHODS")
    print("=" * 60)
    
    # Test SearX instances
    print("1. Testing SearX instances...")
    try:
        import requests
        
        config = load_search_config()
        proxy_config = config.get('web_search', {}).get('proxy', {})
        
        session = requests.Session()
        
        if proxy_config.get('enabled'):
            proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
            session.proxies.update({
                'http': proxy_url,
                'https': proxy_url
            })
        
        # Test a SearX instance
        searx_url = "https://searx.be/search"
        params = {
            'q': 'python tutorial',
            'format': 'json',
            'engines': 'duckduckgo'
        }
        
        response = session.get(searx_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   ✅ SearX working: {len(results)} results")
        else:
            print(f"   ❌ SearX failed: HTTP {response.status_code}")
        
        session.close()
        
    except Exception as e:
        print(f"   ❌ SearX test error: {e}")
    
    # Test Wikipedia API
    print("\n2. Testing Wikipedia API...")
    try:
        import requests
        
        config = load_search_config()
        proxy_config = config.get('web_search', {}).get('proxy', {})
        
        session = requests.Session()
        
        if proxy_config.get('enabled'):
            proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
            session.proxies.update({
                'http': proxy_url,
                'https': proxy_url
            })
        
        wiki_url = "https://en.wikipedia.org/api/rest_v1/page/search"
        params = {'q': 'machine learning', 'limit': 3}
        
        response = session.get(wiki_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get('pages', [])
            print(f"   ✅ Wikipedia working: {len(pages)} results")
        else:
            print(f"   ❌ Wikipedia failed: HTTP {response.status_code}")
        
        session.close()
        
    except Exception as e:
        print(f"   ❌ Wikipedia test error: {e}")

def test_server_integration():
    """Test if the server can use the search functionality"""
    print("\n" + "=" * 60)
    print("TESTING SERVER INTEGRATION")
    print("=" * 60)
    
    try:
        # Try to import and test server integration
        from src.server_integration import WebSearchIntegration
        print("✓ Server integration module available")
        
        # Mock objects for testing
        class MockApp:
            def route(self, *args, **kwargs):
                def decorator(f):
                    return f
                return decorator
        
        class MockMemory:
            pass
        
        class MockLLMClient:
            def __init__(self):
                config = load_search_config()
                self.config = config or {}
        
        class MockUserManager:
            pass
        
        def mock_require_auth(f):
            return f
        
        # Test integration creation
        mock_app = MockApp()
        mock_memory = MockMemory()
        mock_llm_client = MockLLMClient()
        mock_user_manager = MockUserManager()
        
        integration = WebSearchIntegration(
            mock_app, 
            mock_memory, 
            mock_llm_client, 
            mock_user_manager, 
            mock_require_auth
        )
        
        print("✅ Server integration created successfully")
        
        # Test search capability
        capabilities = integration.search_feature.get_search_capabilities()
        
        if capabilities['test_status']['success']:
            print("✅ Server integration search working")
            return True
        else:
            print("❌ Server integration search not working")
            return False
        
    except Exception as e:
        print(f"❌ Server integration test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🧪 COMPREHENSIVE WORKING SEARCH SYSTEM TEST")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Browser Search with Proxy", test_browser_search_with_config),
        ("Web Search Feature", test_web_search_feature), 
        ("Search Capabilities", test_search_capabilities),
        ("Server Integration", test_server_integration)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 50)
        
        try:
            success = test_func()
            test_results.append((test_name, success))
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status}: {test_name}")
            
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            test_results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Run advanced methods test (informational only)
    test_advanced_search_methods()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.0f}%")
    print()
    
    for test_name, success in test_results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your web search system is fully operational!")
        print("\nNext steps:")
        print("1. Start your server: python server.py")
        print("2. Test web search through the web interface")
        print("3. Use enhanced chat with web search capabilities")
        
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        print("Some functionality may not work correctly.")
        print("Check the error messages above for troubleshooting.")
        
        return False

def main():
    """Main test function"""
    success = run_comprehensive_test()
    
    if success:
        print(f"\n✅ Web search system is working with your proxy configuration!")
    else:
        print(f"\n❌ Some issues remain with the web search system.")
        print("Please review the test output above for specific failures.")
    
    return success

if __name__ == "__main__":
    main()