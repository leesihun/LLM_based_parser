# LLM Implementation Reference

This document records the exact LLM implementation patterns used in this codebase for consistent future development.

## Core LLM Architecture

### OllamaClient Class (`src/ollama_client.py`)

**Purpose**: Primary interface for all LLM interactions using Ollama service.

#### Initialization Pattern
```python
from config.config import config

class OllamaClient:
    def __init__(self, default_model: Optional[str] = None):
        # Create Ollama client with configured host
        ollama_host = f"http://{config.ollama_host}"
        self.client = ollama.Client(host=ollama_host, timeout=config.ollama_timeout)
        self.default_model = default_model or config.default_ollama_model
        
        # Always use configured model regardless of detection
        logger.info(f"Using configured model: {self.default_model}")
```

#### Core LLM Call Method
```python
def generate_response(self, prompt: str, model: Optional[str] = None, 
                     system_prompt: Optional[str] = None,
                     temperature: float = 0.7,
                     max_tokens: int = 1000) -> Optional[str]:
    """Standard method for LLM text generation."""
    
    selected_model = model or self.default_model
    
    # Prepare messages in chat format
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Call Ollama with chat interface
    response = self.client.chat(
        model=selected_model,
        messages=messages,
        options={
            "temperature": temperature,
            "num_predict": max_tokens
        }
    )
    
    return response['message']['content']
```

### Configuration System

#### LLM Settings in `config/config.py`
```python
class Config:
    def __init__(self):
        # Ollama connection settings
        self.default_ollama_model = "gemma3:12b"        # Model name
        self.ollama_host = "localhost:11434"            # Ollama service host
        self.ollama_timeout = 60                        # Connection timeout
        
        # LLM generation parameters
        self.default_temperature = 0.4                  # Response creativity
        self.max_tokens = 10000                         # Maximum response length
        self.rag_context_size = 100                     # RAG context documents
```

## LLM Usage Patterns

### Pattern 1: Query Classification (LLMQueryClassifier)
```python
class LLMQueryClassifier:
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama_client = ollama_client or OllamaClient()
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        # Create structured prompt for classification
        prompt = self._create_classification_prompt(query)
        
        # Get LLM response
        response = self.ollama_client.generate_response(prompt)
        
        # Parse JSON response
        classification = self._parse_llm_response(response)
        
        return self._validate_classification(classification)
```

#### Structured JSON Prompt Pattern
```python
def _create_classification_prompt(self, query: str) -> str:
    return f"""You are a query classifier for a cellphone review analysis system.

Classify the following user query into one of these types:
1. COUNT: Questions asking "how many" reviews
2. KEYWORD_EXTRACTION: Questions asking for top/frequent words
3. STATISTICS: Questions asking for overview/summary
4. COMPARISON: Questions comparing positive vs negative
5. SEMANTIC_SEARCH: Other questions seeking information

Extract parameters:
- sentiment: "positive", "negative", or null
- topic: one of {self.available_topics} or null  
- number: any number mentioned or null
- method: "tfidf" if mentioned, otherwise "frequency"

User Query: "{query}"

Respond with ONLY a JSON object:
{{
    "type": "COUNT|KEYWORD_EXTRACTION|STATISTICS|COMPARISON|SEMANTIC_SEARCH",
    "sentiment": "positive|negative|null", 
    "topic": "battery|screen|camera|null",
    "number": number_or_null,
    "method": "frequency|tfidf",
    "confidence": 0.0_to_1.0,
    "reasoning": "brief explanation"
}}"""
```

### Pattern 2: RAG-Based Response Generation (HybridQueryEngine)
```python
def _handle_semantic_search(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    # Get relevant context from RAG system
    rag_results = self.rag_system.query(query, n_results=5)
    
    # Format context for LLM
    context_parts = []
    for i, doc in enumerate(rag_results['documents']):
        context_parts.append(f"Review {i+1}: {doc}")
    context = "\\n\\n".join(context_parts)
    
    # Create enhanced prompt with context
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

Please provide a comprehensive answer based on the review context above."""
    
    # Get LLM response
    llm_response = self.ollama_client.generate_response(prompt)
    
    return {
        'rag_results': rag_results,
        'llm_response': llm_response,
        'context_used': True,
        'context_length': len(context)
    }
```

### Pattern 3: Direct Model Usage
```python
# Simple usage with default settings
client = OllamaClient()
response = client.generate_response("Your prompt here")

# Usage with custom parameters
response = client.generate_response(
    prompt="Your prompt",
    system_prompt="You are a helpful assistant",
    temperature=0.7,
    max_tokens=500
)

# Usage with specific model
response = client.generate_response(
    prompt="Your prompt",
    model="llama3"
)
```

## Error Handling Patterns

### Graceful Degradation
```python
try:
    response = self.ollama_client.generate_response(prompt)
    return self._process_response(response)
except Exception as e:
    logger.error(f"Error in LLM processing: {e}")
    return {
        'type': QueryType.SEMANTIC_SEARCH,  # Fallback type
        'confidence': 0.1,
        'error': str(e)
    }
```

### Model Detection (Non-blocking)
```python
# Model availability check that doesn't block usage
def is_model_available(self, model_name: str) -> bool:
    available = self.get_available_models()
    is_available = model_name in available
    
    if not is_available:
        logger.warning(f"Model '{model_name}' not found in available models: {available}")
        logger.info(f"Will attempt to use '{model_name}' anyway - Ollama may auto-pull it")
        
    return True  # Always return True - let Ollama handle model availability
```

## Key Implementation Principles

1. **Configuration-Driven**: All LLM settings centralized in `config/config.py`
2. **Graceful Fallback**: System continues working even if LLM calls fail
3. **Model Flexibility**: Uses exact configured model name without validation
4. **Structured Prompts**: JSON-based prompts for reliable parsing
5. **Context-Aware**: RAG context integration for enhanced responses
6. **Error Resilience**: Comprehensive error handling with meaningful fallbacks

## Import Pattern
```python
# Standard import pattern for LLM functionality
from src.ollama_client import OllamaClient
from config.config import config

# Initialize with configuration
client = OllamaClient()

# Or initialize with specific model
client = OllamaClient(default_model="llama3")
```

## Dependencies Required
```txt
ollama>=0.1.9
```

This implementation provides a robust, configuration-driven LLM interface that gracefully handles errors and integrates seamlessly with RAG systems and structured query processing.