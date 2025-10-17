# Web Search Troubleshooting Guide - Corporate Proxy Environments

This guide helps diagnose and fix web search issues in corporate proxy environments.

## Quick Diagnosis

Run these scripts in order to identify the problem:

### 1. Basic Web Search Test (Python)
```bash
python test_websearch_proxy.py
```

This will check:
- ✅ Proxy environment variables
- ✅ Node.js installation
- ✅ TypeScript bridge functionality
- ✅ Complete search pipeline

### 2. Simple Node.js Test
```bash
cd websearch_ts
node test_search_simple.js "python programming"
```

This runs a minimal DuckDuckGo search to isolate Node.js issues.

### 3. Comprehensive Proxy Test
```bash
cd websearch_ts
node debug_proxy_test.js
```

This runs extensive diagnostics:
- Proxy environment detection
- DNS resolution tests
- Network connectivity checks
- Multiple header configurations
- Saves HTML responses for inspection

## Common Issues and Solutions

### Issue 1: "No results returned" (0 results)

**Symptoms:**
- Search executes but returns 0 results
- No error messages
- TypeScript bridge works

**Causes:**
1. **Missing User-Agent header** ✅ (Fixed in search.js)
2. **Corporate firewall blocking search engines**
3. **Proxy not configured for Node.js**
4. **SSL certificate interception**

**Solutions:**

#### A. Check if DuckDuckGo is accessible
```bash
# Windows CMD
curl https://html.duckduckgo.com/html/?q=test

# PowerShell
Invoke-WebRequest https://html.duckduckgo.com/html/?q=test
```

If this fails, DuckDuckGo is blocked by your network.

#### B. Configure proxy for Node.js
```bash
# Windows CMD
set HTTP_PROXY=http://proxy.company.com:8080
set HTTPS_PROXY=http://proxy.company.com:8080

# PowerShell
$env:HTTP_PROXY='http://proxy.company.com:8080'
$env:HTTPS_PROXY='http://proxy.company.com:8080'
```

Replace `proxy.company.com:8080` with your actual proxy address.

#### C. Handle SSL certificate interception
If your company uses SSL interception (proxy rewrites HTTPS certificates):

**Temporary fix (testing only):**
```bash
# Windows CMD
set NODE_TLS_REJECT_UNAUTHORIZED=0

# PowerShell
$env:NODE_TLS_REJECT_UNAUTHORIZED='0'
```

**⚠️ WARNING:** Only use this for testing! Don't use in production.

**Proper fix:**
1. Get your company's root CA certificate
2. Add it to Node.js trusted certificates:
```bash
set NODE_EXTRA_CA_CERTS=C:\path\to\company-root-ca.crt
```

### Issue 2: "Connection refused" or "ECONNREFUSED"

**Cause:** Firewall blocking outbound connections from Node.js

