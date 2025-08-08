# RAG System Troubleshooting Guide

## Common Issues and Solutions

### 1. Collection Does Not Exist Error ⚠️

**Error Message**: 
```
chromadb.errors.InvalidCollectionException: Collection documents does not exist
```

**Cause**: This happens when:
- ChromaDB collections were created with different embedding functions
- Collection data is corrupted
- Switching between different embedding models

**Solutions**:

#### Quick Fix (Recommended):
```bash
python fix_rag_collection.py reset
```

#### Manual Fix:
```bash
# Clear ChromaDB directory
rm -rf chroma_db/
# Or on Windows: 
rmdir /s chroma_db

# Restart the system
python setup_system.py
```

#### Alternative Fix:
```bash
# Clear only the collection
python fix_rag_collection.py clear

# Reinitialize
python fix_rag_collection.py reinit
```

### 2. Embedding Model Not Available

**Error**: "Embedding model not available" or "Connection refused"

**Solutions**:
1. **Start Ollama**: `ollama serve`
2. **Install Model**: `ollama pull nomic-embed-text:latest`
3. **Check Config**: Verify `ollama_host` in `config/config.json` matches your Ollama server

### 3. Collection Incompatibility

**Error**: "Embedding function mismatch" or collection creation fails

**Solution**:
- The RAG system now automatically detects and fixes incompatible collections
- If problems persist: `python fix_rag_collection.py reset`

### 4. ChromaDB Connection Issues

**Symptoms**: 
- "Collection creation failed"
- "Unable to connect to ChromaDB"

**Solutions**:
1. Check `persist_directory` permissions in config
2. Ensure ChromaDB version compatibility
3. Clear and recreate database: `python fix_rag_collection.py reset`

### 5. Import/Dependency Errors

**Error**: "No module named 'chromadb'" or similar

**Solution**:
```bash
pip install -r requirements.txt
```

## Utility Scripts

### fix_rag_collection.py

This utility script can fix most RAG collection issues:

```bash
# Available commands:
python fix_rag_collection.py clear      # Clear ChromaDB directory
python fix_rag_collection.py reset      # Full reset and reinitialize  
python fix_rag_collection.py test       # Test RAG system
python fix_rag_collection.py reinit     # Reinitialize collection only
```

### test_rag_config.py

Test RAG configuration without causing collection conflicts:

```bash
python test_rag_config.py               # Run basic tests
python test_rag_config.py --clear       # Clear data and test
```

## Prevention Tips

1. **Consistent Configuration**: Don't change embedding models frequently
2. **Clean Shutdown**: Stop server properly before changing configurations
3. **Backup Important Data**: Keep backups of `combined_data.md` before major changes
4. **Check Dependencies**: Ensure all required packages are installed

## Step-by-Step Recovery Process

If you're experiencing persistent issues, follow this process:

### Step 1: Clean Start
```bash
python fix_rag_collection.py clear
```

### Step 2: Verify Configuration  
```bash
python test_rag_config.py
```

### Step 3: Check Ollama
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, verify model
ollama list | grep nomic-embed-text
```

### Step 4: Reinitialize System
```bash
python setup_system.py
```

### Step 5: Test RAG Functionality
```bash
python fix_rag_collection.py test
```

## Configuration Reference

Key configuration sections in `config/config.json`:

```json
{
  "rag": {
    "embedding": {
      "provider": "ollama",
      "model": "nomic-embed-text:latest",
      "ollama_host": "http://localhost:11434"
    },
    "collection": {
      "name": "documents",
      "persist_directory": "./chroma_db"
    }
  }
}
```

## Getting Help

If issues persist after trying these solutions:

1. Check the setup output for specific error messages
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Test configuration: `python test_rag_config.py`
4. Review server logs for detailed error information

Most collection issues are resolved by clearing the ChromaDB directory and reinitializing the system with the current configuration.