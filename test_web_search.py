#!/usr/bin/env python3
"""
Test script for web search functionality
Use this to debug web search issues
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"  # Change as needed
PASSWORD = "admin123"  # Change as needed

def get_session_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("session_token")
    else:
        print(f"Login failed: {response.text}")
        return None

def test_web_search_direct():
    """Test direct web search endpoint"""
    token = get_session_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("=== Testing Direct Web Search ===")
    
    # Test direct web search
    response = requests.post(
        f"{BASE_URL}/api/search/web",
        headers=headers,
        json={
            "query": "python programming tutorial",
            "max_results": 3
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_web_search_debug():
    """Test web search debug endpoint"""
    token = get_session_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\n=== Testing Web Search Debug Endpoint ===")
    
    # Test different types of queries
    test_queries = [
        "artificial intelligence 2024",
        "How do I install Python on Windows?",
        "latest developments in machine learning",
        "help me debug my React application"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing query: {query} ---")
        response = requests.post(
            f"{BASE_URL}/api/search/test",
            headers=headers,
            json={"query": query}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('result', {}).get('success', False)}")
            print(f"Keywords extracted: {result.get('capabilities', {}).get('keyword_extraction_enabled', False)}")
            
            search_result = result.get('result', {})
            if 'extraction_info' in search_result:
                extraction = search_result['extraction_info']
                print(f"Keywords: {extraction.get('keywords', [])}")
                print(f"Queries: {extraction.get('queries', [])}")
                print(f"Method: {extraction.get('method', 'unknown')}")
            
            if search_result.get('error'):
                print(f"Error: {search_result['error']}")
        else:
            print(f"Error Response: {json.dumps(response.json(), indent=2)}")
            
        print("-" * 50)

def test_web_search_chat():
    """Test web search chat endpoint"""
    token = get_session_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\n=== Testing Web Search Chat ===")
    
    # Test web search chat
    response = requests.post(
        f"{BASE_URL}/api/chat/web-search",
        headers=headers,
        json={
            "message": "What are the latest developments in AI?",
            "max_results": 3
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Session ID: {result.get('session_id')}")
        print(f"Search context used: {result.get('search_context_used')}")
        print(f"Search results count: {result.get('search_results_count')}")
        print(f"Keyword extraction used: {result.get('keyword_extraction_used')}")
        print(f"Response: {result.get('response', '')[:200]}...")
    else:
        print(f"Error Response: {json.dumps(response.json(), indent=2)}")

def test_keyword_extraction():
    """Test keyword extraction directly"""
    token = get_session_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\n=== Testing LLM Keyword Extraction ===")
    
    test_queries = [
        "How do I install Python on Windows?",
        "What are the latest developments in artificial intelligence?",
        "Help me debug my React application",
        "machine learning tutorials for beginners"
    ]
    
    for query in test_queries:
        print(f"\n--- Extracting keywords from: {query} ---")
        response = requests.post(
            f"{BASE_URL}/api/search/extract-keywords",
            headers=headers,
            json={"query": query}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            extraction = result.get('extraction_result', {})
            config = result.get('extractor_config', {})
            
            print(f"LLM enabled: {config.get('use_llm', False)}")
            print(f"LLM available: {config.get('llm_client_available', False)}")
            print(f"Methods: {config.get('extraction_methods', [])}")
            print(f"Keywords: {extraction.get('keywords', [])}")
            print(f"Queries: {extraction.get('queries', [])}")
            print(f"Method used: {extraction.get('method', 'unknown')}")
            print(f"Adequate: {extraction.get('adequate_keywords', False)}")
            
            if extraction.get('extraction_results'):
                for method, results in extraction['extraction_results'].items():
                    print(f"{method} results: {[r[0] if isinstance(r, tuple) else r for r in results[:3]]}")
        else:
            print(f"Error: {response.json()}")
        print("-" * 60)

def test_search_status():
    """Test search capabilities"""
    token = get_session_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Search Status ===")
    
    # Test search status
    response = requests.get(
        f"{BASE_URL}/api/search/status",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def main():
    print("🔍 Web Search Debugging Tool")
    print("=" * 50)
    
    # Test server health first
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✓ Server is running")
            print(f"✓ Web search enabled: {health.get('web_search_enabled')}")
            print(f"✓ Keyword extraction enabled: {health.get('keyword_extraction_enabled')}")
        else:
            print(f"✗ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return
    
    # Run all tests
    test_search_status()
    test_keyword_extraction()
    test_web_search_debug()
    test_web_search_direct()
    test_web_search_chat()

if __name__ == "__main__":
    main()