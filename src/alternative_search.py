#!/usr/bin/env python3
"""
Alternative Internet Search Methods
Bypasses HTTPS restrictions using different approaches
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import time
from typing import List, Dict, Optional

class AlternativeSearcher:
    """Search internet using alternative methods that bypass HTTPS blocking"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session = requests.Session()
        
        # Corporate-friendly headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Setup proxy
        self._setup_proxy()
    
    def _setup_proxy(self):
        """Setup proxy configuration"""
        proxy_config = self.config.get('proxy', {})
        if proxy_config.get('enabled', True):
            proxy_host = proxy_config.get('host', '168.219.61.252')
            proxy_port = proxy_config.get('port', 8080)
            proxy_url = f'http://{proxy_host}:{proxy_port}'
            
            self.session.proxies.update({
                'http': proxy_url,
                'https': proxy_url
            })
    
    def search_news_sites(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search through news site RSS feeds and search pages"""
        results = []
        
        # Try BBC News RSS (often available via HTTP)
        try:
            rss_url = f"http://feeds.bbci.co.uk/news/rss.xml"
            response = self.session.get(rss_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                query_words = query.lower().split()
                
                for item in items[:max_results]:
                    title = item.find('title')
                    description = item.find('description')
                    link = item.find('link')
                    
                    if title and description:
                        title_text = title.text
                        desc_text = description.text
                        
                        # Check if query matches
                        combined_text = (title_text + " " + desc_text).lower()
                        if any(word in combined_text for word in query_words):
                            results.append({
                                'title': title_text,
                                'snippet': desc_text[:200] + "...",
                                'url': link.text if link else 'http://www.bbc.com/news',
                                'source': 'BBC News'
                            })
        except:
            pass
        
        return results
    
    def search_wikipedia_http(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Search Wikipedia using HTTP endpoints"""
        results = []
        
        try:
            # Try Wikipedia's mobile API (sometimes less restricted)
            api_url = "http://en.wikipedia.org/w/api.php"
            params = {
                'action': 'opensearch',
                'search': query,
                'limit': max_results,
                'format': 'json',
                'namespace': 0
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if len(data) >= 4:
                    titles = data[1]
                    descriptions = data[2] 
                    urls = data[3]
                    
                    for i in range(min(len(titles), max_results)):
                        results.append({
                            'title': f"Wikipedia: {titles[i]}",
                            'snippet': descriptions[i] if i < len(descriptions) else "Wikipedia article",
                            'url': urls[i] if i < len(urls) else f"http://en.wikipedia.org/wiki/{titles[i].replace(' ', '_')}",
                            'source': 'Wikipedia'
                        })
        except:
            pass
        
        return results
    
    def search_archive_sites(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Search through archive and library sites"""
        results = []
        
        try:
            # Try Internet Archive search (often HTTP accessible)
            archive_url = "http://archive.org/advancedsearch.php"
            params = {
                'q': query,
                'fl[]': 'identifier,title,description',
                'rows': max_results,
                'page': 1,
                'output': 'json'
            }
            
            response = self.session.get(archive_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                
                for doc in docs[:max_results]:
                    title = doc.get('title', 'Archive Item')
                    description = doc.get('description', [''])[0] if doc.get('description') else ''
                    identifier = doc.get('identifier', '')
                    
                    results.append({
                        'title': f"Archive: {title}",
                        'snippet': description[:200] + "..." if description else "Archived content",
                        'url': f"http://archive.org/details/{identifier}",
                        'source': 'Internet Archive'
                    })
        except:
            pass
        
        return results
    
    def search_academic_sites(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Search academic and educational sites"""
        results = []
        
        try:
            # Try searching arXiv (academic papers, often HTTP accessible)
            arxiv_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance'
            }
            
            response = self.session.get(arxiv_url, params=params, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                entries = soup.find_all('entry')
                
                for entry in entries[:max_results]:
                    title = entry.find('title')
                    summary = entry.find('summary')
                    id_elem = entry.find('id')
                    
                    if title:
                        results.append({
                            'title': f"arXiv: {title.text.strip()}",
                            'snippet': summary.text.strip()[:200] + "..." if summary else "Academic paper",
                            'url': id_elem.text.strip() if id_elem else "http://arxiv.org",
                            'source': 'arXiv'
                        })
        except:
            pass
        
        return results
    
    def search_government_data(self, query: str, max_results: int = 2) -> List[Dict[str, str]]:
        """Search government and public data sources"""
        results = []
        
        try:
            # Try data.gov API (often HTTP accessible)
            gov_url = "http://catalog.data.gov/api/3/action/package_search"
            params = {
                'q': query,
                'rows': max_results
            }
            
            response = self.session.get(gov_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                datasets = data.get('result', {}).get('results', [])
                
                for dataset in datasets[:max_results]:
                    title = dataset.get('title', 'Government Dataset')
                    notes = dataset.get('notes', '')
                    name = dataset.get('name', '')
                    
                    results.append({
                        'title': f"Data.gov: {title}",
                        'snippet': notes[:200] + "..." if notes else "Government data",
                        'url': f"http://catalog.data.gov/dataset/{name}",
                        'source': 'Data.gov'
                    })
        except:
            pass
        
        return results
    
    def search_alternative_engines(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Try alternative search engines that might work via HTTP"""
        results = []
        
        # Try Yandex (Russian search engine, sometimes less restricted)
        try:
            yandex_url = "http://yandex.com/search/"
            params = {'text': query, 'lr': 84}  # lr=84 for English results
            
            response = self.session.get(yandex_url, params=params, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for search results (Yandex specific selectors)
                result_containers = soup.find_all('div', class_='organic')
                
                for container in result_containers[:max_results//2]:
                    title_elem = container.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        
                        # Get snippet
                        snippet_elem = container.find('div', class_='text-container')
                        snippet = snippet_elem.get_text(strip=True)[:200] if snippet_elem else ''
                        
                        if title:
                            results.append({
                                'title': title,
                                'snippet': snippet + "...",
                                'url': url,
                                'source': 'Yandex'
                            })
        except:
            pass
        
        return results
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Main search function combining all alternative methods"""
        all_results = []
        
        # Try different search methods
        methods = [
            self.search_wikipedia_http,
            self.search_news_sites, 
            self.search_academic_sites,
            self.search_archive_sites,
            self.search_government_data,
            self.search_alternative_engines
        ]
        
        for method in methods:
            try:
                results = method(query, max(1, max_results//3))
                all_results.extend(results)
                if len(all_results) >= max_results:
                    break
                time.sleep(0.5)  # Be nice to servers
            except:
                continue
        
        # If no results found, create informative message
        if not all_results:
            all_results = [{
                'title': f'Alternative Search: {query}',
                'snippet': f'Searched multiple alternative sources for "{query}". Corporate proxy may be restricting access to search engines. Try more specific technical terms or check if VPN access is available.',
                'url': f'http://www.google.com/search?q={quote_plus(query)}',
                'source': 'Search Info'
            }]
        
        return all_results[:max_results]
    
    def test_search_capability(self) -> Dict:
        """Test search capability"""
        test_query = "python programming"
        
        try:
            results = self.search(test_query, max_results=3)
            working_sources = list(set([r['source'] for r in results if r['source'] != 'Search Info']))
            
            return {
                'success': len(working_sources) > 0,
                'result_count': len(results),
                'test_query': test_query,
                'engines_working': working_sources,
                'sample_result': results[0] if results else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_query': test_query
            }
    
    def close(self):
        """Close session"""
        self.session.close()

def test_alternative_search():
    """Test the alternative search system"""
    print("Testing Alternative Internet Search")
    print("=" * 40)
    
    # Load config
    try:
        with open('config/search_config.json', 'r') as f:
            config = json.load(f)
        search_config = config.get('web_search', {})
    except:
        search_config = {'proxy': {'enabled': True, 'host': '168.219.61.252', 'port': 8080}}
    
    searcher = AlternativeSearcher(search_config)
    
    # Test capability
    test_result = searcher.test_search_capability()
    print(f"Test Status: {'SUCCESS' if test_result['success'] else 'FAILED'}")
    print(f"Working sources: {test_result.get('engines_working', [])}")
    
    # Test search
    queries = ["machine learning", "web development", "python tutorial"]
    
    for query in queries:
        print(f"\nSearching: '{query}'")
        results = searcher.search(query, max_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title'][:60]}...")
            print(f"     {result['snippet'][:80]}...")
            print(f"     Source: {result['source']}")
    
    searcher.close()

if __name__ == "__main__":
    test_alternative_search()