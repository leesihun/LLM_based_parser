"""
Keyword Extractor Module
Extracts and ranks keywords from reviews using NLP techniques.
Supports TF-IDF analysis and frequency-based keyword extraction.
"""

import logging
from typing import List, Dict, Tuple
from collections import Counter
import re
import math

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """Extractor for identifying important keywords in reviews."""
    
    def __init__(self):
        """Initialize keyword extractor."""
        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'among', 'around', 'beside', 'beyond', 'under', 'over', 'within',
            'without', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those',
            'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'get', 'got', 'go', 'going', 'went', 'gone', 'come', 'came', 'coming',
            'said', 'say', 'saying', 'says', 'see', 'saw', 'seen', 'seeing', 'know', 'knew', 'known',
            'knowing', 'think', 'thought', 'thinking', 'thinks', 'make', 'made', 'making', 'makes',
            'take', 'took', 'taken', 'taking', 'takes', 'give', 'gave', 'given', 'giving', 'gives',
            'want', 'wanted', 'wanting', 'wants', 'need', 'needed', 'needing', 'needs', 'like', 'liked',
            'liking', 'likes', 'use', 'used', 'using', 'uses', 'work', 'worked', 'working', 'works',
            'find', 'found', 'finding', 'finds', 'try', 'tried', 'trying', 'tries', 'look', 'looked',
            'looking', 'looks', 'feel', 'felt', 'feeling', 'feels', 'seem', 'seemed', 'seeming', 'seems',
            'turn', 'turned', 'turning', 'turns', 'put', 'putting', 'puts', 'keep', 'kept', 'keeping',
            'keeps', 'let', 'letting', 'lets', 'run', 'ran', 'running', 'runs', 'move', 'moved',
            'moving', 'moves', 'play', 'played', 'playing', 'plays', 'live', 'lived', 'living', 'lives',
            'show', 'showed', 'showing', 'shows', 'hear', 'heard', 'hearing', 'hears', 'ask', 'asked',
            'asking', 'asks', 'tell', 'told', 'telling', 'tells', 'become', 'became', 'becoming',
            'becomes', 'leave', 'left', 'leaving', 'leaves', 'call', 'called', 'calling', 'calls',
            'back', 'still', 'only', 'now', 'way', 'well', 'also', 'new', 'first', 'last', 'long',
            'great', 'little', 'own', 'other', 'old', 'right', 'big', 'high', 'different', 'small',
            'large', 'next', 'early', 'young', 'important', 'few', 'public', 'same', 'able', 'really',
            'very', 'much', 'many', 'most', 'more', 'some', 'all', 'any', 'each', 'every', 'both',
            'either', 'neither', 'such', 'so', 'too', 'quite', 'rather', 'pretty', 'enough', 'less',
            'least', 'better', 'best', 'worse', 'worst', 'here', 'there', 'where', 'when', 'why',
            'how', 'what', 'who', 'which', 'whose', 'whom', 'whoever', 'whatever', 'whichever',
            'wherever', 'whenever', 'however', 'yes', 'no', 'not', 'never', 'ever', 'always', 'often',
            'sometimes', 'usually', 'again', 'once', 'twice', 'then', 'than', 'as', 'if', 'unless',
            'until', 'while', 'since', 'because', 'although', 'though', 'even', 'just', 'phone'
        }
        
        logger.info("Keyword extractor initialized")
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text by removing sentiment prefix, cleaning, and tokenizing.
        
        Args:
            text: Raw review text
            
        Returns:
            List of cleaned words
        """
        # Remove sentiment prefix
        clean_text = text
        if clean_text.startswith("[POSITIVE]") or clean_text.startswith("[NEGATIVE]"):
            clean_text = clean_text.split("]", 1)[1].strip()
        
        # Convert to lowercase
        clean_text = clean_text.lower()
        
        # Remove special characters and numbers, keep letters and spaces
        clean_text = re.sub(r'[^a-z\s]', ' ', clean_text)
        
        # Split into words and filter
        words = clean_text.split()
        
        # Filter out stop words and very short words
        filtered_words = [
            word for word in words 
            if len(word) > 2 and word not in self.stop_words
        ]
        
        return filtered_words
    
    def extract_keywords_by_frequency(self, reviews: List[str], top_n: int = 100) -> List[Tuple[str, int]]:
        """
        Extract keywords based on frequency analysis.
        
        Args:
            reviews: List of review texts
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, frequency) tuples sorted by frequency
        """
        all_words = []
        for review in reviews:
            words = self.preprocess_text(review)
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        logger.info(f"Extracted top {min(top_n, len(word_counts))} keywords from {len(reviews)} reviews")
        return word_counts.most_common(top_n)
    
    def extract_keywords_by_tfidf(self, reviews: List[str], top_n: int = 100) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF (Term Frequency-Inverse Document Frequency) analysis.
        
        Args:
            reviews: List of review texts
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, tfidf_score) tuples sorted by TF-IDF score
        """
        if not reviews:
            return []
        
        # Preprocess all reviews
        processed_reviews = [self.preprocess_text(review) for review in reviews]
        
        # Calculate term frequencies for each document
        doc_term_freqs = []
        for doc_words in processed_reviews:
            if doc_words:  # Only process non-empty documents
                word_counts = Counter(doc_words)
                total_words = len(doc_words)
                # Normalize by document length (TF)
                term_freq = {word: count / total_words for word, count in word_counts.items()}
                doc_term_freqs.append(term_freq)
            else:
                doc_term_freqs.append({})
        
        # Calculate document frequency for each term
        all_terms = set()
        for doc_tf in doc_term_freqs:
            all_terms.update(doc_tf.keys())
        
        doc_frequencies = {}
        total_docs = len(doc_term_freqs)
        for term in all_terms:
            # Count in how many documents this term appears
            doc_count = sum(1 for doc_tf in doc_term_freqs if term in doc_tf)
            # Calculate IDF
            doc_frequencies[term] = math.log(total_docs / doc_count) if doc_count > 0 else 0
        
        # Calculate TF-IDF scores
        tfidf_scores = {}
        for doc_tf in doc_term_freqs:
            for term, tf in doc_tf.items():
                idf = doc_frequencies[term]
                tfidf = tf * idf
                if term in tfidf_scores:
                    tfidf_scores[term] += tfidf
                else:
                    tfidf_scores[term] = tfidf
        
        # Sort by TF-IDF score and return top N
        sorted_terms = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"Extracted top {min(top_n, len(sorted_terms))} keywords using TF-IDF from {len(reviews)} reviews")
        return sorted_terms[:top_n]
    
    def extract_positive_keywords(self, reviews: List[str], method: str = "frequency", top_n: int = 100) -> List[Tuple[str, float]]:
        """
        Extract keywords specifically from positive reviews.
        
        Args:
            reviews: List of review texts (will be filtered for positive ones)
            method: Extraction method ('frequency' or 'tfidf')
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, score) tuples
        """
        positive_reviews = [review for review in reviews if review.startswith("[POSITIVE]")]
        
        if not positive_reviews:
            logger.warning("No positive reviews found")
            return []
        
        if method == "tfidf":
            return self.extract_keywords_by_tfidf(positive_reviews, top_n)
        else:
            # Convert frequency tuples to match TF-IDF format
            freq_results = self.extract_keywords_by_frequency(positive_reviews, top_n)
            return [(word, float(count)) for word, count in freq_results]
    
    def extract_negative_keywords(self, reviews: List[str], method: str = "frequency", top_n: int = 100) -> List[Tuple[str, float]]:
        """
        Extract keywords specifically from negative reviews.
        
        Args:
            reviews: List of review texts (will be filtered for negative ones)
            method: Extraction method ('frequency' or 'tfidf')
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, score) tuples
        """
        negative_reviews = [review for review in reviews if review.startswith("[NEGATIVE]")]
        
        if not negative_reviews:
            logger.warning("No negative reviews found")
            return []
        
        if method == "tfidf":
            return self.extract_keywords_by_tfidf(negative_reviews, top_n)
        else:
            # Convert frequency tuples to match TF-IDF format
            freq_results = self.extract_keywords_by_frequency(negative_reviews, top_n)
            return [(word, float(count)) for word, count in freq_results]
    
    def compare_sentiment_keywords(self, reviews: List[str], method: str = "frequency", top_n: int = 50) -> Dict[str, List[Tuple[str, float]]]:
        """
        Compare keywords between positive and negative reviews.
        
        Args:
            reviews: List of review texts
            method: Extraction method ('frequency' or 'tfidf')
            top_n: Number of top keywords per sentiment
            
        Returns:
            Dictionary with 'positive' and 'negative' keyword lists
        """
        positive_keywords = self.extract_positive_keywords(reviews, method, top_n)
        negative_keywords = self.extract_negative_keywords(reviews, method, top_n)
        
        return {
            "positive": positive_keywords,
            "negative": negative_keywords
        }
    
    def get_keyword_context(self, reviews: List[str], keyword: str, context_words: int = 5) -> List[str]:
        """
        Get context snippets where a specific keyword appears.
        
        Args:
            reviews: List of review texts
            keyword: Keyword to search for
            context_words: Number of words before and after the keyword
            
        Returns:
            List of context snippets containing the keyword
        """
        contexts = []
        keyword_lower = keyword.lower()
        
        for review in reviews:
            # Remove sentiment prefix
            clean_text = review
            if clean_text.startswith("[POSITIVE]") or clean_text.startswith("[NEGATIVE]"):
                clean_text = clean_text.split("]", 1)[1].strip()
            
            words = clean_text.split()
            
            for i, word in enumerate(words):
                if keyword_lower in word.lower():
                    # Extract context around the keyword
                    start = max(0, i - context_words)
                    end = min(len(words), i + context_words + 1)
                    context = " ".join(words[start:end])
                    contexts.append(f"...{context}...")
        
        return contexts[:20]  # Limit to 20 examples