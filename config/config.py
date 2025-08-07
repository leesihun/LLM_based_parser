"""Configuration management for the LLM-based parser application."""

from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration class for application settings."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        
        # File paths
        self.data_dir = self.base_dir / "data"
        
        # Excel file names (directly configurable here)
        self.positive_filename = "폴드긍정.xlsx"
        self.negative_filename = "폴드부정.xlsx"
        self.positive_file = self.data_dir / self.positive_filename
        self.negative_file = self.data_dir / self.negative_filename
        
        # RAG System settings
        self.rag_collection_name = "cellphone_reviews"
        self.embedding_model = "nomic-embed-text:latest"
        self.chromadb_dir = self.data_dir / "chromadb"
        
        # Ollama settings
        self.default_ollama_model = "gemma3:12b"
        self.ollama_host = "localhost:11434"
        
        # LLM generation settings
        self.default_temperature = 0.7
        self.max_tokens = 1000
        self.rag_context_size = 5
        
        # Similarity threshold for RAG
        self.similarity_threshold = 0.8
        
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
            'positive_filename': self.positive_filename,
            'negative_filename': self.negative_filename,
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
    
    def update_excel_files(self, positive_filename: str = None, negative_filename: str = None):
        """Update Excel file names and paths."""
        if positive_filename:
            self.positive_filename = positive_filename
            self.positive_file = self.data_dir / self.positive_filename
        if negative_filename:
            self.negative_filename = negative_filename
            self.negative_file = self.data_dir / self.negative_filename
    
    def update_ollama_settings(self, host: str = None, model: str = None):
        """Update Ollama settings."""
        if host:
            self.ollama_host = host
        if model:
            self.default_ollama_model = model


# Global configuration instance
config = Config()