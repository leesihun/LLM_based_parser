# LLM-based Parser for Cellphone Reviews

A comprehensive system that uses Ollama LLMs with RAG (Retrieval-Augmented Generation) to analyze cellphone reviews from Excel files.

## 🚀 Features

- **Excel Data Processing**: Reads positive and negative cellphone reviews from configurable Excel files
- **RAG System**: Vector database with ChromaDB and sentence transformers for context retrieval
- **Ollama Integration**: Dynamic model selection and automatic model management
- **Multilingual Support**: Korean and English language support with automatic detection
- **Dual Interface**: Streamlit web app and command-line interface
- **Smart Configuration**: Environment-based settings with flexible parameters

## 📋 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Excel files containing review data in the `data/` directory (filenames configurable via .env)

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

# Setup configuration (optional)
cp .env.example .env

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

Key settings in `.env`:

```bash
# RAG Settings
RAG_COLLECTION_NAME=cellphone_reviews
EMBEDDING_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.8

# Ollama Settings
DEFAULT_OLLAMA_MODEL=llama3
OLLAMA_HOST=localhost:11434

# Generation Settings
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=1000
```

## 📊 Data Requirements

Place your Excel files in the `data/` directory. Default filenames are:
- `fold_positive.xlsx`: Contains positive cellphone reviews  
- `fold_negative.xlsx`: Contains negative cellphone reviews

**Custom Filenames**: Configure different filenames in your `.env` file:
```bash
POSITIVE_FILENAME=your_positive_file.xlsx
NEGATIVE_FILENAME=your_negative_file.xlsx
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
The system automatically detects Korean text and switches language context. You can also manually configure:

```bash
# In .env file
POSITIVE_FILENAME=my_positive_reviews.xlsx
NEGATIVE_FILENAME=my_negative_reviews.xlsx
DEFAULT_OLLAMA_MODEL=qwen2
DEFAULT_LANGUAGE=auto  # Options: auto, en, ko
EMBEDDING_MODEL=nomic-embed-text
```

## 🔧 Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines and architecture notes.

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.