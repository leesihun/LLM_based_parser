"""RAG (Retrieval-Augmented Generation) system for cellphone review data."""

import chromadb
import logging
from typing import List, Dict, Any, Optional
import ollama
import uuid
from pathlib import Path
import sys

# Add config to path
sys.path.append(str(Path(__file__).parent.parent))
from config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """Handles document storage, retrieval, and vector embeddings for RAG."""
    
    def __init__(self, collection_name: str = "cellphone_reviews", 
                 embedding_model: str = "nomic-embed-text:latest",
                 persist_directory: str = "data/chromadb"):
        """
        Initialize RAG system with ChromaDB and Ollama embeddings.
        
        Args:
            collection_name: Name for the ChromaDB collection
            embedding_model: Ollama model for embeddings
            persist_directory: Directory to persist ChromaDB data
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Ollama client with configured host
        try:
            ollama_host = f"http://{config.ollama_host}"
            self.ollama_client = ollama.Client(host=ollama_host)
            logger.info(f"Connecting to Ollama at {ollama_host} for embedding model: {embedding_model}")
            
            # Test connection before proceeding
            self._test_ollama_connection()
            
            # Check if embedding model is available
            self._ensure_embedding_model_available()
            
            logger.info(f"Successfully connected to Ollama and verified embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama at {config.ollama_host}: {e}")
            logger.error("Troubleshooting:")
            logger.error("1. Ensure Ollama is running: 'ollama serve'")
            logger.error("2. Check if host/port is correct in .env: OLLAMA_HOST=localhost:11434")
            logger.error(f"3. Test connection: curl http://{config.ollama_host}/api/tags")
            raise
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Cellphone reviews for RAG system"}
            )
            logger.info(f"Connected to ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def _safe_extract_model_names(self, response):
        """Safely extract model names from Ollama response."""
        try:
            models = []
            
            # Handle different response structures
            if hasattr(response, 'keys') and 'models' in response:
                model_list = response['models']
                logger.debug(f"Found 'models' key with {len(model_list)} items")
            elif isinstance(response, list):
                model_list = response
                logger.debug(f"Using response as direct list with {len(model_list)} items")
            else:
                logger.warning(f"Unexpected response structure: {type(response)}")
                return []
            
            # Extract names from each model entry
            for model in model_list:
                name = None
                if isinstance(model, dict):
                    name = model.get('name') or model.get('model') or model.get('id')
                elif isinstance(model, str):
                    name = model
                
                if name:
                    models.append(name)
            
            return models
            
        except Exception as e:
            logger.error(f"Error extracting model names: {e}")
            logger.debug(f"Raw response: {response}")
            return []

    def _test_ollama_connection(self):
        """Test connection to Ollama server."""
        try:
            # Test basic connection by listing models
            logger.debug("Testing Ollama connection by listing models")
            models_response = self.ollama_client.list()
            
            # Safe extraction
            available_models = self._safe_extract_model_names(models_response)
            
            if available_models:
                logger.info(f"Ollama connection successful. Available models: {len(available_models)}")
                logger.debug(f"Available models: {available_models}")
                return True
            else:
                logger.warning("Connected to Ollama but no models found or couldn't parse response")
                logger.debug(f"Raw response: {models_response}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            raise ConnectionError(f"Cannot connect to Ollama at {config.ollama_host}. Is Ollama running?")
    
    def _ensure_embedding_model_available(self):
        """Ensure the embedding model is available in Ollama."""
        try:
            logger.debug("Checking embedding model availability")
            models_response = self.ollama_client.list()
            
            # Safe extraction
            available_models = self._safe_extract_model_names(models_response)
            
            if not available_models:
                logger.warning("Could not parse model list from Ollama response")
                logger.debug(f"Raw response: {models_response}")
                return
            
            logger.debug(f"Available models: {available_models}")
            logger.debug(f"Looking for embedding model: {self.embedding_model_name}")
            
            if self.embedding_model_name not in available_models:
                logger.warning(f"Embedding model {self.embedding_model_name} not found. Attempting to pull...")
                try:
                    self.ollama_client.pull(self.embedding_model_name)
                    logger.info(f"Successfully pulled embedding model: {self.embedding_model_name}")
                except Exception as pull_error:
                    logger.error(f"Failed to pull embedding model: {pull_error}")
            else:
                logger.info(f"Embedding model {self.embedding_model_name} is available")
                
        except Exception as e:
            logger.error(f"Error checking embedding model availability: {e}")
            logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            # Don't raise here - let it fail later when actually trying to embed
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        embeddings = []
        
        logger.debug(f"Generating embeddings for {len(texts)} texts using model: {self.embedding_model_name}")
        
        for i, text in enumerate(texts):
            try:
                # Truncate text preview for logging
                text_preview = text[:100] + "..." if len(text) > 100 else text
                logger.debug(f"Processing text {i+1}/{len(texts)}: {text_preview}")
                
                response = self.ollama_client.embeddings(
                    model=self.embedding_model_name,
                    prompt=text
                )
                
                if 'embedding' not in response:
                    raise ValueError(f"Invalid response from Ollama: missing 'embedding' field")
                
                embeddings.append(response['embedding'])
                
            except Exception as e:
                logger.error(f"Error generating embedding for text {i+1}/{len(texts)}: {e}")
                logger.error(f"Model: {self.embedding_model_name}")
                logger.error(f"Host: {config.ollama_host}")
                logger.error(f"Text preview: {text[:200]}...")
                
                # Provide specific error handling
                if "connection" in str(e).lower():
                    raise ConnectionError(f"Lost connection to Ollama at {config.ollama_host}. Check if Ollama is still running.")
                elif "model" in str(e).lower():
                    raise ValueError(f"Model '{self.embedding_model_name}' not available. Run: ollama pull {self.embedding_model_name}")
                else:
                    raise RuntimeError(f"Failed to generate embedding: {e}")
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict]] = None):
        """
        Add documents to the vector database.
        
        Args:
            documents: List of text documents to add
            metadata: Optional list of metadata dictionaries for each document
        """
        if not documents:
            logger.warning("No documents provided to add")
            return
        
        try:
            # Generate embeddings using Ollama
            embeddings = self._generate_embeddings(documents)
            
            # Generate IDs
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # Prepare metadata
            if metadata is None:
                metadata = [{"source": "excel_file"} for _ in documents]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to RAG system")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system for relevant documents.
        
        Args:
            query_text: The query string
            n_results: Number of results to return
            
        Returns:
            Dictionary containing query results
        """
        try:
            # Generate query embedding using Ollama
            query_embedding = self._generate_embeddings([query_text])
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            logger.info(f"Retrieved {len(results['documents'][0])} documents for query")
            
            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0],
                'ids': results['ids'][0]
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
    
    def get_context_for_query(self, query_text: str, n_results: int = 5) -> str:
        """
        Get formatted context string for a query.
        
        Args:
            query_text: The query string
            n_results: Number of results to include in context
            
        Returns:
            Formatted context string
        """
        results = self.query(query_text, n_results)
        
        if not results['documents']:
            return "No relevant context found."
        
        context_parts = []
        for i, (doc, distance) in enumerate(zip(results['documents'], results['distances'])):
            # Only include highly relevant results (lower distance = more similar)
            if distance < 0.8:  # Adjust threshold as needed
                context_parts.append(f"Context {i+1}: {doc}")
        
        if not context_parts:
            return "No highly relevant context found."
        
        return "\n\n".join(context_parts)
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Cellphone reviews for RAG system"}
            )
            logger.info("Cleared RAG collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the current collection."""
        try:
            count = self.collection.count()
            return {
                'document_count': count,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'document_count': 0, 'collection_name': self.collection_name}