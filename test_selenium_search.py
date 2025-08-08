#!/usr/bin/env python3
"""
Test Selenium Browser Search System
Tests the web search system using real browser automation
"""

import json
import sys
import os
import time

def load_search_config():
    """Load search configuration"""
    try:
        with open('config/search_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not load search config: {e}")
        return None

def check_dependencies():
    """Check if Selenium dependencies are installed"""
    print("=" * 60)
    print("CHECKING SELENIUM DEPENDENCIES")
    print("=" * 60)
    
    try:
        import selenium
        print(f"✓ selenium - OK (version: {selenium.__version__})")
    except ImportError:
        print("✗ selenium - MISSING")
        print("Install with: pip install selenium webdriver-manager")
        return False
    
    try:
        import webdriver_manager
        print("✓ webdriver-manager - OK")
    except ImportError:
        print("✗ webdriver-manager - MISSING")
        print("Install with: pip install webdriver-manager")
        return False
    
    print("\nAll Selenium dependencies available!")
    return True

def test_selenium_browser_search():
    """Test the Selenium browser search system"""
    print("\n" + "=" * 60)
    print("TESTING SELENIUM BROWSER SEARCH")
    print("=" * 60)
    
    try:
        # Add src to path
        sys.path.append('src')
        from selenium_search import SeleniumSearcher
        
        # Load configuration
        config = load_search_config()
        if not config:
            print("WARNING: Using default configuration")
            config = {}
        
        print("Initializing Selenium WebDriver...")
        print("(This may take a moment to download browser drivers)")
        
        # Create searcher with configuration
        search_config = config.get('web_search', {})
        searcher = SeleniumSearcher(search_config)
        
        print("✓ Selenium WebDriver initialized successfully")
        
        # Test search capability first
        print("\nTesting search capability...")
        test_result = searcher.test_search_capability()
        
        print(f"Test successful: {test_result['success']}")
        if test_result['success']:
            print(f"Results found: {test_result['result_count']}")
            print(f"Working engines: {test_result.get('engines_working', [])}")
            
            if test_result.get('sample_result'):
                sample = test_result['sample_result']
                print(f"\nSample result:")
                print(f"  Title: {sample['title'][:60]}...")
                print(f"  Source: {sample['source']}")
                print(f"  URL: {sample['url'][:60]}...")
        else:
            print(f"Test failed: {test_result.get('error', 'Unknown error')}")
        
        # Test actual searches
        test_queries = [
            "python programming tutorial",
            "web development basics",
            "machine learning introduction"
        ]
        
        for query in test_queries:
            print(f"\nTesting search: '{query}'")
            print("-" * 40)
            
            results = searcher.search(query, max_results=3)
            
            if results and len(results) > 0:
                print(f"✓ Found {len(results)} results")
                
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title'][:50]}...")
                    print(f"     Source: {result['source']}")
                    print(f"     URL: {result['url'][:60]}...")
                    if result.get('snippet'):
                        print(f"     Snippet: {result['snippet'][:80]}...")
                    print()
            else:
                print(f"✗ No results found for '{query}'")
            
            time.sleep(2)  # Pause between searches
        
        searcher.close()
        print("✓ Browser closed successfully")
        return len([r for r in results if 'Fallback' not in r.get('source', '')]) > 0
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure to install: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"✗ Browser search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_search_feature():
    """Test the web search feature integration"""
    print("\n" + "=" * 60)
    print("TESTING WEB SEARCH FEATURE INTEGRATION")
    print("=" * 60)
    
    try:
        sys.path.append('src')
        from web_search_feature import WebSearchFeature
        
        # Load configuration
        config = load_search_config()
        if not config:
            config = {}
        
        search_config = config.get('web_search', {})
        print("Initializing Web Search Feature...")
        
        feature = WebSearchFeature(search_config)
        print("✓ WebSearchFeature initialized")
        
        # Test capabilities
        capabilities = feature.get_search_capabilities()
        print(f"Search enabled: {capabilities['enabled']}")
        print(f"Test status: {'SUCCESS' if capabilities['test_status']['success'] else 'FAILED'}")
        
        if capabilities['test_status']['success']:
            engines = capabilities['test_status'].get('engines_working', [])
            print(f"Working engines: {', '.join(engines)}")
        
        # Test search with LLM formatting
        test_query = "artificial intelligence basics"
        print(f"\nTesting formatted search: '{test_query}'")
        
        result = feature.search_web(test_query, max_results=2, format_for_llm=True)
        
        if result['success']:
            print(f"✓ Search successful: {result['result_count']} results")
            
            # Show formatted context (first 300 chars)
            formatted_context = result.get('formatted_context', '')
            if formatted_context:
                print(f"\nFormatted for LLM (preview):")
                print("-" * 30)
                print(formatted_context[:300] + "..." if len(formatted_context) > 300 else formatted_context)
            
            feature.close()
            return True
        else:
            print(f"✗ Search failed: {result.get('error', 'Unknown error')}")
            feature.close()
            return False
            
    except Exception as e:
        print(f"✗ Web search feature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("SELENIUM BROWSER SEARCH TEST")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Missing required dependencies!")
        print("Please install: pip install -r requirements.txt")
        return False
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Selenium Browser Search
    print(f"\nTEST 1/2: Selenium Browser Search")
    if test_selenium_browser_search():
        tests_passed += 1
        print("✓ Selenium Browser Search - PASSED")
    else:
        print("✗ Selenium Browser Search - FAILED")
    
    # Test 2: Web Search Feature
    print(f"\nTEST 2/2: Web Search Feature Integration")
    if test_web_search_feature():
        tests_passed += 1
        print("✓ Web Search Feature - PASSED")
    else:
        print("✗ Web Search Feature - FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Success rate: {(tests_passed/total_tests)*100:.0f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your Selenium browser search system is working!")
        print("\nBrowser automation successfully bypasses proxy restrictions!")
        print("You can now use real Google/Bing search results in your LLM system.")
        return True
    else:
        print(f"\n⚠️ {total_tests - tests_passed} test(s) failed")
        print("Check browser installation and network connectivity.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nTest completed: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)