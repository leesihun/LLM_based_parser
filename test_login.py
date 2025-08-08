#!/usr/bin/env python3
"""
Test script to verify login authentication works
"""

import requests
import json

def test_login_flow():
    """Test the complete login flow"""
    base_url = "http://localhost:3000"
    
    print("Testing login authentication flow...")
    
    # Test 1: Login with admin credentials
    login_data = {
        "username": "admin",
        "password": "administrator"
    }
    
    try:
        print("\n1. Testing login with admin credentials...")
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"   Session token: {result['session_token'][:20]}...")
            print(f"   User: {result['user']['username']} ({result['user']['role']})")
            
            # Test 2: Verify token with /api/auth/me
            session_token = result['session_token']
            headers = {"Authorization": f"Bearer {session_token}"}
            
            print("\n2. Testing token validation...")
            me_response = requests.get(f"{base_url}/api/auth/me", headers=headers)
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print("✅ Token validation successful!")
                print(f"   User: {user_data['user']['display_name']}")
                print(f"   Email: {user_data['user']['email']}")
                
                # Test 3: Test a protected endpoint
                print("\n3. Testing protected endpoint...")
                health_response = requests.get(f"{base_url}/api/rag/stats", headers=headers)
                
                if health_response.status_code == 200:
                    print("✅ Protected endpoint access successful!")
                    stats = health_response.json()
                    print(f"   RAG documents: {stats.get('stats', {}).get('document_count', 'Unknown')}")
                else:
                    print(f"⚠️  Protected endpoint returned: {health_response.status_code}")
                
                return True
                
            else:
                print(f"❌ Token validation failed: {me_response.status_code}")
                print(f"   Response: {me_response.text}")
                return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        print("   Start server with: python server.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_invalid_credentials():
    """Test login with invalid credentials"""
    base_url = "http://localhost:3000"
    
    print("\n" + "="*50)
    print("Testing invalid credentials...")
    
    invalid_data = {
        "username": "invalid",
        "password": "wrong"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=invalid_data)
        
        if response.status_code == 401:
            print("✅ Invalid credentials properly rejected")
            return True
        else:
            print(f"⚠️  Unexpected response for invalid credentials: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("Login Authentication Test")
    print("=" * 50)
    
    # Test valid login
    success1 = test_login_flow()
    
    # Test invalid login
    success2 = test_invalid_credentials()
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print(f"Valid login flow: {'PASS' if success1 else 'FAIL'}")
    print(f"Invalid credentials: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n✅ All authentication tests passed!")
        print("The login system should work correctly now.")
        print("\nTo test in browser:")
        print("1. Start server: python server.py")
        print("2. Open: http://localhost:3000")
        print("3. Login with: admin / administrator")
    else:
        print("\n❌ Some tests failed. Check server logs for details.")

if __name__ == "__main__":
    main()