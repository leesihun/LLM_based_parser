#!/usr/bin/env python3
"""
Keyword Extraction Module
Extracts relevant keywords from natural language queries for improved web search
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any, Tuple
from collections import Counter
import json
import math


class KeywordExtractor:
    """Multi-method keyword extraction for search query optimization"""
    
    def __init__(self, config: Optional[Dict] = None, llm_client=None):
        """Initialize keyword extractor with configuration"""
        self.config = config or {}
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
        # Load stop words and technical terms
        self.stop_words = self._load_stop_words()
        self.technical_keywords = self._load_technical_keywords()
        
        # Configuration settings
        self.use_llm = self.config.get('use_llm', False)
        if self.use_llm and self.llm_client:
            self.extraction_methods = ['llm_assisted']
        else:
            self.extraction_methods = self.config.get('extraction_methods', ['rule_based', 'tfidf'])
        
        self.max_keywords = self.config.get('max_keywords', 10)
        self.min_keyword_length = self.config.get('min_keyword_length', 2)
        self.enable_query_expansion = self.config.get('query_expansion', True)
        
        self.logger.info("Keyword extractor initialized")
    
    def _load_stop_words(self) -> Set[str]:
        """Load common stop words to filter out"""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'i', 'me',
            'my', 'we', 'our', 'they', 'them', 'their', 'this', 'these',
            'those', 'can', 'could', 'should', 'what', 'where', 'when', 'how',
            'why', 'who', 'which', 'do', 'does', 'did', 'have', 'had', 'been',
            'being', 'get', 'got', 'make', 'made', 'help', 'please', 'thanks',
            'thank', 'understand', 'explain', 'show', 'tell', 'find', 'need',
            'want', 'like', 'know', 'see', 'looking', 'search', 'about',
            'some', 'any', 'all', 'each', 'every', 'both', 'either', 'neither',
            'more', 'most', 'other', 'another', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
    
    def _load_technical_keywords(self) -> Set[str]:
        """Load technical terms that should be prioritized"""
        return {
            'python', 'java', 'javascript', 'html', 'css', 'sql', 'api', 'rest',
            'json', 'xml', 'http', 'https', 'git', 'github', 'docker', 'kubernetes',
            'algorithm', 'algorithms', 'data', 'database', 'framework', 'library',
            'machine learning', 'ml', 'ai', 'artificial intelligence', 'neural network',
            'deep learning', 'nlp', 'natural language processing', 'tensorflow',
            'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'django',
            'flask', 'react', 'angular', 'vue', 'node', 'express', 'mongodb',
            'postgresql', 'mysql', 'redis', 'elasticsearch', 'aws', 'azure',
            'cloud', 'devops', 'ci', 'cd', 'testing', 'unit test', 'integration',
            'security', 'authentication', 'authorization', 'oauth', 'jwt',
            'microservices', 'architecture', 'design pattern', 'solid', 'clean code'
        }
    
    def extract_keywords(self, text: str) -> Dict[str, Any]:
        """
        Main method to extract keywords using multiple approaches
        
        Args:
            text: Input natural language text
            
        Returns:
            Dictionary with extracted keywords and metadata
        """
        if not text or not text.strip():
            return {
                'keywords': [],
                'queries': [],
                'method': 'none',
                'original_text': text,
                'adequate_keywords': False
            }
        
        results = {
            'original_text': text,
            'keywords': [],
            'queries': [],
            'extraction_results': {}
        }
        
        # Try different extraction methods
        for method in self.extraction_methods:
            try:
                if method == 'rule_based':
                    keywords = self._extract_rule_based(text)
                    results['extraction_results']['rule_based'] = keywords
                    
                elif method == 'tfidf':
                    keywords = self._extract_tfidf(text)
                    results['extraction_results']['tfidf'] = keywords
                    
                elif method == 'llm_assisted' and self.llm_client:
                    keywords = self._extract_llm_assisted(text)
                    results['extraction_results']['llm_assisted'] = keywords
                    
            except Exception as e:
                self.logger.warning(f"Extraction method {method} failed: {e}")
                continue
        
        # Combine and rank results
        final_keywords = self._combine_results(results['extraction_results'])
        results['keywords'] = final_keywords[:self.max_keywords]
        
        # Check if we have adequate keywords for search
        adequate_keywords = self._has_adequate_keywords(results['keywords'], text)
        results['adequate_keywords'] = adequate_keywords
        
        # Generate optimized search queries only if we have adequate keywords
        if adequate_keywords and self.enable_query_expansion:
            results['queries'] = self._generate_search_queries(results['keywords'], text)
        elif adequate_keywords:
            results['queries'] = [' '.join(results['keywords'])]
        else:
            results['queries'] = []
        
        results['method'] = 'combined' if len(self.extraction_methods) > 1 else self.extraction_methods[0]
        
        self.logger.debug(f"Extracted {len(results['keywords'])} keywords from text, adequate: {adequate_keywords}")
        return results
    
    def _extract_rule_based(self, text: str) -> List[Tuple[str, float]]:
        """Rule-based keyword extraction using linguistic patterns"""
        # Clean and normalize text
        text = self._clean_text(text)
        words = text.lower().split()
        
        # Filter out stop words and short words
        filtered_words = [
            word for word in words 
            if len(word) >= self.min_keyword_length 
            and word not in self.stop_words
            and re.match(r'^[a-zA-Z0-9_-]+$', word)
        ]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Score words based on various factors
        scored_words = []
        for word, count in word_counts.items():
            score = count
            
            # Boost technical terms
            if word in self.technical_keywords:
                score *= 2.0
            
            # Boost longer words (likely more specific)
            if len(word) > 6:
                score *= 1.3
            
            # Boost capitalized words (likely proper nouns/acronyms)
            if any(w[0].isupper() for w in text.split() if w.lower() == word):
                score *= 1.2
            
            scored_words.append((word, score))
        
        # Extract multi-word technical terms
        multiword_terms = self._extract_multiword_terms(text)
        for term, score in multiword_terms:
            scored_words.append((term, score))
        
        # Sort by score descending
        scored_words.sort(key=lambda x: x[1], reverse=True)
        return scored_words
    
    def _extract_tfidf(self, text: str) -> List[Tuple[str, float]]:
        """TF-IDF based keyword extraction (simplified version)"""
        # Clean text and get words
        text = self._clean_text(text)
        words = [word.lower() for word in text.split() 
                if len(word) >= self.min_keyword_length 
                and word.lower() not in self.stop_words]
        
        if not words:
            return []
        
        # Calculate term frequency
        word_counts = Counter(words)
        total_words = len(words)
        
        # Simple TF-IDF calculation (assuming single document)
        tfidf_scores = []
        for word, count in word_counts.items():
            tf = count / total_words
            # Use inverse document frequency approximation based on word length and rarity
            idf = math.log(len(set(words)) / (count + 1)) + 1
            
            # Boost score for technical terms
            boost = 2.0 if word in self.technical_keywords else 1.0
            
            tfidf_score = tf * idf * boost
            tfidf_scores.append((word, tfidf_score))
        
        tfidf_scores.sort(key=lambda x: x[1], reverse=True)
        return tfidf_scores
    
    def _extract_llm_assisted(self, text: str) -> List[Tuple[str, float]]:
        """Use LLM to intelligently extract keywords with custom system prompt"""
        if not self.llm_client:
            return []
        
        try:
            # Get LLM extraction configuration
            llm_config = self.config.get('llm_extraction', {})
            system_prompt = llm_config.get('system_prompt', '')
            temperature = llm_config.get('temperature', 0.3)
            max_tokens = llm_config.get('max_tokens', 100)
            fallback_to_original = llm_config.get('fallback_to_original', True)
            
            if not system_prompt:
                self.logger.warning("No system prompt configured for LLM keyword extraction")
                return []
            
            # Create conversation context with system prompt and user query
            conversation_context = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ]
            
            # Call LLM with conversation context
            response = self.llm_client.chat_completion(
                conversation_context,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract content from response
            if isinstance(response, dict):
                keywords_text = response.get('content', '').strip()
                # Check if response contains an error
                if keywords_text.lower().startswith('error'):
                    raise Exception(f"LLM returned error: {keywords_text}")
            else:
                keywords_text = str(response).strip()
                # Check if response contains an error
                if keywords_text.lower().startswith('error'):
                    raise Exception(f"LLM returned error: {keywords_text}")
            
            if not keywords_text:
                self.logger.warning("LLM returned empty response for keyword extraction")
                if fallback_to_original:
                    return [(text, 1.0)]
                return []
            
            # Parse the LLM response
            keywords = []
            for keyword in keywords_text.split(','):
                keyword = keyword.strip().strip('"\'')
                if keyword and len(keyword) >= self.min_keyword_length:
                    # Assign higher scores to earlier keywords (LLM ordered by importance)
                    score = 1.0 - (len(keywords) * 0.1)
                    keywords.append((keyword.lower(), max(score, 0.1)))
            
            self.logger.info(f"LLM extracted {len(keywords)} keywords: {[k[0] for k in keywords[:3]]}")
            return keywords
                
        except Exception as e:
            self.logger.warning(f"LLM-assisted extraction failed: {e}")
        
        return []
    
    def _extract_multiword_terms(self, text: str) -> List[Tuple[str, float]]:
        """Extract multi-word technical terms and phrases"""
        multiword_terms = []
        
        # Look for multi-word technical terms
        for term in self.technical_keywords:
            if ' ' in term and term.lower() in text.lower():
                # Count occurrences
                count = text.lower().count(term.lower())
                if count > 0:
                    # Higher score for multi-word technical terms
                    score = count * 2.5
                    multiword_terms.append((term, score))
        
        # Extract quoted phrases (likely important)
        quoted_phrases = re.findall(r'"([^"]+)"', text)
        for phrase in quoted_phrases:
            if len(phrase.split()) <= 4:  # Reasonable phrase length
                multiword_terms.append((phrase.lower(), 2.0))
        
        return multiword_terms
    
    def _combine_results(self, extraction_results: Dict[str, List[Tuple[str, float]]]) -> List[str]:
        """Combine results from different extraction methods"""
        if not extraction_results:
            return []
        
        # Aggregate scores from all methods
        combined_scores = {}
        
        for method, results in extraction_results.items():
            weight = 1.0
            if method == 'llm_assisted':
                weight = 1.5  # Give more weight to LLM results
            elif method == 'rule_based':
                weight = 1.2
            elif method == 'tfidf':
                weight = 1.0
            
            for keyword, score in results:
                if keyword not in combined_scores:
                    combined_scores[keyword] = 0
                combined_scores[keyword] += score * weight
        
        # Sort by combined score
        sorted_keywords = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return just the keywords (without scores)
        return [keyword for keyword, score in sorted_keywords]
    
    def _has_adequate_keywords(self, keywords: List[str], original_text: str) -> bool:
        """
        Determine if extracted keywords are adequate for web search
        
        Args:
            keywords: List of extracted keywords
            original_text: Original input text
            
        Returns:
            True if keywords are adequate for search, False otherwise
        """
        if not keywords:
            return False
        
        # Must have at least 2 meaningful keywords
        if len(keywords) < 2:
            return False
        
        # Check if keywords are too generic
        generic_words = {'help', 'please', 'can', 'how', 'what', 'where', 'when', 'why', 'who', 
                        'question', 'answer', 'explain', 'show', 'tell', 'find', 'search'}
        meaningful_keywords = [kw for kw in keywords if kw.lower() not in generic_words and len(kw) > 2]
        
        # Must have at least 2 meaningful, non-generic keywords
        if len(meaningful_keywords) < 2:
            return False
        
        # Check if we have at least one technical term or substantial keyword
        has_technical_term = any(kw.lower() in self.technical_keywords or len(kw) > 5 for kw in meaningful_keywords)
        
        # Must have either technical terms or substantial keywords
        if not has_technical_term:
            return False
        
        # Check minimum combined keyword length (avoid single-letter combinations)
        total_length = sum(len(kw) for kw in meaningful_keywords)
        if total_length < 8:
            return False
        
        return True
    
    def _generate_search_queries(self, keywords: List[str], original_text: str) -> List[str]:
        """Generate optimized search queries from keywords"""
        if not keywords:
            return []
        
        queries = []
        
        # Primary query: top keywords combined
        primary_keywords = keywords[:5]
        if primary_keywords:
            queries.append(' '.join(primary_keywords))
        
        # Secondary query: focus on technical terms
        tech_keywords = [kw for kw in keywords if kw in self.technical_keywords or len(kw.split()) > 1]
        if tech_keywords and len(tech_keywords) >= 2:
            queries.append(' '.join(tech_keywords[:4]))
        
        # Tertiary query: specific concepts (longer keywords)
        specific_keywords = [kw for kw in keywords if len(kw) > 6 or ' ' in kw]
        if specific_keywords and len(specific_keywords) >= 2:
            queries.append(' '.join(specific_keywords[:3]))
        
        # Don't use fallback - if no queries generated, return empty list
        
        # Remove duplicates while preserving order
        unique_queries = []
        for query in queries:
            if query and query not in unique_queries:
                unique_queries.append(query)
        
        return unique_queries[:3]  # Limit to 3 queries maximum
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove common question words at the beginning
        question_starters = [
            'how do i', 'how to', 'how can i', 'what is', 'what are', 'where is',
            'when is', 'why is', 'can you help', 'please help', 'i need', 'i want'
        ]
        
        text_lower = text.lower()
        for starter in question_starters:
            if text_lower.startswith(starter):
                text = text[len(starter):].strip()
                break
        
        # Remove punctuation except hyphens and underscores
        text = re.sub(r'[^\w\s\-_]', ' ', text)
        
        # Clean up multiple spaces
        text = ' '.join(text.split())
        
        return text
    
    def optimize_query_for_search_engine(self, query: str, search_engine: str = 'bing') -> str:
        """Optimize query for specific search engines"""
        if not query:
            return query
        
        # Engine-specific optimizations
        if search_engine.lower() == 'bing':
            # Bing works well with quoted phrases for exact matches
            words = query.split()
            if len(words) > 1:
                # Quote multi-word technical terms
                for term in self.technical_keywords:
                    if ' ' in term and term.lower() in query.lower():
                        query = query.replace(term, f'"{term}"')
        
        elif search_engine.lower() == 'google':
            # Google handles boolean operators well
            words = query.split()
            if len(words) > 3:
                # Add OR for related terms
                query = ' OR '.join([' '.join(words[i:i+2]) for i in range(0, len(words), 2)])
        
        return query


def test_keyword_extractor():
    """Test the keyword extractor with sample queries"""
    print("Testing Keyword Extractor")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "How can I implement machine learning algorithms for natural language processing in Python?",
        "What are the best practices for React component architecture and state management?",
        "Can you help me understand Docker containerization and Kubernetes deployment strategies?",
        "I need help with SQL database optimization and query performance tuning",
        "Show me examples of REST API design patterns using Express.js and Node.js"
    ]
    
    extractor = KeywordExtractor({
        'extraction_methods': ['rule_based', 'tfidf'],
        'max_keywords': 8,
        'query_expansion': True
    })
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 40)
        
        results = extractor.extract_keywords(query)
        
        print(f"Keywords: {results['keywords'][:5]}")
        print(f"Search Queries:")
        for j, search_query in enumerate(results['queries'], 1):
            print(f"  {j}. {search_query}")
    
    print("\nKeyword extraction test completed!")


if __name__ == "__main__":
    test_keyword_extractor()