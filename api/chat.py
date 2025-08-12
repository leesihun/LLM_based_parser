"""
Chat API Endpoints
Handles different types of conversations and LLM interactions
"""

from flask import request, jsonify
from typing import Dict, Any, Tuple
import logging
import time

logger = logging.getLogger(__name__)


def extract_llm_response_data(llm_response) -> Dict[str, Any]:
    """
    Helper function to extract response data and metrics from LLM response
    
    Args:
        llm_response: Response from LLM client (dict or string)
        
    Returns:
        Dictionary with content and performance metrics
    """
    if isinstance(llm_response, dict):
        return {
            'content': llm_response.get('content', ''),
            'processing_time': llm_response.get('processing_time', 0),
            'tokens_per_second': llm_response.get('tokens_per_second', 0)
        }
    else:
        # Old format - just a string
        return {
            'content': llm_response,
            'processing_time': 0,
            'tokens_per_second': 0
        }


def get_combined_system_prompt(llm_client, mode: str = 'default') -> str:
    """
    Get combined universal + mode-specific system prompt
    
    Args:
        llm_client: LLM client instance
        mode: Prompt mode (default, rag_mode, search_mode, etc.)
        
    Returns:
        Combined system prompt string or None
    """
    system_config = llm_client.config.get('system_prompt', {})
    if not system_config.get('enabled', False):
        return None
    
    # Handle both string and array formats
    def format_prompt(prompt_data):
        if isinstance(prompt_data, list):
            return '\n'.join(prompt_data)
        elif isinstance(prompt_data, str):
            return prompt_data
        else:
            return ''
    
    universal_prompt = format_prompt(system_config.get('universal', ''))
    mode_prompt = format_prompt(system_config.get(mode, system_config.get('default', '')))
    
    if universal_prompt and mode_prompt:
        return f"{universal_prompt}\n\n{mode_prompt}"
    elif universal_prompt:
        return universal_prompt
    elif mode_prompt:
        return mode_prompt
    else:
        return None


def create_chat_endpoints(app, llm_client, memory, rag_system, file_handler, web_search_feature, require_auth):
    """
    Create chat endpoints
    
    Args:
        app: Flask application instance
        llm_client: LLM client for generating responses
        memory: Conversation memory manager
        rag_system: RAG system for knowledge base queries
        file_handler: File handling system
        web_search_feature: Web search functionality
        require_auth: Authentication decorator
    """
    
    @app.route('/api/chat', methods=['POST'])
    @require_auth
    def normal_chat() -> Tuple[Dict[str, Any], int]:
        """
        Normal chat endpoint - standard LLM conversation
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            message (str): User's message
            session_id (str, optional): Conversation session ID
            
        Returns:
            200: Chat response with metrics
            400: Missing message
            403: Session access denied
            500: Server error
        """
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            session_id = data.get('session_id', None)
            user_id = request.user['user_id']
            
            if not user_message:
                return jsonify({'error': 'No message provided'}), 400
            
            # Create new session if none provided
            if not session_id:
                session_id = memory.create_session(user_id)
            
            # Verify session belongs to current user
            session_data = memory.get_session(session_id)
            if not session_data or session_data.get('user_id') != user_id:
                return jsonify({'error': 'Session not found or access denied'}), 403
            
            # Add user message to conversation memory
            memory.add_message(session_id, 'user', user_message)
            
            # Get full conversation context for LLM
            conversation_context = memory.get_context_for_llm(session_id)
            
            # Add combined system prompt if enabled and not already present
            if conversation_context:
                has_system = any(msg['role'] == 'system' for msg in conversation_context)
                if not has_system:
                    system_prompt = get_combined_system_prompt(llm_client, 'default')
                    if system_prompt:
                        conversation_context.insert(0, {'role': 'system', 'content': system_prompt})
            
            # Generate response using full conversation context
            llm_response = llm_client.chat_completion(conversation_context)
            response_data = extract_llm_response_data(llm_response)
            
            # Add assistant response to conversation memory
            memory.add_message(session_id, 'assistant', response_data['content'])
            
            logger.info(f"Normal chat - User: {request.user['username']}, Session: {session_id}")
            
            return jsonify({
                'response': response_data['content'],
                'session_id': session_id,
                'processing_time': response_data['processing_time'],
                'tokens_per_second': response_data['tokens_per_second'],
                'chat_type': 'normal'
            })
            
        except Exception as e:
            logger.error(f"Normal chat error: {str(e)}")
            return jsonify({'error': 'Chat request failed'}), 500
    
    @app.route('/api/chat/rag', methods=['POST'])
    @require_auth
    def rag_chat() -> Tuple[Dict[str, Any], int]:
        """
        RAG chat endpoint - conversation with knowledge base context
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            message (str): User's message/query
            session_id (str, optional): Conversation session ID
            max_results (int, optional): Maximum search results (default: 5)
            
        Returns:
            200: Chat response with RAG context
            400: Missing message
            403: Session access denied
            500: Server error
        """
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            session_id = data.get('session_id', None)
            max_results = data.get('max_results', 5)
            user_id = request.user['user_id']
            
            if not user_message:
                return jsonify({'error': 'No message provided'}), 400
            
            # Create new session if none provided
            if not session_id:
                session_id = memory.create_session(user_id)
            
            # Verify session belongs to current user
            session_data = memory.get_session(session_id)
            if not session_data or session_data.get('user_id') != user_id:
                return jsonify({'error': 'Session not found or access denied'}), 403
            
            # Add user message to conversation memory
            memory.add_message(session_id, 'user', user_message)
            
            # Search RAG system for relevant context
            search_results = rag_system.search(user_message, max_results=max_results)
            context_text = "\\n\\n".join([result['content'] for result in search_results])
            
            # Create enhanced prompt with RAG context
            enhanced_message = f\"\"\"Context from knowledge base:
{context_text}

