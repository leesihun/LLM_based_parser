"""Test TypeScript search integration."""

import json
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.services.search.typescript_bridge import TypeScriptSearchBridge

def test_typescript_bridge():
    """Test the TypeScript search bridge."""
    print("=" * 60)
    print("Testing TypeScript Search Bridge")
    print("=" * 60)

    # Initialize bridge
    config = {
        "google_domain": "google.com",
        "brave_api_key": "",
        "tavily_api_key": "",
        "exa_api_key": ""
    }

    try:
        bridge = TypeScriptSearchBridge(config)
        print("[OK] TypeScript bridge initialized successfully\n")

        # Test search
        query = "python programming tutorial"
        provider = "duckduckgo"
        max_results = 3

        print(f"Testing search:")
        print(f"  Provider: {provider}")
        print(f"  Query: {query}")
        print(f"  Max results: {max_results}\n")

        result = bridge.search(query, provider, max_results)

        print("Search result:")
        print(json.dumps(result, indent=2))

        if result.get("success"):
            print(f"\n[OK] Search succeeded!")
            print(f"   Result count: {result.get('result_count', 0)}")

            results = result.get('results', [])
            if results:
                print(f"\n   Sample result:")
                sample = results[0]
                print(f"   - Title: {sample.get('title', 'N/A')}")
                print(f"   - URL: {sample.get('url', 'N/A')}")
                print(f"   - Snippet: {sample.get('snippet', 'N/A')[:100]}...")
            else:
                print("\n[WARN] No results returned (might be due to network/anti-scraping)")
        else:
            print(f"\n[ERROR] Search failed: {result.get('error')}")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_typescript_bridge()
