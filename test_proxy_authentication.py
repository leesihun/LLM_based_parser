#!/usr/bin/env python3
"""
Proxy Authentication and Configuration Tester
Since DNS works but HTTP requests fail, this tests proxy auth scenarios
"""

import requests
import socket
import time
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib.parse import urlparse
import base64
import getpass

class ProxyAuthTester:
    """Test different proxy authentication methods"""
    
    def __init__(self, proxy_host="168.219.61.252", proxy_port=8080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        
    def test_proxy_connection_types(self):
        """Test different types of proxy connections"""
        print("=" * 60)
        print("PROXY CONNECTION TYPE TESTS")
        print("=" * 60)
        print(f"Testing proxy: {self.proxy_host}:{self.proxy_port}")
        print()
        
        # Test 1: Basic socket connection
        print("1. Testing basic socket connection to proxy...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.proxy_host, self.proxy_port))
            sock.close()
            
            if result == 0:
                print("   ✅ Can connect to proxy server")
            else:
                print(f"   ❌ Cannot connect to proxy server (error: {result})")
                return False
        except Exception as e:
            print(f"   ❌ Socket connection failed: {e}")
            return False
        
        # Test 2: HTTP CONNECT method
        print("\n2. Testing HTTP CONNECT method...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.proxy_host, self.proxy_port))
            
            # Send CONNECT request
            connect_request = f"CONNECT httpbin.org:80 HTTP/1.1\r\nHost: httpbin.org:80\r\n\r\n"
            sock.send(connect_request.encode())
            
            # Read response
            response = sock.recv(1024).decode()
            sock.close()
            
            if "200" in response:
                print("   ✅ CONNECT method works")
                return True
            else:
                print(f"   ❌ CONNECT failed: {response.strip()}")
        except Exception as e:
            print(f"   ❌ CONNECT test failed: {e}")
        
        return False
    
    def test_no_authentication(self):
        """Test proxy without authentication"""
        print("\n3. Testing proxy without authentication...")
        
        proxies = {
            'http': f'http://{self.proxy_host}:{self.proxy_port}',
            'https': f'http://{self.proxy_host}:{self.proxy_port}'
        }
        
        try:
            session = requests.Session()
            session.proxies.update(proxies)
            
            # Try a simple request
            response = session.get('http://httpbin.org/ip', timeout=15)
            
            if response.status_code == 200:
                print("   ✅ Proxy works without authentication!")
                print(f"   Response: {response.text[:100]}")
                return True
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
                
        except requests.exceptions.ProxyError as e:
            print(f"   ❌ Proxy error (likely needs authentication): {e}")
        except requests.exceptions.ConnectTimeout:
            print("   ❌ Connection timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return False
    
    def test_with_authentication(self):
        """Test proxy with authentication"""
        print("\n4. Testing proxy with authentication...")
        
        # Common corporate proxy username/password combinations
        auth_attempts = [
            # Try with user input
            ("manual", "Enter username/password manually"),
        ]
        
        # Also try common defaults
        default_attempts = [
            ("", ""),  # Empty credentials
            ("user", "password"),
            ("proxy", "proxy"),
            ("guest", "guest"),
            ("admin", "admin"),
        ]
        
        # First try manual input
        print("   Would you like to enter proxy credentials? (y/n)")
        try_manual = input("   > ").lower().startswith('y')
        
        if try_manual:
            username = input("   Enter username: ")
            password = getpass.getpass("   Enter password: ")
            auth_attempts.insert(0, (username, password))
        
        # Add default attempts
        auth_attempts.extend(default_attempts)
        
        for username, password in auth_attempts:
            if username == "manual":
                continue
                
            print(f"   Trying: {username}:{'*'*len(password) if password else '(empty)'}")
            
            try:
                # Test with HTTP Basic Auth
                proxies = {
                    'http': f'http://{username}:{password}@{self.proxy_host}:{self.proxy_port}',
                    'https': f'http://{username}:{password}@{self.proxy_host}:{self.proxy_port}'
                }
                
                session = requests.Session()
                session.proxies.update(proxies)
                
                response = session.get('http://httpbin.org/ip', timeout=10)
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS with credentials: {username}:{'*'*len(password)}")
                    print(f"   Response: {response.text[:100]}")
                    return True, username, password
                
            except requests.exceptions.ProxyError as e:
                if "407" in str(e):
                    print(f"   ❌ Authentication failed for {username}")
                else:
                    print(f"   ❌ Proxy error: {e}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return False, None, None
    
    def test_ntlm_authentication(self):
        """Test NTLM authentication (Windows domain auth)"""
        print("\n5. Testing NTLM authentication...")
        
        try:
            from requests_ntlm import HttpNtlmAuth
            
            print("   NTLM library available - testing Windows authentication")
            
            # Try current user credentials
            import getpass
            import os
            
            domain = os.environ.get('USERDOMAIN', '')
            username = os.environ.get('USERNAME', '')
            
            if domain and username:
                print(f"   Trying current user: {domain}\\{username}")
                
                proxies = {
                    'http': f'http://{self.proxy_host}:{self.proxy_port}',
                    'https': f'http://{self.proxy_host}:{self.proxy_port}'
                }
                
                session = requests.Session()
                session.proxies.update(proxies)
                session.auth = HttpNtlmAuth(f'{domain}\\{username}', '')  # No password for current user
                
                try:
                    response = session.get('http://httpbin.org/ip', timeout=15)
                    
                    if response.status_code == 200:
                        print("   ✅ NTLM authentication successful!")
                        print(f"   Response: {response.text[:100]}")
                        return True
                    else:
                        print(f"   ❌ NTLM auth failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ NTLM error: {e}")
            else:
                print("   ❌ Could not determine current user/domain")
                
        except ImportError:
            print("   ⚠️  NTLM library not available (pip install requests-ntlm)")
            print("   💡 To install: pip install requests-ntlm")
        
        return False
    
    def test_system_proxy_settings(self):
        """Test using system proxy settings"""
        print("\n6. Testing system proxy settings...")
        
        try:
            # Use requests with system proxy
            session = requests.Session()
            
            # Let requests use system proxy settings
            response = session.get('http://httpbin.org/ip', timeout=15)
            
            if response.status_code == 200:
                print("   ✅ System proxy settings work!")
                print(f"   Response: {response.text[:100]}")
                return True
            else:
                print(f"   ❌ System proxy failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ System proxy error: {e}")
        
        return False
    
    def test_different_protocols(self):
        """Test HTTP vs HTTPS proxy protocols"""
        print("\n7. Testing different proxy protocols...")
        
        protocols = [
            ('HTTP proxy for HTTP', f'http://{self.proxy_host}:{self.proxy_port}'),
            ('HTTP proxy for HTTPS', f'http://{self.proxy_host}:{self.proxy_port}'),
            ('HTTPS proxy for HTTP', f'https://{self.proxy_host}:{self.proxy_port}'),
            ('HTTPS proxy for HTTPS', f'https://{self.proxy_host}:{self.proxy_port}'),
            ('SOCKS proxy', f'socks5://{self.proxy_host}:{self.proxy_port}'),
        ]
        
        test_urls = [
            ('HTTP URL', 'http://httpbin.org/ip'),
            ('HTTPS URL', 'https://httpbin.org/ip'),
        ]
        
        for proto_name, proxy_url in protocols:
            print(f"   Testing {proto_name}...")
            
            for url_name, test_url in test_urls:
                try:
                    session = requests.Session()
                    
                    if 'socks' in proxy_url:
                        # SOCKS proxy
                        session.proxies = {
                            'http': proxy_url,
                            'https': proxy_url
                        }
                    else:
                        # HTTP proxy
                        if test_url.startswith('https'):
                            session.proxies = {'https': proxy_url}
                        else:
                            session.proxies = {'http': proxy_url}
                    
                    response = session.get(test_url, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"     ✅ {url_name}: SUCCESS")
                        return True
                    else:
                        print(f"     ❌ {url_name}: Failed ({response.status_code})")
                        
                except Exception as e:
                    print(f"     ❌ {url_name}: Error - {e}")
        
        return False
    
    def run_comprehensive_proxy_test(self):
        """Run all proxy tests"""
        print("🔧 COMPREHENSIVE PROXY AUTHENTICATION TEST")
        print("=" * 70)
        print("Since DNS works but HTTP fails, testing proxy configurations...")
        print()
        
        working_configs = []
        
        # Test basic connection first
        if not self.test_proxy_connection_types():
            print("\n❌ Cannot connect to proxy server at all!")
            print("Possible issues:")
            print("- Proxy server is down")
            print("- Wrong proxy address/port") 
            print("- Network firewall blocking proxy")
            return working_configs
        
        # Test different authentication methods
        test_methods = [
            ("No Authentication", self.test_no_authentication),
            ("Basic Authentication", self.test_with_authentication),
            ("NTLM Authentication", self.test_ntlm_authentication),
            ("System Proxy Settings", self.test_system_proxy_settings),
            ("Different Protocols", self.test_different_protocols),
        ]
        
        for method_name, test_method in test_methods:
            print(f"\n🧪 Testing: {method_name}")
            print("-" * 40)
            
            try:
                result = test_method()
                if result:
                    working_configs.append(method_name)
                    print(f"   ✅ {method_name} WORKS!")
                else:
                    print(f"   ❌ {method_name} failed")
            except Exception as e:
                print(f"   ❌ {method_name} error: {e}")
        
        # Summary
        print("\n" + "=" * 70)
        print("PROXY TEST SUMMARY")
        print("=" * 70)
        
        if working_configs:
            print(f"✅ Found {len(working_configs)} working configuration(s):")
            for config in working_configs:
                print(f"   - {config}")
            
            print("\n💡 NEXT STEPS:")
            print("1. Use the working configuration in your web search")
            print("2. Update your search scripts with correct proxy settings")
            print("3. Test the web search functionality again")
            
        else:
            print("❌ No working proxy configurations found!")
            print("\n🔍 ADDITIONAL TROUBLESHOOTING:")
            print("1. Contact your network administrator")
            print("2. Check if proxy requires domain authentication")
            print("3. Verify proxy server is operational")
            print("4. Try connecting from different network location")
            print("5. Check if your IP is blocked by proxy")
        
        return working_configs

def create_working_search_config(working_configs):
    """Create a working search configuration based on test results"""
    if not working_configs:
        return
    
    print("\n" + "=" * 60)
    print("GENERATING WORKING SEARCH CONFIGURATION")
    print("=" * 60)
    
    config_code = '''
# Working proxy configuration based on test results
import requests

def create_working_session():
    """Create a working session based on successful proxy tests"""
    session = requests.Session()
    
    # Based on your test results, use:
'''
    
    if "No Authentication" in working_configs:
        config_code += '''
    # No authentication needed
    session.proxies = {
        'http': 'http://168.219.61.252:8080',
        'https': 'http://168.219.61.252:8080'
    }
'''
    elif "System Proxy Settings" in working_configs:
        config_code += '''
    # Use system proxy settings (no manual configuration needed)
    pass
'''
    elif "Basic Authentication" in working_configs:
        config_code += '''
    # Basic authentication (replace with actual credentials)
    session.proxies = {
        'http': 'http://username:password@168.219.61.252:8080',
        'https': 'http://username:password@168.219.61.252:8080'
    }
'''
    elif "NTLM Authentication" in working_configs:
        config_code += '''
    # NTLM authentication
    from requests_ntlm import HttpNtlmAuth
    session.proxies = {
        'http': 'http://168.219.61.252:8080',
        'https': 'http://168.219.61.252:8080'
    }
    session.auth = HttpNtlmAuth('DOMAIN\\\\username', 'password')
'''
    
    config_code += '''
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    return session

# Test the configuration
if __name__ == "__main__":
    session = create_working_session()
    try:
        response = session.get('http://httpbin.org/ip', timeout=10)
        print(f"Success! Your IP: {response.json()['origin']}")
    except Exception as e:
        print(f"Still not working: {e}")
'''
    
    with open('working_proxy_config.py', 'w') as f:
        f.write(config_code)
    
    print("✅ Created working_proxy_config.py")
    print("   You can now use this configuration in your search scripts")

def main():
    """Main proxy testing function"""
    tester = ProxyAuthTester()
    working_configs = tester.run_comprehensive_proxy_test()
    
    if working_configs:
        create_working_search_config(working_configs)
        print(f"\n🎉 SUCCESS! Found working proxy configuration.")
        print("   Run your web search tests again with the working config.")
    else:
        print(f"\n❌ No working proxy configuration found.")
        print("   You may need to contact your network administrator.")
    
    return len(working_configs) > 0

if __name__ == "__main__":
    main()