# LLM-based Parser for Cellphone Reviews

A comprehensive system that uses Ollama LLMs with RAG (Retrieval-Augmented Generation) to analyze cellphone reviews from Excel files.

## 🚀 Features

- **Excel Data Processing**: Reads positive and negative cellphone reviews from configurable Excel files
- **RAG System**: Vector database with ChromaDB and sentence transformers for context retrieval
- **Ollama Integration**: Dynamic model selection and automatic model management
- **Multilingual Support**: Korean and English language support with automatic detection
- **Dual Interface**: Streamlit web app and command-line interface
- **Simple Configuration**: Direct Python configuration in config/config.py

## 📋 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Excel files containing review data in the `data/` directory (filenames configurable in `config/config.py`)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/LLM_based_parser.git
cd LLM_based_parser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configuration is set in config/config.py

# Initialize the RAG system
python cli.py setup
```

### Usage

#### Web Interface
```bash
streamlit run src/main.py
# Access at http://localhost:8501
```

#### Command Line
```bash
# Interactive query mode
python cli.py query

# Use specific model
python cli.py query --model llama3

# Check system status
python cli.py status
```

## 🏗️ Architecture

The system implements a RAG architecture with the following components:

1. **Data Processing**: Excel file reader with flexible column detection
2. **Vector Database**: ChromaDB for persistent embeddings storage
3. **LLM Integration**: Ollama client with automatic model management
4. **User Interfaces**: Streamlit web app and CLI for different use cases

## 📁 Project Structure

```
LLM_based_parser/
├── src/
│   ├── excel_reader.py      # Excel file processing
│   ├── rag_system.py        # RAG implementation
│   ├── ollama_client.py     # Ollama integration
│   └── main.py              # Streamlit interface
├── config/
│   └── config.py            # Configuration management
├── data/
│   ├── [positive file].xlsx  # Positive reviews (configurable filename)
│   └── [negative file].xlsx  # Negative reviews (configurable filename)
├── requirements.txt         # Dependencies
├── cli.py                  # Command-line interface
└── README.md               # This file
```

## ⚙️ Configuration

All settings are configured in `config/config.py`. Key settings include:

```python
# Excel file names
self.positive_filename = "폴드긍정.xlsx"
self.negative_filename = "폴드부정.xlsx"

# RAG Settings
self.rag_collection_name = "cellphone_reviews"
self.embedding_model = "nomic-embed-text:latest"
self.similarity_threshold = 0.8

# Ollama Settings
self.default_ollama_model = "gemma3:12b"
self.ollama_host = "localhost:11434"

# Generation Settings
self.default_temperature = 0.7
self.max_tokens = 1000
```

Edit `config/config.py` to customize these values for your setup.

## 📊 Data Requirements

Place your Excel files in the `data/` directory. Default filenames are:
- `fold_positive.xlsx`: Contains positive cellphone reviews  
- `fold_negative.xlsx`: Contains negative cellphone reviews

**Custom Filenames**: Edit the filenames directly in `config/config.py`:
```python
self.positive_filename = "your_positive_file.xlsx"
self.negative_filename = "your_negative_file.xlsx"
```

The system automatically detects review text columns (`review`, `text`, `comment`, `content`, etc.).

## 🤖 Ollama Models

### Korean Language Support
For Korean language processing, install Korean-capable models:

```bash
# Recommended for Korean
ollama pull qwen2      # Best Korean support
ollama pull llama3     # Good multilingual support
ollama pull gemma2     # Google's multilingual model

# List available models
ollama list

# Other useful models
ollama pull mistral
ollama pull codellama
```

### Language Configuration
The system automatically detects Korean text and switches language context. Configure settings in `config/config.py`:

```python
# File names
self.positive_filename = "my_positive_reviews.xlsx"
self.negative_filename = "my_negative_reviews.xlsx"

# Model settings
self.default_ollama_model = "qwen2"
self.embedding_model = "nomic-embed-text:latest"
```

## 🔧 Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines and architecture notes.

## 🚨 Troubleshooting

### Common Issues

#### "Failed to connect to Ollama" Error
```
ERROR: rag_system: Error generating embedding for text: Failed to connect to Ollama
```

**Solutions:**
1. **Check Ollama is running:**
   ```bash
   ollama serve
   ```

2. **Verify connection:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Check host configuration in config/config.py:**
   ```python
   self.ollama_host = "localhost:11434"  # Default
   ```

4. **Test embedding model availability:**
   ```bash
   ollama list
   ollama pull nomic-embed-text:latest
   ```

#### Model Not Found Error
```
ERROR: Model 'nomic-embed-text:latest' not available
```

**Solution:**
```bash
ollama pull nomic-embed-text:latest
```

#### Excel File Not Found
**Check your configuration in config/config.py:**
```python
self.positive_filename = "your_positive_file.xlsx"
self.negative_filename = "your_negative_file.xlsx"
```

**Verify files exist in data/ directory**

#### Permission Errors on ChromaDB
**Solution:**
```bash
rm -rf data/chromadb/  # Remove existing database
python cli.py setup    # Reinitialize
```

### Debug Mode
Enable debug logging by setting:
```bash
export PYTHONPATH=$PYTHONPATH:.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python cli.py setup
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.