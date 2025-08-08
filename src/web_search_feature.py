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
except ImportError:
    from selenium_search import SeleniumSearcher


class WebSearchFeature:
    """Web search feature for LLM integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize web search feature"""
        self.config = config or {}
        self.searcher = SeleniumSearcher(config)
        self.enabled = True
        self.search_history = []
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Selenium Search Feature initialized")
    
    def search_web(self, query: str, max_results: Optional[int] = None, 
                   format_for_llm: bool = True) -> Dict[str, Any]:
        """
        Perform web search and return formatted results
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            format_for_llm: Whether to format results for LLM consumption
            
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
            # Perform search
            self.logger.info(f"Searching web for: {query}")
            results = self.searcher.search(query, max_results)
            
            # Log search in history
            search_entry = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'result_count': len(results),
                'success': len(results) > 0
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
                'timestamp': search_entry['timestamp']
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
def create_web_search_feature(config: Optional[Dict] = None) -> WebSearchFeature:
    """Create and return a web search feature instance"""
    return WebSearchFeature(config)


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