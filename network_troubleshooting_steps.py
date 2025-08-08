#!/usr/bin/env python3
"""
Network Troubleshooting Steps for Web Search Issues
Step-by-step guide to resolve connectivity problems
"""

import subprocess
import platform
import socket
import requests
import time

def check_basic_network():
    """Check basic network configuration"""
    print("=" * 60)
    print("BASIC NETWORK CONFIGURATION CHECK")
    print("=" * 60)
    
    try:
        # Check if network interface is up
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            print("Network Interface Status:")
            print(result.stdout[:500])
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            print("Network Interface Status:")
            print(result.stdout[:500])
    except Exception as e:
        print(f"Could not check network interfaces: {e}")
    
    print("\n" + "-" * 40)
    
    # Check default gateway
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.run(['route', 'print', '0.0.0.0'], capture_output=True, text=True)
            print("Default Gateway:")
            lines = result.stdout.split('\n')
            for line in lines:
                if '0.0.0.0' in line and 'Gateway' not in line:
                    print(line.strip())
                    break
        else:
            result = subprocess.run(['route', '-n'], capture_output=True, text=True)
            print("Default Gateway:")
            print(result.stdout)
    except Exception as e:
        print(f"Could not check default gateway: {e}")

def test_different_proxies():
    """Test with different proxy configurations"""
    print("\n" + "=" * 60)
    print("TESTING DIFFERENT PROXY CONFIGURATIONS")
    print("=" * 60)
    
    # Test configurations to try
    proxy_configs = [
        {"name": "Your Current Proxy", "host": "168.219.61.252", "port": 8080},
        {"name": "No Proxy", "host": None, "port": None},
        {"name": "Common Corporate Proxy 1", "host": "proxy.company.com", "port": 8080},
        {"name": "Common Corporate Proxy 2", "host": "proxy", "port": 3128},
        {"name": "Alternative Port", "host": "168.219.61.252", "port": 3128},
    ]
    
    for config in proxy_configs:
        print(f"\nTesting: {config['name']}")
        print("-" * 30)
        
        if config['host'] is None:
            # Test without proxy
            try:
                response = requests.get('http://httpbin.org/ip', timeout=10)
                if response.status_code == 200:
                    print(f"✅ SUCCESS - No proxy needed!")
                    print(f"   Response: {response.text[:100]}")
                    return True
            except Exception as e:
                print(f"❌ Failed without proxy: {e}")
        else:
            # Test with proxy
            try:
                proxies = {
                    'http': f'http://{config["host"]}:{config["port"]}',
                    'https': f'http://{config["host"]}:{config["port"]}'
                }
                
                # First test proxy connectivity
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((config["host"], config["port"]))
                sock.close()
                
                if result == 0:
                    print(f"   ✅ Proxy server reachable")
                    
                    # Test HTTP request
                    response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
                    if response.status_code == 200:
                        print(f"   ✅ HTTP request successful!")
                        print(f"   Response: {response.text[:100]}")
                        return True
                    else:
                        print(f"   ❌ HTTP request failed: {response.status_code}")
                else:
                    print(f"   ❌ Cannot reach proxy server")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    return False

def check_windows_proxy_settings():
    """Check Windows proxy settings"""
    print("\n" + "=" * 60)
    print("WINDOWS PROXY SETTINGS CHECK")
    print("=" * 60)
    
    try:
        # Check registry for proxy settings (Windows only)
        if platform.system().lower() == 'windows':
            import winreg
            
            try:
                # Check Internet Settings
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
                
                try:
                    proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                    print(f"Proxy Enabled: {bool(proxy_enable)}")
                except:
                    print("Proxy Enabled: Not set")
                
                try:
                    proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                    print(f"Proxy Server: {proxy_server}")
                except:
                    print("Proxy Server: Not set")
                
                try:
                    auto_config = winreg.QueryValueEx(key, "AutoConfigURL")[0]
                    print(f"Auto Config URL: {auto_config}")
                except:
                    print("Auto Config URL: Not set")
                
                winreg.CloseKey(key)
                
            except Exception as e:
                print(f"Could not read registry: {e}")
        else:
            print("Not Windows - checking environment variables")
            import os
            
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            for var in proxy_vars:
                value = os.environ.get(var)
                if value:
                    print(f"{var}: {value}")
                else:
                    print(f"{var}: Not set")
    
    except ImportError:
        print("Cannot check Windows registry settings")

def test_dns_resolution():
    """Test DNS resolution with different servers"""
    print("\n" + "=" * 60)
    print("DNS RESOLUTION TEST")
    print("=" * 60)
    
    test_domains = ['google.com', 'github.com', 'stackoverflow.com']
    dns_servers = [
        ('System Default', None),
        ('Google DNS', '8.8.8.8'),
        ('Cloudflare DNS', '1.1.1.1'),
        ('OpenDNS', '208.67.222.222')
    ]
    
    for dns_name, dns_server in dns_servers:
        print(f"\nTesting with {dns_name}:")
        print("-" * 30)
        
        for domain in test_domains:
            try:
                if dns_server:
                    # This is a simplified test - actual DNS server change requires more work
                    print(f"   {domain}: Would test with {dns_server}")
                else:
                    ip = socket.gethostbyname(domain)
                    print(f"   ✅ {domain} → {ip}")
            except Exception as e:
                print(f"   ❌ {domain} → Error: {e}")

