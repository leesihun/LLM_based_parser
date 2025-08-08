# Tavily API Proxy Configuration Guide

## Problem
You're getting "max retries exceeded with url" errors when trying to access Tavily API due to corporate proxy settings.

## Solutions

### Option 1: Quick Test (Recommended)
Use the simple configuration-based tester:

```bash
python test_tavily_with_config.py
```

This will:
1. Auto-create a configuration file if it doesn't exist
2. Guide you through proxy setup
3. Test the connection step by step

### Option 2: Manual Proxy Configuration

#### Step 1: Find Your Proxy Settings
Ask your IT department or check your browser settings for:
- Proxy host (e.g., `proxy.company.com`)
- Proxy port (e.g., `8080`, `3128`, `8888`)
- Username/password (if required)

#### Step 2: Edit proxy_config.json
```json
{
  "proxy_settings": {
    "enabled": true,
    "http": "http://proxy.company.com:8080",
    "https": "http://proxy.company.com:8080",
    "username": "your_username",
    "password": "your_password"
  }
}
```

#### Step 3: Run the Test
```bash
python test_tavily_with_config.py
```

### Option 3: Interactive Setup
For a guided setup experience:

```bash
python test_tavily_simple.py
```

This will ask you for proxy settings interactively.

### Option 4: Environment Variables
Set proxy environment variables (Windows):
```cmd
set HTTP_PROXY=http://proxy.company.com:8080
set HTTPS_PROXY=http://proxy.company.com:8080
```

Or with authentication:
```cmd
set HTTP_PROXY=http://username:password@proxy.company.com:8080
set HTTPS_PROXY=http://username:password@proxy.company.com:8080
```

Then run:
```bash
python test_tavily.py
```

## Common Corporate Proxy Ports
- 8080 (most common)
- 3128
- 8888
- 80
- 443

## Troubleshooting

### Error: "ProxyError"
- Check proxy host and port
- Verify proxy is accessible from your network
- Try different proxy servers if your company has multiple

### Error: "Authentication Required"
- Add username/password to proxy URL
- Check if your credentials are correct
- Some proxies use domain\username format

### Error: "SSL Certificate"
- Your company might be using SSL inspection
- Try HTTP instead of HTTPS for proxy URL
- Contact IT about certificate issues

### Error: "Connection Timeout"
- Increase timeout in configuration
- Check if proxy allows HTTPS connections
- Try different proxy ports

## Testing Steps

1. **Basic Connectivity Test**
   ```bash
   python test_tavily_with_config.py
   ```
   This tests basic internet access first

2. **Proxy Validation**
   The script will test multiple URLs to validate proxy settings

3. **Tavily API Test**
   Finally tests the actual Tavily API with your configuration

## Integration into Main Application

Once you find working proxy settings:

1. Update your main application's requests configuration
2. Use the same proxy settings for all HTTP requests
3. Consider implementing retry logic for network failures

Example integration:
```python
import requests

# Your working proxy configuration
proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'http://proxy.company.com:8080'
}

session = requests.Session()
session.proxies.update(proxies)

# Use this session for all Tavily API calls
response = session.post('https://api.tavily.com/search', json=payload)
```

## Need Help?

If you're still having issues:
1. Run `python test_tavily_with_config.py` and share the output
2. Check with your IT department about:
   - Proxy server details
   - Required authentication method
   - Any firewall rules blocking external APIs
   - SSL/TLS inspection policies

## Files Created
- `test_tavily_simple.py` - Interactive proxy setup
- `test_tavily_with_config.py` - Configuration-based testing
- `proxy_config.json` - Proxy configuration file
- `test_tavily.py` - Comprehensive testing (updated with proxy support)
