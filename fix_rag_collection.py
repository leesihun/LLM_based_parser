#!/usr/bin/env python3
"""
RAG Collection Fix Utility
Fixes common ChromaDB collection issues
"""

import os
import sys
import shutil
from pathlib import Path

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def clear_chromadb():
    """Clear ChromaDB directory completely"""
    chroma_path = Path("./chroma_db")
    if chroma_path.exists():
        print("Clearing ChromaDB directory...")
        shutil.rmtree(chroma_path)
        print("OK: ChromaDB directory cleared")
        return True
    else:
        print("ChromaDB directory doesn't exist")
        return False

def reinitialize_rag():
    """Reinitialize RAG system with fresh collection"""
    try:
        from src.rag_system import RAGSystem
        
        print("Reinitializing RAG system...")
        rag = RAGSystem()
        
        # Check if embedding model is available
        if not rag.check_embedding_model_availability():
            print("ERROR: Embedding model not available")
            print("Please run: ollama pull nomic-embed-text:latest")
            return False
        
        print("OK: RAG system initialized successfully")
        
        # Get stats
        stats = rag.get_collection_stats()
        print(f"Collection stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to reinitialize RAG system: {str(e)}")
        return False

def test_rag_system():
    """Test basic RAG functionality"""
    try:
        from src.rag_system import RAGSystem
        
        rag = RAGSystem()
        
        # Test chunking
        test_text = "This is a test document for chunking."
        chunks = rag.chunk_text(test_text)
        print(f"OK: Text chunking works ({len(chunks)} chunks)")
        
        # Test collection stats
        stats = rag.get_collection_stats()
        print(f"OK: Collection stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: RAG system test failed: {str(e)}")
        return False

def main():
    """Main function"""
    print("RAG Collection Fix Utility")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_rag_collection.py clear     - Clear ChromaDB directory")
        print("  python fix_rag_collection.py reset     - Clear and reinitialize")
        print("  python fix_rag_collection.py test      - Test RAG system")
        print("  python fix_rag_collection.py reinit    - Reinitialize only")
        return
    
    action = sys.argv[1].lower()
    
    if action == "clear":
        clear_chromadb()
        
    elif action == "reset":
        print("Performing full reset...")
        clear_chromadb()
        reinitialize_rag()
        test_rag_system()
        
    elif action == "test":
        test_rag_system()
        
    elif action == "reinit":
        reinitialize_rag()
        
    else:
        print(f"Unknown action: {action}")
        print("Use: clear, reset, test, or reinit")

if __name__ == "__main__":
    main()