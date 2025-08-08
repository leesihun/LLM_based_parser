#!/usr/bin/env python3
"""
Quick Search Test Runner
Runs both comprehensive API tests and improved search test
"""

import sys
import subprocess
import os

def run_comprehensive_test():
    """Run the comprehensive API test"""
    print("🔍 RUNNING COMPREHENSIVE SEARCH API TEST")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, 'test_all_search_apis.py'], 
                              capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def run_improved_search_test():
    """Run the improved search test"""
    print("\n🚀 TESTING IMPROVED SEARCH IMPLEMENTATION")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, 'src/web_search_improved.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Improved search test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running improved search test: {e}")
        return False

def quick_connectivity_test():
    """Quick connectivity test"""
    print("🌐 QUICK CONNECTIVITY TEST")
    print("=" * 30)
    
    import requests
    
    test_urls = [
        ("Google", "https://www.google.com"),
        ("Wikipedia", "https://en.wikipedia.org"),
        ("Reddit", "https://www.reddit.com"),
        ("GitHub", "https://api.github.com"),
        ("Stack Overflow", "https://api.stackexchange.com")
    ]
    
    working_count = 0
    
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Connected")
                working_count += 1
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Failed - {str(e)}")
    
    print(f"\nConnectivity: {working_count}/{len(test_urls)} services reachable")
    return working_count > 0

def main():
    """Main test runner"""
    print("SEARCH FUNCTIONALITY DIAGNOSTIC SUITE")
    print("=" * 80)
    
    # Quick connectivity check first
    has_internet = quick_connectivity_test()
    
    if not has_internet:
        print("\n❌ NO INTERNET CONNECTIVITY DETECTED")
        print("Please check your internet connection and try again.")
        return False
    
    print("\n✅ Internet connectivity confirmed")
    
    # Run comprehensive test
    comprehensive_success = run_comprehensive_test()
    
    # Run improved search test
    improved_success = run_improved_search_test()
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if comprehensive_success:
        print("✅ Comprehensive API test completed successfully")
    else:
        print("❌ Comprehensive API test had issues")
    
    if improved_success:
        print("✅ Improved search implementation working")
    else:
        print("❌ Improved search implementation had issues")
    
    if comprehensive_success or improved_success:
        print("\n🎉 At least one search method is working!")
        print("\nNEXT STEPS:")
        print("1. Check the test output above for working APIs")
        print("2. Implement the working search methods in your system")
        print("3. Update your web_search.py with working providers")
    else:
        print("\n❌ No search methods are working")
        print("\nTROUBLESHOOTING:")
        print("1. Check firewall settings")
        print("2. Verify you're not behind a corporate proxy")
        print("3. Try running from a different network")
        print("4. Consider using manual search fallback only")
    
    return comprehensive_success or improved_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
