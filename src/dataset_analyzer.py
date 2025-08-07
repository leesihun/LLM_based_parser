"""
Dataset Analyzer Module
Provides direct access to all documents for counting, statistics, and filtering operations.
Handles queries that require analysis of the entire dataset rather than semantic search.
"""

import logging
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


class DatasetAnalyzer:
    """Analyzer for dataset-wide operations like counting and statistics."""
    
    def __init__(self, documents: List[str]):
        """
        Initialize with all documents from the dataset.
        
        Args:
            documents: List of text documents (with sentiment prefixes like [POSITIVE], [NEGATIVE])
        """
        self.documents = documents
        self.positive_reviews = [doc for doc in documents if doc.startswith("[POSITIVE]")]
        self.negative_reviews = [doc for doc in documents if doc.startswith("[NEGATIVE]")]
        self.unknown_reviews = [doc for doc in documents if not (doc.startswith("[POSITIVE]") or doc.startswith("[NEGATIVE]"))]
        
        logger.info(f"Dataset initialized: {len(self.positive_reviews)} positive, {len(self.negative_reviews)} negative, {len(self.unknown_reviews)} unknown")
    
    def count_reviews_by_sentiment(self) -> Dict[str, int]:
        """Count reviews by sentiment."""
        return {
            "positive": len(self.positive_reviews),
            "negative": len(self.negative_reviews),
            "unknown": len(self.unknown_reviews),
            "total": len(self.documents)
        }
    
    def get_reviews_by_sentiment(self, sentiment: str) -> List[str]:
        """
        Get all reviews of a specific sentiment.
        
        Args:
            sentiment: 'positive', 'negative', or 'all'
            
        Returns:
            List of matching review documents
        """
        if sentiment.lower() == "positive":
            return self.positive_reviews.copy()
        elif sentiment.lower() == "negative":
            return self.negative_reviews.copy()
        elif sentiment.lower() == "all":
            return self.documents.copy()
        else:
            logger.warning(f"Unknown sentiment: {sentiment}")
            return []
    
    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get comprehensive dataset statistics."""
        sentiment_counts = self.count_reviews_by_sentiment()
        
        # Calculate text statistics
        total_chars = sum(len(doc) for doc in self.documents)
        avg_chars = total_chars / len(self.documents) if self.documents else 0
        
        positive_chars = sum(len(doc) for doc in self.positive_reviews)
        negative_chars = sum(len(doc) for doc in self.negative_reviews)
        
        return {
            "sentiment_counts": sentiment_counts,
            "text_statistics": {
                "total_characters": total_chars,
                "average_characters_per_review": round(avg_chars, 1),
                "positive_characters": positive_chars,
                "negative_characters": negative_chars
            }
        }
    
    def filter_reviews_containing_keywords(self, keywords: List[str], sentiment: str = "all", case_sensitive: bool = False) -> List[str]:
        """
        Filter reviews containing specific keywords.
        
        Args:
            keywords: List of keywords to search for
            sentiment: Filter by sentiment ('positive', 'negative', 'all')
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of matching reviews
        """
        # Get reviews by sentiment
        reviews = self.get_reviews_by_sentiment(sentiment)
        
        if not keywords:
            return reviews
        
        # Filter reviews containing any of the keywords
        matching_reviews = []
        for review in reviews:
            review_text = review if case_sensitive else review.lower()
            search_keywords = keywords if case_sensitive else [kw.lower() for kw in keywords]
            
            if any(keyword in review_text for keyword in search_keywords):
                matching_reviews.append(review)
        
        logger.info(f"Found {len(matching_reviews)} reviews containing keywords: {keywords}")
        return matching_reviews
    
    def count_reviews_containing_keywords(self, keywords: List[str], sentiment: str = "all", case_sensitive: bool = False) -> int:
        """
        Count reviews containing specific keywords.
        
        Args:
            keywords: List of keywords to search for
            sentiment: Filter by sentiment ('positive', 'negative', 'all')
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            Count of matching reviews
        """
        matching_reviews = self.filter_reviews_containing_keywords(keywords, sentiment, case_sensitive)
        return len(matching_reviews)
    
    def get_word_frequency(self, sentiment: str = "all", top_n: int = 100) -> List[tuple]:
        """
        Get word frequency analysis for reviews of specific sentiment.
        
        Args:
            sentiment: Filter by sentiment ('positive', 'negative', 'all')
            top_n: Number of top words to return
            
        Returns:
            List of (word, count) tuples sorted by frequency
        """
        reviews = self.get_reviews_by_sentiment(sentiment)
        
        # Extract words from all reviews
        all_words = []
        for review in reviews:
            # Remove sentiment prefix and split into words
            clean_text = review
            if clean_text.startswith("[POSITIVE]") or clean_text.startswith("[NEGATIVE]"):
                clean_text = clean_text.split("]", 1)[1].strip()
            
            # Simple word extraction (split on whitespace and common punctuation)
            words = clean_text.replace(",", " ").replace(".", " ").replace("!", " ").replace("?", " ").split()
            # Filter out very short words and convert to lowercase
            words = [word.lower().strip(".,!?;:()[]{}\"'") for word in words if len(word.strip(".,!?;:()[]{}\"'")) > 2]
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        return word_counts.most_common(top_n)