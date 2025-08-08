# HE Team LLM Assistant - Enhanced Project Structure

## 📁 Directory Organization

```
LLM_based_parser/
├── 📄 server.py                 # Main Flask server
├── 📄 index.html               # Enhanced web interface  
├── 📄 login.html               # Login page
├── 📄 setup_system.py          # System initialization
├── 📄 requirements.txt         # Python dependencies
├── 📄 CLAUDE.md                # Project instructions
├── 📄 PROJECT_STRUCTURE.md     # This file
│
├── 📁 core/                    # Core system components
│   ├── llm_client.py          # LLM communication
│   ├── conversation_memory.py  # Chat memory management
│   └── user_management.py     # Authentication & users
│
├── 📁 src/                     # Enhanced features
│   ├── excel_to_md_converter.py  # Excel → Markdown
│   ├── rag_system.py          # RAG with ChromaDB
│   └── file_handler.py        # File upload & processing
│
├── 📁 config/                  # Configuration
│   └── config.json            # System configuration
│
├── 📁 scripts/                 # Utility scripts
│   ├── start.py               # System startup
│   └── manage_users.py        # User management CLI
│
├── 📁 data/                    # Source Excel files
│   ├── 폴드긍정.xlsx
│   └── 폴드부정.xlsx
│
├── 📁 uploads/                 # User uploaded files (created at runtime)
├── 📁 chroma_db/              # RAG vector database (created at runtime)
└── 📁 auth/                   # Future auth extensions
```

## 🚀 Quick Start

1. **Setup System**: `python setup_system.py`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Start Server**: `python server.py`
4. **Access Interface**: http://localhost:3000

## ✨ Features

### Enhanced Web Interface
- **4 Chat Modes**: Normal, RAG Search, Document Q&A, File Analysis
- **File Upload**: Drag & drop with multi-format support
- **Real-time Status**: System health and RAG statistics
- **Modern UI**: Responsive design with mode indicators

### Backend Capabilities  
- **RAG System**: ChromaDB vector search with intelligent chunking
- **Multi-format Support**: PDF, DOCX, XLSX, TXT, MD, code files
- **User Authentication**: Secure session management
- **File Processing**: Automatic content extraction and LLM analysis

### Data Processing Pipeline
1. **Excel → Markdown**: Combines all .xlsx files into searchable format
2. **Vector Indexing**: RAG system creates searchable knowledge base  
3. **File Analysis**: Uploaded files processed for LLM consumption
4. **Context-Aware Chat**: Enhanced responses using relevant data

## 🔧 Configuration

Main configuration in `config/config.json`:
- Ollama server settings
- Model selection
- Server host/port
- System parameters

## 📊 File Support

| Category | Extensions | Processing |
|----------|------------|------------|
| Text | .txt, .md, .py, .js, .json, .csv | Direct reading |
| Documents | .pdf, .docx | Content extraction |
| Spreadsheets | .xlsx, .xls | Sheet processing |
| Web | .html, .xml, .yml | Structure parsing |

## 🏗️ Architecture

- **Modular Design**: Each feature in isolated modules
- **Clean Separation**: Core vs enhanced functionality
- **Organized Structure**: Logical directory organization
- **Minimal Dependencies**: Only essential packages
- **Scalable**: Easy to extend with new features

This structure follows the CLAUDE.md requirements with proper organization and minimal changes to existing core functionality.