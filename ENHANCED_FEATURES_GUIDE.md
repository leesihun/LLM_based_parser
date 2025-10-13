# Enhanced Features Integration Guide

This guide explains how to integrate and use the new enhanced features in your LLM Assistant system.

## 🚀 Quick Setup

### 1. Install Enhanced Dependencies

```bash
# Install enhanced requirements
pip install -r requirements_enhanced.txt

# For OCR functionality, also install Tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr
```

### 2. Update Your Server

Add the enhanced features to your server initialization:

```python
# Add to server.py or your main application file
from src.enhanced_file_processor import EnhancedFileProcessor
from src.advanced_rag_system import AdvancedRAGSystem
from src.knowledge_graph import KnowledgeGraph
from api.enhanced_features import create_enhanced_features_endpoints

# Initialize enhanced components
enhanced_processor = EnhancedFileProcessor()
advanced_rag = AdvancedRAGSystem("config/config.json", base_rag_system=rag_system)
knowledge_graph = KnowledgeGraph()

# Create enhanced API endpoints
create_enhanced_features_endpoints(
    app, 
    user_manager, 
    enhanced_processor, 
    advanced_rag, 
    knowledge_graph
)
```

## 📊 Enhanced File Processing

### Supported File Types

The enhanced system now supports:

- **Code Files**: Python, JavaScript, TypeScript, Java, C++, C#, PHP, Ruby, Go, Rust, Swift, Kotlin, Scala, SQL
- **Documents**: PDF (with table extraction), Word (.docx, .doc), PowerPoint (.pptx, .ppt)
- **Images**: PNG, JPG, GIF, BMP, TIFF, WebP (with OCR)
- **Archives**: ZIP, TAR, GZ, RAR, 7Z
- **Spreadsheets**: Excel (.xlsx, .xls), CSV

### API Usage Examples

#### 1. Analyze Any File

```bash
curl -X POST http://localhost:8000/api/files/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "example_file_123.py",
    "analysis_types": ["all"]
  }'
```

Response includes:
- File content and metadata
- Type-specific analysis (code complexity, document structure, etc.)
- Extracted entities and relationships
- Security analysis for code files

#### 2. Code Analysis

```bash
curl -X POST http://localhost:8000/api/files/code-analysis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "my_script.py",
    "include_security": true,
    "include_metrics": true
  }'
```

Response includes:
- Function and class extraction
- Complexity metrics
- Security vulnerability detection
- Code improvement recommendations

#### 3. OCR Analysis

```bash
curl -X POST http://localhost:8000/api/files/image-ocr \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "document_scan.png",
    "enhance_image": true
  }'
```

Or upload directly:

```bash
curl -X POST http://localhost:8000/api/files/image-ocr \
  -H "Authorization: Bearer <token>" \
  -F "image=@document.jpg" \
  -F "enhance_image=true"
```

## 🧠 Advanced RAG Features

### Enhanced Search with Relationships

```bash
curl -X POST http://localhost:8000/api/rag/enhanced-search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "include_relationships": true,
    "max_results": 10
  }'
```

Features:
- Cross-document relationship analysis
- Content similarity scoring
- Related document suggestions
- Search insights and recommendations

### Document Collection Analysis

```bash
curl -X POST http://localhost:8000/api/rag/collection-analysis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "user",
    "force_refresh": false
  }'
```

Provides:
- Document similarity clusters
- Shared entities across documents
- Content overlap analysis
- Knowledge gap identification

### Get Document Suggestions

```bash
curl -X GET "http://localhost:8000/api/rag/document-suggestions/doc123?max_suggestions=5" \
  -H "Authorization: Bearer <token>"
```

Returns related documents with similarity scores and explanations.

## 🕸️ Knowledge Graph Features

### Add Documents to Knowledge Graph

```bash
curl -X POST http://localhost:8000/api/knowledge-graph/add-document \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "research_paper_001",
    "content": "This paper discusses machine learning applications...",
    "metadata": {
      "title": "ML Applications in Healthcare",
      "author": "Dr. Smith",
      "date": "2024-01-15"
    }
  }'
```

### Search Entities in Knowledge Graph

```bash
curl -X POST http://localhost:8000/api/knowledge-graph/search-entities \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "entity_types": ["technology", "concept"],
    "max_results": 20
  }'
```

### Get Knowledge Graph Analytics

```bash
curl -X GET http://localhost:8000/api/knowledge-graph/analytics \
  -H "Authorization: Bearer <token>"
```

