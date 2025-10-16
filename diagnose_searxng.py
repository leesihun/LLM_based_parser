#!/usr/bin/env python3
"""
Diagnose SearXNG connectivity and suggest solutions
"""

import socket
import time
import requests
from urllib.parse import urlencode

SEARXNG_HOST = "192.168.219.113"
SEARXNG_PORT = 8080
SEARXNG_URL = f"http://{SEARXNG_HOST}:{SEARXNG_PORT}"

print("=" * 70)
print("SearXNG Server Diagnostic")
print("=" * 70)

# Test 1: TCP Connection
print(f"\n[1] Testing TCP connection to {SEARXNG_HOST}:{SEARXNG_PORT}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((SEARXNG_HOST, SEARXNG_PORT))
    sock.close()
    
    if result == 0:
        print(f"    [OK] Port {SEARXNG_PORT} is OPEN")
    else:
        print(f"    [FAIL] Port {SEARXNG_PORT} is CLOSED or filtered")
        print(f"    Error code: {result}")
except Exception as e:
    print(f"    [ERROR] {e}")

# Test 2: HTTP Base Endpoint
print(f"\n[2] Testing HTTP base endpoint {SEARXNG_URL}/...")
try:
    response = requests.get(f"{SEARXNG_URL}/", timeout=5)
    print(f"    [OK] Status code: {response.status_code}")
    print(f"    Content length: {len(response.content)} bytes")
    if 'searxng' in response.text.lower():
        print(f"    [OK] Appears to be SearXNG")
except requests.exceptions.Timeout:
    print(f"    [FAIL] Request timed out - service not responding")
except requests.exceptions.ConnectionError as e:
    print(f"    [FAIL] Connection error: {e}")
except Exception as e:
    print(f"    [ERROR] {e}")

# Test 3: Search Endpoint
print(f"\n[3] Testing search endpoint...")
try:
    params = {"q": "test", "format": "json"}
    response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=5)
    print(f"    [OK] Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"    [OK] Got {len(results)} results")
        if results:
            print(f"    Sample: {results[0].get('title', 'N/A')[:50]}")
    else:
        print(f"    [WARN] Unexpected status code")
except requests.exceptions.Timeout:
    print(f"    [FAIL] Search request timed out")
except Exception as e:
    print(f"    [ERROR] {e}")

# Summary
print("\n" + "=" * 70)
print("DIAGNOSIS SUMMARY")
print("=" * 70)
print("\nIssue: Port is open but HTTP service not responding")
print("\nPossible causes:")
print("  1. SearXNG service not started")
print("  2. Service crashed or in error state")
print("  3. Configuration issue (wrong port binding)")
print("  4. Reverse proxy misconfiguration")
print("\nSuggested actions:")
print(f"  - Access http://{SEARXNG_HOST}:{SEARXNG_PORT} in a web browser")
print(f"  - Check server logs on {SEARXNG_HOST}")
print(f"  - If you have access, SSH to {SEARXNG_HOST} and run:")
print(f"      docker ps | grep searxng")
print(f"      docker logs searxng")
print(f"  - Or use the current Selenium fallback (already configured)")
print("=" * 70)
