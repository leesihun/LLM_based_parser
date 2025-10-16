#!/usr/bin/env python3
"""
Web Search Feature Integration
Integrates browser-based web search capability into the LLM system
"""

import json
import logging
from typing import Dict, List, Optional, Any, Iterable
from datetime import datetime

# Import search systems
from backend.services.search.keyword_extractor import KeywordExtractor
from backend.services.search.manager import SearchManager
from backend.services.search.searxng_search import SearXNGSearcher
from backend.services.search.selenium_search import SeleniumSearcher
from backend.services.search.types import SearchExecution, SearchResult


class WebSearchFeature:
    """Web search feature for LLM integration"""
    
    def __init__(self, config: Optional[Dict] = None, llm_client=None):
        """Initialize web search feature"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.llm_client = llm_client  # Store LLM client for search_and_chat

        # Adopt modular search manager mirroring Page Assist behaviour
        self.search_manager = SearchManager(self.config)
        self.searcher = None  # retained for backward compatibility with older integrations
        self.fallback_searcher = None
        self._searxng_fallback = None
        self._searxng_initialised = False
        self._searxng_failed = False
        self._selenium_fallback = None
        self._selenium_initialised = False
        self._selenium_failed = False
        self.logger.info(
            "Web Search Feature initialised with modular manager "
            f"(default provider: {self.search_manager.settings.default_provider})"
        )

        self.enabled = True
        self.search_history = []

        # Initialize keyword extractor
        keyword_config = self.config.get('keyword_extraction', {})
        self.keyword_extractor = KeywordExtractor(keyword_config, llm_client)
        # Check both top-level and nested keyword extraction settings
        self.use_keyword_extraction = self.config.get('use_keyword_extraction', keyword_config.get('enabled', False))
    
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
                    self.logger.info(f"Starting LLM-based keyword extraction for: {query}")
                    extraction_info = self.keyword_extractor.extract_keywords(query)
                    
                    if extraction_info and extraction_info.get('adequate_keywords') and extraction_info.get('queries'):
                        search_queries = extraction_info['queries']
                        keywords = extraction_info.get('keywords', [])
                        method = extraction_info.get('method', 'unknown')
                        
                        self.logger.info(f"??LLM extracted {len(keywords)} keywords using {method} method")
                        self.logger.info(f"??Keywords: {keywords[:5]}")  # Show first 5
                        self.logger.info(f"??Generated {len(search_queries)} optimized queries: {search_queries}")
                    else:
                        reason = "no adequate keywords found" if not extraction_info.get('adequate_keywords') else "no queries generated"
                        self.logger.warning(f"??Keyword extraction failed: {reason}")
                        self.logger.warning(f"??Extraction info: {extraction_info}")
                        
                        # For LLM-based extraction, we might want to be more lenient
                        # If LLM was used but failed, fall back to original query
                        llm_config = self.config.get('keyword_extraction', {})
                        if llm_config.get('use_llm') and llm_config.get('llm_extraction', {}).get('fallback_to_original', True):
                            self.logger.info(f"??Falling back to original query: {query}")
                            search_queries = [query]
                        else:
                            return {
                                'success': False,
                                'error': f'Cannot perform web search: {reason}. Query too generic or lacks searchable terms.',
                                'results': [],
                                'query': query,
                                'timestamp': datetime.now().isoformat(),
                                'extraction_info': extraction_info
                            }
                except Exception as e:
                    self.logger.error(f"??Keyword extraction failed with exception: {e}")
                    
                    # Check if we should fall back to original query
                    llm_config = self.config.get('keyword_extraction', {})
                    if llm_config.get('use_llm') and llm_config.get('llm_extraction', {}).get('fallback_to_original', True):
                        self.logger.info(f"??Exception fallback to original query: {query}")
                        search_queries = [query]
                    else:
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
            
            # Execute searches using the modular manager
            successful_execution: Optional[SearchExecution] = None
            attempted_queries: List[str] = []
            execution_history: List[SearchExecution] = []
            successful_query: Optional[str] = None
            last_query_attempted: Optional[str] = None

            for i, search_query in enumerate(search_queries):
                self.logger.info(
                    "?�� [SEARCH MANAGER] Searching web with query %s/%s via manager: %s",
                    i + 1,
                    len(search_queries),
                    search_query,
                )
                attempted_queries.append(search_query)

                try:
                    self.logger.info("?? [SEARCH MANAGER] Calling SearchManager.search()...")
                    execution = self.search_manager.search(search_query, max_results)
                    self.logger.info(f"??[SEARCH MANAGER] SearchManager returned: success={execution.success}, provider={execution.provider}")
                except Exception as e:
                    self.logger.error(f"??[SEARCH MANAGER] SearchManager.search() failed with exception: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    execution = SearchExecution(
                        query=search_query,
                        provider="error",
                        success=False,
                        error=str(e)
                    )

                execution_history.append(execution)
                last_query_attempted = search_query

                if execution.success and execution.results:
                    successful_execution = execution
                    successful_query = search_query
                    break
                else:
                    self.logger.warning(
                        "?�️ [SEARCH MANAGER] No results for query '%s' (provider=%s, error=%s)",
                        search_query,
                        execution.provider,
                        execution.error,
                    )

            fallback_query = last_query_attempted or (search_queries[-1] if search_queries else query)

            if (
                not self.search_manager.settings.disable_fallbacks
                and (not successful_execution or not successful_execution.results)
                and fallback_query
            ):
                self.logger.info("?�� [FALLBACK] Attempting SearXNG fallback...")
                try:
                    searxng_execution = self._run_fallback_searxng(fallback_query, max_results or 5)
                    if searxng_execution and searxng_execution.results:
                        self.logger.info(f"??[FALLBACK] SearXNG fallback succeeded with {len(searxng_execution.results)} results")
                        successful_execution = searxng_execution
                        successful_query = fallback_query
                        attempted_queries.append(f"{fallback_query} [searxng]")
                    else:
                        self.logger.warning("?�️ [FALLBACK] SearXNG fallback returned no results")
                except Exception as e:
                    self.logger.error(f"??[FALLBACK] SearXNG fallback failed with exception: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")

            if (
                not self.search_manager.settings.disable_fallbacks
                and (not successful_execution or not successful_execution.results)
                and fallback_query
            ):
                self.logger.info("?�� [FALLBACK] Attempting Selenium fallback...")
                try:
                    selenium_execution = self._run_fallback_selenium(fallback_query, max_results or 5)
                    if selenium_execution and selenium_execution.results:
                        self.logger.info(f"??[FALLBACK] Selenium fallback succeeded with {len(selenium_execution.results)} results")
                        successful_execution = selenium_execution
                        successful_query = fallback_query
                        attempted_queries.append(f"{fallback_query} [selenium]")
                    else:
                        self.logger.warning("?�️ [FALLBACK] Selenium fallback returned no results")
                except Exception as e:
                    self.logger.error(f"??[FALLBACK] Selenium fallback failed with exception: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")

            if not successful_execution or not successful_execution.results:
                last_error = (
                    execution_history[-1].error
                    if execution_history and execution_history[-1].error
                    else "No provider returned results."
                )
                self.logger.warning(
                    "Web search failed for queries %s. Last error: %s",
                    attempted_queries,
                    last_error,
                )
                return {
                    'success': False,
                    'error': last_error,
                    'results': [],
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'keyword_extraction_used': extract_keywords,
                    'queries_tried': attempted_queries,
                    'extraction_info': extraction_info
                }

            results = [result.to_dict() for result in successful_execution.results]
            structured_prompt = successful_execution.prompt
            structured_sources = successful_execution.sources
            provider_used = successful_execution.provider
            
            # Log search in history
            search_entry = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'result_count': len(results),
                'success': True,
                'keyword_extraction_used': extract_keywords,
                'successful_query': successful_query if successful_query != query else None,
                'queries_tried': attempted_queries if attempted_queries else [query],
                'provider': provider_used
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
                'queries_tried': attempted_queries if attempted_queries else [query],
                'structured_results': structured_prompt,
                'sources': structured_sources,
                'provider': provider_used,
                'answer': successful_execution.answer
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

    def _ensure_searxng_searcher(self) -> Optional[SearXNGSearcher]:
        """Lazily initialise the SearXNG fallback searcher."""
        if self._searxng_failed:
            return None
        if not self._searxng_initialised:
            self._searxng_initialised = True
            try:
                if 'SearXNGSearcher' in globals():
                    self._searxng_fallback = SearXNGSearcher(self.config)
                else:
                    self._searxng_failed = True
            except Exception as exc:
                self.logger.warning(f"SearXNG fallback initialisation failed: {exc}")
                self._searxng_failed = True
                self._searxng_fallback = None
        return self._searxng_fallback

    def _ensure_selenium_searcher(self) -> Optional[SeleniumSearcher]:
        """Lazily initialise the Selenium fallback searcher."""
        if self._selenium_failed:
            return None
        if not self._selenium_initialised:
            self._selenium_initialised = True
            try:
                if 'SeleniumSearcher' in globals():
                    self._selenium_fallback = SeleniumSearcher(self.config)
                else:
                    self._selenium_failed = True
            except Exception as exc:
                self.logger.warning(f"Selenium fallback initialisation failed: {exc}")
                self._selenium_failed = True
                self._selenium_fallback = None
        return self._selenium_fallback

    def _run_fallback_searxng(self, query: str, max_results: int) -> Optional[SearchExecution]:
        searcher = self._ensure_searxng_searcher()
        if not searcher:
            return None
        try:
            raw_results = searcher.search(query, max_results)
            if not raw_results:
                return None
            execution = self._build_execution_from_raw(query, raw_results, max_results, "searxng")
            if execution:
                self.logger.info("SearXNG fallback provided %s results", execution.result_count)
            return execution
        except Exception as exc:
            self.logger.warning("SearXNG fallback search failed: %s", exc)
            return None

    def _run_fallback_selenium(self, query: str, max_results: int) -> Optional[SearchExecution]:
        searcher = self._ensure_selenium_searcher()
        if not searcher:
            return None
        try:
            raw_results = searcher.search(query, max_results)
            if not raw_results:
                return None
            execution = self._build_execution_from_raw(query, raw_results, max_results, "selenium")
            if execution:
                self.logger.info("Selenium fallback provided %s results", execution.result_count)
            return execution
        except Exception as exc:
            self.logger.warning("Selenium fallback search failed: %s", exc)
            return None

    def _build_execution_from_raw(
        self,
        query: str,
        raw_results: Iterable[Dict[str, Any]],
        max_results: int,
        provider_label: str,
    ) -> Optional[SearchExecution]:
        items = list(raw_results)[:max_results]
        if not items:
            return None
        search_results: List[SearchResult] = []
        seen_urls = set()
        for item in items:
            url = item.get('url', '')
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            snippet = item.get('snippet') or item.get('content') or ''
            search_results.append(
                SearchResult(
                    title=item.get('title') or snippet or url,
                    url=url,
                    snippet=snippet,
                    source=item.get('source') or provider_label,
                    content=item.get('content')
                )
            )
        if not search_results:
            return None
        if self.search_manager.settings.simple_mode:
            for result in search_results:
                result.content = result.snippet
        else:
            self.search_manager.enrich_results(search_results, query)
        prompt = self.search_manager.build_prompt(search_results)
        sources = self.search_manager.build_sources(search_results)
        return SearchExecution(
            query=query,
            provider=provider_label,
            success=True,
            results=search_results,
            prompt=prompt,
            sources=sources,
        )

    def _format_for_llm(self, query: str, results: List[Dict[str, Any]]) -> str:
        if not results:
            return f"No web search results found for: {query}"

        formatted = [f"Web Search Results for '{query}':\n"]
        for idx, result in enumerate(results, start=1):
            title = result.get('title', 'No title')
            formatted.append(f"**Result {idx}:**")
            formatted.append(f"Title: {title}")
            snippet = result.get('snippet') or result.get('content')
            if snippet:
                formatted.append(f"Summary: {snippet}")
            url = result.get('url')
            if url:
                formatted.append(f"URL: {url}")
            source = result.get('source')
            if source:
                formatted.append(f"Source: {source}")
            formatted.append("")
        return "\n".join(formatted)
    def get_search_capabilities(self) -> Dict[str, Any]:
        """Return a snapshot of search feature status and a quick probe result."""
        test_query = "python programming"
        execution = self.search_manager.search(test_query, max_results=3)
        probe = execution

        if (not execution.success or not execution.results) and self._ensure_searxng_searcher():
            probe = self._run_fallback_searxng(test_query, 3) or execution

        return {
            'enabled': self.enabled,
            'keyword_extraction_enabled': self.use_keyword_extraction,
            'recent_activity': len(self.search_history),
            'provider': probe.provider if probe else None,
            'success': bool(probe and probe.success and probe.results),
            'result_count': probe.result_count if probe else 0,
            'error': probe.error if probe and not probe.success else None,
        }

    def enable_search(self):
        self.enabled = True
        self.logger.info("Web search feature enabled")

    def disable_search(self):
        self.enabled = False
        self.logger.info("Web search feature disabled")

    def clear_history(self):
        self.search_history = []
        self.logger.info("Search history cleared")

    def get_search_history(self) -> List[Dict[str, Any]]:
        return list(self.search_history)

    def enable_keyword_extraction(self):
        self.use_keyword_extraction = True
        self.logger.info("Keyword extraction enabled")

    def disable_keyword_extraction(self):
        self.use_keyword_extraction = False
        self.logger.info("Keyword extraction disabled")

    def search_with_raw_query(self, query: str, max_results: Optional[int] = None,
                              format_for_llm: bool = True) -> Dict[str, Any]:
        return self.search_web(query, max_results, format_for_llm, use_keyword_extraction=False)

    def search_with_keyword_extraction(self, query: str, max_results: Optional[int] = None,
                                       format_for_llm: bool = True) -> Dict[str, Any]:
        return self.search_web(query, max_results, format_for_llm, use_keyword_extraction=True)

    def search_and_summarize(self, query: str, max_results: Optional[int] = None) -> str:
        result = self.search_web(query, max_results, format_for_llm=True)
        if result.get('success'):
            return result.get('formatted_context', '')
        return f"Web search failed for '{query}': {result.get('error', 'Unknown error')}"

    def search_and_chat(self, query: str, session_id: Optional[str] = None, 
                       max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform web search and generate LLM response based on search results.
        
        Args:
            query: User's search query
            session_id: Optional session ID for conversation context
            max_results: Maximum number of search results
            
        Returns:
            Dictionary containing response and search metadata
        """
        try:
            # Perform web search
            search_result = self.search_web(query, max_results, format_for_llm=True)
            
            if not search_result.get('success'):
                return {
                    'response': f"I apologize, but I couldn't perform a web search at this time. Error: {search_result.get('error', 'Unknown error')}",
                    'keyword_extraction_used': search_result.get('keyword_extraction_used', False),
                    'optimized_queries': search_result.get('optimized_queries', []),
                    'successful_query': search_result.get('successful_query', query),
                    'search_results': []
                }
            
            # Get search context
            search_context = search_result.get('formatted_context', '')
            
            # Generate LLM response using search context
            if self.llm_client:
                try:
                    # Build system prompt with search mode instructions
                    system_config = self.config.get('system_prompt', {})
                    universal_prompts = system_config.get('universal', [])
                    search_mode_prompts = system_config.get('search_mode', [])
                    
                    # Combine prompts
                    if isinstance(search_mode_prompts, list):
                        system_prompt = '\n'.join(universal_prompts + search_mode_prompts)
                    else:
                        system_prompt = '\n'.join(universal_prompts) + '\n' + search_mode_prompts
                    
                    # Prepare user message with search context
                    user_message = f"""User Question: {query}

Search Results:
{search_context}

Please provide a comprehensive answer based on the search results above."""
                    
                    # Get LLM response
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                    
                    llm_response = self.llm_client.chat(messages)
                    response_text = llm_response.get('response', '')
                    
                except Exception as e:
                    self.logger.error(f"Error generating LLM response: {e}")
                    response_text = f"Based on the search results:\n\n{search_context[:500]}..."
            else:
                # No LLM client available, return formatted search results
                response_text = f"Search results for '{query}':\n\n{search_context}"
            
            return {
                'response': response_text,
                'keyword_extraction_used': search_result.get('keyword_extraction_used', False),
                'optimized_queries': search_result.get('optimized_queries', []),
                'successful_query': search_result.get('successful_query', query),
                'search_results': search_result.get('results', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error in search_and_chat: {e}")
            return {
                'response': f"I apologize, but an error occurred while processing your request: {str(e)}",
                'keyword_extraction_used': False,
                'optimized_queries': [],
                'successful_query': query,
                'search_results': []
            }

    def close(self):
        return


def create_web_search_feature(config: Optional[Dict] = None, llm_client=None) -> WebSearchFeature:
    return WebSearchFeature(config, llm_client)


def test_web_search_integration():
    print("Testing Web Search Feature Integration")
    print("=" * 50)

    search_feature = create_web_search_feature()

    capabilities = search_feature.get_search_capabilities()
    print(f"Search enabled: {capabilities['enabled']}")
    print(f"Probe success: {'SUCCESS' if capabilities['success'] else 'FAILED'}")
    if capabilities['success']:
        print(f"Provider used: {capabilities.get('provider')}")
    else:
        print(f"Error: {capabilities.get('error')}")

    print("\n" + "-" * 30)
    print("Testing search functionality")
    test_query = "python web scraping tutorial"
    result = search_feature.search_web(test_query, max_results=2)
    print(f"Search success: {result['success']}")
    if result['success']:
        print(f"Provider: {result.get('provider')}")
        print(f"Results returned: {result.get('result_count')}")
    else:
        print(f"Error: {result.get('error')}")

    print("\n" + "-" * 30)
    print("Testing search and summarize")
    summary = search_feature.search_and_summarize("artificial intelligence ethics", max_results=2)
    print(summary[:400] + ("..." if len(summary) > 400 else ""))

    print(f"\nSearch history entries: {len(search_feature.get_search_history())}")
    print("\nTest completed")


if __name__ == "__main__":
    test_web_search_integration()
