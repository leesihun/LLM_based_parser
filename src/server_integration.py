#!/usr/bin/env python3
"""
Server Integration for Enhanced Web Search
Provides enhanced web search endpoints using browser automation
"""

from flask import request, jsonify
from functools import wraps
import logging

# Import the web search feature
try:
    from .web_search_feature import WebSearchFeature
except ImportError:
    from web_search_feature import WebSearchFeature


class WebSearchIntegration:
    """Integration class for web search functionality"""
    
    def __init__(self, app, memory, llm_client, user_manager, require_auth):
        """Initialize web search integration"""
        self.app = app
        self.memory = memory
        self.llm_client = llm_client
        self.user_manager = user_manager
        self.require_auth = require_auth
        
        # Initialize search feature
        search_config = llm_client.config.get('web_search', {})
        self.search_feature = WebSearchFeature(search_config)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Add routes
        self._add_routes()
    
    def _add_routes(self):
        """Add web search routes to the Flask app"""
        
        @self.app.route('/api/search/enhanced', methods=['POST'])
        @self.require_auth
        def enhanced_search():
            """Enhanced web search endpoint using browser automation"""
            try:
                data = request.get_json()
                query = data.get('query', '').strip()
                max_results = data.get('max_results', 5)
                
                if not query:
                    return jsonify({'error': 'Search query is required'}), 400
                
                # Perform search
                search_result = self.search_feature.search_web(query, max_results)
                
                return jsonify(search_result)
                
            except Exception as e:
                self.logger.error(f"Enhanced search failed: {str(e)}")
                return jsonify({'error': f'Search failed: {str(e)}'}), 500
        
        @self.app.route('/api/search/enhanced_chat', methods=['POST'])
        @self.require_auth
        def enhanced_search_chat():
            """Enhanced chat with web search context using browser automation"""
            try:
                data = request.get_json()
                user_message = data.get('message', '')
                session_id = data.get('session_id', None)
                user_id = request.user['user_id']
                search_query = data.get('search_query', user_message)  # Allow custom search query
                max_results = data.get('max_results', 5)
                
                if not user_message:
                    return jsonify({'error': 'Message is required'}), 400
                
                # Create new session if none provided
                if not session_id:
                    session_id = self.memory.create_session(user_id)
                
                # Verify session belongs to current user
                session_data = self.memory.get_session(session_id)
                if not session_data or session_data.get('user_id') != user_id:
                    return jsonify({'error': 'Session not found or access denied'}), 403
                
                # Perform web search
                search_result = self.search_feature.search_web(search_query, max_results, format_for_llm=True)
                
                # Add user message to conversation memory
                self.memory.add_message(session_id, 'user', user_message)
                
                # Create enhanced prompt with search results
                if search_result['success']:
                    search_context = search_result['formatted_context']
                    enhanced_message = f"""Recent Web Search Results for "{search_query}":

{search_context}

---

User Question: {user_message}

Please answer the user's question using the web search results above when relevant. Always cite your sources and mention when information comes from web search results."""
                else:
                    enhanced_message = f"""Web search for "{search_query}" was unsuccessful: {search_result.get('error', 'Unknown error')}

User Question: {user_message}

Please answer based on your knowledge, but mention that current web information is unavailable."""
                
                # Get full conversation context for LLM
                conversation_context = self.memory.get_context_for_llm(session_id)
                
                # Add system prompt for search mode if needed
                if conversation_context:
                    has_system = any(msg['role'] == 'system' for msg in conversation_context)
                    if not has_system:
                        system_prompt = self._get_search_system_prompt()
                        if system_prompt:
                            conversation_context.insert(0, {
                                'role': 'system',
                                'content': system_prompt
                            })
                
                # Add the enhanced message to context
                conversation_context.append({
                    'role': 'user',
                    'content': enhanced_message
                })
                
                # Generate response
                response = self.llm_client.generate_response(conversation_context)
                
                # Add response to conversation memory
                self.memory.add_message(session_id, 'assistant', response)
                
                return jsonify({
                    'response': response,
                    'session_id': session_id,
                    'search_performed': search_result['success'],
                    'search_query': search_query,
                    'sources_found': search_result.get('result_count', 0) if search_result['success'] else 0
                })
                
            except Exception as e:
                self.logger.error(f"Enhanced search chat failed: {str(e)}")
                return jsonify({'error': f'Chat with search failed: {str(e)}'}), 500
        
        @self.app.route('/api/search/status', methods=['GET'])
        @self.require_auth
        def search_status():
            """Get web search status and capabilities"""
            try:
                capabilities = self.search_feature.get_search_capabilities()
                return jsonify(capabilities)
                
            except Exception as e:
                self.logger.error(f"Failed to get search status: {str(e)}")
                return jsonify({'error': f'Status check failed: {str(e)}'}), 500
        
        @self.app.route('/api/search/history', methods=['GET'])
        @self.require_auth
        def search_history():
            """Get search history"""
            try:
                history = self.search_feature.get_search_history()
                return jsonify({
                    'history': history,
                    'total_searches': len(history)
                })
                
            except Exception as e:
                self.logger.error(f"Failed to get search history: {str(e)}")
                return jsonify({'error': f'History retrieval failed: {str(e)}'}), 500
        
        @self.app.route('/api/search/clear_history', methods=['POST'])
        @self.require_auth
        def clear_search_history():
            """Clear search history"""
            try:
                self.search_feature.clear_history()
                return jsonify({'message': 'Search history cleared'})
                
            except Exception as e:
                self.logger.error(f"Failed to clear search history: {str(e)}")
                return jsonify({'error': f'Clear history failed: {str(e)}'}), 500
    
    def _get_search_system_prompt(self):
        """Get system prompt for search mode"""
        try:
            system_config = self.llm_client.config.get('system_prompt', {})
            if not system_config.get('enabled', False):
                return None
            
            # Get search-specific system prompt
            search_prompt = system_config.get('search_mode', system_config.get('default', ''))
            
            if isinstance(search_prompt, list):
                return '\n'.join(search_prompt)
            elif isinstance(search_prompt, str):
                return search_prompt
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to get search system prompt: {e}")
            return None


def integrate_web_search(app, memory, llm_client, user_manager, require_auth):
    """
    Integrate web search functionality into the Flask app
    
    Args:
        app: Flask application instance
        memory: ConversationMemory instance
        llm_client: LLMClient instance
        user_manager: UserManager instance
        require_auth: Authentication decorator function
        
    Returns:
        WebSearchIntegration instance
    """
    return WebSearchIntegration(app, memory, llm_client, user_manager, require_auth)


# Test function for standalone testing
def test_integration():
    """Test web search integration functionality"""
    print("Testing Web Search Integration")
    print("=" * 50)
    
    # Test search feature creation
    search_feature = WebSearchFeature()
    
    # Test basic search
    test_query = "python programming best practices"
    result = search_feature.search_web(test_query, max_results=3)
    
    print(f"Test search: {test_query}")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Results: {result['result_count']}")
    else:
        print(f"Error: {result['error']}")
    
    # Test capabilities
    capabilities = search_feature.get_search_capabilities()
    print(f"Search enabled: {capabilities['enabled']}")
    print(f"Test status: {capabilities['test_status']['success']}")
    
    search_feature.close()
    print("Integration test completed!")


if __name__ == "__main__":
    test_integration()