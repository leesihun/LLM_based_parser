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
# Import API endpoints
from api.chat import create_chat_endpoints
from api.conversations import create_conversation_endpoints
from api.model_config import create_model_config_endpoints

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

# Helper functions are now in individual API modules

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

# Chat endpoints are now handled by api/chat.py

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

# RAG chat endpoint is now handled by api/chat.py

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
            'provider': search_result.get('provider'),
            'structured_results': search_result.get('structured_results'),
            'sources': search_result.get('sources', []),
            'answer': search_result.get('answer'),
            'error': search_result.get('error')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Web search chat endpoint is now handled by api/chat.py

@app.route('/api/search/test', methods=['POST'])
@require_auth
def test_web_search():
    """Test web search functionality for debugging"""
    try:
        data = request.get_json()
        query = data.get('query', 'test search query')
        
        # Get search configuration
        search_config = llm_client.config.get('web_search', {})
        
        # Test web search feature status
        capabilities = {
            'web_search_enabled': search_config.get('enabled', False),
            'web_search_feature_available': web_search_feature is not None,
            'keyword_extraction_enabled': getattr(web_search_feature, 'use_keyword_extraction', None),
            'config': search_config
        }
        
        if not web_search_feature:
            return jsonify({
                'error': 'Web search feature not available',
                'capabilities': capabilities
            }), 500
        
        # Test the search
        result = web_search_feature.search_web(query, max_results=3, format_for_llm=False)
        
        return jsonify({
            'query': query,
            'result': result,
            'capabilities': capabilities
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Test failed: {str(e)}',
            'query': query
        }), 500

@app.route('/api/search/extract-keywords', methods=['POST'])
@require_auth
def test_keyword_extraction():
    """Test keyword extraction directly"""
    try:
        data = request.get_json()
        query = data.get('query', 'test query')
        
        if not web_search_feature or not web_search_feature.keyword_extractor:
            return jsonify({
                'error': 'Keyword extractor not available',
                'query': query
            }), 500
        
        # Test keyword extraction directly
        result = web_search_feature.keyword_extractor.extract_keywords(query)
        
        return jsonify({
            'query': query,
            'extraction_result': result,
            'extractor_config': {
                'use_llm': web_search_feature.keyword_extractor.use_llm,
                'extraction_methods': web_search_feature.keyword_extractor.extraction_methods,
                'llm_client_available': web_search_feature.keyword_extractor.llm_client is not None
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Keyword extraction test failed: {str(e)}',
            'query': query
        }), 500

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

# Conversation endpoints are now handled by api/conversations.py

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

# Register API endpoints
create_chat_endpoints(app, llm_client, memory, rag_system, file_handler, web_search_feature, require_auth)
create_conversation_endpoints(app, memory, require_auth)
create_model_config_endpoints(app, llm_client, require_auth)

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
