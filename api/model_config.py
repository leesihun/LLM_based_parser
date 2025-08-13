"""
Model Configuration API Endpoints
Handles dynamic model configuration and switching
"""

from flask import request, jsonify
from typing import Dict, Any, Tuple, List
import logging
import requests
import json

logger = logging.getLogger(__name__)


def create_model_config_endpoints(app, llm_client, require_auth):
    """
    Create model configuration endpoints
    
    Args:
        app: Flask application instance
        llm_client: LLM client instance
        require_auth: Authentication decorator
    """
    
    @app.route('/api/models/available', methods=['GET'])
    @require_auth
    def list_available_models() -> Tuple[Dict[str, Any], int]:
        """
        Get list of available models from Ollama
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: List of available models
            500: Server error
        """
        try:
            # Get available models from Ollama
            ollama_url = llm_client.config.get('ollama', {}).get('host', 'http://localhost:11434')
            
            try:
                response = requests.get(f"{ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    models_data = response.json()
                    models = []
                    
                    for model in models_data.get('models', []):
                        models.append({
                            'name': model.get('name', ''),
                            'size': model.get('size', 0),
                            'modified_at': model.get('modified_at', ''),
                            'digest': model.get('digest', ''),
                            'details': model.get('details', {})
                        })
                    
                    return jsonify({
                        'models': models,
                        'total_count': len(models),
                        'ollama_url': ollama_url
                    })
                else:
                    return jsonify({
                        'error': f'Ollama returned status {response.status_code}',
                        'models': [],
                        'ollama_url': ollama_url
                    }), 500
                    
            except requests.RequestException as e:
                return jsonify({
                    'error': f'Cannot connect to Ollama at {ollama_url}: {str(e)}',
                    'models': [],
                    'ollama_url': ollama_url
                }), 500
                
        except Exception as e:
            logger.error(f"List available models error: {str(e)}")
            return jsonify({'error': 'Failed to get available models'}), 500

    @app.route('/api/models/current', methods=['GET'])
    @require_auth
    def get_current_model() -> Tuple[Dict[str, Any], int]:
        """
        Get current model configuration
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Current model configuration
            500: Server error
        """
        try:
            current_config = llm_client.config.get('ollama', {})
            
            return jsonify({
                'current_model': {
                    'model': current_config.get('model', ''),
                    'host': current_config.get('host', ''),
                    'timeout': current_config.get('timeout', 30000),
                    'num_ctx': current_config.get('num_ctx', 2048),
                    'temperature': current_config.get('temperature', 0.7),
                    'top_p': current_config.get('top_p', 0.9),
                    'top_k': current_config.get('top_k', 40)
                },
                'status': 'active'
            })
            
        except Exception as e:
            logger.error(f"Get current model error: {str(e)}")
            return jsonify({'error': 'Failed to get current model configuration'}), 500

    @app.route('/api/models/configure', methods=['POST'])
    @require_auth
    def configure_model() -> Tuple[Dict[str, Any], int]:
        """
        Configure LLM model parameters
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            model (str, optional): Model name to switch to
            host (str, optional): Ollama host URL
            timeout (int, optional): Request timeout in milliseconds
            num_ctx (int, optional): Context window size
            temperature (float, optional): Sampling temperature (0.0-1.0)
            top_p (float, optional): Top-p sampling (0.0-1.0)
            top_k (int, optional): Top-k sampling
            
        Returns:
            200: Model configured successfully
            400: Invalid parameters
            404: Model not found
            500: Server error
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No configuration provided'}), 400
            
            # Get current configuration
            current_config = llm_client.config.get('ollama', {}).copy()
            changes_made = []
            
            # Validate and apply changes
            if 'model' in data:
                model_name = data['model'].strip()
                if not model_name:
                    return jsonify({'error': 'Model name cannot be empty'}), 400
                
                # Check if model is available
                try:
                    ollama_url = current_config.get('host', 'http://localhost:11434')
                    response = requests.get(f"{ollama_url}/api/tags", timeout=10)
                    if response.status_code == 200:
                        available_models = [m.get('name', '') for m in response.json().get('models', [])]
                        if model_name not in available_models:
                            return jsonify({
                                'error': f'Model "{model_name}" not found in Ollama',
                                'available_models': available_models
                            }), 404
                    else:
                        logger.warning(f"Could not verify model availability: Ollama returned {response.status_code}")
                except requests.RequestException as e:
                    logger.warning(f"Could not verify model availability: {e}")
                
                current_config['model'] = model_name
                changes_made.append(f"model: {model_name}")
            
            if 'host' in data:
                host = data['host'].strip()
                if not host.startswith(('http://', 'https://')):
                    return jsonify({'error': 'Host must start with http:// or https://'}), 400
                current_config['host'] = host
                changes_made.append(f"host: {host}")
            
            if 'timeout' in data:
                timeout = data['timeout']
                if not isinstance(timeout, int) or timeout < 1000 or timeout > 300000:
                    return jsonify({'error': 'Timeout must be between 1000 and 300000 milliseconds'}), 400
                current_config['timeout'] = timeout
                changes_made.append(f"timeout: {timeout}ms")
            
            if 'num_ctx' in data:
                num_ctx = data['num_ctx']
                if not isinstance(num_ctx, int) or num_ctx < 512 or num_ctx > 32768:
                    return jsonify({'error': 'Context size must be between 512 and 32768'}), 400
                current_config['num_ctx'] = num_ctx
                changes_made.append(f"context: {num_ctx}")
            
            if 'temperature' in data:
                temperature = data['temperature']
                if not isinstance(temperature, (int, float)) or temperature < 0.0 or temperature > 1.0:
                    return jsonify({'error': 'Temperature must be between 0.0 and 1.0'}), 400
                current_config['temperature'] = float(temperature)
                changes_made.append(f"temperature: {temperature}")
            
            if 'top_p' in data:
                top_p = data['top_p']
                if not isinstance(top_p, (int, float)) or top_p < 0.0 or top_p > 1.0:
                    return jsonify({'error': 'Top-p must be between 0.0 and 1.0'}), 400
                current_config['top_p'] = float(top_p)
                changes_made.append(f"top_p: {top_p}")
            
            if 'top_k' in data:
                top_k = data['top_k']
                if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
                    return jsonify({'error': 'Top-k must be between 1 and 100'}), 400
                current_config['top_k'] = top_k
                changes_made.append(f"top_k: {top_k}")
            
            if not changes_made:
                return jsonify({'error': 'No valid configuration changes provided'}), 400
            
            # Update the LLM client configuration
            llm_client.config['ollama'] = current_config
            
            # Reinitialize client with new configuration
            try:
                llm_client._initialize_client()
                logger.info(f"Model configuration updated by {request.user['username']}: {', '.join(changes_made)}")
            except Exception as e:
                logger.error(f"Failed to reinitialize LLM client: {e}")
                return jsonify({
                    'error': 'Configuration updated but failed to reinitialize client',
                    'details': str(e)
                }), 500
            
            return jsonify({
                'message': 'Model configuration updated successfully',
                'changes': changes_made,
                'new_config': current_config
            })
            
        except Exception as e:
            logger.error(f"Configure model error: {str(e)}")
            return jsonify({'error': 'Failed to configure model'}), 500

    @app.route('/api/models/test', methods=['POST'])
    @require_auth
    def test_model() -> Tuple[Dict[str, Any], int]:
        """
        Test the current model configuration
        
        Headers:
            Authorization: Bearer <session_token>
            
        Request Body:
            message (str, optional): Test message (default: "Hello, this is a test")
            
        Returns:
            200: Model test results
            500: Server error
        """
        try:
            data = request.get_json() or {}
            test_message = data.get('message', 'Hello, this is a test')
            
            # Test the model with a simple request
            import time
            start_time = time.time()
            
            try:
                response = llm_client.chat_completion([
                    {'role': 'user', 'content': test_message}
                ])
                
                end_time = time.time()
                processing_time = (end_time - start_time) * 1000
                
                if isinstance(response, dict):
                    response_content = response.get('content', '')
                    tokens_per_second = response.get('tokens_per_second', 0)
                else:
                    response_content = str(response)
                    tokens_per_second = 0
                
                return jsonify({
                    'test_successful': True,
                    'model': llm_client.config.get('ollama', {}).get('model', 'unknown'),
                    'test_message': test_message,
                    'response': response_content[:200] + '...' if len(response_content) > 200 else response_content,
                    'processing_time_ms': round(processing_time, 2),
                    'tokens_per_second': tokens_per_second,
                    'response_length': len(response_content)
                })
                
            except Exception as e:
                return jsonify({
                    'test_successful': False,
                    'model': llm_client.config.get('ollama', {}).get('model', 'unknown'),
                    'test_message': test_message,
                    'error': str(e),
                    'error_type': type(e).__name__
                }), 500
                
        except Exception as e:
            logger.error(f"Test model error: {str(e)}")
            return jsonify({'error': 'Failed to test model'}), 500

    @app.route('/api/models/presets', methods=['GET'])
    @require_auth
    def get_model_presets() -> Tuple[Dict[str, Any], int]:
        """
        Get predefined model configuration presets
        
        Headers:
            Authorization: Bearer <session_token>
            
        Returns:
            200: Available presets
            500: Server error
        """
        try:
            presets = {
                'creative': {
                    'name': 'Creative',
                    'description': 'High creativity for creative writing and brainstorming',
                    'temperature': 0.9,
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_ctx': 4096
                },
                'balanced': {
                    'name': 'Balanced',
                    'description': 'Balanced settings for general use',
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_ctx': 4096
                },
                'precise': {
                    'name': 'Precise',
                    'description': 'Low creativity for factual and analytical tasks',
                    'temperature': 0.3,
                    'top_p': 0.7,
                    'top_k': 20,
                    'num_ctx': 4096
                },
                'coding': {
                    'name': 'Coding',
                    'description': 'Optimized for code generation and programming',
                    'temperature': 0.2,
                    'top_p': 0.8,
                    'top_k': 30,
                    'num_ctx': 8192
                },
                'research': {
                    'name': 'Research',
                    'description': 'Large context for research and document analysis',
                    'temperature': 0.4,
                    'top_p': 0.8,
                    'top_k': 25,
                    'num_ctx': 8192
                }
            }
            
            return jsonify({
                'presets': presets,
                'total_count': len(presets)
            })
            
        except Exception as e:
            logger.error(f"Get model presets error: {str(e)}")
            return jsonify({'error': 'Failed to get model presets'}), 500

    @app.route('/api/models/preset/<preset_name>', methods=['POST'])
    @require_auth
    def apply_model_preset(preset_name: str) -> Tuple[Dict[str, Any], int]:
        """
        Apply a predefined model configuration preset
        
        Headers:
            Authorization: Bearer <session_token>
            
        Path Parameters:
            preset_name: Name of preset to apply (creative, balanced, precise, coding, research)
            
        Returns:
            200: Preset applied successfully
            400: Invalid preset
            500: Server error
        """
        try:
            # Get preset configuration
            response = get_model_presets()
            if response[1] != 200:
                return response
            
            presets = response[0].json.get('presets', {})
            
            if preset_name not in presets:
                return jsonify({
                    'error': f'Preset "{preset_name}" not found',
                    'available_presets': list(presets.keys())
                }), 400
            
            preset_config = presets[preset_name]
            
            # Apply the preset configuration
            config_request = {
                'temperature': preset_config['temperature'],
                'top_p': preset_config['top_p'],
                'top_k': preset_config['top_k'],
                'num_ctx': preset_config['num_ctx']
            }
            
            # Use the configure_model endpoint internally
            original_json = request.get_json
            request.get_json = lambda: config_request
            
            try:
                result = configure_model()
                request.get_json = original_json
                
                if result[1] == 200:
                    response_data = result[0].json
                    response_data['preset_applied'] = preset_name
                    response_data['preset_description'] = preset_config['description']
                    return jsonify(response_data)
                else:
                    return result
                    
            except Exception as e:
                request.get_json = original_json
                raise e
                
        except Exception as e:
            logger.error(f"Apply model preset error: {str(e)}")
            return jsonify({'error': 'Failed to apply model preset'}), 500