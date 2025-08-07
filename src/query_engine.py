"""
Hybrid Query Engine
Orchestrates multiple processing modules to handle different types of queries.
Combines RAG, dataset analysis, topic classification, and keyword extraction.
"""

import logging
from typing import List, Dict, Any, Optional
from .query_router import QueryRouter, QueryType
from .dataset_analyzer import DatasetAnalyzer
from .topic_classifier import TopicClassifier
from .keyword_extractor import KeywordExtractor
from .rag_system import RAGSystem
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class HybridQueryEngine:
    """Hybrid query engine that combines multiple processing approaches."""
    
    def __init__(self, documents: List[str], rag_system: RAGSystem, ollama_client: OllamaClient):
        """
        Initialize hybrid query engine with all processing modules.
        
        Args:
            documents: List of all document texts
            rag_system: Initialized RAG system
            ollama_client: Ollama client for LLM interactions
        """
        self.documents = documents
        self.rag_system = rag_system
        self.ollama_client = ollama_client
        
        # Initialize processing modules
        self.query_router = QueryRouter()
        self.dataset_analyzer = DatasetAnalyzer(documents)
        self.topic_classifier = TopicClassifier()
        self.keyword_extractor = KeywordExtractor()
        
        logger.info(f"Hybrid query engine initialized with {len(documents)} documents")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the most appropriate method.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary containing results and metadata
        """
        logger.info(f"Processing query: {query}")
        
        # Route the query
        routing_info = self.query_router.route_query(query)
        query_type = routing_info['classification']['type']
        parameters = self.query_router.validate_query_parameters(routing_info['parameters'])
        
        # Process based on query type
        result = {
            'query': query,
            'type': query_type.value,
            'confidence': routing_info['classification']['confidence'],
            'modules_used': routing_info['processing_modules'],
            'data': {},
            'summary': ''
        }
        
        try:
            if query_type == QueryType.COUNT:
                result['data'] = self._handle_count_query(parameters)
                result['summary'] = self._generate_count_summary(result['data'], parameters)
                
            elif query_type == QueryType.KEYWORD_EXTRACTION:
                result['data'] = self._handle_keyword_extraction(parameters)
                result['summary'] = self._generate_keyword_summary(result['data'], parameters)
                
            elif query_type == QueryType.STATISTICS:
                result['data'] = self._handle_statistics_query(parameters)
                result['summary'] = self._generate_statistics_summary(result['data'])
                
            elif query_type == QueryType.COMPARISON:
                result['data'] = self._handle_comparison_query(parameters)
                result['summary'] = self._generate_comparison_summary(result['data'], parameters)
                
            else:  # SEMANTIC_SEARCH
                result['data'] = self._handle_semantic_search(query, parameters)
                result['summary'] = result['data'].get('llm_response', 'No response generated')
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            result['error'] = str(e)
            result['summary'] = f"Error processing query: {e}"
        
        return result
    
    def _handle_count_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle COUNT type queries."""
        sentiment = parameters.get('sentiment')
        topic = parameters.get('topic')
        
        if topic:
            # Count by topic and sentiment
            if sentiment:
                reviews = self.dataset_analyzer.get_reviews_by_sentiment(sentiment)
                count = self.topic_classifier.count_reviews_by_topic(reviews, topic)
                return {
                    'count': count,
                    'sentiment': sentiment,
                    'topic': topic,
                    'total_sentiment_reviews': len(reviews)
                }
            else:
                # Count all reviews about topic
                count = self.topic_classifier.count_reviews_by_topic(self.documents, topic)
                return {
                    'count': count,
                    'topic': topic,
                    'total_reviews': len(self.documents)
                }
        else:
            # Count by sentiment only
            sentiment_counts = self.dataset_analyzer.count_reviews_by_sentiment()
            if sentiment:
                return {
                    'count': sentiment_counts[sentiment],
                    'sentiment': sentiment,
                    'all_counts': sentiment_counts
                }
            else:
                return {
                    'count': sentiment_counts['total'],
                    'breakdown': sentiment_counts
                }
    
    def _handle_keyword_extraction(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle KEYWORD_EXTRACTION type queries."""
        sentiment = parameters.get('sentiment')
        topic = parameters.get('topic')
        top_n = parameters.get('top_n', 100)
        method = parameters.get('method', 'frequency')
        
        # Filter documents by sentiment and/or topic
        documents = self.documents
        if sentiment:
            documents = self.dataset_analyzer.get_reviews_by_sentiment(sentiment)
        
        if topic and documents:
            documents = self.topic_classifier.filter_reviews_by_topic(documents, topic)
        
        if not documents:
            return {'keywords': [], 'message': 'No matching documents found'}
        
        # Extract keywords
        if sentiment == 'positive':
            keywords = self.keyword_extractor.extract_positive_keywords(documents, method, top_n)
        elif sentiment == 'negative':
            keywords = self.keyword_extractor.extract_negative_keywords(documents, method, top_n)
        else:
            if method == 'tfidf':
                keywords = self.keyword_extractor.extract_keywords_by_tfidf(documents, top_n)
            else:
                freq_keywords = self.keyword_extractor.extract_keywords_by_frequency(documents, top_n)
                keywords = [(word, float(count)) for word, count in freq_keywords]
        
        return {
            'keywords': keywords,
            'method': method,
            'sentiment': sentiment,
            'topic': topic,
            'document_count': len(documents),
            'top_n': top_n
        }
    
    def _handle_statistics_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle STATISTICS type queries."""
        # Get dataset statistics
        stats = self.dataset_analyzer.get_dataset_statistics()
        
        # Get topic distribution if requested
        if parameters.get('include_topics', False):
            topic_dist = self.topic_classifier.get_topic_distribution(self.documents)
            stats['topic_distribution'] = topic_dist
        
        return stats
    
    def _handle_comparison_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle COMPARISON type queries."""
        top_n = parameters.get('top_n', 50)
        method = parameters.get('method', 'frequency')
        
        # Get sentiment counts
        sentiment_counts = self.dataset_analyzer.count_reviews_by_sentiment()
        
        # Compare keywords between positive and negative
        keyword_comparison = self.keyword_extractor.compare_sentiment_keywords(
            self.documents, method, top_n
        )
        
        return {
            'sentiment_counts': sentiment_counts,
            'keyword_comparison': keyword_comparison,
            'method': method,
            'top_n': top_n
        }
    
    def _handle_semantic_search(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SEMANTIC_SEARCH type queries."""
        # Get relevant context from RAG system
        rag_results = self.rag_system.query(query, n_results=5)
        
        if not rag_results['documents']:
            return {
                'rag_results': rag_results,
                'llm_response': 'No relevant documents found for your query.',
                'context_used': False
            }
        
        # Format context for LLM
        context_parts = []
        for i, doc in enumerate(rag_results['documents']):
            context_parts.append(f"Review {i+1}: {doc}")
        context = "\\n\\n".join(context_parts)
        
        # Create enhanced prompt
        sentiment_filter = parameters.get('sentiment', '')
        topic_filter = parameters.get('topic', '')
        
        filter_text = ""
        if sentiment_filter:
            filter_text += f" Focus on {sentiment_filter} reviews."
        if topic_filter:
            filter_text += f" Pay attention to {topic_filter}-related aspects."
        
        prompt = f"""Based on the following cellphone reviews, please answer the user's question.{filter_text}
        
Context (Retrieved Reviews):
{context}

User Question: {query}

Please provide a comprehensive answer based on the review context above. If you notice patterns or can provide insights about user sentiment, please include those."""
        
        # Get LLM response
        try:
            llm_response = self.ollama_client.query(prompt)
            return {
                'rag_results': rag_results,
                'llm_response': llm_response,
                'context_used': True,
                'context_length': len(context)
            }
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return {
                'rag_results': rag_results,
                'llm_response': f"Error generating response: {e}",
                'context_used': True,
                'error': str(e)
            }
    
    def _generate_count_summary(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate summary for count query results."""
        count = data.get('count', 0)
        sentiment = parameters.get('sentiment')
        topic = parameters.get('topic')
        
        if topic and sentiment:
            return f"Found {count} {sentiment} reviews about {topic}."
        elif topic:
            return f"Found {count} reviews about {topic}."
        elif sentiment:
            return f"Found {count} {sentiment} reviews."
        else:
            breakdown = data.get('breakdown', {})
            return f"Total: {count} reviews ({breakdown.get('positive', 0)} positive, {breakdown.get('negative', 0)} negative)"
    
    def _generate_keyword_summary(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate summary for keyword extraction results."""
        keywords = data.get('keywords', [])
        top_n = parameters.get('top_n', 100)
        sentiment = parameters.get('sentiment', '')
        topic = parameters.get('topic', '')
        method = parameters.get('method', 'frequency')
        
        if not keywords:
            return "No keywords found matching the criteria."
        
        filter_text = ""
        if sentiment:
            filter_text += f" {sentiment}"
        if topic:
            filter_text += f" {topic}-related"
        
        top_words = [word for word, score in keywords[:5]]
        summary = f"Top{filter_text} keywords (using {method}): {', '.join(top_words)}"
        
        if len(keywords) > 5:
            summary += f" (and {len(keywords) - 5} more)"
        
        return summary
    
    def _generate_statistics_summary(self, data: Dict[str, Any]) -> str:
        """Generate summary for statistics query results."""
        sentiment_counts = data.get('sentiment_counts', {})
        text_stats = data.get('text_statistics', {})
        
        summary = f"Dataset contains {sentiment_counts.get('total', 0)} reviews: "
        summary += f"{sentiment_counts.get('positive', 0)} positive, {sentiment_counts.get('negative', 0)} negative. "
        summary += f"Average review length: {text_stats.get('average_characters_per_review', 0):.0f} characters."
        
        return summary
    
    def _generate_comparison_summary(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate summary for comparison query results."""
        sentiment_counts = data.get('sentiment_counts', {})
        keyword_comparison = data.get('keyword_comparison', {})
        
        pos_count = sentiment_counts.get('positive', 0)
        neg_count = sentiment_counts.get('negative', 0)
        
        pos_keywords = keyword_comparison.get('positive', [])[:3]
        neg_keywords = keyword_comparison.get('negative', [])[:3]
        
        summary = f"Comparison: {pos_count} positive vs {neg_count} negative reviews. "
        
        if pos_keywords:
            pos_words = [word for word, score in pos_keywords]
            summary += f"Top positive words: {', '.join(pos_words)}. "
        
        if neg_keywords:
            neg_words = [word for word, score in neg_keywords]
            summary += f"Top negative words: {', '.join(neg_words)}."
        
        return summary
    
    def get_query_suggestions(self) -> Dict[str, List[str]]:
        """Get example queries for each query type."""
        suggestions = {}
        for query_type in QueryType:
            suggestions[query_type.value] = self.query_router.get_query_suggestions(query_type)
        return suggestions
    
    def get_available_topics(self) -> List[str]:
        """Get list of available topics."""
        return self.topic_classifier.get_available_topics()