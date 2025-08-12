#!/usr/bin/env python3
"""
Web Search Feature Integration
Integrates browser-based web search capability into the LLM system
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import search systems
try:
    from .selenium_search import SeleniumSearcher
    from .keyword_extractor import KeywordExtractor
except ImportError:
    from selenium_search import SeleniumSearcher
    from keyword_extractor import KeywordExtractor


class WebSearchFeature:
    """Web search feature for LLM integration"""
    
    def __init__(self, config: Optional[Dict] = None, llm_client=None):
        """Initialize web search feature"""
        self.config = config or {}
        self.searcher = SeleniumSearcher(config)
        self.enabled = True
        self.search_history = []
        
        # Initialize keyword extractor
        keyword_config = self.config.get('keyword_extraction', {})
        self.keyword_extractor = KeywordExtractor(keyword_config, llm_client)
        self.use_keyword_extraction = keyword_config.get('enabled', True)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Web Search Feature initialized with keyword extraction")
    
    def search_web(self, query: str, max_results: Optional[int] = None, 
                   format_for_llm: bool = True, use_keyword_extraction: Optional[bool] = None) -> Dict[str, Any]:
        """
        Perform web search and return formatted results
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            format_for_llm: Whether to format results for LLM consumption
            use_keyword_extraction: Override default keyword extraction setting
            
        Returns:
            Dictionary with search results and metadata
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Web search feature is disabled',
                'results': [],
                'query': query
            }
        
        if not query or not query.strip():
            return {
                'success': False,
                'error': 'Empty search query provided',
                'results': [],
                'query': query
            }
        
        try:
            # Determine if keyword extraction should be used
            extract_keywords = use_keyword_extraction if use_keyword_extraction is not None else self.use_keyword_extraction
            
            # Extract keywords and generate optimized queries if enabled
            original_query = query
            search_queries = []
            extraction_info = None
            
            if extract_keywords and self.keyword_extractor:
                try:
                    extraction_info = self.keyword_extractor.extract_keywords(query)
                    if extraction_info and extraction_info.get('adequate_keywords') and extraction_info.get('queries'):
                        search_queries = extraction_info['queries']
                        self.logger.info(f"Extracted {len(extraction_info.get('keywords', []))} adequate keywords from: {query}")
                        self.logger.info(f"Generated {len(search_queries)} optimized queries")
                    else:
                        reason = "no adequate keywords found" if not extraction_info.get('adequate_keywords') else "no queries generated"
                        self.logger.info(f"Keyword extraction failed: {reason}")
                        return {
                            'success': False,
                            'error': f'Cannot perform web search: {reason}. Query too generic or lacks searchable terms.',
                            'results': [],
                            'query': query,
                            'timestamp': datetime.now().isoformat(),
                            'extraction_info': extraction_info
                        }
                except Exception as e:
                    self.logger.error(f"Keyword extraction failed: {e}")
                    return {
                        'success': False,
                        'error': f'Keyword extraction failed: {str(e)}',
                        'results': [],
                        'query': query,
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                # If keyword extraction is disabled, use original query only
                search_queries = [query]
            
            # Try searching with optimized queries
            all_results = []
            successful_query = None
            
            for i, search_query in enumerate(search_queries):
                try:
                    self.logger.info(f"Searching web with query {i+1}/{len(search_queries)}: {search_query}")
                    results = self.searcher.search(search_query, max_results)
                    
                    if results:
                        all_results.extend(results)
                        successful_query = search_query
                        
                        # If we got good results from first query, we can stop
                        if len(results) >= (max_results or 5) // 2:
                            break
                            
                except Exception as e:
                    self.logger.warning(f"Search failed for query '{search_query}': {e}")
                    continue
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_results = []
            for result in all_results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # Limit to max_results
            if max_results and len(unique_results) > max_results:
                unique_results = unique_results[:max_results]
            
            results = unique_results
            
            # Log search in history
            search_entry = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'result_count': len(results),
                'success': len(results) > 0,
                'keyword_extraction_used': extract_keywords,
                'successful_query': successful_query if successful_query != query else None,
                'queries_tried': len(search_queries) if extract_keywords else 1
            }
            self.search_history.append(search_entry)
            
            # Keep only last 50 searches in history
            if len(self.search_history) > 50:
                self.search_history = self.search_history[-50:]
            
            search_result = {
                'success': True,
                'query': query,
                'results': results,
                'result_count': len(results),
                'timestamp': search_entry['timestamp'],
                'keyword_extraction_used': extract_keywords,
                'extraction_info': extraction_info,
                'successful_query': successful_query,
                'queries_tried': search_queries if extract_keywords else [query]
            }
            
            # Add formatted context if requested
            if format_for_llm:
                search_result['formatted_context'] = self._format_for_llm(query, results)
            
            self.logger.info(f"Web search completed: {len(results)} results found")
            return search_result
            
        except Exception as e:
            self.logger.error(f"Web search failed: {str(e)}")
            return {
                'success': False,
                'error': f'Search failed: {str(e)}',
                'results': [],
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
    
    def _format_for_llm(self, query: str, results: List[Dict[str, str]]) -> str:
        """Format search results for LLM consumption"""
        if not results:
            return f"No web search results found for: {query}"
        
        formatted = f"Web Search Results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"**Result {i}:**\n"
            formatted += f"Title: {result.get('title', 'No title')}\n"
            
            if result.get('snippet'):
                formatted += f"Summary: {result['snippet']}\n"
            
            if result.get('url'):
                formatted += f"URL: {result['url']}\n"
            
            if result.get('source'):
                formatted += f"Source: {result['source']}\n"
            
            formatted += "\n"
        
        return formatted
    
    def get_search_capabilities(self) -> Dict[str, Any]:
        """Get information about search capabilities"""
        test_result = self.searcher.test_search_capability()
        
        return {
            'enabled': self.enabled,
            'test_status': test_result,
            'recent_searches': len(self.search_history),
            'last_search': self.search_history[-1] if self.search_history else None
        }
    
    def enable_search(self):
        """Enable web search feature"""
        self.enabled = True
        self.logger.info("Web search feature enabled")
    
    def disable_search(self):
        """Disable web search feature"""
        self.enabled = False
        self.logger.info("Web search feature disabled")
    
    def clear_history(self):
        """Clear search history"""
        self.search_history = []
        self.logger.info("Search history cleared")
    
    def get_search_history(self) -> List[Dict[str, Any]]:
        """Get search history"""
        return self.search_history.copy()
    
    def enable_keyword_extraction(self):
        """Enable keyword extraction for searches"""
        self.use_keyword_extraction = True
        self.logger.info("Keyword extraction enabled")
    
    def disable_keyword_extraction(self):
        """Disable keyword extraction for searches"""
        self.use_keyword_extraction = False
        self.logger.info("Keyword extraction disabled")
    
    def search_with_raw_query(self, query: str, max_results: Optional[int] = None, 
                             format_for_llm: bool = True) -> Dict[str, Any]:
        """
        Perform search using the original query without keyword extraction
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            format_for_llm: Whether to format results for LLM consumption
            
        Returns:
            Dictionary with search results and metadata
        """
        return self.search_web(query, max_results, format_for_llm, use_keyword_extraction=False)
    
    def search_with_keyword_extraction(self, query: str, max_results: Optional[int] = None, 
                                     format_for_llm: bool = True) -> Dict[str, Any]:
        """
        Perform search using keyword extraction
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            format_for_llm: Whether to format results for LLM consumption
            
        Returns:
            Dictionary with search results and metadata
        """
        return self.search_web(query, max_results, format_for_llm, use_keyword_extraction=True)
    
    def search_and_summarize(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Perform search and return a summary suitable for LLM context
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            Formatted summary string
        """
        search_result = self.search_web(query, max_results, format_for_llm=True)
        
        if search_result['success']:
            return search_result['formatted_context']
        else:
            return f"Web search failed for '{query}': {search_result.get('error', 'Unknown error')}"
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'searcher'):
            self.searcher.close()


# Utility functions for integration
def create_web_search_feature(config: Optional[Dict] = None, llm_client=None) -> WebSearchFeature:
    """Create and return a web search feature instance"""
    return WebSearchFeature(config, llm_client)


def test_web_search_integration():
    """Test the web search integration"""
    print("Testing Web Search Feature Integration")
    print("=" * 50)
    
    # Create feature instance
    search_feature = create_web_search_feature()
    
    # Test capabilities
    capabilities = search_feature.get_search_capabilities()
    print(f"Search enabled: {capabilities['enabled']}")
    print(f"Test status: {'SUCCESS' if capabilities['test_status']['success'] else 'FAILED'}")
    
    if capabilities['test_status']['success']:
        engines = capabilities['test_status']['engines_working']
        print(f"Working engines: {', '.join(engines)}")
    
    # Test search functionality
    print("\n" + "-" * 30)
    print("Testing search functionality")
    
    test_query = "python web scraping tutorial"
    result = search_feature.search_web(test_query, max_results=3)
    
    print(f"Search query: {test_query}")
    print(f"Search success: {result['success']}")
    
    if result['success']:
        print(f"Results found: {result['result_count']}")
        
        # Show formatted context
        print("\nFormatted for LLM:")
        print("-" * 20)
        print(result['formatted_context'][:500] + "..." if len(result['formatted_context']) > 500 else result['formatted_context'])
    else:
        print(f"Search error: {result.get('error', 'Unknown error')}")
    
    # Test search and summarize
    print("\n" + "-" * 30)
    print("Testing search and summarize")
    
    summary = search_feature.search_and_summarize("artificial intelligence ethics", max_results=2)
    print("Summary:")
    print(summary[:400] + "..." if len(summary) > 400 else summary)
    
    # Show search history
    history = search_feature.get_search_history()
    print(f"\nSearch history entries: {len(history)}")
    
    search_feature.close()
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_web_search_integration()