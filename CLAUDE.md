# CLAUDE.md - Development Guide

This file provides comprehensive guidance for Claude Code when working with the HE Team LLM Assistant codebase.

## 🎯 Project Overview

The HE Team LLM Assistant is a sophisticated multi-modal AI system designed to provide:

1. **Normal Chat**: Standard AI conversations with configurable system prompts
2. **RAG-Enhanced Chat**: Knowledge base integration using ChromaDB for semantic search
3. **Intelligent Web Search**: Selenium-based search with advanced keyword extraction
4. **File Processing**: Document upload, analysis, and conversation about file contents
5. **Multi-User System**: Secure authentication, session management, and data isolation

## 🏗️ Architecture Principles

### Code Organization
- **Modular Design**: Each feature is isolated in its own module
- **API-First**: Clean RESTful API with well-documented endpoints
- **Separation of Concerns**: Core logic, API layer, and web interface are separate
- **Configuration-Driven**: All settings managed through JSON configuration files

### File Structure Standards
```
/core/          # Core system functionality (LLM, memory, auth)
/src/           # Feature modules (RAG, search, file handling)
/api/           # RESTful API endpoints (auth, chat, search, system)
/config/        # Configuration files
/static/        # Web interface files
/data/          # Persistent data (knowledge base, uploads)
/auth/          # Authentication data
/conversations/ # User conversation history
```

## 🔧 Development Guidelines

### When Adding New Features

1. **Create Feature Module**: Place new functionality in `/src/` directory
2. **Add API Endpoints**: Create corresponding endpoints in `/api/` directory
3. **Update Configuration**: Add necessary config options to `config/config.json`
4. **Document Everything**: Include comprehensive docstrings and comments
5. **Test Thoroughly**: Test all functionality and edge cases

### Code Standards

**Function Documentation:**
```python
def function_name(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of what the function does
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
        
    Returns:
        Dictionary containing result data
        
    Raises:
        SpecificException: When specific condition occurs
    """
```

**API Endpoint Standards:**
```python
@app.route('/api/feature/action', methods=['POST'])
@require_auth
def feature_action() -> Tuple[Dict[str, Any], int]:
    """
    Brief description of endpoint functionality
    
    Headers:
        Authorization: Bearer <session_token>
        
    Request Body:
        param1 (str): Description
        param2 (int, optional): Description
        
    Returns:
        200: Success response description
        400: Error condition description
        401: Authentication required
        500: Server error
    """
```

### Error Handling
- Always use try-catch blocks for external API calls
- Log errors with appropriate detail level
- Return meaningful error messages to API consumers
- Include error context (user, operation, timestamp)

### Security Considerations
- All API endpoints require authentication unless explicitly public
- Validate all input parameters
- Use parameterized queries for database operations
- Never log sensitive information (passwords, tokens)
- Implement proper session management

## 🤖 LLM Integration

### System Prompt Architecture
The system uses a hierarchical prompt system:

1. **Universal Prompt**: Applied to all conversation modes
2. **Mode-Specific Prompt**: Additional instructions for specific modes
3. **Context Prompt**: Dynamic content based on RAG/search results

**Example Configuration:**
```json
{
  "system_prompt": {
    "enabled": true,
    "universal": "You are an AI assistant for the HE team...",
    "default": "Provide general assistance...",
    "rag_mode": "Use the knowledge base context...",
    "search_mode": "Use web search results...",
    "file_mode": "Analyze the provided file..."
  }
}
```

### Response Processing
- Extract performance metrics (processing time, tokens/second)
- Handle both dict and string response formats
- Add conversation context to memory after generation
- Track usage statistics for monitoring

## 🔍 Web Search Intelligence

### Keyword Extraction System
The search system uses multiple extraction methods:

1. **TF-IDF**: Statistical analysis of term frequency
2. **Rule-Based**: Pattern matching for technical terms
3. **LLM-Assisted**: Using the LLM to identify key concepts

### Adequacy Validation
Before performing web search, the system validates if extracted keywords are adequate:

```python
def _has_adequate_keywords(self, keywords: List[str], original_text: str) -> bool:
    # Minimum 2 keywords required
    # Must contain technical/specific terms
    # Generic words are filtered out
    # Total character length threshold
```

### Search Process Flow
```
User Query → Keyword Extraction → Adequacy Check → Web Search → Result Processing
```