User Question: {user_message}

Please answer the question using the provided context when relevant.\"\"\"
            
            # Get full conversation context for LLM
            conversation_context = memory.get_context_for_llm(session_id)
            
            # Add RAG-specific system prompt if enabled and not already present
            if conversation_context:
                has_system = any(msg['role'] == 'system' for msg in conversation_context)
                if not has_system:
                    system_prompt = get_combined_system_prompt(llm_client, 'rag_mode')
                    if system_prompt:
                        conversation_context.insert(0, {'role': 'system', 'content': system_prompt})
            
            # Replace the last user message with enhanced version
            if conversation_context and len(conversation_context) > 0:
                conversation_context[-1]['content'] = enhanced_message
            
            # Generate response using enhanced context
            llm_response = llm_client.chat_completion(conversation_context)
            response_data = extract_llm_response_data(llm_response)
            
            # Add assistant response to conversation memory
            memory.add_message(session_id, 'assistant', response_data['content'])
            
            logger.info(f"RAG chat - User: {request.user['username']}, Results: {len(search_results)}")
            
            return jsonify({
                'response': response_data['content'],
                'session_id': session_id,
                'processing_time': response_data['processing_time'],
                'tokens_per_second': response_data['tokens_per_second'],
                'rag_context_used': True,
                'search_results_count': len(search_results),
                'chat_type': 'rag'
            })
            
        except Exception as e:
            logger.error(f"RAG chat error: {str(e)}")
            return jsonify({'error': 'RAG chat request failed'}), 500
    
    @app.route('/api/chat/web-search', methods=['POST'])
    @require_auth
    def web_search_chat() -> Tuple[Dict[str, Any], int]:
        """
        Web search chat endpoint - conversation with live web search results
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            message (str): User's message/query
            session_id (str, optional): Conversation session ID
            max_results (int, optional): Maximum search results (default: 5)
            
        Returns:
            200: Chat response with search context
            400: Missing message or inadequate search terms
            403: Session access denied or web search disabled
            500: Server error
        """
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            session_id = data.get('session_id', None)
            max_results = data.get('max_results', 5)
            user_id = request.user['user_id']
            
            if not user_message:
                return jsonify({'error': 'No message provided'}), 400
            
            # Check if web search is enabled
            search_config = llm_client.config.get('web_search', {})
            if not search_config.get('enabled', False):
                return jsonify({'error': 'Web search is disabled'}), 403
            
            # Create new session if none provided
            if not session_id:
                session_id = memory.create_session(user_id)
            
            # Verify session belongs to current user
            session_data = memory.get_session(session_id)
            if not session_data or session_data.get('user_id') != user_id:
                return jsonify({'error': 'Session not found or access denied'}), 403
            
            # Measure search processing time
            search_start_time = time.time()
            
            # Perform web search with keyword extraction
            search_result = web_search_feature.search_web(user_message, max_results, format_for_llm=True)
            
            if not search_result.get('success'):
                return jsonify({
                    'error': search_result.get('error', 'Web search failed'),
                    'search_failed': True
                }), 400
            
            search_results = search_result.get('formatted_context', 'No search results available')
            search_processing_time = (time.time() - search_start_time) * 1000
            
            # Add user message to conversation memory
            memory.add_message(session_id, 'user', user_message)
            
            # Create enhanced prompt with search results
            enhanced_message = f\"\"\"Web Search Results:
{search_results}

User Question: {user_message}

Please answer the user's question using the search results above when relevant. Always cite your sources.\"\"\"
            
            # Get full conversation context for LLM
            conversation_context = memory.get_context_for_llm(session_id)
            
            # Add search-specific system prompt if enabled and not already present
            if conversation_context:
                has_system = any(msg['role'] == 'system' for msg in conversation_context)
                if not has_system:
                    system_prompt = get_combined_system_prompt(llm_client, 'search_mode')
                    if system_prompt:
                        conversation_context.insert(0, {'role': 'system', 'content': system_prompt})
            
            # Replace the last user message with enhanced version
            if conversation_context and len(conversation_context) > 0:
                conversation_context[-1]['content'] = enhanced_message
            
            # Generate response using enhanced context
            llm_response = llm_client.chat_completion(conversation_context)
            response_data = extract_llm_response_data(llm_response)
            
            # Add assistant response to conversation memory
            memory.add_message(session_id, 'assistant', response_data['content'])
            
            logger.info(f"Web search chat - User: {request.user['username']}, Keywords: {search_result.get('keyword_extraction_used', False)}")
            
            return jsonify({
                'response': response_data['content'],
                'session_id': session_id,
                'processing_time': response_data['processing_time'],
                'tokens_per_second': response_data['tokens_per_second'],
                'search_processing_time': search_processing_time,
                'search_context_used': True,
                'search_results_count': search_result.get('result_count', 0),
                'keyword_extraction_used': search_result.get('keyword_extraction_used', False),
                'optimized_queries': search_result.get('queries_tried', [user_message]),
                'successful_query': search_result.get('successful_query'),
                'chat_type': 'web_search'
            })
            
        except Exception as e:
            logger.error(f"Web search chat error: {str(e)}")
            return jsonify({'error': 'Web search chat request failed'}), 500