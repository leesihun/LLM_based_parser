"""
Standard OllamaClient following exact LLM_IMPLEMENTATION_REFERENCE.md patterns
"""
import ollama
import json
import logging
from typing import Optional, Dict, Any, List
from config.enhanced_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, default_model: Optional[str] = None):
        # Create Ollama client with configured host - exact pattern from reference
        ollama_host = f"http://{config.ollama_host}"
        self.client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
        self.default_model = default_model or config.default_ollama_model
        
        # Always use configured model regardless of detection - exact pattern from reference
        logger.info(f"Using configured model: {self.default_model}")
    
    def generate_response(self, prompt: str, model: Optional[str] = None, 
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> Optional[str]:
        """Standard method for LLM text generation - exact pattern from reference."""
        
        selected_model = model or self.default_model
        
        # Prepare messages in chat format - exact pattern from reference
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Call Ollama with chat interface - exact pattern from reference
            response = self.client.chat(
                model=selected_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            # Graceful degradation - exact pattern from reference
            logger.error(f"Error in LLM processing: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            models = self.client.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def is_model_available(self, model_name: str) -> bool:
        """Model availability check that doesn't block usage - exact pattern from reference."""
        available = self.get_available_models()
        is_available = model_name in available
        
        if not is_available:
            logger.warning(f"Model '{model_name}' not found in available models: {available}")
            logger.info(f"Will attempt to use '{model_name}' anyway - Ollama may auto-pull it")
            
        return True  # Always return True - let Ollama handle model availability

if __name__ == "__main__":
    # Test the client
    client = OllamaClient()
    
    # Test basic functionality
    test_prompt = "Hello, this is a test."
    response = client.generate_response(test_prompt)
    
    if response:
        print(f"✅ Connection successful!")
        print(f"Model: {client.default_model}")
        print(f"Response: {response[:100]}...")
    else:
        print("❌ Connection failed!")
        print("Available models:", client.get_available_models())