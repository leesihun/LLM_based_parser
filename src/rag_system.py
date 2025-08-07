"""RAG (Retrieval-Augmented Generation) system for cellphone review data."""

import chromadb
import logging
from typing import List, Dict, Any, Optional
import ollama
import uuid
from pathlib import Path

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
        
        # Initialize Ollama client
        try:
            self.ollama_client = ollama.Client()
            logger.info(f"Connected to Ollama for embedding model: {embedding_model}")
            
            # Check if embedding model is available
            self._ensure_embedding_model_available()
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
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
    
    def _ensure_embedding_model_available(self):
        """Ensure the embedding model is available in Ollama."""
        try:
            models_response = self.ollama_client.list()
            available_models = [model['name'] for model in models_response['models']]
            
            if self.embedding_model_name not in available_models:
                logger.warning(f"Embedding model {self.embedding_model_name} not found. Attempting to pull...")
                self.ollama_client.pull(self.embedding_model_name)
                logger.info(f"Successfully pulled embedding model: {self.embedding_model_name}")
            else:
                logger.info(f"Embedding model {self.embedding_model_name} is available")
                
        except Exception as e:
            logger.error(f"Error checking embedding model availability: {e}")
            # Don't raise here - let it fail later when actually trying to embed
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        embeddings = []
        
        for text in texts:
            try:
                response = self.ollama_client.embeddings(
                    model=self.embedding_model_name,
                    prompt=text
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                logger.error(f"Error generating embedding for text: {e}")
                raise
        
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