def generate_troubleshooting_commands():
    """Generate specific commands to run based on OS"""
    print("\n" + "=" * 60)
    print("MANUAL TROUBLESHOOTING COMMANDS")
    print("=" * 60)
    
    if platform.system().lower() == 'windows':
        print("🖥️  WINDOWS COMMANDS TO RUN:")
        print("-" * 30)
        print("1. Check network connectivity:")
        print("   ipconfig /all")
        print("   ping 8.8.8.8")
        print("   ping google.com")
        print("")
        print("2. Check proxy settings:")
        print("   netsh winhttp show proxy")
        print("   netsh winhttp reset proxy")
        print("")
        print("3. Flush DNS cache:")
        print("   ipconfig /flushdns")
        print("")
        print("4. Check firewall:")
        print("   netsh advfirewall show allprofiles")
        print("")
        print("5. Test connectivity:")
        print("   telnet 168.219.61.252 8080")
        print("   curl -x 168.219.61.252:8080 http://httpbin.org/ip")
        
    else:
        print("🐧 LINUX/MAC COMMANDS TO RUN:")
        print("-" * 30)
        print("1. Check network:")
        print("   ip addr show")
        print("   ping -c 3 8.8.8.8")
        print("   ping -c 3 google.com")
        print("")
        print("2. Check proxy:")
        print("   echo $HTTP_PROXY")
        print("   echo $HTTPS_PROXY")
        print("")
        print("3. Test connectivity:")
        print("   telnet 168.219.61.252 8080")
        print("   curl -x 168.219.61.252:8080 http://httpbin.org/ip")

def suggest_solutions():
    """Suggest potential solutions"""
    print("\n" + "=" * 60)
    print("POTENTIAL SOLUTIONS")
    print("=" * 60)
    
    solutions = [
        {
            "title": "🔧 Network Configuration Issues",
            "steps": [
                "Check if your network cable/WiFi is connected",
                "Restart your network adapter",
                "Check if DHCP assigned correct IP address",
                "Try connecting to a different network"
            ]
        },
        {
            "title": "🌐 Proxy Server Issues", 
            "steps": [
                "Verify proxy server address: 168.219.61.252:8080",
                "Check if proxy requires authentication",
                "Try different proxy ports (3128, 8000, 8888)",
                "Contact network administrator for correct proxy settings"
            ]
        },
        {
            "title": "🔒 Corporate Firewall/Security",
            "steps": [
                "Check if your company blocks all external internet",
                "Request whitelist for specific domains needed",
                "Ask IT about approved proxy settings",
                "Check if VPN is required for internet access"
            ]
        },
        {
            "title": "💻 System-Level Issues",
            "steps": [
                "Restart your computer",
                "Check Windows/system proxy settings",
                "Temporarily disable antivirus/firewall",
                "Reset network settings to default"
            ]
        },
        {
            "title": "🆘 Alternative Approaches",
            "steps": [
                "Use mobile hotspot temporarily for testing",
                "Try from a different computer/location",
                "Set up local web search cache/database",
                "Use offline documentation and resources"
            ]
        }
    ]
    
    for solution in solutions:
        print(f"\n{solution['title']}:")
        print("-" * 40)
        for i, step in enumerate(solution['steps'], 1):
            print(f"   {i}. {step}")

def create_offline_search_alternative():
    """Suggest offline alternatives"""
    print("\n" + "=" * 60)
    print("OFFLINE SEARCH ALTERNATIVES")
    print("=" * 60)
    
    print("Since internet connectivity is not available, consider:")
    print("")
    print("📚 LOCAL DOCUMENTATION:")
    print("   - Download Python documentation offline")
    print("   - Install local copies of Stack Overflow data")
    print("   - Use IDE built-in help and documentation")
    print("")
    print("💾 CACHED SEARCH RESULTS:")
    print("   - Pre-download common search results when internet works")
    print("   - Create local knowledge base from previous searches")
    print("   - Use local file indexing for code search")
    print("")
    print("🔄 PERIODIC SYNC:")
    print("   - When internet becomes available, batch download resources")
    print("   - Update local cache during internet-available periods")
    print("   - Sync with team's shared knowledge base")

def main():
    """Run comprehensive network troubleshooting"""
    print("🔧 NETWORK TROUBLESHOOTING FOR WEB SEARCH")
    print("=" * 70)
    print("This will help identify and resolve connectivity issues")
    print("")
    
    # Run all diagnostic steps
    check_basic_network()
    
    # Test different proxy configurations
    connectivity_found = test_different_proxies()
    
    if not connectivity_found:
        check_windows_proxy_settings()
        test_dns_resolution()
        generate_troubleshooting_commands()
        suggest_solutions()
        create_offline_search_alternative()
        
        print("\n" + "=" * 70)
        print("❌ NO INTERNET CONNECTIVITY FOUND")
        print("=" * 70)
        print("IMMEDIATE ACTIONS NEEDED:")
        print("1. Check physical network connection")
        print("2. Verify with network administrator")
        print("3. Try different network/location")
        print("4. Consider offline alternatives")
        
    else:
        print("\n" + "=" * 70)
        print("✅ CONNECTIVITY WORKING!")
        print("=" * 70)
        print("You can now proceed with web search functionality.")
    
    return connectivity_found

if __name__ == "__main__":
    main()