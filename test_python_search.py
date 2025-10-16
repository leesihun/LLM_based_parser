#!/usr/bin/env python3
"""
Test script to search for 'python' and return raw web search results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.web_search_feature import create_web_search_feature
    print("Successfully imported WebSearchFeature")
except ImportError as e:
    print(f"Import error: {e}")
    print("Available files in src directory:")
    for file in os.listdir('src'):
        if file.endswith('.py'):
            print(f"  - {file}")
    sys.exit(1)

def test_python_search():
    """Test web search for 'python' and return raw results"""
    print("Testing Web Search for 'python'")
    print("=" * 50)

    # Create search feature without LLM client
    search_feature = create_web_search_feature()

    # Check capabilities first
    capabilities = search_feature.get_search_capabilities()
    print(f"Search enabled: {capabilities['enabled']}")
    print(f"Probe success: {'SUCCESS' if capabilities['success'] else 'FAILED'}")
    if capabilities['success']:
        print(f"Provider used: {capabilities.get('provider')}")
        print(f"Result count: {capabilities.get('result_count', 0)}")
    else:
        print(f"Error: {capabilities.get('error')}")

    print("\n" + "-" * 50)
    print("Searching for 'python'...")

    # Search for 'python' with raw results
    result = search_feature.search_web('python', max_results=5, format_for_llm=False)

    print(f"Search success: {result['success']}")
    if result['success']:
        print(f"Provider: {result.get('provider')}")
        print(f"Results returned: {result.get('result_count')}")
        print(f"Timestamp: {result.get('timestamp')}")

        # Print raw results
        print("\nRaw Search Results:")
        print("=" * 50)

        results = result.get('results', [])
        for i, item in enumerate(results, 1):
            # Clean title and snippet to avoid encoding issues
            title = item.get('title', 'No title')
            snippet = item.get('snippet', '')

            # Remove common problematic characters
            title = title.replace('\u0001f4da', '').replace('\u2705', '').replace('\u274c', '')
            snippet = snippet.replace('\u0001f4da', '').replace('\u2705', '').replace('\u274c', '')

            print(f"\n{i}. {title}")
            print(f"   URL: {item.get('url', 'No URL')}")
            if snippet:
                print(f"   Snippet: {snippet[:200]}...")
            if item.get('source'):
                print(f"   Source: {item.get('source')}")
            if item.get('content'):
                print(f"   Content length: {len(item.get('content', ''))} chars")

        # Print additional metadata
        print("\nAdditional Information:")
        print(f"   Keyword extraction used: {result.get('keyword_extraction_used', False)}")
        print(f"   Successful query: {result.get('successful_query')}")
        print(f"   Queries tried: {result.get('queries_tried', [])}")
        if result.get('extraction_info'):
            print(f"   Extraction info: {result['extraction_info']}")

    else:
        print(f"Search failed: {result.get('error', 'Unknown error')}")
        print(f"   Queries tried: {result.get('queries_tried', [])}")
        if result.get('extraction_info'):
            print(f"   Extraction info: {result['extraction_info']}")

    print(f"\nSearch history entries: {len(search_feature.get_search_history())}")
    print("\nTest completed")

if __name__ == "__main__":
    test_python_search()
