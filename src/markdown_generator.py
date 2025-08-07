"""
Consolidated Markdown Generator
Creates a comprehensive markdown file from all processed reviews for LLM querying.
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarkdownGenerator:
    def __init__(self, output_directory: str = "output"):
        self.output_directory = output_directory
        os.makedirs(output_directory, exist_ok=True)
    
    def generate_markdown_header(self) -> str:
        """Generate markdown file header with metadata."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# Cellphone Review Analysis Dataset

**Generated:** {timestamp}
**System:** LLM-based Review Parser
**Models:** gemma3:12b (LLM), nomic-embed-text:latest (Embedding)

---

## Dataset Summary

This document contains processed cellphone reviews from Excel files with the following processing:
- **Language Detection**: Automatic detection of review language
- **Translation**: Non-English reviews translated to English with original preserved
- **Spell Correction**: Automatic correction of spelling errors
- **Sentiment Classification**: Reviews categorized as positive/negative based on source file
- **Topic Identification**: Reviews tagged with relevant topics (screen, battery, camera, etc.)

---

"""
    
    def generate_dataset_statistics(self, reviews: List[Dict[str, Any]]) -> str:
        """Generate statistics section for the markdown."""
        total_count = len(reviews)
        
        # Count by sentiment
        sentiment_counts = {}
        language_counts = {}
        file_counts = {}
        translated_count = 0
        
        for review in reviews:
            # Sentiment counts
            sentiment = review.get('sentiment', 'unknown')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # Language counts
            language = review.get('language', 'unknown')
            language_counts[language] = language_counts.get(language, 0) + 1
            
            # File source counts
            file_source = review.get('file_source', 'unknown')
            file_counts[file_source] = file_counts.get(file_source, 0) + 1
            
            # Translation counts
            if review.get('needs_translation', False):
                translated_count += 1
        
        stats_md = f"""## Dataset Statistics

### Overall Counts
- **Total Reviews**: {total_count}
- **Reviews Requiring Translation**: {translated_count}
- **Original Language Reviews**: {total_count - translated_count}

### Sentiment Distribution
"""
        for sentiment, count in sentiment_counts.items():
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            stats_md += f"- **{sentiment.title()}**: {count} ({percentage:.1f}%)\n"
        
        stats_md += "\n### Language Distribution\n"
        for language, count in language_counts.items():
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            stats_md += f"- **{language.title()}**: {count} ({percentage:.1f}%)\n"
        
        stats_md += "\n### Source File Distribution\n"
        for file_name, count in file_counts.items():
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            stats_md += f"- **{file_name}**: {count} ({percentage:.1f}%)\n"
        
        stats_md += "\n---\n\n"
        return stats_md
    
    def extract_topics_from_review(self, review_text: str) -> List[str]:
        """Extract relevant topics from review text using keyword matching."""
        topics = []
        text_lower = review_text.lower()
        
        # Define topic keywords
        topic_keywords = {
            'screen': ['screen', 'display', 'resolution', 'brightness', 'color', 'pixel'],
            'battery': ['battery', 'charge', 'power', 'energy', 'drain', 'life'],
            'camera': ['camera', 'photo', 'picture', 'video', 'lens', 'zoom'],
            'performance': ['performance', 'speed', 'fast', 'slow', 'lag', 'smooth'],
            'design': ['design', 'build', 'quality', 'material', 'premium', 'sleek'],
            'folding': ['fold', 'hinge', 'crease', 'unfold', 'flexible'],
            'user_interface': ['interface', 'ui', 'menu', 'navigation', 'intuitive'],
            'multitasking': ['multitask', 'split', 'window', 'app', 'switch'],
            'durability': ['durable', 'sturdy', 'fragile', 'break', 'scratch'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'value', 'worth']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['general']
    
    def generate_review_section(self, reviews: List[Dict[str, Any]]) -> str:
        """Generate the main reviews section of the markdown."""
        reviews_md = "## Review Collection\n\n"
        
        # Group reviews by sentiment for better organization
        positive_reviews = [r for r in reviews if r.get('sentiment') == 'positive']
        negative_reviews = [r for r in reviews if r.get('sentiment') == 'negative']
        
        # Process positive reviews
        if positive_reviews:
            reviews_md += "### POSITIVE REVIEWS 👍\n\n"
            for idx, review in enumerate(positive_reviews, 1):
                reviews_md += self.format_single_review(review, f"POS-{idx}")
        
        # Process negative reviews
        if negative_reviews:
            reviews_md += "\n### NEGATIVE REVIEWS 👎\n\n"
            for idx, review in enumerate(negative_reviews, 1):
                reviews_md += self.format_single_review(review, f"NEG-{idx}")
        
        return reviews_md
    
    def format_single_review(self, review: Dict[str, Any], review_id: str) -> str:
        """Format a single review entry in markdown."""
        # Extract topics
        translated_text = review.get('translated_text', review.get('original_text', ''))
        topics = self.extract_topics_from_review(translated_text)
        
        # Format language info
        language = review.get('language', 'unknown')
        language_emoji = {
            'korean': '🇰🇷',
            'english': '🇺🇸',
            'chinese': '🇨🇳',
            'japanese': '🇯🇵'
        }.get(language, '🌐')
        
        # Create review entry
        review_md = f"""#### Review {review_id} {language_emoji}

