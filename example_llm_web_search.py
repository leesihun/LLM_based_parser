#!/usr/bin/env python3
"""
Example of LLM-based Web Search with Keyword Extraction
This demonstrates how the LLM intelligently extracts keywords before searching
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_session_token():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    return response.json().get("session_token") if response.status_code == 200 else None

def demonstrate_llm_keyword_extraction():
    """Demonstrate how LLM extracts keywords before web search"""
    token = get_session_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🧠 LLM-Based Web Search with Intelligent Keyword Extraction")
    print("=" * 70)
    
    # Example queries to demonstrate the power of LLM keyword extraction
    examples = [
        {
            "query": "How do I install Python on Windows 11?",
            "expected_keywords": "Python installation, Windows 11, setup"
        },
        {
            "query": "What are the latest developments in artificial intelligence?",
            "expected_keywords": "artificial intelligence, AI developments, latest AI news"
        },
        {
            "query": "Help me debug my React application that's not rendering",
            "expected_keywords": "React debugging, React rendering issues, troubleshooting"
        },
        {
            "query": "Best practices for Docker container optimization",
            "expected_keywords": "Docker optimization, container best practices, Docker performance"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        query = example["query"]
        print(f"\n📝 Example {i}: {query}")
        print("-" * 50)
        
        # Step 1: Show keyword extraction
        print("🔍 Step 1: LLM Keyword Extraction")
        keyword_response = requests.post(
            f"{BASE_URL}/api/search/extract-keywords",
            headers=headers,
            json={"query": query}
        )
        
        if keyword_response.status_code == 200:
            result = keyword_response.json()
            extraction = result.get('extraction_result', {})
            print(f"   Original Query: {query}")
            print(f"   LLM Keywords: {', '.join(extraction.get('keywords', []))}")
            print(f"   Search Queries: {extraction.get('queries', [])}")
            print(f"   Method: {extraction.get('method', 'unknown')}")
        else:
            print(f"   ❌ Keyword extraction failed: {keyword_response.json()}")
            continue
        
        # Step 2: Show web search with LLM-extracted keywords
        print("\n🌐 Step 2: Web Search with LLM Keywords")
        search_response = requests.post(
            f"{BASE_URL}/api/chat/web-search",
            headers=headers,
            json={
                "message": query,
                "max_results": 3
            }
        )
        
        if search_response.status_code == 200:
            result = search_response.json()
            print(f"   ✅ Search successful!")
            print(f"   Results found: {result.get('search_results_count', 0)}")
            print(f"   Keyword extraction used: {result.get('keyword_extraction_used', False)}")
            print(f"   Processing time: {result.get('processing_time', 0)}ms")
            print(f"   Response preview: {result.get('response', '')[:100]}...")
        else:
            error = search_response.json()
            print(f"   ❌ Search failed: {error.get('error', 'Unknown error')}")
        
        print("=" * 70)

def compare_with_without_llm():
    """Compare search results with and without LLM keyword extraction"""
    print("\n🔬 Comparison: With vs Without LLM Keyword Extraction")
    print("=" * 70)
    
    # This would require temporarily disabling LLM extraction
    # For demonstration purposes only
    print("Note: To see the full comparison, you would:")
    print("1. Test with current LLM-enabled config")
    print("2. Temporarily set 'use_llm': false in config")
    print("3. Compare the search quality and results")
    print("4. Re-enable LLM extraction")

def main():
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server not responding")
            return
            
        health = response.json()
        print(f"✅ Server running")
        print(f"✅ Web search: {health.get('web_search_enabled', False)}")
        print(f"✅ Keyword extraction: {health.get('keyword_extraction_enabled', False)}")
        
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run demonstrations
    demonstrate_llm_keyword_extraction()
    compare_with_without_llm()
    
    print("\n🎉 Demo complete!")
    print("\n💡 Key Benefits of LLM Keyword Extraction:")
    print("   • More intelligent keyword selection")
    print("   • Better search results relevancy") 
    print("   • Handles natural language queries better")
    print("   • Configurable system prompts")
    print("   • Fallback to original query if extraction fails")

if __name__ == "__main__":
    main()