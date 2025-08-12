"""
System API Endpoints
Handles system information, health checks, and configuration
"""

from flask import request, jsonify
from typing import Dict, Any, Tuple
import logging
import requests

logger = logging.getLogger(__name__)


def create_system_endpoints(app, llm_client, rag_system, web_search_feature, require_auth):
    """
    Create system endpoints
    
    Args:
        app: Flask application instance
        llm_client: LLM client instance
        rag_system: RAG system instance
        web_search_feature: Web search feature instance
        require_auth: Authentication decorator
    """
    
    @app.route('/health', methods=['GET'])
    def health_check() -> Tuple[Dict[str, Any], int]:
        """
        System health check endpoint
        
        Returns:
            200: System health status with detailed information
            500: System error
        """
        try:
            # Test LLM client status
            llm_status = 'healthy'
            ollama_url = getattr(llm_client, 'ollama_url', 'Not configured')
            model = getattr(llm_client, 'model', 'Not configured')
            
            # Try to ping Ollama to see if it's actually accessible
            try:
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
                'keyword_extraction_enabled': web_search_feature.use_keyword_extraction if web_search_feature else False,
                'timestamp': None  # Could add current timestamp
            })
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'ollama_url': 'Error',
                'model': 'Error'
            }), 500
    
    @app.route('/api/models', methods=['GET'])
    def get_models() -> Tuple[Dict[str, Any], int]:
        """
        Get available LLM models from Ollama
        
        Returns:
            200: List of available models
            500: Server error
        """
        try:
            models = llm_client.list_models()
            return jsonify({'models': models})
            
        except Exception as e:
            logger.error(f"Get models error: {str(e)}")
            return jsonify({'error': 'Failed to get models'}), 500
    
    @app.route('/api/config', methods=['GET'])
    def get_config() -> Tuple[Dict[str, Any], int]:
        """
        Get current system configuration
        
        Returns:
            200: Current configuration
            500: Server error
        """
        try:
            return jsonify(llm_client.config)
            
        except Exception as e:
            logger.error(f"Get config error: {str(e)}")
            return jsonify({'error': 'Failed to get configuration'}), 500
    
    @app.route('/api/config', methods=['POST'])
    @require_auth
    def update_config() -> Tuple[Dict[str, Any], int]:
        """
        Update system configuration (runtime only, doesn't save to file)
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            model (str, optional): LLM model name
            host (str, optional): Ollama host URL
            timeout (int, optional): Request timeout
            
        Returns:
            200: Configuration updated
            400: Invalid configuration
            401: Authentication required
            500: Server error
        """
        try:
            data = request.get_json()
            
            # Update runtime config
            if 'model' in data:
                llm_client.model = data['model']
                logger.info(f"Model updated to: {data['model']} by user: {request.user['username']}")
                
            if 'host' in data:
                llm_client.ollama_url = data['host']
                logger.info(f"Host updated to: {data['host']} by user: {request.user['username']}")
                
            if 'timeout' in data:
                llm_client.timeout = data['timeout']
                logger.info(f"Timeout updated to: {data['timeout']} by user: {request.user['username']}")
            
            return jsonify({'message': 'Configuration updated successfully'})
            
        except Exception as e:
            logger.error(f"Update config error: {str(e)}")
            return jsonify({'error': 'Failed to update configuration'}), 500
    
    @app.route('/api/rag/stats', methods=['GET'])
    @require_auth
    def get_rag_stats() -> Tuple[Dict[str, Any], int]:
        """
        Get RAG system statistics
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: RAG statistics
            500: Server error
        """
        try:
            stats = rag_system.get_stats()
            return jsonify({'stats': stats})
            
        except Exception as e:
            logger.error(f"Get RAG stats error: {str(e)}")
            return jsonify({'error': 'Failed to get RAG statistics'}), 500