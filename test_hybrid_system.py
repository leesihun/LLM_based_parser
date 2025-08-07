#!/usr/bin/env python3
"""
Test script for the hybrid query system.
Tests the three main query types that traditional RAG cannot handle effectively.
"""

import logging
from src.excel_reader import ExcelReader
from src.query_engine import HybridQueryEngine
from src.rag_system import RAGSystem
from src.ollama_client import OllamaClient
from config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🧪 Testing Hybrid Query System")
    print("=" * 50)
    
    # Load configuration
    config = Config()
    
    # Load documents
    print("📖 Loading documents...")
    reader = ExcelReader()
    documents = reader.get_detailed_documents()
    
    if not documents:
        print("❌ No documents found. Please ensure Excel files exist in data/ directory.")
        return
    
    print(f"✅ Loaded {len(documents)} documents")
    
    # Initialize RAG system (mock for testing - we won't actually use it for these queries)
    print("🔧 Initializing RAG system...")
    rag_system = RAGSystem(
        collection_name=config.rag_collection_name,
        embedding_model=config.embedding_model,
        persist_directory=str(config.chromadb_dir)
    )
    
    # Initialize Ollama client
    print("🤖 Initializing Ollama client...")
    ollama_client = OllamaClient()
    
    # Initialize hybrid query engine
    print("⚡ Initializing hybrid query engine...")
    query_engine = HybridQueryEngine(documents, rag_system, ollama_client)
    
    # Test queries that traditional RAG cannot handle effectively
    test_queries = [
        "How many positive reviews are there?",
        "What are the top 10 positive keywords?",
        "How many negative reviews mention battery?",
        "Show me dataset statistics",
        "Compare positive and negative keywords",
        "What do users think about camera quality?"  # This should use RAG
    ]
    
    print("🔍 Testing queries...")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print("-" * 40)
        
        try:
            result = query_engine.process_query(query)
            
            print(f"   Type: {result['type'].upper()}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Modules: {', '.join(result['modules_used'])}")
            print(f"   Summary: {result['summary']}")
            
            # Show some detailed results based on type
            if result['type'] == 'count' and 'data' in result:
                data = result['data']
                if 'count' in data:
                    print(f"   Count: {data['count']}")
                    
            elif result['type'] == 'keyword_extraction' and 'data' in result:
                data = result['data']
                keywords = data.get('keywords', [])[:5]
                if keywords:
                    print(f"   Top keywords: {[word for word, score in keywords]}")
                    
            elif result['type'] == 'statistics' and 'data' in result:
                data = result['data']
                sentiment_counts = data.get('sentiment_counts', {})
                print(f"   Total reviews: {sentiment_counts.get('total', 0)}")
                
            if 'error' in result:
                print(f"   ⚠️ Error: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            logger.exception("Error processing query")
    
    print("\n🎉 Testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()