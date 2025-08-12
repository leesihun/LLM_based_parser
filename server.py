#!/usr/bin/env python3
"""
Local LLM Backend Server - API server for web interface
Provides REST API endpoints for chat functionality
"""

import json
import os

# Disable ChromaDB telemetry before importing RAG system
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from functools import wraps
from core.llm_client import LLMClient
from core.conversation_memory import ConversationMemory
from core.user_management import UserManager
from src.rag_system import RAGSystem
from src.file_handler import FileHandler
# Import web search functionality
from src.web_search_feature import WebSearchFeature
# Import chat endpoints
from api.chat import create_chat_endpoints

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'he_team_llm_assistant_secret_key'  # Change this in production

# Initialize LLM client, conversation memory, user manager, RAG system, file handler, and web searcher
llm_client = LLMClient()
memory = ConversationMemory()
user_manager = UserManager()
rag_system = RAGSystem("config/config.json")  # Pass config path
file_handler = FileHandler()
web_search_feature = WebSearchFeature(llm_client.config.get('web_search', {}), llm_client)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        session_data = user_manager.validate_session(token)
        if not session_data:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Add user data to request context
        request.user = session_data
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'user') or request.user.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def extract_llm_response_data(llm_response):
    """Helper function to extract response data and metrics"""
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

def get_combined_system_prompt(mode='default'):
    """Get combined universal + mode-specific system prompt"""
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

@app.route('/')
def serve_index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/login.html')
def serve_login():
    """Serve the login page"""
    return send_from_directory('static', 'login.html')

