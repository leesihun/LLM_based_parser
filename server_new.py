#!/usr/bin/env python3
"""
HE Team LLM Assistant - Main Server
A comprehensive LLM-powered assistant with RAG, file handling, and web search capabilities.
"""

import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Core components
from core.llm_client import LLMClient
from core.conversation_memory import ConversationMemory
from core.user_management import UserManager
from src.rag_system import RAGSystem
from src.file_handler import FileHandler
from src.web_search_feature import WebSearchFeature

# API modules
from api.auth import create_auth_endpoints
from api.chat import create_chat_endpoints
from api.search import create_search_endpoints
from api.system import create_system_endpoints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'he_team_llm_assistant_secret_key'  # Change this in production


def initialize_components():
    """
    Initialize all system components
    
    Returns:
        Tuple of initialized components
    """
    try:
        logger.info("Initializing system components...")
        
        # Initialize core components
        llm_client = LLMClient()
        memory = ConversationMemory()
        user_manager = UserManager()
        rag_system = RAGSystem("config/config.json")
        file_handler = FileHandler()
        
        # Initialize web search with keyword extraction
        search_config = llm_client.config.get('web_search', {})
        web_search_feature = WebSearchFeature(search_config, llm_client)
        
        logger.info("All components initialized successfully")
        return llm_client, memory, user_manager, rag_system, file_handler, web_search_feature
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        raise


def register_routes(llm_client, memory, user_manager, rag_system, file_handler, web_search_feature):
    """
    Register all API routes
    
    Args:
        Components for route registration
    """
    try:
        logger.info("Registering API routes...")
        
        # Create authentication endpoints and get decorators
        require_auth, require_admin = create_auth_endpoints(app, user_manager)
        
        # Create other API endpoints
        create_chat_endpoints(app, llm_client, memory, rag_system, file_handler, web_search_feature, require_auth)
        create_search_endpoints(app, web_search_feature, require_auth)
        create_system_endpoints(app, llm_client, rag_system, web_search_feature, require_auth)
        
        # Static file routes
        @app.route('/')
        def serve_index():
            """Serve the main HTML page"""
            return send_from_directory('static', 'index.html')

        @app.route('/login.html')
        def serve_login():
            """Serve the login page"""
            return send_from_directory('static', 'login.html')
        
        logger.info("All routes registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register routes: {str(e)}")
        raise


def get_local_ip():
    """
    Get local IP address for display
    
    Returns:
        Local IP address string
    """
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine IP"


def main():
    """Main function to start the server"""
    try:
        # Initialize all components
        components = initialize_components()
        llm_client, memory, user_manager, rag_system, file_handler, web_search_feature = components
        
        # Register all routes
        register_routes(*components)
        
        # Get server configuration
        server_config = llm_client.config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        debug = server_config.get("debug", False)
        
        # Display startup information
        local_ip = get_local_ip()
        logger.info("=" * 60)
        logger.info("HE Team LLM Assistant Server Starting")
        logger.info("=" * 60)
        logger.info(f"LLM Model: {llm_client.model}")
        logger.info(f"Ollama URL: {llm_client.ollama_url}")
        logger.info(f"Web Search: {'Enabled' if web_search_feature.enabled else 'Disabled'}")
        logger.info(f"Keyword Extraction: {'Enabled' if web_search_feature.use_keyword_extraction else 'Disabled'}")
        logger.info(f"Server Host: {host}")
        logger.info(f"Server Port: {port}")
        logger.info(f"Local Access: http://localhost:{port}")
        logger.info(f"Network Access: http://{local_ip}:{port}")
        logger.info("=" * 60)
        
        # Start the Flask server
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        raise
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()