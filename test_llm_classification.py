#!/usr/bin/env python3
"""
Test LLM-based query classification with multilingual support.
"""

import logging
from src.llm_query_classifier import LLMQueryClassifier
from src.query_router import QueryRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_classification():
    """Test LLM classification without full Ollama setup."""
    print("Testing LLM Query Classification")
    print("=" * 50)
    
    # Test queries in multiple languages
    test_queries = {
        # English queries
        "en_count": "How many positive reviews are there?",
        "en_keywords": "What are the top 50 positive keywords?", 
        "en_topic_count": "How many negative reviews mention battery life?",
        "en_statistics": "Show me dataset statistics",
        "en_comparison": "Compare positive and negative keywords",
        "en_semantic": "What do users think about camera quality?",
        
        # Korean queries  
        "ko_count": "긍정적인 리뷰가 몇 개 있나요?",
        "ko_keywords": "상위 100개 부정적 키워드는 무엇인가요?",
        "ko_topic_count": "배터리에 대한 부정적 리뷰가 몇 개 있나요?",
        "ko_statistics": "통계를 보여주세요",
        "ko_comparison": "긍정적 리뷰와 부정적 리뷰를 비교해주세요",
        "ko_semantic": "카메라 품질에 대해 사용자들은 어떻게 생각하나요?",
        
        # Chinese queries
        "zh_count": "有多少正面评价？",
        "zh_keywords": "前10个负面关键词是什么？", 
        "zh_topic_count": "有多少关于屏幕的负面评价？",
        
        # Spanish queries
        "es_count": "¿Cuántas reseñas positivas hay?",
        "es_keywords": "¿Cuáles son las principales palabras clave negativas?",
        "es_semantic": "¿Qué piensan los usuarios sobre el rendimiento?",
        
        # Japanese queries
        "ja_count": "ポジティブなレビューは何件ありますか？",
        "ja_keywords": "トップ50のネガティブキーワードは何ですか？",
        "ja_semantic": "ユーザーはバッテリー性能についてどう思っていますか？",
    }
    
    print("Testing individual LLM classifier...")
    try:
        classifier = LLMQueryClassifier()
        print("✅ LLM Classifier initialized successfully")
        
        # Test a few key examples
        key_tests = ["en_count", "ko_count", "zh_count", "en_keywords", "ko_keywords"]
        for key in key_tests:
            if key in test_queries:
                query = test_queries[key]
                print(f"\nTesting {key}: {query}")
                try:
                    result = classifier.classify_query(query)
                    print(f"  -> Type: {result['type'].value}")
                    print(f"  -> Confidence: {result['confidence']:.2f}")
                    print(f"  -> Sentiment: {result['sentiment']}")
                    print(f"  -> Topic: {result['topic']}")
                    print(f"  -> Number: {result['number']}")
                    if result.get('reasoning'):
                        print(f"  -> Reasoning: {result['reasoning']}")
                except Exception as e:
                    print(f"  -> Error: {e}")
        
    except Exception as e:
        print(f"❌ Failed to initialize LLM classifier: {e}")
        print("This is expected if Ollama is not running or dependencies are missing")
    
    print("\nTesting QueryRouter with LLM fallback...")
    try:
        # Test with LLM enabled (will fallback to rules if LLM fails)
        router = QueryRouter(use_llm=True)
        print("✅ QueryRouter initialized")
        
        # Test a simple English query that should work with rules
        simple_query = "How many positive reviews are there?"
        result = router.classify_query(simple_query)
        print(f"\nTesting: {simple_query}")
        print(f"  -> Type: {result['type'].value}")
        print(f"  -> Confidence: {result['confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ QueryRouter test failed: {e}")
    
    print("\nTesting QueryRouter with rule-based only...")
    try:
        # Test with rules only
        router = QueryRouter(use_llm=False)
        print("✅ Rule-based QueryRouter initialized")
        
        # Test English queries
        english_queries = [
            "How many positive reviews are there?",
            "What are the top 10 keywords?",
            "Show me statistics",
            "What do users think about battery?"
        ]
        
        for query in english_queries:
            result = router.classify_query(query)
            print(f"\nTesting: {query}")
            print(f"  -> Type: {result['type'].value} (confidence: {result['confidence']:.2f})")
        
    except Exception as e:
        print(f"❌ Rule-based router test failed: {e}")

if __name__ == "__main__":
    test_llm_classification()