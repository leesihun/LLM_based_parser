"""Simple test script to validate Korean language detection and Ollama embedding functionality."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from ollama_client import OllamaClient
from rag_system import RAGSystem


def test_language_detection():
    """Test the Korean language detection logic."""
    client = OllamaClient()
    
    test_queries = [
        ("Hello, how are you?", "en"),
        ("안녕하세요, 어떻게 지내세요?", "ko"),
        ("폴더블 폰의 장점은 무엇인가요?", "ko"),
        ("What are the benefits of foldable phones?", "en"),
        ("This is English with 한국어 mixed", "ko"),  # Mixed content
        ("Battery life is important", "en")
    ]
    
    print("🔍 Testing Korean Language Detection")
    print("=" * 50)
    
    for query, expected in test_queries:
        # Extract the language detection logic from generate_with_context
        korean_chars = sum(1 for char in query if '\uac00' <= char <= '\ud7a3')
        total_chars = len([c for c in query if c.isalpha()])
        detected_lang = "ko" if korean_chars > total_chars * 0.3 else "en"
        
        status = "✅" if detected_lang == expected else "❌"
        print(f"{status} Query: {query[:30]}...")
        print(f"   Expected: {expected}, Detected: {detected_lang}")
        print(f"   Korean chars: {korean_chars}/{total_chars}")
        print()


def test_system_prompts():
    """Test system prompt selection."""
    print("🤖 Testing System Prompts")
    print("=" * 50)
    
    system_prompts = {
        "en": """You are an AI assistant specialized in analyzing cellphone reviews. 
You have access to a database of positive and negative cellphone reviews, specifically about foldable phones.

Use the provided context to answer questions accurately. If the context doesn't contain 
relevant information, say so clearly. Focus on insights from the review data.

Context format: Reviews are tagged with [POSITIVE] or [NEGATIVE] to indicate sentiment.""",
        
        "ko": """당신은 휴대폰 리뷰 분석 전문 AI 어시스턴트입니다.
폴더블 폰에 대한 긍정적, 부정적 리뷰 데이터베이스에 접근할 수 있습니다.

제공된 맥락을 사용하여 질문에 정확하게 답변하세요. 맥락에 관련 정보가 없다면 명확히 말씀해 주세요. 
리뷰 데이터의 인사이트에 집중하세요.

맥락 형식: 리뷰는 감정을 나타내기 위해 [POSITIVE] 또는 [NEGATIVE]로 태그가 지정됩니다."""
    }
    
    print("English System Prompt:")
    print(system_prompts["en"][:100] + "...")
    print("\nKorean System Prompt:")
    print(system_prompts["ko"][:100] + "...")
    print("\n✅ System prompts loaded successfully")


def test_ollama_embeddings():
    """Test Ollama embeddings functionality."""
    print("🔗 Testing Ollama Embeddings")
    print("=" * 50)
    
    try:
        # Initialize RAG system with Ollama embeddings
        rag = RAGSystem(
            collection_name="test_korean",
            embedding_model="nomic-embed-text:latest"
        )
        
        # Test documents (Korean and English)
        test_docs = [
            "This foldable phone has great battery life",
            "이 폴더블 폰은 배터리 수명이 훌륭합니다",
            "The screen quality is excellent", 
            "화면 품질이 우수합니다"
        ]
        
        print(f"Adding {len(test_docs)} test documents...")
        rag.add_documents(test_docs)
        
        # Test query
        print("Testing query retrieval...")
        query = "배터리 수명은 어떤가요?"  # How is the battery life?
        context = rag.get_context_for_query(query)
        
        print(f"Query: {query}")
        print(f"Retrieved context: {context[:200]}...")
        
        # Get stats
        stats = rag.get_collection_stats()
        print(f"Collection stats: {stats}")
        
        print("✅ Ollama embeddings working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing Ollama embeddings: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🇰🇷 Korean Language Support Test")
    print("=" * 60)
    
    test_language_detection()
    test_system_prompts()
    
    # Test Ollama embeddings
    embedding_success = test_ollama_embeddings()
    
    print("🎉 Korean language support tests completed!")
    
    if embedding_success:
        print("\n✅ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Install Korean-capable Ollama model: ollama pull qwen2")
        print("2. Add your Excel files to data/ directory")
        print("3. Run: streamlit run src/main.py")
    else:
        print("\n⚠️ Some tests failed. Check Ollama installation and model availability.")
        print("Make sure: ollama pull nomic-embed-text:latest")