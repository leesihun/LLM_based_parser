"""
Enhanced Ollama Client for Language Processing
Extends the original client with language detection, translation, and spell correction.
"""
import ollama
import json
import logging
from typing import Optional, Dict, Any, List
from config.enhanced_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedOllamaClient:
    def __init__(self, default_model: Optional[str] = None):
        # Create Ollama client with configured host
        ollama_host = config.get_ollama_url()
        self.client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
        self.default_model = default_model or config.llm_model
        self.embedding_model = config.embedding_model
        
        logger.info(f"Enhanced Ollama Client initialized:")
        logger.info(f"  LLM Model: {self.default_model}")
        logger.info(f"  Embedding Model: {self.embedding_model}")
        logger.info(f"  Host: {ollama_host}")
    
    def generate_response(self, prompt: str, model: Optional[str] = None, 
                         system_prompt: Optional[str] = None,
                         temperature: float = None,
                         max_tokens: int = None) -> Optional[str]:
        """Standard method for LLM text generation."""
        try:
            selected_model = model or self.default_model
            
            # Prepare messages in chat format
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Get LLM parameters
            llm_params = config.get_llm_params(temperature, max_tokens)
            
            # Call Ollama with chat interface
            response = self.client.chat(
                model=selected_model,
                messages=messages,
                options=llm_params
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            return None
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of the given text."""
        system_prompt = """You are a language detection expert. Analyze the given text and determine its language.
        
        Respond with ONLY a JSON object in this exact format:
        {
            "language": "english|korean|chinese|japanese|spanish|french|german|other",
            "confidence": 0.0_to_1.0,
            "is_english": true_or_false
        }"""
        
        prompt = f"Detect the language of this text: \"{text[:200]}\""
        
        try:
            response = self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            if response:
                detection = json.loads(response)
                return {
                    'language': detection.get('language', 'unknown'),
                    'confidence': detection.get('confidence', 0.5),
                    'is_english': detection.get('is_english', False),
                    'needs_translation': not detection.get('is_english', False)
                }
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
        
        # Fallback detection
        return {
            'language': 'unknown',
            'confidence': 0.1,
            'is_english': False,
            'needs_translation': True
        }
    
    def translate_to_english(self, text: str, source_language: str = None) -> Dict[str, Any]:
        """Translate text to English and correct spelling."""
        if source_language:
            system_prompt = f"""You are a professional translator. Translate the following {source_language} text to English.
            
            Requirements:
            1. Provide accurate, natural English translation
            2. Correct any spelling errors in the translation
            3. Maintain the original meaning and tone
            4. If the text is already in English, just correct spelling and grammar
            
            Respond with ONLY a JSON object:
            {{
                "translated_text": "corrected English translation",
                "original_was_english": true_or_false,
                "corrections_made": "brief description of corrections"
            }}"""
        else:
            system_prompt = """You are a professional translator and editor. For the given text:
            1. If it's in English: correct spelling and grammar errors
            2. If it's in another language: translate to English and correct any errors
            
            Respond with ONLY a JSON object:
            {
                "translated_text": "corrected English text",
                "original_was_english": true_or_false,
                "corrections_made": "brief description of changes made"
            }"""
        
        prompt = f"Process this text: \"{text}\""
        
        try:
            translation_params = config.get_translation_params()
            response = self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=translation_params['temperature'],
                max_tokens=translation_params['num_predict']
            )
            
            if response:
                result = json.loads(response)
                return {
                    'translated_text': result.get('translated_text', text),
                    'original_was_english': result.get('original_was_english', False),
                    'corrections_made': result.get('corrections_made', 'None'),
                    'translation_successful': True
                }
        except Exception as e:
            logger.error(f"Error in translation: {e}")
        
        # Fallback - return original text
        return {
            'translated_text': text,
            'original_was_english': False,
            'corrections_made': 'Translation failed',
            'translation_successful': False
        }
    
    def process_review_text(self, review_text: str) -> Dict[str, Any]:
        """Complete processing: detect language, translate, and correct."""
        # Step 1: Detect language
        language_info = self.detect_language(review_text)
        
        # Step 2: Translate if needed
        if language_info['needs_translation']:
            translation_info = self.translate_to_english(
                review_text, 
                language_info['language']
            )
        else:
            # Still run through translation to correct spelling
            translation_info = self.translate_to_english(review_text)
        
        # Combine results
        return {
            'original_text': review_text,
            'language': language_info['language'],
            'language_confidence': language_info['confidence'],
            'translated_text': translation_info['translated_text'],
            'corrections_made': translation_info['corrections_made'],
            'processing_successful': translation_info['translation_successful']
        }
    
    def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate embeddings using the configured embedding model."""
        try:
            response = self.client.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def batch_process_reviews(self, reviews: List[str], batch_size: int = None) -> List[Dict[str, Any]]:
        """Process multiple reviews in batches."""
        batch_size = batch_size or config.batch_size
        results = []
        
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(reviews) + batch_size - 1)//batch_size}")
            
            for review in batch:
                result = self.process_review_text(review)
                results.append(result)
        
        return results

if __name__ == "__main__":
    # Test the enhanced client
    client = EnhancedOllamaClient()
    
    # Test language detection
    test_korean = "이 휴대폰은 정말 좋습니다"
    test_english = "This phone is really good"
    test_english_errors = "This fone is realy gud"
    
    print("Testing language detection and translation:")
    
    for test_text in [test_korean, test_english, test_english_errors]:
        print(f"\nOriginal: {test_text}")
        result = client.process_review_text(test_text)
        print(f"Language: {result['language']} (confidence: {result['language_confidence']})")
        print(f"Translated: {result['translated_text']}")
        print(f"Corrections: {result['corrections_made']}")