# LLM-based Parser for Cellphone Reviews

A comprehensive system that uses Ollama LLMs with RAG (Retrieval-Augmented Generation) to analyze cellphone reviews from Excel files.

## 🚀 Features

- **Excel Data Processing**: Reads positive and negative cellphone reviews from `fold_positive.xlsx` and `fold_negative.xlsx`
- **RAG System**: Vector database with ChromaDB and sentence transformers for context retrieval
- **Ollama Integration**: Dynamic model selection and automatic model management
- **Dual Interface**: Streamlit web app and command-line interface
- **Smart Configuration**: Environment-based settings with flexible parameters

## 📋 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Excel files: `fold_positive.xlsx` and `fold_negative.xlsx` in the `data/` directory

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
│   ├── fold_positive.xlsx   # Positive reviews (user provided)
│   └── fold_negative.xlsx   # Negative reviews (user provided)
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

Place your Excel files in the `data/` directory:
- `fold_positive.xlsx`: Contains positive cellphone reviews
- `fold_negative.xlsx`: Contains negative cellphone reviews

The system automatically detects review text columns (`review`, `text`, `comment`, `content`, etc.).

## 🤖 Ollama Models

Install and manage models:

```bash
# List available models
ollama list

# Install recommended models
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

## 🔧 Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines and architecture notes.

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.