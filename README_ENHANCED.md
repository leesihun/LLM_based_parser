# Enhanced LLM-based Review Parser

A comprehensive system for processing cellphone review data from Excel files using local LLM models (Ollama).

## System Overview

This enhanced parser processes Korean and English Excel files containing cellphone reviews and creates a consolidated markdown file optimized for LLM analysis. It supports:

- **Multi-file Excel Processing**: Automatically processes all `.xlsx` files in the data directory
- **Language Detection & Translation**: Detects review language and translates to English while preserving originals
- **Spell Correction**: Automatically corrects spelling errors using LLM
- **Intelligent Query System**: Answers specific questions about the review data
- **Semantic Analysis**: Provides keyword frequency and semantic insights

## Quick Start

### Prerequisites

1. **Ollama Service**: Ensure Ollama is running locally on `localhost:11434`
2. **Required Models**:
   ```bash
   ollama pull gemma3:12b           # Main LLM model
   ollama pull nomic-embed-text     # Embedding model
   ```
3. **Python Dependencies**: `pandas`, `openpyxl`, `ollama`

### Basic Usage

1. **Place Excel Files**: Put your `.xlsx` files in the `data/` directory
2. **Run Complete Pipeline**:
   ```bash
   python enhanced_main.py --mode pipeline
   ```
3. **Ask Questions**:
   ```bash
   python enhanced_main.py --mode query --question "How many good vs bad reviews?"
   ```

## Configuration

Edit `config/enhanced_config.py` or set environment variables:

```bash
export LLM_MODEL="gemma3:12b"
export EMBEDDING_MODEL="nomic-embed-text:latest"
export OLLAMA_HOST="localhost:11434"
export DEFAULT_TEMPERATURE="0.4"
```

## Pipeline Steps

The system runs through these stages:

1. **Excel Reading**: Extracts reviews from all `.xlsx` files
2. **Language Processing**: Detects language and translates to English
3. **Markdown Generation**: Creates consolidated review file with metadata
4. **Query System**: Enables LLM-powered analysis of the data

## Supported Question Types

The system can answer:

1. **Count Questions**: "How many responses are good and how many are bad?"
2. **Keyword Analysis**: "What keyword is used most often? Semantically analyze it."
3. **Example Requests**: "Give me an example of good review regarding screen size."
4. **General Analysis**: Any analytical questions about the review patterns

## Output Files

- `output/consolidated_reviews_[timestamp].md`: Main dataset file optimized for LLM analysis
- `output/processing_log.json`: Processing metadata and statistics

## Advanced Usage

### Custom Configuration

```python
from config.enhanced_config import config
config.llm_model = "your-preferred-model"
config.translation_temperature = 0.2
```

### Direct API Usage

```python
from src.enhanced_query_engine import EnhancedQueryEngine

engine = EnhancedQueryEngine("output/consolidated_reviews.md")
result = engine.query("Your question here")
print(result['answer'])
```

### Batch Processing

```python
from enhanced_main import EnhancedPipeline

pipeline = EnhancedPipeline()
result = pipeline.run_complete_pipeline()

if result['success']:
    # Run multiple queries
    questions = ["Question 1", "Question 2"]
    for q in questions:
        answer = pipeline.query_engine.query(q)
        print(f"Q: {q}")
        print(f"A: {answer['answer']}")
```

## Architecture

```
data/*.xlsx → EnhancedExcelReader → EnhancedOllamaClient → MarkdownGenerator → EnhancedQueryEngine
     ↓              ↓                      ↓                    ↓                    ↓
  Raw Reviews → Language Detection → Translation/Correction → Consolidated MD → Query Answers
```

## Key Features

- **Preserves Original Language**: Both original and translated texts are maintained
- **Smart Topic Detection**: Automatically identifies review topics (screen, battery, camera, etc.)
- **Flexible Configuration**: All settings configurable via environment variables
- **Error Resilience**: Graceful handling of translation and processing errors
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## File Structure

```
├── enhanced_main.py              # Main pipeline orchestrator
├── config/enhanced_config.py     # Configuration management
├── src/
│   ├── enhanced_excel_reader.py  # Multi-file Excel processing
│   ├── enhanced_ollama_client.py # LLM client with translation
│   ├── markdown_generator.py     # Consolidated markdown creation
│   └── enhanced_query_engine.py  # Question answering system
├── data/                         # Input Excel files
└── output/                       # Generated markdown and logs
```

## Troubleshooting

1. **Ollama Connection Issues**: Verify Ollama is running and accessible
2. **Model Not Found**: Pull required models with `ollama pull [model-name]`
3. **Translation Errors**: Check model temperature settings in config
4. **Memory Issues**: Adjust batch size in configuration for large datasets

## Performance Notes

- Processing time depends on review count and model response times
- Translation is the most time-intensive step
- Batch processing optimizes performance for large datasets
- Generated markdown files are optimized for LLM token efficiency