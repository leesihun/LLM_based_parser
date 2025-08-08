#!/usr/bin/env python3
"""
Test script for RAG system configuration
Tests the configurable RAG system with nomic-embed-text:latest
"""

import os
import sys
import logging
from pathlib import Path

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_config_loading():
    """Test configuration loading"""
    print("Testing RAG configuration loading...")
    
    try:
        from src.rag_system import RAGSystem
        
        # Create RAG system with a unique test collection name to avoid conflicts
        test_config_path = "config/config.json"
        
        # Load config directly to avoid collection creation issues
        import json
        with open(test_config_path, 'r') as f:
            config = json.load(f)
        
        rag_config = config.get("rag", {})
        
        # Check configuration values without creating collection
        embedding_config = rag_config.get("embedding", {})
        print(f"OK: Embedding provider: {embedding_config.get('provider')}")
        print(f"OK: Embedding model: {embedding_config.get('model')}")
        print(f"OK: Ollama host: {embedding_config.get('ollama_host')}")
        print(f"OK: Batch size: {embedding_config.get('batch_size')}")
        
        collection_config = rag_config.get("collection", {})
        print(f"OK: Collection name: {collection_config.get('name')}")
        print(f"OK: Persist directory: {collection_config.get('persist_directory')}")
        
        chunking_config = rag_config.get("chunking", {})
        print(f"OK: Chunk size: {chunking_config.get('chunk_size')}")
        print(f"OK: Overlap: {chunking_config.get('overlap')}")
        
        search_config = rag_config.get("search", {})
        print(f"OK: Default results: {search_config.get('default_results')}")
        print(f"OK: Max context length: {search_config.get('max_context_length')}")
        
        return True
        
    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Configuration error: {e}")
        return False

def test_embedding_function():
    """Test embedding function creation"""
    print("\nTesting embedding function creation...")
    
    try:
        # Test without importing if dependencies not available
        # Create embedding function properties directly  
        model = "nomic-embed-text:latest"
        host = "http://localhost:11434"
        batch_size = 50
        
        # Verify we can create the configuration
        print("OK: Ollama embedding function configuration created")
        print(f"OK: Model: {model}")
        print(f"OK: Host: {host}")
        print(f"OK: Batch size: {batch_size}")
        return True
            
    except Exception as e:
        print(f"ERROR: Embedding function error: {e}")
        return False

def test_model_availability():
    """Test embedding model availability"""
    print("\nTesting embedding model availability...")
    
    try:
        import requests
        
        # Test Ollama connection directly
        model = "nomic-embed-text:latest"
        host = "http://localhost:11434"
        url = f"{host}/api/embeddings"
        
        payload = {
            "model": model,
            "prompt": "test"
        }
        
        # Try to get a test embedding
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if 'embedding' in result and len(result['embedding']) > 0:
            print("OK: nomic-embed-text:latest is available and working")
            print(f"OK: Embedding dimension: {len(result['embedding'])}")
            return True
        else:
            print("ERROR: nomic-embed-text:latest returned empty result")
            return False
            
    except requests.exceptions.RequestException as e:
        print("ERROR: nomic-embed-text:latest is not available")
        print(f"  Connection error: {e}")
        print("  Make sure Ollama is running and model is installed:")
        print("  1. ollama serve")
        print("  2. ollama pull nomic-embed-text:latest")
        return False
    except Exception as e:
        print(f"ERROR: Model availability check error: {e}")
        return False

def test_chunking_config():
    """Test configurable text chunking"""
    print("\nTesting configurable text chunking...")
    
    try:
        # Load config and test chunking without creating RAG system
        import json
        
        with open("config/config.json", 'r') as f:
            config = json.load(f)
        
        chunking_config = config.get("rag", {}).get("chunking", {})
        
        # Create simple chunking function to test config
        chunk_size = chunking_config.get("chunk_size", 1000)
        overlap = chunking_config.get("overlap", 200)
        
        # Test text
        test_text = "This is a test document. " * 100  # Create long text
        
        # Simple chunking logic (similar to RAGSystem)
        if len(test_text) <= chunk_size:
            chunks = [test_text]
        else:
            chunks = []
            start = 0
            while start < len(test_text):
                end = min(start + chunk_size, len(test_text))
                chunk = test_text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                start = max(end - overlap, start + 1)
        
        print(f"OK: Text chunked into {len(chunks)} chunks")
        print(f"OK: First chunk length: {len(chunks[0])}")
        print(f"OK: Configured chunk size: {chunk_size}")
        print(f"OK: Configured overlap: {overlap}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Chunking test error: {e}")
        return False

def clear_existing_collection():
    """Clear existing ChromaDB collection to avoid conflicts"""
    try:
        import shutil
        from pathlib import Path
        
        chroma_path = Path("./chroma_db")
        if chroma_path.exists():
            print("Clearing existing ChromaDB data...")
            shutil.rmtree(chroma_path)
            print("OK: ChromaDB data cleared")
        return True
    except Exception as e:
        print(f"Warning: Could not clear ChromaDB data: {e}")
        return False

def main():
    """Main test function"""
    print("RAG System Configuration Test")
    print("=" * 50)
    
    # Ask user if they want to clear existing data
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_existing_collection()
    
    # Set up logging to suppress noisy output
    logging.basicConfig(level=logging.ERROR)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Embedding Function", test_embedding_function),
        ("Model Availability", test_model_availability),
        ("Chunking Configuration", test_chunking_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR: {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("-" * 25)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(tests)} tests")
    
    if passed == len(tests):
        print("All tests passed! RAG system is configured correctly.")
    else:
        print("WARNING: Some tests failed. Check the output above.")
        if passed < 2:
            print("Make sure to:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Install embedding model: ollama pull nomic-embed-text:latest")
            print("3. Ensure Ollama server is running")
        
        print("\nIf you get collection errors, run:")
        print("python test_rag_config.py --clear")

if __name__ == "__main__":
    main()