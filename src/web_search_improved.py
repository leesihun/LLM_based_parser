#!/usr/bin/env python3
"""
Improved Web Search System
Uses the most reliable free search APIs and methods
"""

import requests
import json
import re
import time
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
import logging

class ImprovedWebSearcher:
    """Improved web searcher using reliable free APIs"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration"""
        self.config = config or {}
        self.max_results = self.config.get('max_results', 5)
        self.timeout = self.config.get('timeout', 15)
        
        # Session with better headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Search providers in order of reliability
        self.providers = [
            ('wikipedia', self._search_wikipedia),
            ('reddit', self._search_reddit),
            ('github', self._search_github),
            ('stackoverflow', self._search_stackoverflow),
            ('searx', self._search_searx),
            ('duckduckgo_instant', self._search_duckduckgo_instant),
            ('yahoo_html', self._search_yahoo_html),
            ('bing_html', self._search_bing_html),
            ('startpage_html', self._search_startpage_html),
            ('manual_fallback', self._manual_fallback)
        ]
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """Search using multiple providers with fallbacks"""
        if not query or not query.strip():
            return []
        
        max_results = max_results or self.max_results
        all_results = []
        
        # Try each provider
        for provider_name, provider_func in self.providers:
            try:
                self.logger.info(f"Trying provider: {provider_name}")
                results = provider_func(query, max_results)
                
                if results:
                    self.logger.info(f"Got {len(results)} results from {provider_name}")
                    all_results.extend(results)
                    
                    # If we have enough results, stop
                    if len(all_results) >= max_results:
                        break
                        
            except Exception as e:
                self.logger.warning(f"Provider {provider_name} failed: {str(e)}")
                continue
        
        # Remove duplicates and limit results
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
                
                if len(unique_results) >= max_results:
                    break
        
        return unique_results or self._emergency_fallback(query)
    
    def _search_wikipedia(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Wikipedia API"""
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/search"
            params = {'q': query, 'limit': min(max_results, 10)}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for page in data.get('pages', []):
                    results.append({
                        'title': f"Wikipedia: {page.get('title', '')}",
                        'snippet': page.get('description', ''),
                        'url': f"https://en.wikipedia.org/wiki/{page.get('key', '')}",
                        'source': 'Wikipedia'
                    })
                
                return results
        except Exception as e:
            self.logger.error(f"Wikipedia search error: {e}")
        
        return []
    
    def _search_reddit(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Reddit API"""
        try:
            url = "https://www.reddit.com/search.json"
            params = {
                'q': query,
                'limit': min(max_results, 25),
                'sort': 'relevance'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    title = post_data.get('title', '')
                    
                    if title:
                        results.append({
                            'title': f"Reddit: {title}",
                            'snippet': post_data.get('selftext', '')[:150] + '...' if post_data.get('selftext') else f"r/{post_data.get('subreddit', '')}",
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'source': 'Reddit'
                        })
                
                return results[:max_results]
        except Exception as e:
            self.logger.error(f"Reddit search error: {e}")
        
        return []
    
    def _search_github(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search GitHub API"""
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': min(max_results, 30)
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for repo in data.get('items', []):
                    results.append({
                        'title': f"GitHub: {repo.get('full_name', '')}",
                        'snippet': repo.get('description', '') or f"⭐ {repo.get('stargazers_count', 0)} stars",
                        'url': repo.get('html_url', ''),
                        'source': 'GitHub'
                    })
                
                return results[:max_results]
        except Exception as e:
            self.logger.error(f"GitHub search error: {e}")
        
        return []
    
    def _search_stackoverflow(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Stack Overflow API"""
        try:
            url = "https://api.stackexchange.com/2.3/search"
            params = {
                'order': 'desc',
                'sort': 'relevance',
                'intitle': query,
                'site': 'stackoverflow',
                'pagesize': min(max_results, 30)
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for question in data.get('items', []):
                    results.append({
                        'title': f"Stack Overflow: {question.get('title', '')}",
                        'snippet': f"Score: {question.get('score', 0)} | Views: {question.get('view_count', 0)} | Answers: {question.get('answer_count', 0)}",
                        'url': question.get('link', ''),
                        'source': 'Stack Overflow'
                    })
                
                return results[:max_results]
        except Exception as e:
            self.logger.error(f"Stack Overflow search error: {e}")
        
        return []
    
    def _search_searx(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search using Searx public instances"""
        searx_instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.xyz",
            "https://searx.prvcy.eu",
            "https://searx.tiekoetter.com"
        ]
        
        for instance in searx_instances:
            try:
                url = f"{instance}/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'engines': 'google,bing,duckduckgo'
                }
                
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get('results', []):
                        results.append({
                            'title': result.get('title', ''),
                            'snippet': result.get('content', ''),
                            'url': result.get('url', ''),
                            'source': f'Searx ({instance})'
                        })
                    
                    if results:
                        return results[:max_results]
                        
            except Exception as e:
                self.logger.warning(f"Searx instance {instance} failed: {e}")
                continue
        
        return []
    
    def _search_duckduckgo_instant(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo Instant Answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_redirect': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Abstract answer
                if data.get('Abstract'):
                    results.append({
                        'title': f"DuckDuckGo: {data.get('Heading', 'Answer')}",
                        'snippet': data.get('Abstract', ''),
                        'url': data.get('AbstractURL', ''),
                        'source': 'DuckDuckGo'
                    })
                
                # Related topics
                for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:60] + '...',
                            'snippet': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'source': 'DuckDuckGo'
                        })
                
                return results[:max_results]
        except Exception as e:
            self.logger.error(f"DuckDuckGo instant search error: {e}")
        
        return []
    
    def _search_yahoo_html(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Yahoo with HTML parsing"""
        try:
            url = "https://search.yahoo.com/search"
            params = {'p': query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return self._parse_yahoo_results(response.text, max_results)
        except Exception as e:
            self.logger.error(f"Yahoo HTML search error: {e}")
        
        return []
    
    def _search_bing_html(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Bing with HTML parsing"""
        try:
            url = "https://www.bing.com/search"
            params = {'q': query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return self._parse_bing_results(response.text, max_results)
        except Exception as e:
            self.logger.error(f"Bing HTML search error: {e}")
        
        return []
    
    def _search_startpage_html(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search Startpage with HTML parsing"""
        try:
            url = "https://www.startpage.com/sp/search"
            params = {'query': query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return self._parse_startpage_results(response.text, max_results)
        except Exception as e:
            self.logger.error(f"Startpage HTML search error: {e}")
        
        return []
    
    def _parse_yahoo_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Yahoo search results"""
        results = []
        try:
            # Yahoo result pattern
            pattern = r'<h3[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http') and 'yahoo.com' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Yahoo'
                    })
        except Exception as e:
            self.logger.error(f"Yahoo parsing error: {e}")
        
        return results
    
    def _parse_bing_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Bing search results"""
        results = []
        try:
            # Bing result pattern
            pattern = r'<h2><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h2>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http') and 'bing.com' not in url:
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Bing'
                    })
        except Exception as e:
            self.logger.error(f"Bing parsing error: {e}")
        
        return results
    
    def _parse_startpage_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse Startpage search results"""
        results = []
        try:
            # Startpage result pattern
            pattern = r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*w-gl-title[^"]*"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            for url, title in matches[:max_results]:
                if url.startswith('http'):
                    results.append({
                        'title': self._clean_text(title),
                        'snippet': '',
                        'url': url,
                        'source': 'Startpage'
                    })
        except Exception as e:
            self.logger.error(f"Startpage parsing error: {e}")
        
        return results
    
    def _manual_fallback(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Manual fallback with search engine links"""
        return [{
            'title': 'Manual Search Required',
            'snippet': f'Automated search failed. Click to search manually for: "{query}"',
            'url': f'https://www.google.com/search?q={quote_plus(query)}',
            'source': 'Manual'
        }, {
            'title': 'Alternative Search - Bing',
            'snippet': f'Try Bing search for: "{query}"',
            'url': f'https://www.bing.com/search?q={quote_plus(query)}',
            'source': 'Manual'
        }, {
            'title': 'Alternative Search - DuckDuckGo',
            'snippet': f'Try DuckDuckGo search for: "{query}"',
            'url': f'https://duckduckgo.com/?q={quote_plus(query)}',
            'source': 'Manual'
        }]
    
    def _emergency_fallback(self, query: str) -> List[Dict[str, str]]:
        """Emergency fallback when all providers fail"""
        return [{
            'title': 'Search Unavailable',
            'snippet': f'All search providers failed for: "{query}". This may be due to network restrictions, firewall settings, or temporary service issues. Try checking your internet connection or running the diagnostic tool.',
            'url': f'https://www.google.com/search?q={quote_plus(query)}',
            'source': 'System'
        }]
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML text"""
        if not text:
            return ''
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def search_with_context(self, query: str, max_results: Optional[int] = None) -> str:
        """Search and format results for LLM context"""
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
            context += f"   Provider: {result.get('source', 'Unknown')}\n\n"
        
        return context
    
    def close(self):
        """Close the session"""
        self.session.close()

# Example usage
if __name__ == "__main__":
    searcher = ImprovedWebSearcher()
    
    query = "Python web scraping tutorial"
    print(f"Searching for: {query}")
    print("=" * 50)
    
    results = searcher.search(query, max_results=5)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet']}")
        print(f"   {result['url']}")
        print(f"   Source: {result['source']}")
        print()
    
    searcher.close()