# Authentication Endpoints

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Authenticate user
        user_data = user_manager.authenticate_user(username, password)
        if not user_data:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create session
        session_token = user_manager.create_session(user_data)
        
        return jsonify({
            'session_token': session_token,
            'user': user_data,
            'message': 'Login successful'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_manager.logout_session(token)
        
        return jsonify({'message': 'Logout successful'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    try:
        user_data = user_manager.get_user_by_id(request.user['user_id'])
        return jsonify({'user': user_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        success = user_manager.change_password(
            request.user['username'], 
            old_password, 
            new_password
        )
        
        if not success:
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    """Handle chat requests with conversation memory (authenticated)"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = request.user['user_id']
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Create new session if none provided (with user_id)
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
            # Check if system message already exists
            has_system = any(msg['role'] == 'system' for msg in conversation_context)
            if not has_system:
                system_prompt = get_combined_system_prompt('default')
                if system_prompt:
                    conversation_context.insert(0, {'role': 'system', 'content': system_prompt})
        
        # Generate response using full conversation context
        llm_response = llm_client.chat_completion(conversation_context)
        response_data = extract_llm_response_data(llm_response)
        
        # Add assistant response to conversation memory
        memory.add_message(session_id, 'assistant', response_data['content'])
        
        return jsonify({
            'response': response_data['content'],
            'session_id': session_id,
            'processing_time': response_data['processing_time'],
            'tokens_per_second': response_data['tokens_per_second']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Handle single prompt generation"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        system_prompt = data.get('system_prompt', None)
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        response = llm_client.generate_response(prompt, system_prompt)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models from Ollama"""
    try:
        models = llm_client.list_models()
        return jsonify({'models': models})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        return jsonify(llm_client.config)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
@require_auth
def update_config():
    """Update configuration (runtime only, doesn't save to file)"""
    try:
        data = request.get_json()
        
        # Update runtime config
        if 'model' in data:
            llm_client.model = data['model']
        if 'host' in data:
            llm_client.ollama_url = data['host']
        if 'timeout' in data:
            llm_client.timeout = data['timeout']
        
        return jsonify({'message': 'Configuration updated'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# RAG System Endpoints

@app.route('/api/rag/search', methods=['POST'])
@require_auth
def rag_search():
    """Search using RAG system"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        results = rag_system.search(query, n_results)
        
        return jsonify({
            'results': results,
            'query': query,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/chat', methods=['POST'])
@require_auth
def rag_chat():
    """Chat with RAG context"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = request.user['user_id']
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Create new session if none provided
        if not session_id:
            session_id = memory.create_session(user_id)
        
        # Verify session belongs to current user
        session_data = memory.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({'error': 'Session not found or access denied'}), 403
        
        # Get RAG context
        rag_context = rag_system.get_context_for_query(user_message)
        
        # Add user message to conversation memory
        memory.add_message(session_id, 'user', user_message)
        
        # Create enhanced prompt with RAG context
        enhanced_message = f"""Context from knowledge base:
{rag_context}

User question: {user_message}

Please answer the question using the provided context when relevant."""
        
        # Get full conversation context for LLM
        conversation_context = memory.get_context_for_llm(session_id)
        
        # Add RAG-specific combined system prompt if enabled and not already present
        if conversation_context:
            # Check if system message already exists
            has_system = any(msg['role'] == 'system' for msg in conversation_context)
            if not has_system:
                system_prompt = get_combined_system_prompt('rag_mode')
                if system_prompt:
                    conversation_context.insert(0, {'role': 'system', 'content': system_prompt})
        
        # Replace the last user message with enhanced version
        if conversation_context and len(conversation_context) > 0:
            conversation_context[-1]['content'] = enhanced_message
        
        # Generate response using enhanced context
        response = llm_client.chat_completion(conversation_context)
        
        # Add assistant response to conversation memory
        memory.add_message(session_id, 'assistant', response)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'rag_context_used': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/stats', methods=['GET'])
@require_auth
def rag_stats():
    """Get RAG system statistics"""
    try:
        stats = rag_system.get_collection_stats()
        return jsonify({'stats': stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Web Search Endpoints

@app.route('/api/search/web', methods=['POST'])
@require_auth
def web_search():
    """Perform web search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        max_results = data.get('max_results', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Check if web search is enabled
        search_config = llm_client.config.get('web_search', {})
        if not search_config.get('enabled', False):
            return jsonify({'error': 'Web search is disabled'}), 403
        
        search_result = web_search_feature.search_web(query, max_results, format_for_llm=False)
        
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/chat', methods=['POST'])
@require_auth
def search_chat():
    """Chat with web search context"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', None)
        user_id = request.user['user_id']
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
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
        import time
        search_start_time = time.time()
        
        # Perform web search with keyword extraction
        search_result = web_search_feature.search_web(user_message, search_config.get('max_results', 5), format_for_llm=True)
        search_results = search_result.get('formatted_context', 'No search results available')
        
        search_processing_time = (time.time() - search_start_time) * 1000
        
        # Add user message to conversation memory
        memory.add_message(session_id, 'user', user_message)
        
        # Create enhanced prompt with search results
        enhanced_message = f"""Web Search Results:
{search_results}

User Question: {user_message}

Please answer the user's question using the search results above when relevant. Always cite your sources."""
        
        # Get full conversation context for LLM
        conversation_context = memory.get_context_for_llm(session_id)
        
        # Add search-specific combined system prompt if enabled and not already present
        if conversation_context:
            # Check if system message already exists
            has_system = any(msg['role'] == 'system' for msg in conversation_context)
            if not has_system:
                system_prompt = get_combined_system_prompt('search_mode')
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
        
        return jsonify({
            'response': response_data['content'],
            'session_id': session_id,
            'search_context_used': search_result.get('success', False),
            'search_results_count': search_result.get('result_count', 0),
            'keyword_extraction_used': search_result.get('keyword_extraction_used', False),
            'optimized_queries': search_result.get('queries_tried', [user_message]),
            'successful_query': search_result.get('successful_query'),
            'processing_time': response_data['processing_time'],
            'tokens_per_second': response_data['tokens_per_second'],
            'search_processing_time': search_processing_time
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alias for web search chat to match frontend expectations
@app.route('/api/chat/web-search', methods=['POST'])
@require_auth
def web_search_chat():
    """Web search chat endpoint - alias for /api/search/chat"""
    return search_chat()

@app.route('/api/search/keyword-extraction', methods=['GET'])
@require_auth
def get_keyword_extraction_status():
    """Get keyword extraction settings and status"""
    try:
        return jsonify({
            'enabled': web_search_feature.use_keyword_extraction,
            'extraction_methods': web_search_feature.keyword_extractor.extraction_methods,
            'max_keywords': web_search_feature.keyword_extractor.max_keywords,
            'capabilities': web_search_feature.keyword_extractor.technical_keywords.__len__()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/keyword-extraction/enable', methods=['POST'])
@require_auth
def enable_keyword_extraction():
    """Enable keyword extraction for web searches"""
    try:
        web_search_feature.enable_keyword_extraction()
        return jsonify({'success': True, 'message': 'Keyword extraction enabled'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/keyword-extraction/disable', methods=['POST'])
@require_auth
def disable_keyword_extraction():
    """Disable keyword extraction for web searches"""
    try:
        web_search_feature.disable_keyword_extraction()
        return jsonify({'success': True, 'message': 'Keyword extraction disabled'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/extract-keywords', methods=['POST'])
@require_auth
def extract_keywords_only():
    """Extract keywords from text without performing search"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        extraction_result = web_search_feature.keyword_extractor.extract_keywords(text)
        
        return jsonify({
            'success': True,
            'original_text': text,
            'keywords': extraction_result.get('keywords', []),
            'queries': extraction_result.get('queries', []),
            'method': extraction_result.get('method'),
            'extraction_results': extraction_result.get('extraction_results', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File Management Endpoints

@app.route('/api/files/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload a file for processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        user_id = request.user['user_id']
        
        # Save file
        result = file_handler.save_uploaded_file(
            file.read(), 
            file.filename, 
            user_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
@require_auth
def list_files():
    """List user's uploaded files"""
    try:
        user_id = request.user['user_id']
        files = file_handler.list_user_files(user_id)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>/content', methods=['GET'])
@require_auth
def get_file_content(file_id):
    """Get file content"""
    try:
        user_id = request.user['user_id']
        result = file_handler.read_file_content(file_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>/read', methods=['POST'])
@require_auth
def read_file_with_llm(file_id):
    """Read file content with LLM processing"""
    try:
        data = request.get_json()
        user_question = data.get('question', 'Please analyze this file and provide a summary.')
        session_id = data.get('session_id', None)
        user_id = request.user['user_id']
        
        # Get file content
        file_result = file_handler.read_file_content(file_id, user_id)
        if not file_result['success']:
            return jsonify(file_result), 400
        
        # Create new session if none provided
        if not session_id:
            session_id = memory.create_session(user_id)
        
        # Verify session belongs to current user
        session_data = memory.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({'error': 'Session not found or access denied'}), 403
        
        # Create enhanced prompt with file content
        file_info = file_result['file_info']
        file_content = file_result['content']
        
        enhanced_message = f"""File Analysis Request:

File: {file_info['original_name']}
Type: {file_info['category']} ({file_info['file_type']})
Size: {file_info['file_size']} bytes

File Content:
{file_content}

User Question: {user_question}

Please analyze the file content and answer the user's question."""
        
        # Add user message to conversation memory
        memory.add_message(session_id, 'user', f"[File Analysis] {file_info['original_name']}: {user_question}")
        
        # Get combined system prompt for file mode
        system_prompt = get_combined_system_prompt('file_mode')
        
        # Generate response
        response = llm_client.generate_response(enhanced_message, system_prompt)
        
        # Add assistant response to conversation memory
        memory.add_message(session_id, 'assistant', response)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'file_info': {
                'file_id': file_id,
                'original_name': file_info['original_name'],
                'file_type': file_info['file_type'],
                'file_size': file_info['file_size']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>', methods=['DELETE'])
@require_auth
def delete_file(file_id):
    """Delete a file"""
    try:
        user_id = request.user['user_id']
        success = file_handler.delete_file(file_id, user_id)
        if success:
            return jsonify({'message': 'File deleted successfully'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Document Reading Endpoint

@app.route('/api/document/read', methods=['POST'])
@require_auth
def read_markdown_document():
    """Read the combined markdown document"""
    try:
        data = request.get_json()
        user_question = data.get('question', 'Please provide a summary of the document.')
        session_id = data.get('session_id', None)
        user_id = request.user['user_id']
        
        # Check if combined_data.md exists
        if not os.path.exists('data/combined_data.md'):
            return jsonify({'error': 'Combined data document not found. Please generate it first.'}), 404
        
        # Read the document
        try:
            with open('data/combined_data.md', 'r', encoding='utf-8') as f:
                document_content = f.read()
        except Exception as e:
            return jsonify({'error': f'Error reading document: {str(e)}'}), 500
        
        # Create new session if none provided
        if not session_id:
            session_id = memory.create_session(user_id)
        
        # Verify session belongs to current user
        session_data = memory.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({'error': 'Session not found or access denied'}), 403
        
        # Create enhanced prompt with document content
        enhanced_message = f"""Document Reading Request:

Document: data/combined_data.md
Content Length: {len(document_content)} characters

Document Content:
{document_content}

User Question: {user_question}

Please analyze the document content and answer the user's question."""
        
        # Add user message to conversation memory
        memory.add_message(session_id, 'user', f"[Document Reading] data/combined_data.md: {user_question}")
        
        # Get combined system prompt for document mode
        system_prompt = get_combined_system_prompt('document_mode')
        
        # Generate response
        response = llm_client.generate_response(enhanced_message, system_prompt)
        
        # Add assistant response to conversation memory
        memory.add_message(session_id, 'assistant', response)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'document_info': {
                'name': 'data/combined_data.md',
                'size': len(document_content)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test LLM client status
        llm_status = 'healthy'
        ollama_url = getattr(llm_client, 'ollama_url', 'Not configured')
        model = getattr(llm_client, 'model', 'Not configured')
        
        # Try to ping Ollama to see if it's actually accessible
        try:
            import requests
            if hasattr(llm_client, 'ollama_url') and llm_client.ollama_url:
                response = requests.get(f"{llm_client.ollama_url}/api/tags", timeout=5)
                if response.status_code != 200:
                    llm_status = 'ollama_unreachable'
        except:
            llm_status = 'ollama_unreachable'
        
        return jsonify({
            'status': llm_status,
            'ollama_url': ollama_url,
            'model': model,
            'web_search_enabled': web_search_feature.enabled if web_search_feature else False,
            'keyword_extraction_enabled': web_search_feature.use_keyword_extraction if web_search_feature else False
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'ollama_url': 'Error',
            'model': 'Error'
        }), 500

# Conversation Memory Endpoints

@app.route('/api/conversations', methods=['GET'])
@require_auth
def list_conversations():
    """List user's conversation sessions"""
    try:
        user_id = request.user['user_id']
        conversations = memory.list_sessions(user_id=user_id)
        return jsonify({'conversations': conversations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['POST'])
@require_auth
def create_conversation():
    """Create a new conversation session"""
    try:
        user_id = request.user['user_id']
        session_id = memory.create_session(user_id)
        return jsonify({'session_id': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['GET'])
@require_auth
def get_conversation(session_id):
    """Get a specific conversation session"""
    try:
        user_id = request.user['user_id']
        session_data = memory.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify({'conversation': session_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<session_id>/history', methods=['GET'])
@require_auth
def get_conversation_history(session_id):
    """Get conversation history for a session"""
    try:
        user_id = request.user['user_id']
        session_data = memory.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({'error': 'Session not found'}), 404
        
        history = memory.get_conversation_history(session_id, include_system=False)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['DELETE'])
@require_auth
def delete_conversation(session_id):
    """Delete a conversation session"""
    try:
        user_id = request.user['user_id']
        session_data = memory.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({'error': 'Session not found'}), 404
            
        success = memory.delete_session(session_id)
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify({'message': 'Session deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/clear', methods=['POST'])
@require_auth
def clear_conversations():
    """Clear all user's conversations"""
    try:
        user_id = request.user['user_id']
        deleted_count = memory.clear_all_sessions(user_id)
        return jsonify({'message': f'Cleared {deleted_count} conversations'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/stats', methods=['GET'])
@require_auth
def get_memory_stats():
    """Get user's conversation memory statistics"""
    try:
        user_id = request.user['user_id']
        # Filter stats for current user only
        stats = memory.get_session_stats()
        user_sessions = memory.list_sessions(user_id=user_id)
        user_stats = {
            'total_sessions': len(user_sessions),
            'total_messages': sum(s.get('total_messages', 0) for s in user_sessions),
            'max_context_length': stats['max_context_length'],
            'session_timeout_hours': stats['session_timeout_hours']
        }
        return jsonify({'stats': user_stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Endpoints

@app.route('/api/admin/users', methods=['GET'])
@require_auth
@require_admin
def admin_list_users():
    """Admin: List all users"""
    try:
        users = user_manager.list_users(include_inactive=True)
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['POST'])
@require_auth
@require_admin
def admin_create_user():
    """Admin: Create new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        role = data.get('role', 'user')
        display_name = data.get('display_name', '')
        
        if not username or not password or not email:
            return jsonify({'error': 'Username, password, and email are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if role not in ['user', 'admin']:
            return jsonify({'error': 'Role must be "user" or "admin"'}), 400
        
        success = user_manager.create_user(username, password, email, role, display_name)
        if not success:
            return jsonify({'error': 'Username or email already exists'}), 409
        
        return jsonify({'message': f'User {username} created successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<username>', methods=['PUT'])
@require_auth
@require_admin
def admin_update_user(username):
    """Admin: Update user"""
    try:
        data = request.get_json()
        updates = {}
        
        if 'email' in data:
            updates['email'] = data['email']
        if 'role' in data:
            if data['role'] not in ['user', 'admin']:
                return jsonify({'error': 'Role must be "user" or "admin"'}), 400
            updates['role'] = data['role']
        if 'display_name' in data:
            updates['display_name'] = data['display_name']
        if 'is_active' in data:
            updates['is_active'] = bool(data['is_active'])
        
        success = user_manager.update_user(username, updates)
        if not success:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': f'User {username} updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<username>/reset-password', methods=['POST'])
@require_auth
@require_admin
def admin_reset_password(username):
    """Admin: Reset user password"""
    try:
        data = request.get_json()
        new_password = data.get('new_password', '')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        success = user_manager.reset_password(username, new_password)
        if not success:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': f'Password reset for user {username}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<username>', methods=['DELETE'])
@require_auth
@require_admin
def admin_delete_user(username):
    """Admin: Delete user"""
    try:
        success = user_manager.delete_user(username)
        if not success:
            return jsonify({'error': 'User not found or cannot delete last admin'}), 404
        
        return jsonify({'message': f'User {username} deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/sessions', methods=['GET'])
@require_auth
@require_admin
def admin_list_sessions():
    """Admin: List all active sessions"""
    try:
        sessions = user_manager.get_active_sessions()
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
@require_auth
@require_admin
def admin_get_stats():
    """Admin: Get system statistics"""
    try:
        user_stats = user_manager.get_user_stats()
        memory_stats = memory.get_session_stats()
        
        return jsonify({
            'user_stats': user_stats,
            'memory_stats': memory_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_local_ip():
    """Get the local IP address for network access"""
    import socket
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "Unable to determine IP"

# Web search is integrated directly via WebSearchFeature

def main():
    """Main function to start the server"""
    try:
        config = llm_client.config
        host = config['server']['host']
        port = config['server']['port']
        local_ip = get_local_ip()
        
        print("=" * 60)
        print("HE team LLM assistant - Server Starting")
        print("=" * 60)
        print(f"Server Host: {host}")
        print(f"Server Port: {port}")
        print(f"Ollama URL: {llm_client.ollama_url}")
        print(f"Model: {llm_client.model}")
        print()
        print("Access URLs:")
        print(f"  Local:   http://localhost:{port}")
        if local_ip != "Unable to determine IP":
            print(f"  Network: http://{local_ip}:{port}")
        print()
        print("Network Troubleshooting:")
        print("  1. Ensure Windows Firewall allows Python")
        print("  2. Check if port 3000 is available")
        print("  3. Verify clients are on same network")
        print("  4. Try disabling antivirus temporarily")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == '__main__':
    main()