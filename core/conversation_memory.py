#!/usr/bin/env python3
"""
Conversation Memory System for HE team LLM assistant
Handles conversation persistence, session management, and context retention
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class ConversationMemory:
    """Manages conversation sessions and memory persistence"""
    
    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, Dict] = {}
        self.max_context_length = 4000  # Maximum tokens to keep in context
        self.session_timeout = None  # Never expire sessions
        
        # Create storage directory structure for per-user data
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
        
        # Clean old sessions
        self._cleanup_old_sessions()
    
    def _get_user_storage_dir(self, user_id: str) -> str:
        """Get storage directory for specific user"""
        user_dir = os.path.join(self.storage_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def _load_sessions(self):
        """Load existing conversation sessions from disk (all users)"""
        try:
            # Load sessions from user subdirectories
            for user_dir in os.listdir(self.storage_dir):
                user_path = os.path.join(self.storage_dir, user_dir)
                if os.path.isdir(user_path):
                    for filename in os.listdir(user_path):
                        if filename.endswith('.json'):
                            session_id = filename[:-5]  # Remove .json extension
                            filepath = os.path.join(user_path, filename)
                            
                            with open(filepath, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                                self.sessions[session_id] = session_data
            
            # Also load legacy sessions from root directory (for migration)
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    filepath = os.path.join(self.storage_dir, filename)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        if session_id not in self.sessions:  # Don't overwrite user-specific sessions
                            self.sessions[session_id] = session_data
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def _save_session(self, session_id: str):
        """Save a session to disk in user-specific directory"""
        try:
            if session_id in self.sessions:
                session_data = self.sessions[session_id]
                user_id = session_data.get('user_id')
                
                if user_id:
                    # Save in user-specific directory
                    user_dir = self._get_user_storage_dir(user_id)
                    filepath = os.path.join(user_dir, f"{session_id}.json")
                else:
                    # Fallback to root directory for sessions without user_id
                    filepath = os.path.join(self.storage_dir, f"{session_id}.json")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
    
    def _cleanup_old_sessions(self):
        """Remove sessions older than timeout period"""
        # If session_timeout is None, sessions never expire
        if self.session_timeout is None:
            return
            
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            last_activity = datetime.fromisoformat(session_data.get('last_activity', '1970-01-01'))
            if (current_time - last_activity).total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            self._delete_session(session_id)
    
    def _delete_session(self, session_id: str):
        """Delete a session from memory and disk"""
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Remove from disk
        try:
            filepath = os.path.join(self.storage_dir, f"{session_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'id': session_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'messages': [],
            'metadata': {
                'title': 'New Conversation',
                'model': 'llama3.2',
                'total_messages': 0
            }
        }
        
        self._save_session(session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a conversation session"""
        if session_id not in self.sessions:
            return None
        
        # Update last activity
        self.sessions[session_id]['last_activity'] = datetime.now().isoformat()
        self._save_session(session_id)
        
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add a message to a conversation session"""
        if session_id not in self.sessions:
            return False
        
        message = {
            'role': role,  # 'user', 'assistant', 'system'
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.sessions[session_id]['messages'].append(message)
        self.sessions[session_id]['last_activity'] = datetime.now().isoformat()
        self.sessions[session_id]['metadata']['total_messages'] += 1
        
        # Auto-generate title from first user message
        if role == 'user' and self.sessions[session_id]['metadata']['total_messages'] == 1:
            title = content[:50] + "..." if len(content) > 50 else content
            self.sessions[session_id]['metadata']['title'] = title
        
        # Trim conversation if too long
        self._trim_conversation(session_id)
        
        self._save_session(session_id)
        return True
    
    def get_conversation_history(self, session_id: str, include_system: bool = True) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]['messages']
        
        if not include_system:
            messages = [msg for msg in messages if msg['role'] != 'system']
        
        return messages
    
    def get_context_for_llm(self, session_id: str) -> List[Dict]:
        """Get conversation context formatted for LLM API"""
        messages = self.get_conversation_history(session_id, include_system=True)
        
        # Format for Ollama API
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        return formatted_messages
    
    def _trim_conversation(self, session_id: str):
        """Trim conversation to keep within context limits"""
        session = self.sessions[session_id]
        messages = session['messages']
        
        # Calculate approximate token count (rough estimate: 1 token ≈ 4 characters)
        total_chars = sum(len(msg['content']) for msg in messages)
        estimated_tokens = total_chars // 4
        
        if estimated_tokens > self.max_context_length:
            # Keep system messages and recent messages
            system_messages = [msg for msg in messages if msg['role'] == 'system']
            non_system_messages = [msg for msg in messages if msg['role'] != 'system']
            
            # Keep only the most recent messages that fit in context
            keep_chars = self.max_context_length * 4 * 0.8  # Keep 80% for safety
            recent_messages = []
            current_chars = 0
            
            # Add messages from most recent backwards
            for msg in reversed(non_system_messages):
                msg_chars = len(msg['content'])
                if current_chars + msg_chars <= keep_chars:
                    recent_messages.insert(0, msg)
                    current_chars += msg_chars
                else:
                    break
            
            # Combine system messages with recent messages
            session['messages'] = system_messages + recent_messages
            
            # Add a system message to indicate trimming
            if recent_messages:
                trim_message = {
                    'role': 'system',
                    'content': '[Previous conversation history has been trimmed to maintain context limits]',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'type': 'system_trim'}
                }
                session['messages'].insert(-len(recent_messages), trim_message)
    
    def list_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List conversation sessions"""
        sessions = []
        
        for session_id, session_data in self.sessions.items():
            if user_id and session_data.get('user_id') != user_id:
                continue
            
            sessions.append({
                'id': session_id,
                'title': session_data['metadata']['title'],
                'created_at': session_data['created_at'],
                'last_activity': session_data['last_activity'],
                'total_messages': session_data['metadata']['total_messages'],
                'user_id': session_data.get('user_id')
            })
        
        # Sort by last activity (most recent first)
        sessions.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session"""
        if session_id not in self.sessions:
            return False
        
        self._delete_session(session_id)
        return True
    
    def clear_all_sessions(self, user_id: Optional[str] = None) -> int:
        """Clear all sessions (optionally for specific user)"""
        deleted_count = 0
        sessions_to_delete = []
        
        for session_id, session_data in self.sessions.items():
            if user_id is None or session_data.get('user_id') == user_id:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            self._delete_session(session_id)
            deleted_count += 1
        
        return deleted_count
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        total_sessions = len(self.sessions)
        total_messages = sum(session['metadata']['total_messages'] for session in self.sessions.values())
        
        # Calculate storage size
        storage_size = 0
        try:
            for filename in os.listdir(self.storage_dir):
                filepath = os.path.join(self.storage_dir, filename)
                storage_size += os.path.getsize(filepath)
        except Exception:
            storage_size = 0
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'storage_size_bytes': storage_size,
            'storage_size_mb': round(storage_size / (1024 * 1024), 2),
            'max_context_length': self.max_context_length,
            'session_timeout_hours': None if self.session_timeout is None else self.session_timeout / 3600
        }