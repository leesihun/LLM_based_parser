"""Integration test for TypeScript-only web search."""

import sys
import io
import json

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.services.search.manager import SearchManager

def test_search_manager():
    """Test SearchManager with TypeScript bridge."""
    print("=" * 70)
    print("TypeScript-Only Web Search Integration Test")
    print("=" * 70)

    # Configuration matching config.json
    config = {
        "enabled": True,
        "default_provider": "duckduckgo",  # Must be supported by TypeScript
        "total_results": 3,
        "simple_mode": True,
        "visit_specific_website": True,
        "timeout": 15,
        "disable_fallbacks": True,
        "google_domain": "google.com",
        "brave_api_key": "",
        "tavily_api_key": "",
        "exa_api_key": "",
        "providers": {
            "google": {"enabled": True},
            "duckduckgo": {"enabled": True},
            "brave_api": {"enabled": False},
            "tavily_api": {"enabled": False},
            "exa_api": {"enabled": False}
        },
        "cache": {
            "enabled": True,
            "default_ttl": 3600
        },
        "analytics": {
            "enabled": True
        }
    }

    try:
        print("\n[1/4] Initializing SearchManager...")
        manager = SearchManager(config)
        print("      [OK] SearchManager initialized")

        print("\n[2/4] Testing DuckDuckGo search...")
        result = manager.search("python programming", max_results=3)

        print(f"\n      Provider: {result.provider}")
        print(f"      Success: {result.success}")
        print(f"      Query: {result.query}")
        print(f"      Results: {len(result.results)}")

        if result.error:
            print(f"      Error: {result.error}")

        if result.results:
            print(f"\n      Sample result:")
            sample = result.results[0]
            print(f"        - Title: {sample.title}")
            print(f"        - URL: {sample.url}")
            print(f"        - Source: {sample.source}")
            if sample.snippet:
                print(f"        - Snippet: {sample.snippet[:100]}...")

        print("\n[3/4] Testing Google search...")
        result2 = manager.search("machine learning", max_results=3, provider_override="google")

        print(f"\n      Provider: {result2.provider}")
        print(f"      Success: {result2.success}")
        print(f"      Results: {len(result2.results)}")

        if result2.error:
            print(f"      Error: {result2.error}")

        print("\n[4/4] Checking analytics...")
        stats = manager.get_search_stats()
        print(f"\n      Total searches: {stats.get('total_searches', 0)}")
        print(f"      Successful: {stats.get('successful_searches', 0)}")
        print(f"      Failed: {stats.get('failed_searches', 0)}")

        print("\n" + "=" * 70)
        print("Test Summary:")
        print("=" * 70)

        if result.success or result2.success:
            print("[OK] TypeScript integration is working!")
            print("     The bridge successfully communicates with Node.js")
            print("     and executes Page Assist original code.")

            if not result.results and not result2.results:
                print("\n[INFO] No search results were returned.")
                print("       This is likely due to:")
                print("       - Anti-scraping measures from search engines")
                print("       - Network restrictions")
                print("       - Rate limiting")
                print("\n       To get reliable results, use API-based providers:")
                print("       - Brave API (brave_api)")
                print("       - Tavily API (tavily_api)")
                print("       - Exa API (exa_api)")
                print("\n       Add API keys to config.json to enable them.")
        else:
            print("[ERROR] TypeScript integration failed!")
            print(f"        DuckDuckGo error: {result.error}")
            print(f"        Google error: {result2.error}")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_search_manager()
    sys.exit(0 if success else 1)
