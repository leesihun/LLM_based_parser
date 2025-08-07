"""
Enhanced Query Engine for Markdown-based LLM Analysis
Handles specific question types mentioned in requirements.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from src.enhanced_ollama_client import EnhancedOllamaClient
from config.enhanced_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedQueryEngine:
    def __init__(self, markdown_file_path: str, ollama_client: Optional[EnhancedOllamaClient] = None):
        self.markdown_file_path = markdown_file_path
        self.ollama_client = ollama_client or EnhancedOllamaClient()
        self.markdown_content = self._load_markdown_content()
        
        logger.info(f"Enhanced Query Engine initialized with markdown: {markdown_file_path}")
    
    def _load_markdown_content(self) -> str:
        """Load the consolidated markdown file content."""
        try:
            with open(self.markdown_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded markdown content: {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"Error loading markdown file: {e}")
            return ""
    
    def classify_question_type(self, question: str) -> Dict[str, Any]:
        """Classify the type of question being asked."""
        system_prompt = """You are a query classifier for a cellphone review analysis system.
        
        Classify the question into one of these types:
        1. COUNT_SENTIMENT: Questions asking "how many good/bad reviews"
        2. KEYWORD_ANALYSIS: Questions asking about most frequent keywords or semantic analysis
        3. EXAMPLE_REQUEST: Questions asking for examples of reviews (good/bad regarding specific topics)
        4. GENERAL_ANALYSIS: Other analytical questions about the reviews
        
        Also extract:
        - sentiment: "positive", "negative", or null
        - topic: specific topic mentioned (screen, battery, camera, etc.) or null
        - analysis_type: "frequency", "semantic", or "example"
        
        Respond with ONLY a JSON object:
        {
            "type": "COUNT_SENTIMENT|KEYWORD_ANALYSIS|EXAMPLE_REQUEST|GENERAL_ANALYSIS",
            "sentiment": "positive|negative|null",
            "topic": "screen|battery|camera|performance|design|null",
            "analysis_type": "frequency|semantic|example",
            "confidence": 0.0_to_1.0,
            "reasoning": "brief explanation"
        }"""
        
        try:
            response = self.ollama_client.generate_response(
                prompt=f"Classify this question: \"{question}\"",
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            if response:
                classification = json.loads(response)
                return classification
                
        except Exception as e:
            logger.error(f"Error in question classification: {e}")
        
        # Fallback classification
        return {
            "type": "GENERAL_ANALYSIS",
            "sentiment": None,
            "topic": None,
            "analysis_type": "semantic",
            "confidence": 0.1,
            "reasoning": "Classification failed, using fallback"
        }
    
    def handle_count_sentiment_question(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle questions about counting good/bad reviews."""
        system_prompt = """You are analyzing a cellphone review dataset. Based on the provided markdown content,
        answer the question about counting reviews by sentiment.
        
        Look for the "Dataset Statistics" section which contains sentiment distribution data.
        Provide exact numbers and percentages from the statistics section.
        
        Respond in a clear, direct manner with specific numbers."""
        
        prompt = f"""Based on this review dataset, answer: How many responses are good and how many are bad?

Dataset content:
{self.markdown_content[:5000]}  # Truncate for token limits

Provide specific counts and percentages."""
        
        response = self.ollama_client.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
        
        return {
            'answer': response,
            'type': 'count_sentiment',
            'source': 'dataset_statistics'
        }
    
    def handle_keyword_analysis_question(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle questions about keyword frequency and semantic analysis."""
        analysis_type = classification.get('analysis_type', 'semantic')
        
        if analysis_type == 'frequency':
            system_prompt = """You are analyzing keyword frequency in cellphone reviews. 
            Based on the "Keyword Analysis Reference" section in the provided content,
            identify the most frequently used keywords and their counts.
            
            Provide specific keywords with their mention counts and explain what they reveal about user opinions."""
        else:
            system_prompt = """You are performing semantic analysis of cellphone reviews.
            Analyze the review content to identify:
            1. Most common themes and topics
            2. Semantic patterns in positive vs negative reviews
            3. Key concepts that emerge from the reviews
            4. Meaningful word associations and their implications
            
            Go beyond simple word counting to understand deeper meaning patterns."""
        
        # Focus on keyword analysis section
        keyword_section = self._extract_section("Keyword Analysis Reference")
        
        prompt = f"""Analyze the keywords and provide semantic insights:

Keyword Analysis Data:
{keyword_section}

Sample Reviews for Context:
{self.markdown_content[10000:15000]}  # Get some review samples

Question focus: What keywords are used most often and what do they mean semantically?"""
        
        response = self.ollama_client.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        return {
            'answer': response,
            'type': 'keyword_analysis',
            'analysis_type': analysis_type
        }
    
    def handle_example_request_question(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests for specific review examples."""
        sentiment = classification.get('sentiment', 'positive')
        topic = classification.get('topic', None)
        
        # Create search criteria
        search_terms = []
        if sentiment:
            search_terms.append(sentiment.upper())
        if topic:
            search_terms.append(topic)
        
        system_prompt = f"""You are finding specific review examples from a cellphone review dataset.
        Find a good example of a {sentiment} review about {topic if topic else 'the product'}.
        
        Look through the review collection and identify reviews that:
        1. Match the requested sentiment ({sentiment})
        2. Discuss the specific topic ({topic if topic else 'general aspects'})
        3. Are representative and well-written examples
        
        Provide the exact review text and explain why it's a good example."""
        
        # Extract relevant review sections
        if sentiment == 'positive':
            review_section = self._extract_section("POSITIVE REVIEWS")
        else:
            review_section = self._extract_section("NEGATIVE REVIEWS")
        
        prompt = f"""Find an example of a {sentiment} review regarding {topic if topic else 'general experience'}:

Relevant Reviews:
{review_section[:8000]}  # Limit for token constraints

Provide the best example that matches the criteria and explain your choice."""
        
        response = self.ollama_client.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
        
        return {
            'answer': response,
            'type': 'example_request',
            'sentiment': sentiment,
            'topic': topic
        }
    
    def handle_general_analysis_question(self, question: str) -> Dict[str, Any]:
        """Handle general analytical questions about the reviews."""
        system_prompt = """You are a data analyst specializing in customer review analysis.
        Based on the provided cellphone review dataset, answer the analytical question comprehensively.
        
        Use the statistics, keyword analysis, and review content to provide insights.
        Support your analysis with specific examples and data from the dataset."""
        
        prompt = f"""Analyze this question about the cellphone review dataset: "{question}"

Dataset Overview:
{self.markdown_content[:6000]}  # Dataset summary and statistics

Additional Context:
{self.markdown_content[6000:12000]}  # Some review samples

Provide a comprehensive analytical answer based on the data."""
        
        response = self.ollama_client.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        return {
            'answer': response,
            'type': 'general_analysis',
            'question': question
        }
    
    def _extract_section(self, section_name: str) -> str:
        """Extract a specific section from the markdown content."""
        try:
            # Find section start
            start_marker = f"## {section_name}" if section_name.startswith(("Dataset", "Keyword")) else f"### {section_name}"
            start_idx = self.markdown_content.find(start_marker)
            
            if start_idx == -1:
                return ""
            
            # Find next major section
            remaining_content = self.markdown_content[start_idx:]
            next_section_idx = remaining_content.find("\n## ", 1)  # Skip first occurrence
            if next_section_idx == -1:
                next_section_idx = remaining_content.find("\n### ", 1)
            
            if next_section_idx != -1:
                return remaining_content[:next_section_idx]
            else:
                return remaining_content
                
        except Exception as e:
            logger.error(f"Error extracting section {section_name}: {e}")
            return ""
    
    def query(self, question: str) -> Dict[str, Any]:
        """Main query method that routes questions to appropriate handlers."""
        logger.info(f"Processing query: {question}")
        
        # Classify the question
        classification = self.classify_question_type(question)
        question_type = classification.get('type', 'GENERAL_ANALYSIS')
        
        logger.info(f"Classified as: {question_type}")
        
        # Route to appropriate handler
        if question_type == "COUNT_SENTIMENT":
            result = self.handle_count_sentiment_question(classification)
        elif question_type == "KEYWORD_ANALYSIS":
            result = self.handle_keyword_analysis_question(classification)
        elif question_type == "EXAMPLE_REQUEST":
            result = self.handle_example_request_question(classification)
        else:
            result = self.handle_general_analysis_question(question)
        
        # Add metadata
        result['classification'] = classification
        result['question'] = question
        result['timestamp'] = str(datetime.now())
        
        return result

if __name__ == "__main__":
    from datetime import datetime
    
    # Test the query engine (would need actual markdown file)
    markdown_path = "output/consolidated_reviews.md"
    
    if os.path.exists(markdown_path):
        engine = EnhancedQueryEngine(markdown_path)
        
        # Test questions from requirements
        test_questions = [
            "How many responses are good and how many are bad?",
            "What keyword is used most often? and how many times has it been mentioned? Semantically analyze it.",
            "Give me an example of good review regarding screen size.",
            "Give me an example of bad review regarding screen time."
        ]
        
        for question in test_questions:
            print(f"\nQuestion: {question}")
            result = engine.query(question)
            print(f"Answer: {result['answer'][:200]}...")
    else:
        print(f"Markdown file not found: {markdown_path}")
        print("Run the complete pipeline first to generate the consolidated markdown file.")