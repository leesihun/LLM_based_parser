"""
Query Router Module
Classifies user queries by type and routes them to appropriate processing modules.
Supports COUNT, KEYWORD_EXTRACTION, TOPIC_FILTER, and SEMANTIC_SEARCH query types.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Enumeration of query types."""
    COUNT = "count"
    KEYWORD_EXTRACTION = "keyword_extraction" 
    TOPIC_FILTER = "topic_filter"
    SEMANTIC_SEARCH = "semantic_search"
    STATISTICS = "statistics"
    COMPARISON = "comparison"


class QueryRouter:
    """Router for classifying and routing different types of user queries."""
    
    def __init__(self):
        """Initialize query router with pattern matching rules."""
        
        # Patterns for COUNT queries
        self.count_patterns = [
            r'how many.*reviews?',
            r'count.*reviews?',
            r'number of.*reviews?',
            r'total.*reviews?',
            r'how much.*reviews?',
            r'quantity.*reviews?',
        ]
        
        # Patterns for KEYWORD_EXTRACTION queries
        self.keyword_patterns = [
            r'top.*keywords?',
            r'most.*words?',
            r'frequent.*words?',
            r'common.*words?',
            r'popular.*terms?',
            r'important.*keywords?',
            r'key.*words?',
            r'main.*words?',
        ]
        
        # Patterns for STATISTICS queries
        self.statistics_patterns = [
            r'statistics',
            r'stats',
            r'overview',
            r'summary',
            r'distribution',
            r'breakdown',
            r'analysis',
        ]
        
        # Patterns for COMPARISON queries
        self.comparison_patterns = [
            r'compare.*positive.*negative',
            r'difference.*positive.*negative',
            r'positive.*vs.*negative',
            r'negative.*vs.*positive',
        ]
        
        # Sentiment indicators
        self.sentiment_indicators = {
            'positive': ['positive', 'good', 'great', 'excellent', 'amazing', 'love', 'like', 'best'],
            'negative': ['negative', 'bad', 'terrible', 'awful', 'hate', 'dislike', 'worst', 'problem']
        }
        
        # Topic keywords (from TopicClassifier)
        self.topic_keywords = {
            'battery': ['battery', 'power', 'charge', 'charging', 'drain', 'life'],
            'screen': ['screen', 'display', 'brightness', 'color', 'resolution'],
            'camera': ['camera', 'photo', 'picture', 'image', 'video', 'lens'],
            'performance': ['performance', 'speed', 'fast', 'slow', 'lag', 'freeze'],
            'design': ['design', 'look', 'appearance', 'beautiful', 'build'],
            'audio': ['sound', 'audio', 'speaker', 'volume', 'music'],
            'software': ['software', 'android', 'ios', 'update', 'app'],
            'connectivity': ['wifi', 'bluetooth', 'signal', 'network', 'connection'],
            'durability': ['durability', 'durable', 'break', 'scratch', 'drop'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'value', 'money']
        }
        
        # Compile regex patterns
        self.compiled_patterns = {
            QueryType.COUNT: [re.compile(pattern, re.IGNORECASE) for pattern in self.count_patterns],
            QueryType.KEYWORD_EXTRACTION: [re.compile(pattern, re.IGNORECASE) for pattern in self.keyword_patterns],
            QueryType.STATISTICS: [re.compile(pattern, re.IGNORECASE) for pattern in self.statistics_patterns],
            QueryType.COMPARISON: [re.compile(pattern, re.IGNORECASE) for pattern in self.comparison_patterns],
        }
        
        logger.info("Query router initialized with pattern matching rules")
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify a user query and extract relevant parameters.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary containing query type and extracted parameters
        """
        query_lower = query.lower().strip()
        
        # Check for each query type
        classification = {
            'type': QueryType.SEMANTIC_SEARCH,  # Default
            'sentiment': None,
            'topic': None,
            'number': None,
            'method': 'frequency',
            'confidence': 0.0
        }
        
        # Extract number from query (for "top N keywords")
        number_match = re.search(r'\b(\d+)\b', query_lower)
        if number_match:
            classification['number'] = int(number_match.group(1))
        
        # Extract sentiment
        sentiment = self._extract_sentiment(query_lower)
        if sentiment:
            classification['sentiment'] = sentiment
        
        # Extract topic
        topic = self._extract_topic(query_lower)
        if topic:
            classification['topic'] = topic
        
        # Check patterns for specific query types
        for query_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(query_lower):
                    classification['type'] = query_type
                    classification['confidence'] = 0.8
                    break
            if classification['confidence'] > 0:
                break
        
        # Special handling for specific query patterns
        if 'tfidf' in query_lower or 'tf-idf' in query_lower:
            classification['method'] = 'tfidf'
        
        # Adjust confidence based on additional indicators
        if classification['type'] == QueryType.SEMANTIC_SEARCH:
            classification['confidence'] = 0.3  # Low confidence for default
        
        logger.info(f"Query classified as {classification['type'].value} with confidence {classification['confidence']}")
        return classification
    
    def _extract_sentiment(self, query: str) -> Optional[str]:
        """Extract sentiment from query."""
        for sentiment, keywords in self.sentiment_indicators.items():
            if any(keyword in query for keyword in keywords):
                return sentiment
        return None
    
    def _extract_topic(self, query: str) -> Optional[str]:
        """Extract topic from query."""
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in query for keyword in keywords):
                return topic
        return None
    
    def get_query_suggestions(self, query_type: QueryType) -> List[str]:
        """
        Get example queries for a specific query type.
        
        Args:
            query_type: The type of query
            
        Returns:
            List of example queries
        """
        suggestions = {
            QueryType.COUNT: [
                "How many positive reviews are there?",
                "How many negative reviews mention battery?",
                "Count the total number of reviews",
                "How many reviews talk about camera quality?"
            ],
            QueryType.KEYWORD_EXTRACTION: [
                "What are the top 100 positive keywords?",
                "Show me the most common negative words",
                "Extract key terms from positive reviews",
                "What are the frequent words about battery?"
            ],
            QueryType.STATISTICS: [
                "Show me dataset statistics",
                "Give me an overview of the reviews",
                "What's the distribution of sentiments?",
                "Provide a summary of the data"
            ],
            QueryType.COMPARISON: [
                "Compare positive and negative keywords",
                "What's the difference between positive and negative reviews?",
                "Show positive vs negative sentiment analysis"
            ],
            QueryType.SEMANTIC_SEARCH: [
                "What do users think about camera quality?",
                "Tell me about battery performance issues",
                "How is the screen quality perceived?",
                "What are the main complaints about this phone?"
            ]
        }
        
        return suggestions.get(query_type, [])
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Route a query to the appropriate processing module.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary containing routing information and parameters
        """
        classification = self.classify_query(query)
        
        routing_info = {
            'original_query': query,
            'classification': classification,
            'processing_modules': [],
            'parameters': {}
        }
        
        query_type = classification['type']
        
        # Determine which modules to use
        if query_type == QueryType.COUNT:
            routing_info['processing_modules'] = ['dataset_analyzer']
            if classification['topic']:
                routing_info['processing_modules'].append('topic_classifier')
            routing_info['parameters'] = {
                'operation': 'count',
                'sentiment': classification['sentiment'],
                'topic': classification['topic']
            }
            
        elif query_type == QueryType.KEYWORD_EXTRACTION:
            routing_info['processing_modules'] = ['keyword_extractor']
            routing_info['parameters'] = {
                'operation': 'extract_keywords',
                'sentiment': classification['sentiment'],
                'topic': classification['topic'],
                'top_n': classification['number'] or 100,
                'method': classification['method']
            }
            
        elif query_type == QueryType.STATISTICS:
            routing_info['processing_modules'] = ['dataset_analyzer', 'topic_classifier']
            routing_info['parameters'] = {
                'operation': 'statistics',
                'include_topics': True
            }
            
        elif query_type == QueryType.COMPARISON:
            routing_info['processing_modules'] = ['keyword_extractor', 'dataset_analyzer']
            routing_info['parameters'] = {
                'operation': 'compare_sentiments',
                'top_n': classification['number'] or 50,
                'method': classification['method']
            }
            
        else:  # SEMANTIC_SEARCH
            routing_info['processing_modules'] = ['rag_system']
            routing_info['parameters'] = {
                'operation': 'semantic_search',
                'sentiment': classification['sentiment'],
                'topic': classification['topic']
            }
        
        logger.info(f"Query routed to modules: {routing_info['processing_modules']}")
        return routing_info
    
    def get_available_topics(self) -> List[str]:
        """Get list of available topic names."""
        return list(self.topic_keywords.keys())
    
    def validate_query_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize query parameters.
        
        Args:
            parameters: Dictionary of query parameters
            
        Returns:
            Validated and sanitized parameters
        """
        validated = parameters.copy()
        
        # Validate sentiment
        if 'sentiment' in validated and validated['sentiment']:
            if validated['sentiment'] not in ['positive', 'negative']:
                logger.warning(f"Invalid sentiment: {validated['sentiment']}")
                validated['sentiment'] = None
        
        # Validate topic
        if 'topic' in validated and validated['topic']:
            if validated['topic'] not in self.topic_keywords:
                logger.warning(f"Invalid topic: {validated['topic']}")
                validated['topic'] = None
        
        # Validate numbers
        if 'top_n' in validated:
            try:
                validated['top_n'] = max(1, min(1000, int(validated['top_n'])))
            except (ValueError, TypeError):
                validated['top_n'] = 100
        
        # Validate method
        if 'method' in validated and validated['method'] not in ['frequency', 'tfidf']:
            validated['method'] = 'frequency'
        
        return validated