If keywords are inadequate, the system returns an error rather than performing a poor-quality search.

## 🗄️ RAG System Integration

### ChromaDB Setup
- Knowledge base stored in `data/chroma_db/`
- Documents chunked for optimal retrieval
- Embeddings generated for semantic similarity
- Metadata preserved for source attribution

### Search and Retrieval
```python
# Search process
results = rag_system.search(query, max_results=5)
context = "\n\n".join([result['content'] for result in results])

# Enhanced prompt creation
enhanced_prompt = f"""
Context from knowledge base:
{context}

User Question: {query}

Please answer using the provided context.
"""
```

## 📁 File Handling System

### Upload Process
1. File uploaded to `/uploads/` directory
2. Content extracted based on file type
3. Temporary processing for analysis
4. Content made available to LLM for questioning

### Supported File Types
- **Text files**: .txt, .md, .py, .js, etc.
- **Documents**: .pdf, .docx (future enhancement)
- **Data files**: .json, .csv, .xlsx
- **Images**: Basic text extraction capability

## 🔐 Authentication & Security

### Session Management
```python
# Session creation
session_token = user_manager.create_session(user_id)

# Token validation
user_data = user_manager.validate_session(session_token)

# Session cleanup (24-hour expiration)
user_manager.cleanup_expired_sessions()
```

### Data Isolation
- Each user has isolated conversation storage
- File uploads are user-specific
- Admin functions require admin role verification
- API endpoints validate user ownership of resources

## 📊 Performance Monitoring

### Metrics Collection
The system tracks comprehensive performance data:

```python
metrics = {
    'processing_time': llm_processing_time,
    'tokens_per_second': calculated_tps,
    'search_processing_time': search_duration,
    'keyword_extraction_method': extraction_method,
    'response_length': len(response_content)
}
```

### Health Monitoring
- `/health` endpoint for system status
- Ollama connectivity testing
- Resource usage tracking
- Error rate monitoring

## 🧪 Testing Guidelines

### Unit Testing
```python
# Test keyword extraction adequacy
def test_keyword_adequacy():
    extractor = KeywordExtractor()
    
    # Test adequate keywords
    result = extractor.extract_keywords("machine learning algorithms optimization")
    assert result['adequate_keywords'] == True
    
    # Test inadequate keywords
    result = extractor.extract_keywords("help me please")
    assert result['adequate_keywords'] == False
```

### Integration Testing
```python
# Test web search functionality
def test_web_search():
    search_feature = WebSearchFeature(config, llm_client)
    
    result = search_feature.search_web("python programming tutorial", 3)
    assert result['success'] == True
    assert len(result['results']) <= 3
```

### API Testing
```python
# Test authentication flow
def test_auth_flow():
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'test_user',
        'password': 'test_pass'
    })
    assert response.status_code == 200
    token = response.json['session_token']
    
    # Authenticated request
    response = client.post('/api/chat', 
        headers={'Authorization': f'Bearer {token}'},
        json={'message': 'test message'})
    assert response.status_code == 200
```

## 🔄 Configuration Management

### Configuration Schema
```json
{
  "ollama": {
    "host": "string",
    "model": "string", 
    "timeout": "number",
    "num_ctx": "number",
    "temperature": "number"
  },
  "server": {
    "host": "string",
    "port": "number",
    "debug": "boolean"
  },
  "web_search": {
    "enabled": "boolean",
    "use_keyword_extraction": "boolean",
    "max_results": "number",
    "timeout": "number"
  },
  "system_prompt": {
    "enabled": "boolean",
    "universal": "string",
    "default": "string",
    "rag_mode": "string",
    "search_mode": "string"
  }
}
```

### Runtime Configuration Updates
- Use `/api/config` POST endpoint for runtime updates
- Configuration changes don't persist to file (restart reverts)
- Admin authentication required for config modifications

## 🚀 Deployment Guidelines

### Production Setup
1. **Change Default Credentials**: Update admin password immediately
2. **Configure HTTPS**: Use reverse proxy (nginx) for SSL termination
3. **Set Environment Variables**: Configure production settings
4. **Enable Logging**: Ensure comprehensive logging for monitoring
5. **Resource Planning**: Adequate RAM for ChromaDB and LLM operations

### Environment Variables
```bash
export OLLAMA_HOST="http://localhost:11434"
export LLM_MODEL="llama3.2"
export SERVER_PORT="8000"
export ADMIN_PASSWORD="secure_password_here"
```

