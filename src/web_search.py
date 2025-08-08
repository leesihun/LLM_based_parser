#!/usr/bin/env python3
"""
Web Search System for HE team LLM assistant
Provides internet search capabilities using multiple search providers
"""

import requests
import json
import time
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus, urlencode
import logging
import re
from html.parser import HTMLParser
import html

class WebSearcher:
    """Web search functionality using multiple search providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize web searcher with configuration"""
        self.config = config or {}
        self.max_results = self.config.get('max_results', 5)
        self.timeout = self.config.get('timeout', 10)
        self.user_agent = self.config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Search providers in order of preference
        self.providers = self.config.get('providers', ['duckduckgo', 'bing', 'google_custom', 'manual'])
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Search the web using multiple providers as fallbacks
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []
        
        max_results = max_results or self.max_results
        
        # Try each provider in order until one works
        for provider in self.providers:
            try:
                self.logger.info(f"Trying search provider: {provider}")
                
                if provider == 'duckduckgo':
                    results = self._search_duckduckgo(query, max_results)
                elif provider == 'bing':
                    results = self._search_bing(query, max_results)
                elif provider == 'google_custom':
                    results = self._search_google_custom(query, max_results)
                elif provider == 'manual':
                    results = self._manual_search_fallback(query, max_results)
                else:
                    continue
                
                if results:
                    self.logger.info(f"Successfully got {len(results)} results from {provider}")
                    return results
                    
            except Exception as e:
                self.logger.warning(f"Provider {provider} failed: {str(e)}")
                continue
        
        # If all providers fail, return a helpful message
        return [{
            'title': 'Search Unavailable',
            'snippet': f'Unable to perform web search for: {query}. All search providers are currently unavailable. This might be due to network restrictions, firewall settings, or provider limitations.',
            'url': '',
            'source': 'System'
        }]
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search using DuckDuckGo"""
        try:
            # First, get a token from DuckDuckGo
            token_url = "https://duckduckgo.com/"
            token_response = self.session.get(token_url, timeout=self.timeout)
            
            # Extract vqd token (needed for API calls)
            vqd_token = self._extract_vqd_token(token_response.text, query)
            if not vqd_token:
                # Try HTML search as fallback
                return self._duckduckgo_html_search(query, max_results)
            
            # Perform the actual search
            search_url = "https://links.duckduckgo.com/d.js"
            params = {
                'q': query,
                'vqd': vqd_token,
                'kl': 'us-en',
                'l': 'us-en',
                'p': '',
                's': '0',
                'df': '',
                'ex': '-1'
            }
            
            search_response = self.session.get(search_url, params=params, timeout=self.timeout)
            
            if search_response.status_code == 200:
                return self._parse_duckduckgo_results(search_response.text, max_results)
            else:
                # Try HTML search as fallback
                return self._duckduckgo_html_search(query, max_results)
                
        except Exception as e:
            self.logger.error(f"DuckDuckGo search error: {str(e)}")
            return []
    
    def _search_bing(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search using Bing (no API key required)"""
        try:
            search_url = "https://www.bing.com/search"
            params = {
                'q': query,
                'count': max_results,
                'first': 0,
                'FORM': 'PERE'
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return self._parse_bing_results(response.text, max_results)
                
        except Exception as e:
            self.logger.error(f"Bing search error: {str(e)}")
        
        return []
    
    def _search_google_custom(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search using Google Custom Search (requires API key)"""
        try:
            api_key = self.config.get('google_api_key')
            search_engine_id = self.config.get('google_search_engine_id')
            
            if not api_key:
                self.logger.warning("Google Custom Search requires API key")
                return []
            
            if not search_engine_id:
                self.logger.warning("Google Custom Search requires search engine ID - see setup instructions")
                return []
            
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': min(max_results, 10),  # Google allows max 10 per request
                'safe': 'medium',  # Safe search
                'lr': 'lang_en'    # English results
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                results = self._parse_google_results(data, max_results)
                
                if results:
                    self.logger.info(f"Google Custom Search returned {len(results)} results")
                    return results
                else:
                    self.logger.warning("Google Custom Search returned no results")
                    return []
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                self.logger.error(f"Google Custom Search API error: {error_msg}")
                return []
                
        except Exception as e:
            self.logger.error(f"Google Custom Search error: {str(e)}")
        
        return []
    
    def _manual_search_fallback(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Manual fallback with helpful suggestions"""
        return [{
            'title': 'Manual Search Required',
            'snippet': f'Automated search is currently unavailable. Please manually search for: "{query}" using your preferred search engine. You can try: 1) Check your internet connection, 2) Verify firewall settings allow web requests, 3) Try again later if services are temporarily down.',
            'url': f'https://www.google.com/search?q={quote_plus(query)}',
            'source': 'Manual Fallback'
        }]
    
    def _duckduckgo_html_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """DuckDuckGo HTML search as fallback"""
        try:
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return self._parse_html_results(response.text, max_results)
                
        except Exception as e:
            self.logger.error(f"DuckDuckGo HTML search error: {str(e)}")
        
        return []
    
    def _extract_vqd_token(self, html_content: str, query: str) -> Optional[str]:
        """Extract VQD token from DuckDuckGo homepage"""
        try:
            # Look for vqd token in the HTML
            import re
            vqd_match = re.search(r'vqd="([^"]+)"', html_content)
            if vqd_match:
                return vqd_match.group(1)
            
            # Alternative method - look in JavaScript
            js_match = re.search(r'vqd=([^&\s]+)', html_content)
            if js_match:
                return js_match.group(1)
                
        except Exception as e:
            self.logger.error(f"Error extracting VQD token: {str(e)}")
        
        return None
    
    def _parse_duckduckgo_results(self, response_text: str, max_results: int) -> List[Dict[str, str]]:
        """Parse DuckDuckGo search results"""
        results = []
        
        try:
            # DuckDuckGo returns JSONP, need to extract JSON
            if response_text.startswith('DDG.pageLayout.load.searchResults('):
                json_str = response_text[len('DDG.pageLayout.load.searchResults('):-2]
                data = json.loads(json_str)
                
                for item in data.get('results', [])[:max_results]:
                    result = {
                        'title': self._clean_text(item.get('t', '')),
                        'snippet': self._clean_text(item.get('a', '')),
                        'url': item.get('u', ''),
                        'source': 'DuckDuckGo'
                    }
                    if result['title'] and result['url']:
                        results.append(result)
                        
        except Exception as e:
            self.logger.error(f"Error parsing DuckDuckGo results: {str(e)}")
        
        return results
    
    def _parse_bing_results(self, html_content: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Bing search results from HTML"""
        results = []
        
        try:
            # Simple regex-based extraction for Bing results
            # Look for result containers
            result_pattern = r'<h2><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h2>.*?<p[^>]*>([^<]+)</p>'
            matches = re.findall(result_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for url, title, snippet in matches[:max_results]:
                if url.startswith('http') and not 'bing.com' in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': self._clean_text(snippet),
                        'url': url,
                        'source': 'Bing'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error parsing Bing results: {str(e)}")
        
        return results
    
    def _parse_google_results(self, json_data: dict, max_results: int) -> List[Dict[str, str]]:
        """Parse Google Custom Search results from JSON"""
        results = []
        
        try:
            items = json_data.get('items', [])
            
            for item in items[:max_results]:
                results.append({
                    'title': self._clean_text(item.get('title', '')),
                    'snippet': self._clean_text(item.get('snippet', '')),
                    'url': item.get('link', ''),
                    'source': 'Google'
                })
                
        except Exception as e:
            self.logger.error(f"Error parsing Google results: {str(e)}")
        
        return results
    
    def _fallback_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Fallback search method using HTML scraping"""
        try:
            # Simple DuckDuckGo HTML search as fallback
            search_url = f"https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return self._parse_html_results(response.text, max_results)
                
        except Exception as e:
            self.logger.error(f"Fallback search error: {str(e)}")
        
        # If all else fails, return a message indicating search unavailable
        return [{
            'title': 'Search Unavailable',
            'snippet': f'Unable to perform web search for: {query}. Please try again later.',
            'url': '',
            'source': 'System'
        }]
    
    def _parse_html_results(self, html_content: str, max_results: int) -> List[Dict[str, str]]:
        """Parse HTML search results"""
        results = []
        
        try:
            from html.parser import HTMLParser
            import re
            
            # Simple regex-based extraction for basic results
            # Look for result links and snippets
            link_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<div[^>]*class="[^"]*snippet[^"]*"[^>]*>([^<]+)</div>'
            
            links = re.findall(link_pattern, html_content)
            snippets = re.findall(snippet_pattern, html_content)
            
            for i, (url, title) in enumerate(links[:max_results]):
                if url.startswith('http') and not url.startswith('https://duckduckgo.com'):
                    snippet = snippets[i] if i < len(snippets) else ''
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': self._clean_text(snippet),
                        'url': url,
                        'source': 'DuckDuckGo'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error parsing HTML results: {str(e)}")
        
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ''
        
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Search and format results for LLM context
        
        Args:
            query: Search query
            max_results: Maximum results to include
            
        Returns:
            Formatted search results as context string
        """
        results = self.search(query, max_results)
        
        if not results:
            return f"No search results found for: {query}"
        
        context = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            context += f"{i}. **{result['title']}**\n"
            if result['snippet']:
                context += f"   {result['snippet']}\n"
            if result['url']:
                context += f"   Source: {result['url']}\n"
            context += "\n"
        
        return context
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()

# Example usage and testing
if __name__ == "__main__":
    searcher = WebSearcher()
    
    # Test search
    query = "Python programming best practices"
    results = searcher.search(query, max_results=3)
    
    print(f"Search results for: {query}")
    print("=" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet']}")
        print(f"   {result['url']}")
        print()
    
    # Test context formatting
    context = searcher.search_with_context(query, max_results=3)
    print("Context format:")
    print("=" * 50)
    print(context)
    
    searcher.close()
