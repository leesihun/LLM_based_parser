# Working proxy configuration based on test results
import requests

def create_working_session():
    """Create a working session based on successful proxy tests"""
    session = requests.Session()
    
    # Based on your test results, use:
    # No authentication needed
    session.proxies = {
        'http': 'http://168.219.61.252:8080',
        'https': 'http://168.219.61.252:8080'
    }
    
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