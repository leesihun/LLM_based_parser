"""
Conversation Management API Endpoints
Handles conversation listing, creation, and management
"""

from flask import request, jsonify
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def create_conversation_endpoints(app, memory, require_auth):
    """
    Create conversation management endpoints
    
    Args:
        app: Flask application instance
        memory: Conversation memory manager
        require_auth: Authentication decorator
    """
    
    @app.route('/api/conversations', methods=['GET'])
    @require_auth
    def list_conversations() -> Tuple[Dict[str, Any], int]:
        """
        List user's conversation sessions
        
        Headers:
            Authorization: Bearer <session_token>
            
        Query Parameters:
            limit (int, optional): Maximum number of conversations to return (default: 50)
            
        Returns:
            200: List of conversations
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            limit = request.args.get('limit', 50, type=int)
            
            conversations = memory.list_sessions(user_id=user_id, limit=limit)
            
            logger.info(f"Listed conversations - User: {request.user['username']}, Count: {len(conversations)}")
            
            return jsonify({'conversations': conversations})
            
        except Exception as e:
            logger.error(f"List conversations error: {str(e)}")
            return jsonify({'error': 'Failed to list conversations'}), 500

    @app.route('/api/conversations', methods=['POST'])
    @require_auth
    def create_conversation() -> Tuple[Dict[str, Any], int]:
        """
        Create a new conversation session
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: New conversation session ID
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            session_id = memory.create_session(user_id)
            
            logger.info(f"Created conversation - User: {request.user['username']}, Session: {session_id}")
            
            return jsonify({'session_id': session_id})
            
        except Exception as e:
            logger.error(f"Create conversation error: {str(e)}")
            return jsonify({'error': 'Failed to create conversation'}), 500

    @app.route('/api/conversations/<session_id>', methods=['GET'])
    @require_auth
    def get_conversation(session_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get a specific conversation session
        
        Headers:
            Authorization: Bearer <session_token>
            
        Path Parameters:
            session_id: Conversation session ID
            
        Returns:
            200: Conversation session data
            403: Session access denied
            404: Session not found
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            session_data = memory.get_session(session_id)
            
            if not session_data:
                return jsonify({'error': 'Session not found'}), 404
                
            if session_data.get('user_id') != user_id:
                return jsonify({'error': 'Session access denied'}), 403
            
            logger.info(f"Retrieved conversation - User: {request.user['username']}, Session: {session_id}")
            
            return jsonify({'conversation': session_data})
            
        except Exception as e:
            logger.error(f"Get conversation error: {str(e)}")
            return jsonify({'error': 'Failed to get conversation'}), 500

    @app.route('/api/conversations/<session_id>/history', methods=['GET'])
    @require_auth
    def get_conversation_history(session_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get conversation history for a session
        
        Headers:
            Authorization: Bearer <session_token>
            
        Path Parameters:
            session_id: Conversation session ID
            
        Query Parameters:
            include_system (bool, optional): Include system messages (default: false)
            
        Returns:
            200: Conversation history
            403: Session access denied
            404: Session not found
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            include_system = request.args.get('include_system', 'false').lower() == 'true'
            
            session_data = memory.get_session(session_id)
            
            if not session_data:
                return jsonify({'error': 'Session not found'}), 404
                
            if session_data.get('user_id') != user_id:
                return jsonify({'error': 'Session access denied'}), 403
            
            history = memory.get_conversation_history(session_id, include_system=include_system)
            
            logger.info(f"Retrieved conversation history - User: {request.user['username']}, Session: {session_id}, Messages: {len(history)}")
            
            return jsonify({'history': history, 'session_id': session_id})
            
        except Exception as e:
            logger.error(f"Get conversation history error: {str(e)}")
            return jsonify({'error': 'Failed to get conversation history'}), 500

    @app.route('/api/conversations/<session_id>', methods=['DELETE'])
    @require_auth
    def delete_conversation(session_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete a conversation session
        
        Headers:
            Authorization: Bearer <session_token>
            
        Path Parameters:
            session_id: Conversation session ID
            
        Returns:
            200: Success message
            403: Session access denied
            404: Session not found
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            session_data = memory.get_session(session_id)
            
            if not session_data:
                return jsonify({'error': 'Session not found'}), 404
                
            if session_data.get('user_id') != user_id:
                return jsonify({'error': 'Session access denied'}), 403
                
            success = memory.delete_session(session_id)
            if not success:
                return jsonify({'error': 'Failed to delete session'}), 500
            
            logger.info(f"Deleted conversation - User: {request.user['username']}, Session: {session_id}")
            
            return jsonify({'message': 'Session deleted successfully'})
            
        except Exception as e:
            logger.error(f"Delete conversation error: {str(e)}")
            return jsonify({'error': 'Failed to delete conversation'}), 500

    @app.route('/api/conversations/clear', methods=['POST'])
    @require_auth
    def clear_conversations() -> Tuple[Dict[str, Any], int]:
        """
        Clear all user's conversations
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Success message with count
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            deleted_count = memory.clear_all_sessions(user_id)
            
            logger.info(f"Cleared conversations - User: {request.user['username']}, Count: {deleted_count}")
            
            return jsonify({'message': f'Cleared {deleted_count} conversations', 'deleted_count': deleted_count})
            
        except Exception as e:
            logger.error(f"Clear conversations error: {str(e)}")
            return jsonify({'error': 'Failed to clear conversations'}), 500

    @app.route('/api/conversations/stats', methods=['GET'])
    @require_auth
    def get_conversation_stats() -> Tuple[Dict[str, Any], int]:
        """
        Get user's conversation statistics
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Conversation statistics
            500: Server error
        """
        try:
            user_id = request.user['user_id']
            
            # Get user-specific stats
            user_sessions = memory.list_sessions(user_id=user_id)
            global_stats = memory.get_session_stats()
            
            user_stats = {
                'total_sessions': len(user_sessions),
                'total_messages': sum(s.get('total_messages', 0) for s in user_sessions),
                'max_context_length': global_stats['max_context_length'],
                'session_timeout_hours': global_stats['session_timeout_hours']
            }
            
            logger.info(f"Retrieved conversation stats - User: {request.user['username']}")
            
            return jsonify({'stats': user_stats})
            
        except Exception as e:
            logger.error(f"Get conversation stats error: {str(e)}")
            return jsonify({'error': 'Failed to get conversation stats'}), 500