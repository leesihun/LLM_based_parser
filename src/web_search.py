#!/usr/bin/env python3
"""
Web Search System for HE team LLM assistant
Provides internet search capabilities using DuckDuckGo
"""

import requests
import json
import time
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
import logging

class WebSearcher:
    """Web search functionality using DuckDuckGo"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize web searcher with configuration"""
        self.config = config or {}
        self.max_results = self.config.get('max_results', 5)
        self.timeout = self.config.get('timeout', 10)
        self.user_agent = self.config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not query or not query.strip():
            return []
        
        max_results = max_results or self.max_results
        
        try:
            # First, get a token from DuckDuckGo
            token_url = "https://duckduckgo.com/"
            token_response = self.session.get(token_url, timeout=self.timeout)
            
            # Extract vqd token (needed for API calls)
            vqd_token = self._extract_vqd_token(token_response.text, query)
            if not vqd_token:
                self.logger.warning("Could not extract VQD token")
                return self._fallback_search(query, max_results)
            
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
                self.logger.warning(f"Search request failed with status {search_response.status_code}")
                return self._fallback_search(query, max_results)
                
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return self._fallback_search(query, max_results)
    
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
