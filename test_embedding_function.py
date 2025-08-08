#!/usr/bin/env python3
"""
Test the OllamaEmbeddingFunction for ChromaDB compatibility
"""

import os
import sys
from pathlib import Path

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_embedding_function():
    """Test if the embedding function works with ChromaDB"""
    try:
        import requests
        from src.rag_system import OllamaEmbeddingFunction
        
        print("Testing Ollama embedding function...")
        
        # Create embedding function
        model = "nomic-embed-text:latest"
        host = "http://localhost:11434"
        embedding_func = OllamaEmbeddingFunction(model, host, batch_size=1)
        
        # Test single text
        test_texts = ["This is a test"]
        
        print(f"Testing with texts: {test_texts}")
        
        # Call the embedding function
        embeddings = embedding_func(test_texts)
        
        if embeddings and len(embeddings) > 0 and len(embeddings[0]) > 0:
            print(f"OK: Embedding function works!")
            print(f"  - Input texts: {len(test_texts)}")
            print(f"  - Output embeddings: {len(embeddings)}")
            print(f"  - Embedding dimension: {len(embeddings[0])}")
            return True
        else:
            print("ERROR: Embedding function returned empty result")
            return False
            
    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        print("Make sure dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        if "requests" in str(e).lower():
            print(f"ERROR: Cannot connect to Ollama: {e}")
            print("Make sure Ollama is running and nomic-embed-text:latest is installed")
        else:
            print(f"ERROR: Embedding function test failed: {e}")
        return False

def test_chromadb_integration():
    """Test the embedding function with ChromaDB"""
    try:
        import chromadb
        from src.rag_system import OllamaEmbeddingFunction
        
        print("\nTesting ChromaDB integration...")
        
        # Create embedding function
        embedding_func = OllamaEmbeddingFunction(
            model="nomic-embed-text:latest",
            ollama_host="http://localhost:11434",
            batch_size=2
        )
        
        # Create temporary ChromaDB client
        client = chromadb.Client()
        
        # Try to create collection with custom embedding function
        collection = client.create_collection(
            name="test_collection",
            embedding_function=embedding_func
        )
        
        print("OK: ChromaDB collection created with custom embedding function")
        
        # Test adding documents
        test_docs = ["This is document 1", "This is document 2"]
        test_ids = ["doc1", "doc2"]
        
        collection.add(
            documents=test_docs,
            ids=test_ids
        )
        
        print("OK: Documents added to collection")
        
        # Test querying
        results = collection.query(
            query_texts=["document"],
            n_results=1
        )
        
        if results and results['documents']:
            print("OK: Query successful")
            print(f"  - Found {len(results['documents'][0])} results")
            return True
        else:
            print("ERROR: Query returned no results")
            return False
            
    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        print("Make sure dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"ERROR: ChromaDB integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Ollama Embedding Function Test")
    print("=" * 40)
    
    # Test 1: Basic embedding function
    test1_result = test_embedding_function()
    
    # Test 2: ChromaDB integration (only if test 1 passed)
    if test1_result:
        test2_result = test_chromadb_integration()
    else:
        test2_result = False
        print("\nSkipping ChromaDB integration test (embedding function not working)")
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Embedding Function: {'PASS' if test1_result else 'FAIL'}")
    print(f"ChromaDB Integration: {'PASS' if test2_result else 'FAIL'}")
    
    if test1_result and test2_result:
        print("\n✅ All tests passed! Embedding function is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above.")
        print("\nMake sure:")
        print("1. Ollama is running: ollama serve")
        print("2. Model is installed: ollama pull nomic-embed-text:latest")
        print("3. Dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()