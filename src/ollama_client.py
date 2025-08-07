"""Ollama client integration for LLM functionality."""

import ollama
import logging
from typing import List, Dict, Any, Optional
import json
import sys
from pathlib import Path

# Add config to path
sys.path.append(str(Path(__file__).parent.parent))
from config.config import config

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
        # Use configured Ollama host
        ollama_host = f"http://{config.ollama_host}"
        self.client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
        self.default_model = default_model or config.default_ollama_model
        self.available_models = []
        
        logger.info(f"Initializing Ollama client with host: {ollama_host}")
        
        # Try to get available models on initialization, but don't fail if it doesn't work
        try:
            self.refresh_available_models()
        except Exception as e:
            logger.warning(f"Could not refresh models during initialization: {e}")
            logger.info("Will proceed anyway - model detection can be retried later")
    
    def refresh_available_models(self) -> List[str]:
        """Get list of available Ollama models from the system."""
        try:
            models_response = self.client.list()
            logger.debug(f"Raw models response: {models_response}")
            
            # Safely extract model names
            models = []
            if hasattr(models_response, 'models'):
                model_list = models_response.models
            elif isinstance(models_response, dict) and 'models' in models_response:
                model_list = models_response['models']
            else:
                logger.warning(f"Unexpected models response format: {type(models_response)}")
                model_list = []
            
            # Extract names from model entries
            for model in model_list:
                name = None
                if isinstance(model, dict):
                    name = model.get('name') or model.get('model') or model.get('id')
                elif isinstance(model, str):
                    name = model
                elif hasattr(model, 'name'):
                    name = model.name
                
                if name:
                    models.append(name)
            
            self.available_models = models
            logger.info(f"Found {len(self.available_models)} available models: {self.available_models}")
            return self.available_models
            
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            logger.error(f"Host: {config.ollama_host}")
            logger.error("Make sure Ollama is running: ollama serve")
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
                            model: Optional[str] = None, language: str = "auto") -> Optional[str]:
        """
        Generate response with RAG context.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            model: Model to use
            language: Language preference ("auto", "en", "ko")
            
        Returns:
            Generated response
        """
        # Detect language or use specified
        if language == "auto":
            # Simple language detection based on Korean characters
            korean_chars = sum(1 for char in query if '\uac00' <= char <= '\ud7a3')
            total_chars = len([c for c in query if c.isalpha()])
            language = "ko" if korean_chars > total_chars * 0.3 else "en"
        
        # System prompts in both languages
        system_prompts = {
            "en": """You are an AI assistant specialized in analyzing cellphone reviews. 
You have access to a database of positive and negative cellphone reviews, specifically about foldable phones.

Use the provided context to answer questions accurately. If the context doesn't contain 
relevant information, say so clearly. Focus on insights from the review data.

Context format: Reviews are tagged with [POSITIVE] or [NEGATIVE] to indicate sentiment.""",
            
            "ko": """당신은 휴대폰 리뷰 분석 전문 AI 어시스턴트입니다.
폴더블 폰에 대한 긍정적, 부정적 리뷰 데이터베이스에 접근할 수 있습니다.

제공된 맥락을 사용하여 질문에 정확하게 답변하세요. 맥락에 관련 정보가 없다면 명확히 말씀해 주세요. 
리뷰 데이터의 인사이트에 집중하세요.

맥락 형식: 리뷰는 감정을 나타내기 위해 [POSITIVE] 또는 [NEGATIVE]로 태그가 지정됩니다."""
        }
        
        system_prompt = system_prompts.get(language, system_prompts["en"])
        
        # Prompts in both languages
        prompt_templates = {
            "en": """Based on the following context from cellphone reviews, please answer the user's question.

Context:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the review data provided.""",
            
            "ko": """다음 휴대폰 리뷰 맥락을 바탕으로 사용자의 질문에 답변해 주세요.

맥락:
{context}

질문: {query}

제공된 리뷰 데이터를 바탕으로 도움이 되고 정확한 답변을 제공해 주세요."""
        }
        
        prompt_template = prompt_templates.get(language, prompt_templates["en"])
        prompt = prompt_template.format(context=context, query=query)
        
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
            
            # Handle different response formats
            if hasattr(models_response, 'models'):
                model_list = models_response.models
            elif isinstance(models_response, dict) and 'models' in models_response:
                model_list = models_response['models']
            else:
                return None
            
            # Find the matching model
            for model in model_list:
                name = None
                if isinstance(model, dict):
                    name = model.get('name') or model.get('model') or model.get('id')
                elif hasattr(model, 'name'):
                    name = model.name
                
                if name == model_name:
                    return model if isinstance(model, dict) else {'name': name}
            
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