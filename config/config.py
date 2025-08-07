"""Configuration management for the LLM-based parser application."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for application settings."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        
        # File paths
        self.data_dir = self.base_dir / "data"
        self.positive_file = self.data_dir / "fold_positive.xlsx"
        self.negative_file = self.data_dir / "fold_negative.xlsx"
        
        # RAG System settings
        self.rag_collection_name = os.getenv("RAG_COLLECTION_NAME", "cellphone_reviews")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        self.chromadb_dir = self.data_dir / "chromadb"
        
        # Ollama settings
        self.default_ollama_model = os.getenv("DEFAULT_OLLAMA_MODEL", "gemma3:12b")
        self.ollama_host = os.getenv("OLLAMA_HOST", "localhost:11434")
        
        # LLM generation settings
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.rag_context_size = int(os.getenv("RAG_CONTEXT_SIZE", "5"))
        
        # Similarity threshold for RAG
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(exist_ok=True)
        self.chromadb_dir.mkdir(exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'base_dir': str(self.base_dir),
            'data_dir': str(self.data_dir),
            'positive_file': str(self.positive_file),
            'negative_file': str(self.negative_file),
            'rag_collection_name': self.rag_collection_name,
            'embedding_model': self.embedding_model,
            'chromadb_dir': str(self.chromadb_dir),
            'default_ollama_model': self.default_ollama_model,
            'ollama_host': self.ollama_host,
            'default_temperature': self.default_temperature,
            'max_tokens': self.max_tokens,
            'rag_context_size': self.rag_context_size,
            'similarity_threshold': self.similarity_threshold
        }
    
    def get_file_status(self) -> Dict[str, bool]:
        """Check status of required files."""
        return {
            'positive_file_exists': self.positive_file.exists(),
            'negative_file_exists': self.negative_file.exists(),
            'data_dir_exists': self.data_dir.exists(),
            'chromadb_dir_exists': self.chromadb_dir.exists()
        }
    
    @classmethod
    def from_env_file(cls, env_file_path: Optional[str] = None):
        """Create configuration from specific .env file."""
        if env_file_path:
            load_dotenv(env_file_path)
        return cls()


# Global configuration instance
config = Config()