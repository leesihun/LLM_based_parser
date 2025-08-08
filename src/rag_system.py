#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) System
Uses ChromaDB for vector storage and retrieval with the combined markdown data
"""

import chromadb
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import re

class RAGSystem:
    """RAG system for document retrieval and context generation"""
    
    def __init__(self, collection_name="documents", persist_directory="./chroma_db"):
        """
        Initialize RAG system
        
        Args:
            collection_name (str): Name for ChromaDB collection
            persist_directory (str): Directory to persist ChromaDB data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.logger = logging.getLogger(__name__)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            self.logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(name=collection_name)
            self.logger.info(f"Created new collection: {collection_name}")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval
        
        Args:
            text (str): Text to chunk
            chunk_size (int): Size of each chunk
            overlap (int): Overlap between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to find a good breaking point (paragraph, sentence, etc.)
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
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def generate_document_id(self, content: str) -> str:
        """Generate unique ID for document based on content hash"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_metadata_from_chunk(self, chunk: str, source_file: str) -> Dict[str, Any]:
        """
        Extract metadata from chunk content
        
        Args:
            chunk (str): Text chunk
            source_file (str): Source file name
            
        Returns:
            Dict: Metadata dictionary
        """
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
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Successfully ingested document: {file_path}")
            print(f"✅ Ingested {file_path} ({len(chunks)} chunks)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ingesting document {file_path}: {str(e)}")
            print(f"❌ Error ingesting {file_path}: {str(e)}")
            return False
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using query
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: Search results with content and metadata
        """
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
    
    def get_context_for_query(self, query: str, max_context_length: int = 3000) -> str:
        """
        Get relevant context for a query, formatted for LLM consumption
        
        Args:
            query (str): User query
            max_context_length (int): Maximum context length
            
        Returns:
            str: Formatted context string
        """
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
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            self.logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing collection: {str(e)}")
            return False

def main():
    """Main function for testing RAG system"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize RAG system
    rag = RAGSystem()
    
    # Check if combined_data.md exists
    if Path("combined_data.md").exists():
        print("Ingesting combined_data.md into RAG system...")
        success = rag.ingest_document("combined_data.md")
        
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
        
    else:
        print("combined_data.md not found. Please run excel_to_md_converter.py first.")

if __name__ == "__main__":
    main()