"""
Search API Endpoints
Handles web search operations and keyword extraction
"""

from flask import request, jsonify
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def create_search_endpoints(app, web_search_feature, require_auth):
    """
    Create search endpoints
    
    Args:
        app: Flask application instance
        web_search_feature: Web search functionality
        require_auth: Authentication decorator
    """
    
    @app.route('/api/search/web', methods=['POST'])
    @require_auth
    def web_search() -> Tuple[Dict[str, Any], int]:
        """
        Perform web search without chat context
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            query (str): Search query
            max_results (int, optional): Maximum results (default: 5)
            
        Returns:
            200: Search results with metadata
            400: Missing query or inadequate search terms
            403: Web search disabled
            500: Server error
        """
        try:
            data = request.get_json()
            query = data.get('query', '')
            max_results = data.get('max_results', 5)
            
            if not query:
                return jsonify({'error': 'Query is required'}), 400
            
            # Perform search
            search_result = web_search_feature.search_web(query, max_results, format_for_llm=False)
            
            logger.info(f"Web search - User: {request.user['username']}, Query: {query[:50]}")
            
            return jsonify({
                'success': search_result['success'],
                'results': search_result.get('results', []),
                'query': query,
                'count': search_result.get('result_count', 0),
                'keyword_extraction_used': search_result.get('keyword_extraction_used', False),
                'optimized_queries': search_result.get('queries_tried', [query]),
                'successful_query': search_result.get('successful_query'),
                'error': search_result.get('error')
            })
            
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return jsonify({'error': 'Search request failed'}), 500
    
    @app.route('/api/search/extract-keywords', methods=['POST'])
    @require_auth
    def extract_keywords() -> Tuple[Dict[str, Any], int]:
        """
        Extract keywords from text without performing search
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            text (str): Text to extract keywords from
            
        Returns:
            200: Extracted keywords and metadata
            400: Missing text
            500: Server error
        """
        try:
            data = request.get_json()
            text = data.get('text', '')
            
            if not text:
                return jsonify({'error': 'Text is required'}), 400
            
            extraction_result = web_search_feature.keyword_extractor.extract_keywords(text)
            
            logger.info(f"Keyword extraction - User: {request.user['username']}, Keywords: {len(extraction_result.get('keywords', []))}")
            
            return jsonify({
                'success': True,
                'original_text': text,
                'keywords': extraction_result.get('keywords', []),
                'queries': extraction_result.get('queries', []),
                'method': extraction_result.get('method'),
                'adequate_keywords': extraction_result.get('adequate_keywords', False),
                'extraction_results': extraction_result.get('extraction_results', {})
            })
            
        except Exception as e:
            logger.error(f"Keyword extraction error: {str(e)}")
            return jsonify({'error': 'Keyword extraction failed'}), 500
    
    @app.route('/api/search/status', methods=['GET'])
    @require_auth
    def search_status() -> Tuple[Dict[str, Any], int]:
        """
        Get web search feature status and configuration
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Search status and capabilities
            500: Server error
        """
        try:
            capabilities = web_search_feature.get_search_capabilities()
            
            return jsonify({
                'enabled': web_search_feature.enabled,
                'keyword_extraction_enabled': web_search_feature.use_keyword_extraction,
                'extraction_methods': web_search_feature.keyword_extractor.extraction_methods,
                'max_keywords': web_search_feature.keyword_extractor.max_keywords,
                'search_history_count': len(web_search_feature.get_search_history()),
                'capabilities': capabilities
            })
            
        except Exception as e:
            logger.error(f"Search status error: {str(e)}")
            return jsonify({'error': 'Failed to get search status'}), 500
    
    @app.route('/api/search/keyword-extraction/enable', methods=['POST'])
    @require_auth
    def enable_keyword_extraction() -> Tuple[Dict[str, Any], int]:
        """
        Enable keyword extraction for web searches
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Keyword extraction enabled
            500: Server error
        """
        try:
            web_search_feature.enable_keyword_extraction()
            logger.info(f"Keyword extraction enabled by user: {request.user['username']}")
            
            return jsonify({
                'success': True,
                'message': 'Keyword extraction enabled',
                'enabled': True
            })
            
        except Exception as e:
            logger.error(f"Enable keyword extraction error: {str(e)}")
            return jsonify({'error': 'Failed to enable keyword extraction'}), 500
    
    @app.route('/api/search/keyword-extraction/disable', methods=['POST'])
    @require_auth
    def disable_keyword_extraction() -> Tuple[Dict[str, Any], int]:
        """
        Disable keyword extraction for web searches
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Keyword extraction disabled
            500: Server error
        """
        try:
            web_search_feature.disable_keyword_extraction()
            logger.info(f"Keyword extraction disabled by user: {request.user['username']}")
            
            return jsonify({
                'success': True,
                'message': 'Keyword extraction disabled',
                'enabled': False
            })
            
        except Exception as e:
            logger.error(f"Disable keyword extraction error: {str(e)}")
            return jsonify({'error': 'Failed to disable keyword extraction'}), 500