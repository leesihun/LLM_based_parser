#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) System
Uses ChromaDB for vector storage with configurable Ollama embedding models
"""

import os

# Disable ChromaDB telemetry before importing
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
import logging
import json
import requests
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Try to import ChromaDB types, fallback if not available
try:
    from chromadb.api.types import EmbeddingFunction, Embeddings
    CHROMADB_TYPES_AVAILABLE = True
except ImportError:
    # Fallback for older ChromaDB versions
    EmbeddingFunction = object
    Embeddings = List[List[float]]
    CHROMADB_TYPES_AVAILABLE = False

class OllamaEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function that uses Ollama API"""
    
    def __init__(self, model: str, ollama_host: str, batch_size: int = 50):
        """
        Initialize Ollama embedding function
        
        Args:
            model (str): Ollama embedding model name
            ollama_host (str): Ollama server host URL
            batch_size (int): Batch size for embedding requests
        """
        self.model = model
        self.ollama_host = ollama_host.rstrip('/')
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
        
    def __call__(self, input: List[str]) -> Embeddings:
        """
        Generate embeddings for a list of texts (ChromaDB compatible signature)
        
        Args:
            input (List[str]): List of text strings to embed
            
        Returns:
            Embeddings: List of embedding vectors in ChromaDB format
        """
        embeddings = []
        
        # Process texts in batches
        for i in range(0, len(input), self.batch_size):
            batch = input[i:i + self.batch_size]
            batch_embeddings = self._get_batch_embeddings(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def _get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts"""
        embeddings = []
        
        for text in texts:
            try:
                embedding = self._get_single_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                self.logger.error(f"Error getting embedding for text: {str(e)}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 768)  # Assuming 768 dimensions for nomic-embed-text
        
        return embeddings
    
    def _get_single_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        url = f"{self.ollama_host}/api/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = requests.post(
                url, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if 'embedding' in result:
                return result['embedding']
            else:
                raise Exception(f"No embedding in response: {result}")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error for embedding: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing embedding response: {str(e)}")
            raise

class RAGSystem:
    """RAG system for document retrieval and context generation with configurable embedding"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize RAG system with configuration
        
        Args:
            config_path (str): Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.rag_config = self.config.get("rag", {})
        
        # Extract configuration values
        self.embedding_config = self.rag_config.get("embedding", {})
        self.collection_config = self.rag_config.get("collection", {})
        self.chunking_config = self.rag_config.get("chunking", {})
        self.search_config = self.rag_config.get("search", {})
        self.performance_config = self.rag_config.get("performance", {})
        
        # Set up embedding function
        self.embedding_function = self._create_embedding_function()
        
        # Initialize ChromaDB client
        persist_dir = self.collection_config.get("persist_directory", "./data/chroma_db")
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Get or create collection with custom embedding
        collection_name = self.collection_config.get("name", "documents")
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            self.logger.info(f"Loaded existing collection: {collection_name}")
        except Exception as e:
            self.logger.info(f"Collection {collection_name} not found or incompatible, creating new one: {str(e)}")
            
            # If collection exists but with different embedding function, delete it
            try:
                self.client.delete_collection(name=collection_name)
                self.logger.info(f"Deleted incompatible collection: {collection_name}")
            except:
                pass  # Collection didn't exist
                
            # Create new collection
            try:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                self.logger.info(f"Created new collection: {collection_name}")
            except Exception as create_error:
                error_msg = str(create_error)
                if "signature" in error_msg or "__call__" in error_msg:
                    detailed_error = f"""
ChromaDB Embedding Function Signature Error:
- Error: {error_msg}
- This usually means the embedding function doesn't match ChromaDB's expected interface
- Check that Ollama is running: ollama serve  
- Check that the model is available: ollama list | grep nomic-embed-text
- Try clearing ChromaDB: python fix_rag_collection.py clear
"""
                    self.logger.error(detailed_error)
                    raise Exception(f"ChromaDB embedding function signature error. Check Ollama is running and model is available. Full error: {error_msg}")
                else:
                    self.logger.error(f"Failed to create collection {collection_name}: {error_msg}")
                    raise
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file {config_path} not found")
            # Return default config
            return self._get_default_config()
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file {config_path}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default RAG configuration"""
        return {
            "rag": {
                "embedding": {
                    "provider": "ollama",
                    "model": "nomic-embed-text:latest",
                    "ollama_host": "http://localhost:11434",
                    "dimensions": 768,
                    "batch_size": 50
                },
                "collection": {
                    "name": "documents",
                    "persist_directory": "./data/chroma_db"
                },
                "chunking": {
                    "strategy": "semantic",
                    "chunk_size": 1000,
                    "overlap": 200,
                    "min_chunk_size": 100,
                    "max_chunk_size": 2000
                },
                "search": {
                    "default_results": 5,
                    "max_results": 20,
                    "max_context_length": 3000,
                    "similarity_threshold": 0.7
                }
            }
        }
    
    def _create_embedding_function(self):
        """Create embedding function based on configuration"""
        provider = self.embedding_config.get("provider", "ollama")
        
        if provider == "ollama":
            model = self.embedding_config.get("model", "nomic-embed-text:latest")
            host = self.embedding_config.get("ollama_host", "http://localhost:11434")
            batch_size = self.embedding_config.get("batch_size", 50)
            
            return OllamaEmbeddingFunction(model, host, batch_size)
        else:
            self.logger.warning(f"Unknown embedding provider: {provider}, using default")
            return None  # ChromaDB will use default
    
    def check_embedding_model_availability(self) -> bool:
        """Check if the configured embedding model is available"""
        try:
            model = self.embedding_config.get("model", "nomic-embed-text:latest")
            host = self.embedding_config.get("ollama_host", "http://localhost:11434")
            
            # Try to get a test embedding
            test_embedding = self.embedding_function._get_single_embedding("test")
            
            if test_embedding and len(test_embedding) > 0:
                self.logger.info(f"Embedding model {model} is available and working")
                return True
            else:
                self.logger.error(f"Embedding model {model} returned empty result")
                return False
                
        except Exception as e:
            self.logger.error(f"Embedding model availability check failed: {str(e)}")
            return False
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks based on configuration
        
        Args:
            text (str): Text to chunk
            
        Returns:
            List[str]: List of text chunks
        """
        chunk_size = self.chunking_config.get("chunk_size", 1000)
        overlap = self.chunking_config.get("overlap", 200)
        min_size = self.chunking_config.get("min_chunk_size", 100)
        max_size = self.chunking_config.get("max_chunk_size", 2000)
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to find a good breaking point
            if end < len(text):
                # Look for paragraph break first
                para_break = text.rfind('\n\n', start, end)
                if para_break != -1 and para_break > start:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = text.rfind('.', start, end)
                    if sent_break != -1 and sent_break > start:
                        end = sent_break + 1
                    else:
                        # Look for word boundary
                        word_break = text.rfind(' ', start, end)
                        if word_break != -1 and word_break > start:
                            end = word_break
            
            chunk = text[start:end].strip()
            
            # Only add chunk if it meets size requirements
            if chunk and len(chunk) >= min_size:
                # Truncate if too long
                if len(chunk) > max_size:
                    chunk = chunk[:max_size]
                chunks.append(chunk)
            
            start = max(end - overlap, start + 1)  # Prevent infinite loop
        
        return chunks
    
    def generate_document_id(self, content: str) -> str:
        """Generate unique ID for document based on content hash"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_metadata_from_chunk(self, chunk: str, source_file: str) -> Dict[str, Any]:
        """Extract metadata from chunk content"""
        metadata = {
            "source": source_file,
            "chunk_length": len(chunk),
            "type": "unknown"
        }
        
        # Try to detect content type
        if chunk.startswith('# '):
            metadata["type"] = "title"
        elif chunk.startswith('## '):
            metadata["type"] = "section"
        elif chunk.startswith('### '):
            metadata["type"] = "subsection"
        elif '|' in chunk and '---' in chunk:
            metadata["type"] = "table"
        else:
            metadata["type"] = "content"
        
        # Extract section name if available
        lines = chunk.split('\n')
        for line in lines:
            if line.startswith('#'):
                metadata["section"] = line.strip('#').strip()
                break
        
        return metadata
    
    def ingest_document(self, file_path: str, force_reload: bool = False) -> bool:
        """
        Ingest document into RAG system
        
        Args:
            file_path (str): Path to markdown file
            force_reload (bool): Force reload even if already exists
            
        Returns:
            bool: Success status
        """
        try:
            if not Path(file_path).exists():
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Read document
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if document already exists
            doc_id = self.generate_document_id(content)
            
            if not force_reload:
                try:
                    existing = self.collection.get(ids=[doc_id])
                    if existing['ids']:
                        self.logger.info(f"Document already exists: {file_path}")
                        return True
                except:
                    pass  # Document doesn't exist, continue with ingestion
            
            # Split into chunks
            chunks = self.chunk_text(content)
            self.logger.info(f"Split document into {len(chunks)} chunks")
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                metadata = self.extract_metadata_from_chunk(chunk, file_path)
                
                documents.append(chunk)
                metadatas.append(metadata)
                ids.append(chunk_id)
            
            # Add to collection (embeddings will be generated automatically)
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Successfully ingested document: {file_path}")
            print(f"OK: Ingested {file_path} ({len(chunks)} chunks)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ingesting document {file_path}: {str(e)}")
            print(f"ERROR: Error ingesting {file_path}: {str(e)}")
            return False
    
    def search(self, query: str, n_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using query
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: Search results with content and metadata
        """
        if n_results is None:
            n_results = self.search_config.get("default_results", 5)
        
        max_results = self.search_config.get("max_results", 20)
        n_results = min(n_results, max_results)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else None
                    }
                    formatted_results.append(result)
            
            self.logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: Optional[int] = None) -> str:
        """
        Get relevant context for a query, formatted for LLM consumption
        
        Args:
            query (str): User query
            max_context_length (int): Maximum context length
            
        Returns:
            str: Formatted context string
        """
        if max_context_length is None:
            max_context_length = self.search_config.get("max_context_length", 3000)
        
        results = self.search(query, n_results=10)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            metadata = result.get('metadata', {})
            
            # Format context entry
            source_info = f"Source: {metadata.get('source', 'Unknown')}"
            if 'section' in metadata:
                source_info += f", Section: {metadata['section']}"
            
            context_entry = f"--- {source_info} ---\n{content}\n"
            
            # Check if adding this entry would exceed max length
            if current_length + len(context_entry) > max_context_length:
                break
            
            context_parts.append(context_entry)
            current_length += len(context_entry)
        
        if not context_parts:
            return "No relevant information found in the knowledge base."
        
        context = "Relevant information from knowledge base:\n\n" + "\n".join(context_parts)
        
        return context
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            # First check if collection exists
            if not hasattr(self, 'collection') or self.collection is None:
                return {
                    "document_count": 0,
                    "collection_name": self.collection_config.get("name", "documents"),
                    "persist_directory": self.collection_config.get("persist_directory", "./data/chroma_db"),
                    "embedding_model": self.embedding_config.get("model", "nomic-embed-text:latest"),
                    "embedding_provider": self.embedding_config.get("provider", "ollama"),
                    "status": "not_initialized"
                }
            
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection_config.get("name", "documents"),
                "persist_directory": self.collection_config.get("persist_directory", "./data/chroma_db"),
                "embedding_model": self.embedding_config.get("model", "nomic-embed-text:latest"),
                "embedding_provider": self.embedding_config.get("provider", "ollama"),
                "status": "active"
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        try:
            collection_name = self.collection_config.get("name", "documents")
            # Delete the collection and recreate it
            try:
                self.client.delete_collection(name=collection_name)
            except:
                pass  # Collection might not exist
                
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            self.logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing collection: {str(e)}")
            return False
    
    def reinitialize_collection(self) -> bool:
        """Reinitialize the collection (useful for fixing collection issues)"""
        try:
            collection_name = self.collection_config.get("name", "documents")
            
            # Delete existing collection if it exists
            try:
                self.client.delete_collection(name=collection_name)
                self.logger.info(f"Deleted existing collection: {collection_name}")
            except:
                self.logger.info(f"No existing collection to delete: {collection_name}")
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            self.logger.info(f"Reinitialized collection: {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reinitializing collection: {str(e)}")
            return False

def main():
    """Main function for testing RAG system"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize RAG system with config
    rag = RAGSystem()
    
    # Check embedding model availability
    if not rag.check_embedding_model_availability():
        print("ERROR: Embedding model not available. Please ensure nomic-embed-text:latest is installed in Ollama")
        return
    
    # Check if combined_data.md exists
    if Path("data/combined_data.md").exists():
        print("Ingesting data/combined_data.md into RAG system...")
        success = rag.ingest_document("data/combined_data.md")
        
        if success:
            # Show collection stats
            stats = rag.get_collection_stats()
            print(f"Collection stats: {stats}")
            
            # Test search
            test_query = "positive sentiment"
            print(f"\nTesting search with query: '{test_query}'")
            results = rag.search(test_query, n_results=3)
            
            for i, result in enumerate(results):
                print(f"\nResult {i+1}:")
                print(f"Content: {result['content'][:200]}...")
                print(f"Metadata: {result['metadata']}")
                print(f"Distance: {result['distance']}")
        
    else:
        print("data/combined_data.md not found. Please run excel_to_md_converter.py first.")

if __name__ == "__main__":
    main()
