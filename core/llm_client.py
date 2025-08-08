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
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize LLM client with configuration"""
        self.config = self._load_config(config_path)
        self.ollama_url = self.config["ollama"]["host"]
        self.model = self.config["ollama"]["model"]
        self.timeout = self.config["ollama"]["timeout"]
    
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
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from LLM using Ollama API"""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout / 1000
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response received")
            
        except requests.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid response from Ollama"
    
    def chat_completion(self, messages: list) -> str:
        """Chat completion using Ollama chat API"""
        url = f"{self.ollama_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout / 1000
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "No response received")
            
        except requests.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid response from Ollama"
    
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