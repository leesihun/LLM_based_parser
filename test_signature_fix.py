#!/usr/bin/env python3
"""
Test ChromaDB embedding function signature fix
Tests the embedding function signature without requiring Ollama to be running
"""

import os
import sys
from pathlib import Path
import inspect

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_signature_fix():
    """Test if the embedding function signature matches ChromaDB expectations"""
    try:
        from src.rag_system import OllamaEmbeddingFunction
        
        print("Testing OllamaEmbeddingFunction signature...")
        
        # Create embedding function
        embedding_func = OllamaEmbeddingFunction(
            model="nomic-embed-text:latest",
            ollama_host="http://localhost:11434",
            batch_size=1
        )
        
        # Check the __call__ method signature
        call_method = getattr(embedding_func, '__call__')
        sig = inspect.signature(call_method)
        
        print(f"Method signature: {sig}")
        print(f"Parameters: {list(sig.parameters.keys())}")
        
        # Check if the signature matches ChromaDB expectations
        params = list(sig.parameters.keys())
        
        # Should have 'input' parameter (not 'texts')
        if 'input' in params:
            print("PASS: Method has 'input' parameter (ChromaDB compatible)")
            signature_correct = True
        elif 'texts' in params:
            print("FAIL: Method has 'texts' parameter (not ChromaDB compatible)")
            signature_correct = False
        else:
            print("FAIL: Method signature is unexpected")
            signature_correct = False
        
        # Check return type annotation
        return_annotation = sig.return_annotation
        print(f"Return type: {return_annotation}")
        
        if hasattr(embedding_func, '__class__') and hasattr(embedding_func.__class__, '__bases__'):
            bases = embedding_func.__class__.__bases__
            print(f"Inheritance: {[base.__name__ for base in bases]}")
            
            # Check if it inherits from ChromaDB's EmbeddingFunction
            chromadb_compatible = any('EmbeddingFunction' in base.__name__ for base in bases)
            if chromadb_compatible:
                print("PASS: Inherits from ChromaDB EmbeddingFunction")
            else:
                print("FAIL: Does not inherit from ChromaDB EmbeddingFunction")
                signature_correct = False
        
        return signature_correct
        
    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        print("This is expected if chromadb is not installed")
        return False
    except Exception as e:
        print(f"ERROR: Signature test failed: {e}")
        return False

def test_mock_chromadb_call():
    """Test the embedding function call with mock data"""
    try:
        from src.rag_system import OllamaEmbeddingFunction
        
        print("\nTesting mock ChromaDB call...")
        
        # Create embedding function
        embedding_func = OllamaEmbeddingFunction(
            model="nomic-embed-text:latest",
            ollama_host="http://localhost:11434",
            batch_size=1
        )
        
        # Test the call signature (will fail due to no Ollama, but we check the signature)
        test_input = ["test text"]
        
        try:
            # This will fail due to connection, but we're testing the signature
            result = embedding_func(test_input)
            print("✅ PASS: Function call succeeded (unexpected - Ollama should not be running)")
            return True
        except Exception as e:
            error_msg = str(e).lower()
            
            # Expected errors (connection issues) mean signature is correct
            if any(keyword in error_msg for keyword in ['connection', 'refused', 'timeout', 'network']):
                print("PASS: Function call failed due to connection (signature is correct)")
                return True
            # Signature errors mean the fix didn't work
            elif any(keyword in error_msg for keyword in ['signature', '__call__', 'parameter']):
                print(f"FAIL: Signature error: {e}")
                return False
            else:
                print(f"UNKNOWN: Unexpected error: {e}")
                return False
                
    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Mock call test failed: {e}")
        return False

def main():
    """Main test function"""
    print("ChromaDB Embedding Function Signature Fix Test")
    print("=" * 50)
    
    # Test 1: Check method signature
    test1_result = test_signature_fix()
    
    # Test 2: Test mock call
    test2_result = test_mock_chromadb_call()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Signature Check: {'PASS' if test1_result else 'FAIL'}")
    print(f"Mock Call Test: {'PASS' if test2_result else 'FAIL'}")
    
    if test1_result and test2_result:
        print("\nAll tests passed! Signature fix is working correctly.")
        print("The embedding function should now work with ChromaDB.")
    else:
        print("\nSome tests failed. The signature fix may need adjustment.")
        print("\nTo fully test:")
        print("1. Install dependencies: pip install chromadb")
        print("2. Start Ollama: ollama serve")
        print("3. Install model: ollama pull nomic-embed-text:latest")
        print("4. Run: python test_embedding_function.py")

if __name__ == "__main__":
    main()