Returns:
- Graph statistics (nodes, edges, density)
- Top entities by mentions
- Most connected documents
- Relationship type distribution

### Export Knowledge Graph

```bash
curl -X POST http://localhost:8000/api/knowledge-graph/export \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "include_metadata": true
  }'
```

### Find Paths Between Entities

```bash
curl -X POST http://localhost:8000/api/knowledge-graph/find-path \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "person_john_doe",
    "target_id": "organization_acme_corp"
  }'
```

## 🔧 Configuration

### Enhanced Config Options

Add to your `config/config.json`:

```json
{
  "enhanced_features": {
    "file_processing": {
      "max_file_size_mb": 50,
      "ocr_enabled": true,
      "code_analysis_enabled": true,
      "security_scanning_enabled": true
    },
    "rag_system": {
      "similarity_threshold": 0.3,
      "max_relationships": 50,
      "enable_clustering": true,
      "relationship_cache_ttl": 3600
    },
    "knowledge_graph": {
      "entity_extraction_enabled": true,
      "relationship_detection_enabled": true,
      "graph_pruning_enabled": false,
      "max_graph_size": 10000
    }
  }
}
```

## 💡 Usage Patterns

### 1. Document Intelligence Workflow

```python
# Upload and analyze a research paper
upload_response = requests.post('/api/files/upload', files={'file': open('paper.pdf', 'rb')})
file_id = upload_response.json()['file_id']

# Get enhanced analysis
analysis = requests.post('/api/files/analyze', json={'file_id': file_id})

# Add to knowledge graph
kg_response = requests.post('/api/knowledge-graph/add-document', json={
    'document_id': file_id,
    'content': analysis.json()['analysis']['content'],
    'metadata': {'type': 'research_paper'}
})

# Find related documents
suggestions = requests.get(f'/api/rag/document-suggestions/{file_id}')
```

### 2. Code Repository Analysis

```python
# Upload a ZIP file containing code
upload_response = requests.post('/api/files/upload', files={'file': open('codebase.zip', 'rb')})
file_id = upload_response.json()['file_id']

# Analyze the archive
analysis = requests.post('/api/files/analyze', json={'file_id': file_id})

# Check if it's a code project
if analysis.json()['analysis']['is_code_project']:
    # Get project structure analysis
    project_info = analysis.json()['analysis']['project_analysis']
    print(f"Project type: {project_info['project_type']}")
    print(f"Languages: {project_info['languages']}")
```

### 3. Multi-Document Research

```python
# Analyze document collection
collection_analysis = requests.post('/api/rag/collection-analysis', json={'scope': 'user'})

# Find document clusters
clusters = collection_analysis.json()['analysis']['document_clusters']
for cluster in clusters:
    print(f"Cluster: {cluster['theme']}")
    print(f"Documents: {cluster['documents']}")

# Search for specific entities across all documents
entity_search = requests.post('/api/knowledge-graph/search-entities', json={
    'query': 'artificial intelligence',
    'entity_types': ['technology', 'concept']
})
```

## 🔍 Feature Status Check

```bash
curl -X GET http://localhost:8000/api/enhanced-features/status
```

This endpoint returns the availability of all enhanced features and their dependencies.

## 🐛 Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Ensure Tesseract is installed and in PATH
   - Check that pytesseract can find the executable
   - Verify image file format is supported

2. **Office Documents Not Processing**
   - Install python-docx and python-pptx
   - Check file permissions and corruption

3. **Knowledge Graph Errors**
   - Ensure NetworkX is installed
   - Check memory usage for large graphs
   - Verify document content is not empty

4. **Performance Issues**
   - Enable caching in configuration
   - Limit file sizes for processing
   - Use pagination for large result sets

### Logging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('src.enhanced_file_processor').setLevel(logging.DEBUG)
logging.getLogger('src.advanced_rag_system').setLevel(logging.DEBUG)
logging.getLogger('src.knowledge_graph').setLevel(logging.DEBUG)
```

## 📈 Performance Optimization

### For Large Files
- Set appropriate max file sizes
- Enable parallel processing where possible
- Use streaming for large document processing

### For Knowledge Graphs
- Implement graph pruning for large datasets
- Use caching for frequently accessed relationships
- Consider graph database backends for production

### For RAG Systems
- Enable relationship caching
- Use document embedding caching
- Implement incremental analysis updates

This enhanced system provides powerful document intelligence, multi-modal analysis, and knowledge graph capabilities while maintaining API-based access for easy integration.