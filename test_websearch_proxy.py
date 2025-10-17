#!/usr/bin/env python3
"""
Web Search Test for Proxy Environments
Comprehensive test specifically designed for corporate proxy environments
"""

import json
import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def check_proxy_environment():
    """Check and display proxy environment variables"""
    logger.info("=" * 60)
    logger.info("Proxy Environment Check")
    logger.info("=" * 60)

    proxy_vars = {
        'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
        'HTTPS_PROXY': os.environ.get('HTTPS_PROXY'),
        'http_proxy': os.environ.get('http_proxy'),
        'https_proxy': os.environ.get('https_proxy'),
        'NO_PROXY': os.environ.get('NO_PROXY'),
        'no_proxy': os.environ.get('no_proxy')
    }

    found_proxy = False
    for key, value in proxy_vars.items():
        if value:
            logger.info(f"✅ {key} = {value}")
            found_proxy = True
        else:
            logger.info(f"   {key}: not set")

    if not found_proxy:
        logger.warning("\n⚠️  No proxy environment variables detected")
        logger.info("If behind a corporate proxy, set these variables:")
        logger.info("  Windows CMD:")
        logger.info("    set HTTP_PROXY=http://proxy.company.com:port")
        logger.info("    set HTTPS_PROXY=http://proxy.company.com:port")
        logger.info("  PowerShell:")
        logger.info("    $env:HTTP_PROXY='http://proxy.company.com:port'")
        logger.info("    $env:HTTPS_PROXY='http://proxy.company.com:port'")

    return found_proxy

def test_typescript_bridge():
    """Test TypeScript bridge with detailed error reporting"""
    logger.info("\n" + "=" * 60)
    logger.info("TypeScript Bridge Test (DuckDuckGo)")
    logger.info("=" * 60)

    try:
        from services.search.typescript_bridge import TypeScriptSearchBridge

        config = {
            "max_results": 5,
            "google_domain": "google.com"
        }

        logger.info("Initializing TypeScript bridge...")
        bridge = TypeScriptSearchBridge(config)
        logger.info("✅ Bridge initialized")

        query = "python programming"
        logger.info(f"\n🔍 Searching: '{query}'")
        logger.info("Provider: duckduckgo")

        result = bridge.search(query, "duckduckgo", 5)

        logger.info(f"\nSuccess: {result.get('success')}")
        logger.info(f"Result count: {result.get('result_count', 0)}")

        if result.get('error'):
            logger.error(f"Error: {result.get('error')}")

        if result.get('success') and result.get('results'):
            logger.info(f"✅ Got {len(result['results'])} results!")

            for i, item in enumerate(result['results'][:3], 1):
                logger.info(f"\n[{i}] {item.get('title', 'No title')[:60]}...")
                logger.info(f"    URL: {item.get('url', 'No URL')[:80]}")

            return True
        else:
            logger.error("❌ No results returned")
            logger.error("Possible causes:")
            logger.error("  1. Corporate firewall blocking DuckDuckGo")
            logger.error("  2. Proxy not configured for Node.js")
            logger.error("  3. SSL certificate interception by proxy")
            logger.error("  4. Network connectivity issues")

            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error("Stack trace:", exc_info=True)
        return False

def test_search_manager():
    """Test complete search pipeline"""
    logger.info("\n" + "=" * 60)
    logger.info("SearchManager Integration Test")
    logger.info("=" * 60)

    try:
        from services.search.manager import SearchManager

        config = {
            "enabled": True,
            "default_provider": "duckduckgo",
            "total_results": 5,
            "timeout": 30,
            "simple_mode": True,
            "cache": {"enabled": False},
            "result_filtering": {"enabled": False}
        }

        logger.info("Initializing SearchManager...")
        manager = SearchManager(config)
        logger.info("✅ Manager initialized")

        query = "machine learning"
        logger.info(f"\n🔍 Searching: '{query}'")

        execution = manager.search(query, max_results=5)

        logger.info(f"\nProvider: {execution.provider}")
        logger.info(f"Success: {execution.success}")

        if execution.error:
            logger.error(f"Error: {execution.error}")

        if execution.results:
            logger.info(f"✅ Got {len(execution.results)} results!")

            for i, result in enumerate(execution.results[:2], 1):
                logger.info(f"\n[{i}] {result.title[:60]}...")
                logger.info(f"    {result.url[:80]}")

            return True
        else:
            logger.error("❌ No results")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error("Stack trace:", exc_info=True)
        return False

def test_node_connectivity():
    """Test Node.js availability and proxy handling"""
    logger.info("\n" + "=" * 60)
    logger.info("Node.js Connectivity Test")
    logger.info("=" * 60)

    import subprocess

    # Check Node.js version
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"✅ Node.js: {result.stdout.strip()}")
        else:
            logger.error("❌ Node.js not working")
            return False
    except Exception as e:
        logger.error(f"❌ Node.js not found: {e}")
        return False

    # Check npm
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"✅ npm: {result.stdout.strip()}")
        else:
            logger.warning("⚠️  npm not working properly")
    except Exception as e:
        logger.warning(f"⚠️  npm check failed: {e}")

    # Check if websearch_ts directory exists
    ws_dir = Path(__file__).parent / "websearch_ts"
    if ws_dir.exists():
        logger.info(f"✅ websearch_ts directory found")

        node_modules = ws_dir / "node_modules"
        if node_modules.exists():
            logger.info(f"✅ node_modules installed")
        else:
            logger.warning("⚠️  node_modules not found - need to run 'npm install'")

        search_js = ws_dir / "search.js"
        if search_js.exists():
            logger.info(f"✅ search.js found")
        else:
            logger.error("❌ search.js missing!")
            return False
    else:
        logger.error("❌ websearch_ts directory not found!")
        return False

    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Web Search Test - Proxy Environment")
    print("=" * 60 + "\n")

    results = {}

    # Test 1: Proxy detection
    logger.info("TEST 1/4: Checking proxy environment...")
    results['proxy'] = check_proxy_environment()

    # Test 2: Node.js connectivity
    logger.info("\nTEST 2/4: Checking Node.js setup...")
    results['node'] = test_node_connectivity()

    # Test 3: TypeScript bridge
    logger.info("\nTEST 3/4: Testing TypeScript bridge...")
    results['typescript'] = test_typescript_bridge()

    # Test 4: SearchManager
    logger.info("\nTEST 4/4: Testing SearchManager...")
    results['manager'] = test_search_manager()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name.upper()}")

    print("=" * 60)

    if results.get('typescript') and results.get('manager'):
        print("✅ Web search is working!")
        print("\nNote: If you get 0 results on corporate network:")
        print("  1. Check if proxy is configured correctly")
        print("  2. Check if DuckDuckGo is accessible from browser")
        print("  3. Try using API providers (Brave, Tavily, Exa)")
        print("  4. Contact IT about firewall/proxy settings")
        return 0
    else:
        print("❌ Web search has issues")
        print("\nTroubleshooting:")

        if not results.get('node'):
            print("  - Fix Node.js installation")

        if not results.get('typescript'):
            print("  - Check corporate proxy settings")
            print("  - Try: set NODE_TLS_REJECT_UNAUTHORIZED=0")
            print("  - Check firewall rules for Node.js")

        return 1

if __name__ == "__main__":
    sys.exit(main())