**Sentiment:** {review.get('sentiment', 'unknown').upper()}  
**Language:** {language.title()}  
**Topics:** {', '.join(topics)}  
**Source:** {review.get('file_source', 'unknown')}  

"""
        
        # Add original text if it exists and is different from translated
        original_text = review.get('original_text', '')
        if original_text and language != 'english':
            review_md += f"**Original Text ({language}):**  \n> {original_text}\n\n"
        
        # Add translated/corrected text
        review_md += f"**English Text:**  \n> {translated_text}\n\n"
        
        # Add correction info if available
        corrections = review.get('corrections_made', '')
        if corrections and corrections != 'None':
            review_md += f"**Corrections Made:** {corrections}\n\n"
        
        review_md += "---\n\n"
        return review_md
    
    def generate_keyword_analysis_section(self, reviews: List[Dict[str, Any]]) -> str:
        """Generate keyword analysis section for LLM reference."""
        keywords_md = """## Keyword Analysis Reference

### Most Common Words by Category

This section provides keyword frequency data for LLM analysis:

#### Positive Review Keywords
"""
        
        # Collect all positive review texts
        positive_texts = []
        negative_texts = []
        
        for review in reviews:
            text = review.get('translated_text', review.get('original_text', ''))
            if review.get('sentiment') == 'positive':
                positive_texts.append(text.lower())
            elif review.get('sentiment') == 'negative':
                negative_texts.append(text.lower())
        
        # Basic keyword extraction (you could enhance this with proper NLP)
        keywords_md += self.extract_common_keywords(positive_texts, "positive")
        keywords_md += "\n#### Negative Review Keywords\n"
        keywords_md += self.extract_common_keywords(negative_texts, "negative")
        
        keywords_md += "\n---\n\n"
        return keywords_md
    
    def extract_common_keywords(self, texts: List[str], sentiment: str) -> str:
        """Extract and format common keywords from texts."""
        # Simple word frequency analysis
        word_freq = {}
        stop_words = {'the', 'is', 'in', 'terms', 'of', 'a', 'an', 'and', 'or', 'but', 'it', 'this', 'that'}
        
        for text in texts:
            words = text.replace('.', '').replace(',', '').replace('!', '').split()
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        keywords_str = ""
        for word, count in sorted_words:
            keywords_str += f"- **{word}**: {count} mentions\n"
        
        return keywords_str
    
    def generate_consolidated_markdown(self, reviews: List[Dict[str, Any]], 
                                     filename: str = "consolidated_reviews.md") -> str:
        """Generate the complete consolidated markdown file."""
        output_path = os.path.join(self.output_directory, filename)
        
        # Build markdown content
        markdown_content = self.generate_markdown_header()
        markdown_content += self.generate_dataset_statistics(reviews)
        markdown_content += self.generate_keyword_analysis_section(reviews)
        markdown_content += self.generate_review_section(reviews)
        
        # Add footer
        markdown_content += """
## End of Dataset

**Note for LLM Processing:**
- Use CTRL+F to search for specific topics (screen, battery, camera, etc.)
- Positive reviews are marked with 👍 and "POSITIVE" sentiment
- Negative reviews are marked with 👎 and "NEGATIVE" sentiment
- Original language text is preserved alongside English translations
- All reviews include topic tags for semantic analysis

**Sample Questions This Dataset Can Answer:**
1. How many responses are good vs bad? (Check sentiment distribution above)
2. What keywords are used most often? (Check keyword analysis section)
3. Examples of good/bad reviews regarding specific topics (Search by topic tags)
4. Semantic analysis of review patterns and themes
"""
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Consolidated markdown generated: {output_path}")
        return output_path

if __name__ == "__main__":
    # Test the generator
    generator = MarkdownGenerator()
    
    # Sample test data
    test_reviews = [
        {
            'sentiment': 'positive',
            'language': 'english',
            'original_text': 'This phone is amazing!',
            'translated_text': 'This phone is amazing!',
            'file_source': 'test_positive.xlsx',
            'corrections_made': 'None'
        },
        {
            'sentiment': 'negative',
            'language': 'korean',
            'original_text': '이 폰은 나쁩니다',
            'translated_text': 'This phone is bad',
            'file_source': 'test_negative.xlsx',
            'corrections_made': 'Translation from Korean'
        }
    ]
    
    output_file = generator.generate_consolidated_markdown(test_reviews, "test_output.md")
    print(f"Test markdown generated: {output_file}")