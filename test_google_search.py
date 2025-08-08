#!/usr/bin/env python3
"""
Google Custom Search API Test and Setup Helper
Tests your Google API key and helps set up Custom Search Engine
"""

import requests
import json
import sys
from urllib.parse import quote_plus

class GoogleSearchTester:
    def __init__(self, api_key: str, search_engine_id: str = None):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    def test_api_key(self):
        """Test if the API key is valid"""
        print("🔑 TESTING GOOGLE API KEY")
        print("=" * 40)
        print(f"API Key: {self.api_key[:20]}...")
        
        # Test with a minimal request (this will fail without search engine ID but will validate the key)
        url = self.base_url
        params = {
            'key': self.api_key,
            'cx': 'test',  # Invalid search engine ID
            'q': 'test'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', '')
                
                if 'Invalid Value' in error_message and 'cx' in error_message:
                    print("✅ API Key is VALID!")
                    print("❌ But you need to set up a Custom Search Engine ID")
                    return True, "need_search_engine_id"
                elif 'API key not valid' in error_message:
                    print("❌ API Key is INVALID!")
                    return False, "invalid_api_key"
                else:
                    print(f"⚠️  Unexpected error: {error_message}")
                    return False, error_message
            else:
                print(f"⚠️  Unexpected response status: {response.status_code}")
                return False, f"status_{response.status_code}"
                
        except Exception as e:
            print(f"❌ Network error: {str(e)}")
            return False, str(e)
    
    def test_full_search(self):
        """Test full search functionality if search engine ID is provided"""
        if not self.search_engine_id:
            print("❌ No search engine ID provided")
            return False
        
        print("\n🔍 TESTING FULL GOOGLE SEARCH")
        print("=" * 40)
        print(f"Search Engine ID: {self.search_engine_id}")
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': 'Python programming tutorial',
            'num': 3
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                search_info = data.get('searchInformation', {})
                total_results = search_info.get('totalResults', '0')
                search_time = search_info.get('searchTime', '0')
                
                print(f"✅ SEARCH SUCCESSFUL!")
                print(f"   Total results: {total_results}")
                print(f"   Search time: {search_time}s")
                
                items = data.get('items', [])
                if items:
                    print(f"   Retrieved: {len(items)} results")
                    print("\n📋 Sample Results:")
                    for i, item in enumerate(items, 1):
                        print(f"   {i}. {item.get('title', 'No title')}")
                        print(f"      {item.get('link', 'No URL')}")
                        print(f"      {item.get('snippet', 'No snippet')[:100]}...")
                        print()
                
                return True
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"❌ Search failed: {error_message}")
                return False
                
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return False
    
    def show_setup_instructions(self):
        """Show instructions for setting up Google Custom Search Engine"""
        print("\n📋 GOOGLE CUSTOM SEARCH ENGINE SETUP INSTRUCTIONS")
        print("=" * 60)
        print("You need to create a Custom Search Engine to use Google Search API.")
        print()
        print("STEP 1: Create Custom Search Engine")
        print("1. Go to: https://cse.google.com/cse/")
        print("2. Click 'Add' or 'New Search Engine'")
        print("3. In 'Sites to search', enter: www.google.com")
        print("4. Give it a name like 'My Search Engine'")
        print("5. Click 'Create'")
        print()
        print("STEP 2: Configure for Web Search")
        print("1. Click on your newly created search engine")
        print("2. Go to 'Setup' tab")
        print("3. In 'Basics' section, turn ON 'Search the entire web'")
        print("4. Remove 'www.google.com' from the sites list (since you're searching the entire web)")
        print("5. Click 'Update'")
        print()
        print("STEP 3: Get Search Engine ID")
        print("1. Go to 'Setup' tab")
        print("2. In 'Basics' section, find 'Search engine ID'")
        print("3. Copy the Search Engine ID (looks like: 'a1b2c3d4e5f6g7h8i')")
        print()
        print("STEP 4: Update Configuration")
        print("Add the Search Engine ID to your config/config.json:")
        print('  "google_search_engine_id": "YOUR_SEARCH_ENGINE_ID_HERE"')
        print()
        print("STEP 5: Test Again")
        print("Run this script again to test the full setup")
        print()
        print("💡 TIPS:")
        print("- Free tier allows 100 searches per day")
        print("- You can increase limits by enabling billing")
        print("- The search engine will search the entire web once configured")

def main():
    api_key = "AIzaSyDNfDTC08vERYpsO6scvTBfA2Tch4q3Tlo"
    
    print("GOOGLE CUSTOM SEARCH API TESTER")
    print("=" * 50)
    
    # Try to load search engine ID from config
    search_engine_id = None
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        search_engine_id = config.get('web_search', {}).get('google_search_engine_id', '')
        if not search_engine_id:
            search_engine_id = None
    except:
        pass
    
    tester = GoogleSearchTester(api_key, search_engine_id)
    
    # Test API key
    api_valid, status = tester.test_api_key()
    
    if not api_valid:
        print(f"\n❌ SETUP FAILED: {status}")
        if 'invalid_api_key' in status:
            print("Please check your API key and ensure it's correct.")
            print("You can get a new API key from: https://console.cloud.google.com/")
        return False
    
    # If API key is valid but no search engine ID
    if status == "need_search_engine_id":
        tester.show_setup_instructions()
        
        if search_engine_id:
            print(f"\n🔄 Found search engine ID in config: {search_engine_id}")
            print("Testing full search functionality...")
            success = tester.test_full_search()
            
            if success:
                print("\n🎉 GOOGLE SEARCH IS FULLY WORKING!")
                print("Your web search should now work with Google as the primary provider.")
                return True
            else:
                print("\n❌ Search engine ID may be incorrect or not properly configured.")
                print("Please follow the setup instructions above.")
                return False
        else:
            print(f"\n⏭️  NEXT STEP: Set up Custom Search Engine ID")
            print("Follow the instructions above, then update your config.json")
            return False
    
    # If we get here, something else happened
    print(f"\n⚠️  Unexpected status: {status}")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
