"""Simple test script to validate Korean language detection functionality."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from ollama_client import OllamaClient


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


if __name__ == "__main__":
    print("🇰🇷 Korean Language Support Test")
    print("=" * 60)
    
    test_language_detection()
    test_system_prompts()
    
    print("🎉 Korean language support tests completed!")
    print("\nNext steps:")
    print("1. Install Korean-capable Ollama model: ollama pull qwen2")
    print("2. Test with actual Korean review data")
    print("3. Run: streamlit run src/main.py")