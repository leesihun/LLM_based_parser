"""
LLM-based Query Classifier
Uses Ollama LLM to classify user queries by intent, supporting multiple languages.
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from .ollama_client import OllamaClient
from .query_router import QueryType

logger = logging.getLogger(__name__)


class LLMQueryClassifier:
    """LLM-based query classifier supporting multiple languages."""
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """Initialize LLM query classifier."""
        self.ollama_client = ollama_client or OllamaClient()
        
        # Available topics for reference
        self.available_topics = [
            "battery", "screen", "camera", "performance", "design", 
            "audio", "software", "connectivity", "durability", "price"
        ]
        
        logger.info("LLM query classifier initialized")
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify a user query using LLM.
        
        Args:
            query: User query in any language
            
        Returns:
            Dictionary containing query classification and parameters
        """
        prompt = self._create_classification_prompt(query)
        
        try:
            response = self.ollama_client.generate_response(prompt)
            classification = self._parse_llm_response(response)
            
            # Validate and set defaults
            classification = self._validate_classification(classification)
            
            logger.info(f"Query classified as {classification['type']} with confidence {classification['confidence']}")
            return classification
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Fallback to default semantic search
            return {
                'type': QueryType.SEMANTIC_SEARCH,
                'sentiment': None,
                'topic': None,
                'number': None,
                'method': 'frequency',
                'confidence': 0.1,
                'error': str(e)
            }
    
    def _create_classification_prompt(self, query: str) -> str:
        """Create classification prompt for LLM."""
        return f"""You are a query classifier for a cellphone review analysis system. 

Classify the following user query into one of these types:

1. COUNT: Questions asking "how many" reviews (e.g., "How many positive reviews?", "얼마나 많은 긍정적 리뷰가 있나요?")
2. KEYWORD_EXTRACTION: Questions asking for top/most frequent words/keywords (e.g., "What are top keywords?", "주요 키워드는 무엇인가요?")
3. STATISTICS: Questions asking for overview/summary/statistics (e.g., "Show statistics", "통계를 보여주세요")
4. COMPARISON: Questions comparing positive vs negative (e.g., "Compare positive and negative", "긍정과 부정 비교")
5. SEMANTIC_SEARCH: Other questions seeking specific information (e.g., "What do users think about camera?", "카메라에 대해 어떻게 생각하나요?")

Also extract these parameters:
- sentiment: "positive", "negative", or null
- topic: one of {self.available_topics} or null
- number: any number mentioned (for "top N keywords") or null
- method: "tfidf" if mentioned, otherwise "frequency"

User Query: "{query}"

Respond with ONLY a JSON object in this exact format:
{{
    "type": "COUNT|KEYWORD_EXTRACTION|STATISTICS|COMPARISON|SEMANTIC_SEARCH",
    "sentiment": "positive|negative|null",
    "topic": "battery|screen|camera|performance|design|audio|software|connectivity|durability|price|null",
    "number": number_or_null,
    "method": "frequency|tfidf",
    "confidence": 0.0_to_1.0,
    "reasoning": "brief explanation"
}}"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract classification."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result
            else:
                logger.warning("No JSON found in LLM response")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"LLM response was: {response}")
            return {}
    
    def _validate_classification(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean up classification results."""
        # Set defaults
        validated = {
            'type': QueryType.SEMANTIC_SEARCH,
            'sentiment': None,
            'topic': None, 
            'number': None,
            'method': 'frequency',
            'confidence': 0.5,
            'reasoning': ''
        }
        
        # Validate type
        if 'type' in classification:
            type_str = classification['type'].upper()
            try:
                validated['type'] = QueryType(type_str.lower())
            except ValueError:
                logger.warning(f"Invalid query type: {type_str}")
                validated['type'] = QueryType.SEMANTIC_SEARCH
        
        # Validate sentiment
        if 'sentiment' in classification:
            sentiment = classification['sentiment']
            if sentiment and sentiment.lower() in ['positive', 'negative']:
                validated['sentiment'] = sentiment.lower()
        
        # Validate topic
        if 'topic' in classification:
            topic = classification['topic']
            if topic and topic.lower() in self.available_topics:
                validated['topic'] = topic.lower()
        
        # Validate number
        if 'number' in classification and classification['number']:
            try:
                validated['number'] = int(classification['number'])
            except (ValueError, TypeError):
                pass
        
        # Validate method
        if 'method' in classification:
            method = classification['method']
            if method and method.lower() in ['frequency', 'tfidf']:
                validated['method'] = method.lower()
        
        # Validate confidence
        if 'confidence' in classification:
            try:
                confidence = float(classification['confidence'])
                validated['confidence'] = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                pass
        
        # Copy reasoning if present
        if 'reasoning' in classification:
            validated['reasoning'] = str(classification['reasoning'])
        
        return validated
    
    def classify_queries_batch(self, queries: list) -> list:
        """Classify multiple queries in batch for efficiency."""
        results = []
        for query in queries:
            result = self.classify_query(query)
            results.append(result)
        return results
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return [
            "English", "Korean", "Chinese", "Japanese", "Spanish", 
            "French", "German", "Portuguese", "Russian", "Arabic"
        ]
    
    def test_classification_examples(self) -> Dict[str, Any]:
        """Test classification with various example queries."""
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
        }
        
        results = {}
        for key, query in test_queries.items():
            print(f"Testing {key}: {query}")
            classification = self.classify_query(query)
            results[key] = {
                'query': query,
                'classification': classification
            }
            print(f"  -> {classification['type'].value} (confidence: {classification['confidence']:.2f})")
            if classification.get('reasoning'):
                print(f"  -> Reasoning: {classification['reasoning']}")
            print()
        
        return results