**Solutions:**
1. Check Windows Firewall settings for Node.js
2. Contact IT to whitelist Node.js
3. Use API-based providers (don't require HTML scraping)

### Issue 3: "Timeout" or "ETIMEDOUT"

**Causes:**
- Slow proxy connection
- Rate limiting
- Network congestion

**Solutions:**
1. Increase timeout in config.json:
```json
{
  "web_search": {
    "timeout": 60
  }
}
```

2. Add delays between requests (already configured in search.js)

3. Use caching to reduce requests:
```json
{
  "web_search": {
    "cache": {
      "enabled": true,
      "default_ttl": 3600
    }
  }
}
```

### Issue 4: "DNS lookup failed" or "ENOTFOUND"

**Cause:** DNS resolution issues with proxy

**Solutions:**
1. Check DNS settings:
```bash
nslookup html.duckduckgo.com
```

2. Set proxy to resolve DNS:
```bash
set HTTP_PROXY=http://proxy.company.com:8080
set NO_PROXY=""
```

3. Use IP address instead of domain (if allowed)

## Alternative: Use API-Based Providers

If HTML scraping doesn't work through your proxy, use API providers:

### Brave Search API (Recommended)
1. Sign up: https://brave.com/search/api/
2. Get API key (free tier: 2,000 queries/month)
3. Add to config.json:
```json
{
  "web_search": {
    "default_provider": "brave_api",
    "brave_api_key": "YOUR_API_KEY_HERE",
    "providers": {
      "brave_api": {"enabled": true}
    }
  }
}
```

### Tavily API
1. Sign up: https://tavily.com/
2. Add to config.json:
```json
{
  "web_search": {
    "default_provider": "tavily_api",
    "tavily_api_key": "YOUR_API_KEY_HERE",
    "providers": {
      "tavily_api": {"enabled": true}
    }
  }
}
```

### Exa API
1. Sign up: https://exa.ai/
2. Add to config.json:
```json
{
  "web_search": {
    "default_provider": "exa_api",
    "exa_api_key": "YOUR_API_KEY_HERE",
    "providers": {
      "exa_api": {"enabled": true}
    }
  }
}
```

## Debug Scripts Reference

### debug_proxy_test.js
Comprehensive proxy diagnostics:
- Detects proxy environment variables
- Tests DNS resolution
- Tests basic connectivity to multiple sites
- Tests DuckDuckGo with different header configurations
- Saves HTML responses for inspection
- Identifies blocking patterns (CAPTCHA, access denied, etc.)

**Output files:**
- `debug_ddg_with_user-agent.html` - Response with User-Agent header
- `debug_ddg_with_full_headers.html` - Response with all headers
- `debug_ddg_no_headers.html` - Response without headers

### test_search_simple.js
Minimal DuckDuckGo search test:
- Quick test with minimal code
- Good for isolating Node.js issues
- Provides specific error hints

**Usage:**
```bash
node test_search_simple.js "your query here"
```

### test_websearch_proxy.py
Complete Python integration test:
- Tests full pipeline: Python → TypeScript → DuckDuckGo
- Checks Node.js installation
- Verifies all dependencies
- Tests SearchManager integration

## Checking Saved HTML Files

If searches return 0 results, check the saved HTML files:

### Expected DuckDuckGo response (working):
```html
<div class="results_links_deep">
  <a class="result__a" href="...">Result Title</a>
  <a class="result__snippet" href="...">Description text...</a>
</div>
```

### Blocked response (firewall):
```html
Access Denied
You don't have permission to access this resource
```

### CAPTCHA response (anti-bot):
```html
<form action="/captcha">
  Please verify you are human
</form>
```

### Proxy error response:
```html
Proxy Error
The proxy server could not handle the request
```

## Getting Help from IT

If you need to contact your IT department, provide:

1. **Error details:**
   - Run `node debug_proxy_test.js > debug_output.txt`
   - Send debug_output.txt to IT

2. **Requested access:**
   - Domain: `html.duckduckgo.com`
   - Port: 443 (HTTPS)
   - Application: Node.js web scraping for internal AI assistant

3. **Alternative:** Request approval for API providers (Brave, Tavily, Exa)

## Testing Checklist

Run through this checklist to diagnose issues:

- [ ] Can access DuckDuckGo from browser?
- [ ] Proxy environment variables set?
- [ ] Node.js installed and working?
- [ ] npm packages installed in websearch_ts?
- [ ] test_search_simple.js returns results?
- [ ] Firewall allows Node.js outbound connections?
- [ ] SSL certificates configured correctly?
- [ ] API keys configured (if using API providers)?

## Success Indicators

Search is working correctly when:

✅ `test_websearch_proxy.py` shows "Web search is working!"
✅ `test_search_simple.js` returns 3+ results
✅ `debug_proxy_test.js` shows "Found X results!" (where X > 0)
✅ Saved HTML files contain `<div class="results_links_deep">`

## Configuration Tips for Corporate Environments

### Recommended config.json settings:

```json
{
  "web_search": {
    "enabled": true,
    "use_typescript_search": true,
    "default_provider": "duckduckgo",

    "timeout": 60,
    "simple_mode": true,

    "cache": {
      "enabled": true,
      "default_ttl": 7200
    },

    "result_filtering": {
      "enabled": false
    },

    "providers": {
      "duckduckgo": {"enabled": true},
      "brave_api": {"enabled": false},
      "tavily_api": {"enabled": false}
    }
  }
}
```

Key settings explained:
- `timeout: 60` - Longer timeout for slow proxies
- `simple_mode: true` - Skip content enrichment (faster, fewer requests)
- `cache: enabled` - Reduce redundant network calls
- `result_filtering: false` - Don't filter results aggressively

## Still Not Working?

If you've tried everything and it still doesn't work:

1. **Check the basics:**
   ```bash
   # Can Node.js reach the internet at all?
   node -e "fetch('https://www.google.com').then(r => console.log('OK')).catch(e => console.log('FAILED:', e.message))"
   ```

2. **Try a different search engine:**
   - Edit `backend/config/config.json`
   - Change `"default_provider": "google"` (if HTML scraping works for Google)

3. **Use API providers:**
   - Brave API (recommended for corporate environments)
   - Tavily API
   - Exa API

4. **Disable web search temporarily:**
   ```json
   {
     "web_search": {
       "enabled": false
     }
   }
   ```
   The system will still work with RAG and file modes.

## Contact

If you continue to have issues, create a GitHub issue with:
- Output from `test_websearch_proxy.py`
- Output from `debug_proxy_test.js`
- Contents of one saved HTML file
- Your proxy configuration (redact sensitive info)
