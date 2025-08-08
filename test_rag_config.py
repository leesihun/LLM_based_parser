#!/usr/bin/env python3
"""
Test script for RAG system configuration
Tests the configurable RAG system with nomic-embed-text:latest
"""

import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_config_loading():
    """Test configuration loading"""
    print("Testing RAG configuration loading...")
    
    try:
        from src.rag_system import RAGSystem
        
        # Initialize RAG system
        rag = RAGSystem()
        
        # Check configuration values
        embedding_config = rag.embedding_config
        print(f"✓ Embedding provider: {embedding_config.get('provider')}")
        print(f"✓ Embedding model: {embedding_config.get('model')}")
        print(f"✓ Ollama host: {embedding_config.get('ollama_host')}")
        print(f"✓ Batch size: {embedding_config.get('batch_size')}")
        
        collection_config = rag.collection_config
        print(f"✓ Collection name: {collection_config.get('name')}")
        print(f"✓ Persist directory: {collection_config.get('persist_directory')}")
        
        chunking_config = rag.chunking_config
        print(f"✓ Chunk size: {chunking_config.get('chunk_size')}")
        print(f"✓ Overlap: {chunking_config.get('overlap')}")
        
        search_config = rag.search_config
        print(f"✓ Default results: {search_config.get('default_results')}")
        print(f"✓ Max context length: {search_config.get('max_context_length')}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_embedding_function():
    """Test embedding function creation"""
    print("\nTesting embedding function creation...")
    
    try:
        from src.rag_system import RAGSystem, OllamaEmbeddingFunction
        
        # Initialize RAG system
        rag = RAGSystem()
        
        # Check embedding function
        if isinstance(rag.embedding_function, OllamaEmbeddingFunction):
            print("✓ Ollama embedding function created successfully")
            print(f"✓ Model: {rag.embedding_function.model}")
            print(f"✓ Host: {rag.embedding_function.ollama_host}")
            print(f"✓ Batch size: {rag.embedding_function.batch_size}")
            return True
        else:
            print(f"✗ Unexpected embedding function type: {type(rag.embedding_function)}")
            return False
            
    except Exception as e:
        print(f"✗ Embedding function error: {e}")
        return False

def test_model_availability():
    """Test embedding model availability"""
    print("\nTesting embedding model availability...")
    
    try:
        from src.rag_system import RAGSystem
        
        # Initialize RAG system
        rag = RAGSystem()
        
        # Check model availability (this will fail if Ollama/model not available)
        available = rag.check_embedding_model_availability()
        
        if available:
            print("✓ nomic-embed-text:latest is available and working")
            return True
        else:
            print("✗ nomic-embed-text:latest is not available")
            print("  Run: ollama pull nomic-embed-text:latest")
            return False
            
    except Exception as e:
        print(f"✗ Model availability check error: {e}")
        return False

def test_chunking_config():
    """Test configurable text chunking"""
    print("\nTesting configurable text chunking...")
    
    try:
        from src.rag_system import RAGSystem
        
        # Initialize RAG system
        rag = RAGSystem()
        
        # Test text
        test_text = "This is a test document. " * 100  # Create long text
        
        # Test chunking
        chunks = rag.chunk_text(test_text)
        
        print(f"✓ Text chunked into {len(chunks)} chunks")
        print(f"✓ First chunk length: {len(chunks[0])}")
        print(f"✓ Configured chunk size: {rag.chunking_config.get('chunk_size')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Chunking test error: {e}")
        return False

def main():
    """Main test function"""
    print("RAG System Configuration Test")
    print("=" * 50)
    
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
            print(f"✗ {test_name} failed with exception: {e}")
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
        print("🎉 All tests passed! RAG system is configured correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above.")
        if passed < 2:
            print("Make sure to:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Install embedding model: ollama pull nomic-embed-text:latest")
            print("3. Ensure Ollama server is running")

if __name__ == "__main__":
    main()