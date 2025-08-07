# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LLM-based parser project currently in early development stage.
Develop a codebase that uses ollama for LLM.
Make the LLM model selectable by importing ollama settings from the computer.
The objective of this LLM is to 
1. Read .xlsx file containing either positive or negative aspect of the cellphone.
- Excel filenames are configurable via environment variables
2. Setup a RAG of the .xlsx file that is imported.
3. Using the LLM from ollama, answer the questions that user asks.

## Add new features
The LLM must be able to answer user's question such as:
1. How many positive reviews are there?
2. What are top 100 positive keywords regarding the given phone.
3. How many negative reviews are there regarding battery life?
Think hard before you answer as traditional RAG might not be able to solve these problems.
Plan how to enable these features.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables as needed (optional)

# Initialize RAG system with review data
python cli.py setup
```

### Running the Application

#### Streamlit Web Interface
```bash
# Start web interface
streamlit run src/main.py

# Access at http://localhost:8501
```

#### Command Line Interface
```bash
# Setup RAG system
python cli.py setup

# Interactive query mode
python cli.py query

# Check system status
python cli.py status

# Use specific model
python cli.py query --model llama3
```

### Ollama Model Management
```bash
# List available models
ollama list

# Pull a new model
ollama pull llama3
ollama pull mistral
ollama pull codellama

# Default model can be set via environment variables
# DEFAULT_OLLAMA_MODEL=llama3
```



## Project Structure

```
LLM_based_parser/
├── src/
│   ├── excel_reader.py      # Excel file processing for fold_positive/negative.xlsx
│   ├── rag_system.py        # RAG implementation with ChromaDB and embeddings
│   ├── ollama_client.py     # Ollama LLM integration with model selection
│   └── main.py              # Streamlit web interface
├── config/
│   └── config.py            # Configuration management
├── data/
│   ├── [positive file].xlsx # Positive cellphone reviews (configurable filename)
│   ├── [negative file].xlsx # Negative cellphone reviews (configurable filename)
│   └── chromadb/           # Vector database storage (auto-created)
├── requirements.txt         # Python dependencies
├── cli.py                  # Command-line interface
└── CLAUDE.md               # This file
```

## Architecture Notes

The system implements a RAG (Retrieval-Augmented Generation) architecture:

1. **Data Processing Pipeline**: 
   - `ExcelReader` processes fold_positive.xlsx and fold_negative.xlsx files
   - Combines positive/negative reviews with sentiment tagging
   - Converts to text format suitable for embeddings

2. **RAG System**:
   - Uses ChromaDB for vector storage with persistence
   - SentenceTransformers (all-MiniLM-L6-v2) for embeddings
   - Implements similarity search for context retrieval

3. **LLM Integration**:
   - `OllamaClient` manages local Ollama models
   - Automatic model detection and pulling
   - Context-aware prompt engineering for cellphone review analysis

4. **User Interfaces**:
   - Streamlit web interface for interactive querying
   - CLI for setup, query, and system management

### Key Components:
- **Excel Processing**: Handles Excel files with flexible column detection
- **Vector Database**: Persistent ChromaDB storage in data/chromadb/  
- **Model Management**: Dynamic Ollama model selection and availability checking
- **Configuration**: Environment-based settings via system environment variables

## Development Guidelines

### Data Requirements
- Place Excel review files in the `data/` directory (filenames configurable via environment variables)
- Default filenames: `fold_positive.xlsx` and `fold_negative.xlsx`
- Custom filenames: Set `POSITIVE_FILENAME` and `NEGATIVE_FILENAME` environment variables
- Excel files should contain review text in columns like 'review', 'text', 'comment', or 'content'
- System automatically detects appropriate text columns

### Model Management
- Ensure Ollama is installed and running: `ollama serve`
- Install Korean-capable models: `ollama pull qwen2` (recommended) or `ollama pull llama3`
- Configure default model via `DEFAULT_OLLAMA_MODEL` environment variable or use CLI `--model` parameter

### Korean Language Support
- System uses `nomic-embed-text` for Korean-English embedding (optimized for multilingual tasks)
- Automatic language detection based on Korean character presence
- Bilingual system prompts and response templates
- Korean models: qwen2 (best), llama3, gemma2

### Development Setup
- Use virtual environment: `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- Install dependencies: `pip install -r requirements.txt`
- Initialize system: `python cli.py setup`

### Configuration
- Set environment variables as needed for your system
- Key settings: embedding model, similarity threshold, RAG context size
- ChromaDB data persists in `data/chromadb/` directory

### Error Handling
- All modules include comprehensive logging
- RAG system handles missing files gracefully
- Ollama client auto-detects and pulls missing models