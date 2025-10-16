#!/usr/bin/env python3
"""
User Management System for HE team LLM assistant
Handles user authentication, session management, and per-user data storage
"""

import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class UserManager:
    """Manages user accounts, authentication, and sessions"""
    
    def __init__(self, users_file: str = "backend/config/users.json", sessions_file: str = "backend/config/user_sessions.json"):
        self.users_file = users_file
        self.sessions_file = sessions_file
        self.users: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = None  # Never expire sessions
        
        # Load existing users and sessions
        self._load_users()
        self._load_sessions()
        
        # Create default admin user if no users exist
        if not self.users:
            self._create_default_admin()
        
        # Clean expired sessions
        self._cleanup_expired_sessions()
    
    def _load_users(self):
        """Load users from file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            self.users = {}
    
    def _save_users(self):
        """Save users to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _load_sessions(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
            self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Store password as plain text"""
        return password
    
    def _generate_salt(self) -> str:
        """Generate a random salt"""
        return secrets.token_hex(32)
    
    def _generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_password = "administrator"  # Change this in production
        self.create_user(
            username="admin",
            password=admin_password,
            email="admin@heteam.com",
            role="admin",
            display_name="Administrator"
        )
        print(f"Default admin user created:")
        print(f"Username: admin")
        print(f"Password: {admin_password}")
        print(f"Please change the password immediately!")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        # If session_timeout is None, sessions never expire
        if self.session_timeout is None:
            return
            
        current_time = datetime.now()
        expired_sessions = []
        
        for session_token, session_data in self.sessions.items():
            last_activity = datetime.fromisoformat(session_data.get('last_activity', '1970-01-01'))
            if (current_time - last_activity).total_seconds() > self.session_timeout:
                expired_sessions.append(session_token)
        
        for session_token in expired_sessions:
            del self.sessions[session_token]
        
        if expired_sessions:
            self._save_sessions()
    
    def create_user(self, username: str, password: str, email: str, role: str = "user", 
                   display_name: str = None) -> bool:
        """Create a new user account"""
        if username in self.users:
            return False
        
        # Check for duplicate email
        for user_data in self.users.values():
            if user_data.get('email', '').lower() == email.lower():
                return False
        
        self.users[username] = {
            'user_id': username,  # Use username as natural language identifier
            'username': username,
            'email': email,
            'password_hash': password,  # Store as plain text
            'salt': '',  # No salt needed for plain text
            'role': role,  # 'admin', 'user'
            'display_name': display_name or username,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'is_active': True,
            'settings': {
                'theme': 'dark',
                'language': 'en',
                'notifications': True
            }
        }
        
        self._save_users()
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials"""
        if username not in self.users:
            return None
        
        user_data = self.users[username]
        if not user_data.get('is_active', True):
            return None
        
        # Verify password (plain text comparison)
        if password != user_data['password_hash']:
            return None
        
        # Update last login
        user_data['last_login'] = datetime.now().isoformat()
        self._save_users()
        
        return {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'role': user_data['role'],
            'display_name': user_data['display_name']
        }
    
    def create_session(self, user_data: Dict) -> str:
        """Create a new user session"""
        session_token = self._generate_session_token()
        
        self.sessions[session_token] = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'role': user_data['role'],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'ip_address': None,  # Can be set by the calling code
            'user_agent': None   # Can be set by the calling code
        }
        
        self._save_sessions()
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate and refresh a session token"""
        if session_token not in self.sessions:
            return None
        
        session_data = self.sessions[session_token]
        
        # Check if session is expired (only if timeout is set)
        if self.session_timeout is not None:
            last_activity = datetime.fromisoformat(session_data['last_activity'])
            if (datetime.now() - last_activity).total_seconds() > self.session_timeout:
                del self.sessions[session_token]
                self._save_sessions()
                return None
        
        # Update last activity
        session_data['last_activity'] = datetime.now().isoformat()
        self._save_sessions()
        
        return session_data
    
    def logout_session(self, session_token: str) -> bool:
        """Logout and remove session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            self._save_sessions()
            return True
        return False
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user data by user ID (now using username as ID)"""
        if user_id in self.users:
            user_data = self.users[user_id]
            # Return safe user data (without password hash)
            return {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role'],
                'display_name': user_data['display_name'],
                'created_at': user_data['created_at'],
                'last_login': user_data['last_login'],
                'is_active': user_data['is_active'],
                'settings': user_data['settings']
            }
        return None
    
    def update_user(self, username: str, updates: Dict) -> bool:
        """Update user information"""
        if username not in self.users:
            return False
        
        user_data = self.users[username]
        
        # Update allowed fields
        allowed_fields = ['email', 'role', 'display_name', 'is_active', 'settings']
        for field, value in updates.items():
            if field in allowed_fields:
                user_data[field] = value
        
        self._save_users()
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if username not in self.users:
            return False
        
        user_data = self.users[username]
        
        # Verify old password (plain text comparison)
        if old_password != user_data['password_hash']:
            return False
        
        # Set new password (plain text)
        user_data['password_hash'] = new_password
        
        self._save_users()
        return True
    
    def reset_password(self, username: str, new_password: str) -> bool:
        """Reset user password (admin function)"""
        if username not in self.users:
            return False
        
        user_data = self.users[username]
        
        # Set new password (plain text)
        user_data['password_hash'] = new_password
        
        self._save_users()
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete user account"""
        if username not in self.users:
            return False
        
        # Don't allow deleting the last admin user
        admin_count = sum(1 for user in self.users.values() 
                         if user.get('role') == 'admin' and user.get('is_active', True))
        
        if self.users[username].get('role') == 'admin' and admin_count <= 1:
            return False
        
        del self.users[username]
        self._save_users()
        
        # Remove all sessions for this user (using username as user_id)
        sessions_to_remove = [
            token for token, session in self.sessions.items()
            if session['user_id'] == username
        ]
        for token in sessions_to_remove:
            del self.sessions[token]
        self._save_sessions()
        
        return True
    
    def list_users(self, include_inactive: bool = False) -> List[Dict]:
        """List all users"""
        users = []
        for username, user_data in self.users.items():
            if not include_inactive and not user_data.get('is_active', True):
                continue
            
            users.append({
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role'],
                'display_name': user_data['display_name'],
                'created_at': user_data['created_at'],
                'last_login': user_data['last_login'],
                'is_active': user_data['is_active']
            })
        
        return sorted(users, key=lambda x: x['created_at'])
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        self._cleanup_expired_sessions()
        sessions = []
        
        for token, session_data in self.sessions.items():
            user_data = self.get_user_by_id(session_data['user_id'])
            if user_data:
                sessions.append({
                    'session_token': token[:8] + '...',  # Partial token for security
                    'username': user_data['username'],
                    'display_name': user_data['display_name'],
                    'created_at': session_data['created_at'],
                    'last_activity': session_data['last_activity'],
                    'ip_address': session_data.get('ip_address', 'Unknown')
                })
        
        return sorted(sessions, key=lambda x: x['last_activity'], reverse=True)
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user management statistics"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.get('is_active', True))
        admin_users = sum(1 for user in self.users.values() 
                         if user.get('role') == 'admin' and user.get('is_active', True))
        
        self._cleanup_expired_sessions()
        active_sessions = len(self.sessions)
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'inactive_users': total_users - active_users,
            'active_sessions': active_sessions,
            'session_timeout_hours': None if self.session_timeout is None else self.session_timeout / 3600
        }
