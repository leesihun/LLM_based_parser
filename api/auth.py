"""
Authentication API Endpoints
Handles user authentication, session management, and authorization
"""

from flask import request, jsonify
from functools import wraps
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def create_auth_endpoints(app, user_manager):
    """
    Create authentication endpoints
    
    Args:
        app: Flask application instance
        user_manager: UserManager instance for handling authentication
    """
    
    def require_auth(f):
        """
        Decorator to require authentication for endpoints
        
        Returns:
            Decorated function that validates user authentication
        """
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
        """
        Decorator to require admin privileges
        
        Returns:
            Decorated function that validates admin privileges
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'user') or request.user.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/api/auth/login', methods=['POST'])
    def login() -> Tuple[Dict[str, Any], int]:
        """
        User login endpoint
        
        Request Body:
            username (str): User's username
            password (str): User's password
            
        Returns:
            200: Login successful with session token and user data
            400: Missing username or password
            401: Invalid credentials
            500: Server error
        """
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            # Authenticate user
            user_data = user_manager.authenticate_user(username, password)
            if not user_data:
                logger.warning(f"Failed login attempt for username: {username}")
                return jsonify({'error': 'Invalid username or password'}), 401
            
            # Create session
            session_token = user_manager.create_session(user_data)
            logger.info(f"User {username} logged in successfully")
            
            return jsonify({
                'session_token': session_token,
                'user': user_data,
                'message': 'Login successful'
            })
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({'error': 'Login failed'}), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    @require_auth
    def logout() -> Tuple[Dict[str, Any], int]:
        """
        User logout endpoint
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Logout successful
            401: Authentication required
            500: Server error
        """
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                user_manager.invalidate_session(token)
                logger.info(f"User {request.user.get('username')} logged out")
            
            return jsonify({'message': 'Logout successful'})
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return jsonify({'error': 'Logout failed'}), 500
    
    @app.route('/api/auth/me', methods=['GET'])
    @require_auth
    def get_current_user() -> Tuple[Dict[str, Any], int]:
        """
        Get current authenticated user information
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: User information
            401: Authentication required
            500: Server error
        """
        try:
            return jsonify({'user': request.user})
            
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return jsonify({'error': 'Failed to get user information'}), 500
    
    @app.route('/api/auth/change-password', methods=['POST'])
    @require_auth
    def change_password() -> Tuple[Dict[str, Any], int]:
        """
        Change user password endpoint
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            old_password (str): Current password
            new_password (str): New password
            
        Returns:
            200: Password changed successfully
            400: Missing or invalid password
            401: Authentication required or wrong old password
            500: Server error
        """
        try:
            data = request.get_json()
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            
            if not old_password or not new_password:
                return jsonify({'error': 'Old and new passwords are required'}), 400
            
            if len(new_password) < 4:
                return jsonify({'error': 'New password must be at least 4 characters'}), 400
            
            username = request.user['username']
            success = user_manager.change_password(username, old_password, new_password)
            
            if not success:
                return jsonify({'error': 'Invalid old password'}), 401
            
            logger.info(f"Password changed for user: {username}")
            return jsonify({'message': 'Password changed successfully'})
            
        except Exception as e:
            logger.error(f"Change password error: {str(e)}")
            return jsonify({'error': 'Failed to change password'}), 500
    
    # Return decorators for use in other modules
    return require_auth, require_admin