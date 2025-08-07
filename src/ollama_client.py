"""Ollama client integration for LLM functionality."""

import ollama
import logging
from typing import List, Dict, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM models."""
    
    def __init__(self, default_model: Optional[str] = None):
        """
        Initialize Ollama client.
        
        Args:
            default_model: Default model to use if none specified
        """
        self.client = ollama.Client()
        self.default_model = default_model or "llama2"  # Default fallback model
        self.available_models = []
        
        # Get available models on initialization
        self.refresh_available_models()
    
    def refresh_available_models(self) -> List[str]:
        """Get list of available Ollama models from the system."""
        try:
            models_response = self.client.list()
            self.available_models = [model['name'] for model in models_response['models']]
            logger.info(f"Found {len(self.available_models)} available models")
            return self.available_models
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            self.available_models = []
            return []
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        if not self.available_models:
            self.refresh_available_models()
        return self.available_models
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        return model_name in self.get_available_models()
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model if it's not available locally.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            self.refresh_available_models()
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate_response(self, prompt: str, model: Optional[str] = None, 
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> Optional[str]:
        """
        Generate response using Ollama model.
        
        Args:
            prompt: The user prompt
            model: Model to use (uses default if None)
            system_prompt: System prompt for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response or None if error
        """
        selected_model = model or self.default_model
        
        # Check if model is available
        if not self.is_model_available(selected_model):
            logger.warning(f"Model {selected_model} not available. Attempting to pull...")
            if not self.pull_model(selected_model):
                logger.error(f"Failed to pull model {selected_model}")
                return None
        
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Generate response
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
            logger.error(f"Error generating response: {e}")
            return None
    
    def generate_with_context(self, query: str, context: str, 
                            model: Optional[str] = None) -> Optional[str]:
        """
        Generate response with RAG context.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            model: Model to use
            
        Returns:
            Generated response
        """
        system_prompt = """You are an AI assistant specialized in analyzing cellphone reviews. 
You have access to a database of positive and negative cellphone reviews, specifically about foldable phones.

Use the provided context to answer questions accurately. If the context doesn't contain 
relevant information, say so clearly. Focus on insights from the review data.

Context format: Reviews are tagged with [POSITIVE] or [NEGATIVE] to indicate sentiment."""
        
        prompt = f"""Based on the following context from cellphone reviews, please answer the user's question.

Context:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the review data provided."""
        
        return self.generate_response(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more factual responses
        )
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        try:
            models_response = self.client.list()
            for model in models_response['models']:
                if model['name'] == model_name:
                    return model
            return None
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return None
    
    def set_default_model(self, model_name: str) -> bool:
        """Set the default model to use."""
        if self.is_model_available(model_name):
            self.default_model = model_name
            logger.info(f"Default model set to: {model_name}")
            return True
        else:
            logger.error(f"Model {model_name} not available")
            return False