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

# Configure logging to suppress INFO backoff messages while keeping our progress
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress backoff INFO messages - they're just normal load balancing
backoff_logger = logging.getLogger('backoff')
backoff_logger.setLevel(logging.WARNING)

# Also suppress ollama client verbose logs
ollama_logger = logging.getLogger('ollama')
ollama_logger.setLevel(logging.WARNING)

# Suppress HTTP request logs from httpx (used by Ollama internally)
httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)

# Also suppress httpcore logs (lower level HTTP library)
httpcore_logger = logging.getLogger('httpcore')
httpcore_logger.setLevel(logging.WARNING)

# Disable ChromaDB telemetry completely to avoid PostHog connection noise
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'false'


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
            # Add configurable timeout settings to prevent hanging
            self.ollama_client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
            logger.info(f"Connecting to Ollama at {ollama_host} for embedding model: {embedding_model} (timeout: {config.ollama_timeout}s)")
            
            # Test connection before proceeding
            self._test_ollama_connection()
            
            # Check if embedding model is available
            self._ensure_embedding_model_available()
            
            logger.info(f"Successfully connected to Ollama and verified embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama at {config.ollama_host}: {e}")
            logger.error("Troubleshooting:")
            logger.error("1. Ensure Ollama is running: 'ollama serve'")
            logger.error("2. Check if host/port is correct in config.py")
            logger.error("3. Try increasing timeout if server is slow")
            logger.error("4. Check if embedding model needs to be pulled: ollama pull nomic-embed-text:latest")
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
                
                if isinstance(model, str):
                    # Model is directly a string (model name)
                    name = model
                    logger.debug(f"Model is string: {name}")
                elif isinstance(model, dict):
                    # Model is a dictionary, try different field names
                    name = model.get('name') or model.get('model') or model.get('id')
                    if not name:
                        # Try to get any string value from the dict
                        for key, value in model.items():
                            if isinstance(value, str) and value:
                                name = value
                                logger.debug(f"Using value from '{key}' field: {name}")
                                break
                else:
                    logger.debug(f"Unknown model type: {type(model)}")
                
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
            # Simple connection test - just verify we can call the API
            logger.debug("Testing basic Ollama connection")
            response = self.ollama_client.list()
            
            # Don't try to parse the response - just confirm we got one
            logger.info("Ollama connection successful - server is responding")
            logger.debug(f"Response type: {type(response)}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            raise ConnectionError(f"Cannot connect to Ollama at {config.ollama_host}. Is Ollama running?")
    
    def _ensure_embedding_model_available(self):
        """Ensure the embedding model is available in Ollama."""
        try:
            logger.debug(f"Testing embedding model availability: {self.embedding_model_name}")
            
            # Skip complex model list parsing - just test if we can generate an embedding
            test_response = self.ollama_client.embeddings(
                model=self.embedding_model_name,
                prompt="test"
            )
            
            if 'embedding' in test_response:
                logger.info(f"Embedding model {self.embedding_model_name} is working correctly")
                return
            else:
                logger.warning(f"Embedding model response missing 'embedding' field")
                
        except Exception as e:
            logger.warning(f"Embedding model {self.embedding_model_name} not available: {e}")
            
            # Try to pull the model if it's not found
            if "not found" in str(e).lower():
                try:
                    logger.info(f"Attempting to pull embedding model: {self.embedding_model_name}")
                    self.ollama_client.pull(self.embedding_model_name)
                    logger.info(f"Successfully pulled embedding model: {self.embedding_model_name}")
                except Exception as pull_error:
                    logger.error(f"Failed to pull embedding model: {pull_error}")
            
            # Don't raise here - let it fail later when actually trying to embed
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama at full GPU speed."""
        embeddings = []
        
        logger.info(f"🚀 Generating embeddings for {len(texts)} texts using model: {self.embedding_model_name}")
        logger.info(f"⚡ Running at full GPU speed - no artificial rate limiting")
        
        import time
        
        for i, text in enumerate(texts):
            try:
                # Show progress at configured intervals
                if (i + 1) % config.embedding_progress_interval == 0 or i == 0 or i == len(texts) - 1:
                    progress_percent = ((i + 1) / len(texts)) * 100
                    logger.info(f"🔄 Processing {i+1}/{len(texts)} ({progress_percent:.1f}%)")
                
                # Generate embedding with minimal retry logic
                max_retries = config.embedding_max_retries
                
                for retry in range(max_retries):
                    try:
                        response = self.ollama_client.embeddings(
                            model=self.embedding_model_name,
                            prompt=text
                        )
                        break  # Success, exit retry loop
                        
                    except Exception as retry_error:
                        if retry < max_retries - 1:
                            # Minimal backoff - let GPU keep working
                            time.sleep(0.1)  # Just 100ms delay
                            logger.debug(f"Retry {retry+1}/{max_retries} for text {i+1}: {retry_error}")
                        else:
                            raise retry_error
                
                if 'embedding' not in response:
                    raise ValueError(f"Invalid response from Ollama: missing 'embedding' field")
                
                embeddings.append(response['embedding'])
                
            except Exception as e:
                logger.error(f"❌ Error generating embedding for text {i+1}/{len(texts)}: {e}")
                logger.error(f"Model: {self.embedding_model_name}")
                logger.error(f"Host: {config.ollama_host}")
                
                # Provide specific error handling
                if "connection" in str(e).lower():
                    raise ConnectionError(f"Connection issues with Ollama at {config.ollama_host}")
                elif "model" in str(e).lower():
                    raise ValueError(f"Model '{self.embedding_model_name}' not available. Run: ollama pull {self.embedding_model_name}")
                else:
                    raise RuntimeError(f"Failed to generate embedding: {e}")
        
        logger.info(f"🎉 Successfully generated {len(embeddings)} embeddings!")
        return embeddings
    
    def add_documents(self, documents):
        """
        Add documents to the vector database with batching to avoid ChromaDB limits.
        
        Args:
            documents: List of text documents (strings)
        """
        if not documents:
            logger.warning("No documents provided to add")
            return
        
        logger.info(f"📚 Adding {len(documents)} text documents...")
        doc_texts = documents
        
        try:
            # Generate embeddings using Ollama at full GPU speed
            logger.info("⚡ Generating embeddings for all documents at maximum speed...")
            embeddings = self._generate_embeddings(doc_texts)
            
            # Add documents to ChromaDB in batches to avoid batch size limits
            chromadb_batch_size = config.chromadb_batch_size
            total_batches = (len(doc_texts) + chromadb_batch_size - 1) // chromadb_batch_size
            
            logger.info(f"📊 Adding documents to ChromaDB in {total_batches} batches of up to {chromadb_batch_size} documents each...")
            
            for batch_idx in range(0, len(doc_texts), chromadb_batch_size):
                batch_end = min(batch_idx + chromadb_batch_size, len(doc_texts))
                batch_num = (batch_idx // chromadb_batch_size) + 1
                
                logger.info(f"💾 Adding batch {batch_num}/{total_batches} ({batch_idx+1}-{batch_end}/{len(doc_texts)}) to ChromaDB...")
                
                # Generate IDs for this batch
                batch_ids = [str(uuid.uuid4()) for _ in range(batch_idx, batch_end)]
                
                # Add batch to collection
                self.collection.add(
                    documents=doc_texts[batch_idx:batch_end],
                    embeddings=embeddings[batch_idx:batch_end],
                    ids=batch_ids
                )
                
                logger.info(f"✅ Batch {batch_num}/{total_batches} added successfully")
            
            logger.info(f"🎉 Successfully added all {len(doc_texts)} documents to RAG system!")
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            logger.error(f"📊 Document count: {len(doc_texts)}")
            logger.error(f"⚙️ ChromaDB batch size: {config.chromadb_batch_size}")
            
            # Provide helpful error context
            if "batch size" in str(e).lower():
                logger.error(f"💡 Try reducing chromadb_batch_size in config.py (currently {config.chromadb_batch_size})")
            elif "memory" in str(e).lower():
                logger.error("💡 Try reducing embedding_batch_size and chromadb_batch_size in config.py")
            
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
                'distances': results['distances'][0],
                'ids': results['ids'][0]
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            return {'documents': [], 'distances': [], 'ids': []}
    
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