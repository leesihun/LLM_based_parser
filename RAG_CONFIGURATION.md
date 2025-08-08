# RAG System Configuration Guide

## Overview

The RAG (Retrieval-Augmented Generation) system is now fully configurable through the `config/config.json` file. It uses **nomic-embed-text:latest** as the default embedding model via Ollama.

## Configuration Structure

```json
{
  "rag": {
    "embedding": {
      "provider": "ollama",
      "model": "nomic-embed-text:latest",
      "ollama_host": "http://localhost:11434",
      "dimensions": 768,
      "batch_size": 50
    },
    "collection": {
      "name": "documents",
      "persist_directory": "./chroma_db"
    },
    "chunking": {
      "strategy": "semantic",
      "chunk_size": 1000,
      "overlap": 200,
      "min_chunk_size": 100,
      "max_chunk_size": 2000
    },
    "search": {
      "default_results": 5,
      "max_results": 20,
      "max_context_length": 3000,
      "similarity_threshold": 0.7
    },
    "performance": {
      "enable_caching": true,
      "cache_size": 1000,
      "parallel_processing": true
    }
  }
}
```

## Configuration Sections

### Embedding Settings
- **provider**: Embedding service provider ("ollama")
- **model**: Ollama embedding model name ("nomic-embed-text:latest")
- **ollama_host**: Ollama server URL
- **dimensions**: Embedding vector dimensions (768 for nomic-embed-text)
- **batch_size**: Number of texts to process in each batch

### Collection Settings
- **name**: ChromaDB collection name
- **persist_directory**: Directory for vector database storage

### Chunking Settings
- **strategy**: Text chunking strategy (semantic, fixed, sentence)
- **chunk_size**: Target size for each text chunk
- **overlap**: Overlap between consecutive chunks
- **min_chunk_size**: Minimum allowed chunk size
- **max_chunk_size**: Maximum allowed chunk size

### Search Settings
- **default_results**: Default number of search results
- **max_results**: Maximum allowed search results
- **max_context_length**: Maximum length of context for LLM
- **similarity_threshold**: Minimum similarity score for results

### Performance Settings
- **enable_caching**: Enable embedding caching
- **cache_size**: Maximum cache entries
- **parallel_processing**: Enable parallel document processing

## Supported Embedding Models

The system supports any Ollama embedding model. Popular options:

- **nomic-embed-text:latest** (default) - General purpose, high quality
- **all-minilm-l6-v2** - Fast and efficient
- **mxbai-embed-large** - High quality embeddings
- **bge-large-en-v1.5** - Strong performance

To change the model:
1. Update `config.json`: `"model": "your-model-name:latest"`
2. Install the model: `ollama pull your-model-name:latest`
3. Restart the system

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Embedding Model
```bash
ollama pull nomic-embed-text:latest
```

### 3. Verify Configuration
```bash
python test_rag_config.py
```

### 4. Initialize System
```bash
python setup_system.py
```

## Troubleshooting

### Embedding Model Not Available
**Error**: "Embedding model not available"
**Solution**: 
1. Ensure Ollama is running: `ollama serve`
2. Install the model: `ollama pull nomic-embed-text:latest`
3. Check Ollama host in config matches your setup

### ChromaDB Connection Issues
**Error**: "Collection creation failed"
**Solution**:
1. Check persist_directory permissions
2. Ensure ChromaDB version compatibility
3. Clear existing database: `rm -rf chroma_db/`

### Poor Search Results
**Problem**: Irrelevant search results
**Solution**:
1. Adjust `chunk_size` and `overlap` in config
2. Try different embedding model
3. Increase `similarity_threshold`
4. Reduce `max_context_length`

## Performance Tuning

### For Better Accuracy:
- Use larger embedding models (mxbai-embed-large)
- Reduce chunk size for more precise retrieval
- Increase overlap between chunks
- Lower similarity threshold

### for Better Speed:
- Use smaller embedding models (all-minilm-l6-v2)
- Increase chunk size
- Reduce overlap
- Enable caching and parallel processing

## API Integration

The RAG system is automatically used by these API endpoints:
- `POST /api/rag/chat` - Chat with RAG context
- `POST /api/rag/search` - Direct RAG search
- `GET /api/rag/stats` - RAG system statistics

## Custom Configuration Example

```json
{
  "rag": {
    "embedding": {
      "provider": "ollama",
      "model": "mxbai-embed-large:latest",
      "ollama_host": "http://localhost:11434",
      "batch_size": 25
    },
    "chunking": {
      "chunk_size": 800,
      "overlap": 150,
      "min_chunk_size": 50
    },
    "search": {
      "default_results": 8,
      "max_context_length": 4000
    }
  }
}
```

This configuration uses a larger embedding model with smaller chunks and more context for higher accuracy applications.

## Best Practices

1. **Match Model to Use Case**: Use nomic-embed-text for general documents, specialized models for domain-specific content
2. **Tune Chunk Size**: Smaller chunks (500-800) for precise answers, larger chunks (1000-2000) for context
3. **Monitor Performance**: Use `/api/rag/stats` to monitor document count and search performance
4. **Regular Maintenance**: Clear and rebuild collection when source documents change significantly
5. **Test Configuration**: Use `test_rag_config.py` after configuration changes