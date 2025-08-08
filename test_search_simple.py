#!/usr/bin/env python3
"""
Simple Search System Test
Tests the web search system with working proxy configuration
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

def test_browser_search():
    """Test the browser search system"""
    print("=" * 60)
    print("TESTING BROWSER SEARCH SYSTEM")
    print("=" * 60)
    
    try:
        # Add src to path
        sys.path.append('src')
        from browser_search import BrowserSearcher
        
        # Load configuration
        config = load_search_config()
        if not config:
            print("ERROR: Could not load configuration")
            return False
        
        # Create searcher with configuration
        search_config = config.get('web_search', {})
        searcher = BrowserSearcher(search_config)
        
        proxy_info = search_config.get('proxy', {})
        print(f"Using proxy: {proxy_info.get('host')}:{proxy_info.get('port')}")
        
        # Test search capability first
        print("\nTesting search capability...")
        test_result = searcher.test_search_capability()
        
        print(f"Test successful: {test_result['success']}")
        if test_result['success']:
            print(f"Results found: {test_result['result_count']}")
            print(f"Working engines: {test_result.get('engines_working', [])}")
        else:
            print(f"Test failed: {test_result.get('error', 'Unknown error')}")
        
        # Test actual search
        print("\nTesting actual search...")
        query = "python programming tutorial"
        results = searcher.search(query, max_results=3)
        
        if results and len(results) > 0:
            print(f"SUCCESS: Found {len(results)} results for '{query}'")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title'][:50]}...")
                print(f"     Source: {result['source']}")
                print(f"     URL: {result['url'][:60]}...")
                print()
        else:
            print(f"FAILED: No results found for '{query}'")
        
        searcher.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"Browser search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_search_feature():
    """Test the web search feature"""
    print("\n" + "=" * 60)
    print("TESTING WEB SEARCH FEATURE")
    print("=" * 60)
    
    try:
        sys.path.append('src')
        from web_search_feature import WebSearchFeature
        
        # Load configuration
        config = load_search_config()
        if not config:
            print("ERROR: Could not load configuration")
            return False
        
        search_config = config.get('web_search', {})
        feature = WebSearchFeature(search_config)
        
        print("WebSearchFeature initialized")
        
        # Test capabilities
        capabilities = feature.get_search_capabilities()
        print(f"Search enabled: {capabilities['enabled']}")
        print(f"Test status: {'SUCCESS' if capabilities['test_status']['success'] else 'FAILED'}")
        
        if capabilities['test_status']['success']:
            engines = capabilities['test_status'].get('engines_working', [])
            print(f"Working engines: {', '.join(engines)}")
        
        # Test search with LLM formatting
        test_query = "machine learning basics"
        print(f"\nTesting formatted search: '{test_query}'")
        
        result = feature.search_web(test_query, max_results=2, format_for_llm=True)
        
        if result['success']:
            print(f"SUCCESS: Search found {result['result_count']} results")
            
            # Show formatted context (first 300 chars)
            formatted_context = result.get('formatted_context', '')
            if formatted_context:
                print(f"\nFormatted for LLM (preview):")
                print(formatted_context[:300] + "..." if len(formatted_context) > 300 else formatted_context)
            
            feature.close()
            return True
        else:
            print(f"FAILED: Search failed - {result.get('error', 'Unknown error')}")
            feature.close()
            return False
            
    except Exception as e:
        print(f"Web search feature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("=" * 60)
    print("CHECKING DEPENDENCIES")
    print("=" * 60)
    
    required_modules = [
        'requests',
        'bs4',  # beautifulsoup4
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} - OK")
        except ImportError:
            print(f"✗ {module} - MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nMISSING DEPENDENCIES: {', '.join(missing_modules)}")
        print("Install with: pip install requests beautifulsoup4")
        return False
    else:
        print("\nAll dependencies are available!")
        return True

def main():
    """Main test function"""
    print("SIMPLE SEARCH SYSTEM TEST")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        return False
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Browser Search
    print(f"\nTEST 1/2: Browser Search")
    if test_browser_search():
        tests_passed += 1
        print("✓ Browser Search - PASSED")
    else:
        print("✗ Browser Search - FAILED")
    
    time.sleep(2)  # Brief pause between tests
    
    # Test 2: Web Search Feature
    print(f"\nTEST 2/2: Web Search Feature")
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
        print("\n✓ ALL TESTS PASSED!")
        print("Your web search system is working!")
        return True
    else:
        print(f"\n✗ {total_tests - tests_passed} test(s) failed")
        print("Some functionality may not work correctly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)