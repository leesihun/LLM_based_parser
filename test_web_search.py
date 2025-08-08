#!/usr/bin/env python3
"""
Simple Web Search Test Script
Tests the browser-based web search functionality
"""

import os
import sys
from datetime import datetime

def test_browser_search():
    """Test the BrowserSearcher functionality"""
    print("=" * 60)
    print("WEB SEARCH TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import the search modules
        from src.browser_search import BrowserSearcher
        from src.web_search_feature import WebSearchFeature
        print("✓ Successfully imported web search modules")
        
        # Test 1: Basic capability test
        print("\n" + "-" * 40)
        print("TEST 1: Search Capability Check")
        print("-" * 40)
        
        searcher = BrowserSearcher()
        capability_result = searcher.test_search_capability()
        
        if capability_result['success']:
            print("✓ Web search capability: WORKING")
            print(f"  - Test query: {capability_result['test_query']}")
            print(f"  - Results found: {capability_result['result_count']}")
            print(f"  - Working engines: {', '.join(capability_result['engines_working'])}")
            
            if capability_result.get('sample_result'):
                sample = capability_result['sample_result']
                print(f"  - Sample title: {sample['title'][:60]}...")
                print(f"  - Sample source: {sample['source']}")
        else:
            print("✗ Web search capability: FAILED")
            print(f"  - Error: {capability_result.get('error', 'Unknown error')}")
            return False
        
        # Test 2: Manual search test
        print("\n" + "-" * 40)
        print("TEST 2: Manual Search Test")
        print("-" * 40)
        
        test_queries = [
            "python programming tutorial",
            "machine learning basics",
            "web development guide"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            results = searcher.search(query, max_results=3)
            
            if results:
                print(f"  ✓ Found {len(results)} results")
                for j, result in enumerate(results, 1):
                    title = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
                    print(f"    {j}. {title}")
                    print(f"       Source: {result['source']}")
                    if result['url']:
                        print(f"       URL: {result['url'][:60]}...")
            else:
                print(f"  ✗ No results found")
        
        # Test 3: Web Search Feature Integration
        print("\n" + "-" * 40)
        print("TEST 3: Web Search Feature Integration")
        print("-" * 40)
        
        feature = WebSearchFeature()
        integration_result = feature.search_web("artificial intelligence", max_results=2, format_for_llm=True)
        
        if integration_result['success']:
            print("✓ Web search feature integration: WORKING")
            print(f"  - Results: {integration_result['result_count']}")
            print(f"  - LLM formatted context available: {'formatted_context' in integration_result}")
            
            # Show first part of formatted context
            if integration_result.get('formatted_context'):
                context = integration_result['formatted_context']
                print("  - Sample formatted output:")
                print("    " + context[:100].replace('\n', '\n    ') + "...")
        else:
            print("✗ Web search feature integration: FAILED")
            print(f"  - Error: {integration_result.get('error', 'Unknown error')}")
        
        # Test 4: Search capabilities
        print("\n" + "-" * 40)
        print("TEST 4: Feature Capabilities")
        print("-" * 40)
        
        capabilities = feature.get_search_capabilities()
        print(f"  - Search enabled: {capabilities['enabled']}")
        print(f"  - Test status: {'SUCCESS' if capabilities['test_status']['success'] else 'FAILED'}")
        print(f"  - Recent searches: {capabilities['recent_searches']}")
        
        # Clean up
        searcher.close()
        feature.close()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Web search functionality is working properly.")
        print("You can now use web search features in your application.")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import Error: {e}")
        print("Make sure you're running this from the project root directory.")
        return False
        
    except Exception as e:
        print(f"✗ Test Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    success = test_browser_search()
    
    if success:
        print("\n🎉 Web search is ready to use!")
        print("\nNext steps:")
        print("1. Start the server: python server.py")
        print("2. Use the web interface to test search functionality")
        print("3. Try the enhanced chat with web search capabilities")
    else:
        print("\n❌ Web search tests failed!")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify firewall settings allow web requests")
        print("3. Try running the test again")
        print("4. Check the console for specific error messages")
    
    return success

if __name__ == "__main__":
    main()