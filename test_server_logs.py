"""Test to check if TypeScript is actually being called."""

import logging
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.services.search.manager import SearchManager

def test_with_logs():
    """Test search with detailed logging."""
    print("=" * 70)
    print("Testing TypeScript Search with Detailed Logs")
    print("=" * 70)
    print()

    config = {
        "enabled": True,
        "default_provider": "duckduckgo",
        "total_results": 3,
        "google_domain": "google.com"
    }

    print("[1] Initializing SearchManager...")
    manager = SearchManager(config)
    print()

    print("[2] Executing search (check logs for TypeScript indicators)...")
    print()

    result = manager.search("test query", max_results=3)

    print()
    print("=" * 70)
    print("Search Result:")
    print("=" * 70)
    print(f"Provider: {result.provider}")
    print(f"Success: {result.success}")
    print(f"Results: {len(result.results)}")
    print(f"Error: {result.error}")
    print()

    print("=" * 70)
    print("Expected Log Messages:")
    print("=" * 70)
    print("✓ Should see: 'TypeScript search bridge initialized'")
    print("✓ Should see: 'Using TypeScript search (Page Assist original)'")
    print("✓ Should see: 'TypeScript search returned X results'")
    print()

    print("If you DON'T see these messages, TypeScript is NOT being called!")
    print("=" * 70)

if __name__ == "__main__":
    test_with_logs()
