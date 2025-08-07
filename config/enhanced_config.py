"""
Enhanced Configuration Script for LLM-based Parser System
Configurable settings for embedding models, LLM models, and processing parameters.
"""
import os
from typing import Dict, Any

class EnhancedConfig:
    def __init__(self):
        # LLM Model Configuration
        self.llm_model = os.getenv('LLM_MODEL', 'gemma3:12b')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text:latest')
        
        # Ollama Connection Settings
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.ollama_timeout = int(os.getenv('OLLAMA_TIMEOUT', '120'))
        
        # LLM Generation Parameters
        self.default_temperature = float(os.getenv('DEFAULT_TEMPERATURE', '0.4'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '10000'))
        self.translation_temperature = float(os.getenv('TRANSLATION_TEMPERATURE', '0.3'))
        
        # Processing Settings
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.data_directory = os.getenv('DATA_DIRECTORY', 'data')
        self.output_directory = os.getenv('OUTPUT_DIRECTORY', 'output')
        
        # Language Processing
        self.preserve_original = os.getenv('PRESERVE_ORIGINAL', 'True').lower() == 'true'
        self.auto_detect_language = os.getenv('AUTO_DETECT_LANGUAGE', 'True').lower() == 'true'
        
        # RAG Configuration
        self.rag_context_size = int(os.getenv('RAG_CONTEXT_SIZE', '100'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
        
        # Vector Database Settings
        self.vector_db_path = os.getenv('VECTOR_DB_PATH', 'chroma_db')
        self.collection_name = os.getenv('COLLECTION_NAME', 'review_collection')
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
    
    def get_ollama_url(self) -> str:
        """Get full Ollama service URL."""
        return f"http://{self.ollama_host}"
    
    def get_llm_params(self, temperature: float = None, max_tokens: int = None) -> Dict[str, Any]:
        """Get LLM generation parameters."""
        return {
            "temperature": temperature or self.default_temperature,
            "num_predict": max_tokens or self.max_tokens
        }
    
    def get_translation_params(self) -> Dict[str, Any]:
        """Get parameters optimized for translation tasks."""
        return {
            "temperature": self.translation_temperature,
            "num_predict": self.max_tokens
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"""Enhanced LLM Parser Configuration:
  LLM Model: {self.llm_model}
  Embedding Model: {self.embedding_model}
  Ollama Host: {self.ollama_host}
  Temperature: {self.default_temperature}
  Max Tokens: {self.max_tokens}
  Data Directory: {self.data_directory}
  Output Directory: {self.output_directory}
  Preserve Original: {self.preserve_original}
"""

# Global configuration instance
config = EnhancedConfig()

if __name__ == "__main__":
    print("Enhanced Configuration:")
    print(config)