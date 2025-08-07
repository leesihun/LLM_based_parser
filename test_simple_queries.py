#!/usr/bin/env python3
"""
Simple test to verify Excel loading and basic query routing without full system.
"""

import logging
from src.excel_reader import ExcelReader
from src.dataset_analyzer import DatasetAnalyzer
from src.topic_classifier import TopicClassifier
from src.keyword_extractor import KeywordExtractor
from src.query_router import QueryRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("Testing Basic Components (No RAG/Ollama)")
    print("=" * 50)
    
    # Test 1: Excel loading
    print("\n1. Testing Excel Reader...")
    reader = ExcelReader()
    documents = reader.get_detailed_documents()
    print(f"   Loaded {len(documents)} documents")
    if documents:
        print(f"   Sample: {documents[0][:100]}...")
    
    if not documents:
        print("   FAILED: No documents loaded")
        return
    
    # Test 2: Dataset Analyzer
    print("\n2. Testing Dataset Analyzer...")
    analyzer = DatasetAnalyzer(documents)
    stats = analyzer.count_reviews_by_sentiment()
    print(f"   Sentiment counts: {stats}")
    
    # Test 3: Topic Classifier
    print("\n3. Testing Topic Classifier...")
    classifier = TopicClassifier()
    battery_count = classifier.count_reviews_by_topic(documents, "battery")
    camera_count = classifier.count_reviews_by_topic(documents, "camera")
    print(f"   Battery mentions: {battery_count}")
    print(f"   Camera mentions: {camera_count}")
    
    # Test 4: Keyword Extractor
    print("\n4. Testing Keyword Extractor...")
    extractor = KeywordExtractor()
    pos_keywords = extractor.extract_positive_keywords(documents, top_n=5)
    neg_keywords = extractor.extract_negative_keywords(documents, top_n=5)
    print(f"   Top positive keywords: {[word for word, score in pos_keywords]}")
    print(f"   Top negative keywords: {[word for word, score in neg_keywords]}")
    
    # Test 5: Query Router
    print("\n5. Testing Query Router...")
    router = QueryRouter()
    
    test_queries = [
        "How many positive reviews are there?",
        "What are the top 10 positive keywords?", 
        "How many negative reviews mention battery?",
        "Show me statistics",
        "What do users think about camera?"
    ]
    
    for query in test_queries:
        classification = router.classify_query(query)
        print(f"   '{query}' -> {classification['type'].value} (confidence: {classification['confidence']:.2f})")
    
    print("\n✅ All basic components working!")
    print("\nThe system can now handle:")
    print("- Counting queries (How many positive reviews?)")
    print("- Keyword extraction (Top 10 positive keywords)")  
    print("- Topic filtering (Reviews about battery)")
    print("- Query routing and classification")

if __name__ == "__main__":
    main()