### Docker Deployment (Future Enhancement)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "server.py"]
```

## 🐛 Debugging & Troubleshooting

### Common Issues

**Keyword Extraction Failures:**
```python
# Debug extraction results
extractor = KeywordExtractor()
result = extractor.extract_keywords(query)
print("Keywords:", result.get('keywords', []))
print("Adequate:", result.get('adequate_keywords', False))
print("Method:", result.get('method'))
```

**Web Search Problems:**
```python
# Test search capabilities
search_feature = WebSearchFeature(config, llm_client)
capabilities = search_feature.get_search_capabilities()
print("Selenium available:", capabilities.get('selenium_available'))
print("Chrome available:", capabilities.get('chrome_available'))
```

**RAG System Issues:**
```python
# Test RAG connectivity
rag_system = RAGSystem("config/config.json")
stats = rag_system.get_stats()
print("Document count:", stats.get('document_count'))
print("Collection exists:", stats.get('collection_exists'))
```

### Logging Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
```

## 📝 API Documentation Standards

### Endpoint Documentation Template
```python
@app.route('/api/module/action', methods=['POST'])
@require_auth
def module_action() -> Tuple[Dict[str, Any], int]:
    """
    Brief description of what this endpoint does
    
    Headers:
        Authorization: Bearer <session_token>
        Content-Type: application/json
        
    Request Body:
        param1 (str): Required parameter description
        param2 (int, optional): Optional parameter description (default: 5)
        param3 (bool, optional): Boolean parameter (default: False)
        
    Returns:
        200: Successful operation
            {
                "success": true,
                "data": {...},
                "message": "Operation completed"
            }
        400: Bad Request
            {
                "error": "Invalid parameter",
                "details": "Specific error details"
            }
        401: Unauthorized
            {
                "error": "Authentication required"
            }
        403: Forbidden
            {
                "error": "Insufficient permissions"
            }
        500: Internal Server Error
            {
                "error": "Internal server error",
                "details": "Error description"
            }
            
    Example:
        curl -X POST http://localhost:8000/api/module/action \\
          -H "Authorization: Bearer <token>" \\
          -H "Content-Type: application/json" \\
          -d '{"param1": "value", "param2": 10}'
    """
```

## 🔮 Future Enhancements

### Planned Features
1. **Advanced File Processing**: PDF, Word, PowerPoint support
2. **Multi-Language Support**: Internationalization framework
3. **Advanced Analytics**: Usage statistics and user behavior tracking
4. **Plugin System**: Extensible architecture for custom functionality
5. **Mobile Interface**: Responsive design improvements
6. **Voice Integration**: Speech-to-text and text-to-speech capabilities

### Technical Debt
1. **Database Migration**: Move from file-based storage to proper database
2. **Caching Layer**: Redis integration for improved performance
3. **Message Queue**: Asynchronous task processing
4. **Monitoring**: Comprehensive system monitoring with alerts
5. **Rate Limiting**: API rate limiting for resource protection

## 📚 Development Resources

### Key Dependencies
- **Flask**: Web framework and API server
- **ChromaDB**: Vector database for RAG system
- **Selenium**: Web automation for search functionality
- **Requests**: HTTP client for API calls
- **BeautifulSoup**: HTML parsing for search results

### Useful Commands
```bash
# Run development server
python server_new.py

# Test specific functionality
python -c "from src.keyword_extractor import KeywordExtractor; print('OK')"

# Check system health
curl http://localhost:8000/health

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Code Quality Tools
```bash
# Python linting
flake8 src/ core/ api/

# Type checking
mypy src/ core/ api/

# Security scanning
bandit -r src/ core/ api/
```

## 🎯 Best Practices Summary

1. **Always authenticate API endpoints** unless explicitly public
2. **Log important operations** with appropriate detail level
3. **Validate all inputs** before processing
4. **Handle errors gracefully** with meaningful messages
5. **Document all functions** and API endpoints thoroughly
6. **Test edge cases** and error conditions
7. **Follow security guidelines** for sensitive data handling
8. **Use configuration files** instead of hardcoding values
9. **Implement proper session management** with timeouts
10. **Monitor system performance** and resource usage

---

This development guide should be updated as the system evolves and new features are added. Always maintain backwards compatibility when making changes to existing APIs.