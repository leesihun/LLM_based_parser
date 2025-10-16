#!/usr/bin/env python3
"""
Simple test to search for 'python' and return raw web search results structure
"""

import sys
import os
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_python_search():
    """Test web search for 'python' and return raw results structure"""

    try:
        from src.web_search_feature import create_web_search_feature
        print("Successfully imported WebSearchFeature")
    except ImportError as e:
        print(f"Import error: {e}")
        return None

    # Create search feature without LLM client
    search_feature = create_web_search_feature()

    print("Testing web search for 'python'...")

    # Search for 'python' with raw results (no LLM formatting)
    result = search_feature.search_web('python', max_results=3, format_for_llm=False)

    if result['success']:
        print("Search successful!")
        print(f"Provider: {result.get('provider')}")
        print(f"Results count: {result.get('result_count')}")

        # Return the raw results structure
        return {
            'success': result['success'],
            'provider': result.get('provider'),
            'result_count': result.get('result_count'),
            'timestamp': result.get('timestamp'),
            'results': result.get('results', []),
            'keyword_extraction_used': result.get('keyword_extraction_used', False),
            'queries_tried': result.get('queries_tried', []),
            'extraction_info': result.get('extraction_info')
        }
    else:
        print(f"Search failed: {result.get('error')}")
        return {
            'success': False,
            'error': result.get('error'),
            'queries_tried': result.get('queries_tried', [])
        }

if __name__ == "__main__":
    results = test_python_search()

    if results and results['success']:
        print("\n=== RAW SEARCH RESULTS ===")
        print(json.dumps(results, indent=2, ensure_ascii=True, default=str))
    else:
        print("No results to display")
