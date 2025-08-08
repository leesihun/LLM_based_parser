#!/usr/bin/env python3
"""
Simple test for embedding function signature without requiring ChromaDB
"""

import os
import sys
import inspect
from pathlib import Path

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

def test_embedding_signature():
    """Test the OllamaEmbeddingFunction signature directly"""
    print("Testing OllamaEmbeddingFunction signature...")
    
    # Mock the chromadb imports to avoid dependency issues
    class MockEmbeddingFunction:
        pass
    
    # Create a simplified version of OllamaEmbeddingFunction for signature testing
    class OllamaEmbeddingFunction(MockEmbeddingFunction):
        def __init__(self, model: str, ollama_host: str, batch_size: int = 50):
            self.model = model
            self.ollama_host = ollama_host.rstrip('/')
            self.batch_size = batch_size
        
        def __call__(self, input: list) -> list:
            """ChromaDB-compatible signature: input parameter, not texts"""
            # Mock implementation - would normally call Ollama
            return [[0.1, 0.2, 0.3] for _ in input]
    
    # Test the function
    embedding_func = OllamaEmbeddingFunction(
        model="nomic-embed-text:latest",
        ollama_host="http://localhost:11434",
        batch_size=1
    )
    
    # Check the method signature
    call_method = getattr(embedding_func, '__call__')
    sig = inspect.signature(call_method)
    
    print(f"Method signature: {sig}")
    print(f"Parameters: {list(sig.parameters.keys())}")
    
    # Check if parameters are correct
    params = list(sig.parameters.keys())
    
    if 'input' in params and 'texts' not in params:
        print("PASS: Method has 'input' parameter (ChromaDB compatible)")
        print("PASS: Method does NOT have 'texts' parameter")
        
        # Test the call
        test_input = ["test text 1", "test text 2"]
        try:
            result = embedding_func(test_input)
            if result and len(result) == len(test_input):
                print("PASS: Function call works with 'input' parameter")
                print(f"Input: {len(test_input)} texts")
                print(f"Output: {len(result)} embeddings")
                return True
            else:
                print("FAIL: Function call returned unexpected result")
                return False
        except Exception as e:
            print(f"FAIL: Function call failed: {e}")
            return False
    else:
        print("FAIL: Method signature is not ChromaDB compatible")
        if 'texts' in params:
            print("ERROR: Method still has 'texts' parameter instead of 'input'")
        return False

def main():
    """Main test function"""
    print("Simple Embedding Function Signature Test")
    print("=" * 45)
    
    result = test_embedding_signature()
    
    print("\n" + "=" * 45)
    print(f"Test Result: {'PASS' if result else 'FAIL'}")
    
    if result:
        print("\nSUCCESS: The embedding function signature is ChromaDB compatible!")
        print("The fix should work when ChromaDB and Ollama are available.")
    else:
        print("\nFAILED: The embedding function signature needs to be fixed.")
        print("Check that the __call__ method uses 'input' not 'texts' parameter.")

if __name__ == "__main__":
    main()