#!/usr/bin/env python3
"""
Local LLM Client - Main interface for Ollama LLM communication
Handles loading configuration and communicating with Ollama API
"""

import json
import requests
import sys
from typing import Dict, Any, Optional

class LLMClient:
    """Main class for LLM operations using Ollama"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize LLM client with configuration"""
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize or reinitialize client with current configuration"""
        ollama_config = self.config["ollama"]
        self.ollama_url = ollama_config["host"]
        self.model = ollama_config["model"]
        self.timeout = ollama_config["timeout"] / 1000
        self._preload_model()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_path} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file {config_path}")
            sys.exit(1)
    
    def _preload_model(self) -> None:
        """Preload model to reduce cold start times"""
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": "",  # Empty prompt for preloading
                "stream": False,
                "options": {"num_predict": 1}  # Generate only 1 token
            }
            requests.post(url, json=payload, timeout=30)
        except Exception:
            # Silently fail preloading, don't block initialization
            pass
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from LLM using Ollama API"""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": self.config.get("ollama", {}).get("num_ctx", 4096),  # Context window size
                "temperature": self.config.get("ollama", {}).get("temperature", 0.7),
                "top_p": self.config.get("ollama", {}).get("top_p", 0.9),
                "top_k": self.config.get("ollama", {}).get("top_k", 40),
                "num_gpu": -1,  # Use all available GPUs
                "num_thread": 1  # Reduce CPU competition with GPU
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response received")
            
        except requests.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid response from Ollama"
    
    def chat_completion(self, messages: list, temperature: float = None, max_tokens: int = None) -> dict:
        """Chat completion using Ollama chat API with timing metrics"""
        import time
        url = f"{self.ollama_url}/api/chat"
        
        # Use passed parameters or fall back to config defaults
        effective_temperature = temperature if temperature is not None else self.config.get("ollama", {}).get("temperature", 0.7)
        effective_max_tokens = max_tokens if max_tokens is not None else None
        
        options = {
            "num_ctx": self.config.get("ollama", {}).get("num_ctx", 4096),  # Context window size
            "temperature": effective_temperature,
            "top_p": self.config.get("ollama", {}).get("top_p", 0.9),
            "top_k": self.config.get("ollama", {}).get("top_k", 40),
            "num_gpu": -1,  # Use all available GPUs
            "num_thread": 1  # Reduce CPU competition with GPU
        }
        
        # Add max_tokens if specified (Ollama uses num_predict)
        if effective_max_tokens is not None:
            options["num_predict"] = effective_max_tokens
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000
            
            response.raise_for_status()
            
            result = response.json()
            response_content = result.get("message", {}).get("content", "No response received")
            
            # Calculate tokens per second if available
            tokens_per_second = 0
            if 'eval_count' in result and 'eval_duration' in result:
                tokens_per_second = result['eval_count'] / (result['eval_duration'] / 1000000000)
            
            return {
                'content': response_content,
                'processing_time': processing_time_ms,
                'tokens_per_second': tokens_per_second,
                'eval_count': result.get('eval_count', 0),
                'eval_duration': result.get('eval_duration', 0)
            }
            
        except requests.RequestException as e:
            return {
                'content': f"Error communicating with Ollama: {str(e)}",
                'processing_time': 0,
                'tokens_per_second': 0,
                'eval_count': 0,
                'eval_duration': 0
            }
        except json.JSONDecodeError:
            return {
                'content': "Error: Invalid response from Ollama",
                'processing_time': 0,
                'tokens_per_second': 0,
                'eval_count': 0,
                'eval_duration': 0
            }

    def save_config(self, config_path: Optional[str] = None) -> None:
        """Persist current configuration to disk."""
        target = config_path or self.config_path
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(self.config, handle, ensure_ascii=False, indent=2)
    
    def list_models(self) -> list:
        """List available models from Ollama"""
        url = f"{self.ollama_url}/api/tags"
        
        try:
            response = requests.get(url, timeout=self.timeout / 1000)
            response.raise_for_status()
            
            result = response.json()
            return result.get("models", [])
            
        except requests.RequestException as e:
            print(f"Error fetching models: {str(e)}")
            return []

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 2:
        print("Usage: python llm_client.py '<your prompt>'")
        sys.exit(1)
    
    client = LLMClient()
    prompt = " ".join(sys.argv[1:])
    response = client.generate_response(prompt)
    print(response)

if __name__ == "__main__":
    main()
