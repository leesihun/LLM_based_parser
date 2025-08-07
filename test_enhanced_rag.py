#!/usr/bin/env python3
"""Test script to verify the enhanced RAG system improvements."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from excel_reader import ExcelReader
from config.config import config

def test_enhanced_documents():
    """Test the new detailed document format."""
    print("🧪 Testing Enhanced RAG System")
    print("=" * 50)
    
    # Test ExcelReader
    print("\n📊 Testing ExcelReader.get_detailed_documents()...")
    excel_reader = ExcelReader()
    
    # Compare old vs new format
    print("\n📋 Old format (get_review_texts):")
    old_texts = excel_reader.get_review_texts()
    if old_texts:
        print(f"  - Count: {len(old_texts)}")
        print(f"  - Average length: {sum(len(t) for t in old_texts) / len(old_texts):.0f} chars")
        print(f"  - Sample: {old_texts[0][:100]}...")
    else:
        print("  - No data found")
    
    print("\n✨ New format (get_detailed_documents):")
    new_docs = excel_reader.get_detailed_documents()
    if new_docs:
        print(f"  - Count: {len(new_docs)}")
        print(f"  - Average length: {sum(len(d['text']) for d in new_docs) / len(new_docs):.0f} chars")
        print(f"  - Sample text: {new_docs[0]['text'][:100]}...")
        print(f"  - Sample metadata keys: {list(new_docs[0]['metadata'].keys())}")
        print(f"  - Sample sentiment: {new_docs[0]['metadata']['sentiment']}")
        print(f"  - Sample source: {new_docs[0]['metadata']['file_source']}")
        
        # Show improvement stats
        old_total_chars = sum(len(t) for t in old_texts) if old_texts else 0
        new_total_chars = sum(len(d['text']) for d in new_docs)
        improvement = ((new_total_chars - old_total_chars) / old_total_chars * 100) if old_total_chars > 0 else 0
        
        print(f"\n📈 Improvement Analysis:")
        print(f"  - Old total chars: {old_total_chars:,}")
        print(f"  - New total chars: {new_total_chars:,}")
        print(f"  - Content increase: {improvement:+.1f}%")
        
        # Context size comparison
        old_context_chars = old_total_chars * (5 / len(old_texts)) if old_texts else 0  # Old: 5 documents
        new_context_chars = new_total_chars * (config.rag_context_size / len(new_docs))  # New: configurable
        context_improvement = ((new_context_chars - old_context_chars) / old_context_chars * 100) if old_context_chars > 0 else 0
        
        print(f"  - Old context size (5 docs): {old_context_chars:,.0f} chars")
        print(f"  - New context size ({config.rag_context_size} docs): {new_context_chars:,.0f} chars")
        print(f"  - Context increase: {context_improvement:+.1f}%")
        
    else:
        print("  - No data found")
    
    print("\n🎯 Configuration:")
    print(f"  - RAG context size: {config.rag_context_size} documents")
    print(f"  - Max tokens: {config.max_tokens:,}")
    print(f"  - Temperature: {config.default_temperature}")
    
    print("\n✅ Enhanced RAG system ready!")
    print(f"💡 Run 'python cli.py setup' to rebuild with enhanced format")
    print(f"💡 Run 'python cli.py query' to test improved context")

if __name__ == "__main__":
    test_enhanced_documents()